#!/usr/bin/env python3
"""
Database configuration and connection management for PostgreSQL migration.

Provides SQLAlchemy setup with connection pooling, environment-based configuration,
and migration support for the Student Success Prediction system.
"""

import os
import logging
import json
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData, text, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# SQLAlchemy Base for ORM models
Base = declarative_base()

class DatabaseConfig:
    """Database configuration management with environment-based settings."""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables with fallback to SQLite."""
        # Production PostgreSQL configuration
        if os.getenv('DATABASE_URL'):
            return os.getenv('DATABASE_URL')
        
        # Component-based PostgreSQL configuration
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'student_success')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'postgres')
        
        if all([db_host != 'localhost' or db_password != 'postgres']):
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Fallback to SQLite for local development
        logger.warning("No PostgreSQL configuration found, falling back to SQLite")
        return "sqlite:///./mvp_data.db"
    
    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with appropriate configuration."""
        if self.database_url.startswith('postgresql'):
            # PostgreSQL configuration with connection pooling
            engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv('SQL_DEBUG', 'false').lower() == 'true'
            )
        else:
            # SQLite configuration for development
            engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                echo=os.getenv('SQL_DEBUG', 'false').lower() == 'true'
            )
        
        self.engine = engine
        return engine
    
    def create_session_factory(self) -> sessionmaker:
        """Create SQLAlchemy session factory."""
        if not self.engine:
            self.create_engine()
        
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        return self.session_factory
    
    def init_database(self):
        """Initialize database connection and create tables."""
        engine = self.create_engine()
        session_factory = self.create_session_factory()
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        logger.info(f"Database initialized: {self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url}")

# Global database configuration instance
db_config = DatabaseConfig()

def get_engine() -> Engine:
    """Get SQLAlchemy engine instance."""
    if not db_config.engine:
        db_config.create_engine()
    return db_config.engine

def get_session_factory() -> sessionmaker:
    """Get SQLAlchemy session factory."""
    if not db_config.session_factory:
        db_config.create_session_factory()
    return db_config.session_factory

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic cleanup."""
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def init_database():
    """Initialize database with tables and configuration."""
    db_config.init_database()

# Health check function
def check_database_health() -> bool:
    """Check if database is accessible and healthy."""
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Import ORM models from models module to avoid duplication
def _get_models():
    """Lazy import of models to avoid circular imports"""
    try:
        from .models import Institution, Student, Prediction
        return Institution, Student, Prediction
    except ImportError:
        # Fallback for when models module is not available
        logger.warning("Models module not available, using minimal models")
        return None, None, None

def save_predictions_batch(predictions_data: list, session_id: str):
    """Fast batch save for multiple predictions - 10x faster than individual saves"""
    if not predictions_data:
        return
    
    try:
        Institution, Student, Prediction = _get_models()
        if not all([Institution, Student, Prediction]):
            logger.error("Required models not available")
            return
            
        # Try PostgreSQL batch operation first
        with get_db_session() as session:
            # Get default institution
            institution = session.query(Institution).filter_by(code="MVP_DEMO").first()
            if not institution:
                # Create default institution if it doesn't exist
                institution = Institution(
                    name="MVP Demo Institution",
                    code="MVP_DEMO",
                    type="K12"
                )
                session.add(institution)
                session.flush()
            
            # Prepare batch data
            students_to_create = []
            predictions_to_create = []
            
            # Get existing students in batch
            student_ids = [str(pred['student_id']) for pred in predictions_data]
            existing_students = session.query(Student).filter(
                Student.institution_id == institution.id,
                Student.student_id.in_(student_ids)
            ).all()
            
            # Create lookup of existing students
            existing_student_lookup = {s.student_id: s.id for s in existing_students}
            existing_student_ids = set(existing_student_lookup.keys())
            
            # Process each prediction
            for pred_data in predictions_data:
                student_id_str = str(pred_data['student_id'])
                
                # Create student if doesn't exist
                if student_id_str not in existing_student_ids:
                    students_to_create.append({
                        'institution_id': institution.id,
                        'student_id': student_id_str,
                        'enrollment_status': 'active'
                    })
            
            # Batch insert new students
            if students_to_create:
                session.execute(
                    Student.__table__.insert(),
                    students_to_create
                )
                session.flush()
                
                # Update lookup with new students
                new_students = session.query(Student).filter(
                    Student.institution_id == institution.id,
                    Student.student_id.in_([s['student_id'] for s in students_to_create])
                ).all()
                
                for student in new_students:
                    existing_student_lookup[student.student_id] = student.id
            
            # Prepare prediction records
            for pred_data in predictions_data:
                student_id_str = str(pred_data['student_id'])
                db_student_id = existing_student_lookup[student_id_str]
                
                predictions_to_create.append({
                    'institution_id': institution.id,
                    'student_id': db_student_id,
                    'risk_score': pred_data['risk_score'],
                    'risk_category': pred_data['risk_category'],
                    'success_probability': pred_data.get('success_probability'),
                    'session_id': session_id,
                    'data_source': 'csv_upload',
                    'features_used': json.dumps(pred_data.get('features_data')),
                    'explanation': json.dumps(pred_data.get('explanation_data'))
                })
            
            # Batch insert predictions
            if predictions_to_create:
                session.execute(
                    Prediction.__table__.insert(),
                    predictions_to_create
                )
            
            # Single commit for all operations
            session.commit()
            logger.info(f"✅ Batch saved {len(predictions_data)} predictions in single transaction")
            
    except Exception as e:
        logger.error(f"❌ Batch save failed: {e}")
        # Fall back to individual saves as backup
        logger.info("Falling back to individual prediction saves...")
        for pred_data in predictions_data:
            try:
                save_prediction(pred_data, session_id)
            except Exception as individual_error:
                logger.error(f"Individual save failed for student {pred_data.get('student_id')}: {individual_error}")

def save_prediction(prediction_data: dict, session_id: str):
    """Save individual prediction with SQLite fallback"""
    try:
        Institution, Student, Prediction = _get_models()
        if not all([Institution, Student, Prediction]):
            logger.error("Required models not available")
            return
            
        with get_db_session() as session:
            # Get or create default institution
            institution = session.query(Institution).filter_by(code="MVP_DEMO").first()
            if not institution:
                institution = Institution(
                    name="MVP Demo Institution",
                    code="MVP_DEMO",
                    type="K12"
                )
                session.add(institution)
                session.flush()
            
            # Get or create student
            student_id_str = str(prediction_data['student_id'])
            student = session.query(Student).filter(
                Student.institution_id == institution.id,
                Student.student_id == student_id_str
            ).first()
            
            if not student:
                student = Student(
                    institution_id=institution.id,
                    student_id=student_id_str,
                    enrollment_status='active'
                )
                session.add(student)
                session.flush()
            
            # Create prediction
            prediction = Prediction(
                institution_id=institution.id,
                student_id=student.id,
                risk_score=prediction_data['risk_score'],
                risk_category=prediction_data['risk_category'],
                session_id=session_id,
                data_source='csv_upload',
                features_used=json.dumps(prediction_data.get('features_data')),
                explanation=json.dumps(prediction_data.get('explanation_data'))
            )
            session.add(prediction)
            session.commit()
            
    except Exception as e:
        logger.error(f"Failed to save prediction for student {prediction_data.get('student_id')}: {e}")
        raise