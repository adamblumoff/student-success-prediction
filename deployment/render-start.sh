#!/bin/bash
# Render.com startup script for Student Success Predictor

echo "🚀 Starting Student Success Predictor on Render.com"

# Set model paths for production (models are in project root, not in src)
export MODELS_DIR="/opt/render/project/results/models"
export K12_MODELS_DIR="/opt/render/project/results/models/k12"

# Debug: Show current directory and model files
echo "📁 Current directory: $(pwd)"
echo "📁 Project structure:"
ls -la /opt/render/project/ 2>/dev/null | head -10
echo "📁 Results directory:"
ls -la /opt/render/project/results/ 2>/dev/null | head -10
echo "📁 Looking for model files:"
find /opt/render/project -name "*.pkl" -type f 2>/dev/null | head -10

# Debug: Show environment
echo "🔍 MODELS_DIR: $MODELS_DIR"
echo "🔍 K12_MODELS_DIR: $K12_MODELS_DIR"
echo "🔍 Models directory exists: $(test -d "$MODELS_DIR" && echo "YES" || echo "NO")"
echo "🔍 K12 models directory exists: $(test -d "$K12_MODELS_DIR" && echo "YES" || echo "NO")"
if [ -d "$MODELS_DIR" ]; then
    echo "🔍 Files in models directory:"
    ls -la "$MODELS_DIR" 2>/dev/null
fi

# Start the application
cd /opt/render/project
python3 app.py