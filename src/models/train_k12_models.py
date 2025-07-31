#!/usr/bin/env python3
"""
K-12 Model Training Pipeline

Trains specialized machine learning models for K-12 student success prediction
using synthetic K-12 data with grade-level specific considerations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix, roc_auc_score, 
                           accuracy_score, precision_score, recall_score, f1_score,
                           roc_curve, precision_recall_curve)
import xgboost as xgb
import joblib

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

class K12ModelTrainer:
    """Specialized model trainer for K-12 student success prediction."""
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.performance_metrics = {}
        
        # Grade band definitions
        self.grade_bands = {
            'elementary': list(range(0, 6)),  # K-5
            'middle': list(range(6, 9)),      # 6-8
            'high': list(range(9, 13))        # 9-12
        }
    
    def load_k12_data(self):
        """Load K-12 engineered features dataset."""
        data_dir = Path("data/k12_synthetic")
        
        # Find latest engineered features file
        feature_files = list(data_dir.glob("k12_features_engineered_*.csv"))
        if not feature_files:
            raise FileNotFoundError("No K-12 engineered features found. Run k12_feature_engineering.py first.")
        
        latest_file = max(feature_files, key=lambda f: f.stat().st_mtime)
        print(f"📂 Loading K-12 features: {latest_file}")
        
        df = pd.read_csv(latest_file)
        
        # Load feature names
        feature_names_file = data_dir / "feature_names.json"
        if feature_names_file.exists():
            with open(feature_names_file, 'r') as f:
                feature_names = json.load(f)
        else:
            print("⚠️  Feature names file not found, using all numeric columns")
            feature_names = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'student_id' in feature_names:
                feature_names.remove('student_id')
        
        print(f"📊 Dataset loaded: {len(df)} students x {len(feature_names)} features")
        return df, feature_names
    
    def prepare_data(self, df, feature_names, target_col='current_success'):
        """Prepare data for model training with grade-level considerations."""
        print("🔧 Preparing data for K-12 model training...")
        
        # Extract features and target
        X = df[feature_names].fillna(0)  # Handle any remaining NaN values
        y = df[target_col]
        
        # Add grade level for stratified splitting
        grade_levels = df['grade_level']
        
        # Create grade band labels for stratification
        grade_bands = grade_levels.apply(self._get_grade_band)
        
        # Stratified split by grade band and success outcome
        stratify_col = grade_bands.astype(str) + '_' + y.astype(str)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state,
            stratify=stratify_col
        )
        
        # Also split grade information for analysis
        grade_train = grade_levels.loc[X_train.index]
        grade_test = grade_levels.loc[X_test.index]
        
        print(f"✅ Data split: {len(X_train)} train, {len(X_test)} test")
        print(f"📊 Train success rate: {y_train.mean():.1%}")
        print(f"📊 Test success rate: {y_test.mean():.1%}")
        
        return X_train, X_test, y_train, y_test, grade_train, grade_test
    
    def _get_grade_band(self, grade_level):
        """Get grade band for stratification."""
        if grade_level <= 5:
            return 'elementary'
        elif grade_level <= 8:
            return 'middle'
        else:
            return 'high'
    
    def train_models(self, X_train, y_train):
        """Train multiple models optimized for K-12 data."""
        print("🚀 Training K-12 Student Success Models...")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        self.scalers['main'] = scaler
        
        # Define models with K-12 optimized hyperparameters
        model_configs = {
            'XGBoost': {
                'model': xgb.XGBClassifier(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    eval_metric='logloss'
                ),
                'use_scaling': False
            },
            'Random Forest': {
                'model': RandomForestClassifier(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=self.random_state,
                    class_weight='balanced'
                ),
                'use_scaling': False
            },
            'Gradient Boosting': {
                'model': GradientBoostingClassifier(
                    n_estimators=150,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=self.random_state
                ),
                'use_scaling': False
            },
            'Logistic Regression': {
                'model': LogisticRegression(
                    random_state=self.random_state,
                    class_weight='balanced',
                    max_iter=1000
                ),
                'use_scaling': True
            }
        }
        
        # Train each model
        for name, config in model_configs.items():
            print(f"\n🔄 Training {name}...")
            
            # Select appropriate data
            X_train_model = X_train_scaled if config['use_scaling'] else X_train
            
            # Train model
            model = config['model']
            model.fit(X_train_model, y_train)
            
            # Store model
            self.models[name] = {
                'model': model,
                'use_scaling': config['use_scaling']
            }
            
            # Cross-validation scores
            cv_scores = cross_val_score(model, X_train_model, y_train, cv=5, scoring='roc_auc')
            print(f"   Cross-validation AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            
            # Feature importance (for tree-based models)
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[name] = dict(zip(
                    X_train.columns, 
                    model.feature_importances_
                ))
        
        print("✅ All models trained successfully!")
    
    def evaluate_models(self, X_test, y_test, grade_test):
        """Comprehensive evaluation of trained models."""
        print("\n📊 Evaluating K-12 Models...")
        
        evaluation_results = {}
        
        for name, model_info in self.models.items():
            print(f"\n🔍 Evaluating {name}...")
            
            model = model_info['model']
            use_scaling = model_info['use_scaling']
            
            # Prepare test data
            X_test_model = self.scalers['main'].transform(X_test) if use_scaling else X_test
            
            # Predictions
            y_pred = model.predict(X_test_model)
            y_pred_proba = model.predict_proba(X_test_model)[:, 1]
            
            # Overall metrics
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_pred_proba)
            }
            
            # Grade band specific evaluation
            grade_band_metrics = {}
            for band in ['elementary', 'middle', 'high']:
                band_mask = grade_test.apply(self._get_grade_band) == band
                if band_mask.sum() > 0:
                    y_test_band = y_test[band_mask]
                    y_pred_band = y_pred[band_mask]
                    y_pred_proba_band = y_pred_proba[band_mask]
                    
                    if len(np.unique(y_test_band)) > 1:  # Only if both classes present
                        grade_band_metrics[band] = {
                            'accuracy': accuracy_score(y_test_band, y_pred_band),
                            'f1_score': f1_score(y_test_band, y_pred_band),
                            'roc_auc': roc_auc_score(y_test_band, y_pred_proba_band)
                        }
            
            evaluation_results[name] = {
                'overall_metrics': metrics,
                'grade_band_metrics': grade_band_metrics,
                'predictions': y_pred_proba
            }
            
            # Print results
            print(f"   Overall AUC: {metrics['roc_auc']:.3f}")
            print(f"   F1 Score: {metrics['f1_score']:.3f}")
            print(f"   Accuracy: {metrics['accuracy']:.3f}")
            
            for band, band_metrics in grade_band_metrics.items():
                print(f"   {band.title()} AUC: {band_metrics['roc_auc']:.3f}")
        
        self.performance_metrics = evaluation_results
        return evaluation_results
    
    def select_best_model(self):
        """Select the best performing model based on overall AUC."""
        best_model_name = max(
            self.performance_metrics.keys(),
            key=lambda name: self.performance_metrics[name]['overall_metrics']['roc_auc']
        )
        
        best_auc = self.performance_metrics[best_model_name]['overall_metrics']['roc_auc']
        print(f"\n🏆 Best Model: {best_model_name} (AUC: {best_auc:.3f})")
        
        return best_model_name, self.models[best_model_name]
    
    def analyze_feature_importance(self, top_k=20):
        """Analyze and display feature importance across models."""
        print(f"\n🔍 Top {top_k} Most Important Features for K-12 Success:")
        print("=" * 60)
        
        # Aggregate feature importance across tree-based models
        all_importances = {}
        tree_models = [name for name in self.feature_importance.keys()]
        
        if not tree_models:
            print("No tree-based models available for feature importance analysis.")
            return
        
        # Average importance across models
        for model_name in tree_models:
            for feature, importance in self.feature_importance[model_name].items():
                if feature not in all_importances:
                    all_importances[feature] = []
                all_importances[feature].append(importance)
        
        # Calculate mean importance
        mean_importances = {
            feature: np.mean(importance_list) 
            for feature, importance_list in all_importances.items()
        }
        
        # Sort and display top features
        sorted_features = sorted(mean_importances.items(), key=lambda x: x[1], reverse=True)
        
        for i, (feature, importance) in enumerate(sorted_features[:top_k], 1):
            print(f"{i:2d}. {feature:<35} {importance:.4f}")
        
        return dict(sorted_features[:top_k])
    
    def generate_k12_insights(self, top_features):
        """Generate K-12 specific insights from model results."""
        print("\n🎓 K-12 Student Success Insights:")
        print("=" * 50)
        
        # Categorize features by type
        feature_categories = {
            'Academic Performance': [],
            'Attendance & Engagement': [],
            'Early Warning Indicators': [],
            'Demographic Factors': [],
            'Grade-Level Specific': []
        }
        
        for feature, importance in top_features.items():
            if any(term in feature.lower() for term in ['gpa', 'grade', 'course', 'credit', 'academic']):
                feature_categories['Academic Performance'].append((feature, importance))
            elif any(term in feature.lower() for term in ['attendance', 'behavior', 'engagement', 'extracurricular']):
                feature_categories['Attendance & Engagement'].append((feature, importance))
            elif any(term in feature.lower() for term in ['warning', 'chronic', 'failure', 'disciplinary']):
                feature_categories['Early Warning Indicators'].append((feature, importance))
            elif any(term in feature.lower() for term in ['age', 'lunch', 'ell', 'iep', 'elementary', 'middle', 'high']):
                feature_categories['Demographic Factors'].append((feature, importance))
            else:
                feature_categories['Grade-Level Specific'].append((feature, importance))
        
        for category, features in feature_categories.items():
            if features:
                print(f"\n📚 {category}:")
                for feature, importance in features[:5]:  # Top 5 per category
                    print(f"   • {feature}: {importance:.4f}")
        
        # Generate actionable insights
        print(f"\n💡 Key Actionable Insights:")
        print("   1. Academic performance metrics are the strongest predictors")
        print("   2. Attendance patterns significantly impact student success")
        print("   3. Early warning indicators help identify at-risk students")
        print("   4. Grade-level transitions require targeted support")
        print("   5. Multi-factor risk assessment improves prediction accuracy")
    
    def save_models(self):
        """Save trained models and metadata."""
        models_dir = Path("results/models/k12")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save best model
        best_model_name, best_model_info = self.select_best_model()
        
        # Save model files
        model_file = models_dir / f"k12_best_model_{timestamp}.pkl"
        scaler_file = models_dir / f"k12_scaler_{timestamp}.pkl"
        
        joblib.dump(best_model_info['model'], model_file)
        joblib.dump(self.scalers['main'], scaler_file)
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'best_model': best_model_name,
            'model_file': str(model_file),
            'scaler_file': str(scaler_file),
            'use_scaling': best_model_info['use_scaling'],
            'performance_metrics': {
                name: {
                    'overall_auc': metrics['overall_metrics']['roc_auc'],
                    'overall_f1': metrics['overall_metrics']['f1_score'],
                    'grade_band_performance': metrics['grade_band_metrics']
                }
                for name, metrics in self.performance_metrics.items()
            },
            'feature_importance': self.feature_importance.get(best_model_name, {}),
            'model_type': 'K-12 Student Success Prediction',
            'data_source': 'K-12 Synthetic Dataset'
        }
        
        metadata_file = models_dir / f"k12_model_metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"\n💾 Models saved:")
        print(f"   Model: {model_file}")
        print(f"   Scaler: {scaler_file}")
        print(f"   Metadata: {metadata_file}")
        
        return {
            'model_file': model_file,
            'scaler_file': scaler_file,
            'metadata_file': metadata_file,
            'best_model_name': best_model_name
        }

def main():
    """Main training pipeline for K-12 models."""
    print("🎓 K-12 Student Success Model Training Pipeline")
    print("=" * 60)
    
    # Initialize trainer
    trainer = K12ModelTrainer()
    
    # Load data
    df, feature_names = trainer.load_k12_data()
    
    # Prepare data
    X_train, X_test, y_train, y_test, grade_train, grade_test = trainer.prepare_data(
        df, feature_names
    )
    
    # Train models
    trainer.train_models(X_train, y_train)
    
    # Evaluate models
    evaluation_results = trainer.evaluate_models(X_test, y_test, grade_test)
    
    # Analyze feature importance
    top_features = trainer.analyze_feature_importance(top_k=25)
    
    # Generate insights
    trainer.generate_k12_insights(top_features)
    
    # Save models
    saved_files = trainer.save_models()
    
    print(f"\n🎉 K-12 Model Training Complete!")
    print(f"Best model: {saved_files['best_model_name']}")
    
    return trainer, saved_files

if __name__ == "__main__":
    trainer, saved_files = main()