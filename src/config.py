from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathConfig:
    raw_attributes: Path
    processed_dataset: Path
    model_path: Path
    metrics_path: Path


@dataclass(frozen=True)
class DataConfig:
    target_attribute: str
    test_size: float
    random_state: int
    max_rows: int | None
    demo_if_missing: bool


@dataclass(frozen=True)
class ModelConfig:
    algorithm: str
    c: float
    max_iter: int
    class_weight: str | None
    solver: str


@dataclass(frozen=True)
class QualityConfig:
    min_accuracy: float
    min_f1: float


@dataclass(frozen=True)
class AppConfig:
    paths: PathConfig
    data: DataConfig
    model: ModelConfig
    quality: QualityConfig


def _optional_int(value: str) -> int | None:
    value = value.strip()
    if value.lower() in {"", "none", "null"}:
        return None
    return int(value)


def _optional_str(value: str) -> str | None:
    value = value.strip()
    if value.lower() in {"", "none", "null"}:
        return None
    return value


def load_config(path: str | Path = "config.ini") -> AppConfig:
    config_path = Path(path)
    parser = ConfigParser()
    read_files = parser.read(config_path)
    if not read_files:
        raise FileNotFoundError(f"Config file was not found: {config_path}")

    paths = PathConfig(
        raw_attributes=Path(parser["paths"]["raw_attributes"]),
        processed_dataset=Path(parser["paths"]["processed_dataset"]),
        model_path=Path(parser["paths"]["model_path"]),
        metrics_path=Path(parser["paths"]["metrics_path"]),
    )
    data = DataConfig(
        target_attribute=parser["data"]["target_attribute"],
        test_size=parser.getfloat("data", "test_size"),
        random_state=parser.getint("data", "random_state"),
        max_rows=_optional_int(parser["data"].get("max_rows", "")),
        demo_if_missing=parser.getboolean("data", "demo_if_missing", fallback=False),
    )
    model = ModelConfig(
        algorithm=parser["model"]["algorithm"],
        c=parser.getfloat("model", "C"),
        max_iter=parser.getint("model", "max_iter"),
        class_weight=_optional_str(parser["model"].get("class_weight", "")),
        solver=parser["model"].get("solver", "liblinear"),
    )
    quality = QualityConfig(
        min_accuracy=parser.getfloat("quality", "min_accuracy"),
        min_f1=parser.getfloat("quality", "min_f1"),
    )
    return AppConfig(paths=paths, data=data, model=model, quality=quality)
