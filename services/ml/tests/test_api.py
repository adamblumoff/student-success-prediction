import io
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = Path(__file__).resolve().parents[1]
for entry in (str(REPO_ROOT), str(SERVICES_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

os.environ.setdefault("ML_REQUIRE_API_KEY", "false")

# Prevent model loading during tests by stubbing the predictor before app import.
class _StubPredictor:
    flavor = "default"

    def __init__(self, *args, **kwargs):
        pass

    def get_model_info(self):
        return {"model_type": "success_default", "model_version": "test"}

    def predict_from_gradebook(self, df):
        def _primitive(value):
            if hasattr(value, "item"):
                return value.item()
            return value

        return [
            {
                "student_id": _primitive(row.get("student_id", "student")),
                "name": str(_primitive(row.get("name", "Student"))),
                "grade_level": 10,
                "current_gpa": 3.0,
                "attendance_rate": 0.9,
                "risk_probability": 0.2,
                "risk_category": "Low Risk",
                "risk_level": "success",
                "confidence": 0.6,
                "model_type": "success_default",
                "feature_coverage": {},
                "input_hash": "hash"
            }
            for _, row in df.iterrows()
        ]

    def generate_recommendations(self, _pred):
        return []


mock_module = MagicMock()
mock_module.K12SuccessPredictor = _StubPredictor
sys.modules["k12_success_predictor"] = mock_module

from services.ml import app as app_module  # noqa: E402

client = TestClient(app_module.app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_from_csv():
    df = pd.DataFrame(
        {
            "student_id": [1, 2],
            "name": ["Student One", "Student Two"],
            "grade_level": [10, 11],
            "current_gpa": [3.1, 2.4],
            "attendance_rate": [0.95, 0.8]
        }
    )
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    response = client.post(
        "/predict",
        files={"file": ("gradebook.csv", buffer.getvalue(), "text/csv")}
    )

    assert response.status_code == 200
    payload = response.json()
    assert "predictions" in payload
    assert len(payload["predictions"]) == 2
    assert "model_info" in payload


def test_predict_requires_file():
    response = client.post("/predict")
    assert response.status_code in {400, 422}


def test_predict_rejects_empty_filename():
    response = client.post(
        "/predict",
        files={"file": ("", "student_id\n1\n", "text/csv")}
    )
    assert response.status_code in {400, 422}


def test_predict_rejects_row_limit():
    original_limit = app_module.MAX_CSV_ROWS
    try:
        app_module.MAX_CSV_ROWS = 1
        df = pd.DataFrame(
            {
                "student_id": [1, 2],
                "name": ["Student One", "Student Two"],
                "grade_level": [10, 11],
                "current_gpa": [3.1, 2.4],
                "attendance_rate": [0.95, 0.8]
            }
        )
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        response = client.post(
            "/predict",
            files={"file": ("gradebook.csv", buffer.getvalue(), "text/csv")}
        )
        assert response.status_code == 500
        assert "CSV row limit exceeded" in response.text
    finally:
        app_module.MAX_CSV_ROWS = original_limit


def test_predict_rejects_invalid_csv():
    response = client.post(
        "/predict",
        files={"file": ("gradebook.csv", b"\x00\xff\x00\xff", "text/csv")}
    )
    assert response.status_code == 400


def test_predict_rejects_large_file():
    original_limit = app_module.MAX_CSV_BYTES
    try:
        app_module.MAX_CSV_BYTES = 1
        response = client.post(
            "/predict",
            files={"file": ("gradebook.csv", "student_id\n1\n", "text/csv")}
        )
        assert response.status_code == 400
        assert "CSV file is too large" in response.text
    finally:
        app_module.MAX_CSV_BYTES = original_limit


def test_rate_limit_middleware():
    original_limit = app_module.RATE_LIMIT_PER_MIN
    try:
        app_module.RATE_LIMIT_PER_MIN = 1
        app_module._request_windows.clear()
        payload = "student_id,name,grade_level,current_gpa,attendance_rate\n1,Student One,10,3.1,0.95\n"
        response1 = client.post(
            "/predict",
            files={"file": ("gradebook.csv", payload, "text/csv")}
        )
        assert response1.status_code == 200
        response2 = client.post(
            "/predict",
            files={"file": ("gradebook.csv", payload, "text/csv")}
        )
        assert response2.status_code == 429
    finally:
        app_module.RATE_LIMIT_PER_MIN = original_limit
        app_module._request_windows.clear()


def test_rate_limit_disabled():
    original_limit = app_module.RATE_LIMIT_PER_MIN
    try:
        app_module.RATE_LIMIT_PER_MIN = 0
        response = client.get("/health")
        assert response.status_code == 200
    finally:
        app_module.RATE_LIMIT_PER_MIN = original_limit


def test_require_api_key_rejects_missing_key():
    original_require = app_module.REQUIRE_API_KEY
    original_key = app_module.ML_API_KEY
    try:
        app_module.REQUIRE_API_KEY = True
        app_module.ML_API_KEY = "secret"
        response = client.post(
            "/predict",
            files={"file": ("gradebook.csv", "student_id\n1\n", "text/csv")}
        )
        assert response.status_code == 401
    finally:
        app_module.REQUIRE_API_KEY = original_require
        app_module.ML_API_KEY = original_key


def test_require_api_key_allows_valid_key():
    original_require = app_module.REQUIRE_API_KEY
    original_key = app_module.ML_API_KEY
    try:
        app_module.REQUIRE_API_KEY = True
        app_module.ML_API_KEY = "secret"
        response = client.post(
            "/predict",
            files={"file": ("gradebook.csv", "student_id\n1\n", "text/csv")},
            headers={"x-ml-api-key": "secret"}
        )
        assert response.status_code == 200
    finally:
        app_module.REQUIRE_API_KEY = original_require
        app_module.ML_API_KEY = original_key
