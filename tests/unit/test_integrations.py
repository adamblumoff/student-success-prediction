#!/usr/bin/env python3
"""
Unit tests for LMS/SIS Integration System.

Tests Canvas LMS, PowerSchool SIS, and Google Classroom integrations.
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from fastapi.testclient import TestClient
from mvp.mvp_api import app

class TestCanvasIntegration(unittest.TestCase):
    """Test Canvas LMS integration endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['TESTING'] = 'true'
        os.environ['MVP_API_KEY'] = 'test-key-12345'
        os.environ['DATABASE_URL'] = 'sqlite:///./test_canvas.db'
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        cls.client = TestClient(app)
        cls.auth_headers = {'Authorization': 'Bearer test-key-12345'}
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        test_db = Path('./test_canvas.db')
        if test_db.exists():
            test_db.unlink()
            
        test_env_vars = ['TESTING', 'MVP_API_KEY', 'DATABASE_URL', 'DEVELOPMENT_MODE']
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]
                
    def test_canvas_health_endpoint(self):
        """Test Canvas integration health check."""
        response = self.client.get("/api/lms/canvas/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['service'], 'Canvas LMS Integration')
        self.assertIn('status', data)
        self.assertIn('features', data)
        
    @patch('integrations.canvas_lms.CanvasLMS')
    def test_canvas_connection(self, mock_canvas_class):
        """Test Canvas LMS connection endpoint."""
        # Mock Canvas connection
        mock_canvas = MagicMock()
        mock_canvas.test_connection.return_value = {
            'success': True,
            'account_name': 'Test University',
            'user_name': 'Test User'
        }
        mock_canvas_class.return_value = mock_canvas
        
        connection_data = {
            "base_url": "https://test.instructure.com",
            "access_token": "test_token_12345"
        }
        
        response = self.client.post(
            "/api/lms/canvas/connect",
            json=connection_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('account_info', data)
        self.assertEqual(data['message'], 'Successfully connected to Canvas LMS')
        
    @patch('integrations.canvas_lms.CanvasLMS')
    def test_canvas_courses_endpoint(self, mock_canvas_class):
        """Test Canvas courses retrieval."""
        # Mock Canvas courses
        mock_canvas = MagicMock()
        mock_canvas.get_courses.return_value = [
            {
                'id': 12345,
                'name': 'Introduction to Computer Science',
                'course_code': 'CS-101',
                'term': 'Fall 2024',
                'student_count': 25
            },
            {
                'id': 12346,
                'name': 'Data Structures',
                'course_code': 'CS-201', 
                'term': 'Fall 2024',
                'student_count': 18
            }
        ]
        mock_canvas_class.return_value = mock_canvas
        
        request_data = {
            "base_url": "https://test.instructure.com",
            "access_token": "test_token_12345"
        }
        
        response = self.client.post(
            "/api/lms/canvas/courses",
            json=request_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('courses', data)
        self.assertEqual(len(data['courses']), 2)
        
        first_course = data['courses'][0]
        self.assertIn('id', first_course)
        self.assertIn('name', first_course)
        self.assertIn('student_count', first_course)
        
    @patch('integrations.canvas_lms.CanvasLMS')
    @patch('mvp.api.canvas_endpoints.intervention_system')
    def test_canvas_sync_endpoint(self, mock_intervention_system, mock_canvas_class):
        """Test Canvas course synchronization."""
        # Mock Canvas student data
        mock_canvas = MagicMock()
        mock_canvas.get_course_students.return_value = [
            {
                'id': 1001,
                'name': 'John Doe',
                'current_score': 85.5,
                'total_activity_time': 3600,
                'submissions_count': 12
            },
            {
                'id': 1002,
                'name': 'Jane Smith',
                'current_score': 78.2,
                'total_activity_time': 2800,
                'submissions_count': 10
            }
        ]
        mock_canvas_class.return_value = mock_canvas
        
        # Mock intervention system
        import pandas as pd
        mock_predictions = pd.DataFrame([
            {
                'id_student': 1001,
                'risk_score': 0.25,
                'risk_category': 'Low Risk',
                'success_probability': 0.85
            },
            {
                'id_student': 1002,
                'risk_score': 0.45,
                'risk_category': 'Medium Risk', 
                'success_probability': 0.68
            }
        ])
        mock_intervention_system.assess_student_risk.return_value = mock_predictions
        
        sync_data = {
            "base_url": "https://test.instructure.com",
            "access_token": "test_token_12345",
            "course_id": 12345
        }
        
        response = self.client.post(
            "/api/lms/canvas/sync",
            json=sync_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('predictions', data)
        self.assertIn('summary', data)
        self.assertEqual(data['students_processed'], 2)
        
    def test_canvas_invalid_credentials(self):
        """Test Canvas connection with invalid credentials."""
        with patch('integrations.canvas_lms.CanvasLMS') as mock_canvas_class:
            mock_canvas = MagicMock()
            mock_canvas.test_connection.side_effect = Exception("Invalid access token")
            mock_canvas_class.return_value = mock_canvas
            
            connection_data = {
                "base_url": "https://test.instructure.com",
                "access_token": "invalid_token"
            }
            
            response = self.client.post(
                "/api/lms/canvas/connect",
                json=connection_data,
                headers=self.auth_headers
            )
            
            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertIn('error', data['detail'])


class TestPowerSchoolIntegration(unittest.TestCase):
    """Test PowerSchool SIS integration endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['TESTING'] = 'true'
        os.environ['MVP_API_KEY'] = 'test-key-12345'
        os.environ['DATABASE_URL'] = 'sqlite:///./test_powerschool.db'
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        cls.client = TestClient(app)
        cls.auth_headers = {'Authorization': 'Bearer test-key-12345'}
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        test_db = Path('./test_powerschool.db')
        if test_db.exists():
            test_db.unlink()
            
        test_env_vars = ['TESTING', 'MVP_API_KEY', 'DATABASE_URL', 'DEVELOPMENT_MODE']
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]
                
    def test_powerschool_health_endpoint(self):
        """Test PowerSchool integration health check."""
        response = self.client.get("/api/sis/powerschool/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['service'], 'PowerSchool SIS Integration')
        self.assertIn('status', data)
        self.assertIn('features', data)
        
    @patch('integrations.powerschool_sis.PowerSchoolSIS')
    def test_powerschool_authentication(self, mock_ps_class):
        """Test PowerSchool OAuth authentication."""
        # Mock PowerSchool authentication
        mock_ps = MagicMock()
        mock_ps.authenticate.return_value = {
            'success': True,
            'access_token': 'mock_access_token',
            'expires_in': 3600
        }
        mock_ps_class.return_value = mock_ps
        
        auth_data = {
            "base_url": "https://district.powerschool.com",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        }
        
        response = self.client.post(
            "/api/sis/powerschool/authenticate",
            json=auth_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('access_token', data)
        self.assertEqual(data['message'], 'Successfully authenticated with PowerSchool')
        
    @patch('integrations.powerschool_sis.PowerSchoolSIS')
    def test_powerschool_schools_endpoint(self, mock_ps_class):
        """Test PowerSchool schools retrieval."""
        # Mock PowerSchool schools
        mock_ps = MagicMock()
        mock_ps.get_schools.return_value = [
            {
                'id': 1,
                'name': 'Lincoln Elementary',
                'school_number': 101,
                'grades': 'K-5',
                'student_count': 450
            },
            {
                'id': 2,
                'name': 'Washington Middle School',
                'school_number': 201,
                'grades': '6-8',
                'student_count': 380
            }
        ]
        mock_ps_class.return_value = mock_ps
        
        request_data = {
            "base_url": "https://district.powerschool.com",
            "access_token": "test_access_token"
        }
        
        response = self.client.post(
            "/api/sis/powerschool/schools",
            json=request_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('schools', data)
        self.assertEqual(len(data['schools']), 2)
        
    @patch('integrations.powerschool_sis.PowerSchoolSIS')
    @patch('models.k12_ultra_predictor.K12UltraPredictor')
    def test_powerschool_sync_endpoint(self, mock_k12_predictor, mock_ps_class):
        """Test PowerSchool school synchronization."""
        # Mock PowerSchool student data
        mock_ps = MagicMock()
        mock_ps.get_school_students.return_value = [
            {
                'student_number': 'S001',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'grade_level': 8,
                'gpa': 3.2,
                'attendance_rate': 0.92,
                'behavior_incidents': 1
            }
        ]
        mock_ps_class.return_value = mock_ps
        
        # Mock K-12 predictor
        mock_predictor = MagicMock()
        mock_predictor.predict_from_sis_data.return_value = {
            'predictions': [
                {
                    'student_id': 'S001',
                    'student_name': 'Alice Johnson',
                    'grade_level': 8,
                    'risk_level': 'Medium',
                    'risk_score': 0.42,
                    'intervention_recommended': True
                }
            ],
            'summary': {
                'total_students': 1,
                'risk_distribution': {'high': 0, 'medium': 1, 'low': 0}
            }
        }
        mock_k12_predictor.return_value = mock_predictor
        
        sync_data = {
            "base_url": "https://district.powerschool.com",
            "access_token": "test_access_token",
            "school_id": 1
        }
        
        response = self.client.post(
            "/api/sis/powerschool/sync",
            json=sync_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('predictions', data)
        self.assertIn('summary', data)


class TestGoogleClassroomIntegration(unittest.TestCase):
    """Test Google Classroom integration endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['TESTING'] = 'true'
        os.environ['MVP_API_KEY'] = 'test-key-12345'
        os.environ['DATABASE_URL'] = 'sqlite:///./test_google.db'
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        cls.client = TestClient(app)
        cls.auth_headers = {'Authorization': 'Bearer test-key-12345'}
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        test_db = Path('./test_google.db')
        if test_db.exists():
            test_db.unlink()
            
        test_env_vars = ['TESTING', 'MVP_API_KEY', 'DATABASE_URL', 'DEVELOPMENT_MODE']
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]
                
    def test_google_classroom_health_endpoint(self):
        """Test Google Classroom integration health check."""
        response = self.client.get("/api/google/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['service'], 'Google Classroom Integration')
        self.assertIn('status', data)
        self.assertIn('features', data)
        
    @patch('integrations.google_classroom.GoogleClassroomIntegration')
    def test_google_oauth_status(self, mock_google_class):
        """Test Google OAuth status check."""
        # Mock Google OAuth status
        mock_google = MagicMock()
        mock_google.check_credentials.return_value = {
            'authenticated': True,
            'user_email': 'teacher@school.edu',
            'expires_at': '2024-12-31T23:59:59Z'
        }
        mock_google_class.return_value = mock_google
        
        response = self.client.get(
            "/api/google/oauth/status",
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('oauth_status', data)
        self.assertTrue(data['oauth_status']['authenticated'])
        
    @patch('integrations.google_classroom.GoogleClassroomIntegration')
    def test_google_courses_endpoint(self, mock_google_class):
        """Test Google Classroom courses retrieval."""
        # Mock Google Classroom courses
        mock_google = MagicMock()
        mock_google.get_courses.return_value = [
            {
                'id': 'course_001',
                'name': 'Mathematics Grade 8',
                'section': 'Period 1',
                'teacher': 'Ms. Smith',
                'student_count': 28,
                'creation_time': '2024-08-15T10:00:00Z'
            }
        ]
        mock_google_class.return_value = mock_google
        
        response = self.client.get(
            "/api/google/courses",
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('courses', data)
        self.assertEqual(len(data['courses']), 1)
        
    @patch('integrations.google_classroom.GoogleClassroomIntegration')
    def test_google_sync_course(self, mock_google_class):
        """Test Google Classroom course synchronization."""
        # Mock Google Classroom student data
        mock_google = MagicMK()
        mock_google.get_course_students.return_value = [
            {
                'userId': 'student_001',
                'profile': {
                    'name': {'fullName': 'Bob Wilson'},
                    'emailAddress': 'bob.wilson@student.edu'
                }
            }
        ]
        
        mock_google.get_student_work.return_value = [
            {
                'courseId': 'course_001',
                'userId': 'student_001',
                'assignments_completed': 15,
                'assignments_total': 18,
                'average_score': 82.5,
                'submission_timeliness': 0.87
            }
        ]
        mock_google_class.return_value = mock_google
        
        sync_data = {
            "course_id": "course_001"
        }
        
        response = self.client.post(
            "/api/google/sync",
            json=sync_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('students_processed', data)
        self.assertIn('predictions', data)


class TestCombinedIntegrationEndpoints(unittest.TestCase):
    """Test combined/cross-platform integration endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['TESTING'] = 'true'
        os.environ['MVP_API_KEY'] = 'test-key-12345'
        os.environ['DATABASE_URL'] = 'sqlite:///./test_combined.db'
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        cls.client = TestClient(app)
        cls.auth_headers = {'Authorization': 'Bearer test-key-12345'}
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        test_db = Path('./test_combined.db')
        if test_db.exists():
            test_db.unlink()
            
        test_env_vars = ['TESTING', 'MVP_API_KEY', 'DATABASE_URL', 'DEVELOPMENT_MODE']
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]
                
    def test_integration_health_endpoint(self):
        """Test combined integration health check."""
        response = self.client.get("/api/integration/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['service'], 'Combined LMS/SIS Integration')
        self.assertIn('status', data)
        self.assertIn('supported_platforms', data)
        
    @patch('integrations.combined_integration.CombinedIntegration')
    def test_cross_platform_analysis(self, mock_combined_class):
        """Test cross-platform analysis endpoint."""
        # Mock combined analysis results
        mock_combined = MagicMock()
        mock_combined.analyze_cross_platform.return_value = {
            'platforms_analyzed': ['canvas', 'powerschool'],
            'total_students': 150,
            'combined_insights': {
                'engagement_correlation': 0.74,
                'academic_performance_trend': 'improving',
                'risk_factors': ['attendance', 'assignment_completion']
            },
            'recommendations': [
                'Focus on attendance intervention programs',
                'Implement assignment completion tracking'
            ]
        }
        mock_combined_class.return_value = mock_combined
        
        analysis_data = {
            "platforms": ["canvas", "powerschool"],
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            }
        }
        
        response = self.client.post(
            "/api/integration/analyze-cross-platform",
            json=analysis_data,
            headers=self.auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('analysis_results', data)
        self.assertIn('platforms_analyzed', data['analysis_results'])
        
    def test_platform_comparison_endpoint(self):
        """Test platform comparison endpoint."""
        with patch('integrations.combined_integration.CombinedIntegration') as mock_combined_class:
            mock_combined = MagicMock()
            mock_combined.compare_platforms.return_value = {
                'canvas': {
                    'strengths': ['Rich gradebook', 'Assignment tracking'],
                    'student_engagement': 0.82,
                    'data_completeness': 0.95
                },
                'powerschool': {
                    'strengths': ['Attendance tracking', 'Behavioral data'],
                    'student_engagement': 0.78,
                    'data_completeness': 0.88
                }
            }
            mock_combined_class.return_value = mock_combined
            
            response = self.client.get(
                "/api/integration/compare-platforms",
                headers=self.auth_headers
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertEqual(data['status'], 'success')
            self.assertIn('platform_comparison', data)


class TestIntegrationErrorHandling(unittest.TestCase):
    """Test error handling for integration endpoints."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        os.environ['TESTING'] = 'true'
        os.environ['MVP_API_KEY'] = 'test-key-12345'
        os.environ['DATABASE_URL'] = 'sqlite:///./test_errors.db'
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        cls.client = TestClient(app)
        cls.auth_headers = {'Authorization': 'Bearer test-key-12345'}
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        test_db = Path('./test_errors.db')
        if test_db.exists():
            test_db.unlink()
            
        test_env_vars = ['TESTING', 'MVP_API_KEY', 'DATABASE_URL', 'DEVELOPMENT_MODE']
        for var in test_env_vars:
            if var in os.environ:
                del os.environ[var]
                
    def test_missing_credentials_error(self):
        """Test error handling for missing credentials."""
        response = self.client.post(
            "/api/lms/canvas/connect",
            json={},  # Empty request
            headers=self.auth_headers
        )
        
        # Should return validation error
        self.assertEqual(response.status_code, 422)
        
    def test_network_error_handling(self):
        """Test error handling for network issues."""
        with patch('integrations.canvas_lms.CanvasLMS') as mock_canvas_class:
            mock_canvas = MagicMock()
            mock_canvas.test_connection.side_effect = ConnectionError("Network unreachable")
            mock_canvas_class.return_value = mock_canvas
            
            connection_data = {
                "base_url": "https://unreachable.instructure.com",
                "access_token": "test_token"
            }
            
            response = self.client.post(
                "/api/lms/canvas/connect",
                json=connection_data,
                headers=self.auth_headers
            )
            
            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertIn('Network unreachable', data['detail'])
            
    def test_authentication_required(self):
        """Test that authentication is required for integration endpoints."""
        response = self.client.get("/api/lms/canvas/courses")
        
        self.assertEqual(response.status_code, 401)
        
    def test_invalid_course_id_error(self):
        """Test error handling for invalid course/school IDs."""
        with patch('integrations.canvas_lms.CanvasLMS') as mock_canvas_class:
            mock_canvas = MagicMock()
            mock_canvas.get_course_students.side_effect = Exception("Course not found")
            mock_canvas_class.return_value = mock_canvas
            
            sync_data = {
                "base_url": "https://test.instructure.com",
                "access_token": "test_token",
                "course_id": 99999  # Non-existent course
            }
            
            response = self.client.post(
                "/api/lms/canvas/sync",
                json=sync_data,
                headers=self.auth_headers
            )
            
            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertIn('Course not found', data['detail'])


if __name__ == '__main__':
    unittest.main()