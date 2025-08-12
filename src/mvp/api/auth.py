#!/usr/bin/env python3
"""
Database-backed Authentication API
Secure username/password authentication with PostgreSQL storage
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import bcrypt
import secrets
from datetime import datetime, timedelta
import logging

from src.mvp.database import get_db_session
from sqlalchemy.orm import Session

# Database dependency
def get_db() -> Session:
    with get_db_session() as session:
        yield session
from src.mvp.models import User, UserSession, Institution

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: Optional[str] = None

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_session_token() -> str:
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def get_current_user_from_session(request: Request, db: Session = Depends(get_db)):
    """Get user from database session token"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
        
    token = auth_header.split(" ")[1]
    
    # Find active session in database
    session = db.query(UserSession).filter(
        UserSession.session_token == token,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.now()
    ).first()
    
    if not session:
        return None
        
    # Update last activity
    session.last_activity = datetime.now()
    db.commit()
        
    return session.user

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Database-backed login endpoint"""
    try:
        username = login_data.username.strip()
        password = login_data.password
        
        # Basic validation
        if not username or not password:
            raise HTTPException(
                status_code=400, 
                detail="Username and password are required"
            )
            
        # Find user in database (search by username or email)
        user = db.query(User).filter(
            or_(User.username == username, User.email == username),
            User.is_active == True
        ).first()
        
        if not user:
            logger.warning(f"Login attempt with invalid username: {username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
            
        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Login attempt with wrong password for user: {username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
            
        # Create session token
        token = create_session_token()
        expires_at = datetime.now() + timedelta(hours=8)
        
        # Create session in database
        session = UserSession(
            user_id=user.id,
            session_token=token,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent", "")[:500],  # Limit length
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(session)
        
        # Update user last login
        user.last_login = datetime.now()
        db.commit()
        
        # Prepare user info for response
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "name": user.full_name,
            "institution_id": user.institution_id
        }
        
        logger.info(f"Successful login for user: {username} (ID: {user.id})")
        
        return LoginResponse(
            success=True,
            token=token,
            user=user_info,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during login"
        )

@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Database-backed logout endpoint"""
    try:
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Find and deactivate session in database
            session = db.query(UserSession).filter(
                UserSession.session_token == token,
                UserSession.is_active == True
            ).first()
            
            if session:
                session.is_active = False
                session.revoked_at = datetime.now()
                session.revoked_reason = "logout"
                db.commit()
                
                logger.info(f"User logged out: {session.user.username} (ID: {session.user_id})")
        
        return JSONResponse({
            "success": True,
            "message": "Logged out successfully"
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return JSONResponse({
            "success": True,  # Always succeed for logout
            "message": "Logged out"
        })

@router.get("/status")
async def auth_status(request: Request, db: Session = Depends(get_db)):
    """Check authentication status"""
    try:
        user = get_current_user_from_session(request, db)
        
        if user:
            user_info = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "name": user.full_name,
                "institution_id": user.institution_id
            }
            return JSONResponse({
                "authenticated": True,
                "user": user_info
            })
        else:
            return JSONResponse({
                "authenticated": False,
                "user": None
            })
            
    except Exception as e:
        logger.error(f"Auth status error: {e}")
        return JSONResponse({
            "authenticated": False,
            "user": None
        })