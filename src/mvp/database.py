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

from sqlalchemy import create_engine, MetaData, text, Column, Integer, String, DateTime, Float, Text, Boolean, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# SQLAlchemy Base for ORM models
Base = declarative_base()

class DatabaseConfig:
    """Database configuration management with environment-based settings and security."""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.is_production = os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
        self._validate_security_config()
    
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
    
    def _validate_security_config(self) -> None:
        """Validate database security configuration"""
        if self.is_production:
            # Production security requirements
            if not self.database_url.startswith('postgresql'):
                raise ValueError("❌ SECURITY ERROR: Production must use PostgreSQL, not SQLite")
            
            if 'localhost' in self.database_url:
                logger.warning("⚠️ Production database using localhost - ensure this is intended")
            
            # Check for insecure default credentials
            if 'postgres:postgres@' in self.database_url:
                raise ValueError("❌ SECURITY ERROR: Cannot use default PostgreSQL credentials in production")
            
            # Require SSL in production
            if 'sslmode=require' not in self.database_url and 'ssl=true' not in self.database_url:
                logger.warning("⚠️ Production database connection should use SSL")
        
        logger.info("✅ Database security configuration validated")
    
    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with secure configuration and connection pooling."""
        if self.database_url.startswith('postgresql'):
            # Production PostgreSQL configuration with security hardening
            pool_size = int(os.getenv('DB_POOL_SIZE', '5' if self.is_production else '10'))
            max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10' if self.is_production else '20'))
            pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
            
            engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
                connect_args={
                    'connect_timeout': 10,  # Connection timeout
                    'application_name': 'student_success_predictor',
                    'options': '-c statement_timeout=30000'  # 30 second query timeout
                },
                echo=os.getenv('SQL_DEBUG', 'false').lower() == 'true',
                isolation_level='READ_COMMITTED',  # Secure isolation level
                future=True  # Use SQLAlchemy 2.0 style
            )
            
            # Test connection on startup
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"✅ PostgreSQL connection established (pool_size={pool_size})")
            except Exception as e:
                logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
                raise
        else:
            # SQLite configuration for development with security constraints
            engine = create_engine(
                self.database_url,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,  # 30 second timeout for SQLite
                },
                echo=os.getenv('SQL_DEBUG', 'false').lower() == 'true',
                future=True  # Use SQLAlchemy 2.0 style
            )
            logger.info("✅ SQLite connection established (development mode)")
        
        self.engine = engine
        return engine
    
    def create_session_factory(self) -> sessionmaker:
        """Create SQLAlchemy session factory."""
        if not self.engine:
            self.create_engine()
        # Use SafeSession to allow plain-string SQL in tests
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            class_=SafeSession
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

# Initialize encryption middleware when database is configured
def _initialize_encryption_on_startup():
    """Initialize encryption middleware with database configuration"""
    try:
        from .encryption_middleware import encryption_middleware
        from .encryption import encryption_manager
        
        if encryption_manager.enabled:
            logger.info("🔒 Database encryption middleware initialized")
        else:
            logger.info("🔓 Database encryption disabled for development")
            
    except ImportError as e:
        logger.warning(f"⚠️ Encryption modules not available: {e}")

# Initialize encryption when module is imported
_initialize_encryption_on_startup()

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

class SafeSession(Session):
    """SQLAlchemy Session that safely wraps str SQL in text().

    This maintains backwards-compatibility for tests that call
    session.execute("SELECT 1") using plain strings under SQLAlchemy 2.0.
    """

    def execute(self, statement, *args, **kwargs):  # type: ignore[override]
        if isinstance(statement, str):
            statement = text(statement)
        return super().execute(statement, *args, **kwargs)


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
                        'name': pred_data.get('name', 'Unknown'),  # Save student name from CSV
                        'grade_level': str(pred_data.get('grade_level')) if pred_data.get('grade_level') else None,
                        'enrollment_status': 'active',
                        # Academic metrics from CSV
                        'current_gpa': float(pred_data.get('current_gpa')) if pred_data.get('current_gpa') else None,
                        'previous_gpa': float(pred_data.get('previous_gpa')) if pred_data.get('previous_gpa') else None,
                        # Engagement metrics from CSV  
                        'attendance_rate': float(pred_data.get('attendance_rate')) if pred_data.get('attendance_rate') else None,
                        'study_hours_week': int(pred_data.get('study_hours_week')) if pred_data.get('study_hours_week') else None,
                        'extracurricular': int(pred_data.get('extracurricular')) if pred_data.get('extracurricular') else None,
                        # Family/background from CSV
                        'parent_education': int(pred_data.get('parent_education')) if pred_data.get('parent_education') else None,
                        'socioeconomic_status': int(pred_data.get('socioeconomic_status')) if pred_data.get('socioeconomic_status') else None
                    })
            
            # Batch upsert new students (PostgreSQL ON CONFLICT)
            if students_to_create:
                if db_config.database_url.startswith('postgresql'):
                    # PostgreSQL upsert - avoid duplicates
                    from sqlalchemy.dialects.postgresql import insert
                    stmt = insert(Student.__table__).values(students_to_create)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=['institution_id', 'student_id']
                    )
                    session.execute(stmt)
                else:
                    # SQLite - use regular insert for development
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
            
            # Check for existing predictions to avoid duplicates
            student_db_ids = [existing_student_lookup[str(pred['student_id'])] for pred in predictions_data]
            existing_predictions = session.query(Prediction).filter(
                Prediction.institution_id == institution.id,
                Prediction.student_id.in_(student_db_ids)
            ).all()
            
            # Create lookup of existing predictions by student_id
            existing_pred_lookup = {pred.student_id: pred for pred in existing_predictions}
            
            # Process each prediction - update existing or create new
            predictions_to_create = []
            predictions_to_update = []
            
            for pred_data in predictions_data:
                student_id_str = str(pred_data['student_id'])
                db_student_id = existing_student_lookup[student_id_str]
                
                # Store all CSV data as features for later use
                csv_features = {
                    'assignment_completion': pred_data.get('assignment_completion'),
                    'quiz_average': pred_data.get('quiz_average'),
                    'participation_score': pred_data.get('participation_score'),
                    'late_submissions': pred_data.get('late_submissions'),
                    'course_difficulty': pred_data.get('course_difficulty'),
                    'current_gpa': pred_data.get('current_gpa'),
                    'attendance_rate': pred_data.get('attendance_rate'),
                    'previous_gpa': pred_data.get('previous_gpa'),
                    'study_hours_week': pred_data.get('study_hours_week'),
                    'extracurricular': pred_data.get('extracurricular'),
                    'parent_education': pred_data.get('parent_education'),
                    'socioeconomic_status': pred_data.get('socioeconomic_status')
                }
                
                prediction_data = {
                    'risk_score': pred_data['risk_score'],
                    'risk_category': pred_data['risk_category'],
                    'success_probability': pred_data.get('success_probability'),
                    'session_id': session_id,
                    'data_source': 'csv_upload',
                    'features_used': json.dumps(csv_features),  # Store all CSV fields as JSON
                    'explanation': json.dumps(pred_data.get('explanation_data'))
                }
                
                if db_student_id in existing_pred_lookup:
                    # Update existing prediction
                    existing_pred = existing_pred_lookup[db_student_id]
                    predictions_to_update.append({
                        'id': existing_pred.id,
                        **prediction_data
                    })
                else:
                    # Create new prediction
                    predictions_to_create.append({
                        'institution_id': institution.id,
                        'student_id': db_student_id,
                        **prediction_data
                    })
            
            # Batch upsert new predictions (PostgreSQL ON CONFLICT)
            if predictions_to_create:
                if db_config.database_url.startswith('postgresql'):
                    # PostgreSQL upsert - update existing predictions
                    from sqlalchemy.dialects.postgresql import insert
                    stmt = insert(Prediction.__table__).values(predictions_to_create)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['student_id'],
                        set_={
                            'risk_score': stmt.excluded.risk_score,
                            'risk_category': stmt.excluded.risk_category,
                            'success_probability': stmt.excluded.success_probability,
                            'session_id': stmt.excluded.session_id,
                            'data_source': stmt.excluded.data_source,
                            'features_used': stmt.excluded.features_used,
                            'explanation': stmt.excluded.explanation,
                            'created_at': text('CURRENT_TIMESTAMP')
                        }
                    )
                    session.execute(stmt)
                else:
                    # SQLite - use regular insert for development
                    session.execute(
                        Prediction.__table__.insert(),
                        predictions_to_create
                    )
            
            # Batch update existing predictions
            if predictions_to_update:
                for pred_update in predictions_to_update:
                    session.query(Prediction).filter(
                        Prediction.id == pred_update['id']
                    ).update({k: v for k, v in pred_update.items() if k != 'id'})
            
            # Single commit for all operations
            session.commit()
            logger.info(f"✅ Batch processed {len(predictions_data)} predictions: {len(predictions_to_create)} new, {len(predictions_to_update)} updated")
            
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
            
            # Upsert student (PostgreSQL ON CONFLICT)
            student_id_str = str(prediction_data['student_id'])
            
            if db_config.database_url.startswith('postgresql'):
                # PostgreSQL upsert for student
                from sqlalchemy.dialects.postgresql import insert
                student_data = {
                    'institution_id': institution.id,
                    'student_id': student_id_str,
                    'enrollment_status': 'active'
                }
                stmt = insert(Student.__table__).values(**student_data)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['institution_id', 'student_id']
                )
                session.execute(stmt)
                session.flush()
                
                # Get the student (existing or newly created)
                student = session.query(Student).filter(
                    Student.institution_id == institution.id,
                    Student.student_id == student_id_str
                ).first()
            else:
                # SQLite - traditional get or create
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
            
            # Upsert prediction (PostgreSQL ON CONFLICT)
            prediction_data_dict = {
                'institution_id': institution.id,
                'student_id': student.id,
                'risk_score': prediction_data['risk_score'],
                'risk_category': prediction_data['risk_category'],
                'session_id': session_id,
                'data_source': 'csv_upload',
                'features_used': json.dumps(prediction_data.get('features_data')),
                'explanation': json.dumps(prediction_data.get('explanation_data'))
            }
            
            if db_config.database_url.startswith('postgresql'):
                # PostgreSQL upsert for prediction
                from sqlalchemy.dialects.postgresql import insert
                stmt = insert(Prediction.__table__).values(**prediction_data_dict)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['student_id'],
                    set_={
                        'risk_score': stmt.excluded.risk_score,
                        'risk_category': stmt.excluded.risk_category,
                        'session_id': stmt.excluded.session_id,
                        'data_source': stmt.excluded.data_source,
                        'features_used': stmt.excluded.features_used,
                        'explanation': stmt.excluded.explanation,
                        'created_at': text('CURRENT_TIMESTAMP')
                    }
                )
                session.execute(stmt)
            else:
                # SQLite - traditional create
                prediction = Prediction(**prediction_data_dict)
                session.add(prediction)
            
            session.commit()
            
    except Exception as e:
        logger.error(f"Failed to save prediction for student {prediction_data.get('student_id')}: {e}")
        raise

# GPT Insights Database Functions
def save_gpt_insight(insight_data: dict, session_id: str = None, user_id: int = None, institution_id: int = 1):
    """Save GPT insight to database with smart caching logic."""
    try:
        from .models import GPTInsight
        
        with get_db_session() as session:
            # Check if insight already exists with same student_id and data_hash
            existing_insight = session.query(GPTInsight).filter(
                GPTInsight.student_id == str(insight_data['student_id']),
                GPTInsight.data_hash == insight_data['data_hash']
            ).first()
            
            if existing_insight:
                # Update access tracking for existing insight
                existing_insight.cache_hits += 1
                existing_insight.last_accessed = func.now()
                existing_insight.is_cached = True
                session.commit()
                logger.info(f"Updated access for existing GPT insight: student {insight_data['student_id']}, cache hits: {existing_insight.cache_hits + 1}")
                return existing_insight.id
            else:
                # Create new insight - this is a fresh generation
                insight = GPTInsight(
                    institution_id=institution_id,
                    student_id=str(insight_data['student_id']),
                    student_database_id=insight_data.get('student_database_id'),
                    risk_level=insight_data['risk_level'],
                    data_hash=insight_data['data_hash'],
                    raw_response=insight_data['raw_response'],
                    formatted_html=insight_data['formatted_html'],
                    gpt_model=insight_data.get('gpt_model', 'gpt-5-nano'),
                    tokens_used=insight_data.get('tokens_used'),
                    generation_time_ms=insight_data.get('generation_time_ms'),
                    session_id=session_id,
                    user_id=user_id,
                    is_cached=False,  # This is a fresh generation
                    cache_hits=0
                )
                session.add(insight)
                session.commit()
                logger.info(f"Saved new GPT insight for student {insight_data['student_id']}")
                return insight.id
                
    except Exception as e:
        logger.error(f"Failed to save GPT insight for student {insight_data.get('student_id')}: {e}")
        raise

def get_gpt_insight(student_id: str, data_hash: str, institution_id: int = 1):
    """Retrieve existing GPT insight from database if available."""
    try:
        from .models import GPTInsight
        
        with get_db_session() as session:
            insight = session.query(GPTInsight).filter(
                GPTInsight.student_id == str(student_id),
                GPTInsight.data_hash == data_hash,
                GPTInsight.institution_id == institution_id
            ).first()
            
            if insight:
                # Update access tracking
                insight.cache_hits += 1
                insight.last_accessed = func.now()
                insight.is_cached = True
                session.commit()
                
                logger.info(f"Retrieved cached GPT insight for student {student_id}, cache hits: {insight.cache_hits}")
                return {
                    'id': insight.id,
                    'raw_response': insight.raw_response,
                    'formatted_html': insight.formatted_html,
                    'risk_level': insight.risk_level,
                    'created_at': insight.created_at,
                    'is_cached': True,
                    'cache_hits': insight.cache_hits
                }
            else:
                logger.info(f"No cached GPT insight found for student {student_id}")
                return None
                
    except Exception as e:
        logger.error(f"Failed to retrieve GPT insight for student {student_id}: {e}")
        return None

def get_all_gpt_insights_for_session(session_id: str, institution_id: int = 1):
    """Retrieve all GPT insights for a session to restore on login/refresh."""
    try:
        from .models import GPTInsight
        
        with get_db_session() as session:
            insights = session.query(GPTInsight).filter(
                GPTInsight.session_id == session_id,
                GPTInsight.institution_id == institution_id
            ).all()
            
            result = {}
            for insight in insights:
                result[insight.student_id] = {
                    'id': insight.id,
                    'raw_response': insight.raw_response,
                    'formatted_html': insight.formatted_html,
                    'risk_level': insight.risk_level,
                    'data_hash': insight.data_hash,
                    'created_at': insight.created_at,
                    'is_cached': True,
                    'cache_hits': insight.cache_hits
                }
            
            logger.info(f"Retrieved {len(result)} GPT insights for session {session_id}")
            return result
            
    except Exception as e:
        logger.error(f"Failed to retrieve GPT insights for session {session_id}: {e}")
        return {}