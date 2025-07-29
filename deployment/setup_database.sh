#!/bin/bash

echo "🚀 Student Success Prediction - Database Setup"
echo "=============================================="

# Check if PostgreSQL is installed
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client found"
    
    # Try to connect to local PostgreSQL
    if pg_isready -h localhost -p 5432 -U postgres &> /dev/null; then
        echo "✅ PostgreSQL server is running locally"
        LOCAL_PG=true
    else
        echo "❌ PostgreSQL server not found locally"
        LOCAL_PG=false
    fi
else
    echo "❌ PostgreSQL client not found"
    LOCAL_PG=false
fi

if [ "$LOCAL_PG" = true ]; then
    echo ""
    echo "🔧 Setting up local PostgreSQL database..."
    
    # Create database
    createdb -h localhost -U postgres student_success 2>/dev/null || echo "Database may already exist"
    
    # Set environment variables
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_NAME=student_success
    export DB_USER=postgres
    export DB_PASSWORD=postgres
    
    echo "✅ Database environment configured"
    echo ""
    echo "Run these commands to set environment variables:"
    echo "export DB_HOST=localhost"
    echo "export DB_PORT=5432"  
    echo "export DB_NAME=student_success"
    echo "export DB_USER=postgres"
    echo "export DB_PASSWORD=postgres"
    echo ""
    
else
    echo ""
    echo "🌐 Local PostgreSQL not available. Options:"
    echo ""
    echo "1. 🐳 Install Docker and run:"
    echo "   docker compose up -d postgres"
    echo ""
    echo "2. 📦 Install PostgreSQL:"
    echo "   sudo apt update"
    echo "   sudo apt install postgresql postgresql-contrib"
    echo "   sudo systemctl start postgresql"
    echo ""
    echo "3. ☁️ Use cloud database:"
    echo "   - Supabase (free tier): https://supabase.com"
    echo "   - ElephantSQL (free tier): https://www.elephantsql.com"
    echo "   - Neon (free tier): https://neon.tech"
    echo ""
    echo "4. 🔄 Continue with SQLite (current setup works fine for demo)"
    echo ""
fi

echo "🧪 Testing database connection..."
python3 -c "
import sys
sys.path.append('src')
from mvp.database import check_database_health, db_config
print('Database URL:', db_config.database_url)
print('Health check:', '✅ PASSED' if check_database_health() else '❌ FAILED')
"

echo ""
echo "🏃 Ready to run migrations:"
echo "alembic upgrade head"
echo ""
echo "🚀 Start the server:"
echo "python3 run_mvp.py"