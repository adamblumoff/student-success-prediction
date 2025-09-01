#!/usr/bin/env python3
"""
Create demo users for the authentication system
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.mvp.database import get_db_session
from src.mvp.models import User, Institution
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_demo_institution(db):
    """Create or get demo institution"""
    # Check if demo institution exists
    institution = db.query(Institution).filter(
        Institution.code == "MVP_DEMO"
    ).first()
    
    if not institution:
        institution = Institution(
            name="Demo Educational District",
            code="MVP_DEMO",
            type="K12",
            timezone="America/New_York",
            active=True
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        print(f"✅ Created demo institution: {institution.name} (ID: {institution.id})")
    else:
        print(f"✅ Using existing institution: {institution.name} (ID: {institution.id})")
    
    return institution.id

def create_demo_users():
    """Create demo users"""
    # Security check: Prevent demo user creation in production
    environment = os.getenv('ENVIRONMENT', 'unknown').lower()
    development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
    
    if environment == 'production' and not development_mode:
        print("❌ Demo user creation is disabled in production environment")
        print("   This is a security measure to prevent weak credentials in production")
        return
    
    # Get demo users from environment variable (format: username:password,username:password)
    demo_users_env = os.getenv('DEMO_USERS', '')
    if not demo_users_env:
        print("❌ DEMO_USERS environment variable not set")
        print("   Please set DEMO_USERS in format: admin:SecurePassword123!,demo:AnotherSecurePassword!")
        return
    
    with get_db_session() as db:
        institution_id = create_demo_institution(db)
        
        # Parse demo users from environment variable
        demo_users = []
        try:
            user_pairs = demo_users_env.split(',')
            for pair in user_pairs:
                if ':' not in pair:
                    continue
                username, password = pair.strip().split(':', 1)
                
                # Map usernames to roles and details
                role_mapping = {
                    'admin': {'role': 'admin', 'first_name': 'Demo', 'last_name': 'Administrator'},
                    'teacher': {'role': 'teacher', 'first_name': 'Demo', 'last_name': 'Teacher'}, 
                    'educator': {'role': 'teacher', 'first_name': 'Demo', 'last_name': 'Educator'},
                    'principal': {'role': 'principal', 'first_name': 'Demo', 'last_name': 'Principal'},
                    'demo': {'role': 'teacher', 'first_name': 'Demo', 'last_name': 'User'}
                }
                
                user_info = role_mapping.get(username.lower(), {'role': 'teacher', 'first_name': 'Demo', 'last_name': 'User'})
                
                demo_users.append({
                    "username": username,
                    "email": f"{username}@demo.com",
                    "password": password,
                    "first_name": user_info['first_name'],
                    "last_name": user_info['last_name'],
                    "role": user_info['role']
                })
        except Exception as e:
            print(f"❌ Error parsing DEMO_USERS environment variable: {e}")
            print("   Format should be: admin:SecurePassword123!,demo:AnotherSecurePassword!")
            return
        
        created_count = 0
        
        for user_data in demo_users:
            # Check if user already exists
            existing_user = db.query(User).filter(
                User.username == user_data["username"]
            ).first()
            
            if existing_user:
                print(f"⚠️  User '{user_data['username']}' already exists")
                continue
                
            # Create new user
            hashed_password = hash_password(user_data["password"])
            
            new_user = User(
                institution_id=institution_id,
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hashed_password,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=user_data["role"],
                is_active=True,
                is_verified=True
            )
            
            db.add(new_user)
            created_count += 1
            
            print(f"✅ Created user: {user_data['username']} ({user_data['first_name']} {user_data['last_name']}) - {user_data['role']}")
        
        if created_count > 0:
            db.commit()
            print(f"\n🎉 Successfully created {created_count} demo users!")
        else:
            print("\n📌 All demo users already exist")
        
        print("\n🔐 Demo Login Credentials:")
        for user_data in demo_users:
            print(f"   Username: {user_data['username']} | Password: {user_data['password']} | Role: {user_data['role']}")

if __name__ == "__main__":
    try:
        print("🚀 Creating demo users...")
        create_demo_users()
        print("\n✅ Demo user creation complete!")
        
    except (OSError, IOError) as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error creating demo users: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)