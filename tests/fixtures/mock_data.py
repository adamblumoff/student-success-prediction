#!/usr/bin/env python3
"""
Mock data generators for testing Student Success Prediction MVP system.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random
from typing import Dict, List, Any

class MockDataGenerator:
    """Generate realistic mock data for testing."""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducible tests."""
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_student_features(self, num_students: int = 10) -> pd.DataFrame:
        """Generate student features compatible with intervention system."""
        students = []
        
        for i in range(num_students):
            # Risk-based profiles for predictable testing
            if i < 3:  # High risk students
                risk_mult = 0.3
                performance_mult = 0.6
            elif i < 6:  # Medium risk students
                risk_mult = 0.6
                performance_mult = 0.75
            else:  # Low risk students
                risk_mult = 0.9
                performance_mult = 0.9
            
            student = {
                'id_student': 1000 + i,
                'code_module': 'TEST',
                'code_presentation': '2024J',
                
                # Demographics
                'gender_encoded': np.random.randint(0, 2),
                'region_encoded': np.random.randint(0, 13),
                'age_band_encoded': np.random.randint(0, 3),
                'education_encoded': np.random.randint(0, 5),
                'is_male': np.random.randint(0, 2),
                'has_disability': 1 if np.random.random() < 0.1 else 0,
                'studied_credits': np.random.choice([60, 120, 180, 240]),
                'num_of_prev_attempts': np.random.randint(0, 3),
                'registration_delay': np.random.uniform(-10, 30),
                'unregistered': 0,
                
                # Engagement features
                'early_total_clicks': max(10, int(np.random.normal(200 * risk_mult, 100))),
                'early_avg_clicks': max(1, np.random.normal(15 * risk_mult, 8)),
                'early_clicks_std': max(0, np.random.normal(10 * risk_mult, 5)),
                'early_max_clicks': max(5, int(np.random.normal(50 * risk_mult, 20))),
                'early_active_days': max(1, int(np.random.normal(20 * risk_mult, 8))),
                'early_first_access': np.random.randint(-10, 5),
                'early_last_access': np.random.randint(15, 35),
                'early_engagement_consistency': max(0.1, np.random.normal(3 * risk_mult, 1.5)),
                'early_clicks_per_active_day': max(1, np.random.normal(8 * risk_mult, 3)),
                'early_engagement_range': max(5, int(np.random.normal(25 * risk_mult, 10))),
                
                # Assessment features
                'early_assessments_count': np.random.randint(1, 6),
                'early_avg_score': max(0, min(100, np.random.normal(75 * performance_mult, 15))),
                'early_score_std': max(0, np.random.normal(12, 5)),
                'early_min_score': max(0, np.random.normal(60 * performance_mult, 10)),
                'early_max_score': max(0, min(100, np.random.normal(85 * performance_mult, 10))),
                'early_missing_submissions': np.random.randint(0, 3) if risk_mult < 0.6 else 0,
                'early_submitted_count': np.random.randint(2, 6),
                'early_total_weight': np.random.uniform(10, 40),
                'early_banked_count': np.random.randint(0, 2),
                'early_submission_rate': max(0, min(1, np.random.normal(0.9 * performance_mult, 0.2))),
                'early_score_range': max(0, np.random.normal(20, 8)),
            }
            students.append(student)
        
        return pd.DataFrame(students)
    
    def generate_gradebook_csv_data(self, num_students: int = 5) -> str:
        """Generate CSV data string for gradebook upload tests."""
        students = []
        
        for i in range(num_students):
            student = {
                'student_id': f'S{1000 + i:03d}',
                'name': f'Test Student {i+1}',
                'grade_level': np.random.randint(9, 12),
                'current_gpa': round(np.random.uniform(1.5, 4.0), 2),
                'attendance_rate': round(np.random.uniform(0.7, 1.0), 3),
                'discipline_incidents': np.random.randint(0, 5),
                'assignment_completion': round(np.random.uniform(0.4, 1.0), 2),
            }
            students.append(student)
        
        df = pd.DataFrame(students)
        return df.to_csv(index=False)
    
    def generate_canvas_csv_data(self, num_students: int = 3) -> str:
        """Generate Canvas-format CSV data string."""
        students = []
        
        for i in range(num_students):
            student = {
                'Student': f'Test Student {i+1}',
                'ID': 1001 + i,
                'SIS User ID': '',
                'SIS Login ID': f'student{i+1}',
                'Section': 'Section 1',
                'Assignment 1': np.random.randint(60, 95),
                'Assignment 2': np.random.randint(60, 95),
                'Quiz 1': np.random.randint(50, 100),
                'Current Score': round(np.random.uniform(45, 95), 1),
                'Total Activity Time (mins)': np.random.randint(30, 200),
                'Last Activity': '2024-01-15'
            }
            students.append(student)
        
        df = pd.DataFrame(students)
        return df.to_csv(index=False)
    
    def generate_prediction_results(self, num_students: int = 10) -> List[Dict[str, Any]]:
        """Generate mock prediction results."""
        results = []
        
        for i in range(num_students):
            risk_score = np.random.random()
            
            if risk_score < 0.3:
                category = 'Low Risk'
                needs_intervention = False
            elif risk_score < 0.7:
                category = 'Medium Risk'
                needs_intervention = True
            else:
                category = 'High Risk'
                needs_intervention = True
            
            result = {
                'student_id': 1000 + i,
                'risk_score': round(risk_score, 3),
                'risk_category': category,
                'success_probability': round(1 - risk_score, 3),
                'needs_intervention': needs_intervention,
                'confidence': round(np.random.uniform(0.7, 0.95), 3)
            }
            results.append(result)
        
        return results
    
    def generate_k12_prediction_results(self, num_students: int = 5) -> List[Dict[str, Any]]:
        """Generate mock K-12 ultra-advanced prediction results."""
        results = []
        
        for i in range(num_students):
            risk_prob = np.random.random()
            
            if risk_prob < 0.3:
                risk_level = 'success'
                risk_category = 'Low Risk'
            elif risk_prob < 0.7:
                risk_level = 'warning'
                risk_category = 'Moderate Risk'
            else:
                risk_level = 'danger'
                risk_category = 'High Risk'
            
            result = {
                'student_id': f'S{1000 + i:03d}',
                'name': f'Test Student {i+1}',
                'grade_level': np.random.randint(9, 12),
                'current_gpa': round(np.random.uniform(1.5, 4.0), 2),
                'attendance_rate': round(np.random.uniform(0.7, 1.0), 3),
                'risk_probability': round(risk_prob, 3),
                'risk_category': risk_category,
                'risk_level': risk_level,
                'confidence': round(np.random.uniform(0.8, 0.95), 3),
                'model_type': 'ultra_advanced'
            }
            results.append(result)
        
        return results
    
    def generate_explainable_ai_result(self) -> Dict[str, Any]:
        """Generate mock explainable AI result."""
        return {
            'student_id': 1001,
            'risk_score': 0.75,
            'risk_category': 'High Risk',
            'success_probability': 0.25,
            'confidence': 0.87,
            'explanation': 'Student shows concerning patterns in engagement and assessment performance.',
            'top_risk_factors': [
                {'factor': 'Low engagement clicks', 'impact': 0.23, 'severity': 'high'},
                {'factor': 'Poor early assessment scores', 'impact': 0.19, 'severity': 'medium'},
                {'factor': 'Irregular access patterns', 'impact': 0.15, 'severity': 'medium'}
            ],
            'protective_factors': [
                {'factor': 'Consistent registration', 'strength': 0.12, 'level': 'low'}
            ],
            'recommendations': [
                'Schedule academic support meeting immediately',
                'Implement engagement improvement plan',
                'Monitor daily progress closely'
            ]
        }

