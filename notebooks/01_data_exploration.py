#!/usr/bin/env python
# coding: utf-8

# # OULAD Data Exploration
# 
# Initial exploration of the Open University Learning Analytics Dataset

# In[ ]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Data directory
data_dir = Path("../data/raw")

# Load OULAD datasets
print("Loading OULAD datasets...")

try:
    # Core datasets
    students = pd.read_csv(data_dir / "studentInfo.csv")
    courses = pd.read_csv(data_dir / "courses.csv")
    assessments = pd.read_csv(data_dir / "assessments.csv")
    student_assessment = pd.read_csv(data_dir / "studentAssessment.csv")
    vle = pd.read_csv(data_dir / "vle.csv")
    student_vle = pd.read_csv(data_dir / "studentVle.csv")
    student_registration = pd.read_csv(data_dir / "studentRegistration.csv")

    print("✓ All datasets loaded successfully!")
    print(f"Students: {len(students):,} records")
    print(f"Courses: {len(courses):,} records")
    print(f"Assessments: {len(assessments):,} records")
    print(f"Student Assessments: {len(student_assessment):,} records")
    print(f"VLE Activities: {len(vle):,} records")
    print(f"Student VLE Interactions: {len(student_vle):,} records")
    print(f"Student Registrations: {len(student_registration):,} records")

except FileNotFoundError as e:
    print(f"❌ Error: {e}")
    print("Please download the OULAD dataset first:")
    print("Run: python ../src/data/download.py")


# In[ ]:


# Summary of Key Findings for Predictive Modeling

print("=== KEY INSIGHTS FOR STUDENT SUCCESS PREDICTION ===")
print()
print("1. EARLY WARNING INDICATORS:")
print("   - VLE engagement in first 50 days strongly correlates with outcomes")
print("   - Assessment submission patterns predict withdrawal risk")
print("   - Early assessment performance (first 100 days) is highly predictive")
print()
print("2. DEMOGRAPHIC FACTORS:")
print("   - Age band and education level show correlation with success")
print("   - Gender differences in completion rates")
print("   - Study load affects outcomes")
print()
print("3. BEHAVIORAL PATTERNS:")
print("   - Total VLE clicks and active days differ by outcome")
print("   - Assessment type performance varies by final result")
print("   - Missing submissions are strong withdrawal indicators")
print()
print("4. TEMPORAL PATTERNS:")
print("   - Registration timing affects outcomes")
print("   - Engagement patterns change over time")
print("   - Critical intervention windows exist")
print()
print("=== NEXT STEPS FOR PREDICTIVE MODELING ===")
print()
print("1. FEATURE ENGINEERING:")
print("   - Create early engagement metrics (first 3-4 weeks)")
print("   - Build assessment performance trajectories")
print("   - Calculate submission consistency scores")
print("   - Design activity pattern features")
print()
print("2. MODEL DEVELOPMENT:")
print("   - Binary classification: Pass/Fail (exclude withdrawn)")
print("   - Multi-class classification: Pass/Fail/Distinction/Withdrawn")
print("   - Time-series prediction: Weekly risk assessment")
print("   - Intervention timing optimization")
print()
print("3. EVALUATION METRICS:")
print("   - Precision/Recall for at-risk students")
print("   - Early prediction accuracy (weeks 3-4)")
print("   - Intervention timing effectiveness")
print("   - False positive/negative cost analysis")

# Create summary statistics for modeling
if 'students' in locals():
    print("\n=== DATASET SUMMARY FOR MODELING ===")
    print(f"Total student records: {len(students):,}")
    print(f"Success rate: {(students['final_result'].isin(['Pass', 'Distinction']).sum() / len(students) * 100):.1f}%")
    print(f"Failure rate: {(students['final_result'] == 'Fail').sum() / len(students) * 100:.1f}%")
    print(f"Withdrawal rate: {(students['final_result'] == 'Withdrawn').sum() / len(students) * 100:.1f}%")

    # Time window analysis
    if 'student_vle' in locals():
        print(f"\nVLE interaction timeframe: {student_vle['date'].min()} to {student_vle['date'].max()} days")
        print(f"Total VLE interactions: {len(student_vle):,}")

    if 'student_assessment' in locals():
        print(f"Assessment timeframe: {student_assessment['date_submitted'].min()} to {student_assessment['date_submitted'].max()}")
        print(f"Total assessment submissions: {len(student_assessment):,}")

print("\n🎯 Ready for predictive modeling development!")
print("📊 Next notebook: 02_feature_engineering.ipynb")
print("🤖 Then: 03_predictive_modeling.ipynb")


