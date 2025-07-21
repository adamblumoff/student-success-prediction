# PostgreSQL Database Integration

## Overview

The Student Success Prediction system has been enhanced with PostgreSQL database integration to provide production-ready data persistence, replacing the previous CSV-based storage approach.

## Database Architecture

### Schema Design
- **students**: Core student demographic and enrollment data
- **student_engagement**: VLE engagement metrics 
- **student_assessments**: Assessment performance metrics
- **risk_predictions**: ML model predictions with timestamps
- **interventions**: Recommended and applied interventions
- **student_outcomes**: Final results and success tracking

### Key Features
- Normalized database design with proper relationships
- Automatic timestamp tracking
- Built-in data validation constraints
- Performance indexes for common queries
- SQLite fallback for development/testing

## Installation Requirements

### System Packages
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y postgresql postgresql-contrib python3-venv

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
```

### Python Dependencies
```bash
pip install sqlalchemy psycopg2-binary alembic fastapi uvicorn
```

### Environment Variables
```bash
# PostgreSQL Configuration
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=student_success_db

# Or use a complete DATABASE_URL
export DATABASE_URL=postgresql://user:password@host:port/database
```

## Database Setup

### 1. Create Database
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE student_success_db;
CREATE USER student_success_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE student_success_db TO student_success_user;
\q
```

### 2. Initialize Schema
```bash
# Run the schema creation script
psql -U student_success_user -d student_success_db -f database/schema.sql
```

### 3. Migrate Existing Data
```bash
# Load CSV data into database
python database/migrate_csv_to_db.py
```

## API Integration

### Database-First Approach
The FastAPI has been enhanced with:

1. **Automatic Database Detection**: Tries PostgreSQL first, falls back to SQLite
2. **Session Management**: Proper connection pooling and cleanup
3. **Persistent Predictions**: All predictions are saved to database
4. **New Database Endpoints**:
   - `GET /students/{student_id}/predictions` - Get prediction history
   - `GET /analytics/risk-distribution` - Risk analytics
   - `POST /students/create` - Create student records

### Example Usage

#### Create Student and Get Prediction
```python
# Create student record
student_data = {
    "id_student": 12345,
    "code_module": "AAA",
    "code_presentation": "2024J",
    # ... other features
}

# API will automatically:
# 1. Create student record if not exists
# 2. Run ML prediction
# 3. Save prediction to database
# 4. Return prediction result
```

#### Query Prediction History
```python
# Get all predictions for a student
GET /students/12345/predictions

# Response includes:
# - Historical predictions
# - Risk score trends
# - Intervention recommendations
```

## Database Models

### Student Features for ML
The `student_features` view combines all related tables to provide the complete feature set required by the ML model:

```sql
SELECT * FROM student_features WHERE id_student = 12345;
```

### Prediction Tracking
```python
# Each prediction is automatically logged with:
- risk_score: 0.0-1.0
- risk_category: Low/Medium/High Risk  
- model_version: gradient_boosting_v1.0
- confidence_score: Model confidence
- timestamp: Prediction time
```

### Intervention Management
```python
# Interventions are linked to predictions:
- intervention_type: Academic Support, Counseling, etc.
- priority_level: Low/Medium/High/Critical
- status: Recommended/In Progress/Completed
- effectiveness_score: Outcome tracking
```

## Performance Optimizations

### Indexes
- Student ID lookups: `idx_students_id_student`
- Module/presentation queries: `idx_students_module_presentation`
- Risk predictions by date: `idx_risk_predictions_student_date`
- Risk category analytics: `idx_risk_predictions_category`

### Connection Pool
- Pre-ping verification
- Connection recycling (5 minutes)
- Automatic retry on connection loss

## Testing and Validation

### Database Integration Test
```bash
python test_db_integration.py
```

### API Testing with Database
```bash
# Start API (with database integration)
python src/api/student_success_api.py

# Test predictions (will be saved to database)
python test_api.py
```

## Migration Path

### From CSV to Database
1. **Keep existing CSV files** as backup
2. **Run migration script** to populate database
3. **Update API configuration** to use database
4. **Validate data integrity** with test predictions
5. **Switch production traffic** to database-backed API

### Rollback Strategy
- SQLite fallback maintains compatibility
- CSV export functions available for data recovery
- Database dump and restore procedures documented

## Production Deployment

### Docker Configuration
```dockerfile
# Database container
docker run --name postgres-db \
  -e POSTGRES_DB=student_success_db \
  -e POSTGRES_USER=api_user \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13

# API container with database connection
docker run --name student-success-api \
  -e DATABASE_URL=postgresql://api_user:secure_password@postgres-db:5432/student_success_db \
  -p 8000:8000 \
  student-success-api:latest
```

### Monitoring and Backup
- Database connection health checks
- Automated daily backups
- Performance monitoring with query logging
- Alert system for high-risk student detection

## Benefits of Database Integration

### Scalability
- Handle thousands of concurrent predictions
- Efficient queries with proper indexing
- Connection pooling for high load

### Data Integrity
- ACID compliance for consistent state
- Foreign key constraints prevent orphaned data
- Automatic timestamp tracking

### Analytics
- Historical trend analysis
- Intervention effectiveness tracking
- Population-level risk insights

### Auditability
- Complete prediction history
- User action tracking
- Compliance with data governance requirements

## Current Status

✅ **Completed**:
- Database schema design and creation
- SQLAlchemy models and relationships  
- Database connection management with fallback
- CSV to database migration scripts
- FastAPI integration with database persistence
- New database-specific API endpoints

⏳ **Pending Installation**:
- PostgreSQL system packages
- Python database dependencies (SQLAlchemy, psycopg2)

🔄 **Ready for Testing**:
- All code is database-ready
- SQLite fallback ensures functionality
- Production deployment ready once dependencies installed