from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
from sklearn.model_selection import train_test_split

from src.config import AppConfig, load_config
from src.models.train import calculate_metrics, load_training_frame


def evaluate_model(config: AppConfig) -> dict[str, Any]:
    if not config.paths.model_path.exists():
        raise FileNotFoundError(f"Model artifact does not exist: {config.paths.model_path}")

    bundle = joblib.load(config.paths.model_path)
    model = bundle["model"]
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
    del x_train, y_train

    metrics = calculate_metrics(model, x_test, y_test)
    result: dict[str, Any] = {
        "target_attribute": config.data.target_attribute,
        "algorithm": bundle["algorithm"],
        "rows": int(len(features)),
        "features": feature_columns,
        "feature_count": len(feature_columns),
        "metrics": metrics,
        "thresholds": {
            "min_accuracy": config.quality.min_accuracy,
            "min_f1": config.quality.min_f1,
        },
        "passed": bool(
            metrics["accuracy"] >= config.quality.min_accuracy
            and metrics["f1"] >= config.quality.min_f1
        ),
    }

    config.paths.metrics_path.parent.mkdir(parents=True, exist_ok=True)
    config.paths.metrics_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if not result["passed"]:
        raise RuntimeError(
            "Model quality gate failed: "
            f"accuracy={metrics['accuracy']} f1={metrics['f1']} "
            f"thresholds={result['thresholds']}"
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate trained CelebA attribute model.")
    parser.add_argument("--config", default="config.ini", help="Path to config.ini")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    result = evaluate_model(config)
    print(f"Saved metrics to {config.paths.metrics_path}")
    print(result["metrics"])


if __name__ == "__main__":
    main()
