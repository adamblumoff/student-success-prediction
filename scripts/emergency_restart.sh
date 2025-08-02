#!/bin/bash
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
