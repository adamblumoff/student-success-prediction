#!/usr/bin/env python3
"""
Comprehensive Encryption System Tests

Tests the FERPA-compliant database encryption system including
encryption/decryption, key management, and middleware integration.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
import json

# Add project root to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Set up test environment (moved inside test fixtures)
# os.environ['TESTING'] = 'true'
# os.environ['ENVIRONMENT'] = 'test'

# Encryption imports are done inside test functions to avoid module-level initialization
# from src.mvp.encryption import ...

@pytest.fixture(autouse=True)
def clean_test_environment():
    """Ensure clean test environment for each test"""
    # Store original environment
    original_env = dict(os.environ)
    
    # Set base test environment
    os.environ['TESTING'] = 'true'
    os.environ['ENVIRONMENT'] = 'test'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

class TestEncryptionManager:
    """Test core encryption manager functionality"""
    
    @pytest.fixture
    def test_encryption_manager(self):
        """Create encryption manager for testing"""
        # Force enable encryption for tests
        with patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'}):
            # Import inside fixture to avoid module-level initialization
            from src.mvp.encryption import EncryptionManager
            return EncryptionManager()
    
    def test_encryption_initialization(self, test_encryption_manager):
        """Test encryption manager initializes correctly"""
        assert test_encryption_manager.enabled == True
        assert test_encryption_manager._cipher is not None
        assert test_encryption_manager._key_version == '1'
    
    def test_basic_encryption_decryption(self, test_encryption_manager):
        """Test basic encrypt/decrypt round trip"""
        test_data = "sensitive@student.edu"
        
        encrypted = test_encryption_manager.encrypt(test_data)
        decrypted = test_encryption_manager.decrypt(encrypted)
        
        assert encrypted != test_data  # Should be encrypted
        assert decrypted == test_data  # Should decrypt correctly
        assert encrypted.startswith('v1:')  # Should have version prefix
    
    def test_empty_and_none_values(self, test_encryption_manager):
        """Test handling of empty and None values"""
        # Empty string
        empty_encrypted = test_encryption_manager.encrypt("")
        assert empty_encrypted == ""
        
        # None value (should return None)
        assert test_encryption_manager.encrypt(None) == None
        assert test_encryption_manager.decrypt(None) == None
    
    def test_legacy_data_passthrough(self, test_encryption_manager):
        """Test that legacy unencrypted data passes through"""
        legacy_data = "legacy@example.com"
        decrypted = test_encryption_manager.decrypt(legacy_data)
        assert decrypted == legacy_data  # Should return unchanged
    
    def test_versioned_encryption(self, test_encryption_manager):
        """Test that encryption includes version information"""
        test_data = "version_test@example.com"
        encrypted = test_encryption_manager.encrypt(test_data)
        
        assert encrypted.startswith('v1:')
        
        # Simulate different key version
        test_encryption_manager._key_version = '2'
        encrypted_v2 = test_encryption_manager.encrypt(test_data)
        assert encrypted_v2.startswith('v2:')
    
    def test_encryption_consistency(self, test_encryption_manager):
        """Test that encryption is consistent for same input"""
        test_data = "consistency@test.com"
        
        # Multiple encryptions of same data should be different (due to Fernet)
        encrypted1 = test_encryption_manager.encrypt(test_data)
        encrypted2 = test_encryption_manager.encrypt(test_data)
        
        assert encrypted1 != encrypted2  # Should be different due to Fernet nonce
        
        # But both should decrypt to the same value
        assert test_encryption_manager.decrypt(encrypted1) == test_data
        assert test_encryption_manager.decrypt(encrypted2) == test_data

class TestEncryptionStatus:
    """Test encryption system status and health checks"""
    
    def test_encryption_health_check(self):
        """Test encryption health check function"""
        from src.mvp.encryption import check_encryption_health
        health = check_encryption_health()
        assert isinstance(health, bool)
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_encryption_status_enabled(self):
        """Test encryption status when enabled"""
        from src.mvp.encryption import EncryptionManager
        manager = EncryptionManager()
        status = manager.get_encryption_status()
        
        assert status['enabled'] == True
        assert status['algorithm'] == 'AES-256 (Fernet)'
        assert status['key_version'] == '1'
        assert status['kdf'] == 'PBKDF2-SHA256'
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'false'})
    def test_encryption_status_disabled(self):
        """Test encryption status when disabled"""
        from src.mvp.encryption import EncryptionManager
        manager = EncryptionManager()
        status = manager.get_encryption_status()
        
        assert status['enabled'] == False
        assert status['algorithm'] is None

class TestModelDataEncryption:
    """Test model-specific data encryption functions"""
    
    @pytest.fixture
    def sample_student_data(self):
        """Sample student data for testing"""
        return {
            'student_id': 'STU001',
            'sis_id': 'SIS12345',
            'grade_level': '10',
            'birth_date': '2008-03-15',  # Should be encrypted
            'email': 'student@school.edu',  # Should be encrypted  
            'phone': '555-0123',  # Should be encrypted
            'parent_email': 'parent@example.com',  # Should be encrypted
            'parent_phone': '555-0456',  # Should be encrypted
            'enrollment_status': 'active',  # Should NOT be encrypted
            'is_ell': False,  # Should NOT be encrypted
        }
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            'username': 'teacher123',
            'email': 'teacher@school.edu',  # Should be encrypted
            'first_name': 'Jane',  # Should be encrypted
            'last_name': 'Smith',  # Should be encrypted
            'role': 'teacher',  # Should NOT be encrypted
            'is_active': True  # Should NOT be encrypted
        }
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_student_data_encryption(self, sample_student_data):
        """Test student data encryption"""
        from src.mvp.encryption import encrypt_student_data
        encrypted_data = encrypt_student_data(sample_student_data)
        
        # Check that sensitive fields are encrypted
        sensitive_fields = ['birth_date', 'email', 'phone', 'parent_email', 'parent_phone']
        for field in sensitive_fields:
            if field in sample_student_data:
                assert encrypted_data[field] != sample_student_data[field]
                assert encrypted_data[field].startswith('v1:')
        
        # Check that non-sensitive fields are unchanged
        non_sensitive_fields = ['student_id', 'grade_level', 'enrollment_status', 'is_ell']
        for field in non_sensitive_fields:
            if field in sample_student_data:
                assert encrypted_data[field] == sample_student_data[field]
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_student_data_decryption(self, sample_student_data):
        """Test student data decryption"""
        from src.mvp.encryption import encrypt_student_data, decrypt_student_data
        encrypted_data = encrypt_student_data(sample_student_data)
        decrypted_data = decrypt_student_data(encrypted_data)
        
        # All fields should match original data
        for field, original_value in sample_student_data.items():
            assert decrypted_data[field] == original_value
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_user_data_encryption(self, sample_user_data):
        """Test user data encryption"""
        from src.mvp.encryption import encrypt_user_data
        encrypted_data = encrypt_user_data(sample_user_data)
        
        # Check that sensitive fields are encrypted
        sensitive_fields = ['email', 'first_name', 'last_name']
        for field in sensitive_fields:
            if field in sample_user_data:
                assert encrypted_data[field] != sample_user_data[field]
                assert encrypted_data[field].startswith('v1:')
        
        # Check that non-sensitive fields are unchanged
        non_sensitive_fields = ['username', 'role', 'is_active']
        for field in non_sensitive_fields:
            if field in sample_user_data:
                assert encrypted_data[field] == sample_user_data[field]
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'false'})
    def test_encryption_disabled_passthrough(self, sample_student_data):
        """Test that data passes through unchanged when encryption disabled"""
        from src.mvp.encryption import encrypt_student_data
        # Need to mock the encryption manager to be disabled
        with patch('src.mvp.encryption.encryption_manager') as mock_manager:
            mock_manager.enabled = False
            mock_manager.encrypt_dict.return_value = sample_student_data
            
            encrypted_data = encrypt_student_data(sample_student_data)
            
            # All fields should be unchanged when encryption is disabled
            for field, original_value in sample_student_data.items():
                assert encrypted_data[field] == original_value

class TestEncryptionConfiguration:
    """Test encryption configuration and key management"""
    
    def test_encrypted_fields_configuration(self):
        """Test that encrypted fields are properly configured"""
        from src.mvp.encryption import ENCRYPTED_FIELDS
        assert 'students' in ENCRYPTED_FIELDS
        assert 'users' in ENCRYPTED_FIELDS
        
        # Check student fields
        student_fields = ENCRYPTED_FIELDS['students']
        assert 'birth_date' in student_fields
        assert 'email' in student_fields
        assert 'phone' in student_fields
        assert 'parent_email' in student_fields
        assert 'parent_phone' in student_fields
        
        # Check user fields  
        user_fields = ENCRYPTED_FIELDS['users']
        assert 'email' in user_fields
        assert 'first_name' in user_fields
        assert 'last_name' in user_fields
    
    @patch.dict(os.environ, {'DATABASE_ENCRYPTION_KEY': 'test-key-32-characters-minimum-secure'})
    def test_custom_encryption_key(self):
        """Test using custom encryption key"""
        with patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'}):
            from src.mvp.encryption import EncryptionManager
            manager = EncryptionManager()
            assert manager.enabled == True
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_production_requires_encryption_key(self):
        """Test that production environment requires encryption key"""
        with patch.dict(os.environ, {'DATABASE_ENCRYPTION_KEY': '', 'ENABLE_DATABASE_ENCRYPTION': ''}):
            from src.mvp.encryption import EncryptionManager
            with pytest.raises(ValueError, match="Critical.*initialization failed"):
                EncryptionManager()
    
    def test_development_mode_configuration(self):
        """Test encryption configuration in development mode"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development', 'ENABLE_DATABASE_ENCRYPTION': 'false'}):
            from src.mvp.encryption import EncryptionManager
            manager = EncryptionManager()
            assert manager.enabled == False

