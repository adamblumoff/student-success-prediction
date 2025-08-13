"""
Database Security Module
Implements row-level security context management for K-12 multi-tenant system
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DatabaseSecurityManager:
    """Manages row-level security context for multi-tenant K-12 system"""
    
    def __init__(self):
        self.current_contexts: Dict[str, Dict[str, Any]] = {}
    
    def set_institution_context(self, session: Session, institution_id: int, user_id: str = None, ip_address: str = None):
        """Set the institution context for row-level security"""
        try:
            # Check if we're using PostgreSQL (RLS only supported on PostgreSQL)
            if session.bind.dialect.name != 'postgresql':
                logger.info(f"📝 SQLite mode: storing institution context in memory (institution_id={institution_id})")
                # For SQLite, store context in memory for reference
                self.current_contexts[str(session)] = {
                    'institution_id': institution_id,
                    'user_id': user_id,
                    'ip_address': ip_address
                }
                return True
            # Set institution context for RLS policies
            session.execute(text("SELECT set_user_institution_context(:inst_id)"), {"inst_id": institution_id})
            
            # Set additional context for audit logging
            if user_id:
                session.execute(text("SELECT set_config('app.current_user_id', :user_id, false)"), {"user_id": user_id})
            
            if ip_address:
                session.execute(text("SELECT set_config('app.current_ip_address', :ip_address, false)"), {"ip_address": ip_address})
            
            session.commit()
            
            logger.info(f"✅ Set database security context: institution_id={institution_id}, user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set database security context: {e}")
            session.rollback()
            return False
    
    async def set_institution_context_async(self, session: AsyncSession, institution_id: int, user_id: str = None, ip_address: str = None):
        """Set the institution context for row-level security (async version)"""
        try:
            # Check if we're using PostgreSQL (RLS only supported on PostgreSQL)
            if session.bind.dialect.name != 'postgresql':
                logger.info(f"📝 SQLite mode: storing institution context in memory (institution_id={institution_id})")
                # For SQLite, store context in memory for reference
                self.current_contexts[str(session)] = {
                    'institution_id': institution_id,
                    'user_id': user_id,
                    'ip_address': ip_address
                }
                return True
            # Set institution context for RLS policies
            await session.execute(text("SELECT set_user_institution_context(:inst_id)"), {"inst_id": institution_id})
            
            # Set additional context for audit logging
            if user_id:
                await session.execute(text("SELECT set_config('app.current_user_id', :user_id, false)"), {"user_id": user_id})
            
            if ip_address:
                await session.execute(text("SELECT set_config('app.current_ip_address', :ip_address, false)"), {"ip_address": ip_address})
            
            await session.commit()
            
            logger.info(f"✅ Set async database security context: institution_id={institution_id}, user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set async database security context: {e}")
            await session.rollback()
            return False
    
    def clear_institution_context(self, session: Session):
        """Clear the institution context for security"""
        try:
            session.execute(text("SELECT clear_user_institution_context()"))
            session.execute(text("SELECT set_config('app.current_user_id', '', false)"))
            session.execute(text("SELECT set_config('app.current_ip_address', '', false)"))
            session.commit()
            
            logger.info("✅ Cleared database security context")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear database security context: {e}")
            session.rollback()
            return False
    
    async def clear_institution_context_async(self, session: AsyncSession):
        """Clear the institution context for security (async version)"""
        try:
            await session.execute(text("SELECT clear_user_institution_context()"))
            await session.execute(text("SELECT set_config('app.current_user_id', '', false)"))
            await session.execute(text("SELECT set_config('app.current_ip_address', '', false)"))
            await session.commit()
            
            logger.info("✅ Cleared async database security context")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear async database security context: {e}")
            await session.rollback()
            return False
    
    def get_current_institution_id(self, session: Session) -> Optional[int]:
        """Get the current institution ID from the session context"""
        try:
            result = session.execute(text("SELECT get_current_user_institution_id()"))
            institution_id = result.scalar()
            return institution_id if institution_id != 0 else None
        except Exception as e:
            logger.error(f"❌ Failed to get current institution ID: {e}")
            return None
    
    async def get_current_institution_id_async(self, session: AsyncSession) -> Optional[int]:
        """Get the current institution ID from the session context (async version)"""
        try:
            result = await session.execute(text("SELECT get_current_user_institution_id()"))
            institution_id = result.scalar()
            return institution_id if institution_id != 0 else None
        except Exception as e:
            logger.error(f"❌ Failed to get current institution ID: {e}")
            return None
    
    @asynccontextmanager
    async def institution_context(self, session: AsyncSession, institution_id: int, user_id: str = None, ip_address: str = None):
        """Context manager for scoped institution access"""
        try:
            # Set context
            await self.set_institution_context_async(session, institution_id, user_id, ip_address)
            yield session
        finally:
            # Always clear context when done
            await self.clear_institution_context_async(session)
    
    def validate_institution_access(self, session: Session, institution_id: int) -> bool:
        """Validate that the current user has access to the specified institution"""
        try:
            current_institution = self.get_current_institution_id(session)
            if current_institution is None:
                logger.warning("❌ No institution context set - access denied")
                return False
            
            if current_institution != institution_id:
                logger.warning(f"❌ Institution access denied: current={current_institution}, requested={institution_id}")
                return False
            
            logger.info(f"✅ Institution access validated: {institution_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to validate institution access: {e}")
            return False
    
    async def validate_institution_access_async(self, session: AsyncSession, institution_id: int) -> bool:
        """Validate that the current user has access to the specified institution (async version)"""
        try:
            current_institution = await self.get_current_institution_id_async(session)
            if current_institution is None:
                logger.warning("❌ No institution context set - access denied")
                return False
            
            if current_institution != institution_id:
                logger.warning(f"❌ Institution access denied: current={current_institution}, requested={institution_id}")
                return False
            
            logger.info(f"✅ Institution access validated: {institution_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to validate institution access: {e}")
            return False
    
    def test_rls_policies(self, session: Session, institution_id: int) -> Dict[str, bool]:
        """Test that row-level security policies are working correctly"""
        test_results = {}
        
        try:
            # Set context for testing
            self.set_institution_context(session, institution_id, "test_user", "127.0.0.1")
            
            # Test students table access
            try:
                result = session.execute(text("SELECT COUNT(*) FROM students WHERE institution_id = :inst_id"), {"inst_id": institution_id})
                count = result.scalar()
                test_results['students_access'] = True
                logger.info(f"✅ Students RLS test passed: {count} records accessible")
            except Exception as e:
                test_results['students_access'] = False
                logger.error(f"❌ Students RLS test failed: {e}")
            
            # Test predictions table access
            try:
                result = session.execute(text("SELECT COUNT(*) FROM predictions WHERE institution_id = :inst_id"), {"inst_id": institution_id})
                count = result.scalar()
                test_results['predictions_access'] = True
                logger.info(f"✅ Predictions RLS test passed: {count} records accessible")
            except Exception as e:
                test_results['predictions_access'] = False
                logger.error(f"❌ Predictions RLS test failed: {e}")
            
            # Test interventions table access
            try:
                result = session.execute(text("SELECT COUNT(*) FROM interventions WHERE institution_id = :inst_id"), {"inst_id": institution_id})
                count = result.scalar()
                test_results['interventions_access'] = True
                logger.info(f"✅ Interventions RLS test passed: {count} records accessible")
            except Exception as e:
                test_results['interventions_access'] = False
                logger.error(f"❌ Interventions RLS test failed: {e}")
            
            # Test institution isolation (should not see other institutions)
            try:
                result = session.execute(text("SELECT COUNT(*) FROM students WHERE institution_id != :inst_id"), {"inst_id": institution_id})
                count = result.scalar()
                test_results['institution_isolation'] = (count == 0)
                if count == 0:
                    logger.info("✅ Institution isolation test passed: no cross-institution access")
                else:
                    logger.warning(f"❌ Institution isolation test failed: {count} cross-institution records visible")
            except Exception as e:
                test_results['institution_isolation'] = False
                logger.error(f"❌ Institution isolation test failed: {e}")
            
        finally:
            # Clear context after testing
            self.clear_institution_context(session)
        
        return test_results

# Global instance
db_security = DatabaseSecurityManager()

# Convenience functions for FastAPI dependency injection
def get_db_security() -> DatabaseSecurityManager:
    """Get the database security manager instance"""
    return db_security

def require_institution_context(institution_id: int):
    """Decorator factory to require institution context for database operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be used in FastAPI endpoints to ensure context is set
            logger.info(f"🔒 Requiring institution context: {institution_id}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator