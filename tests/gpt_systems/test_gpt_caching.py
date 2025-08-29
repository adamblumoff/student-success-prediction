#!/usr/bin/env python3
"""
GPT Caching System Test Suite

Comprehensive testing of the GPT caching infrastructure for cost optimization
and performance in K-12 educational environments.
"""

import pytest
import json
import hashlib
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sqlite3

# Set test environment
os.environ['TESTING'] = 'true'

try:
    from src.mvp.services.gpt_cache_service import GPTCacheService
    from src.mvp.database import get_db_session, Database
    from src.mvp.models import GPTInsight
except ImportError:
    # For testing without full imports
    pass

@pytest.fixture
def cache_service():
    """GPT cache service for testing"""
    return GPTCacheService()

@pytest.fixture
def sample_student_data():
    """Sample student data for cache key generation"""
    return {
        'student_id': '1309',
        'gpa': 2.1,
        'attendance_rate': 0.73,
        'behavioral_incidents': 2,
        'risk_category': 'High Risk',
        'grade_level': 9
    }

@pytest.fixture
def sample_gpt_response():
    """Sample GPT response for caching"""
    return {
        'recommendations': [
            {
                'title': 'Academic Support Focus',
                'implementation': 'Schedule weekly math tutoring sessions'
            },
            {
                'title': 'Family Engagement Strategy', 
                'implementation': 'Send bi-weekly progress updates to parents'
            },
            {
                'title': 'Behavioral Monitoring Plan',
                'implementation': 'Implement daily check-in system'
            }
        ],
        'format': 'emma-johnson',
        'tokens_used': 145,
        'model_version': 'gpt-5-nano',
        'generated_at': datetime.now().isoformat()
    }

class TestCacheKeyGeneration:
    """Test cache key generation for student data"""
    
    def test_consistent_cache_key_generation(self, cache_service, sample_student_data):
        """Test cache keys are consistent for identical data"""
        key1 = cache_service.generate_cache_key(sample_student_data)
        key2 = cache_service.generate_cache_key(sample_student_data)
        
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 64  # SHA-256 hex digest
    
    def test_different_keys_for_different_data(self, cache_service, sample_student_data):
        """Test different student data generates different cache keys"""
        modified_data = sample_student_data.copy()
        modified_data['gpa'] = 3.5  # Change GPA
        
        key1 = cache_service.generate_cache_key(sample_student_data)
        key2 = cache_service.generate_cache_key(modified_data)
        
        assert key1 != key2
    
    def test_cache_key_excludes_non_relevant_fields(self, cache_service):
        """Test cache key ignores fields that don't affect recommendations"""
        data1 = {
            'student_id': '1309',
            'name': 'Student A',  # Should not affect cache key
            'created_at': '2025-01-01',  # Should not affect cache key
            'gpa': 2.5,
            'attendance_rate': 0.85
        }
        
        data2 = {
            'student_id': '1309',
            'name': 'Student B',  # Different name
            'created_at': '2025-01-02',  # Different timestamp
            'gpa': 2.5,  # Same GPA
            'attendance_rate': 0.85  # Same attendance
        }
        
        key1 = cache_service.generate_cache_key(data1)
        key2 = cache_service.generate_cache_key(data2)
        
        # Keys should be the same (only academic data matters)
        assert key1 == key2
    
    def test_cache_key_sensitive_to_academic_changes(self, cache_service, sample_student_data):
        """Test cache key changes with academically significant changes"""
        base_key = cache_service.generate_cache_key(sample_student_data)
        
        # Test GPA change
        gpa_data = sample_student_data.copy()
        gpa_data['gpa'] = 3.5
        assert cache_service.generate_cache_key(gpa_data) != base_key
        
        # Test attendance change
        attendance_data = sample_student_data.copy()
        attendance_data['attendance_rate'] = 0.95
        assert cache_service.generate_cache_key(attendance_data) != base_key
        
        # Test risk category change
        risk_data = sample_student_data.copy()
        risk_data['risk_category'] = 'Low Risk'
        assert cache_service.generate_cache_key(risk_data) != base_key

class TestCacheStorage:
    """Test cache storage and retrieval operations"""
    
    @patch('src.mvp.services.gpt_cache_service.Database')
    def test_cache_storage_success(self, mock_db, cache_service, sample_student_data, sample_gpt_response):
        """Test successful cache storage"""
        mock_session = Mock()
        mock_db.return_value.get_session.return_value = mock_session
        
        cache_key = cache_service.generate_cache_key(sample_student_data)
        result = cache_service.store_response(cache_key, sample_gpt_response, sample_student_data['student_id'])
        
        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('src.mvp.services.gpt_cache_service.Database')
    def test_cache_retrieval_success(self, mock_db, cache_service, sample_student_data, sample_gpt_response):
        """Test successful cache retrieval"""
        mock_session = Mock()
        mock_insight = Mock()
        mock_insight.raw_response = json.dumps(sample_gpt_response)
        mock_insight.cache_hits = 1
        mock_insight.created_at = datetime.now()
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_insight
        mock_db.return_value.get_session.return_value = mock_session
        
        cache_key = cache_service.generate_cache_key(sample_student_data)
        result = cache_service.get_cached_response(cache_key)
        
        assert result is not None
        assert json.loads(result['raw_response']) == sample_gpt_response
        assert result['cached'] is True
    
    def test_cache_miss(self, cache_service, sample_student_data):
        """Test cache miss returns None"""
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_db.return_value.get_session.return_value = mock_session
            
            cache_key = cache_service.generate_cache_key(sample_student_data)
            result = cache_service.get_cached_response(cache_key)
            
            assert result is None

