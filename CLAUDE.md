# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start
```bash
# MVP (Simple educator interface) - Auto-detects PostgreSQL or falls back to SQLite
python3 run_mvp.py                    # Port 8001, PostgreSQL/SQLite, web UI

# With PostgreSQL (Neon.tech)
export DATABASE_URL="postgresql://user:pass@host/database"
python3 run_mvp.py                    # Uses PostgreSQL with full production schema
```

### Model Operations
```bash
# Train original models (OULAD dataset)
python src/models/train_models.py

# Generate K-12 synthetic dataset
python src/models/k12_data_generator.py

# Engineer K-12 specific features
python src/models/k12_feature_engineering.py

# Train K-12 models (recommended)
python src/models/train_k12_models.py

# Train advanced K-12 model (targeting 89%+ AUC)
python src/models/k12_advanced_model.py

# Train ultra-advanced K-12 model (81.5% AUC achieved)
python src/models/k12_ultra_advanced_model.py

# Test K-12 explainable AI
python src/models/k12_explainable_ai.py

# Test K-12 intervention system
python src/models/k12_intervention_system.py

# Test ultra-advanced K-12 predictor (production-ready, 81.5% AUC)
python src/models/k12_ultra_predictor.py

# Run security tests (if needed)
python3 scripts/security_test.py
```

## GPT-Enhanced AI Insights (Current Feature - August 2025)

### 🧠 Intelligent Student Recommendations with Database Integration
The system includes advanced GPT integration with full database persistence and intelligent caching:

**Current Implementation (Verified):**
- **Database-Backed GPT Insights**: `gpt_insights` table stores all GPT analyses with full metadata
- **Smart Caching**: Database-level caching with `data_hash` validation and cache hit tracking
- **Real Data Integration**: GPT analyses use actual student database records, not sample data
- **Concise Format**: Emma Johnson format - exactly 3 recommendations per student
- **Intervention Awareness**: GPT considers existing interventions stored in `interventions` table
- **Performance Optimized**: Cache hits tracked, automatic invalidation on student data changes

**Database Schema (gpt_insights table):**
```sql
CREATE TABLE gpt_insights (
  id INTEGER PRIMARY KEY,
  institution_id INTEGER,
  student_id VARCHAR(100),
  student_database_id INTEGER,
  risk_level VARCHAR(20),
  data_hash VARCHAR(64),          -- For cache invalidation
  raw_response TEXT,              -- GPT raw output
  formatted_html TEXT,            -- Processed for display
  gpt_model VARCHAR(50),          -- Currently gpt-5-nano
  tokens_used INTEGER,
  generation_time_ms INTEGER,
  is_cached BOOLEAN,              -- Cache status tracking
  cache_hits INTEGER,             -- Performance metrics
  last_accessed DATETIME,
  created_at DATETIME,
  updated_at DATETIME
);
```

**Technical Stack:**
- **Backend**: `src/mvp/api/gpt_enhanced_endpoints.py` - GPT API endpoints with database persistence
- **Service Layer**: `src/mvp/services/gpt_oss_service.py` - OpenAI API integration with fallback handling
- **Caching**: `src/mvp/services/gpt_cache_service.py` - Database-backed caching system
- **Frontend**: `src/mvp/static/js/components/analysis.js` - Real-time GPT insight loading
- **Database**: SQLite (development) / PostgreSQL (production) with full schema support

## Codebase Cleanup (Completed 2024-12)

### 🗑️ Technical Debt Elimination
The codebase underwent aggressive cleanup removing 745+ lines of bloat:

**Phase 1 Removals:**
- ❌ Duplicate entry points (`app.py`, `start_local.py`)
- ❌ One-time database fix script (`fix_student_ids.py`)
- ❌ 6 unused JavaScript integration files
- ❌ Manual backup HTML template
- ❌ All Python cache files

**Phase 2 Removals:**
- ❌ Legacy CSS file (`style.css` - 84KB)
- ❌ Unreferenced test CSV files
- ❌ Obsolete OULAD download script
- ❌ Empty directories (`logs/`, `repo/`)
- 📁 OULAD raw data archived to `data/archive/`

**Impact:** 20-25% codebase reduction, improved maintainability, zero functional impact

## Production Readiness Assessment (Updated 2024-12)

### 🔍 Comprehensive Analysis Results
The application has undergone comprehensive analysis by specialized agents covering code quality, security, testing, deployment, and technical debt. 

