"""Ask the served agent one question and print the answer, citations and steps.

DATABRICKS_CONFIG_PROFILE=coati-free uv run python scripts/ask.py "Which plan has SSO?"
"""

from __future__ import annotations

import argparse
import json
import time

from databricks.sdk import WorkspaceClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--endpoint", default="dev_jorgeortega_coati-agent")
    args = parser.parse_args()

    w = WorkspaceClient()
    body = {"input": [{"role": "user", "content": args.question}]}
    started = time.perf_counter()
    out = w.api_client.do("POST", f"/serving-endpoints/{args.endpoint}/invocations", body=body)
    seconds = time.perf_counter() - started

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


if __name__ == "__main__":
    main()
