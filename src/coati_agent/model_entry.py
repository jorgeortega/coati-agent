"""Models-from-code entry point: MLflow loads this file to build the served model."""

import mlflow

from coati_agent.serve import CoatiAgent

mlflow.models.set_model(CoatiAgent())
