#!/usr/bin/env python3
"""
Main test runner for Student Success Prediction MVP system.

Usage:
    python tests/run_tests.py                 # Run all tests
    python tests/run_tests.py unit           # Run only unit tests
    python tests/run_tests.py integration    # Run only integration tests
    python tests/run_tests.py performance    # Run only performance tests
    python tests/run_tests.py --verbose      # Run with verbose output
    python tests/run_tests.py --coverage     # Run with coverage report
"""

import sys
import os
import argparse
import unittest
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def discover_tests(test_type=None, pattern="test_*.py"):
    """Discover and load tests based on type."""
    test_dir = Path(__file__).parent
    
    if test_type:
        suite_dir = test_dir / test_type
        if not suite_dir.exists():
            print(f"❌ Test directory '{test_type}' not found")
            return None
        loader = unittest.TestLoader()
        return loader.discover(str(suite_dir), pattern=pattern)
    else:
        # Load all tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for test_subdir in ['unit', 'integration', 'performance']:
            subdir_path = test_dir / test_subdir
            if subdir_path.exists():
                subsuite = loader.discover(str(subdir_path), pattern=pattern)
                suite.addTest(subsuite)
        
        return suite

def run_tests_with_coverage(test_suite, verbose=False):
    """Run tests with coverage reporting."""
    try:
        import coverage
        
        # Start coverage
        cov = coverage.Coverage(source=['src'])
        cov.start()
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        result = runner.run(test_suite)
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\n" + "="*50)
        print("📊 COVERAGE REPORT")
        print("="*50)
        cov.report()
        
        # Generate HTML report
        html_dir = project_root / "tests" / "coverage_html"
        cov.html_report(directory=str(html_dir))
        print(f"\n📄 HTML coverage report: file://{html_dir}/index.html")
        
        return result
        
    except ImportError:
        print("⚠️  Coverage package not installed. Running tests without coverage.")
        print("   Install with: pip install coverage")
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
        return runner.run(test_suite)

def print_test_summary(result, start_time):
    """Print a comprehensive test summary."""
    duration = time.time() - start_time
    
    print("\n" + "="*60)
    print("🧪 TEST EXECUTION SUMMARY")
    print("="*60)
    
    print(f"⏱️  Total execution time: {duration:.2f} seconds")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"🎯 Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print(f"❌ Failures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"   • {test}")
    
    if result.errors:
        print(f"💥 Errors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"   • {test}")
    
    if result.skipped:
        print(f"⏭️  Skipped: {len(result.skipped)}")
        for test, reason in result.skipped:
            print(f"   • {test}: {reason}")
    
    # Overall result
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n💔 {len(result.failures + result.errors)} TESTS FAILED")
        return 1

def check_prerequisites():
    """Check if system prerequisites are met for testing."""
    print("🔍 Checking test prerequisites...")
    
    missing_packages = []
    
    # Check required packages
    required_packages = [
        'fastapi', 'pandas', 'numpy', 'sklearn', 'sqlalchemy', 'pytest'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("   Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check if models exist
    models_dir = project_root / "results" / "models"
    if not models_dir.exists():
        print("⚠️  Models directory not found. Some tests may fail.")
        print("   Run training scripts first: python src/models/train_models.py")
    
    print("✅ Prerequisites check completed")
    return True

def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Student Success Prediction Test Runner")
    parser.add_argument('test_type', nargs='?', choices=['unit', 'integration', 'performance'], 
                       help='Type of tests to run (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose test output')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run with coverage reporting')
    parser.add_argument('--pattern', '-p', default='test_*.py',
                       help='Test file pattern (default: test_*.py)')
    parser.add_argument('--no-prereq-check', action='store_true',
                       help='Skip prerequisite checks')
    
    args = parser.parse_args()
    
    print("🚀 Student Success Prediction MVP - Test Suite")
    print("=" * 60)
    
    # Check prerequisites
    if not args.no_prereq_check:
        if not check_prerequisites():
            return 1
    
    # Discover tests
    print(f"🔍 Discovering {args.test_type or 'all'} tests...")
    test_suite = discover_tests(args.test_type, args.pattern)
    
    if not test_suite or test_suite.countTestCases() == 0:
        print("❌ No tests found!")
        return 1
    
    print(f"📋 Found {test_suite.countTestCases()} test cases")
    
    # Set up test environment
    os.environ['TESTING'] = 'true'
    os.environ['MVP_API_KEY'] = 'test-key-12345'
    os.environ['DATABASE_URL'] = 'sqlite:///./test_mvp.db'
    
    start_time = time.time()
    
    try:
        # Run tests
        if args.coverage:
            result = run_tests_with_coverage(test_suite, args.verbose)
        else:
            runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
            result = runner.run(test_suite)
        
        # Print summary
        return print_test_summary(result, start_time)
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        return 1
    finally:
        # Cleanup
        test_db = project_root / "test_mvp.db"
        if test_db.exists():
            test_db.unlink()
            print("🧹 Cleaned up test database")

if __name__ == "__main__":
    sys.exit(main())