class TestCacheExpiration:
    """Test cache expiration and invalidation policies"""
    
    def test_cache_expiration_by_time(self, cache_service):
        """Test cache expires after configured time period"""
        # Set cache TTL to 1 hour for testing
        cache_service.cache_ttl_hours = 1
        
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_insight = Mock()
            mock_insight.raw_response = json.dumps({'test': 'data'})
            mock_insight.cache_hits = 1
            # Set created time to 2 hours ago (expired)
            mock_insight.created_at = datetime.now() - timedelta(hours=2)
            
            mock_session.query.return_value.filter.return_value.first.return_value = mock_insight
            mock_db.return_value.get_session.return_value = mock_session
            
            result = cache_service.get_cached_response('test-key')
            
            # Should return None for expired cache
            assert result is None
    
    def test_cache_invalidation_on_intervention_change(self, cache_service, sample_student_data):
        """Test cache invalidates when student interventions change"""
        # Original data
        base_key = cache_service.generate_cache_key(sample_student_data)
        
        # Add intervention data
        data_with_intervention = sample_student_data.copy()
        data_with_intervention['active_interventions'] = ['academic_support']
        
        intervention_key = cache_service.generate_cache_key(data_with_intervention)
        
        # Keys should be different
        assert base_key != intervention_key
    
    def test_bulk_cache_cleanup(self, cache_service):
        """Test bulk cleanup of expired cache entries"""
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_db.return_value.get_session.return_value = mock_session
            
            # Mock expired entries
            mock_session.query.return_value.filter.return_value.delete.return_value = 15
            
            deleted_count = cache_service.cleanup_expired_cache()
            
            assert deleted_count == 15
            mock_session.commit.assert_called_once()

class TestCostOptimization:
    """Test cache system's impact on API cost optimization"""
    
    def test_token_usage_tracking(self, cache_service, sample_student_data, sample_gpt_response):
        """Test token usage is tracked for cost analysis"""
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_db.return_value.get_session.return_value = mock_session
            
            cache_key = cache_service.generate_cache_key(sample_student_data)
            cache_service.store_response(cache_key, sample_gpt_response, sample_student_data['student_id'])
            
            # Check that stored insight includes token usage
            stored_insight = mock_session.add.call_args[0][0]
            stored_data = json.loads(stored_insight.raw_response)
            assert 'tokens_used' in stored_data
            assert stored_data['tokens_used'] == 145
    
    def test_cache_hit_statistics(self, cache_service, sample_student_data):
        """Test cache hit statistics for monitoring efficiency"""
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_insight = Mock()
            mock_insight.raw_response = json.dumps({'test': 'data'})
            mock_insight.cache_hits = 3
            mock_insight.created_at = datetime.now()
            
            mock_session.query.return_value.filter.return_value.first.return_value = mock_insight
            mock_db.return_value.get_session.return_value = mock_session
            
            cache_key = cache_service.generate_cache_key(sample_student_data)
            result = cache_service.get_cached_response(cache_key)
            
            # Should increment cache hit counter
            assert result['cache_hits'] == 4
    
    def test_cost_savings_calculation(self, cache_service):
        """Test calculation of cost savings from caching"""
        # Mock cache statistics
        cache_stats = {
            'total_requests': 1000,
            'cache_hits': 400,
            'average_tokens_per_request': 150,
            'cost_per_1k_tokens': 0.0001
        }
        
        savings = cache_service.calculate_cost_savings(cache_stats)
        
        # 400 cache hits * 150 tokens * $0.0001/1000 tokens = $0.006 saved
        expected_savings = 400 * 150 * 0.0001 / 1000
        assert abs(savings - expected_savings) < 0.0001

