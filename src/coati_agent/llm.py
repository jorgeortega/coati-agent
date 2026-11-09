"""The model side of the loop: one `chat` call, in OpenAI's chat format.

Databricks' Foundation Model API endpoints accept the OpenAI chat format, so
one small adapter covers every model the evals compare (spec D2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import mlflow
from mlflow.entities import SpanType


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            self.input_tokens + other.input_tokens, self.output_tokens + other.output_tokens
        )


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON, exactly as the model wrote it

    def as_message_part(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {"name": self.name, "arguments": self.arguments},
        }


@dataclass(frozen=True)
class Reply:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)


class ChatModel(Protocol):
    def chat(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Reply: ...


class OpenAICompatibleModel:
    """A Databricks serving endpoint, called through an OpenAI-style client.

    `client` is anything with `chat.completions.create`, for example
    `WorkspaceClient().serving_endpoints.get_open_ai_client()`.
    """

    def __init__(self, client: Any, endpoint: str, max_tokens: int = 500):
        self.client = client
        self.endpoint = endpoint
        self.max_tokens = max_tokens

    @mlflow.trace(span_type=SpanType.CHAT_MODEL, name="chat")
    def chat(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> Reply:
        response = self.client.chat.completions.create(
            model=self.endpoint,
            messages=[{"role": "system", "content": system}, *messages],
            tools=tools or None,
            max_tokens=self.max_tokens,
        )
        message = response.choices[0].message
        calls = [
            ToolCall(id=c.id, name=c.function.name, arguments=c.function.arguments or "{}")
            for c in (message.tool_calls or [])
        ]
        usage = response.usage
        return Reply(
            text=message.content or "",
            tool_calls=calls,
            usage=Usage(usage.prompt_tokens, usage.completion_tokens) if usage else Usage(),
        )
