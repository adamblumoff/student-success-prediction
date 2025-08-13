"""
Comprehensive Audit Logging System
Provides detailed audit trails for all database operations and user actions
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps
from contextlib import contextmanager
import asyncio
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

logger = logging.getLogger(__name__)

class AuditEvent:
    """Represents a single audit event"""
    
    def __init__(
        self,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_id: str = None,
        institution_id: int = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None,
        details: Dict[str, Any] = None,
        compliance_data: Dict[str, Any] = None
    ):
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.user_id = user_id
        self.institution_id = institution_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.session_id = session_id
        self.details = details or {}
        self.compliance_data = compliance_data or {}
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for database storage"""
        return {
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'institution_id': self.institution_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'details': json.dumps(self.details) if self.details else None,
            'compliance_data': json.dumps(self.compliance_data) if self.compliance_data else None,
            'created_at': self.timestamp
        }

class AuditLogger:
    """Comprehensive audit logging system for K-12 student data compliance"""
    
    def __init__(self):
        self.enabled = True
        self.log_sensitive_data = False  # FERPA compliance - don't log PII
        self.batch_size = 100
        self.pending_events: List[AuditEvent] = []
        
    def log_event(
        self,
        session: Session,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_context: Dict[str, Any] = None,
        request_context: Dict[str, Any] = None,
        details: Dict[str, Any] = None,
        compliance_data: Dict[str, Any] = None
    ) -> bool:
        """Log a single audit event to the database"""
        if not self.enabled:
            return True
            
        try:
            # Extract context information
            user_id = user_context.get('user_id') if user_context else None
            institution_id = user_context.get('institution_id') if user_context else None
            
            ip_address = request_context.get('ip_address') if request_context else None
            user_agent = request_context.get('user_agent') if request_context else None
            session_id = request_context.get('session_id') if request_context else None
            
            # Create audit event
            event = AuditEvent(
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                user_id=user_id,
                institution_id=institution_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                details=self._sanitize_details(details or {}),
                compliance_data=compliance_data or {}
            )
            
            # Insert into audit_logs table with database-specific column names
            event_data = event.to_dict()
            bind = session.get_bind()
            
            if 'postgresql' in str(bind.url):
                # PostgreSQL uses created_at column
                session.execute(text("""
                    INSERT INTO audit_logs (
                        institution_id, user_id, user_email, user_role, action,
                        resource_type, resource_id, ip_address, user_agent, session_id,
                        details, compliance_data, created_at
                    ) VALUES (
                        :institution_id, :user_id, :user_email, :user_role, :action,
                        :resource_type, :resource_id, :ip_address, :user_agent, :session_id,
                        :details, :compliance_data, :created_at
                    )
                """), {
                    'institution_id': event_data['institution_id'],
                    'user_id': event_data['user_id'],
                    'user_email': user_context.get('email') if user_context else None,
                    'user_role': user_context.get('role') if user_context else None,
                    'action': event_data['action'],
                    'resource_type': event_data['resource_type'],
                    'resource_id': event_data['resource_id'],
                    'ip_address': event_data['ip_address'],
                    'user_agent': event_data['user_agent'],
                    'session_id': event_data['session_id'],
                    'details': event_data['details'],
                    'compliance_data': event_data['compliance_data'],
                    'created_at': event_data['created_at']
                })
            else:
                # SQLite uses timestamp column and doesn't have details/compliance_data columns
                session.execute(text("""
                    INSERT INTO audit_logs (
                        institution_id, user_id, user_email, user_role, action,
                        resource_type, resource_id, ip_address, user_agent, session_id,
                        timestamp
                    ) VALUES (
                        :institution_id, :user_id, :user_email, :user_role, :action,
                        :resource_type, :resource_id, :ip_address, :user_agent, :session_id,
                        :timestamp
                    )
                """), {
                    'institution_id': event_data['institution_id'],
                    'user_id': event_data['user_id'],
                    'user_email': user_context.get('email') if user_context else None,
                    'user_role': user_context.get('role') if user_context else None,
                    'action': event_data['action'],
                    'resource_type': event_data['resource_type'],
                    'resource_id': event_data['resource_id'],
                    'ip_address': event_data['ip_address'],
                    'user_agent': event_data['user_agent'],
                    'session_id': event_data['session_id'],
                    'timestamp': event_data['created_at']
                })
            
            session.commit()
            
            logger.info(f"📝 Audit logged: {action} on {resource_type} by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {e}")
            session.rollback()
            return False
    
    async def log_event_async(
        self,
        session: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_context: Dict[str, Any] = None,
        request_context: Dict[str, Any] = None,
        details: Dict[str, Any] = None,
        compliance_data: Dict[str, Any] = None
    ) -> bool:
        """Log a single audit event to the database (async version)"""
        if not self.enabled:
            return True
            
        try:
            # Extract context information
            user_id = user_context.get('user_id') if user_context else None
            institution_id = user_context.get('institution_id') if user_context else None
            
            ip_address = request_context.get('ip_address') if request_context else None
            user_agent = request_context.get('user_agent') if request_context else None
            session_id = request_context.get('session_id') if request_context else None
            
            # Create audit event
            event = AuditEvent(
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                user_id=user_id,
                institution_id=institution_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                details=self._sanitize_details(details or {}),
                compliance_data=compliance_data or {}
            )
            
            # Insert into audit_logs table
            event_data = event.to_dict()
            await session.execute(text("""
                INSERT INTO audit_logs (
                    institution_id, user_id, user_email, user_role, action,
                    resource_type, resource_id, ip_address, user_agent, session_id,
                    details, compliance_data, created_at
                ) VALUES (
                    :institution_id, :user_id, :user_email, :user_role, :action,
                    :resource_type, :resource_id, :ip_address, :user_agent, :session_id,
                    :details, :compliance_data, :created_at
                )
            """), {
                'institution_id': event_data['institution_id'],
                'user_id': event_data['user_id'],
                'user_email': user_context.get('email') if user_context else None,
                'user_role': user_context.get('role') if user_context else None,
                'action': event_data['action'],
                'resource_type': event_data['resource_type'],
                'resource_id': event_data['resource_id'],
                'ip_address': event_data['ip_address'],
                'user_agent': event_data['user_agent'],
                'session_id': event_data['session_id'],
                'details': event_data['details'],
                'compliance_data': event_data['compliance_data'],
                'created_at': event_data['created_at']
            })
            
            await session.commit()
            
            logger.info(f"📝 Audit logged: {action} on {resource_type} by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log audit event: {e}")
            await session.rollback()
            return False
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from audit details for FERPA compliance"""
        if not self.log_sensitive_data:
            # Remove or mask PII fields
            sensitive_fields = [
                'password', 'social_security_number', 'ssn', 'student_name',
                'parent_email', 'home_address', 'phone_number', 'birth_date'
            ]
            
            sanitized = {}
            for key, value in details.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = "[REDACTED_PII]"
                elif isinstance(value, str) and len(value) > 100:
                    # Truncate very long strings
                    sanitized[key] = value[:100] + "..."
                else:
                    sanitized[key] = value
            
            return sanitized
        
        return details
    
    def log_api_access(
        self,
        session: Session,
        request: Request,
        user_context: Dict[str, Any],
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float = None
    ):
        """Log API access for compliance tracking"""
        try:
            compliance_data = {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'response_time_ms': response_time_ms,
                'ferpa_compliance': True,
                'audit_category': 'api_access'
            }
            
            request_context = {
                'ip_address': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
                'session_id': user_context.get('session_id')
            }
            
            self.log_event(
                session=session,
                action=f"{method}_ACCESS",
                resource_type='api_endpoint',
                resource_id=endpoint,
                user_context=user_context,
                request_context=request_context,
                details={'status_code': status_code},
                compliance_data=compliance_data
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to log API access: {e}")
    
    def log_data_access(
        self,
        session: Session,
        user_context: Dict[str, Any],
        action: str,
        table_name: str,
        record_ids: List[str] = None,
        record_count: int = None
    ):
        """Log data access events for student data compliance"""
        try:
            compliance_data = {
                'data_category': 'student_data' if 'student' in table_name else 'system_data',
                'ferpa_protected': 'student' in table_name,
                'audit_category': 'data_access',
                'record_count': record_count
            }
            
            details = {
                'table': table_name,
                'record_count': record_count
            }
            
            if record_ids and len(record_ids) <= 10:
                # Only log IDs for small result sets to avoid logging sensitive data
                details['record_ids'] = record_ids
            
            self.log_event(
                session=session,
                action=action,
                resource_type=table_name,
                resource_id=record_ids[0] if record_ids and len(record_ids) == 1 else None,
                user_context=user_context,
                details=details,
                compliance_data=compliance_data
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to log data access: {e}")
    
    def log_student_data_access(
        self,
        session: Session,
        user_context: Dict[str, Any],
        action: str,
        student_ids: List[str],
        purpose: str = "educational_analysis"
    ):
        """Specialized logging for FERPA-protected student data access"""
        try:
            compliance_data = {
                'ferpa_protected': True,
                'educational_purpose': purpose,
                'legitimate_interest': True,
                'audit_category': 'student_data_access',
                'student_count': len(student_ids)
            }
            
            details = {
                'purpose': purpose,
                'student_count': len(student_ids),
                'access_justification': 'Educational improvement and early intervention'
            }
            
            # Only log student IDs in non-production environments
            if logger.level <= logging.DEBUG and len(student_ids) <= 5:
                details['sample_student_ids'] = student_ids[:5]
            
            self.log_event(
                session=session,
                action=action,
                resource_type='student_data',
                user_context=user_context,
                details=details,
                compliance_data=compliance_data
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to log student data access: {e}")
    
    @contextmanager
    def audit_context(self, session: Session, user_context: Dict[str, Any], operation: str):
        """Context manager for comprehensive operation auditing"""
        start_time = datetime.utcnow()
        operation_id = f"{operation}_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Log operation start
            self.log_event(
                session=session,
                action=f"{operation}_START",
                resource_type='operation',
                resource_id=operation_id,
                user_context=user_context,
                compliance_data={'audit_category': 'operation_tracking'}
            )
            
            yield operation_id
            
            # Log operation success
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.log_event(
                session=session,
                action=f"{operation}_SUCCESS",
                resource_type='operation',
                resource_id=operation_id,
                user_context=user_context,
                details={'duration_ms': duration_ms},
                compliance_data={'audit_category': 'operation_tracking'}
            )
            
        except Exception as e:
            # Log operation failure
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            error_details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'duration_ms': duration_ms
            }
            
            if logger.level <= logging.DEBUG:
                error_details['traceback'] = traceback.format_exc()
            
            self.log_event(
                session=session,
                action=f"{operation}_FAILURE",
                resource_type='operation',
                resource_id=operation_id,
                user_context=user_context,
                details=error_details,
                compliance_data={'audit_category': 'operation_tracking'}
            )
            
            raise
    
    def get_audit_summary(self, session: Session, institution_id: int, days: int = 30) -> Dict[str, Any]:
        """Get audit summary for compliance reporting"""
        try:
            # Detect database type and use appropriate SQL syntax
            bind = session.get_bind()
            if 'postgresql' in str(bind.url):
                # PostgreSQL syntax with created_at column
                sql = text("""
                    SELECT 
                        action,
                        resource_type,
                        COUNT(*) as event_count,
                        COUNT(DISTINCT user_id) as unique_users,
                        MIN(created_at) as first_event,
                        MAX(created_at) as last_event
                    FROM audit_logs 
                    WHERE institution_id = :institution_id 
                    AND created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY action, resource_type
                    ORDER BY event_count DESC
                """ % days)
            else:
                # SQLite syntax with timestamp column
                sql = text("""
                    SELECT 
                        action,
                        resource_type,
                        COUNT(*) as event_count,
                        COUNT(DISTINCT user_id) as unique_users,
                        MIN(timestamp) as first_event,
                        MAX(timestamp) as last_event
                    FROM audit_logs 
                    WHERE institution_id = :institution_id 
                    AND timestamp >= datetime('now', '-%s days')
                    GROUP BY action, resource_type
                    ORDER BY event_count DESC
                """ % days)
            
            result = session.execute(sql, {"institution_id": institution_id})
            
            events = []
            for row in result.fetchall():
                # Handle different datetime formats between PostgreSQL and SQLite
                first_event = row.first_event
                last_event = row.last_event
                
                # Convert to ISO format if it's a datetime object, otherwise use as-is
                if hasattr(first_event, 'isoformat'):
                    first_event = first_event.isoformat()
                elif first_event:
                    first_event = str(first_event)
                    
                if hasattr(last_event, 'isoformat'):
                    last_event = last_event.isoformat()
                elif last_event:
                    last_event = str(last_event)
                
                events.append({
                    'action': row.action,
                    'resource_type': row.resource_type,
                    'event_count': row.event_count,
                    'unique_users': row.unique_users,
                    'first_event': first_event,
                    'last_event': last_event
                })
            
            total_events = sum(event['event_count'] for event in events)
            
            return {
                'summary_period_days': days,
                'institution_id': institution_id,
                'total_events': total_events,
                'events_by_type': events,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate audit summary: {e}")
            return {'error': str(e)}

# Global audit logger instance
audit_logger = AuditLogger()

# Decorator for automatic audit logging
def audit_operation(action: str, resource_type: str):
    """Decorator to automatically audit function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Look for session and user_context in arguments
            session = None
            user_context = None
            
            for arg in args:
                if isinstance(arg, Session):
                    session = arg
                elif isinstance(arg, dict) and 'user_id' in arg:
                    user_context = arg
            
            for key, value in kwargs.items():
                if key == 'session' and isinstance(value, Session):
                    session = value
                elif key == 'user_context' and isinstance(value, dict):
                    user_context = value
            
            if session and user_context:
                with audit_logger.audit_context(session, user_context, f"{action}_{func.__name__}"):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Convenience functions
def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    return audit_logger