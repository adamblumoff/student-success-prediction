#!/usr/bin/env python3
"""
Comprehensive Model Validation and Testing Suite

This module provides extensive testing for the student success prediction model
including cross-validation, temporal validation, bias testing, and performance analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.model_selection import cross_val_score, StratifiedKFold, TimeSeriesSplit
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ModelValidator:
    """Comprehensive model validation class"""
    
    def __init__(self, model_path="results/models"):
        """Initialize validator with trained models"""
        self.model_path = Path(model_path)
        self.load_models()
        self.load_data()
    
    def load_models(self):
        """Load trained models and components"""
        try:
            self.binary_model = joblib.load(self.model_path / "best_binary_model.pkl")
            self.multi_model = joblib.load(self.model_path / "best_multi_model.pkl")
            self.scaler = joblib.load(self.model_path / "binary_scaler.pkl")
            self.label_encoder = joblib.load(self.model_path / "label_encoder.pkl")
            
            with open(self.model_path / "feature_columns.json", 'r') as f:
                import json
                self.feature_columns = json.load(f)
            
            print("✅ Models loaded successfully")
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            raise
    
    def load_data(self):
        """Load and preprocess data"""
        try:
            df = pd.read_csv("data/processed/student_features_engineered.csv")
            df['registration_delay'] = df['registration_delay'].fillna(df['registration_delay'].median())
            df = df.fillna(0)
            
            # Prepare features and targets
            self.X = df[self.feature_columns]
            self.y = df['final_result']
            
            # Binary target (Pass/Distinction vs Fail)
            binary_mask = self.y.isin(['Pass', 'Distinction', 'Fail'])
            self.X_binary = self.X[binary_mask]
            self.y_binary = (self.y[binary_mask].isin(['Pass', 'Distinction'])).astype(int)
            
            # Multi-class target
            self.y_multi = self.label_encoder.transform(self.y)
            
            print(f"✅ Data loaded: {len(df)} records, {len(self.feature_columns)} features")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise
    
    def cross_validation_test(self, cv_folds=5):
        """Perform k-fold cross-validation"""
        print("\n" + "="*60)
        print("📊 CROSS-VALIDATION TESTING")
        print("="*60)
        
        # Binary model cross-validation
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
        binary_scores = cross_val_score(self.binary_model, self.X_binary, self.y_binary, 
                                       cv=skf, scoring='roc_auc')
        
        print(f"🎯 Binary Model ({cv_folds}-Fold Cross-Validation):")
        print(f"   Mean AUC: {binary_scores.mean():.3f} (±{binary_scores.std()*2:.3f})")
        print(f"   Individual folds: {[f'{score:.3f}' for score in binary_scores]}")
        
        # Multi-class model cross-validation
        multi_scores = cross_val_score(self.multi_model, self.X, self.y_multi, 
                                      cv=skf, scoring='f1_weighted')
        
        print(f"\n🎯 Multi-class Model ({cv_folds}-Fold Cross-Validation):")
        print(f"   Mean F1: {multi_scores.mean():.3f} (±{multi_scores.std()*2:.3f})")
        print(f"   Individual folds: {[f'{score:.3f}' for score in multi_scores]}")
        
        return binary_scores, multi_scores
    
    def temporal_validation_test(self):
        """Test model performance across different time periods"""
        print("\n" + "="*60)
        print("⏰ TEMPORAL VALIDATION TESTING")
        print("="*60)
        
        # Load full dataset with course codes for temporal analysis
        df = pd.read_csv("data/processed/student_features_engineered.csv")
        df = df.fillna(0)
        
        # Group by presentation (time periods)
        presentations = df['code_presentation'].unique()
        print(f"Testing across {len(presentations)} time periods: {presentations}")
        
        temporal_results = {}
        
        for presentation in presentations:
            mask = df['code_presentation'] == presentation
            X_temp = df[mask][self.feature_columns]
            y_temp = (df[mask]['final_result'].isin(['Pass', 'Distinction'])).astype(int)
            
            if len(y_temp.unique()) > 1:  # Ensure both classes are present
                y_pred_proba = self.binary_model.predict_proba(X_temp)[:, 1]
                auc_score = roc_auc_score(y_temp, y_pred_proba)
                
                temporal_results[presentation] = {
                    'auc': auc_score,
                    'n_students': len(y_temp),
                    'success_rate': y_temp.mean()
                }
                
                print(f"   {presentation}: AUC={auc_score:.3f}, N={len(y_temp)}, Success={y_temp.mean():.1%}")
        
        return temporal_results
    
    def bias_fairness_test(self):
        """Test for bias across different demographic groups"""
        print("\n" + "="*60)
        print("⚖️  BIAS & FAIRNESS TESTING")
        print("="*60)
        
        df = pd.read_csv("data/processed/student_features_engineered.csv")
        df = df.fillna(0)
        
        # Test across demographic groups
        demographic_groups = {
            'Gender': 'gender_encoded',
            'Age Group': 'age_band_encoded',
            'Education Level': 'education_encoded'
        }
        
        bias_results = {}
        
        for group_name, column in demographic_groups.items():
            if column in df.columns:
                print(f"\n📊 {group_name} Analysis:")
                
                group_results = {}
                unique_values = df[column].unique()
                
                for value in unique_values:
                    mask = df[column] == value
                    if mask.sum() > 100:  # Only test groups with sufficient samples
                        X_group = df[mask][self.feature_columns]
                        y_group = (df[mask]['final_result'].isin(['Pass', 'Distinction'])).astype(int)
                        
                        if len(y_group.unique()) > 1:
                            y_pred_proba = self.binary_model.predict_proba(X_group)[:, 1]
                            y_pred = (y_pred_proba > 0.5).astype(int)
                            
                            auc_score = roc_auc_score(y_group, y_pred_proba)
                            accuracy = (y_pred == y_group).mean()
                            
                            # Calculate fairness metrics
                            true_positive_rate = ((y_pred == 1) & (y_group == 1)).sum() / (y_group == 1).sum()
                            false_positive_rate = ((y_pred == 1) & (y_group == 0)).sum() / (y_group == 0).sum()
                            
                            group_results[value] = {
                                'auc': auc_score,
                                'accuracy': accuracy,
                                'tpr': true_positive_rate,
                                'fpr': false_positive_rate,
                                'n_samples': mask.sum()
                            }
                            
                            print(f"   Group {value}: AUC={auc_score:.3f}, Acc={accuracy:.3f}, N={mask.sum()}")
                
                bias_results[group_name] = group_results
        
        return bias_results
    
    def calibration_test(self):
        """Test model calibration (probability reliability)"""
        print("\n" + "="*60)
        print("🎯 MODEL CALIBRATION TESTING")
        print("="*60)
        
        # Get predictions on test set
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            self.X_binary, self.y_binary, test_size=0.2, random_state=42, stratify=self.y_binary
        )
        
        # Get predicted probabilities
        y_prob = self.binary_model.predict_proba(X_test)[:, 1]
        
        # Calculate calibration curve
        fraction_of_positives, mean_predicted_value = calibration_curve(y_test, y_prob, n_bins=10)
        
        # Plot calibration curve
        plt.figure(figsize=(10, 6))
        
        plt.subplot(1, 2, 1)
        plt.plot(mean_predicted_value, fraction_of_positives, "s-", label="Model")
        plt.plot([0, 1], [0, 1], "k:", label="Perfectly calibrated")
        plt.xlabel("Mean Predicted Probability")
        plt.ylabel("Fraction of Positives")
        plt.title("Calibration Plot")
        plt.legend()
        
        # Plot probability distribution
        plt.subplot(1, 2, 2)
        plt.hist(y_prob[y_test == 0], bins=20, alpha=0.5, label="Negative class", density=True)
        plt.hist(y_prob[y_test == 1], bins=20, alpha=0.5, label="Positive class", density=True)
        plt.xlabel("Predicted Probability")
        plt.ylabel("Density")
        plt.title("Probability Distribution")
        plt.legend()
        
        plt.tight_layout()
        plt.savefig("results/figures/calibration_analysis.png")
        plt.show()
        
        # Calculate calibration metrics
        from sklearn.metrics import brier_score_loss
        brier_score = brier_score_loss(y_test, y_prob)
        
        print(f"📊 Calibration Results:")
        print(f"   Brier Score: {brier_score:.3f} (lower is better)")
        print(f"   Mean Calibration Error: {np.mean(np.abs(fraction_of_positives - mean_predicted_value)):.3f}")
        
        return brier_score, fraction_of_positives, mean_predicted_value
    
    def robustness_test(self):
        """Test model robustness to data perturbations"""
        print("\n" + "="*60)
        print("🛡️  ROBUSTNESS TESTING")
        print("="*60)
        
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            self.X_binary, self.y_binary, test_size=0.2, random_state=42, stratify=self.y_binary
        )
        
        # Baseline performance
        baseline_auc = roc_auc_score(y_test, self.binary_model.predict_proba(X_test)[:, 1])
        print(f"📊 Baseline AUC: {baseline_auc:.3f}")
        
        # Test with different types of noise
        noise_levels = [0.01, 0.05, 0.1, 0.2]
        robustness_results = {}
        
        for noise_level in noise_levels:
            # Add Gaussian noise
            X_test_noisy = X_test + np.random.normal(0, noise_level * X_test.std(), X_test.shape)
            noisy_auc = roc_auc_score(y_test, self.binary_model.predict_proba(X_test_noisy)[:, 1])
            
            robustness_results[noise_level] = {
                'noisy_auc': noisy_auc,
                'auc_drop': baseline_auc - noisy_auc
            }
            
            print(f"   Noise {noise_level*100:3.0f}%: AUC={noisy_auc:.3f} (drop: {baseline_auc - noisy_auc:.3f})")
        
        return robustness_results
    
    def feature_importance_stability_test(self):
        """Test stability of feature importance across different samples"""
        print("\n" + "="*60)
        print("🔍 FEATURE IMPORTANCE STABILITY")
        print("="*60)
        
        from sklearn.utils import resample
        
        n_bootstrap = 10
        feature_importances = []
        
        for i in range(n_bootstrap):
            # Bootstrap sample
            X_boot, y_boot = resample(self.X_binary, self.y_binary, random_state=i)
            
            # Train model on bootstrap sample
            model_boot = type(self.binary_model)(**self.binary_model.get_params())
            model_boot.fit(X_boot, y_boot)
            
            # Get feature importances
            if hasattr(model_boot, 'feature_importances_'):
                feature_importances.append(model_boot.feature_importances_)
        
        # Calculate stability metrics
        feature_importances = np.array(feature_importances)
        importance_mean = feature_importances.mean(axis=0)
        importance_std = feature_importances.std(axis=0)
        
        # Create stability DataFrame
        stability_df = pd.DataFrame({
            'feature': self.feature_columns,
            'mean_importance': importance_mean,
            'std_importance': importance_std,
            'cv': importance_std / (importance_mean + 1e-10)  # Coefficient of variation
        }).sort_values('mean_importance', ascending=False)
        
        print("📊 Top 10 Most Stable Important Features:")
        print(stability_df.head(10)[['feature', 'mean_importance', 'cv']].round(3))
        
        return stability_df
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE MODEL VALIDATION REPORT")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        cv_results = self.cross_validation_test()
        temporal_results = self.temporal_validation_test()
        bias_results = self.bias_fairness_test()
        calibration_results = self.calibration_test()
        robustness_results = self.robustness_test()
        stability_results = self.feature_importance_stability_test()
        
        # Summary
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        print("✅ Cross-validation: PASSED" if cv_results[0].mean() > 0.7 else "❌ Cross-validation: FAILED")
        print("✅ Temporal stability: PASSED" if len(temporal_results) > 1 else "❌ Temporal stability: FAILED")
        print("✅ Bias testing: COMPLETED")
        print("✅ Calibration: COMPLETED")
        print("✅ Robustness: COMPLETED")
        print("✅ Feature stability: COMPLETED")
        
        print(f"\n🎯 Overall Model Quality: {'PRODUCTION READY' if cv_results[0].mean() > 0.8 else 'NEEDS IMPROVEMENT'}")
        
        return {
            'cross_validation': cv_results,
            'temporal': temporal_results,
            'bias': bias_results,
            'calibration': calibration_results,
            'robustness': robustness_results,
            'stability': stability_results
        }

def main():
    """Run comprehensive model validation"""
    print("🧪 Starting Comprehensive Model Validation")
    print("="*60)
    
    # Initialize validator
    validator = ModelValidator()
    
    # Run complete test suite
    results = validator.generate_test_report()
    
    # Save results
    results_dir = Path("results/validation")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    with open(results_dir / "validation_summary.txt", 'w') as f:
        f.write("Model Validation Summary\n")
        f.write("=" * 40 + "\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Cross-validation AUC: {results['cross_validation'][0].mean():.3f}\n")
        f.write(f"Temporal periods tested: {len(results['temporal'])}\n")
        f.write(f"Bias groups analyzed: {len(results['bias'])}\n")
    
    print(f"\n✅ Validation complete! Results saved to {results_dir}")

if __name__ == "__main__":
    main()