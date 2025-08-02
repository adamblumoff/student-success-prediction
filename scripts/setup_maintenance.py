#!/usr/bin/env python3
"""
Setup script for system maintenance tools.

This script sets up automated maintenance, monitoring, and testing infrastructure.
"""

import os
import stat
import json
import shutil
from pathlib import Path
from typing import Dict, Any

def setup_logging_directories():
    """Create necessary logging directories."""
    directories = [
        'logs',
        'logs/health_reports', 
        'test_reports',
        'backups'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def make_scripts_executable():
    """Make all maintenance scripts executable."""
    script_files = [
        'scripts/system_health_monitor.py',
        'scripts/run_automated_tests.py',
        'scripts/setup_maintenance.py',
        'scripts/security_test.py'
    ]
    
    for script_file in script_files:
        script_path = Path(script_file)
        if script_path.exists():
            # Make executable
            current_permissions = script_path.stat().st_mode
            script_path.chmod(current_permissions | stat.S_IEXEC)
            print(f"✅ Made executable: {script_file}")
        else:
            print(f"⚠️  Script not found: {script_file}")

def create_health_monitor_config():
    """Create default health monitor configuration."""
    config = {
        "base_url": "http://localhost:8001",
        "api_key": None,
        "checks": {
            "api_endpoints": True,
            "database": True,
            "models": True,
            "notifications": True,
            "integrations": True,
            "file_system": True
        },
        "thresholds": {
            "response_time_ms": 5000,
            "memory_usage_mb": 1000,
            "disk_usage_percent": 85
        },
        "email_alerts": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": None,
            "password": None,
            "recipients": []
        },
        "log_level": "INFO",
        "log_file": "logs/health_monitor.log"
    }
    
    config_file = Path('config/health_monitor.json')
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created health monitor config: {config_file}")

def create_test_runner_config():
    """Create default test runner configuration."""
    config = {
        "test_suites": {
            "unit_tests": {
                "enabled": True,
                "command": "python -m pytest tests/unit/ -v --tb=short",
                "timeout": 300
            },
            "api_tests": {
                "enabled": True,
                "command": "python -m pytest tests/unit/test_api_endpoints.py -v",
                "timeout": 300
            },
            "notification_tests": {
                "enabled": True,
                "command": "python -m pytest tests/unit/test_notifications.py -v",
                "timeout": 300
            },
            "integration_tests": {
                "enabled": True,
                "command": "python -m pytest tests/unit/test_integrations.py -v",
                "timeout": 300
            }
        },
        "coverage": {
            "enabled": True,
            "min_coverage": 70,
            "exclude_patterns": ["*/venv/*", "*/tests/*", "*/__pycache__/*"]
        },
        "performance": {
            "enabled": True,
            "benchmarks": ["model_prediction", "api_response", "database_query"]
        },
        "reporting": {
            "formats": ["console", "json", "html"],
            "output_dir": "test_reports"
        },
        "notifications": {
            "on_failure": True,
            "on_success": False,
            "email_enabled": False
        }
    }
    
    config_file = Path('config/test_runner.json')
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created test runner config: {config_file}")

