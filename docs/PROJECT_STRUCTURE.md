# 📁 Project Structure

## Overview
This document describes the organized folder structure of the Student Success Prediction system after PostgreSQL migration.

## Root Directory Structure

```
student-success-prediction/
├── 📱 Application Core
│   ├── run_mvp.py                 # Main application entry point
│   ├── requirements.txt           # Python dependencies
│   └── .env.example              # Environment template
│
├── 🧠 Source Code
│   └── src/
│       ├── models/               # ML models and training
│       │   ├── train_models.py
│       │   ├── intervention_system.py
│       │   └── explainable_ai.py
│       └── mvp/                  # MVP application
│           ├── mvp_api.py        # FastAPI application
│           ├── simple_auth.py    # Authentication
│           ├── database.py       # Database layer (NEW)
│           ├── models.py         # SQLAlchemy ORM models (NEW)
│           ├── templates/        # HTML templates
│           └── static/           # CSS, JS, assets
│
├── 🗄️ Database & Migration
│   ├── alembic.ini              # Alembic configuration
│   └── alembic/                 # Database migrations
│       ├── env.py               # Migration environment
│       ├── script.py.mako       # Migration template
│       └── versions/            # Migration files
│
├── 🚀 Deployment
│   ├── docker-compose.yml       # PostgreSQL container
│   ├── deploy_postgres.sh       # Deployment automation
│   ├── setup_database.sh        # Database setup
│   └── sql/                     # SQL initialization scripts
│       └── init.sql
│
├── 📚 Documentation
│   ├── CLAUDE.md                # Development guide
│   ├── PROJECT_STRUCTURE.md     # This file
│   └── docs/
│       └── deployment/
│           └── setup_cloud_db.md
│
├── 📊 ML Assets
│   └── results/
│       ├── models/              # Trained model files (.pkl)
│       └── model_metadata.json  # Model performance metrics
│
└── 🔧 Configuration
    ├── .gitignore              # Git ignore rules
    ├── .env                    # Local environment (not committed)
    └── .env.example            # Environment template
```

## Key Folders Explained

### `/src/mvp/` - MVP Application
- **Purpose**: Core application code
- **Key Files**:
  - `mvp_api.py` - FastAPI web application with all endpoints
  - `database.py` - Database connection layer with PostgreSQL/SQLite support
  - `models.py` - SQLAlchemy ORM models for K-12 schema
  - `simple_auth.py` - API key authentication

### `/alembic/` - Database Migration System
- **Purpose**: Version control for database schema
- **Key Files**:
  - `env.py` - Migration environment setup
  - `versions/` - Auto-generated migration files
- **Commands**:
  - `alembic upgrade head` - Apply all migrations
  - `alembic revision --autogenerate -m "message"` - Create new migration

### `/deployment/` - Deployment Tools
- **Purpose**: Production deployment automation
- **Key Files**:
  - `docker-compose.yml` - PostgreSQL container setup
  - `deploy_postgres.sh` - Full deployment automation
  - `setup_database.sh` - Database configuration helper

### `/docs/` - Documentation
- **Purpose**: Project documentation and guides
- **Structure**:
  - `deployment/` - Deployment-specific guides
  - Future: `api/`, `user-guides/`, etc.

## File Organization Principles

### ✅ **What's Included**
- Production-ready application code
- Database schema and migrations  
- Deployment automation scripts
- Comprehensive documentation
- Configuration templates

### ❌ **What's Excluded** (.gitignore)
- Database files (*.db, *.sqlite3)
- Environment variables (.env)
- Python cache (__pycache__)
- Large model files (*.pkl over limit)
- Temporary files
- IDE configurations
- Log files

## Development Workflow

### **Daily Development**
1. Work in `/src/mvp/` for application changes
2. Use `/alembic/` for database schema changes
3. Update `/docs/` for documentation
4. Test with `/deployment/` scripts

### **Database Changes**
1. Modify models in `src/mvp/models.py`
2. Generate migration: `alembic revision --autogenerate`
3. Apply migration: `alembic upgrade head`
4. Test with both PostgreSQL and SQLite

### **Deployment**
1. Use `/deployment/deploy_postgres.sh` for full setup
2. Configure with `/deployment/docker-compose.yml` for containers
3. Reference `/docs/deployment/` for cloud setup

This structure supports both development simplicity and production scalability while maintaining clear separation of concerns.