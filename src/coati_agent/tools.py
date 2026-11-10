"""What a tool returns, and which tools run outside this process."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse


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

# What a client tool's answer cites: the page that runs the same rules.
READINESS = Citation("Agent readiness check", "https://latitude10.tech/agent-readiness")
CLIENT_CITATIONS: dict[str, Citation] = {"check_readiness": READINESS}


def client_tool_error(name: str, arguments: str) -> str | None:
    """Why a client call can't be handed back, or None. The Worker checks again."""
    try:
        args = json.loads(arguments or "{}")
    except ValueError:
        args = None
    if not isinstance(args, dict) or not isinstance(args.get("url"), str):
        return f"Error: {name} needs a url: the https URL of an OpenAPI document."
    url = args["url"].strip()
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or len(url) > 2048:
        return (
            f"Error: {name} only checks a public https URL of an OpenAPI document. "
            "Ask the visitor for one."
        )
    return None


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
