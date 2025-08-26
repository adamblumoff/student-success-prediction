#!/usr/bin/env python3
"""
Production-Ready Configuration Management

Centralized configuration system with validation, type safety, and environment-specific settings.
Provides comprehensive configuration management for the Student Success Prediction system.
"""

import os
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import secrets
from urllib.parse import urlparse


class Environment(Enum):
    """Environment types with explicit validation."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    
    @classmethod
    def from_string(cls, env_str: str) -> 'Environment':
        """Parse environment string with validation."""
        env_mapping = {
            'dev': cls.DEVELOPMENT,
            'development': cls.DEVELOPMENT,
            'test': cls.TESTING,
            'testing': cls.TESTING,
            'stage': cls.STAGING,
            'staging': cls.STAGING,
            'prod': cls.PRODUCTION,
            'production': cls.PRODUCTION,
        }
        
        normalized = env_str.lower().strip()
        if normalized not in env_mapping:
            raise ValueError(f"Invalid environment: {env_str}. Must be one of: {list(env_mapping.keys())}")
        
        return env_mapping[normalized]


class LogLevel(Enum):
    """Logging levels with validation."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, level_str: str) -> 'LogLevel':
        """Parse log level string with validation."""
        try:
            return cls(level_str.upper().strip())
        except ValueError:
            raise ValueError(f"Invalid log level: {level_str}. Must be one of: {[e.value for e in cls]}")


@dataclass
class SecurityConfig:
    """Security-related configuration with comprehensive validation."""
    api_key: str
    session_secret: str
    development_mode: bool = False
    max_file_size_mb: int = 10
    rate_limit_per_minute: int = 60
    allowed_hosts: List[str] = field(default_factory=lambda: ['localhost', '127.0.0.1'])
    csrf_protection: bool = True
    secure_headers: bool = True
    
    def __post_init__(self):
        """Validate security configuration after initialization."""
        self._validate_api_key()
        self._validate_session_secret()
        self._validate_file_size()
        self._validate_rate_limit()
        self._validate_environment_consistency()
    
    def _validate_api_key(self) -> None:
        """Validate API key strength and security."""
        if not self.api_key:
            raise ValueError("API key cannot be empty")
        
        if len(self.api_key) < 16:
            raise ValueError("API key must be at least 16 characters long")
        
        if self.api_key == "dev-key-change-me" and not self.development_mode:
            raise ValueError("Cannot use default API key in production environment")
        
        # Check for weak patterns
        if self.api_key.isalnum() and len(set(self.api_key)) < 8:
            logging.warning("API key may be weak - consider using higher entropy")
    
    def _validate_session_secret(self) -> None:
        """Validate session secret strength."""
        if not self.session_secret:
            raise ValueError("Session secret cannot be empty")
        
        if len(self.session_secret) < 32:
            raise ValueError("Session secret must be at least 32 characters long")
    
    def _validate_file_size(self) -> None:
        """Validate file size limits."""
        if self.max_file_size_mb <= 0 or self.max_file_size_mb > 100:
            raise ValueError("Max file size must be between 1 and 100 MB")
    
    def _validate_rate_limit(self) -> None:
        """Validate rate limiting configuration."""
        if self.rate_limit_per_minute <= 0 or self.rate_limit_per_minute > 1000:
            raise ValueError("Rate limit must be between 1 and 1000 requests per minute")
    
    def _validate_environment_consistency(self) -> None:
        """Validate security settings are appropriate for environment."""
        if self.development_mode:
            logging.warning("Development mode is enabled - authentication bypass allowed for localhost")


