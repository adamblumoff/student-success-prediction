#!/usr/bin/env python3
"""
Unit tests for CSV processing and file upload functionality.

Tests gradebook format detection, conversion, and feature extraction.
"""

import unittest
import pandas as pd
import numpy as np
import io
import os
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from mvp.mvp_api import (
    detect_gradebook_format, universal_gradebook_converter,
    convert_canvas_to_prediction_format, extract_student_identifier,
    extract_assignment_scores, extract_engagement_metrics
)
from mvp.simple_auth import simple_file_validation
from tests.fixtures.mock_data import mock_data

class TestGradebookFormatDetection(unittest.TestCase):
    """Test gradebook format detection functionality."""
    
    def test_detect_canvas_format(self):
        """Test detection of Canvas gradebook format."""
        canvas_data = {
            'Student': ['Alice Johnson', 'Bob Smith'],
            'ID': [12001, 12002], 
            'Current Score': [85.5, 62.1],
            'Assignment 1 (100 pts)': [85, 65]
        }
        df = pd.DataFrame(canvas_data)
        
        format_type = detect_gradebook_format(df)
        self.assertEqual(format_type, 'canvas')
    
    def test_detect_generic_format(self):
        """Test detection of generic gradebook format."""
        generic_data = {
            'student_id': ['S001', 'S002'],
            'student_name': ['Alice', 'Bob'],
            'overall_grade': [85, 72],
            'assignment_score': [90, 68]
        }
        df = pd.DataFrame(generic_data)
        
        format_type = detect_gradebook_format(df)
        self.assertEqual(format_type, 'generic')
    
    def test_detect_prediction_format(self):
        """Test detection of existing prediction format."""
        prediction_data = {
            'id_student': [1001, 1002],
            'early_avg_score': [85.5, 72.3],
            'early_total_clicks': [200, 150]
        }
        df = pd.DataFrame(prediction_data)
        
        format_type = detect_gradebook_format(df)
        self.assertEqual(format_type, 'prediction_format')
    
    def test_detect_unknown_format(self):
        """Test detection of unknown format."""
        unknown_data = {
            'random_column': ['data1', 'data2'],
            'another_column': ['value1', 'value2']
        }
        df = pd.DataFrame(unknown_data)
        
        format_type = detect_gradebook_format(df)
        self.assertEqual(format_type, 'unknown')

class TestStudentIdentifierExtraction(unittest.TestCase):
    """Test student identifier extraction from different formats."""
    
    def test_extract_canvas_identifiers(self):
        """Test extraction of student IDs from Canvas format."""
        canvas_data = {
            'Student': ['Alice Johnson', 'Bob Smith'],
            'ID': [12001, 12002],
            'Current Score': [85.5, 62.1]
        }
        df = pd.DataFrame(canvas_data)
        
        identifiers = extract_student_identifier(df, 'canvas')
        expected = pd.Series(['12001', '12002'], index=[0, 1])
        
        pd.testing.assert_series_equal(identifiers, expected)
    
    def test_extract_generic_identifiers(self):
        """Test extraction from generic format with ID column."""
        generic_data = {
            'student_id': ['S001', 'S002'],
            'name': ['Alice', 'Bob'],
            'grade': [85, 72]
        }
        df = pd.DataFrame(generic_data)
        
        identifiers = extract_student_identifier(df, 'generic')
        expected = pd.Series(['S001', 'S002'], index=[0, 1])
        
        pd.testing.assert_series_equal(identifiers, expected)
    
    def test_extract_prediction_format_identifiers(self):
        """Test extraction from prediction format."""
        prediction_data = {
            'id_student': [1001, 1002],
            'risk_score': [0.3, 0.7]
        }
        df = pd.DataFrame(prediction_data)
        
        identifiers = extract_student_identifier(df, 'prediction_format')
        expected = pd.Series(['1001', '1002'], index=[0, 1])
        
        pd.testing.assert_series_equal(identifiers, expected)
    
    def test_fallback_identifiers(self):
        """Test fallback identifier generation."""
        data = {'column1': ['value1', 'value2']}
        df = pd.DataFrame(data)
        
        identifiers = extract_student_identifier(df, 'unknown')
        
        # Should generate sequential IDs starting from 1000
        self.assertEqual(len(identifiers), 2)
        self.assertTrue(all(isinstance(id_val, str) for id_val in identifiers))
        self.assertEqual(identifiers.iloc[0], '1000')
        self.assertEqual(identifiers.iloc[1], '1001')