**Overall Production Readiness Score:**
- **Single K-12 District** (≤5000 students): **80% Ready** - Critical security fixes needed
- **Multi-District/State-wide** (≥50K students): **40% Ready** - Architectural scaling required

### 🚨 Critical Issues Requiring Immediate Attention

#### Security Vulnerabilities (HIGH PRIORITY)
1. **Default PostgreSQL Credentials** - `src/mvp/database.py:68-69`
   - Issue: Uses `postgres:postgres@` fallback in production
   - Risk: Unauthorized database access to FERPA-protected data
   - Fix: Remove fallback credentials, enforce environment-based config

2. **Hardcoded Demo Passwords** - `scripts/create_demo_users.py:64`
   - Issue: Predictable passwords ("admin123", "demo123") may reach production
   - Risk: Administrative access bypass
   - Fix: Environment check to prevent demo users in production

3. **Encryption Disabled by Default** - `src/mvp/encryption.py:42-48`
   - Issue: Student PII stored unencrypted unless explicitly enabled
   - Risk: FERPA compliance violation
   - Fix: Enable encryption by default in production environments

4. **Unsafe SQL Construction** - `src/mvp/database.py:472-476`
   - Issue: String interpolation in SQL queries despite SQLAlchemy usage
   - Risk: SQL injection vulnerability
   - Fix: Use parameterized queries exclusively

#### Code Quality Issues (MEDIUM PRIORITY)
1. **Monolithic Functions** - `src/mvp/api/core.py:89-243`
   - Issue: 154-line function handling multiple responsibilities
   - Impact: Difficult testing and debugging
   - Fix: Separate into focused service classes

2. **Code Duplication** - Multiple files
   - Issue: Gradebook processing logic duplicated across 7+ files
   - Impact: Maintenance burden and inconsistency risk
   - Fix: Extract centralized GradebookProcessingService

3. **Print Statement Pollution** - Codebase-wide
   - Issue: 316 print statements instead of proper logging
   - Impact: Uncontrolled console output in production
   - Fix: Replace with structured logging using existing framework

#### Test Coverage Gaps (MEDIUM PRIORITY)
1. **Security Test Failures** - `tests/api/test_security.py`
   - Issue: 24 failing security tests indicating authentication bypass
   - Impact: Unverified security controls
   - Fix: Correct API key validation and environment configuration

2. **Missing Integration Coverage** - `src/integrations/*.py`
   - Issue: No test coverage for Canvas/PowerSchool/Google Classroom APIs
   - Impact: Integration failures may go undetected
   - Fix: Implement mock-based integration testing

3. **CSV Processing Uncovered** - `src/mvp/csv_processing.py`
   - Issue: Core data processing logic lacks dedicated tests
   - Impact: Data validation failures may cause incorrect predictions
   - Fix: Add comprehensive CSV processing test suite

### 📈 Technical Debt Analysis

#### High Impact/Low Effort (Quick Wins)
1. **Exception Handling** - 4 files with bare `except:` clauses
2. **Logging Standardization** - Replace print statements with structured logging
3. **Configuration Cleanup** - Remove hardcoded magic numbers and paths

#### High Impact/High Effort (Major Refactoring)
1. **Service Extraction** - Break monolithic API functions into focused services
2. **Database Layer** - Add connection monitoring, circuit breakers, batch optimization
3. **Security Hardening** - Implement distributed rate limiting, token rotation

#### Code Bloat Elimination (15-20% Reduction)
**Safe to Remove Immediately:**
- `app.py` (102 lines) - Duplicate application entry point
- `start_local.py` (65 lines) - Redundant local launcher
- `fix_student_ids.py` (178 lines) - One-time database fix script
- `src/mvp/templates/index_backup.html` - Manual backup file

**Estimated Impact:** 345+ lines of redundant code elimination

### 🏗️ Architecture Assessment

#### Current Architecture Strengths
- Modular API design with focused routers
- Comprehensive encryption system for FERPA compliance
- Strong ML model foundation (81.5% AUC K-12 predictor)
- Extensive audit logging and monitoring infrastructure

#### Scaling Limitations
1. **Monolithic Deployment** - Single FastAPI process handling all concerns
2. **In-Memory Dependencies** - Rate limiting and session storage not distributed
3. **Database Single Point of Failure** - No replication or high availability
4. **ML Model Resource Usage** - 1.2GB+ memory per instance

#### Production Deployment Strategy
**Immediate (Single District):**
- Fix critical security vulnerabilities
- Enable HTTPS enforcement with proper SSL
- Implement persistent session storage
- Add database connection monitoring

