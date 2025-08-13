#!/usr/bin/env python3
"""
Database Encryption Middleware
Transparent encryption/decryption for SQLAlchemy ORM operations
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.event import listen
from sqlalchemy.orm import Session, InstanceState
from sqlalchemy.orm.events import InstanceEvents
from sqlalchemy.inspection import inspect

from .encryption import (
    encryption_manager, 
    ENCRYPTED_FIELDS,
    encrypt_model_data,
    decrypt_model_data
)

logger = logging.getLogger(__name__)

class EncryptionMiddleware:
    """
    SQLAlchemy middleware for transparent field-level encryption
    
    Automatically encrypts sensitive fields before database writes
    and decrypts them after database reads.
    """
    
    def __init__(self):
        self.enabled = encryption_manager.enabled
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for automatic encryption/decryption"""
        if not self.enabled:
            logger.info("🔓 Encryption middleware disabled")
            return
        
        # Listen for before_insert events to encrypt data
        listen(Session, 'before_insert', self._encrypt_before_insert)
        
        # Listen for before_update events to encrypt data
        listen(Session, 'before_update', self._encrypt_before_update)
        
        # Listen for after_load events to decrypt data
        listen(InstanceEvents, 'load', self._decrypt_after_load, propagate=True)
        
        logger.info("🔒 Encryption middleware enabled with SQLAlchemy event listeners")
    
    def _get_model_name(self, instance) -> Optional[str]:
        """Get model name from SQLAlchemy instance"""
        try:
            return instance.__tablename__
        except AttributeError:
            return None
    
    def _encrypt_before_insert(self, mapper, connection, target):
        """Encrypt sensitive fields before INSERT operations"""
        try:
            model_name = self._get_model_name(target)
            if not model_name or model_name not in ENCRYPTED_FIELDS:
                return
            
            # Get fields that need encryption for this model
            fields_to_encrypt = ENCRYPTED_FIELDS[model_name]
            
            # Encrypt each sensitive field
            for field_name in fields_to_encrypt:
                if hasattr(target, field_name):
                    current_value = getattr(target, field_name)
                    if current_value is not None and current_value != '':
                        encrypted_value = encryption_manager.encrypt(str(current_value))
                        setattr(target, field_name, encrypted_value)
                        logger.debug(f"🔒 Encrypted {model_name}.{field_name} for INSERT")
            
        except Exception as e:
            logger.error(f"❌ Encryption before INSERT failed: {e}")
            # In production, fail hard for security
            if encryption_manager.enabled:
                raise
    
    def _encrypt_before_update(self, mapper, connection, target):
        """Encrypt sensitive fields before UPDATE operations"""
        try:
            model_name = self._get_model_name(target)
            if not model_name or model_name not in ENCRYPTED_FIELDS:
                return
            
            # Get fields that need encryption for this model
            fields_to_encrypt = ENCRYPTED_FIELDS[model_name]
            
            # Get dirty (changed) attributes
            state = inspect(target)
            if not state.modified:
                return
            
            # Only encrypt fields that have been modified
            for field_name in fields_to_encrypt:
                if hasattr(target, field_name) and field_name in state.attrs:
                    attr = state.attrs[field_name]
                    if attr.history.has_changes():
                        current_value = getattr(target, field_name)
                        if current_value is not None and current_value != '':
                            # Check if already encrypted to avoid double encryption
                            if not str(current_value).startswith('v'):
                                encrypted_value = encryption_manager.encrypt(str(current_value))
                                setattr(target, field_name, encrypted_value)
                                logger.debug(f"🔒 Encrypted {model_name}.{field_name} for UPDATE")
            
        except Exception as e:
            logger.error(f"❌ Encryption before UPDATE failed: {e}")
            # In production, fail hard for security
            if encryption_manager.enabled:
                raise
    
    def _decrypt_after_load(self, target, context):
        """Decrypt sensitive fields after loading from database"""
        try:
            model_name = self._get_model_name(target)
            if not model_name or model_name not in ENCRYPTED_FIELDS:
                return
            
            # Get fields that need decryption for this model
            fields_to_decrypt = ENCRYPTED_FIELDS[model_name]
            
            # Decrypt each sensitive field
            for field_name in fields_to_decrypt:
                if hasattr(target, field_name):
                    encrypted_value = getattr(target, field_name)
                    if encrypted_value is not None and encrypted_value != '':
                        decrypted_value = encryption_manager.decrypt(str(encrypted_value))
                        setattr(target, field_name, decrypted_value)
                        logger.debug(f"🔓 Decrypted {model_name}.{field_name} after LOAD")
            
        except Exception as e:
            logger.error(f"❌ Decryption after LOAD failed: {e}")
            # Don't fail hard on decryption - graceful degradation
            logger.warning("⚠️ Continuing with encrypted data due to decryption failure")

