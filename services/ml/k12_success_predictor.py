#!/usr/bin/env python3
"""
K-12 Success Predictor

Predicts probability of student success (>= 60% final grade).
Outputs risk_probability = 1 - success_probability for UI compatibility.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class K12SuccessPredictor:
    """Success predictor interface for gradebook CSV files."""

    def __init__(self, models_dir: str | None = None, flavor: str | None = None):
        if models_dir is None:
            models_env = os.getenv("K12_MODELS_DIR")
            if models_env:
                models_dir = Path(models_env)
            else:
                models_dir = Path(__file__).parent / "results" / "models" / "k12"

        self.models_dir = Path(models_dir)
        self.flavor = flavor or os.getenv("K12_MODEL_FLAVOR", "default")
        self.model = None
        self.features = None
        self.metadata = None

        self.gradebook_mappings = {
            "grade_level": ["grade_level", "grade", "current_grade_level"],
            "current_gpa": ["current_gpa", "gpa", "grade_avg", "current_grade"],
            "attendance_rate": ["attendance_rate", "attendance", "attendance_pct"],
            "discipline_incidents": ["discipline_incidents", "disciplinary_incidents", "referrals"],
            "assignment_completion": ["assignment_completion", "assignment_rate", "homework_rate"],
            "parent_engagement_frequency": ["parent_engagement", "parent_contact", "family_contact"],
            "homework_quality": ["homework_quality", "assignment_quality", "work_quality"],
            "math_performance": ["math_grade", "math_score", "mathematics", "math_performance"],
            "reading_performance": ["reading_grade", "reading_score", "ela_grade", "reading_performance"],
            "science_performance": ["science_grade", "science_score", "science_performance"],
            "course_failures": ["course_failures", "failures", "failed_courses"],
            "extracurricular_participation": ["extracurricular", "activities", "clubs"],
            "teacher_relationship_quality": ["teacher_rating", "teacher_relationship", "teacher_relationship_quality"],
            "social_skills": ["social_skills", "peer_relationships"],
        }

        self._load_models()

    def _model_paths(self):
        default_model = self.models_dir / "k12_success_default_gb.pkl"
        fast_model = self.models_dir / "k12_success_fast_lr.pkl"
        feature_file = self.models_dir / "k12_success_features.json"
        metadata_file = self.models_dir / "k12_success_metadata.json"
        return default_model, fast_model, feature_file, metadata_file

    def _load_models(self):
        default_model, fast_model, feature_file, metadata_file = self._model_paths()

        model_path = default_model if self.flavor == "default" else fast_model
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model = joblib.load(model_path)

        if feature_file.exists():
            with open(feature_file, "r") as f:
                self.features = json.load(f)
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                self.metadata = json.load(f)

    def _safe_float(self, value, default=0.0):
        try:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized = df.copy()
        normalized.columns = [
            str(col).strip().lower().replace(" ", "_").replace("-", "_")
            for col in normalized.columns
        ]
        return normalized

    def _extract_features(self, df: pd.DataFrame) -> dict:
        extracted = {}
        coverage = {"total": 0, "from_input": 0}

        for model_feature, possible_cols in self.gradebook_mappings.items():
            found_value = None
            for col in possible_cols:
                if col in df.columns:
                    found_value = df[col].iloc[0] if len(df) > 0 else None
                    break

            coverage["total"] += 1
            if found_value is None or pd.isna(found_value):
                if model_feature == "current_gpa":
                    extracted[model_feature] = 2.5
                elif model_feature == "attendance_rate":
                    extracted[model_feature] = 0.9
                elif model_feature == "grade_level":
                    extracted[model_feature] = 9
                elif "performance" in model_feature:
                    extracted[model_feature] = 0.7
                elif "quality" in model_feature:
                    extracted[model_feature] = 0.7
                elif "frequency" in model_feature or "participation" in model_feature:
                    extracted[model_feature] = 1
                else:
                    extracted[model_feature] = 0
            else:
                extracted[model_feature] = self._safe_float(found_value, default=0.0)
                coverage["from_input"] += 1

        extracted["_feature_coverage"] = coverage
        return extracted

    def _normalize_value(self, value):
        if value is None:
            return None
        if isinstance(value, (np.floating, float)) and np.isnan(value):
            return None
        if isinstance(value, (np.integer, int)):
            return int(value)
        if isinstance(value, (np.floating, float)):
            return float(value)
        if isinstance(value, str):
            return value.strip()
        return value

    def _row_hash(self, row: pd.Series) -> str:
        normalized = {}
        for key, value in row.items():
            if key is None:
                continue
            norm_key = str(key).strip().lower().replace(" ", "_").replace("-", "_")
            normalized[norm_key] = self._normalize_value(value)
        payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        return str(joblib.hash(payload))

    def _feature_vector(self, feature_dict: dict) -> np.ndarray:
        feature_list = self.features or list(self.gradebook_mappings.keys())
        values = [feature_dict.get(name, 0) for name in feature_list]
        return np.array(values, dtype=float).reshape(1, -1)

    def predict_from_gradebook(self, gradebook_df: pd.DataFrame):
        predictions = []
        normalized_df = self._normalize_columns(gradebook_df)

        for idx, row in gradebook_df.iterrows():
            normalized_row = normalized_df.loc[idx]
            features = self._extract_features(pd.DataFrame([normalized_row]))
            X = self._feature_vector(features)
            success_prob = float(self.model.predict_proba(X)[0, 1])
            risk_prob = 1.0 - success_prob

            if risk_prob < 0.3:
                risk_category = "Low Risk"
                risk_level = "success"
            elif risk_prob < 0.7:
                risk_category = "Moderate Risk"
                risk_level = "warning"
            else:
                risk_category = "High Risk"
                risk_level = "danger"

            result = {
                "student_id": row.get("student_id", row.get("id", row.get("ID", f"student_{idx}"))),
                "name": row.get("name", row.get("student_name", row.get("Student", "Unknown"))),
                "grade_level": int(features.get("grade_level", 9)),
                "current_gpa": float(features.get("current_gpa", 2.5)),
                "attendance_rate": float(features.get("attendance_rate", 0.9)),
                "risk_probability": risk_prob,
                "risk_category": risk_category,
                "risk_level": risk_level,
                "confidence": float(abs(risk_prob - 0.5) * 2),
                "model_type": "success_default" if self.flavor == "default" else "success_fast",
                "feature_coverage": features.get("_feature_coverage", {}),
                "input_hash": self._row_hash(normalized_row),
                "assignment_completion": row.get("assignment_completion"),
                "quiz_average": row.get("quiz_average"),
                "participation_score": row.get("participation_score"),
                "late_submissions": row.get("late_submissions"),
                "course_difficulty": row.get("course_difficulty"),
                "previous_gpa": row.get("previous_gpa"),
                "study_hours_week": row.get("study_hours_week"),
                "extracurricular": row.get("extracurricular"),
                "parent_education": row.get("parent_education"),
                "socioeconomic_status": row.get("socioeconomic_status"),
            }
            predictions.append(result)

        return predictions

    def generate_recommendations(self, student_result: dict) -> list[str]:
        grade_level = student_result.get("grade_level", 9)
        risk_level = student_result.get("risk_level", "warning")
        gpa = student_result.get("current_gpa", 2.5)
        attendance = student_result.get("attendance_rate", 0.9)

        recommendations = []

        if risk_level in ["warning", "danger"]:
            if gpa < 2.0:
                if grade_level <= 8:
                    recommendations.append("Implement intensive academic support with daily check-ins")
                    recommendations.append("Provide grade-level appropriate skill building")
                else:
                    recommendations.append("Enroll in credit recovery and graduation planning")
                    recommendations.append("Implement weekly academic progress monitoring")
            elif gpa < 2.5:
                recommendations.append("Provide targeted subject-specific tutoring")
                recommendations.append("Implement study skills and organization training")

            if attendance < 0.85:
                recommendations.append("Develop comprehensive attendance improvement plan")
                recommendations.append("Coordinate with family for attendance barriers")
            elif attendance < 0.9:
                recommendations.append("Monitor attendance patterns and early intervention")

            if risk_level == "danger":
                recommendations.append("Convene student support team meeting immediately")
                recommendations.append("Develop intensive multi-tiered intervention plan")
                recommendations.append("Coordinate with counseling and family support services")
            else:
                recommendations.append("Schedule regular progress monitoring meetings")
        else:
            recommendations.append("Continue current support strategies")
            recommendations.append("Recognize positive academic progress")
            recommendations.append("Monitor for continued success")

        return recommendations[:5]

    def get_model_info(self):
        if self.metadata:
            return {
                "model_type": self.metadata.get("model_type", "success_model"),
                "model_version": self.metadata.get("timestamp"),
                "auc_score": self.metadata.get("auc_score"),
                "feature_count": self.metadata.get("feature_count"),
                "approach": self.metadata.get("approach"),
                "data_samples": self.metadata.get("data_samples"),
            }
        return {
            "model_type": "success_model",
            "model_version": None,
            "auc_score": None,
            "feature_count": None,
            "approach": None,
            "data_samples": None,
        }
