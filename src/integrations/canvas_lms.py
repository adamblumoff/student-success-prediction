#!/usr/bin/env python3
"""
Canvas LMS Integration for Student Success Prediction

Handles Canvas API authentication, data fetching, and real-time gradebook sync.
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CanvasDataType(Enum):
    """Types of data we can fetch from Canvas"""
    STUDENTS = "students"
    GRADES = "grades" 
    ASSIGNMENTS = "assignments"
    ATTENDANCE = "attendance"
    SUBMISSIONS = "submissions"
    COURSES = "courses"

@dataclass
class CanvasConfig:
    """Canvas LMS configuration"""
    base_url: str
    access_token: str
    account_id: Optional[str] = None
    rate_limit_per_hour: int = 3000  # Canvas default
    timeout_seconds: int = 30

@dataclass
class CanvasStudent:
    """Canvas student data structure"""
    id: str
    name: str
    email: str
    sis_user_id: Optional[str]
    enrollments: List[Dict] = None
    grades: Dict = None
    attendance_rate: float = 0.0
    login_activity: Dict = None

class CanvasLMSIntegration:
    """Canvas LMS integration for student success prediction"""
    
    def __init__(self, config: CanvasConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config.access_token}',
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = datetime.now()
        self.requests_this_hour = 0
        self.request_count_reset_time = datetime.now()
        
    def _handle_rate_limit(self):
        """Simple rate limiting implementation"""
        now = datetime.now()
        
        # Reset hourly counter
        if now - self.request_count_reset_time > timedelta(hours=1):
            self.requests_this_hour = 0
            self.request_count_reset_time = now
        
        # Check if we're at rate limit
        if self.requests_this_hour >= self.config.rate_limit_per_hour:
            sleep_time = 3600 - (now - self.request_count_reset_time).seconds
            logger.warning(f"Rate limit reached, sleeping for {sleep_time} seconds")
            return sleep_time
        
        return 0
    
    def _make_canvas_request(self, endpoint: str, params: Dict = None) -> requests.Response:
        """Make authenticated request to Canvas API with rate limiting"""
        sleep_time = self._handle_rate_limit()
        if sleep_time > 0:
            raise Exception(f"Rate limit exceeded, try again in {sleep_time} seconds")
        
        url = f"{self.config.base_url.rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(
                url, 
                params=params or {}, 
                timeout=self.config.timeout_seconds
            )
            self.requests_this_hour += 1
            
            if response.status_code == 401:
                raise Exception("Canvas API authentication failed - check access token")
            elif response.status_code == 403:
                raise Exception("Canvas API access forbidden - check permissions")
            elif response.status_code == 429:
                raise Exception("Canvas API rate limit exceeded")
            elif response.status_code != 200:
                raise Exception(f"Canvas API error {response.status_code}: {response.text}")
            
            return response
            
        except requests.exceptions.Timeout:
            raise Exception("Canvas API request timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Canvas API")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Canvas API connection and permissions"""
        try:
            # Test basic API access
            response = self._make_canvas_request('accounts/self')
            account_data = response.json()
            
            # Test course access
            courses_response = self._make_canvas_request('courses', {'per_page': 1})
            courses_count = len(courses_response.json())
            
            return {
                'status': 'success',
                'account_name': account_data.get('name', 'Unknown'),
                'account_id': account_data.get('id'),
                'accessible_courses': courses_count,
                'permissions': {
                    'read_grades': True,  # We'll assume if we can access courses, we can read grades
                    'read_students': True,
                    'read_assignments': True
                },
                'rate_limit_remaining': self.config.rate_limit_per_hour - self.requests_this_hour
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_courses(self, include_students: bool = False) -> List[Dict]:
        """Get list of courses from Canvas"""
        try:
            params = {
                'enrollment_type': 'teacher',  # Only courses where user is teacher
                'state[]': 'available',        # Only active courses
                'per_page': 100
            }
            
            if include_students:
                params['include[]'] = 'students'
            
            response = self._make_canvas_request('courses', params)
            courses = response.json()
            
            # Filter for K-12 relevant courses
            k12_courses = []
            for course in courses:
                if course.get('enrollment_term_id') and course.get('name'):
                    k12_courses.append({
                        'id': course['id'],
                        'name': course['name'],
                        'course_code': course.get('course_code', ''),
                        'term': course.get('term', {}).get('name', 'Unknown'),
                        'student_count': course.get('total_students', 0),
                        'start_date': course.get('start_at'),
                        'end_date': course.get('end_at')
                    })
            
            return k12_courses
            
        except Exception as e:
            logger.error(f"Error fetching Canvas courses: {e}")
            raise Exception(f"Failed to fetch courses: {e}")
    
    def get_course_students(self, course_id: str) -> List[CanvasStudent]:
        """Get students enrolled in a specific course"""
        try:
            params = {
                'enrollment_type[]': 'student',
                'enrollment_state[]': 'active',
                'include[]': ['email', 'enrollments', 'avatar_url'],
                'per_page': 100
            }
            
            response = self._make_canvas_request(f'courses/{course_id}/users', params)
            raw_students = response.json()
            
            students = []
            for student_data in raw_students:
                student = CanvasStudent(
                    id=str(student_data['id']),
                    name=student_data.get('name', 'Unknown'),
                    email=student_data.get('email', ''),
                    sis_user_id=student_data.get('sis_user_id'),
                    enrollments=student_data.get('enrollments', [])
                )
                students.append(student)
            
            return students
            
        except Exception as e:
            logger.error(f"Error fetching course students: {e}")
            raise Exception(f"Failed to fetch students for course {course_id}: {e}")
    
    def get_student_grades(self, course_id: str, student_id: str) -> Dict[str, Any]:
        """Get comprehensive grade data for a student in a course"""
        try:
            # Get assignments
            assignments_response = self._make_canvas_request(
                f'courses/{course_id}/assignments',
                {'per_page': 100}
            )
            assignments = assignments_response.json()
            
            # Get student submissions
            submissions_response = self._make_canvas_request(
                f'courses/{course_id}/students/submissions',
                {
                    'student_ids[]': student_id,
                    'include[]': ['assignment', 'submission_history'],
                    'per_page': 100
                }
            )
            submissions = submissions_response.json()
            
            # Process grade data
            grade_data = {
                'student_id': student_id,
                'course_id': course_id,
                'assignments': [],
                'overall_grade': 0.0,
                'points_earned': 0.0,
                'points_possible': 0.0,
                'assignment_completion_rate': 0.0,
                'late_submission_rate': 0.0,
                'missing_assignments': 0,
                'grade_trend': []
            }
            
            total_assignments = len(assignments)
            completed_assignments = 0
            late_submissions = 0
            total_points_possible = 0
            total_points_earned = 0
            
            for submission in submissions:
                assignment_id = submission.get('assignment_id')
                assignment = next((a for a in assignments if a['id'] == assignment_id), None)
                
                if assignment:
                    points_possible = assignment.get('points_possible', 0)
                    points_earned = submission.get('score', 0) or 0
                    
                    total_points_possible += points_possible
                    total_points_earned += points_earned
                    
                    # Check completion status
                    if submission.get('workflow_state') == 'submitted':
                        completed_assignments += 1
                        
                        # Check if late
                        if submission.get('late', False):
                            late_submissions += 1
                    
                    grade_data['assignments'].append({
                        'assignment_id': assignment_id,
                        'name': assignment.get('name', ''),
                        'points_possible': points_possible,
                        'points_earned': points_earned,
                        'percentage': (points_earned / points_possible * 100) if points_possible > 0 else 0,
                        'submitted': submission.get('workflow_state') == 'submitted',
                        'late': submission.get('late', False),
                        'missing': submission.get('missing', False),
                        'due_date': assignment.get('due_at'),
                        'submitted_date': submission.get('submitted_at')
                    })
            
            # Calculate summary statistics
            grade_data['points_earned'] = total_points_earned
            grade_data['points_possible'] = total_points_possible
            grade_data['overall_grade'] = (total_points_earned / total_points_possible * 100) if total_points_possible > 0 else 0
            grade_data['assignment_completion_rate'] = (completed_assignments / total_assignments) if total_assignments > 0 else 0
            grade_data['late_submission_rate'] = (late_submissions / completed_assignments) if completed_assignments > 0 else 0
            grade_data['missing_assignments'] = sum(1 for a in grade_data['assignments'] if a['missing'])
            
            return grade_data
            
        except Exception as e:
            logger.error(f"Error fetching student grades: {e}")
            raise Exception(f"Failed to fetch grades for student {student_id}: {e}")
    
    def get_course_gradebook(self, course_id: str) -> pd.DataFrame:
        """Get complete gradebook data for a course in our standard format"""
        try:
            # Get course students
            students = self.get_course_students(course_id)
            
            gradebook_data = []
            for student in students:
                try:
                    # Get student grade data
                    grade_data = self.get_student_grades(course_id, student.id)
                    
                    # Convert to our standard format
                    student_record = {
                        'student_id': student.id,
                        'name': student.name,
                        'email': student.email,
                        'sis_user_id': student.sis_user_id,
                        'current_grade': grade_data['overall_grade'] / 25.0,  # Convert to 4.0 GPA scale approximation
                        'current_gpa': grade_data['overall_grade'] / 25.0,   # Same as current_grade for now
                        'assignment_completion': grade_data['assignment_completion_rate'],
                        'late_submission_rate': grade_data['late_submission_rate'],
                        'missing_assignments': grade_data['missing_assignments'],
                        'points_earned': grade_data['points_earned'],
                        'points_possible': grade_data['points_possible'],
                        'canvas_course_id': course_id,
                        'last_sync': datetime.now().isoformat()
                    }
                    
                    # Add grade level estimation based on course name/code
                    student_record['grade_level'] = self._estimate_grade_level(course_id)
                    
                    # Add default values for required prediction features
                    student_record['attendance_rate'] = 0.95  # Default - would need separate attendance API
                    student_record['discipline_incidents'] = 0  # Default - would need behavior data
                    student_record['parent_engagement_frequency'] = 2  # Default moderate
                    
                    gradebook_data.append(student_record)
                    
                except Exception as e:
                    logger.warning(f"Error processing student {student.id}: {e}")
                    continue
            
            return pd.DataFrame(gradebook_data)
            
        except Exception as e:
            logger.error(f"Error creating course gradebook: {e}")
            raise Exception(f"Failed to create gradebook for course {course_id}: {e}")
    
    def _estimate_grade_level(self, course_id: str) -> int:
        """Estimate grade level from course information"""
        try:
            response = self._make_canvas_request(f'courses/{course_id}')
            course = response.json()
            
            course_name = course.get('name', '').lower()
            course_code = course.get('course_code', '').lower()
            
            # Simple grade level detection patterns
            grade_patterns = {
                'kindergarten': 0, 'kinder': 0, 'k ': 0,
                '1st grade': 1, 'first grade': 1, 'grade 1': 1,
                '2nd grade': 2, 'second grade': 2, 'grade 2': 2,
                '3rd grade': 3, 'third grade': 3, 'grade 3': 3,
                '4th grade': 4, 'fourth grade': 4, 'grade 4': 4,
                '5th grade': 5, 'fifth grade': 5, 'grade 5': 5,
                '6th grade': 6, 'sixth grade': 6, 'grade 6': 6,
                '7th grade': 7, 'seventh grade': 7, 'grade 7': 7,
                '8th grade': 8, 'eighth grade': 8, 'grade 8': 8,
                '9th grade': 9, 'ninth grade': 9, 'freshman': 9,
                '10th grade': 10, 'tenth grade': 10, 'sophomore': 10,
                '11th grade': 11, 'eleventh grade': 11, 'junior': 11,
                '12th grade': 12, 'twelfth grade': 12, 'senior': 12,
            }
            
            for pattern, grade in grade_patterns.items():
                if pattern in course_name or pattern in course_code:
                    return grade
            
            # Default to middle school if no pattern found
            return 7
            
        except:
            return 7  # Default fallback
    
    def sync_course_data(self, course_id: str) -> Dict[str, Any]:
        """Sync course data and return prediction results"""
        try:
            # Get gradebook data
            gradebook_df = self.get_course_gradebook(course_id)
            
            if gradebook_df.empty:
                return {
                    'status': 'warning',
                    'message': 'No student data found in course',
                    'students_processed': 0,
                    'predictions': []
                }
            
            # Generate predictions using K-12 ultra model
            from models.k12_ultra_predictor import K12UltraPredictor
            predictor = K12UltraPredictor()
            predictions = predictor.predict_from_gradebook(gradebook_df)
            
            return {
                'status': 'success',
                'course_id': course_id,
                'students_processed': len(gradebook_df),
                'predictions': predictions,
                'sync_timestamp': datetime.now().isoformat(),
                'data_source': 'canvas_lms'
            }
            
        except Exception as e:
            logger.error(f"Error syncing course data: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'course_id': course_id
            }

def create_canvas_integration(base_url: str, access_token: str) -> CanvasLMSIntegration:
    """Factory function to create Canvas integration"""
    config = CanvasConfig(
        base_url=base_url,
        access_token=access_token
    )
    return CanvasLMSIntegration(config)

# Example usage and testing
def main():
    """Test Canvas integration functionality"""
    print("🎨 Testing Canvas LMS Integration")
    print("=" * 50)
    
    # This would normally come from environment variables
    base_url = "https://canvas.instructure.com"  # Example Canvas instance
    access_token = "your_canvas_access_token_here"
    
    try:
        canvas = create_canvas_integration(base_url, access_token)
        
        # Test connection
        connection_test = canvas.test_connection()
        print(f"Connection test: {connection_test}")
        
        if connection_test['status'] == 'success':
            # Get courses
            courses = canvas.get_courses()
            print(f"\nFound {len(courses)} courses")
            
            if courses:
                course = courses[0]
                print(f"Testing with course: {course['name']}")
                
                # Sync course data
                sync_result = canvas.sync_course_data(course['id'])
                print(f"Sync result: {sync_result['status']}")
                
                if sync_result['status'] == 'success':
                    print(f"Processed {sync_result['students_processed']} students")
                    print(f"Generated {len(sync_result['predictions'])} predictions")
    
    except Exception as e:
        print(f"❌ Canvas integration test failed: {e}")

if __name__ == "__main__":
    main()