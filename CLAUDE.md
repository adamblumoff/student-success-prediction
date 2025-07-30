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

**Production PostgreSQL Schema** (6 tables):
```sql
-- Core Tables
institutions (id, name, code, type, timezone, active, timestamps)
students (id, institution_id, student_id, grade_level, demographics, special_populations)
predictions (id, student_id, risk_score, risk_category, model_metadata, explanation_data)
interventions (id, student_id, type, status, outcome, roi_tracking)
audit_logs (id, user_id, action, resource, compliance_data)
model_metadata (id, version, performance_metrics, deployment_info)
```

**Development SQLite Fallback**:
- Automatic fallback when PostgreSQL unavailable
- Compatible schema subset for local development
- Zero-configuration setup for quick demos

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

**MVP Endpoints** (`src/mvp/mvp_api.py`):
```
GET  /                           # Main web interface
POST /api/mvp/analyze            # CSV upload and analysis (original model)
POST /api/mvp/analyze-detailed   # Detailed analysis with explanations
POST /api/mvp/analyze-k12        # K-12 gradebook analysis (ultra-advanced 81.5% AUC model)
GET  /api/mvp/sample             # Load demo data
GET  /api/mvp/stats              # Simple analytics
GET  /api/mvp/explain/{id}       # Individual prediction explanation
GET  /api/mvp/insights           # Global model insights
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
- `src/mvp/templates/index.html` - Main web interface
- `src/mvp/static/css/style.css` - Styling including explainable AI components
- `src/mvp/static/js/app.js` - Core JavaScript functionality
- `src/mvp/static/js/explainable-ui.js` - Explainable AI UI components

### Model Files
- `results/models/` - Trained model artifacts (.pkl files)
- `results/models/model_metadata.json` - Model performance metrics

### Configuration Files
- `requirements.txt` - Simplified Python dependencies (9 packages)
- `CLAUDE.md` - This development guide

## Development Workflow

1. **Start MVP** for testing: `python3 run_mvp.py`
2. **Use web interface** at http://localhost:8001
3. **Upload CSV** or try sample data
4. **View explanations** by clicking "Explain Prediction" on any student
5. **Check insights** in the Model Insights panel

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

**Note**: Currently uses sample data for explanations since CSV uploads don't store complete student feature profiles. Future enhancement could extract actual student features from uploaded data.

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

## Development Guidelines for Claude Code

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

### CLAUDE.md Update Pattern
After making changes, always:
1. **Review this file** to ensure it reflects current simplified architecture
2. **Add new patterns** you've implemented to the relevant sections
3. **Update commands** if you've added new scripts
4. **Document new explainable AI features** 
5. **Commit the updated CLAUDE.md** along with your code changes

Example commit workflow:
```bash
# Make your code changes
git add src/mvp/new_feature.py

# Update CLAUDE.md to reflect the changes
git add CLAUDE.md

# Commit both together with descriptive message
git commit -m "Add new explainable AI visualization feature

- Implement risk factor severity visualization in student explanations
- Add color-coded risk indicators in the web interface  
- Update CLAUDE.md with new explainable AI patterns

🤖 Generated with [Claude Code](https://claude.ai/code)"
```

This ensures future Claude instances always have up-to-date guidance that reflects the current simplified MVP state.