"""An OpenAI client for a Databricks workspace's serving endpoints.

Every request asks the Databricks SDK for fresh auth headers, so the CLI's
OAuth tokens (which expire after about an hour) never go stale mid-run. This
is what the SDK's deprecated `get_open_ai_client()` does; its replacement,
`databricks-openai`, needs openai<3 and brings an agents SDK this repo doesn't use.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import httpx
from openai import OpenAI


class DatabricksAuth(httpx.Auth):
    def __init__(self, config: Any):
        self.config = config  # databricks.sdk.config.Config

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers.update(self.config.authenticate())
        yield request


def openai_client(profile: str | None = None, max_retries: int = 2) -> OpenAI:
    from databricks.sdk import WorkspaceClient

    config = WorkspaceClient(profile=profile).config
    return OpenAI(
        base_url=f"{config.host.rstrip('/')}/serving-endpoints",
        api_key="unused",  # DatabricksAuth sets the Authorization header
        http_client=httpx.Client(auth=DatabricksAuth(config), timeout=60),
        max_retries=max_retries,
    )
