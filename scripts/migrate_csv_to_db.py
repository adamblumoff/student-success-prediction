#!/usr/bin/env python3
"""
Migration script to load CSV data into PostgreSQL database
"""

import pandas as pd
import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database.models import Base, create_student_with_features
from database.connection import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_csv_data(csv_path: str) -> pd.DataFrame:
    """Load and prepare CSV data for database insertion"""
    logger.info(f"Loading CSV data from {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} records from CSV")
        
        # Handle NaN values
        df = df.fillna({
            'registration_delay': 0.0,
            'early_total_clicks': 0.0,
            'early_avg_clicks': 0.0,
            'early_clicks_std': 0.0,
            'early_max_clicks': 0.0,
            'early_active_days': 0,
            'early_first_access': 0,
            'early_last_access': 0,
            'early_engagement_consistency': 0.0,
            'early_clicks_per_active_day': 0.0,
            'early_engagement_range': 0.0,
            'early_assessments_count': 0,
            'early_avg_score': 0.0,
            'early_score_std': 0.0,
            'early_min_score': 0.0,
            'early_max_score': 0.0,
            'early_missing_submissions': 0,
            'early_submitted_count': 0,
            'early_total_weight': 0.0,
            'early_banked_count': 0,
            'early_submission_rate': 0.0,
            'early_score_range': 0.0
        })
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to load CSV data: {e}")
        raise


def migrate_students_batch(db: Session, df: pd.DataFrame, batch_size: int = 1000):
    """Migrate students in batches for better performance"""
    total_records = len(df)
    logger.info(f"Migrating {total_records} students in batches of {batch_size}")
    
    successful_inserts = 0
    failed_inserts = 0
    
    for i in range(0, total_records, batch_size):
        batch_df = df.iloc[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_records + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_df)} records)")
        
        try:
            for _, row in batch_df.iterrows():
                try:
                    student_data = row.to_dict()
                    create_student_with_features(db, student_data)
                    successful_inserts += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert student {row.get('id_student', 'unknown')}: {e}")
                    failed_inserts += 1
                    db.rollback()
                    continue
            
            logger.info(f"Batch {batch_num} completed successfully")
            
        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
            db.rollback()
            continue
    
    logger.info(f"Migration completed: {successful_inserts} successful, {failed_inserts} failed")
    return successful_inserts, failed_inserts


def setup_database():
    """Setup database with schema"""
    try:
        # Try PostgreSQL first
        db_manager = DatabaseManager()
        
        if not db_manager.test_connection():
            logger.warning("PostgreSQL connection failed, using SQLite fallback")
            from database.connection import init_fallback_db
            sqlite_manager = init_fallback_db()
            return sqlite_manager
        
        # Create tables
        db_manager.create_tables()
        return db_manager
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        logger.info("Falling back to SQLite...")
        
        from database.connection import init_fallback_db
        sqlite_manager = init_fallback_db()
        return sqlite_manager


def main():
    """Main migration function"""
    # Paths
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "data" / "processed" / "student_features_engineered.csv"
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    try:
        # Load CSV data
        df = load_csv_data(str(csv_path))
        
        # Setup database
        db_manager = setup_database()
        
        # Migrate data
        with next(db_manager.get_session()) as db:
            successful, failed = migrate_students_batch(db, df)
            
            if successful > 0:
                logger.info(f"✅ Migration completed successfully!")
                logger.info(f"   - {successful} students migrated")
                logger.info(f"   - {failed} failed inserts")
                return True
            else:
                logger.error("❌ Migration failed - no records inserted")
                return False
                
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)