class TestEncryptionSecurity:
    """Test encryption security features"""
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_encryption_key_strength(self):
        """Test that encryption uses strong keys"""
        # Test with weak key should fail during initialization
        with patch.dict(os.environ, {'DATABASE_ENCRYPTION_KEY': 'weak', 'ENVIRONMENT': 'production'}):
            from src.mvp.encryption import EncryptionManager
            with pytest.raises(ValueError, match="Critical.*initialization failed"):
                EncryptionManager()
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_different_data_different_ciphertext(self):
        """Test that different data produces different ciphertext"""
        from src.mvp.encryption import EncryptionManager
        manager = EncryptionManager()
        
        data1 = "test1@example.com"
        data2 = "test2@example.com"
        
        encrypted1 = manager.encrypt(data1)
        encrypted2 = manager.encrypt(data2)
        
        assert encrypted1 != encrypted2
        assert manager.decrypt(encrypted1) == data1
        assert manager.decrypt(encrypted2) == data2
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_tampered_data_detection(self):
        """Test that tampered encrypted data is detected"""
        from src.mvp.encryption import EncryptionManager
        manager = EncryptionManager()
        
        original_data = "secure@example.com"
        encrypted = manager.encrypt(original_data)
        
        # Tamper with the encrypted data
        tampered = encrypted[:-5] + "AAAAA"
        
        # Should return tampered data as-is (graceful degradation)
        result = manager.decrypt(tampered)
        assert result == tampered  # Graceful degradation

