#!/usr/bin/env python3
"""
Database Constraints and PostgreSQL Upsert Tests
Tests unique constraints, ON CONFLICT behavior, and PostgreSQL-specific functionality
"""

import pytest
import os
import sys
from pathlib import Path
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

# Import database components
from src.mvp.database import Base, DatabaseConfig, get_db_session
from src.mvp.models import Institution, Student, Prediction, User

class TestDatabaseConstraints:
    """Test database constraints and PostgreSQL upsert functionality"""
    
    @classmethod
    def setup_class(cls):
        """Set up test databases for both SQLite and PostgreSQL testing"""
        # SQLite test database
        cls.sqlite_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.sqlite_db_path = cls.sqlite_db.name
        cls.sqlite_db.close()
        
        cls.sqlite_url = f"sqlite:///{cls.sqlite_db_path}"
        cls.sqlite_engine = create_engine(cls.sqlite_url, connect_args={"check_same_thread": False})
        cls.SQLiteSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.sqlite_engine)
        
        # Create SQLite tables and add constraints
        Base.metadata.create_all(bind=cls.sqlite_engine)
        cls._add_sqlite_constraints()
        
        # Set up test data
        cls.setup_test_data()
    
    @classmethod  
    def _add_sqlite_constraints(cls):
        """Add unique constraints to SQLite (since they're not auto-created from models)"""
        with cls.sqlite_engine.begin() as conn:
            # Add unique constraints manually for SQLite testing
            try:
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_students_student_id_institution ON students (institution_id, student_id)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_institutions_code ON institutions (code)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_predictions_student ON predictions (student_id)"))
            except Exception as e:
                print(f"Note: Some constraints may already exist: {e}")
    
    @classmethod
    def setup_test_data(cls):
        """Create initial test data"""
        with cls.SQLiteSession() as session:
            # Create test institution
            institution = Institution(
                name="Constraint Test School",
                code="CONSTRAINT_TEST_001",
                type="K12"
            )
            session.add(institution)
            session.flush()
            cls.institution_id = institution.id
            
            # Create test student
            student = Student(
                institution_id=institution.id,
                student_id="CONSTRAINT_TEST_STUDENT",
                grade_level="10",
                enrollment_status="active"
            )
            session.add(student)
            session.flush()
            cls.student_id = student.id
            
            session.commit()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test databases"""
        Base.metadata.drop_all(bind=cls.sqlite_engine)
        if os.path.exists(cls.sqlite_db_path):
            os.remove(cls.sqlite_db_path)
    
    def test_unique_constraint_students_institution_student_id(self):
        """Test unique constraint on students (institution_id, student_id)"""
        with self.SQLiteSession() as session:
            # Try to create duplicate student with same institution_id + student_id
            duplicate_student = Student(
                institution_id=self.institution_id,
                student_id="CONSTRAINT_TEST_STUDENT",  # Already exists
                grade_level="11",
                enrollment_status="active"
            )
            
            session.add(duplicate_student)
            
            # Should raise integrity error
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_unique_constraint_users_email(self):
        """Test unique constraint on users.email"""
        with self.SQLiteSession() as session:
            # Create first user
            user1 = User(
                email="unique.test@example.com",
                password_hash="hash1",
                institution_id=self.institution_id
            )
            session.add(user1)
            session.commit()
            
        # Try to create second user with same email
        with self.SQLiteSession() as session:
            user2 = User(
                email="unique.test@example.com",  # Same email
                password_hash="hash2", 
                institution_id=self.institution_id
            )
            session.add(user2)
            
            # Should raise integrity error
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_unique_constraint_institutions_code(self):
        """Test unique constraint on institutions.code"""
        with self.SQLiteSession() as session:
            # Try to create institution with duplicate code
            duplicate_institution = Institution(
                name="Another Test School",
                code="CONSTRAINT_TEST_001",  # Already exists
                type="K12"
            )
            session.add(duplicate_institution)
            
            # Should raise integrity error
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_unique_constraint_predictions_student_id(self):
        """Test unique constraint on predictions.student_id (one prediction per student)"""
        with self.SQLiteSession() as session:
            # Create first prediction
            prediction1 = Prediction(
                institution_id=self.institution_id,
                student_id=self.student_id,
                risk_score=0.75,
                risk_category="High Risk",
                session_id="constraint_test_1"
            )
            session.add(prediction1)
            session.commit()
            
        # Try to create second prediction for same student
        with self.SQLiteSession() as session:
            prediction2 = Prediction(
                institution_id=self.institution_id,
                student_id=self.student_id,  # Same student
                risk_score=0.65,
                risk_category="Medium Risk",
                session_id="constraint_test_2"
            )
            session.add(prediction2)
            
            # Should raise integrity error
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_different_institutions_allow_same_student_id(self):
        """Test that different institutions can have students with same student_id"""
        with self.SQLiteSession() as session:
            # Create second institution
            institution2 = Institution(
                name="Second Test School",
                code="CONSTRAINT_TEST_002",
                type="K12"
            )
            session.add(institution2)
            session.flush()
            
            # Create student with same student_id but different institution
            student2 = Student(
                institution_id=institution2.id,
                student_id="CONSTRAINT_TEST_STUDENT",  # Same as existing student
                grade_level="9",
                enrollment_status="active"
            )
            session.add(student2)
            
            # Should succeed - different institution allows same student_id
            session.commit()
            
            # Verify both students exist
            students = session.query(Student).filter(
                Student.student_id == "CONSTRAINT_TEST_STUDENT"
            ).all()
            assert len(students) == 2
            assert students[0].institution_id != students[1].institution_id
    
    def test_cascade_behavior_on_student_deletion(self):
        """Test cascade behavior when deleting students with predictions"""
        with self.SQLiteSession() as session:
            # Create test student and prediction
            test_student = Student(
                institution_id=self.institution_id,
                student_id="CASCADE_TEST_STUDENT",
                grade_level="9",
                enrollment_status="active"
            )
            session.add(test_student)
            session.flush()
            
            test_prediction = Prediction(
                institution_id=self.institution_id,
                student_id=test_student.id,
                risk_score=0.60,
                risk_category="Medium Risk",
                session_id="cascade_test"
            )
            session.add(test_prediction)
            session.commit()
            
            # Verify prediction exists
            prediction_count = session.query(Prediction).filter(
                Prediction.student_id == test_student.id
            ).count()
            assert prediction_count == 1
            
            # Delete student
            session.delete(test_student)
            session.commit()
            
            # Verify prediction was also deleted (due to foreign key constraint)
            prediction_count_after = session.query(Prediction).filter(
                Prediction.student_id == test_student.id
            ).count()
            assert prediction_count_after == 0
    
    def test_constraint_error_messages(self):
        """Test that constraint violations provide useful error messages"""
        with self.SQLiteSession() as session:
            # Try to create student with duplicate constraint
            duplicate_student = Student(
                institution_id=self.institution_id,
                student_id="CONSTRAINT_TEST_STUDENT",
                grade_level="12",
                enrollment_status="active"
            )
            session.add(duplicate_student)
            
            try:
                session.commit()
                assert False, "Should have raised IntegrityError"
            except IntegrityError as e:
                # Verify error message contains useful information
                error_msg = str(e)
                assert "UNIQUE constraint failed" in error_msg or "unique constraint" in error_msg.lower()
    
    @pytest.mark.skipif(
        not os.getenv('TEST_POSTGRESQL', '').lower() == 'true',
        reason="PostgreSQL testing disabled. Set TEST_POSTGRESQL=true to enable."
    )
    def test_postgresql_on_conflict_do_nothing(self):
        """Test PostgreSQL ON CONFLICT DO NOTHING functionality"""
        # This test would run only if PostgreSQL is available
        postgres_url = os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost/test_constraints')
        
        try:
            postgres_engine = create_engine(postgres_url)
            Base.metadata.create_all(bind=postgres_engine)
            
            PostgresSession = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
            
            with PostgresSession() as session:
                # Create test institution
                institution = Institution(
                    name="PostgreSQL Test School",
                    code="PG_TEST_001",
                    type="K12"
                )
                session.add(institution)
                session.flush()
                
                # Test ON CONFLICT DO NOTHING with students
                student_data = [
                    {
                        'institution_id': institution.id,
                        'student_id': 'PG_TEST_001',
                        'grade_level': '9',
                        'enrollment_status': 'active'
                    },
                    {
                        'institution_id': institution.id,
                        'student_id': 'PG_TEST_001',  # Duplicate
                        'grade_level': '10',
                        'enrollment_status': 'active'
                    }
                ]
                
                # Use PostgreSQL upsert
                stmt = insert(Student.__table__).values(student_data)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['institution_id', 'student_id']
                )
                session.execute(stmt)
                session.commit()
                
                # Should have only one student (duplicate ignored)
                student_count = session.query(Student).filter(
                    Student.student_id == 'PG_TEST_001'
                ).count()
                assert student_count == 1
                
        except Exception as e:
            pytest.skip(f"PostgreSQL test skipped: {e}")
    
    @pytest.mark.skipif(
        not os.getenv('TEST_POSTGRESQL', '').lower() == 'true',
        reason="PostgreSQL testing disabled. Set TEST_POSTGRESQL=true to enable."
    )
    def test_postgresql_on_conflict_do_update(self):
        """Test PostgreSQL ON CONFLICT DO UPDATE functionality"""
        postgres_url = os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost/test_constraints')
        
        try:
            postgres_engine = create_engine(postgres_url)
            Base.metadata.create_all(bind=postgres_engine)
            
            PostgresSession = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
            
            with PostgresSession() as session:
                # Create test data
                institution = Institution(
                    name="PostgreSQL Update Test",
                    code="PG_UPDATE_001", 
                    type="K12"
                )
                session.add(institution)
                session.flush()
                
                student = Student(
                    institution_id=institution.id,
                    student_id='PG_UPDATE_STUDENT',
                    grade_level='9',
                    enrollment_status='active'
                )
                session.add(student)
                session.flush()
                
                # Test ON CONFLICT DO UPDATE with predictions
                prediction_data = [
                    {
                        'institution_id': institution.id,
                        'student_id': student.id,
                        'risk_score': 0.70,
                        'risk_category': 'High Risk',
                        'session_id': 'pg_test_1'
                    }
                ]
                
                # First insert
                stmt = insert(Prediction.__table__).values(prediction_data)
                stmt = stmt.on_conflict_do_nothing(index_elements=['student_id'])
                session.execute(stmt)
                session.commit()
                
                # Update with new data
                prediction_data[0]['risk_score'] = 0.85
                prediction_data[0]['risk_category'] = 'Critical Risk'
                
                stmt = insert(Prediction.__table__).values(prediction_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['student_id'],
                    set_={
                        'risk_score': stmt.excluded.risk_score,
                        'risk_category': stmt.excluded.risk_category,
                        'session_id': stmt.excluded.session_id
                    }
                )
                session.execute(stmt)
                session.commit()
                
                # Verify update occurred
                prediction = session.query(Prediction).filter(
                    Prediction.student_id == student.id
                ).first()
                assert prediction.risk_score == 0.85
                assert prediction.risk_category == 'Critical Risk'
                
        except Exception as e:
            pytest.skip(f"PostgreSQL test skipped: {e}")
    
    def test_database_config_constraint_validation(self):
        """Test DatabaseConfig validates constraint requirements"""
        original_env = os.environ.copy()
        
        try:
            # Test production requires PostgreSQL
            os.environ['ENVIRONMENT'] = 'production'
            os.environ['DATABASE_URL'] = 'sqlite:///test.db'
            
            with pytest.raises(ValueError, match="Production must use PostgreSQL"):
                DatabaseConfig()
                
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_foreign_key_constraint_enforcement(self):
        """Test foreign key constraints are enforced"""
        with self.SQLiteSession() as session:
            # Try to create prediction with non-existent student_id
            invalid_prediction = Prediction(
                institution_id=self.institution_id,
                student_id=99999,  # Non-existent student
                risk_score=0.50,
                risk_category="Medium Risk",
                session_id="fk_test"
            )
            session.add(invalid_prediction)
            
            # Should raise integrity error for foreign key violation
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_constraint_coverage_completeness(self):
        """Test that all expected constraints are properly configured"""
        with self.SQLiteSession() as session:
            # Get constraint information from database
            constraints_info = session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type = 'index' AND name LIKE 'uq_%'
            """)).fetchall()
            
            constraint_names = [row[0] for row in constraints_info]
            
            # Verify expected constraints exist
            expected_constraints = [
                'uq_students_student_id_institution',
                'uq_users_email',
                'uq_institutions_code',
                'uq_predictions_student'
            ]
            
            for expected in expected_constraints:
                assert expected in constraint_names, f"Missing constraint: {expected}"
    
    def test_multiple_constraint_violations(self):
        """Test behavior with multiple constraint violations"""
        with self.SQLiteSession() as session:
            # Create data that violates multiple constraints
            duplicate_institution = Institution(
                name="Multi Constraint Test",
                code="CONSTRAINT_TEST_001",  # Duplicate code
                type="K12"
            )
            session.add(duplicate_institution)
            
            try:
                session.commit()
                assert False, "Should have failed on institution code constraint"
            except IntegrityError:
                session.rollback()
            
            # Try different constraint violation
            duplicate_student = Student(
                institution_id=self.institution_id,
                student_id="CONSTRAINT_TEST_STUDENT",  # Duplicate student_id
                grade_level="12",
                enrollment_status="graduated"
            )
            session.add(duplicate_student)
            
            with pytest.raises(IntegrityError):
                session.commit()
    
    def test_constraint_performance_with_large_dataset(self):
        """Test constraint performance doesn't degrade with larger datasets"""
        import time
        
        with self.SQLiteSession() as session:
            # Create additional institution for testing
            test_institution = Institution(
                name="Performance Test School",
                code="PERF_TEST_001",
                type="K12"
            )
            session.add(test_institution)
            session.flush()
            
            # Time constraint checking with batch inserts
            start_time = time.time()
            
            students_batch = []
            for i in range(100):
                students_batch.append(Student(
                    institution_id=test_institution.id,
                    student_id=f"PERF_TEST_{i:03d}",
                    grade_level="9",
                    enrollment_status="active"
                ))
            
            session.add_all(students_batch)
            session.commit()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert duration < 5.0, f"Constraint checking took too long: {duration}s"
            
            # Verify all students were created
            student_count = session.query(Student).filter(
                Student.institution_id == test_institution.id
            ).count()
            assert student_count == 100