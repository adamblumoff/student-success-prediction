#!/usr/bin/env python3
"""
Predictive Modeling for Student Success

This script builds machine learning models to predict student outcomes using the 
engineered features from the OULAD dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import joblib
import json

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

def load_data():
    """Load the engineered features"""
    data_dir = Path("data/processed")
    df = pd.read_csv(data_dir / "student_features_engineered.csv")
    
    print(f"Loaded {len(df)} records with {len(df.columns)} columns")
    print(f"Target distribution:")
    print(df['final_result'].value_counts())
    print(f"Success rate: {(df['final_result'].isin(['Pass', 'Distinction']).sum() / len(df) * 100):.1f}%")
    
    return df

def preprocess_data(df):
    """Preprocess data for modeling"""
    # Handle missing values
    df['registration_delay'] = df['registration_delay'].fillna(df['registration_delay'].median())
    df = df.fillna(0)
    
    # Prepare features and target
    feature_columns = [col for col in df.columns if col not in ['id_student', 'code_module', 'code_presentation', 'final_result']]
    X = df[feature_columns]
    y = df['final_result']
    
    return X, y, feature_columns

def train_binary_models(X, y, feature_columns):
    """Train binary classification models (Pass vs Fail)"""
    print("=== BINARY CLASSIFICATION (Pass vs Fail) ===")
    
    # Create binary dataset (exclude withdrawn)
    binary_mask = y.isin(['Pass', 'Distinction', 'Fail'])
    X_binary = X[binary_mask]
    y_binary = y[binary_mask]
    y_binary = (y_binary.isin(['Pass', 'Distinction'])).astype(int)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_binary, y_binary, test_size=0.2, random_state=42, stratify=y_binary
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train models
    models = {
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBClassifier(random_state=42, eval_metric='logloss'),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"Training {name}...")
        
        if name == 'Logistic Regression':
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)
        
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc,
            'model': model
        }
        
        print(f"  Accuracy: {accuracy:.3f}")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall: {recall:.3f}")
        print(f"  F1-Score: {f1:.3f}")
        print(f"  AUC: {auc:.3f}")
        print()
    
    # Find best model
    best_model = max(results.items(), key=lambda x: x[1]['auc'])
    print(f"🏆 Best binary model: {best_model[0]} (AUC: {best_model[1]['auc']:.3f})")
    
    return results, best_model, scaler, X_test, y_test

def train_multiclass_models(X, y, feature_columns):
    """Train multi-class classification models"""
    print("\\n=== MULTI-CLASS CLASSIFICATION ===")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train models
    models = {
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000, multi_class='ovr'),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'XGBoost': xgb.XGBClassifier(random_state=42, eval_metric='mlogloss'),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"Training {name}...")
        
        if name == 'Logistic Regression':
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'model': model
        }
        
        print(f"  Accuracy: {accuracy:.3f}")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall: {recall:.3f}")
        print(f"  F1-Score: {f1:.3f}")
        print()
    
    # Find best model
    best_model = max(results.items(), key=lambda x: x[1]['f1'])
    print(f"🏆 Best multi-class model: {best_model[0]} (F1: {best_model[1]['f1']:.3f})")
    
    return results, best_model, label_encoder, scaler

def get_feature_importance(model, feature_names):
    """Extract feature importance from trained model"""
    if hasattr(model, 'feature_importances_'):
        return pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
    elif hasattr(model, 'coef_'):
        if len(model.coef_.shape) == 1:
            coef = model.coef_
        else:
            coef = np.mean(np.abs(model.coef_), axis=0)
        return pd.DataFrame({
            'feature': feature_names,
            'importance': np.abs(coef)
        }).sort_values('importance', ascending=False)
    else:
        return None

def create_early_warning_system(model, scaler, X_test, threshold=0.5):
    """Create early warning system for at-risk students"""
    
    # Prepare data
    if scaler is not None:
        X_test_scaled = scaler.transform(X_test)
        risk_proba = model.predict_proba(X_test_scaled)[:, 1]
    else:
        risk_proba = model.predict_proba(X_test)[:, 1]
    
    # Calculate risk scores
    risk_score = 1 - risk_proba
    
    # Assign risk categories
    risk_category = pd.cut(risk_score, 
                          bins=[0, 0.3, 0.6, 1.0], 
                          labels=['Low Risk', 'Medium Risk', 'High Risk'])
    
    results = pd.DataFrame({
        'success_probability': risk_proba,
        'risk_score': risk_score,
        'risk_category': risk_category,
        'needs_intervention': risk_score > threshold
    })
    
    return results

def save_models(binary_results, multi_results, binary_scaler, multi_scaler, label_encoder, feature_columns):
    """Save trained models and results"""
    
    # Create models directory
    models_dir = Path("results/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Get best models
    best_binary = max(binary_results.items(), key=lambda x: x[1]['auc'])
    best_multi = max(multi_results.items(), key=lambda x: x[1]['f1'])
    
    # Save models
    joblib.dump(best_binary[1]['model'], models_dir / "best_binary_model.pkl")
    joblib.dump(best_multi[1]['model'], models_dir / "best_multi_model.pkl")
    joblib.dump(binary_scaler, models_dir / "binary_scaler.pkl")
    joblib.dump(multi_scaler, models_dir / "multi_scaler.pkl")
    joblib.dump(label_encoder, models_dir / "label_encoder.pkl")
    
    # Save feature columns
    with open(models_dir / "feature_columns.json", 'w') as f:
        json.dump(feature_columns, f)
    
    # Save metadata
    model_metadata = {
        'best_binary_model': {
            'name': best_binary[0],
            'metrics': {k: v for k, v in best_binary[1].items() if k != 'model'}
        },
        'best_multi_model': {
            'name': best_multi[0],
            'metrics': {k: v for k, v in best_multi[1].items() if k != 'model'}
        },
        'feature_count': len(feature_columns)
    }
    
    with open(models_dir / "model_metadata.json", 'w') as f:
        json.dump(model_metadata, f, indent=2)
    
    print(f"✅ Models saved to {models_dir}")
    return best_binary, best_multi

def main():
    """Main training pipeline"""
    print("🚀 Starting Student Success Prediction Model Training")
    print("=" * 60)
    
    # Load and preprocess data
    df = load_data()
    X, y, feature_columns = preprocess_data(df)
    
    print(f"\\nFeatures: {len(feature_columns)}")
    print(f"Records: {len(X)}")
    
    # Train binary models
    binary_results, best_binary, binary_scaler, X_test_bin, y_test_bin = train_binary_models(X, y, feature_columns)
    
    # Train multi-class models
    multi_results, best_multi, label_encoder, multi_scaler = train_multiclass_models(X, y, feature_columns)
    
    # Feature importance analysis
    print("\\n=== FEATURE IMPORTANCE ANALYSIS ===")
    importance = get_feature_importance(best_binary[1]['model'], feature_columns)
    if importance is not None:
        print("Top 10 most important features:")
        print(importance.head(10))
    
    # Early warning system
    print("\\n=== EARLY WARNING SYSTEM ===")
    risk_assessment = create_early_warning_system(
        best_binary[1]['model'], 
        binary_scaler if best_binary[0] == 'Logistic Regression' else None,
        X_test_bin
    )
    
    print(f"Risk distribution:")
    print(risk_assessment['risk_category'].value_counts())
    print(f"Students needing intervention: {risk_assessment['needs_intervention'].sum()}/{len(risk_assessment)}")
    
    # Save models
    save_models(binary_results, multi_results, binary_scaler, multi_scaler, label_encoder, feature_columns)
    
    print("\\n🎯 Training completed successfully!")
    print("📊 Models ready for deployment")
    print("📱 Next: Create intervention system and dashboard")

if __name__ == "__main__":
    main()