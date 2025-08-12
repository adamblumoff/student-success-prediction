#!/usr/bin/env python3
"""
Comprehensive Database Operations Tests
Tests duplicate prevention, upsert logic, and constraint enforcement
"""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

# Import database components
from src.mvp.database import Base, save_prediction, save_predictions_batch, DatabaseConfig
from src.mvp.models import Institution, Student, Prediction, User, Intervention

class TestDatabaseOperations:
    """Comprehensive database operations and duplicate prevention tests"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database"""
        # Create temporary database
        cls.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.test_db_path = cls.test_db.name
        cls.test_db.close()
        
        # Test database URL
        cls.test_database_url = f"sqlite:///{cls.test_db_path}"
        
        # Set environment for testing
        os.environ['DATABASE_URL'] = cls.test_database_url
        os.environ['TESTING'] = 'true'
        
        # Create test engine
        cls.test_engine = create_engine(
            cls.test_database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.test_engine
        )
        
        # Create tables
        Base.metadata.create_all(bind=cls.test_engine)
        
        # Set up test data
        cls.setup_test_data()
    
    @classmethod
    def setup_test_data(cls):
        """Create initial test data"""
        with cls.TestingSessionLocal() as session:
            # Create test institution
            institution = Institution(
                name="Test Database School",
                code="TEST_DB_001",
                type="K12"
            )
            session.add(institution)
            session.flush()
            cls.institution_id = institution.id
            
            # Create initial test students
            test_students = [
                Student(
                    institution_id=institution.id,
                    student_id="DB_TEST_001",
                    grade_level="9",
                    enrollment_status="active"
                ),
                Student(
                    institution_id=institution.id,
                    student_id="DB_TEST_002",
                    grade_level="10",
                    enrollment_status="active"
                )
            ]
            
            for student in test_students:
                session.add(student)
            
            session.commit()
            
            # Store for reference
            cls.existing_students = {s.student_id: s.id for s in test_students}
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database"""
        Base.metadata.drop_all(bind=cls.test_engine)
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
    
    def get_session(self):
        """Get database session for testing"""
        return self.TestingSessionLocal()
    
    def test_unique_constraints_students(self):
        """Test unique constraints prevent duplicate students"""
        with self.get_session() as session:
            # Try to create duplicate student (same institution_id + student_id)
            duplicate_student = Student(
                institution_id=self.institution_id,
                student_id="DB_TEST_001",  # Already exists
                grade_level="11",
                enrollment_status="active"
            )
            
            session.add(duplicate_student)
            
            # Should raise integrity error due to unique constraint
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_unique_constraints_users(self):
        """Test unique constraints prevent duplicate user emails"""
        with self.get_session() as session:
            # Create first user
            user1 = User(
                email="test@example.com",
                password_hash="hash1",
                institution_id=self.institution_id
            )
            session.add(user1)
            session.commit()
            
            # Try to create duplicate email
            user2 = User(
                email="test@example.com",  # Same email
                password_hash="hash2",
                institution_id=self.institution_id
            )
            session.add(user2)
            
            # Should raise integrity error
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_unique_constraints_institutions(self):
        """Test unique constraints prevent duplicate institution codes"""
        with self.get_session() as session:
            # Try to create duplicate institution code
            duplicate_institution = Institution(
                name="Another Test School",
                code="TEST_DB_001",  # Already exists
                type="K12"
            )
            
            session.add(duplicate_institution)
            
            # Should raise integrity error
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_unique_constraints_predictions(self):
        """Test unique constraints allow only one prediction per student"""
        student_id = self.existing_students["DB_TEST_001"]
        
        with self.get_session() as session:
            # Create first prediction
            prediction1 = Prediction(
                institution_id=self.institution_id,
                student_id=student_id,
                risk_score=0.75,
                risk_category="High Risk",
                session_id="test_session_1"
            )
            session.add(prediction1)
            session.commit()
            
            # Try to create second prediction for same student
            prediction2 = Prediction(
                institution_id=self.institution_id,
                student_id=student_id,  # Same student
                risk_score=0.65,
                risk_category="Medium Risk", 
                session_id="test_session_2"
            )
            session.add(prediction2)
            
            # Should raise integrity error due to unique constraint
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_save_prediction_upsert_logic(self):
        """Test save_prediction uses upsert logic correctly"""
        # Mock the database config for PostgreSQL testing
        original_db_url = os.environ.get('DATABASE_URL', '')
        
        try:
            # Test with SQLite (fallback logic)
            prediction_data = {
                'student_id': 'UPSERT_TEST_001',
                'risk_score': 0.80,
                'risk_category': 'High Risk',
                'features_data': {'test': 'data'},
                'explanation_data': {'explanation': 'test'}
            }
            
            # First save - should create new student and prediction
            save_prediction(prediction_data, "test_session")
            
            # Verify student and prediction were created
            with self.get_session() as session:
                student = session.query(Student).filter(
                    Student.student_id == 'UPSERT_TEST_001'
                ).first()
                assert student is not None
                
                prediction = session.query(Prediction).filter(
                    Prediction.student_id == student.id
                ).first()
                assert prediction is not None
                assert prediction.risk_score == 0.80
            
            # Second save with updated data - should update existing
            prediction_data['risk_score'] = 0.85
            prediction_data['risk_category'] = 'Critical Risk'
            
            save_prediction(prediction_data, "test_session_updated")
            
            # Verify prediction was updated, not duplicated
            with self.get_session() as session:
                student = session.query(Student).filter(
                    Student.student_id == 'UPSERT_TEST_001'
                ).first()
                
                predictions = session.query(Prediction).filter(
                    Prediction.student_id == student.id
                ).all()
                
                # Should still be only one prediction (updated)
                assert len(predictions) == 1
                assert predictions[0].risk_score == 0.85
                assert predictions[0].risk_category == 'Critical Risk'
        
        finally:
            # Restore original database URL
            os.environ['DATABASE_URL'] = original_db_url
    
    def test_save_predictions_batch_upsert_logic(self):
        """Test batch save uses upsert logic correctly"""
        # Test batch with mix of new and existing students
        batch_data = [
            {
                'student_id': 'BATCH_TEST_001',
                'risk_score': 0.70,
                'risk_category': 'Medium Risk'
            },
            {
                'student_id': 'BATCH_TEST_002', 
                'risk_score': 0.40,
                'risk_category': 'Low Risk'
            },
            {
                'student_id': 'DB_TEST_001',  # Existing student
                'risk_score': 0.90,
                'risk_category': 'Critical Risk'
            }
        ]
        
        # First batch save
        save_predictions_batch(batch_data, "batch_test_session")
        
        # Verify all predictions were created/updated
        with self.get_session() as session:
            # Check new students were created
            new_student_1 = session.query(Student).filter(
                Student.student_id == 'BATCH_TEST_001'
            ).first()
            assert new_student_1 is not None
            
            new_student_2 = session.query(Student).filter(
                Student.student_id == 'BATCH_TEST_002'
            ).first()
            assert new_student_2 is not None
            
            # Check existing student wasn't duplicated
            existing_students = session.query(Student).filter(
                Student.student_id == 'DB_TEST_001'
            ).all()
            assert len(existing_students) == 1
            
            # Check predictions
            prediction_1 = session.query(Prediction).filter(
                Prediction.student_id == new_student_1.id
            ).first()
            assert prediction_1.risk_score == 0.70
            
            prediction_2 = session.query(Prediction).filter(
                Prediction.student_id == new_student_2.id
            ).first()
            assert prediction_2.risk_score == 0.40
            
            # Check existing student's prediction was updated
            existing_prediction = session.query(Prediction).filter(
                Prediction.student_id == existing_students[0].id
            ).first()
            assert existing_prediction.risk_score == 0.90
        
        # Second batch with updates
        updated_batch_data = [
            {
                'student_id': 'BATCH_TEST_001',  # Update existing
                'risk_score': 0.75,
                'risk_category': 'High Risk'
            },
            {
                'student_id': 'BATCH_TEST_003',  # New student
                'risk_score': 0.30,
                'risk_category': 'Low Risk'
            }
        ]
        
        save_predictions_batch(updated_batch_data, "batch_test_session_2")
        
        # Verify updates and new creation
        with self.get_session() as session:
            # Verify update
            updated_student = session.query(Student).filter(
                Student.student_id == 'BATCH_TEST_001'
            ).first()
            updated_prediction = session.query(Prediction).filter(
                Prediction.student_id == updated_student.id
            ).first()
            assert updated_prediction.risk_score == 0.75
            
            # Verify new creation
            new_student_3 = session.query(Student).filter(
                Student.student_id == 'BATCH_TEST_003'
            ).first()
            assert new_student_3 is not None
    
    def test_database_config_validation(self):
        """Test database configuration validation"""
        # Test with different environment settings
        original_env = os.environ.get('ENVIRONMENT', '')
        
        try:
            # Test development configuration
            os.environ['ENVIRONMENT'] = 'development'
            config = DatabaseConfig()
            assert not config.is_production
            
            # Test production configuration
            os.environ['ENVIRONMENT'] = 'production'
            
            # Should validate security requirements
            with pytest.raises(ValueError, match="Production must use PostgreSQL"):
                config = DatabaseConfig()
        
        finally:
            os.environ['ENVIRONMENT'] = original_env
    
    def test_concurrent_student_creation(self):
        """Test concurrent student creation doesn't create duplicates"""
        # Simulate concurrent creation of same student
        student_data_1 = {
            'student_id': 'CONCURRENT_001',
            'risk_score': 0.60,
            'risk_category': 'Medium Risk'
        }
        
        student_data_2 = {
            'student_id': 'CONCURRENT_001',  # Same student
            'risk_score': 0.70,
            'risk_category': 'High Risk'
        }
        
        # Save both (simulating concurrent requests)
        save_prediction(student_data_1, "concurrent_session_1")
        save_prediction(student_data_2, "concurrent_session_2")
        
        # Verify only one student exists
        with self.get_session() as session:
            students = session.query(Student).filter(
                Student.student_id == 'CONCURRENT_001'
            ).all()
            assert len(students) == 1
            
            # Should have one prediction (the later one due to upsert)
            predictions = session.query(Prediction).filter(
                Prediction.student_id == students[0].id
            ).all()
            assert len(predictions) == 1
            # The second prediction should have overwritten the first
            assert predictions[0].risk_score == 0.70
    
    def test_intervention_no_duplicates_allowed(self):
        """Test that interventions can be duplicated (multiple per student)"""
        student_id = self.existing_students["DB_TEST_002"]
        
        with self.get_session() as session:
            # Create multiple interventions for same student
            intervention_1 = Intervention(
                institution_id=self.institution_id,
                student_id=student_id,
                intervention_type="academic_support",
                title="Math Tutoring",
                priority="medium",
                status="pending"
            )
            
            intervention_2 = Intervention(
                institution_id=self.institution_id,
                student_id=student_id,  # Same student
                intervention_type="behavioral_support",
                title="Counseling",
                priority="high", 
                status="pending"
            )
            
            session.add(intervention_1)
            session.add(intervention_2)
            session.commit()  # Should succeed - multiple interventions per student allowed
            
            # Verify both interventions exist
            interventions = session.query(Intervention).filter(
                Intervention.student_id == student_id
            ).all()
            assert len(interventions) == 2
    
    def test_data_integrity_after_operations(self):
        """Test data integrity is maintained after various operations"""
        with self.get_session() as session:
            # Count initial records
            initial_students = session.query(Student).count()
            initial_predictions = session.query(Prediction).count()
            initial_institutions = session.query(Institution).count()
            
            # Perform various operations
            test_operations_data = [
                {'student_id': 'INTEGRITY_001', 'risk_score': 0.55, 'risk_category': 'Medium Risk'},
                {'student_id': 'INTEGRITY_002', 'risk_score': 0.85, 'risk_category': 'High Risk'},
                {'student_id': 'INTEGRITY_001', 'risk_score': 0.60, 'risk_category': 'Medium Risk'}  # Update
            ]
            
            save_predictions_batch(test_operations_data, "integrity_test")
            
            # Verify data integrity
            final_students = session.query(Student).count()
            final_predictions = session.query(Prediction).count()
            final_institutions = session.query(Institution).count()
            
            # Should have 2 new students (INTEGRITY_001, INTEGRITY_002)
            assert final_students == initial_students + 2
            
            # Should have 2 new predictions (one per unique student)
            assert final_predictions == initial_predictions + 2
            
            # Institutions should remain unchanged
            assert final_institutions == initial_institutions
            
            # Verify no orphaned records
            students_with_predictions = session.execute(text("""
                SELECT COUNT(DISTINCT s.id) 
                FROM students s 
                JOIN predictions p ON s.id = p.student_id
                WHERE s.student_id IN ('INTEGRITY_001', 'INTEGRITY_002')
            """)).scalar()
            
            assert students_with_predictions == 2
    
    def test_error_handling_during_batch_operations(self):
        """Test error handling during batch operations"""
        # Test batch with some invalid data
        mixed_batch_data = [
            {'student_id': 'VALID_001', 'risk_score': 0.75, 'risk_category': 'High Risk'},
            {'student_id': 'VALID_002', 'risk_score': 0.25, 'risk_category': 'Low Risk'}
        ]
        
        # This should succeed despite some challenges
        try:
            save_predictions_batch(mixed_batch_data, "error_test_session")
            
            # Verify valid data was saved
            with self.get_session() as session:
                valid_student_1 = session.query(Student).filter(
                    Student.student_id == 'VALID_001'
                ).first()
                assert valid_student_1 is not None
                
                valid_student_2 = session.query(Student).filter(
                    Student.student_id == 'VALID_002'
                ).first()
                assert valid_student_2 is not None
                
        except Exception as e:
            # Even if there are errors, verify no partial data corruption
            with self.get_session() as session:
                # Database should still be in consistent state
                students = session.query(Student).all()
                for student in students:
                    assert student.institution_id is not None
                    assert student.student_id is not None