def create_maintenance_scripts():
    """Create convenience maintenance scripts."""
    
    # Daily maintenance script
    daily_script = """#!/bin/bash
# Daily Maintenance Script
echo "🔍 Running daily maintenance checks..."

# Health check
python3 scripts/system_health_monitor.py --output console

# Quick API test
curl -s http://localhost:8001/health > /dev/null && echo "✅ API responding" || echo "❌ API not responding"

# Disk space check
df -h | grep -E '(Filesystem|/dev/)' | awk '$5 > 85 {print "⚠️  High disk usage: " $5 " on " $1}'

# Log summary
echo "📋 Recent errors in logs:"
grep -i error logs/*.log 2>/dev/null | tail -5 || echo "No recent errors"

echo "✅ Daily maintenance completed"
"""
    
    script_file = Path('scripts/daily_maintenance.sh')
    with open(script_file, 'w') as f:
        f.write(daily_script)
    script_file.chmod(script_file.stat().st_mode | stat.S_IEXEC)
    print(f"✅ Created: {script_file}")
    
    # Weekly maintenance script
    weekly_script = """#!/bin/bash
# Weekly Maintenance Script
echo "🔧 Running weekly maintenance..."

# Full test suite
echo "Running full test suite..."
python3 scripts/run_automated_tests.py --output both

# Health monitoring with email
echo "Running comprehensive health check..."
python3 scripts/system_health_monitor.py --output both

# Database maintenance (if PostgreSQL)
if [ ! -z "$DATABASE_URL" ] && [[ $DATABASE_URL == postgresql* ]]; then
    echo "Running database maintenance..."
    python3 -c "
import asyncpg
import asyncio
import os

async def maintenance():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.execute('ANALYZE;')
        print('✅ Database maintenance completed')
        await conn.close()
    except Exception as e:
        print(f'❌ Database maintenance failed: {e}')

asyncio.run(maintenance())
"
fi

# Log rotation
echo "Rotating logs..."
find logs/ -name "*.log" -mtime +7 -exec gzip {} \\;
find logs/ -name "*.gz" -mtime +30 -delete

# Clean temporary files
echo "Cleaning temporary files..."
find . -name "test_*.db" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Weekly maintenance completed"
"""
    
    script_file = Path('scripts/weekly_maintenance.sh')
    with open(script_file, 'w') as f:
        f.write(weekly_script)
    script_file.chmod(script_file.stat().st_mode | stat.S_IEXEC)
    print(f"✅ Created: {script_file}")

def create_emergency_scripts():
    """Create emergency response scripts."""
    
    # Emergency restart script
    restart_script = """#!/bin/bash
# Emergency System Restart Script
echo "🚨 Emergency restart initiated..."

# Stop all Python processes related to the system
pkill -f "python3 run_mvp.py" || echo "No running MVP processes found"
pkill -f "system_health_monitor.py" || echo "No running monitor processes found"

# Wait for processes to stop
sleep 5

# Check database connection
echo "Checking database connection..."
python3 -c "
import os
import sys

try:
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        import asyncpg
        import asyncio
        
        async def test():
            conn = await asyncpg.connect(database_url)
            await conn.fetchval('SELECT 1')
            await conn.close()
            print('✅ Database connection OK')
        
        asyncio.run(test())
    else:
        import sqlite3
        conn = sqlite3.connect('mvp_data.db')
        conn.execute('SELECT 1')
        conn.close()
        print('✅ SQLite connection OK')
        
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "Starting system..."
    nohup python3 run_mvp.py > logs/system.log 2>&1 &
    
    # Wait for system to start
    sleep 10
    
    # Test system health
    if curl -s http://localhost:8001/health > /dev/null; then
        echo "✅ System restarted successfully"
    else
        echo "❌ System failed to start properly"
        exit 1
    fi
else
    echo "❌ Cannot restart - database connection failed"
    exit 1
fi
"""
    
    script_file = Path('scripts/emergency_restart.sh')
    with open(script_file, 'w') as f:
        f.write(restart_script)
    script_file.chmod(script_file.stat().st_mode | stat.S_IEXEC)
    print(f"✅ Created: {script_file}")
    
    # System status script
    status_script = """#!/bin/bash
# Quick System Status Check
echo "📊 System Status Report"
echo "======================"

# API Status
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ API: Running"
else
    echo "❌ API: Not responding"
fi

# Process Status
if pgrep -f "python3 run_mvp.py" > /dev/null; then
    echo "✅ MVP Process: Running"
else
    echo "❌ MVP Process: Not running"
fi

# Database Status
python3 -c "
import os
try:
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgresql'):
        import asyncpg
        import asyncio
        
        async def test():
            conn = await asyncpg.connect(database_url)
            await conn.close()
            print('✅ Database: Connected')
        
        asyncio.run(test())
    else:
        import sqlite3
        conn = sqlite3.connect('mvp_data.db')
        conn.close()
        print('✅ Database: Connected (SQLite)')
        
except Exception as e:
    print(f'❌ Database: Connection failed')
"

# Disk Space
echo "💾 Disk Usage:"
df -h | grep -E '(Filesystem|/$)' | awk 'NR==1 || $5+0 >= 80'

# Memory Usage
echo "🧠 Memory Usage:"
free -h | grep -E '(Mem|Swap)'

# Recent Errors
echo "🚨 Recent Errors (last 5):"
grep -i error logs/*.log 2>/dev/null | tail -5 || echo "No recent errors found"

echo "======================"
"""
    
    script_file = Path('scripts/system_status.sh')
    with open(script_file, 'w') as f:
        f.write(status_script)
    script_file.chmod(script_file.stat().st_mode | stat.S_IEXEC)
    print(f"✅ Created: {script_file}")

