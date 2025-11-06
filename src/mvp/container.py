#!/usr/bin/env python3
"""
Production-ready Dependency Injection Container

Implements the Service Locator and Dependency Injection patterns for better
testability, maintainability, and production deployment flexibility.
"""

import os
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Type, List
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Core model classes referenced throughout the container
from src.models.intervention_system import InterventionRecommendationSystem
from src.models.k12_ultra_predictor import K12UltraPredictor

class ServiceLifetime:
    """Service lifetime management patterns."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class ServiceDescriptor:
    """Service registration descriptor."""
    
    def __init__(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        lifetime: str = ServiceLifetime.SINGLETON,
        dependencies: Optional[list] = None
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.factory = factory
        self.lifetime = lifetime
        self.dependencies = dependencies or []
        
        if not implementation and not factory:
            raise ValueError("Either implementation or factory must be provided")

class ServiceContainer:
    """Production-ready dependency injection container with lifecycle management."""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._building_services = set()  # Prevent circular dependencies
        
    def register_singleton(self, service_type: Type, implementation: Type = None, factory: Callable = None) -> 'ServiceContainer':
        """Register a singleton service."""
        return self._register(service_type, implementation, factory, ServiceLifetime.SINGLETON)
    
    def register_transient(self, service_type: Type, implementation: Type = None, factory: Callable = None) -> 'ServiceContainer':
        """Register a transient service (new instance each time)."""
        return self._register(service_type, implementation, factory, ServiceLifetime.TRANSIENT)
    
    def register_scoped(self, service_type: Type, implementation: Type = None, factory: Callable = None) -> 'ServiceContainer':
        """Register a scoped service (one per request scope)."""
        return self._register(service_type, implementation, factory, ServiceLifetime.SCOPED)
    
    def _register(self, service_type: Type, implementation: Type, factory: Callable, lifetime: str) -> 'ServiceContainer':
        """Internal registration method."""
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                factory=factory,
                lifetime=lifetime
            )
            self._services[service_type] = descriptor
            logger.debug(f"Registered {service_type.__name__} as {lifetime}")
            return self
    
    def get(self, service_type: Type[T]) -> T:
        """Get service instance with dependency resolution."""
        with self._lock:
            if service_type in self._building_services:
                raise ValueError(f"Circular dependency detected for {service_type.__name__}")
            
            # Check if singleton already exists
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            # Get service descriptor
            if service_type not in self._services:
                raise ValueError(f"Service {service_type.__name__} not registered")
            
            descriptor = self._services[service_type]
            
            # Track that we're building this service
            self._building_services.add(service_type)
            
            try:
                # Create instance
                if descriptor.factory:
                    instance = descriptor.factory(self)
                elif descriptor.implementation:
                    instance = self._create_instance(descriptor.implementation)
                else:
                    raise ValueError(f"No implementation or factory for {service_type.__name__}")
                
                # Store singleton if needed
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    self._singletons[service_type] = instance
                
                return instance
                
            finally:
                self._building_services.discard(service_type)
    
    def _create_instance(self, implementation_type: Type):
        """Create instance with constructor dependency injection."""
        # Simple implementation - in production, you'd use more sophisticated DI
        try:
            return implementation_type()
        except TypeError as e:
            # If constructor requires dependencies, this would resolve them
            # For now, we'll use the factory pattern for complex dependencies
            raise ValueError(f"Cannot instantiate {implementation_type.__name__}: {e}")
    
    def clear_singletons(self):
        """Clear singleton cache (useful for testing)."""
        with self._lock:
            self._singletons.clear()
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if service is registered."""
        return service_type in self._services

# Global container instance
_container = ServiceContainer()
_services_configured = False

def _ensure_services_configured():
    """Ensure container registrations have been performed."""
    global _services_configured
    if not _services_configured:
        configure_production_services()

def get_container() -> ServiceContainer:
    """Get the global service container."""
    return _container

# Service registration for production
def configure_production_services():
    """Configure all production services in the container."""
    global _services_configured
    if _services_configured:
        return
    
    # Database services
    from .database import DatabaseConfig
    _container.register_singleton(DatabaseConfig, factory=lambda c: DatabaseConfig())
    
    # ML Model services with conditional registration
    def ml_model_factory(container):
        """Factory for ML models with fallback handling."""
        try:
            models_dir = Path(os.getenv('MODELS_DIR', 'results/models'))
            return InterventionRecommendationSystem(models_dir=models_dir)
        except Exception as e:
            logger.warning(f"Failed to load InterventionRecommendationSystem: {e}")
            return None
    
    def k12_model_factory(container):
        """Factory for K-12 models with fallback handling."""
        try:
            return K12UltraPredictor()
        except Exception as e:
            logger.warning(f"Failed to load K12UltraPredictor: {e}")
            return None
    
    # Register ML services
    
    _container.register_singleton(InterventionRecommendationSystem, factory=ml_model_factory)
    _container.register_singleton(K12UltraPredictor, factory=k12_model_factory)
    
    # GPT and context services
    from src.mvp.services.gpt_oss_service import GPTOSSService
    from src.mvp.services.gpt_enhanced_predictor import GPTEnhancedPredictor
    from src.mvp.services.context_builder import ContextBuilder
    from src.mvp.services.metrics_aggregator import MetricsAggregator

    def gpt_service_factory(container):
        """Factory for GPT service with fallback demo implementation."""
        try:
            service = GPTOSSService()
            return service
        except Exception as exc:
            logger.warning(f"GPT service unavailable, using demo service: {exc}")
            return DemoGPTService()

    _container.register_singleton(GPTOSSService, factory=gpt_service_factory)
    _container.register_singleton(GPTEnhancedPredictor, factory=lambda c: GPTEnhancedPredictor())
    _container.register_singleton(ContextBuilder, factory=lambda c: ContextBuilder())
    _container.register_singleton(MetricsAggregator, factory=lambda c: MetricsAggregator())
    
    # Cache services
    _container.register_singleton(
        ProductionCacheService,
        factory=lambda c: ProductionCacheService()
    )
    
    # Monitoring services
    _container.register_singleton(
        MetricsCollector, 
        factory=lambda c: MetricsCollector()
    )
    
    _services_configured = True
    logger.info("Production services configured successfully")

