#!/bin/bash
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
