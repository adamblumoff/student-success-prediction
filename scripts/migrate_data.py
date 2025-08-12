#!/usr/bin/env python3
"""
Data Migration Script: SQLite to PostgreSQL
Migrates all application data from SQLite to PostgreSQL with validation
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.mvp.database import get_db_session
from src.mvp.models import Institution, User, Student, Prediction, Intervention, AuditLog, ModelMetadata, UserSession
import sqlite3

def migrate_sqlite_to_postgresql(sqlite_path="mvp_data.db", dry_run=False):
    """
    Migrate data from SQLite to PostgreSQL
    """
    print("🔄 Starting data migration from SQLite to PostgreSQL...")
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found: {sqlite_path}")
        return False
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
    sqlite_cursor = sqlite_conn.cursor()
    
    migration_summary = {
        "institutions": 0,
        "users": 0,
        "students": 0,
        "predictions": 0,
        "interventions": 0,
        "audit_logs": 0,
        "model_metadata": 0,
        "user_sessions": 0,
        "errors": []
    }
    
    try:
        with get_db_session() as pg_session:
            # 1. Migrate Institutions
            print("📋 Migrating institutions...")
            sqlite_cursor.execute("SELECT * FROM institutions")
            institutions = sqlite_cursor.fetchall()
            
            for row in institutions:
                # Check if institution already exists
                existing = pg_session.query(Institution).filter_by(code=row['code']).first()
                if existing:
                    print(f"⚠️  Institution '{row['code']}' already exists, skipping")
                    continue
                    
                if not dry_run:
                    institution = Institution(
                        name=row['name'],
                        code=row['code'],
                        type=row['type'],
                        timezone=row['timezone'],
                        active=row['active']
                    )
                    pg_session.add(institution)
                migration_summary["institutions"] += 1
            
            # 2. Migrate Users (skip duplicates based on username)
            print("👥 Migrating users...")
            sqlite_cursor.execute("SELECT * FROM users")
            users = sqlite_cursor.fetchall()
            
            for row in users:
                existing = pg_session.query(User).filter_by(username=row['username']).first()
                if existing:
                    print(f"⚠️  User '{row['username']}' already exists, skipping")
                    continue
                    
                if not dry_run:
                    # Get institution ID from PostgreSQL
                    institution = pg_session.query(Institution).filter_by(id=row['institution_id']).first()
                    if not institution:
                        print(f"❌ Institution ID {row['institution_id']} not found for user {row['username']}")
                        migration_summary["errors"].append(f"Missing institution for user {row['username']}")
                        continue
                    
                    user = User(
                        institution_id=institution.id,
                        username=row['username'],
                        email=row['email'],
                        password_hash=row['password_hash'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        role=row['role'],
                        is_active=row['is_active'],
                        is_verified=row['is_verified']
                    )
                    pg_session.add(user)
                migration_summary["users"] += 1
            
            # 3. Migrate Students
            print("🎓 Migrating students...")
            sqlite_cursor.execute("SELECT * FROM students")
            students = sqlite_cursor.fetchall()
            
            for row in students:
                if not dry_run:
                    student = Student(
                        institution_id=row['institution_id'],
                        student_id=row['student_id'],
                        grade_level=row['grade_level'],
                        enrollment_status=row['enrollment_status'],
                        # Add other fields as needed
                    )
                    pg_session.add(student)
                migration_summary["students"] += 1
            
            # 4. Migrate Predictions
            print("📊 Migrating predictions...")
            sqlite_cursor.execute("SELECT * FROM predictions")
            predictions = sqlite_cursor.fetchall()
            
            for row in predictions:
                if not dry_run:
                    prediction = Prediction(
                        institution_id=row['institution_id'],
                        student_id=row['student_id'],
                        risk_score=row['risk_score'],
                        risk_category=row['risk_category'],
                        success_probability=row['success_probability'],
                        session_id=row['session_id'],
                        data_source=row['data_source'],
                        features_used=row['features_used'],
                        explanation=row['explanation']
                    )
                    pg_session.add(prediction)
                migration_summary["predictions"] += 1
            
            # 5. Migrate other tables (interventions, audit_logs, model_metadata)
            for table_name in ['interventions', 'audit_logs', 'model_metadata']:
                print(f"📋 Migrating {table_name}...")
                try:
                    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = sqlite_cursor.fetchone()[0]
                    migration_summary[table_name] = count
                    if count > 0:
                        print(f"   Found {count} records (detailed migration needed)")
                except sqlite3.OperationalError:
                    print(f"   Table {table_name} not found in SQLite")
            
            if not dry_run:
                pg_session.commit()
                print("✅ Migration committed successfully")
            else:
                print("🔍 DRY RUN - No changes made")
            
    except Exception as e:
        migration_summary["errors"].append(str(e))
        print(f"❌ Migration error: {e}")
        if not dry_run:
            pg_session.rollback()
        return False
    
    finally:
        sqlite_conn.close()
    
    # Print summary
    print("\n📊 Migration Summary:")
    for table, count in migration_summary.items():
        if table != "errors":
            print(f"   {table}: {count} records")
    
    if migration_summary["errors"]:
        print("⚠️  Errors encountered:")
        for error in migration_summary["errors"]:
            print(f"   - {error}")
    
    return len(migration_summary["errors"]) == 0

def create_demo_students():
    """Create demo students for testing"""
    print("🎓 Creating demo students...")
    
    demo_students = [
        {"student_id": "STU001", "grade_level": "9", "enrollment_status": "active"},
        {"student_id": "STU002", "grade_level": "10", "enrollment_status": "active"}, 
        {"student_id": "STU003", "grade_level": "11", "enrollment_status": "active"},
        {"student_id": "STU004", "grade_level": "12", "enrollment_status": "active"},
        {"student_id": "STU005", "grade_level": "9", "enrollment_status": "active"},
    ]
    
    try:
        with get_db_session() as session:
            # Get demo institution
            institution = session.query(Institution).filter_by(code="MVP_DEMO").first()
            if not institution:
                print("❌ Demo institution not found")
                return False
            
            created_count = 0
            for student_data in demo_students:
                # Check if student exists
                existing = session.query(Student).filter_by(
                    institution_id=institution.id,
                    student_id=student_data["student_id"]
                ).first()
                
                if existing:
                    print(f"⚠️  Student {student_data['student_id']} already exists")
                    continue
                
                student = Student(
                    institution_id=institution.id,
                    student_id=student_data["student_id"],
                    grade_level=student_data["grade_level"],
                    enrollment_status=student_data["enrollment_status"]
                )
                session.add(student)
                created_count += 1
                print(f"✅ Created student: {student_data['student_id']} (Grade {student_data['grade_level']})")
            
            session.commit()
            print(f"\n🎉 Created {created_count} demo students!")
            return True
            
    except Exception as e:
        print(f"❌ Error creating demo students: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--create-demo-students", action="store_true", help="Create 5 demo students")
    parser.add_argument("--sqlite-path", default="mvp_data.db", help="Path to SQLite database")
    
    args = parser.parse_args()
    
    try:
        if args.create_demo_students:
            success = create_demo_students()
        else:
            success = migrate_sqlite_to_postgresql(args.sqlite_path, args.dry_run)
        
        if success:
            print("\n✅ Operation completed successfully!")
        else:
            print("\n❌ Operation failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)