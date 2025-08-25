# Repository Directory Structure

This document provides a clear overview of the repository organization for easy navigation.

## 🏗️ Core Application Architecture

```
src/
├── mvp/                     # Production-Ready Web Application
│   ├── mvp_api.py          # Main API entry point (imports all routers)
│   ├── api/                # Modular API Routers (6 specialized modules)
│   │   ├── core.py         # Core MVP endpoints (/api/mvp/*)
│   │   ├── interventions.py # Comprehensive intervention system (/api/interventions/*)
│   │   │                   #   - Individual & bulk CRUD operations
│   │   │                   #   - Mixed selection (students + interventions)
│   │   │                   #   - Real-time status updates
│   │   ├── canvas_endpoints.py     # Canvas LMS integration (/api/lms/*)
│   │   ├── powerschool_endpoints.py # PowerSchool SIS integration (/api/sis/*)
│   │   ├── google_classroom_v2.py  # Google Classroom integration (/api/google/*)
│   │   └── combined_endpoints.py   # Multi-platform integration (/api/integration/*)
│   ├── database.py         # Hybrid PostgreSQL/SQLite database layer
│   ├── models.py           # SQLAlchemy ORM models (6 production tables)
│   ├── simple_auth.py      # API key authentication system
│   ├── static/             # Modern Web Assets
│   │   ├── css/            
│   │   │   ├── style.css   # Main application styles
│   │   │   └── bulk-actions.css # Bulk intervention system styles (1000+ lines)
│   │   ├── js/             
│   │   │   ├── main.js     # Application initialization
│   │   │   ├── interventions.js # Intervention management with real-time updates
│   │   │   └── components/ # Modular JavaScript Architecture (11 components)
│   │   │       ├── selection-manager.js        # Advanced selection system
│   │   │       ├── bulk-operations-manager.js  # Operations coordinator
│   │   │       ├── bulk-intervention-modal.js  # Bulk creation wizard
│   │   │       ├── bulk-status-modal.js        # Bulk status updates
│   │   │       ├── bulk-assignment-modal.js    # Staff assignment system
│   │   │       ├── analysis.js                 # Student analysis component
│   │   │       ├── dashboard.js                # Analytics dashboard
│   │   │       └── file-upload.js              # CSV processing component
│   └── templates/          # HTML templates with bulk operations UI
├── models/                 # Advanced Machine Learning Pipeline
│   ├── k12_ultra_predictor.py      # Production K-12 model (81.5% AUC)
│   ├── k12_explainable_ai.py       # Explainable AI engine
│   ├── intervention_system.py      # ML-powered intervention recommendations
│   ├── k12_feature_engineering.py  # 40-feature K-12 pipeline
│   └── train_k12_models.py         # Model training scripts
├── integrations/          # External System Integrations
│   ├── canvas_lms.py      # Canvas LMS gradebook processing
│   ├── powerschool_sis.py # PowerSchool SIS data synchronization
│   ├── google_classroom.py # Google Classroom assignment integration
│   └── combined_integration.py # Multi-platform workflow integration
└── data/
    └── download.py        # Data acquisition utilities
```

## 📊 Data & Machine Learning Pipeline

```
data/
├── raw/                   # Original datasets (OULAD - 32K students)
├── processed/             # Engineered features (31-feature pipeline)
└── k12_synthetic/         # K-12 synthetic dataset (30K students)
    ├── k12_synthetic_dataset_20250729.csv    # Training data
    ├── k12_features_engineered_20250729.csv  # 40 engineered features
    └── dataset_metadata.json                 # Feature documentation

results/
├── models/                # Trained Model Artifacts
│   ├── best_binary_model.pkl     # Original OULAD model (84.9% AUC)
│   ├── model_metadata.json       # Performance metrics
│   └── k12/                      # K-12 Specialized Models
│       ├── k12_ultra_advanced_20250730_113326.pkl  # Production model (81.5% AUC)
│       ├── k12_ultra_metadata_20250730_113326.json # Model specifications
│       └── k12_ultra_features_20250730_113326.json # 40 selected features
└── reports/              # Analysis and validation reports
```

## 🧪 Comprehensive Testing Infrastructure

