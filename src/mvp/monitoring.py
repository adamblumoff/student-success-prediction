#!/usr/bin/env python3
"""
Production Monitoring and Health Checks

Comprehensive monitoring, metrics collection, and health checking system
for production deployment observability.
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'response_time_ms': round(self.response_time_ms, 2),
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }

class HealthChecker:
    """Comprehensive health checking system."""
    
    def __init__(self):
        self._checks = {}
        self._last_results = {}
        
    def register_check(self, name: str, check_func, timeout: float = 5.0):
        """Register a health check function."""
        self._checks[name] = {
            'function': check_func,
            'timeout': timeout
        }
        logger.debug(f"Registered health check: {name}")
    
    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a single health check."""
        if name not in self._checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' not found",
                response_time_ms=0,
                timestamp=datetime.now()
            )
        
        check_info = self._checks[name]
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                check_info['function'](),
                timeout=check_info['timeout']
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheckResult):
                result.response_time_ms = response_time
                result.timestamp = datetime.now()
                return result
            elif isinstance(result, bool):
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.CRITICAL,
                    message="OK" if result else "Check failed",
                    response_time_ms=response_time,
                    timestamp=datetime.now()
                )
            else:
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    message=str(result) if result else "OK",
                    response_time_ms=response_time,
                    timestamp=datetime.now()
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Health check timed out after {check_info['timeout']}s",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(),
                details={'error': str(e), 'error_type': type(e).__name__}
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        if not self._checks:
            return {}
        
        # Run all checks concurrently
        tasks = [
            asyncio.create_task(self.run_check(name))
            for name in self._checks.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        health_results = {}
        for i, result in enumerate(results):
            check_name = list(self._checks.keys())[i]
            
            if isinstance(result, Exception):
                health_results[check_name] = HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check execution failed: {str(result)}",
                    response_time_ms=0,
                    timestamp=datetime.now()
                )
            else:
                health_results[check_name] = result
        
        # Cache results
        self._last_results = health_results
        return health_results
    
    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status."""
        if not results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.WARNING

class SystemMetrics:
    """System metrics collection for monitoring."""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_metrics = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            except:
                network_metrics = {}
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': network_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

class ApplicationMetrics:
    """Application-specific metrics collection."""
    
    def __init__(self):
        self._request_count = 0
        self._request_times = []
        self._error_count = 0
        self._prediction_count = 0
        self._prediction_times = []
        self._active_sessions = 0
        
    def record_request(self, response_time_ms: float, status_code: int):
        """Record HTTP request metrics."""
        self._request_count += 1
        self._request_times.append(response_time_ms)
        
        if status_code >= 400:
            self._error_count += 1
        
        # Keep only last 1000 request times for memory efficiency
        if len(self._request_times) > 1000:
            self._request_times = self._request_times[-1000:]
    
    def record_prediction(self, response_time_ms: float, student_count: int):
        """Record ML prediction metrics."""
        self._prediction_count += 1
        self._prediction_times.append(response_time_ms)
        
        # Keep only last 100 prediction times
        if len(self._prediction_times) > 100:
            self._prediction_times = self._prediction_times[-100:]
    
    def set_active_sessions(self, count: int):
        """Update active session count."""
        self._active_sessions = count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected application metrics."""
        avg_request_time = (
            sum(self._request_times) / len(self._request_times)
            if self._request_times else 0
        )
        
        avg_prediction_time = (
            sum(self._prediction_times) / len(self._prediction_times)
            if self._prediction_times else 0
        )
        
        error_rate = (
            (self._error_count / self._request_count * 100)
            if self._request_count > 0 else 0
        )
        
        return {
            'requests': {
                'total': self._request_count,
                'avg_response_time_ms': round(avg_request_time, 2),
                'error_count': self._error_count,
                'error_rate_percent': round(error_rate, 2)
            },
            'predictions': {
                'total': self._prediction_count,
                'avg_response_time_ms': round(avg_prediction_time, 2)
            },
            'sessions': {
                'active': self._active_sessions
            },
            'timestamp': datetime.now().isoformat()
        }

# Global instances
health_checker = HealthChecker()
app_metrics = ApplicationMetrics()

# Built-in health checks
async def database_health_check():
    """Check database connectivity."""
    try:
        from .database import check_database_health
        is_healthy = check_database_health()
        
        if is_healthy:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                response_time_ms=0,
                timestamp=datetime.now()
            )
        else:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.CRITICAL,
                message="Database connection failed",
                response_time_ms=0,
                timestamp=datetime.now()
            )
            
    except Exception as e:
        return HealthCheckResult(
            name="database",
            status=HealthStatus.CRITICAL,
            message=f"Database health check error: {str(e)}",
            response_time_ms=0,
            timestamp=datetime.now(),
            details={'error': str(e)}
        )

