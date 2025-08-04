#!/usr/bin/env python3
"""
Google Classroom API Endpoints (Refactored)

Modular Google Classroom integration with focused sub-routers.
Replaces the monolithic 762-line google_classroom_endpoints.py file.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import logging

from .google_classroom.auth_endpoints import router as auth_router
from .google_classroom.course_endpoints import router as course_router
from .shared.google_deps import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create main router  
router = APIRouter()

# Include sub-routers
router.include_router(auth_router, prefix="/auth", tags=["Google Authentication"])
router.include_router(course_router, prefix="/courses", tags=["Google Courses"])

@router.get("/health")
async def google_classroom_health(current_user: dict = Depends(get_current_user)):
    """Health check for Google Classroom integration"""
    try:
        from .shared.google_deps import get_google_classroom_integration
        google_classroom = get_google_classroom_integration()
        
        return JSONResponse({
            'status': 'healthy',
            'authenticated': google_classroom.is_authenticated(),
            'service': 'google_classroom',
            'version': '2.0'
        })
        
    except Exception as e:
        logger.error(f"Google Classroom health check failed: {e}")
        raise HTTPException(status_code=503, detail="Google Classroom service unavailable")


# TODO: Add remaining endpoint modules:
# - student_endpoints.py (students/analyze, predict/enhanced)  
# - analytics_endpoints.py (analytics/cross-platform, insights/google-specific)
# - sync_endpoints.py (sync/comprehensive)
#
# This modular approach breaks the 762-line file into focused ~100-150 line modules
# making the code much more maintainable and testable.