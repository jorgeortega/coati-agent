"""check_readiness, the client tool: handed back pending, resumed with the Worker's result.

The fixture is a real free summary from the site's rules
(`readinessSummary()` over tests/fixtures/agentify-orders-openapi.json).
"""

import json
from pathlib import Path

import numpy as np

from coati_agent.agent import MAX_CLIENT_OUTPUT, Agent
from coati_agent.index import build_index
from coati_agent.llm import Reply, ToolCall, Usage
from coati_agent.serve import CoatiAgent
from coati_agent.tools import CHECK_READINESS_SPEC, READINESS

SUMMARY = (Path(__file__).parent / "fixtures" / "readiness-summary.json").read_text()
SPEC_URL = "https://api.example.com/openapi.json"
QUESTION = [{"role": "user", "content": f"How ready is {SPEC_URL} for agents?"}]


class FakeModel:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.seen = []

    def chat(self, system, messages, tools):
        self.seen.append([dict(m) for m in messages])
        return self.replies.pop(0)


def readiness(call_id="r1", **args):
    args = args or {"url": SPEC_URL}
    return Reply("", [ToolCall(call_id, "check_readiness", json.dumps(args))], Usage(10, 5))


def say(text):
    return Reply(text, [], Usage(20, 7))


def loop(*replies):
    return Agent(
        model=FakeModel(*replies),
        system="rules",
        tool_specs=[CHECK_READINESS_SPEC],
        tools={},
    )


def resumed(first_messages, content=SUMMARY, call_id="r1"):
    return [*first_messages, {"role": "tool", "tool_call_id": call_id, "content": content}]


# The loop


def test_a_question_with_a_spec_url_ends_with_a_pending_check_readiness_call():
    turn = loop(readiness()).run(QUESTION)

    assert turn.answer is None
    assert turn.pending.name == "check_readiness"
    assert json.loads(turn.pending.arguments) == {"url": SPEC_URL}
    assert turn.citations == []


def test_the_resumed_turn_answers_from_the_result_and_cites_the_readiness_check():
    a = loop(readiness(), say("It scores 54: agents will struggle with it."))
    first = a.run(QUESTION)

    second = a.run(resumed(first.messages))

    assert second.pending is None
    assert "54" in second.answer
    assert a.model.seen[1][-1]["content"] == SUMMARY
    assert second.citations == [READINESS]
    client = [s for s in second.steps if s["type"] == "CLIENT_TOOL"]
    assert client == [
        {
            "name": "check_readiness",
            "type": "CLIENT_TOOL",
            "sources": [{"title": READINESS.title, "url": READINESS.url}],
        }
    ]


def test_a_client_result_from_an_earlier_question_is_not_reported_again():
    a = loop(readiness(), say("It scores 54."), say("Pro is $150 a month."))
    first = a.run(QUESTION)
    second = a.run(resumed(first.messages))
    later = [
        *second.messages,
        {"role": "assistant", "content": second.answer},
        {"role": "user", "content": "What does Pro cost?"},
    ]

    third = a.run(later)

    assert third.citations == []
    assert [s["type"] for s in third.steps] == ["CHAT_MODEL"]


def test_a_url_that_is_not_https_is_refused_here_and_never_handed_back():
    a = loop(readiness(url="http://10.0.0.1/openapi.json"), say("I need an https URL."))
    turn = a.run(QUESTION)

    assert turn.pending is None
    assert turn.answer == "I need an https URL."
    refusal = a.model.seen[1][-1]
    assert refusal["role"] == "tool"
    assert "https" in refusal["content"]


def test_a_call_with_no_url_is_refused_too():
    a = loop(readiness(spec="openapi: 3.1.0"), say("Send me the URL."))
    turn = a.run(QUESTION)

    assert turn.pending is None
    assert "url" in a.model.seen[1][-1]["content"]


def test_a_pending_call_the_caller_never_answered_is_closed_before_the_model_sees_it():
    a = loop(readiness(), say("I couldn't run the check. Try again?"))
    first = a.run(QUESTION)

    second = a.run(first.messages)  # the follow-up came back without the result

    sent = a.model.seen[1]
    assert sent[-1]["role"] == "tool"
    assert sent[-1]["tool_call_id"] == "r1"
    assert "wasn't run" in sent[-1]["content"]
    assert second.answer.startswith("I couldn't")
    assert second.citations == []


def test_an_oversized_result_is_cut_before_the_model_sees_it():
    a = loop(readiness(), say("It scores 54."))
    first = a.run(QUESTION)

    a.run(resumed(first.messages, content="x" * (MAX_CLIENT_OUTPUT * 3)))

    sent = a.model.seen[1][-1]["content"]
    assert len(sent) <= MAX_CLIENT_OUTPUT + 100
    assert sent.endswith("[cut: the result was too long]")


def test_the_fixture_fits_under_the_cap():
    assert len(SUMMARY) < MAX_CLIENT_OUTPUT


# The served model: the two requests the Worker makes


class Embedder:
    def embed(self, texts):
        return np.array([[1.0, 0.0] for _ in texts])


def served(*replies):
    rows = [{"path": "a.md", "url": "u/a", "title": "A", "text": "## A\n\nA."}]
    return CoatiAgent.from_parts(
        model=FakeModel(*replies),
        index=build_index(rows, Embedder()),
        embedder=Embedder(),
        system="rules",
    )


def ask(a, items):
    return a.predict({"input": items}).model_dump(exclude_none=True)


def test_the_worker_round_trip_with_a_real_summary():
    a = served(readiness(), say("Orders API scores 54 of 100. Start with operationIds."))
    question = [{"role": "user", "content": QUESTION[0]["content"]}]

    first = ask(a, question)
    assert first["custom_outputs"]["status"] == "pending"
    call = first["output"][-1]
    assert (call["type"], call["name"]) == ("function_call", "check_readiness")

    result = {"type": "function_call_output", "call_id": call["call_id"], "output": SUMMARY}
    second = ask(a, [*question, *first["output"], result])

    custom = second["custom_outputs"]
    assert custom["status"] == "answered"
    assert "54" in second["output"][-1]["content"][0]["text"]
    assert custom["citations"] == [{"title": READINESS.title, "url": READINESS.url}]
    assert [s["type"] for s in custom["steps"]] == ["CLIENT_TOOL", "CHAT_MODEL"]


def test_a_closed_call_sends_the_model_only_the_chat_fields():
    a = loop(readiness(), say("Try again?"))
    first = a.run(QUESTION)
    a.run(first.messages)

    assert set(a.model.seen[1][-1]) == {"role", "tool_call_id", "content"}