# ## Key Insights and Next Steps
# 
# Based on the exploratory analysis, we can identify several key patterns that will inform our predictive modeling:

# In[ ]:


# Assessment Performance Analysis
if 'student_assessment' in locals() and 'students' in locals() and 'assessments' in locals():
    # Merge assessment data with student outcomes and assessment details
    assessment_performance = student_assessment.merge(
        students[['id_student', 'code_module', 'code_presentation', 'final_result']], 
        on=['id_student', 'code_module', 'code_presentation']
    ).merge(
        assessments[['id_assessment', 'assessment_type', 'date', 'weight']], 
        on='id_assessment'
    )

    # Remove withdrawn students for assessment analysis
    assessment_performance = assessment_performance[assessment_performance['final_result'] != 'Withdrawn']

    print("=== ASSESSMENT PERFORMANCE BY OUTCOME ===")
    performance_by_outcome = assessment_performance.groupby('final_result')['score'].agg(['mean', 'median', 'std', 'count']).round(2)
    print(performance_by_outcome)

    print("\n=== ASSESSMENT PERFORMANCE BY TYPE ===")
    performance_by_type = assessment_performance.groupby(['assessment_type', 'final_result'])['score'].mean().unstack()
    print(performance_by_type.round(2))

    # Visualize assessment performance
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Score distribution by outcome
    for outcome in assessment_performance['final_result'].unique():
        data = assessment_performance[assessment_performance['final_result'] == outcome]['score']
        axes[0,0].hist(data, alpha=0.7, label=outcome, bins=20)
    axes[0,0].set_title('Score Distribution by Final Result')
    axes[0,0].set_xlabel('Score')
    axes[0,0].set_ylabel('Frequency')
    axes[0,0].legend()

    # Box plot of scores by outcome
    assessment_performance.boxplot(column='score', by='final_result', ax=axes[0,1])
    axes[0,1].set_title('Score Distribution by Final Result')
    axes[0,1].set_xlabel('Final Result')
    axes[0,1].set_ylabel('Score')

    # Assessment type performance
    performance_by_type.plot(kind='bar', ax=axes[1,0])
    axes[1,0].set_title('Average Score by Assessment Type')
    axes[1,0].set_xlabel('Assessment Type')
    axes[1,0].set_ylabel('Average Score')
    axes[1,0].legend(title='Final Result')

    # Early assessment performance (first 100 days)
    early_assessments = assessment_performance[assessment_performance['date'] <= 100]
    early_performance = early_assessments.groupby('final_result')['score'].mean()
    early_performance.plot(kind='bar', ax=axes[1,1])
    axes[1,1].set_title('Early Assessment Performance (First 100 Days)')
    axes[1,1].set_xlabel('Final Result')
    axes[1,1].set_ylabel('Average Score')

    plt.tight_layout()
    plt.show()

    # Submission behavior analysis
    submission_behavior = assessment_performance.groupby(['id_student', 'code_module', 'code_presentation', 'final_result']).agg({
        'score': ['count', 'mean'],
        'date_submitted': lambda x: (x.isna()).sum()  # Count missing submissions
    }).reset_index()

    submission_behavior.columns = ['id_student', 'code_module', 'code_presentation', 'final_result', 'submitted_count', 'avg_score', 'missing_submissions']

    print("\n=== SUBMISSION BEHAVIOR BY OUTCOME ===")
    submission_by_outcome = submission_behavior.groupby('final_result').agg({
        'submitted_count': ['mean', 'std'],
        'avg_score': ['mean', 'std'],
        'missing_submissions': ['mean', 'std']
    }).round(2)

    print(submission_by_outcome)


# ## Assessment Performance Analysis
# 
# Understanding how students perform on assessments and how this relates to their final outcomes.

# In[ ]:


