#!/usr/bin/env python3
"""
Production Configuration Management

Centralized configuration management with validation, environment-specific settings,
and security best practices for production deployment.
"""

import os
import logging
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
from functools import lru_cache

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """Database configuration with validation."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo_sql: bool = False
    
    def __post_init__(self):
        """Validate database configuration."""
        if not self.url:
            raise ValueError("Database URL is required")
        
        # Production validation
        if Environment.PRODUCTION.value in os.getenv('ENVIRONMENT', '').lower():
            if 'sqlite' in self.url:
                raise ValueError("SQLite not allowed in production")
            if 'localhost' in self.url and 'sslmode=disable' in self.url:
                logger.warning("⚠️ Production database using localhost without SSL")

@dataclass
class SecurityConfig:
    """Security configuration with validation."""
    api_key: str
    session_secret: str
    password_salt: str = None
    rate_limit_per_minute: int = 60
    max_file_size_mb: int = 10
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    jwt_expiry_hours: int = 24
    
    def __post_init__(self):
        """Validate security configuration."""
        if len(self.api_key) < 16:
            raise ValueError("API key must be at least 16 characters")
        
        if len(self.session_secret) < 32:
            raise ValueError("Session secret must be at least 32 characters")
        
        # Production security checks
        if Environment.PRODUCTION.value in os.getenv('ENVIRONMENT', '').lower():
            if self.api_key == "dev-key-change-me":
                raise ValueError("Cannot use default API key in production")
            if "*" in self.allowed_origins:
                logger.warning("⚠️ Wildcard CORS allowed in production")

@dataclass
class MLConfig:
    """Machine learning configuration."""
    models_dir: str
    prediction_cache_ttl: int = 300  # 5 minutes
    batch_size: int = 1000
    prediction_timeout: int = 30
    feature_importance_threshold: float = 0.01
    
    def __post_init__(self):
        """Validate ML configuration."""
        models_path = Path(self.models_dir)
        if not models_path.exists():
            logger.warning(f"Models directory does not exist: {self.models_dir}")

@dataclass
class IntegrationConfig:
    """External integration configuration."""
    canvas_base_url: Optional[str] = None
    canvas_api_token: Optional[str] = None
    powerschool_base_url: Optional[str] = None
    powerschool_client_id: Optional[str] = None
    powerschool_client_secret: Optional[str] = None
    google_credentials_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate integration configuration."""
        # Validate Canvas configuration if provided
        if self.canvas_api_token and not self.canvas_base_url:
            raise ValueError("Canvas base URL required when API token is provided")
        
        # Validate PowerSchool configuration if provided
        if self.powerschool_client_id and not self.powerschool_client_secret:
            raise ValueError("PowerSchool client secret required when client ID is provided")

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    log_level: str = "INFO"
    structured_logging: bool = True
    metrics_enabled: bool = True
    health_check_interval: int = 60
    error_reporting_enabled: bool = True
    performance_monitoring: bool = True

@dataclass
class AppConfig:
    """Complete application configuration."""
    environment: Environment
    debug: bool
    database: DatabaseConfig
    security: SecurityConfig
    ml: MLConfig
    integrations: IntegrationConfig
    monitoring: MonitoringConfig
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8001
    workers: int = 1
    
    def __post_init__(self):
        """Validate complete configuration."""
        # Production-specific validations
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug mode cannot be enabled in production")
            if self.workers < 2:
                logger.warning("⚠️ Production should use multiple workers")

