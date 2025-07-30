#!/usr/bin/env python3
"""
K-12 Synthetic Data Generator

Generates realistic synthetic K-12 student data for model training,
based on research patterns and real-world K-12 success factors.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime, timedelta
import random

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)

class K12DataGenerator:
    """Generate synthetic K-12 student data for model training."""
    
    def __init__(self, n_students=10000, n_years=3):
        self.n_students = n_students
        self.n_years = n_years
        self.current_year = 2024
        
        # K-12 Research-based correlation patterns
        self.grade_bands = {
            'elementary': list(range(0, 6)),  # K-5
            'middle': list(range(6, 9)),      # 6-8
            'high': list(range(9, 13))        # 9-12
        }
        
        # Success rate patterns by grade (based on research)
        self.base_success_rates = {
            0: 0.95, 1: 0.94, 2: 0.93, 3: 0.92, 4: 0.91, 5: 0.90,  # Elementary
            6: 0.87, 7: 0.85, 8: 0.86,  # Middle (dip in 7th grade)
            9: 0.82, 10: 0.84, 11: 0.86, 12: 0.88  # High (recovery pattern)
        }
    
    def generate_demographics(self):
        """Generate student demographic information."""
        demographics = []
        
        for student_id in range(1, self.n_students + 1):
            # Grade distribution (more students in elementary) - ensure sum = 1.0
            grade_weights = [0.095] * 6 + [0.08] * 3 + [0.075] * 4  # K-12 weights
            grade_weights = np.array(grade_weights) / np.sum(grade_weights)  # Normalize
            grade = np.random.choice(range(13), p=grade_weights)
            
            # Age calculation (with some variation)
            base_age = 5 + grade  # Typical age for grade
            age_variation = np.random.choice([-1, 0, 1], p=[0.1, 0.8, 0.1])
            age = base_age + age_variation
            
            # Demographics with realistic distributions
            demographics.append({
                'student_id': student_id,
                'grade_level': grade,
                'age': age,
                'gender': np.random.choice(['M', 'F'], p=[0.51, 0.49]),
                'race_ethnicity': np.random.choice([
                    'White', 'Hispanic', 'Black', 'Asian', 'Multi-racial', 'Other'
                ], p=[0.47, 0.27, 0.15, 0.06, 0.04, 0.01]),
                'free_reduced_lunch': np.random.choice([0, 1], p=[0.52, 0.48]),
                'ell_status': np.random.choice([0, 1], p=[0.90, 0.10]),
                'iep_status': np.random.choice([0, 1], p=[0.86, 0.14]),
                'section_504': np.random.choice([0, 1], p=[0.95, 0.05]),
                'gifted_program': np.random.choice([0, 1], p=[0.94, 0.06])
            })
        
        return pd.DataFrame(demographics)
    
    def generate_academic_history(self, demographics_df):
        """Generate academic performance history."""
        academic_data = []
        
        for _, student in demographics_df.iterrows():
            student_id = student['student_id']
            grade = student['grade_level']
            
            # Base success probability for this student's grade
            base_success = self.base_success_rates[grade]
            
            # Adjust based on risk factors (research-based)
            risk_adjustments = 0
            if student['free_reduced_lunch']: risk_adjustments -= 0.15
            if student['ell_status']: risk_adjustments -= 0.10
            if student['iep_status']: risk_adjustments -= 0.08
            if student['age'] > (5 + grade + 0.5): risk_adjustments -= 0.12  # Over-age
            if student['gifted_program']: risk_adjustments += 0.10
            
            adjusted_success = max(0.1, min(0.95, base_success + risk_adjustments))
            
            # Generate multi-year academic data
            yearly_data = []
            cumulative_gpa = []
            
            for year_offset in range(min(3, grade + 1)):  # Up to 3 years of history
                year_grade = max(0, grade - year_offset)
                
                # Generate grades for core subjects
                if year_grade <= 5:  # Elementary
                    subjects = ['Reading', 'Math', 'Science', 'Social_Studies']
                    grade_scale = 4.0  # Often standards-based
                elif year_grade <= 8:  # Middle
                    subjects = ['ELA', 'Math', 'Science', 'Social_Studies', 'Elective1', 'Elective2']
                    grade_scale = 4.0
                else:  # High school
                    subjects = ['English', 'Math', 'Science', 'Social_Studies', 'Elective1', 'Elective2', 'PE']
                    grade_scale = 4.0
                
                # Generate subject grades with correlation
                subject_grades = {}
                base_performance = np.random.normal(adjusted_success * grade_scale, 0.5)
                
                for subject in subjects:
                    # Subject-specific variation
                    subject_variation = np.random.normal(0, 0.3)
                    grade_points = max(0, min(grade_scale, base_performance + subject_variation))
                    subject_grades[f'{subject}_Grade'] = round(grade_points, 2)
                
                yearly_data.append({
                    'year': self.current_year - year_offset,
                    'grade_level': year_grade,
                    **subject_grades,
                    'year_gpa': round(np.mean(list(subject_grades.values())), 2)
                })
                
                cumulative_gpa.append(yearly_data[-1]['year_gpa'])
            
            # Calculate academic summary metrics
            current_gpa = yearly_data[0]['year_gpa'] if yearly_data else 2.0
            gpa_trend = 0
            if len(cumulative_gpa) > 1:
                gpa_trend = cumulative_gpa[0] - cumulative_gpa[-1]  # Recent - Oldest
            
            # Course failures and retention
            failure_prob = max(0, 1 - adjusted_success - 0.3)
            course_failures = np.random.poisson(failure_prob * 2)
            grade_retained = 1 if np.random.random() < (failure_prob * 0.3) else 0
            
            academic_data.append({
                'student_id': student_id,
                'current_gpa': current_gpa,
                'cumulative_gpa': round(np.mean(cumulative_gpa), 2) if cumulative_gpa else current_gpa,
                'gpa_trend': round(gpa_trend, 2),
                'course_failures_total': course_failures,
                'grade_retained_ever': grade_retained,
                'years_data_available': len(yearly_data),
                'credits_earned': max(0, grade * 6 - course_failures * 2),  # Rough calculation
                **{f'recent_{k}': v for k, v in yearly_data[0].items() if k not in ['year', 'grade_level']}
            })
        
        return pd.DataFrame(academic_data)
    
    def generate_engagement_metrics(self, demographics_df):
        """Generate student engagement and behavior metrics."""
        engagement_data = []
        
        for _, student in demographics_df.iterrows():
            student_id = student['student_id']
            grade = student['grade_level']
            
            # Base engagement patterns by grade band
            if grade <= 5:  # Elementary
                base_attendance = 0.96
                base_behavior = 0.95
            elif grade <= 8:  # Middle school engagement dip
                base_attendance = 0.93
                base_behavior = 0.88
            else:  # High school
                base_attendance = 0.91
                base_behavior = 0.90
            
            # Risk factor adjustments
            if student['free_reduced_lunch']:
                base_attendance -= 0.04
                base_behavior -= 0.03
            if student['iep_status']:
                base_behavior -= 0.05
            
            # Generate metrics with realistic correlation
            attendance_rate = max(0.6, min(0.99, np.random.normal(base_attendance, 0.08)))
            chronic_absent = 1 if attendance_rate < 0.90 else 0
            
            tardiness_rate = max(0, np.random.exponential(0.02))
            if chronic_absent:
                tardiness_rate *= 2
            
            # Behavioral metrics
            behavior_score = max(0.1, min(1.0, np.random.normal(base_behavior, 0.10)))
            disciplinary_incidents = np.random.poisson((1 - behavior_score) * 3)
            suspensions = min(disciplinary_incidents, np.random.poisson((1 - behavior_score) * 1))
            
            # Engagement activities (varies by grade)
            if grade <= 5:
                extracurricular = np.random.choice([0, 1], p=[0.7, 0.3])
                parent_engagement = np.random.choice([0, 1, 2], p=[0.2, 0.5, 0.3])
            elif grade <= 8:
                extracurricular = np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1])
                parent_engagement = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
            else:
                extracurricular = np.random.choice([0, 1, 2, 3], p=[0.5, 0.3, 0.15, 0.05])
                parent_engagement = np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2])
            
            # Technology engagement (increases with grade)
            tech_access = np.random.choice([0, 1], p=[0.15, 0.85])
            if grade >= 6:
                tech_access = np.random.choice([0, 1], p=[0.05, 0.95])
            
            engagement_data.append({
                'student_id': student_id,
                'attendance_rate': round(attendance_rate, 3),
                'chronic_absenteeism': chronic_absent,
                'tardiness_rate': round(tardiness_rate, 3),
                'behavior_score': round(behavior_score, 3),
                'disciplinary_incidents': disciplinary_incidents,
                'suspensions': suspensions,
                'extracurricular_count': extracurricular,
                'parent_engagement_level': parent_engagement,
                'technology_access': tech_access
            })
        
        return pd.DataFrame(engagement_data)
    
    def generate_outcomes(self, demographics_df, academic_df, engagement_df):
        """Generate student success outcomes based on all factors."""
        # Merge all data
        merged_df = demographics_df.merge(academic_df, on='student_id').merge(engagement_df, on='student_id')
        
        outcome_data = []
        
        for _, student in merged_df.iterrows():
            grade = student['grade_level']
            
            # Calculate success probability based on multiple factors
            success_prob = self.base_success_rates[grade]
            
            # Academic factors (strongest predictors)
            success_prob += (student['current_gpa'] - 2.5) * 0.15
            success_prob -= student['course_failures_total'] * 0.08
            success_prob -= student['grade_retained_ever'] * 0.12
            
            # Engagement factors
            success_prob += (student['attendance_rate'] - 0.90) * 0.3
            success_prob -= student['chronic_absenteeism'] * 0.10
            success_prob -= student['disciplinary_incidents'] * 0.02
            success_prob += student['extracurricular_count'] * 0.03
            
            # Demographic factors
            success_prob -= student['free_reduced_lunch'] * 0.08
            success_prob -= student['ell_status'] * 0.06
            success_prob -= student['iep_status'] * 0.04
            success_prob += student['parent_engagement_level'] * 0.04
            
            # Grade-specific adjustments
            if grade == 3:  # Critical reading milestone
                reading_proficient = 1 if success_prob > 0.7 else 0
                if not reading_proficient:
                    success_prob -= 0.15
            
            if grade >= 9:  # High school credit requirements
                on_track_credits = 1 if student['credits_earned'] >= (grade - 8) * 6 else 0
                if not on_track_credits:
                    success_prob -= 0.20
            
            # Bound probability
            success_prob = max(0.05, min(0.95, success_prob))
            
            # Generate outcomes
            current_success = 1 if np.random.random() < success_prob else 0
            
            # Risk categories
            if success_prob >= 0.8:
                risk_category = 'Low Risk'
            elif success_prob >= 0.6:
                risk_category = 'Medium Risk'
            else:
                risk_category = 'High Risk'
            
            # Future prediction (next grade success)
            next_grade_prob = min(0.95, success_prob + np.random.normal(0, 0.05))
            next_grade_success = 1 if np.random.random() < next_grade_prob else 0
            
            # Graduation prediction (for grade 9+)
            if grade >= 9:
                grad_factors = success_prob + (student['current_gpa'] - 2.0) * 0.1
                grad_prob = max(0.3, min(0.95, grad_factors))
                will_graduate = 1 if np.random.random() < grad_prob else 0
            else:
                will_graduate = None
                grad_prob = None
            
            outcome_data.append({
                'student_id': student['student_id'],
                'success_probability': round(success_prob, 3),
                'current_success': current_success,
                'risk_category': risk_category,
                'next_grade_success_pred': next_grade_success,
                'next_grade_success_prob': round(next_grade_prob, 3),
                'graduation_prediction': will_graduate,
                'graduation_probability': round(grad_prob, 3) if grad_prob else None
            })
        
        return pd.DataFrame(outcome_data)
    
    def generate_full_dataset(self):
        """Generate complete K-12 synthetic dataset."""
        print("🏫 Generating K-12 Synthetic Dataset...")
        print(f"Students: {self.n_students:,}")
        print(f"Years of data: {self.n_years}")
        
        # Generate each component
        print("📊 Generating demographics...")
        demographics = self.generate_demographics()
        
        print("📚 Generating academic history...")
        academic = self.generate_academic_history(demographics)
        
        print("🎯 Generating engagement metrics...")
        engagement = self.generate_engagement_metrics(demographics)
        
        print("🎓 Generating outcomes...")
        outcomes = self.generate_outcomes(demographics, academic, engagement)
        
        # Merge all data
        full_dataset = demographics.merge(academic, on='student_id') \
                                 .merge(engagement, on='student_id') \
                                 .merge(outcomes, on='student_id')
        
        print(f"✅ Generated complete dataset: {len(full_dataset)} students x {len(full_dataset.columns)} features")
        
        # Generate summary statistics
        self.generate_summary_stats(full_dataset)
        
        return full_dataset
    
    def generate_summary_stats(self, df):
        """Generate and display summary statistics."""
        print("\n📈 Dataset Summary Statistics:")
        print("=" * 50)
        
        # Grade distribution
        print("\n🎒 Grade Distribution:")
        grade_dist = df.groupby('grade_level').size()
        for grade, count in grade_dist.items():
            grade_name = f"Grade {grade}" if grade > 0 else "Kindergarten"
            print(f"  {grade_name}: {count:,} students ({count/len(df)*100:.1f}%)")
        
        # Risk distribution
        print("\n⚠️ Risk Category Distribution:")
        risk_dist = df['risk_category'].value_counts()
        for risk, count in risk_dist.items():
            print(f"  {risk}: {count:,} students ({count/len(df)*100:.1f}%)")
        
        # Key correlations
        print(f"\n📊 Key Success Factors:")
        print(f"  Average GPA: {df['current_gpa'].mean():.2f}")
        print(f"  Average Attendance: {df['attendance_rate'].mean():.1%}")
        print(f"  Students with Course Failures: {(df['course_failures_total'] > 0).sum():,} ({(df['course_failures_total'] > 0).mean():.1%})")
        print(f"  Chronic Absenteeism Rate: {df['chronic_absenteeism'].mean():.1%}")
        print(f"  Students on Free/Reduced Lunch: {df['free_reduced_lunch'].sum():,} ({df['free_reduced_lunch'].mean():.1%})")
        print(f"  ELL Students: {df['ell_status'].sum():,} ({df['ell_status'].mean():.1%})")
        print(f"  Students with IEPs: {df['iep_status'].sum():,} ({df['iep_status'].mean():.1%})")
        
        # Success rates by grade band
        print(f"\n🎯 Success Rates by Grade Band:")
        elementary = df[df['grade_level'] <= 5]['current_success'].mean()
        middle = df[(df['grade_level'] >= 6) & (df['grade_level'] <= 8)]['current_success'].mean()
        high = df[df['grade_level'] >= 9]['current_success'].mean()
        print(f"  Elementary (K-5): {elementary:.1%}")
        print(f"  Middle School (6-8): {middle:.1%}")
        print(f"  High School (9-12): {high:.1%}")

def main():
    """Generate K-12 synthetic dataset for model training."""
    # Create output directory
    output_dir = Path("data/k12_synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    generator = K12DataGenerator(n_students=15000, n_years=3)
    dataset = generator.generate_full_dataset()
    
    # Save to CSV
    output_file = output_dir / f"k12_synthetic_dataset_{datetime.now().strftime('%Y%m%d')}.csv"
    dataset.to_csv(output_file, index=False)
    print(f"\n💾 Dataset saved to: {output_file}")
    
    # Save metadata
    metadata = {
        'generated_date': datetime.now().isoformat(),
        'n_students': len(dataset),
        'n_features': len(dataset.columns),
        'grade_distribution': dataset['grade_level'].value_counts().to_dict(),
        'risk_distribution': dataset['risk_category'].value_counts().to_dict(),
        'success_rate_overall': float(dataset['current_success'].mean()),
        'feature_list': list(dataset.columns)
    }
    
    metadata_file = output_dir / "dataset_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"📋 Metadata saved to: {metadata_file}")
    print("\n🎉 K-12 synthetic dataset generation complete!")
    
    return dataset

if __name__ == "__main__":
    dataset = main()