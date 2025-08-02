#!/usr/bin/env python3
"""
System Health Monitor for Student Success Prediction System

Monitors system health, runs diagnostic checks, and sends alerts for issues.
Can be run manually or scheduled via cron.
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiohttp
import asyncpg
import sqlite3
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

@dataclass
class HealthCheck:
    """Health check result."""
    component: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: Optional[float] = None

@dataclass
class SystemHealthReport:
    """Complete system health report."""
    timestamp: datetime
    overall_status: str
    checks: List[HealthCheck]
    summary: Dict[str, int]
    alerts: List[str]

class SystemHealthMonitor:
    """Monitors system health and generates reports."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.base_url = self.config.get('base_url', 'http://localhost:8001')
        self.api_key = self.config.get('api_key', os.getenv('MVP_API_KEY', 'dev-key-change-me'))
        
    def load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            'base_url': 'http://localhost:8001',
            'api_key': None,
            'checks': {
                'api_endpoints': True,
                'database': True,
                'models': True,
                'notifications': True,
                'integrations': True,
                'file_system': True
            },
            'thresholds': {
                'response_time_ms': 5000,
                'memory_usage_mb': 1000,
                'disk_usage_percent': 85
            },
            'email_alerts': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': None,
                'password': None,
                'recipients': []
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
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', 'logs/health_monitor.log')
        
        # Create logs directory if it doesn't exist
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def run_health_checks(self) -> SystemHealthReport:
        """Run all configured health checks."""
        self.logger.info("🔍 Starting system health checks")
        
        checks = []
        start_time = datetime.now()
        
        # Run enabled checks
        if self.config['checks']['api_endpoints']:
            checks.extend(await self.check_api_endpoints())
            
        if self.config['checks']['database']:
            checks.append(await self.check_database())
            
        if self.config['checks']['models']:
            checks.append(await self.check_models())
            
        if self.config['checks']['notifications']:
            checks.append(await self.check_notifications())
            
        if self.config['checks']['integrations']:
            checks.extend(await self.check_integrations())
            
        if self.config['checks']['file_system']:
            checks.extend(await self.check_file_system())
            
        # Generate summary
        summary = {
            'healthy': sum(1 for c in checks if c.status == 'healthy'),
            'warning': sum(1 for c in checks if c.status == 'warning'),
            'critical': sum(1 for c in checks if c.status == 'critical'),
            'unknown': sum(1 for c in checks if c.status == 'unknown'),
            'total': len(checks)
        }
        
        # Determine overall status
        if summary['critical'] > 0:
            overall_status = 'critical'
        elif summary['warning'] > 0:
            overall_status = 'warning'
        elif summary['healthy'] == summary['total']:
            overall_status = 'healthy'
        else:
            overall_status = 'unknown'
            
        # Generate alerts
        alerts = []
        for check in checks:
            if check.status in ['critical', 'warning']:
                alerts.append(f"{check.component}: {check.message}")
                
        report = SystemHealthReport(
            timestamp=start_time,
            overall_status=overall_status,
            checks=checks,
            summary=summary,
            alerts=alerts
        )
        
        self.logger.info(f"✅ Health checks completed: {overall_status} status")
        return report
        
    async def check_api_endpoints(self) -> List[HealthCheck]:
        """Check API endpoint health."""
        endpoints = [
            ('Main API', '/health'),
            ('Core MVP', '/api/mvp/sample'),
            ('Canvas LMS', '/api/lms/canvas/health'),
            ('PowerSchool SIS', '/api/sis/powerschool/health'),
            ('Google Classroom', '/api/google/health'),
            ('Notifications', '/api/notifications/health'),
            ('Combined Integration', '/api/integration/health')
        ]
        
        checks = []
        headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        
        async with aiohttp.ClientSession() as session:
            for name, endpoint in endpoints:
                try:
                    start_time = time.time()
                    
                    async with session.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            data = await response.json()
                            status = 'healthy'
                            message = f"API responding normally ({response.status})"
                        elif response.status == 401:
                            status = 'warning'
                            message = "Authentication required"
                            data = {}
                        else:
                            status = 'warning'
                            message = f"HTTP {response.status}"
                            data = {}
                            
                        # Check response time
                        if response_time > self.config['thresholds']['response_time_ms']:
                            status = 'warning' if status == 'healthy' else status
                            message += f" (slow response: {response_time:.0f}ms)"
                            
                        checks.append(HealthCheck(
                            component=f"API: {name}",
                            status=status,
                            message=message,
                            details=data,
                            timestamp=datetime.now(),
                            response_time_ms=response_time
                        ))
                        
                except asyncio.TimeoutError:
                    checks.append(HealthCheck(
                        component=f"API: {name}",
                        status='critical',
                        message="Request timeout",
                        details={},
                        timestamp=datetime.now()
                    ))
                except Exception as e:
                    checks.append(HealthCheck(
                        component=f"API: {name}",
                        status='critical',
                        message=f"Connection failed: {str(e)}",
                        details={'error': str(e)},
                        timestamp=datetime.now()
                    ))
                    
        return checks
        
    async def check_database(self) -> HealthCheck:
        """Check database connectivity and health."""
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            return HealthCheck(
                component="Database",
                status='warning',
                message="No DATABASE_URL configured, using SQLite fallback",
                details={'type': 'sqlite'},
                timestamp=datetime.now()
            )
            
        try:
            if database_url.startswith('postgresql'):
                # PostgreSQL health check
                conn = await asyncpg.connect(database_url)
                
                # Test basic query
                result = await conn.fetchval('SELECT 1')
                
                # Check table existence
                tables_query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                """
                tables = await conn.fetch(tables_query)
                table_names = [row['table_name'] for row in tables]
                
                await conn.close()
                
                status = 'healthy'
                message = f"PostgreSQL connected, {len(table_names)} tables"
                details = {
                    'type': 'postgresql',
                    'tables': table_names,
                    'connection_test': result == 1
                }
                
            else:
                # SQLite health check
                db_path = database_url.replace('sqlite:///', '')
                if not Path(db_path).exists():
                    status = 'critical'
                    message = f"SQLite database file not found: {db_path}"
                    details = {'type': 'sqlite', 'path': db_path}
                else:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Test basic query
                    cursor.execute('SELECT 1')
                    result = cursor.fetchone()
                    
                    # Check tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    conn.close()
                    
                    status = 'healthy'
                    message = f"SQLite connected, {len(tables)} tables"
                    details = {
                        'type': 'sqlite',
                        'path': db_path,
                        'tables': tables,
                        'connection_test': result[0] == 1
                    }
                    
        except Exception as e:
            status = 'critical'
            message = f"Database connection failed: {str(e)}"
            details = {'error': str(e), 'traceback': traceback.format_exc()}
            
        return HealthCheck(
            component="Database",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
        
    async def check_models(self) -> HealthCheck:
        """Check ML model availability and health."""
        models_dir = Path('results/models')
        
        try:
            if not models_dir.exists():
                return HealthCheck(
                    component="ML Models",
                    status='critical',
                    message="Models directory not found",
                    details={'models_dir': str(models_dir)},
                    timestamp=datetime.now()
                )
                
            # Check for required model files
            required_files = [
                'best_binary_model.pkl',
                'binary_scaler.pkl',
                'feature_columns.json',
                'model_metadata.json'
            ]
            
            k12_dir = models_dir / 'k12'
            k12_files = []
            if k12_dir.exists():
                k12_files = list(k12_dir.glob('k12_ultra_*.pkl'))
                
            missing_files = []
            for file in required_files:
                if not (models_dir / file).exists():
                    missing_files.append(file)
                    
            # Check model metadata
            metadata = {}
            metadata_file = models_dir / 'model_metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
            if missing_files:
                status = 'warning'
                message = f"Missing model files: {', '.join(missing_files)}"
            elif not k12_files:
                status = 'warning'
                message = "K-12 models not found"
            else:
                status = 'healthy'
                message = f"Models loaded, K-12 models: {len(k12_files)}"
                
            details = {
                'models_dir': str(models_dir),
                'required_files_present': len(required_files) - len(missing_files),
                'missing_files': missing_files,
                'k12_models': len(k12_files),
                'metadata': metadata
            }
            
        except Exception as e:
            status = 'critical'
            message = f"Model check failed: {str(e)}"
            details = {'error': str(e)}
            
        return HealthCheck(
            component="ML Models",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
        
    async def check_notifications(self) -> HealthCheck:
        """Check notification system health."""
        try:
            # Import notification system
            from mvp.notifications import notification_system
            
            # Get statistics
            stats = notification_system.get_alert_statistics()
            
            # Check WebSocket connections
            active_connections = len(notification_system.websocket_connections)
            notification_rules = len(notification_system.notification_rules)
            
            status = 'healthy'
            message = f"Notification system active, {notification_rules} rules, {active_connections} connections"
            
            details = {
                'statistics': stats,
                'active_connections': active_connections,
                'notification_rules': notification_rules,
                'default_rules_loaded': notification_rules >= 4
            }
            
        except Exception as e:
            status = 'critical'
            message = f"Notification system error: {str(e)}"
            details = {'error': str(e)}
            
        return HealthCheck(
            component="Notification System",
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now()
        )
        
    async def check_integrations(self) -> List[HealthCheck]:
        """Check integration system health."""
        checks = []
        
        # Check integration modules
        integrations = [
            ('Canvas LMS', 'integrations.canvas_lms'),
            ('PowerSchool SIS', 'integrations.powerschool_sis'),
            ('Google Classroom', 'integrations.google_classroom'),
            ('Combined Integration', 'integrations.combined_integration')
        ]
        
        for name, module_name in integrations:
            try:
                __import__(module_name)
                status = 'healthy'
                message = f"{name} integration module loaded"
                details = {'module': module_name}
            except ImportError as e:
                status = 'warning'
                message = f"{name} integration not available: {str(e)}"
                details = {'module': module_name, 'error': str(e)}
            except Exception as e:
                status = 'critical'
                message = f"{name} integration error: {str(e)}"
                details = {'module': module_name, 'error': str(e)}
                
            checks.append(HealthCheck(
                component=f"Integration: {name}",
                status=status,
                message=message,
                details=details,
                timestamp=datetime.now()
            ))
            
        return checks
        
    async def check_file_system(self) -> List[HealthCheck]:
        """Check file system health."""
        checks = []
        
        # Check disk usage
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            
            usage_percent = (used / total) * 100
            threshold = self.config['thresholds']['disk_usage_percent']
            
            if usage_percent > threshold:
                status = 'warning'
                message = f"Disk usage high: {usage_percent:.1f}%"
            else:
                status = 'healthy'
                message = f"Disk usage normal: {usage_percent:.1f}%"
                
            checks.append(HealthCheck(
                component="Disk Usage",
                status=status,
                message=message,
                details={
                    'total_gb': round(total / (1024**3), 2),
                    'used_gb': round(used / (1024**3), 2),
                    'free_gb': round(free / (1024**3), 2),
                    'usage_percent': round(usage_percent, 1)
                },
                timestamp=datetime.now()
            ))
        except Exception as e:
            checks.append(HealthCheck(
                component="Disk Usage",
                status='unknown',
                message=f"Could not check disk usage: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now()
            ))
            
        # Check critical directories
        critical_dirs = [
            'src/mvp',
            'src/models',
            'results/models',
            'logs'
        ]
        
        for dir_path in critical_dirs:
            path = Path(dir_path)
            if path.exists():
                status = 'healthy'
                message = f"Directory exists"
                
                # Count files in directory
                file_count = len(list(path.rglob('*'))) if path.is_dir() else 0
                details = {'path': str(path), 'file_count': file_count}
            else:
                status = 'warning'
                message = f"Directory missing"
                details = {'path': str(path)}
                
            checks.append(HealthCheck(
                component=f"Directory: {dir_path}",
                status=status,
                message=message,
                details=details,
                timestamp=datetime.now()
            ))
            
        return checks
        
    def generate_report(self, report: SystemHealthReport) -> str:
        """Generate a formatted health report."""
        lines = [
            "=" * 60,
            "SYSTEM HEALTH REPORT",
            "=" * 60,
            f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Status: {report.overall_status.upper()}",
            "",
            "SUMMARY:",
            f"  ✅ Healthy: {report.summary['healthy']}",
            f"  ⚠️  Warning: {report.summary['warning']}",
            f"  🚨 Critical: {report.summary['critical']}",
            f"  ❓ Unknown: {report.summary['unknown']}",
            f"  📊 Total Checks: {report.summary['total']}",
            ""
        ]
        
        if report.alerts:
            lines.append("ALERTS:")
            for alert in report.alerts:
                lines.append(f"  🔥 {alert}")
            lines.append("")
            
        lines.append("DETAILED RESULTS:")
        for check in report.checks:
            icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '🚨',
                'unknown': '❓'
            }.get(check.status, '❓')
            
            lines.append(f"  {icon} {check.component}: {check.message}")
            
            if check.response_time_ms:
                lines.append(f"    Response time: {check.response_time_ms:.0f}ms")
                
        lines.append("=" * 60)
        
        return "\n".join(lines)
        
    async def send_email_alert(self, report: SystemHealthReport):
        """Send email alert if configured and needed."""
        email_config = self.config.get('email_alerts', {})
        if not email_config.get('enabled', False):
            return
            
        if report.overall_status not in ['warning', 'critical']:
            return
            
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = email_config['username']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"System Health Alert - {report.overall_status.upper()}"
            
            body = self.generate_report(report)
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
                
            self.logger.info("📧 Health alert email sent")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send email alert: {e}")
            
    async def save_report(self, report: SystemHealthReport):
        """Save health report to file."""
        reports_dir = Path('logs/health_reports')
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = report.timestamp.strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"health_report_{timestamp_str}.json"
        
        # Convert to JSON-serializable format
        report_data = asdict(report)
        
        # Convert datetime objects to strings
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
            
        self.logger.info(f"📄 Health report saved to {report_file}")


async def main():
    """Main function to run health checks."""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Health Monitor')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--output', choices=['console', 'file', 'both'], default='console',
                        help='Output format')
    parser.add_argument('--email', action='store_true', help='Send email alerts')
    parser.add_argument('--continuous', type=int, help='Run continuously with interval (minutes)')
    
    args = parser.parse_args()
    
    monitor = SystemHealthMonitor(args.config)
    
    async def run_checks():
        """Run health checks and handle output."""
        try:
            report = await monitor.run_health_checks()
            
            # Generate and display report
            formatted_report = monitor.generate_report(report)
            
            if args.output in ['console', 'both']:
                print(formatted_report)
                
            if args.output in ['file', 'both']:
                await monitor.save_report(report)
                
            if args.email:
                await monitor.send_email_alert(report)
                
            return report.overall_status
            
        except Exception as e:
            monitor.logger.error(f"❌ Health check failed: {e}")
            print(f"Health check failed: {e}")
            return 'critical'
            
    if args.continuous:
        print(f"🔄 Running continuous health monitoring (every {args.continuous} minutes)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                status = await run_checks()
                print(f"\n⏰ Next check in {args.continuous} minutes...")
                await asyncio.sleep(args.continuous * 60)
        except KeyboardInterrupt:
            print("\n👋 Health monitoring stopped")
    else:
        status = await run_checks()
        
        # Exit with appropriate code
        exit_codes = {
            'healthy': 0,
            'warning': 1,
            'critical': 2,
            'unknown': 3
        }
        sys.exit(exit_codes.get(status, 3))


if __name__ == '__main__':
    asyncio.run(main())