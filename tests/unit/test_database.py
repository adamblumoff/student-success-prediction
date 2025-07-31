#!/usr/bin/env python3
"""
Unit tests for database operations in Student Success Prediction MVP system.

Tests both PostgreSQL and SQLite fallback functionality.
"""

import unittest
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from mvp.database import DatabaseConfig, get_db_session, init_database, check_database_health
from mvp.models import Institution, Student, Prediction, Intervention, AuditLog, ModelMetadata
from tests.fixtures.mock_data import SAMPLE_DATABASE_RECORDS

class TestDatabaseConfiguration(unittest.TestCase):
    """Test database configuration and connection management."""
    
    def setUp(self):
        """Set up test environment."""
        self.original_db_url = os.environ.get('DATABASE_URL')
        
    def tearDown(self):
        """Clean up test environment."""
        if self.original_db_url:
            os.environ['DATABASE_URL'] = self.original_db_url
        elif 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_sqlite_fallback_configuration(self):
        """Test SQLite fallback when PostgreSQL not configured."""
        # Remove PostgreSQL configuration
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        config = DatabaseConfig()
        self.assertTrue(config.database_url.startswith('sqlite:///'))
        self.assertIn('mvp_data.db', config.database_url)
    
    def test_postgresql_configuration(self):
        """Test PostgreSQL configuration from environment."""
        test_url = "postgresql://test:test@localhost:5432/test_db"
        os.environ['DATABASE_URL'] = test_url
        
        config = DatabaseConfig()
        self.assertEqual(config.database_url, test_url)
    
    def test_engine_creation(self):
        """Test SQLAlchemy engine creation."""
        config = DatabaseConfig()
        engine = config.create_engine()
        
        self.assertIsNotNone(engine)
        self.assertIsNotNone(config.engine)
    
    def test_session_factory_creation(self):
        """Test session factory creation."""
        config = DatabaseConfig()
        session_factory = config.create_session_factory()
        
        self.assertIsNotNone(session_factory)
        self.assertIsNotNone(config.session_factory)

