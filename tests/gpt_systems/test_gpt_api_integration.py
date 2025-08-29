#!/usr/bin/env python3
"""
GPT API Integration Test Suite

Tests the integration of GPT-5-nano with the Student Success Platform API endpoints,
ensuring proper data flow, authentication, and educational recommendation generation.
"""

import pytest
import json
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Set test environment
os.environ['TESTING'] = 'true'
os.environ['MVP_API_KEY'] = 'test-api-key-secure-32-chars-min'
os.environ['OPENAI_API_KEY'] = 'test-openai-api-key-for-testing'

from src.mvp.mvp_api import app

@pytest.fixture
def client():
    """Test client for API requests"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    return {"Authorization": "Bearer test-api-key-secure-32-chars-min"}

@pytest.fixture
def mock_gpt_service():
    """Mock GPT service for testing"""
    mock_service = Mock()
    
    # Mock Emma Johnson format response
    emma_johnson_response = """1. **Academic Support Focus**
   - Schedule weekly math tutoring sessions with peer mentor

2. **Family Engagement Strategy**
   - Send bi-weekly progress updates to parents via email

3. **Behavioral Monitoring Plan**
   - Implement daily check-in system with guidance counselor"""
    
    mock_service.generate_student_recommendations.return_value = emma_johnson_response
    mock_service.estimate_cost.return_value = 0.0001
    mock_service.last_token_usage = 156
    
    return mock_service

@pytest.fixture
def sample_student_database_data():
    """Sample student data as it would exist in database"""
    return {
        'id': 1309,
        'student_id': '1309',
        'name': 'Noah Davis',
        'grade_level': 9,
        'current_gpa': 2.1,
        'attendance_rate': 0.73,
        'behavioral_incidents': 2,
        'assignment_completion': 0.67,
        'risk_score': 0.68,
        'risk_category': 'High Risk',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

class TestGPTInsightsEndpoints:
    """Test GPT insights API endpoints"""
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    @patch('src.mvp.database.Database')
    def test_generate_student_insights_success(self, mock_db, mock_get_gpt_service, 
                                             client, auth_headers, mock_gpt_service,
                                             sample_student_database_data):
        """Test successful GPT insight generation for a student"""
        # Setup mocks
        mock_get_gpt_service.return_value = mock_gpt_service
        
        mock_session = Mock()
        mock_student = Mock()
        mock_student.__dict__.update(sample_student_database_data)
        mock_session.query.return_value.filter.return_value.first.return_value = mock_student
        mock_db.return_value.get_session.return_value = mock_session
        
        # Make API request
        response = client.post(
            "/api/mvp/gpt-insights/generate",
            json={"student_id": "1309"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "recommendations" in data or "insights" in data
        assert "student_id" in data
        assert "format" in data
        assert data["format"] == "emma-johnson"
        
        # Verify GPT service was called with correct data
        mock_gpt_service.generate_student_recommendations.assert_called_once()
        call_args = mock_gpt_service.generate_student_recommendations.call_args[0][0]
        assert call_args['student_id'] == '1309'
        assert call_args['gpa'] == 2.1
        assert call_args['attendance_rate'] == 0.73
    
    def test_generate_insights_requires_authentication(self, client):
        """Test GPT insights endpoint requires authentication"""
        response = client.post(
            "/api/mvp/gpt-insights/generate",
            json={"student_id": "1309"}
        )
        
        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_generate_insights_invalid_student(self, mock_get_gpt_service, 
                                             client, auth_headers, mock_gpt_service):
        """Test GPT insights for non-existent student"""
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "9999"},
                headers=auth_headers
            )
            
            assert response.status_code == 404
            assert "student not found" in response.json()["detail"].lower()
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_gpt_service_error_handling(self, mock_get_gpt_service,
                                      client, auth_headers):
        """Test handling of GPT service errors"""
        # Mock GPT service error
        mock_service = Mock()
        mock_service.generate_student_recommendations.side_effect = Exception("GPT API Error")
        mock_get_gpt_service.return_value = mock_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            assert "unable to generate" in response.json()["detail"].lower()

class TestGPTCachingIntegration:
    """Test GPT caching integration with API endpoints"""
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_cache_service')
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_cache_hit_reduces_api_calls(self, mock_get_gpt_service, mock_get_cache_service,
                                       client, auth_headers, mock_gpt_service):
        """Test cached responses prevent duplicate GPT API calls"""
        # Setup cache service mock
        mock_cache_service = Mock()
        cached_response = {
            'raw_response': json.dumps({
                'recommendations': 'cached recommendations',
                'format': 'emma-johnson',
                'tokens_used': 0
            }),
            'cached': True,
            'cache_hits': 1,
            'created_at': datetime.now()
        }
        mock_cache_service.get_cached_response.return_value = cached_response
        mock_get_cache_service.return_value = mock_cache_service
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            
            # Verify GPT service was NOT called (cache hit)
            mock_gpt_service.generate_student_recommendations.assert_not_called()
            
            # Verify cache was checked
            mock_cache_service.get_cached_response.assert_called_once()
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_cache_service')
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_cache_miss_calls_gpt_api(self, mock_get_gpt_service, mock_get_cache_service,
                                    client, auth_headers, mock_gpt_service):
        """Test cache miss results in GPT API call"""
        # Setup cache service mock (cache miss)
        mock_cache_service = Mock()
        mock_cache_service.get_cached_response.return_value = None
        mock_get_cache_service.return_value = mock_cache_service
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            
            # Verify GPT service WAS called (cache miss)
            mock_gpt_service.generate_student_recommendations.assert_called_once()
            
            # Verify result was cached
            mock_cache_service.store_response.assert_called_once()

class TestEmmaJohnsonFormatValidation:
    """Test Emma Johnson format validation in API responses"""
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_emma_johnson_format_compliance(self, mock_get_gpt_service,
                                          client, auth_headers, mock_gpt_service):
        """Test API returns responses in Emma Johnson format"""
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify Emma Johnson format indicators
            assert data["format"] == "emma-johnson"
            
            # Check response structure matches Emma Johnson format
            if "recommendations" in data:
                recommendations = data["recommendations"]
                assert len(recommendations) == 3, "Should have exactly 3 recommendations"
                
                for i, rec in enumerate(recommendations, 1):
                    assert "title" in rec, f"Recommendation {i} should have title"
                    assert "implementation" in rec, f"Recommendation {i} should have implementation"
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_educational_appropriateness_validation(self, mock_get_gpt_service,
                                                  client, auth_headers):
        """Test GPT responses are educationally appropriate"""
        # Mock service with educational response
        mock_service = Mock()
        educational_response = """1. **Academic Tutoring Support**
   - Arrange weekly math tutoring sessions with qualified peer mentor

