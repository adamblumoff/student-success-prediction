#!/usr/bin/env python3
"""
Unit tests for explainable AI functionality in Student Success Prediction system.

Tests the ExplainableAI class and intervention system explanation features.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import json
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from models.explainable_ai import ExplainableAI
from models.intervention_system import InterventionRecommendationSystem
from tests.fixtures.mock_data import (
    SAMPLE_STUDENT_FEATURES, SAMPLE_EXPLAINABLE_AI_RESULT, mock_data
)

class TestExplainableAIInitialization(unittest.TestCase):
    """Test ExplainableAI class initialization."""
    
    def setUp(self):
        """Set up mock model and features for testing."""
        # Create mock model
        self.mock_model = MagicMock()
        self.mock_model.feature_importances_ = np.array([0.3, 0.2, 0.15, 0.1, 0.25])
        
        # Mock features list
        self.mock_features = [
            'early_avg_score', 'early_total_clicks', 'attendance_rate', 
            'assignment_completion', 'discipline_incidents'
        ]
    
    def test_explainable_ai_initialization(self):
        """Test basic ExplainableAI initialization."""
        explainer = ExplainableAI(self.mock_model, self.mock_features)
        
        self.assertEqual(explainer.model, self.mock_model)
        self.assertEqual(explainer.feature_names, self.mock_features)
        self.assertIsNotNone(explainer.feature_categories)
    
    def test_feature_categorization(self):
        """Test automatic feature categorization."""
        explainer = ExplainableAI(self.mock_model, self.mock_features)
        
        # Should categorize features into logical groups
        categories = explainer.feature_categories
        
        # Should have assessment category for score-related features
        assessment_features = [f for f, cat in categories.items() if cat == 'assessment']
        self.assertIn('early_avg_score', assessment_features)
        
        # Should have engagement category for click-related features
        engagement_features = [f for f, cat in categories.items() if cat == 'engagement']
        self.assertIn('early_total_clicks', engagement_features)
        
        # Should have behavioral category for discipline
        behavioral_features = [f for f, cat in categories.items() if cat == 'behavioral'] 
        self.assertIn('discipline_incidents', behavioral_features)

class TestFeatureImportanceAnalysis(unittest.TestCase):
    """Test feature importance analysis and explanation."""
    
    def setUp(self):
        """Set up explainer with mock data."""
        self.mock_model = MagicMock()
        self.mock_model.feature_importances_ = np.array([0.25, 0.20, 0.18, 0.15, 0.12, 0.10])
        
        self.features = [
            'early_avg_score', 'early_total_clicks', 'attendance_rate',
            'assignment_completion', 'discipline_incidents', 'parent_engagement'
        ]
        
        self.explainer = ExplainableAI(self.mock_model, self.features)
    
    def test_get_feature_importance(self):
        """Test feature importance extraction."""
        importance = self.explainer.get_feature_importance()
        
        # Should return sorted importance scores
        self.assertEqual(len(importance), len(self.features))
        
        # Should be sorted in descending order
        importance_values = [item['importance'] for item in importance]
        self.assertEqual(importance_values, sorted(importance_values, reverse=True))
        
        # Top feature should be early_avg_score
        self.assertEqual(importance[0]['feature'], 'early_avg_score')
        self.assertEqual(importance[0]['importance'], 0.25)
    
    def test_get_category_importance(self):
        """Test category-level importance aggregation."""
        category_importance = self.explainer.get_category_importance()
        
        # Should aggregate features by category
        self.assertIn('assessment', category_importance)
        self.assertIn('engagement', category_importance)
        self.assertIn('behavioral', category_importance)
        
        # Importance values should sum to approximately 1.0
        total_importance = sum(category_importance.values())
        self.assertAlmostEqual(total_importance, 1.0, places=2)
    
    def test_get_top_features(self):
        """Test getting top N features."""
        top_3_features = self.explainer.get_top_features(n=3)
        
        self.assertEqual(len(top_3_features), 3)
        
        # Should be the highest importance features
        expected_top_3 = ['early_avg_score', 'early_total_clicks', 'attendance_rate']
        actual_features = [item['feature'] for item in top_3_features]
        self.assertEqual(actual_features, expected_top_3)

class TestIndividualPredictionExplanation(unittest.TestCase):
    """Test individual student prediction explanations."""
    
    def setUp(self):
        """Set up explainer and sample data."""
        self.mock_model = MagicMock()
        self.mock_model.feature_importances_ = np.array([0.3, 0.25, 0.2, 0.15, 0.1])
        self.mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])  # High risk
        
        self.features = [
            'early_avg_score', 'early_total_clicks', 'attendance_rate',
            'assignment_completion', 'discipline_incidents'
        ]
        
        self.explainer = ExplainableAI(self.mock_model, self.features)
        
        # Sample student data
        self.sample_student = pd.DataFrame([{
            'id_student': 1001,
            'early_avg_score': 45.0,  # Low score - risk factor
            'early_total_clicks': 50,  # Low engagement - risk factor
            'attendance_rate': 0.95,  # Good attendance - protective factor
            'assignment_completion': 0.6,  # Below average - risk factor
            'discipline_incidents': 2  # Some issues - risk factor
        }])
    
    def test_predict_with_explanation_basic(self):
        """Test basic prediction with explanation."""
        explanation = self.explainer.predict_with_explanation(self.sample_student)
        
        # Should return explanation with required fields
        required_fields = [
            'student_id', 'risk_score', 'risk_category', 'explanation',
            'top_risk_factors', 'protective_factors', 'recommendations'
        ]
        
        for field in required_fields:
            self.assertIn(field, explanation)
    
    def test_risk_factor_identification(self):
        """Test identification of risk factors."""
        explanation = self.explainer.predict_with_explanation(self.sample_student)
        
        risk_factors = explanation['top_risk_factors']
        
        # Should identify multiple risk factors
        self.assertGreater(len(risk_factors), 0)
        
        # Should identify low assessment score as risk factor
        risk_factor_names = [rf['factor'] for rf in risk_factors]
        self.assertTrue(any('assessment' in name.lower() or 'score' in name.lower() 
                          for name in risk_factor_names))
        
        # Each risk factor should have impact and severity
        for risk_factor in risk_factors:
            self.assertIn('factor', risk_factor)
            self.assertIn('impact', risk_factor)
            self.assertIn('severity', risk_factor)
    
    def test_protective_factor_identification(self):
        """Test identification of protective factors."""
        explanation = self.explainer.predict_with_explanation(self.sample_student)
        
        protective_factors = explanation['protective_factors']
        
        # Should identify protective factors (good attendance)
        self.assertGreater(len(protective_factors), 0)
        
        # Each protective factor should have strength and impact
        for pf in protective_factors:
            self.assertIn('factor', pf)
            self.assertIn('strength', pf)
            self.assertIn('impact', pf)
    
    def test_recommendation_generation(self):
        """Test generation of actionable recommendations."""
        explanation = self.explainer.predict_with_explanation(self.sample_student)
        
        recommendations = explanation['recommendations']
        
        # Should provide actionable recommendations
        self.assertGreater(len(recommendations), 0)
        self.assertLessEqual(len(recommendations), 5)
        
        # Recommendations should be strings
        for rec in recommendations:
            self.assertIsInstance(rec, str)
            self.assertGreater(len(rec), 10)  # Should be meaningful
    
    def test_explanation_text_generation(self):
        """Test generation of human-readable explanation text."""
        explanation = self.explainer.predict_with_explanation(self.sample_student)
        
        explanation_text = explanation['explanation']
        
        # Should be a meaningful explanation
        self.assertIsInstance(explanation_text, str)
        self.assertGreater(len(explanation_text), 20)
        
        # Should mention key factors
        explanation_lower = explanation_text.lower()
        # Should reference some aspect of the student's situation
        self.assertTrue(any(keyword in explanation_lower 
                          for keyword in ['score', 'performance', 'engagement', 'risk']))

class TestGlobalInsights(unittest.TestCase):
    """Test global model insights functionality."""
    
    def setUp(self):
        """Set up explainer with comprehensive feature set."""
        self.mock_model = MagicMock()
        
        # Create realistic feature importance distribution
        feature_count = 31
        importance_values = np.random.dirichlet(np.ones(feature_count))
        self.mock_model.feature_importances_ = importance_values
        
        # Use actual feature names from the system
        self.features = [
            # Demographics
            'gender_encoded', 'region_encoded', 'age_band_encoded', 'education_encoded',
            'is_male', 'has_disability',
            # Academic History  
            'studied_credits', 'num_of_prev_attempts', 'registration_delay', 'unregistered',
            # Early VLE Engagement
            'early_total_clicks', 'early_avg_clicks', 'early_clicks_std', 'early_max_clicks',
            'early_active_days', 'early_first_access', 'early_last_access',
            'early_engagement_consistency', 'early_clicks_per_active_day', 'early_engagement_range',
            # Early Assessment Performance
            'early_assessments_count', 'early_avg_score', 'early_score_std', 'early_min_score',
            'early_max_score', 'early_missing_submissions', 'early_submitted_count',
            'early_total_weight', 'early_banked_count', 'early_submission_rate', 'early_score_range'
        ]
        
        self.explainer = ExplainableAI(self.mock_model, self.features)
    
    def test_get_global_insights(self):
        """Test global insights generation."""
        insights = self.explainer.get_global_insights()
        
        # Should contain expected sections
        expected_sections = [
            'feature_importance', 'category_importance', 'top_predictive_factors',
            'model_summary'
        ]
        
        for section in expected_sections:
            self.assertIn(section, insights)
    
    def test_feature_importance_insights(self):
        """Test feature importance insights."""
        insights = self.explainer.get_global_insights()
        
        feature_importance = insights['feature_importance']
        
        # Should be sorted list of all features
        self.assertEqual(len(feature_importance), len(self.features))
        
        # Should be sorted by importance (descending)
        importance_values = [item['importance'] for item in feature_importance]
        self.assertEqual(importance_values, sorted(importance_values, reverse=True))
    
    def test_category_insights(self):
        """Test category-level insights."""
        insights = self.explainer.get_global_insights()
        
        category_importance = insights['category_importance']
        
        # Should have all major categories
        expected_categories = ['assessment', 'engagement', 'demographics', 'behavioral']
        for category in expected_categories:
            if category in category_importance:  # Some may not exist if no features match
                self.assertGreater(category_importance[category], 0)
    
    def test_top_predictive_factors(self):
        """Test identification of top predictive factors."""
        insights = self.explainer.get_global_insights()
        
        top_factors = insights['top_predictive_factors']
        
        # Should identify top 10 most important factors
        self.assertLessEqual(len(top_factors), 10)
        
        # Each factor should have description and importance
        for factor in top_factors:
            self.assertIn('feature', factor)
            self.assertIn('importance', factor)
            self.assertIn('description', factor)
    
    def test_model_summary(self):
        """Test model summary generation."""
        insights = self.explainer.get_global_insights()
        
        model_summary = insights['model_summary']
        
        # Should contain key statistics
        expected_fields = ['total_features', 'feature_categories', 'top_category']
        for field in expected_fields:
            self.assertIn(field, model_summary)

class TestInterventionSystemExplainability(unittest.TestCase):
    """Test explainable AI integration with intervention system."""
    
    @patch('models.intervention_system.joblib.load')
    @patch('models.intervention_system.Path.exists')
    def test_intervention_system_explainable_predictions(self, mock_exists, mock_load):
        """Test explainable predictions through intervention system."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock model loading
        mock_model = MagicMock()
        mock_model.feature_importances_ = np.array([0.3, 0.2, 0.15, 0.1, 0.25])
        mock_model.predict_proba.return_value = np.array([[0.4, 0.6], [0.7, 0.3]])
        mock_load.return_value = mock_model
        
        # Mock feature columns
        with patch('builtins.open', mock_open_json(self.mock_features)):
            system = InterventionRecommendationSystem()
            
            # Test explainable predictions
            explanations = system.get_explainable_predictions(SAMPLE_STUDENT_FEATURES.head(2))
            
            self.assertEqual(len(explanations), 2)
            
            # Each explanation should have required structure
            for explanation in explanations:
                required_fields = ['student_id', 'risk_category', 'explanation']
                for field in required_fields:
                    self.assertIn(field, explanation)
    
    @property
    def mock_features(self):
        """Mock feature list for testing."""
        return [
            'early_avg_score', 'early_total_clicks', 'attendance_rate',
            'assignment_completion', 'discipline_incidents'
        ]

