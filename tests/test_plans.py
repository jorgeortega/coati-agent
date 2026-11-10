"""get_plans: the SQL that builds the table and function, and the tool (no network)."""

import json

import pytest

from coati_agent.plans import GET_PLANS_SPEC, get_plans_tool, parse_result, render_sql
from coati_agent.tools import Citation

FUNCTION = "workspace.coati_agent.get_plans"


def test_the_sql_builds_the_table_from_the_volume_and_a_function_over_it():
    statements = render_sql(
        "workspace", "coati_agent", "/Volumes/workspace/coati_agent/artifacts/plans"
    )

    assert len(statements) == 2
    table, function = statements
    assert table.startswith("CREATE OR REPLACE TABLE workspace.coati_agent.plans")
    assert "read_files('/Volumes/workspace/coati_agent/artifacts/plans/plans.jsonl'" in table
    assert function.startswith("CREATE OR REPLACE FUNCTION workspace.coati_agent.get_plans")
    assert "FROM workspace.coati_agent.plans" in function


@pytest.mark.parametrize("catalog", ["work space", "x;DROP TABLE y", "a.b", ""])
def test_refuses_names_that_are_not_plain_identifiers(catalog):
    with pytest.raises(ValueError):
        render_sql(catalog, "coati_agent", "/Volumes/a/b/c")


def test_parses_a_statement_result_into_rows_with_arrays():
    result = {
        "manifest": {
            "schema": {
                "columns": [
                    {"name": "id", "type_name": "STRING"},
                    {"name": "seats", "type_name": "INT"},
                    {"name": "included", "type_name": "ARRAY"},
                    {"name": "price", "type_name": "STRING"},
                ]
            }
        },
        "result": {"data_array": [["pro", "5", '["SSO","Audit log"]', None]]},
    }

    assert parse_result(result) == [
        {"id": "pro", "seats": 5, "included": ["SSO", "Audit log"], "price": None}
    ]


def fake_sql(rows):
    calls = []

    def run(statement, parameters):
        calls.append((statement, parameters))
        return rows

    return run, calls


def test_the_tool_calls_the_function_with_the_plan_as_a_parameter():
    run, calls = fake_sql([{"id": "pro", "name": "Pro", "price": "$150 a month", "builds": None}])
    tool = get_plans_tool(run, FUNCTION)

    result = tool(plan="Pro")

    assert calls == [(f"SELECT * FROM {FUNCTION}(:plan)", {"plan": "Pro"})]
    assert json.loads(result.content) == [{"id": "pro", "name": "Pro", "price": "$150 a month"}]
    assert result.citations == [Citation("Pricing", "https://latitude10.tech/pricing")]


def test_a_plan_that_builds_on_another_says_it_includes_everything_in_it():
    run, _ = fake_sql([{"id": "business", "name": "Business", "builds": "Pro"}])
    result = get_plans_tool(run, FUNCTION)(plan="Business")

    assert json.loads(result.content) == [
        {"id": "business", "name": "Business", "includes_everything_in": "Pro"}
    ]


def test_the_spec_sends_other_limits_and_how_features_work_to_search_docs():
    description = GET_PLANS_SPEC["function"]["description"]
    assert "includes_everything_in" in description
    assert "search_docs" in description
    assert "custom domains" in description


def test_without_a_plan_the_tool_asks_for_all_of_them():
    run, calls = fake_sql([])
    get_plans_tool(run, FUNCTION)()

    assert calls[0][1] == {"plan": None}


def test_says_so_when_no_plan_matches():
    run, _ = fake_sql([])
    result = get_plans_tool(run, FUNCTION)(plan="Platinum")

    assert "No plan" in result.content
    assert result.citations == []


def test_the_spec_names_the_tool_and_its_optional_argument():
    function = GET_PLANS_SPEC["function"]
    assert function["name"] == "get_plans"
    assert function["parameters"].get("required", []) == []


def test_a_statement_with_no_columns_has_no_rows():
    assert parse_result({"manifest": {"schema": {}}, "status": {"state": "SUCCEEDED"}}) == []
    assert parse_result({"status": {"state": "SUCCEEDED"}}) == []
