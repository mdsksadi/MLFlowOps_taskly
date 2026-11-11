"""Promote registered MLflow models using aliases."""

import argparse
import os

from mlflow import MlflowClient

MODEL_NAME = "task-priority-classifier"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=["staging", "production"],
        help="Target alias",
    )
    parser.add_argument(
        "--version",
        help="Model version to assign to staging",
    )
    args = parser.parse_args()

    tracking_uri = os.environ.get(
        "MLFLOW_TRACKING_URI", "http://localhost:5000"
    )
    client = MlflowClient(tracking_uri=tracking_uri)

    if args.stage == "staging":
        if not args.version:
            parser.error("--version is required for staging")

        version = client.get_model_version(
            MODEL_NAME, args.version
        )

        if version.status != "READY":
            raise RuntimeError(
                f"Model version {args.version} is not READY"
            )

        client.set_registered_model_alias(
            MODEL_NAME, "staging", args.version
        )
        print(f"Staging alias -> Version {args.version}")

    elif args.stage == "production":
        staging = client.get_model_version_by_alias(
            MODEL_NAME, "staging"
        )

        if staging.status != "READY":
            raise RuntimeError("Staging model is not READY")

        client.set_registered_model_alias(
            MODEL_NAME, "production", staging.version
        )
        print(f"Production alias -> Version {staging.version}")


if __name__ == "__main__":
    main()
