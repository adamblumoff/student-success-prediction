#!/usr/bin/env python3
"""
K-12 Feature Engineering Pipeline

Transforms raw K-12 student data into ML-ready features optimized for 
student success prediction in elementary, middle, and high school contexts.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings('ignore')

class K12FeatureEngineer:
    """Feature engineering pipeline specifically designed for K-12 data."""
    
    def __init__(self):
        self.grade_bands = {
            'elementary': list(range(0, 6)),  # K-5
            'middle': list(range(6, 9)),      # 6-8  
            'high': list(range(9, 13))        # 9-12
        }
        
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
    
    def create_demographic_features(self, df):
        """Create demographic and socioeconomic features."""
        features = df.copy()
        
        # Grade band encoding
        features['grade_band'] = features['grade_level'].apply(self._get_grade_band)
        features['is_elementary'] = (features['grade_level'] <= 5).astype(int)
        features['is_middle_school'] = ((features['grade_level'] >= 6) & (features['grade_level'] <= 8)).astype(int)
        features['is_high_school'] = (features['grade_level'] >= 9).astype(int)
        
        # Age-grade alignment (key early warning indicator)
        features['expected_age'] = 5 + features['grade_level']
        features['age_grade_diff'] = features['age'] - features['expected_age']
        features['over_age_for_grade'] = (features['age_grade_diff'] > 0.5).astype(int)
        features['under_age_for_grade'] = (features['age_grade_diff'] < -0.5).astype(int)
        
        # Gender encoding
        features['is_male'] = (features['gender'] == 'M').astype(int)
        features['is_female'] = (features['gender'] == 'F').astype(int)
        
        # Socioeconomic risk factors
        features['socioeconomic_risk_score'] = (
            features['free_reduced_lunch'] * 0.4 +
            features['ell_status'] * 0.3 +
            features['iep_status'] * 0.2 +
            features['section_504'] * 0.1
        )
        
        # Special populations compound risk
        features['multiple_risk_factors'] = (
            features['free_reduced_lunch'] + 
            features['ell_status'] + 
            features['iep_status']
        )
        features['high_needs_student'] = (features['multiple_risk_factors'] >= 2).astype(int)
        
        # Protective factors
        features['has_protective_factors'] = features['gifted_program'].astype(int)
        
        return features
    
    def create_academic_features(self, df):
        """Create academic performance and trajectory features."""
        features = df.copy()
        
        # GPA analysis
        features['gpa_normalized'] = features['current_gpa'] / 4.0  # Normalize to 0-1
        
        # Grade-specific GPA expectations
        features['gpa_below_grade_expectation'] = 0
        for grade in range(13):
            grade_mask = features['grade_level'] == grade
            if grade <= 5:  # Elementary
                threshold = 3.0
            elif grade <= 8:  # Middle
                threshold = 2.8
            else:  # High school
                threshold = 2.5
            
            features.loc[grade_mask, 'gpa_below_grade_expectation'] = (
                features.loc[grade_mask, 'current_gpa'] < threshold
            ).astype(int)
        
        # GPA trajectory features
        features['gpa_trend_positive'] = (features['gpa_trend'] > 0.1).astype(int)
        features['gpa_trend_negative'] = (features['gpa_trend'] < -0.1).astype(int)
        features['gpa_trend_stable'] = (abs(features['gpa_trend']) <= 0.1).astype(int)
        
        # Course failure analysis
        features['has_course_failures'] = (features['course_failures_total'] > 0).astype(int)
        features['multiple_course_failures'] = (features['course_failures_total'] > 1).astype(int)
        features['failure_rate'] = features['course_failures_total'] / np.maximum(1, features['years_data_available'])
        
        # Grade retention (critical early warning indicator)
        features['retention_risk_multiplier'] = np.where(features['grade_retained_ever'], 2.0, 1.0)
        
        # Credit accumulation (high school specific)
        features['credits_on_track'] = 0
        features['credits_behind'] = 0
        
        high_school_mask = features['grade_level'] >= 9
        if high_school_mask.any():
            expected_credits = (features.loc[high_school_mask, 'grade_level'] - 8) * 6  # ~6 credits per year
            features.loc[high_school_mask, 'credits_on_track'] = (
                features.loc[high_school_mask, 'credits_earned'] >= expected_credits * 0.9
            ).astype(int)
            features.loc[high_school_mask, 'credits_behind'] = np.maximum(
                0, expected_credits - features.loc[high_school_mask, 'credits_earned']
            )
        
        # Subject-specific performance (if available)
        subject_cols = ['recent_Reading_Grade', 'recent_Math_Grade', 'recent_Science_Grade']
        available_subjects = [col for col in subject_cols if col in features.columns]
        
        if available_subjects:
            features['core_subject_avg'] = features[available_subjects].mean(axis=1)
            features['core_subject_min'] = features[available_subjects].min(axis=1)
            features['subject_performance_gap'] = (
                features[available_subjects].max(axis=1) - features[available_subjects].min(axis=1)
            )
            
            # Math/Reading specific (critical for early grades)
            if 'recent_Reading_Grade' in features.columns:
                features['reading_below_proficient'] = (features['recent_Reading_Grade'] < 2.5).astype(int)
            if 'recent_Math_Grade' in features.columns:
                features['math_below_proficient'] = (features['recent_Math_Grade'] < 2.5).astype(int)
        
        return features
    
    def create_engagement_features(self, df):
        """Create student engagement and behavioral features."""
        features = df.copy()
        
        # Attendance analysis (strongest predictor)
        features['attendance_excellent'] = (features['attendance_rate'] >= 0.96).astype(int)
        features['attendance_good'] = ((features['attendance_rate'] >= 0.90) & 
                                     (features['attendance_rate'] < 0.96)).astype(int)
        features['attendance_concerning'] = ((features['attendance_rate'] >= 0.80) & 
                                           (features['attendance_rate'] < 0.90)).astype(int)
        features['attendance_critical'] = (features['attendance_rate'] < 0.80).astype(int)
        
        # Chronic absenteeism (federal definition: missing 10%+ of school days)
        features['chronic_absenteeism_severe'] = (features['attendance_rate'] < 0.85).astype(int)
        
        # Tardiness patterns
        features['tardiness_minimal'] = (features['tardiness_rate'] < 0.02).astype(int)
        features['tardiness_concerning'] = (features['tardiness_rate'] >= 0.05).astype(int)
        
        # Behavioral analysis
        features['behavior_excellent'] = (features['behavior_score'] >= 0.95).astype(int)
        features['behavior_concerning'] = (features['behavior_score'] < 0.80).astype(int)
        
        # Disciplinary patterns
        features['has_disciplinary_issues'] = (features['disciplinary_incidents'] > 0).astype(int)
        features['multiple_disciplinary_issues'] = (features['disciplinary_incidents'] > 2).astype(int)
        features['has_suspensions'] = (features['suspensions'] > 0).astype(int)
        
        # Engagement level composite
        features['engagement_composite'] = (
            features['attendance_rate'] * 0.4 +
            features['behavior_score'] * 0.3 +
            (1 - features['chronic_absenteeism']) * 0.2 +
            (features['extracurricular_count'] / 3) * 0.1  # Cap at 3 activities
        )
        
        # Extracurricular engagement (protective factor)
        features['no_extracurriculars'] = (features['extracurricular_count'] == 0).astype(int)
        features['multiple_extracurriculars'] = (features['extracurricular_count'] >= 2).astype(int)
        
        # Parent engagement (critical for K-12 success)
        features['low_parent_engagement'] = (features['parent_engagement_level'] == 0).astype(int)
        features['high_parent_engagement'] = (features['parent_engagement_level'] >= 2).astype(int)
        
        # Technology access (increasingly important)
        features['digital_divide_risk'] = (1 - features['technology_access']).astype(int)
        
        return features
    
    def create_early_warning_features(self, df):
        """Create early warning indicator features based on K-12 research."""
        features = df.copy()
        
        # ABC's of Early Warning (Attendance, Behavior, Course Performance)
        features['early_warning_attendance'] = features['chronic_absenteeism'].astype(int)
        features['early_warning_behavior'] = (features['disciplinary_incidents'] > 0).astype(int)
        features['early_warning_course'] = (features['course_failures_total'] > 0).astype(int)
        
        # Early Warning Composite Score
        features['early_warning_score'] = (
            features['early_warning_attendance'] +
            features['early_warning_behavior'] +
            features['early_warning_course']
        )
        
        # Grade-specific early warning indicators
        features['grade_specific_warning'] = 0
        
        # Elementary: Reading by 3rd grade
        grade_3_mask = features['grade_level'] == 3
        if grade_3_mask.any() and 'reading_below_proficient' in features.columns:
            features.loc[grade_3_mask, 'grade_specific_warning'] = features.loc[
                grade_3_mask, 'reading_below_proficient'
            ]
        
        # Middle school: Course failures and engagement drop
        middle_mask = (features['grade_level'] >= 6) & (features['grade_level'] <= 8)
        if middle_mask.any():
            features.loc[middle_mask, 'grade_specific_warning'] = (
                (features.loc[middle_mask, 'course_failures_total'] > 0) |
                (features.loc[middle_mask, 'attendance_rate'] < 0.90) |
                (features.loc[middle_mask, 'current_gpa'] < 2.5)
            ).astype(int)
        
        # High school: Credit accumulation
        high_mask = features['grade_level'] >= 9
        if high_mask.any():
            features.loc[high_mask, 'grade_specific_warning'] = (
                1 - features.loc[high_mask, 'credits_on_track']
            )
        
        # Compound risk indicators
        features['multiple_risk_indicators'] = (
            features['socioeconomic_risk_score'] > 0.3
        ).astype(int) + features['early_warning_score']
        
        features['high_risk_student'] = (features['multiple_risk_indicators'] >= 3).astype(int)
        
        return features
    
    def create_grade_band_features(self, df):
        """Create grade-band specific features."""
        features = df.copy()
        
        # Elementary-specific features (K-5)
        elementary_mask = features['grade_level'] <= 5
        features['elementary_reading_focus'] = 0
        features['elementary_foundational_skills'] = 0
        
        if elementary_mask.any():
            # Reading proficiency by grade 3 (critical milestone)
            features.loc[elementary_mask, 'elementary_reading_focus'] = (
                features.loc[elementary_mask, 'grade_level'] <= 3
            ).astype(int)
            
            # Foundational skills mastery
            if 'core_subject_avg' in features.columns:
                features.loc[elementary_mask, 'elementary_foundational_skills'] = (
                    features.loc[elementary_mask, 'core_subject_avg'] >= 3.0
                ).astype(int)
        
        # Middle school-specific features (6-8)
        middle_mask = (features['grade_level'] >= 6) & (features['grade_level'] <= 8)
        features['middle_school_transition'] = 0
        features['middle_school_engagement_drop'] = 0
        
        if middle_mask.any():
            # 6th grade transition challenge
            features.loc[features['grade_level'] == 6, 'middle_school_transition'] = 1
            
            # Engagement drop identification
            features.loc[middle_mask, 'middle_school_engagement_drop'] = (
                (features.loc[middle_mask, 'attendance_rate'] < 0.90) |
                (features.loc[middle_mask, 'behavior_score'] < 0.85) |
                (features.loc[middle_mask, 'no_extracurriculars'] == 1)
            ).astype(int)
        
        # High school-specific features (9-12)
        high_mask = features['grade_level'] >= 9
        features['freshman_transition'] = 0
        features['graduation_track'] = 0
        features['college_career_ready'] = 0
        
        if high_mask.any():
            # 9th grade transition (critical year)
            features.loc[features['grade_level'] == 9, 'freshman_transition'] = 1
            
            # Graduation tracking
            features.loc[high_mask, 'graduation_track'] = features.loc[high_mask, 'credits_on_track']
            
            # College/career readiness indicators
            features.loc[high_mask, 'college_career_ready'] = (
                (features.loc[high_mask, 'current_gpa'] >= 3.0) &
                (features.loc[high_mask, 'credits_on_track'] == 1) &
                (features.loc[high_mask, 'attendance_rate'] >= 0.90)
            ).astype(int)
        
        return features
    
    def _get_grade_band(self, grade_level):
        """Determine grade band for a given grade level."""
        if grade_level <= 5:
            return 'elementary'
        elif grade_level <= 8:
            return 'middle'
        else:
            return 'high'
    
    def fit_transform(self, df, target_column='current_success'):
        """Fit feature engineering pipeline and transform data."""
        print("🔧 Starting K-12 Feature Engineering...")
        
        # Apply all feature engineering steps
        features = self.create_demographic_features(df)
        print("✅ Demographic features created")
        
        features = self.create_academic_features(features)
        print("✅ Academic features created")
        
        features = self.create_engagement_features(features)
        print("✅ Engagement features created")
        
        features = self.create_early_warning_features(features)
        print("✅ Early warning features created")
        
        features = self.create_grade_band_features(features)
        print("✅ Grade-band specific features created")
        
        # Select feature columns (exclude ID and raw categorical columns)
        exclude_cols = [
            'student_id', 'gender', 'race_ethnicity', 'grade_band',
            target_column, 'risk_category', 'next_grade_success_pred',
            'graduation_prediction', 'success_probability', 'next_grade_success_prob',
            'graduation_probability'
        ]
        
        # Include subject grades if they exist
        subject_cols = [col for col in features.columns if col.startswith('recent_') and col.endswith('_Grade')]
        exclude_cols.extend(subject_cols)
        
        feature_cols = [col for col in features.columns if col not in exclude_cols]
        
        X = features[feature_cols]
        y = features[target_column] if target_column in features.columns else None
        
        # Handle missing values
        imputer = SimpleImputer(strategy='mean')
        X_imputed = pd.DataFrame(
            imputer.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
        
        # Store feature names for later use
        self.feature_names = list(X_imputed.columns)
        
        print(f"✅ Feature engineering complete!")
        print(f"📊 Features created: {len(self.feature_names)}")
        print(f"🎯 Target variable: {target_column}")
        
        # Display feature summary
        self._display_feature_summary(X_imputed)
        
        return X_imputed, y, features
    
    def _display_feature_summary(self, X):
        """Display summary of engineered features."""
        print(f"\n📋 Feature Engineering Summary:")
        print("=" * 50)
        
        feature_categories = {
            'Demographic': [f for f in X.columns if any(term in f.lower() for term in ['age', 'grade', 'male', 'female', 'elementary', 'middle', 'high'])],
            'Socioeconomic': [f for f in X.columns if any(term in f.lower() for term in ['lunch', 'ell', 'iep', '504', 'socioeconomic', 'risk'])],
            'Academic': [f for f in X.columns if any(term in f.lower() for term in ['gpa', 'course', 'failure', 'credit', 'subject', 'reading', 'math'])],
            'Engagement': [f for f in X.columns if any(term in f.lower() for term in ['attendance', 'behavior', 'extracurricular', 'parent', 'engagement'])],
            'Early Warning': [f for f in X.columns if any(term in f.lower() for term in ['warning', 'chronic', 'disciplinary', 'suspension'])],
            'Grade-Specific': [f for f in X.columns if any(term in f.lower() for term in ['transition', 'foundational', 'graduation', 'college'])]
        }
        
        for category, features in feature_categories.items():
            if features:
                print(f"\n{category} Features ({len(features)}):")
                for feature in features[:5]:  # Show first 5
                    print(f"  - {feature}")
                if len(features) > 5:
                    print(f"  - ... and {len(features) - 5} more")

def main():
    """Test the K-12 feature engineering pipeline."""
    from pathlib import Path
    
    # Load the generated K-12 dataset
    data_dir = Path("data/k12_synthetic")
    data_files = list(data_dir.glob("k12_synthetic_dataset_*.csv"))
    
    if not data_files:
        print("❌ No K-12 dataset found. Run k12_data_generator.py first.")
        return
    
    latest_file = max(data_files, key=lambda f: f.stat().st_mtime)
    print(f"📂 Loading dataset: {latest_file}")
    
    df = pd.read_csv(latest_file)
    print(f"📊 Dataset loaded: {len(df)} students x {len(df.columns)} columns")
    
    # Apply feature engineering
    engineer = K12FeatureEngineer()
    X, y, features_df = engineer.fit_transform(df, target_column='current_success')
    
    # Save engineered features
    output_file = data_dir / f"k12_features_engineered_{pd.Timestamp.now().strftime('%Y%m%d')}.csv"
    features_df.to_csv(output_file, index=False)
    print(f"\n💾 Engineered features saved to: {output_file}")
    
    # Save feature names for model training
    feature_names_file = data_dir / "feature_names.json"
    import json
    with open(feature_names_file, 'w') as f:
        json.dump(engineer.feature_names, f, indent=2)
    
    print(f"📋 Feature names saved to: {feature_names_file}")
    print("\n🎉 K-12 feature engineering complete!")
    
    return X, y, features_df

if __name__ == "__main__":
    X, y, features_df = main()