#!/usr/bin/env python3
"""
Prepare UCI Student Performance dataset into gradebook-like rows.
"""

import argparse
from pathlib import Path
import io
import zipfile

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare UCI student performance dataset.")
    parser.add_argument("--zip", required=True, help="Path to UCI student.zip file.")
    parser.add_argument("--out", required=True, help="Output CSV path.")
    return parser.parse_args()


def clamp(series, low, high):
    return series.clip(lower=low, upper=high)


def read_csv_from_zip(zip_path: Path, filename: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        if filename in zf.namelist():
            with zf.open(filename) as f:
                return pd.read_csv(f, sep=";")

        if "student.zip" in zf.namelist():
            nested = zf.read("student.zip")
            with zipfile.ZipFile(io.BytesIO(nested)) as inner:
                with inner.open(filename) as f:
                    return pd.read_csv(f, sep=";")

        raise KeyError(f"{filename} not found in archive")


def build_gradebook(df: pd.DataFrame, subject: str) -> pd.DataFrame:
    g1 = df["G1"].astype(float)
    g2 = df["G2"].astype(float)
    g3 = df["G3"].astype(float)

    current_gpa = clamp(((g1 + g2) / 2) / 20.0 * 4.0, 0.0, 4.0)
    attendance_rate = clamp(1.0 - (df["absences"].astype(float) / 93.0), 0.0, 1.0)
    assignment_completion = clamp(df["studytime"].astype(float) / 4.0, 0.0, 1.0)
    discipline_incidents = df["failures"].astype(float)
    parent_engagement_frequency = clamp(df["famrel"].astype(float) - 1.0, 0.0, 4.0)
    homework_quality = clamp(((g1 + g2) / 2) / 20.0, 0.0, 1.0)

    success_label = (g3 >= 12).astype(int)  # 60% threshold on 0-20 scale

    age = df["age"].astype(float)
    grade_level = clamp(age - 5.0, 6.0, 12.0).round(0).astype(int)

    output = pd.DataFrame(
        {
            "student_id": [f"{subject}_{i}" for i in df.index],
            "name": None,
            "grade_level": grade_level,
            "current_gpa": current_gpa.round(2),
            "attendance_rate": attendance_rate.round(3),
            "discipline_incidents": discipline_incidents,
            "assignment_completion": assignment_completion.round(3),
            "parent_engagement_frequency": parent_engagement_frequency.round(0),
            "homework_quality": homework_quality.round(3),
            "math_performance": homework_quality.round(3) if subject == "mat" else 0.7,
            "reading_performance": homework_quality.round(3) if subject == "por" else 0.7,
            "science_performance": 0.7,
            "course_failures": df["failures"].astype(int),
            "extracurricular_participation": 0,
            "teacher_relationship_quality": 0.7,
            "social_skills": 0.7,
            "success_label": success_label,
            "risk_label": 1 - success_label,
            "source": "uci",
        }
    )
    return output


def main() -> int:
    args = parse_args()
    zip_path = Path(args.zip)
    if not zip_path.exists():
        print(f"Zip not found: {zip_path}")
        return 1

    student_mat = read_csv_from_zip(zip_path, "student-mat.csv")
    student_por = read_csv_from_zip(zip_path, "student-por.csv")

    mat_out = build_gradebook(student_mat, "mat")
    por_out = build_gradebook(student_por, "por")
    output = pd.concat([mat_out, por_out], ignore_index=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(out_path, index=False)
    print(f"Wrote UCI gradebook CSV: {out_path} ({len(output)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
