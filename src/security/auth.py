#!/usr/bin/env python3
"""
Authentication and authorization utilities
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles authentication and authorization"""
    
    def __init__(self):
        # Load from environment variables
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', self._generate_secret_key())
        self.jwt_algorithm = 'HS256'
        self.jwt_expiration_hours = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
        
        # API Keys (in production, store in database with hashing)
        self.api_keys = self._load_api_keys()
        
        # Rate limiting tracking
        self.failed_attempts = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        key = secrets.token_urlsafe(32)
        logger.warning("Using generated JWT secret key. Set JWT_SECRET_KEY environment variable for production.")
        return key
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from environment variables"""
        api_keys = {}
        
        # Admin API key
        admin_key = os.getenv('ADMIN_API_KEY')
        if admin_key:
            api_keys[self._hash_api_key(admin_key)] = {
                'role': 'admin',
                'permissions': ['read', 'write', 'admin'],
                'description': 'Admin access'
            }
        
        # Teacher API key
        teacher_key = os.getenv('TEACHER_API_KEY')
        if teacher_key:
            api_keys[self._hash_api_key(teacher_key)] = {
                'role': 'teacher',
                'permissions': ['read', 'write'],
                'description': 'Teacher access'
            }
        
        # Read-only API key
        readonly_key = os.getenv('READONLY_API_KEY')
        if readonly_key:
            api_keys[self._hash_api_key(readonly_key)] = {
                'role': 'readonly',
                'permissions': ['read'],
                'description': 'Read-only access'
            }
        
        # Fallback for development (remove in production)
        if not api_keys:
            if os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true':
                dev_key = 'dev-key-change-me'
                api_keys[self._hash_api_key(dev_key)] = {
                    'role': 'admin',
                    'permissions': ['read', 'write', 'admin'],
                    'description': 'Development key - CHANGE IN PRODUCTION'
                }
                logger.warning("Using development API key. Set proper API keys for production.")
            else:
                logger.error("No API keys configured and not in development mode. Set API key environment variables.")
        
        return api_keys
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _is_ip_locked_out(self, client_ip: str) -> bool:
        """Check if IP is locked out due to failed attempts"""
        if client_ip in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[client_ip]
            if attempts >= self.max_failed_attempts:
                if datetime.now() - last_attempt < self.lockout_duration:
                    return True
                else:
                    # Reset failed attempts after lockout period
                    del self.failed_attempts[client_ip]
        return False
    
    def _record_failed_attempt(self, client_ip: str) -> None:
        """Record a failed authentication attempt"""
        if client_ip in self.failed_attempts:
            attempts, _ = self.failed_attempts[client_ip]
            self.failed_attempts[client_ip] = (attempts + 1, datetime.now())
        else:
            self.failed_attempts[client_ip] = (1, datetime.now())
    
    def _clear_failed_attempts(self, client_ip: str) -> None:
        """Clear failed attempts for successful authentication"""
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]
    
    def validate_api_key(self, api_key: str, client_ip: str = "unknown") -> Dict[str, Any]:
        """Validate API key and return user info"""
        # Check if IP is locked out
        if self._is_ip_locked_out(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )
        
        # Hash the provided key
        key_hash = self._hash_api_key(api_key)
        
        # Check if key exists
        if key_hash not in self.api_keys:
            self._record_failed_attempt(client_ip)
            logger.warning(f"Invalid API key attempt from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Clear failed attempts on successful auth
        self._clear_failed_attempts(client_ip)
        
        # Return user info
        user_info = self.api_keys[key_hash].copy()
        user_info['authenticated'] = True
        user_info['client_ip'] = client_ip
        
        logger.info(f"Successful API key authentication: role={user_info['role']}, ip={client_ip}")
        return user_info
    
    def create_jwt_token(self, user_info: Dict[str, Any]) -> str:
        """Create JWT token for user"""
        payload = {
            'role': user_info['role'],
            'permissions': user_info['permissions'],
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
            'iat': datetime.utcnow(),
            'client_ip': user_info.get('client_ip', 'unknown')
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def validate_jwt_token(self, token: str, client_ip: str = "unknown") -> Dict[str, Any]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Optionally validate IP (comment out if clients change IPs frequently)
            # if payload.get('client_ip') != client_ip:
            #     raise HTTPException(
            #         status_code=status.HTTP_401_UNAUTHORIZED,
            #         detail="Token IP mismatch"
            #     )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def check_permission(self, user_info: Dict[str, Any], required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in user_info.get('permissions', [])
    
    def require_permission(self, user_info: Dict[str, Any], required_permission: str) -> None:
        """Require specific permission or raise exception"""
        if not self.check_permission(user_info, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )

# Global instance
security_manager = SecurityManager()

# FastAPI dependency for API key authentication
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    try:
        # First try JWT token validation
        user_info = security_manager.validate_jwt_token(credentials.credentials)
        return user_info
    except HTTPException:
        # Fallback to API key validation
        user_info = security_manager.validate_api_key(credentials.credentials)
        return user_info

async def require_read_permission(user: Dict[str, Any] = Security(get_current_user)) -> Dict[str, Any]:
    """Require read permission"""
    security_manager.require_permission(user, 'read')
    return user

async def require_write_permission(user: Dict[str, Any] = Security(get_current_user)) -> Dict[str, Any]:
    """Require write permission"""
    security_manager.require_permission(user, 'write')
    return user

async def require_admin_permission(user: Dict[str, Any] = Security(get_current_user)) -> Dict[str, Any]:
    """Require admin permission"""
    security_manager.require_permission(user, 'admin')
    return user