class TestAssignmentScoreExtraction(unittest.TestCase):
    """Test assignment score extraction and statistics calculation."""
    
    def test_extract_canvas_scores(self):
        """Test score extraction from Canvas format."""
        canvas_data = {
            'Student': ['Alice', 'Bob'],
            'Assignment 1 (100 pts)': [85, 65],
            'Assignment 2 (100 pts)': [92, 58],
            'Quiz 1 (50 pts)': [44, 36],
            'Final Exam (200 pts)': [170, 120]  # Should be excluded
        }
        df = pd.DataFrame(canvas_data)
        
        scores_df = extract_assignment_scores(df, 'canvas')
        
        self.assertEqual(len(scores_df), 2)
        
        # Check Alice's scores (first row)
        alice_scores = scores_df.iloc[0]
        self.assertAlmostEqual(alice_scores['early_avg_score'], 87.67, places=1)  # (85+92+88)/3
        self.assertEqual(alice_scores['early_submitted_count'], 3)
        self.assertGreater(alice_scores['early_score_std'], 0)
    
    def test_extract_generic_scores(self):
        """Test score extraction from generic format."""
        generic_data = {
            'student_id': ['S001', 'S002'],
            'assignment_1': [85, 65],
            'quiz_score': [90, 70],
            'test_grade': [88, 72]
        }
        df = pd.DataFrame(generic_data)
        
        scores_df = extract_assignment_scores(df, 'generic')
        
        self.assertEqual(len(scores_df), 2)
        self.assertIn('early_avg_score', scores_df.columns)
        self.assertIn('early_submitted_count', scores_df.columns)
    
    def test_handle_missing_scores(self):
        """Test handling of missing or invalid scores."""
        data_with_missing = {
            'student_id': ['S001', 'S002'],
            'Assignment 1': [85, np.nan],
            'Assignment 2': ['', 'N/A'],
            'Assignment 3': [90, 75]
        }
        df = pd.DataFrame(data_with_missing)
        
        scores_df = extract_assignment_scores(df, 'generic')
        
        # Should handle missing values gracefully
        self.assertEqual(len(scores_df), 2)
        self.assertGreaterEqual(scores_df.iloc[0]['early_submitted_count'], 1)
        self.assertGreaterEqual(scores_df.iloc[1]['early_submitted_count'], 1)
    
    def test_score_format_parsing(self):
        """Test parsing of different score formats."""
        score_formats = {
            'student_id': ['S001', 'S002', 'S003'],
            'Assignment 1': ['85/100', '72%', '88'],  # Different formats
            'Assignment 2': ['92/100', '65%', '76']
        }
        df = pd.DataFrame(score_formats)
        
        scores_df = extract_assignment_scores(df, 'generic')
        
        # All formats should be converted to percentages
        self.assertEqual(len(scores_df), 3)
        
        # Check that scores are reasonable (0-100 range)
        for i in range(3):
            avg_score = scores_df.iloc[i]['early_avg_score']
            self.assertGreaterEqual(avg_score, 0)
            self.assertLessEqual(avg_score, 100)

class TestEngagementMetricsExtraction(unittest.TestCase):
    """Test engagement metrics extraction."""
    
    def test_extract_canvas_engagement(self):
        """Test engagement extraction from Canvas format."""
        canvas_data = {
            'Student': ['Alice', 'Bob'],
            'Total Activity Time (mins)': [240, 120],
            'Last Activity': ['2024-01-25 14:30:00', '2024-01-20 10:15:00']
        }
        df = pd.DataFrame(canvas_data)
        
        engagement_df = extract_engagement_metrics(df, 'canvas')
        
        self.assertEqual(len(engagement_df), 2)
        
        # Check Alice's engagement (more active)
        alice_engagement = engagement_df.iloc[0]
        bob_engagement = engagement_df.iloc[1]
        
        self.assertGreater(alice_engagement['early_total_clicks'], bob_engagement['early_total_clicks'])
        self.assertGreater(alice_engagement['early_avg_clicks'], bob_engagement['early_avg_clicks'])
    
    def test_extract_generic_engagement(self):
        """Test engagement extraction from generic format."""
        generic_data = {
            'student_id': ['S001', 'S002'],
            'activity_time': [180, 90],
            'participation_score': [8, 4]
        }
        df = pd.DataFrame(generic_data)
        
        engagement_df = extract_engagement_metrics(df, 'generic')
        
        self.assertEqual(len(engagement_df), 2)
        self.assertIn('early_total_clicks', engagement_df.columns)
        self.assertIn('early_avg_clicks', engagement_df.columns)
    
    def test_engagement_defaults(self):
        """Test default engagement values when no data available."""
        minimal_data = {
            'student_id': ['S001', 'S002']
        }
        df = pd.DataFrame(minimal_data)
        
        engagement_df = extract_engagement_metrics(df, 'generic')
        
        # Should provide reasonable defaults
        self.assertEqual(len(engagement_df), 2)
        
        for i in range(2):
            engagement = engagement_df.iloc[i]
            self.assertGreater(engagement['early_total_clicks'], 0)
            self.assertGreater(engagement['early_avg_clicks'], 0)