```
tests/                            # Complete Test Suite (125+ tests)
├── components/                   # Frontend Component Tests (82 tests)
│   ├── analysis.test.js         # Student analysis functionality
│   ├── dashboard.test.js        # Dashboard and visualization tests
│   ├── file-upload.test.js      # CSV processing and validation
│   └── interventions.test.js    # Intervention management workflows
├── api/                         # Backend API Tests (24 tests)
│   ├── test_interventions.py    # Intervention CRUD and bulk operations
│   ├── test_security.py         # Authentication and authorization
│   └── test_database_operations.py # Database integrity and constraints
├── integration/                 # End-to-End Workflow Tests (15+ tests)
│   └── workflow.test.js         # Complete user journeys
├── performance/                 # Performance and Edge Case Tests
│   └── edge-cases.test.js       # Stress testing and boundary conditions
└── TEST_COVERAGE_REPORT.md      # Detailed coverage analysis

scripts/                         # Testing and Automation Scripts
├── run_automated_tests.py       # Complete system validation
├── run_intervention_tests.py    # Intervention system focused testing
└── validate_deployment.py       # Production readiness validation
```

## 📋 Comprehensive Documentation

```
docs/                            # Technical Documentation Hub
├── COMPREHENSIVE_SYSTEM_GUIDE.md   # Complete technical documentation (NEW)
├── PRODUCTION_READINESS_ANALYSIS.md # Security and deployment analysis
├── Canvas_LMS_Integration_Guide.md # LMS integration instructions
├── Google_Classroom_Setup.md       # Google Classroom configuration
├── ENCRYPTION_SYSTEM.md            # Security and FERPA compliance
├── K12_DATASET_RESEARCH.md         # Educational research foundation
└── SCALING_GUIDE.md                # Production scaling considerations

CLAUDE.md                        # Comprehensive development guide (2000+ lines)
README.md                        # Simple project overview (NEW - simplified)
DIRECTORY_STRUCTURE.md           # This navigation guide (UPDATED)
PRODUCTION_READINESS_ASSESSMENT.md # Production deployment checklist
```

## 🚀 Production Deployment & Infrastructure

```
deployment/                      # Production Infrastructure
├── Dockerfile.production        # Optimized production container
├── docker-compose.production.yml # Production stack configuration
├── deploy.sh                    # Automated deployment script
└── nginx/                       # Production web server configuration

alembic/                         # Database Migration System
├── versions/                    # Migration scripts (6 versions)
│   ├── 22d74651db59_initial_migration_with_comprehensive_k_.py
│   ├── 1d63a289fd84_add_user_authentication_tables_complete_.py
│   └── cd8752e735e5_implement_row_level_security_policies.py
└── alembic.ini                 # Migration configuration

config/                         # System Configuration
├── health_monitor.json         # Health monitoring configuration
├── test_runner.json           # Automated testing configuration
└── cron_examples.txt          # Maintenance scheduling examples

requirements.txt                # Python dependencies (25 packages)
package.json                   # JavaScript testing dependencies
run_mvp.py                     # Production application launcher
```

## 📝 Development & Automation Tools

```
examples/                       # Sample Data & Configurations  
├── gradebooks/                # Sample CSV formats
│   └── canvas_sample.csv      # Canvas LMS example data
└── config/                    # Configuration templates

scripts/                       # Automation & Utility Scripts
├── cleanup.sh                 # Repository maintenance
├── create_demo_users.py       # Demo user generation  
├── system_health_monitor.py   # Production monitoring
├── daily_maintenance.sh       # Automated maintenance
└── security_test.py           # Security validation

logs/                          # System Logging
test-results/                  # Test execution results
```

## 🗂️ Navigation Guide

### Quick Access Commands
```bash
# 🚀 Start Application (Development)
python3 run_mvp.py                        # Auto-detects database, starts on :8001

# 🧪 Testing
npm test                                  # Frontend component tests (82 tests)
python3 -m pytest                        # Backend API tests (24 tests)  
python3 scripts/run_automated_tests.py   # Complete system validation (125+ tests)

# 🗄️ Database
alembic upgrade head                      # Apply latest migrations
python3 scripts/validate_deployment.py   # Production readiness check

# 📊 API Documentation & Health
# Start server, then visit: http://localhost:8001/docs  (Interactive API docs)
# http://localhost:8001/health                          (System health check)
```

### Key Files by Development Focus

**🎯 Bulk Intervention System (Primary Feature):**
- **Backend API**: `src/mvp/api/interventions.py` (24 endpoints, 750+ lines)
- **Frontend Components**: `src/mvp/static/js/components/bulk-*.js` (5 modular components)  
- **Selection Manager**: `src/mvp/static/js/components/selection-manager.js` (mixed selection)
- **Styles**: `src/mvp/static/css/bulk-actions.css` (1000+ lines)

