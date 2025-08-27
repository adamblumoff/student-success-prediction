# 🎓 Student Success Prediction System

An AI-powered platform that helps K-12 educators identify at-risk students early and implement targeted interventions to improve student outcomes. Now featuring **GPT-5-nano enhanced AI insights** for personalized student recommendations.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python3 run_mvp.py

# Open browser to http://localhost:8001
# Default API key: dev-key-change-me
```

## ✨ What It Does

- **🤖 AI Risk Prediction**: Identifies students at risk using 81.5% AUC K-12 specialized model
- **🧠 GPT-5-Nano AI Insights**: Personalized recommendations with intelligent caching for cost savings
- **📊 Explainable AI**: Shows why students are at risk with detailed, formatted explanations
- **🎯 Intervention Management**: Create and track interventions with bulk operations
- **📈 Real-Time Dashboard**: Live analytics and progress monitoring
- **📚 Multi-Platform**: Works with Canvas LMS and generic CSV gradebook formats

## 📊 How It Works

1. **Upload**: Canvas LMS gradebook or CSV file
2. **Analyze**: AI processes student data and predicts risk levels  
3. **Generate AI Insights**: Click "Generate AI Insights" for GPT-5-nano personalized recommendations
4. **Explain**: Click "Explain Prediction" to see detailed risk factors
5. **Intervene**: Create targeted interventions for at-risk students
6. **Track**: Monitor progress with real-time updates

## 🎯 Key Features

### 🧠 GPT-5-Nano Enhanced AI Insights
- **Personalized Recommendations**: Adaptive prompts based on individual student profiles
- **Intelligent Caching**: Saves money by caching insights until student data changes
- **Structured Formatting**: Beautiful cards with bullet points and expandable layout
- **Intervention-Aware**: Recommendations consider existing interventions to avoid duplication
- **Auto-Display**: Cached insights appear immediately, new insights generated on demand

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
- **PostgreSQL/SQLite**: Hybrid database support for development and production

## 🛠️ Technical Stack

- **Backend**: Python/FastAPI with PostgreSQL
- **Frontend**: JavaScript with modular components
- **ML**: Neural Network (81.5% AUC) with explainable AI
- **Testing**: 125+ tests covering components and API

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)**: Complete development guide
- **[docs/](docs/)**: Technical documentation and guides
- **[PRODUCTION_READINESS_ANALYSIS.md](PRODUCTION_READINESS_ANALYSIS.md)**: Security checklist

---

**Ready to help students succeed with AI-powered insights!** 🎯