#!/bin/bash
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
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
find logs/ -name "*.gz" -mtime +30 -delete

# Clean temporary files
echo "Cleaning temporary files..."
find . -name "test_*.db" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Weekly maintenance completed"
