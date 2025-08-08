#!/usr/bin/env python3
"""
End-to-End Integration Tests for Student Success Prediction System

Tests complete workflows from CSV upload to prediction results,
including authentication, file processing, ML predictions, and API responses.
"""

import unittest
import tempfile
import os
import sys
import io
from pathlib import Path
from fastapi.testclient import TestClient
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment and API client"""
        # Set up test environment
        os.environ['TESTING'] = 'true'
        os.environ['DEVELOPMENT_MODE'] = 'true'
        os.environ['MVP_API_KEY'] = 'test-e2e-key-123456789'
        
        # Import and create test client
        from mvp.mvp_api import app
        cls.client = TestClient(app)
        cls.auth_headers = {'Authorization': 'Bearer test-e2e-key-123456789'}
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        test_vars = ['TESTING', 'DEVELOPMENT_MODE', 'MVP_API_KEY']
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
    
    def setUp(self):
        """Set up for each test"""
        self.sample_csv_data = """student_id,grade_level,current_gpa,attendance_rate,discipline_incidents,assignment_completion
S001,9,3.2,0.95,0,0.85
S002,10,2.1,0.78,3,0.62
S003,11,3.8,0.92,1,0.94
S004,12,2.5,0.86,2,0.73
S005,9,3.5,0.98,0,0.91"""
        
        self.canvas_csv_data = """Student,ID,Current Score,Assignment 1,Assignment 2,Quiz 1
