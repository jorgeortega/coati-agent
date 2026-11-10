"""The agent loop, driven by a scripted fake model (no network)."""

import json

import pytest

from coati_agent.agent import GIVE_UP, MAX_STEPS, Agent
from coati_agent.llm import Reply, ToolCall, Usage
from coati_agent.tools import Citation, ToolResult


class FakeModel:
    """Returns the scripted replies in order and records what it was sent."""

    def __init__(self, *replies: Reply):
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    def chat(self, system, messages, tools):
        self.calls.append([dict(m) for m in messages])
        return self.replies.pop(0)


def say(text: str) -> Reply:
    return Reply(text=text, tool_calls=[], usage=Usage(10, 5))


def call(name: str, call_id: str = "c1", **args) -> Reply:
    return Reply(
        text="",
        tool_calls=[ToolCall(id=call_id, name=name, arguments=json.dumps(args))],
        usage=Usage(10, 5),
    )


def search_docs(query: str) -> ToolResult:
    search_docs.queries.append(query)
    return ToolResult(
        content=f"Enterprise includes SSO. (query: {query})",
        citations=[Citation(title="Enterprise", url="/enterprise")],
    )


search_docs.queries = []

SPECS = [{"type": "function", "function": {"name": "search_docs"}}]


@pytest.fixture(autouse=True)
def reset_queries():
    search_docs.queries.clear()


def agent(model: FakeModel) -> Agent:
    return Agent(model=model, system="rules", tool_specs=SPECS, tools={"search_docs": search_docs})


USER = [{"role": "user", "content": "Which plan has SSO?"}]


def test_answers_directly_when_the_model_calls_no_tool():
    turn = agent(FakeModel(say("Enterprise."))).run(USER)

    assert turn.answer == "Enterprise."
    assert turn.pending is None
    assert turn.citations == []


def test_runs_a_server_tool_and_feeds_the_result_back():
    model = FakeModel(call("search_docs", query="SSO"), say("Enterprise has SSO."))
    turn = agent(model).run(USER)

    assert search_docs.queries == ["SSO"]
    assert turn.answer == "Enterprise has SSO."
    assert turn.citations == [Citation(title="Enterprise", url="/enterprise")]
    second = model.calls[1]
    assert second[-2]["role"] == "assistant"
    assert second[-2]["tool_calls"][0]["id"] == "c1"
    assert second[-1] == {
        "role": "tool",
        "tool_call_id": "c1",
        "content": "Enterprise includes SSO. (query: SSO)",
    }


def test_hands_a_client_tool_back_as_pending():
    model = FakeModel(call("check_readiness", call_id="r1", url="https://x.dev/openapi.json"))
    turn = agent(model).run(USER)

    assert turn.answer is None
    assert turn.pending == ToolCall(
        id="r1", name="check_readiness", arguments='{"url": "https://x.dev/openapi.json"}'
    )
    # The transcript ends with the assistant's call, ready for the client's result.
    assert turn.messages[-1]["tool_calls"][0]["id"] == "r1"


def test_runs_server_tools_in_the_same_reply_before_handing_back():
    reply = Reply(
        text="",
        tool_calls=[
            ToolCall(id="s1", name="search_docs", arguments='{"query": "readiness"}'),
            ToolCall(id="r1", name="check_readiness", arguments='{"url": "https://x.dev/a"}'),
        ],
        usage=Usage(10, 5),
    )
    turn = agent(FakeModel(reply)).run(USER)

    assert search_docs.queries == ["readiness"]
    assert turn.pending.id == "r1"
    assert [m.get("tool_call_id") for m in turn.messages if m["role"] == "tool"] == ["s1"]


def test_refuses_an_unknown_tool_without_running_anything():
    model = FakeModel(call("delete_everything"), say("I can't do that."))
    turn = agent(model).run(USER)

    assert search_docs.queries == []
    assert turn.answer == "I can't do that."
    result = model.calls[1][-1]
    assert result["role"] == "tool"
    assert "unknown tool" in result["content"]


