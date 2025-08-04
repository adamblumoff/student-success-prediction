#!/usr/bin/env python3
"""
Shared Google Classroom Dependencies

Provides common dependencies for Google Classroom API endpoints.
"""

from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from integrations.google_classroom import GoogleClassroomIntegration
from mvp.simple_auth import simple_auth

# Global Google Classroom integration instance  
_google_classroom = None

def get_google_classroom_integration() -> GoogleClassroomIntegration:
    """Get or create Google Classroom integration instance"""
    global _google_classroom
    if _google_classroom is None:
        _google_classroom = GoogleClassroomIntegration()
    return _google_classroom

def get_current_user(request: Request):
    """Simple authentication dependency"""
    # Check for Authorization header
    auth_header = request.headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return simple_auth(credentials)
    
    # For development/demo mode, allow requests from localhost without auth
    import os
    if os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true':
        client_host = request.client.host if request.client else 'unknown'
        if client_host in ['127.0.0.1', 'localhost', '::1']:
            return {"user": "demo_user", "permissions": ["read", "write"]}
    
    # Fallback: Allow web browser requests
    user_agent = request.headers.get('user-agent', '').lower()
    if any(browser in user_agent for browser in ['mozilla', 'chrome', 'safari', 'firefox', 'edge']):
        return {"user": "browser_user", "permissions": ["read", "write"]}
    
    raise HTTPException(status_code=401, detail="Authentication required")