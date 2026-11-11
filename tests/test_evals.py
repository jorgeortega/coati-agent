"""The eval set's shape and the deterministic checks (no network, no judge)."""

from collections import Counter

from coati_agent.evals import (
    BEHAVIOUR,
    CASES,
    as_output,
    docs_links_ok,
    groups,
    known_prices,
    load_cases,
    prices_ok,
    retrieved_expected,
    tool_ok,
)
from coati_agent.llm import ToolCall

# --- the set ----------------------------------------------------------------


def test_the_set_has_its_cases_in_seven_categories():
    cases = load_cases(CASES)
    counts = Counter(c["expectations"]["category"] for c in cases)

    assert len(cases) >= 40
    assert set(counts) == {"summary", "docs", "refuse", "injection", "dont_know", "tool", "plans"}
    assert len({c["expectations"]["id"] for c in cases}) == len(cases)
    # Results are matched to cases by question, so no two may share one.
    assert len({c["inputs"]["question"] for c in cases}) == len(cases)


def test_every_case_carries_what_its_scorers_need():
    for case in load_cases(CASES):
        e = case["expectations"]
        if e["category"] in ("summary", "docs", "plans"):
            assert e["expected_facts"], e["id"]
        if e["category"] == "docs":
            assert e["expected_doc"].startswith("https://docs.latitude10.tech/"), e["id"]
        if e["category"] in BEHAVIOUR:
            assert 1 <= len(e["guidelines"]) <= 2, e["id"]
        if e["category"] == "tool":
            assert e["expected_url"] in case["inputs"]["question"], e["id"]


def test_expected_docs_are_real_pages():
    from coati_agent.index import load_rows

    urls = {row["url"] for row in load_rows()}
    for case in load_cases(CASES):
        if "expected_doc" in case["expectations"]:
            assert case["expectations"]["expected_doc"] in urls, case["expectations"]["id"]


def test_groups_split_the_set_without_losing_a_case():
    cases = load_cases(CASES)
    grouped = groups(cases)
    assert sum(len(rows) for rows in grouped.values()) == len(cases)
    assert set(grouped) == {"summary", "docs", "behaviour", "tool", "plans"}


# --- outputs ----------------------------------------------------------------


def test_a_pending_call_becomes_a_readable_output():
    call = ToolCall("r1", "check_readiness", '{"url": "https://x.dev/openapi.json"}')
    assert as_output(None, call) == 'CALL check_readiness {"url": "https://x.dev/openapi.json"}'
    assert as_output("Enterprise.", None) == "Enterprise."


# --- tool_ok ----------------------------------------------------------------

TOOL = {"category": "tool", "expected_url": "https://x.dev/openapi.json"}


def test_tool_case_passes_only_with_the_call_and_its_url():
    assert tool_ok('CALL check_readiness {"url": "https://x.dev/openapi.json"}', TOOL)
    assert not tool_ok('CALL check_readiness {"url": "https://other.dev/a.json"}', TOOL)
    assert not tool_ok("Your spec looks great!", TOOL)


def test_other_cases_must_not_call_the_client_tool():
    assert tool_ok("Pro costs $150.", {"category": "summary"})
    assert not tool_ok('CALL check_readiness {"url": "https://x"}', {"category": "refuse"})


# --- retrieved_expected -----------------------------------------------------


def test_retrieval_passes_when_the_expected_page_was_retrieved():
    expected = {"expected_doc": "https://docs.latitude10.tech/enterprise/sso"}
    assert retrieved_expected(["https://docs.latitude10.tech/enterprise/sso"], expected)
    assert not retrieved_expected(["https://docs.latitude10.tech/enterprise"], expected)
    assert not retrieved_expected([], expected)


# --- docs_links_ok ----------------------------------------------------------


def test_docs_links_must_use_the_docs_host():
    assert docs_links_ok("See https://docs.latitude10.tech/hosted-mcp/setup.")
    assert docs_links_ok("See /pricing or https://latitude10.tech/platform/mcp.")
    assert docs_links_ok("Enterprise has SSO: https://latitude10.tech/enterprise")
    assert not docs_links_ok("See /hosted-mcp/refused-hosts.")
    assert not docs_links_ok("See https://latitude10.tech/sdks/python for details.")
    assert not docs_links_ok("Read (/get-started/keys-and-tokens).")
    assert not docs_links_ok("See https://latitude10.tech/enterprise/sso")


# --- prices_ok --------------------------------------------------------------


def test_known_prices_come_from_the_export():
    prices = known_prices()
    assert {"150", "125", "600", "500", "19", "2500", "11000"} <= prices


def test_prices_must_be_ones_the_site_publishes():
    prices = {"150", "125", "19"}
    assert prices_ok("Pro is $150 a month, or $125 billed annually.", prices)
    assert prices_ok("Kits from $19, paid once.", prices)
    assert not prices_ok("Pro is $99 a month.", prices)
    assert not prices_ok("Kits from US$1,500.", prices)
    assert prices_ok("No prices here.", prices)


def test_summarise_survives_missing_expectation_columns():
    from types import SimpleNamespace

    import pandas as pd

    from coati_agent.evals import Recorder, summarise

    cases = load_cases(CASES)
    q1, q2 = (c["inputs"]["question"] for c in cases[:2])
    feedback = {"assessment_name": "correctness", "feedback": {"value": "yes"}}
    df = pd.DataFrame(
        [
            {
                "request": {"question": q1},
                "response": "a",
                "id/value": "s01",
                "assessments": [feedback],
            },
            {
                "request": {"question": q2},
                "response": "b",
                "id/value": float("nan"),
                "assessments": [feedback],
            },
        ]
    )
    recorder = Recorder()
    recorder.add(q1, ms=1200, input_tokens=10, output_tokens=2)

    out = summarise(
        "m", "databricks", {"summary": SimpleNamespace(result_df=df)}, recorder, "run", cases
    )

    assert [r["id"] for r in out["rows"]] == [
        cases[0]["expectations"]["id"],
        cases[1]["expectations"]["id"],
    ]
    assert out["scores"]["correctness"]["pass"] == 2
    assert out["latency_ms"]["p50"] == 1200