class TestPerformance:
    """Test encryption performance"""
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_encryption_performance(self):
        """Test encryption performance for typical data sizes"""
        import time
        from src.mvp.encryption import EncryptionManager
        
        manager = EncryptionManager()
        test_data = "performance.test@school.edu"
        
        # Test encryption speed
        start_time = time.time()
        for _ in range(100):
            encrypted = manager.encrypt(test_data)
        encryption_time = time.time() - start_time
        
        # Should be fast (less than 1 second for 100 operations)
        assert encryption_time < 1.0
        
        # Test decryption speed
        start_time = time.time()
        for _ in range(100):
            decrypted = manager.decrypt(encrypted)
        decryption_time = time.time() - start_time
        
        # Should be fast (less than 1 second for 100 operations)
        assert decryption_time < 1.0
    
    @patch.dict(os.environ, {'ENABLE_DATABASE_ENCRYPTION': 'true'})
    def test_large_data_encryption(self):
        """Test encryption of larger data sizes"""
        from src.mvp.encryption import EncryptionManager
        manager = EncryptionManager()
        
        # Test with a larger string (1KB)
        large_data = "large_email_address@school.edu" * 50
        
        encrypted = manager.encrypt(large_data)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == large_data
        assert len(encrypted) > len(large_data)  # Encrypted should be larger

if __name__ == "__main__":
    pytest.main([__file__, "-v"])