"""The simulated week (Task 18): one eval question per run to the served endpoint.

The public page stays closed until a measured month fits the budget, so the
traffic is simulated: a scheduled job asks one question from the eval set an
hour, at real intervals, so the endpoint idles down and wakes up as it would
for visitors. Each request becomes one line in the artifacts volume
(`traffic/<date>.jsonl`): the question's id, the time, the tries, the tokens
and the status, never any text. After seven days the token totals are set
against Databricks' billing for the endpoint.

    DATABRICKS_CONFIG_PROFILE=coati-paid uv run coati-traffic --endpoint coati-agent
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

# The eval set: inside the wheel on Databricks, in evals/ in a checkout.
_PACKAGED = Path(__file__).resolve().parent / "data" / "questions.jsonl"
QUESTIONS = (
    _PACKAGED
    if _PACKAGED.exists()
    else Path(__file__).resolve().parents[2] / "evals" / "questions.jsonl"
)

# A cold endpoint took 2 min 40 s to answer on 2026-11-10; leave room.
WAIT_S = 360
EVERY_S = 20
# The HTTP statuses, and SDK errors, that mean "still scaling up".
WAKING_STATUSES = {503, 504}
WAKING_ERRORS = {"TemporarilyUnavailable", "DeadlineExceeded", "Timeout", "ReadTimeout"}


def pick(questions: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    """One question, the same for the same run, spread across runs."""
    digest = hashlib.sha256(run_id.encode("utf-8")).digest()
    return questions[int.from_bytes(digest[:8], "big") % len(questions)]


def _waking(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    return status in WAKING_STATUSES or type(error).__name__ in WAKING_ERRORS


def ask(
    api: Any,
    endpoint: str,
    question: str,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    wait_s: float = WAIT_S,
    every_s: float = EVERY_S,
) -> dict[str, Any]:
    """Ask once, asking again while the endpoint scales up from zero."""
    started = clock()
    tries = 0
    body = {"input": [{"role": "user", "content": question}]}
    while True:
        tries += 1
        try:
            reply = api.do("POST", f"/serving-endpoints/{endpoint}/invocations", body=body)
        except Exception as error:  # the SDK's errors, timeouts
            if _waking(error) and clock() - started + every_s < wait_s:
                sleep(every_s)
                continue
            status = "gave_up" if _waking(error) else "error"
            return _result(status, tries, clock() - started, error=str(error)[:200])
        custom = reply.get("custom_outputs") or {}
        usage = custom.get("usage") or {}
        return _result(
            custom.get("status") or "unknown",
            tries,
            clock() - started,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            steps=[s.get("name") for s in custom.get("steps") or [] if isinstance(s, dict)],
        )


def _result(status: str, tries: int, seconds: float, **fields: Any) -> dict[str, Any]:
    base = {"status": status, "tries": tries, "ms": round(seconds * 1000)}
    return {"input_tokens": 0, "output_tokens": 0, **base, **fields}


def record_for(question: dict[str, Any], result: dict[str, Any], at: str) -> dict[str, Any]:
    """The line kept for one request: the question's id, never its text."""
    return {"at": at, "id": question["id"], **result}


def merge_lines(existing: str, record: dict[str, Any]) -> str:
    return existing + json.dumps(record) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the served agent one eval question.")
    parser.add_argument("--endpoint", default="coati-agent")
    parser.add_argument("--volume-dir", default="/Volumes/workspace/coati_agent/artifacts")
    args = parser.parse_args()

    from databricks.sdk import WorkspaceClient
    from databricks.sdk.core import Config

    questions = [
        json.loads(line)
        for line in QUESTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    now = datetime.datetime.now(datetime.UTC)
    at = now.isoformat(timespec="seconds")
    question = pick(questions, at)

    # A request waits up to two minutes before the SDK gives up on it, and the
    # SDK doesn't retry on its own: ask() does, and counts the tries. Through
    # Config, which older SDKs (the serverless environment's) accept too.
    w = WorkspaceClient(config=Config(http_timeout_seconds=120, retry_timeout_seconds=0))
    record = record_for(question, ask(w.api_client, args.endpoint, question["question"]), at)

    path = f"{args.volume_dir}/traffic/{now.date().isoformat()}.jsonl"
    try:
        with w.files.download(path).contents as stream:
            existing = stream.read().decode("utf-8")
    except Exception:  # the day's first run
        existing = ""
    w.files.upload(path, io.BytesIO(merge_lines(existing, record).encode("utf-8")), overwrite=True)
    print(json.dumps(record))


if __name__ == "__main__":
    main()
