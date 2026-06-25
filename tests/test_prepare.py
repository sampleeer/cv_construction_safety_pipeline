from pathlib import Path

from src.data.prepare import build_demo_dataset, prepare_dataset, read_celeba_attributes


def test_read_celeba_attributes_parses_official_format(tmp_path: Path) -> None:
    raw_file = tmp_path / "list_attr_celeba.txt"
    raw_file.write_text(
        "\n".join(
            [
                "2",
                "Smiling Young Male",
                "000001.jpg 1 -1 1",
                "000002.jpg -1 1 -1",
            ]
        ),
        encoding="utf-8",
    )

    dataframe = read_celeba_attributes(raw_file)

    assert dataframe.to_dict("records") == [
        {"image_id": "000001.jpg", "Smiling": 1, "Young": 0, "Male": 1},
        {"image_id": "000002.jpg", "Smiling": 0, "Young": 1, "Male": 0},
    ]


def test_prepare_dataset_uses_demo_data_when_raw_file_is_missing(tmp_path: Path) -> None:
    output_file = tmp_path / "processed.csv"

    dataframe = prepare_dataset(
        raw_path=tmp_path / "missing.txt",
        output_path=output_file,
        target_attribute="Smiling",
        max_rows=100,
        random_state=42,
        demo_if_missing=True,
    )

    assert output_file.exists()
    assert len(dataframe) == 100
    assert set(dataframe["dataset_source"]) == {"demo"}
    assert "Smiling" in dataframe.columns


def test_demo_dataset_is_deterministic() -> None:
    first = build_demo_dataset(rows=10, random_state=7)
    second = build_demo_dataset(rows=10, random_state=7)

    assert first.equals(second)
