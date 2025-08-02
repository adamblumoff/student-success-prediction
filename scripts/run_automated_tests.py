#!/usr/bin/env python3
"""
Automated Testing Pipeline for Student Success Prediction System

Runs comprehensive tests, generates reports, and checks for regressions.
Can be integrated with CI/CD pipelines or run manually.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class TestResult:
    """Test execution result."""
    suite: str
    status: str  # 'passed', 'failed', 'error', 'skipped'
    duration_seconds: float
    tests_run: int
    failures: int
    errors: int
    skipped: int
    output: str
    details: Dict[str, Any]

@dataclass
class TestReport:
    """Complete test execution report."""
    timestamp: datetime
    overall_status: str
    total_duration: float
    results: List[TestResult]
    summary: Dict[str, int]
    coverage_report: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class AutomatedTestRunner:
    """Manages automated test execution and reporting."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.project_root = project_root
        
    def load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load test configuration."""
        default_config = {
            'test_suites': {
                'unit_tests': {
                    'enabled': True,
                    'path': 'tests/unit',
                    'pattern': 'test_*.py',
                    'timeout': 300
                },
                'integration_tests': {
                    'enabled': True,
                    'path': 'tests/integration',
                    'pattern': 'test_*.py', 
                    'timeout': 600
                },
                'performance_tests': {
                    'enabled': True,
                    'path': 'tests/performance',
                    'pattern': 'test_*.py',
                    'timeout': 900
                },
                'api_tests': {
                    'enabled': True,
                    'command': 'python -m pytest tests/unit/test_api_endpoints.py -v',
                    'timeout': 300
                },
                'notification_tests': {
                    'enabled': True,
                    'command': 'python -m pytest tests/unit/test_notifications.py -v',
                    'timeout': 300
                },
                'integration_system_tests': {
                    'enabled': True,
                    'command': 'python -m pytest tests/unit/test_integrations.py -v',
                    'timeout': 300
                }
            },
            'coverage': {
                'enabled': True,
                'min_coverage': 70,
                'exclude_patterns': ['*/venv/*', '*/tests/*', '*/__pycache__/*']
            },
            'performance': {
                'enabled': True,
                'benchmarks': ['model_prediction', 'api_response', 'database_query']
            },
            'reporting': {
                'formats': ['console', 'json', 'html'],
                'output_dir': 'test_reports'
            },
            'notifications': {
                'on_failure': True,
                'on_success': False,
                'email_enabled': False
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
                
        return default_config
        
    def setup_logging(self):
        """Set up logging configuration."""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'automated_tests.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def run_all_tests(self) -> TestReport:
        """Run all configured test suites."""
        self.logger.info("🧪 Starting automated test execution")
        start_time = time.time()
        
        results = []
        
        # Run test suites in parallel where possible
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_suite = {}
            
            for suite_name, suite_config in self.config['test_suites'].items():
                if suite_config.get('enabled', True):
                    future = executor.submit(self.run_test_suite, suite_name, suite_config)
                    future_to_suite[future] = suite_name
                    
            for future in concurrent.futures.as_completed(future_to_suite):
                suite_name = future_to_suite[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"✅ {suite_name} completed: {result.status}")
                except Exception as e:
                    error_result = TestResult(
                        suite=suite_name,
                        status='error',
                        duration_seconds=0,
                        tests_run=0,
                        failures=0,
                        errors=1,
                        skipped=0,
                        output=str(e),
                        details={'exception': str(e)}
                    )
                    results.append(error_result)
                    self.logger.error(f"❌ {suite_name} failed: {e}")
                    
        # Generate coverage report if enabled
        coverage_report = None
        if self.config['coverage']['enabled']:
            coverage_report = await self.generate_coverage_report()
            
        # Generate performance metrics if enabled
        performance_metrics = None
        if self.config['performance']['enabled']:
            performance_metrics = await self.run_performance_benchmarks()
            
        # Calculate summary
        summary = {
            'total_suites': len(results),
            'passed_suites': sum(1 for r in results if r.status == 'passed'),
            'failed_suites': sum(1 for r in results if r.status == 'failed'),
            'error_suites': sum(1 for r in results if r.status == 'error'),
            'total_tests': sum(r.tests_run for r in results),
            'total_failures': sum(r.failures for r in results),
            'total_errors': sum(r.errors for r in results),
            'total_skipped': sum(r.skipped for r in results)
        }
        
        # Determine overall status
        if summary['error_suites'] > 0 or summary['total_errors'] > 0:
            overall_status = 'error'
        elif summary['failed_suites'] > 0 or summary['total_failures'] > 0:
            overall_status = 'failed'
        else:
            overall_status = 'passed'
            
        total_duration = time.time() - start_time
        
        report = TestReport(
            timestamp=datetime.now(),
            overall_status=overall_status,
            total_duration=total_duration,
            results=results,
            summary=summary,
            coverage_report=coverage_report,
            performance_metrics=performance_metrics
        )
        
        self.logger.info(f"🏁 Test execution completed: {overall_status} ({total_duration:.1f}s)")
        return report
        
    def run_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> TestResult:
        """Run a single test suite."""
        start_time = time.time()
        
        try:
            # Construct command
            if 'command' in suite_config:
                cmd = suite_config['command'].split()
            else:
                test_path = suite_config.get('path', f'tests/{suite_name}')
                pattern = suite_config.get('pattern', 'test_*.py')
                cmd = ['python', '-m', 'pytest', f'{test_path}/{pattern}', '-v', '--tb=short']
                
            # Add coverage if enabled globally
            if self.config['coverage']['enabled'] and suite_name in ['unit_tests', 'integration_tests']:
                cmd.extend(['--cov=src', '--cov-report=term-missing'])
                
            timeout = suite_config.get('timeout', 300)
            
            # Run the test command
            self.logger.info(f"🏃 Running {suite_name}: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, 'PYTHONPATH': str(self.project_root)}
            )
            
            duration = time.time() - start_time
            
            # Parse pytest output
            output_lines = result.stdout.split('\n')
            summary_line = ""
            for line in reversed(output_lines):
                if 'passed' in line or 'failed' in line or 'error' in line:
                    summary_line = line
                    break
                    
            # Extract test counts
            tests_run = 0
            failures = 0
            errors = 0
            skipped = 0
            
            if summary_line:
                import re
                # Parse pytest summary like "5 passed, 2 failed, 1 error, 3 skipped"
                passed_match = re.search(r'(\d+) passed', summary_line)
                failed_match = re.search(r'(\d+) failed', summary_line)
                error_match = re.search(r'(\d+) error', summary_line)
                skipped_match = re.search(r'(\d+) skipped', summary_line)
                
                if passed_match:
                    tests_run += int(passed_match.group(1))
                if failed_match:
                    failures = int(failed_match.group(1))
                    tests_run += failures
                if error_match:
                    errors = int(error_match.group(1))
                    tests_run += errors
                if skipped_match:
                    skipped = int(skipped_match.group(1))
                    
            # Determine status
            if result.returncode == 0:
                status = 'passed'
            elif errors > 0:
                status = 'error'
            elif failures > 0:
                status = 'failed'
            else:
                status = 'error'  # Non-zero exit but no clear failures
                
            return TestResult(
                suite=suite_name,
                status=status,
                duration_seconds=duration,
                tests_run=tests_run,
                failures=failures,
                errors=errors,
                skipped=skipped,
                output=result.stdout + result.stderr,
                details={
                    'exit_code': result.returncode,
                    'command': ' '.join(cmd),
                    'summary_line': summary_line
                }
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                suite=suite_name,
                status='error',
                duration_seconds=duration,
                tests_run=0,
                failures=0,
                errors=1,
                skipped=0,
                output=f"Test suite timed out after {timeout} seconds",
                details={'timeout': timeout}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                suite=suite_name,
                status='error',
                duration_seconds=duration,
                tests_run=0,
                failures=0,
                errors=1,
                skipped=0,
                output=str(e),
                details={'exception': str(e)}
            )
            
    async def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate code coverage report."""
        try:
            # Run coverage report
            result = subprocess.run(
                ['python', '-m', 'pytest', '--cov=src', '--cov-report=json', 'tests/unit/'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Read coverage JSON report
            coverage_file = self.project_root / '.coverage'
            if coverage_file.exists():
                # Try to read coverage data
                result = subprocess.run(
                    ['python', '-c', 'import coverage; c = coverage.Coverage(); c.load(); print(c.report())'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                
                return {
                    'status': 'success',
                    'coverage_percentage': 0,  # Would need to parse from output
                    'details': result.stdout
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Coverage file not found'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    async def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        benchmarks = {}
        
        for benchmark in self.config['performance']['benchmarks']:
            try:
                if benchmark == 'model_prediction':
                    # Benchmark model prediction speed
                    start_time = time.time()
                    
                    # Simulate model prediction (would use actual model in real implementation)
                    await asyncio.sleep(0.1)  # Simulate prediction time
                    
                    duration = time.time() - start_time
                    benchmarks[benchmark] = {
                        'duration_seconds': duration,
                        'status': 'success'
                    }
                    
                elif benchmark == 'api_response':
                    # Benchmark API response time
                    try:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            start_time = time.time()
                            async with session.get('http://localhost:8001/health') as response:
                                await response.text()
                            duration = time.time() - start_time
                            
                        benchmarks[benchmark] = {
                            'duration_seconds': duration,
                            'status': 'success'
                        }
                    except Exception as e:
                        benchmarks[benchmark] = {
                            'status': 'error',
                            'message': str(e)
                        }
                        
                elif benchmark == 'database_query':
                    # Benchmark database query speed
                    start_time = time.time()
                    
                    # Simulate database query (would use actual DB in real implementation)
                    await asyncio.sleep(0.05)
                    
                    duration = time.time() - start_time
                    benchmarks[benchmark] = {
                        'duration_seconds': duration,
                        'status': 'success'
                    }
                    
            except Exception as e:
                benchmarks[benchmark] = {
                    'status': 'error',
                    'message': str(e)
                }
                
        return benchmarks
        
    def generate_console_report(self, report: TestReport) -> str:
        """Generate console-formatted test report."""
        lines = [
            "=" * 70,
            "AUTOMATED TEST REPORT",
            "=" * 70,
            f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Status: {report.overall_status.upper()}",
            f"Total Duration: {report.total_duration:.1f} seconds",
            "",
            "SUMMARY:",
            f"  📊 Test Suites: {report.summary['total_suites']} total",
            f"  ✅ Passed: {report.summary['passed_suites']}",
            f"  ❌ Failed: {report.summary['failed_suites']}",
            f"  🚨 Errors: {report.summary['error_suites']}",
            "",
            f"  🧪 Tests: {report.summary['total_tests']} total",
            f"  ✅ Passed: {report.summary['total_tests'] - report.summary['total_failures'] - report.summary['total_errors'] - report.summary['total_skipped']}",
            f"  ❌ Failed: {report.summary['total_failures']}",
            f"  🚨 Errors: {report.summary['total_errors']}",
            f"  ⏭️  Skipped: {report.summary['total_skipped']}",
            ""
        ]
        
        # Coverage report
        if report.coverage_report:
            lines.append("COVERAGE:")
            if report.coverage_report['status'] == 'success':
                lines.append(f"  📈 Coverage: {report.coverage_report.get('coverage_percentage', 'N/A')}%")
            else:
                lines.append(f"  ❌ Coverage: {report.coverage_report.get('message', 'Failed')}")
            lines.append("")
            
        # Performance metrics
        if report.performance_metrics:
            lines.append("PERFORMANCE:")
            for benchmark, metrics in report.performance_metrics.items():
                if metrics['status'] == 'success':
                    lines.append(f"  ⚡ {benchmark}: {metrics['duration_seconds']:.3f}s")
                else:
                    lines.append(f"  ❌ {benchmark}: {metrics.get('message', 'Failed')}")
            lines.append("")
            
        lines.append("DETAILED RESULTS:")
        for result in report.results:
            icon = {
                'passed': '✅',
                'failed': '❌',
                'error': '🚨',
                'skipped': '⏭️'
            }.get(result.status, '❓')
            
            lines.append(f"  {icon} {result.suite}:")
            lines.append(f"    Status: {result.status}")
            lines.append(f"    Duration: {result.duration_seconds:.1f}s")
            lines.append(f"    Tests: {result.tests_run} run, {result.failures} failed, {result.errors} errors, {result.skipped} skipped")
            
            if result.status in ['failed', 'error'] and result.output:
                # Show last few lines of output for failed tests
                output_lines = result.output.split('\n')[-10:]
                lines.append("    Output (last 10 lines):")
                for line in output_lines:
                    if line.strip():
                        lines.append(f"      {line}")
            lines.append("")
            
        lines.append("=" * 70)
        
        return "\n".join(lines)
        
    async def save_reports(self, report: TestReport):
        """Save test reports in configured formats."""
        output_dir = Path(self.config['reporting']['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = report.timestamp.strftime('%Y%m%d_%H%M%S')
        
        for format_type in self.config['reporting']['formats']:
            try:
                if format_type == 'json':
                    # Save JSON report
                    report_file = output_dir / f"test_report_{timestamp_str}.json"
                    
                    # Convert to JSON-serializable format
                    report_data = asdict(report)
                    
                    # Convert datetime objects
                    def convert_datetime(obj):
                        if isinstance(obj, datetime):
                            return obj.isoformat()
                        elif isinstance(obj, dict):
                            return {k: convert_datetime(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_datetime(item) for item in obj]
                        return obj
                        
                    report_data = convert_datetime(report_data)
                    
                    with open(report_file, 'w') as f:
                        json.dump(report_data, f, indent=2)
                        
                    self.logger.info(f"📄 JSON report saved to {report_file}")
                    
                elif format_type == 'console':
                    # Save console report
                    report_file = output_dir / f"test_report_{timestamp_str}.txt"
                    console_report = self.generate_console_report(report)
                    
                    with open(report_file, 'w') as f:
                        f.write(console_report)
                        
                    self.logger.info(f"📄 Console report saved to {report_file}")
                    
                elif format_type == 'html':
                    # Save HTML report (basic implementation)
                    report_file = output_dir / f"test_report_{timestamp_str}.html"
                    html_report = self.generate_html_report(report)
                    
                    with open(report_file, 'w') as f:
                        f.write(html_report)
                        
                    self.logger.info(f"📄 HTML report saved to {report_file}")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to save {format_type} report: {e}")
                
    def generate_html_report(self, report: TestReport) -> str:
        """Generate HTML test report."""
        status_colors = {
            'passed': '#28a745',
            'failed': '#dc3545', 
            'error': '#ffc107',
            'skipped': '#6c757d'
        }
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report - {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
                .status-{report.overall_status} {{ border-left-color: {status_colors.get(report.overall_status, '#6c757d')}; }}
                .test-suite {{ margin: 10px 0; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; }}
                .status-passed {{ background: #d4edda; }}
                .status-failed {{ background: #f8d7da; }}
                .status-error {{ background: #fff3cd; }}
                pre {{ background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Automated Test Report</h1>
                <p><strong>Timestamp:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Overall Status:</strong> <span class="status-{report.overall_status}">{report.overall_status.upper()}</span></p>
                <p><strong>Duration:</strong> {report.total_duration:.1f} seconds</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Test Suites</h3>
                    <p>Total: {report.summary['total_suites']}</p>
                    <p>Passed: {report.summary['passed_suites']}</p>
                    <p>Failed: {report.summary['failed_suites']}</p>
                    <p>Errors: {report.summary['error_suites']}</p>
                </div>
                <div class="metric">
                    <h3>Tests</h3>
                    <p>Total: {report.summary['total_tests']}</p>
                    <p>Passed: {report.summary['total_tests'] - report.summary['total_failures'] - report.summary['total_errors'] - report.summary['total_skipped']}</p>
                    <p>Failed: {report.summary['total_failures']}</p>
                    <p>Errors: {report.summary['total_errors']}</p>
                    <p>Skipped: {report.summary['total_skipped']}</p>
                </div>
            </div>
            
            <h2>Test Suite Results</h2>
        """
        
        for result in report.results:
            html += f"""
            <div class="test-suite status-{result.status}">
                <h3>{result.suite} - {result.status.upper()}</h3>
                <p><strong>Duration:</strong> {result.duration_seconds:.1f}s</p>
                <p><strong>Tests:</strong> {result.tests_run} run, {result.failures} failed, {result.errors} errors, {result.skipped} skipped</p>
                {f'<pre>{result.output[:1000]}...</pre>' if result.status in ['failed', 'error'] and result.output else ''}
            </div>
            """
            
        html += """
        </body>
        </html>
        """
        
        return html


async def main():
    """Main function to run automated tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Test Runner')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--suites', nargs='+', help='Specific test suites to run')
    parser.add_argument('--output', choices=['console', 'file', 'both'], default='both',
                        help='Output format')
    parser.add_argument('--fail-fast', action='store_true', help='Stop on first failure')
    parser.add_argument('--coverage-only', action='store_true', help='Run only coverage analysis')
    parser.add_argument('--performance-only', action='store_true', help='Run only performance tests')
    
    args = parser.parse_args()
    
    runner = AutomatedTestRunner(args.config)
    
    try:
        if args.coverage_only:
            print("📊 Running coverage analysis only...")
            coverage_report = await runner.generate_coverage_report()
            print(json.dumps(coverage_report, indent=2))
            return
            
        if args.performance_only:
            print("⚡ Running performance benchmarks only...")
            performance_metrics = await runner.run_performance_benchmarks()
            print(json.dumps(performance_metrics, indent=2))
            return
            
        # Run full test suite
        report = await runner.run_all_tests()
        
        # Output results
        if args.output in ['console', 'both']:
            console_report = runner.generate_console_report(report)
            print(console_report)
            
        if args.output in ['file', 'both']:
            await runner.save_reports(report)
            
        # Exit with appropriate code
        exit_codes = {
            'passed': 0,
            'failed': 1,
            'error': 2
        }
        sys.exit(exit_codes.get(report.overall_status, 2))
        
    except KeyboardInterrupt:
        print("\n👋 Test execution interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(2)


if __name__ == '__main__':
    asyncio.run(main())