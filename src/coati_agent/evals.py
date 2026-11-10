"""The eval set, its scorers, and the runner.

    DATABRICKS_CONFIG_PROFILE=coati-free uv run python -m coati_agent.evals \
        --model databricks-gpt-oss-120b
    DATABRICKS_CONFIG_PROFILE=coati-free uv run python -m coati_agent.evals --target baseline

Each run writes evals/results/<date>-<label>.json. The judge is Databricks'
managed judge, which is none of the models being compared. Cases are scored
in four groups, so a scorer only sees the cases it applies to:

- summary: facts from the site summary. Correctness.
- docs: facts only the docs have. Correctness, expected page retrieved, groundedness.
- behaviour: refusals, injections, unknowns. The case's guidelines.
- tool: a spec URL to score. check_readiness called with that URL.

Every group also runs the code checks: no unpublished prices, docs links on
the docs host, and check_readiness only where it belongs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import statistics
import time
from pathlib import Path
from typing import Any

from .llm import ToolCall
from .prompt import DATA_DIR, load_export

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "evals" / "questions.jsonl"
RESULTS = ROOT / "evals" / "results"

# Behaviour cases carry their own guidelines in questions.jsonl: one or two
# that apply to that case only. (v1 gave every case its category's list, and
# the judge failed answers on guidelines that didn't apply to them.)
BEHAVIOUR = ("refuse", "injection", "dont_know")

GROUP_OF = {
    "summary": "summary",
    "docs": "docs",
    "refuse": "behaviour",
    "injection": "behaviour",
    "dont_know": "behaviour",
    "tool": "tool",
}


# --- the set ----------------------------------------------------------------


def load_cases(path: Path = CASES) -> list[dict[str, Any]]:
    """Rows in mlflow.genai.evaluate's shape: inputs and expectations."""
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        expectations = {"id": row["id"], **row["expectations"]}
        cases.append({"inputs": {"question": row["question"]}, "expectations": expectations})
    return cases


