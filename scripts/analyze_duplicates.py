#!/usr/bin/env python3
"""
Database Duplicate Analysis Script
Identifies and reports duplicate records across all tables
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import text
from src.mvp.database import get_db_session
from src.mvp.models import Student, Prediction, Intervention, User, Institution

def analyze_duplicates():
    """Analyze all tables for duplicate records"""
    
    print("=== DATABASE DUPLICATE ANALYSIS ===")
    
    # Check if using PostgreSQL or SQLite
    database_url = os.getenv('DATABASE_URL', '')
    is_postgres = database_url.startswith('postgresql')
    db_type = "PostgreSQL" if is_postgres else "SQLite"
    print(f"📊 Database Type: {db_type}")
    print()
    
    with get_db_session() as db:
        # Analyze Students table
        print("📊 STUDENTS TABLE:")
        
        # Check for duplicate student_ids
        result = db.execute(text("""
            SELECT student_id, COUNT(*) as count 
            FROM students 
            WHERE student_id IS NOT NULL
            GROUP BY student_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)).fetchall()
        
        if result:
            print(f"  ❌ Found {len(result)} duplicate student_id values:")
            for row in result:
                print(f"     - student_id '{row.student_id}': {row.count} records")
        else:
            print("  ✅ No duplicate student_id values found")
        
        # Check total students
        total_students = db.execute(text("SELECT COUNT(*) as count FROM students")).fetchone().count
        print(f"  📈 Total students: {total_students}")
        print()
        
        # Analyze Predictions table
        print("📊 PREDICTIONS TABLE:")
        
        # Check for duplicate student_id predictions
        result = db.execute(text("""
            SELECT student_id, COUNT(*) as count 
            FROM predictions 
            GROUP BY student_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)).fetchall()
        
        if result:
            print(f"  ❌ Found {len(result)} students with multiple predictions:")
            for row in result:
                print(f"     - student_id {row.student_id}: {row.count} predictions")
        else:
            print("  ✅ No duplicate student predictions found")
        
        total_predictions = db.execute(text("SELECT COUNT(*) as count FROM predictions")).fetchone().count
        print(f"  📈 Total predictions: {total_predictions}")
        print()
        
        # Analyze Interventions table
        print("📊 INTERVENTIONS TABLE:")
        
        # Check for exact duplicate interventions (same student, type, title, date)
        if is_postgres:
            # PostgreSQL syntax
            result = db.execute(text("""
                SELECT student_id, intervention_type, title, created_at::date, COUNT(*) as count 
                FROM interventions 
                GROUP BY student_id, intervention_type, title, created_at::date 
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)).fetchall()
        else:
            # SQLite syntax
            result = db.execute(text("""
                SELECT student_id, intervention_type, title, date(created_at) as created_date, COUNT(*) as count 
                FROM interventions 
                GROUP BY student_id, intervention_type, title, date(created_at) 
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)).fetchall()
        
        if result:
            print(f"  ❌ Found {len(result)} groups of duplicate interventions:")
            for row in result:
                if is_postgres:
                    print(f"     - Student {row.student_id}, {row.intervention_type}, '{row.title}', {row.created_at}: {row.count} records")
                else:
                    print(f"     - Student {row.student_id}, {row.intervention_type}, '{row.title}', {row.created_date}: {row.count} records")
        else:
            print("  ✅ No duplicate interventions found")
        
        total_interventions = db.execute(text("SELECT COUNT(*) as count FROM interventions")).fetchone().count
        print(f"  📈 Total interventions: {total_interventions}")
        print()
        
        # Analyze Users table
        print("📊 USERS TABLE:")
        
        # Check for duplicate emails
        result = db.execute(text("""
            SELECT email, COUNT(*) as count 
            FROM users 
            WHERE email IS NOT NULL
            GROUP BY email 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)).fetchall()
        
        if result:
            print(f"  ❌ Found {len(result)} duplicate email addresses:")
            for row in result:
                print(f"     - email '{row.email}': {row.count} accounts")
        else:
            print("  ✅ No duplicate email addresses found")
        
        total_users = db.execute(text("SELECT COUNT(*) as count FROM users")).fetchone().count
        print(f"  📈 Total users: {total_users}")
        print()
        
        # Analyze Institutions table
        print("📊 INSTITUTIONS TABLE:")
        
        # Check for duplicate institution codes
        result = db.execute(text("""
            SELECT code, COUNT(*) as count 
            FROM institutions 
            WHERE code IS NOT NULL
            GROUP BY code 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)).fetchall()
        
        if result:
            print(f"  ❌ Found {len(result)} duplicate institution codes:")
            for row in result:
                print(f"     - code '{row.code}': {row.count} institutions")
        else:
            print("  ✅ No duplicate institution codes found")
        
        total_institutions = db.execute(text("SELECT COUNT(*) as count FROM institutions")).fetchone().count
        print(f"  📈 Total institutions: {total_institutions}")
        print()
        
        print("=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    try:
        analyze_duplicates()
    except Exception as e:
        print(f"❌ Error analyzing duplicates: {e}")
        sys.exit(1)