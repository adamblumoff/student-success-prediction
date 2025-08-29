#!/usr/bin/env python3
"""
Comprehensive GPT-5-nano Service Testing Framework

Tests all aspects of the GPT integration for the K-12 Student Success Platform:
- API call patterns and response formats
- Emma Johnson format compliance
- Cost management and caching systems
- Error handling and fallback behaviors
- Educational content appropriateness
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from typing import List
import time

# Set test environment
os.environ['TESTING'] = 'true'
os.environ['OPENAI_API_KEY'] = 'test-openai-api-key-for-testing'

from src.mvp.services.gpt_oss_service import GPTOSSService
from src.mvp.services.gpt_cache_service import GPTCacheService

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock_client = Mock()
    
    # Mock Chat Completions API response (standard OpenAI format)
    mock_chat_response = Mock()
    mock_chat_response.choices = [Mock()]
    mock_chat_response.choices[0].message.content = """1. **Academic Support Focus**
   - Schedule weekly math tutoring sessions with peer mentor

2. **Family Engagement Strategy** 
   - Send bi-weekly progress updates to parents via email

3. **Behavioral Monitoring Plan**
   - Implement daily check-in system with guidance counselor"""
    mock_chat_response.usage.total_tokens = 156
    
    # Mock Responses API response (OpenAI GPT-5-nano format)
    mock_responses_response = Mock()
    mock_responses_response.content = """1. **Academic Support Focus**
   - Schedule weekly math tutoring sessions with peer mentor

2. **Family Engagement Strategy** 
   - Send bi-weekly progress updates to parents via email

