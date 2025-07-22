# Student Success Prediction System

A comprehensive machine learning system for predicting student success and providing early intervention recommendations using the Open University Learning Analytics Dataset (OULAD). Features enterprise-ready database integration, REST API, and real-time prediction capabilities.

## 🎯 Project Overview

This project builds an intelligent early warning system that can:
- **Predict student outcomes** within the first 3-4 weeks of a course (89.4% AUC)
- **Identify at-risk students** before they drop out or fail
- **Provide personalized intervention recommendations** for educators
- **Offer actionable insights** through REST API and interactive dashboards
- **Scale to thousands of students** with PostgreSQL database backend

## 📊 Key Results

- **89.4% AUC** for binary classification (Pass/Fail prediction)
- **77% F1-Score** for multi-class classification (Pass/Fail/Distinction/Withdrawn)
- **8.4ms API response time** for real-time predictions
- **Enterprise database** integration with PostgreSQL + SQLite fallback
- **32,593 students** successfully processed and analyzed
- **Early prediction** capability using only 28 days of VLE data and 70 days of assessment data

## 🗂️ Project Structure

```
student-success-prediction/
├── data/
│   ├── raw/                           # Original OULAD dataset
│   └── processed/                     # Engineered features
├── src/
│   ├── api/
│   │   └── student_success_api.py     # Production FastAPI server
│   ├── database/
│   │   ├── __init__.py               # Database package
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   └── connection.py             # Database connection management
│   ├── models/
│   │   ├── train_models.py           # Model training pipeline
│   │   └── intervention_system.py    # Intervention recommendations
│   ├── dashboard/
│   │   ├── cli_dashboard.py          # Command-line dashboard
│   │   └── teacher_dashboard.py      # Streamlit web dashboard
│   └── data/
│       └── download.py               # Data download utilities
├── scripts/
│   ├── schema.sql                    # PostgreSQL database schema
│   └── migrate_csv_to_db.py          # CSV to database migration
├── notebooks/
│   ├── 01_data_exploration.ipynb     # Data analysis & insights
│   ├── 02_feature_engineering.ipynb  # Feature creation
│   └── 03_predictive_modeling.ipynb  # Model development
├── tests/
│   └── integration/                  # Integration tests
├── docs/
│   ├── business_proposal.md          # Business case & ROI analysis
│   └── setup/
│       ├── DATABASE_SETUP.md         # Database setup guide
│       └── TESTING_SUMMARY.md        # Testing documentation
├── results/
│   ├── models/                       # Trained models (.pkl files)
│   ├── figures/                      # Visualizations
│   └── reports/                      # Analysis reports
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/student-success-prediction.git
cd student-success-prediction

# Install dependencies
pip install -r requirements.txt

# Install database dependencies (optional, for PostgreSQL)
pip install sqlalchemy psycopg2-binary alembic
```

### 2. Database Setup (Optional)

For production deployment with PostgreSQL:
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb student_success_db

# Run schema creation
psql -f scripts/schema.sql student_success_db

# Set environment variable
export DATABASE_URL=postgresql://user:password@localhost/student_success_db
```

For development, the system automatically uses SQLite fallback.

### 3. Data Setup

Download the OULAD dataset:
```bash
python src/data/download.py
```

Visit https://analyse.kmi.open.ac.uk/open_dataset and download these files to `data/raw/`:
- studentInfo.csv, courses.csv, assessments.csv, studentAssessment.csv
- vle.csv, studentVle.csv, studentRegistration.csv

### 4. Run the System

```bash
# Option A: Use the REST API (Recommended)
python src/api/student_success_api.py

# Option B: Run analysis notebooks
jupyter notebook notebooks/01_data_exploration.ipynb

# Option C: Train models directly
python src/models/train_models.py

