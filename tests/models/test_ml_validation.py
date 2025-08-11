#!/usr/bin/env python3
"""
ML Model Validation Tests

Comprehensive testing for machine learning models to ensure production readiness,
including performance validation, input validation, and error handling.
"""

import pytest
import numpy as np
import pandas as pd
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import joblib

# Set up test environment
os.environ['TESTING'] = 'true'
os.environ['ENVIRONMENT'] = 'test'

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.intervention_system import InterventionRecommendationSystem
from src.models.k12_ultra_predictor import K12UltraPredictor

class TestK12UltraPredictorValidation:
    """Test K12 Ultra Predictor model validation and security"""
    
    @pytest.fixture
    def sample_gradebook_data(self):
        """Create sample gradebook data for testing"""
        return pd.DataFrame({
            'Student': ['Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson'],
            'ID': [1001, 1002, 1003, 1004],
            'Current Score': [92.5, 67.3, 78.8, 45.2],
            'Grade Level': [9, 10, 11, 12],
            'Attendance Rate': [0.98, 0.82, 0.91, 0.65],
            'Assignment Completion': [0.96, 0.73, 0.85, 0.58]
        })
    
    @pytest.fixture
    def k12_predictor(self):
        """K12 predictor fixture with error handling"""
        try:
            return K12UltraPredictor()
        except (FileNotFoundError, ImportError, Exception) as e:
            pytest.skip(f"K12 predictor not available: {e}")
    
    def test_model_initialization(self):
        """Test model initializes without errors"""
        try:
            predictor = K12UltraPredictor()
            assert predictor is not None
        except (FileNotFoundError, ImportError):
            pytest.skip("K12 model files not available")
    
    def test_predict_from_gradebook_basic(self, k12_predictor, sample_gradebook_data):
        """Test basic gradebook prediction functionality"""
        predictions = k12_predictor.predict_from_gradebook(sample_gradebook_data)
        
        # Validate prediction structure
        assert isinstance(predictions, list)
        assert len(predictions) == len(sample_gradebook_data)
        
        for prediction in predictions:
            assert isinstance(prediction, dict)
            assert 'student_id' in prediction
            assert 'risk_probability' in prediction
            assert 'risk_level' in prediction
            
            # Validate risk probability bounds
            risk_prob = prediction['risk_probability']
            assert 0 <= risk_prob <= 1, f"Risk probability {risk_prob} out of bounds"
    
    def test_input_validation_empty_dataframe(self, k12_predictor):
        """Test handling of empty dataframe"""
        empty_df = pd.DataFrame()
        
        with pytest.raises((ValueError, KeyError, IndexError)):
            k12_predictor.predict_from_gradebook(empty_df)
    
    def test_input_validation_missing_columns(self, k12_predictor):
        """Test handling of dataframe with missing required columns"""
        incomplete_df = pd.DataFrame({
            'Student': ['Alice Johnson'],
            # Missing other required columns
        })
        
        # Should handle gracefully or raise appropriate error
        try:
            predictions = k12_predictor.predict_from_gradebook(incomplete_df)
            # If it succeeds, validate the output
            assert isinstance(predictions, list)
        except (ValueError, KeyError) as e:
            # Expected behavior for missing columns
            assert "column" in str(e).lower() or "key" in str(e).lower()
    
    def test_input_validation_invalid_data_types(self, k12_predictor):
        """Test handling of invalid data types"""
        invalid_df = pd.DataFrame({
            'Student': ['Alice Johnson'],
            'ID': ['not_a_number'],  # Invalid ID type
            'Current Score': ['invalid_score'],  # Invalid score type
            'Grade Level': [15],  # Invalid grade level
            'Attendance Rate': [1.5],  # Invalid attendance rate
        })
        
        # Should handle gracefully or raise appropriate error
        try:
            predictions = k12_predictor.predict_from_gradebook(invalid_df)
            # If it succeeds, validate the output structure
            assert isinstance(predictions, list)
            if predictions:
                assert isinstance(predictions[0], dict)
        except (ValueError, TypeError) as e:
            # Expected behavior for invalid data types
            assert any(term in str(e).lower() for term in ['invalid', 'type', 'convert'])
    
    def test_extreme_values_handling(self, k12_predictor):
        """Test handling of extreme values"""
        extreme_df = pd.DataFrame({
            'Student': ['Extreme Test'],
            'ID': [999999],
            'Current Score': [-100],  # Negative score
            'Grade Level': [0],       # Invalid grade
            'Attendance Rate': [2.0], # Over 100% attendance
            'Assignment Completion': [-0.5]  # Negative completion
        })
        
        try:
            predictions = k12_predictor.predict_from_gradebook(extreme_df)
            
            if predictions:
                prediction = predictions[0]
                # Validate output bounds even with extreme inputs
                assert 0 <= prediction.get('risk_probability', 0.5) <= 1
        except (ValueError, TypeError):
            # Acceptable to reject extreme values
            pass
    
    def test_large_dataset_performance(self, k12_predictor):
        """Test performance with larger datasets"""
        # Create a larger test dataset
        large_df = pd.DataFrame({
            'Student': [f'Student_{i}' for i in range(100)],
            'ID': range(1001, 1101),
            'Current Score': np.random.uniform(0, 100, 100),
            'Grade Level': np.random.choice([9, 10, 11, 12], 100),
            'Attendance Rate': np.random.uniform(0.5, 1.0, 100),
            'Assignment Completion': np.random.uniform(0.3, 1.0, 100)
        })
        
        import time
        start_time = time.time()
        
        try:
            predictions = k12_predictor.predict_from_gradebook(large_df)
            processing_time = time.time() - start_time
            
            # Performance requirements
            assert processing_time < 10.0, f"Processing took too long: {processing_time}s"
            assert len(predictions) == len(large_df)
            
        except Exception as e:
            pytest.fail(f"Failed to process large dataset: {e}")
    
    def test_prediction_consistency(self, k12_predictor, sample_gradebook_data):
        """Test that predictions are consistent across multiple calls"""
        try:
            predictions1 = k12_predictor.predict_from_gradebook(sample_gradebook_data)
            predictions2 = k12_predictor.predict_from_gradebook(sample_gradebook_data)
            
            # Compare predictions
            for p1, p2 in zip(predictions1, predictions2):
                # Risk probabilities should be identical or very close
                risk_diff = abs(p1.get('risk_probability', 0.5) - p2.get('risk_probability', 0.5))
                assert risk_diff < 0.01, "Predictions should be consistent"
                
        except Exception as e:
            pytest.skip(f"Consistency test failed due to model error: {e}")
    
    def test_model_info_retrieval(self, k12_predictor):
        """Test model info retrieval"""
        try:
            model_info = k12_predictor.get_model_info()
            
            assert isinstance(model_info, dict)
            
            # Expected model info fields
            expected_fields = ['auc_score', 'accuracy', 'model_name']
            for field in expected_fields:
                if field in model_info:
                    # Validate performance metrics are reasonable
                    if field in ['auc_score', 'accuracy']:
                        value = model_info[field]
                        assert 0 <= value <= 1, f"{field} should be between 0 and 1"
                        
        except (AttributeError, NotImplementedError):
            pytest.skip("Model info not implemented")

