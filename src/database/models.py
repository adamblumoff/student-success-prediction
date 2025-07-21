"""
SQLAlchemy Models for Student Success Prediction Database
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


class Student(Base):
    """Student demographic and enrollment information"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    id_student = Column(Integer, unique=True, nullable=False, index=True)
    code_module = Column(String(10), nullable=False)
    code_presentation = Column(String(10), nullable=False)
    gender_encoded = Column(Integer)
    region_encoded = Column(Integer)
    age_band_encoded = Column(Integer)
    education_encoded = Column(Integer)
    is_male = Column(Boolean, default=False)
    has_disability = Column(Boolean, default=False)
    studied_credits = Column(Integer)
    num_of_prev_attempts = Column(Integer, default=0)
    registration_delay = Column(Float)
    unregistered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    engagement = relationship("StudentEngagement", back_populates="student", uselist=False)
    assessments = relationship("StudentAssessment", back_populates="student", uselist=False)
    predictions = relationship("RiskPrediction", back_populates="student")
    interventions = relationship("Intervention", back_populates="student")
    outcome = relationship("StudentOutcome", back_populates="student", uselist=False)

    def __repr__(self):
        return f"<Student(id_student={self.id_student}, module={self.code_module})>"


class StudentEngagement(Base):
    """Student VLE engagement metrics"""
    __tablename__ = "student_engagement"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), unique=True)
    early_total_clicks = Column(Float)
    early_avg_clicks = Column(Float)
    early_clicks_std = Column(Float)
    early_max_clicks = Column(Float)
    early_active_days = Column(Integer)
    early_first_access = Column(Integer)
    early_last_access = Column(Integer)
    early_engagement_consistency = Column(Float)
    early_clicks_per_active_day = Column(Float)
    early_engagement_range = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("Student", back_populates="engagement")

    def __repr__(self):
        return f"<StudentEngagement(student_id={self.student_id}, total_clicks={self.early_total_clicks})>"


class StudentAssessment(Base):
    """Student assessment performance metrics"""
    __tablename__ = "student_assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), unique=True)
    early_assessments_count = Column(Integer, default=0)
    early_avg_score = Column(Float)
    early_score_std = Column(Float)
    early_min_score = Column(Float)
    early_max_score = Column(Float)
    early_missing_submissions = Column(Integer, default=0)
    early_submitted_count = Column(Integer, default=0)
    early_total_weight = Column(Float)
    early_banked_count = Column(Integer, default=0)
    early_submission_rate = Column(Float)
    early_score_range = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("Student", back_populates="assessments")

    def __repr__(self):
        return f"<StudentAssessment(student_id={self.student_id}, avg_score={self.early_avg_score})>"


class RiskPrediction(Base):
    """ML model risk predictions for students"""
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True)
    risk_score = Column(Float, nullable=False)
    risk_category = Column(String(20))
    needs_intervention = Column(Boolean, default=False)
    prediction_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    model_version = Column(String(50))
    confidence_score = Column(Float)

    # Constraints
    __table_args__ = (
        CheckConstraint('risk_score >= 0 AND risk_score <= 1', name='check_risk_score_range'),
        CheckConstraint("risk_category IN ('Low Risk', 'Medium Risk', 'High Risk')", name='check_risk_category')
    )

    # Relationships
    student = relationship("Student", back_populates="predictions")
    interventions = relationship("Intervention", back_populates="prediction")

    def __repr__(self):
        return f"<RiskPrediction(student_id={self.student_id}, risk_score={self.risk_score:.3f})>"


class Intervention(Base):
    """Recommended and applied interventions"""
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True)
    prediction_id = Column(Integer, ForeignKey("risk_predictions.id", ondelete="CASCADE"))
    intervention_type = Column(String(100), nullable=False)
    priority_level = Column(String(20))
    description = Column(Text)
    recommended_date = Column(DateTime(timezone=True), server_default=func.now())
    implemented_date = Column(DateTime(timezone=True))
    status = Column(String(20), default="Recommended")
    effectiveness_score = Column(Float)
    notes = Column(Text)

    # Constraints
    __table_args__ = (
        CheckConstraint("priority_level IN ('Low', 'Medium', 'High', 'Critical')", name='check_priority_level'),
        CheckConstraint("status IN ('Recommended', 'In Progress', 'Completed', 'Cancelled')", name='check_status'),
        CheckConstraint('effectiveness_score >= 0 AND effectiveness_score <= 1', name='check_effectiveness_range')
    )

    # Relationships
    student = relationship("Student", back_populates="interventions")
    prediction = relationship("RiskPrediction", back_populates="interventions")

    def __repr__(self):
        return f"<Intervention(student_id={self.student_id}, type={self.intervention_type})>"


class StudentOutcome(Base):
    """Final student outcomes and success tracking"""
    __tablename__ = "student_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), unique=True)
    final_result = Column(String(20), index=True)
    outcome_date = Column(DateTime(timezone=True))
    predicted_correctly = Column(Boolean)
    intervention_applied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint("final_result IN ('Pass', 'Fail', 'Withdrawn', 'Distinction')", name='check_final_result'),
    )

    # Relationships
    student = relationship("Student", back_populates="outcome")

    def __repr__(self):
        return f"<StudentOutcome(student_id={self.student_id}, result={self.final_result})>"


