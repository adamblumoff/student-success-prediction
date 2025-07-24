#!/usr/bin/env python3
"""
Canvas LMS API endpoints for Student Success Prediction System

Provides endpoints for Canvas OAuth2 integration and data synchronization
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import logging
import os
import secrets
import json
from datetime import datetime
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent))

from integrations.canvas import CanvasIntegration, CanvasClient, AuthenticationError, APIError
from security.auth import require_write_permission, require_admin_permission
from security.rate_limiter import rate_limiter
from models.intervention_system import InterventionRecommendationSystem

logger = logging.getLogger(__name__)

# Create router for Canvas endpoints
canvas_router = APIRouter(prefix="/canvas", tags=["canvas"])

# Pydantic models
class CanvasConfig(BaseModel):
    base_url: str = Field(..., description="Canvas instance URL (e.g., https://school.instructure.com)")
    client_id: str = Field(..., description="Canvas Developer Key Client ID")
    client_secret: str = Field(..., description="Canvas Developer Key Secret")
    redirect_uri: str = Field(..., description="OAuth2 redirect URI")

class CanvasCourse(BaseModel):
    id: int
    name: str
    course_code: str
    enrollment_term_id: Optional[int]
    start_at: Optional[str]
    end_at: Optional[str]
    total_students: Optional[int]

class CanvasStudent(BaseModel):
    id: int
    name: str
    sortable_name: str
    short_name: str
    email: Optional[str]
    login_id: Optional[str]

class CanvasSyncResult(BaseModel):
    course_id: str
    course_name: str
    students_synced: int
    assignments_found: int
    risk_predictions: List[Dict[str, Any]]
    high_risk_count: int
    sync_timestamp: str

# Global Canvas integration instance (will be configured per institution)
canvas_integration: Optional[CanvasIntegration] = None

def get_canvas_integration() -> CanvasIntegration:
    """Get configured Canvas integration instance"""
    global canvas_integration
    if not canvas_integration:
        # Load from environment variables
        base_url = os.getenv('CANVAS_BASE_URL')
        client_id = os.getenv('CANVAS_CLIENT_ID') 
        client_secret = os.getenv('CANVAS_CLIENT_SECRET')
        redirect_uri = os.getenv('CANVAS_REDIRECT_URI')
        
        if not all([base_url, client_id, client_secret, redirect_uri]):
            raise HTTPException(
                status_code=503,
                detail="Canvas integration not configured. Set CANVAS_BASE_URL, CANVAS_CLIENT_ID, CANVAS_CLIENT_SECRET, and CANVAS_REDIRECT_URI environment variables."
            )
        
        canvas_integration = CanvasIntegration(base_url, client_id, client_secret, redirect_uri)
    
    return canvas_integration

@canvas_router.post("/configure")
async def configure_canvas(
    config: CanvasConfig,
    current_user: dict = Depends(require_admin_permission)
):
    """Configure Canvas integration (Admin only)"""
    global canvas_integration
    
    try:
        canvas_integration = CanvasIntegration(
            base_url=config.base_url,
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri
        )
        
        logger.info(f"Canvas integration configured for {config.base_url}")
        return {
            "status": "configured",
            "canvas_url": config.base_url,
            "message": "Canvas integration configured successfully"
        }
        
    except Exception as e:
        logger.error(f"Canvas configuration failed: {e}")
        raise HTTPException(status_code=400, detail=f"Configuration failed: {str(e)}")

@canvas_router.get("/auth/url")
async def get_auth_url(
    request: Request,
    current_user: dict = Depends(require_write_permission)
):
    """Get Canvas OAuth2 authorization URL"""
    try:
        canvas = get_canvas_integration()
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session (in production, use Redis or database)
        # For now, we'll include it in the response for client-side handling
        
        auth_url = canvas.get_authorization_url(state=state)
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "instructions": "Visit the authorization URL to grant access to Canvas"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate Canvas auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Auth URL generation failed: {str(e)}")

@canvas_router.post("/auth/callback")
async def handle_auth_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Canvas"),
    state: str = Query(None, description="State parameter for CSRF protection"),
    current_user: dict = Depends(require_write_permission)
):
    """Handle Canvas OAuth2 callback and exchange code for token"""
    try:
        canvas = get_canvas_integration()
        
        # In production, verify state parameter against session
        # For now, we'll skip state verification but log it
        if state:
            logger.info(f"OAuth callback received with state: {state[:10]}...")
        
        # Exchange authorization code for access token
        token_response = await canvas.authenticate(code)
        
        logger.info("Canvas authentication successful")
        return {
            "status": "authenticated",
            "message": "Successfully connected to Canvas",
            "token_info": {
                "expires_at": canvas.token_expires_at.isoformat() if canvas.token_expires_at else None,
                "scopes": token_response.get('scope', 'unknown')
            }
        }
        
    except AuthenticationError as e:
        logger.error(f"Canvas authentication failed: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        raise HTTPException(status_code=500, detail=f"Callback handling failed: {str(e)}")

@canvas_router.get("/courses")
async def get_canvas_courses(
    request: Request,
    current_user: dict = Depends(require_write_permission)
) -> List[CanvasCourse]:
    """Get list of Canvas courses for the authenticated user"""
    try:
        # Rate limiting
        rate_limiter.enforce_rate_limit(request, 'analysis')
        
        canvas = get_canvas_integration()
        
        courses_data = await canvas.get_courses()
        
        # Convert to response format
        courses = []
        for course in courses_data:
            courses.append(CanvasCourse(
                id=course['id'],
                name=course['name'],
                course_code=course.get('course_code', ''),
                enrollment_term_id=course.get('enrollment_term_id'),
                start_at=course.get('start_at'),
                end_at=course.get('end_at'),
                total_students=course.get('total_students', 0)
            ))
        
        logger.info(f"Retrieved {len(courses)} Canvas courses")
        return courses
        
    except APIError as e:
        logger.error(f"Failed to get Canvas courses: {e}")
        raise HTTPException(status_code=502, detail=f"Canvas API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting Canvas courses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get courses: {str(e)}")

@canvas_router.get("/courses/{course_id}/students")
async def get_course_students(
    course_id: str,
    request: Request,
    current_user: dict = Depends(require_write_permission)
) -> List[CanvasStudent]:
    """Get list of students in a Canvas course"""
    try:
        # Rate limiting
        rate_limiter.enforce_rate_limit(request, 'analysis')
        
        canvas = get_canvas_integration()
        
        students_data = await canvas.get_course_students(course_id)
        
        # Convert to response format
        students = []
        for student in students_data:
            students.append(CanvasStudent(
                id=student['id'],
                name=student['name'],
                sortable_name=student['sortable_name'],
                short_name=student['short_name'],
                email=student.get('email'),
                login_id=student.get('login_id')
            ))
        
        logger.info(f"Retrieved {len(students)} students from Canvas course {course_id}")
        return students
        
    except APIError as e:
        logger.error(f"Failed to get Canvas course students: {e}")
        raise HTTPException(status_code=502, detail=f"Canvas API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting course students: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get students: {str(e)}")

@canvas_router.post("/courses/{course_id}/sync")
async def sync_course_for_prediction(
    course_id: str,
    request: Request,
    current_user: dict = Depends(require_write_permission)
) -> CanvasSyncResult:
    """Sync Canvas course data and generate risk predictions"""
    try:
        # Rate limiting for intensive operations
        rate_limiter.enforce_rate_limit(request, 'analysis')
        
        canvas = get_canvas_integration()
        
        # Sync complete course data
        logger.info(f"Starting Canvas course sync for course {course_id}")
        course_data = await canvas.sync_course_data(course_id)
        
        # Convert to prediction format
        prediction_df = canvas.convert_to_prediction_format(course_data)
        
        if prediction_df.empty:
            raise HTTPException(status_code=400, detail="No student data available for prediction")
        
        # Generate risk predictions
        intervention_system = InterventionRecommendationSystem()
        risk_results = intervention_system.assess_student_risk(prediction_df)
        
        # Format results
        predictions = []
        high_risk_count = 0
        
        for _, row in risk_results.iterrows():
            prediction = {
                'student_id': int(row['id_student']),
                'risk_score': float(row['risk_score']),
                'risk_category': row['risk_category'],
                'success_probability': float(row['success_probability']),
                'needs_intervention': bool(row['needs_intervention'])
            }
            predictions.append(prediction)
            
            if row['risk_category'] == 'High Risk':
                high_risk_count += 1
        
        # Save results to database if available
        # (This would integrate with our existing database system)
        
        sync_result = CanvasSyncResult(
            course_id=course_id,
            course_name=course_data['course']['name'],
            students_synced=len(prediction_df),
            assignments_found=len(course_data.get('assignments', [])),
            risk_predictions=predictions,
            high_risk_count=high_risk_count,
            sync_timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Canvas sync completed: {len(predictions)} students analyzed, {high_risk_count} high risk")
        return sync_result
        
    except APIError as e:
        logger.error(f"Canvas sync failed: {e}")
        raise HTTPException(status_code=502, detail=f"Canvas API error: {str(e)}")
    except Exception as e:
        logger.error(f"Course sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@canvas_router.get("/courses/{course_id}/analytics")
async def get_course_analytics(
    course_id: str,
    request: Request,
    current_user: dict = Depends(require_write_permission)
):
    """Get Canvas course analytics data"""
    try:
        # Rate limiting
        rate_limiter.enforce_rate_limit(request, 'analysis')
        
        canvas = get_canvas_integration()
        
        analytics_data = await canvas.get_course_analytics(course_id)
        
        return {
            "course_id": course_id,
            "analytics": analytics_data,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except APIError as e:
        logger.error(f"Failed to get Canvas analytics: {e}")
        raise HTTPException(status_code=502, detail=f"Canvas API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting course analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

@canvas_router.get("/status")
async def canvas_integration_status(
    current_user: dict = Depends(require_write_permission)
):
    """Get Canvas integration status"""
    try:
        canvas = get_canvas_integration()
        
        return {
            "status": "configured",
            "base_url": canvas.base_url,
            "authenticated": canvas.is_token_valid(),
            "token_expires_at": canvas.token_expires_at.isoformat() if canvas.token_expires_at else None
        }
        
    except HTTPException as e:
        # Integration not configured
        return {
            "status": "not_configured",
            "error": e.detail
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# Cleanup function for integration
async def cleanup_canvas_integration():
    """Cleanup Canvas integration resources"""
    global canvas_integration
    if canvas_integration:
        await canvas_integration.close()
        canvas_integration = None