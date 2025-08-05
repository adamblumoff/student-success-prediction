#!/bin/bash
# Render.com startup script for Student Success Predictor

echo "🚀 Starting Student Success Predictor on Render.com"

# Set model paths for production (models are in project root, not src)
export MODELS_DIR="/opt/render/project/results/models"
export K12_MODELS_DIR="/opt/render/project/results/models/k12"

# Train models if they don't exist
echo "🤖 Checking for trained models..."
if [ ! -f "$MODELS_DIR/best_binary_model.pkl" ]; then
    echo "📚 Models not found - generating and training models for production..."
    cd /opt/render/project
    
    # Create results directory structure
    mkdir -p results/models
    mkdir -p results/models/k12
    mkdir -p data/processed
    
    # Set up Python path and verify files exist
    export PYTHONPATH="/opt/render/project:$PYTHONPATH"
    echo "🔍 Python path: $PYTHONPATH"
    echo "🔍 Current directory: $(pwd)"
    echo "🔍 Checking for training scripts..."
    
    if [ -f "src/models/train_models.py" ]; then
        echo "✅ Found src/models/train_models.py"
    else
        echo "❌ src/models/train_models.py not found"
        echo "📁 Contents of src/:"
        ls -la src/ 2>/dev/null || echo "src directory not found"
        echo "📁 Contents of src/models/:"
        ls -la src/models/ 2>/dev/null || echo "src/models directory not found"
    fi
    
    # Generate synthetic data first (since OULAD data may not be available)
    echo "🎲 Generating synthetic dataset for training..."
    cd /opt/render/project
    timeout 300 python3 -c "
import sys
sys.path.append('/opt/render/project')
try:
    from src.models.k12_data_generator import K12DataGenerator
    generator = K12DataGenerator()
    print('📊 Generating synthetic dataset...')
    df = generator.generate_dataset(student_count=5000)
    df.to_csv('data/processed/student_features_engineered.csv', index=False)
    print('✅ Synthetic dataset generated successfully')
except Exception as e:
    print(f'❌ Synthetic data generation failed: {e}')
    # Create minimal dataset for basic functionality
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    minimal_df = pd.DataFrame({
        'id_student': range(1, 101),
        'final_result': np.random.choice(['Pass', 'Fail', 'Distinction', 'Withdrawn'], 100),
        'gender_encoded': np.random.randint(0, 2, 100),
        'region_encoded': np.random.randint(0, 4, 100),
        'age_band_encoded': np.random.randint(0, 3, 100),
        'education_encoded': np.random.randint(0, 4, 100),
        'is_male': np.random.randint(0, 2, 100),
        'has_disability': np.random.randint(0, 2, 100),
        'studied_credits': np.random.randint(30, 180, 100),
        'num_of_prev_attempts': np.random.randint(0, 5, 100),
        'registration_delay': np.random.randint(0, 20, 100),
        'unregistered': np.random.randint(0, 2, 100)
    })
    # Add remaining required features with random values
    for i in range(20):  # Add 20 more features to reach ~31 total
        minimal_df[f'feature_{i}'] = np.random.normal(0.5, 0.2, 100)
    minimal_df.to_csv('data/processed/student_features_engineered.csv', index=False)
    print('✅ Minimal fallback dataset created')
"
    
    # Train the original models (required for intervention system)
    echo "🔬 Training original OULAD models..."
    cd /opt/render/project
    timeout 300 python3 -m src.models.train_models
    
    if [ $? -eq 0 ]; then
        echo "✅ Original models trained successfully"
        
        # Train K-12 models (optional but recommended)
        echo "🎓 Training K-12 models..."
        timeout 300 python3 -m src.models.train_k12_models || echo "⚠️  K-12 training skipped (non-critical)"
        
        echo "✅ Model training completed"
    else
        echo "❌ Model training failed or timed out - trying alternative approach..."
        echo "🔬 Attempting direct script execution..."
        cd /opt/render/project
        timeout 300 python3 src/models/train_models.py
        
        if [ $? -eq 0 ]; then
            echo "✅ Models trained with direct execution"
        else
            echo "❌ All training approaches failed"
            echo "🚀 Starting with fallback model handling..."
        fi
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
cd /opt/render/project
echo "📁 Changed to directory: $(pwd)"
echo "📁 Looking for startup files:"
ls -la run_mvp.py 2>/dev/null && echo "✅ Found run_mvp.py" || echo "❌ run_mvp.py not found"
ls -la app.py 2>/dev/null && echo "✅ Found app.py" || echo "❌ app.py not found"

# Try to run from the correct location (prefer run_mvp.py)
if [ -f "run_mvp.py" ]; then
    echo "🚀 Starting MVP application with run_mvp.py"
    python3 run_mvp.py
elif [ -f "app.py" ]; then
    echo "🚀 Starting application with app.py"
    python3 app.py
else
    echo "❌ Cannot find run_mvp.py or app.py in $(pwd)"
    echo "📁 Directory contents:"
    ls -la | head -10
    exit 1
fi