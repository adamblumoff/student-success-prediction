#!/usr/bin/env python3
"""
Combine synthetic + real datasets into a mixed dataset.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


BASE_COLUMNS = [
    "student_id",
    "name",
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
    "success_label",
    "risk_label",
    "source",
]

DEFAULT_VALUES = {
    "grade_level": 9,
    "current_gpa": 2.5,
    "attendance_rate": 0.9,
    "discipline_incidents": 0,
    "assignment_completion": 0.7,
    "parent_engagement_frequency": 1,
    "homework_quality": 0.7,
    "math_performance": 0.7,
    "reading_performance": 0.7,
    "science_performance": 0.7,
    "course_failures": 0,
    "extracurricular_participation": 0,
    "teacher_relationship_quality": 0.7,
    "social_skills": 0.7,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build mixed dataset.")
    parser.add_argument("--synthetic", required=True, help="Path to synthetic CSV.")
    parser.add_argument("--oulad", required=True, help="Path to OULAD gradebook CSV.")
    parser.add_argument("--uci", required=True, help="Path to UCI gradebook CSV.")
    parser.add_argument("--out", required=True, help="Output CSV path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--synthetic-frac", type=float, default=0.5, help="Fraction synthetic.")
    parser.add_argument("--oulad-frac", type=float, default=0.3, help="Fraction OULAD.")
    parser.add_argument("--uci-frac", type=float, default=0.2, help="Fraction UCI.")
    parser.add_argument("--rows", type=int, default=10000, help="Total output rows.")
    parser.add_argument(
        "--feature-noise",
        type=float,
        default=0.02,
        help="Gaussian noise std for numeric features (default: 0.02).",
    )
    parser.add_argument(
        "--dropout-rate",
        type=float,
        default=0.03,
        help="Fraction of numeric values to drop (default: 0.03).",
    )
    return parser.parse_args()


def normalize_frame(df: pd.DataFrame, source: str) -> pd.DataFrame:
    frame = df.copy()
    frame["source"] = frame.get("source", source)
    for col in BASE_COLUMNS:
        if col not in frame.columns:
            frame[col] = np.nan
    for col, default in DEFAULT_VALUES.items():
        frame[col] = frame[col].fillna(default)
    if "success_label" not in frame.columns:
        frame["success_label"] = 0
    if "risk_label" not in frame.columns:
        frame["risk_label"] = 1 - frame["success_label"]
    return frame[BASE_COLUMNS]


def sample_frame(df: pd.DataFrame, rows: int, rng: np.random.Generator) -> pd.DataFrame:
    replace = rows > len(df)
    idx = rng.choice(len(df), size=rows, replace=replace)
    return df.iloc[idx].reset_index(drop=True)


def main() -> int:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    synthetic_df = normalize_frame(pd.read_csv(args.synthetic), "synthetic")
    oulad_df = normalize_frame(pd.read_csv(args.oulad), "oulad")
    uci_df = normalize_frame(pd.read_csv(args.uci), "uci")

    total = args.rows
    weights = np.array([args.synthetic_frac, args.oulad_frac, args.uci_frac], dtype=float)
    if weights.sum() <= 0:
        print("Invalid mix fractions.")
        return 1
    weights = weights / weights.sum()
    counts = (weights * total).astype(int)
    counts[-1] = total - counts[:-1].sum()

    mixed = pd.concat(
        [
            sample_frame(synthetic_df, counts[0], rng),
            sample_frame(oulad_df, counts[1], rng),
            sample_frame(uci_df, counts[2], rng),
        ],
        ignore_index=True,
    )
    mixed = mixed.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)

    numeric_cols = [
        "current_gpa",
        "attendance_rate",
        "assignment_completion",
        "homework_quality",
        "math_performance",
        "reading_performance",
        "science_performance",
        "teacher_relationship_quality",
        "social_skills",
    ]
    if args.feature_noise > 0:
        for col in numeric_cols:
            jitter = rng.normal(0.0, args.feature_noise, size=len(mixed))
            if col == "current_gpa":
                mixed[col] = mixed[col].add(jitter).clip(0.0, 4.0)
            else:
                mixed[col] = mixed[col].add(jitter).clip(0.0, 1.0)

    if args.dropout_rate > 0:
        mask = rng.random((len(mixed), len(numeric_cols))) < args.dropout_rate
        for i, col in enumerate(numeric_cols):
            mixed.loc[mask[:, i], col] = np.nan

    for col, default in DEFAULT_VALUES.items():
        mixed[col] = mixed[col].fillna(default)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mixed.to_csv(out_path, index=False)
    print(f"Wrote mixed dataset: {out_path} ({len(mixed)} rows)")
    print(f"Success rate: {mixed['success_label'].mean():.3f}")
    print(f"Source mix: {mixed['source'].value_counts(normalize=True).to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
