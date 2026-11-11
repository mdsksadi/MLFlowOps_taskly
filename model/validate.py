"""Validate the MLflow staging model with a smoke test."""

import os

import mlflow
import mlflow.pyfunc
from mlflow import MlflowClient

MODEL_NAME = "task-priority-classifier"
MODEL_ALIAS = "staging"
VALID_PRIORITIES = {"low", "medium", "high"}


def main():
    tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI", "http://localhost:5000"
    )
    mlflow.set_tracking_uri(tracking_uri)

    client = MlflowClient(tracking_uri=tracking_uri)
    version = client.get_model_version_by_alias(
        MODEL_NAME, MODEL_ALIAS
    )

    model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
    model = mlflow.pyfunc.load_model(model_uri)

    sample = ["Production server outage Server is down"]
    prediction = model.predict(sample)[0]

    print(f"Staging model version: {version.version}")
    print(f"Sample prediction: {prediction}")

    if prediction not in VALID_PRIORITIES:
        raise RuntimeError(
            f"Invalid prediction: {prediction}"
        )

    print("Staging validation PASSED")


if __name__ == "__main__":
    main()
