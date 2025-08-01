#!/usr/bin/env python3
"""
Google Classroom Integration for Student Success Prediction

Provides comprehensive Google Classroom API integration with OAuth2 authentication,
course management, assignment tracking, and student engagement analytics.

Key Features:
- OAuth2 authentication with Google Classroom API
- Course roster and enrollment management
- Assignment and submission tracking
- Student engagement metrics (participation, completion rates)
- Grade and performance data synchronization
- Enhanced ML features for Google-specific engagement patterns

Market Position: Google Classroom is gaining market share in K-12 education
with strong teacher adoption due to simplicity and Google ecosystem integration.
"""

import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import pandas as pd

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBRARIES_AVAILABLE = True
except ImportError:
    # Create stub classes when Google libraries aren't available
    class Request: pass
    class Credentials: 
        def __init__(self): 
            self.valid = False
            self.expired = False
    class InstalledAppFlow: 
        @classmethod
        def from_client_secrets_file(cls, *args, **kwargs): 
            return cls()
        def run_local_server(self, *args, **kwargs): 
            return Credentials()
    class HttpError(Exception): pass
    def build(*args, **kwargs): return None
    GOOGLE_LIBRARIES_AVAILABLE = False
    logging.warning("Google API client libraries not installed. Install with: pip install google-api-python-client google-auth-oauthlib")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Classroom API scopes
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses',
    'https://www.googleapis.com/auth/classroom.rosters',
    'https://www.googleapis.com/auth/classroom.coursework.students',
    'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
    'https://www.googleapis.com/auth/classroom.profile.emails',
    'https://www.googleapis.com/auth/classroom.profile.photos'
]

@dataclass
class GoogleClassroomStudent:
    """Enhanced student data model for Google Classroom integration"""
    student_id: str
    email: str
    name: str
    photo_url: Optional[str] = None
    
    # Course enrollment data
    enrolled_courses: List[str] = None
    active_courses: int = 0
    
    # Engagement metrics (Google-specific)
    classroom_participation_rate: float = 0.0
    assignment_completion_rate: float = 0.0
    google_drive_activity: float = 0.0
    meet_attendance_rate: float = 0.0
    discussion_posts: int = 0
    
    # Performance metrics
    avg_assignment_score: float = 0.0
    late_submissions: int = 0
    missing_assignments: int = 0
    total_assignments: int = 0
    
    # Behavioral patterns
    peak_activity_hours: List[int] = None
    weekend_activity: bool = False
    mobile_vs_desktop_ratio: float = 0.5
    
    # Risk indicators (Google Classroom specific)
    days_since_last_activity: int = 0
    declining_participation_trend: bool = False
    resource_access_rate: float = 0.0
    
    def __post_init__(self):
        if self.enrolled_courses is None:
            self.enrolled_courses = []
        if self.peak_activity_hours is None:
            self.peak_activity_hours = []

@dataclass
class ClassroomCourse:
    """Google Classroom course information"""
    course_id: str
    name: str
    description: str
    teacher_email: str
    enrollment_count: int
    state: str  # ACTIVE, ARCHIVED, PROVISIONED, DECLINED, SUSPENDED
    creation_date: datetime
    
    # Course analytics
    avg_engagement_rate: float = 0.0
    assignment_frequency: float = 0.0  # assignments per week
    resource_count: int = 0

@dataclass 
class ClassroomAssignment:
    """Google Classroom assignment with engagement tracking"""
    assignment_id: str
    course_id: str
    title: str
    description: str
    due_date: Optional[datetime]
    points: Optional[float]
    
    # Submission analytics
    submission_rate: float = 0.0
    avg_score: float = 0.0
    late_submissions: int = 0
    on_time_submissions: int = 0

