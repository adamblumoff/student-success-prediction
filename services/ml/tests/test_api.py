import io
import os
import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = Path(__file__).resolve().parents[1]
for entry in (str(REPO_ROOT), str(SERVICES_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

os.environ.setdefault("ML_REQUIRE_API_KEY", "false")

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