# Utility functions for manual encryption/decryption operations

def encrypt_query_parameters(model_name: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt query parameters for WHERE clauses involving encrypted fields
    
    Args:
        model_name: Name of the model being queried
        query_params: Dictionary of query parameters
        
    Returns:
        Dictionary with encrypted field values
    """
    if not encryption_manager.enabled or model_name not in ENCRYPTED_FIELDS:
        return query_params
    
    encrypted_params = query_params.copy()
    fields_to_encrypt = ENCRYPTED_FIELDS[model_name]
    
    for field_name in fields_to_encrypt:
        if field_name in encrypted_params:
            value = encrypted_params[field_name]
            if value is not None and value != '':
                encrypted_params[field_name] = encryption_manager.encrypt(str(value))
                logger.debug(f"🔒 Encrypted query parameter {field_name}")
    
    return encrypted_params

def decrypt_query_results(model_name: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Decrypt query results when using raw SQL queries
    
    Args:
        model_name: Name of the model
        results: List of dictionaries representing query results
        
    Returns:
        List with decrypted field values
    """
    if not encryption_manager.enabled or model_name not in ENCRYPTED_FIELDS:
        return results
    
    decrypted_results = []
    fields_to_decrypt = ENCRYPTED_FIELDS[model_name]
    
    for row in results:
        decrypted_row = row.copy()
        for field_name in fields_to_decrypt:
            if field_name in decrypted_row:
                value = decrypted_row[field_name]
                if value is not None and value != '':
                    decrypted_row[field_name] = encryption_manager.decrypt(str(value))
        decrypted_results.append(decrypted_row)
    
    return decrypted_results

def create_encrypted_student(session: Session, student_data: Dict[str, Any]) -> 'Student':
    """
    Create a new student record with automatic encryption
    
    Args:
        session: SQLAlchemy session
        student_data: Dictionary of student data
        
    Returns:
        Created Student instance
    """
    from .models import Student
    
    # Encryption will be handled automatically by middleware
    student = Student(**student_data)
    session.add(student)
    session.flush()  # Get the ID without committing
    
    logger.info(f"👤 Created encrypted student record (ID: {student.id})")
    return student

def update_encrypted_student(session: Session, student_id: int, update_data: Dict[str, Any]) -> Optional['Student']:
    """
    Update a student record with automatic encryption
    
    Args:
        session: SQLAlchemy session
        student_id: ID of student to update
        update_data: Dictionary of fields to update
        
    Returns:
        Updated Student instance or None if not found
    """
    from .models import Student
    
    student = session.query(Student).filter(Student.id == student_id).first()
    if not student:
        return None
    
    # Update fields (encryption will be handled automatically by middleware)
    for field, value in update_data.items():
        if hasattr(student, field):
            setattr(student, field, value)
    
    session.flush()
    logger.info(f"👤 Updated encrypted student record (ID: {student.id})")
    return student

def search_encrypted_field(session: Session, model_class, field_name: str, search_value: str):
    """
    Search for records by encrypted field value
    
    Note: This requires encrypting the search value and doing exact match.
    Full-text search on encrypted fields requires special handling.
    
    Args:
        session: SQLAlchemy session
        model_class: SQLAlchemy model class
        field_name: Name of the encrypted field
        search_value: Value to search for
        
    Returns:
        Query result
    """
    model_name = model_class.__tablename__
    
    if encryption_manager.enabled and model_name in ENCRYPTED_FIELDS and field_name in ENCRYPTED_FIELDS[model_name]:
        # Encrypt the search value for exact match
        encrypted_search_value = encryption_manager.encrypt(search_value)
        return session.query(model_class).filter(getattr(model_class, field_name) == encrypted_search_value)
    else:
        # Regular search for unencrypted fields
        return session.query(model_class).filter(getattr(model_class, field_name) == search_value)

# Global middleware instance
encryption_middleware = EncryptionMiddleware()

def get_encryption_middleware() -> EncryptionMiddleware:
    """Get the global encryption middleware instance"""
    return encryption_middleware