#!/usr/bin/env python3
"""
Direct Database Setup - Creates tables without Alembic
Simple and reliable for Railway deployment
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_database():
    """Create all tables directly using SQLAlchemy"""
    print("🚀 Direct Database Setup Starting...")
    print("=" * 50)
    
    try:
        from src.mvp.database import engine, Base
        from src.mvp.models import (
            Institution, Student, User, Prediction, 
            Intervention, GPTInsight, AuditLog, UserSession
        )
        import time
        
        # Wait for database
        print("⏳ Waiting for database connection...")
        time.sleep(3)
        
        # Test connection
        print("🔍 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful!")
        
        # Drop and recreate all tables (clean slate)
        print("🗑️ Dropping existing tables if any...")
        Base.metadata.drop_all(bind=engine)
        print("✅ Old tables dropped")
        
        # Create all tables
        print("🔨 Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        print("\n📋 Created tables:")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        for table_name in inspector.get_table_names():
            print(f"   ✓ {table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_initial_data():
    """Create institution and admin user"""
    print("\n👤 Creating initial data...")
    
    try:
        from src.mvp.database import get_db_session
        from src.mvp.models import Institution, User
        from werkzeug.security import generate_password_hash
        import datetime
        
        with get_db_session() as db:
            # Create institution
            institution = Institution(
                name='Demo Educational District',
                code='DEMO_DIST',
                type='K12',
                active=True
            )
            db.add(institution)
            db.flush()
            print("🏫 Created institution: Demo Educational District")
            
            # Create admin user
            admin = User(
                institution_id=institution.id,
                username='admin',
                email='admin@school.edu',
                full_name='System Administrator',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                is_active=True,
                created_at=datetime.datetime.now()
            )
            db.add(admin)
            db.commit()
            
            print("✅ Created admin user:")
            print("   Username: admin")
            print("   Password: admin123")
            
            # Verify data
            user_count = db.query(User).count()
            inst_count = db.query(Institution).count()
            print(f"\n📊 Database contains:")
            print(f"   • {inst_count} institution(s)")
            print(f"   • {user_count} user(s)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating initial data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 Railway Direct Database Setup")
    print("=" * 50)
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed!")
        sys.exit(1)
    
    # Create initial data
    if not create_initial_data():
        print("\n❌ Initial data creation failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("You can now log in with:")
    print("  Username: admin")
    print("  Password: admin123")
    print("=" * 50)