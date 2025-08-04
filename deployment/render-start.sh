#!/bin/bash
# Render.com startup script for Student Success Predictor

echo "🚀 Starting Student Success Predictor on Render.com"

# Set model paths for production (models are in project root, not src)
export MODELS_DIR="/opt/render/project/results/models"
export K12_MODELS_DIR="/opt/render/project/results/models/k12"

# Train models if they don't exist
echo "🤖 Checking for trained models..."
if [ ! -f "$MODELS_DIR/best_binary_model.pkl" ]; then
    echo "📚 Models not found - training models for production..."
    cd /opt/render/project
    
    # Create results directory structure
    mkdir -p results/models
    mkdir -p results/models/k12
    
    # Train the original models (required for intervention system)
    echo "🔬 Training original OULAD models..."
    timeout 300 python3 src/models/train_models.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Original models trained successfully"
        
        # Train K-12 models (optional but recommended)
        echo "🎓 Training K-12 models..."
        timeout 300 python3 src/models/train_k12_models.py || echo "⚠️  K-12 training skipped (non-critical)"
        
        echo "✅ Model training completed"
    else
        echo "❌ Model training failed or timed out"
        echo "🚀 Attempting to start with minimal model fallback..."
        # The app will use fallback models or graceful degradation
    fi
else
    echo "✅ Models found - skipping training"
fi

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

# Start the application - ensure we're in the right directory
cd /opt/render/project/src
echo "📁 Changed to directory: $(pwd)"
echo "📁 Looking for app.py:"
ls -la app.py 2>/dev/null || echo "❌ app.py not found in $(pwd)"
ls -la ../app.py 2>/dev/null && echo "✅ Found app.py in parent directory"

# Try to run from the correct location
if [ -f "../app.py" ]; then
    echo "🚀 Starting app.py from parent directory"
    cd /opt/render/project
    python3 app.py
elif [ -f "app.py" ]; then
    echo "🚀 Starting app.py from current directory"
    python3 app.py
else
    echo "❌ Cannot find app.py in current or parent directory"
    echo "📁 Directory contents:"
    ls -la
    exit 1
fi