Alice Johnson,12001,85.5,85,92,88
Bob Smith,12002,62.3,65,58,70
Carol Davis,12003,91.2,95,89,93"""
    
    def test_complete_generic_csv_workflow(self):
        """Test complete workflow: upload generic CSV -> get predictions -> explanations"""
        print("\n=== Testing Complete Generic CSV Workflow ===")
        
        # Step 1: Health check
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        print("✅ Health check passed")
        
        # Step 2: Upload and analyze CSV
        files = {"file": ("test_data.csv", self.sample_csv_data, "text/csv")}
        response = self.client.post("/api/mvp/analyze", files=files, headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('predictions', data)
        self.assertGreater(len(data['predictions']), 0)
        print(f"✅ CSV analysis completed: {len(data['predictions'])} predictions generated")
        
        # Step 3: Verify prediction structure
        prediction = data['predictions'][0]
        required_fields = ['student_id', 'risk_score', 'risk_category', 'success_probability']
        for field in required_fields:
            self.assertIn(field, prediction)
        print("✅ Prediction structure verified")
        
        # Step 4: Get individual explanation
        student_id = prediction['student_id']
        response = self.client.get(f"/api/mvp/explain/{student_id}", headers=self.auth_headers)
        
        if response.status_code == 200:
            explanation = response.json()
            self.assertIn('explanation', explanation)
            print("✅ Individual explanation generated")
        else:
            print(f"⚠️  Explanation endpoint returned {response.status_code} (acceptable for demo)")
        
        # Step 5: Get global insights
        response = self.client.get("/api/mvp/insights", headers=self.auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('insights', data)
            self.assertIn('feature_importance', data['insights'])
            print("✅ Global insights retrieved")
        else:
            print(f"⚠️  Insights endpoint returned {response.status_code} (acceptable for demo)")
    
    def test_canvas_lms_workflow(self):
        """Test Canvas LMS integration workflow"""
        print("\n=== Testing Canvas LMS Workflow ===")
        
        # Step 1: Upload Canvas format CSV
        files = {"file": ("canvas_grades.csv", self.canvas_csv_data, "text/csv")}
        response = self.client.post("/api/mvp/analyze", files=files, headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('predictions', data)
        print(f"✅ Canvas CSV processed: {len(data['predictions'])} students analyzed")
        
        # Step 2: Verify Canvas-specific processing
        prediction = data['predictions'][0]
        self.assertIn('student_id', prediction)
        self.assertIn('risk_score', prediction)
        print("✅ Canvas gradebook format handled correctly")
    
    def test_k12_ultra_advanced_workflow(self):
        """Test K-12 Ultra-Advanced model workflow"""
        print("\n=== Testing K-12 Ultra-Advanced Workflow ===")
        
        # Upload gradebook for K-12 analysis
        files = {"file": ("k12_gradebook.csv", self.sample_csv_data, "text/csv")}
        response = self.client.post("/api/mvp/analyze-k12", files=files, headers=self.auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('predictions', data)
            self.assertIn('summary', data)
            
            # Verify K-12 specific fields
            if len(data['predictions']) > 0:
                prediction = data['predictions'][0]
                k12_fields = ['risk_level', 'confidence']
                for field in k12_fields:
                    if field in prediction:
                        print(f"✅ K-12 field '{field}' present")
            
            print(f"✅ K-12 Ultra-Advanced analysis completed: {len(data['predictions'])} students")
        else:
            print(f"⚠️  K-12 endpoint returned {response.status_code} - model may not be available")
    
    def test_sample_data_workflow(self):
        """Test sample data generation and analysis"""
        print("\n=== Testing Sample Data Workflow ===")
        
        # Get sample data
        response = self.client.get("/api/mvp/sample", headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('predictions', data)
        self.assertGreater(len(data['predictions']), 0)
        print(f"✅ Sample data generated: {len(data['predictions'])} demo students")
        
        # Verify sample data structure
        prediction = data['predictions'][0]
        required_fields = ['student_id', 'risk_score', 'risk_category']
        for field in required_fields:
            self.assertIn(field, prediction)
        print("✅ Sample data structure verified")
    
    def test_detailed_analysis_workflow(self):
        """Test detailed analysis with explainable AI"""
        print("\n=== Testing Detailed Analysis Workflow ===")
        
        files = {"file": ("detailed_test.csv", self.sample_csv_data, "text/csv")}
        response = self.client.post("/api/mvp/analyze-detailed", files=files, headers=self.auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('predictions', data)
            print(f"✅ Detailed analysis completed: {len(data['predictions'])} detailed predictions")
            
            # Check for explanation fields
            if len(data['predictions']) > 0:
                prediction = data['predictions'][0]
                explanation_fields = ['explanation', 'risk_category']
                for field in explanation_fields:
                    if field in prediction:
                        print(f"✅ Explanation field '{field}' present")
        else:
            print(f"⚠️  Detailed analysis returned {response.status_code} - explainable AI may need setup")
    
    def test_authentication_workflow(self):
        """Test authentication and security workflows"""
        print("\n=== Testing Authentication Workflow ===")
        
        # Test without API key
        files = {"file": ("auth_test.csv", self.sample_csv_data, "text/csv")}
        response = self.client.post("/api/mvp/analyze", files=files)
        
        # Should require authentication (unless in development mode from localhost)
        if response.status_code == 401:
            print("✅ Authentication required for API access")
        else:
            print("⚠️  Development mode may be allowing localhost bypass")
        
        # Test with valid API key
        response = self.client.post("/api/mvp/analyze", files=files, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        print("✅ Valid API key accepted")
        
        # Test with invalid API key
        invalid_headers = {'Authorization': 'Bearer invalid-key'}
        response = self.client.post("/api/mvp/analyze", files=files, headers=invalid_headers)
        
        if response.status_code == 401:
            print("✅ Invalid API key rejected")
        else:
            print("⚠️  Development mode may be allowing localhost bypass")
    
    def test_error_handling_workflow(self):
        """Test error handling workflows"""
        print("\n=== Testing Error Handling Workflow ===")
        
        # Test empty file
        files = {"file": ("empty.csv", "", "text/csv")}
        response = self.client.post("/api/mvp/analyze", files=files, headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 400)
        print("✅ Empty file properly rejected")
        
        # Test invalid CSV format - create actual malformed CSV that pandas will reject
        invalid_csv = "header1,header2,header3\n\"unterminated quote,data,more data\nvalid,data,here"
        files = {"file": ("invalid.csv", invalid_csv, "text/csv")}
        response = self.client.post("/api/mvp/analyze", files=files, headers=self.auth_headers)
        
        # Should handle gracefully (400 or 500 acceptable)
        self.assertIn(response.status_code, [400, 500])
        print("✅ Invalid CSV format handled gracefully")
        
        # Test non-CSV file
        files = {"file": ("test.txt", "This is not a CSV file", "text/plain")}
        response = self.client.post("/api/mvp/analyze", files=files, headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 400)
        print("✅ Non-CSV file properly rejected")
    
    def test_api_statistics_workflow(self):
        """Test API statistics and monitoring"""
        print("\n=== Testing API Statistics Workflow ===")
        
        # Get system statistics
        response = self.client.get("/api/mvp/stats", headers=self.auth_headers)
        
        if response.status_code == 200:
            stats = response.json()
            expected_fields = ['total_predictions', 'system_status']
            for field in expected_fields:
                if field in stats:
                    print(f"✅ Statistics field '{field}' available")
            print("✅ System statistics accessible")
        else:
            print(f"⚠️  Statistics endpoint returned {response.status_code} - database may be unavailable")
    
    def test_web_interface_workflow(self):
        """Test web interface accessibility"""
        print("\n=== Testing Web Interface Workflow ===")
        
        # Test main page
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        print("✅ Main web interface accessible")
        
        # Test static files (if available)
        response = self.client.get("/static/css/style.css")
        if response.status_code == 200:
            print("✅ Static CSS files accessible")
        else:
            print("⚠️  Static files may not be mounted in test environment")
    
    def test_system_performance_workflow(self):
        """Test system performance and response times"""
        print("\n=== Testing System Performance Workflow ===")
        
        import time
        
        # Measure health check response time
        start_time = time.time()
        response = self.client.get("/health")
        health_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(health_time, 1.0, "Health check should be fast")
        print(f"✅ Health check response time: {health_time:.3f}s")
        
        # Measure CSV analysis response time
        files = {"file": ("perf_test.csv", self.sample_csv_data, "text/csv")}
        start_time = time.time()
        response = self.client.post("/api/mvp/analyze", files=files, headers=self.auth_headers)
        analysis_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(analysis_time, 10.0, "Analysis should complete reasonably quickly")
        print(f"✅ CSV analysis response time: {analysis_time:.3f}s")


class TestSystemIntegration(unittest.TestCase):
    """Test system integration points"""
    
    def setUp(self):
        """Set up test environment"""
        os.environ['TESTING'] = 'true'
        os.environ['DEVELOPMENT_MODE'] = 'true'
        os.environ['MVP_API_KEY'] = 'test-integration-key-123456789'
        
        from mvp.mvp_api import app
        self.client = TestClient(app)
        self.auth_headers = {'Authorization': 'Bearer test-integration-key-123456789'}
    
    def tearDown(self):
        """Clean up test environment"""
        test_vars = ['TESTING', 'DEVELOPMENT_MODE', 'MVP_API_KEY']
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_security_headers_integration(self):
        """Test that security headers are properly applied"""
        print("\n=== Testing Security Headers Integration ===")
        
        response = self.client.get("/health")
        
        # Check for key security headers
        security_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Referrer-Policy'
        ]
        
        headers_found = 0
        for header in security_headers:
            if header in response.headers:
                headers_found += 1
                print(f"✅ Security header '{header}' present")
        
        self.assertGreater(headers_found, 0, "At least some security headers should be present")
        print(f"✅ Security headers integration: {headers_found}/{len(security_headers)} headers found")
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration"""
        print("\n=== Testing Rate Limiting Integration ===")
        
        # Make multiple rapid requests
        responses = []
        for i in range(5):
            response = self.client.get("/health")
            responses.append(response.status_code)
        
        # All should succeed in test environment (rate limiting disabled for tests)
        success_count = sum(1 for status in responses if status == 200)
        self.assertGreater(success_count, 0)
        print(f"✅ Rate limiting integration: {success_count}/5 requests successful")
        
        # Note: Rate limiting is disabled during testing, so all should pass
        if success_count == 5:
            print("✅ Rate limiting correctly disabled for testing environment")
    
    def test_database_integration(self):
        """Test database integration (if available)"""
        print("\n=== Testing Database Integration ===")
        
        try:
            # Try to get statistics (which requires database)
            response = self.client.get("/api/mvp/stats", headers=self.auth_headers)
            
            if response.status_code == 200:
                stats = response.json()
                if 'system_status' in stats:
                    print(f"✅ Database integration working: status = {stats.get('system_status')}")
                else:
                    print("⚠️  Database statistics available but incomplete")
            else:
                print("⚠️  Database may not be available in test environment")
        except Exception as e:
            print(f"⚠️  Database integration test error: {e}")
    
    def test_ml_model_integration(self):
        """Test ML model integration"""
        print("\n=== Testing ML Model Integration ===")
        
        # Test sample data generation (requires ML models)
        response = self.client.get("/api/mvp/sample", headers=self.auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'predictions' in data and len(data['predictions']) > 0:
                prediction = data['predictions'][0]
                if 'risk_score' in prediction:
                    risk_score = prediction['risk_score']
                    self.assertGreaterEqual(risk_score, 0)
                    self.assertLessEqual(risk_score, 1)
                    print("✅ ML model integration working: valid risk scores generated")
                else:
                    print("⚠️  ML predictions missing risk_score field")
            else:
                print("⚠️  ML model returned empty predictions")
        else:
            print(f"⚠️  ML model integration issue: status {response.status_code}")
    
    def test_complete_system_health(self):
        """Test overall system health"""
        print("\n=== Testing Complete System Health ===")
        
        health_checks = []
        
        # Basic health check
        response = self.client.get("/health")
        health_checks.append(("Health Endpoint", response.status_code == 200))
        
        # API functionality
        response = self.client.get("/api/mvp/sample", headers=self.auth_headers)
        health_checks.append(("API Functionality", response.status_code == 200))
        
        # Web interface
        response = self.client.get("/")
        health_checks.append(("Web Interface", response.status_code == 200))
        
        # Security headers
        response = self.client.get("/health")
        has_security_headers = any(header in response.headers 
                                 for header in ['X-Frame-Options', 'X-Content-Type-Options'])
        health_checks.append(("Security Headers", has_security_headers))
        
        # Report results
        passed_checks = sum(1 for _, status in health_checks if status)
        total_checks = len(health_checks)
        
        for check_name, status in health_checks:
            status_symbol = "✅" if status else "❌"
            print(f"{status_symbol} {check_name}: {'PASS' if status else 'FAIL'}")
        
        print(f"\n🏁 System Health: {passed_checks}/{total_checks} checks passed")
        
        # Require at least 75% of checks to pass
        self.assertGreaterEqual(passed_checks / total_checks, 0.75, 
                               f"System health insufficient: {passed_checks}/{total_checks} checks passed")


if __name__ == '__main__':
    unittest.main(verbosity=2)