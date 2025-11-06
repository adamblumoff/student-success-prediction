# 🎓 Student Success Prediction System

An AI-powered platform that helps K-12 educators identify at-risk students early and implement targeted interventions to improve student outcomes. Features **GPT-enhanced AI insights** with database persistence and intelligent caching for personalized student recommendations.

## 🏆 Production Status

- **✅ Production Ready**: Deployed on Railway with PostgreSQL
- **✅ FERPA Compliant**: Full encryption and audit logging
- **✅ Security Hardened**: Comprehensive security policies enforced
- **✅ CI/CD Pipeline**: GitHub Actions with automated testing
- **✅ Demo Ready**: Reliable sample data loading for presentations

## 🚀 Quick Start

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Configure PostgreSQL (or supply DATABASE_URL)
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export DB_NAME=student_success

# Start the application (PostgreSQL required)
python3 run_mvp.py

# Open browser to http://localhost:8001
# Default API key: dev-key-change-me
```

### Production (Railway)
```bash
# Live Application: https://student-success-prediction-production.up.railway.app/
# Deploys automatically on push to master branch
# Configure environment variables in Railway dashboard:
MVP_API_KEY=<32+ character secure key>
SESSION_SECRET=<64+ character secure key>
DATABASE_ENCRYPTION_KEY=<32+ character key>
ENVIRONMENT=production
```

## ✨ What It Does

- **🤖 AI Risk Prediction**: Identifies students at risk using 81.5% AUC K-12 specialized neural network
- **🧠 GPT AI Insights**: Database-backed personalized recommendations with intelligent caching
- **📊 Explainable AI**: Shows why students are at risk with detailed, actionable explanations
- **🎯 Intervention Management**: Create and track interventions with real-time status updates
- **📈 Live Dashboard**: Real-time analytics and progress monitoring without page refreshes
- **📚 Multi-Platform**: Canvas LMS, PowerSchool SIS, Google Classroom, and generic CSV support

## 📊 How It Works

1. **Upload**: Canvas LMS gradebook, PowerSchool export, or CSV file
2. **Analyze**: K-12 specialized AI processes student data and predicts risk levels  
3. **Generate AI Insights**: GPT analyzes actual student data for personalized recommendations
4. **Explain**: View detailed risk factors and protective factors with confidence scores
5. **Intervene**: Create and assign targeted interventions with status tracking
6. **Monitor**: Track progress with real-time dashboard updates and intervention outcomes

## 🎯 Key Features

### 🧠 GPT-Enhanced AI Insights
- **Database Integration**: Uses actual student records stored in database, not sample data
- **Smart Caching**: Database-backed caching with automatic invalidation on data changes
- **Emma Johnson Format**: Exactly 3 concise, actionable recommendations per student
- **Intervention-Aware**: Considers existing interventions to build upon current efforts
- **Performance Tracking**: Cache hits and generation time monitoring for optimization

### Individual & Bulk Operations  
- Create interventions for single or multiple students
- Update status, assign staff, track outcomes
- Mixed selection (students + interventions)
- Real-time updates without page refresh

### AI Risk Prediction
- High/Medium/Low risk categories with confidence scoring
- 81.5% AUC K-12 specialized neural network model
- Risk and protective factor identification
- Grade-appropriate explanations (K-5, 6-8, 9-12)

### Integration Support
- **Canvas LMS**: Direct gradebook import with auto-format detection
- **Generic CSV**: Any CSV format with student IDs and grades
- **PostgreSQL-Only**: Single database backend across environments

## 🛠️ Technical Stack

- **Backend**: Python/FastAPI with modular API architecture (6 specialized routers)
- **Database**: PostgreSQL across environments with SSL enforcement in production
- **Frontend**: Modern JavaScript with 11+ modular components and real-time updates
- **ML**: K-12 specialized neural network (81.5% AUC) with explainable AI
- **GPT Integration**: OpenAI API with database persistence and intelligent caching
- **Testing**: 125+ comprehensive tests covering components, API, and integration workflows

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)**: Comprehensive development guide (2000+ lines)
- **[DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)**: Repository navigation and architecture
- **[docs/](docs/)**: Technical documentation, integration guides, and system analysis
- **[PRODUCTION_READINESS_ASSESSMENT.md](PRODUCTION_READINESS_ASSESSMENT.md)**: Security and deployment checklist

---

**Ready to help students succeed with AI-powered insights!** 🎯
