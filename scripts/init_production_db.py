#!/usr/bin/env python3
"""
Production database initialization script
Handles PostgreSQL table creation and data migration
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def run_alembic_migrations():
    """Run Alembic migrations to create tables"""
    try:
        print("🔄 Running Alembic database migrations...")
        
        # Change to project root directory
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Alembic migrations completed successfully")
            print(result.stdout)
            return True
        else:
            print("❌ Alembic migrations failed:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("⚠️  Alembic not found, falling back to SQLAlchemy table creation")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  Alembic migration timed out")
        return False
    except Exception as e:
        print(f"⚠️  Alembic migration error: {e}")
        return False

def check_if_tables_exist():
    """Check if database tables already exist"""
    try:
        from mvp.database import get_engine
        from sqlalchemy import inspect
        
        engine = get_engine()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Check for key tables
        required_tables = ['institutions', 'students', 'predictions']
        existing_tables = [t for t in required_tables if t in tables]
        
        if len(existing_tables) == len(required_tables):
            print(f"✅ All tables already exist: {', '.join(tables)}")
            return True
        else:
            print(f"📋 Missing tables: {set(required_tables) - set(existing_tables)}")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check existing tables: {e}")
        return False

def create_tables_with_sqlalchemy():
    """Fallback: Create tables using SQLAlchemy (only if they don't exist)"""
    try:
        print("🔄 Creating tables with SQLAlchemy...")
        
        from mvp.database import init_database, check_database_health
        from mvp.models import Institution
        
        # Initialize database (this only creates tables if they don't exist)
        init_database()
        
        # Verify health
        if check_database_health():
            print("✅ Database tables verified")
            
            # Create default institution if it doesn't exist
            from mvp.database import get_db_session
            with get_db_session() as session:
                existing = session.query(Institution).filter_by(code="MVP_DEMO").first()
                if not existing:
                    default_institution = Institution(
                        name="MVP Demo Institution",
                        code="MVP_DEMO",
                        type="K12",
                        active=True
                    )
                    session.add(default_institution)
                    session.commit()
                    print("✅ Created default institution")
                else:
                    print("✅ Default institution already exists")
            
            return True
        else:
            print("❌ Database health check failed")
            return False
            
    except Exception as e:
        print(f"❌ SQLAlchemy table creation failed: {e}")
        return False

def main():
    """Main database initialization function"""
    print("🗄️  Checking Production Database Setup")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("⚠️  No DATABASE_URL found, skipping PostgreSQL setup")
        return True
    
    # Hide password in logs
    safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
    print(f"🔗 Database: {safe_url}")
    
    # First check if tables already exist
    if check_if_tables_exist():
        print("✅ Database tables already exist, skipping creation")
        return True
    
    print("📋 Tables missing, initializing database...")
    
    # Try Alembic first (preferred for production)
    if run_alembic_migrations():
        print("✅ Database initialized with Alembic")
        return True
    
    # Fallback to SQLAlchemy
    if create_tables_with_sqlalchemy():
        print("✅ Database initialized with SQLAlchemy")
        return True
    
    print("❌ Database initialization failed")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)