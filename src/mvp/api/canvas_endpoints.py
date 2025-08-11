#!/usr/bin/env python3
"""
Canvas LMS Integration API Endpoints

Handles Canvas LMS connection, course management, and real-time gradebook
synchronization for student success prediction.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
import sys
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from mvp.security import get_current_user_secure as get_current_user
from mvp.database import save_predictions_batch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/canvas", tags=["Canvas LMS"])

@router.get("/health")
async def canvas_health():
    return JSONResponse({
        'status': 'healthy',
        'service': 'Canvas LMS Integration'
    })

@router.get("/courses")
async def get_canvas_courses_get(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """GET variant to satisfy tests calling GET /api/lms/canvas/courses"""
    try:
        body = {'base_url': request.headers.get('X-Canvas-URL', ''),
                'access_token': request.headers.get('X-Canvas-Token', '')}
        if not body['base_url'] or not body['access_token']:
            raise HTTPException(status_code=401, detail="Canvas credentials required")
        from integrations.canvas_lms import create_canvas_integration
        canvas = create_canvas_integration(body['base_url'], body['access_token'])
        courses = canvas.get_courses(include_students=False)
        return JSONResponse({'status': 'success', 'courses': courses, 'total_courses': len(courses)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Canvas courses (GET): {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")
@router.post("/connect")
async def connect_canvas_lms(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Connect to Canvas LMS and test authentication"""
    try:
        body = await request.json()
        base_url = body.get('base_url', '').strip()
        access_token = body.get('access_token', '').strip()
        
        if not base_url or not access_token:
            raise HTTPException(status_code=400, detail="Canvas URL and access token are required")
        
        # Import Canvas integration
        from integrations.canvas_lms import create_canvas_integration
        
        # Create Canvas integration
        canvas = create_canvas_integration(base_url, access_token)
        
        # Test connection
        connection_result = canvas.test_connection()
        
        if connection_result['status'] == 'success':
            # Store connection details in session (simplified for MVP)
            # In production, this would be encrypted and stored securely
            return JSONResponse({
                'status': 'success',
                'message': 'Successfully connected to Canvas LMS',
                'account_info': {
                    'name': connection_result.get('account_name'),
                    'accessible_courses': connection_result.get('accessible_courses', 0),
                    'rate_limit_remaining': connection_result.get('rate_limit_remaining', 0)
                },
                'permissions': connection_result.get('permissions', {})
            })
        else:
            raise HTTPException(status_code=400, detail=f"Canvas connection failed: {connection_result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to Canvas: {e}")
        raise HTTPException(status_code=500, detail=f"Canvas connection error: {str(e)}")

@router.post("/courses")
async def get_canvas_courses(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get list of courses from Canvas LMS"""
    try:
        body = await request.json()
        base_url = body.get('base_url', '').strip()
        access_token = body.get('access_token', '').strip()
        
        if not base_url or not access_token:
            raise HTTPException(status_code=400, detail="Canvas credentials required")
        
        from integrations.canvas_lms import create_canvas_integration
        canvas = create_canvas_integration(base_url, access_token)
        
        # Get courses
        courses = canvas.get_courses(include_students=False)
        
        return JSONResponse({
            'status': 'success',
            'courses': courses,
            'total_courses': len(courses)
        })
        
    except Exception as e:
        logger.error(f"Error fetching Canvas courses: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@router.post("/sync")
async def sync_canvas_course(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Sync Canvas course data and generate predictions"""
    try:
        body = await request.json()
        base_url = body.get('base_url', '').strip()
        access_token = body.get('access_token', '').strip()
        course_id = body.get('course_id', '').strip()
        
        if not all([base_url, access_token, course_id]):
            raise HTTPException(status_code=400, detail="Canvas URL, access token, and course ID are required")
        
        from integrations.canvas_lms import create_canvas_integration
        canvas = create_canvas_integration(base_url, access_token)
        
        # Sync course data and generate predictions
        sync_result = canvas.sync_course_data(course_id)
        
        if sync_result['status'] == 'success':
            # Save predictions to database if available
            try:
                session_id = f"canvas_{course_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if sync_result['predictions']:
                    save_predictions_batch(sync_result['predictions'], session_id)
                    logger.info(f"Saved {len(sync_result['predictions'])} Canvas predictions to database")
            except Exception as db_error:
                logger.warning(f"Could not save Canvas predictions to database: {db_error}")
            
            # Generate summary statistics
            predictions = sync_result['predictions']
            if predictions:
                total_students = len(predictions)
                high_risk = sum(1 for p in predictions if p.get('risk_level') == 'danger')
                moderate_risk = sum(1 for p in predictions if p.get('risk_level') == 'warning') 
                low_risk = sum(1 for p in predictions if p.get('risk_level') == 'success')
                
                avg_gpa = sum(p.get('current_gpa', 0) for p in predictions) / total_students if total_students > 0 else 0
                avg_attendance = sum(p.get('attendance_rate', 0) for p in predictions) / total_students if total_students > 0 else 0
                
                sync_result['summary'] = {
                    'total_students': total_students,
                    'risk_distribution': {
                        'high_risk': high_risk,
                        'moderate_risk': moderate_risk,
                        'low_risk': low_risk
                    },
                    'class_averages': {
                        'gpa': round(avg_gpa, 2),
                        'attendance': round(avg_attendance * 100, 1)
                    }
                }
            
            return JSONResponse(sync_result)
        else:
            raise HTTPException(status_code=400, detail=f"Canvas sync failed: {sync_result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing Canvas course: {e}")
        raise HTTPException(status_code=500, detail=f"Canvas sync error: {str(e)}")

@router.get("/student/{course_id}/{student_id}")
async def get_canvas_student_details(
    course_id: str,
    student_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed Canvas student information"""
    try:
        # Get Canvas credentials from request headers (simplified for MVP)
        base_url = request.headers.get('X-Canvas-URL')
        access_token = request.headers.get('X-Canvas-Token')
        
        if not base_url or not access_token:
            raise HTTPException(status_code=400, detail="Canvas credentials required in headers")
        
        from integrations.canvas_lms import create_canvas_integration
        canvas = create_canvas_integration(base_url, access_token)
        
        # Get detailed student grades
        grade_data = canvas.get_student_grades(course_id, student_id)
        
        return JSONResponse({
            'status': 'success',
            'student_data': grade_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching Canvas student details: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching student details: {str(e)}")