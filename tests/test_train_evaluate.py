from configparser import ConfigParser
from pathlib import Path

from src.config import load_config
from src.data.prepare import prepare_dataset
from src.models.evaluate import evaluate_model
from src.models.train import train_model


def write_test_config(tmp_path: Path) -> Path:
    config = ConfigParser()
    config["paths"] = {
        "raw_attributes": str(tmp_path / "missing.txt"),
        "processed_dataset": str(tmp_path / "processed.csv"),
        "model_path": str(tmp_path / "model.joblib"),
        "metrics_path": str(tmp_path / "metrics.json"),
    }
    config["data"] = {
        "target_attribute": "Smiling",
        "test_size": "0.2",
        "random_state": "42",
        "max_rows": "400",
        "demo_if_missing": "true",
    }
    config["model"] = {
        "algorithm": "logistic_regression",
        "C": "1.0",
        "max_iter": "1000",
        "class_weight": "balanced",
        "solver": "liblinear",
    }
    config["quality"] = {
        "min_accuracy": "0.60",
        "min_f1": "0.60",
    }

    config_path = tmp_path / "config.ini"
    with config_path.open("w", encoding="utf-8") as file:
        config.write(file)
    return config_path


def test_train_and_evaluate_pipeline(tmp_path: Path) -> None:
    config = load_config(write_test_config(tmp_path))
    prepare_dataset(
        raw_path=config.paths.raw_attributes,
        output_path=config.paths.processed_dataset,
        target_attribute=config.data.target_attribute,
        max_rows=config.data.max_rows,
        random_state=config.data.random_state,
        demo_if_missing=config.data.demo_if_missing,
    )

    bundle = train_model(config)
    result = evaluate_model(config)

    assert config.paths.model_path.exists()
    assert config.paths.metrics_path.exists()
    assert bundle["target_attribute"] == "Smiling"
    assert result["passed"] is True
    assert result["metrics"]["accuracy"] >= 0.60
