# coati-agent

The support agent of [Latitude 10](https://latitude10.tech), rebuilt on
Databricks as a small, readable harness: a tool-calling loop, retrieval over
the docs, MLflow tracing, an eval set, and a serving endpoint. It powers the
Agent Lab page, where you can talk to it and watch each turn's trace.

Status: under construction. The plan lives in the Latitude 10 repo
(`docs/superpowers/specs/2026-11-09-databricks-agent.md`).

## Why it's built this way

- **No framework.** The loop is a few dozen lines, so you can read the whole
  thing.
- **No Vector Search.** A Vector Search endpoint can't scale to zero (one unit
  minimum, about $200 a month). The docs are a few hundred chunks, so the
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

## License

MIT
