#!/usr/bin/env python
# coding: utf-8

# # Feature Engineering for Student Success Prediction
# 
# This notebook creates predictive features from the OULAD dataset, focusing on early warning indicators that can predict student outcomes within the first 3-4 weeks of a course.

# In[ ]:


import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Load the datasets
data_dir = Path("../data/raw")
students = pd.read_csv(data_dir / "studentInfo.csv")
student_vle = pd.read_csv(data_dir / "studentVle.csv")
student_assessment = pd.read_csv(data_dir / "studentAssessment.csv")
assessments = pd.read_csv(data_dir / "assessments.csv")
student_registration = pd.read_csv(data_dir / "studentRegistration.csv")

print("Datasets loaded successfully!")


# ## 1. Early VLE Engagement Features
# 
# Create features based on Virtual Learning Environment interactions in the first few weeks.

# In[ ]:


def create_early_vle_features(student_vle_df, time_window=28):
    """
    Create VLE engagement features for early prediction

    Args:
        student_vle_df: StudentVLE dataset
        time_window: Number of days to consider for 'early' engagement

    Returns:
        DataFrame with early VLE features
    """

    # Filter to early engagement period
    early_vle = student_vle_df[student_vle_df['date'] <= time_window].copy()

    # Aggregate features by student
    vle_features = early_vle.groupby(['id_student', 'code_module', 'code_presentation']).agg({
        'sum_click': [
            'sum',      # Total clicks
            'mean',     # Average clicks per day
            'std',      # Variability in daily clicks
            'max'       # Peak engagement day
        ],
        'date': [
            'count',    # Number of active days
            'min',      # First engagement day
            'max'       # Last engagement day
        ]
    }).reset_index()

    # Flatten column names
    vle_features.columns = [
        'id_student', 'code_module', 'code_presentation',
        'early_total_clicks', 'early_avg_clicks', 'early_clicks_std', 'early_max_clicks',
        'early_active_days', 'early_first_access', 'early_last_access'
    ]

    # Fill NaN values
    vle_features['early_clicks_std'] = vle_features['early_clicks_std'].fillna(0)

    # Create derived features
    vle_features['early_engagement_consistency'] = vle_features['early_active_days'] / time_window
    vle_features['early_clicks_per_active_day'] = vle_features['early_total_clicks'] / vle_features['early_active_days']
    vle_features['early_engagement_range'] = vle_features['early_last_access'] - vle_features['early_first_access']

    return vle_features

# Create early VLE features
early_vle_features = create_early_vle_features(student_vle, time_window=28)
print(f"Early VLE features created for {len(early_vle_features)} student records")
print("\nFeature columns:")
print(early_vle_features.columns.tolist())


# ## 2. Early Assessment Features
# 
# Create features based on assessment performance and submission behavior in early weeks.

# In[ ]:


def create_early_assessment_features(student_assessment_df, assessments_df, time_window=70):
    """
    Create assessment-based features for early prediction

    Args:
        student_assessment_df: Student assessment scores
        assessments_df: Assessment details
        time_window: Number of days to consider for 'early' assessments

    Returns:
        DataFrame with early assessment features
    """

    # Merge with assessment details
    assessment_data = student_assessment_df.merge(assessments_df, on='id_assessment')

    # Filter to early assessment period
    early_assessments = assessment_data[assessment_data['date'] <= time_window].copy()

    # Create features by student
    assessment_features = early_assessments.groupby(['id_student', 'code_module', 'code_presentation']).agg({
        'score': [
            'count',    # Number of assessments submitted
            'mean',     # Average score
            'std',      # Score variability
            'min',      # Worst score
            'max'       # Best score
        ],
        'date_submitted': [
            lambda x: x.isna().sum(),  # Missing submissions
            'count'     # Submitted assessments
        ],
        'weight': 'sum',  # Total weight of completed assessments
        'is_banked': 'sum'  # Number of banked assessments
    }).reset_index()

    # Flatten column names
    assessment_features.columns = [
        'id_student', 'code_module', 'code_presentation',
        'early_assessments_count', 'early_avg_score', 'early_score_std', 'early_min_score', 'early_max_score',
        'early_missing_submissions', 'early_submitted_count', 'early_total_weight', 'early_banked_count'
    ]

    # Fill NaN values
    assessment_features['early_score_std'] = assessment_features['early_score_std'].fillna(0)

    # Create derived features
    assessment_features['early_submission_rate'] = (assessment_features['early_submitted_count'] / 
                                                   (assessment_features['early_submitted_count'] + assessment_features['early_missing_submissions']))
    assessment_features['early_score_range'] = assessment_features['early_max_score'] - assessment_features['early_min_score']

    return assessment_features

# Create early assessment features
early_assessment_features = create_early_assessment_features(student_assessment, assessments, time_window=70)
print(f"Early assessment features created for {len(early_assessment_features)} student records")
print("\nFeature columns:")
print(early_assessment_features.columns.tolist())


# ## 3. Student Demographic Features
# 
# Process demographic and registration information.

# In[ ]:


