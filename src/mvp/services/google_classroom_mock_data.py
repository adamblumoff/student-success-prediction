"""
Google Classroom Mock Data Generator
Generates realistic K-12 student data matching Google Classroom format and structure
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class GoogleClassroomMockDataGenerator:
    """
    Generates mock Google Classroom data for K-12 education
    Focuses on class-based structure, assignments, and participation data
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
        
        # Google Classroom classes with realistic K-12 structure
        self.classrooms = [
            {
                'id': 'GC001',
                'name': 'Mrs. Johnson\'s 3rd Grade',
                'subject': 'Elementary',
                'grade_level': '3',
                'teacher': 'Mrs. Sarah Johnson',
                'students_per_class': 24
            },
            {
                'id': 'GC002',
                'name': 'Mr. Davis\'s 5th Grade Math',
                'subject': 'Mathematics',
                'grade_level': '5', 
                'teacher': 'Mr. Michael Davis',
                'students_per_class': 26
            },
            {
                'id': 'GC003',
                'name': 'Ms. Rodriguez\'s 7th Grade Science',
                'subject': 'Science',
                'grade_level': '7',
                'teacher': 'Ms. Maria Rodriguez',
                'students_per_class': 28
            },
            {
                'id': 'GC004',
                'name': 'Mr. Thompson\'s High School English',
                'subject': 'English',
                'grade_level': '10',
                'teacher': 'Mr. Robert Thompson',
                'students_per_class': 32
            },
            {
                'id': 'GC005',
                'name': 'Mrs. Wilson\'s AP Biology',
                'subject': 'Biology',
                'grade_level': '11',
                'teacher': 'Mrs. Jennifer Wilson',
                'students_per_class': 22
            }
        ]
        
        # Assignment types by grade level
        self.elementary_assignments = ['Reading Log', 'Math Worksheet', 'Science Journal', 'Art Project', 'Show and Tell']
        self.middle_assignments = ['Research Project', 'Lab Report', 'Book Review', 'Math Problem Set', 'Creative Writing']
        self.high_assignments = ['Essay', 'Research Paper', 'Lab Experiment', 'Presentation', 'Unit Test', 'Group Project']
        
        # Participation factors
        self.participation_levels = ['High', 'Medium', 'Low']
        self.submission_patterns = ['Always On Time', 'Usually On Time', 'Sometimes Late', 'Often Late']
    
    def generate_student_id(self) -> str:
        """Generate realistic Google Classroom student ID"""
        return f"GC{random.randint(100000, 999999)}"
    
    def generate_student_demographics(self) -> Dict[str, Any]:
        """Generate realistic K-12 student demographics for Google Classroom"""
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
            'email': f"{first_name.lower()}.{last_name.lower()}@students.edu",
            'gender': gender,
            'grade_level': grade_level,
            'grade_name': grade_name,
            'age': age,
            'birth_date': birth_date.strftime('%Y-%m-%d'),
            'ethnicity': random.choice(['White', 'Hispanic/Latino', 'Black/African American', 'Asian', 'Two or More Races', 'American Indian', 'Pacific Islander']),
            'participation_level': random.choice(self.participation_levels),
            'submission_pattern': random.choice(self.submission_patterns)
        }
    
    def generate_academic_data(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic academic performance data from Google Classroom"""
        grade_level = student['grade_level']
        
        # Determine assignment types based on grade level
        if grade_level in ['K', '1', '2', '3', '4', '5']:
            assignments = self.elementary_assignments
            max_assignments = 15
        elif grade_level in ['6', '7', '8']:
            assignments = self.middle_assignments
            max_assignments = 20
        else:
            assignments = self.high_assignments
            max_assignments = 25
        
        # Generate assignment grades
        assignment_scores = {}
        total_points = 0
        total_assignments = random.randint(max_assignments - 5, max_assignments)
        
        # Base performance influenced by participation
        if student['participation_level'] == 'High':
            base_performance = random.uniform(80, 100)
        elif student['participation_level'] == 'Medium':
            base_performance = random.uniform(70, 90)
        else:
            base_performance = random.uniform(60, 80)
        
        # Adjust for submission patterns
        if student['submission_pattern'] == 'Often Late':
            base_performance -= random.uniform(5, 15)
        elif student['submission_pattern'] == 'Sometimes Late':
            base_performance -= random.uniform(2, 8)
        
        base_performance = max(50, min(100, base_performance))
        
        for i in range(total_assignments):
            assignment_name = f"{random.choice(assignments)} {i+1}"
            # Add some variance per assignment
            score = base_performance + random.uniform(-10, 10)
            score = max(0, min(100, score))
            
            assignment_scores[assignment_name] = {
                'score': round(score, 1),
                'max_points': 100,
                'submitted_on_time': student['submission_pattern'] in ['Always On Time', 'Usually On Time'] or random.random() > 0.3,
                'submission_date': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
            }
            total_points += score
        
        overall_grade = round(total_points / total_assignments, 1) if total_assignments else 0
        
        return {
            'overall_grade': overall_grade,
            'assignment_count': total_assignments,
            'assignments_submitted': len([a for a in assignment_scores.values() if a['score'] > 0]),
            'on_time_submissions': len([a for a in assignment_scores.values() if a['submitted_on_time']]),
            'assignment_scores': assignment_scores,
            'class_participation': student['participation_level'],
            'academic_year': '2024-2025',
            'semester': 'Fall 2024'
        }
    
    def assign_classroom(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Assign student to appropriate Google Classroom based on grade level"""
        grade = student['grade_level']
        
        # Find classrooms that match the grade level or subject area
        eligible_classrooms = []
        
        for classroom in self.classrooms:
            classroom_grade = classroom['grade_level']
            # Elementary students can be in general elementary classes
            if grade in ['K', '1', '2', '3', '4', '5'] and classroom_grade in ['3', '5']:
                eligible_classrooms.append(classroom)
            # Middle school students
            elif grade in ['6', '7', '8'] and classroom_grade == '7':
                eligible_classrooms.append(classroom)
            # High school students
            elif grade in ['9', '10', '11', '12'] and classroom_grade in ['10', '11']:
                eligible_classrooms.append(classroom)
        
        if eligible_classrooms:
            classroom = random.choice(eligible_classrooms)
            return {
                'classroom_id': classroom['id'],
                'classroom_name': classroom['name'],
                'subject': classroom['subject'],
                'teacher': classroom['teacher']
            }
        
        # Fallback
        return {
            'classroom_id': 'GC001',
            'classroom_name': 'Mrs. Johnson\'s 3rd Grade',
            'subject': 'Elementary',
            'teacher': 'Mrs. Sarah Johnson'
        }
    
    def generate_google_classroom_students(self, count: int = 150) -> List[Dict[str, Any]]:
        """
        Generate comprehensive Google Classroom student dataset
        Focuses on K-12 specific data points and classroom-based learning patterns
        """
        students = []
        
        for _ in range(count):
            # Generate core student data
            student = self.generate_student_demographics()
            
            # Add classroom assignment
            classroom_info = self.assign_classroom(student)
            student.update(classroom_info)
            
            # Generate academic performance
            academic_data = self.generate_academic_data(student)
            student.update(academic_data)
            
            # Add Google Classroom-specific metadata
            student.update({
                'enrollment_date': (datetime.now() - timedelta(days=random.randint(30, 200))).strftime('%Y-%m-%d'),
                'status': 'Active',
                'guardian_email': f"parent.{student['last_name'].lower()}@email.com",
                'last_login': (datetime.now() - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d'),
                'last_updated': datetime.now().isoformat()
            })
            
            students.append(student)
        
        return students
    
    def get_classrooms_summary(self) -> List[Dict[str, Any]]:
        """Get summary of available Google Classrooms for UI display"""
        summary = []
        
        for classroom in self.classrooms:
            summary.append({
                'id': classroom['id'],
                'name': classroom['name'],
                'subject': classroom['subject'],
                'grade_level': classroom['grade_level'],
                'teacher': classroom['teacher'],
                'expected_students': classroom['students_per_class']
            })
        
        return summary

# Global instance for easy access
google_classroom_data_generator = GoogleClassroomMockDataGenerator()