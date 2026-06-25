from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_config


CELEBA_ATTRIBUTES = [
    "5_o_Clock_Shadow",
    "Arched_Eyebrows",
    "Attractive",
    "Bags_Under_Eyes",
    "Bald",
    "Bangs",
    "Big_Lips",
    "Big_Nose",
    "Black_Hair",
    "Blond_Hair",
    "Blurry",
    "Brown_Hair",
    "Bushy_Eyebrows",
    "Chubby",
    "Double_Chin",
    "Eyeglasses",
    "Goatee",
    "Gray_Hair",
    "Heavy_Makeup",
    "High_Cheekbones",
    "Male",
    "Mouth_Slightly_Open",
    "Mustache",
    "Narrow_Eyes",
    "No_Beard",
    "Oval_Face",
    "Pale_Skin",
    "Pointy_Nose",
    "Receding_Hairline",
    "Rosy_Cheeks",
    "Sideburns",
    "Smiling",
    "Straight_Hair",
    "Wavy_Hair",
    "Wearing_Earrings",
    "Wearing_Hat",
    "Wearing_Lipstick",
    "Wearing_Necklace",
    "Wearing_Necktie",
    "Young",
]


def read_celeba_attributes(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    """Read the official list_attr_celeba.txt file into a binary dataframe."""
    if not path.exists():
        raise FileNotFoundError(f"Raw CelebA attributes file was not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        total_line = file.readline().strip()
        header = file.readline().strip().split()

    if not total_line.isdigit():
        raise ValueError("Unexpected CelebA attribute file format: first line must be row count")

    dataframe = pd.read_csv(
        path,
        sep=r"\s+",
        skiprows=2,
        names=["image_id", *header],
        nrows=max_rows,
    )
    for column in header:
        dataframe[column] = dataframe[column].map({-1: 0, 1: 1}).astype("int8")
    return dataframe


def build_demo_dataset(rows: int, random_state: int) -> pd.DataFrame:
    """Create a small deterministic CelebA-like table for CI without the full dataset."""
    rng = np.random.default_rng(random_state)
    data: dict[str, np.ndarray | list[str]] = {
        "image_id": [f"demo_{index:06d}.jpg" for index in range(rows)]
    }

    for attribute in CELEBA_ATTRIBUTES:
        if attribute == "Smiling":
            continue
        probability = 0.5
        if attribute in {"Young", "Attractive", "High_Cheekbones", "Mouth_Slightly_Open"}:
            probability = 0.58
        elif attribute in {"Bald", "Mustache", "Goatee", "Wearing_Hat"}:
            probability = 0.18
        data[attribute] = rng.binomial(1, probability, rows).astype("int8")

    score = (
        2.4 * data["Mouth_Slightly_Open"]
        + 1.6 * data["High_Cheekbones"]
        + 0.8 * data["Young"]
        + 0.7 * data["Attractive"]
        - 1.0 * data["Bags_Under_Eyes"]
        - 0.8 * data["Mustache"]
        + rng.normal(0, 0.9, rows)
    )
    data["Smiling"] = (score > 1.9).astype("int8")
    return pd.DataFrame(data, columns=["image_id", *CELEBA_ATTRIBUTES])


def prepare_dataset(
    raw_path: Path,
    output_path: Path,
    target_attribute: str,
    max_rows: int | None,
    random_state: int,
    demo_if_missing: bool,
) -> pd.DataFrame:
    if raw_path.exists():
        dataframe = read_celeba_attributes(raw_path, max_rows=max_rows)
        source = "celeba"
    elif demo_if_missing:
        rows = max_rows or 1000
        dataframe = build_demo_dataset(rows=rows, random_state=random_state)
        source = "demo"
    else:
        raise FileNotFoundError(
            f"{raw_path} does not exist. Download list_attr_celeba.txt or enable demo_if_missing."
        )

    if target_attribute not in dataframe.columns:
        raise ValueError(f"Target attribute '{target_attribute}' is absent from the dataset")

    dataframe = dataframe.dropna().drop_duplicates(subset=["image_id"]).reset_index(drop=True)
    dataframe["dataset_source"] = source

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return dataframe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare CelebA attributes for model training.")
    parser.add_argument("--config", default="config.ini", help="Path to config.ini")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    dataframe = prepare_dataset(
        raw_path=config.paths.raw_attributes,
        output_path=config.paths.processed_dataset,
        target_attribute=config.data.target_attribute,
        max_rows=config.data.max_rows,
        random_state=config.data.random_state,
        demo_if_missing=config.data.demo_if_missing,
    )
    print(
        f"Prepared {len(dataframe)} rows with target '{config.data.target_attribute}' "
        f"at {config.paths.processed_dataset}"
    )


if __name__ == "__main__":
    main()
