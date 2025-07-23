"""
Monitoring and metrics collection for the Student Success Prediction API
"""

import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

PREDICTION_COUNT = Counter(
    'predictions_total',
    'Total predictions made',
    ['risk_category']
)

ACTIVE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections'
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage'
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_usage_percent',
    'System disk usage percentage'
)

MODEL_INFERENCE_TIME = Histogram(
    'model_inference_duration_seconds',
    'Model inference time in seconds',
    ['model_type']
)

class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics"""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        self.request_count += 1
        if status_code >= 400:
            self.error_count += 1
    
    def record_prediction(self, risk_category: str, inference_time: float):
        """Record prediction metrics"""
        PREDICTION_COUNT.labels(risk_category=risk_category).inc()
        MODEL_INFERENCE_TIME.labels(model_type='gradient_boosting').observe(inference_time)
    
    def update_system_metrics(self):
        """Update system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            SYSTEM_DISK_USAGE.set(disk_percent)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def get_health_status(self, db: Session = None) -> Dict[str, Any]:
        """Get comprehensive health status"""
        try:
            uptime = time.time() - self.start_time
            
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database health
            db_healthy = True
            db_connections = 0
            
            if db:
                try:
                    # Test database connectivity
                    db.execute("SELECT 1")
                    # Get connection count (PostgreSQL specific)
                    result = db.execute(
                        "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                    ).scalar()
                    db_connections = result or 0
                    ACTIVE_CONNECTIONS.set(db_connections)
                except Exception as e:
                    logger.error(f"Database health check failed: {e}")
                    db_healthy = False
            
            # Calculate error rate
            error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
            
            # Health status
            status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or not db_healthy:
                status = "unhealthy"
            elif cpu_percent > 75 or memory.percent > 75 or error_rate > 5:
                status = "degraded"
            
            return {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": round(uptime, 2),
                "system": {
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory.percent, 2),
                    "disk_percent": round((disk.used / disk.total) * 100, 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                "database": {
                    "healthy": db_healthy,
                    "active_connections": db_connections
                },
                "api": {
                    "total_requests": self.request_count,
                    "error_count": self.error_count,
                    "error_rate_percent": round(error_rate, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

# Global metrics collector instance
metrics_collector = MetricsCollector()

async def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate request duration
    duration = time.time() - start_time
    
    # Extract endpoint from path (remove query parameters)
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code
    
    # Record metrics
    metrics_collector.record_request(method, endpoint, status_code, duration)
    
    return response

async def get_metrics():
    """Get Prometheus metrics"""
    # Update system metrics before returning
    metrics_collector.update_system_metrics()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def record_prediction_metrics(risk_category: str, inference_time: float):
    """Helper function to record prediction metrics"""
    metrics_collector.record_prediction(risk_category, inference_time)

class HealthChecker:
    """Advanced health checking with different levels"""
    
    @staticmethod
    async def liveness_probe() -> Dict[str, Any]:
        """Basic liveness check - is the application running?"""
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def readiness_probe(db: Session = None) -> Dict[str, Any]:
        """Readiness check - is the application ready to serve requests?"""
        try:
            # Check if models are loaded
            from ..models.intervention_system import InterventionRecommendationSystem
            
            # Try to initialize (this checks if models exist)
            try:
                system = InterventionRecommendationSystem()
                model_ready = system.model is not None
            except Exception:
                model_ready = False
            
            # Check database connectivity
            db_ready = True
            if db:
                try:
                    db.execute("SELECT 1")
                except Exception:
                    db_ready = False
            
            # Overall readiness
            ready = model_ready and db_ready
            
            return {
                "status": "ready" if ready else "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "model_loaded": model_ready,
                    "database_connected": db_ready
                }
            }
            
        except Exception as e:
            return {
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    @staticmethod
    async def startup_probe() -> Dict[str, Any]:
        """Startup check - has the application finished starting up?"""
        try:
            # Check if critical components are initialized
            uptime = time.time() - metrics_collector.start_time
            
            # Consider started after 30 seconds or if we've served requests
            started = uptime > 30 or metrics_collector.request_count > 0
            
            return {
                "status": "started" if started else "starting",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": round(uptime, 2)
            }
            
        except Exception as e:
            return {
                "status": "starting",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }