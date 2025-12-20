from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODELS_DIR = os.getenv("K12_MODELS_DIR")
if not MODELS_DIR:
    candidate = ROOT / "results" / "models" / "k12"
    if candidate.exists():
        MODELS_DIR = str(candidate)

from k12_ultra_predictor import K12UltraPredictor  # noqa: E402

app = FastAPI(title="Student Success ML Service", version="1.0")

predictor = K12UltraPredictor(models_dir=MODELS_DIR) if MODELS_DIR else K12UltraPredictor()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="CSV file is required")

    try:
        df = pd.read_csv(file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc

    try:
        predictions = predictor.predict_from_gradebook(df)
        for pred in predictions:
            pred["recommendations"] = predictor.generate_recommendations(pred)
        return JSONResponse(
            {
                "predictions": predictions,
                "model_info": predictor.get_model_info()
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
