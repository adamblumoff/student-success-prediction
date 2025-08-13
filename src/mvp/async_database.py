#!/usr/bin/env python3
"""
Async Database Operations for Production Performance

Provides async database operations with connection pooling, transaction management,
and optimized bulk operations for high-throughput production environments.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager
import json
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, update, delete, and_, or_, text
from sqlalchemy.dialects.postgresql import insert
import asyncpg

from .database import db_config, Base
from .models import Institution, Student, Prediction, Intervention, AuditLog
from .exceptions import DatabaseError, DatabaseConnectionError, ErrorContext

logger = logging.getLogger(__name__)

class AsyncDatabaseManager:
    """Production-ready async database manager with connection pooling."""
    
    def __init__(self):
        self.async_engine = None
        self.async_session_factory = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize async database connections."""
        if self._initialized:
            return
            
        try:
            # Convert sync database URL to async
            async_url = self._convert_to_async_url(db_config.database_url)
            
            # Create async engine with production settings
            self.async_engine = create_async_engine(
                async_url,
                pool_size=20,  # Production pool size
                max_overflow=30,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False,  # Disable in production
                future=True
            )
            
            # Create async session factory
            self.async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autoflush=False,
                autocommit=False
            )
            
            # Test connection
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                
            self._initialized = True
            logger.info("✅ Async database manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize async database: {e}")
            raise DatabaseConnectionError(
                f"Failed to initialize async database: {e}",
                context=ErrorContext(additional_data={"database_url": async_url})
            )
    
    def _convert_to_async_url(self, sync_url: str) -> str:
        """Convert synchronous database URL to async."""
        if sync_url.startswith('postgresql://'):
            return sync_url.replace('postgresql://', 'postgresql+asyncpg://')
        elif sync_url.startswith('sqlite:///'):
            return sync_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
        else:
            return sync_url
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup."""
        if not self._initialized:
            await self.initialize()
            
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise DatabaseError(
                    f"Database operation failed: {e}",
                    operation="session_management",
                    context=ErrorContext()
                )
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Async health check for database connectivity."""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global async database manager
async_db = AsyncDatabaseManager()

