import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.ml.k12_success_predictor import K12SuccessPredictor


def test_normalize_columns():
    predictor = K12SuccessPredictor()
    df = pd.DataFrame({"Student ID": [1], "Current GPA": [3.2]})
    normalized = predictor._normalize_columns(df)
    assert "student_id" in normalized.columns
    assert "current_gpa" in normalized.columns


def test_extract_features_defaults():
    predictor = K12SuccessPredictor()
    df = pd.DataFrame({"student_id": [1]})
    extracted = predictor._extract_features(df)
    coverage = extracted.get("_feature_coverage", {})

    assert extracted["grade_level"] == 9
    assert extracted["current_gpa"] == 2.5
    assert extracted["attendance_rate"] == 0.9
    assert coverage.get("total") == len(predictor.gradebook_mappings)


def test_safe_float_handles_invalid():
    predictor = K12SuccessPredictor()
    assert predictor._safe_float("not-a-number", default=1.0) == 1.0
    assert predictor._safe_float(None, default=2.0) == 2.0


def test_row_hash_stable():
    predictor = K12SuccessPredictor()
    row = pd.Series({"Student ID": 1, "Current GPA": 3.2})
    first = predictor._row_hash(row)
    second = predictor._row_hash(row)
    assert first == second


def test_feature_vector_respects_feature_list():
    predictor = K12SuccessPredictor()
    predictor.features = ["current_gpa", "attendance_rate"]
    vec = predictor._feature_vector({"current_gpa": 3.1, "attendance_rate": 0.8})
    assert vec.shape == (1, 2)
    assert float(vec[0, 0]) == 3.1
    assert float(vec[0, 1]) == 0.8


def test_normalize_value_handles_types():
    predictor = K12SuccessPredictor()
    assert predictor._normalize_value("  hi ") == "hi"
    assert predictor._normalize_value(3) == 3
    assert predictor._normalize_value(3.5) == 3.5


def test_generate_recommendations_low_risk():
    predictor = K12SuccessPredictor()
    recs = predictor.generate_recommendations(
        {"risk_level": "success", "current_gpa": 3.5, "attendance_rate": 0.95}
    )
    assert len(recs) > 0
    assert "Monitor for continued success" in recs[-1]


def test_generate_recommendations_high_risk():
    predictor = K12SuccessPredictor()
    recs = predictor.generate_recommendations(
        {"risk_level": "danger", "current_gpa": 1.8, "attendance_rate": 0.8, "grade_level": 9}
    )
    assert any("attendance" in r.lower() for r in recs)
    assert any("support" in r.lower() or "intervention" in r.lower() for r in recs)


def test_get_model_info_defaults():
    predictor = K12SuccessPredictor()
    predictor.metadata = None
    info = predictor.get_model_info()
    assert info["model_type"] == "success_model"
