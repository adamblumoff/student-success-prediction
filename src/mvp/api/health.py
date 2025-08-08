#!/usr/bin/env python3
"""
Health Check API Endpoints

Provides comprehensive system health monitoring for production deployment.
Includes database connectivity, ML model status, and system resource checks.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import sys
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint for load balancers"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "mvp-api"
    })

@router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with system diagnostics"""
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "student-success-predictor",
        "version": "2.0",
        "checks": {}
    }
    
    # Database connectivity check
    try:
        from mvp.database import check_database_health, get_db_session
        db_healthy = check_database_health()
        
        if db_healthy:
            # Test database query
            with get_db_session() as session:
                from mvp.models import Institution
                institution_count = session.query(Institution).count()
                health_status["checks"]["database"] = {
                    "status": "healthy",
                    "connection": "active",
                    "institutions": institution_count,
                    "type": "postgresql" if os.getenv('DATABASE_URL') else "sqlite"
                }
        else:
            raise Exception("Database health check failed")
            
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "type": "sqlite_fallback"
        }
        health_status["status"] = "degraded"

    # ML Models check
    try:
        from src.models.intervention_system import InterventionRecommendationSystem
        from src.models.k12_ultra_predictor import K12UltraPredictor
        
        # Test intervention system loading
        intervention_system = InterventionRecommendationSystem()
        health_status["checks"]["ml_models"] = {
            "status": "healthy",
            "intervention_system": "loaded",
            "k12_predictor": "available",
            "model_path": "results/models/"
        }
        
    except Exception as e:
        health_status["checks"]["ml_models"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # System resources check
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["checks"]["system_resources"] = {
            "status": "healthy",
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 1)
            },
            "cpu_percent": psutil.cpu_percent(interval=1)
        }
        
        # Check for resource warnings
        if memory.percent > 85:
            health_status["checks"]["system_resources"]["warnings"] = ["High memory usage"]
        if disk.percent > 90:
            health_status["checks"]["system_resources"]["warnings"] = health_status["checks"]["system_resources"].get("warnings", []) + ["Low disk space"]
            
    except Exception as e:
        health_status["checks"]["system_resources"] = {
            "status": "unknown",
            "error": str(e)
        }

    # Authentication system check
    try:
        from mvp.simple_auth import simple_auth
        from fastapi.security import HTTPAuthorizationCredentials
        
        # Test API key validation
        test_key = os.getenv('MVP_API_KEY', 'dev-key-change-me')
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=test_key)
        auth_result = simple_auth(credentials)
        
        health_status["checks"]["authentication"] = {
            "status": "healthy",
            "api_key_validation": "working",
            "session_auth": "enabled"
        }
        
    except Exception as e:
        health_status["checks"]["authentication"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Static files check
    try:
        static_dir = Path(__file__).parent.parent / "static"
        css_file = static_dir / "css" / "style.css"
        js_file = static_dir / "js" / "app.js"
        
        health_status["checks"]["static_files"] = {
            "status": "healthy",
            "css_exists": css_file.exists(),
            "js_exists": js_file.exists(),
            "static_dir": str(static_dir)
        }
        
    except Exception as e:
        health_status["checks"]["static_files"] = {
            "status": "unknown",
            "error": str(e)
        }

    # Response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Overall status determination
    unhealthy_checks = [check for check in health_status["checks"].values() if check.get("status") == "unhealthy"]
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
    elif health_status["status"] != "degraded":
        health_status["status"] = "healthy"

    return JSONResponse(health_status)

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    try:
        # Check critical components only
        from mvp.database import check_database_health
        from src.models.intervention_system import InterventionRecommendationSystem
        
        # Database must be accessible
        if not check_database_health():
            raise Exception("Database not accessible")
        
        # ML models must load
        intervention_system = InterventionRecommendationSystem()
        
        return JSONResponse({
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@router.get("/health/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return JSONResponse({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - psutil.boot_time()) if hasattr(psutil, 'boot_time') else None
    })

@router.get("/health/metrics")
async def system_metrics():
    """Basic system metrics for monitoring"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return JSONResponse({
            "timestamp": datetime.utcnow().isoformat(),
            "memory_usage_percent": memory.percent,
            "disk_usage_percent": round((disk.used / disk.total) * 100, 1),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "available_memory_mb": round(memory.available / (1024**2)),
            "free_disk_gb": round(disk.free / (1024**3), 2)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics unavailable: {str(e)}")