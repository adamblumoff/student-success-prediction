#!/usr/bin/env python3
"""
Google Classroom Authentication Endpoints

Handles OAuth2 authentication flow for Google Classroom integration.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse  
from pydantic import BaseModel
from typing import Dict, Any
import logging

from ..shared.google_deps import get_google_classroom_integration, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class AuthStartRequest(BaseModel):
    """Request model for starting OAuth2 flow"""
    redirect_uri: str
    

@router.post("/start")
async def start_google_auth(
    request: AuthStartRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start Google Classroom OAuth2 authentication flow"""
    try:
        google_classroom = get_google_classroom_integration()
        
        # Generate authorization URL
        auth_url = google_classroom.get_authorization_url(request.redirect_uri)
        
        return JSONResponse({
            'status': 'success',
            'auth_url': auth_url,
            'message': 'Navigate to auth_url to complete authentication'
        })
        
    except Exception as e:
        logger.error(f"Error starting Google auth: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication initiation failed: {str(e)}")
        

@router.post("/complete")  
async def complete_google_auth(
    auth_code: str,
    current_user: dict = Depends(get_current_user)
):
    """Complete Google Classroom OAuth2 authentication"""
    try:
        google_classroom = get_google_classroom_integration()
        
        # Exchange code for credentials
        result = google_classroom.complete_oauth_flow(auth_code)
        
        if result['success']:
            return JSONResponse({
                'status': 'authenticated',
                'user_info': result.get('user_info', {}),
                'message': 'Google Classroom authentication successful'
            })
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Authentication failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error completing Google auth: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication completion failed: {str(e)}")