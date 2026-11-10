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
from .plans import GET_PLANS_SPEC
from .prompt import load_export, system_prompt
from .tools import CHECK_READINESS_SPEC, ServerTool

DEFAULT_CONFIG = {
    "llm_endpoint": "databricks-qwen35-122b-a10b",  # chosen by the Task 7 evals
    "embedding_endpoint": "databricks-gte-large-en",
    "max_tokens": 1500,  # Qwen3.5 reasons first; 500 left some answers empty
    "k": 5,
    # get_plans reads the plans.jsonl the model ships with, unless both of
    # these are set: then it calls the Unity Catalog function on this SQL
    # warehouse (the demo on Free Edition; spec, open question 6).
    "plans_function": None,
    "warehouse_id": None,
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
        plans: ServerTool | None = None,
    ) -> CoatiAgent:
        specs = [SEARCH_DOCS_SPEC, CHECK_READINESS_SPEC]
        tools = {"search_docs": search_docs_tool(index, embedder, k=k)}
        if plans is not None:
            specs.insert(1, GET_PLANS_SPEC)
            tools["get_plans"] = plans
        self = cls()
        self.agent = Agent(model=model, system=system, tool_specs=specs, tools=tools)
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
            plans=_plans_tool(config, Path(context.artifacts["data"])),
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


def _plans_tool(config: dict[str, Any], data_dir: Path) -> ServerTool:
    from .plans import file_plans_tool, parse_rows

    if not (config.get("plans_function") and config.get("warehouse_id")):
        return file_plans_tool(parse_rows(load_export(data_dir)["plans.jsonl"]))
    from databricks.sdk import WorkspaceClient

    from .plans import get_plans_tool, warehouse_sql

    run = warehouse_sql(WorkspaceClient(), config["warehouse_id"])
    return get_plans_tool(run, config["plans_function"])
