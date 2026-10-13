from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="CelebA Smiling Classifier",
    version="1.0.0",
    description="Classic ML API for CelebA attribute classification.",
)


class PredictRequest(BaseModel):
    features: dict[str, float | int | bool] = Field(
        ...,
        description="CelebA attribute values. Missing model features are filled with 0.",
    )


class PredictResponse(BaseModel):
    target_attribute: str
    prediction: int
    probability: float
    missing_features: list[str]


@lru_cache(maxsize=1)
def load_model_bundle(model_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(model_path or os.getenv("MODEL_PATH", "models/model.joblib"))
    if not path.exists():
        raise FileNotFoundError(f"Model artifact was not found: {path}")
    return joblib.load(path)


def build_feature_frame(bundle: dict[str, Any], payload: dict[str, float | int | bool]) -> pd.DataFrame:
    feature_columns = bundle["feature_columns"]
    normalized = {feature: int(payload.get(feature, 0)) for feature in feature_columns}
    return pd.DataFrame([normalized], columns=feature_columns)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/model")
def model_info() -> dict[str, Any]:
    try:
        bundle = load_model_bundle()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return {
        "target_attribute": bundle["target_attribute"],
        "algorithm": bundle["algorithm"],
        "feature_count": len(bundle["feature_columns"]),
        "features": bundle["feature_columns"],
        "metrics": bundle.get("metrics", {}),
    }


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    try:
        bundle = load_model_bundle()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    feature_frame = build_feature_frame(bundle, request.features)
    model = bundle["model"]
    probability = float(model.predict_proba(feature_frame)[:, 1][0])
    prediction = int(probability >= 0.5)
    missing_features = [
        feature for feature in bundle["feature_columns"] if feature not in request.features
    ]
    return PredictResponse(
        target_attribute=bundle["target_attribute"],
        prediction=prediction,
        probability=round(probability, 4),
        missing_features=missing_features,
    )
