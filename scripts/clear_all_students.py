#!/usr/bin/env python3
"""
Clear All Students Database Script
Completely removes all student data from the database while preserving system data
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import text
from src.mvp.database import get_db_session
from src.mvp.models import Student, Prediction, Institution, Intervention, GPTInsight, AuditLog

def clear_all_students():
    """Completely clear all student data from the database"""
    
    print("=== COMPLETE STUDENT DATA CLEARANCE ===")
    print()
    print("⚠️  WARNING: This will remove ALL student data from the database!")
    print("   This includes:")
    print("   - All student records")
    print("   - All predictions")
    print("   - All interventions")
    print("   - All GPT insights")
    print("   - Student-related audit logs")
    print()
    print("   This PRESERVES:")
    print("   - User accounts and authentication data")
    print("   - Institution/district data")
    print("   - Model metadata")
    print("   - System configurations")
    print()
    
    # Confirm with user
    confirm = input("Type 'CLEAR ALL' to confirm complete student data removal: ")
    if confirm != "CLEAR ALL":
        print("❌ Operation cancelled. No data was removed.")
        return
    
    print()
    print("🗑️  Proceeding with complete student data clearance...")
    print()

    with get_db_session() as db:
        print("📊 BEFORE CLEARANCE:")
        
        # Show current counts
        student_count = db.query(Student).count()
        prediction_count = db.query(Prediction).count()
        intervention_count = db.query(Intervention).count()
        gpt_insight_count = db.query(GPTInsight).count()
        
        print(f"  Students: {student_count}")
        print(f"  Predictions: {prediction_count}")
        print(f"  Interventions: {intervention_count}")
        print(f"  GPT Insights: {gpt_insight_count}")
        print()
        
        if student_count == 0:
            print("✅ Database is already clear of student data!")
            return
        
        print("🧹 CLEARING OPERATIONS:")
        
        try:
            # Step 1: Clear GPT insights (references students)
            if gpt_insight_count > 0:
                db.execute(text("DELETE FROM gpt_insights"))
                print(f"  🗑️  Removed {gpt_insight_count} GPT insights")
            
            # Step 2: Clear interventions (references students)
            if intervention_count > 0:
                db.execute(text("DELETE FROM interventions"))
                print(f"  🗑️  Removed {intervention_count} interventions")
            
            # Step 3: Clear predictions (references students)
            if prediction_count > 0:
                db.execute(text("DELETE FROM predictions"))
                print(f"  🗑️  Removed {prediction_count} predictions")
            
            # Step 4: Clear student-related audit logs
            audit_result = db.execute(text("""
                DELETE FROM audit_logs 
                WHERE entity_type = 'student' 
                   OR action LIKE '%student%' 
                   OR details LIKE '%student%'
            """))
            if audit_result.rowcount > 0:
                print(f"  🗑️  Removed {audit_result.rowcount} student-related audit logs")
            
            # Step 5: Clear all students
            db.execute(text("DELETE FROM students"))
            print(f"  🗑️  Removed {student_count} students")
            
            # Commit all changes
            db.commit()
            
            print()
            print("📊 AFTER CLEARANCE:")
            
            # Show final counts (should all be 0)
            final_student_count = db.query(Student).count()
            final_prediction_count = db.query(Prediction).count()
            final_intervention_count = db.query(Intervention).count()
            final_gpt_insight_count = db.query(GPTInsight).count()
            
            print(f"  Students: {final_student_count}")
            print(f"  Predictions: {final_prediction_count}")
            print(f"  Interventions: {final_intervention_count}")
            print(f"  GPT Insights: {final_gpt_insight_count}")
            
            print()
            if final_student_count == 0:
                print("✅ COMPLETE STUDENT DATA CLEARANCE SUCCESSFUL!")
                print("   Database is now clear of all student data.")
                print("   System data (institutions, users, model metadata) preserved.")
            else:
                print("⚠️  Warning: Some student data may remain.")
            
        except Exception as e:
            db.rollback()
            print(f"❌ ERROR during clearance: {e}")
            print("   Database changes have been rolled back.")
            return
        
        print()
        print("🔄 READY FOR FRESH DATA:")
        print("   You can now upload new student data via the web interface")
        print("   or API endpoints without conflicts.")

if __name__ == "__main__":
    clear_all_students()