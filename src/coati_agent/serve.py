"""The coati agent as an MLflow ResponsesAgent, for a Model Serving endpoint.

Input: Responses items (the conversation, plus any tool items from earlier
in the turn). Output: the items this turn produced, ending in either the
answer or a pending client tool call, and `custom_outputs` with the status,
citations, usage and the steps for the Agent Lab page (spec D3).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

from .agent import Agent, Turn
from .index import SEARCH_DOCS_SPEC, DatabricksEmbedder, DocsIndex, Embedder, search_docs_tool
from .llm import ChatModel, OpenAICompatibleModel
from .prompt import system_prompt
from .tools import CHECK_READINESS_SPEC

DEFAULT_CONFIG = {
    "llm_endpoint": "databricks-gpt-oss-120b",  # Task 6 comparison; Task 7 evals decide
    "embedding_endpoint": "databricks-gte-large-en",
    "max_tokens": 500,
    "k": 5,
}


class CoatiAgent(ResponsesAgent):
    agent: Agent

    @classmethod
    def from_parts(
        cls,
        model: ChatModel,
        index: DocsIndex,
        embedder: Embedder,
        system: str,
        k: int = 5,
    ) -> CoatiAgent:
        self = cls()
        self.agent = Agent(
            model=model,
            system=system,
            tool_specs=[SEARCH_DOCS_SPEC, CHECK_READINESS_SPEC],
            tools={"search_docs": search_docs_tool(index, embedder, k=k)},
        )
        return self

    def load_context(self, context: Any) -> None:
        """Called once when the endpoint starts: artifacts and config from the logged model."""
        from .workspace import openai_client

        config = {**DEFAULT_CONFIG, **(getattr(context, "model_config", None) or {})}
        client = openai_client(max_retries=2)  # the endpoint's own credentials
        model = OpenAICompatibleModel(client, config["llm_endpoint"], config["max_tokens"])
        # One question per turn, so no pacing; still back off on a 429.
        embedder = DatabricksEmbedder(
            client, config["embedding_endpoint"], retries=2, min_interval=0
        )
        built = CoatiAgent.from_parts(
            model=model,
            index=DocsIndex.load(Path(context.artifacts["index"])),
            embedder=embedder,
            system=system_prompt(Path(context.artifacts["data"])),
            k=int(config["k"]),
        )
        self.agent = built.agent

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        items = [item.model_dump(exclude_none=True) for item in request.input]
        messages = self.prep_msgs_for_cc_llm(items)
        turn = self.agent.run(messages)
        output = self._items(turn.messages[len(messages) :])
        if turn.pending is None:
            output.append(self.create_text_output_item(turn.answer or "", _id()))
        status = "pending" if turn.pending else "answered"
        return ResponsesAgentResponse(output=output, custom_outputs=_custom(turn, status))

    def _items(self, new_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """The turn's assistant tool calls and tool results, as Responses items."""
        items: list[dict[str, Any]] = []
        for message in new_messages:
            if message["role"] == "assistant":
                for call in message.get("tool_calls", []):
                    function = call["function"]
                    items.append(
                        self.create_function_call_item(
                            _id(), call["id"], function["name"], function["arguments"]
                        )
                    )
            elif message["role"] == "tool":
                items.append(
                    self.create_function_call_output_item(
                        message["tool_call_id"], message["content"]
                    )
                )
        return items


def _custom(turn: Turn, status: str) -> dict[str, Any]:
    return {
        "status": status,
        "citations": [{"title": c.title, "url": c.url} for c in turn.citations],
        "usage": {
            "input_tokens": turn.usage.input_tokens,
            "output_tokens": turn.usage.output_tokens,
        },
        "steps": turn.steps,
    }


def _id() -> str:
    return uuid.uuid4().hex