# Cache service for production
class ProductionCacheService:
    """Production-ready caching service with TTL and memory management."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache = {}
        self._ttl = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        
    def get(self, key: str, default=None):
        """Get cached value with TTL check."""
        with self._lock:
            if key not in self._cache:
                return default
                
            # Check TTL
            import time
            if time.time() > self._ttl.get(key, 0):
                del self._cache[key]
                del self._ttl[key]
                return default
                
            return self._cache[key]
    
    def set(self, key: str, value, ttl: Optional[int] = None):
        """Set cached value with TTL."""
        with self._lock:
            # Evict oldest items if cache is full
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
                
            import time
            self._cache[key] = value
            self._ttl[key] = time.time() + (ttl or self._default_ttl)
    
    def _evict_oldest(self):
        """Evict the oldest cached item."""
        if not self._cache:
            return
            
        oldest_key = min(self._ttl.keys(), key=self._ttl.get)
        del self._cache[oldest_key]
        del self._ttl[oldest_key]
    
    def clear(self):
        """Clear all cached items."""
        with self._lock:
            self._cache.clear()
            self._ttl.clear()

class DemoGPTService:
    """Fallback GPT service that returns deterministic demo responses."""
    
    def __init__(self):
        self.is_initialized = True
        self.model_name = "demo-gpt-service"
    
    def initialize_model(self) -> bool:
        """Interface compatibility with GPTOSSService."""
        self.is_initialized = True
        return True
    
    def generate_analysis(self, prompt: str, analysis_type: str = "student_analysis", 
                          max_tokens: int = 1024, bypass_cache: bool = False) -> Dict[str, Any]:
        """Return a deterministic analysis payload."""
        return {
            "success": True,
            "analysis": (
                "⚠️ Demo GPT service active. Provide targeted academic support, "
                "increase engagement touchpoints, and schedule a family check‑in."
            ),
            "analysis_type": analysis_type,
            "metadata": {
                "model": self.model_name,
                "analysis_type": analysis_type,
                "timestamp": "demo",
                "tokens_generated": 0,
                "cache_hit": False
            }
        }
    
    def predict_from_gradebook(self, gradebook_df, include_gpt_analysis: bool = True,
                               analysis_depth: str = "basic") -> List[Dict[str, Any]]:
        """Return mock prediction results for gradebook uploads."""
        results = []
        iterator = []
        if hasattr(gradebook_df, "iterrows"):
            iterator = gradebook_df.iterrows()
        elif isinstance(gradebook_df, list):
            iterator = enumerate(gradebook_df)
        
        for _, row in iterator:
            student_id = str(getattr(row, "get", lambda k, d=None: row[k])("student_id", "demo_student"))
            result = {
                "student_id": student_id,
                "risk_score": 0.65,
                "risk_category": "Medium Risk",
                "success_probability": 0.35,
                "needs_intervention": True
            }
            if include_gpt_analysis:
                result["gpt_insights"] = self.generate_analysis(
                    f"Analyze student {student_id}", analysis_type=analysis_depth
                )
            results.append(result)
        if not results:
            results.append({
                "student_id": "demo_student",
                "risk_score": 0.6,
                "risk_category": "Medium Risk",
                "success_probability": 0.4,
                "needs_intervention": True
            })
        return results

# Metrics collection for monitoring
class MetricsCollector:
    """Production metrics collection service."""
    
    def __init__(self):
        self._metrics = {}
        self._lock = threading.RLock()
    
    def increment(self, metric_name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._build_key(metric_name, tags)
            self._metrics[key] = self._metrics.get(key, 0) + value
    
    def gauge(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric."""
        with self._lock:
            key = self._build_key(metric_name, tags)
            self._metrics[key] = value
    
    def timing(self, metric_name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timing metric."""
        with self._lock:
            key = self._build_key(metric_name, tags)
            if key not in self._metrics:
                self._metrics[key] = []
            self._metrics[key].append(duration_ms)
    
    def _build_key(self, metric_name: str, tags: Dict[str, str] = None) -> str:
        """Build metric key with tags."""
        if not tags:
            return metric_name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric_name}|{tag_str}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            return self._metrics.copy()
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()

# FastAPI dependency functions
def get_intervention_system():
    """FastAPI dependency to get intervention system."""
    _ensure_services_configured()
    return _container.get(InterventionRecommendationSystem)

def get_k12_ultra_predictor():
    """FastAPI dependency to get K-12 predictor."""
    _ensure_services_configured()
    return _container.get(K12UltraPredictor)

def get_cache_service():
    """FastAPI dependency to get cache service."""
    _ensure_services_configured()
    return _container.get(ProductionCacheService)

def get_metrics_service():
    """FastAPI dependency to get metrics service."""
    _ensure_services_configured()
    return _container.get(MetricsCollector)

def get_gpt_service():
    """FastAPI dependency to get GPT service."""
    from src.mvp.services.gpt_oss_service import GPTOSSService  # local import for typing
    _ensure_services_configured()
    return _container.get(GPTOSSService)

def get_gpt_enhanced_predictor():
    """FastAPI dependency to get GPT-enhanced predictor."""
    from src.mvp.services.gpt_enhanced_predictor import GPTEnhancedPredictor
    _ensure_services_configured()
    return _container.get(GPTEnhancedPredictor)

def get_context_builder():
    """FastAPI dependency to get context builder."""
    from src.mvp.services.context_builder import ContextBuilder
    _ensure_services_configured()
    return _container.get(ContextBuilder)

def get_metrics_aggregator():
    """FastAPI dependency to get metrics aggregator."""
    from src.mvp.services.metrics_aggregator import MetricsAggregator
    _ensure_services_configured()
    return _container.get(MetricsAggregator)

# Startup function
def initialize_container():
    """Initialize the service container for production use."""
    configure_production_services()
    logger.info("Service container initialized successfully")
