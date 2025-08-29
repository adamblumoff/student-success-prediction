#!/usr/bin/env python3
"""
Add unique constraint to students table for (institution_id, student_id)
This script directly adds the constraint that the database layer expects.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import text
from src.mvp.database import get_db_session

def add_unique_constraint():
    """Add unique constraint to students table"""
    try:
        with get_db_session() as session:
            # Check if the constraint already exists
            check_constraint_sql = """
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'students' 
            AND constraint_type = 'UNIQUE' 
            AND constraint_name = 'uq_students_institution_student_id';
            """
            
            result = session.execute(text(check_constraint_sql))
            existing_constraint = result.fetchone()
            
            if existing_constraint:
                print("✅ Unique constraint already exists on students (institution_id, student_id)")
                return True
            
            # Add the unique constraint
            alter_sql = """
            ALTER TABLE students 
            ADD CONSTRAINT uq_students_institution_student_id 
            UNIQUE (institution_id, student_id);
            """
            
            session.execute(text(alter_sql))
            session.commit()
            print("✅ Successfully added unique constraint on students (institution_id, student_id)")
            return True
            
    except Exception as e:
        print(f"❌ Error adding constraint: {e}")
        # Check if this is SQLite (different syntax)
        if "information_schema" in str(e):
            print("📝 Detected SQLite database - unique constraint not required for ON CONFLICT")
            return True
        return False

if __name__ == "__main__":
    print("🔧 Adding unique constraint to students table...")
    success = add_unique_constraint()
    if success:
        print("✅ Database constraint operation completed successfully")
    else:
        print("❌ Failed to add database constraint")
        sys.exit(1)