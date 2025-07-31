#!/usr/bin/env python3
"""
K-12 Explainable AI System

Provides detailed, grade-appropriate explanations for K-12 student success predictions
with actionable insights for educators, parents, and administrators.
"""

import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class K12ExplainableAI:
    """Explainable AI system specifically designed for K-12 education context."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the K-12 explainable AI system."""
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.feature_importance = {}
        self.model_metadata = {}
        
        # K-12 specific feature categories and interpretations
        self.feature_categories = {
            'academic_performance': {
                'features': ['gpa', 'grade', 'course', 'credit', 'academic', 'subject'],
                'weight': 0.4,
                'description': 'Academic achievement and progress'
            },
            'attendance_engagement': {
                'features': ['attendance', 'behavior', 'engagement', 'extracurricular', 'participation'],
                'weight': 0.3,
                'description': 'School engagement and participation'
            },
            'early_warning': {
                'features': ['warning', 'chronic', 'failure', 'disciplinary', 'suspension', 'retention'],
                'weight': 0.2,
                'description': 'Early warning indicators'
            },
            'demographics': {
                'features': ['age', 'lunch', 'ell', 'iep', '504', 'socioeconomic'],
                'weight': 0.1,
                'description': 'Student characteristics and support needs'
            }
        }
        
        # Grade band specific messaging
        self.grade_bands = {
            'elementary': {
                'range': list(range(0, 6)),
                'focus': 'foundational skills',
                'key_factors': ['reading proficiency', 'attendance', 'behavior', 'family engagement']
            },
            'middle': {
                'range': list(range(6, 9)),
                'focus': 'transition and engagement',
                'key_factors': ['course performance', 'engagement drop', 'peer relationships', 'study habits']
            },
            'high': {
                'range': list(range(9, 13)),
                'focus': 'graduation readiness',
                'key_factors': ['credit accumulation', 'attendance', 'course failures', 'college/career prep']
            }
        }
        
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Load the trained K-12 model and associated metadata."""
        model_dir = Path(model_path).parent
        
        # Load model files
        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")
        
        self.model = joblib.load(model_file)
        
        # Load scaler if it exists
        scaler_files = list(model_dir.glob("k12_scaler_*.pkl"))
        if scaler_files:
            latest_scaler = max(scaler_files, key=lambda f: f.stat().st_mtime)
            self.scaler = joblib.load(latest_scaler)
        
        # Load metadata
        metadata_files = list(model_dir.glob("k12_model_metadata_*.json"))
        if metadata_files:
            latest_metadata = max(metadata_files, key=lambda f: f.stat().st_mtime)
            with open(latest_metadata, 'r') as f:
                self.model_metadata = json.load(f)
                self.feature_importance = self.model_metadata.get('feature_importance', {})
        
        # Load feature names
        feature_names_file = Path("data/k12_synthetic/feature_names.json")
        if feature_names_file.exists():
            with open(feature_names_file, 'r') as f:
                self.feature_names = json.load(f)
        
        print(f"✅ K-12 model loaded: {self.model_metadata.get('best_model', 'Unknown')}")
        print(f"📊 Features: {len(self.feature_names)}")
        print(f"🎯 Model AUC: {self.model_metadata.get('performance_metrics', {}).get(self.model_metadata.get('best_model', ''), {}).get('overall_auc', 'Unknown')}")
    
    def load_latest_model(self):
        """Load the most recently trained K-12 model."""
        models_dir = Path("results/models/k12")
        if not models_dir.exists():
            raise FileNotFoundError("No K-12 models directory found. Train a model first.")
        
        model_files = list(models_dir.glob("k12_best_model_*.pkl"))
        if not model_files:
            raise FileNotFoundError("No K-12 models found. Train a model first.")
        
        latest_model = max(model_files, key=lambda f: f.stat().st_mtime)
        self.load_model(str(latest_model))
    
    def predict_with_explanation(self, student_data: Dict) -> Dict:
        """Generate prediction with detailed K-12 appropriate explanation."""
        if self.model is None:
            self.load_latest_model()
        
        # Prepare input data
        X = self._prepare_input_data(student_data)
        
        # Make prediction
        if self.scaler and self.model_metadata.get('use_scaling', False):
            X_scaled = self.scaler.transform(X)
            prediction_proba = self.model.predict_proba(X_scaled)[0]
            prediction = self.model.predict(X_scaled)[0]
        else:
            prediction_proba = self.model.predict_proba(X)[0]
            prediction = self.model.predict(X)[0]
        
        success_probability = prediction_proba[1]
        risk_score = 1 - success_probability
        
        # Determine risk category
        risk_category = self._get_risk_category(risk_score)
        
        # Get grade band
        grade_level = student_data.get('grade_level', 0)
        grade_band = self._get_grade_band(grade_level)
        
        # Generate detailed explanation
        explanation = self._generate_detailed_explanation(
            student_data, X, success_probability, risk_category, grade_band
        )
        
        return {
            'student_id': student_data.get('student_id', 'Unknown'),
            'grade_level': grade_level,
            'grade_band': grade_band,
            'prediction': {
                'success_probability': round(success_probability, 3),
                'risk_score': round(risk_score, 3),
                'risk_category': risk_category,
                'predicted_outcome': 'Success' if prediction == 1 else 'At Risk'
            },
            'explanation': explanation,
            'model_info': {
                'model_type': self.model_metadata.get('best_model', 'Unknown'),
                'model_auc': self.model_metadata.get('performance_metrics', {}).get(
                    self.model_metadata.get('best_model', ''), {}
                ).get('overall_auc', 'Unknown')
            }
        }
    
    def _prepare_input_data(self, student_data: Dict) -> np.ndarray:
        """Prepare student data for model input."""
        # Create feature vector with defaults
        feature_vector = []
        
        for feature_name in self.feature_names:
            if feature_name in student_data:
                feature_vector.append(student_data[feature_name])
            else:
                # Use reasonable defaults based on feature type
                if 'rate' in feature_name.lower() or 'probability' in feature_name.lower():
                    feature_vector.append(0.5)  # Neutral probability
                elif 'score' in feature_name.lower() or 'gpa' in feature_name.lower():
                    feature_vector.append(2.5)  # Average performance
                elif any(risk_term in feature_name.lower() for risk_term in ['risk', 'warning', 'failure']):
                    feature_vector.append(0)  # No risk by default
                else:
                    feature_vector.append(0)  # Default to 0
        
        return np.array(feature_vector).reshape(1, -1)
    
    def _get_risk_category(self, risk_score: float) -> str:
        """Determine risk category based on score."""
        if risk_score >= 0.7:
            return 'High Risk'
        elif risk_score >= 0.4:
            return 'Medium Risk'
        else:
            return 'Low Risk'
    
    def _get_grade_band(self, grade_level: int) -> str:
        """Determine grade band for grade-appropriate messaging."""
        if grade_level <= 5:
            return 'elementary'
        elif grade_level <= 8:
            return 'middle'
        else:
            return 'high'
    
    def _generate_detailed_explanation(self, student_data: Dict, X: np.ndarray, 
                                     success_probability: float, risk_category: str, 
                                     grade_band: str) -> Dict:
        """Generate comprehensive, grade-appropriate explanation."""
        
        # Analyze feature contributions
        feature_contributions = self._analyze_feature_contributions(X[0])
        
        # Identify key factors
        risk_factors = self._identify_risk_factors(feature_contributions, student_data, grade_band)
        protective_factors = self._identify_protective_factors(feature_contributions, student_data, grade_band)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, protective_factors, grade_band, student_data)
        
        # Create grade-appropriate summary
        summary = self._create_grade_appropriate_summary(
            success_probability, risk_category, grade_band, student_data
        )
        
        return {
            'summary': summary,
            'key_insights': {
                'risk_factors': risk_factors,
                'protective_factors': protective_factors,
                'grade_band_focus': self.grade_bands[grade_band]['focus']
            },
            'recommendations': recommendations,
            'confidence_indicators': {
                'model_confidence': self._calculate_confidence(success_probability),
                'data_completeness': self._assess_data_completeness(student_data),
                'grade_band_relevance': 'High'  # Always high for K-12 specific model
            }
        }
    
    def _analyze_feature_contributions(self, feature_values: np.ndarray) -> Dict[str, float]:
        """Analyze how each feature contributes to the prediction."""
        contributions = {}
        
        # Use feature importance as proxy for contribution
        for i, feature_name in enumerate(self.feature_names):
            importance = self.feature_importance.get(feature_name, 0)
            value = feature_values[i]
            
            # Simple contribution calculation (importance * normalized value)
            normalized_value = min(max(value, 0), 1) if 'rate' in feature_name else value
            contribution = importance * normalized_value
            contributions[feature_name] = contribution
        
        return contributions
    
    def _identify_risk_factors(self, contributions: Dict[str, float], 
                              student_data: Dict, grade_band: str) -> List[Dict]:
        """Identify specific risk factors for this student."""
        risk_factors = []
        
        # Check key risk indicators by category
        risk_checks = {
            'Academic Performance': {
                'low_gpa': lambda: student_data.get('current_gpa', 4.0) < 2.5,
                'course_failures': lambda: student_data.get('course_failures_total', 0) > 0,
                'below_grade_level': lambda: student_data.get('gpa_below_grade_expectation', 0) == 1
            },
            'Attendance & Engagement': {
                'chronic_absenteeism': lambda: student_data.get('chronic_absenteeism', 0) == 1,
                'low_attendance': lambda: student_data.get('attendance_rate', 1.0) < 0.90,
                'behavior_issues': lambda: student_data.get('has_disciplinary_issues', 0) == 1
            },
            'Early Warning Indicators': {
                'multiple_risk_factors': lambda: student_data.get('multiple_risk_indicators', 0) >= 2,
                'grade_retention': lambda: student_data.get('grade_retained_ever', 0) == 1,
                'high_risk_classification': lambda: student_data.get('high_risk_student', 0) == 1
            }
        }
        
        for category, checks in risk_checks.items():
            for factor_name, check_func in checks.items():
                try:
                    if check_func():
                        severity = self._calculate_factor_severity(factor_name, student_data, contributions)
                        risk_factors.append({
                            'factor': self._humanize_factor_name(factor_name),
                            'category': category,
                            'severity': severity,
                            'description': self._get_factor_description(factor_name, grade_band, 'risk'),
                            'impact': contributions.get(factor_name, 0)
                        })
                except (KeyError, TypeError):
                    continue
        
        # Sort by severity and impact
        risk_factors.sort(key=lambda x: (x['severity'], x['impact']), reverse=True)
        return risk_factors[:5]  # Top 5 risk factors
    
    def _identify_protective_factors(self, contributions: Dict[str, float], 
                                   student_data: Dict, grade_band: str) -> List[Dict]:
        """Identify protective factors supporting student success."""
        protective_factors = []
        
        protective_checks = {
            'Academic Strengths': {
                'high_gpa': lambda: student_data.get('current_gpa', 0) >= 3.5,
                'positive_gpa_trend': lambda: student_data.get('gpa_trend_positive', 0) == 1,
                'no_course_failures': lambda: student_data.get('course_failures_total', 1) == 0
            },
            'Strong Engagement': {
                'excellent_attendance': lambda: student_data.get('attendance_excellent', 0) == 1,
                'high_engagement': lambda: student_data.get('engagement_composite', 0) >= 0.8,
                'extracurricular_participation': lambda: student_data.get('multiple_extracurriculars', 0) == 1
            },
            'Support Systems': {
                'parent_engagement': lambda: student_data.get('high_parent_engagement', 0) == 1,
                'gifted_program': lambda: student_data.get('gifted_program', 0) == 1,
                'technology_access': lambda: student_data.get('technology_access', 0) == 1
            }
        }
        
        for category, checks in protective_checks.items():
            for factor_name, check_func in checks.items():
                try:
                    if check_func():
                        strength = self._calculate_factor_strength(factor_name, student_data, contributions)
                        protective_factors.append({
                            'factor': self._humanize_factor_name(factor_name),
                            'category': category,
                            'strength': strength,
                            'description': self._get_factor_description(factor_name, grade_band, 'protective'),
                            'impact': contributions.get(factor_name, 0)
                        })
                except (KeyError, TypeError):
                    continue
        
        protective_factors.sort(key=lambda x: (x['strength'], x['impact']), reverse=True)
        return protective_factors[:5]  # Top 5 protective factors
    
    def _generate_recommendations(self, risk_factors: List[Dict], protective_factors: List[Dict], 
                                grade_band: str, student_data: Dict) -> Dict:
        """Generate grade-appropriate intervention recommendations."""
        recommendations = {
            'immediate_actions': [],
            'ongoing_support': [],
            'family_engagement': [],
            'monitoring_plan': []
        }
        
        grade_level = student_data.get('grade_level', 0)
        
        # Immediate actions based on risk factors
        for risk_factor in risk_factors[:3]:  # Top 3 risks
            if 'attendance' in risk_factor['factor'].lower():
                recommendations['immediate_actions'].append({
                    'action': 'Implement attendance intervention plan',
                    'description': f'Work with family to address attendance barriers and create daily check-in system',
                    'priority': 'High',
                    'timeline': '1-2 weeks'
                })
            elif 'academic' in risk_factor['category'].lower():
                if grade_band == 'elementary':
                    recommendations['immediate_actions'].append({
                        'action': 'Provide targeted academic support',
                        'description': 'Implement small group instruction and peer tutoring for foundational skills',
                        'priority': 'High',
                        'timeline': '2-4 weeks'
                    })
                else:
                    recommendations['immediate_actions'].append({
                        'action': 'Academic intervention and credit recovery',
                        'description': 'Provide intensive tutoring and consider credit recovery options',
                        'priority': 'High',
                        'timeline': '4-6 weeks'
                    })
        
        # Ongoing support based on grade band
        if grade_band == 'elementary':
            recommendations['ongoing_support'] = [
                'Daily reading practice with family involvement',
                'Social-emotional learning activities',
                'Regular progress monitoring meetings'
            ]
        elif grade_band == 'middle':
            recommendations['ongoing_support'] = [
                'Study skills and organization training',
                'Peer mentoring program',
                'Regular counselor check-ins'
            ]
        else:  # high school
            recommendations['ongoing_support'] = [
                'College and career planning sessions',
                'Credit tracking and graduation planning',
                'Work-based learning opportunities'
            ]
        
        # Family engagement strategies
        if student_data.get('low_parent_engagement', 0) == 1:
            recommendations['family_engagement'] = [
                'Schedule regular family conferences',
                'Provide home learning resources',
                'Connect family with community supports'
            ]
        else:
            recommendations['family_engagement'] = [
                'Continue strong home-school partnership',
                'Share progress updates regularly',
                'Involve family in goal setting'
            ]
        
        # Monitoring plan
        recommendations['monitoring_plan'] = [
            'Weekly progress check-ins',
            'Monthly data review meetings',
            'Quarterly intervention plan updates'
        ]
        
        return recommendations
    
    def _humanize_factor_name(self, factor_name: str) -> str:
        """Convert technical factor names to human-readable descriptions."""
        humanized_names = {
            'low_gpa': 'Below Grade-Level Academic Performance',
            'course_failures': 'Course Failures',
            'chronic_absenteeism': 'Chronic Absenteeism',
            'behavior_issues': 'Behavioral Concerns',
            'high_gpa': 'Strong Academic Performance',
            'excellent_attendance': 'Excellent Attendance',
            'parent_engagement': 'Strong Family Support',
            'multiple_risk_factors': 'Multiple Risk Indicators',
            'high_engagement': 'High School Engagement',
            'extracurricular_participation': 'Extracurricular Involvement'
        }
        
        return humanized_names.get(factor_name, factor_name.replace('_', ' ').title())
    
    def _get_factor_description(self, factor_name: str, grade_band: str, factor_type: str) -> str:
        """Get detailed description for a risk or protective factor."""
        descriptions = {
            'elementary': {
                'risk': {
                    'low_gpa': 'Student is not meeting grade-level expectations in core subjects',
                    'chronic_absenteeism': 'Missing too many school days affects learning foundation',
                    'course_failures': 'Struggling with essential elementary skills'
                },
                'protective': {
                    'high_gpa': 'Demonstrates strong mastery of grade-level skills',
                    'excellent_attendance': 'Consistent presence supports continuous learning',
                    'parent_engagement': 'Family involvement strongly supports elementary success'
                }
            },
            'middle': {
                'risk': {
                    'low_gpa': 'Academic performance decline during critical transition years',
                    'chronic_absenteeism': 'Missing school during important developmental period',
                    'behavior_issues': 'Behavioral challenges typical of middle school transition'
                },
                'protective': {
                    'high_gpa': 'Maintaining strong academics during challenging transition',
                    'high_engagement': 'Staying connected despite typical middle school challenges'
                }
            },
            'high': {
                'risk': {
                    'course_failures': 'Course failures threaten graduation timeline',
                    'chronic_absenteeism': 'Poor attendance jeopardizes graduation requirements',
                    'low_gpa': 'GPA impacts college and career opportunities'
                },
                'protective': {
                    'high_gpa': 'Strong GPA supports college and career readiness',
                    'excellent_attendance': 'Consistent attendance supports graduation success'
                }
            }
        }
        
        return descriptions.get(grade_band, {}).get(factor_type, {}).get(
            factor_name, 'Important factor for student success'
        )
    
    def _calculate_factor_severity(self, factor_name: str, student_data: Dict, 
                                 contributions: Dict) -> str:
        """Calculate severity level for risk factors."""
        # Simple severity calculation based on factor type and value
        if 'chronic' in factor_name or 'failure' in factor_name:
            return 'High'
        elif 'low' in factor_name or 'below' in factor_name:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_factor_strength(self, factor_name: str, student_data: Dict, 
                                 contributions: Dict) -> str:
        """Calculate strength level for protective factors."""
        if 'excellent' in factor_name or 'high' in factor_name:
            return 'High'
        elif 'good' in factor_name or 'positive' in factor_name:
            return 'Medium'
        else:
            return 'Low'
    
    def _create_grade_appropriate_summary(self, success_probability: float, 
                                        risk_category: str, grade_band: str, 
                                        student_data: Dict) -> str:
        """Create a grade-appropriate summary of the prediction."""
        grade_level = student_data.get('grade_level', 0)
        grade_name = f"Grade {grade_level}" if grade_level > 0 else "Kindergarten"
        
        if success_probability >= 0.8:
            if grade_band == 'elementary':
                summary = f"This {grade_name} student is on track for academic success with strong foundational skills."
            elif grade_band == 'middle':
                summary = f"This {grade_name} student is successfully navigating the middle school transition."
            else:
                summary = f"This {grade_name} student is on track for graduation and post-secondary success."
        elif success_probability >= 0.6:
            summary = f"This {grade_name} student shows promise but would benefit from targeted support to ensure continued success."
        else:
            if grade_band == 'elementary':
                summary = f"This {grade_name} student needs immediate intervention to build essential foundational skills."
            elif grade_band == 'middle':
                summary = f"This {grade_name} student is struggling with the middle school transition and needs comprehensive support."
            else:
                summary = f"This {grade_name} student is at risk of not graduating and needs intensive intervention."
        
        return summary
    
    def _calculate_confidence(self, success_probability: float) -> str:
        """Calculate model confidence level."""
        # Confidence is higher when probability is further from 0.5 (uncertain)
        distance_from_uncertain = abs(success_probability - 0.5)
        
        if distance_from_uncertain >= 0.4:
            return 'High'
        elif distance_from_uncertain >= 0.2:
            return 'Medium'
        else:
            return 'Low'
    
    def _assess_data_completeness(self, student_data: Dict) -> str:
        """Assess completeness of available student data."""
        required_fields = ['grade_level', 'current_gpa', 'attendance_rate', 'behavior_score']
        available_fields = sum(1 for field in required_fields if field in student_data)
        
        completeness_ratio = available_fields / len(required_fields)
        
        if completeness_ratio >= 0.8:
            return 'High'
        elif completeness_ratio >= 0.6:
            return 'Medium'
        else:
            return 'Low'

def main():
    """Test the K-12 Explainable AI system."""
    # Initialize the explainable AI system
    explainer = K12ExplainableAI()
    
    try:
        explainer.load_latest_model()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return
    
    # Test with sample student data
    sample_students = [
        {
            'student_id': 'TEST_001',
            'grade_level': 3,
            'current_gpa': 2.1,
            'attendance_rate': 0.85,
            'chronic_absenteeism': 1,
            'behavior_score': 0.9,
            'course_failures_total': 1,
            'free_reduced_lunch': 1,
            'ell_status': 0,
            'parent_engagement_level': 1
        },
        {
            'student_id': 'TEST_002',
            'grade_level': 8,
            'current_gpa': 3.8,
            'attendance_rate': 0.96,
            'chronic_absenteeism': 0,
            'behavior_score': 0.95,
            'course_failures_total': 0,
            'extracurricular_count': 2,
            'parent_engagement_level': 2
        },
        {
            'student_id': 'TEST_003',
            'grade_level': 11,
            'current_gpa': 2.3,
            'attendance_rate': 0.78,
            'chronic_absenteeism': 1,
            'course_failures_total': 3,
            'credits_earned': 18,
            'disciplinary_incidents': 5
        }
    ]
    
    print("🎓 K-12 Explainable AI Testing")
    print("=" * 50)
    
    for i, student in enumerate(sample_students, 1):
        print(f"\n📊 Sample Student {i} Analysis:")
        print("-" * 30)
        
        explanation = explainer.predict_with_explanation(student)
        
        print(f"Student: {explanation['student_id']} ({explanation['grade_band'].title()} - Grade {explanation['grade_level']})")
        print(f"Prediction: {explanation['prediction']['predicted_outcome']}")
        print(f"Success Probability: {explanation['prediction']['success_probability']:.1%}")
        print(f"Risk Category: {explanation['prediction']['risk_category']}")
        print(f"\nSummary: {explanation['explanation']['summary']}")
        
        print(f"\nTop Risk Factors:")
        for factor in explanation['explanation']['key_insights']['risk_factors']:
            print(f"  • {factor['factor']} ({factor['severity']} severity)")
        
        print(f"\nTop Protective Factors:")
        for factor in explanation['explanation']['key_insights']['protective_factors']:
            print(f"  • {factor['factor']} ({factor['strength']} strength)")
        
        print(f"\nImmediate Actions:")
        for action in explanation['explanation']['recommendations']['immediate_actions'][:2]:
            print(f"  • {action['action']}")
    
    print(f"\n🎉 K-12 Explainable AI testing complete!")

if __name__ == "__main__":
    main()