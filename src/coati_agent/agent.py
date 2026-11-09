"""The loop: ask the model, run the tools it calls, repeat, answer.

Small on purpose. Every step is an MLflow span, so a turn's trace shows the
model calls and tool calls in order, with their timings and tokens.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import mlflow
from mlflow.entities import SpanType

from .llm import ChatModel, ToolCall, Usage
from .tools import CLIENT_TOOLS, Citation, ServerTool

MAX_STEPS = 4
GIVE_UP = (
    "Sorry, I couldn't finish that answer. Please try asking more simply, "
    "or write to us at https://latitude10.tech/contact."
)


@dataclass
class Turn:
    """One turn's outcome: an answer, or a client tool call to run first."""

    answer: str | None
    messages: list[dict[str, Any]]
    pending: ToolCall | None = None
    citations: list[Citation] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)


class Agent:
    def __init__(
        self,
        model: ChatModel,
        system: str,
        tool_specs: list[dict[str, Any]],
        tools: dict[str, ServerTool],
        client_tools: frozenset[str] = CLIENT_TOOLS,
    ):
        self.model = model
        self.system = system
        self.tool_specs = tool_specs
        self.tools = tools
        self.client_tools = client_tools

    @mlflow.trace(span_type=SpanType.AGENT, name="coati_agent")
    def run(self, messages: list[dict[str, Any]]) -> Turn:
        messages = [dict(m) for m in messages]
        citations: list[Citation] = []
        usage = Usage()

        for _ in range(MAX_STEPS):
            reply = self.model.chat(self.system, messages, self.tool_specs)
            usage += reply.usage
            if not reply.tool_calls:
                return Turn(reply.text, messages, citations=citations, usage=usage)

            messages.append(
                {
                    "role": "assistant",
                    "content": reply.text,
                    "tool_calls": [c.as_message_part() for c in reply.tool_calls],
                }
            )
            pending = None
            for tool_call in reply.tool_calls:
                if tool_call.name in self.client_tools:
                    pending = pending or tool_call
                    continue
                content = self._run_tool(tool_call, citations)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": content})
            if pending:
                return Turn(None, messages, pending=pending, citations=citations, usage=usage)

        return Turn(GIVE_UP, messages, citations=citations, usage=usage)

    def _run_tool(self, tool_call: ToolCall, citations: list[Citation]) -> str:
        with mlflow.start_span(name=tool_call.name, span_type=SpanType.TOOL) as span:
            span.set_inputs({"arguments": tool_call.arguments})
            tool = self.tools.get(tool_call.name)
            if tool is None:
                content = (
                    f"Error: unknown tool {tool_call.name!r}. Use only the tools you were given."
                )
            else:
                try:
                    args = json.loads(tool_call.arguments or "{}")
                    if not isinstance(args, dict):
                        raise ValueError("arguments must be a JSON object")
                except ValueError as error:
                    content = f"Error: invalid arguments for {tool_call.name}: {error}"
                else:
                    try:
                        result = tool(**args)
                    except Exception as error:  # the model gets the error, the turn goes on
                        content = f"Error: {tool_call.name} failed: {type(error).__name__}"
                    else:
                        citations.extend(c for c in result.citations if c not in citations)
                        content = result.content
            span.set_outputs({"content": content})
            return content