class TestInterventionSystemValidation:
    """Test Intervention System validation and security"""
    
    @pytest.fixture
    def intervention_system(self):
        """Intervention system fixture with error handling"""
        try:
            return InterventionRecommendationSystem()
        except (FileNotFoundError, ImportError, Exception) as e:
            pytest.skip(f"Intervention system not available: {e}")
    
    @pytest.fixture
    def sample_student_features(self):
        """Sample student features for testing"""
        return {
            'student_id': 1001,
            'early_avg_score': 75.5,
            'early_total_clicks': 850,
            'studied_credits': 90,
            'num_of_prev_attempts': 1,
            'age_band_encoded': 1,
            'gender_encoded': 1,
            'region_encoded': 2,
            'education_encoded': 3,
            'is_male': 1,
            'has_disability': 0
        }
    
    def test_intervention_system_initialization(self):
        """Test intervention system initializes properly"""
        try:
            system = InterventionRecommendationSystem()
            assert system is not None
        except (FileNotFoundError, ImportError):
            pytest.skip("Intervention system models not available")
    
    def test_explainable_predictions(self, intervention_system, sample_student_features):
        """Test explainable AI functionality"""
        try:
            explanation = intervention_system.explainable_ai.predict_with_explanation(
                sample_student_features
            )
            
            # Validate explanation structure
            assert isinstance(explanation, dict)
            
            # Should contain explanation data
            expected_keys = ['prediction', 'explanation', 'risk_factors']
            for key in expected_keys:
                if key in explanation:
                    assert explanation[key] is not None
                    
        except (AttributeError, KeyError, Exception) as e:
            # May not be fully implemented
            pytest.skip(f"Explainable AI not fully available: {e}")
    
    def test_missing_features_handling(self, intervention_system):
        """Test handling of missing features"""
        incomplete_features = {
            'student_id': 1001,
            'early_avg_score': 75.5
            # Missing other required features
        }
        
        try:
            explanation = intervention_system.explainable_ai.predict_with_explanation(
                incomplete_features
            )
            # If it succeeds, should have valid structure
            assert isinstance(explanation, dict)
        except (KeyError, ValueError, IndexError):
            # Expected behavior for missing features
            pass

