#!/usr/bin/env python3
"""
Simple authentication for MVP
Replaces complex security layer with basic API key check
"""

import os
import time
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any
from collections import defaultdict, deque
from fastapi import Depends
from sqlalchemy.orm import Session
import time

# Rate limiting with time-based sliding windows
_rate_limit_storage = defaultdict(lambda: deque())
_blocked_ips = {}
RATE_LIMIT_WINDOW = 60  # 1 minute window
MAX_REQUESTS_PER_MINUTE = 60  # Default limit

def validate_security_configuration_on_startup() -> Dict[str, str]:
    """
    Validate security configuration on startup
    Ensures production systems have proper security settings
    """
    result = {}
    
    # Validate development mode setting
    dev_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower()
    if dev_mode == 'true':
        print("⚠️  WARNING: Development mode is ENABLED - authentication bypass allowed for localhost")
        if os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']:
            raise ValueError("❌ SECURITY ERROR: DEVELOPMENT_MODE cannot be 'true' in production environment")
    else:
        print("✅ Development mode is DISABLED - full authentication required")
    
    result['development_mode'] = dev_mode
    
    # Validate API key
    result['api_key'] = validate_api_key()
    
    return result

def validate_api_key() -> str:
    """
    Validate API key configuration on startup
    Ensures production systems don't use insecure default keys
    """
    api_key = os.getenv("MVP_API_KEY")
    
    # Check for missing API key
    if not api_key:
        if os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true':
            print("⚠️  WARNING: No API key set, using development default")
            return "dev-key-change-me"
        else:
            raise ValueError("❌ SECURITY ERROR: MVP_API_KEY environment variable must be set in production")
    
    # Check for insecure default key in non-development environments
    if api_key == "dev-key-change-me":
        if os.getenv('DEVELOPMENT_MODE', 'false').lower() != 'true':
            raise ValueError("❌ SECURITY ERROR: Cannot use default API key 'dev-key-change-me' in production")
        else:
            print("⚠️  WARNING: Using development API key")
    
    # Check key strength (minimum requirements)
    if len(api_key) < 16:
        raise ValueError("❌ SECURITY ERROR: API key must be at least 16 characters long")
    
    if api_key.isalnum() and len(set(api_key)) < 8:
        print(f"⚠️  WARNING: API key may be weak (low entropy)")
    
    print(f"✅ API key validated: {api_key[:8]}***")
    return api_key

def simple_auth(credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
    """Simple API key authentication for MVP with institution context"""
    expected_key = os.getenv("MVP_API_KEY", "dev-key-change-me")
    
    if not credentials or credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="Authentication required - invalid API key")
    
    # For MVP, use default institution ID 1 (can be extended for multi-tenant)
    default_institution_id = int(os.getenv("DEFAULT_INSTITUTION_ID", "1"))
    
    return {
        "user": "mvp_user", 
        "permissions": ["read", "write"],
        "institution_id": default_institution_id,
        "user_id": "mvp_user_001",
        "role": "educator"
    }

def get_current_user_secure(
    request: Request,
    credentials: HTTPAuthorizationCredentials,
    db: Session = None
) -> Dict[str, Any]:
    """Enhanced authentication with database security context setup"""
    # First, apply rate limiting
    simple_rate_limit(request)
    
    # Perform authentication
    user_info = simple_auth(credentials)
    
    # Set up database security context and audit logging if database session provided
    if db is not None:
        try:
            from .database_security import db_security
            from .audit_logger import audit_logger
            
            # Set institution context for row-level security
            success = db_security.set_institution_context(
                session=db,
                institution_id=user_info["institution_id"],
                user_id=user_info["user_id"],
                ip_address=request.client.host if request.client else "unknown"
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to establish secure database context")
            
            # Log successful authentication for audit trail
            request_context = {
                'ip_address': request.client.host if request.client else "unknown",
                'user_agent': request.headers.get('user-agent', 'unknown'),
                'session_id': f"session_{int(time.time())}"
            }
            
            audit_logger.log_event(
                session=db,
                action="USER_AUTHENTICATION",
                resource_type="authentication",
                user_context=user_info,
                request_context=request_context,
                details={'authentication_method': 'api_key'},
                compliance_data={
                    'ferpa_compliance': True,
                    'audit_category': 'authentication',
                    'security_level': 'standard'
                }
            )
                
        except ImportError:
            # Database security module not available (development mode)
            pass
        except Exception as e:
            # Log error but don't fail authentication in MVP mode
            print(f"⚠️  Warning: Database security context setup failed: {e}")
    
    return user_info

def simple_rate_limit(request: Request, limit: int = MAX_REQUESTS_PER_MINUTE) -> None:
    """
    Time-based sliding window rate limiting for MVP
    Allows 'limit' requests per minute per IP address
    """
    if os.getenv('TESTING', 'false').lower() == 'true':
        # Skip rate limiting during tests
        return
    
    client_ip = request.client.host
    current_time = time.time()
    
    # Get the request timestamps for this IP
    timestamps = _rate_limit_storage[client_ip]
    
    # Remove timestamps older than the window
    while timestamps and current_time - timestamps[0] > RATE_LIMIT_WINDOW:
        timestamps.popleft()
    
    # Check if we're over the limit
    if len(timestamps) >= limit:
        # Calculate time until oldest request expires
        time_to_wait = RATE_LIMIT_WINDOW - (current_time - timestamps[0])
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Try again in {int(time_to_wait)} seconds"
        )
    
    # Add current request timestamp
    timestamps.append(current_time)
    
    # Optional: Clean up storage for IPs with no recent requests
    if len(_rate_limit_storage) > 1000:  # Prevent memory bloat
        _cleanup_old_entries(current_time)

def _cleanup_old_entries(current_time: float) -> None:
    """Clean up rate limiting storage for IPs with no recent requests"""
    to_remove = []
    for ip, timestamps in _rate_limit_storage.items():
        if not timestamps or current_time - timestamps[-1] > RATE_LIMIT_WINDOW * 2:
            to_remove.append(ip)
    
    for ip in to_remove:
        del _rate_limit_storage[ip]

def simple_file_validation(contents: bytes, filename: str) -> None:
    """Simple file validation for MVP"""
    # Basic size check (configurable via MAX_FILE_SIZE_MB, default 10MB)
    try:
        max_mb = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    except ValueError:
        max_mb = 10
    if len(contents) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {max_mb}MB)")
    
    # Basic CSV check
    if not filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    # Basic content check
    try:
        content_str = contents.decode('utf-8')
        if len(content_str.strip()) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding")