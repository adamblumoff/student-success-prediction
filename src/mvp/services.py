#!/usr/bin/env python3
"""
Dependency Injection for ML Models and Services

Provides FastAPI dependencies for ML models and external integrations.
Replaces global variables with proper dependency injection pattern.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

# Add project root to path for model imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.intervention_system import InterventionRecommendationSystem
from src.models.k12_ultra_predictor import K12UltraPredictor

logger = logging.getLogger(__name__)

# Service instances (singleton pattern)
_intervention_system: Optional[InterventionRecommendationSystem] = None
_k12_ultra_predictor: Optional[K12UltraPredictor] = None
_google_classroom_integration = None
_gpt_oss_service = None
_gpt_cache_service = None


def get_intervention_system() -> InterventionRecommendationSystem:
    """
    FastAPI dependency to get or create InterventionRecommendationSystem instance.
    
    Returns:
        InterventionRecommendationSystem: ML intervention system
        
    Raises:
        RuntimeError: If system cannot be initialized
    """
    global _intervention_system
    
    if _intervention_system is None:
        try:
            logger.info("🤖 Initializing InterventionRecommendationSystem")
            _intervention_system = InterventionRecommendationSystem()
            logger.info("✅ InterventionRecommendationSystem initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize InterventionRecommendationSystem: {e}")
            raise RuntimeError(f"ML system initialization failed: {str(e)}")
    
    return _intervention_system


def get_k12_ultra_predictor() -> K12UltraPredictor:
    """
    FastAPI dependency to get or create K12UltraPredictor instance.
    
    Returns:
        K12UltraPredictor: K-12 specialized ML predictor
        
    Raises:
        RuntimeError: If predictor cannot be initialized
    """
    global _k12_ultra_predictor
    
    if _k12_ultra_predictor is None:
        try:
            logger.info("🎓 Initializing K12UltraPredictor")
            _k12_ultra_predictor = K12UltraPredictor()
            logger.info("✅ K12UltraPredictor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize K12UltraPredictor: {e}")
            raise RuntimeError(f"K-12 predictor initialization failed: {str(e)}")
    
    return _k12_ultra_predictor


def get_google_classroom_integration():
    """
    FastAPI dependency to get or create Google Classroom integration.
    
    Returns:
        GoogleClassroomIntegration: Google Classroom service instance
        
    Raises:
        RuntimeError: If integration cannot be initialized
    """
    global _google_classroom_integration
    
    if _google_classroom_integration is None:
        try:
            logger.info("📚 Initializing Google Classroom integration")
            from integrations.google_classroom import GoogleClassroomIntegration
            _google_classroom_integration = GoogleClassroomIntegration()
            logger.info("✅ Google Classroom integration initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Classroom integration: {e}")
            raise RuntimeError(f"Google Classroom integration failed: {str(e)}")
    
    return _google_classroom_integration


def get_gpt_oss_service():
    """
    FastAPI dependency to get or create GPT-OSS service instance.
    
    Returns:
        GPTOSSService: GPT-OSS 20B model service
        
    Raises:
        RuntimeError: If service cannot be initialized
    """
    global _gpt_oss_service
    
    if _gpt_oss_service is None:
        try:
            logger.info("🤖 Initializing GPT-OSS service")
            from src.mvp.services.gpt_oss_service import GPTOSSService
            _gpt_oss_service = GPTOSSService()
            logger.info("✅ GPT-OSS service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPT-OSS service: {e}")
            # Don't raise error - allow system to work without GPT-OSS
            logger.warning("⚠️ System will continue without GPT-OSS enhancement")
    
    return _gpt_oss_service


def get_gpt_cache_service():
    """
    FastAPI dependency to get or create GPT Cache service instance.
    
    Returns:
        GPTCacheService: GPT analysis caching service
    """
    global _gpt_cache_service
    
    if _gpt_cache_service is None:
        try:
            logger.info("🗄️ Initializing GPT Cache service")
            from src.mvp.services.gpt_cache_service import GPTCacheService
            _gpt_cache_service = GPTCacheService()
            logger.info("✅ GPT Cache service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPT Cache service: {e}")
            # Don't raise error - allow system to work without caching
            logger.warning("⚠️ System will continue without GPT caching")
    
    return _gpt_cache_service


def reset_services():
    """
    Reset all service instances (useful for testing).
    
    Warning: This will force re-initialization of all services.
    """
    global _intervention_system, _k12_ultra_predictor, _google_classroom_integration, _gpt_oss_service, _gpt_cache_service
    
    logger.info("🔄 Resetting all service instances")
    _intervention_system = None
    _k12_ultra_predictor = None
    _google_classroom_integration = None
    _gpt_oss_service = None
    _gpt_cache_service = None


def health_check_services() -> dict:
    """
    Check health status of all initialized services.
    
    Returns:
        dict: Health status of each service
    """
    return {
        'intervention_system': _intervention_system is not None,
        'k12_ultra_predictor': _k12_ultra_predictor is not None,
        'google_classroom': _google_classroom_integration is not None,
        'gpt_oss_service': _gpt_oss_service is not None,
        'gpt_cache_service': _gpt_cache_service is not None
    }