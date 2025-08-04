#!/bin/bash
# Render.com startup script for Student Success Predictor

echo "🚀 Starting Student Success Predictor on Render.com"

# Set model paths for production
export MODELS_DIR="/opt/render/project/src/results/models"
export K12_MODELS_DIR="/opt/render/project/src/results/models/k12"

# Debug: Show current directory and model files
echo "📁 Current directory: $(pwd)"
echo "📁 Listing project files:"
find /opt/render/project -name "*.pkl" -type f 2>/dev/null | head -10

# Debug: Show environment
echo "🔍 MODELS_DIR: $MODELS_DIR"
echo "🔍 K12_MODELS_DIR: $K12_MODELS_DIR"
echo "🔍 Models directory exists: $(test -d "$MODELS_DIR" && echo "YES" || echo "NO")"

# Start the application
cd /opt/render/project
python3 run_mvp.py