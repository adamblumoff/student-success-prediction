# System Maintenance Guide

This guide provides comprehensive procedures for maintaining the Student Success Prediction System to ensure optimal performance, reliability, and security.

## Table of Contents

1. [Daily Maintenance](#daily-maintenance)
2. [Weekly Maintenance](#weekly-maintenance)
3. [Monthly Maintenance](#monthly-maintenance)
4. [Health Monitoring](#health-monitoring)
5. [Automated Testing](#automated-testing)
6. [Database Maintenance](#database-maintenance)
7. [Model Management](#model-management)
8. [Security Updates](#security-updates)
9. [Performance Optimization](#performance-optimization)
10. [Backup Procedures](#backup-procedures)
11. [Troubleshooting](#troubleshooting)
12. [Emergency Procedures](#emergency-procedures)

## Daily Maintenance

### Automated Checks (5 minutes)

```bash
# Run system health check
python3 scripts/system_health_monitor.py --output console

# Check service status
systemctl status student-success-api  # If using systemd

# Check disk usage
df -h

# Check memory usage
free -h

# Review recent logs
tail -n 50 logs/health_monitor.log
tail -n 50 logs/automated_tests.log
```

### Manual Verification (10 minutes)

1. **Web Interface Check**
   - Access http://localhost:8001
   - Test file upload with sample data
   - Verify predictions are generated
   - Check explainable AI features

2. **API Health Check**
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8001/api/notifications/health
   ```

3. **Database Connection**
   ```bash
   # PostgreSQL
   python3 -c "
   import asyncpg
   import asyncio
   import os
   async def test():
       conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
       result = await conn.fetchval('SELECT 1')
       print('Database OK' if result == 1 else 'Database Error')
       await conn.close()
   asyncio.run(test())"
   ```

### Log Review Checklist

- [ ] No critical errors in application logs
- [ ] No failed health checks
- [ ] No notification system errors
- [ ] No database connection issues
- [ ] No integration failures

## Weekly Maintenance

### Comprehensive System Check (30 minutes)

```bash
# Run full test suite
python3 scripts/run_automated_tests.py

# Comprehensive health monitoring
python3 scripts/system_health_monitor.py --output both --email

# Check system resources
htop  # or top
iostat -x 1 5  # I/O statistics
```

### Database Maintenance

```bash
# PostgreSQL maintenance
python3 -c "
import asyncpg
import asyncio
import os

async def maintenance():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    # Analyze tables for performance
    await conn.execute('ANALYZE;')
    
    # Check table sizes
    result = await conn.fetch('''
        SELECT schemaname, tablename, 
               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    ''')
    
    print('Table sizes:')
    for row in result:
        print(f'  {row[\"tablename\"]}: {row[\"size\"]}')
    
    await conn.close()

asyncio.run(maintenance())
"
```

### Log Rotation

```bash
# Compress old logs
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;

# Remove logs older than 30 days
find logs/ -name "*.gz" -mtime +30 -delete

# Clean up test databases
find . -name "test_*.db" -delete
```

### Update Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update requirements (review changes first)
pip install --upgrade -r requirements.txt

# Test after updates
python3 scripts/run_automated_tests.py
```

## Monthly Maintenance

### Full System Audit (2 hours)

```bash
# Comprehensive security scan
python3 scripts/security_test.py

# Performance baseline
python3 scripts/run_automated_tests.py --performance-only

# Full backup
python3 scripts/backup_system.py --full
```

### Model Retraining Check

```bash
# Check model performance
python3 -c "
import json
from pathlib import Path

metadata_file = Path('results/models/model_metadata.json')
if metadata_file.exists():
    with open(metadata_file) as f:
        metadata = json.load(f)
    print(f'Model accuracy: {metadata.get(\"binary_accuracy\", \"N/A\")}')
    print(f'Last trained: {metadata.get(\"training_date\", \"N/A\")}')
else:
    print('Model metadata not found')
"

# Retrain if performance degraded (manual decision)
# python3 src/models/train_k12_models.py
```

### Database Optimization

```bash
# PostgreSQL optimization
python3 -c "
import asyncpg
import asyncio
import os

async def optimize():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    # Vacuum and analyze
    await conn.execute('VACUUM ANALYZE;')
    
    # Reindex if needed
    await conn.execute('REINDEX DATABASE student_success;')
    
    # Update statistics
    await conn.execute('ANALYZE;')
    
    print('Database optimization completed')
    await conn.close()

asyncio.run(optimize())
"
```

## Health Monitoring

### Automated Monitoring Setup

1. **Cron Job Setup** (recommended for production):

```bash
# Edit crontab
crontab -e

# Add these entries:
# Health check every 15 minutes
*/15 * * * * /path/to/python3 /path/to/scripts/system_health_monitor.py --output file

# Daily comprehensive check
0 6 * * * /path/to/python3 /path/to/scripts/system_health_monitor.py --output both --email

# Weekly test suite
0 2 * * 0 /path/to/python3 /path/to/scripts/run_automated_tests.py --output file
```

2. **Systemd Service** (alternative):

```ini
# /etc/systemd/system/student-success-monitor.service
[Unit]
Description=Student Success Health Monitor
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/student-success-prediction
ExecStart=/path/to/python3 scripts/system_health_monitor.py --continuous 15
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

### Monitoring Metrics

**Key Performance Indicators:**
- API response time < 500ms
- Model prediction time < 100ms
- Database query time < 50ms
- Memory usage < 80%
- Disk usage < 85%
- CPU usage < 70% (average)

**Alerting Thresholds:**
- Critical: System unavailable, database down, API errors > 50%
- Warning: Slow response times, high resource usage, prediction errors
- Info: Successful deployments, daily summaries

## Automated Testing

### Test Categories

1. **Unit Tests** - Test individual components
   ```bash
   python3 -m pytest tests/unit/ -v
   ```

2. **Integration Tests** - Test component interactions
   ```bash
   python3 -m pytest tests/integration/ -v
   ```

3. **API Tests** - Test all API endpoints
   ```bash
   python3 -m pytest tests/unit/test_api_endpoints.py -v
   ```

4. **Notification Tests** - Test real-time notification system
   ```bash
   python3 -m pytest tests/unit/test_notifications.py -v
   ```

5. **Integration System Tests** - Test LMS/SIS integrations
   ```bash
   python3 -m pytest tests/unit/test_integrations.py -v
   ```

### Test Automation

```bash
# Run all tests with coverage
python3 scripts/run_automated_tests.py --coverage-only

# Run specific test suites
python3 scripts/run_automated_tests.py --suites unit_tests api_tests

# Performance benchmarking
python3 scripts/run_automated_tests.py --performance-only
```

### Continuous Integration

For CI/CD pipeline integration:

```yaml
# .github/workflows/test.yml (GitHub Actions example)
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python3 scripts/run_automated_tests.py
```

## Database Maintenance

### PostgreSQL Maintenance

```sql
-- Weekly maintenance queries
VACUUM ANALYZE;
REINDEX DATABASE student_success;

-- Check database size
SELECT pg_size_pretty(pg_database_size('student_success'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check for unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

### SQLite Maintenance

```bash
# Optimize SQLite database
python3 -c "
import sqlite3
conn = sqlite3.connect('mvp_data.db')
conn.execute('VACUUM;')
conn.execute('ANALYZE;')
conn.close()
print('SQLite optimization completed')
"
```

### Backup Procedures

```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# SQLite backup
cp mvp_data.db backup_$(date +%Y%m%d_%H%M%S).db
```

## Model Management

### Model Monitoring

```bash
# Check model files
ls -la results/models/

# Verify model metadata
python3 -c "
import json
from pathlib import Path

metadata_file = Path('results/models/model_metadata.json')
if metadata_file.exists():
    with open(metadata_file) as f:
        metadata = json.load(f)
    
    print('Model Information:')
    print(f'  Binary Accuracy: {metadata.get(\"binary_accuracy\", \"N/A\")}')
    print(f'  Multi-class F1: {metadata.get(\"multi_f1_score\", \"N/A\")}')
    print(f'  Training Date: {metadata.get(\"training_date\", \"N/A\")}')
    print(f'  Feature Count: {metadata.get(\"feature_count\", \"N/A\")}')
else:
    print('Model metadata not found - models may need retraining')
"
```

### Model Retraining

```bash
# Retrain original models
python3 src/models/train_models.py

# Retrain K-12 models
python3 src/models/train_k12_models.py

# Train ultra-advanced K-12 model
python3 src/models/k12_ultra_advanced_model.py

# Test models after retraining
python3 src/models/k12_ultra_predictor.py
```

### Model Versioning

```bash
# Create model backup before retraining
mkdir -p results/models/backup_$(date +%Y%m%d)
cp results/models/*.pkl results/models/backup_$(date +%Y%m%d)/
cp results/models/*.json results/models/backup_$(date +%Y%m%d)/
```

## Security Updates

### Regular Security Checks

```bash
# Check for security vulnerabilities in dependencies
pip audit

# Update security-critical packages
pip install --upgrade cryptography requests urllib3

# Check for known vulnerabilities
python3 scripts/security_test.py
```

### Security Hardening

```bash
# Check file permissions
find . -type f -name "*.py" -not -path "./venv/*" -exec chmod 644 {} \;
find . -type f -name "*.sh" -exec chmod 755 {} \;

# Check for sensitive data in logs
grep -r "password\|token\|key\|secret" logs/ || echo "No sensitive data found in logs"

# Verify SSL/TLS configuration (if using HTTPS)
openssl s_client -connect localhost:8001 -servername localhost < /dev/null
```

## Performance Optimization

### Performance Monitoring

```bash
# Monitor API response times
python3 -c "
import time
import requests

start = time.time()
response = requests.get('http://localhost:8001/health')
duration = time.time() - start

print(f'API Response Time: {duration:.3f}s')
print(f'Status Code: {response.status_code}')
"

# Monitor model prediction time
python3 -c "
import time
import pandas as pd
from src.models.intervention_system import InterventionRecommendationSystem

# Load system
system = InterventionRecommendationSystem()

# Create sample data
sample_data = pd.DataFrame({
    'id_student': [1, 2, 3],
    'early_avg_score': [85, 70, 92],
    'early_total_clicks': [150, 80, 200],
    'studied_credits': [60, 45, 75]
})

start = time.time()
predictions = system.assess_student_risk(sample_data)
duration = time.time() - start

print(f'Model Prediction Time: {duration:.3f}s for {len(sample_data)} students')
print(f'Average per student: {duration/len(sample_data):.3f}s')
"
```

### Optimization Techniques

1. **Database Query Optimization**
   - Add indexes for frequently queried columns
   - Use connection pooling
   - Optimize slow queries

2. **Model Performance**
   - Use model caching
   - Batch predictions when possible
   - Consider model quantization for deployment

3. **API Optimization**
   - Enable response compression
   - Use caching for static data
   - Implement rate limiting

## Troubleshooting

### Common Issues

1. **API Not Responding**
   ```bash
   # Check if service is running
   ps aux | grep python3
   
   # Check port availability
   netstat -tlnp | grep :8001
   
   # Restart service
   pkill -f "python3 run_mvp.py"
   python3 run_mvp.py &
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   python3 -c "
   import os
   print('DATABASE_URL:', os.getenv('DATABASE_URL', 'Not set'))
   
   # Test connection
   try:
       if os.getenv('DATABASE_URL', '').startswith('postgresql'):
           import asyncpg
           import asyncio
           async def test():
               conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
               await conn.close()
               print('PostgreSQL connection: OK')
           asyncio.run(test())
       else:
           import sqlite3
           conn = sqlite3.connect('mvp_data.db')
           conn.close()
           print('SQLite connection: OK')
   except Exception as e:
       print(f'Database connection failed: {e}')
   "
   ```

3. **Model Loading Errors**
   ```bash
   # Check model files
   ls -la results/models/
   
   # Test model loading
   python3 -c "
   try:
       from src.models.intervention_system import InterventionRecommendationSystem
       system = InterventionRecommendationSystem()
       print('Models loaded successfully')
   except Exception as e:
       print(f'Model loading failed: {e}')
   "
   ```

4. **High Memory Usage**
   ```bash
   # Check memory usage by process
   ps aux --sort=-%mem | head -10
   
   # Monitor memory over time
   free -m -s 5
   
   # Clear cache if needed
   sync && echo 3 > /proc/sys/vm/drop_caches
   ```

### Log Analysis

```bash
# Find errors in logs
grep -i error logs/*.log | tail -20

# Find warnings
grep -i warning logs/*.log | tail -20

# Monitor logs in real-time
tail -f logs/health_monitor.log

# Analyze API access patterns
grep "GET\|POST" logs/*.log | cut -d' ' -f7 | sort | uniq -c | sort -nr
```

## Emergency Procedures

### System Down

1. **Immediate Response** (< 5 minutes)
   ```bash
   # Check system status
   python3 scripts/system_health_monitor.py
   
   # Restart application
   pkill -f "python3 run_mvp.py"
   python3 run_mvp.py &
   
   # Check logs for errors
   tail -50 logs/*.log
   ```

2. **Service Recovery** (< 15 minutes)
   ```bash
   # Restore from backup if needed
   # pg_restore -d $DATABASE_URL backup_latest.sql
   
   # Verify all services
   curl http://localhost:8001/health
   
   # Run quick tests
   python3 scripts/run_automated_tests.py --suites api_tests
   ```

### Data Corruption

1. **Assess Damage**
   ```bash
   # Check database integrity
   python3 -c "
   import asyncpg
   import asyncio
   import os
   
   async def check():
       conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
       tables = await conn.fetch('SELECT tablename FROM pg_tables WHERE schemaname = $1', 'public')
       for table in tables:
           count = await conn.fetchval(f'SELECT COUNT(*) FROM {table[\"tablename\"]}')
           print(f'{table[\"tablename\"]}: {count} rows')
       await conn.close()
   
   asyncio.run(check())
   "
   ```

2. **Restore from Backup**
   ```bash
   # Stop application
   pkill -f "python3 run_mvp.py"
   
   # Restore database
   dropdb student_success
   createdb student_success
   pg_restore -d student_success backup_latest.sql
   
   # Restart application
   python3 run_mvp.py &
   ```

### Security Incident

1. **Immediate Isolation**
   ```bash
   # Stop all services
   pkill -f "python3 run_mvp.py"
   
   # Check for unauthorized access
   grep -i "unauthorized\|failed\|403\|401" logs/*.log
   
   # Change API keys
   export MVP_API_KEY="new-secure-key-$(date +%s)"
   ```

2. **Investigation**
   ```bash
   # Analyze access logs
   grep -E "POST|PUT|DELETE" logs/*.log | grep -v "200 OK"
   
   # Check system integrity
   python3 scripts/security_test.py
   
   # Document incident
   echo "$(date): Security incident detected" >> logs/security_incidents.log
   ```

## Maintenance Checklist

### Daily (5 minutes)
- [ ] Run health check
- [ ] Review error logs
- [ ] Verify API accessibility
- [ ] Check disk space

### Weekly (30 minutes)
- [ ] Run full test suite
- [ ] Database maintenance
- [ ] Log rotation
- [ ] Update dependencies
- [ ] Performance check

### Monthly (2 hours)
- [ ] Security audit
- [ ] Model performance review
- [ ] Database optimization
- [ ] Full system backup
- [ ] Update documentation

### Quarterly (4 hours)
- [ ] Model retraining evaluation
- [ ] Security vulnerability assessment
- [ ] Performance baseline update
- [ ] Disaster recovery test
- [ ] Documentation review

---

## Contact Information

**System Administrator**: [Your Name]
**Email**: [admin@example.com]
**Phone**: [Emergency contact]
**Documentation Last Updated**: [Date]