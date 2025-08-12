#!/usr/bin/env python3
"""
Database Cleanup Script
Remove excess students and keep only essential demo data
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import text
from src.mvp.database import get_db_session
from src.mvp.models import Student, Prediction, Institution, Intervention

def cleanup_database():
    """Clean up database to reasonable demo size"""
    
    print("=== DATABASE CLEANUP ===")
    print()
    
    # Set PostgreSQL URL
    os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost:5432/student_success"
    
    with get_db_session() as db:
        print("📊 BEFORE CLEANUP:")
        
        # Show current counts
        student_count = db.query(Student).count()
        prediction_count = db.query(Prediction).count()
        intervention_count = db.query(Intervention).count()
        
        print(f"  Students: {student_count}")
        print(f"  Predictions: {prediction_count}")
        print(f"  Interventions: {intervention_count}")
        print()
        
        print("🧹 CLEANUP OPERATIONS:")
        
        # Keep only essential students:
        # 1. STU001-STU005 (demo students)
        # 2. A few sample numeric students for testing
        
        students_to_keep = []
        
        # Keep STU prefixed students (demo data)
        stu_students = db.query(Student).filter(Student.student_id.like('STU%')).all()
        students_to_keep.extend([s.id for s in stu_students])
        print(f"  ✅ Keeping {len(stu_students)} STU demo students")
        
        # Keep first 10 numeric students for sample data
        numeric_students = db.query(Student).filter(Student.student_id.regexp_match('^[0-9]+$')).order_by(Student.student_id).limit(10).all()
        students_to_keep.extend([s.id for s in numeric_students])
        print(f"  ✅ Keeping {len(numeric_students)} numeric sample students")
        
        # Remove TEST students (they were just for testing)
        test_students = db.query(Student).filter(Student.student_id.like('TEST%')).all()
        if test_students:
            test_ids = [s.id for s in test_students]
            
            # Delete predictions for test students
            db.execute(text("DELETE FROM predictions WHERE student_id IN :ids"), {"ids": tuple(test_ids)})
            
            # Delete interventions for test students  
            db.execute(text("DELETE FROM interventions WHERE student_id IN :ids"), {"ids": tuple(test_ids)})
            
            # Delete test students
            db.execute(text("DELETE FROM students WHERE id IN :ids"), {"ids": tuple(test_ids)})
            
            print(f"  🗑️  Removed {len(test_students)} TEST students")
        
        # Remove excess numeric students (keep only first 10)
        excess_students = db.query(Student).filter(
            Student.student_id.regexp_match('^[0-9]+$'),
            Student.id.notin_(students_to_keep)
        ).all()
        
        if excess_students:
            excess_ids = [s.id for s in excess_students]
            
            # Delete predictions for excess students
            db.execute(text("DELETE FROM predictions WHERE student_id IN :ids"), {"ids": tuple(excess_ids)})
            
            # Delete interventions for excess students
            db.execute(text("DELETE FROM interventions WHERE student_id IN :ids"), {"ids": tuple(excess_ids)})
            
            # Delete excess students
            db.execute(text("DELETE FROM students WHERE id IN :ids"), {"ids": tuple(excess_ids)})
            
            print(f"  🗑️  Removed {len(excess_students)} excess numeric students")
        
        # Commit changes
        db.commit()
        
        print()
        print("📊 AFTER CLEANUP:")
        
        # Show final counts
        final_student_count = db.query(Student).count()
        final_prediction_count = db.query(Prediction).count()  
        final_intervention_count = db.query(Intervention).count()
        
        print(f"  Students: {final_student_count}")
        print(f"  Predictions: {final_prediction_count}")
        print(f"  Interventions: {final_intervention_count}")
        
        print()
        print("🎯 REMAINING STUDENTS:")
        
        remaining_students = db.query(Student).order_by(Student.student_id).all()
        for student in remaining_students:
            prediction_count = db.query(Prediction).filter(Prediction.student_id == student.id).count()
            intervention_count = db.query(Intervention).filter(Intervention.student_id == student.id).count()
            print(f"  - {student.student_id}: {prediction_count} predictions, {intervention_count} interventions")
        
        print()
        print("✅ DATABASE CLEANUP COMPLETE!")

if __name__ == "__main__":
    cleanup_database()