3. **Behavioral Monitoring Plan**
   - Implement daily check-in system with guidance counselor"""
    
    mock_client.chat.completions.create.return_value = mock_chat_response
    mock_client.responses.create.return_value = mock_responses_response
    
    return mock_client

@pytest.fixture
def mock_cache_service():
    """Mock GPT cache service for testing"""
    mock_cache = Mock(spec=GPTCacheService)
    mock_cache.get_cached_response.return_value = None
    mock_cache.cache_response.return_value = True
    mock_cache.clear_cache.return_value = True
    return mock_cache

@pytest.fixture
def gpt_service(mock_openai_client, mock_cache_service):
    """GPT service with mocked dependencies"""
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value = mock_openai_client
        service = GPTOSSService(api_key="test-key")
        service.cache_service = mock_cache_service
        return service

@pytest.fixture
def sample_student_data():
    """Sample K-12 student data for testing"""
    return {
        'student_id': '1309',
        'name': 'Test Student',
        'grade_level': 9,
        'gpa': 2.1,
        'attendance_rate': 0.73,
        'behavioral_incidents': 2,
        'assignment_completion': 0.67,
        'risk_score': 0.68,
        'risk_category': 'High Risk'
    }

class TestGPTServiceInitialization:
    """Test GPT service initialization and configuration"""
    
    def test_service_initialization_with_api_key(self):
        """Test service initializes correctly with API key"""
        with patch('openai.OpenAI') as mock_openai:
            service = GPTOSSService(api_key="test-key")
            assert service.model_name == "gpt-5-nano"
            assert service.timeout == 60
            assert service.enable_caching == True
    
    def test_service_initialization_without_openai(self):
        """Test service handles missing OpenAI gracefully"""
        with patch('src.mvp.services.gpt_oss_service.OPENAI_AVAILABLE', False):
            service = GPTOSSService(api_key="test-key")
            assert service.client is None
    
    def test_service_initialization_with_custom_model(self):
        """Test service accepts custom model configuration"""
        with patch('openai.OpenAI'):
            service = GPTOSSService(
                api_key="test-key", 
                model_name="gpt-4o-mini",
                timeout=120,
                enable_caching=False
            )
            assert service.model_name == "gpt-4o-mini"
            assert service.timeout == 120
            assert service.enable_caching == False

class TestEmmaJohnsonFormat:
    """Test Emma Johnson format compliance for educational recommendations"""
    
    def test_emma_johnson_format_validation(self, gpt_service, sample_student_data):
        """Test response follows Emma Johnson format: 3 recommendations, 1 bullet each"""
        response = gpt_service.generate_student_recommendations(sample_student_data)
        
        # Should be 3 numbered recommendations
        lines = response.strip().split('\n')
        recommendation_lines = [line for line in lines if line.strip().startswith(('1.', '2.', '3.'))]
        assert len(recommendation_lines) == 3, f"Expected 3 recommendations, got {len(recommendation_lines)}"
        
        # Each should have exactly 1 implementation bullet
        for i in range(1, 4):
            recommendation_section = self._extract_recommendation_section(response, i)
            bullet_lines = [line for line in recommendation_section if line.strip().startswith('-')]
            assert len(bullet_lines) == 1, f"Recommendation {i} should have exactly 1 bullet point"
    
    def test_educational_content_appropriateness(self, gpt_service, sample_student_data):
        """Test recommendations are appropriate for K-12 educational context"""
        response = gpt_service.generate_student_recommendations(sample_student_data)
        
        # Should contain educational terminology
        educational_terms = [
            'academic', 'tutoring', 'support', 'family', 'engagement', 
            'behavioral', 'monitoring', 'counselor', 'teacher', 'parents'
        ]
        
        response_lower = response.lower()
        found_terms = [term for term in educational_terms if term in response_lower]
        assert len(found_terms) >= 3, f"Response should contain educational terms, found: {found_terms}"
        
        # Should not contain inappropriate content
        inappropriate_terms = ['medication', 'therapy', 'diagnosis', 'psychiatric']
        for term in inappropriate_terms:
            assert term not in response_lower, f"Response should not contain medical term: {term}"
    
    def test_grade_level_appropriate_language(self, gpt_service):
        """Test recommendations adjust language for different grade levels"""
        elementary_student = {
            'student_id': '1001', 'grade_level': 3, 'gpa': 2.5, 
            'attendance_rate': 0.85, 'risk_category': 'Medium Risk'
        }
        
        high_school_student = {
            'student_id': '1002', 'grade_level': 11, 'gpa': 2.5,
            'attendance_rate': 0.85, 'risk_category': 'Medium Risk'
        }
        
        elementary_response = gpt_service.generate_student_recommendations(elementary_student)
        high_school_response = gpt_service.generate_student_recommendations(high_school_student)
        
        # Elementary should focus on foundational skills
        assert any(term in elementary_response.lower() for term in ['reading', 'basic', 'foundational', 'family'])
        
        # High school should focus on college/career prep
        assert any(term in high_school_response.lower() for term in ['college', 'career', 'graduation', 'credits'])
    
    def _extract_recommendation_section(self, response: str, recommendation_num: int) -> List[str]:
        """Helper to extract a specific recommendation section"""
        lines = response.split('\n')
        start_line = f"{recommendation_num}."
        next_start_line = f"{recommendation_num + 1}."
        
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.strip().startswith(start_line):
                in_section = True
                section_lines.append(line)
            elif in_section and line.strip().startswith(next_start_line):
                break
            elif in_section:
                section_lines.append(line)
        
        return section_lines

class TestCostManagement:
    """Test GPT API cost management and optimization"""
    
    def test_caching_reduces_api_calls(self, gpt_service, mock_cache_service, sample_student_data):
        """Test that caching prevents duplicate API calls"""
        # First call - should hit API
        mock_cache_service.get_cached_response.return_value = None
        response1 = gpt_service.generate_student_recommendations(sample_student_data)
        
        # Verify API was called
        assert gpt_service.client.responses.create.called
        
        # Reset mock
        gpt_service.client.responses.create.reset_mock()
        
        # Second call - should use cache
        cached_response = {
            'response': response1,
            'tokens_used': 0,
            'cached': True,
            'cache_timestamp': datetime.now().isoformat()
        }
        mock_cache_service.get_cached_response.return_value = cached_response
        
        response2 = gpt_service.generate_student_recommendations(sample_student_data)
        
        # Verify API was NOT called again
        assert not gpt_service.client.responses.create.called
        assert response2 == response1
    
    def test_cache_invalidation_on_data_change(self, gpt_service, mock_cache_service, sample_student_data):
        """Test cache invalidates when student data changes"""
        # Generate cache key for original data
        original_key = gpt_service._generate_cache_key(sample_student_data)
        
        # Modify student data
        modified_data = sample_student_data.copy()
        modified_data['gpa'] = 3.2  # Significant change
        modified_key = gpt_service._generate_cache_key(modified_data)
        
        # Keys should be different
        assert original_key != modified_key
    
    def test_token_usage_tracking(self, gpt_service, sample_student_data):
        """Test token usage is properly tracked and reported"""
        response_data = gpt_service.generate_student_recommendations(sample_student_data)
        
        # Should track token usage (mocked to return 156 tokens)
        assert hasattr(gpt_service, 'last_token_usage')
        assert gpt_service.last_token_usage == 156
    
    def test_cost_estimation(self, gpt_service):
        """Test GPT API cost estimation for budgeting"""
        # GPT-5-nano pricing (example rates)
        cost_per_1k_tokens = 0.0001  # $0.0001 per 1K tokens
        
        estimated_cost = gpt_service.estimate_cost(tokens=1000)
        expected_cost = cost_per_1k_tokens
        
        assert abs(estimated_cost - expected_cost) < 0.0001
    
    def test_batch_processing_optimization(self, gpt_service):
        """Test batch processing for cost efficiency"""
        students = [
            {'student_id': f'100{i}', 'gpa': 2.5 + (i * 0.1), 'risk_category': 'Medium Risk'}
            for i in range(5)
        ]
        
        # Should process efficiently without hitting rate limits
        responses = gpt_service.generate_batch_recommendations(students)
        assert len(responses) == 5

class TestErrorHandling:
    """Test error handling and fallback mechanisms"""
    
    def test_openai_api_error_handling(self, gpt_service, sample_student_data):
        """Test handling of OpenAI API errors"""
        # Mock API error
        gpt_service.client.responses.create.side_effect = Exception("API Error")
        
        # Should return fallback response, not crash
        response = gpt_service.generate_student_recommendations(sample_student_data)
        assert response is not None
        assert "unable to generate" in response.lower() or "error" in response.lower()
    
    def test_rate_limit_handling(self, gpt_service, sample_student_data):
        """Test handling of rate limit errors"""
        from openai import RateLimitError
        
        # Mock rate limit error
        gpt_service.client.responses.create.side_effect = RateLimitError("Rate limited")
        
        # Should implement exponential backoff or return cached response
        response = gpt_service.generate_student_recommendations(sample_student_data)
        assert response is not None
    
    def test_invalid_api_key_handling(self, sample_student_data):
        """Test handling of invalid API key"""
        with patch('openai.OpenAI') as mock_openai:
            from openai import AuthenticationError
            mock_client = Mock()
            mock_client.responses.create.side_effect = AuthenticationError("Invalid API key")
            mock_openai.return_value = mock_client
            
            service = GPTOSSService(api_key="invalid-key")
            response = service.generate_student_recommendations(sample_student_data)
            
            # Should handle gracefully
            assert response is not None
    
    def test_network_timeout_handling(self, gpt_service, sample_student_data):
        """Test handling of network timeouts"""
        import requests
        
        # Mock timeout error
        gpt_service.client.responses.create.side_effect = requests.Timeout("Request timed out")
        
        response = gpt_service.generate_student_recommendations(sample_student_data)
        assert response is not None

class TestDataPrivacy:
    """Test data privacy and FERPA compliance"""
    
    def test_no_pii_in_logs(self, gpt_service, sample_student_data):
        """Test that no PII is logged during GPT processing"""
        with patch('src.mvp.services.gpt_oss_service.logger') as mock_logger:
            gpt_service.generate_student_recommendations(sample_student_data)
            
            # Check all log calls for PII
            for call in mock_logger.info.call_args_list + mock_logger.error.call_args_list:
                log_message = str(call)
                assert 'Test Student' not in log_message  # Student name
                assert sample_student_data['student_id'] not in log_message  # Student ID
    
    def test_data_minimization(self, gpt_service):
        """Test only necessary data is sent to GPT API"""
        student_with_pii = {
            'student_id': '1309',
            'name': 'John Doe',
            'ssn': '123-45-6789',  # Should not be sent
            'address': '123 Main St',  # Should not be sent
            'gpa': 2.5,  # Should be sent
            'attendance_rate': 0.85,  # Should be sent
            'risk_category': 'Medium Risk'  # Should be sent
        }
        
        # Mock the OpenAI call to capture what data is actually sent
        with patch.object(gpt_service.client.responses, 'create') as mock_create:
            gpt_service.generate_student_recommendations(student_with_pii)
            
            # Check the prompt sent to GPT
            call_args = mock_create.call_args
            prompt_data = str(call_args)
            
            # Should not contain PII
            assert '123-45-6789' not in prompt_data
            assert '123 Main St' not in prompt_data
            
            # Should contain relevant academic data
            assert '2.5' in prompt_data  # GPA
            assert '0.85' in prompt_data or '85%' in prompt_data  # Attendance

class TestPerformance:
    """Test performance characteristics of GPT integration"""
    
    def test_response_time_requirements(self, gpt_service, sample_student_data):
        """Test response time meets educational software requirements"""
        start_time = time.time()
        response = gpt_service.generate_student_recommendations(sample_student_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within 10 seconds for real-time use
        assert response_time < 10.0, f"Response time {response_time}s exceeds 10s requirement"
    
    def test_concurrent_request_handling(self, gpt_service):
        """Test handling of concurrent requests"""
        students = [
            {'student_id': f'100{i}', 'gpa': 2.0 + i * 0.2, 'risk_category': 'Medium Risk'}
            for i in range(3)
        ]
        
        # Should handle concurrent requests without errors
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(gpt_service.generate_student_recommendations, student)
                for student in students
            ]
            
            responses = [future.result() for future in futures]
            assert len(responses) == 3
            assert all(response is not None for response in responses)

class TestIntegrationWithEducationalSystems:
    """Test integration with educational data systems"""
    
    def test_canvas_lms_data_integration(self, gpt_service):
        """Test processing of Canvas LMS gradebook data"""
        canvas_data = {
            'student_id': 'canvas_12345',
            'name': 'Canvas Student',
            'current_score': 67.5,
            'submissions': 12,
            'late_submissions': 3,
            'missing_assignments': 2
        }
        
        response = gpt_service.generate_student_recommendations(canvas_data)
        
        # Should handle Canvas-specific data fields
        assert 'assignment' in response.lower() or 'submission' in response.lower()
    
    def test_powerschool_sis_data_integration(self, gpt_service):
        """Test processing of PowerSchool SIS data"""
        powerschool_data = {
            'student_id': 'ps_67890',
            'grade_level': 10,
            'gpa': 2.3,
            'credits_earned': 18.5,
            'attendance_rate': 0.78,
            'discipline_incidents': 1
        }
        
        response = gpt_service.generate_student_recommendations(powerschool_data)
        
        # Should handle SIS-specific data fields
        assert 'credit' in response.lower() or 'attendance' in response.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])