# Create a global instance for easy access
mock_data = MockDataGenerator()

# Sample data for tests
SAMPLE_PREDICTION_RESULTS = mock_data.generate_prediction_results(10)
SAMPLE_K12_RESULTS = mock_data.generate_k12_prediction_results(5)
SAMPLE_EXPLAINABLE_AI_RESULT = mock_data.generate_explainable_ai_result()
SAMPLE_STUDENT_FEATURES = mock_data.generate_student_features(5)

# Database sample records
SAMPLE_DATABASE_RECORDS = {
    'institutions': [
        {'name': 'Test High School', 'code': 'THS001', 'type': 'K12'},
        {'name': 'Demo Middle School', 'code': 'DMS002', 'type': 'K12'},
        {'name': 'Sample Elementary', 'code': 'SE003', 'type': 'K12'}
    ],
    'students': [
        {
            'institution_id': 1,
            'student_id': 'S001',
            'grade_level': '9',
            'enrollment_status': 'active',
            'is_ell': False,
            'has_iep': False,
            'has_504': False,
            'is_economically_disadvantaged': False
        },
        {
            'institution_id': 1,
            'student_id': 'S002',
            'grade_level': '10',
            'enrollment_status': 'active',
            'is_ell': True,
            'has_iep': False,
            'has_504': True,
            'is_economically_disadvantaged': True
        }
    ],
    'predictions': [
        {
            'institution_id': 1,
            'student_id': 1,
            'risk_score': 0.25,
            'risk_category': 'Low Risk',
            'success_probability': 0.75,
            'confidence_score': 0.89,
            'model_version': '1.0',
            'model_type': 'binary',
            'session_id': 'test_session_1',
            'data_source': 'test'
        },
        {
            'institution_id': 1,
            'student_id': 2,
            'risk_score': 0.78,
            'risk_category': 'High Risk',
            'success_probability': 0.22,
            'confidence_score': 0.82,
            'model_version': '1.0',
            'model_type': 'binary',
            'session_id': 'test_session_2',
            'data_source': 'test'
        }
    ]
}

def _create_mock_dataframe(data_list):
    """Helper to create mock pandas DataFrame."""
    return pd.DataFrame(data_list)

# Add the helper method to the mock_data instance
mock_data._create_mock_dataframe = _create_mock_dataframe