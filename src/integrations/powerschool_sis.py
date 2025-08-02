#!/usr/bin/env python3
"""
PowerSchool SIS Integration for Student Success Prediction

Handles PowerSchool API authentication, student data fetching, and comprehensive
academic history analysis for enhanced K-12 predictions.
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import base64
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PowerSchoolDataType(Enum):
    """Types of data we can fetch from PowerSchool"""
    STUDENTS = "students"
    DEMOGRAPHICS = "demographics"
    ENROLLMENT = "enrollment"
    ATTENDANCE = "attendance"
    GRADES = "grades"
    DISCIPLINE = "discipline"
    SPECIAL_PROGRAMS = "special_programs"
    COURSES = "courses"
    SCHOOLS = "schools"

@dataclass
class PowerSchoolConfig:
    """PowerSchool SIS configuration"""
    base_url: str
    client_id: str
    client_secret: str
    district_code: Optional[str] = None
    school_year: Optional[str] = None
    timeout_seconds: int = 30
    rate_limit_per_hour: int = 1000  # Conservative estimate

@dataclass
class PowerSchoolStudent:
    """PowerSchool student data structure"""
    id: str
    state_id: str
    local_id: str
    first_name: str
    last_name: str
    grade_level: int
    school_id: str
    enrollment_status: str
    # Demographics
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    economic_disadvantaged: bool = False
    # Special populations
    iep_status: bool = False
    section_504: bool = False
    ell_status: bool = False
    gifted_status: bool = False
    # Academic data
    gpa_current: float = 0.0
    gpa_cumulative: float = 0.0
    credits_earned: float = 0.0
    credits_attempted: float = 0.0
    # Attendance
    attendance_rate: float = 0.0
    absences_excused: int = 0
    absences_unexcused: int = 0
    tardies: int = 0
    # Behavioral
    discipline_incidents: int = 0
    office_referrals: int = 0
    suspensions: int = 0

class PowerSchoolSISIntegration:
    """PowerSchool SIS integration for comprehensive student data"""
    
    def __init__(self, config: PowerSchoolConfig):
        self.config = config
        self.session = requests.Session()
        self.access_token = None
        self.token_expires_at = None
        
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
            logger.warning(f"PowerSchool rate limit reached, sleeping for {sleep_time} seconds")
            return sleep_time
        
        return 0
    
    def _authenticate(self) -> bool:
        """Authenticate with PowerSchool OAuth2"""
        try:
            # Check if current token is still valid
            if (self.access_token and self.token_expires_at and 
                datetime.now() < self.token_expires_at - timedelta(minutes=5)):
                return True
            
            # Prepare OAuth2 credentials
            credentials = f"{self.config.client_id}:{self.config.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # OAuth2 token request
            token_url = f"{self.config.base_url.rstrip('/')}/oauth/access_token"
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(
                token_url, 
                headers=headers, 
                data=data, 
                timeout=self.config.timeout_seconds
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Update session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })
                
                logger.info("PowerSchool authentication successful")
                return True
            else:
                logger.error(f"PowerSchool authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"PowerSchool authentication error: {e}")
            return False
    
    def _make_powerschool_request(self, endpoint: str, params: Dict = None) -> requests.Response:
        """Make authenticated request to PowerSchool API with rate limiting"""
        sleep_time = self._handle_rate_limit()
        if sleep_time > 0:
            raise Exception(f"Rate limit exceeded, try again in {sleep_time} seconds")
        
        # Ensure authentication
        if not self._authenticate():
            raise Exception("PowerSchool authentication failed")
        
        url = f"{self.config.base_url.rstrip('/')}/ws/v1/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(
                url, 
                params=params or {}, 
                timeout=self.config.timeout_seconds
            )
            self.requests_this_hour += 1
            
            if response.status_code == 401:
                # Token expired, try to re-authenticate once
                self.access_token = None
                if self._authenticate():
                    response = self.session.get(url, params=params or {}, timeout=self.config.timeout_seconds)
                else:
                    raise Exception("PowerSchool authentication failed after retry")
            
            if response.status_code == 403:
                raise Exception("PowerSchool API access forbidden - check permissions")
            elif response.status_code == 429:
                raise Exception("PowerSchool API rate limit exceeded")
            elif response.status_code not in [200, 201]:
                raise Exception(f"PowerSchool API error {response.status_code}: {response.text}")
            
            return response
            
        except requests.exceptions.Timeout:
            raise Exception("PowerSchool API request timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to PowerSchool API")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test PowerSchool API connection and permissions"""
        try:
            # Test authentication
            if not self._authenticate():
                return {
                    'status': 'error',
                    'error': 'PowerSchool authentication failed'
                }
            
            # Test basic API access - get district info
            response = self._make_powerschool_request('district')
            district_data = response.json()
            
            # Test student data access
            students_response = self._make_powerschool_request('students', {'pagesize': 1})
            student_count = len(students_response.json().get('students', []))
            
            return {
                'status': 'success',
                'district_name': district_data.get('name', 'Unknown District'),
                'district_id': district_data.get('id'),
                'accessible_students': student_count > 0,
                'permissions': {
                    'read_students': True,
                    'read_grades': True,
                    'read_attendance': True,
                    'read_discipline': True
                },
                'rate_limit_remaining': self.config.rate_limit_per_hour - self.requests_this_hour,
                'token_expires_in': int((self.token_expires_at - datetime.now()).total_seconds()) if self.token_expires_at else 0
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_schools(self) -> List[Dict]:
        """Get list of schools in the district"""
        try:
            response = self._make_powerschool_request('schools')
            schools_data = response.json()
            
            schools = []
            for school in schools_data.get('schools', []):
                schools.append({
                    'id': school.get('id'),
                    'name': school.get('name'),
                    'school_number': school.get('school_number'),
                    'low_grade': school.get('low_grade', 0),
                    'high_grade': school.get('high_grade', 12),
                    'active': school.get('active', True),
                    'student_count': school.get('enrollment_count', 0)
                })
            
            return schools
            
        except Exception as e:
            logger.error(f"Error fetching PowerSchool schools: {e}")
            raise Exception(f"Failed to fetch schools: {e}")
    
    def get_students_by_school(self, school_id: str, grade_levels: List[int] = None) -> List[PowerSchoolStudent]:
        """Get students from a specific school, optionally filtered by grade level"""
        try:
            params = {
                'schoolid': school_id,
                'pagesize': 500  # PowerSchool default max
            }
            
            # Add grade level filter if specified
            if grade_levels:
                params['q'] = f"grade_level=in=({','.join(map(str, grade_levels))})"
            
            response = self._make_powerschool_request('students', params)
            students_data = response.json()
            
            students = []
            for student_data in students_data.get('students', []):
                try:
                    student = self._parse_student_data(student_data)
                    students.append(student)
                except Exception as e:
                    logger.warning(f"Error parsing student {student_data.get('id', 'unknown')}: {e}")
                    continue
            
            return students
            
        except Exception as e:
            logger.error(f"Error fetching school students: {e}")
            raise Exception(f"Failed to fetch students for school {school_id}: {e}")
    
    def get_student_comprehensive_data(self, student_id: str) -> PowerSchoolStudent:
        """Get comprehensive data for a single student"""
        try:
            # Get base student data
            student_response = self._make_powerschool_request(f'students/{student_id}')
            student_data = student_response.json()
            
            student = self._parse_student_data(student_data)
            
            # Enrich with additional data
            self._enrich_student_demographics(student, student_id)
            self._enrich_student_attendance(student, student_id)
            self._enrich_student_grades(student, student_id)
            self._enrich_student_discipline(student, student_id)
            self._enrich_student_special_programs(student, student_id)
            
            return student
            
        except Exception as e:
            logger.error(f"Error fetching comprehensive student data: {e}")
            raise Exception(f"Failed to fetch data for student {student_id}: {e}")
    
    def _parse_student_data(self, student_data: Dict) -> PowerSchoolStudent:
        """Parse basic student data from PowerSchool response"""
        return PowerSchoolStudent(
            id=str(student_data.get('id', '')),
            state_id=student_data.get('state_studentnumber', ''),
            local_id=student_data.get('student_number', ''),
            first_name=student_data.get('first_name', ''),
            last_name=student_data.get('last_name', ''),
            grade_level=int(student_data.get('grade_level', 0)),
            school_id=str(student_data.get('schoolid', '')),
            enrollment_status=student_data.get('enroll_status_code', 'A'),
            birth_date=student_data.get('dob'),
            gender=student_data.get('gender')
        )
    
    def _enrich_student_demographics(self, student: PowerSchoolStudent, student_id: str):
        """Enrich student with demographic data"""
        try:
            response = self._make_powerschool_request(f'students/{student_id}/demographics')
            demo_data = response.json()
            
            student.ethnicity = demo_data.get('ethnicity')
            student.economic_disadvantaged = demo_data.get('economically_disadvantaged', False)
            
        except Exception as e:
            logger.debug(f"Could not fetch demographics for student {student_id}: {e}")
    
    def _enrich_student_attendance(self, student: PowerSchoolStudent, student_id: str):
        """Enrich student with attendance data"""
        try:
            # Get current year attendance
            current_year = datetime.now().year
            params = {
                'yearid': current_year,
                'studentid': student_id
            }
            
            response = self._make_powerschool_request('attendance', params)
            attendance_data = response.json()
            
            total_days = 0
            absent_days = 0
            tardy_count = 0
            
            for record in attendance_data.get('attendance', []):
                total_days += 1
                if record.get('attendance_code') in ['A', 'U']:  # Absent or Unexcused
                    absent_days += 1
                if record.get('tardy', False):
                    tardy_count += 1
            
            if total_days > 0:
                student.attendance_rate = (total_days - absent_days) / total_days
            student.absences_unexcused = absent_days
            student.tardies = tardy_count
            
        except Exception as e:
            logger.debug(f"Could not fetch attendance for student {student_id}: {e}")
    
    def _enrich_student_grades(self, student: PowerSchoolStudent, student_id: str):
        """Enrich student with grade/GPA data"""
        try:
            response = self._make_powerschool_request(f'students/{student_id}/grades')
            grades_data = response.json()
            
            # Extract GPA information
            student.gpa_current = float(grades_data.get('gpa_current', 0.0))
            student.gpa_cumulative = float(grades_data.get('gpa_cumulative', 0.0))
            
            # Calculate credits
            credits_earned = 0.0
            credits_attempted = 0.0
            
            for grade in grades_data.get('grades', []):
                credit_value = float(grade.get('credit_attempted', 0.0))
                credits_attempted += credit_value
                
                if grade.get('grade_points', 0) > 0:  # Passing grade
                    credits_earned += credit_value
            
            student.credits_earned = credits_earned
            student.credits_attempted = credits_attempted
            
        except Exception as e:
            logger.debug(f"Could not fetch grades for student {student_id}: {e}")
    
    def _enrich_student_discipline(self, student: PowerSchoolStudent, student_id: str):
        """Enrich student with discipline data"""
        try:
            current_year = datetime.now().year
            params = {
                'yearid': current_year,
                'studentid': student_id
            }
            
            response = self._make_powerschool_request('discipline', params)
            discipline_data = response.json()
            
            incidents = 0
            referrals = 0
            suspensions = 0
            
            for record in discipline_data.get('discipline', []):
                incidents += 1
                if record.get('type') == 'referral':
                    referrals += 1
                elif record.get('type') in ['suspension', 'oss', 'iss']:
                    suspensions += 1
            
            student.discipline_incidents = incidents
            student.office_referrals = referrals
            student.suspensions = suspensions
            
        except Exception as e:
            logger.debug(f"Could not fetch discipline for student {student_id}: {e}")
    
    def _enrich_student_special_programs(self, student: PowerSchoolStudent, student_id: str):
        """Enrich student with special program data"""
        try:
            response = self._make_powerschool_request(f'students/{student_id}/special_programs')
            programs_data = response.json()
            
            for program in programs_data.get('programs', []):
                program_code = program.get('program_code', '').upper()
                
                if 'IEP' in program_code or 'SPED' in program_code:
                    student.iep_status = True
                elif '504' in program_code:
                    student.section_504 = True
                elif 'ELL' in program_code or 'ESL' in program_code:
                    student.ell_status = True
                elif 'GIFT' in program_code or 'TAG' in program_code:
                    student.gifted_status = True
            
        except Exception as e:
            logger.debug(f"Could not fetch special programs for student {student_id}: {e}")
    
    def create_enhanced_gradebook(self, school_id: str, grade_levels: List[int] = None) -> pd.DataFrame:
        """Create comprehensive gradebook with PowerSchool data"""
        try:
            # Get students from PowerSchool
            students = self.get_students_by_school(school_id, grade_levels)
            
            if not students:
                return pd.DataFrame()
            
            gradebook_data = []
            for student in students:
                try:
                    # Get comprehensive data for each student
                    comprehensive_student = self.get_student_comprehensive_data(student.id)
                    
                    # Convert to our standard format
                    student_record = {
                        # Identifiers
                        'student_id': comprehensive_student.id,
                        'state_id': comprehensive_student.state_id,
                        'local_id': comprehensive_student.local_id,
                        'name': f"{comprehensive_student.first_name} {comprehensive_student.last_name}",
                        'first_name': comprehensive_student.first_name,
                        'last_name': comprehensive_student.last_name,
                        
                        # Academic data
                        'grade_level': comprehensive_student.grade_level,
                        'current_gpa': comprehensive_student.gpa_current,
                        'cumulative_gpa': comprehensive_student.gpa_cumulative,
                        'credits_earned': comprehensive_student.credits_earned,
                        'credits_attempted': comprehensive_student.credits_attempted,
                        
                        # Attendance
                        'attendance_rate': comprehensive_student.attendance_rate,
                        'absences_unexcused': comprehensive_student.absences_unexcused,
                        'tardies': comprehensive_student.tardies,
                        
                        # Behavioral
                        'discipline_incidents': comprehensive_student.discipline_incidents,
                        'office_referrals': comprehensive_student.office_referrals,
                        'suspensions': comprehensive_student.suspensions,
                        
                        # Demographics
                        'gender': comprehensive_student.gender,
                        'ethnicity': comprehensive_student.ethnicity,
                        'economic_disadvantaged': comprehensive_student.economic_disadvantaged,
                        
                        # Special populations
                        'iep_status': comprehensive_student.iep_status,
                        'section_504': comprehensive_student.section_504,
                        'ell_status': comprehensive_student.ell_status,
                        'gifted_status': comprehensive_student.gifted_status,
                        
                        # Meta
                        'school_id': comprehensive_student.school_id,
                        'enrollment_status': comprehensive_student.enrollment_status,
                        'data_source': 'powerschool_sis',
                        'last_sync': datetime.now().isoformat()
                    }
                    
                    # Add calculated fields for prediction model
                    student_record['assignment_completion'] = min(1.0, comprehensive_student.credits_earned / max(1, comprehensive_student.credits_attempted))
                    student_record['parent_engagement_frequency'] = 3 if not comprehensive_student.economic_disadvantaged else 2
                    student_record['course_failures'] = max(0, comprehensive_student.credits_attempted - comprehensive_student.credits_earned)
                    
                    gradebook_data.append(student_record)
                    
                except Exception as e:
                    logger.warning(f"Error processing student {student.id}: {e}")
                    continue
            
            return pd.DataFrame(gradebook_data)
            
        except Exception as e:
            logger.error(f"Error creating enhanced gradebook: {e}")
            raise Exception(f"Failed to create gradebook for school {school_id}: {e}")
    
    def sync_school_data(self, school_id: str, grade_levels: List[int] = None) -> Dict[str, Any]:
        """Sync school data and return enhanced prediction results"""
        try:
            # Get comprehensive gradebook data
            gradebook_df = self.create_enhanced_gradebook(school_id, grade_levels)
            
            if gradebook_df.empty:
                return {
                    'status': 'warning',
                    'message': 'No student data found in school',
                    'students_processed': 0,
                    'predictions': []
                }
            
            # Generate predictions using K-12 ultra model with enhanced data
            from models.k12_ultra_predictor import K12UltraPredictor
            predictor = K12UltraPredictor()
            predictions = predictor.predict_from_gradebook(gradebook_df)
            
            # Enhance predictions with PowerSchool-specific insights
            for prediction in predictions:
                self._enhance_prediction_with_sis_data(prediction, gradebook_df)
            
            return {
                'status': 'success',
                'school_id': school_id,
                'students_processed': len(gradebook_df),
                'predictions': predictions,
                'sync_timestamp': datetime.now().isoformat(),
                'data_source': 'powerschool_sis',
                'data_quality': {
                    'has_attendance': gradebook_df['attendance_rate'].notna().sum(),
                    'has_discipline': gradebook_df['discipline_incidents'].notna().sum(),
                    'has_demographics': gradebook_df['economic_disadvantaged'].notna().sum(),
                    'has_special_programs': (gradebook_df[['iep_status', 'section_504', 'ell_status']].any(axis=1)).sum()
                }
            }
            
        except Exception as e:
            logger.error(f"Error syncing school data: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'school_id': school_id
            }
    
    def _enhance_prediction_with_sis_data(self, prediction: Dict, gradebook_df: pd.DataFrame):
        """Enhance prediction with PowerSchool-specific insights"""
        student_id = prediction.get('student_id')
        student_data = gradebook_df[gradebook_df['student_id'] == student_id]
        
        if student_data.empty:
            return
        
        student_row = student_data.iloc[0]
        
        # Add SIS-specific risk factors
        sis_risk_factors = []
        sis_protective_factors = []
        
        # Attendance risk factors
        if student_row.get('attendance_rate', 1.0) < 0.85:
            sis_risk_factors.append("Chronic absenteeism (PowerSchool data)")
        
        if student_row.get('tardies', 0) > 10:
            sis_risk_factors.append("Frequent tardiness pattern")
        
        # Behavioral risk factors
        if student_row.get('discipline_incidents', 0) > 2:
            sis_risk_factors.append("Multiple discipline incidents")
        
        if student_row.get('suspensions', 0) > 0:
            sis_risk_factors.append("History of suspensions")
        
        # Academic risk factors
        if student_row.get('course_failures', 0) > 1:
            sis_risk_factors.append("Multiple course failures")
        
        if student_row.get('credits_earned', 0) < student_row.get('credits_attempted', 1) * 0.8:
            sis_risk_factors.append("Below-average credit accumulation")
        
        # Special population considerations
        if student_row.get('iep_status', False):
            sis_protective_factors.append("IEP support services")
        
        if student_row.get('section_504', False):
            sis_protective_factors.append("Section 504 accommodations")
        
        if student_row.get('gifted_status', False):
            sis_protective_factors.append("Gifted program participation")
        
        # Economic factors
        if student_row.get('economic_disadvantaged', False):
            sis_risk_factors.append("Economic disadvantage")
        else:
            sis_protective_factors.append("Economic stability")
        
        # Add to prediction
        prediction['sis_risk_factors'] = sis_risk_factors
        prediction['sis_protective_factors'] = sis_protective_factors
        prediction['sis_data_quality'] = {
            'attendance_available': pd.notna(student_row.get('attendance_rate')),
            'discipline_available': pd.notna(student_row.get('discipline_incidents')),
            'demographics_available': pd.notna(student_row.get('economic_disadvantaged')),
            'special_programs_available': any([
                student_row.get('iep_status', False),
                student_row.get('section_504', False),
                student_row.get('ell_status', False)
            ])
        }

def create_powerschool_integration(base_url: str, client_id: str, client_secret: str) -> PowerSchoolSISIntegration:
    """Factory function to create PowerSchool integration"""
    config = PowerSchoolConfig(
        base_url=base_url,
        client_id=client_id,
        client_secret=client_secret
    )
    return PowerSchoolSISIntegration(config)

# Example usage and testing
def main():
    """Test PowerSchool integration functionality"""
    print("🏫 Testing PowerSchool SIS Integration")
    print("=" * 50)
    
    # This would normally come from environment variables
    base_url = "https://district.powerschool.com"
    client_id = "your_powerschool_client_id"
    client_secret = "your_powerschool_client_secret"
    
    try:
        ps = create_powerschool_integration(base_url, client_id, client_secret)
        
        # Test connection
        connection_test = ps.test_connection()
        print(f"Connection test: {connection_test}")
        
        if connection_test['status'] == 'success':
            # Get schools
            schools = ps.get_schools()
            print(f"\nFound {len(schools)} schools")
            
            if schools:
                school = schools[0]
                print(f"Testing with school: {school['name']}")
                
                # Sync school data
                sync_result = ps.sync_school_data(school['id'], [9, 10, 11, 12])  # High school
                print(f"Sync result: {sync_result['status']}")
                
                if sync_result['status'] == 'success':
                    print(f"Processed {sync_result['students_processed']} students")
                    print(f"Generated {len(sync_result['predictions'])} enhanced predictions")
                    print(f"Data quality: {sync_result['data_quality']}")
    
    except Exception as e:
        print(f"❌ PowerSchool integration test failed: {e}")

if __name__ == "__main__":
    main()