#!/usr/bin/env python3
"""
Simple Student Data Clear Script
Uses raw SQL to clear student data regardless of schema mismatches
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import text
from src.mvp.database import get_db_session

def simple_clear_students():
    """Simple clear all student data using raw SQL"""
    
    print("=== SIMPLE STUDENT DATA CLEARANCE ===")
    print()
    print("⚠️  WARNING: This will remove ALL student data!")
    print("   Preserves: Users, Institutions, Model metadata")
    print()
    
    # Auto-confirm for testing purposes
    print("🗑️  Proceeding with student data clearance...")
    print()

    with get_db_session() as db:
        print("🧹 CLEARING OPERATIONS:")
        
        try:
            # List of tables to clear (in dependency order)
            tables_to_clear = [
                "gpt_insights",      # References students
                "interventions",     # References students  
                "predictions",       # References students
                "students"           # Main student table
            ]
            
            total_removed = 0
            
            for table_name in tables_to_clear:
                try:
                    # Check if table exists and get count
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    
                    if count > 0:
                        # Clear the table
                        db.execute(text(f"DELETE FROM {table_name}"))
                        print(f"  🗑️  Removed {count} records from {table_name}")
                        total_removed += count
                    else:
                        print(f"  ✅ {table_name} already empty")
                        
                except Exception as e:
                    if "no such table" in str(e).lower():
                        print(f"  ⏭️  {table_name} table doesn't exist, skipping")
                    else:
                        print(f"  ⚠️  Error with {table_name}: {e}")
            
            # Clear student-related audit logs if audit_logs table exists
            try:
                result = db.execute(text("""
                    DELETE FROM audit_logs 
                    WHERE entity_type = 'student' 
                       OR action LIKE '%student%' 
                       OR details LIKE '%student%'
                """))
                if result.rowcount > 0:
                    print(f"  🗑️  Removed {result.rowcount} student-related audit logs")
                    total_removed += result.rowcount
            except Exception as e:
                if "no such table" not in str(e).lower():
                    print(f"  ⚠️  Error clearing audit logs: {e}")
            
            # Commit all changes
            db.commit()
            
            print()
            print("✅ STUDENT DATA CLEARANCE COMPLETED!")
            print(f"   Total records removed: {total_removed}")
            print("   Database is ready for fresh student data.")
            
        except Exception as e:
            db.rollback()
            print(f"❌ ERROR during clearance: {e}")
            print("   Database changes have been rolled back.")

if __name__ == "__main__":
    simple_clear_students()