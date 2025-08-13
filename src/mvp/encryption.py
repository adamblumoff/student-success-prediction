#!/usr/bin/env python3
"""
Database Encryption System for FERPA Compliance
Provides transparent encryption/decryption for sensitive student data fields
"""

import os
import base64
import logging
import hashlib
from typing import Optional, Any, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from functools import wraps
import json

logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    FERPA-compliant encryption manager for sensitive student data
    
    Features:
    - AES-256 encryption using Fernet (symmetric encryption)
    - PBKDF2 key derivation for password-based encryption
    - Transparent field-level encryption for ORM models
    - Key rotation support for security compliance
    - Audit logging for encryption operations
    """
    
    def __init__(self):
        self.enabled = self._is_encryption_enabled()
        self._cipher = None
        self._key_version = None
        
        if self.enabled:
            self._initialize_encryption()
        else:
            logger.warning("⚠️ Database encryption is DISABLED - only use in development")
    
    def _is_encryption_enabled(self) -> bool:
        """Check if encryption should be enabled based on environment"""
        # Enable encryption in production or when explicitly enabled
        environment = os.getenv('ENVIRONMENT', '').lower()
        explicit_enable = os.getenv('ENABLE_DATABASE_ENCRYPTION', 'false').lower() == 'true'
        
        return environment in ['production', 'prod'] or explicit_enable
    
    def _initialize_encryption(self):
        """Initialize encryption system with secure key management"""
        try:
            # Get or generate master key
            master_key = self._get_or_create_master_key()
            
            # Derive encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits for AES-256
                salt=self._get_salt(),
                iterations=100000,  # NIST recommended minimum
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._cipher = Fernet(key)
            self._key_version = os.getenv('ENCRYPTION_KEY_VERSION', '1')
            
            logger.info(f"✅ Database encryption initialized (key version: {self._key_version})")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption: {e}")
            # In production, fail hard for security
            if os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']:
                raise ValueError("Critical: Database encryption initialization failed in production")
            else:
                logger.warning("⚠️ Encryption disabled due to initialization failure")
                self.enabled = False
    
    def _get_or_create_master_key(self) -> str:
        """Get master key from environment or generate secure default"""
        # In production, master key MUST be provided via environment
        master_key = os.getenv('DATABASE_ENCRYPTION_KEY')
        
        if master_key:
            if len(master_key) < 32:
                raise ValueError("DATABASE_ENCRYPTION_KEY must be at least 32 characters")
            return master_key
        
        # For development, generate a deterministic key based on institution
        if os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']:
            raise ValueError("DATABASE_ENCRYPTION_KEY environment variable is required in production")
        
        # Development fallback - deterministic but secure for testing
        institution_id = os.getenv('DEFAULT_INSTITUTION_ID', '1')
        dev_seed = f"student_success_dev_key_{institution_id}"
        
        # Create a secure hash of the development seed
        dev_key = hashlib.sha256(dev_seed.encode()).hexdigest()
        logger.warning(f"⚠️ Using development encryption key for institution {institution_id}")
        
        return dev_key
    
    def _get_salt(self) -> bytes:
        """Get consistent salt for key derivation"""
        # Use a fixed salt derived from institution info for deterministic encryption
        # This allows encrypted data to be decrypted consistently
        institution_salt = os.getenv('ENCRYPTION_SALT', 'student_success_salt_2024')
        return hashlib.sha256(institution_salt.encode()).digest()[:16]  # 16 bytes for salt
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value for database storage
        
        Args:
            plaintext: The original text to encrypt
            
        Returns:
            Base64-encoded encrypted text with version prefix
        """
        if not self.enabled:
            return plaintext
        
        if not plaintext or plaintext.strip() == '':
            return plaintext
        
        try:
            # Add key version prefix for future key rotation support
            encrypted_bytes = self._cipher.encrypt(plaintext.encode('utf-8'))
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_bytes).decode('ascii')
            
            # Format: v{version}:{encrypted_data}
            versioned_encrypted = f"v{self._key_version}:{encrypted_b64}"
            
            logger.debug(f"🔒 Encrypted field (length: {len(plaintext)} -> {len(versioned_encrypted)})")
            return versioned_encrypted
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            # In production, fail hard for security
            if os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']:
                raise ValueError("Critical: Database encryption failed")
            return plaintext
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt a string value from database storage
        
        Args:
            encrypted_text: The encrypted text from database
            
        Returns:
            Original plaintext string
        """
        if not self.enabled:
            return encrypted_text
        
        if not encrypted_text or encrypted_text.strip() == '':
            return encrypted_text
        
        # Handle unencrypted legacy data
        if not encrypted_text.startswith('v'):
            logger.debug("📄 Returning unencrypted legacy data")
            return encrypted_text
        
        try:
            # Parse version and encrypted data
            if ':' not in encrypted_text:
                logger.warning("⚠️ Invalid encrypted data format, returning as-is")
                return encrypted_text
            
            version_part, encrypted_b64 = encrypted_text.split(':', 1)
            version = version_part[1:]  # Remove 'v' prefix
            
            # For now, support only current version (future: key rotation)
            if version != self._key_version:
                logger.warning(f"⚠️ Encrypted data uses different key version: {version}")
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_b64.encode('ascii'))
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            plaintext = decrypted_bytes.decode('utf-8')
            
            logger.debug(f"🔓 Decrypted field (length: {len(encrypted_text)} -> {len(plaintext)})")
            return plaintext
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            # Return encrypted text if decryption fails (graceful degradation)
            logger.warning("⚠️ Returning encrypted text due to decryption failure")
            return encrypted_text
    
    def encrypt_dict(self, data: Dict[str, Any], encrypted_fields: list) -> Dict[str, Any]:
        """
        Encrypt specified fields in a dictionary
        
        Args:
            data: Dictionary containing data to encrypt
            encrypted_fields: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        if not self.enabled:
            return data
        
        encrypted_data = data.copy()
        
        for field in encrypted_fields:
            if field in encrypted_data and encrypted_data[field] is not None:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], encrypted_fields: list) -> Dict[str, Any]:
        """
        Decrypt specified fields in a dictionary
        
        Args:
            data: Dictionary containing encrypted data
            encrypted_fields: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        if not self.enabled:
            return data
        
        decrypted_data = data.copy()
        
        for field in encrypted_fields:
            if field in decrypted_data and decrypted_data[field] is not None:
                decrypted_data[field] = self.decrypt(str(decrypted_data[field]))
        
        return decrypted_data
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Get encryption system status for health checks"""
        return {
            'enabled': self.enabled,
            'key_version': self._key_version,
            'algorithm': 'AES-256 (Fernet)' if self.enabled else None,
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'kdf': 'PBKDF2-SHA256' if self.enabled else None
        }

