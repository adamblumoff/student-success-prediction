#!/usr/bin/env python3
"""
Evaluate K12 model predictions against a labeled CSV.

Expected: a CSV with a binary label column (0/1).
"""

import argparse
from pathlib import Path
import sys

import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from k12_success_predictor import K12SuccessPredictor  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate model on labeled CSV.")
    parser.add_argument("--csv", required=True, help="Path to labeled CSV.")
    parser.add_argument(
        "--label-col",
        default="risk_label",
        help="Binary label column name (default: risk_label).",
    )
    parser.add_argument(
        "--label-type",
        choices=["risk", "success"],
        default="risk",
        help="Whether label represents risk or success (default: risk).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Decision threshold for classification metrics (default: 0.5).",
    )
    return parser.parse_args()


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

    label_series = df[args.label_col].astype(float)
    eval_df = df.drop(columns=[args.label_col])
    eval_df = eval_df.dropna(subset=eval_df.columns, how="all")
    label_series = label_series.loc[eval_df.index]

    predictor = K12SuccessPredictor()
    results = predictor.predict_from_gradebook(eval_df)

    y_true = label_series.values
    risk_probs = pd.Series([r.get("risk_probability", 0.5) for r in results]).values
    if args.label_type == "success":
        y_prob = 1.0 - risk_probs
    else:
        y_prob = risk_probs
    y_pred = (y_prob >= args.threshold).astype(int)

    metrics = {
        "roc_auc": roc_auc_score(y_true, y_prob) if len(set(y_true)) > 1 else None,
        "avg_precision": average_precision_score(y_true, y_prob) if len(set(y_true)) > 1 else None,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "brier": brier_score_loss(y_true, y_prob),
    }

    coverage = [
        r.get("feature_coverage", {}).get("from_input", 0) / max(1, r.get("feature_coverage", {}).get("total", 1))
        for r in results
    ]
    coverage_avg = sum(coverage) / max(1, len(coverage))

    print("Evaluation summary")
    print(f"- rows: {len(eval_df)}")
    print(f"- label_col: {args.label_col}")
    print(f"- threshold: {args.threshold}")
    print(f"- feature_coverage_avg: {coverage_avg:.3f}")
    for key, value in metrics.items():
        if value is None:
            print(f"- {key}: n/a (single class)")
        else:
            print(f"- {key}: {value:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
