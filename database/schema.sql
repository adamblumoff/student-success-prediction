-- Student Success Prediction Database Schema
-- PostgreSQL Database Schema for Student Success Prediction System

-- Create database (run this manually in psql)
-- CREATE DATABASE student_success_db;

-- Students table - Core student demographic and enrollment data
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    id_student INTEGER UNIQUE NOT NULL,
    code_module VARCHAR(10) NOT NULL,
    code_presentation VARCHAR(10) NOT NULL,
    gender_encoded INTEGER,
    region_encoded INTEGER,
    age_band_encoded INTEGER,
    education_encoded INTEGER,
    is_male BOOLEAN DEFAULT FALSE,
    has_disability BOOLEAN DEFAULT FALSE,
    studied_credits INTEGER,
    num_of_prev_attempts INTEGER DEFAULT 0,
    registration_delay FLOAT,
    unregistered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student engagement features table - Early engagement metrics
CREATE TABLE student_engagement (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    early_total_clicks FLOAT,
    early_avg_clicks FLOAT,
    early_clicks_std FLOAT,
    early_max_clicks FLOAT,
    early_active_days INTEGER,
    early_first_access INTEGER,
    early_last_access INTEGER,
    early_engagement_consistency FLOAT,
    early_clicks_per_active_day FLOAT,
    early_engagement_range FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id)
);

-- Student assessment features table - Early assessment performance
CREATE TABLE student_assessments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    early_assessments_count INTEGER DEFAULT 0,
    early_avg_score FLOAT,
    early_score_std FLOAT,
    early_min_score FLOAT,
    early_max_score FLOAT,
    early_missing_submissions INTEGER DEFAULT 0,
    early_submitted_count INTEGER DEFAULT 0,
    early_total_weight FLOAT,
    early_banked_count INTEGER DEFAULT 0,
    early_submission_rate FLOAT,
    early_score_range FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id)
);

-- Risk predictions table - Store model predictions
CREATE TABLE risk_predictions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    risk_score FLOAT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 1),
    risk_category VARCHAR(20) CHECK (risk_category IN ('Low Risk', 'Medium Risk', 'High Risk')),
    needs_intervention BOOLEAN DEFAULT FALSE,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50),
    confidence_score FLOAT
);

-- Interventions table - Track recommended and applied interventions
CREATE TABLE interventions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    prediction_id INTEGER REFERENCES risk_predictions(id) ON DELETE CASCADE,
    intervention_type VARCHAR(100) NOT NULL,
    priority_level VARCHAR(20) CHECK (priority_level IN ('Low', 'Medium', 'High', 'Critical')),
    description TEXT,
    recommended_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    implemented_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Recommended' CHECK (status IN ('Recommended', 'In Progress', 'Completed', 'Cancelled')),
    effectiveness_score FLOAT CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    notes TEXT
);

-- Student outcomes table - Final results and success tracking
CREATE TABLE student_outcomes (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    final_result VARCHAR(20) CHECK (final_result IN ('Pass', 'Fail', 'Withdrawn', 'Distinction')),
    outcome_date TIMESTAMP,
    predicted_correctly BOOLEAN,
    intervention_applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_students_id_student ON students(id_student);
CREATE INDEX idx_students_module_presentation ON students(code_module, code_presentation);
CREATE INDEX idx_risk_predictions_student_date ON risk_predictions(student_id, prediction_date);
CREATE INDEX idx_risk_predictions_category ON risk_predictions(risk_category);
CREATE INDEX idx_interventions_student ON interventions(student_id);
CREATE INDEX idx_interventions_status ON interventions(status);
CREATE INDEX idx_student_outcomes_result ON student_outcomes(final_result);

-- Create a view for complete student data (for ML model)
CREATE VIEW student_features AS
SELECT 
    s.id,
    s.id_student,
    s.code_module,
    s.code_presentation,
    s.gender_encoded,
    s.region_encoded,
    s.age_band_encoded,
    s.education_encoded,
    s.is_male,
    s.has_disability,
    s.studied_credits,
    s.num_of_prev_attempts,
    s.registration_delay,
    s.unregistered,
    
    -- Engagement features
    e.early_total_clicks,
    e.early_avg_clicks,
    e.early_clicks_std,
    e.early_max_clicks,
    e.early_active_days,
    e.early_first_access,
    e.early_last_access,
    e.early_engagement_consistency,
    e.early_clicks_per_active_day,
    e.early_engagement_range,
    
    -- Assessment features
    a.early_assessments_count,
    a.early_avg_score,
    a.early_score_std,
    a.early_min_score,
    a.early_max_score,
    a.early_missing_submissions,
    a.early_submitted_count,
    a.early_total_weight,
    a.early_banked_count,
    a.early_submission_rate,
    a.early_score_range,
    
    -- Outcome
    o.final_result
    
FROM students s
LEFT JOIN student_engagement e ON s.id = e.student_id
LEFT JOIN student_assessments a ON s.id = a.student_id
LEFT JOIN student_outcomes o ON s.id = o.student_id;

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at timestamps
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();