**Long-term (Multi-District):**
- Implement service mesh architecture (API gateway + ML service + data service)
- Add database read replicas with connection routing
- External ML model serving (MLflow/Seldon)
- Redis-based distributed caching

### 🧪 Testing Strategy Improvements

#### Current Status
- **Coverage Score:** ~60% (116/145 tests passing)
- **Frontend Tests:** 125 tests documented and passing
- **Backend Tests:** Comprehensive security, database, and API coverage

#### Priority Improvements
1. **Fix Failing Tests** - Resolve 24 security test failures
2. **Add Integration Mocks** - Canvas LMS, PowerSchool, Google Classroom
3. **CSV Processing Suite** - Comprehensive data validation testing
4. **Performance Testing** - Load testing for 1000+ concurrent users

## Architecture Overview

### Production-Ready MVP Architecture
The system implements a **hybrid architecture** supporting both development and production deployments:

**MVP Architecture** (`src/mvp/`):
- **Purpose**: Full-featured educator interface with explainable AI
- **Database**: PostgreSQL (production) with SQLite fallback (development)
- **Security**: API key authentication with rate limiting and audit logging
- **Deployment**: Single Python process with auto-scaling database support
- **Gradebook Support**: Canvas LMS and generic CSV formats
- **Explainable AI**: Feature importance, prediction explanations, risk factor analysis
- **Multi-Tenant**: Institution-based data isolation for K-12 districts

### Database Architecture

**Current Database Schema** (10 tables):
```sql
-- Core Tables (Verified Current)
institutions       -- Institution management
students          -- Student records with K-12 demographics
predictions       -- ML model predictions and risk scores
interventions     -- Intervention tracking and outcomes
gpt_insights      -- GPT analysis cache and metadata (NEW)
audit_logs        -- Security and compliance logging
model_metadata    -- ML model version and performance data
users             -- User authentication and authorization
user_sessions     -- Session management
alembic_version   -- Database migration tracking
```

**Development SQLite (Current Default)**:
- Automatic fallback when PostgreSQL unavailable (DATABASE_URL not set)
- Full schema compatibility with all 10 production tables
- Zero-configuration setup for quick demos
- File: `mvp_data.db` in project root

### Machine Learning Pipeline

**K-12 Specialized Models** (Current - Recommended):
- **Feature Engineering** (85 total features): Grade-band specific features for elementary (K-5), middle (6-8), and high school (9-12)
- **Demographics** (24): Age, grade level, socioeconomic factors, special populations (IEP, ELL, 504 plans)
- **Academic Performance** (23): GPA trends, course failures, credit accumulation, subject-specific performance
- **Engagement & Behavior** (18): Attendance patterns, behavioral metrics, extracurricular involvement
- **Early Warning Indicators** (12): Research-based ABC indicators (Attendance, Behavior, Course performance)
- **Grade-Specific** (8): Elementary reading focus, middle school transition, high school graduation tracking

**K-12 Model Performance**:
- **Ultra-Advanced Model**: 81.5% AUC (Neural Network with Stacking Ensemble)
- **Advanced Model**: 77.7% AUC (Extra Trees with Feature Selection)
- **Original K-12 Model**: 74.3% AUC (Logistic Regression)
- **Synthetic Dataset**: 30,000 students with ultra-realistic archetype separation
- **Feature Count**: 40 optimized features from 59 engineered features
- **Response Time**: <100ms for real-time predictions

**Original Models** (OULAD - Higher Education):
- **Feature Engineering** (31 total features): University-focused features
- **Binary Classification**: 89.4% AUC (Pass/Fail prediction)
- **Multi-class Classification**: 77% F1-Score (Pass/Fail/Distinction/Withdrawn)
- **Dataset**: Open University Learning Analytics Dataset

**Model Loading Pattern**:
```python
# K-12 Models (recommended for school districts)
from src.models.k12_intervention_system import K12InterventionSystem
intervention_system = K12InterventionSystem()
risk_results = intervention_system.assess_student_risk(student_data)
explanations = intervention_system.explainable_ai.predict_with_explanation(student_data)

# Original Models (higher education)
from src.models.intervention_system import InterventionRecommendationSystem
intervention_system = InterventionRecommendationSystem()
risk_results = intervention_system.assess_student_risk(student_df)
```

### Security Framework

