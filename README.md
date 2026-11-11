# coati-agent

The support agent of [Latitude 10](https://latitude10.tech), rebuilt on
Databricks as a small, readable harness: a tool-calling loop, retrieval over
the docs, MLflow tracing, an eval set, and a serving endpoint. It powers the
Agent Lab page, where you can talk to it and watch each turn's trace.

Status: built and served; the page goes public once a measured month fits
the budget. The plan lives in the Latitude 10 repo
(`docs/superpowers/specs/2026-11-09-databricks-agent.md`).

## Why it's built this way

- **No framework.** The loop is a few dozen lines, so you can read the whole
  thing.
- **No Vector Search.** A Vector Search endpoint can't scale to zero (one unit
  minimum, about $200 a month). The docs are under a hundred chunks, so the
  index ships inside the agent and search is a cosine scan in memory.
- **The model is a setting.** The eval set picks it, not taste.

## Develop

Needs Python 3.12+, [uv](https://docs.astral.sh/uv/) and the Databricks CLI.

```
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
databricks auth login --host <workspace-url> --profile coati-free
databricks bundle validate -t dev
```

## Deploy

Two targets in `databricks.yml`, each tied to a CLI profile by name:

| Target | Profile | Workspace | `get_plans` |
|---|---|---|---|
| `dev` | `coati-free` | Free Edition, for building and evals (non-commercial use only) | the Unity Catalog function on a SQL warehouse |
| `prod` | `coati-paid` | pay-as-you-go, for the public page | the `plans.jsonl` shipped in the model |

Log in under those profile names, or change `workspace.profile` in your copy.
`data/` already holds the site's export (rules, summary, docs, plans, with a
manifest of hashes), so there's nothing to fetch first.

The first deploy goes in two passes, because the serving endpoint needs a
registered model and the model needs the schema and the index:

```
# 1. Schema, volume and jobs. The endpoint fails here until a model exists.
databricks bundle deploy -t dev

# 2. The docs index in the artifacts volume (a few cents of embedding calls).
databricks bundle run -t dev embed_docs

# 3. dev only: the plans table and get_plans function, on a SQL warehouse
#    (set warehouse_id in databricks.yml first, or pass --var to step 1).
databricks bundle run -t dev load_plans

# 4. Log and register the model. It runs one real prediction first, so a
#    broken model fails here. It prints the version and the experiment.
DATABRICKS_CONFIG_PROFILE=coati-free uv run python scripts/log_model.py \
    --warehouse-id <warehouse id>                 # dev
DATABRICKS_CONFIG_PROFILE=coati-paid uv run python scripts/log_model.py \
    --schema coati_agent                          # prod: no warehouse

# 5. Serve that version, with traces going to that experiment.
databricks bundle deploy -t dev --var model_version=<n> --var experiment_id=<id>
```

Then ask it something:

```
DATABRICKS_CONFIG_PROFILE=coati-free uv run python scripts/ask.py \
    "Which plan has SSO?" --endpoint dev_<you>_coati-agent
```

In `dev` the bundle prefixes names with `dev_<you>_`; in `prod` the endpoint
is `coati-agent`. A cold endpoint takes a few minutes to scale up from zero.
To serve a new version later, rerun steps 4 and 5 (and 2 after a new export).

## Evaluate

```
DATABRICKS_CONFIG_PROFILE=coati-free uv run python -m coati_agent.evals \
    --model databricks-qwen35-122b-a10b --label <label>
uv run python -m coati_agent.evals --table
```

The first writes `evals/results/<date>-<label>.json` and logs the run to
MLflow; the second regenerates `evals/RESULTS.md`. `evals/README.md` explains
the cases, the judges and every run so far.

## License

MIT
