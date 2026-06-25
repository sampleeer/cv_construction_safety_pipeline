from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import AppConfig, load_config


EXCLUDED_COLUMNS = {"image_id", "dataset_source"}


def load_training_frame(path: Path, target_attribute: str) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Prepared dataset does not exist: {path}")
    dataframe = pd.read_csv(path)
    if target_attribute not in dataframe.columns:
        raise ValueError(f"Target attribute '{target_attribute}' is absent from {path}")

    feature_columns = [
        column for column in dataframe.columns if column not in EXCLUDED_COLUMNS | {target_attribute}
    ]
    features = dataframe[feature_columns].astype(float)
    target = dataframe[target_attribute].astype(int)
    return features, target, feature_columns


def make_model(config: AppConfig) -> Pipeline:
    if config.model.algorithm != "logistic_regression":
        raise ValueError(f"Unsupported algorithm: {config.model.algorithm}")

    classifier = LogisticRegression(
        C=config.model.c,
        max_iter=config.model.max_iter,
        class_weight=config.model.class_weight,
        solver=config.model.solver,
        random_state=config.data.random_state,
    )
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("classifier", classifier),
        ]
    )


def calculate_metrics(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float]:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "f1": round(float(f1_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
    }


def train_model(config: AppConfig) -> dict[str, Any]:
    features, target, feature_columns = load_training_frame(
        config.paths.processed_dataset,
        config.data.target_attribute,
    )
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=config.data.test_size,
        random_state=config.data.random_state,
        stratify=target,
    )

    model = make_model(config)
    model.fit(x_train, y_train)
    metrics = calculate_metrics(model, x_test, y_test)

    bundle: dict[str, Any] = {
        "model": model,
        "target_attribute": config.data.target_attribute,
        "feature_columns": feature_columns,
        "metrics": metrics,
        "algorithm": config.model.algorithm,
        "random_state": config.data.random_state,
    }
    config.paths.model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, config.paths.model_path)
    return bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train CelebA attribute model.")
    parser.add_argument("--config", default="config.ini", help="Path to config.ini")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    bundle = train_model(config)
    print(f"Saved {bundle['algorithm']} model to {config.paths.model_path}")
    print(f"Training holdout metrics: {bundle['metrics']}")


if __name__ == "__main__":
    main()
