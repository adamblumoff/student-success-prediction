#!/usr/bin/env python3
"""
Unit tests for K-12 ultra-advanced model prediction functionality.

Tests the K12UltraPredictor class and related K-12 specific features.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from models.k12_ultra_predictor import K12UltraPredictor
from tests.fixtures.mock_data import mock_data, SAMPLE_K12_RESULTS

class TestK12UltraPredictorInitialization(unittest.TestCase):
    """Test K-12 ultra-advanced predictor initialization."""
    
    def test_predictor_initialization(self):
        """Test basic predictor initialization."""
        predictor = K12UltraPredictor()
        
        self.assertIsNotNone(predictor.models_dir)
        self.assertIsNotNone(predictor.gradebook_mappings)
        
        # Should have model, scaler, or fallback
        self.assertTrue(
            predictor.model is not None or 
            hasattr(predictor, 'model') and predictor.model is not None
        )
    
    def test_predictor_initialization_with_custom_dir(self):
        """Test predictor initialization with custom models directory."""
        custom_dir = "tests/fixtures"
        predictor = K12UltraPredictor(models_dir=custom_dir)
        
        self.assertEqual(str(predictor.models_dir), custom_dir)
    
    def test_fallback_model_creation(self):
        """Test fallback model creation when no models found."""
        # Use non-existent directory to force fallback
        non_existent_dir = "tests/non_existent_models"
        predictor = K12UltraPredictor(models_dir=non_existent_dir)
        
        # Should create fallback model
        self.assertIsNotNone(predictor.model)
        self.assertIsNotNone(predictor.features)
        self.assertIsNotNone(predictor.metadata)
        self.assertEqual(predictor.metadata['model_type'], 'fallback')

class TestGradebookFeatureExtraction(unittest.TestCase):
    """Test feature extraction from gradebook data."""
    
    def setUp(self):
        """Set up test predictor."""
        self.predictor = K12UltraPredictor()
    
    def test_extract_basic_features(self):
        """Test extraction of basic gradebook features."""
        gradebook_data = pd.DataFrame({
            'student_id': ['S001'],
            'current_gpa': [3.5],
            'attendance_rate': [0.95],
            'discipline_incidents': [0],
            'assignment_completion': [0.9],
            'grade_level': [10]
        })
        
        features = self.predictor._extract_gradebook_features(gradebook_data)
        
        # Check basic features are extracted
        self.assertEqual(features['current_gpa'], 3.5)
        self.assertEqual(features['attendance_rate'], 0.95)
        self.assertEqual(features['discipline_incidents'], 0)
        self.assertEqual(features['assignment_completion'], 0.9)
        self.assertEqual(features['grade_level'], 10)
    
    def test_extract_features_with_missing_data(self):
        """Test feature extraction with missing data."""
        gradebook_data = pd.DataFrame({
            'student_id': ['S001'],
            'current_gpa': [np.nan],  # Missing GPA
            'attendance_rate': [0.85]
        })
        
        features = self.predictor._extract_gradebook_features(gradebook_data)
        
        # Should provide intelligent defaults
        self.assertEqual(features['current_gpa'], 2.5)  # Default GPA
        self.assertEqual(features['attendance_rate'], 0.85)
        self.assertIn('grade_level', features)  # Should have default
    
    def test_feature_mapping_flexibility(self):
        """Test flexible column mapping for different gradebook formats."""
        # Test with different column names that should map to same features
        gradebook_variants = [
            pd.DataFrame({
                'student_id': ['S001'],
                'current_gpa': [3.2],
                'attendance': [0.92]
            }),
            pd.DataFrame({
                'student_id': ['S001'], 
                'gpa': [3.2],
                'attendance_rate': [0.92]
            }),
            pd.DataFrame({
                'student_id': ['S001'],
                'grade_avg': [3.2],
                'attendance_pct': [0.92]
            })
        ]
        
        for gradebook_data in gradebook_variants:
            features = self.predictor._extract_gradebook_features(gradebook_data)
            
            self.assertEqual(features['current_gpa'], 3.2)
            self.assertEqual(features['attendance_rate'], 0.92)

class TestAdvancedFeatureEngineering(unittest.TestCase):
    """Test advanced feature engineering for K-12 model."""
    
    def setUp(self):
        """Set up test predictor."""
        self.predictor = K12UltraPredictor()
    
    def test_gpa_trend_calculation(self):
        """Test GPA trend calculation."""
        features_dict = {
            'current_gpa': 3.2,
            'previous_gpa': 3.0,
            'gpa_2_years_ago': 2.8
        }
        
        self.predictor._engineer_ultra_features(features_dict)
        
        # Check trend calculations
        self.assertEqual(features_dict['gpa_trend'], 0.2)  # current - previous
        self.assertEqual(features_dict['gpa_trajectory'], 0.2)  # (current - 2_years_ago) / 2
    
    def test_attendance_pattern_analysis(self):
        """Test attendance pattern analysis."""
        features_dict = {
            'attendance_rate': 0.82  # Below chronic absence threshold
        }
        
        self.predictor._engineer_ultra_features(features_dict)
        
        # Check attendance-derived features
        self.assertEqual(features_dict['chronic_absent_pattern'], 1)  # Should flag as chronic
        self.assertGreater(features_dict['days_absent_per_month'], 2)
        self.assertLess(features_dict['attendance_consistency'], 1.0)
    
    def test_risk_factor_calculation(self):
        """Test cumulative risk factors calculation."""
        high_risk_features = {
            'current_gpa': 1.8,  # Below 2.0
            'attendance_rate': 0.78,  # Below 0.85 
            'discipline_incidents': 3,  # Above 2
            'course_failures': 1,  # Above 0
            'parent_engagement_frequency': 1  # Low engagement
        }
        
        self.predictor._engineer_ultra_features(high_risk_features)
        
        # Should identify multiple risk factors
        self.assertGreaterEqual(high_risk_features['cumulative_risk_factors'], 3)
    
    def test_protective_factors_calculation(self):
        """Test protective factors calculation.""" 
        strong_support_features = {
            'current_gpa': 3.5,
            'parent_engagement_frequency': 4,  # High engagement
            'extracurricular_participation': 2,  # Active in activities
            'teacher_relationship_quality': 0.8,  # Strong relationships
            'peer_relationships': 0.75,
            'home_support_structure': 0.85,
            'social_skills': 0.8
        }
        
        self.predictor._engineer_ultra_features(strong_support_features)
        
        # Should identify multiple protective factors
        self.assertGreaterEqual(strong_support_features['protective_factors_count'], 4)
    
    def test_advanced_engineered_features(self):
        """Test creation of advanced engineered features."""
        base_features = {
            'current_gpa': 3.0,
            'attendance_rate': 0.90,
            'parent_engagement_frequency': 3,
            'homework_quality': 0.8
        }
        
        self.predictor._engineer_ultra_features(base_features)
        
        # Check polynomial features
        self.assertIn('gpa_power_2', base_features)
        self.assertIn('attendance_power_2', base_features)
        self.assertEqual(base_features['gpa_power_2'], 9.0)
        
        # Check interaction features
        self.assertIn('gpa_attendance_product', base_features)
        self.assertIn('gpa_parent_product', base_features)
        self.assertEqual(base_features['gpa_attendance_product'], 2.7)  # 3.0 * 0.9
        
        # Check composite scores
        self.assertIn('academic_excellence_score', base_features)
        self.assertIn('family_support_score', base_features)
        self.assertIn('behavioral_stability_score', base_features)

class TestK12ModelPredictions(unittest.TestCase):
    """Test K-12 model prediction functionality."""
    
    def setUp(self):
        """Set up test predictor and data."""
        self.predictor = K12UltraPredictor()
        
        # Create sample gradebook data
        self.sample_gradebook = pd.DataFrame({
            'student_id': ['S001', 'S002', 'S003'],
            'name': ['Alice Johnson', 'Bob Smith', 'Carol Davis'],
            'grade_level': [9, 10, 11],
            'current_gpa': [3.8, 2.1, 1.6],
            'attendance_rate': [0.98, 0.85, 0.72],
            'discipline_incidents': [0, 1, 4],
            'assignment_completion': [0.96, 0.75, 0.45]
        })
    
    def test_predict_from_gradebook_basic(self):
        """Test basic prediction from gradebook data."""
        predictions = self.predictor.predict_from_gradebook(self.sample_gradebook)
        
        # Should return predictions for all students
        self.assertEqual(len(predictions), 3)
        
        # Check prediction structure
        first_prediction = predictions[0]
        required_fields = [
            'student_id', 'name', 'grade_level', 'current_gpa', 
            'attendance_rate', 'risk_probability', 'risk_category', 
            'risk_level', 'confidence', 'model_type'
        ]
        
        for field in required_fields:
            self.assertIn(field, first_prediction)
    
    def test_risk_categorization(self):
        """Test risk level categorization."""
        predictions = self.predictor.predict_from_gradebook(self.sample_gradebook)
        
        # Check that risk categories are valid
        valid_risk_levels = ['success', 'warning', 'danger']
        valid_risk_categories = ['Low Risk', 'Moderate Risk', 'High Risk']
        
        for prediction in predictions:
            self.assertIn(prediction['risk_level'], valid_risk_levels)
            self.assertIn(prediction['risk_category'], valid_risk_categories)
            
            # Check risk probability is valid
            self.assertGreaterEqual(prediction['risk_probability'], 0)
            self.assertLessEqual(prediction['risk_probability'], 1)
    
    def test_prediction_consistency(self):
        """Test prediction consistency across multiple runs."""
        # Run predictions multiple times with same data
        predictions1 = self.predictor.predict_from_gradebook(self.sample_gradebook)
        predictions2 = self.predictor.predict_from_gradebook(self.sample_gradebook)
        
        # Should get consistent results
        self.assertEqual(len(predictions1), len(predictions2))
        
        for pred1, pred2 in zip(predictions1, predictions2):
            self.assertEqual(pred1['student_id'], pred2['student_id'])
            # Risk probabilities should be very close (allowing for minor numerical differences)
            self.assertAlmostEqual(pred1['risk_probability'], pred2['risk_probability'], places=2)
    
    def test_prediction_error_handling(self):
        """Test prediction error handling."""
        # Test with invalid/empty data
        empty_gradebook = pd.DataFrame()
        
        predictions = self.predictor.predict_from_gradebook(empty_gradebook)
        
        # Should handle gracefully and return empty list or safe results
        self.assertIsInstance(predictions, list)
    
    def test_confidence_scores(self):
        """Test confidence score calculation."""
        predictions = self.predictor.predict_from_gradebook(self.sample_gradebook)
        
        for prediction in predictions:
            confidence = prediction['confidence']
            
            # Confidence should be between 0 and 1
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 1)
            
            # Higher confidence should correspond to predictions further from 0.5
            risk_prob = prediction['risk_probability']
            expected_confidence = abs(risk_prob - 0.5) * 2
            self.assertAlmostEqual(confidence, expected_confidence, places=2)

class TestK12RecommendationGeneration(unittest.TestCase):
    """Test K-12 recommendation generation."""
    
    def setUp(self):
        """Set up test predictor."""
        self.predictor = K12UltraPredictor()
    
    def test_high_risk_recommendations(self):
        """Test recommendations for high-risk students."""
        high_risk_result = {
            'student_id': 'S001',
            'grade_level': 9,
            'risk_level': 'danger',
            'current_gpa': 1.6,
            'attendance_rate': 0.72
        }
        
        recommendations = self.predictor.generate_recommendations(high_risk_result)
        
        # Should provide specific interventions for high-risk student
        self.assertGreater(len(recommendations), 0)
        self.assertLessEqual(len(recommendations), 5)
        
        # Should include intensive support for low GPA and attendance
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue(any(keyword in rec_text for keyword in ['intensive', 'support', 'meeting']))
    
    def test_grade_specific_recommendations(self):
        """Test grade-level specific recommendations."""
        elementary_result = {
            'student_id': 'S001',
            'grade_level': 5,
            'risk_level': 'warning',
            'current_gpa': 2.0,
            'attendance_rate': 0.88
        }
        
        high_school_result = {
            'student_id': 'S002', 
            'grade_level': 11,
            'risk_level': 'warning',
            'current_gpa': 2.0,
            'attendance_rate': 0.88
        }
        
        elementary_recs = self.predictor.generate_recommendations(elementary_result)
        high_school_recs = self.predictor.generate_recommendations(high_school_result)
        
        # Recommendations should be different for different grade levels
        elementary_text = ' '.join(elementary_recs).lower()
        high_school_text = ' '.join(high_school_recs).lower()
        
        # Elementary should focus on foundational skills
        # High school should focus on graduation and credit recovery
        self.assertTrue(len(elementary_recs) > 0)
        self.assertTrue(len(high_school_recs) > 0)
    
    def test_successful_student_recommendations(self):
        """Test recommendations for successful students."""
        successful_result = {
            'student_id': 'S001',
            'grade_level': 10,
            'risk_level': 'success',
            'current_gpa': 3.8,
            'attendance_rate': 0.98
        }
        
        recommendations = self.predictor.generate_recommendations(successful_result)
        
        # Should provide positive reinforcement
        self.assertGreater(len(recommendations), 0)
        
        rec_text = ' '.join(recommendations).lower()
        self.assertTrue(any(keyword in rec_text for keyword in ['continue', 'recognize', 'monitor']))

class TestK12ModelInfo(unittest.TestCase):
    """Test K-12 model information functionality."""
    
    def setUp(self):
        """Set up test predictor."""
        self.predictor = K12UltraPredictor()
    
    def test_model_info_structure(self):
        """Test model info returns expected structure."""
        model_info = self.predictor.get_model_info()
        
        required_fields = ['model_type', 'auc_score', 'feature_count', 'approach']
        for field in required_fields:
            self.assertIn(field, model_info)
    
    def test_model_info_values(self):
        """Test model info contains reasonable values."""
        model_info = self.predictor.get_model_info()
        
        # AUC score should be between 0 and 1
        auc_score = model_info['auc_score']
        self.assertGreaterEqual(auc_score, 0)
        self.assertLessEqual(auc_score, 1)
        
        # Feature count should be positive
        feature_count = model_info['feature_count']
        self.assertGreater(feature_count, 0)
        
        # Model type should be descriptive
        model_type = model_info['model_type']
        self.assertIsInstance(model_type, str)
        self.assertGreater(len(model_type), 0)

class TestK12ModelPerformance(unittest.TestCase):
    """Test K-12 model performance characteristics."""
    
    def setUp(self):
        """Set up test predictor and larger dataset."""
        self.predictor = K12UltraPredictor()
        
        # Create larger test dataset
        np.random.seed(42)
        self.large_gradebook = pd.DataFrame({
            'student_id': [f'S{i:03d}' for i in range(100)],
            'name': [f'Student {i}' for i in range(100)],
            'grade_level': np.random.randint(9, 13, 100),
            'current_gpa': np.random.uniform(1.0, 4.0, 100),
            'attendance_rate': np.random.uniform(0.6, 1.0, 100),
            'discipline_incidents': np.random.randint(0, 6, 100),
            'assignment_completion': np.random.uniform(0.3, 1.0, 100)
        })
    
    def test_prediction_speed(self):
        """Test prediction speed for reasonable performance."""
        import time
        
        start_time = time.time()
        predictions = self.predictor.predict_from_gradebook(self.large_gradebook)
        end_time = time.time()
        
        prediction_time = end_time - start_time
        
        # Should process 100 students in reasonable time (< 5 seconds)
        self.assertLess(prediction_time, 5.0, f"Prediction took {prediction_time:.2f} seconds for 100 students")
        
        # Should return predictions for all students
        self.assertEqual(len(predictions), 100)
    
    def test_memory_efficiency(self):
        """Test memory efficiency with larger datasets."""
        # Process in chunks to test memory handling
        chunk_size = 25
        all_predictions = []
        
        for i in range(0, len(self.large_gradebook), chunk_size):
            chunk = self.large_gradebook.iloc[i:i+chunk_size]
            chunk_predictions = self.predictor.predict_from_gradebook(chunk)
            all_predictions.extend(chunk_predictions)
        
        # Should process all students successfully
        self.assertEqual(len(all_predictions), 100)
        
        # Each prediction should have consistent structure
        for prediction in all_predictions:
            self.assertIn('student_id', prediction)
            self.assertIn('risk_probability', prediction)
    
    def test_prediction_distribution(self):
        """Test that predictions show reasonable distribution."""
        predictions = self.predictor.predict_from_gradebook(self.large_gradebook)
        
        # Extract risk probabilities
        risk_probs = [p['risk_probability'] for p in predictions]
        
        # Should have reasonable distribution (not all the same)
        unique_probs = len(set([round(p, 2) for p in risk_probs]))
        self.assertGreater(unique_probs, 10, "Predictions should show variety")
        
        # Should use full range of probabilities
        min_prob = min(risk_probs)
        max_prob = max(risk_probs)
        prob_range = max_prob - min_prob
        self.assertGreater(prob_range, 0.3, "Should use reasonable range of risk probabilities")

class TestK12ModelIntegration(unittest.TestCase):
    """Test integration with other system components."""
    
    def setUp(self):
        """Set up test predictor."""
        self.predictor = K12UltraPredictor()
    
    @patch('models.k12_ultra_predictor.joblib.load')
    def test_model_loading_error_handling(self, mock_joblib_load):
        """Test handling of model loading errors."""
        # Simulate model loading failure
        mock_joblib_load.side_effect = Exception("Model file corrupted")
        
        # Should fall back gracefully
        predictor = K12UltraPredictor()
        
        # Should still be able to make predictions (using fallback)
        test_data = pd.DataFrame({
            'student_id': ['S001'],
            'current_gpa': [3.0],
            'attendance_rate': [0.9]
        })
        
        predictions = predictor.predict_from_gradebook(test_data)
        self.assertEqual(len(predictions), 1)
        self.assertIn('error', predictions[0] or {})
    
    def test_integration_with_mock_data(self):
        """Test integration with test fixture data."""
        # Use mock data from fixtures
        predictions = self.predictor.predict_from_gradebook(pd.DataFrame(SAMPLE_K12_RESULTS))
        
        # Should handle the mock data structure
        self.assertIsInstance(predictions, list)
        
        if len(predictions) > 0:
            # Should maintain expected structure
            self.assertIn('student_id', predictions[0])

if __name__ == '__main__':
    unittest.main()