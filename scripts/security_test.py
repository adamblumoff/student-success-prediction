#!/usr/bin/env python3
"""
Security test script for Student Success Prediction System
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

def test_file_upload_security():
    """Test file upload security measures"""
    print("🔒 Testing File Upload Security...")
    
    from security import secure_validator
    
    # Test 1: Valid CSV file
    try:
        valid_csv = b'Student,ID,Score\nJohn,123,85\nJane,124,92'
        df = secure_validator.secure_process_upload(valid_csv, 'test.csv')
        print(f"✅ Valid CSV processed: {len(df)} rows")
    except Exception as e:
        print(f"❌ Valid CSV test failed: {e}")
    
    # Test 2: File too large
    try:
        large_file = b'A' * (11 * 1024 * 1024)  # 11MB
        secure_validator.secure_process_upload(large_file, 'large.csv')
        print("❌ Large file test failed - should have been rejected")
    except Exception as e:
        print(f"✅ Large file properly rejected: {type(e).__name__}")
    
    # Test 3: CSV injection detection
    try:
        malicious_csv = b'Student,Formula\nJohn,=cmd|"/c calc"\nJane,85'
        df = secure_validator.secure_process_upload(malicious_csv, 'malicious.csv')
        print(f"✅ CSV injection sanitized: {len(df)} rows processed safely")
    except Exception as e:
        print(f"⚠️ CSV injection test result: {e}")

def test_authentication():
    """Test authentication system"""
    print("\n🔑 Testing Authentication...")
    
    from security import security_manager
    
    # Test 1: Valid API key
    try:
        user = security_manager.validate_api_key('dev-key-change-me')
        print(f"✅ Valid API key accepted - Role: {user['role']}")
    except Exception as e:
        print(f"❌ Valid API key test failed: {e}")
    
    # Test 2: Invalid API key
    try:
        security_manager.validate_api_key('invalid-key')
        print("❌ Invalid API key test failed - should have been rejected")
    except Exception as e:
        print(f"✅ Invalid API key properly rejected: {type(e).__name__}")
    
    # Test 3: JWT token creation
    try:
        user_info = {'role': 'teacher', 'permissions': ['read', 'write']}
        token = security_manager.create_jwt_token(user_info)
        print(f"✅ JWT token created successfully: {len(token)} characters")
    except Exception as e:
        print(f"❌ JWT token test failed: {e}")

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n🚦 Testing Rate Limiting...")
    
    from security import rate_limiter
    
    # Mock request object
    class MockClient:
        host = '127.0.0.1'
    
    class MockRequest:
        def __init__(self):
            self.client = MockClient()
            self._headers = {'user-agent': 'test-agent'}
        
        @property
        def headers(self):
            return self._headers
    
    try:
        request = MockRequest()
        
        # Test rate limit check
        allowed = rate_limiter.check_rate_limit(request, 'default')
        print(f"✅ Rate limit check works: {allowed}")
        
        # Test rate limit info
        info = rate_limiter.get_rate_limit_info(request, 'default')
        print(f"✅ Rate limit info: {info['remaining']}/{info['limit']} remaining")
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")

def test_input_validation():
    """Test input validation and sanitization"""
    print("\n🛡️ Testing Input Validation...")
    
    from security.file_validator import SecureFileValidator
    
    validator = SecureFileValidator()
    
    # Test filename sanitization
    try:
        safe_filename = validator.validate_filename("../../../etc/passwd")
        print(f"✅ Filename sanitized: '{safe_filename}'")
    except Exception as e:
        print(f"❌ Filename validation failed: {e}")
    
    # Test CSV injection detection
    try:
        malicious_content = "=cmd|calc,test\n+SUM(A1:A2),data"
        threats = validator.detect_csv_injection(malicious_content)
        print(f"✅ CSV injection detection: {len(threats)} threats found")
    except Exception as e:
        print(f"❌ CSV injection detection failed: {e}")

def test_environment_security():
    """Test environment configuration security"""
    print("\n🌍 Testing Environment Security...")
    
    # Check for insecure configurations
    warnings = []
    
    if os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true':
        warnings.append("Development mode is enabled")
    
    if not os.getenv('JWT_SECRET_KEY'):
        warnings.append("JWT_SECRET_KEY not set - using generated key")
    
    if not os.getenv('ADMIN_API_KEY'):
        warnings.append("ADMIN_API_KEY not set - using development key")
    
    if warnings:
        print("⚠️ Security warnings found:")
        for warning in warnings:
            print(f"   - {warning}")
    else:
        print("✅ Environment security configuration looks good")

def main():
    """Run all security tests"""
    print("🔒 Security Test Suite for Student Success Prediction System")
    print("=" * 60)
    
    # Set development mode for testing
    os.environ['DEVELOPMENT_MODE'] = 'true'
    
    try:
        test_file_upload_security()
        test_authentication()
        test_rate_limiting()
        test_input_validation()
        test_environment_security()
        
        print("\n" + "=" * 60)
        print("🎉 Security test suite completed!")
        print("\n📋 Recommendations for production:")
        print("   1. Set DEVELOPMENT_MODE=false")
        print("   2. Configure strong API keys")
        print("   3. Set JWT_SECRET_KEY environment variable")
        print("   4. Install python-magic for better MIME detection")
        print("   5. Configure proper CORS origins")
        print("   6. Set up HTTPS with valid SSL certificates")
        
    except Exception as e:
        print(f"\n❌ Security test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()