import os

import mlflow
import pytest

# Write traces synchronously, so a test can read the trace it just made.
os.environ["MLFLOW_ENABLE_ASYNC_TRACE_LOGGING"] = "false"


@pytest.fixture(autouse=True, scope="session")
def local_mlflow(tmp_path_factory):
    """Traces from tests go to a throwaway store, never the repo or a workspace."""
    store = tmp_path_factory.mktemp("mlflow") / "mlflow.db"
    mlflow.set_tracking_uri(f"sqlite:///{store}")
    yield