class TestUniversalGradebookConverter(unittest.TestCase):
    """Test the universal gradebook converter."""
    
    def test_convert_canvas_gradebook(self):
        """Test conversion of Canvas gradebook to prediction format."""
        canvas_csv = mock_data.generate_canvas_csv_data(3)
        df = pd.read_csv(io.StringIO(canvas_csv))
        
        converted_df = universal_gradebook_converter(df)
        
        # Check that required features are present
        required_features = [
            'id_student', 'early_avg_score', 'early_total_clicks', 
            'early_active_days', 'early_submission_rate'
        ]
        
        for feature in required_features:
            self.assertIn(feature, converted_df.columns)
        
        # Check that all students have valid data
        self.assertEqual(len(converted_df), 3)
        self.assertTrue(all(converted_df['id_student'].notna()))
    
    def test_convert_generic_gradebook(self):
        """Test conversion of generic gradebook format."""
        generic_csv = mock_data.generate_gradebook_csv_data(5)
        df = pd.read_csv(io.StringIO(generic_csv))
        
        converted_df = universal_gradebook_converter(df)
        
        # Should have all required columns
        required_columns = [
            'id_student', 'early_avg_score', 'early_total_clicks',
            'code_module', 'code_presentation', 'gender_encoded'
        ]
        
        for col in required_columns:
            self.assertIn(col, converted_df.columns)
        
        self.assertEqual(len(converted_df), 5)
    
    def test_convert_prediction_format_passthrough(self):
        """Test that prediction format data passes through unchanged."""
        prediction_data = {
            'id_student': [1001, 1002],
            'early_avg_score': [85.5, 72.3],
            'early_total_clicks': [200, 150],
            'code_module': ['TEST', 'TEST'],
            'code_presentation': ['2024J', '2024J']
        }
        df = pd.DataFrame(prediction_data)
        
        converted_df = universal_gradebook_converter(df)
        
        # Should remain unchanged
        pd.testing.assert_frame_equal(df, converted_df)
    
    def test_handle_unknown_format(self):
        """Test handling of unknown gradebook format."""
        unknown_data = {
            'weird_column': ['data1', 'data2'],
            'another_column': ['value1', 'value2']
        }
        df = pd.DataFrame(unknown_data)
        
        # Should attempt generic conversion
        converted_df = universal_gradebook_converter(df)
        
        # Should have required columns with defaults
        self.assertIn('id_student', converted_df.columns)
        self.assertIn('early_avg_score', converted_df.columns)
        self.assertEqual(len(converted_df), 2)

class TestCanvasSpecificConversion(unittest.TestCase):
    """Test Canvas-specific conversion functionality."""
    
    def test_canvas_to_prediction_format(self):
        """Test direct Canvas to prediction format conversion."""
        canvas_data = {
            'Student': ['Alice Johnson', 'Bob Smith'],
            'ID': [12001, 12002],
            'Current Score': [85.5, 62.1],
            'Assignment 1': [85, 65],
            'Assignment 2': [92, 58],
            'Total Activity Time (mins)': [240, 120],
            'Last Activity': ['2024-01-25 14:30:00', '2024-01-20 10:15:00']
        }
        df = pd.DataFrame(canvas_data)
        
        converted_df = convert_canvas_to_prediction_format(df)
        
        # Check Canvas-specific features
        self.assertIn('id_student', converted_df.columns) 
        self.assertEqual(converted_df.iloc[0]['id_student'], 12001)
        self.assertEqual(converted_df.iloc[1]['id_student'], 12002)
        
        # Check score conversion
        self.assertAlmostEqual(converted_df.iloc[0]['early_avg_score'], 85.5, places=1)
        self.assertAlmostEqual(converted_df.iloc[1]['early_avg_score'], 62.1, places=1)
        
        # Check engagement conversion
        self.assertGreater(converted_df.iloc[0]['early_total_clicks'], converted_df.iloc[1]['early_total_clicks'])

