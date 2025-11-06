"""
PowerSchool SIS Mock Data Generator
Generates realistic K-12 student data matching PowerSchool SIS format and structure
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class PowerSchoolMockDataGenerator:
    """
    Generates mock PowerSchool SIS data for K-12 education
    Focuses on demographics, grades, attendance, and behavioral data
    """
    
    def __init__(self):
        # K-12 Grade levels with realistic distributions
        self.grade_levels = [
            ('K', 'Kindergarten', 5, 6),
            ('1', '1st Grade', 6, 7),
            ('2', '2nd Grade', 7, 8),
            ('3', '3rd Grade', 8, 9),
            ('4', '4th Grade', 9, 10),
            ('5', '5th Grade', 10, 11),
            ('6', '6th Grade', 11, 12),
            ('7', '7th Grade', 12, 13),
            ('8', '8th Grade', 13, 14),
            ('9', '9th Grade', 14, 15),
            ('10', '10th Grade', 15, 16),
            ('11', '11th Grade', 16, 17),
            ('12', '12th Grade', 17, 18)
        ]
        
        # K-12 focused demographics
        self.first_names = {
            'male': ['Liam', 'Noah', 'Oliver', 'Elijah', 'James', 'William', 'Benjamin', 'Lucas', 'Henry', 'Alexander', 'Mason', 'Michael', 'Ethan', 'Daniel', 'Jacob', 'Logan', 'Jackson', 'Sebastian', 'Jack', 'Owen'],
            'female': ['Emma', 'Olivia', 'Ava', 'Isabella', 'Sophia', 'Charlotte', 'Mia', 'Amelia', 'Harper', 'Evelyn', 'Abigail', 'Emily', 'Elizabeth', 'Mila', 'Ella', 'Avery', 'Sofia', 'Camila', 'Aria', 'Scarlett']
        }
        
        self.last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson']
        
        # K-12 Schools with realistic structures
        self.schools = [
            {
                'id': 'PS001',
                'name': 'Lincoln Elementary School',
                'type': 'Elementary',
                'grades': ['K', '1', '2', '3', '4', '5'],
                'students_per_grade': 22
            },
            {
                'id': 'PS002', 
                'name': 'Roosevelt Middle School',
                'type': 'Middle',
                'grades': ['6', '7', '8'],
                'students_per_grade': 28
            },
            {
                'id': 'PS003',
                'name': 'Washington High School',
                'type': 'High',
                'grades': ['9', '10', '11', '12'],
                'students_per_grade': 32
            },
            {
                'id': 'PS004',
                'name': 'Jefferson Elementary School', 
                'type': 'Elementary',
                'grades': ['K', '1', '2', '3', '4', '5'],
                'students_per_grade': 20
            }
        ]
        
        # K-12 specific courses by grade level
        self.elementary_courses = ['Reading', 'Mathematics', 'Science', 'Social Studies', 'Art', 'Music', 'Physical Education']
        self.middle_courses = ['English Language Arts', 'Mathematics', 'Science', 'Social Studies', 'Physical Education', 'Art', 'Music', 'Technology']
        self.high_courses = ['English I', 'English II', 'English III', 'English IV', 'Algebra I', 'Geometry', 'Algebra II', 'Pre-Calculus', 'Biology', 'Chemistry', 'Physics', 'World History', 'US History', 'Government', 'Economics']
        
        # Risk factors for realistic academic variance
        self.socioeconomic_factors = ['Low Income', 'Free Lunch', 'Reduced Lunch', 'Not Eligible']
        self.special_populations = ['IEP', 'ELL', '504 Plan', 'Gifted', 'None']
        self.behavioral_flags = ['Frequent Absences', 'Tardiness', 'Disciplinary Issues', 'Academic Struggles', 'None']
    
    def generate_student_id(self) -> str:
        """Generate realistic PowerSchool student ID"""
        return f"PS{random.randint(100000, 999999)}"
    
    def generate_student_demographics(self) -> Dict[str, Any]:
        """Generate realistic K-12 student demographics"""
        gender = random.choice(['M', 'F'])
        first_name = random.choice(self.first_names['male' if gender == 'M' else 'female'])
        last_name = random.choice(self.last_names)
        
        # Select grade level and corresponding age
        grade_info = random.choice(self.grade_levels)
        grade_level, grade_name, min_age, max_age = grade_info
        age = random.randint(min_age, max_age)
        
        # Birth date based on age
        birth_date = datetime.now() - timedelta(days=age * 365 + random.randint(0, 364))
        
        return {
            'student_id': self.generate_student_id(),
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}",
            'gender': gender,
            'grade_level': grade_level,
            'grade_name': grade_name,
            'age': age,
            'birth_date': birth_date.strftime('%Y-%m-%d'),
            'ethnicity': random.choice(['White', 'Hispanic/Latino', 'Black/African American', 'Asian', 'Two or More Races', 'American Indian', 'Pacific Islander']),
            'socioeconomic_status': random.choice(self.socioeconomic_factors),
            'special_population': random.choice(self.special_populations),
            'home_language': random.choice(['English', 'Spanish', 'French', 'Other'])
        }
    
    def generate_academic_data(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic academic performance data"""
        grade_level = student['grade_level']
        
        # Determine course list based on grade level
        if grade_level in ['K', '1', '2', '3', '4', '5']:
            courses = self.elementary_courses
            grade_scale = 4.0  # Elementary often uses 4-point scale
        elif grade_level in ['6', '7', '8']:
            courses = self.middle_courses
            grade_scale = 4.0
        else:
            courses = self.high_courses[:8]  # High schoolers take ~8 courses
            grade_scale = 4.0
        
        # Generate grades with realistic distribution
        grades = {}
        total_points = 0
        credit_hours = 0
        
        # Academic performance influenced by risk factors
        base_performance = random.uniform(2.0, 4.0)
        
        # Adjust for special populations
        if student['special_population'] == 'Gifted':
            base_performance += random.uniform(0.3, 0.8)
        elif student['special_population'] in ['IEP', 'ELL']:
            base_performance -= random.uniform(0.2, 0.6)
        
        # Adjust for socioeconomic factors
        if student['socioeconomic_status'] in ['Low Income', 'Free Lunch']:
            base_performance -= random.uniform(0.1, 0.4)
        
        base_performance = max(0.5, min(4.0, base_performance))
        
        for course in courses:
            # Add some variance per course
            course_grade = base_performance + random.uniform(-0.5, 0.5)
            course_grade = max(0.0, min(4.0, course_grade))
            
            grades[course] = {
                'grade_points': round(course_grade, 2),
                'letter_grade': self.convert_to_letter_grade(course_grade),
                'credit_hours': 1.0,
                'percentage': round(course_grade / 4.0 * 100, 1)
            }
            
            total_points += course_grade
            credit_hours += 1.0
        
        gpa = round(total_points / len(courses), 2) if courses else 0.0
        
        return {
            'gpa': gpa,
            'credit_hours_earned': credit_hours,
            'credit_hours_attempted': credit_hours,
            'courses': grades,
            'academic_year': '2024-2025',
            'semester': 'Fall 2024'
        }
    
    def generate_attendance_data(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic attendance patterns"""
        school_days = 180  # Typical school year
        
        # Base attendance rate
        base_attendance = random.uniform(0.85, 0.98)
        
        # Adjust for risk factors
        if student['socioeconomic_status'] in ['Low Income', 'Free Lunch']:
            base_attendance -= random.uniform(0.05, 0.15)
        
        if student['special_population'] in ['IEP', 'ELL']:
            base_attendance -= random.uniform(0.02, 0.08)
        
        base_attendance = max(0.60, min(0.99, base_attendance))
        
        days_present = int(school_days * base_attendance)
        days_absent = school_days - days_present
        tardies = random.randint(0, max(1, days_absent // 2))
        
        return {
            'days_enrolled': school_days,
            'days_present': days_present,
            'days_absent': days_absent,
            'tardies': tardies,
            'attendance_rate': round(base_attendance * 100, 1),
            'chronic_absenteeism': days_absent > (school_days * 0.1)  # 10%+ absence rate
        }
    
    def generate_behavioral_data(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Generate behavioral and disciplinary data"""
        # Risk-based behavioral issues
        risk_level = 'Low'
        disciplinary_incidents = 0
        suspensions = 0
        
        # Higher risk students have more behavioral challenges
        if student['socioeconomic_status'] in ['Low Income', 'Free Lunch']:
            if random.random() < 0.15:  # 15% chance
                risk_level = 'Medium'
                disciplinary_incidents = random.randint(1, 3)
                
        if student['special_population'] == 'IEP' and student['grade_level'] in ['6', '7', '8', '9', '10']:
            if random.random() < 0.20:  # 20% chance for middle/high IEP students
                risk_level = 'Medium'
                disciplinary_incidents = random.randint(1, 2)
        
        if disciplinary_incidents > 2:
            suspensions = random.randint(0, 1)
            risk_level = 'High'
        
        return {
            'disciplinary_incidents': disciplinary_incidents,
            'suspensions': suspensions,
            'behavioral_risk_level': risk_level,
            'positive_behavior_points': random.randint(50, 200) if risk_level == 'Low' else random.randint(10, 80),
            'counselor_referrals': random.randint(0, 2) if risk_level in ['Medium', 'High'] else 0
        }
    
    def convert_to_letter_grade(self, gpa: float) -> str:
        """Convert GPA to letter grade"""
        if gpa >= 3.7:
            return 'A'
        elif gpa >= 3.3:
            return 'B+'
        elif gpa >= 3.0:
            return 'B'
        elif gpa >= 2.7:
            return 'C+'
        elif gpa >= 2.3:
            return 'C'
        elif gpa >= 2.0:
            return 'D+'
        elif gpa >= 1.7:
            return 'D'
        else:
            return 'F'
    
    def assign_school(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Assign student to appropriate school based on grade level"""
        grade = student['grade_level']
        
        # Find schools that serve this grade level
        eligible_schools = [school for school in self.schools if grade in school['grades']]
        
        if eligible_schools:
            school = random.choice(eligible_schools)
            return {
                'school_id': school['id'],
                'school_name': school['name'],
                'school_type': school['type']
            }
        
        # Fallback
        return {
            'school_id': 'PS001',
            'school_name': 'Default Elementary School',
            'school_type': 'Elementary'
        }
    
    def generate_powerschool_students(self, count: int = 120) -> List[Dict[str, Any]]:
        """
        Generate comprehensive PowerSchool student dataset
        Focuses on K-12 specific data points and realistic academic patterns
        """
        students = []
        
        for _ in range(count):
            # Generate core student data
            student = self.generate_student_demographics()
            
            # Add school assignment
            school_info = self.assign_school(student)
            student.update(school_info)
            
            # Generate academic performance
            academic_data = self.generate_academic_data(student)
            student.update(academic_data)
            
            # Generate attendance data
            attendance_data = self.generate_attendance_data(student)
            student.update(attendance_data)
            
            # Generate behavioral data
            behavioral_data = self.generate_behavioral_data(student)
            student.update(behavioral_data)
            
            # Add PowerSchool-specific metadata
            student.update({
                'enrollment_date': (datetime.now() - timedelta(days=random.randint(30, 200))).strftime('%Y-%m-%d'),
                'student_status': 'Active',
                'district_id': 'DISTRICT001',
                'district_name': 'Sample School District',
                'last_updated': datetime.now().isoformat()
            })
            
            students.append(student)
        
        return students
    
    def get_schools_summary(self) -> List[Dict[str, Any]]:
        """Get summary of available schools for UI display"""
        summary = []
        
        for school in self.schools:
            # Calculate expected student count
            expected_students = len(school['grades']) * school['students_per_grade']
            
            summary.append({
                'id': school['id'],
                'name': school['name'],
                'type': school['type'],
                'grades': school['grades'],
                'expected_students': expected_students,
                'grade_range': f"{school['grades'][0]}-{school['grades'][-1]}"
            })
        
        return summary

# Global instance for easy access
powerschool_data_generator = PowerSchoolMockDataGenerator()