#!/bin/bash

echo "🚀 PostgreSQL Deployment Script"
echo "==============================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL environment variable not set!"
    echo ""
    echo "Please set it with one of these formats:"
    echo "Supabase: export DATABASE_URL=\"postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres\""
    echo "Neon: export DATABASE_URL=\"postgresql://USER:PASSWORD@HOST.neon.tech/DATABASE?sslmode=require\""
    echo "ElephantSQL: export DATABASE_URL=\"postgresql://USER:PASSWORD@HOST.elephantsql.com/USER\""
    exit 1
fi

echo "✅ DATABASE_URL is set"
echo "🔍 Database host: $(echo $DATABASE_URL | sed 's/.*@\([^:]*\).*/\1/')"

# Test database connection
echo ""
echo "🧪 Testing database connection..."
python3 -c "
import sys
sys.path.append('src')
from mvp.database import check_database_health, db_config
print('Database URL:', db_config.database_url.split('@')[-1] if '@' in db_config.database_url else db_config.database_url)
health = check_database_health()
print('Connection test:', '✅ PASSED' if health else '❌ FAILED')
exit(0 if health else 1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed. Please check your DATABASE_URL."
    exit 1
fi

echo ""
echo "📋 Running Alembic migration..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Migration failed. Please check the error above."
    exit 1
fi

echo ""
echo "🧪 Testing migrated database..."
python3 -c "
import sys
sys.path.append('src')
from mvp.database import get_db_session
from mvp.models import Institution, Student, Prediction

try:
    with get_db_session() as session:
        # Test basic operations
        institution_count = session.query(Institution).count()
        student_count = session.query(Student).count()
        prediction_count = session.query(Prediction).count()
        
        print(f'📊 Database ready with tables:')
        print(f'   Institutions: {institution_count} records')
        print(f'   Students: {student_count} records')
        print(f'   Predictions: {prediction_count} records')
        print('✅ All tables accessible')
except Exception as e:
    print(f'❌ Database test failed: {e}')
    exit(1)
"

echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "==============================="
echo "Your PostgreSQL database is ready for production!"
echo ""
echo "Next steps:"
echo "1. Start the server: python3 run_mvp.py"
echo "2. Test with CSV upload at http://localhost:8001"
echo "3. Check explainable AI features"
echo ""
echo "The system will now use PostgreSQL for all operations."