async def ml_models_health_check():
    """Check ML models availability."""
    try:
        from .services import get_intervention_system, get_k12_ultra_predictor
        
        # Check if models can be loaded
        intervention_system = get_intervention_system()
        k12_predictor = get_k12_ultra_predictor()
        
        issues = []
        if intervention_system is None:
            issues.append("Intervention system not available")
        if k12_predictor is None:
            issues.append("K-12 predictor not available")
        
        if issues:
            return HealthCheckResult(
                name="ml_models",
                status=HealthStatus.WARNING,
                message=f"Some ML models unavailable: {', '.join(issues)}",
                response_time_ms=0,
                timestamp=datetime.now(),
                details={'issues': issues}
            )
        else:
            return HealthCheckResult(
                name="ml_models",
                status=HealthStatus.HEALTHY,
                message="All ML models available",
                response_time_ms=0,
                timestamp=datetime.now()
            )
            
    except Exception as e:
        return HealthCheckResult(
            name="ml_models",
            status=HealthStatus.CRITICAL,
            message=f"ML models health check error: {str(e)}",
            response_time_ms=0,
            timestamp=datetime.now(),
            details={'error': str(e)}
        )

async def system_resources_health_check():
    """Check system resource usage."""
    try:
        metrics = SystemMetrics.get_system_metrics()
        
        if 'error' in metrics:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.WARNING,
                message="Could not collect system metrics",
                response_time_ms=0,
                timestamp=datetime.now(),
                details=metrics
            )
        
        # Check thresholds
        warnings = []
        critical = []
        
        # Memory check
        memory_percent = metrics['memory']['percent']
        if memory_percent > 90:
            critical.append(f"Memory usage critical: {memory_percent}%")
        elif memory_percent > 80:
            warnings.append(f"Memory usage high: {memory_percent}%")
        
        # CPU check
        cpu_percent = metrics['cpu']['percent']
        if cpu_percent > 95:
            critical.append(f"CPU usage critical: {cpu_percent}%")
        elif cpu_percent > 85:
            warnings.append(f"CPU usage high: {cpu_percent}%")
        
        # Disk check
        disk_percent = metrics['disk']['percent']
        if disk_percent > 95:
            critical.append(f"Disk usage critical: {disk_percent}%")
        elif disk_percent > 85:
            warnings.append(f"Disk usage high: {disk_percent}%")
        
        if critical:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"Critical resource issues: {'; '.join(critical)}",
                response_time_ms=0,
                timestamp=datetime.now(),
                details=metrics
            )
        elif warnings:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.WARNING,
                message=f"Resource warnings: {'; '.join(warnings)}",
                response_time_ms=0,
                timestamp=datetime.now(),
                details=metrics
            )
        else:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.HEALTHY,
                message="System resources within normal ranges",
                response_time_ms=0,
                timestamp=datetime.now(),
                details=metrics
            )
            
    except Exception as e:
        return HealthCheckResult(
            name="system_resources",
            status=HealthStatus.CRITICAL,
            message=f"System resources check error: {str(e)}",
            response_time_ms=0,
            timestamp=datetime.now(),
            details={'error': str(e)}
        )

# Register built-in health checks
def register_default_health_checks():
    """Register default health checks."""
    health_checker.register_check("database", database_health_check, timeout=10.0)
    health_checker.register_check("ml_models", ml_models_health_check, timeout=15.0)
    health_checker.register_check("system_resources", system_resources_health_check, timeout=5.0)
    
    logger.info("Default health checks registered")

# API response functions
async def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status for API endpoints."""
    results = await health_checker.run_all_checks()
    overall_status = health_checker.get_overall_status(results)
    
    return {
        'status': overall_status.value,
        'timestamp': datetime.now().isoformat(),
        'checks': {name: result.to_dict() for name, result in results.items()},
        'summary': {
            'total_checks': len(results),
            'healthy': len([r for r in results.values() if r.status == HealthStatus.HEALTHY]),
            'warning': len([r for r in results.values() if r.status == HealthStatus.WARNING]),
            'critical': len([r for r in results.values() if r.status == HealthStatus.CRITICAL])
        }
    }

async def get_metrics() -> Dict[str, Any]:
    """Get comprehensive metrics for monitoring."""
    system_metrics = SystemMetrics.get_system_metrics()
    application_metrics = app_metrics.get_metrics()
    
    return {
        'system': system_metrics,
        'application': application_metrics,
        'timestamp': datetime.now().isoformat()
    }

# Monitoring middleware for FastAPI
class MonitoringMiddleware:
    """Middleware to collect request metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Intercept response to get status code
        response_started = False
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
        
        # Record metrics
        if response_started:
            response_time = (time.time() - start_time) * 1000
            app_metrics.record_request(response_time, status_code)

# Initialize monitoring on startup
def initialize_monitoring():
    """Initialize monitoring system."""
    register_default_health_checks()
    logger.info("✅ Monitoring system initialized")