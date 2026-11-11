"""prune_traces: delete the served agent's traces after 30 days.

The serving endpoint logs every turn to an MLflow experiment, question and
answer included (spec D3). Latitude 10's privacy policy says they are deleted
after 30 days, so a daily job deletes every trace older than that.

    DATABRICKS_CONFIG_PROFILE=coati-paid uv run coati-prune --experiment-id <id>
"""

from __future__ import annotations

import argparse
import datetime
from typing import Any

# The privacy policy's number (app/legal/_content/privacy.tsx, "The Agent Lab").
KEEP_DAYS = 30
BATCH = 1000


def cutoff_ms(now: datetime.datetime, days: int = KEEP_DAYS) -> int:
    """Traces older than this, in milliseconds since the epoch, are deleted."""
    if days < 1:
        raise ValueError("keep traces at least a day")
    return int((now - datetime.timedelta(days=days)).timestamp() * 1000)


def prune(
    client: Any,
    experiment_id: str,
    now: datetime.datetime,
    days: int = KEEP_DAYS,
    max_rounds: int = 1000,
) -> int:
    """Delete in batches until nothing older than the cutoff is left."""
    cutoff = cutoff_ms(now, days)
    total = 0
    for _ in range(max_rounds):
        deleted = client.delete_traces(experiment_id, max_timestamp_millis=cutoff, max_traces=BATCH)
        total += deleted
        # A store may delete fewer than asked per call: stop only at zero.
        if deleted == 0:
            return total
    raise RuntimeError(f"still deleting after {max_rounds} batches: check the experiment")


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete agent traces older than 30 days.")
    parser.add_argument("--experiment-id", required=True)
    args = parser.parse_args()

    import mlflow
    from mlflow import MlflowClient

    mlflow.set_tracking_uri("databricks")
    now = datetime.datetime.now(datetime.UTC)
    deleted = prune(MlflowClient(), args.experiment_id, now)
    print(f"Deleted {deleted} traces older than {KEEP_DAYS} days", f"({args.experiment_id}).")


if __name__ == "__main__":
    main()
