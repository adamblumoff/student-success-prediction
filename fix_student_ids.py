#!/usr/bin/env python3
"""
Fix student ID mismatch for bulk intervention system
Add students 1001, 1002, 1003 to database so UI selection works
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/student_success")

def fix_student_ids():
    """Add missing students to database"""
    print("🔧 Fixing student ID mismatch for bulk intervention system")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check current students
        result = session.execute(text("SELECT id, student_id FROM students ORDER BY id"))
        existing_students = result.fetchall()
        
        print(f"📊 Current students in database: {len(existing_students)}")
        for student in existing_students:
            print(f"   DB ID: {student[0]}, Student ID: {student[1]}")
        
        # Get institution ID (assuming MVP_DEMO institution exists)
        inst_result = session.execute(text("SELECT id FROM institutions WHERE code = 'MVP_DEMO' LIMIT 1"))
        institution = inst_result.fetchone()
        
        if not institution:
            print("❌ MVP_DEMO institution not found")
            return False
            
        institution_id = institution[0]
        print(f"✅ Using institution ID: {institution_id}")
        
        # Students we need for the UI (matching display IDs)
        needed_students = [
            (1001, 'Demo Student 1001', 9),
            (1002, 'Demo Student 1002', 10), 
            (1003, 'Demo Student 1003', 11)
        ]
        
        added_count = 0
        for student_id, name, grade in needed_students:
            # Check if student already exists
            check_result = session.execute(
                text("SELECT id FROM students WHERE student_id = :sid"),
                {"sid": str(student_id)}
            )
            existing = check_result.fetchone()
            
            if existing:
                print(f"✅ Student {student_id} already exists (DB ID: {existing[0]})")
            else:
                # Add new student
                session.execute(text("""
                    INSERT INTO students (institution_id, student_id, name, grade_level, created_at, updated_at)
                    VALUES (:inst_id, :student_id, :name, :grade, NOW(), NOW())
                """), {
                    "inst_id": institution_id,
                    "student_id": str(student_id),
                    "name": name,
                    "grade": grade
                })
                added_count += 1
                print(f"➕ Added student {student_id}: {name}")
        
        session.commit()
        
        # Show final state
        print(f"\n✅ Added {added_count} new students")
        
        # Get updated student list with database IDs
        final_result = session.execute(text("""
            SELECT id, student_id, name FROM students 
            WHERE student_id IN ('1001', '1002', '1003', '36', '37')
            ORDER BY id
        """))
        final_students = final_result.fetchall()
        
        print("\n📋 Students now available for bulk intervention:")
        for student in final_students:
            print(f"   DB ID: {student[0]} → Student ID: {student[1]} ({student[2]})")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing student IDs: {e}")
        return False

def test_bulk_with_correct_ids():
    """Test bulk intervention with the correct student IDs"""
    import requests
    
    print("\n🧪 Testing bulk intervention with correct student IDs")
    
    # First get the database IDs for students 1001, 1002, 1003
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        result = session.execute(text("""
            SELECT id, student_id FROM students 
            WHERE student_id IN ('1001', '1002', '1003')
            ORDER BY student_id
        """))
        students = result.fetchall()
        session.close()
        
        if not students:
            print("❌ No students found with IDs 1001, 1002, 1003")
            return
            
        database_ids = [student[0] for student in students]
        print(f"📋 Using database IDs: {database_ids}")
        
        # Test bulk creation
        bulk_data = {
            "student_ids": database_ids,
            "intervention_type": "academic_support", 
            "title": "Fixed ID Test - Math Support",
            "description": "Testing with correct database IDs",
            "priority": "medium"
        }
        
        response = requests.post(
            "http://localhost:8001/api/interventions/bulk/create",
            json=bulk_data,
            headers={
                "Authorization": "Bearer test-key",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bulk creation successful: {result['successful']}/{result['total_requested']}")
            print(f"   Execution time: {result['execution_time']}s")
            
            if result['failed'] > 0:
                print("❌ Some failures occurred:")
                for item in result.get('results', []):
                    if not item['success']:
                        print(f"   Student {item['id']}: {item['error_message']}")
        else:
            print(f"❌ Bulk creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing bulk intervention: {e}")

def main():
    print("=" * 60)
    print("STUDENT ID MISMATCH FIX")
    print("=" * 60)
    
    # Fix the student IDs
    if fix_student_ids():
        # Test the bulk system
        test_bulk_with_correct_ids()
        print("\n🎉 Student ID mismatch fixed!")
        print("   The bulk intervention system should now work correctly.")
    else:
        print("\n❌ Failed to fix student ID mismatch")
    
    print("=" * 60)

if __name__ == "__main__":
    main()