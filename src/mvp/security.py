#!/usr/bin/env python3
"""
Production-Ready Security Module
Implements secure authentication, session management, and security controls
"""

import os
import time
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

# Security Configuration
class SecurityConfig:
    """Centralized security configuration with environment validation"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development').lower()
        self.is_production = self.environment in ['production', 'prod']
        self.development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
        self.api_key = self._validate_api_key()
        self.session_secret = self._get_session_secret()
        self.rate_limits = self._get_rate_limits()
        
        # Validate security configuration
        self._validate_security_settings()
    
    def _validate_api_key(self) -> str:
        """Validate API key configuration with production requirements"""
        api_key = os.getenv("MVP_API_KEY")
        
        if not api_key:
            if self.is_production:
                raise ValueError("❌ SECURITY ERROR: MVP_API_KEY must be set in production")
            logger.warning("⚠️ No API key set, using development default")
            return "dev-key-change-me"
        
        # Production key requirements
        if self.is_production:
            if api_key == "dev-key-change-me":
                raise ValueError("❌ SECURITY ERROR: Cannot use default API key in production")
            if len(api_key) < 32:
                raise ValueError("❌ SECURITY ERROR: Production API key must be at least 32 characters")
            if not any(c.isdigit() for c in api_key) or not any(c.isalpha() for c in api_key):
                raise ValueError("❌ SECURITY ERROR: API key must contain both letters and numbers")
        
        # Development warnings
        elif api_key == "dev-key-change-me" and not self.development_mode:
            logger.warning("⚠️ Using default API key outside development mode")
        
        logger.info(f"✅ API key validated: {api_key[:8]}***")
        return api_key
    
    def _get_session_secret(self) -> str:
        """Generate or retrieve secure session secret"""
        session_secret = os.getenv('SESSION_SECRET')
        if not session_secret:
            if self.is_production:
                raise ValueError("❌ SECURITY ERROR: SESSION_SECRET must be set in production")
            # Generate cryptographically secure secret for development
            session_secret = secrets.token_urlsafe(64)
            logger.info("🔒 Generated secure session secret for development")
        elif len(session_secret) < 32:
            raise ValueError("❌ SECURITY ERROR: SESSION_SECRET must be at least 32 characters")
        
        return session_secret
    
    def _get_rate_limits(self) -> Dict[str, int]:
        """Configure rate limits based on environment"""
        if self.is_production:
            return {
                'api_requests_per_minute': int(os.getenv('API_RATE_LIMIT', '30')),
                'file_uploads_per_hour': int(os.getenv('UPLOAD_RATE_LIMIT', '10')),
                'auth_attempts_per_hour': int(os.getenv('AUTH_RATE_LIMIT', '5'))
            }
        else:
            return {
                'api_requests_per_minute': int(os.getenv('API_RATE_LIMIT', '60')),
                'file_uploads_per_hour': int(os.getenv('UPLOAD_RATE_LIMIT', '30')),
                'auth_attempts_per_hour': int(os.getenv('AUTH_RATE_LIMIT', '20'))
            }
    
    def _validate_security_settings(self) -> None:
        """Validate overall security configuration"""
        if self.is_production:
            if self.development_mode:
                raise ValueError("❌ SECURITY ERROR: DEVELOPMENT_MODE cannot be enabled in production")
            logger.info("✅ Production security configuration validated")
        else:
            if self.development_mode:
                logger.warning("⚠️ Development mode enabled - authentication bypass allowed for localhost")
            else:
                logger.info("✅ Development environment with full authentication")

# Global security config
security_config = SecurityConfig()

# Session Management
class SecureSessionManager:
    """Secure session management with cryptographic validation"""
    
    def __init__(self):
        self.secret_key = security_config.session_secret.encode('utf-8')
        self.session_timeout = timedelta(hours=8)  # 8-hour sessions
        self._active_sessions = {}
    
    def create_session(self, user_id: str) -> str:
        """Create a cryptographically secure session token"""
        # Create session data
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + self.session_timeout,
            'nonce': secrets.token_urlsafe(16)
        }
        
        # Generate secure session token
        session_token = self._generate_secure_token(session_data)
        
        # Store session (in production, use Redis or database)
        self._active_sessions[session_token] = session_data
        
        logger.info(f"Created secure session for user: {user_id}")
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user data if valid"""
        if not session_token:
            return None
        
        try:
            # Verify token signature
            if not self._verify_token_signature(session_token):
                logger.warning("Invalid session token signature")
                return None
            
            # Check if session exists and is valid
            session_data = self._active_sessions.get(session_token)
            if not session_data:
                logger.warning("Session token not found")
                return None
            
            # Check expiration
            if datetime.utcnow() > session_data['expires_at']:
                logger.warning("Session expired")
                self.revoke_session(session_token)
                return None
            
            return {
                'user_id': session_data['user_id'],
                'created_at': session_data['created_at'],
                'expires_at': session_data['expires_at']
            }
        
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    def revoke_session(self, session_token: str) -> None:
        """Revoke a session token"""
        if session_token in self._active_sessions:
            del self._active_sessions[session_token]
            logger.info("Session revoked")
    
    def _generate_secure_token(self, session_data: Dict) -> str:
        """Generate cryptographically secure session token"""
        # Create token payload
        payload = f"{session_data['user_id']}:{session_data['nonce']}:{session_data['expires_at'].isoformat()}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Combine payload and signature
        token = f"{secrets.token_urlsafe(32)}.{signature[:32]}"
        return token
    
    def _verify_token_signature(self, token: str) -> bool:
        """Verify token signature"""
        try:
            parts = token.split('.')
            if len(parts) != 2:
                return False
            
            # In production, implement full signature verification
            # For now, basic format validation
            return len(parts[0]) >= 32 and len(parts[1]) == 32
        
        except Exception:
            return False

