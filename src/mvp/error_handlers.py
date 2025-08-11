#!/usr/bin/env python3
"""
Production-Ready Error Handling Module

Implements comprehensive error handling with secure error messages,
proper logging, and user-friendly responses for all API endpoints.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorCategories:
    """Standard error categories for consistent handling"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    FILE_PROCESSING = "file_processing"
    DATABASE = "database"
    ML_MODEL = "ml_model"
    SYSTEM = "system"
    EXTERNAL_API = "external_api"

class SecureErrorHandler:
    """Secure error handling that prevents information leakage"""
    
    def __init__(self):
        self.is_production = os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']
        self.log_level = logging.ERROR if self.is_production else logging.WARNING
    
    def handle_authentication_error(self, error: Exception, request: Request) -> JSONResponse:
        """Handle authentication-related errors securely"""
        client_ip = self._get_client_ip(request)
        
        # Log detailed error for security monitoring
        logger.warning(
            f"Authentication failed from {client_ip}: {type(error).__name__}",
            extra={
                'category': ErrorCategories.AUTHENTICATION,
                'client_ip': client_ip,
                'endpoint': str(request.url.path),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Return generic error to prevent information leakage
        return JSONResponse(
            status_code=401,
            content={
                'error': 'Authentication required',
                'category': ErrorCategories.AUTHENTICATION,
                'timestamp': datetime.utcnow().isoformat()
            },
            headers={'WWW-Authenticate': 'Bearer'}
        )
    
    def handle_rate_limit_error(self, error: HTTPException, request: Request) -> JSONResponse:
        """Handle rate limiting errors with user guidance"""
        client_ip = self._get_client_ip(request)
        
        logger.warning(
            f"Rate limit exceeded for {client_ip}: {error.detail}",
            extra={
                'category': ErrorCategories.RATE_LIMIT,
                'client_ip': client_ip,
                'endpoint': str(request.url.path)
            }
        )
        
        return JSONResponse(
            status_code=429,
            content={
                'error': 'Too many requests',
                'category': ErrorCategories.RATE_LIMIT,
                'message': 'Please wait before making another request',
                'user_message': str(error.detail),
                'timestamp': datetime.utcnow().isoformat()
            },
            headers={'Retry-After': '60'}
        )
    
    def handle_validation_error(self, error: ValidationError, request: Request) -> JSONResponse:
        """Handle input validation errors with helpful guidance"""
        logger.info(
            f"Validation error: {error}",
            extra={
                'category': ErrorCategories.VALIDATION,
                'endpoint': str(request.url.path)
            }
        )
        
        # Sanitize validation errors to prevent information leakage
        safe_errors = []
        for err in error.errors():
            safe_error = {
                'field': '.'.join(str(loc) for loc in err['loc']),
                'message': err['msg'],
                'type': err['type']
            }
            safe_errors.append(safe_error)
        
        return JSONResponse(
            status_code=422,
            content={
                'error': 'Validation failed',
                'category': ErrorCategories.VALIDATION,
                'details': safe_errors,
                'message': 'Please check your input data',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def handle_file_processing_error(self, error: Exception, request: Request, 
                                   filename: str = None) -> JSONResponse:
        """Handle file processing errors with user-friendly messages"""
        error_type = type(error).__name__
        
        logger.error(
            f"File processing error for {filename}: {error_type} - {str(error)}",
            extra={
                'category': ErrorCategories.FILE_PROCESSING,
                'filename': filename,
                'error_type': error_type
            }
        )
        
        # Map specific errors to user-friendly messages
        user_messages = {
            'UnicodeDecodeError': 'File encoding is invalid. Please ensure your CSV file is saved as UTF-8.',
            'pd.errors.EmptyDataError': 'The uploaded file appears to be empty.',
            'pd.errors.ParserError': 'The CSV file format is invalid. Please check the file structure.',
            'FileNotFoundError': 'The requested file could not be found.',
            'PermissionError': 'Unable to process the file due to permissions.'
        }
        
        user_message = user_messages.get(error_type, 'Unable to process the uploaded file.')
        
        status_code = 400
        if error_type in ['FileNotFoundError']:
            status_code = 404
        elif error_type in ['PermissionError']:
            status_code = 500
        
        return JSONResponse(
            status_code=status_code,
            content={
                'error': 'File processing failed',
                'category': ErrorCategories.FILE_PROCESSING,
                'message': user_message,
                'filename': filename,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def handle_database_error(self, error: Exception, request: Request) -> JSONResponse:
        """Handle database errors securely"""
        error_type = type(error).__name__
        
        logger.error(
            f"Database error: {error_type} - {str(error)}",
            extra={
                'category': ErrorCategories.DATABASE,
                'error_type': error_type,
                'endpoint': str(request.url.path)
            }
        )
        
        # Don't expose database details in production
        if self.is_production:
            message = "A database error occurred. Please try again later."
        else:
            message = f"Database error: {str(error)}"
        
        return JSONResponse(
            status_code=503,
            content={
                'error': 'Database unavailable',
                'category': ErrorCategories.DATABASE,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def handle_ml_model_error(self, error: Exception, request: Request, 
                            model_name: str = None) -> JSONResponse:
        """Handle ML model errors with appropriate fallbacks"""
        error_type = type(error).__name__
        
        logger.error(
            f"ML model error ({model_name}): {error_type} - {str(error)}",
            extra={
                'category': ErrorCategories.ML_MODEL,
                'model_name': model_name,
                'error_type': error_type
            }
        )
        
        # Provide helpful error messages based on error type
        if error_type in ['FileNotFoundError', 'ImportError', 'ModuleNotFoundError']:
            message = f"The {model_name or 'ML'} model is currently unavailable."
            status_code = 503
        elif error_type in ['ValueError', 'KeyError']:
            message = "Input data format is incompatible with the model."
            status_code = 400
        else:
            message = f"An error occurred while processing with the {model_name or 'ML'} model."
            status_code = 500
        
        return JSONResponse(
            status_code=status_code,
            content={
                'error': 'ML model error',
                'category': ErrorCategories.ML_MODEL,
                'message': message,
                'model': model_name,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def handle_system_error(self, error: Exception, request: Request) -> JSONResponse:
        """Handle unexpected system errors securely"""
        error_type = type(error).__name__
        
        # Log full traceback for debugging
        logger.error(
            f"Unexpected system error: {error_type} - {str(error)}",
            extra={
                'category': ErrorCategories.SYSTEM,
                'error_type': error_type,
                'endpoint': str(request.url.path),
                'traceback': traceback.format_exc() if not self.is_production else None
            }
        )
        
        # Generic error message for production
        if self.is_production:
            message = "An unexpected error occurred. Please try again later."
        else:
            message = f"System error: {str(error)}"
        
        return JSONResponse(
            status_code=500,
            content={
                'error': 'Internal server error',
                'category': ErrorCategories.SYSTEM,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address securely"""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
        
        return request.client.host if request.client else 'unknown'

# Global error handler instance
error_handler = SecureErrorHandler()

# Decorator for automatic error handling
def handle_api_errors(endpoint_name: str = None):
    """Decorator to automatically handle common API errors"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions (already handled)
                raise
            except ValidationError as e:
                request = next((arg for arg in args if isinstance(arg, Request)), None)
                if request:
                    return error_handler.handle_validation_error(e, request)
                raise
            except Exception as e:
                request = next((arg for arg in args if isinstance(arg, Request)), None)
                if request:
                    return error_handler.handle_system_error(e, request)
                raise
        return wrapper
    return decorator

# Error response helpers
def create_success_response(data: Dict[str, Any], message: str = None) -> JSONResponse:
    """Create standardized success response"""
    response = {
        'success': True,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    
    if message:
        response['message'] = message
    
    return JSONResponse(response)

def create_error_response(error_category: str, message: str, 
                         status_code: int = 400, details: Dict = None) -> JSONResponse:
    """Create standardized error response"""
    response = {
        'success': False,
        'error': True,
        'category': error_category,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        response['details'] = details
    
    return JSONResponse(status_code=status_code, content=response)