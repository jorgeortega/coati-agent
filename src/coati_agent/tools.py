"""What a tool returns, and which tools run outside this process."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Citation:
    title: str
    url: str


@dataclass(frozen=True)
class ToolResult:
    content: str
    citations: list[Citation] = field(default_factory=list)


# A server tool runs here, in the endpoint, with the model's arguments.
ServerTool = Callable[..., ToolResult]

# Client tools are run by the caller (the site's Worker), never here: the
# readiness rules are TypeScript, and Free Edition can't reach the internet
# freely. The loop hands the call back and resumes when the result arrives.
CLIENT_TOOLS: frozenset[str] = frozenset({"check_readiness"})

CHECK_READINESS_SPEC = {
    "type": "function",
    "function": {
        "name": "check_readiness",
        "description": (
            "Score how ready an OpenAPI document is for AI agents (0 to 100), with the "
            "same rules as https://latitude10.tech/agent-readiness. Use it when the "
            "visitor gives the URL of their OpenAPI document and asks about it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The https URL of an OpenAPI 3.0 or 3.1 document.",
                }
            },
            "required": ["url"],
        },
    },
}