class TestCachePerformance:
    """Test cache system performance characteristics"""
    
    def test_cache_lookup_performance(self, cache_service, sample_student_data):
        """Test cache lookups complete within performance requirements"""
        import time
        
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_insight = Mock()
            mock_insight.raw_response = json.dumps({'test': 'data'})
            mock_insight.cache_hits = 1
            mock_insight.created_at = datetime.now()
            
            mock_session.query.return_value.filter.return_value.first.return_value = mock_insight
            mock_db.return_value.get_session.return_value = mock_session
            
            cache_key = cache_service.generate_cache_key(sample_student_data)
            
            start_time = time.time()
            result = cache_service.get_cached_response(cache_key)
            end_time = time.time()
            
            lookup_time = end_time - start_time
            
            # Cache lookup should be very fast (< 100ms)
            assert lookup_time < 0.1, f"Cache lookup took {lookup_time}s, should be < 0.1s"
    
    def test_cache_storage_performance(self, cache_service, sample_student_data, sample_gpt_response):
        """Test cache storage completes within performance requirements"""
        import time
        
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_db.return_value.get_session.return_value = mock_session
            
            cache_key = cache_service.generate_cache_key(sample_student_data)
            
            start_time = time.time()
            result = cache_service.store_response(cache_key, sample_gpt_response, sample_student_data['student_id'])
            end_time = time.time()
            
            storage_time = end_time - start_time
            
            # Cache storage should be fast (< 200ms)
            assert storage_time < 0.2, f"Cache storage took {storage_time}s, should be < 0.2s"

class TestDataIntegrity:
    """Test cache data integrity and consistency"""
    
    def test_cache_data_serialization(self, cache_service, sample_gpt_response):
        """Test GPT response data serializes/deserializes correctly"""
        # Serialize
        serialized = cache_service._serialize_response(sample_gpt_response)
        assert isinstance(serialized, str)
        
        # Deserialize
        deserialized = cache_service._deserialize_response(serialized)
        assert deserialized == sample_gpt_response
    
    def test_cache_data_corruption_handling(self, cache_service):
        """Test handling of corrupted cache data"""
        corrupted_data = "invalid json data"
        
        result = cache_service._deserialize_response(corrupted_data)
        assert result is None  # Should handle gracefully
    
    def test_cache_concurrent_access_safety(self, cache_service, sample_student_data, sample_gpt_response):
        """Test cache handles concurrent access safely"""
        import threading
        import time
        
        results = []
        errors = []
        
        def cache_operation(thread_id):
            try:
                cache_key = cache_service.generate_cache_key({
                    **sample_student_data,
                    'student_id': f'student_{thread_id}'
                })
                
                # Store
                with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
                    mock_session = Mock()
                    mock_db.return_value.get_session.return_value = mock_session
                    
                    result = cache_service.store_response(cache_key, sample_gpt_response, f'student_{thread_id}')
                    results.append(result)
                    
            except Exception as e:
                errors.append(e)
        
        # Run concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        assert len(errors) == 0
        assert len(results) == 5
        assert all(result is True for result in results)

class TestEducationalContextIntegration:
    """Test cache integration with educational contexts"""
    
    def test_grade_level_cache_segmentation(self, cache_service):
        """Test cache considers grade-level context"""
        elementary_data = {
            'student_id': '1001',
            'grade_level': 3,
            'gpa': 2.5,
            'reading_level': 2.8
        }
        
        high_school_data = {
            'student_id': '1002', 
            'grade_level': 11,
            'gpa': 2.5,
            'credits_earned': 15.5
        }
        
        elem_key = cache_service.generate_cache_key(elementary_data)
        hs_key = cache_service.generate_cache_key(high_school_data)
        
        # Should generate different keys for different grade levels
        assert elem_key != hs_key
    
    def test_intervention_context_cache_invalidation(self, cache_service):
        """Test cache invalidates when intervention context changes"""
        base_data = {
            'student_id': '1309',
            'gpa': 2.5,
            'risk_category': 'Medium Risk'
        }
        
        data_with_intervention = {
            **base_data,
            'active_interventions': ['academic_support', 'behavioral_monitoring']
        }
        
        base_key = cache_service.generate_cache_key(base_data)
        intervention_key = cache_service.generate_cache_key(data_with_intervention)
        
        # Should be different keys
        assert base_key != intervention_key

class TestMaintenanceOperations:
    """Test cache maintenance and administration operations"""
    
    def test_cache_size_monitoring(self, cache_service):
        """Test cache size monitoring for storage management"""
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_session.query.return_value.count.return_value = 2500
            mock_db.return_value.get_session.return_value = mock_session
            
            cache_size = cache_service.get_cache_size()
            assert cache_size == 2500
    
    def test_cache_health_check(self, cache_service):
        """Test cache system health monitoring"""
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            mock_db.return_value.get_session.return_value = mock_session
            
            health = cache_service.health_check()
            
            assert 'database_connected' in health
            assert 'cache_accessible' in health
            assert 'last_cleanup' in health
    
    def test_cache_statistics_reporting(self, cache_service):
        """Test cache statistics for performance monitoring"""
        with patch('src.mvp.services.gpt_cache_service.Database') as mock_db:
            mock_session = Mock()
            
            # Mock statistics queries
            mock_session.query.return_value.count.return_value = 1000
            mock_session.query.return_value.filter.return_value.count.return_value = 400
            
            mock_db.return_value.get_session.return_value = mock_session
            
            stats = cache_service.get_statistics()
            
            assert 'total_entries' in stats
            assert 'cache_hit_rate' in stats
            assert 'average_tokens_saved' in stats

if __name__ == "__main__":
    pytest.main([__file__, "-v"])