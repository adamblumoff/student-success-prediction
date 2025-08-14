# 🎓 Student Success Prediction System

An AI-powered platform that helps K-12 educators identify at-risk students early and implement targeted interventions to improve student outcomes.

## 🚀 Quick Start

### Development (SQLite)
```bash
# Start with automatic SQLite fallback
python3 run_mvp.py

# Open your browser to http://localhost:8001
```

### Production (Docker)
```bash
# ⚠️  IMPORTANT: Review security checklist before production deployment
# See docs/PRODUCTION_READINESS_ANALYSIS.md for critical security fixes

# Copy and configure environment
cp .env.production .env
nano .env  # Update DATABASE_URL and API keys

# Deploy with Docker
./deploy.sh --environment production

# Verify deployment
curl http://localhost:8001/health
```

## 🛡️ Production Readiness Status

**Current Status:** 80% ready for single K-12 district deployment  
**Last Assessment:** December 2024  

### ✅ Strengths
- Comprehensive ML model (81.5% AUC)
- FERPA-compliant encryption system
- Extensive test coverage (116 tests passing)
- Production-ready Docker deployment

### ⚠️ Critical Issues (Must Fix Before Production)
- **Security**: Default database credentials, hardcoded demo passwords
- **Compliance**: Encryption disabled by default
- **Testing**: 24 failing security tests
- **See**: `docs/PRODUCTION_READINESS_ANALYSIS.md` for complete details

## ✨ Features

- **🤖 AI-Powered Risk Prediction**: Identifies students at risk of academic failure using 31 engineered features
- **📊 Explainable AI**: Provides detailed explanations for each prediction with risk factors and protective factors
- **🎯 Comprehensive Intervention Management**: Full-featured intervention tracking with bulk operations
  - **Individual & Bulk Creation**: Create interventions for single students or multiple students at once
  - **Mixed Selection**: Select both students and interventions simultaneously for complex operations
  - **Status Management**: Update, assign, and track intervention progress with real-time updates
  - **Cancellation with Deletion**: Permanently remove cancelled interventions with confirmation
- **📈 Real-Time Analytics**: Comprehensive dashboard with advanced analytics and ROI calculations
- **🏫 Multi-Tenant Architecture**: Supports multiple school districts with data isolation
- **📚 Universal Integration**: Canvas LMS, PowerSchool SIS, Google Classroom, and generic CSV formats
- **🔔 Real-Time Notifications**: WebSocket-based alert system for at-risk students
- **🔒 FERPA Compliant**: Audit logging and security features for educational data privacy

## 📊 How It Works

1. **Upload Data**: CSV file with student information (ID, scores, engagement metrics)
2. **AI Analysis**: Machine learning models analyze 31 features across demographics, engagement, and performance  
3. **Risk Prediction**: Students classified as High/Medium/Low risk with confidence scores
4. **Explanations**: Detailed breakdown of risk factors and protective elements
5. **Intervention Management**: Create, track, and manage interventions with comprehensive bulk operations
6. **Real-Time Updates**: All changes reflect immediately without page refreshes

## 🎯 Supported Data Formats

- **Canvas LMS**: Direct CSV exports from Canvas gradebooks
- **Generic CSV**: Any CSV with student ID and performance/engagement data
- **Sample Data**: Built-in demo data for testing

### Required CSV Columns (minimum):
- Student ID or identifier
- At least one score/grade column  
- Any engagement metrics (optional but improves accuracy)

## 🧠 Machine Learning Models

- **Binary Classification**: 89.4% AUC for Pass/Fail prediction
- **Multi-class Classification**: 77% F1-Score for detailed outcomes
- **Feature Engineering**: 31 carefully crafted features
- **Real-time Speed**: Predictions in under 100ms

### Top Predictive Features:
1. Early assignment scores (22.3% importance)
2. Platform engagement clicks (18.7% importance) 
3. Previous course attempts (12.4% importance)
4. Active study days (11.2% importance)
5. Registration timing (9.8% importance)

## 💡 Intervention Management System

