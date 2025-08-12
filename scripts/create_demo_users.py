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
    with get_db_session() as db:
        institution_id = create_demo_institution(db)
        
        demo_users = [
            {
                "username": "teacher",
                "email": "teacher@demo.com",
                "password": "demo123",
                "first_name": "Demo",
                "last_name": "Teacher",
                "role": "teacher"
            },
            {
                "username": "admin",
                "email": "admin@demo.com", 
                "password": "admin123",
                "first_name": "Demo",
                "last_name": "Administrator",
                "role": "admin"
            },
            {
                "username": "principal",
                "email": "principal@demo.com",
                "password": "principal123", 
                "first_name": "Demo",
                "last_name": "Principal",
                "role": "principal"
            }
        ]
        
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
        
    except Exception as e:
        print(f"❌ Error creating demo users: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)