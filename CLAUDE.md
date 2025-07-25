# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start
```bash
# MVP (Simple educator interface)
python3 run_mvp.py                    # Port 8001, SQLite, web UI
```

### Model Operations
```bash
# Train models from scratch
python src/models/train_models.py

# Run security tests (if needed)
python3 scripts/security_test.py
```

## Architecture Overview

### Simplified MVP Architecture
The system implements a **single, focused architecture** for educational demonstrations:

**MVP Architecture** (`src/mvp/`):
- **Purpose**: Simple educator interface for quick demos and explainable AI
- **Database**: SQLite for zero-configuration setup  
- **Security**: Simple API key authentication with basic rate limiting
- **Deployment**: Single Python process (`python3 run_mvp.py`)
- **Gradebook Support**: Canvas LMS and generic CSV formats
- **Explainable AI**: Feature importance, prediction explanations, risk factor analysis

### Database Architecture

**Simple SQLite Schema**:
```sql
predictions (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    risk_score REAL,
    risk_category TEXT,
    timestamp TEXT,
    session_id TEXT
)
```

### Machine Learning Pipeline

**Feature Engineering** (31 total features):
- **Demographics** (6): Age, gender, education, region, disability status
- **Academic History** (4): Credits, previous attempts, registration timing
- **Early VLE Engagement** (10): First 28 days of interaction patterns
- **Early Assessment Performance** (11): First 70 days of assessment data

**Model Performance**:
- **Binary Classification**: 89.4% AUC (Pass/Fail prediction)
- **Multi-class Classification**: 77% F1-Score (Pass/Fail/Distinction/Withdrawn)
- **Response Time**: <100ms for real-time predictions

**Model Loading Pattern**:
```python
# Models auto-load from results/models/
intervention_system = InterventionRecommendationSystem()
risk_results = intervention_system.assess_student_risk(student_df)
explanations = intervention_system.get_explainable_predictions(student_df)
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
POST /api/mvp/analyze            # CSV upload and analysis
POST /api/mvp/analyze-detailed   # Detailed analysis with explanations
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

The system is designed for educational demonstration with explainable AI features, focusing on simplicity while maintaining core ML functionality.

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