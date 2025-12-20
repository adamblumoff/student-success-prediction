#!/usr/bin/env python3
"""
Train and save default (gradient boosting) and fast (logistic regression) success models.
"""

import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, f1_score
import joblib
import json


DEFAULT_FEATURES = [
    "grade_level",
    "current_gpa",
    "attendance_rate",
    "discipline_incidents",
    "assignment_completion",
    "parent_engagement_frequency",
    "homework_quality",
    "math_performance",
    "reading_performance",
    "science_performance",
    "course_failures",
    "extracurricular_participation",
    "teacher_relationship_quality",
    "social_skills",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train success models.")
    parser.add_argument("--csv", required=True, help="Path to training CSV.")
    parser.add_argument(
        "--label-col",
        default="success_label",
        help="Binary label column (default: success_label).",
    )
    parser.add_argument(
        "--out-dir",
        default="services/ml/results/models/k12",
        help="Output directory for models.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--test-size", type=float, default=0.2, help="Validation split size.")
    return parser.parse_args()


def prep_data(df: pd.DataFrame, label_col: str):
    missing = [col for col in DEFAULT_FEATURES if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    X = df[DEFAULT_FEATURES].copy()
    X = X.fillna(0)
    y = df[label_col].astype(int).values
    return X.values, y


def main() -> int:
    args = parse_args()
    df = pd.read_csv(args.csv)
    if args.label_col not in df.columns:
        raise ValueError(f"Label column '{args.label_col}' not found.")

    X, y = prep_data(df, args.label_col)
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=y if len(set(y)) > 1 else None,
    )

    fast_model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    default_model = GradientBoostingClassifier(random_state=args.seed)

    fast_model.fit(X_train, y_train)
    default_model.fit(X_train, y_train)

    fast_probs = fast_model.predict_proba(X_val)[:, 1]
    default_probs = default_model.predict_proba(X_val)[:, 1]

    metrics = {
        "fast_auc": roc_auc_score(y_val, fast_probs) if len(set(y_val)) > 1 else None,
        "fast_f1": f1_score(y_val, (fast_probs >= 0.5).astype(int), zero_division=0),
        "default_auc": roc_auc_score(y_val, default_probs) if len(set(y_val)) > 1 else None,
        "default_f1": f1_score(y_val, (default_probs >= 0.5).astype(int), zero_division=0),
    }

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(default_model, out_dir / "k12_success_default_gb.pkl")
    joblib.dump(fast_model, out_dir / "k12_success_fast_lr.pkl")

    with open(out_dir / "k12_success_features.json", "w") as f:
        json.dump(DEFAULT_FEATURES, f, indent=2)

    metadata = {
        "timestamp": timestamp,
        "model_type": "success_models",
        "feature_count": len(DEFAULT_FEATURES),
        "approach": "gradient_boost_default_log_reg_fast",
        "data_samples": int(len(df)),
        "metrics": metrics,
    }
    with open(out_dir / "k12_success_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("Training complete.")
    print(metrics)
    print(f"Saved models to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