class GoogleClassroomIntegration:
    """
    Comprehensive Google Classroom integration for student success prediction.
    
    Provides OAuth2 authentication, data synchronization, and enhanced ML features
    for Google Classroom engagement patterns and academic performance tracking.
    """
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize Google Classroom integration
        
        Args:
            credentials_file: Path to Google API credentials JSON file
            token_file: Path to store OAuth2 tokens
        """
        self.credentials_file = credentials_file or 'config/google_credentials.json'
        self.token_file = token_file or 'config/google_token.json'
        self.service = None
        self.credentials = None
        
        # Data caches for performance
        self.courses_cache = {}
        self.students_cache = {}
        self.assignments_cache = {}
        
        logger.info("🎓 Google Classroom Integration initialized")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Classroom API using OAuth2
        
        Returns:
            bool: True if authentication successful
        """
        # In demo mode (no Google libraries), simulate successful authentication
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.info("🎓 Google Classroom authentication simulated (demo mode)")
            self.credentials = Credentials()
            self.service = None  # Demo mode service
            return True
        
        # Check if credentials file exists
        if not os.path.exists(self.credentials_file):
            logger.error(f"❌ Google credentials file not found: {self.credentials_file}")
            logger.info("📋 To set up Google Classroom integration:")
            logger.info("   1. Follow the setup guide: docs/Google_Classroom_Setup.md")
            logger.info("   2. Place your google_credentials.json in the config/ directory")
            logger.info("   3. Restart the application")
            return False
            
        try:
            creds = None
            
            # Load existing token
            try:
                with open(self.token_file, 'r') as token:
                    creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
            except FileNotFoundError:
                pass
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('classroom', 'v1', credentials=creds)
            
            logger.info("✅ Google Classroom API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Google Classroom authentication failed: {e}")
            return False
    
    def get_courses(self, teacher_only: bool = True) -> List[ClassroomCourse]:
        """
        Fetch all courses from Google Classroom
        
        Args:
            teacher_only: If True, only return courses where user is teacher
            
        Returns:
            List of ClassroomCourse objects
        """
        try:
            if not self.service:
                raise Exception("Not authenticated. Call authenticate() first.")
            
            results = self.service.courses().list().execute()
            courses = results.get('courses', [])
            
            classroom_courses = []
            for course_data in courses:
                # Skip if teacher_only and user is not teacher
                if teacher_only and course_data.get('courseState') != 'ACTIVE':
                    continue
                
                course = ClassroomCourse(
                    course_id=course_data['id'],
                    name=course_data['name'],
                    description=course_data.get('description', ''),
                    teacher_email=course_data.get('ownerId', ''),
                    enrollment_count=course_data.get('enrollmentCount', 0),
                    state=course_data.get('courseState', 'UNKNOWN'),
                    creation_date=datetime.fromisoformat(course_data.get('creationTime', datetime.now().isoformat()).rstrip('Z'))
                )
                
                classroom_courses.append(course)
                self.courses_cache[course.course_id] = course
            
            logger.info(f"✅ Retrieved {len(classroom_courses)} Google Classroom courses")
            return classroom_courses
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Google Classroom courses: {e}")
            return []
    
    def get_course_students(self, course_id: str) -> List[GoogleClassroomStudent]:
        """
        Get all students enrolled in a specific course
        
        Args:
            course_id: Google Classroom course ID
            
        Returns:
            List of GoogleClassroomStudent objects
        """
        try:
            if not self.service:
                raise Exception("Not authenticated")
            
            results = self.service.courses().students().list(courseId=course_id).execute()
            students_data = results.get('students', [])
            
            students = []
            for student_data in students_data:
                profile = student_data.get('profile', {})
                
                student = GoogleClassroomStudent(
                    student_id=student_data['userId'],
                    email=profile.get('emailAddress', ''),
                    name=profile.get('name', {}).get('fullName', ''),
                    photo_url=profile.get('photoUrl'),
                    enrolled_courses=[course_id]
                )
                
                students.append(student)
                self.students_cache[student.student_id] = student
            
            logger.info(f"✅ Retrieved {len(students)} students from course {course_id}")
            return students
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch students for course {course_id}: {e}")
            return []
    
    def get_course_assignments(self, course_id: str) -> List[ClassroomAssignment]:
        """
        Get all assignments (coursework) for a specific course
        
        Args:
            course_id: Google Classroom course ID
            
        Returns:
            List of ClassroomAssignment objects
        """
        try:
            if not self.service:
                raise Exception("Not authenticated")
            
            results = self.service.courses().courseWork().list(courseId=course_id).execute()
            coursework_data = results.get('courseWork', [])
            
            assignments = []
            for work_data in coursework_data:
                due_date = None
                if 'dueDate' in work_data:
                    due_info = work_data['dueDate']
                    due_date = datetime(
                        due_info['year'], 
                        due_info['month'], 
                        due_info['day']
                    )
                
                assignment = ClassroomAssignment(
                    assignment_id=work_data['id'],
                    course_id=course_id,
                    title=work_data['title'],
                    description=work_data.get('description', ''),
                    due_date=due_date,
                    points=work_data.get('maxPoints')
                )
                
                assignments.append(assignment)
                self.assignments_cache[assignment.assignment_id] = assignment
            
            logger.info(f"✅ Retrieved {len(assignments)} assignments from course {course_id}")
            return assignments
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch assignments for course {course_id}: {e}")
            return []
    
    def calculate_student_engagement_metrics(self, student_id: str, course_id: str) -> Dict[str, float]:
        """
        Calculate comprehensive engagement metrics for a student in a course
        
        Args:
            student_id: Google Classroom student ID
            course_id: Course ID
            
        Returns:
            Dictionary of engagement metrics
        """
        try:
            # Get student submissions for the course
            submissions = self.service.courses().courseWork().studentSubmissions().list(
                courseId=course_id,
                userId=student_id
            ).execute()
            
            submission_data = submissions.get('studentSubmissions', [])
            
            if not submission_data:
                return {
                    'participation_rate': 0.0,
                    'completion_rate': 0.0,
                    'on_time_rate': 0.0,
                    'avg_score': 0.0
                }
            
            total_assignments = len(submission_data)
            completed = sum(1 for s in submission_data if s.get('state') == 'TURNED_IN')
            on_time = sum(1 for s in submission_data if s.get('late') != True)
            
            # Calculate scores
            scores = []
            for submission in submission_data:
                if 'assignedGrade' in submission:
                    scores.append(float(submission['assignedGrade']))
            
            metrics = {
                'participation_rate': completed / total_assignments if total_assignments > 0 else 0.0,
                'completion_rate': completed / total_assignments if total_assignments > 0 else 0.0,
                'on_time_rate': on_time / total_assignments if total_assignments > 0 else 0.0,
                'avg_score': sum(scores) / len(scores) if scores else 0.0,
                'total_assignments': total_assignments,
                'completed_assignments': completed
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate engagement metrics for student {student_id}: {e}")
            return {}
    
    def sync_course_data(self, course_id: str) -> Dict[str, Any]:
        """
        Comprehensive data synchronization for a specific course
        
        Args:
            course_id: Google Classroom course ID
            
        Returns:
            Dictionary containing all course data and analytics
        """
        try:
            logger.info(f"🔄 Syncing Google Classroom data for course {course_id}")
            
            # Get course info
            course_info = self.service.courses().get(id=course_id).execute()
            
            # Get students and assignments
            students = self.get_course_students(course_id)
            assignments = self.get_course_assignments(course_id)
            
            # Calculate engagement metrics for each student
            enhanced_students = []
            for student in students:
                metrics = self.calculate_student_engagement_metrics(student.student_id, course_id)
                
                # Update student object with calculated metrics
                student.classroom_participation_rate = metrics.get('participation_rate', 0.0)
                student.assignment_completion_rate = metrics.get('completion_rate', 0.0)
                student.avg_assignment_score = metrics.get('avg_score', 0.0)
                student.total_assignments = metrics.get('total_assignments', 0)
                
                enhanced_students.append(student)
            
            sync_result = {
                'course_id': course_id,
                'course_name': course_info['name'],
                'students': enhanced_students,
                'assignments': assignments,
                'sync_timestamp': datetime.now().isoformat(),
                'total_students': len(enhanced_students),
                'total_assignments': len(assignments),
                'avg_engagement': sum(s.classroom_participation_rate for s in enhanced_students) / len(enhanced_students) if enhanced_students else 0.0
            }
            
            logger.info(f"✅ Google Classroom sync complete: {len(enhanced_students)} students, {len(assignments)} assignments")
            return sync_result
            
        except Exception as e:
            logger.error(f"❌ Google Classroom sync failed for course {course_id}: {e}")
            return {}
    
    def generate_ml_features(self, students: List[GoogleClassroomStudent]) -> pd.DataFrame:
        """
        Generate enhanced ML features from Google Classroom data
        
        Args:
            students: List of GoogleClassroomStudent objects
            
        Returns:
            DataFrame with Google Classroom-specific ML features
        """
        try:
            features_data = []
            
            for student in students:
                features = {
                    'student_id': student.student_id,
                    'google_email_domain': student.email.split('@')[-1] if '@' in student.email else 'unknown',
                    
                    # Core engagement features
                    'gc_participation_rate': student.classroom_participation_rate,
                    'gc_completion_rate': student.assignment_completion_rate,
                    'gc_avg_score': student.avg_assignment_score,
                    'gc_active_courses': student.active_courses,
                    
                    # Behavioral features
                    'gc_late_submissions_ratio': student.late_submissions / max(student.total_assignments, 1),
                    'gc_missing_assignments_ratio': student.missing_assignments / max(student.total_assignments, 1),
                    'gc_discussion_engagement': student.discussion_posts,
                    'gc_resource_access_rate': student.resource_access_rate,
                    
                    # Risk indicators
                    'gc_days_inactive': student.days_since_last_activity,
                    'gc_declining_trend': 1 if student.declining_participation_trend else 0,
                    'gc_weekend_activity': 1 if student.weekend_activity else 0,
                    'gc_mobile_usage_ratio': student.mobile_vs_desktop_ratio,
                    
                    # Performance indicators
                    'gc_assignment_velocity': student.total_assignments / max(student.active_courses, 1),
                    'gc_engagement_consistency': 1.0 - abs(0.5 - student.classroom_participation_rate) * 2,
                    
                    # Google ecosystem features
                    'gc_drive_activity': student.google_drive_activity,
                    'gc_meet_attendance': student.meet_attendance_rate,
                    'gc_peak_hours_count': len(student.peak_activity_hours),
                }
                
                features_data.append(features)
            
            df = pd.DataFrame(features_data)
            logger.info(f"✅ Generated {len(df.columns)} Google Classroom ML features for {len(students)} students")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to generate ML features: {e}")
            return pd.DataFrame()
    
    def get_risk_analysis(self, student: GoogleClassroomStudent) -> Dict[str, Any]:
        """
        Perform risk analysis for a student based on Google Classroom patterns
        
        Args:
            student: GoogleClassroomStudent object
            
        Returns:
            Risk analysis results
        """
        risk_factors = []
        risk_score = 0.0
        
        # Participation risk
        if student.classroom_participation_rate < 0.5:
            risk_factors.append("Low Google Classroom participation")
            risk_score += 0.3
        
        # Assignment completion risk
        if student.assignment_completion_rate < 0.7:
            risk_factors.append("Poor assignment completion rate")
            risk_score += 0.25
        
        # Engagement trend risk
        if student.declining_participation_trend:
            risk_factors.append("Declining participation trend")
            risk_score += 0.2
        
        # Inactivity risk
        if student.days_since_last_activity > 7:
            risk_factors.append("Extended period of inactivity")
            risk_score += 0.15
        
        # Missing assignments risk
        if student.missing_assignments > 3:
            risk_factors.append("Multiple missing assignments")
            risk_score += 0.1
        
        risk_level = "Low"
        if risk_score > 0.7:
            risk_level = "High"
        elif risk_score > 0.4:
            risk_level = "Medium"
        
        return {
            'student_id': student.student_id,
            'risk_score': min(risk_score, 1.0),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': self._generate_recommendations(risk_factors),
            'google_classroom_data': {
                'participation_rate': student.classroom_participation_rate,
                'completion_rate': student.assignment_completion_rate,
                'avg_score': student.avg_assignment_score,
                'active_courses': student.active_courses
            }
        }
    
    def _generate_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Generate intervention recommendations based on risk factors"""
        recommendations = []
        
        for factor in risk_factors:
            if "participation" in factor.lower():
                recommendations.append("Encourage active participation in Google Classroom discussions")
                recommendations.append("Set up Google Meet office hours for additional support")
            elif "completion" in factor.lower():
                recommendations.append("Implement assignment reminders through Google Classroom")
                recommendations.append("Break down large assignments into smaller, manageable tasks")
            elif "declining" in factor.lower():
                recommendations.append("Schedule one-on-one check-in via Google Meet")
                recommendations.append("Review Google Classroom engagement patterns with student")
            elif "inactivity" in factor.lower():
                recommendations.append("Send personalized Google Classroom notification")
                recommendations.append("Contact student and parent/guardian directly")
            elif "missing" in factor.lower():
                recommendations.append("Set up Google Calendar reminders for assignments")
                recommendations.append("Provide catch-up resources in Google Drive")
        
        return list(set(recommendations))  # Remove duplicates
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of Google Classroom integration
        
        Returns:
            Health status and system information
        """
        health_status = {
            'service': 'Google Classroom Integration',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'authentication': False,
            'api_access': False,
            'features': []
        }
        
        # Check if Google libraries are available
        if not GOOGLE_LIBRARIES_AVAILABLE:
            health_status['status'] = 'limited'
            health_status['warning'] = 'Google API libraries not installed'
            health_status['features'].append('Demo mode only')
            return health_status
        
        # Check if credentials file exists
        if not os.path.exists(self.credentials_file):
            health_status['status'] = 'setup_required'
            health_status['warning'] = 'Google credentials not configured'
            health_status['setup_guide'] = 'docs/Google_Classroom_Setup.md'
            health_status['features'].append('Credentials setup required')
            return health_status
        
        try:
            # Check authentication
            if self.credentials and self.credentials.valid:
                health_status['authentication'] = True
            
            # Check API access
            if self.service:
                # Try to make a simple API call
                self.service.courses().list(pageSize=1).execute()
                health_status['api_access'] = True
            
            # List available features
            health_status['features'] = [
                'OAuth2 Authentication',
                'Course Management',
                'Student Roster Sync',
                'Assignment Tracking',
                'Engagement Analytics',
                'Risk Assessment',
                'ML Feature Generation',
                'Cross-platform Integration'
            ]
            
            if health_status['authentication'] and health_status['api_access']:
                health_status['status'] = 'healthy'
            else:
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status

# Example usage and testing
if __name__ == "__main__":
    async def test_google_classroom():
        """Test Google Classroom integration"""
        try:
            gc = GoogleClassroomIntegration()
            
            print("🧪 Testing Google Classroom Integration")
            print("=" * 50)
            
            # Health check
            health = gc.health_check()
            print(f"Health Status: {health['status']}")
            
            # Note: Actual API calls require proper authentication setup
            print("✅ Google Classroom integration module loaded successfully")
            print("📋 Features available:")
            for feature in health.get('features', []):
                print(f"  - {feature}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Run test
    asyncio.run(test_google_classroom())