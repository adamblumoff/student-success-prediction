#!/usr/bin/env python3
"""
SQLAlchemy ORM models for the Student Success Prediction system.

Defines database schema with proper relationships, indexes, and constraints
for production PostgreSQL deployment.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class Institution(Base):
    """Institution/District model for multi-tenant architecture."""
    __tablename__ = "institutions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # District code
    type = Column(String(50), nullable=False)  # K12, university, etc.
    
    # Configuration
    timezone = Column(String(50), default="UTC")
    active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    students = relationship("Student", back_populates="institution")
    predictions = relationship("Prediction", back_populates="institution")
    interventions = relationship("Intervention", back_populates="institution")

class Student(Base):
    """Student model with enhanced fields for K-12 context."""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Student identification
    student_id = Column(String(100), nullable=False, index=True)  # External student ID
    sis_id = Column(String(100), index=True)  # SIS system ID
    name = Column(String(255), index=True)  # Student name
    
    # Demographics
    grade_level = Column(String(10))  # K, 1, 2, ..., 12
    birth_date = Column(DateTime(timezone=True))
    gender = Column(String(10))
    ethnicity = Column(String(50))
    
    # Academic metrics (commonly stored at student level)
    current_gpa = Column(Float)
    previous_gpa = Column(Float)
    
    # Engagement metrics
    attendance_rate = Column(Float)
    study_hours_week = Column(Integer)
    extracurricular = Column(Integer)  # Number of activities
    
    # Family/background
    parent_education = Column(Integer)  # Education level scale
    socioeconomic_status = Column(Integer)  # SES scale
    
    # Academic status
    enrollment_status = Column(String(20), default="active", index=True)
    enrollment_date = Column(DateTime(timezone=True))
    graduation_date = Column(DateTime(timezone=True))
    
    # Special populations
    is_ell = Column(Boolean, default=False, index=True)  # English Language Learner
    has_iep = Column(Boolean, default=False, index=True)  # Individual Education Plan
    has_504 = Column(Boolean, default=False, index=True)  # Section 504 plan
    is_economically_disadvantaged = Column(Boolean, default=False, index=True)
    
    # Contact information (encrypted in production)
    email = Column(String(255))
    phone = Column(String(20))
    parent_email = Column(String(255))
    parent_phone = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True))
    
    # Relationships
    institution = relationship("Institution", back_populates="students")
    predictions = relationship("Prediction", back_populates="student")
    interventions = relationship("Intervention", back_populates="student")
    
    # Composite indexes for performance
    __table_args__ = (
        Index('ix_students_institution_student_id', 'institution_id', 'student_id'),
        Index('ix_students_institution_grade', 'institution_id', 'grade_level'),
        Index('ix_students_institution_status', 'institution_id', 'enrollment_status'),
    )

class Prediction(Base):
    """Prediction model with comprehensive risk assessment data."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    
    # Prediction results
    risk_score = Column(Float, nullable=False, index=True)
    risk_category = Column(String(20), nullable=False, index=True)  # High, Medium, Low
    success_probability = Column(Float)
    confidence_score = Column(Float)
    
    # Model information
    model_version = Column(String(50))
    model_type = Column(String(50))  # binary, multiclass
    prediction_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Features used (JSON in PostgreSQL, TEXT in SQLite)
    features_used = Column(Text)  # JSON string of features
    feature_importance = Column(Text)  # JSON string of importance scores
    
    # Context
    session_id = Column(String(100), index=True)  # Upload session or batch ID
    data_source = Column(String(50))  # CSV upload, API, scheduled
    
    # Explanation data
    explanation = Column(Text)  # JSON string of AI explanation
    risk_factors = Column(Text)  # JSON string of identified risk factors
    protective_factors = Column(Text)  # JSON string of protective factors
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    institution = relationship("Institution", back_populates="predictions")
    student = relationship("Student", back_populates="predictions")
    interventions = relationship("Intervention", back_populates="prediction")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_predictions_student_date', 'student_id', 'prediction_date'),
        Index('ix_predictions_institution_risk', 'institution_id', 'risk_category'),
        Index('ix_predictions_institution_date', 'institution_id', 'prediction_date'),
    )

