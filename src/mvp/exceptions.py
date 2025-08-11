#!/usr/bin/env python3
"""
Production-Ready Exception Handling System

Comprehensive exception hierarchy and error handling patterns for the
Student Success Prediction system. Provides structured error handling
with proper logging, monitoring, and user-friendly error messages.
"""

import logging
import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """Error severity levels for classification and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization and handling."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    ML_MODEL = "ml_model"
    EXTERNAL_API = "external_api"
    FILE_PROCESSING = "file_processing"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    BUSINESS_LOGIC = "business_logic"


@dataclass
class ErrorContext:
    """Enhanced error context for debugging and monitoring."""
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    student_count: Optional[int] = None
    file_name: Optional[str] = None
    model_type: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        return {
            k: v for k, v in self.__dict__.items() 
            if v is not None
        }


class BaseApplicationError(Exception):
    """Base exception class for all application errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        user_message: Optional[str] = None,
        http_status_code: int = 500,
        should_log: bool = True,
        should_alert: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.user_message = user_message or self._generate_user_friendly_message()
        self.http_status_code = http_status_code
        self.should_log = should_log
        self.should_alert = should_alert
        self.timestamp = datetime.utcnow()
        self.traceback_info = traceback.format_exc() if should_log else None
        
        if should_log:
            self._log_error()
    
    def _generate_user_friendly_message(self) -> str:
        """Generate user-friendly error message based on category."""
        category_messages = {
            ErrorCategory.AUTHENTICATION: "Authentication is required to access this resource.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.VALIDATION: "The provided data is invalid. Please check your input.",
            ErrorCategory.DATABASE: "A database error occurred. Please try again later.",
            ErrorCategory.ML_MODEL: "The prediction service is temporarily unavailable.",
            ErrorCategory.EXTERNAL_API: "An external service is temporarily unavailable.",
            ErrorCategory.FILE_PROCESSING: "There was an error processing your file. Please check the format.",
            ErrorCategory.CONFIGURATION: "A system configuration error occurred.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again later.",
            ErrorCategory.BUSINESS_LOGIC: "Unable to complete the requested operation."
        }
        return category_messages.get(self.category, "An unexpected error occurred.")
    
    def _log_error(self) -> None:
        """Log error with structured information."""
        logger = logging.getLogger(self.__class__.__module__)
        
        log_data = {
            'error_class': self.__class__.__name__,
            'category': self.category.value,
            'severity': self.severity.value,
            'http_status': self.http_status_code,
            'timestamp': self.timestamp.isoformat(),
            **self.context.to_dict()
        }
        
        log_message = f"{self.category.value.upper()}: {self.message}"
        
        if self.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(log_message, extra=log_data, exc_info=True)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=log_data)
        else:
            logger.info(log_message, extra=log_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            'error': {
                'type': self.__class__.__name__,
                'message': self.user_message,
                'category': self.category.value,
                'severity': self.severity.value,
                'timestamp': self.timestamp.isoformat(),
                'request_id': self.context.request_id
            }
        }


# Authentication and Authorization Errors
class AuthenticationError(BaseApplicationError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            http_status_code=401,
            should_alert=False
        )


class AuthorizationError(BaseApplicationError):
    """Authorization-related errors."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            http_status_code=403,
            should_alert=False
        )


# Validation Errors
class ValidationError(BaseApplicationError):
    """Data validation errors."""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, List[str]]] = None, context: Optional[ErrorContext] = None):
        self.field_errors = field_errors or {}
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            context=context,
            http_status_code=400,
            should_alert=False
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.field_errors:
            result['error']['field_errors'] = self.field_errors
        return result


class FileValidationError(ValidationError):
    """File-specific validation errors."""
    
    def __init__(self, message: str, filename: Optional[str] = None, context: Optional[ErrorContext] = None):
        if context is None:
            context = ErrorContext()
        context.file_name = filename
        
        super().__init__(
            message=message,
            context=context
        )
        self.category = ErrorCategory.FILE_PROCESSING


# Database Errors
class DatabaseError(BaseApplicationError):
    """Database-related errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, context: Optional[ErrorContext] = None):
        self.operation = operation
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            context=context,
            http_status_code=503,
            should_alert=True
        )