@dataclass
class DatabaseConfig:
    """Database configuration with connection validation."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    echo_queries: bool = False
    
    def __post_init__(self):
        """Validate database configuration."""
        self._validate_url()
        self._validate_pool_settings()
    
    def _validate_url(self) -> None:
        """Validate database URL format and accessibility."""
        if not self.url:
            raise ValueError("Database URL cannot be empty")
        
        try:
            parsed = urlparse(self.url)
            if parsed.scheme not in ['postgresql', 'postgres', 'sqlite']:
                raise ValueError(f"Unsupported database scheme: {parsed.scheme}")
        except Exception as e:
            raise ValueError(f"Invalid database URL format: {e}")
    
    def _validate_pool_settings(self) -> None:
        """Validate connection pool settings."""
        if self.pool_size <= 0 or self.pool_size > 100:
            raise ValueError("Pool size must be between 1 and 100")
        
        if self.max_overflow < 0 or self.max_overflow > 200:
            raise ValueError("Max overflow must be between 0 and 200")
        
        if self.pool_recycle <= 0:
            raise ValueError("Pool recycle time must be positive")
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.url.startswith(('postgresql://', 'postgres://'))
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.url.startswith('sqlite://')


@dataclass
class MLConfig:
    """Machine learning model configuration."""
    model_cache_size: int = 5
    prediction_timeout_seconds: int = 30
    batch_size: int = 1000
    enable_explainable_ai: bool = True
    model_validation_enabled: bool = True
    
    def __post_init__(self):
        """Validate ML configuration."""
        if self.model_cache_size <= 0 or self.model_cache_size > 20:
            raise ValueError("Model cache size must be between 1 and 20")
        
        if self.prediction_timeout_seconds <= 0 or self.prediction_timeout_seconds > 300:
            raise ValueError("Prediction timeout must be between 1 and 300 seconds")
        
        if self.batch_size <= 0 or self.batch_size > 10000:
            raise ValueError("Batch size must be between 1 and 10000")


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enable_metrics: bool = True
    enable_tracing: bool = False
    health_check_interval: int = 60
    log_level: LogLevel = LogLevel.INFO
    structured_logging: bool = True
    log_file_rotation_mb: int = 10
    log_file_backup_count: int = 5
    
    def __post_init__(self):
        """Validate monitoring configuration."""
        if self.health_check_interval <= 0 or self.health_check_interval > 3600:
            raise ValueError("Health check interval must be between 1 and 3600 seconds")
        
        if self.log_file_rotation_mb <= 0 or self.log_file_rotation_mb > 100:
            raise ValueError("Log file rotation size must be between 1 and 100 MB")


@dataclass
class ApplicationConfig:
    """Complete application configuration with all subsystems."""
    environment: Environment
    security: SecurityConfig
    database: DatabaseConfig
    ml: MLConfig
    monitoring: MonitoringConfig
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8001
    workers: int = 1
    
    def __post_init__(self):
        """Validate complete application configuration."""
        self._validate_server_config()
    
    def _validate_server_config(self) -> None:
        """Validate server configuration."""
        if not (1 <= self.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        
        if not (1 <= self.workers <= 32):
            raise ValueError("Worker count must be between 1 and 32")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


class ConfigurationLoader:
    """Production-ready configuration loader with comprehensive validation."""
    
    @staticmethod
    def load() -> ApplicationConfig:
        """Load and validate complete application configuration."""
        try:
            # Load environment
            env_str = os.getenv('ENVIRONMENT', 'development')
            environment = Environment.from_string(env_str)
            
            # Load security configuration
            security = ConfigurationLoader._load_security_config(environment)
            
            # Load database configuration
            database = ConfigurationLoader._load_database_config()
            
            # Load ML configuration
            ml = ConfigurationLoader._load_ml_config()
            
            # Load monitoring configuration
            monitoring = ConfigurationLoader._load_monitoring_config(environment)
            
            # Server configuration
            host = os.getenv('HOST', '0.0.0.0')
            port = int(os.getenv('PORT', '8001'))
            workers = int(os.getenv('WORKERS', '1'))
            
            config = ApplicationConfig(
                environment=environment,
                security=security,
                database=database,
                ml=ml,
                monitoring=monitoring,
                host=host,
                port=port,
                workers=workers
            )
            
            # Log configuration summary
            logger = logging.getLogger(__name__)
            logger.info(f"Configuration loaded successfully for {environment.value} environment")
            logger.info(f"Database: {database.url.split('@')[-1] if '@' in database.url else 'SQLite'}")
            logger.info(f"Security: API key configured, development_mode={security.development_mode}")
            
            return config
            
        except Exception as e:
            raise RuntimeError(f"Failed to load application configuration: {e}")
    
    @staticmethod
    def _load_security_config(environment: Environment) -> SecurityConfig:
        """Load security configuration with environment-appropriate defaults."""
        # API Key handling
        api_key = os.getenv('MVP_API_KEY')
        if not api_key:
            if environment == Environment.DEVELOPMENT:
                api_key = "dev-key-change-me"
            else:
                raise ValueError("MVP_API_KEY environment variable is required in production")
        
        # Session secret handling
        session_secret = os.getenv('SESSION_SECRET')
        if not session_secret:
            if environment == Environment.DEVELOPMENT:
                session_secret = secrets.token_urlsafe(32)
                logging.info("Generated temporary session secret for development")
            else:
                raise ValueError("SESSION_SECRET environment variable is required in production")
        
        return SecurityConfig(
            api_key=api_key,
            session_secret=session_secret,
            development_mode=os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true',
            max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', '10')),
            rate_limit_per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', '60')),
            allowed_hosts=os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(','),
            csrf_protection=os.getenv('CSRF_PROTECTION', 'true').lower() == 'true',
            secure_headers=os.getenv('SECURE_HEADERS', 'true').lower() == 'true'
        )
    
    @staticmethod
    def _load_database_config() -> DatabaseConfig:
        """Load database configuration with intelligent defaults."""
        # Primary database URL
        database_url = os.getenv('DATABASE_URL')
        
        # Component-based fallback (no hardcoded credentials)
        if not database_url:
            db_host = os.getenv('DB_HOST')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'student_success')
            db_user = os.getenv('DB_USER')
            db_password = os.getenv('DB_PASSWORD')
            
            # Check if we have complete PostgreSQL configuration
            if db_host and db_user and db_password:
                # Only create PostgreSQL URL if all credentials are explicitly provided
                database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                logging.info("Using PostgreSQL database from environment variables")
            else:
                # SQLite fallback for development only
                missing_vars = []
                if not db_host:
                    missing_vars.append('DB_HOST')
                if not db_user:
                    missing_vars.append('DB_USER')
                if not db_password:
                    missing_vars.append('DB_PASSWORD')
                
                if os.getenv('ENVIRONMENT') == 'production':
                    raise ValueError(f"❌ SECURITY ERROR: Production requires PostgreSQL credentials. Missing: {', '.join(missing_vars)}")
                
                database_url = "sqlite:///./mvp_data.db"
                logging.warning(f"PostgreSQL credentials missing ({', '.join(missing_vars)}), falling back to SQLite for development")
        
        return DatabaseConfig(
            url=database_url,
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
            pool_pre_ping=os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true',
            echo_queries=os.getenv('SQL_DEBUG', 'false').lower() == 'true'
        )
    
    @staticmethod
    def _load_ml_config() -> MLConfig:
        """Load machine learning configuration."""
        return MLConfig(
            model_cache_size=int(os.getenv('ML_MODEL_CACHE_SIZE', '5')),
            prediction_timeout_seconds=int(os.getenv('ML_PREDICTION_TIMEOUT', '30')),
            batch_size=int(os.getenv('ML_BATCH_SIZE', '1000')),
            enable_explainable_ai=os.getenv('ML_ENABLE_EXPLAINABLE_AI', 'true').lower() == 'true',
            model_validation_enabled=os.getenv('ML_MODEL_VALIDATION', 'true').lower() == 'true'
        )
    
    @staticmethod
    def _load_monitoring_config(environment: Environment) -> MonitoringConfig:
        """Load monitoring configuration with environment-appropriate defaults."""
        return MonitoringConfig(
            enable_metrics=os.getenv('MONITORING_ENABLE_METRICS', 'true').lower() == 'true',
            enable_tracing=os.getenv('MONITORING_ENABLE_TRACING', 'false').lower() == 'true',
            health_check_interval=int(os.getenv('MONITORING_HEALTH_CHECK_INTERVAL', '60')),
            log_level=LogLevel.from_string(os.getenv('LOG_LEVEL', 'INFO')),
            structured_logging=environment != Environment.DEVELOPMENT,
            log_file_rotation_mb=int(os.getenv('LOG_FILE_ROTATION_MB', '10')),
            log_file_backup_count=int(os.getenv('LOG_FILE_BACKUP_COUNT', '5'))
        )


# Global configuration instance
_config: Optional[ApplicationConfig] = None


def get_config() -> ApplicationConfig:
    """Get global application configuration instance."""
    global _config
    if _config is None:
        _config = ConfigurationLoader.load()
    return _config


def reload_config() -> ApplicationConfig:
    """Reload configuration from environment variables."""
    global _config
    _config = ConfigurationLoader.load()
    return _config


def validate_production_config() -> Dict[str, Any]:
    """Validate configuration for production deployment."""
    config = get_config()
    issues = []
    warnings = []
    
    if not config.is_production:
        warnings.append("Not running in production environment")
    
    if config.security.development_mode:
        issues.append("Development mode is enabled in production")
    
    if config.security.api_key == "dev-key-change-me":
        issues.append("Using default API key")
    
    if not config.database.is_postgresql and config.is_production:
        warnings.append("Using SQLite in production (not recommended)")
    
    if not config.monitoring.enable_metrics:
        warnings.append("Metrics collection is disabled")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'environment': config.environment.value,
        'database_type': 'postgresql' if config.database.is_postgresql else 'sqlite'
    }
