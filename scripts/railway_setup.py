#!/usr/bin/env python3
"""
Railway Database Setup Script
Runs migrations and creates admin user
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_migrations():
    """Run Alembic migrations"""
    print("🔧 Running database migrations...")
    try:
        # Wait for database to be ready
        import time
        print("⏳ Waiting for database connection...")
        time.sleep(5)
        
        # Run alembic upgrade head
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Migration failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False
    
    return True

def create_admin_user():
    """Create admin user"""
    print("👤 Creating admin user...")
    try:
        from src.mvp.database import get_db_session
        from mvp.models import User, Institution
        from werkzeug.security import generate_password_hash
        import datetime
        
        with get_db_session() as db:
            # Get or create institution
            institution = db.query(Institution).first()
            if not institution:
                institution = Institution(
                    name='Demo Educational District',
                    code='DEMO_DIST',
                    type='K12',
                    active=True
                )
                db.add(institution)
                db.flush()
                print("🏫 Created demo institution")
            
            # Check if admin exists
            existing = db.query(User).filter_by(username='admin').first()
            if not existing:
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
                print('✅ Admin user created!')
                print('   Username: admin')
                print('   Password: admin123')
            else:
                print('ℹ️ Admin user already exists')
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Railway Database Setup")
    print("=" * 40)
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    # Create admin user
    if not create_admin_user():
        sys.exit(1)
    
    print("=" * 40)
    print("✅ Setup completed successfully!")
    print("You can now log in with:")
    print("  Username: admin")
    print("  Password: admin123")