from __future__ import annotations

import os
from pathlib import Path
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODELS_DIR = os.getenv("K12_MODELS_DIR")
if not MODELS_DIR:
    candidate = ROOT / "results" / "models" / "k12"
    if candidate.exists():
        MODELS_DIR = str(candidate)

from k12_success_predictor import K12SuccessPredictor  # noqa: E402

app = FastAPI(title="Student Success ML Service", version="1.0")

predictor = K12SuccessPredictor(models_dir=MODELS_DIR) if MODELS_DIR else K12SuccessPredictor()
model_info = predictor.get_model_info()
print(
    f"✅ ML model loaded | flavor={predictor.flavor} "
    f"type={model_info.get('model_type')} version={model_info.get('model_version')}"
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="CSV file is required")

    start = time.perf_counter()
    try:
        df = pd.read_csv(file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc

    try:
        predictions = predictor.predict_from_gradebook(df)
        for pred in predictions:
            pred["recommendations"] = predictor.generate_recommendations(pred)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return JSONResponse(
            {
                "predictions": predictions,
                "model_info": predictor.get_model_info(),
                "latency_ms": latency_ms
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
