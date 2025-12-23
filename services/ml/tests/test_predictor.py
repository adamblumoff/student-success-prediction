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
