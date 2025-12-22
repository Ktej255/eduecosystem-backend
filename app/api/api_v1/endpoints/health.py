"""
Health check endpoint for monitoring system status
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.cache import cache
from app.core.websocket import manager
import time
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns status of all critical system components
    """
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # Database check
    try:
        db = SessionLocal()
        start = time.time()
        db.execute(text("SELECT 1"))
        db.close()
        latency = (time.time() - start) * 1000

        checks["checks"]["database"] = {"status": "up", "latency_ms": round(latency, 2)}
    except Exception as e:
        checks["status"] = "unhealthy"
        checks["checks"]["database"] = {"status": "down", "error": str(e)}

    # Redis/Cache check
    if cache.is_available():
        try:
            start = time.time()
            cache.client.ping()
            latency = (time.time() - start) * 1000

            checks["checks"]["redis"] = {
                "status": "up",
                "latency_ms": round(latency, 2),
            }
        except Exception as e:
            checks["checks"]["redis"] = {"status": "down", "error": str(e)}
    else:
        checks["checks"]["redis"] = {
            "status": "disabled",
            "message": "Redis not configured",
        }

    # WebSocket check
    try:
        active_connections = sum(
            len(conns) for conns in manager.active_connections.values()
        )
        checks["checks"]["websocket"] = {
            "status": "up",
            "active_connections": active_connections,
        }
    except Exception as e:
        checks["checks"]["websocket"] = {"status": "down", "error": str(e)}

    return checks


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe
    Returns 200 if service is ready to accept traffic
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe
    Returns 200 if service is alive (basic check)
    """
    return {"status": "alive"}
