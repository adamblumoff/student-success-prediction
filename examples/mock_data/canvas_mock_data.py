#!/usr/bin/env python3
"""
Canvas Mock Data Generator
Creates realistic student data based on Canvas course structure for demo purposes
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

class CanvasMockDataGenerator:
    """Generates realistic Canvas student data for demo purposes"""
    
    def __init__(self):
        self.courses = [
            {
                'id': '12345',
                'name': 'Algebra I - Period 1',
                'code': 'MATH-ALG1-P1',
                'students': 28,
                'assignments': 15,
                'grade_level': '9',
                'subject': 'Mathematics'
            },
            {
                'id': '12346', 
                'name': 'English 9 - Period 3',
                'code': 'ENG-9-P3',
                'students': 24,
                'assignments': 22,
                'grade_level': '9',
                'subject': 'English Language Arts'
            },
            {
                'id': '12347',
                'name': 'Biology - Period 5',
                'code': 'SCI-BIO-P5',
                'students': 26,
                'assignments': 18,
                'grade_level': '10',
                'subject': 'Science'
            },
            {
                'id': '12348',
                'name': 'World History - Period 2',
                'code': 'HIST-WH-P2', 
                'students': 30,
                'assignments': 12,
                'grade_level': '10',
                'subject': 'Social Studies'
            }
        ]
        
        self.first_names = [
            'Emma', 'Olivia', 'Sophia', 'Charlotte', 'Amelia', 'Isabella', 'Mia', 'Harper',
            'Evelyn', 'Abigail', 'Emily', 'Elizabeth', 'Sofia', 'Avery', 'Ella', 'Scarlett',
            'Grace', 'Chloe', 'Victoria', 'Riley', 'Aria', 'Lily', 'Aubrey', 'Zoey', 'Penelope',
            'Liam', 'Noah', 'William', 'James', 'Oliver', 'Benjamin', 'Elijah', 'Lucas',
            'Mason', 'Logan', 'Alexander', 'Ethan', 'Jacob', 'Michael', 'Daniel', 'Henry',
            'Jackson', 'Sebastian', 'Aiden', 'Matthew', 'Samuel', 'David', 'Joseph', 'Carter'
        ]
        
        self.last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
            'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores'
        ]
        
        self.ethnicities = ['White', 'Hispanic/Latino', 'Black/African American', 'Asian', 'Native American', 'Pacific Islander', 'Multiracial']
        
    def generate_student_name(self) -> tuple[str, str]:
        """Generate a realistic student name"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        return first_name, last_name
    
    def generate_student_id(self, course_code: str, student_number: int) -> str:
        """Generate a Canvas-style student ID"""
        return f"CVS_{course_code}_{student_number:03d}"
    
    def generate_realistic_grades(self, subject: str, grade_level: str) -> Dict[str, Any]:
        """Generate realistic grades based on subject and grade level"""
        # Base performance varies by subject
        base_performance = {
            'Mathematics': 0.72,  # Math tends to be more challenging
            'English Language Arts': 0.78,
            'Science': 0.75,
            'Social Studies': 0.80
        }
        
        base = base_performance.get(subject, 0.75)
        
        # Grade 10 students perform slightly better than grade 9
        grade_adjustment = 0.03 if grade_level == '10' else 0.0
        
        # Generate current GPA with some variance
        performance_factor = random.normalvariate(base + grade_adjustment, 0.15)
        performance_factor = max(0.4, min(0.95, performance_factor))  # Clamp between 40-95%
        
        current_gpa = performance_factor * 4.0
        previous_gpa = current_gpa + random.normalvariate(0, 0.2)
        previous_gpa = max(1.0, min(4.0, previous_gpa))
        
        return {
            'current_gpa': round(current_gpa, 2),
            'previous_gpa': round(previous_gpa, 2),
            'performance_factor': performance_factor
        }
    
    def generate_engagement_metrics(self, performance_factor: float) -> Dict[str, Any]:
        """Generate engagement metrics correlated with performance"""
        # Students with higher performance tend to have better engagement
        base_attendance = 0.85 + (performance_factor - 0.7) * 0.5
        base_attendance = max(0.6, min(0.98, base_attendance))
        
        attendance_rate = random.normalvariate(base_attendance, 0.08)
        attendance_rate = max(0.5, min(1.0, attendance_rate))
        
        # Study hours correlated with performance
        base_study_hours = 8 + (performance_factor - 0.7) * 10
        study_hours = max(2, min(20, int(random.normalvariate(base_study_hours, 3))))
        
        # Extracurricular activities
        extracurricular = random.choices([0, 1, 2, 3, 4], weights=[20, 35, 30, 12, 3])[0]
        
        return {
            'attendance_rate': round(attendance_rate, 3),
            'study_hours_week': study_hours,
            'extracurricular': extracurricular
        }
    
    def generate_demographics(self, grade_level: str) -> Dict[str, Any]:
        """Generate realistic demographic information"""
        # Age based on grade level with some variance
        base_age = 14 if grade_level == '9' else 15
        birth_year = datetime.now().year - base_age - random.choice([0, 0, 0, 1])  # Some students held back
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        birth_date = datetime(birth_year, birth_month, birth_day)
        
        return {
            'grade_level': grade_level,
            'birth_date': birth_date,
            'gender': random.choice(['Male', 'Female']),
            'ethnicity': random.choices(
                self.ethnicities,
                weights=[45, 25, 15, 8, 3, 2, 2]  # Roughly US demographics
            )[0]
        }
    
    def generate_family_background(self) -> Dict[str, Any]:
        """Generate family and socioeconomic background"""
        # Parent education levels (1-5 scale)
        parent_education = random.choices([1, 2, 3, 4, 5], weights=[10, 20, 30, 25, 15])[0]
        
        # Socioeconomic status correlated with parent education
        base_ses = parent_education
        socioeconomic_status = max(1, min(5, base_ses + random.randint(-1, 1)))
        
        # Special populations
        is_ell = random.random() < 0.12  # ~12% ELL students
        has_iep = random.random() < 0.13  # ~13% have IEPs
        has_504 = random.random() < 0.07  # ~7% have 504 plans
        is_economically_disadvantaged = random.random() < (0.6 - socioeconomic_status * 0.1)
        
        return {
            'parent_education': parent_education,
            'socioeconomic_status': socioeconomic_status,
            'is_ell': is_ell,
            'has_iep': has_iep,
            'has_504': has_504,
            'is_economically_disadvantaged': is_economically_disadvantaged
        }
    
    def generate_contact_info(self, first_name: str, last_name: str) -> Dict[str, Any]:
        """Generate contact information"""
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100, 999)}@student.school.edu"
        parent_email = f"{random.choice(['mom', 'dad', 'parent'])}.{last_name.lower()}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])}"
        
        return {
            'email': email,
            'parent_email': parent_email,
            'phone': f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            'parent_phone': f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
        }
    
    def generate_students_for_course(self, course: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate all students for a specific course"""
        students = []
        
        for i in range(course['students']):
            first_name, last_name = self.generate_student_name()
            student_id = self.generate_student_id(course['code'], i + 1)
            
            # Generate grades based on course subject and grade level
            grades = self.generate_realistic_grades(course['subject'], course['grade_level'])
            engagement = self.generate_engagement_metrics(grades['performance_factor'])
            demographics = self.generate_demographics(course['grade_level'])
            family = self.generate_family_background()
            contact = self.generate_contact_info(first_name, last_name)
            
            student = {
                'student_id': student_id,
                'sis_id': f"SIS_{student_id}",
                'name': f"{first_name} {last_name}",
                'course_name': course['name'],
                'course_code': course['code'],
                'canvas_course_id': course['id'],
                **grades,
                **engagement,
                **demographics,
                **family,
                **contact,
                'enrollment_status': 'active',
                'enrollment_date': datetime.now() - timedelta(days=random.randint(30, 90)),
                'last_activity': datetime.now() - timedelta(hours=random.randint(1, 48))
            }
            
            students.append(student)
        
        return students
    
    def generate_all_canvas_students(self, selected_course_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Generate students for all or selected Canvas courses"""
        if selected_course_ids is None:
            selected_courses = self.courses
        else:
            selected_courses = [c for c in self.courses if c['id'] in selected_course_ids]
        
        all_students = []
        
        for course in selected_courses:
            course_students = self.generate_students_for_course(course)
            all_students.extend(course_students)
        
        return all_students
    
    def create_canvas_dataframe(self, selected_course_ids: List[str] = None) -> pd.DataFrame:
        """Create a pandas DataFrame with Canvas student data"""
        students = self.generate_all_canvas_students(selected_course_ids)
        return pd.DataFrame(students)
    
    def get_import_summary(self, selected_course_ids: List[str] = None) -> Dict[str, Any]:
        """Get summary statistics for Canvas import"""
        if selected_course_ids is None:
            selected_courses = self.courses
        else:
            selected_courses = [c for c in self.courses if c['id'] in selected_course_ids]
        
        total_students = sum(c['students'] for c in selected_courses)
        courses_by_grade = {}
        
        for course in selected_courses:
            grade = course['grade_level']
            if grade not in courses_by_grade:
                courses_by_grade[grade] = []
            courses_by_grade[grade].append(course['name'])
        
        return {
            'total_students': total_students,
            'total_courses': len(selected_courses),
            'courses_by_grade': courses_by_grade,
            'grade_levels': list(courses_by_grade.keys()),
            'subjects': [c['subject'] for c in selected_courses]
        }

if __name__ == "__main__":
    # Test the generator
    generator = CanvasMockDataGenerator()
    
    # Generate sample data
    df = generator.create_canvas_dataframe()
    print(f"Generated {len(df)} Canvas students")
    
    # Show summary
    summary = generator.get_import_summary()
    print(f"Courses: {summary['total_courses']}")
    print(f"Grade levels: {', '.join(summary['grade_levels'])}")
    print(f"Subjects: {', '.join(set(summary['subjects']))}")
    
    # Show sample records
    print("\nSample students:")
    print(df[['name', 'course_name', 'grade_level', 'current_gpa', 'attendance_rate']].head())