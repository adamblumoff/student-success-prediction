#!/usr/bin/env python3
"""
Logging Configuration for Student Success Predictor

Provides structured logging for production debugging and monitoring.
Includes different log levels, request tracking, and error aggregation.
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
import json
from pathlib import Path

# Ensure logs directory exists
logs_dir = Path(__file__).parent.parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs for production"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'endpoint'):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, 'student_count'):
            log_entry["student_count"] = record.student_count
        if hasattr(record, 'processing_time'):
            log_entry["processing_time_ms"] = record.processing_time
            
        return json.dumps(log_entry)

class SimpleFormatter(logging.Formatter):
    """Simple formatter for development and console output"""
    
    def format(self, record):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"[{timestamp}] {record.levelname:8} {record.name:20} {record.getMessage()}"

def setup_logging():
    """Configure logging for the application"""
    
    # Determine environment
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                '()': StructuredFormatter,
            },
            'simple': {
                '()': SimpleFormatter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'simple' if environment == 'development' else 'structured',
                'stream': sys.stdout
            }
        },
        'loggers': {
            'src.mvp': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'mvp': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'fastapi': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }
    
    # Add file logging for production
    if environment in ['production', 'prod']:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'structured',
            'filename': str(logs_dir / 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
        
        config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'structured',
            'filename': str(logs_dir / 'errors.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
        
        # Add file handlers to all loggers
        for logger_name in ['src.mvp', 'mvp', 'root']:
            if logger_name in config['loggers']:
                config['loggers'][logger_name]['handlers'].extend(['file', 'error_file'])
            else:
                config['loggers'][logger_name] = {
                    'level': log_level,
                    'handlers': ['console', 'file', 'error_file'],
                    'propagate': False
                }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized for environment: {environment}, level: {log_level}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

def log_request(endpoint: str, method: str, user_id: str = None, processing_time: float = None):
    """Log API request with structured data"""
    logger = get_logger('mvp.requests')
    extra = {
        'endpoint': endpoint,
        'method': method,
        'processing_time': processing_time
    }
    if user_id:
        extra['user_id'] = user_id
        
    logger.info(f"{method} {endpoint}", extra=extra)

def log_prediction(student_count: int, model_type: str = None, processing_time: float = None):
    """Log ML prediction with metrics"""
    logger = get_logger('mvp.predictions')
    extra = {
        'student_count': student_count,
        'processing_time': processing_time
    }
    if model_type:
        extra['model_type'] = model_type
        
    logger.info(f"Prediction completed for {student_count} students", extra=extra)

def log_error(error: Exception, context: str = None, user_id: str = None):
    """Log error with context"""
    logger = get_logger('mvp.errors')
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    if context:
        extra['context'] = context
        
    logger.error(f"Error in {context}: {str(error)}", exc_info=True, extra=extra)

# Initialize logging when module is imported
setup_logging()