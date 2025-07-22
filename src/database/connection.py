"""
Database connection and session management for PostgreSQL
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        # Production database URL
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            return database_url
        
        # Default local PostgreSQL configuration
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "student_success_db")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _initialize_database(self):
        """Initialize database engine and session factory"""
        try:
            database_url = self._get_database_url()
            logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
            
            # Create engine
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=300,    # Recycle connections after 5 minutes
                echo=False  # Set to True for SQL query logging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get synchronous database session (manual cleanup required)"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close_all_connections(self):
        """Close all database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("All database connections closed")


# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    yield from db_manager.get_session()

# Utility functions for common operations
def init_db():
    """Initialize database with tables"""
    try:
        db_manager.create_tables()
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def test_db_connection() -> bool:
    """Test database connectivity"""
    return db_manager.test_connection()

def get_db_stats(db: Session) -> dict:
    """Get basic database statistics"""
    try:
        from .models import Student, RiskPrediction, Intervention
        
        stats = {
            "total_students": db.query(Student).count(),
            "total_predictions": db.query(RiskPrediction).count(),
            "total_interventions": db.query(Intervention).count(),
            "high_risk_students": db.query(RiskPrediction).filter(
                RiskPrediction.risk_category == 'High Risk'
            ).count(),
            "active_interventions": db.query(Intervention).filter(
                Intervention.status.in_(['Recommended', 'In Progress'])
            ).count()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}

# SQLite fallback for development/testing
class SQLiteManager:
    """Fallback SQLite database manager for development"""
    
    def __init__(self, db_path: str = "data/student_success.db"):
        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"SQLite tables created at {self.db_path}")
    
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

# Initialize SQLite fallback if PostgreSQL is not available
def init_fallback_db() -> SQLiteManager:
    """Initialize SQLite fallback database"""
    sqlite_manager = SQLiteManager()
    sqlite_manager.create_tables()
    logger.info("SQLite fallback database initialized")
    return sqlite_manager