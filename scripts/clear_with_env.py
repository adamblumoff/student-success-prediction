#!/usr/bin/env python3
"""
Clear Student Data Using .env Configuration
Properly connects to the database specified in .env file
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

def clear_with_env():
    """Clear student data using proper .env database configuration"""
    
    print("=== STUDENT DATA CLEARANCE WITH .ENV CONFIG ===")
    print()
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"🔗 Using database: {database_url.split('@')[0]}@[hidden]")
    else:
        print("🔗 Using SQLite fallback: mvp_data.db")
    
    print()
    print("⚠️  WARNING: This will remove ALL student data from the configured database!")
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
            print("🧹 CLEARING OPERATIONS:")
            
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
                        result = db.execute(text(f"DELETE FROM {table_name}"))
                        deleted_count = result.rowcount if hasattr(result, 'rowcount') else count
                        print(f"  🗑️  Removed {deleted_count} records from {table_name}")
                        total_removed += deleted_count
                    else:
                        print(f"  ✅ {table_name} already empty")
                        
                except Exception as e:
                    if "no such table" in str(e).lower() or "does not exist" in str(e).lower():
                        print(f"  ⏭️  {table_name} table doesn't exist, skipping")
                    else:
                        print(f"  ⚠️  Error with {table_name}: {e}")
            
            # Try to clear audit logs if they exist
            try:
                # First check what columns exist in audit_logs
                columns_result = db.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'audit_logs'
                """))
                columns = [row[0] for row in columns_result.fetchall()]
                
                if 'entity_type' in columns:
                    result = db.execute(text("""
                        DELETE FROM audit_logs 
                        WHERE entity_type = 'student' 
                           OR action LIKE '%student%' 
                           OR details LIKE '%student%'
                    """))
                    if result.rowcount > 0:
                        print(f"  🗑️  Removed {result.rowcount} student-related audit logs")
                        total_removed += result.rowcount
                else:
                    # Fallback for simpler audit log structure
                    result = db.execute(text("DELETE FROM audit_logs"))
                    if result.rowcount > 0:
                        print(f"  🗑️  Removed {result.rowcount} audit logs (all)")
                        total_removed += result.rowcount
                        
            except Exception as e:
                if "information_schema" not in str(e).lower():
                    print(f"  ⚠️  Could not clear audit logs: {e}")
            
            # Commit all changes
            db.commit()
            
            print()
            print("📊 VERIFICATION:")
            
            # Verify clearance
            verification_passed = True
            for table_name in ["students", "predictions", "interventions", "gpt_insights"]:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    if count > 0:
                        print(f"  ⚠️  {table_name} still has {count} records!")
                        verification_passed = False
                    else:
                        print(f"  ✅ {table_name} confirmed empty")
                except Exception as e:
                    if "no such table" in str(e).lower() or "does not exist" in str(e).lower():
                        print(f"  ✅ {table_name} table doesn't exist")
            
            print()
            if verification_passed:
                print("✅ STUDENT DATA CLEARANCE COMPLETED SUCCESSFULLY!")
                print(f"   Total records removed: {total_removed}")
                print("   All student-related data has been cleared.")
            else:
                print("⚠️  CLEARANCE INCOMPLETE - Some data may remain")
            
            print("   Preserved: User accounts, institutions, model metadata")
            
    except Exception as e:
        print(f"❌ ERROR connecting to database: {e}")
        print("   Make sure the database server is running and credentials are correct.")

if __name__ == "__main__":
    clear_with_env()