**Simplified Authentication** (`src/mvp/simple_auth.py`):
- **API Key**: Single development key for MVP use
- **Rate Limiting**: Simple in-memory rate limiting
- **File Validation**: Basic CSV validation with size limits

**Security Configuration**:
- Development: Uses default API key `dev-key-change-me`
- Environment variable: `MVP_API_KEY` for custom key

### API Structure

**Current API Endpoints** (Modular Router Architecture):
```
# Core MVP (src/mvp/api/core.py)
POST /api/mvp/analyze            # CSV upload and K-12 analysis
POST /api/mvp/analyze-detailed   # Detailed analysis with explanations
GET  /api/mvp/sample             # Demo data with full feature set
GET  /api/mvp/stats              # Analytics dashboard
GET  /api/mvp/explain/{id}       # Prediction explanations

# GPT Enhanced Analysis (src/mvp/api/gpt_enhanced_endpoints.py)
POST /api/mvp/gpt-insights/check     # Check for cached GPT insights
POST /api/mvp/gpt-insights/generate  # Generate new GPT analysis
GET  /api/mvp/gpt-insights/{id}      # Retrieve specific GPT insight

# Intervention Management (src/mvp/api/interventions.py)
POST /api/interventions              # Create intervention
GET  /api/interventions/student/{id} # Get student interventions
PUT  /api/interventions/{id}/status  # Update intervention status
DELETE /api/interventions/{id}       # Delete intervention

# Health & Monitoring
GET  /health                         # System health check
GET  /docs                           # Interactive API documentation
```

### Explainable AI Features

**Individual Explanations**:
- Risk factor identification with severity levels
- Protective factor analysis
- Confidence scoring and uncertainty quantification
- Personalized intervention recommendations

**Global Insights**:
- Feature importance visualization
- Category-based importance (demographics, engagement, assessment)
- Top predictive factors across all students

### Universal Gradebook Integration

**Supported Platforms**:
- **Canvas LMS**: Detects "Student", "ID", "Current Score" columns
- **Generic CSV**: Any format with ID and score columns

**Conversion Logic** (`src/mvp/mvp_api.py`):
```python
# Auto-detection and conversion (simplified)
format_type = detect_gradebook_format(df)  # 'canvas' or 'generic'
df = universal_gradebook_converter(df)
```

## Key Development Patterns

### Simple Authentication
```python
# Simple API key check
def simple_auth(credentials):
    if credentials.credentials != os.getenv("MVP_API_KEY", "dev-key-change-me"):
        raise HTTPException(401, "Invalid API key")
    return {"user": "mvp_user"}
```

### Explainable AI Integration
```python
# Get detailed explanations
explanations = intervention_system.get_explainable_predictions(student_df)
for explanation in explanations:
    print(f"Student {explanation['student_id']}: {explanation['risk_category']}")
    print(f"Explanation: {explanation['explanation']}")
```

### Error Handling Pattern
```python
try:
    # Business logic
except HTTPException:
    raise  # Re-raise HTTP exceptions
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Generic error message")
```

## Important Files and Locations

### Core Application Files
- `run_mvp.py` - Main application launcher
- `src/mvp/mvp_api.py` - MVP API implementation
- `src/mvp/simple_auth.py` - Simplified security layer
- `src/models/intervention_system.py` - ML system with explainable AI
- `src/models/explainable_ai.py` - Explainable AI module

### UI Files
- `src/mvp/templates/index.html` - Main web interface with GPT insights integration
- `src/mvp/static/css/modern-style.css` - Modern UI styling
- `src/mvp/static/css/bulk-actions.css` - Intervention management styles
- `src/mvp/static/js/main.js` - Application initialization
- `src/mvp/static/js/components/analysis.js` - Student analysis with GPT insights
- `src/mvp/static/js/components/dashboard.js` - Analytics dashboard
- `src/mvp/static/js/interventions.js` - Intervention management system

### Model Files
- `results/models/` - Trained model artifacts (.pkl files)
- `results/models/model_metadata.json` - Model performance metrics

### Configuration Files
- `requirements.txt` - Production dependencies (~25 packages)
- `package.json` - JavaScript testing dependencies
- `alembic.ini` - Database migration configuration
- `CLAUDE.md` - This development guide (2000+ lines)

## Development Workflow

### Local Development
1. **Start MVP** for testing: `python3 run_mvp.py`
2. **Use web interface** at http://localhost:8001
3. **Upload CSV** or try sample data
4. **View explanations** by clicking "Explain Prediction" on any student
5. **Check insights** in the Model Insights panel
6. **Test notifications** via browser console: `notificationSystem.testAlert()`

