import httpx

from coati_agent.workspace import DatabricksAuth


class Config:
    def __init__(self):
        self.calls = 0

    def authenticate(self):
        self.calls += 1
        return {"Authorization": f"Bearer token-{self.calls}"}


def test_each_request_gets_fresh_headers():
    config = Config()
    seen = []
    transport = httpx.MockTransport(
        lambda request: seen.append(request.headers["Authorization"]) or httpx.Response(200)
    )
    client = httpx.Client(auth=DatabricksAuth(config), transport=transport)

    client.get("https://example.cloud.databricks.com/a")
    client.get("https://example.cloud.databricks.com/b")

    assert seen == ["Bearer token-1", "Bearer token-2"]
