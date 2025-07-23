#!/usr/bin/env python3
"""
Production database setup and migration script
"""

import os
import sys
import logging
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database.models import Base
from database.connection import DatabaseManager
from scripts.migrate_csv_to_db import load_csv_data, migrate_students_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionDatabaseSetup:
    """Production database setup and migration"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.engine = create_engine(self.database_url)
        logger.info(f"Connecting to database: {self.database_url.split('@')[1] if '@' in self.database_url else 'local'}")
    
    def wait_for_database(self, max_retries=30, delay=2):
        """Wait for database to be ready"""
        logger.info("Waiting for database to be ready...")
        
        for attempt in range(max_retries):
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("✅ Database is ready!")
                return True
            except OperationalError as e:
                logger.info(f"Attempt {attempt + 1}/{max_retries}: Database not ready, retrying in {delay}s...")
                time.sleep(delay)
        
        raise Exception("Database failed to become ready within timeout")
    
    def create_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    def verify_tables(self):
        """Verify all tables were created"""
        logger.info("Verifying database tables...")
        
        expected_tables = [
            'students', 'student_engagement', 'student_assessments',
            'risk_predictions', 'interventions', 'student_outcomes'
        ]
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """))
                
                existing_tables = [row[0] for row in result]
                
                for table in expected_tables:
                    if table in existing_tables:
                        logger.info(f"✅ Table '{table}' exists")
                    else:
                        logger.error(f"❌ Table '{table}' missing")
                        return False
                
                logger.info("✅ All required tables verified")
                return True
                
        except Exception as e:
            logger.error(f"❌ Table verification failed: {e}")
            return False
    
    def create_indexes(self):
        """Create additional performance indexes"""
        logger.info("Creating performance indexes...")
        
        indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_students_module_year ON students(code_module, code_presentation);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_date_desc ON risk_predictions(prediction_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_risk_score ON risk_predictions(risk_score);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interventions_status_priority ON interventions(status, priority_level);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_outcomes_result ON student_outcomes(final_result);",
        ]
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SET maintenance_work_mem = '256MB';"))  # Optimize for index creation
                
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        logger.info(f"✅ Created index: {index_sql.split(' ')[5]}")
                    except Exception as e:
                        logger.warning(f"⚠️ Index creation failed (may already exist): {e}")
                
                conn.commit()
                logger.info("✅ Performance indexes created")
                
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
            raise
    
    def migrate_data(self, csv_path=None, batch_size=1000):
        """Migrate data from CSV if provided"""
        if not csv_path:
            csv_path = Path(__file__).parent.parent / "data" / "processed" / "student_features_engineered.csv"
        
        if not Path(csv_path).exists():
            logger.warning(f"⚠️ CSV file not found at {csv_path}, skipping data migration")
            return
        
        logger.info(f"Starting data migration from {csv_path}")
        
        try:
            # Load CSV data
            df = load_csv_data(str(csv_path))
            logger.info(f"Loaded {len(df)} records from CSV")
            
            # Use database manager for migration
            db_manager = DatabaseManager()
            
            with next(db_manager.get_session()) as db:
                successful, failed = migrate_students_batch(db, df, batch_size)
                
                logger.info(f"✅ Migration completed: {successful} successful, {failed} failed")
                
                if successful > 0:
                    return True
                else:
                    logger.error("❌ No records were migrated successfully")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False
    
    def setup_monitoring_tables(self):
        """Create additional tables for monitoring and analytics"""
        logger.info("Creating monitoring tables...")
        
        monitoring_tables = [
            """
            CREATE TABLE IF NOT EXISTS api_metrics (
                id SERIAL PRIMARY KEY,
                endpoint VARCHAR(255) NOT NULL,
                method VARCHAR(10) NOT NULL,
                response_time_ms FLOAT NOT NULL,
                status_code INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS model_performance (
                id SERIAL PRIMARY KEY,
                model_version VARCHAR(50) NOT NULL,
                accuracy FLOAT,
                precision_score FLOAT,
                recall FLOAT,
                f1_score FLOAT,
                auc_score FLOAT,
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS system_health (
                id SERIAL PRIMARY KEY,
                cpu_usage FLOAT,
                memory_usage FLOAT,
                disk_usage FLOAT,
                active_connections INTEGER,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        try:
            with self.engine.connect() as conn:
                for table_sql in monitoring_tables:
                    conn.execute(text(table_sql))
                conn.commit()
                
            logger.info("✅ Monitoring tables created")
            
        except Exception as e:
            logger.error(f"❌ Monitoring tables creation failed: {e}")
            raise

def main():
    """Main setup function"""
    logger.info("🚀 STARTING PRODUCTION DATABASE SETUP")
    logger.info("=" * 60)
    
    try:
        # Initialize setup
        setup = ProductionDatabaseSetup()
        
        # Wait for database to be ready
        setup.wait_for_database()
        
        # Create tables
        setup.create_tables()
        
        # Verify tables
        if not setup.verify_tables():
            raise Exception("Table verification failed")
        
        # Create performance indexes
        setup.create_indexes()
        
        # Setup monitoring tables
        setup.setup_monitoring_tables()
        
        # Migrate data (optional)
        migrate_data = os.getenv('MIGRATE_DATA', 'false').lower() == 'true'
        if migrate_data:
            setup.migrate_data()
        else:
            logger.info("⏭️ Data migration skipped (set MIGRATE_DATA=true to enable)")
        
        logger.info("🎉 PRODUCTION DATABASE SETUP COMPLETED SUCCESSFULLY!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Production database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)