### Production Deployment
1. **Validate deployment readiness**: `python3 scripts/validate_deployment.py`
2. **Configure environment**: Copy `.env.production` to `.env` and update values
3. **Deploy with Docker**: `./deploy.sh --environment production`
4. **Verify deployment**: `curl http://localhost:8001/health`
5. **Monitor system**: Check logs with `docker compose -f docker-compose.prod.yml logs -f`

### Docker Deployment Options

**Quick Development Setup**:
```bash
# Copy environment file
cp .env.development .env

# Deploy development environment
./deploy.sh --environment development

# Access application
open http://localhost:8001
```

**Production Deployment**:
```bash
# Validate deployment readiness
python3 scripts/validate_deployment.py

# Configure production environment
cp .env.production .env
nano .env  # Update DATABASE_URL, MVP_API_KEY, etc.

# Deploy with full testing
./deploy.sh --environment production

# Or skip tests for faster deployment
./deploy.sh --environment production --skip-tests

# Verify deployment
curl http://localhost:8001/health
curl http://localhost:8001/docs
```

**Manual Docker Commands**:
```bash
# Build production image
docker build --target production -t student-success-prediction:latest .

# Run production stack
docker compose -f docker-compose.prod.yml up -d --build

# Check status
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f app

# Stop and cleanup
docker compose -f docker-compose.prod.yml down
```

## Common Issues and Solutions

### Model Loading
- Models auto-load from `results/models/` directory
- If models missing, run `python src/models/train_models.py`
- Check model metadata in `results/models/model_metadata.json`

### File Upload Issues
- Maximum file size: 10MB
- Supported formats: CSV only
- Automatic format detection for Canvas and generic CSV

### Authentication
- Default API key: `dev-key-change-me`
- Set custom key via `MVP_API_KEY` environment variable
- All endpoints require authentication

### Explainable AI "Explain Prediction" Button Issues
**Problem**: 500 errors when clicking "Explain AI Prediction" buttons

**Root Cause**: The ML model requires all 31 engineered features, but the API endpoint was only providing 10 sample features, causing a pandas index error.

**Solution**: Updated `/api/mvp/explain/{student_id}` endpoint to provide complete feature set:
```python
# All 31 required features must be provided:
# Demographics (6): gender_encoded, region_encoded, age_band_encoded, education_encoded, is_male, has_disability
# Academic History (4): studied_credits, num_of_prev_attempts, registration_delay, unregistered  
# Early VLE Engagement (10): early_total_clicks, early_avg_clicks, early_clicks_std, etc.
# Early Assessment Performance (11): early_assessments_count, early_avg_score, early_score_std, etc.
```

**Debugging Command**: `python3 test_endpoints.py` to verify explainable AI functionality

**Current Implementation**: The system now uses actual database student records for GPT analysis. When students are uploaded via CSV, they're stored in the `students` table with full K-12 demographic data, and GPT analyses reference this real data rather than sample features.

## PostgreSQL Migration & Deployment

### Database Setup Options

**Option 1: Neon.tech (Recommended - IPv4 Compatible)**
```bash
# 1. Create account at https://neon.tech
# 2. Create database named 'student_success'
# 3. Copy connection string
export DATABASE_URL="postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/student_success?sslmode=require"

# Run migration
alembic upgrade head

# Start server
python3 run_mvp.py
```

**Option 2: Supabase (IPv6 Required)**
```bash
# Note: Requires IPv6 connectivity (cloud environments)
export DATABASE_URL="postgresql://postgres:pass@db.project.supabase.co:5432/postgres"
alembic upgrade head
python3 run_mvp.py
```

**Option 3: Development with Auto-Fallback**
```bash
# No DATABASE_URL set - automatically uses SQLite
python3 run_mvp.py  # Uses mvp_data.db
```

### Migration System

**Alembic Configuration**:
- **Location**: `alembic/` directory with complete K-12 schema
- **Migration**: `alembic upgrade head` creates all 6 production tables
- **Rollback**: `alembic downgrade base` removes all tables
- **Status**: `alembic current` shows current migration version

**Database Health Check**:
```python
from mvp.database import check_database_health
print("Health:", "✅ PASSED" if check_database_health() else "❌ FAILED")
```

### Environment Configuration

**Environment Variables**:
```bash
DATABASE_URL=postgresql://user:pass@host/database  # PostgreSQL connection
MVP_API_KEY=your-secure-api-key                   # API authentication
SQL_DEBUG=true                                     # Enable SQL logging
PORT=8001                                          # Server port
```

**Configuration Files**:
- `.env` - Local environment variables (not committed)
- `.env.example` - Template for environment setup
- `CLAUDE.md` - This development guide (always keep updated)

### K-12 Specialized Features

**Grade-Band Specific Analysis**:
- **Elementary (K-5)**: Reading proficiency by grade 3, foundational skills, family engagement focus
- **Middle School (6-8)**: Engagement drop identification, transition support, peer relationship factors  
- **High School (9-12)**: Credit accumulation tracking, graduation likelihood, college/career readiness

**Comprehensive Intervention System**:
```python
# Generate full intervention plan with family communication
intervention_plan = intervention_system.generate_intervention_plan(student_data)
family_comm = intervention_system.generate_family_communication(intervention_plan)

# Intervention categories: academic_support, attendance_support, behavioral_support, 
# engagement_support, family_engagement
```

**K-12 Data Generation**:
- **Synthetic Dataset**: 15,000 students with realistic K-12 patterns based on educational research
- **Feature Categories**: Demographics, academic history, engagement metrics, early warning indicators
- **Grade-Level Considerations**: Age-grade alignment, retention patterns, special populations
- **Multi-Year Tracking**: Up to 3 years of academic history per student

**Explainable AI for Educators**:
- Grade-appropriate explanations for elementary, middle, and high school contexts
- Risk and protective factor identification with severity/strength ratings
- Actionable recommendations with implementation timelines
- Family-friendly communication templates

The system is designed for educational demonstration with explainable AI features, now supporting both development simplicity and production scalability with specialized K-12 capabilities.

## Repository Cleanup Guidelines

### Regular Cleanup Process
**When to perform cleanup**: After completing major features or integrations

**Cleanup checklist**:
1. **Remove old model files**: Keep only the latest/best performing models in `results/models/`
2. **Delete backup files**: Remove any `*.bak`, `*_old*`, `*~`, `.DS_Store` files
3. **Consolidate documentation**: Remove duplicate documentation files
4. **Organize test files**: Ensure all tests are in the `tests/` directory
5. **Clean empty directories**: Remove empty directories in `results/figures/` etc.
6. **Update structure docs**: Update `DIRECTORY_STRUCTURE.md` to reflect new integrations
7. **Commit and push**: Always commit cleanup changes with descriptive messages

**Cleanup command pattern**:
```bash
# Remove old model versions (keep latest/best performing)
rm -f results/models/k12/k12_*_old_date_*.pkl

# Update documentation to reflect current structure
# Update CLAUDE.md with new features/patterns

# Commit the cleanup
git add -A
git commit -m "Clean up repository structure and remove outdated files

- Remove outdated model files (keep ultra-advanced 81.5% AUC model)
- Consolidate duplicate documentation
- Update directory structure to reflect Google Classroom integration
- Organize repository for better navigation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin dev
```

**Files to always keep**:
- Latest K-12 ultra-advanced model (`k12_ultra_advanced_*.pkl`)
- Production-ready trained models
- Current integration code
- Active documentation and guides

**Files safe to remove**:
- Older model versions with lower performance
- Duplicate structure documentation
- Empty result directories
- Backup/temporary files


## System Maintenance and Reliability

### Automated Testing and Health Monitoring

The system includes comprehensive testing and monitoring infrastructure to ensure reliability:

**Health Monitoring:**
```bash
# Run system health check
python3 scripts/system_health_monitor.py

# Continuous monitoring (every 15 minutes)
python3 scripts/system_health_monitor.py --continuous 15

# Email alerts on issues
python3 scripts/system_health_monitor.py --email
```

**Automated Testing:**
```bash
# Run full test suite
python3 scripts/run_automated_tests.py

# Run specific test categories
python3 scripts/run_automated_tests.py --suites unit_tests api_tests notification_tests

# Performance benchmarking
python3 scripts/run_automated_tests.py --performance-only
```

**Maintenance Scripts:**
```bash
# Daily maintenance
./scripts/daily_maintenance.sh

# Weekly maintenance
./scripts/weekly_maintenance.sh

# Emergency restart
./scripts/emergency_restart.sh

# System status check
./scripts/system_status.sh
```

### Test Coverage

The system includes comprehensive tests:
- **Unit Tests**: Individual component testing
- **API Tests**: All endpoint testing with authentication
- **Notification Tests**: Real-time notification system testing
- **Integration Tests**: LMS/SIS integration testing
- **Performance Tests**: Response time and throughput testing

