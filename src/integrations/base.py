#!/usr/bin/env python3
"""
Base LMS Integration class defining the interface for all LMS integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

class BaseLMSIntegration(ABC):
    """Base class for all LMS integrations"""
    
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    @abstractmethod
    async def authenticate(self, authorization_code: str) -> Dict[str, Any]:
        """Authenticate with the LMS using OAuth2 authorization code"""
        pass
    
    @abstractmethod
    async def refresh_token(self) -> Dict[str, Any]:
        """Refresh the access token"""
        pass
    
    @abstractmethod
    async def get_courses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of courses for the authenticated user or specific user"""
        pass
    
    @abstractmethod
    async def get_course_students(self, course_id: str) -> List[Dict[str, Any]]:
        """Get list of students enrolled in a course"""
        pass
    
    @abstractmethod
    async def get_course_assignments(self, course_id: str) -> List[Dict[str, Any]]:
        """Get list of assignments for a course"""
        pass
    
    @abstractmethod
    async def get_student_grades(self, course_id: str, student_id: str) -> Dict[str, Any]:
        """Get grades for a specific student in a course"""
        pass
    
    @abstractmethod
    async def get_course_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics data for a course"""
        pass
    
    @abstractmethod
    def convert_to_prediction_format(self, course_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert LMS data to the format expected by our prediction system"""
        pass
    
    def is_token_valid(self) -> bool:
        """Check if the current access token is valid"""
        if not self.access_token:
            return False
        if not self.token_expires_at:
            return True  # No expiration info, assume valid
        return datetime.now() < self.token_expires_at
    
    async def ensure_authenticated(self):
        """Ensure we have a valid access token, refresh if needed"""
        if not self.is_token_valid():
            if self.access_token:  # We have a token but it's expired
                await self.refresh_token()
            else:
                raise ValueError("No valid access token. Call authenticate() first.")

class LMSIntegrationError(Exception):
    """Base exception for LMS integration errors"""
    pass

class AuthenticationError(LMSIntegrationError):
    """Raised when authentication fails"""
    pass

class APIError(LMSIntegrationError):
    """Raised when API requests fail"""
    pass

class DataConversionError(LMSIntegrationError):
    """Raised when data conversion fails"""
    pass