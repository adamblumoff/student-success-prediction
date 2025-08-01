# Repository Directory Structure

This document provides a clear overview of the repository organization for easy navigation.

## 🏗️ Core Application Structure

```
src/
├── mvp/                     # MVP Web Application
│   ├── mvp_api.py          # Main API entry point (modular)
│   ├── api/                # Modular API endpoints
│   │   ├── core.py         # Core MVP endpoints (/api/mvp/*)
│   │   ├── canvas_endpoints.py     # Canvas LMS (/api/lms/*)
│   │   ├── powerschool_endpoints.py # PowerSchool SIS (/api/sis/*)
│   │   └── combined_endpoints.py   # Combined integration (/api/integration/*)
│   ├── database.py         # Database connection & ORM
│   ├── models.py           # SQLAlchemy models
│   ├── simple_auth.py      # Authentication system
│   ├── static/             # Web assets (CSS, JS)
│   └── templates/          # HTML templates
├── models/                 # Machine Learning Models
│   ├── intervention_system.py      # Original ML system
│   ├── k12_*.py           # K-12 specialized models
│   └── explainable_ai.py  # Explainable AI components
├── integrations/          # External System Integrations
│   ├── canvas_lms.py      # Canvas LMS integration
│   ├── powerschool_sis.py # PowerSchool SIS integration
│   └── combined_integration.py # Combined system integration
└── data/
    └── download.py        # Data acquisition utilities
```

## 📊 Data & Models

```
data/
├── raw/                   # Original datasets (OULAD)
├── processed/             # Engineered features
└── k12_synthetic/         # Generated K-12 data

results/
├── models/                # Trained model artifacts
│   ├── *.pkl             # Production models
│   └── k12/              # K-12 specialized models
└── reports/              # Analysis reports
```

## 🧪 Testing & Quality

```
tests/
├── unit/                 # Unit tests
├── performance/          # Performance tests
├── fixtures/             # Test data and mocks
└── run_tests.py         # Test runner

run_all_tests.py         # Complete test suite
```

## 📋 Documentation

```
docs/                     # Technical documentation
├── business_proposal.md # Business case
├── SECURITY.md          # Security guidelines
├── deployment/          # Deployment guides
└── setup/               # Setup instructions

CLAUDE.md                # Development guidelines
README.md                # Project overview
```

## 🚀 Deployment & Configuration

```
deployment/              # Deployment configurations
├── docker-compose.yml   # Local deployment
├── sql/                 # Database schemas
└── *.sh                # Setup scripts

alembic/                 # Database migrations
requirements.txt         # Python dependencies
run_mvp.py              # Application launcher
```

## 📝 Development Tools

```
examples/               # Sample data and configurations
notebooks/              # Jupyter analysis notebooks
scripts/                # Utility scripts
```

## 🗂️ Navigation Tips

### Quick Access Commands
```bash
# Start the application
python3 run_mvp.py

# Run tests
python3 run_all_tests.py

# Database migrations
alembic upgrade head

# View API documentation
# Start server, then visit: http://localhost:8001/docs
```

### Key Files for Development
- **API Endpoints**: `src/mvp/api/` (modular structure)
- **ML Models**: `src/models/` (especially `k12_ultra_predictor.py`)
- **Database**: `src/mvp/database.py` and `src/mvp/models.py`
- **Web UI**: `src/mvp/templates/index.html`
- **Integration APIs**: `src/integrations/`

### Key Files for Configuration
- **Environment**: `.env` (create from examples)
- **Dependencies**: `requirements.txt`
- **Database**: `alembic.ini` and `alembic/`
- **Development Guidelines**: `CLAUDE.md`

## 🧹 Maintenance

This structure is designed for:
- **Easy Navigation**: Logical grouping by function
- **Scalability**: Modular API design
- **Debugging**: Isolated components
- **Testing**: Comprehensive test coverage
- **Documentation**: Clear guidance for developers

Last updated: January 2025