# Option D: Launch dashboard
python src/dashboard/teacher_dashboard.py
```

## 📈 Key Features

### REST API (Production-Ready)
- **FastAPI backend** with automatic OpenAPI documentation
- **8.4ms response time** for real-time predictions
- **Database persistence** for all predictions and interventions
- **Authentication** with Bearer token security
- **Batch processing** support for multiple students
- **Health monitoring** and system status endpoints

### Database Integration
- **PostgreSQL** for production with automatic fallback to SQLite
- **6 normalized tables** with proper relationships and constraints
- **Persistent storage** of predictions, interventions, and outcomes
- **Analytics queries** for risk distribution and student history
- **Migration tools** for loading 32K+ student records

### Data Analysis & Insights
- **32,593 student records** across 7 courses
- **10.6M VLE interactions** and **174K assessments**
- **Success rate: 47.2%** (Pass + Distinction)
- **Withdrawal rate: 31.2%** (primary prediction target)

### Predictive Features (31 total)
- **Demographic features (10)**: Age, gender, education, region, etc.
- **Early VLE engagement (10)**: First 28 days of interaction patterns
- **Early assessment performance (11)**: First 70 days of assessment data

### Machine Learning Models
- **Binary Classification**: Pass/Fail prediction (85% AUC)
- **Multi-class Classification**: All outcomes (77% F1-Score)
- **Algorithms**: Gradient Boosting, Random Forest, XGBoost, Logistic Regression

### Intervention System
- **Risk Assessment**: Low/Medium/High risk categorization
- **Personalized Recommendations**: Targeted interventions based on risk factors
- **Priority Scoring**: Critical/High/Medium/Low intervention priorities
- **Resource Allocation**: Cost-effective intervention strategies

## 📊 Dashboard Features

### Overview Tab
- Real-time student metrics
- Risk distribution visualization
- Success rate tracking
- Outcome vs prediction analysis

### At-Risk Students Tab
- Highest risk student identification
- Risk factor analysis
- Interactive risk gauges
- Detailed student profiles

### Interventions Tab
- Personalized intervention recommendations
- Resource requirements
- Timeline and cost estimates
- Priority-based action plans

### Analytics Tab
- Feature importance analysis
- Correlation studies
- Engagement vs performance trends
- Advanced statistical insights

## 🎯 Intervention Recommendations

The system provides four types of interventions:

### 1. **Immediate Interventions**
- Urgent academic advisor meetings
- Crisis intervention protocols
- Emergency support services

### 2. **Academic Support**
- Tutoring programs
- Study skills workshops
- Assessment strategy training
- Writing center support

### 3. **Engagement Interventions**
- VLE gamification
- Peer learning groups
- Interactive content delivery
- Motivation enhancement

### 4. **Demographic Support**
- Age-appropriate learning resources
- Technology training for mature learners
- Cultural adaptation support
- Accessibility accommodations

## 📊 Model Performance

### Binary Classification (Pass/Fail)
- **Gradient Boosting**: 85.0% AUC, 81.3% Accuracy
- **Random Forest**: 83.9% AUC, 80.7% Accuracy
- **XGBoost**: 83.7% AUC, 80.6% Accuracy
- **Logistic Regression**: 80.4% AUC, 77.5% Accuracy

### Multi-class Classification (All Outcomes)
- **Gradient Boosting**: 77.2% F1-Score, 78.6% Accuracy
- **XGBoost**: 76.9% F1-Score, 78.0% Accuracy
- **Random Forest**: 76.5% F1-Score, 77.8% Accuracy
- **Logistic Regression**: 72.2% F1-Score, 75.9% Accuracy

### Top Predictive Features
1. **Early Average Score** (30.8% importance)
2. **Early Assessment Count** (24.8% importance)
3. **Early Total Weight** (9.1% importance)
4. **Early Minimum Score** (6.6% importance)
5. **Study Credits** (6.0% importance)

## 🔧 Technical Implementation

### Data Pipeline
1. **Data Ingestion**: OULAD CSV files → Pandas DataFrames
2. **Feature Engineering**: Time-windowed aggregations and derived metrics
3. **Model Training**: Scikit-learn pipeline with cross-validation
4. **Prediction**: Real-time risk assessment and intervention recommendations

### Technology Stack
- **Data Processing**: Pandas, NumPy
- **Machine Learning**: Scikit-learn, XGBoost
- **Visualization**: Matplotlib, Seaborn, Plotly
- **Dashboard**: Streamlit
- **Deployment**: Docker-ready, cloud-compatible

## 🎓 Educational Impact

### For Educators
- **Early Warning**: Identify at-risk students in weeks 3-4
- **Intervention Guidance**: Specific, actionable recommendations
- **Resource Optimization**: Efficient allocation of support services
- **Progress Monitoring**: Real-time dashboard for course oversight

### For Students
- **Timely Support**: Interventions before it's too late
- **Personalized Help**: Targeted assistance based on individual needs
- **Improved Outcomes**: Higher success rates through early intervention
- **Reduced Dropouts**: Proactive support to prevent withdrawal

### For Institutions
- **Cost Reduction**: Efficient use of support resources
- **Retention Improvement**: Higher student completion rates
- **Data-Driven Decisions**: Evidence-based educational policies
- **Scalable Solution**: Applicable across multiple courses and programs

## 🚀 Future Enhancements

### Model Improvements
- **Deep Learning**: Neural networks for complex pattern recognition
- **Time Series**: Temporal modeling for dynamic risk assessment
- **Ensemble Methods**: Combining multiple models for better accuracy
- **Explainable AI**: Enhanced interpretability for educators

### Feature Expansion
- **Social Learning**: Peer interaction and collaboration metrics
- **Learning Pathways**: Sequential activity pattern analysis
- **External Factors**: Demographics, socioeconomic indicators
- **Real-time Feedback**: Immediate intervention triggers

### Dashboard Enhancements
- **Mobile App**: Responsive design for mobile devices
- **Automated Alerts**: Push notifications for critical situations
- **Integration**: LMS and SIS system connectivity
- **Reporting**: Comprehensive analytics and reporting tools

## 📋 Usage Examples

### Command Line
```bash
# Train models
python src/models/train_models.py

# Generate intervention report
python src/models/intervention_system.py

# Launch dashboard
python run_dashboard.py
```

### Python API
```python
from src.models.intervention_system import InterventionRecommendationSystem

# Initialize system
system = InterventionRecommendationSystem()

# Assess student risk
risk_assessment = system.assess_student_risk(student_data)

# Get intervention recommendations
recommendations = system.get_intervention_recommendations(student_data)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 References

- [Open University Learning Analytics Dataset (OULAD)](https://analyse.kmi.open.ac.uk/open_dataset)
- Kuzilek, J., Hlosta, M., Zdrahal, Z. (2017). Open University Learning Analytics dataset Scientific Data 4:170171
- [Scikit-learn Documentation](https://scikit-learn.org/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 📧 Contact

For questions, suggestions, or collaborations, please open an issue or contact the maintainers.

---

**🎯 Empowering educators with data-driven insights for student success!**