# Database utility functions
def create_student_with_features(db: Session, student_data: dict) -> Student:
    """Create a student record with all related features"""
    
    # Create student
    student = Student(
        id_student=student_data['id_student'],
        code_module=student_data['code_module'],
        code_presentation=student_data['code_presentation'],
        gender_encoded=student_data.get('gender_encoded'),
        region_encoded=student_data.get('region_encoded'),
        age_band_encoded=student_data.get('age_band_encoded'),
        education_encoded=student_data.get('education_encoded'),
        is_male=student_data.get('is_male', False),
        has_disability=student_data.get('has_disability', False),
        studied_credits=student_data.get('studied_credits'),
        num_of_prev_attempts=student_data.get('num_of_prev_attempts', 0),
        registration_delay=student_data.get('registration_delay'),
        unregistered=student_data.get('unregistered', False)
    )
    
    db.add(student)
    db.flush()  # Get the student ID
    
    # Create engagement record
    engagement = StudentEngagement(
        student_id=student.id,
        early_total_clicks=student_data.get('early_total_clicks'),
        early_avg_clicks=student_data.get('early_avg_clicks'),
        early_clicks_std=student_data.get('early_clicks_std'),
        early_max_clicks=student_data.get('early_max_clicks'),
        early_active_days=student_data.get('early_active_days'),
        early_first_access=student_data.get('early_first_access'),
        early_last_access=student_data.get('early_last_access'),
        early_engagement_consistency=student_data.get('early_engagement_consistency'),
        early_clicks_per_active_day=student_data.get('early_clicks_per_active_day'),
        early_engagement_range=student_data.get('early_engagement_range')
    )
    
    # Create assessment record
    assessment = StudentAssessment(
        student_id=student.id,
        early_assessments_count=student_data.get('early_assessments_count', 0),
        early_avg_score=student_data.get('early_avg_score'),
        early_score_std=student_data.get('early_score_std'),
        early_min_score=student_data.get('early_min_score'),
        early_max_score=student_data.get('early_max_score'),
        early_missing_submissions=student_data.get('early_missing_submissions', 0),
        early_submitted_count=student_data.get('early_submitted_count', 0),
        early_total_weight=student_data.get('early_total_weight'),
        early_banked_count=student_data.get('early_banked_count', 0),
        early_submission_rate=student_data.get('early_submission_rate'),
        early_score_range=student_data.get('early_score_range')
    )
    
    # Create outcome if available
    if student_data.get('final_result'):
        outcome = StudentOutcome(
            student_id=student.id,
            final_result=student_data['final_result']
        )
        db.add(outcome)
    
    db.add_all([engagement, assessment])
    db.commit()
    db.refresh(student)
    
    return student


def get_student_features_for_ml(db: Session, student_id: int) -> Optional[dict]:
    """Get all student features formatted for ML model prediction"""
    
    query = db.query(Student).filter(Student.id == student_id).first()
    if not query:
        return None
    
    # Build feature dictionary matching the ML model's expected format
    features = {
        'id_student': query.id_student,
        'code_module': query.code_module,
        'code_presentation': query.code_presentation,
        'gender_encoded': query.gender_encoded,
        'region_encoded': query.region_encoded,
        'age_band_encoded': query.age_band_encoded,
        'education_encoded': query.education_encoded,
        'is_male': query.is_male,
        'has_disability': query.has_disability,
        'studied_credits': query.studied_credits,
        'num_of_prev_attempts': query.num_of_prev_attempts,
        'registration_delay': query.registration_delay,
        'unregistered': query.unregistered
    }
    
    # Add engagement features
    if query.engagement:
        eng = query.engagement
        features.update({
            'early_total_clicks': eng.early_total_clicks,
            'early_avg_clicks': eng.early_avg_clicks,
            'early_clicks_std': eng.early_clicks_std,
            'early_max_clicks': eng.early_max_clicks,
            'early_active_days': eng.early_active_days,
            'early_first_access': eng.early_first_access,
            'early_last_access': eng.early_last_access,
            'early_engagement_consistency': eng.early_engagement_consistency,
            'early_clicks_per_active_day': eng.early_clicks_per_active_day,
            'early_engagement_range': eng.early_engagement_range
        })
    
    # Add assessment features  
    if query.assessments:
        assess = query.assessments
        features.update({
            'early_assessments_count': assess.early_assessments_count,
            'early_avg_score': assess.early_avg_score,
            'early_score_std': assess.early_score_std,
            'early_min_score': assess.early_min_score,
            'early_max_score': assess.early_max_score,
            'early_missing_submissions': assess.early_missing_submissions,
            'early_submitted_count': assess.early_submitted_count,
            'early_total_weight': assess.early_total_weight,
            'early_banked_count': assess.early_banked_count,
            'early_submission_rate': assess.early_submission_rate,
            'early_score_range': assess.early_score_range
        })
    
    return features