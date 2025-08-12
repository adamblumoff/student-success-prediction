#!/usr/bin/env python3
"""
Investigate Student Data
Analyze student records to understand data sources and creation patterns
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import text
from src.mvp.database import get_db_session
from src.mvp.models import Student, Prediction, Institution

def investigate_students():
    """Investigate student data to understand creation patterns"""
    
    print("=== INVESTIGATING STUDENT DATA CREATION ===")
    print()
    
    # Set PostgreSQL URL
    os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost:5432/student_success"
    
    with get_db_session() as db:
        print("📊 STUDENT ANALYSIS:")
        
        # Show student_id ranges and patterns
        result = db.execute(text("""
            SELECT 
                MIN(student_id) as min_id,
                MAX(student_id) as max_id,
                COUNT(*) as total_count,
                COUNT(DISTINCT student_id) as unique_student_ids
            FROM students
        """)).fetchone()
        
        print(f"  📈 Student ID Range: {result.min_id} to {result.max_id}")
        print(f"  📈 Total Records: {result.total_count}")
        print(f"  📈 Unique student_id values: {result.unique_student_ids}")
        
        if result.total_count != result.unique_student_ids:
            print(f"  ❌ DUPLICATE ISSUE: {result.total_count - result.unique_student_ids} duplicates found!")
        else:
            print("  ✅ No duplicate student_id values")
        
        print()
        
        # Show student_id patterns
        print("📊 STUDENT ID PATTERNS:")
        result = db.execute(text("""
            SELECT 
                CASE 
                    WHEN student_id LIKE 'STU%' THEN 'STU prefix'
                    WHEN student_id ~ '^[0-9]+$' THEN 'Numeric only'
                    WHEN student_id LIKE 'student_%' THEN 'student_X format'
                    ELSE 'Other format'
                END as pattern,
                COUNT(*) as count,
                MIN(student_id) as example_min,
                MAX(student_id) as example_max
            FROM students
            GROUP BY 1
            ORDER BY count DESC
        """)).fetchall()
        
        for row in result:
            print(f"  - {row.pattern}: {row.count} students ({row.example_min} to {row.example_max})")
        
        print()
        
        # Show creation timeline
        print("📊 CREATION TIMELINE:")
        result = db.execute(text("""
            SELECT 
                DATE(created_at) as creation_date,
                COUNT(*) as students_created
            FROM students
            WHERE created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY creation_date DESC
            LIMIT 10
        """)).fetchall()
        
        for row in result:
            print(f"  - {row.creation_date}: {row.students_created} students created")
        
        print()
        
        # Show predictions per student
        print("📊 PREDICTIONS PER STUDENT:")
        result = db.execute(text("""
            SELECT 
                COUNT(p.id) as prediction_count,
                COUNT(*) as student_count
            FROM students s
            LEFT JOIN predictions p ON s.id = p.student_id
            GROUP BY s.id
            ORDER BY prediction_count DESC
            LIMIT 10
        """)).fetchall()
        
        predictions_per_student = {}
        total_students_checked = 0
        for row in result:
            pred_count = row.prediction_count or 0
            if pred_count not in predictions_per_student:
                predictions_per_student[pred_count] = 0
            predictions_per_student[pred_count] += 1
            total_students_checked += 1
        
        for pred_count, student_count in sorted(predictions_per_student.items()):
            if pred_count == 0:
                print(f"  - {student_count} students have NO predictions")
            else:
                print(f"  - {student_count} students have {pred_count} prediction(s)")
        
        print()
        
        # Show sample of student data
        print("📊 SAMPLE STUDENT DATA:")
        result = db.execute(text("""
            SELECT s.id, s.student_id, s.grade_level, s.enrollment_status, s.created_at,
                   COUNT(p.id) as prediction_count
            FROM students s
            LEFT JOIN predictions p ON s.id = p.student_id
            GROUP BY s.id, s.student_id, s.grade_level, s.enrollment_status, s.created_at
            ORDER BY s.created_at DESC
            LIMIT 15
        """)).fetchall()
        
        print("  Recent students:")
        for row in result:
            print(f"    ID {row.id}: student_id='{row.student_id}', grade={row.grade_level}, predictions={row.prediction_count}")

if __name__ == "__main__":
    investigate_students()