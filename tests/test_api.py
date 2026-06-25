from pathlib import Path

from fastapi.testclient import TestClient

from src.api import main as api_main
from src.config import load_config
from src.data.prepare import prepare_dataset
from src.models.train import train_model
from tests.test_train_evaluate import write_test_config


def test_api_model_and_prediction(tmp_path: Path, monkeypatch) -> None:
    config = load_config(write_test_config(tmp_path))
    prepare_dataset(
        raw_path=config.paths.raw_attributes,
        output_path=config.paths.processed_dataset,
        target_attribute=config.data.target_attribute,
        max_rows=config.data.max_rows,
        random_state=config.data.random_state,
        demo_if_missing=config.data.demo_if_missing,
    )
    train_model(config)

    monkeypatch.setenv("MODEL_PATH", str(config.paths.model_path))
    api_main.load_model_bundle.cache_clear()
    client = TestClient(api_main.app)

    health_response = client.get("/health")
    model_response = client.get("/model")
    predict_response = client.post(
        "/predict",
        json={
            "features": {
                "Mouth_Slightly_Open": 1,
                "High_Cheekbones": 1,
                "Young": 1,
                "Attractive": 1,
            }
        },
    )

    assert health_response.json() == {"status": "ok"}
    assert model_response.status_code == 200
    assert model_response.json()["target_attribute"] == "Smiling"
    assert predict_response.status_code == 200
    assert "probability" in predict_response.json()
