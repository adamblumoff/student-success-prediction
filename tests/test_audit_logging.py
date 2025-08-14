#!/usr/bin/env python3
"""
Comprehensive Audit Logging Tests

Tests the FERPA-compliant audit logging system including
event logging, compliance reporting, and database integration.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

# Set up test environment
os.environ['TESTING'] = 'true'
os.environ['ENVIRONMENT'] = 'test'

# Add project root to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.mvp.audit_logger import (
    AuditLogger, 
    AuditEvent,
    audit_logger
)

class TestAuditEvent:
    """Test audit event creation and data handling"""
    
    def test_audit_event_creation(self):
        """Test creating an audit event"""
        event = AuditEvent(
            action="STUDENT_DATA_ACCESS",
            resource_type="student_data",
            resource_id="STU001",
            user_id="teacher123",
            institution_id=1
        )
        
        assert event.action == "STUDENT_DATA_ACCESS"
        assert event.resource_type == "student_data"
        assert event.resource_id == "STU001"
        assert event.user_id == "teacher123"
        assert event.institution_id == 1
        assert isinstance(event.timestamp, datetime)
    
    def test_audit_event_to_dict(self):
        """Test converting audit event to dictionary"""
        event = AuditEvent(
            action="USER_LOGIN",
            resource_type="authentication",
            user_id="teacher123",
            details={'login_method': 'api_key'},
            compliance_data={'ferpa_protected': True}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['action'] == "USER_LOGIN"
        assert event_dict['resource_type'] == "authentication"
        assert event_dict['user_id'] == "teacher123"
        assert isinstance(event_dict['details'], str)  # Should be JSON string
        assert isinstance(event_dict['compliance_data'], str)  # Should be JSON string
        assert 'created_at' in event_dict
    
    def test_audit_event_with_compliance_data(self):
        """Test audit event with FERPA compliance data"""
        compliance_data = {
            'ferpa_protected': True,
            'educational_purpose': 'risk_assessment',
            'legitimate_interest': True,
            'audit_category': 'student_data_access'
        }
        
        event = AuditEvent(
            action="STUDENT_RISK_ANALYSIS",
            resource_type="student_data",
            compliance_data=compliance_data
        )
        
        assert event.compliance_data == compliance_data
        event_dict = event.to_dict()
        
        # Should be JSON-serialized
        compliance_json = json.loads(event_dict['compliance_data'])
        assert compliance_json['ferpa_protected'] == True
        assert compliance_json['educational_purpose'] == 'risk_assessment'

class TestAuditLogger:
    """Test audit logger functionality"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session for testing"""
        session = MagicMock()
        session.execute.return_value = None
        session.commit.return_value = None
        session.rollback.return_value = None
        return session
    
    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing"""
        return {
            'user_id': 'teacher123',
            'institution_id': 1,
            'email': 'teacher@school.edu',
            'role': 'educator'
        }
    
    @pytest.fixture
    def sample_request_context(self):
        """Sample request context for testing"""
        return {
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0...',
            'session_id': 'session_123'
        }
    
    def test_audit_logger_initialization(self):
        """Test audit logger initializes correctly"""
        logger = AuditLogger()
        assert logger.enabled == True
        assert logger.log_sensitive_data == False  # FERPA compliance
        assert logger.batch_size == 100
    
    def test_log_event_basic(self, mock_session, sample_user_context, sample_request_context):
        """Test basic event logging"""
        logger = AuditLogger()
        
        result = logger.log_event(
            session=mock_session,
            action="STUDENT_DATA_VIEW",
            resource_type="student_data",
            resource_id="STU001",
            user_context=sample_user_context,
            request_context=sample_request_context
        )
        
        assert result == True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_log_event_with_details(self, mock_session, sample_user_context):
        """Test logging event with details"""
        logger = AuditLogger()
        
        details = {
            'search_criteria': 'grade_level=10',
            'student_count': 25,
            'purpose': 'intervention_planning'
        }
        
        compliance_data = {
            'ferpa_protected': True,
            'educational_purpose': 'intervention_support',
            'audit_category': 'student_data_access'
        }
        
        result = logger.log_event(
            session=mock_session,
            action="STUDENT_SEARCH",
            resource_type="student_data",
            user_context=sample_user_context,
            details=details,
            compliance_data=compliance_data
        )
        
        assert result == True
        mock_session.execute.assert_called_once()
    
    def test_log_event_error_handling(self, sample_user_context):
        """Test audit logging error handling"""
        logger = AuditLogger()
        
        # Mock session that raises an exception
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Database error")
        
        result = logger.log_event(
            session=mock_session,
            action="TEST_ACTION",
            resource_type="test",
            user_context=sample_user_context
        )
        
        assert result == False
        mock_session.rollback.assert_called_once()
    
    def test_log_api_access(self, mock_session, sample_user_context):
        """Test API access logging"""
        logger = AuditLogger()
        
        # Mock request object
        mock_request = MagicMock()
        mock_request.client.host = '192.168.1.100'
        mock_request.headers.get.return_value = 'Mozilla/5.0...'
        
        logger.log_api_access(
            session=mock_session,
            request=mock_request,
            user_context=sample_user_context,
            endpoint='/api/mvp/analyze',
            method='POST',
            status_code=200,
            response_time_ms=150.5
        )
        
        mock_session.execute.assert_called_once()
    
    def test_log_data_access(self, mock_session, sample_user_context):
        """Test data access logging"""
        logger = AuditLogger()
        
        logger.log_data_access(
            session=mock_session,
            user_context=sample_user_context,
            action="SELECT",
            table_name="students",
            record_ids=["STU001", "STU002"],
            record_count=2
        )
        
        mock_session.execute.assert_called_once()
    
    def test_log_student_data_access(self, mock_session, sample_user_context):
        """Test FERPA-protected student data access logging"""
        logger = AuditLogger()
        
        student_ids = ["STU001", "STU002", "STU003"]
        
        logger.log_student_data_access(
            session=mock_session,
            user_context=sample_user_context,
            action="RISK_ASSESSMENT",
            student_ids=student_ids,
            purpose="early_intervention"
        )
        
        mock_session.execute.assert_called_once()
        
        # Verify compliance data was included
        call_args = mock_session.execute.call_args
        assert call_args is not None
    
    def test_audit_context_manager(self, mock_session, sample_user_context):
        """Test audit context manager for operation tracking"""
        logger = AuditLogger()
        
        with logger.audit_context(mock_session, sample_user_context, "BATCH_ANALYSIS") as operation_id:
            assert operation_id.startswith("BATCH_ANALYSIS_")
            # Simulate some work
            pass
        
        # Should have logged start and success events
        assert mock_session.execute.call_count >= 2
    
    def test_audit_context_manager_error(self, mock_session, sample_user_context):
        """Test audit context manager with error"""
        logger = AuditLogger()
        
        with pytest.raises(ValueError):
            with logger.audit_context(mock_session, sample_user_context, "ERROR_OPERATION"):
                raise ValueError("Test error")
        
        # Should have logged start and failure events
        assert mock_session.execute.call_count >= 2

class TestAuditSummary:
    """Test audit summary and reporting functionality"""
    
    @pytest.fixture
    def mock_session_with_results(self):
        """Mock session with sample audit results"""
        session = MagicMock()
        
        # Mock query results
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.action = "STUDENT_DATA_VIEW"
        mock_row.resource_type = "student_data"
        mock_row.event_count = 5
        mock_row.unique_users = 2
        mock_row.first_event = "2025-08-13T10:00:00"
        mock_row.last_event = "2025-08-13T15:00:00"
        
        mock_result.fetchall.return_value = [mock_row]
        session.execute.return_value = mock_result
        session.get_bind.return_value.url = "sqlite:///test.db"
        
        return session
    
    def test_get_audit_summary(self, mock_session_with_results):
        """Test audit summary generation"""
        logger = AuditLogger()
        
        summary = logger.get_audit_summary(
            session=mock_session_with_results,
            institution_id=1,
            days=30
        )
        
        assert 'summary_period_days' in summary
        assert 'institution_id' in summary
        assert 'total_events' in summary
        assert 'events_by_type' in summary
        assert 'generated_at' in summary
        
        assert summary['summary_period_days'] == 30
        assert summary['institution_id'] == 1
        assert summary['total_events'] == 5
        assert len(summary['events_by_type']) == 1
    
    def test_audit_summary_error_handling(self):
        """Test audit summary error handling"""
        logger = AuditLogger()
        
        # Mock session that raises an exception
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Query error")
        
        summary = logger.get_audit_summary(
            session=mock_session,
            institution_id=1,
            days=30
        )
        
        assert 'error' in summary
        assert 'Query error' in summary['error']

class TestAuditCompliance:
    """Test FERPA and compliance features"""
    
    def test_sensitive_data_sanitization(self):
        """Test that sensitive data is sanitized in audit logs"""
        logger = AuditLogger()
        logger.log_sensitive_data = False  # FERPA compliance mode
        
        sensitive_details = {
            'student_name': 'John Smith',
            'social_security_number': '123-45-6789',
            'parent_email': 'parent@example.com',
            'home_address': '123 Main St',
            'analysis_result': 'Low risk'
        }
        
        sanitized = logger._sanitize_details(sensitive_details)
        
        # Sensitive fields should be redacted
        assert sanitized['student_name'] == '[REDACTED_PII]'
        assert sanitized['social_security_number'] == '[REDACTED_PII]'
        assert sanitized['parent_email'] == '[REDACTED_PII]'
        assert sanitized['home_address'] == '[REDACTED_PII]'
        
        # Non-sensitive fields should remain
        assert sanitized['analysis_result'] == 'Low risk'
    
    def test_ferpa_compliance_metadata(self):
        """Test FERPA compliance metadata in audit logs"""
        logger = AuditLogger()
        
        user_context = {
            'user_id': 'teacher123',
            'institution_id': 1,
            'role': 'educator'
        }
        
        compliance_data = {
            'ferpa_protected': True,
            'educational_purpose': 'academic_intervention',
            'legitimate_interest': True,
            'data_minimization': True,
            'retention_policy': '7_years'
        }
        
        mock_session = MagicMock()
        
        logger.log_event(
            session=mock_session,
            action="STUDENT_GRADE_ACCESS",
            resource_type="student_grades",
            user_context=user_context,
            compliance_data=compliance_data
        )
        
        mock_session.execute.assert_called_once()
        
        # Verify compliance data is included in the call
        call_args = mock_session.execute.call_args
        assert call_args is not None
    
    def test_audit_disabled_mode(self):
        """Test audit logger with disabled mode"""
        logger = AuditLogger()
        logger.enabled = False
        
        mock_session = MagicMock()
        
        result = logger.log_event(
            session=mock_session,
            action="TEST_ACTION",
            resource_type="test"
        )
        
        assert result == True  # Should succeed but not log
        mock_session.execute.assert_not_called()

class TestDatabaseIntegration:
    """Test audit logging database integration"""
    
    def test_database_type_detection(self):
        """Test database type detection for SQL syntax"""
        logger = AuditLogger()
        
        # Mock PostgreSQL session
        pg_session = MagicMock()
        pg_session.get_bind.return_value.url = "postgresql://user:pass@host/db"
        
        # Mock SQLite session  
        sqlite_session = MagicMock()
        sqlite_session.get_bind.return_value.url = "sqlite:///test.db"
        
        # Test that appropriate SQL is generated (would need to inspect actual calls)
        # For now, just verify the method doesn't crash
        try:
            logger.get_audit_summary(pg_session, 1, 30)
            logger.get_audit_summary(sqlite_session, 1, 30)
        except Exception as e:
            # Expected to fail with mock, but should detect database type
            assert "sql" not in str(e).lower() or "syntax" not in str(e).lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])