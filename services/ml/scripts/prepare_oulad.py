#!/usr/bin/env python3
"""
Prepare OULAD (Open University Learning Analytics Dataset) into gradebook-like rows.
"""

import argparse
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare OULAD into gradebook schema.")
    parser.add_argument("--zip", required=True, help="Path to OULAD zip file.")
    parser.add_argument("--out", required=True, help="Output CSV path.")
    return parser.parse_args()


def clamp(series, low, high):
    return series.clip(lower=low, upper=high)


def read_csv_from_zip(zip_path: Path, filename: str) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(filename) as f:
            return pd.read_csv(f)


def main() -> int:
    args = parse_args()
    zip_path = Path(args.zip)
    if not zip_path.exists():
        print(f"Zip not found: {zip_path}")
        return 1

    student_info = read_csv_from_zip(zip_path, "studentInfo.csv")
    student_vle = read_csv_from_zip(zip_path, "studentVle.csv")
    student_assessment = read_csv_from_zip(zip_path, "studentAssessment.csv")
    assessments = read_csv_from_zip(zip_path, "assessments.csv")
    courses = read_csv_from_zip(zip_path, "courses.csv")

    # Label: success if final_result is Pass or Distinction
    final_result = student_info["final_result"].fillna("Unknown")
    success_label = final_result.isin(["Pass", "Distinction"]).astype(int)

    # Course length
    courses_key = ["code_module", "code_presentation"]
    length_col = "length" if "length" in courses.columns else "module_presentation_length"
    course_length = courses[courses_key + [length_col]].drop_duplicates()
    course_length = course_length.rename(columns={length_col: "length"})

    # VLE engagement features
    vle_group = (
        student_vle.groupby(["id_student", "code_module", "code_presentation"])
        .agg(total_clicks=("sum_click", "sum"), active_days=("date", "nunique"))
        .reset_index()
    )

    # Assessment features
    assessments_key = ["id_assessment", "code_module", "code_presentation"]
    assessment_lookup = assessments[assessments_key + ["weight"]].copy()
    student_assessment = student_assessment.merge(
        assessment_lookup, on="id_assessment", how="left"
    )

    total_assessments = (
        assessments.groupby(courses_key)
        .agg(total_assessments=("id_assessment", "nunique"))
        .reset_index()
    )

    assessment_group = (
        student_assessment.groupby(["id_student", "code_module", "code_presentation"])
        .agg(
            assessments_submitted=("id_assessment", "nunique"),
            assessment_avg_score=("score", "mean"),
        )
        .reset_index()
    )

    features = student_info.merge(vle_group, on=["id_student", "code_module", "code_presentation"], how="left")
    features = features.merge(assessment_group, on=["id_student", "code_module", "code_presentation"], how="left")
    features = features.merge(total_assessments, on=courses_key, how="left")
    features = features.merge(course_length, on=courses_key, how="left")

    features["total_clicks"] = features["total_clicks"].fillna(0)
    features["active_days"] = features["active_days"].fillna(0)
    features["assessments_submitted"] = features["assessments_submitted"].fillna(0)
    features["assessment_avg_score"] = features["assessment_avg_score"].fillna(0)
    features["total_assessments"] = features["total_assessments"].fillna(1)
    features["length"] = features["length"].fillna(120)

    attendance_rate = clamp(features["active_days"] / features["length"], 0.0, 1.0)
    assignment_completion = clamp(
        features["assessments_submitted"] / features["total_assessments"], 0.0, 1.0
    )
    homework_quality = clamp(features["assessment_avg_score"] / 100.0, 0.0, 1.0)
    current_gpa = clamp((features["assessment_avg_score"] / 100.0) * 4.0, 0.0, 4.0)
    course_failures = (homework_quality < 0.5).astype(int)

    output = pd.DataFrame(
        {
            "student_id": features["id_student"].astype(str),
            "name": None,
            "grade_level": 12,
            "current_gpa": current_gpa.round(2),
            "attendance_rate": attendance_rate.round(3),
            "discipline_incidents": 0,
            "assignment_completion": assignment_completion.round(3),
            "parent_engagement_frequency": 1,
            "homework_quality": homework_quality.round(3),
            "math_performance": homework_quality.round(3),
            "reading_performance": homework_quality.round(3),
            "science_performance": homework_quality.round(3),
            "course_failures": course_failures,
            "extracurricular_participation": 0,
            "teacher_relationship_quality": 0.7,
            "social_skills": 0.7,
            "success_label": success_label,
            "risk_label": 1 - success_label,
            "source": "oulad",
        }
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(out_path, index=False)
    print(f"Wrote OULAD gradebook CSV: {out_path} ({len(output)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
