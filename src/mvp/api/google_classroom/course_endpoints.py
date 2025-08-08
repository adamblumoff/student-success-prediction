#!/usr/bin/env python3
"""
Google Classroom Course Management Endpoints

Handles course operations, enrollment, and course-level data management.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from ..shared.google_deps import get_google_classroom_integration, get_current_user
from mvp.simple_auth import simple_rate_limit

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class CourseSyncRequest(BaseModel):
    """Request model for course synchronization"""
    course_ids: Optional[List[str]] = Field(None, description="Specific course IDs to sync")
    include_archived: bool = Field(False, description="Include archived courses")
    

@router.get("/")
async def get_courses(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get list of Google Classroom courses"""
    try:
        simple_rate_limit(request, 30)
        google_classroom = get_google_classroom_integration()
        
        if hasattr(google_classroom, 'is_authenticated') and not google_classroom.is_authenticated():
            raise HTTPException(status_code=401, detail="Google Classroom not authenticated")
        
        # Get courses
        courses = google_classroom.get_courses()
        
        # Format course data
        formatted_courses = []
        for course in courses:
            formatted_courses.append({
                'id': course.get('id'),
                'name': course.get('name'),
                'section': course.get('section', ''),
                'description': course.get('description', ''),
                'state': course.get('courseState', 'UNKNOWN'),
                'enrollment_count': course.get('enrollmentCode', 'N/A'),
                'creation_time': course.get('creationTime'),
                'update_time': course.get('updateTime')
            })
        
        return JSONResponse({
            'courses': formatted_courses,
            'total_count': len(formatted_courses),
            'message': f'Retrieved {len(formatted_courses)} courses'
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve courses: {str(e)}")


@router.post("/sync")
async def sync_courses(
    request: CourseSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Synchronize course data from Google Classroom"""
    try:
        google_classroom = get_google_classroom_integration()
        
        if not google_classroom.is_authenticated():
            raise HTTPException(status_code=401, detail="Google Classroom not authenticated")
        
        # Start background sync task
        background_tasks.add_task(
            _sync_courses_background,
            google_classroom,
            request.course_ids,
            request.include_archived
        )
        
        return JSONResponse({
            'status': 'sync_started',
            'message': 'Course synchronization started in background',
            'sync_scope': {
                'specific_courses': request.course_ids is not None,
                'course_count': len(request.course_ids) if request.course_ids else 'all',
                'include_archived': request.include_archived
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting course sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


async def _sync_courses_background(
    google_classroom,
    course_ids: Optional[List[str]] = None,
    include_archived: bool = False
):
    """Background task for course synchronization"""
    try:
        logger.info(f"Starting background course sync: {course_ids}")
        
        # Get courses to sync
        if course_ids:
            courses = []
            for course_id in course_ids:
                course = google_classroom.get_course(course_id)
                if course:
                    courses.append(course)
        else:
            courses = google_classroom.get_courses(include_archived=include_archived)
        
        logger.info(f"Syncing {len(courses)} courses")
        
        # Process each course
        for course in courses:
            try:
                # Get detailed course data
                course_details = google_classroom.get_course_details(course['id'])
                
                # Get students for this course
                students = google_classroom.get_course_students(course['id'])
                
                logger.info(f"Synced course '{course['name']}' with {len(students)} students")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as course_error:
                logger.error(f"Error syncing course {course.get('id')}: {course_error}")
                continue
        
        logger.info("Background course sync completed")
        
    except Exception as e:
        logger.error(f"Background course sync failed: {e}")