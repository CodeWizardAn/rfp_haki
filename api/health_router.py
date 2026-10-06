"""
Enterprise Health, Readiness & Metrics Endpoints
Compliant with Kubernetes / Cloud Liveness & Readiness probe standards.
"""

import time
import os
from typing import Dict, Any
from fastapi import APIRouter, Response, status
from pydantic import BaseModel

health_router = APIRouter(tags=["Enterprise Observability"])

_START_TIME = time.time()

class ServiceHealthStatus(BaseModel):
    status: str
    uptime_seconds: float
    environment: str
    dependencies: Dict[str, Any]

@health_router.get("/healthz", status_code=status.HTTP_200_OK)
@health_router.get("/livez", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe: returns 200 if the process is alive."""
    return {"status": "alive", "timestamp": time.time()}

@health_router.get("/readyz")
async def readiness_probe(response: Response):
    """
    Readiness probe: validates critical dependencies before routing production traffic.
    Returns 200 if ready, 503 if an essential dependency is unavailable.
    """
    deps: Dict[str, Any] = {}
    is_ready = True

    # 1. Check Redis / Distributed Cache
    try:
        from core.redis_client import get_distributed_state
        state = get_distributed_state()
        if state._redis is not None:
            state._redis.ping()
            deps["redis"] = {"status": "healthy"}
        else:
            deps["redis"] = {"status": "fallback_in_memory", "warning": "Redis not configured"}
    except Exception as e:
        deps["redis"] = {"status": "unhealthy", "error": str(e)}

    # 2. Check Database Connectivity
    try:
        from database.db_engine import engine
        if engine is not None:
            with engine.connect() as conn:
                deps["database"] = {"status": "healthy", "type": engine.name}
        else:
            deps["database"] = {"status": "available", "type": "sqlite_fallback"}
    except Exception as e:
        deps["database"] = {"status": "unhealthy", "error": str(e)}
        is_ready = False

    # 3. Check Storage Backend
    try:
        from core.storage import get_storage_provider
        storage = get_storage_provider()
        deps["storage"] = {"status": "healthy", "type": storage.__class__.__name__}
    except Exception as e:
        deps["storage"] = {"status": "unhealthy", "error": str(e)}

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ServiceHealthStatus(
        status="ready" if is_ready else "degraded",
        uptime_seconds=round(time.time() - _START_TIME, 2),
        environment=os.getenv("ENVIRONMENT", "production"),
        dependencies=deps,
    )

@health_router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint for cluster monitoring."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return Response(content="# Prometheus client not installed\n", media_type="text/plain")
