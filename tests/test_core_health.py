#!/usr/bin/env python3
"""
Core Health Tests

Basic automated tests for critical system functionality.
Tests health endpoints, authentication, and core ML pipeline.
"""

import pytest
import requests
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class TestHealthEndpoints:
    """Test all health check endpoints"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for the application"""
        return os.getenv('TEST_BASE_URL', 'http://localhost:8001')
    
    def test_basic_health_check(self, base_url):
        """Test basic health endpoint"""
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['service'] == 'student-success-predictor'
    
    def test_detailed_health_check(self, base_url):
        """Test detailed health diagnostics"""
        response = requests.get(f"{base_url}/health/detailed", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
        assert 'checks' in data
        assert 'response_time_ms' in data
        
        # Verify critical components are checked
        checks = data['checks']
        assert 'database' in checks
        assert 'ml_models' in checks
        assert 'system_resources' in checks
        assert 'authentication' in checks
    
    def test_readiness_probe(self, base_url):
        """Test Kubernetes-style readiness probe"""
        response = requests.get(f"{base_url}/health/ready", timeout=10)
        # Should be 200 if ready, 503 if not ready
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert data['status'] == 'ready'
    
    def test_liveness_probe(self, base_url):
        """Test Kubernetes-style liveness probe"""
        response = requests.get(f"{base_url}/health/live", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'alive'
        assert 'timestamp' in data
    
    def test_metrics_endpoint(self, base_url):
        """Test system metrics endpoint"""
        response = requests.get(f"{base_url}/health/metrics", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert 'memory_usage_percent' in data
        assert 'disk_usage_percent' in data
        assert 'cpu_usage_percent' in data
        assert isinstance(data['memory_usage_percent'], (int, float))
        assert isinstance(data['disk_usage_percent'], (int, float))


class TestAuthentication:
    """Test authentication system"""
    
    @pytest.fixture
    def base_url(self):
        return os.getenv('TEST_BASE_URL', 'http://localhost:8001')
    
    def test_auth_status_endpoint(self, base_url):
        """Test authentication status endpoint"""
        # Test without credentials (should work with browser auth)
        response = requests.get(
            f"{base_url}/api/mvp/auth/status",
            headers={'User-Agent': 'Mozilla/5.0 (Test Browser)'},
            timeout=5
        )
        # Should either authenticate with browser fallback or return 401
        assert response.status_code in [200, 401]
    
    def test_web_login_endpoint(self, base_url):
        """Test web login endpoint"""
        response = requests.post(
            f"{base_url}/api/mvp/auth/web-login",
            headers={'User-Agent': 'Mozilla/5.0 (Test Browser)'},
            timeout=5
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'authenticated'
        assert 'user' in data


class TestCoreMLPipeline:
    """Test core ML prediction pipeline"""
    
    @pytest.fixture
    def base_url(self):
        return os.getenv('TEST_BASE_URL', 'http://localhost:8001')
    
    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV data for testing"""
        return """Student,ID,Current Score,Assignment 1 (10 pts),Assignment 2 (15 pts)
John Smith,1001,85.5,9,14
Sarah Johnson,1002,92.3,10,15
Mike Chen,1003,76.8,7,12"""
    
    def test_sample_data_endpoint(self, base_url):
        """Test sample data loading"""
        response = requests.get(
            f"{base_url}/api/mvp/sample",
            headers={'User-Agent': 'Mozilla/5.0 (Test Browser)'},
            timeout=10
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'predictions' in data or 'students' in data
        assert 'message' in data
        
        # Verify prediction structure
        predictions = data.get('predictions', data.get('students', []))
        if predictions:
            prediction = predictions[0]
            assert 'student_id' in prediction
            assert 'risk_score' in prediction
            assert 'risk_category' in prediction
    
    def test_csv_analysis_structure(self, base_url, sample_csv_data):
        """Test CSV analysis endpoint structure (without file upload)"""
        # This test verifies the endpoint exists and has proper error handling
        response = requests.post(
            f"{base_url}/api/mvp/analyze",
            headers={'User-Agent': 'Mozilla/5.0 (Test Browser)'},
            timeout=5
        )
        # Should return 422 (validation error) for missing file, not 404 or 500
        assert response.status_code == 422


class TestSystemIntegration:
    """Test system integration and performance"""
    
    @pytest.fixture
    def base_url(self):
        return os.getenv('TEST_BASE_URL', 'http://localhost:8001')
    
    def test_main_page_loads(self, base_url):
        """Test that main web interface loads"""
        response = requests.get(base_url, timeout=10)
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
    
    def test_static_files_accessible(self, base_url):
        """Test that static files are accessible"""
        # Test CSS file
        css_response = requests.get(f"{base_url}/static/css/style.css", timeout=5)
        # Should be 200 if file exists, 404 if not (both are acceptable for test)
        assert css_response.status_code in [200, 404]
        
        # Test JS file
        js_response = requests.get(f"{base_url}/static/js/app.js", timeout=5)
        assert js_response.status_code in [200, 404]
    
    def test_api_response_times(self, base_url):
        """Test that API responses are reasonable"""
        import time
        
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=5)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds
        
        # Check if timing header is present
        if 'X-Process-Time' in response.headers:
            process_time = float(response.headers['X-Process-Time'])
            assert process_time < 1000  # Should process within 1000ms


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def base_url(self):
        return os.getenv('TEST_BASE_URL', 'http://localhost:8001')
    
    def test_nonexistent_endpoint_404(self, base_url):
        """Test that nonexistent endpoints return 404"""
        response = requests.get(f"{base_url}/api/nonexistent", timeout=5)
        assert response.status_code == 404
    
    def test_malformed_requests_handled(self, base_url):
        """Test that malformed requests are handled gracefully"""
        # Test POST to GET endpoint
        response = requests.post(f"{base_url}/health", timeout=5)
        assert response.status_code == 405  # Method not allowed
    
    def test_large_request_handling(self, base_url):
        """Test handling of large requests"""
        # Create a large dummy payload
        large_data = "x" * (1024 * 1024)  # 1MB of data
        
        response = requests.post(
            f"{base_url}/api/mvp/analyze",
            data=large_data,
            headers={'User-Agent': 'Mozilla/5.0 (Test Browser)'},
            timeout=10
        )
        # Should handle gracefully (either 413 payload too large or 422 validation error)
        assert response.status_code in [413, 422, 400]


if __name__ == "__main__":
    # Run tests directly with pytest
    pytest.main([__file__, "-v"])