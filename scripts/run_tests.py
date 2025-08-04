#!/usr/bin/env python3
"""
Test Runner for Student Success Predictor

Runs comprehensive tests for health checks, authentication, and core functionality.
Can be run locally or in CI/CD pipelines.
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def check_server_running(base_url="http://localhost:8001", max_attempts=30):
    """Check if the server is running and responding"""
    print(f"🔍 Checking if server is running at {base_url}...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Server is running and responding")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            print(f"⏳ Attempt {attempt + 1}/{max_attempts} - Server not ready, waiting...")
            time.sleep(2)
    
    print(f"❌ Server is not responding after {max_attempts} attempts")
    return False

def install_test_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    
    dependencies = [
        "pytest>=7.0.0",
        "requests>=2.28.0",
        "psutil>=5.9.0"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Could not install {dep}: {e}")

def run_health_tests(base_url="http://localhost:8001"):
    """Run health check tests"""
    print("\n🏥 Running Health Check Tests...")
    
    env = os.environ.copy()
    env['TEST_BASE_URL'] = base_url
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_core_health.py::TestHealthEndpoints",
            "-v", "--tb=short"
        ], env=env, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running health tests: {e}")
        return False

def run_auth_tests(base_url="http://localhost:8001"):
    """Run authentication tests"""
    print("\n🔐 Running Authentication Tests...")
    
    env = os.environ.copy()
    env['TEST_BASE_URL'] = base_url
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_core_health.py::TestAuthentication",
            "-v", "--tb=short"
        ], env=env, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running auth tests: {e}")
        return False

def run_ml_tests(base_url="http://localhost:8001"):
    """Run ML pipeline tests"""
    print("\n🤖 Running ML Pipeline Tests...")
    
    env = os.environ.copy()
    env['TEST_BASE_URL'] = base_url
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_core_health.py::TestCoreMLPipeline",
            "-v", "--tb=short"
        ], env=env, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running ML tests: {e}")
        return False

def run_integration_tests(base_url="http://localhost:8001"):
    """Run system integration tests"""
    print("\n🔗 Running Integration Tests...")
    
    env = os.environ.copy()
    env['TEST_BASE_URL'] = base_url
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_core_health.py::TestSystemIntegration",
            "-v", "--tb=short"
        ], env=env, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False

def run_error_tests(base_url="http://localhost:8001"):
    """Run error handling tests"""
    print("\n🚨 Running Error Handling Tests...")
    
    env = os.environ.copy()
    env['TEST_BASE_URL'] = base_url
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_core_health.py::TestErrorHandling",
            "-v", "--tb=short"
        ], env=env, capture_output=True, text=True)
        
        print(result.stdout)  
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running error tests: {e}")
        return False

def main():
    """Main test runner"""
    print("🧪 Student Success Predictor - Test Suite")
    print("=" * 50)
    
    # Parse command line arguments
    base_url = os.getenv('TEST_BASE_URL', 'http://localhost:8001')
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # Install dependencies
    install_test_dependencies()
    
    # Check if server is running
    if not check_server_running(base_url):
        print("\n💡 To run tests:")
        print("1. Start the server: python3 run_mvp.py")
        print("2. Run tests: python3 scripts/run_tests.py")
        return 1
    
    # Run all test suites
    test_results = {
        "Health Checks": run_health_tests(base_url),
        "Authentication": run_auth_tests(base_url),
        "ML Pipeline": run_ml_tests(base_url),
        "Integration": run_integration_tests(base_url),
        "Error Handling": run_error_tests(base_url)
    }
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for production.")
        return 0
    else:
        print("⚠️  Some tests failed. Review the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())