#!/usr/bin/env python3
"""
Generate a synthetic gradebook CSV with a heuristic risk label.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


FIRST_NAMES = [
    "Jordan", "Casey", "Riley", "Taylor", "Morgan", "Avery", "Cameron",
    "Drew", "Elliot", "Parker", "Quinn", "Reese", "Rowan", "Sage", "Skyler"
]

LAST_NAMES = [
    "Smith", "Lee", "Johnson", "Garcia", "Patel", "Nguyen", "Brown",
    "Davis", "Martinez", "Wilson", "Anderson", "Thomas", "Moore"
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic gradebook CSV.")
    parser.add_argument("--rows", type=int, default=2000, help="Number of rows to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--out", required=True, help="Output CSV path.")
    parser.add_argument(
        "--target-success-rate",
        type=float,
        default=0.5,
        help="Target fraction of success labels (default: 0.5).",
    )
    parser.add_argument(
        "--label-col",
        default="risk_label",
        help="Binary label column name (default: risk_label).",
    )
    parser.add_argument(
        "--label-noise",
        type=float,
        default=0.05,
        help="Flip a fraction of labels (default: 0.05).",
    )
    parser.add_argument(
        "--feature-noise",
        type=float,
        default=0.02,
        help="Gaussian noise std for numeric features (default: 0.02).",
    )
    return parser.parse_args()


def clamp(values, low, high):
    return np.clip(values, low, high)


def calibrate_bias(risk_score, target_rate):
    if target_rate <= 0 or target_rate >= 1:
        return 0.0

    lo, hi = -10.0, 10.0
    for _ in range(40):
        mid = (lo + hi) / 2
        prob = 1 / (1 + np.exp(-(risk_score + mid)))
        rate = prob.mean()
        if rate > target_rate:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def main() -> int:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    rows = args.rows
    grade_level = rng.integers(6, 13, size=rows)

    # Core academic signals
    current_gpa = clamp(rng.normal(2.6, 0.7, size=rows), 0.0, 4.0)
    attendance_rate = clamp(rng.normal(0.92, 0.08, size=rows), 0.6, 1.0)
    assignment_completion = clamp(rng.normal(0.78, 0.15, size=rows), 0.2, 1.0)

    # Behavior & support signals
    discipline_incidents = clamp(rng.poisson(0.6, size=rows), 0, 10)
    parent_engagement_frequency = clamp(rng.integers(0, 5, size=rows), 0, 4)
    homework_quality = clamp(rng.normal(0.75, 0.15, size=rows), 0.2, 1.0)

    # Subject performance correlated with GPA
    base_perf = clamp((current_gpa / 4.0) + rng.normal(0.0, 0.1, size=rows), 0.2, 1.0)
    math_performance = clamp(base_perf + rng.normal(0.0, 0.08, size=rows), 0.2, 1.0)
    reading_performance = clamp(base_perf + rng.normal(0.0, 0.08, size=rows), 0.2, 1.0)
    science_performance = clamp(base_perf + rng.normal(0.0, 0.08, size=rows), 0.2, 1.0)

    course_failures = clamp(
        (current_gpa < 2.0).astype(int) + (assignment_completion < 0.5).astype(int),
        0,
        3,
    )

    extracurricular_participation = clamp(rng.integers(0, 3, size=rows), 0, 2)
    teacher_relationship_quality = clamp(rng.normal(0.7, 0.15, size=rows), 0.2, 1.0)
    social_skills = clamp(rng.normal(0.7, 0.15, size=rows), 0.2, 1.0)

    # Success score (heuristic, attendance-heavy)
    success_score = (
        (attendance_rate - 0.85) * 5.0 +
        (current_gpa - 2.2) * 1.6 +
        (assignment_completion - 0.65) * 2.4 +
        (parent_engagement_frequency / 4.0) * 0.6 +
        (homework_quality - 0.7) * 1.0 +
        (teacher_relationship_quality - 0.65) * 0.8 +
        (social_skills - 0.65) * 0.6 -
        (discipline_incidents / 5.0) * 1.2 -
        (course_failures / 2.0) * 1.6
    )

    # Convert to probability and sample label (calibrated to target success rate)
    bias = calibrate_bias(success_score, args.target_success_rate)
    success_prob = 1 / (1 + np.exp(-(success_score + bias)))
    success_label = rng.binomial(1, clamp(success_prob, 0.0, 1.0))

    if args.label_noise > 0:
        flip_mask = rng.random(rows) < args.label_noise
        success_label = np.where(flip_mask, 1 - success_label, success_label)

    risk_label = 1 - success_label

    student_ids = [f"S{10000 + i}" for i in range(rows)]
    names = [
        f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        for _ in range(rows)
    ]

    df = pd.DataFrame(
        {
            "student_id": student_ids,
            "name": names,
            "grade_level": grade_level,
            "current_gpa": current_gpa.round(2),
            "attendance_rate": attendance_rate.round(3),
            "discipline_incidents": discipline_incidents,
            "assignment_completion": assignment_completion.round(3),
            "parent_engagement_frequency": parent_engagement_frequency,
            "homework_quality": homework_quality.round(3),
            "math_performance": math_performance.round(3),
            "reading_performance": reading_performance.round(3),
            "science_performance": science_performance.round(3),
            "course_failures": course_failures,
            "extracurricular_participation": extracurricular_participation,
            "teacher_relationship_quality": teacher_relationship_quality.round(3),
            "social_skills": social_skills.round(3),
            "success_label": success_label,
            "risk_label": risk_label,
        }
    )

    if args.feature_noise > 0:
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
        for col in numeric_cols:
            jitter = rng.normal(0.0, args.feature_noise, size=rows)
            if col == "current_gpa":
                df[col] = clamp(df[col] + jitter, 0.0, 4.0)
            else:
                df[col] = clamp(df[col] + jitter, 0.0, 1.0)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote synthetic gradebook: {out_path} ({len(df)} rows)")
    print(f"Target success rate: {args.target_success_rate:.2f}, actual: {df['success_label'].mean():.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
