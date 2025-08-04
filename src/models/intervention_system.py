#!/usr/bin/env python3
"""
Intervention Recommendation System

This module provides personalized intervention recommendations for at-risk students
based on their risk profile and feature patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import joblib
import json
import os
from typing import Dict, List, Tuple, Optional
import warnings
import sys
warnings.filterwarnings('ignore')

# Import explainable AI module
sys.path.append(str(Path(__file__).parent))
from explainable_ai import ExplainableAI

class InterventionRecommendationSystem:
    """
    Intelligent intervention recommendation system for at-risk students
    """
    
    def __init__(self, models_dir: Path = None):
        """
        Initialize the intervention system
        
        Args:
            models_dir: Directory containing trained models
        """
        if models_dir is None:
            # Use environment variable if set (for production deployments)
            models_env = os.getenv('MODELS_DIR')
            if models_env:
                models_dir = Path(models_env)
            else:
                # Calculate relative to current working directory (more reliable)
                import os
                cwd = Path(os.getcwd())
                models_dir = cwd / "results" / "models"
                
                # If not found, try relative to file location
                if not models_dir.exists():
                    file_based = Path(__file__).parent.parent.parent / "results" / "models"
                    if file_based.exists():
                        models_dir = file_based
        self.models_dir = models_dir
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.explainable_ai = None
        self.load_models()
        
    def load_models(self):
        """Load trained models and components"""
        try:
            # Load the best binary model for risk assessment
            self.model = joblib.load(self.models_dir / "best_binary_model.pkl")
            
            # Load scaler (might be None for tree-based models)
            scaler_path = self.models_dir / "binary_scaler.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
            
            # Load feature columns
            with open(self.models_dir / "feature_columns.json", 'r') as f:
                self.feature_columns = json.load(f)
            
            # Initialize explainable AI
            self.explainable_ai = ExplainableAI(self.model, self.feature_columns)
                
            print(f"✅ Models loaded successfully from {self.models_dir}")
            print(f"✅ Explainable AI initialized with {len(self.feature_columns)} features")
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            raise
    
    def assess_student_risk(self, student_data: pd.DataFrame) -> pd.DataFrame:
        """
        Assess risk level for students
        
        Args:
            student_data: DataFrame with student features
            
        Returns:
            DataFrame with risk assessment
        """
        # Prepare features
        features = student_data[self.feature_columns]
        
        # Apply scaling if needed
        if self.scaler is not None:
            features_scaled = self.scaler.transform(features)
            success_proba = self.model.predict_proba(features_scaled)[:, 1]
        else:
            success_proba = self.model.predict_proba(features)[:, 1]
        
        # Calculate risk metrics
        risk_score = 1 - success_proba
        
        # Assign risk categories
        risk_category = pd.cut(risk_score, 
                              bins=[0, 0.3, 0.6, 1.0], 
                              labels=['Low Risk', 'Medium Risk', 'High Risk'])
        
        # Create results
        results = pd.DataFrame({
            'student_id': student_data.get('id_student', range(len(student_data))),
            'success_probability': success_proba,
            'risk_score': risk_score,
            'risk_category': risk_category,
            'needs_intervention': risk_score > 0.5
        })
        
        return results
    
    def analyze_risk_factors(self, student_data: pd.DataFrame) -> Dict:
        """
        Analyze individual risk factors for a student
        
        Args:
            student_data: Single student's feature data
            
        Returns:
            Dictionary of risk factor analysis
        """
        if len(student_data) != 1:
            raise ValueError("This method works with single student data only")
        
        # Get feature importance if available
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        else:
            feature_importance = {col: 1.0 for col in self.feature_columns}
        
        # Analyze student's feature values
        student_features = student_data[self.feature_columns].iloc[0]
        
        risk_factors = {
            'demographic': self._analyze_demographic_risk(student_features),
            'engagement': self._analyze_engagement_risk(student_features),
            'assessment': self._analyze_assessment_risk(student_features),
            'overall_risk': self.assess_student_risk(student_data)['risk_score'].iloc[0]
        }
        
        return risk_factors
    
    def _analyze_demographic_risk(self, student_features: pd.Series) -> Dict:
        """Analyze demographic risk factors"""
        risk_factors = []
        
        # Age risk
        age_band = student_features.get('age_band_encoded', 0)
        if age_band == 0:  # 0-35 age group
            risk_factors.append("Young age group - may need time management support")
        elif age_band == 2:  # 55+ age group
            risk_factors.append("Mature learner - may need technology support")
        
        # Education level
        education = student_features.get('education_encoded', 0)
        if education < 2:  # Below A-level
            risk_factors.append("Lower education background - may need foundational support")
        
        # Previous attempts
        prev_attempts = student_features.get('num_of_prev_attempts', 0)
        if prev_attempts > 0:
            risk_factors.append(f"Previous attempts: {prev_attempts} - may need motivation support")
        
        # Registration delay
        reg_delay = student_features.get('registration_delay', 0)
        if reg_delay > 10:
            risk_factors.append("Late registration - may need catch-up support")
        
        return {
            'risk_factors': risk_factors,
            'risk_level': 'High' if len(risk_factors) >= 2 else 'Medium' if len(risk_factors) == 1 else 'Low'
        }
    
    def _analyze_engagement_risk(self, student_features: pd.Series) -> Dict:
        """Analyze VLE engagement risk factors"""
        risk_factors = []
        
        # Total clicks
        total_clicks = student_features.get('early_total_clicks', 0)
        if total_clicks < 100:
            risk_factors.append("Very low VLE engagement - needs immediate attention")
        elif total_clicks < 500:
            risk_factors.append("Low VLE engagement - encourage more interaction")
        
        # Active days
        active_days = student_features.get('early_active_days', 0)
        if active_days < 5:
            risk_factors.append("Very few active days - needs engagement boost")
        elif active_days < 15:
            risk_factors.append("Irregular engagement pattern - needs consistency")
        
        # Engagement consistency
        consistency = student_features.get('early_engagement_consistency', 0)
        if consistency < 0.3:
            risk_factors.append("Inconsistent engagement - needs routine building")
        
        return {
            'risk_factors': risk_factors,
            'risk_level': 'High' if len(risk_factors) >= 2 else 'Medium' if len(risk_factors) == 1 else 'Low'
        }
    
    def _analyze_assessment_risk(self, student_features: pd.Series) -> Dict:
        """Analyze assessment performance risk factors"""
        risk_factors = []
        
        # Average score
        avg_score = student_features.get('early_avg_score', 0)
        if avg_score < 40:
            risk_factors.append("Very low assessment scores - needs academic support")
        elif avg_score < 60:
            risk_factors.append("Below average scores - needs improvement strategies")
        
        # Submission rate
        submission_rate = student_features.get('early_submission_rate', 0)
        if submission_rate < 0.5:
            risk_factors.append("Poor submission rate - needs deadline management")
        elif submission_rate < 0.8:
            risk_factors.append("Some missing submissions - needs organization support")
        
        # Assessment count
        assessment_count = student_features.get('early_assessments_count', 0)
        if assessment_count < 2:
            risk_factors.append("Very few assessments completed - needs immediate intervention")
        
        return {
            'risk_factors': risk_factors,
            'risk_level': 'High' if len(risk_factors) >= 2 else 'Medium' if len(risk_factors) == 1 else 'Low'
        }
    
    def get_intervention_recommendations(self, student_data: pd.DataFrame) -> List[Dict]:
        """
        Generate personalized intervention recommendations
        
        Args:
            student_data: DataFrame with student features
            
        Returns:
            List of intervention recommendations
        """
        recommendations = []
        
        for idx, student in student_data.iterrows():
            student_df = pd.DataFrame([student])
            risk_assessment = self.assess_student_risk(student_df)
            risk_factors = self.analyze_risk_factors(student_df)
            
            # Generate recommendations based on risk level and factors
            interventions = self._generate_specific_interventions(
                risk_assessment.iloc[0], 
                risk_factors
            )
            
            recommendations.append({
                'student_id': student.get('id_student', idx),
                'risk_level': risk_assessment.iloc[0]['risk_category'],
                'risk_score': risk_assessment.iloc[0]['risk_score'],
                'interventions': interventions,
                'priority': self._calculate_intervention_priority(risk_assessment.iloc[0], risk_factors)
            })
        
        return recommendations
    
    def _generate_specific_interventions(self, risk_assessment: pd.Series, risk_factors: Dict) -> List[Dict]:
        """Generate specific intervention recommendations"""
        interventions = []
        
        # High-level risk interventions
        if risk_assessment['risk_category'] == 'High Risk':
            interventions.extend([
                {
                    'type': 'immediate',
                    'category': 'academic_support',
                    'title': 'Immediate Academic Intervention',
                    'description': 'Schedule urgent meeting with academic advisor',
                    'timeline': 'Within 24 hours',
                    'resources': ['Academic Advisor', 'Study Skills Workshop'],
                    'cost': 'High'
                },
                {
                    'type': 'ongoing',
                    'category': 'mentoring',
                    'title': 'Intensive Mentoring Program',
                    'description': 'Assign dedicated mentor for weekly check-ins',
                    'timeline': 'Ongoing - weekly',
                    'resources': ['Peer Mentor', 'Faculty Advisor'],
                    'cost': 'Medium'
                }
            ])
        
        # Engagement-specific interventions
        if risk_factors['engagement']['risk_level'] in ['High', 'Medium']:
            interventions.append({
                'type': 'behavioral',
                'category': 'engagement',
                'title': 'VLE Engagement Boost',
                'description': 'Gamification and engagement strategies',
                'timeline': '2-3 weeks',
                'resources': ['Learning Technology Team', 'Engagement Platform'],
                'cost': 'Low'
            })
        
        # Assessment-specific interventions
        if risk_factors['assessment']['risk_level'] in ['High', 'Medium']:
            interventions.append({
                'type': 'academic',
                'category': 'assessment_support',
                'title': 'Assessment Skills Development',
                'description': 'Workshops on assessment strategies and time management',
                'timeline': '1-2 weeks',
                'resources': ['Study Skills Center', 'Writing Center'],
                'cost': 'Medium'
            })
        
        # Demographic-specific interventions
        if risk_factors['demographic']['risk_level'] in ['High', 'Medium']:
            interventions.append({
                'type': 'support',
                'category': 'demographic_support',
                'title': 'Targeted Support Services',
                'description': 'Specialized support based on demographic needs',
                'timeline': 'Ongoing',
                'resources': ['Student Support Services', 'Counseling Center'],
                'cost': 'Variable'
            })
        
        return interventions
    
    def _calculate_intervention_priority(self, risk_assessment: pd.Series, risk_factors: Dict) -> str:
        """Calculate intervention priority"""
        risk_score = risk_assessment['risk_score']
        
        if risk_score > 0.8:
            return 'Critical'
        elif risk_score > 0.6:
            return 'High'
        elif risk_score > 0.4:
            return 'Medium'
        else:
            return 'Low'
    
    def generate_intervention_report(self, student_data: pd.DataFrame) -> str:
        """
        Generate a comprehensive intervention report
        
        Args:
            student_data: DataFrame with student features
            
        Returns:
            Formatted intervention report
        """
        recommendations = self.get_intervention_recommendations(student_data)
        
        report = []
        report.append("=" * 80)
        report.append("STUDENT INTERVENTION RECOMMENDATIONS REPORT")
        report.append("=" * 80)
        
        # Summary statistics
        total_students = len(recommendations)
        high_risk = sum(1 for r in recommendations if r['risk_level'] == 'High Risk')
        medium_risk = sum(1 for r in recommendations if r['risk_level'] == 'Medium Risk')
        critical_priority = sum(1 for r in recommendations if r['priority'] == 'Critical')
        
        report.append(f"\\nSUMMARY:")
        report.append(f"Total Students Assessed: {total_students}")
        report.append(f"High Risk Students: {high_risk}")
        report.append(f"Medium Risk Students: {medium_risk}")
        report.append(f"Critical Priority Interventions: {critical_priority}")
        
        # Individual recommendations
        for rec in recommendations:
            if rec['risk_level'] != 'Low Risk':  # Focus on students needing intervention
                report.append(f"\\n{'-' * 60}")
                report.append(f"STUDENT ID: {rec['student_id']}")
                report.append(f"Risk Level: {rec['risk_level']}")
                report.append(f"Risk Score: {rec['risk_score']:.3f}")
                report.append(f"Priority: {rec['priority']}")
                
                report.append("\\nRECOMMENDED INTERVENTIONS:")
                for i, intervention in enumerate(rec['interventions'], 1):
                    report.append(f"  {i}. {intervention['title']}")
                    report.append(f"     Type: {intervention['type']}")
                    report.append(f"     Timeline: {intervention['timeline']}")
                    report.append(f"     Resources: {', '.join(intervention['resources'])}")
                    report.append(f"     Cost: {intervention['cost']}")
                    report.append("")
        
        return "\\n".join(report)

    def get_explainable_predictions(self, student_data: pd.DataFrame) -> List[Dict]:
        """
        Get explainable predictions for students with detailed reasoning
        
        Args:
            student_data: DataFrame with student features
            
        Returns:
            List of detailed prediction explanations
        """
        try:
            # Get risk predictions
            risk_results = self.assess_student_risk(student_data)
            
            explanations = []
            for i, (_, row) in enumerate(risk_results.iterrows()):
                student_dict = student_data.iloc[i].to_dict()
                
                # Get detailed explanation
                explanation = self.explainable_ai.explain_prediction(
                    student_dict, 
                    row['risk_score'], 
                    row['risk_category']
                )
                
                explanations.append(explanation)
            
            return explanations
            
        except Exception as e:
            print(f"Error generating explainable predictions: {e}")
            return []
    
    def get_global_insights(self) -> Dict:
        """
        Get global insights about the model and feature importance
        
        Returns:
            Dictionary with global model insights
        """
        try:
            if self.explainable_ai is None:
                return {'error': 'Explainable AI not initialized'}
            
            return self.explainable_ai.get_global_feature_importance()
            
        except Exception as e:
            print(f"Error getting global insights: {e}")
            return {'error': str(e)}
    
    def analyze_risk_trends(self, student_id: int, historical_predictions: List[Dict]) -> Dict:
        """
        Analyze risk trends for a student over time
        
        Args:
            student_id: Student identifier
            historical_predictions: List of historical prediction data
            
        Returns:
            Trend analysis results
        """
        try:
            if self.explainable_ai is None:
                return {'error': 'Explainable AI not initialized'}
            
            return self.explainable_ai.generate_risk_trend_analysis(historical_predictions)
            
        except Exception as e:
            print(f"Error analyzing risk trends: {e}")
            return {'error': str(e)}

def main():
    """Main function to demonstrate the intervention system"""
    # Initialize system
    system = InterventionRecommendationSystem()
    
    # Load sample data
    data_dir = Path("data/processed")
    df = pd.read_csv(data_dir / "student_features_engineered.csv")
    
    # Select a few sample students for demonstration
    sample_students = df.head(10)
    
    print("🎯 INTERVENTION RECOMMENDATION SYSTEM DEMO")
    print("=" * 60)
    
    # Generate recommendations
    recommendations = system.get_intervention_recommendations(sample_students)
    
    # Display results
    print(f"\\nGenerated recommendations for {len(recommendations)} students:")
    
    for rec in recommendations:
        if rec['risk_level'] != 'Low Risk':
            print(f"\\n📋 Student {rec['student_id']}:")
            print(f"   Risk Level: {rec['risk_level']}")
            print(f"   Priority: {rec['priority']}")
            print(f"   Interventions: {len(rec['interventions'])}")
    
    # Generate full report
    print("\\n" + "=" * 60)
    print("GENERATING COMPREHENSIVE REPORT...")
    print("=" * 60)
    
    report = system.generate_intervention_report(sample_students)
    
    # Save report
    reports_dir = Path("results/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    with open(reports_dir / "intervention_report.txt", 'w') as f:
        f.write(report)
    
    print(f"\\n✅ Intervention report saved to {reports_dir}/intervention_report.txt")
    print("\\n🚀 Intervention system ready for deployment!")

if __name__ == "__main__":
    main()