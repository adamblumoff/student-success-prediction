#!/usr/bin/env python3
"""
Comprehensive test runner for Student Success Prediction MVP system.
Handles setup, execution, and cleanup of all test suites.
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def setup_test_environment():
    """Set up the test environment with required variables and database."""
    print("🔧 Setting up test environment...")
    
    # Set test environment variables
    test_env = {
        'TESTING': 'true',
        'MVP_API_KEY': 'test-key-comprehensive',
        'DATABASE_URL': 'sqlite:///./test_comprehensive.db',
        'DEVELOPMENT_MODE': 'true',
        'PYTHONPATH': f"{project_root}:{project_root}/src"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    # Initialize database
    try:
        from mvp.database import init_database
        init_database()
        print("✅ Test database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    return test_env

def cleanup_test_environment():
    """Clean up test environment and temporary files."""
    print("🧹 Cleaning up test environment...")
    
    # Remove test databases
    test_dbs = [
        'test_comprehensive.db',
        'test_api.db',
        'test_analysis.db',
        'test_sample.db',
        'test_explain.db',
        'test_k12.db',
        'test_demo.db',
        'test_rate_limit.db',
        'test_api_perf.db',
        'mvp_data.db'
    ]
    
    for db_file in test_dbs:
        db_path = project_root / db_file
        if db_path.exists():
            try:
                db_path.unlink()
                print(f"   Removed {db_file}")
            except Exception as e:
                print(f"   Warning: Could not remove {db_file}: {e}")
    
    # Clean up coverage files
    coverage_files = [
        '.coverage',
        'coverage.xml',
        'tests/coverage_html'
    ]
    
    for coverage_file in coverage_files:
        coverage_path = project_root / coverage_file
        if coverage_path.exists():
            try:
                if coverage_path.is_dir():
                    shutil.rmtree(coverage_path)
                else:
                    coverage_path.unlink()
                print(f"   Removed {coverage_file}")
            except Exception as e:
                print(f"   Warning: Could not remove {coverage_file}: {e}")

def run_test_suite(test_type=None, verbose=False, coverage=False):
    """Run specific test suite with proper error handling."""
    cmd = [sys.executable, 'tests/run_tests.py', '--no-prereq-check']
    
    if test_type:
        cmd.append(test_type)
    
    if verbose:
        cmd.append('--verbose')
    
    if coverage:
        cmd.append('--coverage')
    
    print(f"🚀 Running {'all' if not test_type else test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        print(f"⏱️  Test execution time: {duration:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("📊 STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Test suite timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"💥 Error running tests: {e}")
        return False

def run_performance_benchmarks():
    """Run performance benchmarks and report results."""
    print("⚡ Running performance benchmarks...")
    
    try:
        # Run batch performance test
        result = subprocess.run([
            sys.executable, 'test_batch_performance.py'
        ], cwd=project_root, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Batch performance test passed")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Batch performance test failed")
            if result.stderr:
                print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"⚠️  Performance benchmark error: {e}")
        return False

def validate_models():
    """Validate that all models are loadable and functional."""
    print("🤖 Validating ML models...")
    
    try:
        # Test K-12 Ultra Advanced Model
        from models.k12_ultra_predictor import K12UltraPredictor
        predictor = K12UltraPredictor()
        model_info = predictor.get_model_info()
        print(f"✅ K-12 Ultra Model: {model_info['auc_score']:.3f} AUC")
        
        # Test Original Model
        from models.intervention_system import InterventionRecommendationSystem
        system = InterventionRecommendationSystem()
        print(f"✅ Original Model: {len(system.feature_columns)} features")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        return False

def run_api_health_check():
    """Run a quick health check on the API."""
    print("🏥 Running API health check...")
    
    try:
        from fastapi.testclient import TestClient
        from mvp.mvp_api import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API health check error: {e}")
        return False

def generate_test_report(results):
    """Generate a comprehensive test report."""
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE TEST REPORT")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"📊 Overall Results: {passed_tests}/{total_tests} test suites passed")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🕐 Report generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed_tests == total_tests

def main():
    """Main test execution function."""
    print("🧪 Student Success Prediction - Comprehensive Test Suite")
    print("="*80)
    
    # Setup
    setup_test_environment()
    
    # Track results
    results = {}
    
    try:
        # Run individual test suites
        print("\n1️⃣  Running Unit Tests...")
        results['Unit Tests'] = run_test_suite('unit', verbose=True)
        
        print("\n2️⃣  Running Integration Tests...")
        results['Integration Tests'] = run_test_suite('integration', verbose=True)
        
        print("\n3️⃣  Running Performance Tests...")
        results['Performance Tests'] = run_test_suite('performance', verbose=True)
        
        print("\n4️⃣  Running Performance Benchmarks...")
        results['Performance Benchmarks'] = run_performance_benchmarks()
        
        print("\n5️⃣  Validating Models...")
        results['Model Validation'] = validate_models()
        
        print("\n6️⃣  API Health Check...")
        results['API Health Check'] = run_api_health_check()
        
        # Generate final report
        print("\n7️⃣  Generating Test Report...")
        overall_success = generate_test_report(results)
        
        if overall_success:
            print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
            return 0
        else:
            print("\n💔 SOME TESTS FAILED! Please review the results above.")
            return 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        return 1
    finally:
        cleanup_test_environment()

if __name__ == "__main__":
    sys.exit(main())