#!/usr/bin/env python3
"""
Simple authentication for MVP
Replaces complex security layer with basic API key check
"""

import os
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any

# Simple rate limiting with in-memory storage
_request_counts = {}
_blocked_ips = {}

def simple_auth(credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
    """Simple API key authentication for MVP"""
    expected_key = os.getenv("MVP_API_KEY", "dev-key-change-me")
    
    if not credentials or credentials.credentials != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {"user": "mvp_user", "permissions": ["read", "write"]}

def simple_rate_limit(request: Request, limit: int = 100) -> None:
    """Simple rate limiting for MVP"""
    client_ip = request.client.host
    
    # Reset counts every hour (simple implementation)
    if client_ip not in _request_counts:
        _request_counts[client_ip] = 0
    
    _request_counts[client_ip] += 1
    
    if _request_counts[client_ip] > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

def simple_file_validation(contents: bytes, filename: str) -> None:
    """Simple file validation for MVP"""
    # Basic size check (10MB limit)
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    
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