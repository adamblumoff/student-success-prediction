#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DATA_DIR="${DATA_DIR:-$ROOT_DIR/data}"
SYNTH_ROWS="${SYNTH_ROWS:-5000}"
MIX_ROWS="${MIX_ROWS:-10000}"
SYNTH_SUCCESS_RATE="${SYNTH_SUCCESS_RATE:-0.5}"
SYNTH_LABEL_NOISE="${SYNTH_LABEL_NOISE:-0.08}"
SYNTH_FEATURE_NOISE="${SYNTH_FEATURE_NOISE:-0.03}"
MIX_FEATURE_NOISE="${MIX_FEATURE_NOISE:-0.03}"
MIX_DROPOUT_RATE="${MIX_DROPOUT_RATE:-0.05}"
SYNTH_FRAC="${SYNTH_FRAC:-0.5}"
OULAD_FRAC="${OULAD_FRAC:-0.3}"
UCI_FRAC="${UCI_FRAC:-0.2}"
MODEL_OUT_DIR="${MODEL_OUT_DIR:-$ROOT_DIR/results/models/k12}"

mkdir -p "$DATA_DIR"

echo "📥 Downloading public datasets (if missing)"
python3 "$ROOT_DIR/scripts/download_public_datasets.py" --dest-dir "$DATA_DIR"

echo "🧹 Preparing OULAD"
python3 "$ROOT_DIR/scripts/prepare_oulad.py" \
  --zip "$DATA_DIR/oulad.zip" \
  --out "$DATA_DIR/oulad_gradebook.csv"

echo "🧹 Preparing UCI student performance"
python3 "$ROOT_DIR/scripts/prepare_uci_student_performance.py" \
  --zip "$DATA_DIR/student-performance.zip" \
  --out "$DATA_DIR/uci_gradebook.csv"

echo "🧪 Generating synthetic gradebook"
python3 "$ROOT_DIR/scripts/generate_synthetic_gradebook.py" \
  --rows "$SYNTH_ROWS" \
  --target-success-rate "$SYNTH_SUCCESS_RATE" \
  --label-noise "$SYNTH_LABEL_NOISE" \
  --feature-noise "$SYNTH_FEATURE_NOISE" \
  --out "$DATA_DIR/gradebook-synth.csv" \
  --label-col success_label

echo "🧬 Building mixed dataset"
python3 "$ROOT_DIR/scripts/build_mixed_dataset.py" \
  --synthetic "$DATA_DIR/gradebook-synth.csv" \
  --oulad "$DATA_DIR/oulad_gradebook.csv" \
  --uci "$DATA_DIR/uci_gradebook.csv" \
  --out "$DATA_DIR/gradebook-mixed.csv" \
  --rows "$MIX_ROWS" \
  --synthetic-frac "$SYNTH_FRAC" \
  --oulad-frac "$OULAD_FRAC" \
  --uci-frac "$UCI_FRAC" \
  --feature-noise "$MIX_FEATURE_NOISE" \
  --dropout-rate "$MIX_DROPOUT_RATE"

echo "🏋️ Training success models"
python3 "$ROOT_DIR/scripts/train_success_models.py" \
  --csv "$DATA_DIR/gradebook-mixed.csv" \
  --label-col success_label \
  --out-dir "$MODEL_OUT_DIR"

echo "🚀 Starting ML service"
exec python3 -m uvicorn app:app --host 0.0.0.0 --port "${PORT:-9000}"
