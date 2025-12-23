from __future__ import annotations

import os
from pathlib import Path
import time
from collections import defaultdict, deque
from typing import Deque, DefaultDict
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import pandas as pd

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
MODELS_DIR = os.getenv("K12_MODELS_DIR")
if not MODELS_DIR:
    candidate = ROOT / "results" / "models" / "k12"
    if candidate.exists():
        MODELS_DIR = str(candidate)

from k12_success_predictor import K12SuccessPredictor  # noqa: E402

app = FastAPI(title="Student Success ML Service", version="1.0")

ML_API_KEY = os.getenv("ML_SERVICE_API_KEY")
REQUIRE_API_KEY = os.getenv("ML_REQUIRE_API_KEY", "true").lower() in {"1", "true", "yes"}
if REQUIRE_API_KEY and not ML_API_KEY:
    raise RuntimeError("ML_SERVICE_API_KEY must be set when ML_REQUIRE_API_KEY is true")

MAX_CSV_BYTES = int(os.getenv("MAX_CSV_BYTES", str(5 * 1024 * 1024)))
MAX_CSV_ROWS = int(os.getenv("MAX_CSV_ROWS", "20000"))
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))

_request_windows: DefaultDict[str, Deque[float]] = defaultdict(deque)

predictor = K12SuccessPredictor(models_dir=MODELS_DIR) if MODELS_DIR else K12SuccessPredictor()
model_info = predictor.get_model_info()
print(
    f"✅ ML model loaded | flavor={predictor.flavor} "
    f"type={model_info.get('model_type')} version={model_info.get('model_version')}"
)

def _require_api_key(request: Request) -> None:
    if not REQUIRE_API_KEY:
        return
    provided = request.headers.get("x-ml-api-key")
    if not provided or provided != ML_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if RATE_LIMIT_PER_MIN <= 0:
        return await call_next(request)

    client_host = request.client.host if request.client else "unknown"
    now = time.time()
    window = _request_windows[client_host]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= RATE_LIMIT_PER_MIN:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    window.append(now)

    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(request: Request, file: UploadFile = File(...)):
    _require_api_key(request)
    if not file.filename:
        raise HTTPException(status_code=400, detail="CSV file is required")

    start = time.perf_counter()
    try:
        size_bytes = None
        try:
            file.file.seek(0, os.SEEK_END)
            size_bytes = file.file.tell()
            file.file.seek(0)
        except Exception:
            size_bytes = None
        if size_bytes is not None and size_bytes > MAX_CSV_BYTES:
            raise HTTPException(status_code=413, detail="CSV file is too large")
        df = pd.read_csv(file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc

    try:
        if len(df.index) > MAX_CSV_ROWS:
            raise HTTPException(status_code=413, detail="CSV row limit exceeded")
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