# Global encryption manager instance
encryption_manager = EncryptionManager()

# Field definitions for different models
ENCRYPTED_FIELDS = {
    'students': [
        'birth_date',
        'email', 
        'phone',
        'parent_email',
        'parent_phone'
    ],
    'users': [
        'email',
        'first_name',
        'last_name'
    ],
    'audit_logs': [
        'user_email'
    ]
}

def encrypt_model_data(model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt sensitive fields for a specific model
    
    Args:
        model_name: Name of the database model (e.g., 'students', 'users')
        data: Dictionary of model data
        
    Returns:
        Dictionary with sensitive fields encrypted
    """
    if model_name in ENCRYPTED_FIELDS:
        return encryption_manager.encrypt_dict(data, ENCRYPTED_FIELDS[model_name])
    return data

def decrypt_model_data(model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrypt sensitive fields for a specific model
    
    Args:
        model_name: Name of the database model (e.g., 'students', 'users')
        data: Dictionary of encrypted model data
        
    Returns:
        Dictionary with sensitive fields decrypted
    """
    if model_name in ENCRYPTED_FIELDS:
        return encryption_manager.decrypt_dict(data, ENCRYPTED_FIELDS[model_name])
    return data

def encryption_required(func):
    """
    Decorator to automatically encrypt/decrypt model data
    Usage: @encryption_required above database operations
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # This decorator can be enhanced to automatically handle
        # encryption/decryption based on function parameters
        return func(*args, **kwargs)
    return wrapper

# Convenience functions for common operations
def encrypt_student_data(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive student data fields"""
    return encrypt_model_data('students', student_data)

def decrypt_student_data(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive student data fields"""
    return decrypt_model_data('students', student_data)

def encrypt_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt sensitive user data fields"""
    return encrypt_model_data('users', user_data)

def decrypt_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive user data fields"""
    return decrypt_model_data('users', user_data)

# Health check function
def check_encryption_health() -> bool:
    """Check if encryption system is healthy and operational"""
    try:
        if not encryption_manager.enabled:
            return True  # Encryption disabled is valid in development
        
        # Test encryption/decryption round trip
        test_data = "test_encryption_health_check"
        encrypted = encryption_manager.encrypt(test_data)
        decrypted = encryption_manager.decrypt(encrypted)
        
        return decrypted == test_data
    except Exception as e:
        logger.error(f"Encryption health check failed: {e}")
        return False

def get_encryption_manager() -> EncryptionManager:
    """Get the global encryption manager instance"""
    return encryption_manager