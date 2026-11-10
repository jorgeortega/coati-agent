"""The loop: ask the model, run the tools it calls, repeat, answer.

Small on purpose. Every step is an MLflow span, so a turn's trace shows the
model calls and tool calls in order, with their timings and tokens.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import mlflow
from mlflow.entities import SpanType

from .llm import ChatModel, ToolCall, Usage
from .tools import CLIENT_CITATIONS, CLIENT_TOOLS, Citation, ServerTool, client_tool_error

MAX_STEPS = 4
# A client tool's result comes from the caller; cut it before the model reads
# it (a readiness summary is about 5 KB).
MAX_CLIENT_OUTPUT = 12_000
CUT = "\n[cut: the result was too long]"
NOT_RUN = "Error: {name} wasn't run, so there is no result. Say so, and offer to try again."
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
    # A short, safe record of each step for the Agent Lab page: no prompts,
    # no tool payloads (the full trace goes to MLflow).
    steps: list[dict[str, Any]] = field(default_factory=list)


class Agent:
    def __init__(
        self,
        model: ChatModel,
        system: str,
        tool_specs: list[dict[str, Any]],
        tools: dict[str, ServerTool],
        client_tools: frozenset[str] = CLIENT_TOOLS,
        clock: Callable[[], float] = time.perf_counter,
    ):
        self.clock = clock
        self.model = model
        self.system = system
        self.tool_specs = tool_specs
        self.tools = tools
        self.client_tools = client_tools

    @mlflow.trace(span_type=SpanType.AGENT, name="coati_agent")
    def run(self, messages: list[dict[str, Any]]) -> Turn:
        messages, not_run = self._close_unanswered([dict(m) for m in messages])
        citations: list[Citation] = []
        usage = Usage()
        steps: list[dict[str, Any]] = []
        retried_empty = False
        self._take_client_results(messages, not_run, citations, steps)

        def turn(answer: str | None, pending: ToolCall | None = None) -> Turn:
            return Turn(answer, messages, pending, citations, usage, steps)

        for _ in range(MAX_STEPS):
            started = self.clock()
            reply = self.model.chat(self.system, messages, self.tool_specs)
            usage += reply.usage
            steps.append(
                {
                    "name": "chat",
                    "type": "CHAT_MODEL",
                    "ms": self._ms_since(started),
                    "input_tokens": reply.usage.input_tokens,
                    "output_tokens": reply.usage.output_tokens,
                }
            )
            if not reply.tool_calls:
                if reply.text.strip():
                    return turn(reply.text)
                # Some reasoning models spend the whole budget thinking and
                # answer with nothing. Ask once more; never show a blank.
                steps[-1]["empty"] = True
                if retried_empty:
                    return turn(GIVE_UP)
                retried_empty = True
                continue

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
                    error = client_tool_error(tool_call.name, tool_call.arguments)
                    if error is None:
                        pending = pending or tool_call
                        continue
                    steps.append({"name": tool_call.name, "type": "CLIENT_TOOL", "refused": True})
                    messages.append(
                        {"role": "tool", "tool_call_id": tool_call.id, "content": error}
                    )
                    continue
                started = self.clock()
                found: list[Citation] = []
                content = self._run_tool(tool_call, found)
                for c in found:  # one citation per page: its best-ranked section
                    if all(c.url != seen.url for seen in citations):
                        citations.append(c)
                steps.append(
                    {
                        "name": tool_call.name,
                        "type": "TOOL",
                        "ms": self._ms_since(started),
                        "sources": [{"title": c.title, "url": c.url} for c in found],
                    }
                )
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": content})
            if pending:
                return turn(None, pending)

        return turn(GIVE_UP)

    def _close_unanswered(
        self, messages: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], set[str]]:
        """Give every tool call a result: chat APIs refuse a call left open.

        A follow-up that drops a pending call's result gets NOT_RUN in its place.
        """
        closed: list[dict[str, Any]] = []
        not_run: set[str] = set()
        i = 0
        while i < len(messages):
            message = messages[i]
            closed.append(message)
            i += 1
            calls = message.get("tool_calls") if message.get("role") == "assistant" else None
            if not calls:
                continue
            answered = set()
            while i < len(messages) and messages[i].get("role") == "tool":
                answered.add(messages[i].get("tool_call_id"))
                closed.append(messages[i])
                i += 1
            for call in calls:
                if call["id"] not in answered:
                    name = call["function"]["name"]
                    content = NOT_RUN.format(name=name)
                    closed.append({"role": "tool", "tool_call_id": call["id"], "content": content})
                    not_run.add(call["id"])
        return closed, not_run

    def _take_client_results(
        self,
        messages: list[dict[str, Any]],
        not_run: set[str],
        citations: list[Citation],
        steps: list[dict[str, Any]],
    ) -> None:
        """Cap, record and cite the client results that resume this question."""
        last_user = max((i for i, m in enumerate(messages) if m.get("role") == "user"), default=-1)
        names = {
            call["id"]: call["function"]["name"]
            for m in messages[last_user + 1 :]
            if m.get("role") == "assistant"
            for call in m.get("tool_calls") or []
        }
        for message in messages[last_user + 1 :]:
            name = names.get(message.get("tool_call_id"))
            if message.get("role") != "tool" or name not in self.client_tools:
                continue
            if message["tool_call_id"] in not_run:
                continue
            content = str(message.get("content") or "")
            if len(content) > MAX_CLIENT_OUTPUT:
                message["content"] = content[:MAX_CLIENT_OUTPUT] + CUT
            found = [c for c in [CLIENT_CITATIONS.get(name)] if c]
            for c in found:
                if c not in citations:
                    citations.append(c)
            steps.append(
                {
                    "name": name,
                    "type": "CLIENT_TOOL",
                    "sources": [{"title": c.title, "url": c.url} for c in found],
                }
            )

    def _ms_since(self, started: float) -> int:
        return round((self.clock() - started) * 1000)

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
