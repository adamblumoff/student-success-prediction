#!/bin/bash
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