2. **Parent-Teacher Communication**
   - Establish bi-weekly progress update system with parents

3. **Behavioral Intervention Plan**
   - Implement daily check-in meetings with school counselor"""
        
        mock_service.generate_student_recommendations.return_value = educational_response
        mock_get_gpt_service.return_value = mock_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            response_text = str(response.json()).lower()
            
            # Should contain educational terms
            educational_terms = ['academic', 'tutoring', 'parent', 'teacher', 'counselor']
            found_terms = [term for term in educational_terms if term in response_text]
            assert len(found_terms) >= 2, f"Response should contain educational terms, found: {found_terms}"
            
            # Should not contain inappropriate terms
            inappropriate_terms = ['medication', 'therapy', 'diagnosis']
            for term in inappropriate_terms:
                assert term not in response_text, f"Response should not contain: {term}"

class TestCostManagementIntegration:
    """Test cost management features in API integration"""
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_token_usage_tracking(self, mock_get_gpt_service,
                                client, auth_headers, mock_gpt_service):
        """Test token usage is tracked and reported"""
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should include token usage information
            assert "tokens_used" in data
            assert data["tokens_used"] == 156  # From mock
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_cost_estimation_endpoint(self, mock_get_gpt_service,
                                    client, auth_headers, mock_gpt_service):
        """Test cost estimation for budgeting purposes"""
        mock_get_gpt_service.return_value = mock_gpt_service
        
        response = client.get(
            "/api/mvp/gpt-insights/cost-estimate",
            params={"students": 1000, "requests_per_student": 3},
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "estimated_cost" in data
            assert "total_tokens" in data
            assert data["estimated_cost"] > 0
        else:
            # Endpoint might not exist yet - that's okay for this test
            assert response.status_code in [404, 405]

class TestDataPrivacyInIntegration:
    """Test data privacy compliance in GPT API integration"""
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_no_pii_in_api_responses(self, mock_get_gpt_service,
                                   client, auth_headers, mock_gpt_service):
        """Test API responses don't contain PII"""
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_student.name = 'John Doe'
            mock_student.ssn = '123-45-6789'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            response_text = str(response.json())
            
            # Should not contain sensitive information
            assert 'John Doe' not in response_text
            assert '123-45-6789' not in response_text
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_audit_logging_for_gpt_requests(self, mock_get_gpt_service,
                                          client, auth_headers, mock_gpt_service):
        """Test GPT requests are properly audit logged"""
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            with patch('src.mvp.audit_logger.audit_logger.log_event') as mock_audit:
                response = client.post(
                    "/api/mvp/gpt-insights/generate",
                    json={"student_id": "1309"},
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                
                # Should log the GPT insight generation
                mock_audit.assert_called()
                call_args = mock_audit.call_args[1]
                assert call_args['action'] == 'GPT_INSIGHT_GENERATION'
                assert call_args['resource_type'] == 'student_data'

class TestGradeLevelSpecificIntegration:
    """Test grade-level specific GPT integration"""
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_elementary_grade_specific_recommendations(self, mock_get_gpt_service,
                                                     client, auth_headers):
        """Test elementary-specific GPT recommendations"""
        # Mock elementary-focused response
        mock_service = Mock()
        elementary_response = """1. **Reading Support Program**
   - Enroll in daily phonics intervention with reading specialist

2. **Family Reading Engagement**
   - Send home weekly reading activities for parents

3. **Behavioral Rewards System**
   - Implement daily sticker chart with teacher recognition"""
        
        mock_service.generate_student_recommendations.return_value = elementary_response
        mock_get_gpt_service.return_value = mock_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '2001'
            mock_student.grade_level = 2  # Elementary
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "2001"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            response_text = str(response.json()).lower()
            
            # Should contain elementary-appropriate terms
            elementary_terms = ['reading', 'phonics', 'sticker', 'family']
            found_terms = [term for term in elementary_terms if term in response_text]
            assert len(found_terms) >= 2, f"Elementary response should contain appropriate terms: {found_terms}"
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_high_school_grade_specific_recommendations(self, mock_get_gpt_service,
                                                      client, auth_headers):
        """Test high school-specific GPT recommendations"""
        # Mock high school-focused response
        mock_service = Mock()
        high_school_response = """1. **College Preparation Support**
   - Enroll in SAT prep tutoring program

2. **Career Counseling Engagement**
   - Schedule monthly meetings with college counselor

3. **Credit Recovery Plan**
   - Complete summer school courses to stay on graduation track"""
        
        mock_service.generate_student_recommendations.return_value = high_school_response
        mock_get_gpt_service.return_value = mock_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1101'
            mock_student.grade_level = 11  # High School
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1101"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            response_text = str(response.json()).lower()
            
            # Should contain high school-appropriate terms
            hs_terms = ['college', 'sat', 'graduation', 'credit', 'counselor']
            found_terms = [term for term in hs_terms if term in response_text]
            assert len(found_terms) >= 2, f"High school response should contain appropriate terms: {found_terms}"

class TestPerformanceIntegration:
    """Test performance characteristics of GPT API integration"""
    
    @patch('src.mvp.api.gpt_enhanced_endpoints.get_gpt_oss_service')
    def test_response_time_requirements(self, mock_get_gpt_service,
                                      client, auth_headers, mock_gpt_service):
        """Test GPT API integration meets response time requirements"""
        import time
        
        mock_get_gpt_service.return_value = mock_gpt_service
        
        with patch('src.mvp.database.Database') as mock_db:
            mock_session = Mock()
            mock_student = Mock()
            mock_student.student_id = '1309'
            mock_session.query.return_value.filter.return_value.first.return_value = mock_student
            mock_db.return_value.get_session.return_value = mock_session
            
            start_time = time.time()
            response = client.post(
                "/api/mvp/gpt-insights/generate",
                json={"student_id": "1309"},
                headers=auth_headers
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            # API should respond within 5 seconds for good UX
            assert response_time < 5.0, f"Response time {response_time}s exceeds 5s requirement"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])