### Monitoring and Alerting

**Health Checks Monitor:**
- API endpoint responsiveness
- Database connectivity
- Model loading and performance
- Notification system functionality
- Integration system health
- File system and resource usage

**Alerting Thresholds:**
- Response time > 5 seconds (warning)
- Disk usage > 85% (warning)
- Memory usage > 80% (warning)
- API errors > 50% (critical)
- Database connection failures (critical)

### Maintenance Schedule

**Daily (Automated):**
- Health monitoring every 15 minutes
- Error log analysis
- Basic connectivity checks

**Weekly (Automated):**
- Full test suite execution
- Database maintenance and optimization
- Log rotation and cleanup
- Dependency updates

**Monthly (Manual Review):**
- Model performance evaluation
- Security audit
- Full system backup
- Documentation updates

### Configuration Files

**Health Monitor**: `config/health_monitor.json`
**Test Runner**: `config/test_runner.json`
**Cron Jobs**: `config/cron_examples.txt`
**Systemd Service**: `config/student-success.service`

See `docs/SYSTEM_MAINTENANCE.md` for comprehensive maintenance procedures.

## Development Guidelines for Claude Code

### Modular API Architecture (2024 Update)

**Why Split APIs?**: To improve debugging, maintainability, and development velocity.

**Current Modular Structure**:
```
src/mvp/mvp_api.py          # Main entry point - imports all routers
src/mvp/api/
├── core.py                 # Core MVP endpoints (/api/mvp/*)
├── canvas_endpoints.py     # Canvas LMS endpoints (/api/lms/*)
├── powerschool_endpoints.py # PowerSchool SIS endpoints (/api/sis/*)
├── google_classroom_endpoints.py # Google Classroom endpoints (/api/google/*)
└── combined_endpoints.py   # Combined integration endpoints (/api/integration/*)
```

**Benefits Achieved**:
- **Easier Debugging**: Each integration system isolated in separate files
- **Faster Development**: Can work on specific integrations without navigating large monolithic files
- **Better Testing**: Each router can be tested independently
- **Cleaner Organization**: Related endpoints grouped logically
- **Reduced Merge Conflicts**: Multiple developers can work on different integrations simultaneously

**Development Pattern**:
```python
# When adding new endpoints, create focused routers:
from fastapi import APIRouter
router = APIRouter()

@router.post("/new-endpoint")
async def new_endpoint():
    return {"status": "success"}

# Then include in main API:
app.include_router(router, prefix="/api/category", tags=["Category"])
```