def test_reports_bad_arguments_to_the_model_instead_of_crashing():
    bad = Reply(
        text="",
        tool_calls=[ToolCall(id="c1", name="search_docs", arguments="{not json")],
        usage=Usage(10, 5),
    )
    model = FakeModel(bad, say("Sorry."))
    turn = agent(model).run(USER)

    assert search_docs.queries == []
    assert "invalid arguments" in model.calls[1][-1]["content"]
    assert turn.answer == "Sorry."


def test_gives_up_after_max_steps():
    model = FakeModel(*[call("search_docs", call_id=f"c{i}", query="x") for i in range(10)])
    turn = agent(model).run(USER)

    assert len(model.calls) == MAX_STEPS
    assert turn.answer == GIVE_UP


def test_resumes_after_the_client_runs_its_tool():
    model = FakeModel(
        call("check_readiness", call_id="r1", url="https://x.dev/a"), say("Score 72.")
    )
    a = agent(model)
    first = a.run(USER)
    resumed = [*first.messages, {"role": "tool", "tool_call_id": "r1", "content": '{"score": 72}'}]

    second = a.run(resumed)

    assert second.answer == "Score 72."
    assert model.calls[1][-1]["content"] == '{"score": 72}'


def test_adds_up_token_usage_across_steps():
    model = FakeModel(call("search_docs", query="SSO"), say("Enterprise."))
    turn = agent(model).run(USER)

    assert turn.usage == Usage(20, 10)


def test_never_mutates_the_callers_messages():
    messages = [dict(m) for m in USER]
    agent(FakeModel(call("search_docs", query="SSO"), say("ok"))).run(messages)

    assert messages == USER


def test_reports_a_failing_tool_to_the_model_instead_of_crashing():
    model = FakeModel(call("search_docs", wrong_name="SSO"), say("Sorry."))
    turn = agent(model).run(USER)

    assert "failed" in model.calls[1][-1]["content"]
    assert turn.answer == "Sorry."


def test_records_each_step_for_the_page():
    clock = iter([0.0, 0.4, 0.4, 0.5, 0.5, 1.2]).__next__
    model = FakeModel(call("search_docs", query="SSO"), say("Enterprise."))
    a = Agent(
        model=model,
        system="rules",
        tool_specs=SPECS,
        tools={"search_docs": search_docs},
        clock=clock,
    )

    turn = a.run(USER)

    assert turn.steps == [
        {"name": "chat", "type": "CHAT_MODEL", "ms": 400, "input_tokens": 10, "output_tokens": 5},
        {
            "name": "search_docs",
            "type": "TOOL",
            "ms": 100,
            "sources": [{"title": "Enterprise", "url": "/enterprise"}],
        },
        {"name": "chat", "type": "CHAT_MODEL", "ms": 700, "input_tokens": 10, "output_tokens": 5},
    ]


def test_keeps_one_citation_per_page():
    def two_chunks(query: str) -> ToolResult:
        return ToolResult(
            content="...",
            citations=[
                Citation(title="Errors › Refused", url="/errors"),
                Citation(title="Errors › Timeouts", url="/errors"),
            ],
        )

    model = FakeModel(call("search_docs", query="x"), say("ok"))
    a = Agent(model=model, system="r", tool_specs=SPECS, tools={"search_docs": two_chunks})

    assert a.run(USER).citations == [Citation(title="Errors › Refused", url="/errors")]


def test_asks_again_once_when_the_answer_is_empty():
    model = FakeModel(say("  "), say("Enterprise."))
    turn = agent(model).run(USER)

    assert turn.answer == "Enterprise."
    assert len(model.calls) == 2
    assert model.calls[1] == USER  # the empty reply is not added to the history
    assert [s.get("empty") for s in turn.steps] == [True, None]


def test_gives_up_when_the_answer_is_empty_twice():
    model = FakeModel(say(""), say(""))
    turn = agent(model).run(USER)

    assert turn.answer == GIVE_UP
    assert len(model.calls) == 2
