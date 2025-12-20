#!/usr/bin/env python3
"""
Create a stratified validation split from a labeled CSV.
"""

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a validation CSV split.")
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
        "--out",
        required=True,
        help="Output path for validation CSV.",
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

    y = df[args.label_col].astype(float)
    train_df, val_df = train_test_split(
        df,
        test_size=args.test_size,
        random_state=42,
        stratify=y if len(set(y)) > 1 else None,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    val_df.to_csv(out_path, index=False)

    print(f"Wrote validation CSV: {out_path} ({len(val_df)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