class AsyncInterventionService:
    """High-performance async intervention operations."""
    
    @staticmethod
    async def create_bulk_interventions(
        intervention_data_list: List[Dict[str, Any]],
        institution_id: int
    ) -> Dict[str, Any]:
        """Create multiple interventions with optimized batch processing."""
        start_time = asyncio.get_event_loop().time()
        
        async with async_db.get_session() as session:
            try:
                # Validate students exist in batch
                student_ids = [data['student_id'] for data in intervention_data_list]
                
                stmt = select(Student).where(
                    and_(
                        Student.institution_id == institution_id,
                        Student.id.in_(student_ids)
                    )
                )
                result = await session.execute(stmt)
                existing_students = {s.id: s for s in result.scalars().all()}
                
                # Prepare bulk insert data
                interventions_to_create = []
                validation_errors = []
                
                for data in intervention_data_list:
                    student_id = data['student_id']
                    
                    if student_id not in existing_students:
                        validation_errors.append({
                            'student_id': student_id,
                            'error': 'Student not found'
                        })
                        continue
                    
                    intervention_data = {
                        'institution_id': institution_id,
                        'student_id': student_id,
                        'intervention_type': data['intervention_type'],
                        'title': data['title'],
                        'description': data.get('description'),
                        'priority': data.get('priority', 'medium'),
                        'status': 'pending',
                        'assigned_to': data.get('assigned_to'),
                        'due_date': data.get('due_date'),
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                    interventions_to_create.append(intervention_data)
                
                # Bulk insert with PostgreSQL optimization
                if interventions_to_create:
                    if db_config.database_url.startswith('postgresql'):
                        # PostgreSQL bulk insert
                        stmt = insert(Intervention.__table__).values(interventions_to_create)
                        await session.execute(stmt)
                    else:
                        # SQLite fallback
                        session.add_all([
                            Intervention(**data) for data in interventions_to_create
                        ])
                
                await session.commit()
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                return {
                    'total_requested': len(intervention_data_list),
                    'successful': len(interventions_to_create),
                    'failed': len(validation_errors),
                    'execution_time': round(execution_time, 3),
                    'validation_errors': validation_errors
                }
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(
                    f"Bulk intervention creation failed: {e}",
                    operation="bulk_create_interventions",
                    context=ErrorContext(additional_data={'count': len(intervention_data_list)})
                )
    
    @staticmethod
    async def get_interventions_paginated(
        institution_id: int,
        page: int = 1,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get paginated interventions with optimized joins."""
        async with async_db.get_session() as session:
            try:
                # Build query with joins
                stmt = select(Intervention).options(
                    joinedload(Intervention.student),
                    joinedload(Intervention.prediction)
                ).where(Intervention.institution_id == institution_id)
                
                # Apply filters
                if filters:
                    if filters.get('status'):
                        stmt = stmt.where(Intervention.status == filters['status'])
                    if filters.get('intervention_type'):
                        stmt = stmt.where(Intervention.intervention_type == filters['intervention_type'])
                    if filters.get('priority'):
                        stmt = stmt.where(Intervention.priority == filters['priority'])
                    if filters.get('assigned_to'):
                        stmt = stmt.where(Intervention.assigned_to.ilike(f"%{filters['assigned_to']}%"))
                
                # Count total for pagination
                count_stmt = select(Intervention.id).where(Intervention.institution_id == institution_id)
                if filters:
                    # Apply same filters to count
                    if filters.get('status'):
                        count_stmt = count_stmt.where(Intervention.status == filters['status'])
                    # ... apply other filters
                
                total_result = await session.execute(count_stmt)
                total_count = len(total_result.scalars().all())
                
                # Apply pagination
                offset = (page - 1) * limit
                stmt = stmt.offset(offset).limit(limit).order_by(Intervention.created_at.desc())
                
                result = await session.execute(stmt)
                interventions = result.scalars().all()
                
                # Calculate pagination info
                total_pages = (total_count + limit - 1) // limit
                
                return {
                    'interventions': [
                        {
                            'id': i.id,
                            'student_id': i.student_id,
                            'student_name': f"Student {i.student.student_id}" if i.student else "Unknown",
                            'intervention_type': i.intervention_type,
                            'title': i.title,
                            'priority': i.priority,
                            'status': i.status,
                            'assigned_to': i.assigned_to,
                            'due_date': i.due_date.isoformat() if i.due_date else None,
                            'created_at': i.created_at.isoformat()
                        }
                        for i in interventions
                    ],
                    'pagination': {
                        'current_page': page,
                        'total_pages': total_pages,
                        'total_items': total_count,
                        'items_per_page': limit,
                        'has_next': page < total_pages,
                        'has_prev': page > 1
                    }
                }
                
            except Exception as e:
                raise DatabaseError(
                    f"Failed to get paginated interventions: {e}",
                    operation="get_interventions_paginated",
                    context=ErrorContext(additional_data={'page': page, 'limit': limit})
                )

class AsyncPredictionService:
    """High-performance async prediction operations."""
    
    @staticmethod
    async def save_predictions_bulk(
        predictions_data: List[Dict[str, Any]],
        session_id: str,
        institution_id: int
    ) -> Dict[str, Any]:
        """Ultra-fast bulk prediction saves with conflict resolution."""
        start_time = asyncio.get_event_loop().time()
        
        async with async_db.get_session() as session:
            try:
                # Prepare student data for upsert
                students_data = []
                predictions_data_final = []
                
                for pred_data in predictions_data:
                    student_id_str = str(pred_data['student_id'])
                    
                    # Prepare student upsert data
                    student_data = {
                        'institution_id': institution_id,
                        'student_id': student_id_str,
                        'enrollment_status': 'active'
                    }
                    students_data.append(student_data)
                    
                    # Prepare prediction data
                    prediction_data = {
                        'institution_id': institution_id,
                        'student_id': student_id_str,  # Will be replaced with DB ID
                        'risk_score': pred_data['risk_score'],
                        'risk_category': pred_data['risk_category'],
                        'success_probability': pred_data.get('success_probability'),
                        'session_id': session_id,
                        'data_source': 'csv_upload',
                        'features_used': json.dumps(pred_data.get('features_data')),
                        'explanation': json.dumps(pred_data.get('explanation_data')),
                        'created_at': datetime.utcnow()
                    }
                    predictions_data_final.append(prediction_data)
                
                # Bulk upsert students (PostgreSQL optimization)
                if db_config.database_url.startswith('postgresql'):
                    # PostgreSQL UPSERT for students
                    stmt = insert(Student.__table__).values(students_data)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=['institution_id', 'student_id']
                    )
                    await session.execute(stmt)
                    await session.flush()
                    
                    # Get student ID mappings
                    student_ids = [data['student_id'] for data in students_data]
                    stmt = select(Student.student_id, Student.id).where(
                        and_(
                            Student.institution_id == institution_id,
                            Student.student_id.in_(student_ids)
                        )
                    )
                    result = await session.execute(stmt)
                    student_mapping = {row[0]: row[1] for row in result.all()}
                    
                    # Update prediction data with database student IDs
                    for pred_data in predictions_data_final:
                        pred_data['student_id'] = student_mapping[pred_data['student_id']]
                    
                    # Bulk upsert predictions
                    stmt = insert(Prediction.__table__).values(predictions_data_final)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['student_id'],
                        set_={
                            'risk_score': stmt.excluded.risk_score,
                            'risk_category': stmt.excluded.risk_category,
                            'success_probability': stmt.excluded.success_probability,
                            'session_id': stmt.excluded.session_id,
                            'features_used': stmt.excluded.features_used,
                            'explanation': stmt.excluded.explanation,
                            'created_at': stmt.excluded.created_at
                        }
                    )
                    await session.execute(stmt)
                    
                else:
                    # SQLite fallback - less optimized but functional
                    for student_data in students_data:
                        # Check if student exists
                        stmt = select(Student).where(
                            and_(
                                Student.institution_id == student_data['institution_id'],
                                Student.student_id == student_data['student_id']
                            )
                        )
                        result = await session.execute(stmt)
                        student = result.scalar()
                        
                        if not student:
                            student = Student(**student_data)
                            session.add(student)
                    
                    await session.flush()
                    
                    # Get student mappings and create predictions
                    for pred_data in predictions_data_final:
                        stmt = select(Student.id).where(
                            and_(
                                Student.institution_id == institution_id,
                                Student.student_id == pred_data['student_id']
                            )
                        )
                        result = await session.execute(stmt)
                        db_student_id = result.scalar()
                        
                        pred_data['student_id'] = db_student_id
                        prediction = Prediction(**pred_data)
                        session.add(prediction)
                
                await session.commit()
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                logger.info(f"✅ Bulk saved {len(predictions_data)} predictions in {execution_time:.3f}s")
                
                return {
                    'predictions_saved': len(predictions_data),
                    'execution_time': round(execution_time, 3),
                    'throughput_per_second': round(len(predictions_data) / execution_time, 2)
                }
                
            except Exception as e:
                await session.rollback()
                raise DatabaseError(
                    f"Bulk prediction save failed: {e}",
                    operation="save_predictions_bulk",
                    context=ErrorContext(additional_data={'count': len(predictions_data)})
                )

# FastAPI dependencies for async operations
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async with async_db.get_session() as session:
        yield session

def get_async_intervention_service() -> AsyncInterventionService:
    """FastAPI dependency for async intervention service."""
    return AsyncInterventionService()

def get_async_prediction_service() -> AsyncPredictionService:
    """FastAPI dependency for async prediction service."""
    return AsyncPredictionService()

# Startup/shutdown functions
async def initialize_async_database():
    """Initialize async database on startup."""
    await async_db.initialize()

async def shutdown_async_database():
    """Cleanup async database on shutdown."""
    if async_db.async_engine:
        await async_db.async_engine.dispose()
        logger.info("Async database connections closed")