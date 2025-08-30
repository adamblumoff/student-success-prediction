#!/usr/bin/env python3
"""
Verify Database Clearance
Double-check that all student data has been removed
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

def verify_clearance():
    """Verify that all student data has been cleared"""
    
    print("=== DATABASE CLEARANCE VERIFICATION ===")
    print()
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"🔗 Checking database: {database_url.split('@')[0]}@[hidden]")
    else:
        print("🔗 Checking SQLite: mvp_data.db")
    
    print()
    
    try:
        # Create engine and session using environment config
        if database_url:
            engine = create_engine(database_url)
        else:
            # Fallback to SQLite
            engine = create_engine('sqlite:///mvp_data.db')
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            print("📊 CURRENT DATA COUNTS:")
            
            # Check all student-related tables
            tables_to_check = [
                "students",
                "predictions", 
                "interventions",
                "gpt_insights"
            ]
            
            all_clear = True
            
            for table_name in tables_to_check:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    
                    if count > 0:
                        print(f"  ⚠️  {table_name}: {count} records (NOT CLEAR)")
                        all_clear = False
                    else:
                        print(f"  ✅ {table_name}: 0 records (CLEAR)")
                        
                except Exception as e:
                    if "no such table" in str(e).lower() or "does not exist" in str(e).lower():
                        print(f"  ✅ {table_name}: table doesn't exist (CLEAR)")
                    else:
                        print(f"  ❌ {table_name}: error checking - {e}")
                        all_clear = False
            
            print()
            print("📊 PRESERVED DATA COUNTS:")
            
            # Check preserved tables
            preserved_tables = [
                "institutions",
                "users", 
                "user_sessions",
                "model_metadata"
            ]
            
            for table_name in preserved_tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"  📋 {table_name}: {count} records (preserved)")
                except Exception as e:
                    if "no such table" in str(e).lower() or "does not exist" in str(e).lower():
                        print(f"  📋 {table_name}: table doesn't exist")
                    else:
                        print(f"  ⚠️  {table_name}: error checking - {e}")
            
            print()
            if all_clear:
                print("✅ VERIFICATION PASSED!")
                print("   All student data has been successfully cleared.")
                print("   Database is ready for fresh student uploads.")
            else:
                print("❌ VERIFICATION FAILED!")
                print("   Some student data remains in the database.")
            
    except Exception as e:
        print(f"❌ ERROR connecting to database: {e}")

if __name__ == "__main__":
    verify_clearance()