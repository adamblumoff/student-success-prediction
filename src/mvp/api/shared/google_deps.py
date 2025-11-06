#!/usr/bin/env python3
"""
Shared Google Classroom Dependencies

Provides common dependencies for Google Classroom API endpoints.
"""

from fastapi import Request, HTTPException, Depends
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from integrations.google_classroom import GoogleClassroomIntegration
from src.mvp.security import auth_dependency

# Global Google Classroom integration instance  
_google_classroom = None

def get_google_classroom_integration() -> GoogleClassroomIntegration:
    """Get or create Google Classroom integration instance"""
    global _google_classroom
    if _google_classroom is None:
        _google_classroom = GoogleClassroomIntegration()
    return _google_classroom

def get_current_user(current_user: dict = Depends(auth_dependency)):
    """Standardized authentication dependency for Google APIs."""
    return current_user
