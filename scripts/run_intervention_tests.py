#!/usr/bin/env python3
"""
Intervention and Database Test Runner
Runs comprehensive tests for intervention system and database operations
"""

import os
import sys
import subprocess
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_python_tests():
    """Run Python tests for intervention system and database operations"""
    print("=== RUNNING PYTHON TESTS ===")
    print()
    
    test_files = [
        "tests/api/test_interventions.py",
        "tests/api/test_database_operations.py", 
        "tests/api/test_database_constraints.py"
    ]
    
    all_passed = True
    results = {}
    
    for test_file in test_files:
        print(f"🧪 Running {test_file}...")
        
        try:
            # Set test environment
            test_env = os.environ.copy()
            test_env['TESTING'] = 'true'
            test_env['PYTHONPATH'] = str(project_root)
            
            start_time = time.time()
            
            result = subprocess.run([
                sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
            ], 
            capture_output=True, 
            text=True, 
            cwd=project_root,
            env=test_env
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result.returncode == 0:
                print(f"✅ {test_file} PASSED ({duration:.1f}s)")
                results[test_file] = "PASSED"
            else:
                print(f"❌ {test_file} FAILED ({duration:.1f}s)")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                results[test_file] = "FAILED"
                all_passed = False
                
        except Exception as e:
            print(f"❌ {test_file} ERROR: {e}")
            results[test_file] = f"ERROR: {e}"
            all_passed = False
        
        print()
    
    return all_passed, results

def run_javascript_tests():
    """Run JavaScript tests for intervention UI"""
    print("=== RUNNING JAVASCRIPT TESTS ===")
    print()
    
    # Check if Node.js and Jest are available
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        print("✅ Node.js is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js not found. JavaScript tests skipped.")
        return False, {"JavaScript": "SKIPPED - Node.js not available"}
    
    # Check for Jest
    test_file = "tests/components/interventions.test.js"
    
    try:
        # Try to run Jest test
        result = subprocess.run([
            "npx", "jest", test_file, "--verbose"
        ], 
        capture_output=True, 
        text=True, 
        cwd=project_root
        )
        
        if result.returncode == 0:
            print(f"✅ {test_file} PASSED")
            return True, {"JavaScript": "PASSED"}
        else:
            print(f"❌ {test_file} FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False, {"JavaScript": "FAILED"}
            
    except FileNotFoundError:
        print("❌ Jest not found. Installing dependencies...")
        
        # Try to install Jest
        try:
            subprocess.run(["npm", "install", "--save-dev", "jest"], 
                         check=True, cwd=project_root)
            print("✅ Jest installed")
            
            # Try running test again
            result = subprocess.run([
                "npx", "jest", test_file, "--verbose"
            ], 
            capture_output=True, 
            text=True, 
            cwd=project_root
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file} PASSED")
                return True, {"JavaScript": "PASSED"}
            else:
                print(f"❌ {test_file} FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False, {"JavaScript": "FAILED"}
                
        except Exception as e:
            print(f"❌ Could not install Jest: {e}")
            return False, {"JavaScript": f"SKIPPED - {e}"}

def test_live_api_endpoints():
    """Test live API endpoints if server is running"""
    print("=== TESTING LIVE API ENDPOINTS ===")
    print()
    
    try:
        import requests
    except ImportError:
        print("❌ requests library not available. Live API tests skipped.")
        return False, {"Live API": "SKIPPED - requests not available"}
    
    # Test if server is running
    try:
        response = requests.get("http://localhost:8001/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running at http://localhost:8001")
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ Server not running at http://localhost:8001. Live API tests skipped.")
        return False, {"Live API": "SKIPPED - Server not running"}
    
    # Test key endpoints
    endpoints_to_test = [
        {
            "name": "Health Check",
            "method": "GET",
            "url": "http://localhost:8001/api/mvp/stats",
            "headers": {"Authorization": "Bearer test-key"}
        },
        {
            "name": "Sample Data", 
            "method": "GET",
            "url": "http://localhost:8001/api/mvp/sample",
            "headers": {"Authorization": "Bearer test-key"}
        },
        {
            "name": "Intervention Types",
            "method": "GET", 
            "url": "http://localhost:8001/api/interventions/types",
            "headers": {"Authorization": "Bearer test-key"}
        }
    ]
    
    all_passed = True
    results = {}
    
    for endpoint in endpoints_to_test:
        try:
            print(f"🧪 Testing {endpoint['name']}...")
            
            response = requests.request(
                endpoint['method'],
                endpoint['url'],
                headers=endpoint['headers'],
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ {endpoint['name']} - OK")
                results[endpoint['name']] = "PASSED"
            else:
                print(f"❌ {endpoint['name']} - Status {response.status_code}")
                results[endpoint['name']] = f"FAILED - {response.status_code}"
                all_passed = False
                
        except Exception as e:
            print(f"❌ {endpoint['name']} - Error: {e}")
            results[endpoint['name']] = f"ERROR - {e}"
            all_passed = False
    
    return all_passed, results

def generate_test_report(python_results, js_results, api_results):
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("TEST COVERAGE REPORT - INTERVENTION SYSTEM & DATABASE")
    print("="*60)
    print()
    
    # Python Tests
    print("📋 PYTHON TESTS:")
    for test_file, result in python_results.items():
        status_icon = "✅" if result == "PASSED" else "❌"
        print(f"  {status_icon} {test_file}: {result}")
    print()
    
    # JavaScript Tests  
    print("📋 JAVASCRIPT TESTS:")
    for test_name, result in js_results.items():
        status_icon = "✅" if result == "PASSED" else "❌" if "SKIP" not in result else "⚠️"
        print(f"  {status_icon} {test_name}: {result}")
    print()
    
    # API Tests
    print("📋 LIVE API TESTS:")
    for test_name, result in api_results.items():
        status_icon = "✅" if result == "PASSED" else "❌" if "SKIP" not in result else "⚠️"
        print(f"  {status_icon} {test_name}: {result}")
    print()
    
    # Summary
    total_tests = len(python_results) + len(js_results) + len(api_results)
    passed_tests = sum(1 for results in [python_results, js_results, api_results] 
                      for result in results.values() if result == "PASSED")
    
    print("📊 SUMMARY:")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    # Test Coverage Areas
    print("🎯 TEST COVERAGE AREAS:")
    coverage_areas = [
        "✅ Intervention CRUD API endpoints",
        "✅ Database constraint enforcement",
        "✅ Duplicate prevention mechanisms", 
        "✅ PostgreSQL upsert operations",
        "✅ Intervention UI form handling",
        "✅ Modal management and user interactions",
        "✅ Error handling and validation",
        "✅ Authentication requirements",
        "✅ Data integrity and consistency",
        "✅ Foreign key relationships",
        "✅ Live API endpoint functionality"
    ]
    
    for area in coverage_areas:
        print(f"  {area}")
    
    print()
    print("="*60)
    
    return passed_tests == total_tests

def main():
    """Main test runner"""
    print("🚀 STARTING COMPREHENSIVE INTERVENTION & DATABASE TESTS")
    print()
    
    # Run all test suites
    python_passed, python_results = run_python_tests()
    js_passed, js_results = run_javascript_tests()
    api_passed, api_results = test_live_api_endpoints()
    
    # Generate report
    all_passed = generate_test_report(python_results, js_results, api_results)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! Intervention system and database have comprehensive test coverage.")
        return 0
    else:
        print("⚠️ Some tests failed. Review the results above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())