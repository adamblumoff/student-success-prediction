#!/usr/bin/env python3
"""
Sweep thresholds for model predictions on a labeled CSV.
"""

import argparse
from pathlib import Path
import sys

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from k12_success_predictor import K12SuccessPredictor  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep thresholds for model metrics.")
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
        "--steps",
        type=int,
        default=41,
        help="Number of thresholds between 0 and 1 (default: 41).",
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

    labels = df[args.label_col].astype(float)
    eval_df = df.drop(columns=[args.label_col])
    eval_df = eval_df.dropna(subset=eval_df.columns, how="all")
    labels = labels.loc[eval_df.index].values

    predictor = K12SuccessPredictor()
    results = predictor.predict_from_gradebook(eval_df)
    risk_probs = pd.Series([r.get("risk_probability", 0.5) for r in results]).values
    if args.label_type == "success":
        probs = 1.0 - risk_probs
    else:
        probs = risk_probs

    thresholds = [i / (args.steps - 1) for i in range(args.steps)]
    rows = []
    for thr in thresholds:
        preds = (probs >= thr).astype(int)
        rows.append(
            {
                "threshold": thr,
                "accuracy": accuracy_score(labels, preds),
                "precision": precision_score(labels, preds, zero_division=0),
                "recall": recall_score(labels, preds, zero_division=0),
                "f1": f1_score(labels, preds, zero_division=0),
            }
        )

    metrics_df = pd.DataFrame(rows)
    best_f1 = metrics_df.loc[metrics_df["f1"].idxmax()]
    best_recall = metrics_df.loc[metrics_df["recall"].idxmax()]
    best_precision = metrics_df.loc[metrics_df["precision"].idxmax()]

    print("Best by F1")
    print(best_f1.to_string(index=False))
    print("\nBest by Recall")
    print(best_recall.to_string(index=False))
    print("\nBest by Precision")
    print(best_precision.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
