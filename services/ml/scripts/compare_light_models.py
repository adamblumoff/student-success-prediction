#!/usr/bin/env python3
"""
Train lightweight models on a labeled CSV and compare accuracy + inference speed.
"""

import argparse
from pathlib import Path
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare lightweight models.")
    parser.add_argument("--csv", required=True, help="Path to labeled CSV.")
    parser.add_argument(
        "--label-col",
        default="risk_label",
        help="Binary label column name (default: risk_label).",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Validation split size (default: 0.2).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )
    return parser.parse_args()


def prep_data(df: pd.DataFrame, label_col: str):
    y = df[label_col].astype(int).values
    drop_cols = {label_col, "success_label", "risk_label", "source", "name", "student_id"}
    existing = [col for col in drop_cols if col in df.columns]
    X = df.drop(columns=existing).copy()
    X = X.select_dtypes(include=[np.number]).fillna(0)
    return X.values, y


def time_predict(model, X):
    start = time.perf_counter()
    probs = model.predict_proba(X)[:, 1]
    total_ms = (time.perf_counter() - start) * 1000
    per_row_ms = total_ms / max(1, X.shape[0])
    return probs, total_ms, per_row_ms


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 1

    df = pd.read_csv(csv_path)
    if args.label_col not in df.columns:
        print(f"Label column '{args.label_col}' not found in CSV.")
        return 1

    X, y = prep_data(df, args.label_col)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, stratify=y if len(set(y)) > 1 else None
    )

    models = {
        "log_reg": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "grad_boost": GradientBoostingClassifier(random_state=args.seed),
    }

    print("Model comparison")
    for name, model in models.items():
        start_fit = time.perf_counter()
        model.fit(X_train, y_train)
        fit_ms = (time.perf_counter() - start_fit) * 1000

        probs, total_ms, per_row_ms = time_predict(model, X_val)
        auc = roc_auc_score(y_val, probs) if len(set(y_val)) > 1 else float("nan")
        f1 = f1_score(y_val, (probs >= 0.5).astype(int), zero_division=0)
        print(
            f"- {name}: auc={auc:.4f} f1={f1:.4f} "
            f"fit_ms={fit_ms:.1f} infer_ms={total_ms:.2f} per_row_ms={per_row_ms:.4f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
