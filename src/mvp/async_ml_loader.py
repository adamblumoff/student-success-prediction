#!/usr/bin/env python3
"""
Async ML Model Loading System

Provides asynchronous model loading and caching for production performance.
Implements model warmup, lazy loading, and memory-efficient model management.
"""

import asyncio
import logging
import threading
from typing import Dict, Any, Optional, Callable, Awaitable
from pathlib import Path
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import weakref
import gc
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    """Model loading status"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    CACHED = "cached"

@dataclass
class ModelInfo:
    """Model information and metadata"""
    name: str
    path: Path
    loader_func: Callable
    last_used: datetime
    load_time: float
    memory_usage: int
    status: ModelStatus
    error_message: Optional[str] = None
    instance: Optional[Any] = None

class AsyncMLLoader:
    """Asynchronous ML model loader with caching and memory management"""
    
    def __init__(self, max_workers: int = 2, cache_ttl: int = 3600, max_memory_mb: int = 1024):
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl  # Time to live in seconds
        self.max_memory_mb = max_memory_mb
        
        self._models: Dict[str, ModelInfo] = {}
        self._loading_locks: Dict[str, asyncio.Lock] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._cache_cleanup_task: Optional[asyncio.Task] = None
        
        # Memory tracking
        self._total_memory_usage = 0
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._cache_cleanup_task is None or self._cache_cleanup_task.done():
            self._cache_cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
    
    async def _cache_cleanup_loop(self):
        """Background task to clean up expired cached models"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._cleanup_expired_models()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_expired_models(self):
        """Clean up expired models from cache"""
        current_time = datetime.now()
        expired_models = []
        
        for name, model_info in self._models.items():
            if (model_info.status == ModelStatus.CACHED and 
                current_time - model_info.last_used > timedelta(seconds=self.cache_ttl)):
                expired_models.append(name)
        
        for name in expired_models:
            await self._unload_model(name)
            logger.info(f"Unloaded expired model: {name}")
    
    async def _unload_model(self, name: str):
        """Unload a model from memory"""
        if name in self._models:
            model_info = self._models[name]
            
            # Clear instance reference
            if model_info.instance:
                model_info.instance = None
                
            # Update memory tracking
            self._total_memory_usage -= model_info.memory_usage
            
            # Update status
            model_info.status = ModelStatus.UNLOADED
            model_info.memory_usage = 0
            
            # Force garbage collection
            gc.collect()
    
    def register_model(self, name: str, path: Path, loader_func: Callable) -> None:
        """Register a model for async loading"""
        self._models[name] = ModelInfo(
            name=name,
            path=path,
            loader_func=loader_func,
            last_used=datetime.now(),
            load_time=0.0,
            memory_usage=0,
            status=ModelStatus.UNLOADED
        )
        self._loading_locks[name] = asyncio.Lock()
        logger.info(f"Registered model: {name}")
    
    async def load_model(self, name: str, force_reload: bool = False) -> Any:
        """Load a model asynchronously with caching"""
        if name not in self._models:
            raise ValueError(f"Model '{name}' not registered")
        
        model_info = self._models[name]
        
        # Return cached model if available and not forcing reload
        if not force_reload and model_info.status == ModelStatus.READY and model_info.instance:
            model_info.last_used = datetime.now()
            return model_info.instance
        
        # Use lock to prevent concurrent loading
        async with self._loading_locks[name]:
            # Double-check after acquiring lock
            if not force_reload and model_info.status == ModelStatus.READY and model_info.instance:
                model_info.last_used = datetime.now()
                return model_info.instance
            
            # Check memory constraints
            if not await self._ensure_memory_available(name):
                raise RuntimeError(f"Insufficient memory to load model '{name}'")
            
            # Load model
            model_info.status = ModelStatus.LOADING
            start_time = time.time()
            
            try:
                # Load in thread pool to avoid blocking event loop
                model_instance = await asyncio.get_event_loop().run_in_executor(
                    self._executor, model_info.loader_func
                )
                
                load_time = time.time() - start_time
                
                # Estimate memory usage (simplified)
                memory_usage = await self._estimate_memory_usage(model_instance)
                
                # Update model info
                model_info.instance = model_instance
                model_info.status = ModelStatus.READY
                model_info.load_time = load_time
                model_info.memory_usage = memory_usage
                model_info.last_used = datetime.now()
                model_info.error_message = None
                
                # Update total memory usage
                self._total_memory_usage += memory_usage
                
                logger.info(f"Loaded model '{name}' in {load_time:.2f}s ({memory_usage/1024/1024:.1f}MB)")
                return model_instance
                
            except Exception as e:
                model_info.status = ModelStatus.ERROR
                model_info.error_message = str(e)
                logger.error(f"Failed to load model '{name}': {e}")
                raise
    
    async def _ensure_memory_available(self, name: str) -> bool:
        """Ensure sufficient memory is available for loading model"""
        # Get current memory usage
        import psutil
        process = psutil.Process()
        current_memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Estimate required memory (conservative estimate)
        estimated_model_size = 200  # MB - conservative estimate
        
        if current_memory_mb + estimated_model_size > self.max_memory_mb:
            # Try to free memory by unloading least recently used models
            await self._free_memory_lru()
            
            # Check again
            current_memory_mb = process.memory_info().rss / 1024 / 1024
            if current_memory_mb + estimated_model_size > self.max_memory_mb:
                logger.warning(f"Insufficient memory for model '{name}': {current_memory_mb}MB used")
                return False
        
        return True
    
    async def _free_memory_lru(self):
        """Free memory by unloading least recently used models"""
        # Sort models by last used time
        cached_models = [
            (name, info) for name, info in self._models.items() 
            if info.status == ModelStatus.READY and info.instance
        ]
        
        cached_models.sort(key=lambda x: x[1].last_used)
        
        # Unload oldest models until we have some free memory
        for name, model_info in cached_models[:len(cached_models)//2]:
            await self._unload_model(name)
            logger.info(f"Freed memory by unloading LRU model: {name}")
    
    async def _estimate_memory_usage(self, model_instance: Any) -> int:
        """Estimate memory usage of model instance"""
        try:
            import sys
            return sys.getsizeof(model_instance)
        except:
            # Fallback estimate
            return 100 * 1024 * 1024  # 100MB
    
    async def get_model_status(self, name: str) -> Dict[str, Any]:
        """Get status information for a model"""
        if name not in self._models:
            return {"status": "not_registered"}
        
        model_info = self._models[name]
        return {
            "name": name,
            "status": model_info.status.value,
            "last_used": model_info.last_used.isoformat() if model_info.last_used else None,
            "load_time": model_info.load_time,
            "memory_usage_mb": model_info.memory_usage / 1024 / 1024,
            "error_message": model_info.error_message,
            "is_loaded": model_info.instance is not None
        }
    
    async def warmup_models(self, model_names: list[str] = None) -> Dict[str, bool]:
        """Warm up models by pre-loading them"""
        if model_names is None:
            model_names = list(self._models.keys())
        
        results = {}
        warmup_tasks = []
        
        for name in model_names:
            if name in self._models:
                task = asyncio.create_task(self._warmup_single_model(name))
                warmup_tasks.append((name, task))
        
        # Wait for all warmup tasks to complete
        for name, task in warmup_tasks:
            try:
                await task
                results[name] = True
            except Exception as e:
                logger.error(f"Warmup failed for model '{name}': {e}")
                results[name] = False
        
        return results
    
    async def _warmup_single_model(self, name: str):
        """Warm up a single model"""
        try:
            await self.load_model(name)
            logger.info(f"Warmed up model: {name}")
        except Exception as e:
            logger.error(f"Warmup failed for {name}: {e}")
            raise
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        import psutil
        process = psutil.Process()
        
        loaded_models = sum(1 for info in self._models.values() 
                          if info.status == ModelStatus.READY)
        
        return {
            "total_models": len(self._models),
            "loaded_models": loaded_models,
            "total_memory_usage_mb": self._total_memory_usage / 1024 / 1024,
            "system_memory_usage_mb": process.memory_info().rss / 1024 / 1024,
            "max_memory_limit_mb": self.max_memory_mb,
            "cache_ttl_seconds": self.cache_ttl,
            "executor_workers": self.max_workers
        }
    
    async def shutdown(self):
        """Shutdown the loader and cleanup resources"""
        # Cancel background tasks
        if self._cache_cleanup_task:
            self._cache_cleanup_task.cancel()
            try:
                await self._cache_cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Unload all models
        for name in list(self._models.keys()):
            await self._unload_model(name)
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("AsyncMLLoader shutdown complete")

# Global instance
_global_loader: Optional[AsyncMLLoader] = None

def get_ml_loader() -> AsyncMLLoader:
    """Get global ML loader instance"""
    global _global_loader
    if _global_loader is None:
        _global_loader = AsyncMLLoader()
    return _global_loader

async def load_model_async(name: str, force_reload: bool = False) -> Any:
    """Convenience function to load a model asynchronously"""
    loader = get_ml_loader()
    return await loader.load_model(name, force_reload)

def register_standard_models():
    """Register standard models used in the application"""
    loader = get_ml_loader()
    
    # Register K12 Ultra Predictor
    try:
        from src.models.k12_ultra_predictor import K12UltraPredictor
        model_path = Path("results/models/k12_ultra_advanced_model.pkl")
        if model_path.exists():
            loader.register_model(
                "k12_ultra_predictor",
                model_path,
                lambda: K12UltraPredictor()
            )
    except ImportError as e:
        logger.warning(f"Could not register K12UltraPredictor: {e}")
    
    # Register Intervention System
    try:
        from src.models.intervention_system import InterventionRecommendationSystem
        loader.register_model(
            "intervention_system",
            Path("results/models/"),
            lambda: InterventionRecommendationSystem()
        )
    except ImportError as e:
        logger.warning(f"Could not register InterventionSystem: {e}")

# Initialize standard models on import
try:
    register_standard_models()
except Exception as e:
    logger.error(f"Failed to register standard models: {e}")