class Intervention(Base):
    """Intervention tracking model for workflow management."""
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), index=True)
    
    # Intervention details
    intervention_type = Column(String(100), nullable=False, index=True)  # meeting, tutoring, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), index=True)  # Critical, High, Medium, Low
    
    # Status tracking
    status = Column(String(20), default="planned", index=True)  # planned, active, completed, cancelled
    assigned_to = Column(String(255))  # Staff member assigned
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True))
    completed_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    
    # Outcome tracking
    outcome = Column(String(50))  # successful, unsuccessful, no_response
    outcome_notes = Column(Text)
    follow_up_needed = Column(Boolean, default=False)
    
    # Cost tracking for ROI analysis
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    time_spent_minutes = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    institution = relationship("Institution", back_populates="interventions")
    student = relationship("Student", back_populates="interventions")
    prediction = relationship("Prediction", back_populates="interventions")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_interventions_student_status', 'student_id', 'status'),
        Index('ix_interventions_institution_type', 'institution_id', 'intervention_type'),
        Index('ix_interventions_assigned_status', 'assigned_to', 'status'),
    )

class AuditLog(Base):
    """Audit log for FERPA compliance and security tracking."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    
    # User information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # nullable for anonymous actions
    user_email = Column(String(255))
    user_role = Column(String(50))
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # view_student, upload_csv, run_prediction
    resource_type = Column(String(50))  # student, prediction, intervention
    resource_id = Column(String(100))
    
    # Context
    ip_address = Column(String(45))  # IPv6-compatible
    user_agent = Column(Text)
    session_id = Column(String(100))
    
    # Request details
    request_method = Column(String(10))
    request_path = Column(String(500))
    request_params = Column(Text)  # JSON string
    
    # Response details
    response_status = Column(Integer)
    processing_time_ms = Column(Integer)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    institution = relationship("Institution")
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes for performance and compliance queries
    __table_args__ = (
        Index('ix_audit_logs_user_action', 'user_id', 'action'),
        Index('ix_audit_logs_institution_timestamp', 'institution_id', 'timestamp'),
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id'),
    )

class ModelMetadata(Base):
    """Model metadata and performance tracking."""
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), index=True)
    
    # Model identification
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(50))  # global, institution-specific
    
    # Performance metrics
    accuracy = Column(Float)
    auc_score = Column(Float)
    f1_score = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    
    # Training information
    training_data_size = Column(Integer)
    training_features = Column(Text)  # JSON string
    training_date = Column(DateTime(timezone=True))
    
    # Model configuration
    hyperparameters = Column(Text)  # JSON string
    feature_engineering_version = Column(String(50))
    
    # Deployment
    deployed_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    institution = relationship("Institution")
    
    # Unique constraint for active models
    __table_args__ = (
        Index('ix_model_active', 'institution_id', 'model_type', 'is_active'),
    )

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Authentication
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # teacher, admin, district_admin, etc.
    
    # Account status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    institution = relationship("Institution")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"

class UserSession(Base):
    """User session model for secure session management."""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, index=True)
    
    # Security
    revoked_at = Column(DateTime(timezone=True))
    revoked_reason = Column(String(100))  # logout, timeout, security, etc.
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"

class GPTInsight(Base):
    """GPT-generated insights for students with smart caching."""
    __tablename__ = "gpt_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Student identification - flexible to handle both database IDs and CSV IDs
    student_id = Column(String(100), nullable=False, index=True)  # The student ID used in the frontend
    student_database_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)  # Database reference if available
    
    # Analysis context for cache validation
    risk_level = Column(String(20), nullable=False, index=True)  # High Risk, Medium Risk, Low Risk
    data_hash = Column(String(64), nullable=False, index=True)  # Hash of student data to detect changes
    
    # GPT analysis content
    raw_response = Column(Text, nullable=False)  # Full GPT response
    formatted_html = Column(Text, nullable=False)  # HTML-formatted response for display
    
    # Analysis metadata
    gpt_model = Column(String(50), default="gpt-5-nano")  # Model version used
    tokens_used = Column(Integer)  # Cost tracking
    generation_time_ms = Column(Integer)  # Performance tracking
    
    # Session and user tracking
    session_id = Column(String(100), index=True)  # Session that generated this insight
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Cache management
    is_cached = Column(Boolean, default=False, index=True)  # Whether this was loaded from cache
    cache_hits = Column(Integer, default=0)  # How many times this cached result was used
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    institution = relationship("Institution")
    student = relationship("Student", foreign_keys=[student_database_id])
    user = relationship("User")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('ix_gpt_insights_student_hash', 'student_id', 'data_hash'),
        Index('ix_gpt_insights_session_risk', 'session_id', 'risk_level'),
        Index('ix_gpt_insights_institution_created', 'institution_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<GPTInsight(student_id='{self.student_id}', risk_level='{self.risk_level}', cached={self.is_cached})>"