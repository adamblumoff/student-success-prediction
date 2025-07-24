#!/usr/bin/env python3
"""
Canvas LMS Integration for Student Success Prediction System

Provides comprehensive integration with Canvas LMS including:
- OAuth2 authentication
- Course and student data retrieval
- Gradebook access and analysis
- Real-time webhook support
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import logging
from urllib.parse import urlencode
import json

from .base import BaseLMSIntegration, AuthenticationError, APIError, DataConversionError

logger = logging.getLogger(__name__)

class CanvasIntegration(BaseLMSIntegration):
    """Canvas LMS Integration with OAuth2 authentication and comprehensive API access"""
    
    def __init__(self, base_url: str, client_id: str, client_secret: str, redirect_uri: str = None):
        super().__init__(base_url, client_id, client_secret)
        self.redirect_uri = redirect_uri
        self.api_base = f"{self.base_url}/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def get_authorization_url(self, state: str = None, scopes: List[str] = None) -> str:
        """
        Generate Canvas OAuth2 authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            scopes: List of Canvas scopes to request
            
        Returns:
            Authorization URL for Canvas OAuth2 flow
        """
        if not self.redirect_uri:
            raise ValueError("redirect_uri is required for OAuth2 flow")
        
        # Default Canvas scopes for student success prediction
        if scopes is None:
            scopes = [
                'url:GET|/api/v1/courses',
                'url:GET|/api/v1/courses/:course_id/students',
                'url:GET|/api/v1/courses/:course_id/assignments',
                'url:GET|/api/v1/courses/:course_id/analytics',
                'url:GET|/api/v1/courses/:course_id/enrollments',
                'url:GET|/api/v1/users/:user_id/courses'
            ]
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes)
        }
        
        if state:
            params['state'] = state
            
        return f"{self.base_url}/login/oauth2/auth?{urlencode(params)}"
    
    async def authenticate(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            authorization_code: Authorization code from Canvas OAuth2 callback
            
        Returns:
            Token response with access_token, refresh_token, etc.
        """
        session = await self._get_session()
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': authorization_code
        }
        
        try:
            async with session.post(
                f"{self.base_url}/login/oauth2/token",
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise AuthenticationError(f"Token exchange failed: {error_text}")
                
                token_response = await response.json()
                
                # Store token information
                self.access_token = token_response.get('access_token')
                if 'expires_in' in token_response:
                    self.token_expires_at = datetime.now() + timedelta(seconds=token_response['expires_in'])
                
                logger.info("Canvas authentication successful")
                return token_response
                
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Network error during authentication: {e}")
    
    async def refresh_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using refresh token
        Note: Canvas tokens typically don't expire, so this may not be needed
        """
        # Canvas access tokens typically don't expire
        # This method is here for interface compliance
        logger.info("Canvas tokens typically don't expire, refresh not needed")
        return {"status": "no_refresh_needed"}
    
    async def _make_api_request(
        self, 
        endpoint: str, 
        method: str = 'GET', 
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to Canvas
        
        Args:
            endpoint: API endpoint (without /api/v1 prefix)
            method: HTTP method
            params: Query parameters
            data: Request body data
            
        Returns:
            API response data
        """
        await self.ensure_authenticated()
        session = await self._get_session()
        
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data if data else None
            ) as response:
                if response.status == 401:
                    raise AuthenticationError("Access token is invalid or expired")
                elif response.status not in (200, 201):
                    error_text = await response.text()
                    raise APIError(f"API request failed ({response.status}): {error_text}")
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise APIError(f"Network error during API request: {e}")
    
    async def get_courses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of courses for the authenticated user or specific user
        
        Args:
            user_id: Optional user ID, defaults to current user
            
        Returns:
            List of course objects
        """
        if user_id:
            endpoint = f"users/{user_id}/courses"
        else:
            endpoint = "courses"
        
        params = {
            'enrollment_state': 'active',
            'include': ['total_students', 'teachers', 'term'],
            'per_page': 100
        }
        
        courses = []
        page = 1
        
        while True:
            params['page'] = page
            response = await self._make_api_request(endpoint, params=params)
            
            if not response:
                break
                
            courses.extend(response)
            
            if len(response) < 100:  # Last page
                break
            page += 1
        
        logger.info(f"Retrieved {len(courses)} courses from Canvas")
        return courses
    
    async def get_course_students(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get list of students enrolled in a course
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            List of student objects with enrollment information
        """
        endpoint = f"courses/{course_id}/users"
        params = {
            'enrollment_type[]': 'student',
            'enrollment_state[]': 'active',
            'include[]': ['enrollments', 'email', 'avatar_url'],
            'per_page': 100
        }
        
        students = []
        page = 1
        
        while True:
            params['page'] = page
            response = await self._make_api_request(endpoint, params=params)
            
            if not response:
                break
                
            students.extend(response)
            
            if len(response) < 100:  # Last page
                break
            page += 1
        
        logger.info(f"Retrieved {len(students)} students from course {course_id}")
        return students
    
    async def get_course_assignments(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get list of assignments for a course
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            List of assignment objects
        """
        endpoint = f"courses/{course_id}/assignments"
        params = {
            'include[]': ['submission', 'score_statistics'],
            'per_page': 100
        }
        
        assignments = []
        page = 1
        
        while True:
            params['page'] = page
            response = await self._make_api_request(endpoint, params=params)
            
            if not response:
                break
                
            assignments.extend(response)
            
            if len(response) < 100:  # Last page
                break
            page += 1
        
        logger.info(f"Retrieved {len(assignments)} assignments from course {course_id}")
        return assignments
    
    async def get_student_grades(self, course_id: str, student_id: str) -> Dict[str, Any]:
        """
        Get grades for a specific student in a course
        
        Args:
            course_id: Canvas course ID
            student_id: Canvas user ID
            
        Returns:
            Student grade information
        """
        endpoint = f"courses/{course_id}/students/submissions"
        params = {
            'student_ids[]': student_id,
            'include[]': ['assignment', 'submission_history', 'rubric_assessment'],
            'per_page': 100
        }
        
        submissions = []
        page = 1
        
        while True:
            params['page'] = page
            response = await self._make_api_request(endpoint, params=params)
            
            if not response:
                break
                
            submissions.extend(response)
            
            if len(response) < 100:  # Last page
                break
            page += 1
        
        # Calculate summary statistics
        total_points = 0
        earned_points = 0
        submitted_count = 0
        missing_count = 0
        
        for submission in submissions:
            if submission.get('score') is not None:
                earned_points += submission['score']
                submitted_count += 1
            else:
                missing_count += 1
            
            if submission.get('assignment', {}).get('points_possible'):
                total_points += submission['assignment']['points_possible']
        
        current_grade = (earned_points / total_points * 100) if total_points > 0 else 0
        
        return {
            'student_id': student_id,
            'course_id': course_id,
            'current_grade': current_grade,
            'total_points_possible': total_points,
            'total_points_earned': earned_points,
            'assignments_submitted': submitted_count,
            'assignments_missing': missing_count,
            'submissions': submissions
        }
    
    async def get_course_analytics(self, course_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a course
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            Course analytics data
        """
        try:
            # Get course-level analytics
            endpoint = f"courses/{course_id}/analytics/activity"
            activity_data = await self._make_api_request(endpoint)
            
            # Get student summaries
            endpoint = f"courses/{course_id}/analytics/student_summaries"
            student_summaries = await self._make_api_request(endpoint)
            
            return {
                'course_id': course_id,
                'activity_data': activity_data,
                'student_summaries': student_summaries,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except APIError as e:
            # Analytics may not be available for all courses
            logger.warning(f"Analytics not available for course {course_id}: {e}")
            return {
                'course_id': course_id,
                'error': 'Analytics not available',
                'retrieved_at': datetime.now().isoformat()
            }
    
    def convert_to_prediction_format(self, course_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert Canvas course data to the format expected by our prediction system
        
        Args:
            course_data: Dictionary containing course, students, assignments, and grades data
            
        Returns:
            DataFrame in prediction system format
        """
        try:
            students = course_data.get('students', [])
            grades_data = course_data.get('grades', {})
            assignments = course_data.get('assignments', [])
            
            prediction_data = []
            
            for student in students:
                student_id = student['id']
                student_grades = grades_data.get(str(student_id), {})
                
                # Extract basic student info
                row = {
                    'id_student': student_id,
                    'code_module': course_data.get('course', {}).get('course_code', 'UNKNOWN'),
                    'code_presentation': course_data.get('course', {}).get('term', {}).get('name', '2024'),
                    
                    # Demographics (Canvas doesn't provide much demographic data)
                    'gender_encoded': 0,  # Unknown
                    'region_encoded': 0,  # Unknown
                    'age_band_encoded': 1,  # Unknown, assume middle age
                    'education_encoded': 2,  # Unknown, assume some higher ed
                    'is_male': 0,  # Unknown
                    'has_disability': 0,  # Unknown
                    'studied_credits': 120,  # Default assumption
                    'num_of_prev_attempts': 0,  # Unknown
                    'registration_delay': 0.0,
                    'unregistered': 0
                }
                
                # Calculate assessment features from Canvas grades
                if student_grades and student_grades.get('submissions'):
                    submissions = student_grades['submissions']
                    scores = [s['score'] for s in submissions if s.get('score') is not None]
                    
                    if scores:
                        row.update({
                            'early_avg_score': sum(scores) / len(scores),
                            'early_min_score': min(scores),
                            'early_max_score': max(scores),
                            'early_score_std': pd.Series(scores).std() if len(scores) > 1 else 0,
                            'early_submitted_count': len(scores),
                            'early_assessments_count': len(assignments),
                            'early_missing_submissions': student_grades.get('assignments_missing', 0),
                            'early_score_range': max(scores) - min(scores) if len(scores) > 1 else 0
                        })
                    else:
                        # No scores available
                        row.update({
                            'early_avg_score': 0,
                            'early_min_score': 0,
                            'early_max_score': 0,
                            'early_score_std': 0,
                            'early_submitted_count': 0,
                            'early_assessments_count': len(assignments),
                            'early_missing_submissions': len(assignments),
                            'early_score_range': 0
                        })
                    
                    # Calculate submission rate
                    total_assignments = max(len(assignments), 1)
                    row['early_submission_rate'] = row['early_submitted_count'] / total_assignments
                    
                    # Calculate total weight (approximate)
                    total_points = sum(a.get('points_possible', 0) for a in assignments)
                    row['early_total_weight'] = min(total_points / 10, 100)  # Normalize to reasonable range
                    
                else:
                    # No grade data available
                    row.update({
                        'early_avg_score': 50,  # Default
                        'early_min_score': 0,
                        'early_max_score': 50,
                        'early_score_std': 0,
                        'early_submitted_count': 0,
                        'early_assessments_count': len(assignments),
                        'early_missing_submissions': len(assignments),
                        'early_submission_rate': 0,
                        'early_score_range': 0,
                        'early_total_weight': 25
                    })
                
                # Default engagement features (Canvas doesn't provide detailed VLE data)
                row.update({
                    'early_total_clicks': 150,  # Default assumption
                    'early_avg_clicks': 10,
                    'early_clicks_std': 8,
                    'early_max_clicks': 40,
                    'early_active_days': 15,
                    'early_first_access': 0,
                    'early_last_access': 25,
                    'early_engagement_consistency': 2.5,
                    'early_clicks_per_active_day': 7,
                    'early_engagement_range': 20,
                    'early_banked_count': 0
                })
                
                prediction_data.append(row)
            
            df = pd.DataFrame(prediction_data)
            logger.info(f"Converted Canvas data to prediction format: {len(df)} students")
            return df
            
        except Exception as e:
            raise DataConversionError(f"Failed to convert Canvas data: {e}")

    async def sync_course_data(self, course_id: str) -> Dict[str, Any]:
        """
        Sync complete course data including students, assignments, and grades
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            Complete course data ready for prediction analysis
        """
        logger.info(f"Starting Canvas course sync for course {course_id}")
        
        try:
            # Get course info
            course_info = await self._make_api_request(f"courses/{course_id}")
            
            # Get students
            students = await self.get_course_students(course_id)
            
            # Get assignments
            assignments = await self.get_course_assignments(course_id)
            
            # Get grades for each student
            grades_data = {}
            for student in students:
                student_id = student['id']
                try:
                    grades = await self.get_student_grades(course_id, str(student_id))
                    grades_data[str(student_id)] = grades
                except APIError as e:
                    logger.warning(f"Failed to get grades for student {student_id}: {e}")
                    grades_data[str(student_id)] = {}
            
            # Get analytics if available
            analytics = await self.get_course_analytics(course_id)
            
            course_data = {
                'course': course_info,
                'students': students,
                'assignments': assignments,
                'grades': grades_data,
                'analytics': analytics,
                'sync_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Canvas course sync completed: {len(students)} students, {len(assignments)} assignments")
            return course_data
            
        except Exception as e:
            logger.error(f"Canvas course sync failed for course {course_id}: {e}")
            raise APIError(f"Course sync failed: {e}")

# Async context manager support
class CanvasClient:
    """Async context manager for Canvas integration"""
    
    def __init__(self, base_url: str, client_id: str, client_secret: str, redirect_uri: str = None):
        self.canvas = CanvasIntegration(base_url, client_id, client_secret, redirect_uri)
    
    async def __aenter__(self):
        return self.canvas
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.canvas.close()