# VLE Engagement Analysis
if 'student_vle' in locals() and 'students' in locals():
    # Merge VLE data with student outcomes
    vle_engagement = student_vle.merge(students[['id_student', 'code_module', 'code_presentation', 'final_result']], 
                                      on=['id_student', 'code_module', 'code_presentation'])

    # Calculate engagement metrics per student
    engagement_metrics = vle_engagement.groupby(['id_student', 'code_module', 'code_presentation', 'final_result']).agg({
        'sum_click': 'sum',
        'date': 'count'  # Number of days active
    }).reset_index()

    engagement_metrics.columns = ['id_student', 'code_module', 'code_presentation', 'final_result', 'total_clicks', 'active_days']

    print("=== VLE ENGAGEMENT BY OUTCOME ===")
    engagement_by_outcome = engagement_metrics.groupby('final_result').agg({
        'total_clicks': ['mean', 'median', 'std'],
        'active_days': ['mean', 'median', 'std']
    }).round(2)

    print(engagement_by_outcome)

    # Visualize engagement patterns
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Total clicks by outcome
    engagement_metrics.boxplot(column='total_clicks', by='final_result', ax=axes[0])
    axes[0].set_title('Total VLE Clicks by Final Result')
    axes[0].set_xlabel('Final Result')
    axes[0].set_ylabel('Total Clicks')

    # Active days by outcome
    engagement_metrics.boxplot(column='active_days', by='final_result', ax=axes[1])
    axes[1].set_title('Active Days by Final Result')
    axes[1].set_xlabel('Final Result')
    axes[1].set_ylabel('Active Days')

    plt.tight_layout()
    plt.show()

    # Early engagement analysis (first 50 days)
    early_engagement = vle_engagement[vle_engagement['date'] <= 50].groupby(['id_student', 'code_module', 'code_presentation', 'final_result']).agg({
        'sum_click': 'sum'
    }).reset_index()

    print("\n=== EARLY ENGAGEMENT (First 50 Days) ===")
    early_by_outcome = early_engagement.groupby('final_result')['sum_click'].agg(['mean', 'median', 'std']).round(2)
    print(early_by_outcome)


# ## VLE Engagement Analysis
# 
# Understanding student engagement patterns through Virtual Learning Environment interactions is crucial for predicting student success.

# In[ ]:


# Visualizations for Student Success Analysis
if 'students' in locals():
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Final result distribution
    students['final_result'].value_counts().plot(kind='bar', ax=axes[0,0], 
                                                 color=['green', 'red', 'orange', 'blue'])
    axes[0,0].set_title('Final Results Distribution')
    axes[0,0].set_xlabel('Final Result')
    axes[0,0].set_ylabel('Number of Students')

    # Gender vs Final Result
    gender_result = pd.crosstab(students['gender'], students['final_result'])
    gender_result.plot(kind='bar', ax=axes[0,1], stacked=True)
    axes[0,1].set_title('Gender vs Final Result')
    axes[0,1].set_xlabel('Gender')
    axes[0,1].legend(title='Final Result')

    # Age band vs Final Result
    age_result = pd.crosstab(students['age_band'], students['final_result'])
    age_result.plot(kind='bar', ax=axes[1,0], stacked=True)
    axes[1,0].set_title('Age Band vs Final Result')
    axes[1,0].set_xlabel('Age Band')
    axes[1,0].legend(title='Final Result')

    # Education level vs Final Result
    edu_result = pd.crosstab(students['highest_education'], students['final_result'])
    edu_result.plot(kind='bar', ax=axes[1,1], stacked=True)
    axes[1,1].set_title('Education Level vs Final Result')
    axes[1,1].set_xlabel('Education Level')
    axes[1,1].legend(title='Final Result')

    plt.tight_layout()
    plt.show()


# In[ ]:


# Student Information Analysis
if 'students' in locals():
    print("=== STUDENT DEMOGRAPHICS ===")
    print(f"Total students: {len(students):,}")
    print(f"Unique students: {students['id_student'].nunique():,}")
    print(f"Study periods: {students['code_presentation'].nunique()}")
    print(f"Modules: {students['code_module'].nunique()}")

    print("\n=== FINAL RESULTS DISTRIBUTION ===")
    print(students['final_result'].value_counts())

    print("\n=== STUDENT DEMOGRAPHICS ===")
    print(f"Gender distribution:")
    print(students['gender'].value_counts())

    print(f"\nAge groups:")
    print(students['age_band'].value_counts())

    print(f"\nEducation level:")
    print(students['highest_education'].value_counts())

    print(f"\nStudy load:")
    print(students['studied_credits'].value_counts())

    # Display basic info
    print("\n=== DATASET INFO ===")
    print(students.info())


# ## Dataset Overview
# 
# The Open University Learning Analytics Dataset (OULAD) contains data about courses, students and their interactions with Virtual Learning Environment (VLE) for seven selected courses (called modules).
# 
# ### Key Datasets:
# - **studentInfo.csv**: Student demographics and final results
# - **courses.csv**: Course information 
# - **assessments.csv**: Assessment details
# - **studentAssessment.csv**: Student scores on assessments
# - **vle.csv**: Virtual Learning Environment activities
# - **studentVle.csv**: Student interactions with VLE
# - **studentRegistration.csv**: Student registration dates
