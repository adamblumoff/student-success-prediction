# Model Development Notes (Success Prediction)

This document describes how the current ML models are created, trained, and integrated.

## Goal
- Predict student **success probability** (≥ 60% final grade).
- The API exposes `risk_probability` for UI compatibility, computed as `1 - success_probability`.

## Data sources
1) **Synthetic gradebook data**
   - Generated with `services/ml/scripts/generate_synthetic_gradebook.py`.
   - Parameters tuned for **50% success rate** and **attendance as the strongest driver**.
   - Includes label noise + feature noise to reduce overfitting to clean rules.

2) **Open University Learning Analytics Dataset (OULAD)**
   - Higher‑education dataset with pass/fail outcomes.
   - Prepared via `services/ml/scripts/prepare_oulad.py`.
   - Mapped to gradebook-like fields (attendance, GPA proxy, completion).

3) **UCI Student Performance**
   - Secondary education dataset with course grades.
   - Prepared via `services/ml/scripts/prepare_uci_student_performance.py`.
   - Success label uses final grade ≥ 60%.

## Dataset preparation
1) Download public datasets:
   - `services/ml/scripts/download_public_datasets.py`
2) Prepare real datasets:
   - `prepare_oulad.py` → `/tmp/oulad_gradebook.csv`
   - `prepare_uci_student_performance.py` → `/tmp/uci_gradebook.csv`
3) Generate synthetic data:
   - `generate_synthetic_gradebook.py` → `/tmp/gradebook-synth.csv`
4) Mix datasets:
   - `build_mixed_dataset.py` → `/tmp/gradebook-mixed.csv`
   - Default mix: 50% synthetic, 30% OULAD, 20% UCI
   - Adds numeric jitter + dropout to increase realism

## Feature set
The models use a stable subset of gradebook fields:
- `grade_level`
- `current_gpa`
- `attendance_rate`
- `discipline_incidents`
- `assignment_completion`
- `parent_engagement_frequency`
- `homework_quality`
- `math_performance`
- `reading_performance`
- `science_performance`
- `course_failures`
- `extracurricular_participation`
- `teacher_relationship_quality`
- `social_skills`

Missing values are filled with defaults in the predictor.

## Training
Use `services/ml/scripts/train_success_models.py`:
- **Default model:** Gradient Boosting
- **Fast model:** Logistic Regression (with StandardScaler)

Example:
```bash
python3 services/ml/scripts/train_success_models.py \
  --csv /tmp/gradebook-mixed.csv \
  --label-col success_label \
  --out-dir services/ml/results/models/k12
```

Saved artifacts:
- `k12_success_default_gb.pkl`
- `k12_success_fast_lr.pkl`
- `k12_success_features.json`
- `k12_success_metadata.json`

## Integration
The API uses `K12SuccessPredictor` (`services/ml/k12_success_predictor.py`).
- Default model: gradient boosting
- Fast model: logistic regression
- Configure with `K12_MODEL_FLAVOR=default|fast`

The `/predict` endpoint returns:
- `risk_probability` (1 − success probability)
- `risk_level` and `risk_category` based on that risk value

## Evaluation
Use:
- `evaluate_model.py` for metrics
- `threshold_sweep.py` for best success threshold
- `compare_light_models.py` for model comparisons

## Notes
Because public datasets differ from real K‑12 environments, treat these metrics as directional.
Once real outcomes are available, replace the mixed dataset with real labeled data.
