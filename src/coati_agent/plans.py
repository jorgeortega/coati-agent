"""get_plans: Latitude 10's plans in a Unity Catalog table, read through a SQL function.

The site exports `plans.jsonl` from `plans.ts` (prices only for launched
plans). `coati-plans` copies it into the artifacts volume and runs
`sql/get_plans.sql`, which builds the table and the function. The agent's
tool calls the function on a SQL warehouse with the model's argument as a
parameter, never pasted into the SQL.

    DATABRICKS_CONFIG_PROFILE=coati-free uv run coati-plans --warehouse-id <id>
"""

from __future__ import annotations

import argparse
import io
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .prompt import DATA_DIR, load_export
from .tools import Citation, ServerTool, ToolResult

SQL = Path(__file__).resolve().parent / "sql" / "get_plans.sql"
PRICING = Citation("Pricing", "https://latitude10.tech/pricing")
IDENTIFIER = re.compile(r"[A-Za-z0-9_]+")
VOLUME_DIR = re.compile(r"/Volumes(/[A-Za-z0-9_]+){3}(/[A-Za-z0-9_.-]+)*")

GET_PLANS_SPEC = {
    "type": "function",
    "function": {
        "name": "get_plans",
        "description": (
            "Latitude 10's plans (Free, Pro, Business, Enterprise): monthly and annual "
            "price, the APIs, seats and SDK endpoints each allows, and the features each "
            "adds. A plan with includes_everything_in also has every feature of that plan. "
            "Use it for a plan's price or those three limits. For any other limit (custom "
            "domains, versions, requests, storage) or how a feature works, call search_docs "
            "instead. A plan with no price has none published: never guess one."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "plan": {
                    "type": "string",
                    "description": "One plan's id or name. Leave it out for every plan.",
                }
            },
        },
    },
}

# v4 read Business's `builds: "Pro"` as "has none of Pro's features" (eval d08).
RENAMED = {"builds": "includes_everything_in"}

# What a warehouse query returns: one dict per row.
RunSql = Callable[[str, dict[str, str | None]], list[dict[str, Any]]]


def render_sql(catalog: str, schema: str, volume_dir: str) -> list[str]:
    for name in (catalog, schema):
        if not IDENTIFIER.fullmatch(name):
            raise ValueError(f"not a plain identifier: {name!r}")
    if not VOLUME_DIR.fullmatch(volume_dir):
        raise ValueError(f"not a volume path: {volume_dir!r}")
    text = SQL.read_text(encoding="utf-8")
    body = "\n".join(line for line in text.splitlines() if not line.startswith("--"))
    body = body.format(catalog=catalog, schema=schema, volume_dir=volume_dir)
    return [s.strip() for s in body.split(";\n") if s.strip().rstrip(";")]


_INTS = {"INT", "LONG", "SHORT", "BYTE"}


def _value(raw: str | None, type_name: str) -> Any:
    if raw is None:
        return None
    if type_name in _INTS:
        return int(raw)
    if type_name == "BOOLEAN":
        return raw == "true"
    if type_name in ("ARRAY", "MAP", "STRUCT"):
        return json.loads(raw)
    return raw


def parse_result(response: dict[str, Any]) -> list[dict[str, Any]]:
    """A Statement Execution API response (JSON_ARRAY format) as a list of rows."""
    columns = ((response.get("manifest") or {}).get("schema") or {}).get("columns") or []
    rows = (response.get("result") or {}).get("data_array") or []
    return [
        {c["name"]: _value(v, c["type_name"]) for c, v in zip(columns, row, strict=True)}
        for row in rows
    ]


def get_plans_tool(run_sql: RunSql, function: str) -> ServerTool:
    statement = f"SELECT * FROM {function}(:plan)"

    def get_plans(plan: str | None = None) -> ToolResult:
        rows = run_sql(statement, {"plan": plan})
        if not rows:
            return ToolResult(
                f"No plan is called {plan!r}. The plans are Free, Pro, Business and Enterprise."
            )
        compact = [
            {RENAMED.get(k, k): v for k, v in row.items() if v not in (None, [])} for row in rows
        ]
        return ToolResult(json.dumps(compact, ensure_ascii=False), [PRICING])

    return get_plans


def warehouse_sql(workspace: Any, warehouse_id: str, wait: str = "30s") -> RunSql:
    """Run a statement on a SQL warehouse and wait for its rows (cancel after `wait`)."""
    from databricks.sdk.service.sql import (
        ExecuteStatementRequestOnWaitTimeout,
        StatementParameterListItem,
        StatementState,
    )

    def run(statement: str, parameters: dict[str, str | None]) -> list[dict[str, Any]]:
        response = workspace.statement_execution.execute_statement(
            statement=statement,
            warehouse_id=warehouse_id,
            parameters=[
                StatementParameterListItem(name=k, value=v, type="STRING")
                for k, v in parameters.items()
            ],
            wait_timeout=wait,
            on_wait_timeout=ExecuteStatementRequestOnWaitTimeout.CANCEL,
        )
        if response.status.state != StatementState.SUCCEEDED:
            error = response.status.error.message if response.status.error else ""
            raise RuntimeError(f"statement {response.status.state.value}: {error}")
        return parse_result(response.as_dict())

    return run


def main() -> None:
    parser = argparse.ArgumentParser(description="Load plans.jsonl and create get_plans.")
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="dev_jorgeortega_coati_agent")
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--volume-dir", default=None, help="Default: <artifacts volume>/plans")
    args = parser.parse_args()

    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    volume_dir = args.volume_dir or f"/Volumes/{args.catalog}/{args.schema}/artifacts/plans"
    statements = render_sql(args.catalog, args.schema, volume_dir)
    plans = load_export(DATA_DIR)["plans.jsonl"]  # hash-checked against the manifest
    w.files.upload(f"{volume_dir}/plans.jsonl", io.BytesIO(plans.encode("utf-8")), overwrite=True)
    run = warehouse_sql(w, args.warehouse_id, wait="50s")
    for statement in statements:
        run(statement, {})
    rows = run(f"SELECT * FROM {args.catalog}.{args.schema}.get_plans(:plan)", {"plan": None})
    print(f"get_plans returns {len(rows)} plans: {', '.join(r['name'] for r in rows)}")


if __name__ == "__main__":
    main()