class TestExplainabilityEdgeCases(unittest.TestCase):
    """Test edge cases in explainable AI functionality."""
    
    def setUp(self):
        """Set up explainer."""
        self.mock_model = MagicMock()
        self.mock_model.feature_importances_ = np.array([0.4, 0.3, 0.2, 0.1])
        
        self.features = ['feature_1', 'feature_2', 'feature_3', 'feature_4']
        self.explainer = ExplainableAI(self.mock_model, self.features)
    
    def test_single_student_explanation(self):
        """Test explanation for single student."""
        single_student = pd.DataFrame([{
            'id_student': 1001,
            'feature_1': 85.0,
            'feature_2': 150,
            'feature_3': 0.95,
            'feature_4': 0.8
        }])
        
        self.mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])
        
        explanation = self.explainer.predict_with_explanation(single_student)
        
        # Should handle single student correctly
        self.assertEqual(explanation['student_id'], 1001)
        self.assertIsInstance(explanation['risk_score'], (int, float))
    
    def test_missing_feature_importance(self):
        """Test handling when model doesn't have feature_importances_."""
        model_without_importance = MagicMock()
        del model_without_importance.feature_importances_
        
        # Should handle gracefully
        try:
            explainer = ExplainableAI(model_without_importance, self.features)
            importance = explainer.get_feature_importance()
            
            # Should provide fallback or handle gracefully
            self.assertIsInstance(importance, list)
        except AttributeError:
            # Acceptable to raise AttributeError for models without feature importance
            pass
    
    def test_zero_importance_features(self):
        """Test handling of features with zero importance."""
        self.mock_model.feature_importances_ = np.array([0.5, 0.3, 0.2, 0.0])
        
        importance = self.explainer.get_feature_importance()
        
        # Should include all features, even those with zero importance
        self.assertEqual(len(importance), 4)
        
        # Zero importance feature should be last
        self.assertEqual(importance[-1]['importance'], 0.0)
    
    def test_extreme_risk_scores(self):
        """Test explanation with extreme risk scores."""
        extreme_student = pd.DataFrame([{
            'id_student': 1001,
            'feature_1': 0.0,  # Extreme low value
            'feature_2': 1000.0,  # Extreme high value
            'feature_3': 0.5,
            'feature_4': 0.5
        }])
        
        # Very high risk prediction
        self.mock_model.predict_proba.return_value = np.array([[0.05, 0.95]])
        
        explanation = self.explainer.predict_with_explanation(extreme_student)
        
        # Should handle extreme values
        self.assertGreaterEqual(explanation['risk_score'], 0)
        self.assertLessEqual(explanation['risk_score'], 1)
        self.assertIn('risk_category', explanation)