class ConfigurationManager:
    """Central configuration manager with environment-specific loading."""
    
    def __init__(self):
        self._config: Optional[AppConfig] = None
        self._environment = self._detect_environment()
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from various sources."""
        env_var = os.getenv('ENVIRONMENT', 'development').lower()
        
        env_mapping = {
            'dev': Environment.DEVELOPMENT,
            'development': Environment.DEVELOPMENT,
            'test': Environment.TESTING,
            'testing': Environment.TESTING,
            'stage': Environment.STAGING,
            'staging': Environment.STAGING,
            'prod': Environment.PRODUCTION,
            'production': Environment.PRODUCTION
        }
        
        return env_mapping.get(env_var, Environment.DEVELOPMENT)
    
    @lru_cache(maxsize=1)
    def load_config(self) -> AppConfig:
        """Load configuration with caching."""
        if self._config is not None:
            return self._config
        
        try:
            # Load environment-specific configuration
            config_methods = {
                Environment.DEVELOPMENT: self._load_development_config,
                Environment.TESTING: self._load_testing_config,
                Environment.STAGING: self._load_staging_config,
                Environment.PRODUCTION: self._load_production_config
            }
            
            config_loader = config_methods.get(self._environment, self._load_development_config)
            self._config = config_loader()
            
            logger.info(f"✅ Configuration loaded for {self._environment.value} environment")
            return self._config
            
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            raise ValueError(f"Configuration loading failed: {e}")
    
    def _load_development_config(self) -> AppConfig:
        """Load development configuration."""
        return AppConfig(
            environment=Environment.DEVELOPMENT,
            debug=True,
            database=DatabaseConfig(
                url=os.getenv('DATABASE_URL', 'sqlite:///./mvp_data.db'),
                pool_size=5,
                echo_sql=os.getenv('SQL_DEBUG', 'false').lower() == 'true'
            ),
            security=SecurityConfig(
                api_key=os.getenv('MVP_API_KEY', 'dev-key-change-me'),
                session_secret=os.getenv('SESSION_SECRET', 'dev-session-secret-change-me-in-production'),
                rate_limit_per_minute=120,  # Generous for development
                allowed_origins=["*"]  # Permissive for development
            ),
            ml=MLConfig(
                models_dir=os.getenv('MODELS_DIR', 'results/models'),
                prediction_cache_ttl=60  # Short TTL for development
            ),
            integrations=IntegrationConfig(
                canvas_base_url=os.getenv('CANVAS_BASE_URL'),
                canvas_api_token=os.getenv('CANVAS_API_TOKEN'),
                powerschool_base_url=os.getenv('POWERSCHOOL_BASE_URL'),
                powerschool_client_id=os.getenv('POWERSCHOOL_CLIENT_ID'),
                powerschool_client_secret=os.getenv('POWERSCHOOL_CLIENT_SECRET'),
                google_credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH')
            ),
            monitoring=MonitoringConfig(
                log_level="DEBUG",
                structured_logging=False,  # Simple logging for development
                metrics_enabled=False  # Disabled for development
            ),
            host="127.0.0.1",  # Localhost for development
            port=int(os.getenv('PORT', '8001')),
            workers=1
        )
    
    def _load_testing_config(self) -> AppConfig:
        """Load testing configuration."""
        config = self._load_development_config()
        config.environment = Environment.TESTING
        config.debug = False
        config.database.url = os.getenv('TEST_DATABASE_URL', 'sqlite:///./test.db')
        config.security.rate_limit_per_minute = 1000  # High for testing
        config.ml.prediction_cache_ttl = 0  # No caching in tests
        config.monitoring.metrics_enabled = False
        return config
    
    def _load_staging_config(self) -> AppConfig:
        """Load staging configuration."""
        return AppConfig(
            environment=Environment.STAGING,
            debug=False,
            database=DatabaseConfig(
                url=self._require_env('DATABASE_URL'),
                pool_size=10,
                max_overflow=20,
                echo_sql=False
            ),
            security=SecurityConfig(
                api_key=self._require_env('MVP_API_KEY'),
                session_secret=self._require_env('SESSION_SECRET'),
                rate_limit_per_minute=60,
                allowed_origins=os.getenv('ALLOWED_ORIGINS', '*').split(',')
            ),
            ml=MLConfig(
                models_dir=os.getenv('MODELS_DIR', '/opt/models'),
                prediction_cache_ttl=300
            ),
            integrations=IntegrationConfig(
                canvas_base_url=os.getenv('CANVAS_BASE_URL'),
                canvas_api_token=os.getenv('CANVAS_API_TOKEN'),
                powerschool_base_url=os.getenv('POWERSCHOOL_BASE_URL'),
                powerschool_client_id=os.getenv('POWERSCHOOL_CLIENT_ID'),
                powerschool_client_secret=os.getenv('POWERSCHOOL_CLIENT_SECRET'),
                google_credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH')
            ),
            monitoring=MonitoringConfig(
                log_level="INFO",
                structured_logging=True,
                metrics_enabled=True,
                error_reporting_enabled=True
            ),
            port=int(os.getenv('PORT', '8001')),
            workers=2
        )
    
    def _load_production_config(self) -> AppConfig:
        """Load production configuration with strict validation."""
        return AppConfig(
            environment=Environment.PRODUCTION,
            debug=False,
            database=DatabaseConfig(
                url=self._require_env('DATABASE_URL'),
                pool_size=int(os.getenv('DB_POOL_SIZE', '20')),
                max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '30')),
                pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
                echo_sql=False  # Never echo SQL in production
            ),
            security=SecurityConfig(
                api_key=self._require_env('MVP_API_KEY'),
                session_secret=self._require_env('SESSION_SECRET'),
                password_salt=self._require_env('PASSWORD_SALT'),
                rate_limit_per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', '60')),
                max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', '10')),
                allowed_origins=self._require_env('ALLOWED_ORIGINS').split(','),
                jwt_expiry_hours=int(os.getenv('JWT_EXPIRY_HOURS', '24'))
            ),
            ml=MLConfig(
                models_dir=os.getenv('MODELS_DIR', '/opt/models'),
                prediction_cache_ttl=int(os.getenv('PREDICTION_CACHE_TTL', '300')),
                batch_size=int(os.getenv('ML_BATCH_SIZE', '1000')),
                prediction_timeout=int(os.getenv('PREDICTION_TIMEOUT', '30'))
            ),
            integrations=IntegrationConfig(
                canvas_base_url=os.getenv('CANVAS_BASE_URL'),
                canvas_api_token=os.getenv('CANVAS_API_TOKEN'),
                powerschool_base_url=os.getenv('POWERSCHOOL_BASE_URL'),
                powerschool_client_id=os.getenv('POWERSCHOOL_CLIENT_ID'),
                powerschool_client_secret=os.getenv('POWERSCHOOL_CLIENT_SECRET'),
                google_credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH')
            ),
            monitoring=MonitoringConfig(
                log_level=os.getenv('LOG_LEVEL', 'INFO'),
                structured_logging=True,
                metrics_enabled=True,
                health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '60')),
                error_reporting_enabled=True,
                performance_monitoring=True
            ),
            port=int(os.getenv('PORT', '8001')),
            workers=int(os.getenv('WORKERS', '4'))
        )
    
    def _require_env(self, var_name: str) -> str:
        """Require environment variable with clear error message."""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Required environment variable {var_name} is not set")
        return value
    
    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        return self.load_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration and return status."""
        try:
            config = self.get_config()
            
            validation_results = {
                'valid': True,
                'environment': config.environment.value,
                'warnings': [],
                'errors': []
            }
            
            # Environment-specific validations
            if config.environment == Environment.PRODUCTION:
                if config.debug:
                    validation_results['errors'].append("Debug mode enabled in production")
                    validation_results['valid'] = False
                
                if 'dev-key' in config.security.api_key:
                    validation_results['errors'].append("Default API key in production")
                    validation_results['valid'] = False
                
                if config.workers < 2:
                    validation_results['warnings'].append("Single worker in production")
            
            # Database validations
            try:
                # Test database connection would go here
                pass
            except Exception as e:
                validation_results['errors'].append(f"Database connection failed: {e}")
                validation_results['valid'] = False
            
            # ML models validation
            models_path = Path(config.ml.models_dir)
            if not models_path.exists():
                validation_results['warnings'].append(f"Models directory not found: {config.ml.models_dir}")
            
            return validation_results
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Configuration validation failed: {e}"],
                'warnings': []
            }

# Global configuration manager
config_manager = ConfigurationManager()

# Convenience functions for FastAPI dependencies
def get_config() -> AppConfig:
    """Get application configuration."""
    return config_manager.get_config()

def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return config_manager.get_config().database

def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    return config_manager.get_config().security

def get_ml_config() -> MLConfig:
    """Get ML configuration."""
    return config_manager.get_config().ml

# Configuration validation endpoint data
def get_config_status() -> Dict[str, Any]:
    """Get configuration validation status."""
    return config_manager.validate_config()