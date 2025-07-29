#!/usr/bin/env python3
"""
Database configuration and connection management for PostgreSQL migration.

Provides SQLAlchemy setup with connection pooling, environment-based configuration,
and migration support for the Student Success Prediction system.
"""

import os
import logging
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

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