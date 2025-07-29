# 🌐 Cloud PostgreSQL Setup Guide

## Option 1: Supabase (Recommended - Free Tier)

1. **Sign up**: Go to https://supabase.com and create account
2. **Create project**: Click "New Project"
3. **Get connection details**: Go to Settings > Database
4. **Set environment variables**:

```bash
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
```

## Option 2: Neon (Serverless PostgreSQL)

1. **Sign up**: Go to https://neon.tech
2. **Create database**: Click "Create a database"
3. **Copy connection string**: From dashboard
4. **Set environment variables**:

```bash
export DATABASE_URL="postgresql://[user]:[password]@[host]/[database]?sslmode=require"
```

## Option 3: ElephantSQL (Simple Setup)

1. **Sign up**: Go to https://www.elephantsql.com
2. **Create instance**: Choose "Tiny Turtle" (free)
3. **Get URL**: From instance details
4. **Set environment variables**:

```bash
export DATABASE_URL="postgresql://[user]:[password]@[host]/[database]"
```

## Quick Test Setup

For immediate testing, you can use this temporary database:

```bash
# WARNING: This is for testing only - do not use for production
export DATABASE_URL="postgresql://demo:demo123@localhost:5432/student_success_demo"
```

## After Setting Up Database

1. **Run migrations**:
```bash
alembic upgrade head
```

2. **Test connection**:
```bash
python3 -c "
import sys; sys.path.append('src')
from mvp.database import check_database_health
print('Health check:', '✅ PASSED' if check_database_health() else '❌ FAILED')
"
```

3. **Start server**:
```bash
python3 run_mvp.py
```

The system will automatically detect PostgreSQL and use the new schema!