class DatabaseConnectionError(DatabaseError):
    """Database connection-specific errors."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            operation="connection",
            context=context
        )
        self.severity = ErrorSeverity.CRITICAL
        self.user_message = "Database service is temporarily unavailable. Please try again later."


# Machine Learning Errors
class MLModelError(BaseApplicationError):
    """Machine learning model-related errors."""
    
    def __init__(self, message: str, model_type: Optional[str] = None, context: Optional[ErrorContext] = None):
        if context is None:
            context = ErrorContext()
        context.model_type = model_type
        
        super().__init__(
            message=message,
            category=ErrorCategory.ML_MODEL,
            severity=ErrorSeverity.HIGH,
            context=context,
            http_status_code=503,
            should_alert=True
        )


class ModelNotFoundError(MLModelError):
    """Model file not found errors."""
    
    def __init__(self, model_path: str, model_type: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(
            message=f"ML model not found: {model_path}",
            model_type=model_type,
            context=context
        )
        self.model_path = model_path
        self.user_message = "The prediction service is temporarily unavailable due to missing model files."


class ModelPredictionError(MLModelError):
    """Model prediction-specific errors."""
    
    def __init__(self, message: str, student_count: Optional[int] = None, model_type: Optional[str] = None, context: Optional[ErrorContext] = None):
        if context is None:
            context = ErrorContext()
        context.student_count = student_count
        
        super().__init__(
            message=message,
            model_type=model_type,
            context=context
        )
        self.user_message = "Unable to generate predictions. Please check your data format and try again."


# External API Errors
class ExternalAPIError(BaseApplicationError):
    """External API integration errors."""
    
    def __init__(self, message: str, service_name: str, status_code: Optional[int] = None, context: Optional[ErrorContext] = None):
        self.service_name = service_name
        self.api_status_code = status_code
        
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            http_status_code=502,
            should_alert=True
        )
        self.user_message = f"{service_name} service is temporarily unavailable. Please try again later."


class RateLimitError(BaseApplicationError):
    """Rate limiting errors."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, context: Optional[ErrorContext] = None):
        self.retry_after = retry_after
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.LOW,
            context=context,
            http_status_code=429,
            should_alert=False
        )
        self.user_message = f"Rate limit exceeded. Please try again in {retry_after or 'a few'} seconds."


# Configuration Errors
class ConfigurationError(BaseApplicationError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, context: Optional[ErrorContext] = None):
        self.config_key = config_key
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            context=context,
            http_status_code=500,
            should_alert=True
        )
        self.user_message = "System configuration error. Please contact support."


# System Errors
class SystemError(BaseApplicationError):
    """System-level errors."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            context=context,
            http_status_code=500,
            should_alert=True
        )


# Business Logic Errors
class BusinessLogicError(BaseApplicationError):
    """Business logic validation errors."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None, user_message: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            user_message=user_message,
            http_status_code=422,
            should_alert=False
        )


class InsufficientDataError(BusinessLogicError):
    """Insufficient data for processing errors."""
    
    def __init__(self, message: str, required_count: Optional[int] = None, provided_count: Optional[int] = None, context: Optional[ErrorContext] = None):
        self.required_count = required_count
        self.provided_count = provided_count
        
        super().__init__(
            message=message,
            context=context,
            user_message=f"Insufficient data provided. Expected at least {required_count} records, got {provided_count}."
        )


# Error Handler Utilities
class ErrorHandler:
    """Centralized error handling utilities."""
    
    @staticmethod
    def handle_database_error(e: Exception, operation: str, context: Optional[ErrorContext] = None) -> DatabaseError:
        """Convert database exceptions to structured errors."""
        error_message = str(e)
        
        if "connection" in error_message.lower():
            return DatabaseConnectionError(f"Database connection failed during {operation}: {error_message}", context)
        elif "timeout" in error_message.lower():
            return DatabaseError(f"Database timeout during {operation}: {error_message}", operation, context)
        else:
            return DatabaseError(f"Database error during {operation}: {error_message}", operation, context)
    
    @staticmethod
    def handle_ml_error(e: Exception, model_type: Optional[str] = None, context: Optional[ErrorContext] = None) -> MLModelError:
        """Convert ML exceptions to structured errors."""
        error_message = str(e)
        
        if "not found" in error_message.lower() or "no such file" in error_message.lower():
            return ModelNotFoundError(error_message, model_type, context)
        elif "prediction" in error_message.lower() or "transform" in error_message.lower():
            return ModelPredictionError(error_message, context=context, model_type=model_type)
        else:
            return MLModelError(error_message, model_type, context)
    
    @staticmethod
    def handle_validation_error(e: Exception, context: Optional[ErrorContext] = None) -> ValidationError:
        """Convert validation exceptions to structured errors."""
        return ValidationError(str(e), context=context)
    
    @staticmethod
    def handle_unexpected_error(e: Exception, context: Optional[ErrorContext] = None) -> SystemError:
        """Handle unexpected system errors."""
        return SystemError(f"Unexpected error: {str(e)}", context)


# Decorator for automatic error handling
def handle_errors(category: ErrorCategory = ErrorCategory.SYSTEM, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """Decorator to automatically handle and convert exceptions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseApplicationError:
                # Re-raise our custom errors
                raise
            except Exception as e:
                # Convert unexpected errors
                context = ErrorContext()
                if hasattr(func, '__name__'):
                    context.additional_data = {'function': func.__name__}
                
                raise SystemError(
                    message=f"Unexpected error in {func.__name__ if hasattr(func, '__name__') else 'function'}: {str(e)}",
                    context=context
                )
        return wrapper
    return decorator


# Error reporting and monitoring integration
class ErrorReporter:
    """Error reporting and monitoring integration."""
    
    @staticmethod
    def should_alert(error: BaseApplicationError) -> bool:
        """Determine if error should trigger alerts."""
        return (
            error.should_alert or 
            error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH] or
            error.category in [ErrorCategory.DATABASE, ErrorCategory.SYSTEM, ErrorCategory.CONFIGURATION]
        )
    
    @staticmethod
    def get_error_metrics(error: BaseApplicationError) -> Dict[str, Any]:
        """Extract metrics from error for monitoring."""
        return {
            'error_count': 1,
            'error_category': error.category.value,
            'error_severity': error.severity.value,
            'http_status': error.http_status_code,
            'should_alert': ErrorReporter.should_alert(error)
        }
