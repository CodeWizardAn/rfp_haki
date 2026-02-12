"""
REST API Performance Integration
================================
Integrates performance optimizations directly into the FastAPI REST API.

Usage:
    from api.api_performance import setup_api_performance
    
    # In your FastAPI app:
    app = FastAPI()
    setup_api_performance(app)
"""

import logging
import time
import functools
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import performance module
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from performance.integration import (
        get_performance_manager,
        init_performance,
        shutdown_performance,
        get_performance_status,
        get_optimization_recommendations,
        cached,
        rate_limited,
        profiled,
        with_timeout,
        AgentPerformanceTracker,
        EmbeddingPerformanceOptimizer
    )
    from performance.rate_limiter import TokenBucket, TokenBucketConfig
    from performance.request_queue import PriorityRequestQueue, QueuedRequest, Priority
    
    PERFORMANCE_AVAILABLE = True
    logger.info("Performance module loaded successfully")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Performance module not available: {e}")


# Request tracking
_request_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'avg_response_time_ms': 0,
    'requests_by_endpoint': {},
    'requests_by_status': {}
}


def setup_api_performance(app):
    """
    Set up performance optimizations for a FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    if not PERFORMANCE_AVAILABLE:
        logger.warning("Performance module not available, skipping setup")
        return
    
    # Initialize performance manager
    pm = init_performance(start_monitoring=True)
    
    # Rate limiters for different endpoint types
    api_limiter = TokenBucket(TokenBucketConfig(capacity=100, refill_rate=100/60))
    search_limiter = TokenBucket(TokenBucketConfig(capacity=20, refill_rate=20/60))
    upload_limiter = TokenBucket(TokenBucketConfig(capacity=5, refill_rate=5/60))
    
    @app.middleware("http")
    async def performance_middleware(request, call_next):
        """Middleware to track request performance and apply rate limiting"""
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Select appropriate rate limiter based on path
        if '/search' in path or '/match' in path:
            limiter = search_limiter
        elif '/upload' in path:
            limiter = upload_limiter
        else:
            limiter = api_limiter
        
        # Check rate limit
        result = limiter.is_allowed(client_ip)
        if not result.allowed:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": result.retry_after,
                    "message": f"Please wait {result.retry_after:.1f} seconds before retrying"
                },
                headers={"Retry-After": str(int(result.retry_after))}
            )
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            success = status_code < 400
        except Exception as e:
            logger.error(f"Request error: {e}")
            status_code = 500
            success = False
            raise
        finally:
            # Record metrics
            elapsed = (time.time() - start_time) * 1000  # ms
            _update_request_stats(path, status_code, elapsed, success)
            
            # Log slow requests
            if elapsed > 1000:  # > 1 second
                logger.warning(f"Slow request: {path} took {elapsed:.2f}ms")
        
        return response
    
    # Add performance endpoints
    @app.get("/api/v1/performance/status", tags=["Performance"])
    async def api_performance_status():
        """Get current performance status"""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "request_stats": _request_stats,
            "system_status": get_performance_status()
        }
    
    @app.get("/api/v1/performance/metrics", tags=["Performance"])
    async def api_performance_metrics():
        """Get detailed performance metrics"""
        pm = get_performance_manager()
        
        return {
            "cache_stats": pm.cache.get_stats() if hasattr(pm.cache, 'get_stats') else {},
            "embedding_cache_stats": pm.embedding_cache.get_stats(),
            "monitor_snapshot": pm.monitor.get_snapshot().to_dict() if pm.monitor else {},
            "request_stats": _request_stats
        }
    
    @app.get("/api/v1/performance/recommendations", tags=["Performance"])
    async def api_performance_recommendations():
        """Get performance optimization recommendations"""
        return {
            "recommendations": get_optimization_recommendations(),
            "generated_at": datetime.now().isoformat()
        }
    
    @app.get("/api/v1/performance/bottlenecks", tags=["Performance"])
    async def api_bottlenecks():
        """Get detected performance bottlenecks"""
        pm = get_performance_manager()
        detector = pm.get_component('bottleneck_detector')
        
        if detector:
            bottlenecks = detector.detect()
            return {
                "bottlenecks": [
                    {
                        "type": b.bottleneck_type.value,
                        "severity": b.severity.value,
                        "description": b.description,
                        "metric_value": b.metric_value,
                        "threshold": b.threshold,
                        "detected_at": b.detected_at.isoformat()
                    }
                    for b in bottlenecks
                ],
                "count": len(bottlenecks)
            }
        
        return {"bottlenecks": [], "count": 0}
    
    # Register shutdown handler
    @app.on_event("shutdown")
    async def shutdown_performance_on_exit():
        shutdown_performance()
        logger.info("Performance system shutdown complete")
    
    logger.info("API performance integration complete")
    return pm


def _update_request_stats(path: str, status_code: int, elapsed_ms: float, success: bool):
    """Update request statistics"""
    _request_stats['total_requests'] += 1
    
    if success:
        _request_stats['successful_requests'] += 1
    else:
        _request_stats['failed_requests'] += 1
    
    # Update average response time (exponential moving average)
    alpha = 0.1
    _request_stats['avg_response_time_ms'] = (
        alpha * elapsed_ms + (1 - alpha) * _request_stats['avg_response_time_ms']
    )
    
    # Track by endpoint
    if path not in _request_stats['requests_by_endpoint']:
        _request_stats['requests_by_endpoint'][path] = {'count': 0, 'avg_ms': 0}
    
    endpoint_stats = _request_stats['requests_by_endpoint'][path]
    endpoint_stats['count'] += 1
    endpoint_stats['avg_ms'] = (
        alpha * elapsed_ms + (1 - alpha) * endpoint_stats['avg_ms']
    )
    
    # Track by status code
    status_key = str(status_code)
    _request_stats['requests_by_status'][status_key] = \
        _request_stats['requests_by_status'].get(status_key, 0) + 1


# Decorator for caching API responses
def cached_response(ttl: int = 300, key_prefix: str = "api"):
    """
    Cache API response decorator
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
    """
    if not PERFORMANCE_AVAILABLE:
        return lambda f: f
    
    return cached(ttl=ttl, key_prefix=key_prefix)


# Decorator for rate limiting specific endpoints
def rate_limit_endpoint(requests_per_minute: int = 30):
    """
    Rate limit decorator for endpoints
    
    Args:
        requests_per_minute: Maximum requests per minute
    """
    if not PERFORMANCE_AVAILABLE:
        return lambda f: f
    
    return rate_limited(requests_per_minute=requests_per_minute)


# Export
__all__ = [
    'setup_api_performance',
    'cached_response',
    'rate_limit_endpoint',
    'PERFORMANCE_AVAILABLE'
]
