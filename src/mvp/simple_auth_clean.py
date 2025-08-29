#!/usr/bin/env python3
"""
Clean, Simple Authentication for MVP
Single API key check with development mode bypass
"""

import os
import time
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, Any
from collections import defaultdict, deque

# Simple rate limiting (optional)
_rate_limit_storage = defaultdict(lambda: deque())
RATE_LIMIT_WINDOW = 60  # 1 minute window
MAX_REQUESTS_PER_MINUTE = 100  # More permissive for simplicity

# HTTPBearer for FastAPI dependency injection
security = HTTPBearer(auto_error=False)

def simple_auth_check(
    request: Request, 
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Simple API key authentication - one function, clear logic
    
    Returns user context dict on success, raises HTTPException on failure
    """
    
    # Development mode: allow localhost requests without auth
    if os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true':
        if request.client and request.client.host in ['127.0.0.1', 'localhost', '::1']:
            return {
                "user": "dev_user",
                "mode": "development",
                "permissions": ["read", "write"],
                "institution_id": 1
            }
    
    # Check for API key in Authorization header
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required - invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Validate API key
    expected_key = os.getenv("MVP_API_KEY", "dev-key-change-me")
    if credentials.credentials != expected_key:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required - invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Optional rate limiting (can be disabled by setting RATE_LIMIT_ENABLED=false)
    if os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true':
        try:
            apply_rate_limit(request)
        except HTTPException:
            raise  # Re-raise rate limit errors
        except Exception:
            pass  # Don't fail auth due to rate limiting errors
    
    # Return user context
    return {
        "user": "api_user",
        "mode": "api_key",
        "permissions": ["read", "write"],
        "institution_id": 1
    }

def apply_rate_limit(request: Request, limit: int = MAX_REQUESTS_PER_MINUTE):
    """Simple rate limiting - optional, can be disabled"""
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Get request history for this IP
    timestamps = _rate_limit_storage[client_ip]
    
    # Remove old requests outside the window
    while timestamps and current_time - timestamps[0] > RATE_LIMIT_WINDOW:
        timestamps.popleft()
    
    # Check if over limit
    if len(timestamps) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add current request
    timestamps.append(current_time)
    
    # Cleanup storage periodically
    if len(_rate_limit_storage) > 1000:
        cleanup_old_ips(current_time)

def cleanup_old_ips(current_time: float):
    """Remove IPs with no recent requests"""
    to_remove = []
    for ip, timestamps in _rate_limit_storage.items():
        if not timestamps or current_time - timestamps[-1] > RATE_LIMIT_WINDOW * 2:
            to_remove.append(ip)
    
    for ip in to_remove:
        del _rate_limit_storage[ip]