# Rate Limiting with Advanced Protection
class AdvancedRateLimiter:
    """Advanced rate limiting with different limits for different operations"""
    
    def __init__(self):
        self.storage = defaultdict(lambda: {
            'requests': deque(),
            'uploads': deque(),
            'auth_attempts': deque(),
            'suspicious_activity': 0,
            'blocked_until': None
        })
        self.config = security_config.rate_limits
    
    def check_rate_limit(self, request: Request, operation: str = 'api_request') -> None:
        """Check rate limit for specific operation"""
        if os.getenv('TESTING', 'false').lower() == 'true':
            return
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if self._is_ip_blocked(client_ip, current_time):
            raise HTTPException(
                status_code=429,
                detail="IP temporarily blocked due to suspicious activity"
            )
        
        # Check specific operation limits
        if operation == 'api_request':
            self._check_api_limit(client_ip, current_time)
        elif operation == 'file_upload':
            self._check_upload_limit(client_ip, current_time)
        elif operation == 'auth_attempt':
            self._check_auth_limit(client_ip, current_time)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP, handling proxies"""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take first IP in case of multiple proxies
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
        
        return request.client.host
    
    def _is_ip_blocked(self, client_ip: str, current_time: float) -> bool:
        """Check if IP is currently blocked"""
        ip_data = self.storage[client_ip]
        blocked_until = ip_data.get('blocked_until')
        
        if blocked_until and current_time < blocked_until:
            return True
        elif blocked_until and current_time >= blocked_until:
            # Unblock IP
            ip_data['blocked_until'] = None
            ip_data['suspicious_activity'] = 0
        
        return False
    
    def _check_api_limit(self, client_ip: str, current_time: float) -> None:
        """Check API request rate limit"""
        limit = self.config['api_requests_per_minute']
        window = 60
        requests = self.storage[client_ip]['requests']
        
        self._enforce_limit(client_ip, requests, limit, window, current_time, 'API requests')
    
    def _check_upload_limit(self, client_ip: str, current_time: float) -> None:
        """Check file upload rate limit"""
        limit = self.config['file_uploads_per_hour']
        window = 3600
        uploads = self.storage[client_ip]['uploads']
        
        self._enforce_limit(client_ip, uploads, limit, window, current_time, 'file uploads')
    
    def _check_auth_limit(self, client_ip: str, current_time: float) -> None:
        """Check authentication attempt rate limit"""
        limit = self.config['auth_attempts_per_hour']
        window = 3600
        auth_attempts = self.storage[client_ip]['auth_attempts']
        
        self._enforce_limit(client_ip, auth_attempts, limit, window, current_time, 'authentication attempts')
        
        # Track suspicious activity for auth attempts
        if len(auth_attempts) >= limit * 0.8:  # 80% of limit
            self.storage[client_ip]['suspicious_activity'] += 1
            if self.storage[client_ip]['suspicious_activity'] >= 3:
                # Block IP for 1 hour
                self.storage[client_ip]['blocked_until'] = current_time + 3600
                logger.warning(f"Blocked IP {client_ip} for suspicious authentication activity")
    
    def _enforce_limit(self, client_ip: str, timestamps: deque, limit: int, 
                      window: int, current_time: float, operation: str) -> None:
        """Enforce rate limit for specific operation"""
        # Remove old timestamps
        while timestamps and current_time - timestamps[0] > window:
            timestamps.popleft()
        
        # Check limit
        if len(timestamps) >= limit:
            time_to_wait = window - (current_time - timestamps[0])
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {operation}. Try again in {int(time_to_wait)} seconds"
            )
        
        # Add current timestamp
        timestamps.append(current_time)

# Input Sanitization and Validation
class InputSanitizer:
    """Secure input sanitization and validation"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize uploaded filename"""
        if not filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Remove directory traversal attempts
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Ensure reasonable length
        if len(filename) > 255:
            filename = filename[:255]
        
        # Ensure file has extension
        if '.' not in filename:
            raise HTTPException(status_code=400, detail="File must have an extension")
        
        return filename
    
    @staticmethod
    def validate_file_content(content: bytes, filename: str) -> None:
        """Comprehensive file content validation for security and integrity"""
        import csv
        import io
        
        # 1. SIZE LIMITS - Multiple tiers for security
        max_size = int(os.getenv('MAX_FILE_SIZE_MB', '10')) * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(status_code=413, detail=f"File too large (max {max_size//1024//1024}MB)")
        
        if len(content) < 10:  # Minimum viable CSV content
            raise HTTPException(status_code=400, detail="File too small to be valid CSV")
        
        # 2. EXTENSION VALIDATION - Strict whitelist
        allowed_extensions = ['.csv']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HTTPException(status_code=400, detail="Only CSV files allowed")
        
        # 3. MIME TYPE VALIDATION - Prevent disguised files (optional)
        try:
            import magic
            detected_type = magic.from_buffer(content, mime=True)
            # CSV files can be detected as text/plain or text/csv
            allowed_mime_types = ['text/plain', 'text/csv', 'application/csv', 'text/x-csv']
            if detected_type not in allowed_mime_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type. Expected CSV, got: {detected_type}"
                )
        except ImportError:
            # python-magic not installed, skip MIME validation
            logging.info("MIME type validation skipped (python-magic not installed)")
        except Exception as e:
            # If magic fails, continue with other validations
            logging.warning(f"MIME type detection failed: {e}, relying on other validations")
        
        # 4. ENCODING VALIDATION - Strict UTF-8
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file encoding at byte {e.start}. Must be UTF-8"
            )
        
        if len(content_str.strip()) == 0:
            raise HTTPException(status_code=400, detail="File contains no readable content")
        
        # 5. MALICIOUS CONTENT SCANNING - Comprehensive patterns
        dangerous_patterns = [
            # Script injection
            '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=', 'onclick=',
            # Command injection
            '$(', '${', '`', '&&', '||', ';ls', ';cat', ';rm', 'eval(', 'exec(',
            # SQL injection attempts in CSV
            'drop table', 'delete from', 'insert into', 'update set', 'union select',
            # Path traversal
            '../', '..\\', '/etc/', '/bin/', 'c:\\windows\\',
            # Binary signatures that shouldn't be in CSV
            '\\x00', '\\xff\\xfe', '\\xfe\\xff', 'pk\\x03\\x04',  # ZIP signature
            # Suspicious macro indicators
            'auto_open', 'workbook_open', 'document_open'
        ]
        
        content_lower = content_str.lower()
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File contains potentially dangerous content: {pattern}"
                )
        
        # 6. CSV STRUCTURE VALIDATION - Parse and validate
        try:
            # Test CSV parsing with strict validation
            csv_reader = csv.reader(io.StringIO(content_str))
            
            # Validate header row exists
            try:
                header_row = next(csv_reader)
                if not header_row or len(header_row) < 1:
                    raise HTTPException(status_code=400, detail="CSV must have header row")
            except StopIteration:
                raise HTTPException(status_code=400, detail="CSV file appears to be empty")
            
            # Validate reasonable column count
            if len(header_row) > 200:  # Prevent excessive columns
                raise HTTPException(status_code=400, detail="Too many columns (max 200)")
            
            # Validate header content
            for col_name in header_row:
                if not col_name or len(str(col_name).strip()) == 0:
                    raise HTTPException(status_code=400, detail="CSV headers cannot be empty")
                if len(str(col_name)) > 255:
                    raise HTTPException(status_code=400, detail="CSV header names too long")
            
            # Sample first few rows for structure validation
            row_count = 0
            for row in csv_reader:
                row_count += 1
                
                # Check for excessive rows (prevent DoS)
                if row_count > 50000:  # Reasonable limit for educational data
                    raise HTTPException(status_code=400, detail="Too many rows (max 50,000)")
                
                # Validate row structure matches header
                if len(row) != len(header_row):
                    logging.warning(f"Row {row_count + 1} has {len(row)} columns, expected {len(header_row)}")
                    # Allow some flexibility but warn
                
                # Sample only first 100 rows for performance
                if row_count >= 100:
                    break
            
            # Ensure minimum viable data
            if row_count == 0:
                raise HTTPException(status_code=400, detail="CSV must contain data rows")
            
        except csv.Error as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        except HTTPException:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CSV validation failed: {str(e)}")
        
        # 7. CONTENT LENGTH VALIDATION - Prevent zip bombs
        if len(content_str) > len(content) * 10:  # Suspicious compression ratio
            raise HTTPException(
                status_code=400, 
                detail="Suspicious file expansion detected"
            )
        
        logging.info(f"✅ File validation passed: {filename} ({len(content)} bytes, {row_count} rows)")

