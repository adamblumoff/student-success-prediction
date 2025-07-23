# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start Options
```bash
# MVP (Simple educator interface)
python3 run_mvp.py                    # Port 8001, SQLite, web UI

# Production API
python src/api/student_success_api.py # Port 8000, PostgreSQL

# Docker development (full stack)
docker-compose up                     # All services + monitoring
```

### Model Operations
```bash
# Train models from scratch
python src/models/train_models.py

# Run security tests
python3 scripts/security_test.py

# Database migration (CSV to DB)
python scripts/migrate_csv_to_db.py

# Production database setup
python scripts/setup_production_db.py
```

### Testing
```bash
# Integration tests
python -m pytest tests/integration/

# Database tests
python tests/integration/test_db_integration.py

# API endpoint tests  
python tests/integration/test_api.py

# ML model validation
python tests/integration/test_ml_with_db.py
```

## Architecture Overview

### Dual-Architecture Pattern
The system implements **two distinct architectures** for different use cases:

**MVP Architecture** (`src/mvp/`):
- **Purpose**: Simple educator interface for quick demos
- **Database**: SQLite for zero-configuration setup
- **Security**: Basic file validation with development API keys
- **Deployment**: Single Python process (`python3 run_mvp.py`)
- **Universal Gradebook Support**: Automatically detects Canvas, Blackboard, Moodle, Google Classroom formats

**Production Architecture** (`src/api/` + `src/database/`):
- **Purpose**: Enterprise-ready deployment with full security
- **Database**: PostgreSQL primary with SQLite fallback
- **Security**: Multi-tier authentication, rate limiting, enterprise security headers
- **Deployment**: Docker Compose with Nginx, Redis, monitoring stack
- **Performance**: 8.4ms API response time, handles 32K+ students

### Database Architecture

**Normalized Schema** (6 tables):
```
Student (1) ←→ (1) StudentEngagement    # VLE interaction metrics
Student (1) ←→ (1) StudentAssessment    # Assessment performance 
Student (1) ←→ (n) RiskPrediction       # Historical predictions
Student (1) ←→ (n) Intervention         # Recommended actions
Student (1) ←→ (1) StudentOutcome       # Final course results
```

**Dual Database Support**:
- **PostgreSQL**: Production deployment with connection pooling
- **SQLite**: Development/fallback with automatic schema creation
- **Connection Logic**: `src/database/connection.py` handles graceful fallback

### Machine Learning Pipeline

**Feature Engineering** (31 total features):
- **Demographics** (10): Age, gender, education, region, disability status
- **Early VLE Engagement** (10): First 28 days of interaction patterns
- **Early Assessment Performance** (11): First 70 days of assessment data

**Model Performance**:
- **Binary Classification**: 89.4% AUC (Pass/Fail prediction)
- **Multi-class Classification**: 77% F1-Score (Pass/Fail/Distinction/Withdrawn)
- **Response Time**: 8.4ms for real-time predictions

**Model Loading Pattern**:
```python
# Models auto-load from results/models/
intervention_system = InterventionRecommendationSystem()
risk_results = intervention_system.assess_student_risk(student_df)
recommendations = intervention_system.get_intervention_recommendations(student_df)
```

### Security Framework

**Multi-layer Authentication** (`src/security/`):
- **API Keys**: Three-tier system (Admin/Teacher/Read-only)
- **JWT Tokens**: Configurable expiration with IP validation
- **Brute Force Protection**: 5 failed attempts = 15-minute lockout

**File Upload Security**:
- **Size Limits**: 10MB maximum with configurable limits
- **MIME Validation**: python-magic with fallback to extension checking
- **CSV Injection Prevention**: Detects and sanitizes formula injection (`=`, `+`, `-`, `@`)
- **Content Validation**: Max 10,000 rows, 100 columns

**Rate Limiting** (endpoint-specific):
- Default: 100 requests/hour
- File uploads: 10/hour
- Analysis: 50/hour
- Authentication: 5 attempts/5 minutes

**Security Configuration**:
- Development: Uses `.env.security` template
- Production: Copy `.env.production.template` to `.env.production`
- Never commit `.env.*` files (except templates)

### API Structure

**Production Endpoints** (`src/api/student_success_api.py`):
```
POST /predict/single        # Individual student risk assessment
POST /predict/batch         # Multiple students (up to 1000)
POST /interventions/recommend # Get intervention recommendations
GET  /models/info           # Model metadata and performance
GET  /students/{id}/predictions # Student prediction history
GET  /analytics/risk-distribution # System-wide analytics
```

**MVP Endpoints** (`src/mvp/mvp_api.py`):
```
GET  /                      # Educator web interface
POST /api/mvp/analyze       # CSV upload and analysis
GET  /api/mvp/sample        # Load demo data
GET  /api/mvp/stats         # Simple analytics
```

### Universal Gradebook Integration

The system automatically detects and converts multiple gradebook formats:

**Supported Platforms**:
- **Canvas LMS**: Detects "Student", "ID", "Current Score" columns
- **Blackboard Learn**: Detects "Last Name", "First Name" separate columns
- **Moodle**: Detects "Email address", "Course total"
- **Google Classroom**: Detects "Timestamp", "Score" patterns
- **PowerSchool** (K-12): Detects "Student Number", "Grade Level"
- **Generic CSV**: Fallback for any format with ID and score columns

**Conversion Logic** (`src/mvp/mvp_api.py`):
```python
# Auto-detection and conversion
format_type = detect_gradebook_format(df)
df = universal_gradebook_converter(df)
```

## Key Development Patterns

### Environment-Based Configuration
```python
# Security depends on environment
if os.getenv('DEVELOPMENT_MODE', 'true').lower() == 'true':
    # Use development defaults
else:
    # Require production configuration
```

### Graceful Degradation
```python
# Database connection with fallback
db_available = test_db_connection()
if db_available:
    # Use PostgreSQL
else:
    # Fall back to SQLite
```

### Security-First Design
All endpoints require authentication by default:
```python
@app.post("/api/mvp/analyze")
async def analyze_student_data(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_write_permission)  # Security required
):
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

### Configuration Files
- `.env.security` - Security configuration template
- `.env.production.template` - Production deployment template
- `docker-compose.yml` - Full stack deployment
- `requirements.txt` - Python dependencies

### Security-Critical Files
- `src/security/` - Complete security framework
- `scripts/security_test.py` - Security validation suite
- `docs/SECURITY.md` - Comprehensive security documentation

### Database Files
- `src/database/models.py` - SQLAlchemy ORM models
- `src/database/connection.py` - Connection management with fallback
- `scripts/schema.sql` - PostgreSQL schema
- `scripts/migrate_csv_to_db.py` - Data migration utilities

### Model Files
- `src/models/intervention_system.py` - Main ML system
- `results/models/` - Trained model artifacts (.pkl files)
- `results/models/model_metadata.json` - Model performance metrics

## Development Workflow

1. **Start with MVP** for quick testing: `python3 run_mvp.py`
2. **Use production API** for full features: `python src/api/student_success_api.py`
3. **Run security tests** before deployment: `python3 scripts/security_test.py`
4. **Test with sample data** using examples in `examples/gradebooks/`
5. **Deploy with Docker** for production: `docker-compose up`

## Common Issues and Solutions

### Database Connection Issues
- System automatically falls back to SQLite if PostgreSQL unavailable
- Check `DATABASE_URL` environment variable
- Verify PostgreSQL service is running: `docker-compose up postgres`

### Security Configuration
- Development mode uses default API key: `dev-key-change-me`
- Production requires proper API keys in environment variables
- Run `python3 scripts/security_test.py` to validate configuration

### File Upload Issues
- Maximum file size: 10MB (configurable via `MAX_FILE_SIZE`)
- Supported formats: CSV with automatic gradebook detection
- CSV injection protection automatically sanitizes dangerous content

### Model Loading
- Models auto-load from `results/models/` directory
- If models missing, run `python src/models/train_models.py`
- Check model metadata in `results/models/model_metadata.json`

The system is designed for both educational demonstration (MVP) and production deployment, with comprehensive security, monitoring, and scalability features.

## Development Guidelines for Claude Code

### Commit Frequently and Update Documentation
- **Commit after every significant change** - Don't batch multiple unrelated changes
- **Update this CLAUDE.md file** after every commit that adds new features, changes architecture, or modifies development workflows
- **Use descriptive commit messages** that explain the business value, not just technical changes
- **Include security considerations** in commit messages when adding new endpoints or file handling

### When to Update CLAUDE.md
Update this file whenever you:
- Add new API endpoints or modify existing ones
- Change database schema or add new models
- Implement new security features or authentication methods
- Add new deployment options or Docker configurations
- Create new development scripts or change existing workflows
- Modify the universal gradebook converter or add new platform support
- Change the ML model training process or add new features
- Update environment variable requirements or configuration patterns

### CLAUDE.md Update Pattern
After making changes, always:
1. **Review this file** to ensure it reflects current architecture
2. **Add new patterns** you've implemented to the relevant sections
3. **Update commands** if you've added new scripts or changed existing ones
4. **Document new security measures** in the security framework section
5. **Commit the updated CLAUDE.md** along with your code changes

Example commit workflow:
```bash
# Make your code changes
git add src/new_feature.py

# Update CLAUDE.md to reflect the changes
# (Add new commands, update architecture notes, etc.)
git add CLAUDE.md

# Commit both together with descriptive message
git commit -m "Add new risk assessment endpoint with rate limiting

- Implement POST /api/risk/detailed for granular risk analysis
- Add rate limiting (20 requests/hour) for detailed analysis
- Update CLAUDE.md with new endpoint documentation and usage patterns

🤖 Generated with [Claude Code](https://claude.ai/code)"
```

This ensures future Claude instances always have up-to-date guidance that reflects the current state of the codebase.