def groups(cases: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        out.setdefault(GROUP_OF[case["expectations"]["category"]], []).append(case)
    return out


# --- outputs and the code checks ----------------------------------------------


def as_output(answer: str | None, pending: ToolCall | None) -> str:
    """What a judge and the checks see: the answer, or the pending client call."""
    if pending is not None:
        return f"CALL {pending.name} {pending.arguments}"
    return answer or ""


def tool_ok(output: str, expectations: dict[str, Any]) -> bool:
    called = output.startswith("CALL check_readiness")
    if expectations.get("category") == "tool":
        return called and expectations["expected_url"] in output
    return not output.startswith("CALL ")


def retrieved_expected(doc_uris: list[str], expectations: dict[str, Any]) -> bool:
    return expectations["expected_doc"] in doc_uris


DOCS_SECTIONS = (
    "get-started",
    "quickstart",
    "registry",
    "registry-api",
    "api-reference",
    "api-client",
    "docs-hosting",
    "sdks",
    "hosted-mcp",
)
# A docs path written on the site's host, or as a bare path. /enterprise is a
# site page too, so only its subpages (/enterprise/sso) count as docs paths.
_WRONG_HOST = re.compile(
    r"(?:https?://(?:www\.)?latitude10\.tech|(?<![\w.:/])|(?<=\())"
    rf"/(?:(?:{'|'.join(DOCS_SECTIONS)})(?=[/\s).,;:]|$)|enterprise/[a-z])"
)


def docs_links_ok(output: str) -> bool:
    return _WRONG_HOST.search(output) is None


_PRICE = re.compile(r"\$\s?(\d[\d,]*)(?:\.\d+)?")


def known_prices(data_dir: Path = DATA_DIR) -> set[str]:
    text = "".join(load_export(data_dir).values())
    return {m.group(1).replace(",", "") for m in _PRICE.finditer(text)}


def prices_ok(output: str, prices: set[str]) -> bool:
    return all(m.group(1).replace(",", "") in prices for m in _PRICE.finditer(output))


# --- MLflow scorers ---------------------------------------------------------------


def make_scorers(judge: str | None) -> dict[str, list[Any]]:
    from mlflow.entities import SpanType
    from mlflow.genai.scorers import (
        Correctness,
        ExpectationsGuidelines,
        RetrievalGroundedness,
        scorer,
    )

    prices = known_prices()
    model = {} if judge in (None, "databricks") else {"model": judge}

    @scorer
    def check_readiness_use(outputs: str, expectations: dict[str, Any]) -> bool:
        return tool_ok(outputs, expectations)

    @scorer
    def published_prices(outputs: str) -> bool:
        return prices_ok(outputs, prices)

    @scorer
    def docs_links(outputs: str) -> bool:
        return docs_links_ok(outputs)

    @scorer
    def expected_page_retrieved(expectations: dict[str, Any], trace: Any) -> bool:
        uris = [
            doc.get("metadata", {}).get("doc_uri", "")
            for span in trace.search_spans(span_type=SpanType.RETRIEVER)
            for doc in (span.outputs or [])
        ]
        return retrieved_expected(uris, expectations)

    checks = [check_readiness_use, published_prices, docs_links]
    return {
        "summary": [Correctness(**model), *checks],
        "docs": [
            Correctness(**model),
            expected_page_retrieved,
            RetrievalGroundedness(**model),
            *checks,
        ],
        "behaviour": [ExpectationsGuidelines(**model), *checks],
        "tool": checks,
    }


# --- targets ----------------------------------------------------------------------


class Recorder:
    """Latency and tokens per question, beside what MLflow records."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}

    def add(self, question: str, **values: Any) -> None:
        self.rows[question] = values


def local_target(model: str, recorder: Recorder, profile: str | None = None):
    """The served agent's code, in this process, on a Foundation Model API model."""
    import mlflow
    from mlflow.entities import SpanType

    from .index import DatabricksEmbedder, DocsIndex
    from .llm import OpenAICompatibleModel
    from .prompt import system_prompt
    from .serve import DEFAULT_CONFIG, CoatiAgent
    from .workspace import openai_client

    index_dir = ROOT / "build" / "index"
    if not index_dir.exists():
        raise SystemExit("No build/index: run `python -m coati_agent.index` first.")
    client = openai_client(profile, max_retries=6)
    agent = CoatiAgent.from_parts(
        model=OpenAICompatibleModel(client, model, DEFAULT_CONFIG["max_tokens"]),
        index=DocsIndex.load(index_dir),
        embedder=DatabricksEmbedder(client, "databricks-gte-large-en", min_interval=0),
        system=system_prompt(),
    )

    @mlflow.trace(span_type=SpanType.AGENT, name="eval_turn")
    def predict(question: str) -> str:
        started = time.perf_counter()
        out = agent.predict({"input": [{"role": "user", "content": question}]})
        ms = round((time.perf_counter() - started) * 1000)
        custom = out.custom_outputs or {}
        last = out.output[-1].model_dump()
        if last["type"] == "function_call":
            text = as_output(None, ToolCall(last["call_id"], last["name"], last["arguments"]))
        else:
            text = as_output(last["content"][0]["text"], None)
        recorder.add(question, ms=ms, **custom.get("usage", {}))
        return text

    return predict


def baseline_target(
    url: str,
    recorder: Recorder,
    client: Any = None,
    sleep: Any = time.sleep,
    patience: int = 12,
):
    """Today's coati: the site's /api/support (Claude Haiku 5.5, no tools).

    The site allows 20 messages per IP per 10 minutes, and the set is bigger,
    so a 429 waits a minute and tries again rather than loosening the site.
    """
    import httpx
    import mlflow
    from mlflow.entities import SpanType

    http = client or httpx.Client(timeout=60)

    @mlflow.trace(span_type=SpanType.AGENT, name="eval_turn")
    def predict(question: str) -> str:
        body = {"messages": [{"role": "user", "content": question}]}
        for _ in range(patience):
            started = time.perf_counter()
            response = http.post(url, json=body)
            if response.status_code != 429:
                break
            sleep(60)
        response.raise_for_status()
        recorder.add(question, ms=round((time.perf_counter() - started) * 1000))
        return response.text

    return predict


# --- the run ----------------------------------------------------------------------


def summarise(
    label: str,
    judge: str,
    results: dict[str, Any],
    recorder: Recorder,
    run_id: str,
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    # Ids and categories come from the set, by question: a row whose
    # expectation columns are missing comes back from pandas as NaN.
    by_question = {c["inputs"]["question"]: c["expectations"] for c in cases}
    rows: list[dict[str, Any]] = []
    for group, result in results.items():
        df = result.result_df
        for _, record in df.iterrows():
            scores, notes = {}, {}
            for assessment in record.get("assessments") or []:
                feedback = assessment.get("feedback")
                if feedback is None:  # an expectation, not a score
                    continue
                name = assessment["assessment_name"]
                error = feedback.get("error") or assessment.get("error")
                value = feedback.get("value")
                if error and "No retrieval context" in str(error):
                    # The agent didn't search: expected_page_retrieved already fails it.
                    scores[name], error = "skipped", None
                else:
                    scores[name] = "error" if error else value
                rationale = assessment.get("rationale")
                if error or (rationale and value not in (True, "yes")):
                    notes[name] = str(error or rationale)[:400]
            request = record.get("request")
            question = request.get("question", "") if isinstance(request, dict) else ""
            expected = by_question.get(question, {})
            rows.append(
                {
                    "id": expected.get("id", "unknown"),
                    "category": expected.get("category", "unknown"),
                    "group": group,
                    "question": question,
                    "output": record.get("response"),
                    "scores": scores,
                    "notes": notes,
                    **recorder.rows.get(question, {}),
                }
            )
    rows.sort(key=lambda r: r["id"])

    def tally(subset: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for row in subset:
            for name, value in row["scores"].items():
                t = out.setdefault(name, {"pass": 0, "fail": 0, "error": 0, "skipped": 0})
                if value == "skipped":
                    t["skipped"] += 1
                elif value == "error" or value is None:
                    t["error"] += 1
                elif value in (True, "yes"):
                    t["pass"] += 1
                else:
                    t["fail"] += 1
        return out

    ms = sorted(r["ms"] for r in rows if "ms" in r)
    answered = [r for r in rows if "input_tokens" in r]
    return {
        "label": label,
        "date": dt.date.today().isoformat(),
        "judge": judge,
        "mlflow_run_id": run_id,
        "cases": len(rows),
        "scores": tally(rows),
        "by_category": {
            c: tally([r for r in rows if r["category"] == c])
            for c in sorted({r["category"] for r in rows})
        },
        "latency_ms": {
            "p50": statistics.median(ms) if ms else None,
            "p90": ms[int(0.9 * (len(ms) - 1))] if ms else None,
        },
        "tokens_per_turn": {
            "input": round(statistics.mean(r["input_tokens"] for r in answered))
            if answered
            else None,
            "output": round(statistics.mean(r["output_tokens"] for r in answered))
            if answered
            else None,
        },
        "rows": rows,
    }


TABLE_CHECKS = [
    ("correctness", "Correct facts"),
    ("expected_page_retrieved", "Right page searched"),
    ("retrieval_groundedness", "Grounded in search"),
    ("expectations_guidelines", "Behaviour"),
    ("check_readiness_use", "Tool use"),
    ("published_prices", "No unpublished prices"),
    ("docs_links", "Docs links on docs host"),
]


def results_table(runs: list[dict[str, Any]]) -> str:
    """A Markdown table: one row per run, passes out of scored cases per check."""
    header = ["Target", *(label for _, label in TABLE_CHECKS), "p50", "Tokens in/out"]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for run in runs:
        cells = [run["label"]]
        for key, _ in TABLE_CHECKS:
            t = run["scores"].get(key)
            cells.append(f"{t['pass']}/{t['pass'] + t['fail']}" if t else "n/a")
        p50 = run["latency_ms"]["p50"]
        cells.append(f"{p50 / 1000:.1f} s" if p50 else "n/a")
        tokens = run["tokens_per_turn"]
        cells.append(f"{tokens['input']}/{tokens['output']}" if tokens["input"] else "n/a")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_results_md() -> Path:
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RESULTS.glob("*.json"))]
    runs = [r for r in runs if not r["label"].endswith("-pilot")]
    out = ROOT / "evals" / "RESULTS.md"
    dates = sorted({r["date"] for r in runs})
    out.write_text(
        "# Eval results\n\n"
        f"{runs[0]['cases'] if runs else 0} cases (`evals/questions.jsonl`), judged by "
        "Databricks' managed judge. Generated by `python -m coati_agent.evals --table` "
        f"from `evals/results/` ({', '.join(dates)}). A check counts only the cases it "
        "applies to; groundedness is skipped when the agent didn't search.\n\n"
        + results_table(runs),
        encoding="utf-8",
    )
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the eval set against one target.")
    parser.add_argument("--target", choices=["local", "baseline"], default="local")
    parser.add_argument("--model", default="databricks-gpt-oss-120b")
    parser.add_argument("--baseline-url", default="http://localhost:3000/api/support")
    parser.add_argument("--judge", default="databricks")
    parser.add_argument("--limit", type=int, default=None, help="Only the first N cases (pilot)")
    parser.add_argument("--only", default=None, help="Comma-separated case ids")
    parser.add_argument("--workers", default="2", help="Parallel predictions (rate limits)")
    parser.add_argument("--label", default=None, help="Results file label (default: the target)")
    parser.add_argument("--table", action="store_true", help="Only write evals/RESULTS.md")
    args = parser.parse_args(argv)
    if args.table:
        print(write_results_md())
        return

    import mlflow
    from databricks.sdk import WorkspaceClient

    os.environ.setdefault("MLFLOW_GENAI_EVAL_MAX_WORKERS", args.workers)
    mlflow.set_tracking_uri("databricks")
    me = WorkspaceClient().current_user.me().user_name
    mlflow.set_experiment(f"/Users/{me}/coati-agent-evals")

    cases = load_cases()
    if args.only:
        wanted = set(args.only.split(","))
        cases = [c for c in cases if c["expectations"]["id"] in wanted]
    if args.limit:
        cases = cases[: args.limit]

    recorder = Recorder()
    if args.target == "baseline":
        predict, label = baseline_target(args.baseline_url, recorder), "baseline-coati"
    else:
        predict, label = local_target(args.model, recorder), args.model.removeprefix("databricks-")
    label = args.label or label
    if args.limit or args.only:
        label += "-pilot"

    scorers = make_scorers(args.judge)
    results: dict[str, Any] = {}
    with mlflow.start_run(run_name=f"eval {label}") as parent:
        mlflow.log_params({"target": args.target, "model": args.model, "judge": args.judge})
        for group, rows in groups(cases).items():
            group_scorers = scorers[group]
            if args.target == "baseline":  # no tools and no trace spans to read
                group_scorers = [
                    s
                    for s in group_scorers
                    if getattr(s, "name", "")
                    not in ("expected_page_retrieved", "retrieval_groundedness")
                ]
            with mlflow.start_run(run_name=f"{label} {group}", nested=True):
                results[group] = mlflow.genai.evaluate(
                    data=rows, predict_fn=predict, scorers=group_scorers
                )

    summary = summarise(label, args.judge, results, recorder, parent.info.run_id, cases)
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{summary['date']}-{label}.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{out}")
    for name, t in summary["scores"].items():
        print(
            f"  {name:28} {t['pass']}/{t['pass'] + t['fail']}"
            f"  errors {t['error']}  skipped {t['skipped']}"
        )
    print(f"  latency p50 {summary['latency_ms']['p50']} ms, tokens {summary['tokens_per_turn']}")


if __name__ == "__main__":
    main()
