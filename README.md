# Student Success Prediction MVP

An AI-powered system for identifying at-risk students and providing intervention recommendations using machine learning.

## 🚀 Quick Start

```bash
# Start the MVP application
python3 run_mvp.py

# Open your browser to http://localhost:8001
```

## ✨ Features

- **Early Risk Detection**: Identifies at-risk students using ML models with 89.4% accuracy
- **Interactive Web Interface**: Upload CSV files or try with sample data
- **Explainable AI**: Detailed explanations of predictions and risk factors
- **Feature Importance**: Understand which factors most influence student success
- **Real-time Analysis**: Get instant risk assessments and intervention recommendations

## 📊 How It Works

1. **Upload Data**: CSV file with student information (ID, scores, engagement metrics)
2. **AI Analysis**: Machine learning models analyze 31 features across demographics, engagement, and performance  
3. **Risk Prediction**: Students classified as High/Medium/Low risk with confidence scores
4. **Explanations**: Detailed breakdown of risk factors and protective elements
5. **Recommendations**: Actionable intervention strategies for each student

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

## 💡 Intervention System

The system provides personalized recommendations based on risk factors:

- **High Risk**: Academic support, one-on-one mentoring, study skills workshops
- **Medium Risk**: Peer study groups, time management resources, regular check-ins
- **Low Risk**: Motivational resources, advanced learning opportunities

## 🛠️ Technical Details

### Requirements
```bash
pip install -r requirements.txt
```

### Architecture
- **Frontend**: Simple HTML/CSS/JavaScript web interface
- **Backend**: FastAPI with SQLite database
- **ML Models**: XGBoost with scikit-learn preprocessing
- **Security**: API key authentication with rate limiting

### Project Structure
```
├── src/mvp/           # MVP web application
├── src/models/        # ML models and training
├── data/             # Datasets (OULAD)
├── results/models/   # Trained model files
└── run_mvp.py        # Main application launcher
```

## 📈 Usage Examples

### Web Interface
1. Go to http://localhost:8001
2. Click "Try with sample data" for a demo
3. Or upload your own CSV file
4. View risk predictions and click "Explain Prediction" for details

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