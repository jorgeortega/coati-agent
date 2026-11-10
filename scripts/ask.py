"""Ask the served agent one question and print the answer, citations and steps.

DATABRICKS_CONFIG_PROFILE=coati-free uv run python scripts/ask.py "Which plan has SSO?"

With --readiness, this script plays the site's Worker: when the agent hands
back a check_readiness call, it sends that file as the result and asks again.

uv run python scripts/ask.py "How ready is https://api.example.com/openapi.json?" \\
    --readiness tests/fixtures/readiness-summary.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from databricks.sdk import WorkspaceClient


def invoke(w: WorkspaceClient, endpoint: str, items: list[dict[str, Any]]) -> tuple[dict, float]:
    started = time.perf_counter()
    out = w.api_client.do(
        "POST", f"/serving-endpoints/{endpoint}/invocations", body={"input": items}
    )
    return out, time.perf_counter() - started


def show(out: dict[str, Any], seconds: float) -> None:
    custom = out.get("custom_outputs", {})
    last = out["output"][-1]
    if last["type"] == "message":
        print(last["content"][0]["text"])
    else:
        print(f"[pending {last['name']}({last['arguments']})]")
    print(f"\nstatus: {custom.get('status')}   round trip: {seconds:.1f}s")
    for c in custom.get("citations", []):
        print(f"  cites {c['title']}  {c['url']}")
    for step in custom.get("steps", []):
        print("  step", json.dumps(step))
    print("  usage", json.dumps(custom.get("usage")))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--endpoint", default="dev_jorgeortega_coati-agent")
    parser.add_argument("--readiness", type=Path, help="A readiness summary to send back")
    args = parser.parse_args()

    w = WorkspaceClient()
    items: list[dict[str, Any]] = [{"role": "user", "content": args.question}]
    out, seconds = invoke(w, args.endpoint, items)
    show(out, seconds)

    last = out["output"][-1]
    pending = last["type"] == "function_call" and last["name"] == "check_readiness"
    if pending and args.readiness:
        print("\n--- sending the fixture as the check_readiness result ---\n")
        result = {
            "type": "function_call_output",
            "call_id": last["call_id"],
            "output": args.readiness.read_text(encoding="utf-8"),
        }
        show(*invoke(w, args.endpoint, [*items, *out["output"], result]))


if __name__ == "__main__":
    main()
