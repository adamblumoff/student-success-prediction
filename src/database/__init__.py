"""
Database package for Student Success Prediction System
"""

from .models import (
    Base,
    Student,
    StudentEngagement,
    StudentAssessment,
    RiskPrediction,
    Intervention,
    StudentOutcome,
    create_student_with_features,
    get_student_features_for_ml
)

from .connection import (
    DatabaseManager,
    db_manager,
    get_db,
    init_db,
    test_db_connection,
    get_db_stats,
    SQLiteManager,
    init_fallback_db
)

__all__ = [
    # Models
    "Base",
    "Student", 
    "StudentEngagement",
    "StudentAssessment",
    "RiskPrediction",
    "Intervention",
    "StudentOutcome",
    "create_student_with_features",
    "get_student_features_for_ml",
    
    # Connection
    "DatabaseManager",
    "db_manager",
    "get_db",
    "init_db", 
    "test_db_connection",
    "get_db_stats",
    "SQLiteManager",
    "init_fallback_db"
]