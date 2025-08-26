#!/usr/bin/env python3
"""
GPT Analysis Caching Service

Implements intelligent caching for GPT-OSS analysis results to reduce computational
overhead and improve response times. Includes cache invalidation strategies based
on student data changes.
"""

import sys
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mvp.logging_config import get_logger

logger = get_logger(__name__)

class GPTCacheService:
    """Service for caching GPT analysis results with intelligent invalidation."""
    
    def __init__(self, max_cache_size: int = 1000, default_ttl_minutes: int = 60):
        """
        Initialize GPT cache service.
        
        Args:
            max_cache_size: Maximum number of cached entries
            default_ttl_minutes: Default time-to-live for cache entries in minutes
        """
        self.max_cache_size = max_cache_size
        self.default_ttl_minutes = default_ttl_minutes
        
        # In-memory cache storage
        self.cache = {}  # cache_key -> cache_entry
        self.access_times = {}  # cache_key -> last_access_time
        self.creation_times = {}  # cache_key -> creation_time
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "invalidations": 0,
            "total_requests": 0
        }
        
        # Cache configuration by analysis type
        self.cache_configs = {
            "student_analysis": {
                "ttl_minutes": 30,  # Student analysis expires quickly
                "depends_on": ["student_data", "predictions", "interventions"]
            },
            "cohort_analysis": {
                "ttl_minutes": 120,  # Cohort analysis can be cached longer
                "depends_on": ["cohort_data", "risk_distribution"]
            },
            "intervention_planning": {
                "ttl_minutes": 45,  # Intervention plans should be relatively fresh
                "depends_on": ["student_data", "intervention_history", "available_resources"]
            },
            "quick_insight": {
                "ttl_minutes": 15,  # Quick insights should be very fresh
                "depends_on": ["student_data"]
            },
            "narrative_report": {
                "ttl_minutes": 60,  # Reports can be cached moderately
                "depends_on": ["student_data", "predictions", "interventions"]
            }
        }
        
        logger.info(f"🗄️ GPT Cache Service initialized with {max_cache_size} max entries")
    
    def generate_cache_key(self, analysis_type: str, input_data: Dict[str, Any], 
                          additional_params: Dict[str, Any] = None) -> str:
        """
        Generate a unique cache key based on analysis type and input data.
        
        Args:
            analysis_type: Type of GPT analysis
            input_data: Input data for the analysis
            additional_params: Additional parameters affecting the analysis
            
        Returns:
            Unique cache key string
        """
        # Create a normalized representation of the input
        cache_data = {
            "type": analysis_type,
            "data": self._normalize_cache_data(input_data),
        }
        
        # Include additional parameters
        if additional_params:
            cache_data["params"] = self._normalize_cache_data(additional_params)
        
        # Create hash of the normalized data
        cache_json = json.dumps(cache_data, sort_keys=True, separators=(',', ':'))
        cache_key = hashlib.sha256(cache_json.encode()).hexdigest()[:16]  # 16 char hash
        
        return f"{analysis_type}_{cache_key}"
    
    def _normalize_cache_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize data for consistent cache key generation."""
        if not isinstance(data, dict):
            return {"value": str(data)}
        
        normalized = {}
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                normalized[key] = value
            elif isinstance(value, (list, tuple)):
                # Sort lists for consistent ordering
                try:
                    normalized[key] = sorted([str(v) for v in value])
                except:
                    normalized[key] = [str(v) for v in value]
            elif isinstance(value, dict):
                normalized[key] = self._normalize_cache_data(value)
            else:
                normalized[key] = str(value)
        
        return normalized
    
    def get_cached_analysis(self, analysis_type: str, input_data: Dict[str, Any],
                           additional_params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached GPT analysis if available and valid.
        
        Args:
            analysis_type: Type of GPT analysis
            input_data: Input data for the analysis
            additional_params: Additional parameters
            
        Returns:
            Cached analysis result or None if not available
        """
        self.stats["total_requests"] += 1
        
        try:
            # Generate cache key
            cache_key = self.generate_cache_key(analysis_type, input_data, additional_params)
            
            # Check if cached entry exists
            if cache_key not in self.cache:
                self.stats["misses"] += 1
                logger.debug(f"🔍 Cache miss for {analysis_type}")
                return None
            
            # Check if entry is still valid (TTL)
            if self._is_cache_entry_expired(cache_key, analysis_type):
                self._remove_cache_entry(cache_key)
                self.stats["misses"] += 1
                logger.debug(f"⏰ Cache expired for {analysis_type}")
                return None
            
            # Update access time and return cached result
            self.access_times[cache_key] = time.time()
            cached_result = self.cache[cache_key]
            
            self.stats["hits"] += 1
            logger.debug(f"✅ Cache hit for {analysis_type} (saved ~{cached_result.get('processing_time_seconds', 0):.1f}s)")
            
            # Add cache metadata to result
            result = cached_result.copy()
            result["_cache_info"] = {
                "cached": True,
                "cache_key": cache_key,
                "cached_at": self.creation_times.get(cache_key),
                "cache_hit": True
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Cache retrieval error: {str(e)}")
            self.stats["misses"] += 1
            return None
    
    def cache_analysis_result(self, analysis_type: str, input_data: Dict[str, Any],
                             analysis_result: Dict[str, Any], 
                             additional_params: Dict[str, Any] = None,
                             custom_ttl_minutes: Optional[int] = None) -> None:
        """
        Cache a GPT analysis result.
        
        Args:
            analysis_type: Type of GPT analysis
            input_data: Input data used for the analysis
            analysis_result: The analysis result to cache
            additional_params: Additional parameters used
            custom_ttl_minutes: Custom TTL override
        """
        try:
            # Generate cache key
            cache_key = self.generate_cache_key(analysis_type, input_data, additional_params)
            
            # Ensure we don't exceed cache size limit
            self._ensure_cache_capacity()
            
            # Determine TTL
            ttl_minutes = custom_ttl_minutes or self.cache_configs.get(
                analysis_type, {}
            ).get("ttl_minutes", self.default_ttl_minutes)
            
            # Store the result with metadata
            cache_entry = analysis_result.copy()
            cache_entry["_cache_metadata"] = {
                "analysis_type": analysis_type,
                "cache_key": cache_key,
                "ttl_minutes": ttl_minutes,
                "created_at": datetime.now().isoformat(),
                "input_data_hash": hashlib.sha256(
                    json.dumps(input_data, sort_keys=True).encode()
                ).hexdigest()[:8]
            }
            
            # Store in cache
            current_time = time.time()
            self.cache[cache_key] = cache_entry
            self.creation_times[cache_key] = current_time
            self.access_times[cache_key] = current_time
            
            logger.debug(f"💾 Cached {analysis_type} result (TTL: {ttl_minutes}m)")
            
        except Exception as e:
            logger.error(f"❌ Cache storage error: {str(e)}")
    
    def _is_cache_entry_expired(self, cache_key: str, analysis_type: str) -> bool:
        """Check if a cache entry has expired based on TTL."""
        if cache_key not in self.creation_times:
            return True
        
        # Get TTL for this analysis type
        ttl_minutes = self.cache_configs.get(analysis_type, {}).get(
            "ttl_minutes", self.default_ttl_minutes
        )
        
        # Check if expired
        creation_time = self.creation_times[cache_key]
        expiry_time = creation_time + (ttl_minutes * 60)  # Convert to seconds
        
        return time.time() > expiry_time
    
    def _ensure_cache_capacity(self) -> None:
        """Ensure cache doesn't exceed maximum size by evicting old entries."""
        while len(self.cache) >= self.max_cache_size:
            # Find least recently used entry
            oldest_key = min(self.access_times.keys(), 
                           key=lambda k: self.access_times[k])
            
            self._remove_cache_entry(oldest_key)
            self.stats["evictions"] += 1
            logger.debug(f"🗑️ Evicted cache entry {oldest_key}")
    
    def _remove_cache_entry(self, cache_key: str) -> None:
        """Remove a cache entry completely."""
        self.cache.pop(cache_key, None)
        self.access_times.pop(cache_key, None)
        self.creation_times.pop(cache_key, None)
    
    def invalidate_student_cache(self, student_id: int) -> int:
        """
        Invalidate all cache entries related to a specific student.
        
        Args:
            student_id: ID of the student whose cache should be invalidated
            
        Returns:
            Number of cache entries invalidated
        """
        invalidated_count = 0
        student_str = str(student_id)
        
        # Find all cache entries that might be related to this student
        keys_to_remove = []
        
        for cache_key, cache_entry in self.cache.items():
            # Check if this entry is related to the student
            if self._is_cache_entry_related_to_student(cache_entry, student_str):
                keys_to_remove.append(cache_key)
        
        # Remove identified entries
        for cache_key in keys_to_remove:
            self._remove_cache_entry(cache_key)
            invalidated_count += 1
        
        self.stats["invalidations"] += invalidated_count
        
        if invalidated_count > 0:
            logger.info(f"🗑️ Invalidated {invalidated_count} cache entries for student {student_id}")
        
        return invalidated_count
    
    def _is_cache_entry_related_to_student(self, cache_entry: Dict[str, Any], 
                                         student_str: str) -> bool:
        """Check if a cache entry is related to a specific student."""
        # Check in various common fields where student ID might appear
        entry_str = json.dumps(cache_entry, default=str).lower()
        
        # Look for student ID patterns
        student_patterns = [
            f'"student_id":{student_str}',
            f'"student_id":"{student_str}"',
            f'student_{student_str}',
            f'"id":{student_str}',
            f'"id":"{student_str}"'
        ]
        
        return any(pattern in entry_str for pattern in student_patterns)
    
    def invalidate_cohort_cache(self, institution_id: int, grade_level: str = None) -> int:
        """
        Invalidate cohort-level cache entries for an institution.
        
        Args:
            institution_id: Institution whose cohort cache should be invalidated
            grade_level: Optional specific grade level to invalidate
            
        Returns:
            Number of cache entries invalidated
        """
        invalidated_count = 0
        keys_to_remove = []
        
        for cache_key, cache_entry in self.cache.items():
            # Check if this is a cohort analysis for the institution
            if self._is_cache_entry_related_to_cohort(cache_entry, institution_id, grade_level):
                keys_to_remove.append(cache_key)
        
        # Remove identified entries
        for cache_key in keys_to_remove:
            self._remove_cache_entry(cache_key)
            invalidated_count += 1
        
        self.stats["invalidations"] += invalidated_count
        
        if invalidated_count > 0:
            logger.info(f"🗑️ Invalidated {invalidated_count} cohort cache entries for institution {institution_id}")
        
        return invalidated_count
    
    def _is_cache_entry_related_to_cohort(self, cache_entry: Dict[str, Any],
                                        institution_id: int, grade_level: str = None) -> bool:
        """Check if cache entry is related to cohort analysis."""
        metadata = cache_entry.get("_cache_metadata", {})
        analysis_type = metadata.get("analysis_type", "")
        
        # Only invalidate cohort-related analysis types
        if analysis_type not in ["cohort_analysis"]:
            return False
        
        entry_str = json.dumps(cache_entry, default=str)
        
        # Check for institution ID
        if f'"institution_id":{institution_id}' not in entry_str:
            return False
        
        # Check for grade level if specified
        if grade_level and f'"grade_level":"{grade_level}"' not in entry_str:
            return False
        
        return True
    
    def clear_expired_entries(self) -> int:
        """
        Manually clear all expired cache entries.
        
        Returns:
            Number of expired entries removed
        """
        expired_keys = []
        
        for cache_key in list(self.cache.keys()):
            # Extract analysis type from cache key
            analysis_type = cache_key.split('_')[0] if '_' in cache_key else "unknown"
            
            if self._is_cache_entry_expired(cache_key, analysis_type):
                expired_keys.append(cache_key)
        
        # Remove expired entries
        for cache_key in expired_keys:
            self._remove_cache_entry(cache_key)
        
        removed_count = len(expired_keys)
        if removed_count > 0:
            logger.info(f"🧹 Cleared {removed_count} expired cache entries")
        
        return removed_count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = self.stats["total_requests"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate memory usage estimate
        cache_size_estimate = sum(
            len(json.dumps(entry, default=str)) for entry in self.cache.values()
        )
        
        # Analyze cache by type
        type_breakdown = {}
        for cache_key, entry in self.cache.items():
            analysis_type = cache_key.split('_')[0] if '_' in cache_key else "unknown"
            if analysis_type not in type_breakdown:
                type_breakdown[analysis_type] = 0
            type_breakdown[analysis_type] += 1
        
        return {
            "cache_performance": {
                "hit_rate_percentage": round(hit_rate, 2),
                "total_requests": total_requests,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "invalidations": self.stats["invalidations"]
            },
            "cache_size": {
                "current_entries": len(self.cache),
                "max_entries": self.max_cache_size,
                "utilization_percentage": round(len(self.cache) / self.max_cache_size * 100, 1),
                "estimated_memory_bytes": cache_size_estimate
            },
            "cache_breakdown": type_breakdown,
            "configuration": {
                "default_ttl_minutes": self.default_ttl_minutes,
                "analysis_type_configs": self.cache_configs
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache service."""
        try:
            # Clear expired entries as part of health check
            expired_cleared = self.clear_expired_entries()
            
            # Get current statistics
            stats = self.get_cache_statistics()
            
            # Determine health status
            utilization = stats["cache_size"]["utilization_percentage"]
            hit_rate = stats["cache_performance"]["hit_rate_percentage"]
            
            if utilization > 95:
                health_status = "warning_high_utilization"
            elif hit_rate < 20 and stats["cache_performance"]["total_requests"] > 10:
                health_status = "warning_low_hit_rate"
            else:
                health_status = "healthy"
            
            return {
                "service": "GPT Cache Service",
                "status": health_status,
                "expired_entries_cleared": expired_cleared,
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Cache health check failed: {str(e)}")
            return {
                "service": "GPT Cache Service",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def preload_common_analyses(self, common_patterns: List[Dict[str, Any]]) -> int:
        """
        Preload cache with commonly requested analysis patterns.
        
        Args:
            common_patterns: List of common analysis patterns to preload
            
        Returns:
            Number of patterns preloaded
        """
        preloaded_count = 0
        
        for pattern in common_patterns:
            try:
                analysis_type = pattern.get("analysis_type")
                input_data = pattern.get("input_data", {})
                mock_result = pattern.get("mock_result")
                
                if analysis_type and mock_result:
                    self.cache_analysis_result(
                        analysis_type=analysis_type,
                        input_data=input_data,
                        analysis_result=mock_result,
                        custom_ttl_minutes=pattern.get("ttl_minutes")
                    )
                    preloaded_count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to preload pattern: {str(e)}")
                continue
        
        if preloaded_count > 0:
            logger.info(f"📚 Preloaded {preloaded_count} common analysis patterns")
        
        return preloaded_count
    
    def export_cache_state(self) -> Dict[str, Any]:
        """Export current cache state for backup/analysis purposes."""
        return {
            "cache_entries": len(self.cache),
            "statistics": self.get_cache_statistics(),
            "configuration": {
                "max_cache_size": self.max_cache_size,
                "default_ttl_minutes": self.default_ttl_minutes,
                "cache_configs": self.cache_configs
            },
            "export_timestamp": datetime.now().isoformat()
        }