class TestExplainabilityPerformance(unittest.TestCase):
    """Test performance of explainable AI functionality."""
    
    def setUp(self):
        """Set up explainer with larger feature set."""
        feature_count = 50
        self.mock_model = MagicMock()
        self.mock_model.feature_importances_ = np.random.dirichlet(np.ones(feature_count))
        
        self.features = [f'feature_{i}' for i in range(feature_count)]
        self.explainer = ExplainableAI(self.mock_model, self.features)
    
    def test_explanation_speed(self):
        """Test that explanations are generated quickly."""
        import time
        
        # Create batch of students
        num_students = 20
        students_data = []
        for i in range(num_students):
            student = {'id_student': 1000 + i}
            for j, feature in enumerate(self.features):
                student[feature] = np.random.random()
            students_data.append(student)
        
        students_df = pd.DataFrame(students_data)
        
        # Mock predictions
        self.mock_model.predict_proba.return_value = np.random.random((num_students, 2))
        
        start_time = time.time()
        
        # Generate explanations for all students
        explanations = []
        for i in range(num_students):
            student = students_df.iloc[[i]]
            explanation = self.explainer.predict_with_explanation(student)
            explanations.append(explanation)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process reasonably quickly (< 2 seconds for 20 students)
        self.assertLess(processing_time, 2.0, 
                       f"Explanation generation took {processing_time:.2f}s for {num_students} students")
        
        self.assertEqual(len(explanations), num_students)

# Helper function for mocking file operations
def mock_open_json(data):
    """Mock open function that returns JSON data."""
    from unittest.mock import mock_open
    import json
    return mock_open(read_data=json.dumps(data))

if __name__ == '__main__':
    unittest.main()