### Individual Interventions
Create targeted interventions with detailed tracking:
- **8 Intervention Types**: Academic, Attendance, Behavioral, Engagement, Family, College/Career, Health, Technology
- **Priority Levels**: Low, Medium, High, Critical with visual indicators
- **Status Tracking**: Pending → In Progress → Completed/Cancelled
- **Staff Assignment**: Assign interventions to specific team members
- **Due Dates**: Set and track intervention deadlines
- **Outcome Recording**: Document results and notes for completed interventions

### Bulk Operations
Efficiently manage multiple interventions:
- **Bulk Creation**: Create interventions for multiple students simultaneously
- **Mixed Selection**: Select both students and interventions at once for complex operations
- **Bulk Status Updates**: Update multiple interventions' status, assignments, or outcomes
- **Bulk Deletion**: Remove multiple interventions with confirmation
- **Real-Time Updates**: All changes reflect immediately across the interface

### Smart Recommendations
AI-powered intervention suggestions based on risk factors:
- **High Risk**: Academic support, one-on-one mentoring, study skills workshops
- **Medium Risk**: Peer study groups, time management resources, regular check-ins  
- **Low Risk**: Motivational resources, advanced learning opportunities

## 🛠️ Technical Details

### Requirements
```bash
pip install -r requirements.txt
```

### Architecture
- **Frontend**: HTML/CSS/JavaScript web interface with explainable AI components
- **Backend**: FastAPI with PostgreSQL/SQLite hybrid database layer
- **ML Models**: XGBoost with comprehensive feature engineering
- **Database**: Production PostgreSQL with development SQLite fallback
- **Security**: API key authentication, rate limiting, and audit logging

### Project Structure
```
├── src/mvp/              # Core application
├── alembic/              # Database migrations
├── deployment/           # Deployment tools
├── docs/                 # Documentation
├── results/models/       # Trained ML models
└── run_mvp.py           # Application entry point
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed folder organization.

## 📈 Usage Examples

### Web Interface
1. Go to http://localhost:8001
2. Click "Try with sample data" for a demo or upload your own CSV file
3. View risk predictions and click "Explain Prediction" for details
4. **Create Interventions**: Click "Create Intervention" for individual students
5. **Bulk Operations**: Enable "Bulk Actions" to:
   - Select multiple students using checkboxes
   - Create interventions for multiple students at once
   - Update, assign, or delete multiple interventions
   - Use mixed selection for complex operations

### API Usage (Advanced)
```python
import requests

# Upload and analyze CSV
files = {'file': open('student_data.csv', 'rb')}
response = requests.post(
    'http://localhost:8001/api/mvp/analyze',
    files=files,
    headers={'Authorization': 'Bearer dev-key-change-me'}
)

results = response.json()
print(f"High risk students: {results['summary']['high_risk']}")
```

## 🔍 Understanding Results

### Risk Categories
- **High Risk (>70%)**: Needs immediate intervention
- **Medium Risk (40-70%)**: Monitor closely, provide support
- **Low Risk (<40%)**: On track for success

### Explanation Features
- **Risk Factors**: Specific areas of concern for each student
- **Protective Factors**: Strengths that support success
- **Confidence Score**: How certain the AI is about the prediction
- **Recommendations**: Specific actions educators can take

## 🎓 Educational Use Cases

- **Early Warning Systems**: Identify struggling students before it's too late
- **Resource Allocation**: Focus support on students who need it most  
- **Intervention Planning**: Data-driven strategies for student support
- **Academic Analytics**: Understand patterns in student success

## 🔐 Security & Privacy

- Simple API key authentication
- File upload validation (CSV only, 10MB max)
- No sensitive data stored permanently
- Rate limiting to prevent abuse

## 📄 Data Sources

Built using the Open University Learning Analytics Dataset (OULAD):
- 32,593 students across multiple courses
- Demographics, VLE interactions, and assessment data
- Proven benchmark for educational ML research

---

**🎯 Ready to help students succeed with AI-powered insights!**