def create_cron_examples():
    """Create example cron entries."""
    cron_content = """# Student Success Prediction System - Maintenance Cron Jobs
# Add these entries to your crontab with: crontab -e

# Health check every 15 minutes
*/15 * * * * cd /path/to/student-success-prediction && python3 scripts/system_health_monitor.py --output file >> logs/cron.log 2>&1

# Daily maintenance at 6 AM
0 6 * * * cd /path/to/student-success-prediction && ./scripts/daily_maintenance.sh >> logs/cron.log 2>&1

# Weekly maintenance on Sundays at 2 AM
0 2 * * 0 cd /path/to/student-success-prediction && ./scripts/weekly_maintenance.sh >> logs/cron.log 2>&1

# Monthly full backup on 1st of month at 1 AM
0 1 1 * * cd /path/to/student-success-prediction && python3 scripts/backup_system.py --full >> logs/cron.log 2>&1

# Log rotation daily at midnight
0 0 * * * cd /path/to/student-success-prediction && find logs/ -name "*.log" -size +100M -exec gzip {} \\;

# Clean old test databases daily
0 3 * * * cd /path/to/student-success-prediction && find . -name "test_*.db" -mtime +1 -delete

# Update system dependencies weekly (Sunday at 3 AM)
0 3 * * 0 cd /path/to/student-success-prediction && pip install --upgrade -r requirements.txt >> logs/cron.log 2>&1

# NOTE: Replace /path/to/student-success-prediction with your actual path
# To install these cron jobs:
# 1. Copy this file content
# 2. Run: crontab -e
# 3. Paste the content
# 4. Save and exit
"""
    
    cron_file = Path('config/cron_examples.txt')
    with open(cron_file, 'w') as f:
        f.write(cron_content)
    
    print(f"✅ Created cron examples: {cron_file}")

def create_systemd_service():
    """Create systemd service example."""
    service_content = """[Unit]
Description=Student Success Prediction System
After=network.target postgresql.service
Requires=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/student-success-prediction
Environment=PATH=/path/to/student-success-prediction/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/path/to/student-success-prediction
ExecStart=/path/to/student-success-prediction/venv/bin/python run_mvp.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=student-success

[Install]
WantedBy=multi-user.target

# To install this service:
# 1. Copy this file to /etc/systemd/system/student-success.service
# 2. Update paths and user as needed
# 3. Run: sudo systemctl daemon-reload
# 4. Run: sudo systemctl enable student-success
# 5. Run: sudo systemctl start student-success
"""
    
    service_file = Path('config/student-success.service')
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Created systemd service example: {service_file}")