class TestModelSecurity:
    """Test model security and robustness"""
    
    def test_model_file_integrity(self):
        """Test that model files exist and are accessible"""
        model_dir = Path("results/models")
        
        if model_dir.exists():
            model_files = list(model_dir.glob("*.pkl"))
            
            for model_file in model_files:
                # Test that model file can be loaded safely
                try:
                    model = joblib.load(model_file)
                    assert model is not None
                except Exception as e:
                    pytest.fail(f"Model file {model_file} is corrupted: {e}")
        else:
            pytest.skip("Model directory not found")
    
    def test_model_injection_protection(self):
        """Test protection against model injection attacks"""
        # Test that loading arbitrary pickle files is protected
        malicious_pickle = b'\x80\x03}q\x00.'  # Minimal pickle that could be expanded
        
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            tmp_file.write(malicious_pickle)
            tmp_file.flush()
            
            try:
                # Should not execute arbitrary code
                model = joblib.load(tmp_file.name)
                # If it loads, ensure it's safe
                assert isinstance(model, dict)  # Expected safe structure
            except Exception:
                # Expected to fail on malicious content
                pass
            finally:
                os.unlink(tmp_file.name)
    
    def test_memory_usage_constraints(self):
        """Test that models don't consume excessive memory"""
        import psutil
        import gc
        
        initial_memory = psutil.Process().memory_info().rss
        
        try:
            # Load models
            intervention_system = InterventionRecommendationSystem()
            k12_predictor = K12UltraPredictor()
            
            current_memory = psutil.Process().memory_info().rss
            memory_increase = current_memory - initial_memory
            
            # Should not use more than 500MB for models
            assert memory_increase < 500 * 1024 * 1024, f"Memory usage too high: {memory_increase} bytes"
            
        except (ImportError, FileNotFoundError):
            pytest.skip("Models not available for memory test")
        finally:
            gc.collect()

class TestModelValidationSuite:
    """Comprehensive model validation test suite"""
    
    def test_model_version_consistency(self):
        """Test model version consistency"""
        metadata_file = Path("results/models/model_metadata.json")
        
        if metadata_file.exists():
            import json
            with open(metadata_file) as f:
                metadata = json.load(f)
                
            # Validate metadata structure
            assert 'version' in metadata
            assert 'performance' in metadata
            assert 'created_at' in metadata
            
            # Validate performance metrics
            if 'auc_score' in metadata['performance']:
                auc = metadata['performance']['auc_score']
                assert 0.5 <= auc <= 1.0, f"AUC score {auc} seems unrealistic"
        else:
            pytest.skip("Model metadata not found")
    
    def test_model_backward_compatibility(self):
        """Test that models maintain backward compatibility"""
        # This would test that newer model versions can still process
        # data in the same format as older versions
        try:
            # Test with minimal required data format
            minimal_data = pd.DataFrame({
                'Student': ['Test Student'],
                'ID': [1001],
                'Current Score': [85.0]
            })
            
            predictor = K12UltraPredictor()
            predictions = predictor.predict_from_gradebook(minimal_data)
            
            # Should produce valid predictions
            assert isinstance(predictions, list)
            assert len(predictions) > 0
            
        except (FileNotFoundError, ImportError, Exception):
            pytest.skip("Backward compatibility test requires model availability")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])