class TestFileValidation(unittest.TestCase):
    """Test file upload validation functionality."""
    
    def test_valid_csv_file(self):
        """Test validation of valid CSV file."""
        valid_csv = "student_id,grade\nS001,85\nS002,72"
        
        # Should not raise an exception
        try:
            simple_file_validation(valid_csv.encode('utf-8'), 'valid.csv')
        except Exception as e:
            self.fail(f"Valid CSV file rejected: {e}")
    
    def test_file_size_limit(self):
        """Test file size limit enforcement."""
        # Create content that exceeds 10MB
        large_content = "a" * (11 * 1024 * 1024)
        
        with self.assertRaises(Exception) as context:
            simple_file_validation(large_content.encode('utf-8'), 'large.csv')
        
        self.assertIn('large', str(context.exception).lower())
    
    def test_invalid_file_extension(self):
        """Test rejection of non-CSV files."""
        text_content = "This is not a CSV file"
        
        with self.assertRaises(Exception) as context:
            simple_file_validation(text_content.encode('utf-8'), 'file.txt')
        
        self.assertIn('csv', str(context.exception).lower())
    
    def test_empty_file(self):
        """Test rejection of empty files."""
        empty_content = ""
        
        with self.assertRaises(Exception) as context:
            simple_file_validation(empty_content.encode('utf-8'), 'empty.csv')
        
        self.assertIn('empty', str(context.exception).lower())
    
    def test_invalid_encoding(self):
        """Test handling of invalid file encoding."""
        # Create content with invalid UTF-8 sequences
        invalid_content = b'\xff\xfe\x00\x00invalid encoding'
        
        with self.assertRaises(Exception) as context:
            simple_file_validation(invalid_content, 'invalid.csv')
        
        self.assertIn('encoding', str(context.exception).lower())

class TestCSVProcessingEdgeCases(unittest.TestCase):
    """Test edge cases in CSV processing."""
    
    def test_single_student_processing(self):
        """Test processing of single-student CSV."""
        single_student = {
            'Student': ['Alice Johnson'],
            'ID': [12001],
            'Current Score': [85.5],
            'Assignment 1': [85]
        }
        df = pd.DataFrame(single_student)
        
        converted_df = universal_gradebook_converter(df)
        
        self.assertEqual(len(converted_df), 1)
        self.assertIn('id_student', converted_df.columns)
    
    def test_missing_columns_handling(self):
        """Test handling of missing expected columns."""
        minimal_data = {
            'some_id': ['S001', 'S002'],
            'some_score': [85, 72]
        }
        df = pd.DataFrame(minimal_data)
        
        converted_df = universal_gradebook_converter(df)
        
        # Should fill in missing columns with defaults
        required_columns = ['early_avg_score', 'early_total_clicks', 'gender_encoded']
        for col in required_columns:
            self.assertIn(col, converted_df.columns)
    
    def test_special_characters_in_data(self):
        """Test handling of special characters in student data."""
        special_data = {
            'Student': ['José García', 'François Müller'],
            'ID': [12001, 12002],
            'Current Score': [85.5, 72.3]
        }
        df = pd.DataFrame(special_data)
        
        # Should handle special characters without error
        try:
            converted_df = universal_gradebook_converter(df)
            self.assertEqual(len(converted_df), 2)
        except Exception as e:
            self.fail(f"Special characters caused error: {e}")
    
    def test_very_large_gradebook(self):
        """Test processing of large gradebook files."""
        # Create a larger dataset (100 students)
        large_csv = mock_data.generate_gradebook_csv_data(100)
        df = pd.read_csv(io.StringIO(large_csv))
        
        converted_df = universal_gradebook_converter(df)
        
        self.assertEqual(len(converted_df), 100)
        self.assertIn('id_student', converted_df.columns)
        
        # Check that all students have valid data
        self.assertTrue(all(converted_df['id_student'].notna()))
        self.assertTrue(all(converted_df['early_avg_score'] >= 0))

if __name__ == '__main__':
    unittest.main()