class TestDatabaseOperations(unittest.TestCase):
    """Test basic database operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Use temporary SQLite database for testing
        cls.test_db_file = tempfile.mktemp(suffix='.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{cls.test_db_file}'
        
        # Initialize test database
        init_database()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if hasattr(cls, 'test_db_file') and os.path.exists(cls.test_db_file):
            os.unlink(cls.test_db_file)
        
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_database_health_check(self):
        """Test database health check functionality."""
        self.assertTrue(check_database_health())
    
    def test_session_context_manager(self):
        """Test database session context manager."""
        with get_db_session() as session:
            # Test that session is available
            self.assertIsNotNone(session)
            result = session.execute("SELECT 1")
            self.assertEqual(result.scalar(), 1)
    
    def test_session_rollback_on_error(self):
        """Test session rollback on error."""
        try:
            with get_db_session() as session:
                # This should cause an error and rollback
                session.execute("SELECT * FROM non_existent_table")
        except Exception:
            # Exception is expected, test that system handles it
            pass
        
        # Verify database is still functional after error
        self.assertTrue(check_database_health())

class TestDatabaseModels(unittest.TestCase):
    """Test database model operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.test_db_file = tempfile.mktemp(suffix='.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{cls.test_db_file}'
        init_database()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if hasattr(cls, 'test_db_file') and os.path.exists(cls.test_db_file):
            os.unlink(cls.test_db_file)
        
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_institution_creation(self):
        """Test institution model creation."""
        with get_db_session() as session:
            institution = Institution(
                name="Test Institution",
                code="TEST001",
                type="K12"
            )
            session.add(institution)
            session.commit()
            
            # Verify creation
            saved_institution = session.query(Institution).filter_by(code="TEST001").first()
            self.assertIsNotNone(saved_institution)
            self.assertEqual(saved_institution.name, "Test Institution")
            self.assertEqual(saved_institution.type, "K12")
            self.assertTrue(saved_institution.active)
    
    def test_student_creation(self):
        """Test student model creation."""
        with get_db_session() as session:
            # Create institution first
            institution = Institution(name="Test School", code="TESTSCH", type="K12")
            session.add(institution)
            session.flush()
            
            # Create student
            student = Student(
                institution_id=institution.id,
                student_id="S12345",
                grade_level="9",
                enrollment_status="active",
                is_ell=False,
                has_iep=True,
                has_504=False,
                is_economically_disadvantaged=True
            )
            session.add(student)
            session.commit()
            
            # Verify creation
            saved_student = session.query(Student).filter_by(student_id="S12345").first()
            self.assertIsNotNone(saved_student)
            self.assertEqual(saved_student.grade_level, "9")
            self.assertTrue(saved_student.has_iep)
            self.assertTrue(saved_student.is_economically_disadvantaged)
    
    def test_prediction_creation(self):
        """Test prediction model creation."""
        with get_db_session() as session:
            # Create institution and student
            institution = Institution(name="Test School", code="PREDSCH", type="K12")
            session.add(institution)
            session.flush()
            
            student = Student(
                institution_id=institution.id,
                student_id="S67890",
                enrollment_status="active"
            )
            session.add(student)
            session.flush()
            
            # Create prediction
            prediction = Prediction(
                institution_id=institution.id,
                student_id=student.id,
                risk_score=0.75,
                risk_category="High Risk",
                success_probability=0.25,
                confidence_score=0.82,
                model_version="1.0",
                model_type="binary",
                session_id="test_session",
                data_source="test",
                features_used=json.dumps({"test": "features"}),
                explanation=json.dumps({"explanation": "test explanation"})
            )
            session.add(prediction)
            session.commit()
            
            # Verify creation
            saved_prediction = session.query(Prediction).filter_by(session_id="test_session").first()
            self.assertIsNotNone(saved_prediction)
            self.assertEqual(saved_prediction.risk_score, 0.75)
            self.assertEqual(saved_prediction.risk_category, "High Risk")
            self.assertIsNotNone(saved_prediction.features_used)
    
    def test_intervention_creation(self):
        """Test intervention model creation."""
        with get_db_session() as session:
            # Create required records
            institution = Institution(name="Test School", code="INTSCH", type="K12")
            session.add(institution)
            session.flush()
            
            student = Student(
                institution_id=institution.id,
                student_id="S11111",
                enrollment_status="active"
            )
            session.add(student)
            session.flush()
            
            # Create intervention
            intervention = Intervention(
                institution_id=institution.id,
                student_id=student.id,
                intervention_type="academic_support",
                title="Math Tutoring",
                description="Weekly math tutoring sessions",
                priority="High",
                status="planned",
                assigned_to="Ms. Johnson",
                estimated_cost=100.0,
                time_spent_minutes=60
            )
            session.add(intervention)
            session.commit()
            
            # Verify creation
            saved_intervention = session.query(Intervention).filter_by(title="Math Tutoring").first()
            self.assertIsNotNone(saved_intervention)
            self.assertEqual(saved_intervention.intervention_type, "academic_support")
            self.assertEqual(saved_intervention.priority, "High")
            self.assertEqual(saved_intervention.status, "planned")
    
    def test_audit_log_creation(self):
        """Test audit log model creation."""
        with get_db_session() as session:
            # Create institution
            institution = Institution(name="Test School", code="AUDITSCH", type="K12")
            session.add(institution)
            session.flush()
            
            # Create audit log
            audit_log = AuditLog(
                institution_id=institution.id,
                user_id="test_user",
                user_email="test@example.com",
                user_role="teacher",
                action="view_student",
                resource_type="student",
                resource_id="S12345",
                ip_address="127.0.0.1",
                user_agent="Test Browser",
                session_id="test_session",
                request_method="GET",
                request_path="/api/student/12345",
                response_status=200,
                processing_time_ms=45
            )
            session.add(audit_log)
            session.commit()
            
            # Verify creation
            saved_log = session.query(AuditLog).filter_by(user_id="test_user").first()
            self.assertIsNotNone(saved_log)
            self.assertEqual(saved_log.action, "view_student")
            self.assertEqual(saved_log.response_status, 200)
    
    def test_model_metadata_creation(self):
        """Test model metadata creation."""
        with get_db_session() as session:
            # Create institution
            institution = Institution(name="Test School", code="MODELSCH", type="K12")
            session.add(institution)
            session.flush()
            
            # Create model metadata
            metadata = ModelMetadata(
                institution_id=institution.id,
                model_name="K12_Ultra_Advanced",
                model_version="2.1",
                model_type="global",
                accuracy=0.845,
                auc_score=0.815,
                f1_score=0.782,
                precision_score=0.801,
                recall_score=0.765,
                training_data_size=15000,
                training_features=json.dumps(["gpa", "attendance", "engagement"]),
                hyperparameters=json.dumps({"learning_rate": 0.01, "epochs": 100}),
                feature_engineering_version="3.2",
                is_active=True
            )
            session.add(metadata)
            session.commit()
            
            # Verify creation
            saved_metadata = session.query(ModelMetadata).filter_by(model_name="K12_Ultra_Advanced").first()
            self.assertIsNotNone(saved_metadata)
            self.assertEqual(saved_metadata.auc_score, 0.815)
            self.assertTrue(saved_metadata.is_active)

class TestBatchDatabaseOperations(unittest.TestCase):
    """Test batch database operations for performance."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.test_db_file = tempfile.mktemp(suffix='.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{cls.test_db_file}'
        init_database()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if hasattr(cls, 'test_db_file') and os.path.exists(cls.test_db_file):
            os.unlink(cls.test_db_file)
        
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_batch_institution_creation(self):
        """Test batch creation of institutions."""
        # Create unique institutions for this test to avoid constraint conflicts
        unique_institutions_data = [
            {'name': f'Batch Test High School {i}', 'code': f'BTHS{i:03d}', 'type': 'K12'}
            for i in range(3)
        ]
        
        with get_db_session() as session:
            # Check if institutions already exist and skip if they do
            existing_codes = {inst.code for inst in session.query(Institution).all()}
            new_institutions_data = [inst for inst in unique_institutions_data 
                                   if inst['code'] not in existing_codes]
            
            if new_institutions_data:
                # Batch insert institutions
                institutions = [Institution(**data) for data in new_institutions_data]
                session.add_all(institutions)
                session.commit()
            
            # Verify creation (count institutions with our test pattern)
            count = session.query(Institution).filter(Institution.code.like('BTHS%')).count()
            self.assertGreaterEqual(count, len(unique_institutions_data))
    
    def test_batch_student_creation(self):
        """Test batch creation of students."""
        students_data = SAMPLE_DATABASE_RECORDS['students'][:10]  # Test with smaller subset
        
        with get_db_session() as session:
            # Ensure institutions exist
            institutions = session.query(Institution).all()
            if not institutions:
                self.skipTest("No institutions available for student creation")
            
            # Batch insert students
            students = [Student(**data) for data in students_data]
            session.add_all(students)
            session.commit()
            
            # Verify batch creation
            count = session.query(Student).count()
            self.assertGreaterEqual(count, len(students_data))
    
    def test_batch_prediction_creation(self):
        """Test batch creation of predictions."""
        with get_db_session() as session:
            # Ensure we have institutions and students
            institution_count = session.query(Institution).count()
            student_count = session.query(Student).count()
            
            if institution_count == 0 or student_count == 0:
                self.skipTest("No institutions or students available for prediction creation")
            
            # Create batch predictions
            predictions_data = SAMPLE_DATABASE_RECORDS['predictions'][:10]
            predictions = [Prediction(**data) for data in predictions_data]
            session.add_all(predictions)
            session.commit()
            
            # Verify batch creation
            count = session.query(Prediction).count()
            self.assertGreaterEqual(count, len(predictions_data))

class TestDatabasePerformance(unittest.TestCase):
    """Test database performance characteristics."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.test_db_file = tempfile.mktemp(suffix='.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{cls.test_db_file}'
        init_database()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if hasattr(cls, 'test_db_file') and os.path.exists(cls.test_db_file):
            os.unlink(cls.test_db_file)
        
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_query_performance_with_indexes(self):
        """Test that indexed queries perform efficiently."""
        with get_db_session() as session:
            # Create test institution
            institution = Institution(name="Performance Test", code="PERF001", type="K12")
            session.add(institution)
            session.flush()
            
            # Create multiple students for performance testing
            students = []
            for i in range(50):
                student = Student(
                    institution_id=institution.id,
                    student_id=f"PERF{i:03d}",
                    grade_level=str((i % 4) + 9),
                    enrollment_status="active"
                )
                students.append(student)
            
            session.add_all(students)
            session.commit()
            
            # Test indexed query performance
            import time
            start_time = time.time()
            
            result = session.query(Student).filter(
                Student.institution_id == institution.id,
                Student.enrollment_status == "active"
            ).all()
            
            query_time = time.time() - start_time
            
            # Verify results and performance
            self.assertEqual(len(result), 50)
            self.assertLess(query_time, 1.0, "Query took too long - index may not be working")

if __name__ == '__main__':
    unittest.main()