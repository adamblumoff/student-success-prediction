#!/usr/bin/env python3
"""
One-time manual database setup script
Run this ONCE when you first connect PostgreSQL to create all tables
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """One-time database setup"""
    print("🗄️  ONE-TIME DATABASE SETUP")
    print("=" * 50)
    print("This script will create all database tables and initial data.")
    print("⚠️  Only run this ONCE when you first connect PostgreSQL!")
    print()
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not set")
        print()
        print("To set it:")
        print("export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
        return False
    
    # Hide password in logs
    safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
    print(f"🔗 Database: {safe_url}")
    print()
    
    # Import after setting path
    from mvp.database import init_database, check_database_health, get_db_session
    from mvp.models import Institution
    
    try:
        print("1️⃣  Creating database tables...")
        init_database()
        print("✅ Tables created successfully")
        
        print("2️⃣  Verifying database connection...")
        if not check_database_health():
            raise Exception("Database health check failed")
        print("✅ Database connection verified")
        
        print("3️⃣  Creating default institution...")
        with get_db_session() as session:
            # Check if default institution already exists
            existing = session.query(Institution).filter_by(code="MVP_DEMO").first()
            if existing:
                print("✅ Default institution already exists")
            else:
                default_institution = Institution(
                    name="Student Success Demo",
                    code="MVP_DEMO", 
                    type="K12",
                    active=True
                )
                session.add(default_institution)
                session.commit()
                print("✅ Created default institution")
        
        print()
        print("🎉 DATABASE SETUP COMPLETE!")
        print("=" * 50)
        print("✅ All tables created")
        print("✅ Default data initialized") 
        print("✅ System ready for production use")
        print()
        print("📋 Next steps:")
        print("1. Deploy your app to Render")
        print("2. Your app will automatically use the PostgreSQL database")
        print("3. File uploads will now be saved to PostgreSQL")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Verify your DATABASE_URL is correct")
        print("2. Ensure PostgreSQL database exists")
        print("3. Check database permissions")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)