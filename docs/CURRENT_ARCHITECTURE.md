# Current System Architecture

## Overview

The Student Success Prediction System is a modern, modular K-12 educational AI platform built with Python/FastAPI backend, JavaScript frontend, and hybrid PostgreSQL/SQLite database architecture. The system features GPT-enhanced AI insights, real-time intervention management, and comprehensive integration capabilities.

**Last Updated**: August 2025
**Production Readiness**: 80% for single district, 40% for multi-district

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Layer (Browser)                      │
├─────────────────────────────────────────────────────────────────────┤
│  Modern JavaScript Frontend (11 Modular Components)                │
│  ├─ Analysis Component (GPT Insights Integration)                  │
│  ├─ Dashboard (Real-time Analytics)                                │
│  ├─ Interventions (CRUD + Bulk Operations)                        │
│  ├─ File Upload (CSV Processing)                                   │
│  └─ Notification System                                            │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Application Server                     │
├─────────────────────────────────────────────────────────────────────┤
│  Modular Router Architecture (6 Specialized Routers)               │
│  ├─ Core MVP (/api/mvp/*)                                         │
│  ├─ GPT Enhanced (/api/mvp/gpt-insights/*)                        │
│  ├─ Interventions (/api/interventions/*)                          │
│  ├─ Canvas LMS (/api/lms/*)                                       │
│  ├─ PowerSchool (/api/sis/*)                                      │
│  └─ Google Classroom (/api/google/*)                              │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕
┌─────────────────────────────────────────────────────────────────────┐
│                        Service Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│  ├─ GPT OSS Service (OpenAI API Integration)                      │
│  ├─ GPT Cache Service (Database-backed Caching)                   │
│  ├─ Metrics Aggregator (Analytics)                                │
│  ├─ Context Builder (Prompt Engineering)                          │
│  └─ ML Model Services (K-12 Specialized)                          │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    Machine Learning Pipeline                       │
├─────────────────────────────────────────────────────────────────────┤
│  K-12 Ultra Predictor (81.5% AUC Neural Network)                  │
│  ├─ 40 Optimized Features (from 59 engineered)                    │
│  ├─ Grade-band Specific Analysis (K-5, 6-8, 9-12)                 │
│  ├─ Explainable AI (Risk/Protective Factors)                      │
│  └─ Intervention Recommendations                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    Database Layer (Hybrid)                         │
├─────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (Production) / SQLite (Development)                    │
│  ├─ 10 Tables: students, predictions, interventions, etc.         │
│  ├─ GPT Insights Table (Caching & Metadata)                       │
│  ├─ Alembic Migrations (6 Migration Scripts)                      │
│  └─ Row-Level Security & Encryption Support                       │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕
┌─────────────────────────────────────────────────────────────────────┐
│                    External Integrations                           │
├─────────────────────────────────────────────────────────────────────┤
│  ├─ OpenAI API (GPT-5-nano for Student Insights)                  │
│  ├─ Canvas LMS API (Gradebook Import)                              │
│  ├─ PowerSchool SIS API (Student Data Sync)                       │
│  └─ Google Classroom API (Assignment Integration)                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Architecture

**Modern JavaScript with Component Pattern**
- **Location**: `src/mvp/static/js/components/`
- **Components**: 11 modular components with independent testing
- **State Management**: Centralized AppState with reactive updates
- **Real-time Updates**: No manual page refreshes required

**Key Components**:
```
analysis.js              # Student analysis with GPT insights
dashboard.js             # Analytics and performance metrics
interventions.js         # Intervention management with CRUD operations
file-upload.js          # CSV processing and validation
tab-navigation.js       # Navigation state management
bulk-operations-manager.js  # Bulk intervention operations
notification-system.js  # Real-time user feedback
```

**UI Framework**:
- **Styling**: `modern-style.css` + `bulk-actions.css` (1000+ lines)
- **Responsive Design**: Mobile-friendly with adaptive layouts
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Performance**: Lazy loading and efficient DOM updates

### 2. Backend Architecture

**FastAPI with Modular Router Design**
- **Main Entry**: `src/mvp/mvp_api.py` (imports all routers)
- **Router Pattern**: 6 specialized routers for different functional areas
- **Authentication**: API key-based with rate limiting
- **Error Handling**: Comprehensive error handling with structured responses

**API Routers**:
```
core.py                 # Core MVP endpoints (/api/mvp/*)
gpt_enhanced_endpoints.py  # GPT analysis endpoints
interventions.py        # Intervention management (/api/interventions/*)
canvas_endpoints.py     # Canvas LMS integration
powerschool_endpoints.py  # PowerSchool SIS integration
google_classroom_v2.py  # Google Classroom integration
```

**Benefits of Modular Design**:
- **Easier Debugging**: Each integration system isolated
- **Independent Testing**: Each router tested separately
- **Parallel Development**: Multiple developers can work simultaneously
- **Better Organization**: Related endpoints grouped logically

### 3. Service Layer

**Business Logic Services**
- **Location**: `src/mvp/services/`
- **Pattern**: Service-oriented architecture with dependency injection
- **Caching**: Intelligent caching with database persistence

**Key Services**:
```python
GPTOSSService           # OpenAI API integration with fallback handling
GPTCacheService         # Database-backed caching system
MetricsAggregator      # Analytics and performance metrics
ContextBuilder         # GPT prompt engineering for education context
GPTEnhancedPredictor   # Combined ML + GPT analysis
```

### 4. Machine Learning Pipeline

**K-12 Specialized Neural Network**
- **Model**: K12UltraPredictor with 81.5% AUC
- **Features**: 40 optimized features from K-12 educational research
- **Performance**: <100ms prediction time
- **Explainability**: Risk and protective factor identification

**Feature Categories**:
```
Demographics (24)        # Grade level, special populations, socioeconomic
Academic Performance (23)  # GPA trends, course failures, credit tracking
Engagement & Behavior (18)  # Attendance, extracurriculars, discipline
Early Warning Indicators (12)  # ABC indicators (Attendance, Behavior, Course)
Grade-Specific (8)       # Elementary reading, HS graduation tracking
```

**Model Architecture**:
- **Type**: Neural Network with Stacking Ensemble
- **Training Data**: 30,000 synthetic K-12 students with realistic patterns
- **Validation**: Cross-validated with holdout test sets
- **Deployment**: Pickle serialization with metadata tracking

### 5. Database Architecture

**Hybrid PostgreSQL/SQLite Design**
- **Production**: PostgreSQL with full ACID compliance
- **Development**: SQLite fallback for zero-config setup
- **Migration**: Alembic for schema versioning
- **Security**: Row-level security and encryption support

**Current Schema (10 Tables)**:
```sql
institutions           # Multi-tenant institution management
students              # K-12 student records with demographics
predictions           # ML model outputs and risk scores
interventions         # Intervention tracking and outcomes
gpt_insights          # GPT analysis cache and metadata (NEW)
audit_logs            # Security and compliance logging
model_metadata        # ML model versions and performance
users                 # Authentication and authorization
user_sessions         # Session management
alembic_version       # Database migration tracking
```

**GPT Insights Table (Key Innovation)**:
```sql
CREATE TABLE gpt_insights (
  id INTEGER PRIMARY KEY,
  student_id VARCHAR(100),        # Links to student record
  data_hash VARCHAR(64),          # For cache invalidation
  raw_response TEXT,              # GPT raw output
  formatted_html TEXT,            # Processed for display
  gpt_model VARCHAR(50),          # Model used (gpt-5-nano)
  tokens_used INTEGER,            # Cost tracking
  is_cached BOOLEAN,              # Performance optimization
  cache_hits INTEGER,             # Usage analytics
  created_at DATETIME,
  updated_at DATETIME
);
```

### 6. GPT Integration Architecture

**Database-Backed GPT System**
- **Model**: GPT-5-nano via OpenAI API
- **Format**: Emma Johnson format (exactly 3 recommendations)
- **Data Source**: Actual student database records, not sample data
- **Caching**: Intelligent database-backed caching with hash validation

**GPT Analysis Flow**:
```
1. Student Selection → 2. Check Cache (data_hash) → 3. Cache Hit?
                                                    ↓ No
4. Build Context from DB → 5. Call OpenAI API → 6. Process Response
                                                ↓
7. Save to gpt_insights → 8. Return Formatted HTML → 9. Display to User
```

**Cost Optimization**:
- **Smart Caching**: Cache invalidated only when student data changes
- **Batch Processing**: Multiple students analyzed efficiently
- **Token Management**: Track usage for cost control
- **Fallback Mode**: Graceful degradation if GPT unavailable

## Integration Architecture

### 1. Canvas LMS Integration

**Gradebook Processing**
- **Detection**: Auto-detects Canvas format ("Student", "ID", "Current Score")
- **Processing**: Converts to internal format with validation
- **Features**: Grade passback, assignment sync, roster management

### 2. PowerSchool SIS Integration

**Student Information System**
- **Data Sync**: Bulk student import with duplicate prevention
- **Attendance**: Real-time attendance data integration
- **Demographics**: Comprehensive student profile sync

### 3. Google Classroom Integration

**OAuth 2.0 Flow**
- **Authentication**: Secure OAuth 2.0 with refresh tokens
- **Classroom Data**: Assignment grades and class rosters
- **Real-time Sync**: Webhook-based updates

## Security Architecture

### 1. Authentication & Authorization

**API Key Authentication**
- **Development**: Default key `dev-key-change-me`
- **Production**: Environment-based secure keys
- **Rate Limiting**: 100 requests/minute, 10/minute for GPT endpoints
- **Session Management**: Database-backed user sessions

### 2. Data Protection

**FERPA Compliance**
- **Encryption**: AES-256 encryption for sensitive data (optional, disabled by default)
- **Audit Logging**: All actions logged with timestamps and user tracking
- **Data Anonymization**: PII handling with proper safeguards
- **Access Controls**: Role-based permissions

### 3. Security Best Practices

**Input Validation**
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **File Upload Validation**: CSV format validation with size limits
- **Rate Limiting**: In-memory rate limiting with IP tracking
- **Error Handling**: Generic error messages to prevent information disclosure

## Deployment Architecture

### 1. Development Deployment

**Zero-Configuration Setup**
```bash
python3 run_mvp.py  # Automatically uses SQLite, starts on :8001
```

**Features**:
- SQLite fallback database (`mvp_data.db`)
- Development API key
- Hot reloading for development
- Debug logging enabled

### 2. Production Deployment

**PostgreSQL with Docker**
```bash
# Environment setup
export DATABASE_URL="postgresql://user:pass@host/database"
export MVP_API_KEY="secure-production-key"

# Database migration
alembic upgrade head

# Start application
python3 run_mvp.py
```

**Production Features**:
- PostgreSQL with connection pooling
- Secure API key management
- SSL/HTTPS enforcement
- Production logging
- Health monitoring endpoints

### 3. Scaling Considerations

**Current Limitations**:
- **Monolithic Deployment**: Single FastAPI process
- **In-Memory Rate Limiting**: Not distributed
- **Database Single Point of Failure**: No replication
- **GPT Token Limits**: OpenAI API rate limits

**Future Scaling Options**:
- **Service Mesh**: Split into API gateway + ML service + data service
- **Redis Caching**: Distributed caching layer
- **Database Replicas**: Read/write splitting
- **Load Balancing**: Multiple application instances
- **CDN**: Static asset delivery

## Testing Architecture

**Comprehensive Test Suite (125+ Tests)**
- **Frontend**: 82 component tests using Jest
- **Backend**: 24 API tests with pytest
- **Integration**: 15+ end-to-end workflow tests
- **Performance**: Load testing with edge case scenarios

**Test Categories**:
```
tests/components/       # Frontend component tests (82 tests)
tests/api/             # Backend API tests (24 tests)
tests/integration/     # End-to-end workflows (15+ tests)
tests/performance/     # Load and stress testing
tests/models/          # ML model validation
```

## Monitoring & Observability

### 1. Health Monitoring

**System Health Endpoints**
- `/health` - Overall system status
- `/docs` - Interactive API documentation
- Database connectivity checks
- ML model availability
- GPT service status

### 2. Performance Metrics

**Key Metrics Tracked**:
- API response times
- GPT token usage and costs
- Database query performance
- Cache hit rates
- Error rates and patterns

### 3. Logging & Audit

**Structured Logging**
- Application logs with correlation IDs
- Security audit logs for compliance
- Performance metrics logging
- Error tracking and alerting

## Development Workflow

### 1. Local Development

**Quick Start**:
```bash
git clone <repository>
pip install -r requirements.txt
python3 run_mvp.py
# Access: http://localhost:8001
```

### 2. Testing Workflow

**Frontend Testing**:
```bash
npm test                    # All component tests
npm run test:watch         # Watch mode
```

**Backend Testing**:
```bash
python3 -m pytest         # All API tests
python3 scripts/run_automated_tests.py  # Full suite
```

### 3. Database Management

**Migration Commands**:
```bash
alembic upgrade head       # Apply migrations
alembic current           # Check current version
alembic downgrade base    # Reset database
```

## Future Architecture Considerations

### 1. Microservices Migration

**Potential Service Split**:
- **API Gateway**: Authentication, routing, rate limiting
- **ML Service**: Model inference and prediction
- **GPT Service**: AI analysis and insights
- **Data Service**: Database operations and caching
- **Integration Service**: External system connections

### 2. Event-Driven Architecture

**Message Queue Integration**:
- **Student Data Updates**: Event-driven cache invalidation
- **Intervention Workflows**: Async task processing
- **Notification System**: Real-time user notifications
- **Batch Processing**: Large dataset handling

### 3. Cloud-Native Deployment

**Kubernetes Architecture**:
- **Horizontal Pod Autoscaling**: Dynamic scaling based on load
- **Service Mesh**: Inter-service communication
- **Database Operators**: Managed PostgreSQL clusters
- **Monitoring Stack**: Prometheus + Grafana observability

## Summary

The current architecture represents a mature, production-ready system with:

- **Modern Stack**: FastAPI + JavaScript + PostgreSQL/SQLite
- **AI Integration**: 81.5% AUC ML model + GPT-enhanced insights
- **Modular Design**: 6 specialized API routers, 11 frontend components
- **Database Innovation**: GPT caching with intelligent invalidation
- **Comprehensive Testing**: 125+ tests covering all system areas
- **Production Features**: Security, monitoring, and deployment automation

The system is well-positioned for single-district deployment (80% production ready) and provides a solid foundation for future scaling to multi-district environments.