def update_claude_md():
    """Update CLAUDE.md with maintenance information."""
    claude_md_path = Path('CLAUDE.md')
    
    if not claude_md_path.exists():
        print("⚠️  CLAUDE.md not found, skipping update")
        return
    
    maintenance_section = """
## System Maintenance and Reliability

### Automated Testing and Health Monitoring

The system includes comprehensive testing and monitoring infrastructure to ensure reliability:

**Health Monitoring:**
```bash
# Run system health check
python3 scripts/system_health_monitor.py

# Continuous monitoring (every 15 minutes)
python3 scripts/system_health_monitor.py --continuous 15

# Email alerts on issues
python3 scripts/system_health_monitor.py --email
```

**Automated Testing:**
```bash
# Run full test suite
python3 scripts/run_automated_tests.py

# Run specific test categories
python3 scripts/run_automated_tests.py --suites unit_tests api_tests notification_tests

# Performance benchmarking
python3 scripts/run_automated_tests.py --performance-only
```

**Maintenance Scripts:**
```bash
# Daily maintenance
./scripts/daily_maintenance.sh

# Weekly maintenance
./scripts/weekly_maintenance.sh

# Emergency restart
./scripts/emergency_restart.sh

# System status check
./scripts/system_status.sh
```

### Test Coverage

The system includes comprehensive tests:
- **Unit Tests**: Individual component testing
- **API Tests**: All endpoint testing with authentication
- **Notification Tests**: Real-time notification system testing
- **Integration Tests**: LMS/SIS integration testing
- **Performance Tests**: Response time and throughput testing

### Monitoring and Alerting

**Health Checks Monitor:**
- API endpoint responsiveness
- Database connectivity
- Model loading and performance
- Notification system functionality
- Integration system health
- File system and resource usage

**Alerting Thresholds:**
- Response time > 5 seconds (warning)
- Disk usage > 85% (warning)
- Memory usage > 80% (warning)
- API errors > 50% (critical)
- Database connection failures (critical)

### Maintenance Schedule

**Daily (Automated):**
- Health monitoring every 15 minutes
- Error log analysis
- Basic connectivity checks

**Weekly (Automated):**
- Full test suite execution
- Database maintenance and optimization
- Log rotation and cleanup
- Dependency updates

**Monthly (Manual Review):**
- Model performance evaluation
- Security audit
- Full system backup
- Documentation updates

### Configuration Files

**Health Monitor**: `config/health_monitor.json`
**Test Runner**: `config/test_runner.json`
**Cron Jobs**: `config/cron_examples.txt`
**Systemd Service**: `config/student-success.service`

See `docs/SYSTEM_MAINTENANCE.md` for comprehensive maintenance procedures.
"""
    
    # Read current CLAUDE.md
    with open(claude_md_path, 'r') as f:
        content = f.read()
    
    # Check if maintenance section already exists
    if "System Maintenance and Reliability" in content:
        print("✅ CLAUDE.md already contains maintenance section")
        return
    
    # Add maintenance section before the last line
    lines = content.split('\n')
    insert_index = len(lines) - 1
    
    # Find a good place to insert (before any existing final sections)
    for i, line in enumerate(lines):
        if line.startswith('## Development Guidelines for Claude Code'):
            insert_index = i
            break
    
    lines.insert(insert_index, maintenance_section)
    
    # Write updated content
    with open(claude_md_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ Updated CLAUDE.md with maintenance information")

def main():
    """Main setup function."""
    print("🔧 Setting up system maintenance infrastructure...")
    print("=" * 50)
    
    # Create directories
    setup_logging_directories()
    
    # Make scripts executable
    make_scripts_executable()
    
    # Create configuration files
    create_health_monitor_config()
    create_test_runner_config()
    
    # Create maintenance scripts
    create_maintenance_scripts()
    create_emergency_scripts()
    
    # Create examples and documentation
    create_cron_examples()
    create_systemd_service()
    
    # Update documentation
    update_claude_md()
    
    print("\n" + "=" * 50)
    print("✅ Maintenance setup completed!")
    print("\nNext steps:")
    print("1. Review configuration files in config/")
    print("2. Set up automated monitoring:")
    print("   - Add cron jobs from config/cron_examples.txt")
    print("   - Or install systemd service from config/student-success.service")
    print("3. Configure email alerts in config/health_monitor.json")
    print("4. Test the setup:")
    print("   python3 scripts/system_health_monitor.py")
    print("   python3 scripts/run_automated_tests.py")
    print("5. Review docs/SYSTEM_MAINTENANCE.md for detailed procedures")

if __name__ == '__main__':
    main()