**Future Considerations**:
- Consider splitting routers further if they exceed 300-400 lines
- Keep related endpoints together (don't over-split)
- Always include proper error handling and logging in each router
- Maintain consistent authentication patterns across all routers

### Key Debugging Improvements Made

**1. Fixed Sample Endpoint**: The original `/api/mvp/sample` endpoint only provided 7 features but the ML model requires all 31 engineered features. Fixed by providing complete feature set:

```python
# All 31 required features must be provided:
# Demographics (6): gender_encoded, region_encoded, age_band_encoded, education_encoded, is_male, has_disability
# Academic History (4): studied_credits, num_of_prev_attempts, registration_delay, unregistered  
# Early VLE Engagement (10): early_total_clicks, early_avg_clicks, early_clicks_std, etc.
# Early Assessment Performance (11): early_assessments_count, early_avg_score, early_score_std, etc.
```

**2. Fixed Database Function Imports**: Added missing `save_predictions_batch` and `save_prediction` functions to `src/mvp/database.py` with proper ORM model integration.

**3. Import Path Consistency**: Standardized all imports to use `src.` prefix for consistency across the modular structure.

**4. DataFrame to Dict Conversion**: Fixed API endpoints to properly convert intervention system DataFrame outputs to JSON-serializable dictionaries:

```python
# Convert DataFrame results to API format
results = []
for _, row in results_df.iterrows():
    results.append({
        'student_id': int(row['student_id']),
        'risk_score': float(row['risk_score']),
        'risk_category': str(row['risk_category']),
        'success_probability': float(row['success_probability']),
        'needs_intervention': bool(row['needs_intervention'])
    })
```

### Commit Frequently and Update Documentation
- **Commit after every significant change** - Don't batch multiple unrelated changes
- **Update this CLAUDE.md file** after every commit that adds new features or changes architecture
- **Use descriptive commit messages** that explain the business value
- **Focus on MVP functionality** - avoid adding production complexity

### When to Update CLAUDE.md
Update this file whenever you:
- Add new API endpoints or modify existing ones
- Implement new explainable AI features
- Change the simplified security model
- Add new UI components or visualizations
- Modify the gradebook conversion logic
- Update the intervention recommendation system
- **Make architectural changes like API modularization**
- **Fix debugging issues that future developers might encounter**

### CLAUDE.md Update Pattern
After making changes, always:
1. **Review this file** to ensure it reflects current simplified architecture
2. **Add new patterns** you've implemented to the relevant sections
3. **Update commands** if you've added new scripts
4. **Document new explainable AI features** 
5. **Document debugging fixes and architectural decisions**
6. **Commit the updated CLAUDE.md** along with your code changes

Example commit workflow:
```bash
# Make your code changes
git add src/mvp/api/

# Update CLAUDE.md to reflect the changes
git add CLAUDE.md

# Commit both together with descriptive message
git commit -m "Refactor monolithic API into modular structure for easier debugging

- Split MVP API into 4 focused routers (core, canvas, powerschool, combined)
- Fix sample endpoint to provide all 31 required ML features
- Add missing database functions with proper ORM integration
- Standardize import paths for consistency
- Update CLAUDE.md with modular architecture patterns

Benefits: Easier debugging, faster development, better testing isolation

🤖 Generated with [Claude Code](https://claude.ai/code)"
```

This ensures future Claude instances always have up-to-date guidance that reflects the current modular architecture and debugging improvements.

## Repository Cleanup and Organization

### Regular Cleanup Process

**When to Clean Up**: Perform repository cleanup regularly, especially:
- After major feature development
- Before important commits/releases
- When repository becomes cluttered
- After refactoring or modularization
- When onboarding new developers

**Cleanup Checklist**:
```bash
# 1. Remove unnecessary files
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
rm -f *_old.py *_backup.py *.tmp

# 2. Remove duplicate test files from root
rm -f test_*.py  # (if they exist in tests/ directory)

# 3. Check for empty directories
find . -type d -empty | grep -v ".git" | grep -v "venv"

# 4. Verify .gitignore is up to date
git status  # Check for untracked files that should be ignored

# 5. Update documentation
# - Update DIRECTORY_STRUCTURE.md if structure changed
# - Update CLAUDE.md with new patterns
# - Update README.md if major changes made
```

### Repository Organization Principles

**Directory Structure Goals**:
- **Logical Grouping**: Related functionality in same directories
- **Modular Design**: Each module can be developed/tested independently  
- **Clear Navigation**: Developers can quickly find what they need
- **Scalability**: Structure supports growth without reorganization

**Current Organization**:
```
📁 Core Application (src/mvp/) - Web app and API
📁 ML Models (src/models/) - All machine learning components
📁 Integrations (src/integrations/) - External system connections
📁 Testing (tests/) - Comprehensive test suite
📁 Documentation (docs/ + *.md) - All project documentation
📁 Data & Results (data/, results/) - Datasets and model outputs
📁 Deployment (deployment/, alembic/) - Infrastructure and migrations
```

**Navigation Helper**: Use `DIRECTORY_STRUCTURE.md` for quick reference to file locations and purposes.

### Automated Cleanup Integration

**Repository Cleanup Commands** (Available in scripts/cleanup.sh):
```bash
# Quick cleanup (run before commits)
./scripts/cleanup.sh

# Manual cleanup steps:
find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.tmp" -delete && find . -name "*~" -delete 2>/dev/null || true
rm -f *_old.py *_backup.py *.bak 2>/dev/null || true

# Clean old logs and reports
find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true  
find test_reports/ -name "*" -mtime +7 -delete 2>/dev/null || true

# Validate repository structure
python3 scripts/validate_deployment.py
```

**Integration with Development Workflow**:
1. **Before Major Commits**: Run cleanup to ensure repository is organized
2. **After Refactoring**: Remove old files and update structure documentation
3. **Weekly Maintenance**: Quick cleanup check during development
4. **Before Deployment**: Ensure no development artifacts in production code

This systematic approach maintains a clean, navigable repository that scales with the project's growth.
- this product is made for teachers/adminstrators for k-12 schools and making their workflow easier
- always have the server running in the background so that i can test it
- need to make sure features work before committing
- if there is a problem with data in some way, please query the database and see what is going on.
- use .env whenever connecting to the database