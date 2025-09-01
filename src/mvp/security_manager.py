#!/usr/bin/env python3
"""
Production Security Manager
Enforces security policies and environment-specific configurations
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EnvironmentType(Enum):
    """Environment types with security implications"""
    PRODUCTION = "production"
    STAGING = "staging" 
    DEVELOPMENT = "development"
    TESTING = "testing"
    UNKNOWN = "unknown"

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    require_https: bool = True
    require_database_encryption: bool = True
    allow_demo_users: bool = False
    require_strong_api_keys: bool = True
    enable_audit_logging: bool = True
    require_environment_config: bool = True
    min_api_key_length: int = 32
    allowed_debug_features: List[str] = None

    def __post_init__(self):
        if self.allowed_debug_features is None:
            self.allowed_debug_features = []

class SecurityManager:
    """
    Manages security policies and environment detection
    Enforces FERPA compliance and production security requirements
    """
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.policy = self._get_security_policy()
        self._enforce_security_policy()
        
        logger.info(f"Security Manager initialized for {self.environment.value} environment")
    
    def _detect_environment(self) -> EnvironmentType:
        """Detect current environment based on multiple indicators"""
        
        # Primary environment variable
        env_var = os.getenv('ENVIRONMENT', '').lower().strip()
        if env_var:
            try:
                return EnvironmentType(env_var)
            except ValueError:
                logger.warning(f"Unknown ENVIRONMENT value: {env_var}")
        
        # Secondary indicators
        indicators = {
            'production': [
                os.getenv('RAILWAY_ENVIRONMENT_NAME') == 'production',
                os.getenv('VERCEL_ENV') == 'production',
                os.getenv('NODE_ENV') == 'production',
                'prod' in os.getenv('DATABASE_URL', '').lower(),
                os.getenv('ENABLE_HTTPS', 'false').lower() == 'true'
            ],
            'staging': [
                os.getenv('RAILWAY_ENVIRONMENT_NAME') == 'staging',
                os.getenv('VERCEL_ENV') == 'preview',
                'staging' in os.getenv('DATABASE_URL', '').lower()
            ],
            'development': [
                os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true',
                os.getenv('SQL_DEBUG', 'false').lower() == 'true',
                'localhost' in os.getenv('DATABASE_URL', ''),
                'sqlite' in os.getenv('DATABASE_URL', '').lower()
            ]
        }
        
        # Score each environment type
        scores = {}
        for env_type, conditions in indicators.items():
            scores[env_type] = sum(1 for condition in conditions if condition)
        
        # Return highest scoring environment
        if scores['production'] > 0:
            return EnvironmentType.PRODUCTION
        elif scores['staging'] > 0:
            return EnvironmentType.STAGING
        elif scores['development'] > 0:
            return EnvironmentType.DEVELOPMENT
        
        logger.warning("Could not determine environment type, defaulting to UNKNOWN")
        return EnvironmentType.UNKNOWN
    
    def _get_security_policy(self) -> SecurityPolicy:
        """Get security policy based on environment"""
        
        if self.environment == EnvironmentType.PRODUCTION:
            return SecurityPolicy(
                require_https=True,
                require_database_encryption=True,
                allow_demo_users=False,
                require_strong_api_keys=True,
                enable_audit_logging=True,
                require_environment_config=True,
                min_api_key_length=32,
                allowed_debug_features=[]
            )
        
        elif self.environment == EnvironmentType.STAGING:
            return SecurityPolicy(
                require_https=True,
                require_database_encryption=True,
                allow_demo_users=True,  # For testing
                require_strong_api_keys=True,
                enable_audit_logging=True,
                require_environment_config=True,
                min_api_key_length=24,
                allowed_debug_features=['sql_debug']
            )
        
        elif self.environment == EnvironmentType.DEVELOPMENT:
            return SecurityPolicy(
                require_https=False,
                require_database_encryption=False,  # Can be disabled for development
                allow_demo_users=True,
                require_strong_api_keys=False,
                enable_audit_logging=False,  # Optional in development
                require_environment_config=False,
                min_api_key_length=8,
                allowed_debug_features=['sql_debug', 'verbose_logging', 'test_endpoints']
            )
        
        else:
            # Unknown/testing - restrictive policy
            return SecurityPolicy(
                require_https=True,
                require_database_encryption=True,
                allow_demo_users=False,
                require_strong_api_keys=True,
                enable_audit_logging=True,
                require_environment_config=True,
                min_api_key_length=32,
                allowed_debug_features=[]
            )
    
    def _enforce_security_policy(self):
        """Enforce security policy requirements"""
        violations = []
        
        # Check HTTPS requirement
        if self.policy.require_https:
            enable_https = os.getenv('ENABLE_HTTPS', 'false').lower() == 'true'
            railway_url = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
            
            if not enable_https and not railway_url.startswith('https://'):
                if self.environment == EnvironmentType.PRODUCTION:
                    violations.append("HTTPS is required in production environment")
                else:
                    logger.warning("HTTPS is not enabled - this is required for production")
        
        # Check API key strength
        if self.policy.require_strong_api_keys:
            api_key = os.getenv('MVP_API_KEY', '')
            if len(api_key) < self.policy.min_api_key_length:
                if self.environment == EnvironmentType.PRODUCTION:
                    violations.append(f"API key must be at least {self.policy.min_api_key_length} characters in production")
                else:
                    logger.warning(f"API key should be at least {self.policy.min_api_key_length} characters for security")
        
        # Check database encryption
        if self.policy.require_database_encryption:
            disable_encryption = os.getenv('DISABLE_ENCRYPTION', 'false').lower() == 'true'
            if disable_encryption and self.environment == EnvironmentType.PRODUCTION:
                violations.append("Database encryption cannot be disabled in production")
        
        # Check required environment configuration
        if self.policy.require_environment_config:
            required_vars = ['DATABASE_URL', 'MVP_API_KEY', 'SESSION_SECRET']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars and self.environment == EnvironmentType.PRODUCTION:
                violations.append(f"Missing required environment variables in production: {', '.join(missing_vars)}")
        
        # Fail hard on production violations
        if violations:
            error_msg = f"Security policy violations in {self.environment.value} environment:\n" + "\n".join(f"- {v}" for v in violations)
            
            if self.environment == EnvironmentType.PRODUCTION:
                logger.critical(error_msg)
                raise SecurityError(error_msg)
            else:
                logger.warning(error_msg)
        
        logger.info(f"✅ Security policy enforcement completed for {self.environment.value}")
    
    def is_feature_allowed(self, feature: str) -> bool:
        """Check if a debug/development feature is allowed in current environment"""
        return feature in self.policy.allowed_debug_features
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        return {
            'environment': self.environment.value,
            'policy': {
                'require_https': self.policy.require_https,
                'require_database_encryption': self.policy.require_database_encryption,
                'allow_demo_users': self.policy.allow_demo_users,
                'require_strong_api_keys': self.policy.require_strong_api_keys,
                'enable_audit_logging': self.policy.enable_audit_logging,
                'min_api_key_length': self.policy.min_api_key_length,
                'allowed_debug_features': self.policy.allowed_debug_features
            },
            'environment_indicators': {
                'ENVIRONMENT': os.getenv('ENVIRONMENT'),
                'RAILWAY_ENVIRONMENT_NAME': os.getenv('RAILWAY_ENVIRONMENT_NAME'),
                'DEVELOPMENT_MODE': os.getenv('DEVELOPMENT_MODE'),
                'ENABLE_HTTPS': os.getenv('ENABLE_HTTPS'),
                'has_database_url': bool(os.getenv('DATABASE_URL'))
            }
        }
    
    def validate_api_key(self, api_key: Optional[str]) -> bool:
        """Validate API key according to current security policy"""
        if not api_key:
            return not self.policy.require_strong_api_keys
        
        return len(api_key) >= self.policy.min_api_key_length

class SecurityError(Exception):
    """Security policy violation error"""
    pass

# Global security manager instance
security_manager = SecurityManager()

def get_security_manager() -> SecurityManager:
    """Get the global security manager instance"""
    return security_manager

def is_production_environment() -> bool:
    """Check if running in production environment"""
    return security_manager.environment == EnvironmentType.PRODUCTION

def is_development_environment() -> bool:
    """Check if running in development environment"""
    return security_manager.environment == EnvironmentType.DEVELOPMENT

def enforce_production_security():
    """Enforce production security requirements - called at app startup"""
    security_manager._enforce_security_policy()

def get_environment_type() -> EnvironmentType:
    """Get current environment type"""
    return security_manager.environment