def test_the_baseline_waits_out_the_sites_throttle():
    import httpx

    from coati_agent.evals import Recorder, baseline_target

    answers = iter([httpx.Response(429), httpx.Response(429), httpx.Response(200, text="Pro.")])
    client = httpx.Client(transport=httpx.MockTransport(lambda request: next(answers)))
    sleeps: list[float] = []

    predict = baseline_target(
        "http://x/api/support", Recorder(), client=client, sleep=sleeps.append
    )

    assert predict("What does Pro cost?") == "Pro."
    assert sleeps == [60, 60]


def test_results_table_has_a_row_per_run_and_rates_per_check():
    from coati_agent.evals import results_table

    def run(label, retrieved, latency):
        return {
            "label": label,
            "date": "2026-11-10",
            "judge": "databricks",
            "cases": 40,
            "scores": {
                "correctness": {"pass": 18, "fail": 6, "error": 0, "skipped": 0},
                "expected_page_retrieved": {
                    "pass": retrieved,
                    "fail": 16 - retrieved,
                    "error": 0,
                    "skipped": 0,
                },
            },
            "latency_ms": {"p50": latency, "p90": latency * 2},
            "tokens_per_turn": {"input": 15000, "output": 150},
        }

    table = results_table([run("qwen", 13, 4969), run("baseline-coati", 0, 1500)])

    lines = table.splitlines()
    assert lines[0].startswith("| Target |")
    assert "| qwen | 18/24 | 13/16 |" in table
    assert "| baseline-coati | 18/24 | 0/16 |" in table
    assert "5.0 s" in table


# --- the LangGraph lab's agent (coati-langgraph), over HTTP ------------------------

LG_CHUNKS = [
    {
        "heading": "Keys and tokens › CI keys",
        "url": "https://docs.latitude10.tech/get-started/keys-and-tokens",
        "text": "A CI key starts with l10p_.",
    },
    {
        "heading": "Workflow › 3. Add",
        "url": "https://docs.latitude10.tech/sdks/workflow",
        "text": "First.",
    },
    {
        "heading": "Workflow › 3. Add",
        "url": "https://docs.latitude10.tech/sdks/workflow",
        "text": "Second.",
    },
]


def test_a_langgraph_answer_becomes_the_output_and_its_searches_the_retrieved_docs():
    from coati_agent.evals import langgraph_reply

    body = {
        "answer": "Rotate it on the project page.",
        "steps": [
            {"name": "chat", "type": "CHAT_MODEL", "ms": 10},
            {
                "name": "search_docs",
                "type": "TOOL",
                "ms": 5,
                "sources": [
                    {
                        "title": "Keys and tokens › CI keys",
                        "url": "https://docs.latitude10.tech/get-started/keys-and-tokens",
                    },
                    {
                        "title": "Workflow › 3. Add",
                        "url": "https://docs.latitude10.tech/sdks/workflow",
                    },
                ],
            },
            {"name": "get_plans", "type": "TOOL", "ms": 1, "sources": []},
        ],
        "usage": {"input_tokens": 3000, "output_tokens": 40},
        "model": "gpt-oss-120b",
    }
    reply = langgraph_reply(body, LG_CHUNKS)

    assert reply["output"] == "Rotate it on the project page."
    assert reply["tools"] == ["search_docs", "get_plans"]
    [search] = reply["searches"]
    assert [d["metadata"]["doc_uri"] for d in search] == [
        "https://docs.latitude10.tech/get-started/keys-and-tokens",
        "https://docs.latitude10.tech/sdks/workflow",
    ]
    assert search[0]["page_content"] == "A CI key starts with l10p_."
    # One heading on one page names two chunks: both count.
    assert search[1]["page_content"] == "First.\n\nSecond."
    assert reply["usage"] == {"input_tokens": 3000, "output_tokens": 40}


def test_a_pending_langgraph_call_is_scored_like_the_local_agents():
    from coati_agent.evals import langgraph_reply

    url = "https://petstore3.swagger.io/api/v3/openapi.json"
    body = {
        "pending": {"id": "c1", "name": "check_readiness", "args": {"url": url}},
        "messages": [],
        "steps": [],
        "usage": {},
    }
    out = langgraph_reply(body, LG_CHUNKS)["output"]

    assert out.startswith("CALL check_readiness ")
    assert tool_ok(out, {"category": "tool", "expected_url": url})


def test_the_langgraph_target_refuses_a_different_model_than_its_label():
    import httpx
    import pytest

    from coati_agent.evals import Recorder, langgraph_target

    reply = {
        "answer": "Hi.",
        "steps": [],
        "usage": {"input_tokens": 1, "output_tokens": 1},
        "model": "qwen3-30b-a3b",
    }
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=reply))
    )
    recorder = Recorder()

    predict = langgraph_target(
        "http://x/invoke", "qwen3-30b-a3b", recorder, LG_CHUNKS, client=client
    )
    assert predict("Hi?") == "Hi."
    assert recorder.rows["Hi?"]["input_tokens"] == 1

    wrong = langgraph_target(
        "http://x/invoke", "gpt-oss-120b", Recorder(), LG_CHUNKS, client=client
    )
    with pytest.raises(RuntimeError, match="qwen3-30b-a3b"):
        wrong("Hi?")