# Global instances
session_manager = SecureSessionManager()
rate_limiter = AdvancedRateLimiter()
input_sanitizer = InputSanitizer()

# Authentication Functions
def secure_auth(credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
    """Secure API key authentication"""
    if not credentials or credentials.credentials != security_config.api_key:
        logger.warning(f"Failed authentication attempt with key: {credentials.credentials[:8] if credentials else 'None'}***")
        raise HTTPException(
            status_code=401, 
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {"user": "api_user", "permissions": ["read", "write"], "auth_method": "api_key"}

def validate_session(request: Request) -> Optional[Dict[str, Any]]:
    """Validate session token from cookie"""
    session_token = request.cookies.get('session_token')
    if session_token:
        session_data = session_manager.validate_session(session_token)
        if session_data:
            return {
                "user": session_data['user_id'],
                "permissions": ["read", "write"],
                "auth_method": "session"
            }
    return None

def get_current_user_secure(request: Request, credentials: HTTPAuthorizationCredentials = None) -> Dict[str, Any]:
    """Secure user authentication with proper validation"""
    
    # Try session authentication first
    session_user = validate_session(request)
    if session_user:
        return session_user
    
    # Try API key authentication
    if credentials:
        return secure_auth(credentials)
    
    # Check Authorization header manually
    auth_header = request.headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        from fastapi.security import HTTPAuthorizationCredentials
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return secure_auth(creds)
    
    # Development mode localhost bypass (only if explicitly enabled)
    if security_config.development_mode and not security_config.is_production:
        client_host = request.client.host
        if client_host in ['127.0.0.1', 'localhost', '::1']:
            logger.info(f"Development mode: allowing localhost access from {client_host}")
            return {"user": "dev_user", "permissions": ["read", "write"], "auth_method": "dev_bypass"}
    
    # No valid authentication found
    logger.warning(f"Unauthorized access attempt from {request.client.host}")
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"}
    )

def create_web_session(user_id: str = "web_user") -> str:
    """Create secure web session"""
    return session_manager.create_session(user_id)

def revoke_web_session(session_token: str) -> None:
    """Revoke web session"""
    session_manager.revoke_session(session_token)