#!/usr/bin/env python3
"""
Test script for database integration with SQLite fallback
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_integration():
    """Test database models and operations"""
    try:
        # Test with SQLite fallback (since PostgreSQL packages aren't installed)
        from database.connection import SQLiteManager
        from database.models import create_student_with_features, get_student_features_for_ml
        
        logger.info("🔍 Testing SQLite database integration...")
        
        # Initialize SQLite database
        sqlite_manager = SQLiteManager("test_student_success.db")
        sqlite_manager.create_tables()
        logger.info("✅ SQLite tables created")
        
        # Get session
        with next(sqlite_manager.get_session()) as db:
            # Test creating a student
            sample_student = {
                'id_student': 99999,
                'code_module': 'TEST',
                'code_presentation': '2024J',
                'gender_encoded': 1,
                'age_band_encoded': 1,
                'education_encoded': 2,
                'is_male': True,
                'has_disability': False,
                'studied_credits': 60,
                'num_of_prev_attempts': 0,
                'registration_delay': -10.0,
                'early_total_clicks': 500.0,
                'early_avg_clicks': 10.5,
                'early_active_days': 25,
                'early_assessments_count': 3,
                'early_avg_score': 75.0,
                'early_submission_rate': 0.8,
                'final_result': 'Pass'
            }
            
            # Create student
            student = create_student_with_features(db, sample_student)
            logger.info(f"✅ Student created with database ID: {student.id}")
            
            # Test retrieving features for ML
            features = get_student_features_for_ml(db, student.id)
            logger.info(f"✅ Retrieved {len(features)} features for ML model")
            
            # Test predictions (mock)
            from database.models import RiskPrediction
            prediction = RiskPrediction(
                student_id=student.id,
                risk_score=0.25,
                risk_category='Low Risk',
                needs_intervention=False,
                model_version='test_v1.0',
                confidence_score=0.85
            )
            db.add(prediction)
            db.commit()
            logger.info("✅ Risk prediction saved to database")
            
            # Test intervention
            from database.models import Intervention
            intervention = Intervention(
                student_id=student.id,
                prediction_id=prediction.id,
                intervention_type='Academic Support',
                priority_level='Medium',
                description='Provide additional tutoring sessions',
                status='Recommended'
            )
            db.add(intervention)
            db.commit()
            logger.info("✅ Intervention recommendation saved")
            
            # Test database stats
            from database.connection import get_db_stats
            stats = get_db_stats(db)
            logger.info(f"✅ Database stats: {stats}")
        
        logger.info("🎉 Database integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database integration test failed: {e}")
        return False

def test_api_models():
    """Test that API models can import database modules"""
    try:
        logger.info("🔍 Testing API database imports...")
        
        # Test imports (without actually running the API)
        from database import get_db, Student, RiskPrediction, Intervention
        from database.models import create_student_with_features, get_student_features_for_ml
        
        logger.info("✅ All database imports successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ API database import test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 TESTING DATABASE INTEGRATION")
    logger.info("=" * 50)
    
    # Test database operations
    db_test = test_database_integration()
    
    # Test API imports
    api_test = test_api_models()
    
    # Summary
    if db_test and api_test:
        logger.info("🎉 ALL TESTS PASSED - Database integration ready!")
        return True
    else:
        logger.error("❌ SOME TESTS FAILED - Check errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)