**🤖 AI & Machine Learning:**
- **Production Model**: `src/models/k12_ultra_predictor.py` (81.5% AUC K-12 model)
- **Explainable AI**: `src/models/k12_explainable_ai.py` (risk factor analysis)
- **Feature Engineering**: `src/models/k12_feature_engineering.py` (40-feature pipeline)
- **Model Artifacts**: `results/models/k12/` (trained models and metadata)

**🏗️ Core Architecture:**
- **API Routers**: `src/mvp/api/` (6 specialized modules)
- **Database Layer**: `src/mvp/database.py` (PostgreSQL/SQLite hybrid)
- **ORM Models**: `src/mvp/models.py` (6 production tables)
- **Web Interface**: `src/mvp/templates/index.html` (comprehensive UI)

**📚 Integration Systems:**
- **Canvas LMS**: `src/integrations/canvas_lms.py` + `src/mvp/api/canvas_endpoints.py`
- **PowerSchool**: `src/integrations/powerschool_sis.py` + `src/mvp/api/powerschool_endpoints.py`  
- **Google Classroom**: `src/integrations/google_classroom.py` + `src/mvp/api/google_classroom_v2.py`

### Configuration & Documentation Files

**📋 Essential Documentation:**
- **README.md**: Simple project overview (quick start)
- **CLAUDE.md**: Comprehensive development guide (2000+ lines)
- **docs/COMPREHENSIVE_SYSTEM_GUIDE.md**: Complete technical documentation (NEW)
- **docs/PRODUCTION_READINESS_ANALYSIS.md**: Security checklist and deployment guide

**⚙️ Configuration:**
- **Environment**: `.env.production` (template), `.env` (local - create from template)
- **Dependencies**: `requirements.txt` (Python), `package.json` (JavaScript testing)
- **Database**: `alembic.ini` (migrations), `alembic/versions/` (schema evolution)

**🧪 Testing & Quality:**
- **Test Reports**: `tests/TEST_COVERAGE_REPORT.md` (125+ test breakdown)
- **Test Runner**: `scripts/run_automated_tests.py` (comprehensive validation)
- **Security Tests**: `scripts/security_test.py` (FERPA compliance validation)

### Development Workflow Navigation

**🎯 For New Features:**
1. **Backend**: Add endpoint to appropriate `src/mvp/api/*.py` router
2. **Frontend**: Create component in `src/mvp/static/js/components/`
3. **Tests**: Add tests in `tests/components/` and `tests/api/`
4. **Documentation**: Update `CLAUDE.md` with new patterns

**🐛 For Bug Fixes:**
1. **Reproduce**: Use `python3 run_mvp.py` and browser dev tools
2. **Debug**: Check browser console and server logs
3. **Test**: Run relevant test suite (`npm test` or `python3 -m pytest`)
4. **Validate**: Run `scripts/run_automated_tests.py` before commit

**🚀 For Deployment:**
1. **Validation**: Run `scripts/validate_deployment.py` 
2. **Security**: Check `docs/PRODUCTION_READINESS_ANALYSIS.md`
3. **Deploy**: Use `./deployment/deploy.sh --environment production`
4. **Monitor**: Check health at `/health` endpoint

## 🧹 Repository Maintenance

### Architecture Design Principles
- **📦 Modular API Design**: 6 specialized routers for easy debugging and testing
- **🧪 Component Isolation**: 11 JavaScript components with independent testing
- **🔄 Real-Time Architecture**: Database changes reflect immediately without manual refresh
- **🎯 Production Ready**: Docker deployment with PostgreSQL and comprehensive security
- **📊 Evidence-Based**: K-12 model trained on educational research and synthetic data

### Recent Major Improvements
- **✅ Bulk Intervention Management**: Complete workflow with mixed selection (December 2024)
- **✅ Real-Time UI Updates**: Eliminated manual page refreshes across entire system  
- **✅ Modular API Structure**: Split monolithic API into 6 focused routers for easier debugging
- **✅ Comprehensive Testing**: 125+ tests covering components, API, and integration workflows
- **✅ Production Security**: FERPA-compliant encryption, audit logging, and security analysis

*Last updated: December 2024 - Post Bulk Intervention Management System Completion*