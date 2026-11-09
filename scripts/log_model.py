"""Log the agent to MLflow on Databricks and register it in Unity Catalog.

    DATABRICKS_CONFIG_PROFILE=coati-free uv run python scripts/log_model.py

The index is the one the embed_docs job built in the artifacts volume. Logging
runs one prediction locally against the workspace (the input example), so a
broken model fails here, not on the endpoint.
"""

from __future__ import annotations

import argparse
import tempfile
from importlib.metadata import version
from pathlib import Path

import mlflow
from databricks.sdk import WorkspaceClient
from mlflow.models.resources import DatabricksServingEndpoint

from coati_agent.serve import DEFAULT_CONFIG

ROOT = Path(__file__).resolve().parents[1]
PINNED = ["mlflow", "databricks-sdk", "openai", "numpy", "httpx"]


def download_index(w: WorkspaceClient, volume_dir: str, to: Path) -> Path:
    to.mkdir(parents=True, exist_ok=True)
    for name in ("chunks.jsonl", "meta.json", "vectors.npy"):
        with w.files.download(f"{volume_dir}/{name}").contents as stream:
            (to / name).write_bytes(stream.read())
    return to


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="workspace")
    parser.add_argument("--schema", default="dev_jorgeortega_coati_agent")
    parser.add_argument("--llm", default=DEFAULT_CONFIG["llm_endpoint"])
    parser.add_argument("--experiment", default=None)
    args = parser.parse_args()

    w = WorkspaceClient()
    me = w.current_user.me().user_name
    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(args.experiment or f"/Users/{me}/coati-agent")

    volume_dir = f"/Volumes/{args.catalog}/{args.schema}/artifacts/index"
    config = {**DEFAULT_CONFIG, "llm_endpoint": args.llm}
    model_name = f"{args.catalog}.{args.schema}.coati_agent"

    with tempfile.TemporaryDirectory() as tmp, mlflow.start_run(run_name="log coati_agent"):
        index_dir = download_index(w, volume_dir, Path(tmp) / "index")
        info = mlflow.pyfunc.log_model(
            name="agent",
            python_model=str(ROOT / "src/coati_agent/model_entry.py"),
            code_paths=[str(ROOT / "src/coati_agent")],
            artifacts={"index": str(index_dir), "data": str(ROOT / "data")},
            model_config=config,
            resources=[
                DatabricksServingEndpoint(endpoint_name=config["llm_endpoint"]),
                DatabricksServingEndpoint(endpoint_name=config["embedding_endpoint"]),
            ],
            pip_requirements=[f"{p}=={version(p)}" for p in PINNED],
            input_example={"input": [{"role": "user", "content": "Which plan includes SSO?"}]},
            registered_model_name=model_name,
        )
    print(f"logged {info.model_uri}")
    print(f"registered {model_name} version {info.registered_model_version}")


if __name__ == "__main__":
    main()