def create_demographic_features(students_df, registration_df):
    """
    Create demographic and registration features

    Args:
        students_df: Student information
        registration_df: Registration dates

    Returns:
        DataFrame with demographic features
    """

    # Start with student info
    demo_features = students_df.copy()

    # Add registration information
    demo_features = demo_features.merge(registration_df, 
                                      on=['id_student', 'code_module', 'code_presentation'], 
                                      how='left')

    # Encode categorical variables
    demo_features['gender_encoded'] = demo_features['gender'].map({'F': 0, 'M': 1})
    demo_features['region_encoded'] = pd.Categorical(demo_features['region']).codes

    # Age band encoding (ordered)
    age_mapping = {'0-35': 0, '35-55': 1, '55<=': 2}
    demo_features['age_band_encoded'] = demo_features['age_band'].map(age_mapping)

    # Education level encoding (ordered)
    education_mapping = {
        'No Formal quals': 0,
        'Lower Than A Level': 1,
        'A Level or Equivalent': 2,
        'HE Qualification': 3,
        'Post Graduate Qualification': 4
    }
    demo_features['education_encoded'] = demo_features['highest_education'].map(education_mapping)

    # Create binary features
    demo_features['is_male'] = (demo_features['gender'] == 'M').astype(int)
    demo_features['has_disability'] = (demo_features['disability'] == 'Y').astype(int)

    # Registration timing features
    demo_features['registration_delay'] = demo_features['date_registration']  # Days from course start
    demo_features['unregistered'] = demo_features['date_unregistration'].notna().astype(int)

    # Select final features
    feature_columns = [
        'id_student', 'code_module', 'code_presentation',
        'gender_encoded', 'region_encoded', 'age_band_encoded', 'education_encoded',
        'is_male', 'has_disability', 'studied_credits', 'num_of_prev_attempts',
        'registration_delay', 'unregistered'
    ]

    return demo_features[feature_columns]

# Create demographic features
demographic_features = create_demographic_features(students, student_registration)
print(f"Demographic features created for {len(demographic_features)} student records")
print("\nFeature columns:")
print(demographic_features.columns.tolist())


# ## 4. Combine All Features
# 
# Merge all feature sets and create the final dataset for modeling.

# In[ ]:


# Merge all features
final_features = demographic_features.merge(
    early_vle_features, 
    on=['id_student', 'code_module', 'code_presentation'],
    how='left'
).merge(
    early_assessment_features,
    on=['id_student', 'code_module', 'code_presentation'],
    how='left'
)

# Add target variable
target_data = students[['id_student', 'code_module', 'code_presentation', 'final_result']].copy()
final_features = final_features.merge(target_data, on=['id_student', 'code_module', 'code_presentation'])

# Fill missing values (students with no VLE or assessment activity)
vle_columns = [col for col in final_features.columns if 'early_' in col and 'vle' in col.lower()]
assessment_columns = [col for col in final_features.columns if 'early_' in col and ('score' in col or 'assessment' in col or 'submission' in col)]

# Fill VLE missing values with 0 (no engagement)
for col in early_vle_features.columns[3:]:  # Skip ID columns
    if col in final_features.columns:
        final_features[col] = final_features[col].fillna(0)

# Fill assessment missing values appropriately
for col in early_assessment_features.columns[3:]:  # Skip ID columns
    if col in final_features.columns:
        if 'count' in col or 'missing' in col:
            final_features[col] = final_features[col].fillna(0)
        elif 'score' in col:
            final_features[col] = final_features[col].fillna(final_features[col].median())
        else:
            final_features[col] = final_features[col].fillna(0)

print(f"Final feature set created with {len(final_features)} records and {len(final_features.columns)} features")
print("\nTarget distribution:")
print(final_features['final_result'].value_counts())

# Display feature summary
print("\nFeature summary:")
print(f"Demographic features: {len(demographic_features.columns) - 3}")
print(f"Early VLE features: {len(early_vle_features.columns) - 3}")
print(f"Early Assessment features: {len(early_assessment_features.columns) - 3}")
print(f"Total features: {len(final_features.columns) - 4}")

# Check for missing values
print("\nMissing values by column:")
missing_counts = final_features.isnull().sum()
missing_counts = missing_counts[missing_counts > 0]
if len(missing_counts) > 0:
    print(missing_counts)
else:
    print("No missing values found!")

# Display first few rows
print("\nFirst 5 rows of final features:")
print(final_features.head())


# ## 5. Save Processed Features
# 
# Save the engineered features for use in predictive modeling.

# In[ ]:


# Save to processed data directory
output_dir = Path("../data/processed")
output_dir.mkdir(exist_ok=True)

# Save the final feature set
final_features.to_csv(output_dir / "student_features_engineered.csv", index=False)

# Save feature metadata
feature_metadata = {
    'total_records': len(final_features),
    'total_features': len(final_features.columns) - 4,  # Exclude ID columns and target
    'demographic_features': len(demographic_features.columns) - 3,
    'vle_features': len(early_vle_features.columns) - 3,
    'assessment_features': len(early_assessment_features.columns) - 3,
    'vle_time_window': 28,
    'assessment_time_window': 70,
    'target_distribution': final_features['final_result'].value_counts().to_dict()
}

import json
with open(output_dir / "feature_metadata.json", 'w') as f:
    json.dump(feature_metadata, f, indent=2)

print("✅ Features saved successfully!")
print(f"📁 Location: {output_dir}")
print(f"📊 Main file: student_features_engineered.csv")
print(f"📋 Metadata: feature_metadata.json")
print("\n🚀 Ready for predictive modeling!")
print("📓 Next notebook: 03_predictive_modeling.ipynb")

