"""The served model: Responses items in, Responses items and steps out."""

import json

import numpy as np

from coati_agent.index import build_index
from coati_agent.llm import Reply, ToolCall, Usage
from coati_agent.serve import CoatiAgent


class FakeModel:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.seen = []

    def chat(self, system, messages, tools):
        self.seen.append([dict(m) for m in messages])
        return self.replies.pop(0)


class Embedder:
    def embed(self, texts):
        return np.array([[1.0, float("sso" in t.lower())] for t in texts])


ROWS = [{"path": "e.md", "url": "u/e", "title": "Enterprise", "text": "## SSO\n\nSSO here."}]


def agent(*replies):
    return CoatiAgent.from_parts(
        model=FakeModel(*replies),
        index=build_index(ROWS, Embedder()),
        embedder=Embedder(),
        system="rules",
    )


def call(name, call_id, **args):
    return Reply("", [ToolCall(call_id, name, json.dumps(args))], Usage(10, 5))


def ask(a, items):
    return a.predict({"input": items}).model_dump(exclude_none=True)


def test_an_answer_comes_back_with_the_tool_items_citations_and_steps():
    a = agent(
        call("search_docs", "c1", query="SSO"), Reply("Enterprise has SSO.", [], Usage(20, 7))
    )

    out = ask(a, [{"role": "user", "content": "Which plan has SSO?"}])

    kinds = [item["type"] for item in out["output"]]
    assert kinds == ["function_call", "function_call_output", "message"]
    assert out["output"][0]["name"] == "search_docs"
    assert out["output"][2]["content"][0]["text"] == "Enterprise has SSO."
    custom = out["custom_outputs"]
    assert custom["status"] == "answered"
    assert custom["citations"] == [{"title": "Enterprise › SSO", "url": "u/e"}]
    assert [s["type"] for s in custom["steps"]] == ["CHAT_MODEL", "TOOL", "CHAT_MODEL"]
    assert custom["usage"] == {"input_tokens": 30, "output_tokens": 12}


def test_a_client_tool_comes_back_pending_and_the_turn_resumes_with_its_output():
    a = agent(
        call("check_readiness", "r1", url="https://x.dev/openapi.json"),
        Reply("It scores 72.", [], Usage(5, 5)),
    )
    question = [{"role": "user", "content": "Check https://x.dev/openapi.json"}]

    first = ask(a, question)

    assert first["custom_outputs"]["status"] == "pending"
    pending = first["output"][-1]
    assert (pending["type"], pending["name"], pending["call_id"]) == (
        "function_call",
        "check_readiness",
        "r1",
    )

    result = {"type": "function_call_output", "call_id": "r1", "output": '{"score": 72}'}
    second = ask(a, [*question, *first["output"], result])

    assert second["custom_outputs"]["status"] == "answered"
    assert second["output"][-1]["content"][0]["text"] == "It scores 72."
    sent = a.agent.model.seen[1]
    assert sent[-1] == {"role": "tool", "content": '{"score": 72}', "tool_call_id": "r1"}


def test_the_served_tools_are_search_docs_and_the_client_tool():
    names = [spec["function"]["name"] for spec in agent().agent.tool_specs]
    assert names == ["search_docs", "check_readiness"]


def test_get_plans_is_offered_and_run_when_a_plans_tool_is_given():
    from coati_agent.tools import Citation, ToolResult

    def get_plans(plan=None):
        return ToolResult('[{"name": "Pro", "seats": 5}]', [Citation("Pricing", "p")])

    model = FakeModel(call("get_plans", "c1", plan="Pro"), Reply("Pro has 5 seats.", [], Usage()))
    a = CoatiAgent.from_parts(
        model=model,
        index=build_index(ROWS, Embedder()),
        embedder=Embedder(),
        system="rules",
        plans=get_plans,
    )

    out = ask(a, [{"role": "user", "content": "How many seats on Pro?"}])

    assert "get_plans" in [s["function"]["name"] for s in a.agent.tool_specs]
    assert out["output"][1]["output"] == '[{"name": "Pro", "seats": 5}]'
    assert out["custom_outputs"]["citations"] == [{"title": "Pricing", "url": "p"}]


def test_without_a_plans_tool_get_plans_is_not_offered():
    names = [s["function"]["name"] for s in agent().agent.tool_specs]
    assert "get_plans" not in names


def test_without_a_warehouse_get_plans_reads_the_shipped_file():
    from coati_agent.prompt import DATA_DIR
    from coati_agent.serve import DEFAULT_CONFIG, _plans_tool

    tool = _plans_tool(DEFAULT_CONFIG, DATA_DIR)

    rows = json.loads(tool(plan="Pro").content)
    assert [r["name"] for r in rows] == ["Pro"]
    assert rows[0]["price"].startswith("$")
