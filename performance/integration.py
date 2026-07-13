"""
Performance Integration Module
==============================
Integrates all performance optimization components with the main application.

This module provides:
1. Application-wide performance initialization
2. Database integration with connection pooling
3. API middleware for rate limiting and caching
4. Agent performance monitoring
5. Automatic bottleneck detection
6. Performance dashboard data collection
"""

import logging
import threading
import functools
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager
from datetime import datetime
import time
import os
import sys

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

# Import all performance modules
from .redis_cache import RedisCache, RedisCacheConfig, InMemoryFallback
from .embedding_cache import LRUCache, EmbeddingCache
from .query_optimizer import QueryOptimizer, QueryPlan
from .db_indexing import IndexManager, IndexRecommendation
from .connection_pool import (
    BaseConnectionPool, PoolConfig, PoolStats,
    DatabasePool, ConnectionPoolManager
)
from .batch_processor import BatchProcessor, BatchConfig, BatchResult
from .async_ops import AsyncExecutor, TaskManager
from .parallel_matcher import ParallelMatcher, MatchTask, MatchResult
from .load_balancer import LoadBalancer, BalancingStrategy, LoadBalancerConfig
from .rate_limiter import (
    TokenBucket, TokenBucketConfig,
    SlidingWindowLimiter, SlidingWindowConfig,
    RateLimitMiddleware
)
from .request_queue import PriorityRequestQueue, QueuedRequest, Priority, QueueConfig
from .resource_monitor import ResourceMonitor, MonitorConfig, SystemSnapshot
from .profiler import FunctionProfiler, CodeProfiler
from .bottleneck_detector import BottleneckDetector, DetectorConfig, Bottleneck
from .auto_scaler import AutoScaler, ScalerConfig, ScalingPolicy
from .dashboard import PerformanceDashboard, DashboardConfig, MetricsRegistry
from .optimizer import PerformanceOptimizer


class PerformanceManager:
    """
    Central performance management singleton.
    Coordinates all performance optimization components.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._components: Dict[str, Any] = {}
        self._started = False
        
        # Initialize core components
        self._init_caching()
        self._init_connection_pools()
        self._init_rate_limiting()
        self._init_monitoring()
        self._init_optimization()
        
        logger.info("PerformanceManager initialized")
    
    def _init_caching(self):
        """Initialize caching components"""
        # Redis cache (with in-memory fallback)
        try:
            redis_config = RedisCacheConfig(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                key_prefix='haki:',
                default_ttl=3600
            )
            self._components['redis_cache'] = RedisCache(redis_config)
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory fallback: {e}")
            self._components['redis_cache'] = InMemoryFallback()
        
        # Embedding cache for vector operations
        self._components['embedding_cache'] = EmbeddingCache(
            max_embeddings=10000,
            max_memory_mb=500,
            default_ttl=7200
        )
        
        # Query result cache
        self._components['query_cache'] = LRUCache(max_size=5000, max_memory_mb=200)
        
        logger.info("Caching components initialized")
    
    def _init_connection_pools(self):
        """Initialize connection pool management"""
        self._components['pool_manager'] = ConnectionPoolManager()
        
        # Query optimizer
        self._components['query_optimizer'] = QueryOptimizer(
            slow_query_threshold_ms=100.0
        )
        
        # Index manager
        self._components['index_manager'] = IndexManager()
        
        logger.info("Connection pool components initialized")
    
    def _init_rate_limiting(self):
        """Initialize rate limiting components"""
        # API rate limiter - 100 requests per minute per client
        api_config = TokenBucketConfig(capacity=100, refill_rate=100/60)
        self._components['api_rate_limiter'] = TokenBucket(api_config)
        
        # Heavy operation limiter - 10 per minute
        heavy_config = TokenBucketConfig(capacity=10, refill_rate=10/60)
        self._components['heavy_rate_limiter'] = TokenBucket(heavy_config)
        
        # Request queue for managing load
        queue_config = QueueConfig(max_size=10000)
        self._components['request_queue'] = PriorityRequestQueue(config=queue_config)
        
        # Load balancer for distributed operations
        lb_config = LoadBalancerConfig(
            strategy=BalancingStrategy.LEAST_CONNECTIONS,
            health_check_interval=30
        )
        self._components['load_balancer'] = LoadBalancer(lb_config)
        
        logger.info("Rate limiting components initialized")
    
    def _init_monitoring(self):
        """Initialize monitoring components"""
        # Resource monitor
        monitor_config = MonitorConfig(
            interval=5.0,
            cpu_warning=70.0,
            cpu_critical=80.0,
            memory_warning=75.0,
            memory_critical=85.0,
            disk_warning=80.0,
            disk_critical=90.0
        )
        self._components['resource_monitor'] = ResourceMonitor(monitor_config)
        
        # Performance profiler
        self._components['profiler'] = FunctionProfiler()
        
        # Bottleneck detector
        detector_config = DetectorConfig(
            check_interval=30,
            history_window=300
        )
        self._components['bottleneck_detector'] = BottleneckDetector(detector_config)
        
        # Auto scaler
        scaler_config = ScalerConfig(check_interval=60, default_cooldown=300)
        self._components['auto_scaler'] = AutoScaler(scaler_config)
        
        # Performance dashboard
        dashboard_config = DashboardConfig(refresh_interval=5)
        self._components['dashboard'] = PerformanceDashboard(dashboard_config)
        
        # Metrics registry
        self._components['metrics_registry'] = MetricsRegistry()
        
        logger.info("Monitoring components initialized")
    
    def _init_optimization(self):
        """Initialize optimization components"""
        self._components['optimizer'] = PerformanceOptimizer()
        
        # Batch processor for bulk operations
        batch_config = BatchConfig(
            batch_size=100,
            max_workers=4,
            max_retries=3
        )
        self._components['batch_processor'] = BatchProcessor(batch_config)
        
        # Async executor
        self._components['async_executor'] = AsyncExecutor(max_workers=8)
        
        # Parallel matcher for spec matching
        self._components['parallel_matcher'] = ParallelMatcher(num_workers=4, chunk_size=50)
        
        logger.info("Optimization components initialized")
    
    def start(self):
        """Start all performance components"""
        if self._started:
            return
        
        # Start resource monitor
        self._components['resource_monitor'].start()
        
        # Start bottleneck detector
        self._components['bottleneck_detector'].start()
        
        # Start async executor
        self._components['async_executor'].start()
        
        self._started = True
        logger.info("Performance components started")
    
    def stop(self):
        """Stop all performance components"""
        if not self._started:
            return
        
        # Stop in reverse order
        self._components.get('async_executor', None) and self._components['async_executor'].stop()
        self._components.get('bottleneck_detector', None) and self._components['bottleneck_detector'].stop()
        self._components.get('resource_monitor', None) and self._components['resource_monitor'].stop()
        self._components.get('auto_scaler', None) and self._components['auto_scaler'].stop()
        
        # Close connection pools
        pool_manager = self._components.get('pool_manager')
        if pool_manager:
            pool_manager.close_all()
        
        self._started = False
        logger.info("Performance components stopped")
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get a specific performance component"""
        return self._components.get(name)
    
    @property
    def cache(self):
        """Get Redis cache (or fallback)"""
        return self._components['redis_cache']
    
    @property
    def embedding_cache(self):
        """Get embedding cache"""
        return self._components['embedding_cache']
    
    @property
    def query_optimizer(self):
        """Get query optimizer"""
        return self._components['query_optimizer']
    
    @property
    def profiler(self):
        """Get function profiler"""
        return self._components['profiler']
    
    @property
    def monitor(self):
        """Get resource monitor"""
        return self._components['resource_monitor']
    
    @property
    def dashboard(self):
        """Get performance dashboard"""
        return self._components['dashboard']
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all performance components"""
        status = {
            'started': self._started,
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for name, component in self._components.items():
            if hasattr(component, 'get_stats'):
                status['components'][name] = component.get_stats()
            elif hasattr(component, 'get_status'):
                status['components'][name] = component.get_status()
            else:
                status['components'][name] = {'active': True}
        
        return status
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get performance optimization recommendations"""
        optimizer = self._components.get('optimizer')
        if not optimizer:
            return []

        from performance.optimizer import AnalysisContext

        monitor = self._components.get('resource_monitor')
        monitor_stats = monitor.get_stats() if monitor else {}
        cache = self._components.get('redis_cache')
        cache_stats = cache.get_stats() if cache and hasattr(cache, 'get_stats') else {}

        context = AnalysisContext(
            cpu_usage=monitor_stats.get('current', {}).get('cpu_percent', 0.0),
            memory_usage=monitor_stats.get('current', {}).get('memory_percent', 0.0),
            cache_hit_rate=cache_stats.get('hit_rate', 0.0),
        )
        return optimizer.analyze(context)


# Global performance manager instance
_performance_manager: Optional[PerformanceManager] = None


def get_performance_manager() -> PerformanceManager:
    """Get or create the global performance manager"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager()
    return _performance_manager


# =============================================================================
# Decorators for Application Integration
# =============================================================================

def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            pm = get_performance_manager()
            cache = pm.cache
            
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


def rate_limited(requests_per_minute: int = 60, key_func: Callable = None):
    """
    Decorator to rate limit function calls
    
    Args:
        requests_per_minute: Max requests allowed per minute
        key_func: Function to extract rate limit key from args
    """
    def decorator(func: Callable) -> Callable:
        limiter = SlidingWindowLimiter(SlidingWindowConfig(
            window_seconds=60,
            max_requests=requests_per_minute
        ))
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = "global"
            
            # Check rate limit
            result = limiter.is_allowed(key)
            if not result.allowed:
                raise Exception(f"Rate limit exceeded. Retry after {result.retry_after:.2f} seconds")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def profiled(func: Callable) -> Callable:
    """Decorator to profile function execution"""
    pm = get_performance_manager()
    profiler = pm.profiler
    return profiler.profile(func)


def with_timeout(seconds: float):
    """
    Decorator to add timeout to function execution
    
    Args:
        seconds: Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
        return wrapper
    return decorator


def batch_execute(batch_size: int = 100):
    """
    Decorator to enable batch processing for functions that accept lists
    
    Args:
        batch_size: Size of each batch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(items: List[Any], *args, **kwargs):
            pm = get_performance_manager()
            processor = pm.get_component('batch_processor')
            
            def process_item(item):
                return func([item], *args, **kwargs)
            
            config = BatchConfig(batch_size=batch_size)
            result = processor.process(items, process_item)
            return result
        return wrapper
    return decorator


# =============================================================================
# Database Integration
# =============================================================================

class DatabasePerformanceIntegration:
    """
    Integrates performance optimizations with database operations
    """
    
    def __init__(self, db_url: str = None):
        self.pm = get_performance_manager()
        self.db_url = db_url
        self._pool: Optional[DatabasePool] = None
    
    def setup_pool(self, db_url: str = None):
        """Set up optimized database connection pool"""
        url = db_url or self.db_url
        if not url:
            raise ValueError("Database URL required")
        
        config = PoolConfig(
            min_size=2,
            max_size=10,
            max_overflow=5,
            timeout=30.0,
            recycle=3600
        )
        
        pool_manager = self.pm.get_component('pool_manager')
        self._pool = pool_manager.create_database_pool('main', url, config)
        
        return self._pool
    
    @contextmanager
    def connection(self):
        """Get a connection from the pool with performance tracking"""
        if not self._pool:
            raise RuntimeError("Database pool not initialized. Call setup_pool() first.")
        
        start = time.time()
        conn = self._pool.get()
        
        try:
            yield conn.connection
        finally:
            self._pool.put(conn)
            
            # Record metrics
            elapsed = time.time() - start
            registry = self.pm.get_component('metrics_registry')
            if registry:
                registry.record('db.connection_time', elapsed * 1000)
    
    def optimize_query(self, query: str) -> QueryPlan:
        """Analyze and optimize a SQL query"""
        optimizer = self.pm.query_optimizer
        return optimizer.analyze(query)
    
    def get_index_recommendations(self, table_name: str) -> List[IndexRecommendation]:
        """Get index recommendations for a table"""
        index_manager = self.pm.get_component('index_manager')
        return index_manager.recommend(table_name)


# =============================================================================
# API Integration (FastAPI/Flask)
# =============================================================================

class FastAPIPerformanceMiddleware:
    """
    FastAPI middleware for performance optimization
    """
    
    def __init__(self, app):
        self.app = app
        self.pm = get_performance_manager()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        request_id = str(time.time())
        
        # Rate limiting check
        rate_limiter = self.pm.get_component('api_rate_limiter')
        client_ip = scope.get("client", ("unknown",))[0]
        
        if rate_limiter:
            result = rate_limiter.is_allowed(client_ip)
            if not result.allowed:
                response = {
                    "error": "Rate limit exceeded",
                    "retry_after": result.retry_after
                }
                await self._send_json_response(send, response, 429)
                return
        
        # Process request
        await self.app(scope, receive, send)
        
        # Record metrics
        elapsed = time.time() - start_time
        registry = self.pm.get_component('metrics_registry')
        if registry:
            path = scope.get("path", "unknown")
            registry.record(f'api.request_time.{path}', elapsed * 1000)
            registry.record('api.total_requests', 1)
    
    async def _send_json_response(self, send, data: dict, status: int):
        import json
        body = json.dumps(data).encode()
        
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })


def create_flask_performance_middleware():
    """
    Create Flask middleware for performance optimization
    
    Usage:
        from performance.integration import create_flask_performance_middleware
        
        app = Flask(__name__)
        
        @app.before_request
        def before_request():
            return create_flask_performance_middleware()['before']()
        
        @app.after_request
        def after_request(response):
            return create_flask_performance_middleware()['after'](response)
    """
    pm = get_performance_manager()
    
    def before_request():
        from flask import request, g
        
        g.request_start_time = time.time()
        g.request_id = str(time.time())
        
        # Rate limiting
        rate_limiter = pm.get_component('api_rate_limiter')
        if rate_limiter:
            client_ip = request.remote_addr or 'unknown'
            result = rate_limiter.is_allowed(client_ip)
            
            if not result.allowed:
                from flask import jsonify
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": result.retry_after
                }), 429
        
        return None
    
    def after_request(response):
        from flask import request, g
        
        # Record metrics
        elapsed = time.time() - getattr(g, 'request_start_time', time.time())
        registry = pm.get_component('metrics_registry')
        
        if registry:
            path = request.path
            registry.record(f'api.request_time', elapsed * 1000)
            registry.record('api.total_requests', 1)
            
            if response.status_code >= 400:
                registry.record('api.errors', 1)
        
        return response
    
    return {'before': before_request, 'after': after_request}


# =============================================================================
# Agent Integration
# =============================================================================

class AgentPerformanceTracker:
    """
    Track performance of agent operations
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.pm = get_performance_manager()
        self._operation_times: Dict[str, List[float]] = {}
    
    @contextmanager
    def track_operation(self, operation_name: str):
        """Track duration of an agent operation"""
        start = time.time()
        
        try:
            yield
        finally:
            elapsed = time.time() - start
            
            # Record locally
            if operation_name not in self._operation_times:
                self._operation_times[operation_name] = []
            self._operation_times[operation_name].append(elapsed)
            
            # Record to metrics registry
            registry = self.pm.get_component('metrics_registry')
            if registry:
                registry.record(f'agent.{self.agent_name}.{operation_name}', elapsed * 1000)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        stats = {}
        
        for op_name, times in self._operation_times.items():
            if times:
                stats[op_name] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times) * 1000,
                    'min_ms': min(times) * 1000,
                    'max_ms': max(times) * 1000,
                    'total_ms': sum(times) * 1000
                }
        
        return stats
    
    def cache_result(self, key: str, value: Any, ttl: int = 3600):
        """Cache an agent result"""
        cache = self.pm.cache
        full_key = f"agent:{self.agent_name}:{key}"
        cache.set(full_key, value, ttl=ttl)
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """Get a cached agent result"""
        cache = self.pm.cache
        full_key = f"agent:{self.agent_name}:{key}"
        return cache.get(full_key)


# =============================================================================
# Embedding/Vector Search Integration
# =============================================================================

class EmbeddingPerformanceOptimizer:
    """
    Optimize embedding generation and vector search operations
    """
    
    def __init__(self):
        self.pm = get_performance_manager()
    
    def get_or_compute_embedding(self, text: str, compute_func: Callable) -> List[float]:
        """
        Get embedding from cache or compute and cache it
        
        Args:
            text: Text to embed
            compute_func: Function to compute embedding
            
        Returns:
            Embedding vector
        """
        cache = self.pm.embedding_cache
        
        # Check cache
        cached = cache.get(text)
        if cached is not None:
            return cached
        
        # Compute embedding
        embedding = compute_func(text)
        
        # Cache result
        cache.set(text, embedding)
        
        return embedding
    
    def batch_embed(self, texts: List[str], compute_func: Callable) -> List[List[float]]:
        """
        Batch compute embeddings with caching
        
        Args:
            texts: List of texts to embed
            compute_func: Function to compute embeddings (accepts list)
            
        Returns:
            List of embedding vectors
        """
        cache = self.pm.embedding_cache
        results = [None] * len(texts)
        to_compute = []
        to_compute_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            cached = cache.get(text)
            if cached is not None:
                results[i] = cached
            else:
                to_compute.append(text)
                to_compute_indices.append(i)
        
        # Compute missing embeddings in batch
        if to_compute:
            computed = compute_func(to_compute)
            
            for idx, (text, embedding) in enumerate(zip(to_compute, computed)):
                original_idx = to_compute_indices[idx]
                results[original_idx] = embedding
                cache.set(text, embedding)
        
        return results
    
    def parallel_similarity_search(self, query_embedding: List[float],
                                    embeddings: List[List[float]],
                                    top_k: int = 10) -> List[int]:
        """
        Perform parallel similarity search
        
        Args:
            query_embedding: Query vector
            embeddings: List of vectors to search
            top_k: Number of top results
            
        Returns:
            Indices of top_k most similar embeddings
        """
        matcher = self.pm.get_component('parallel_matcher')
        
        def similarity_func(emb):
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, emb))
            norm_q = sum(a * a for a in query_embedding) ** 0.5
            norm_e = sum(a * a for a in emb) ** 0.5
            return dot_product / (norm_q * norm_e) if norm_q and norm_e else 0
        
        # Compute similarities in parallel
        similarities = matcher.map(similarity_func, embeddings)
        
        # Get top_k indices
        indexed_scores = list(enumerate(similarities))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [idx for idx, _ in indexed_scores[:top_k]]


# =============================================================================
# Application Setup Functions
# =============================================================================

def init_performance(start_monitoring: bool = True):
    """
    Initialize performance system for the application
    
    Args:
        start_monitoring: Whether to start monitoring threads
        
    Returns:
        PerformanceManager instance
    """
    pm = get_performance_manager()
    
    if start_monitoring:
        pm.start()
    
    logger.info("Performance system initialized")
    return pm


def shutdown_performance():
    """Shutdown performance system gracefully"""
    global _performance_manager
    
    if _performance_manager:
        _performance_manager.stop()
        logger.info("Performance system shutdown complete")


def get_performance_status() -> Dict[str, Any]:
    """Get current performance status"""
    pm = get_performance_manager()
    return pm.get_status()


def get_optimization_recommendations() -> List[Dict[str, Any]]:
    """Get performance optimization recommendations"""
    pm = get_performance_manager()
    return pm.get_recommendations()


# =============================================================================
# Flask App Integration Helper
# =============================================================================

def integrate_flask_app(app):
    """
    Integrate performance optimizations with a Flask app
    
    Usage:
        from flask import Flask
        from performance.integration import integrate_flask_app
        
        app = Flask(__name__)
        integrate_flask_app(app)
    """
    pm = init_performance()
    middleware = create_flask_performance_middleware()
    
    @app.before_request
    def perf_before_request():
        return middleware['before']()
    
    @app.after_request
    def perf_after_request(response):
        return middleware['after'](response)
    
    @app.teardown_appcontext
    def perf_teardown(exception=None):
        pass  # Cleanup if needed
    
    # Add performance status endpoint
    @app.route('/api/performance/status')
    def perf_status():
        from flask import jsonify
        return jsonify(get_performance_status())
    
    @app.route('/api/performance/recommendations')
    def perf_recommendations():
        from flask import jsonify
        return jsonify(get_optimization_recommendations())
    
    logger.info(f"Flask app '{app.name}' integrated with performance system")
    return pm


def integrate_fastapi_app(app):
    """
    Integrate performance optimizations with a FastAPI app
    
    Usage:
        from fastapi import FastAPI
        from performance.integration import integrate_fastapi_app
        
        app = FastAPI()
        integrate_fastapi_app(app)
    """
    pm = init_performance()
    
    # Add middleware
    app.add_middleware(FastAPIPerformanceMiddleware)
    
    # Add performance endpoints
    @app.get('/api/performance/status')
    async def perf_status():
        return get_performance_status()
    
    @app.get('/api/performance/recommendations')
    async def perf_recommendations():
        return get_optimization_recommendations()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        shutdown_performance()
    
    logger.info("FastAPI app integrated with performance system")
    return pm


# Export all
__all__ = [
    # Manager
    'PerformanceManager',
    'get_performance_manager',
    
    # Decorators
    'cached',
    'rate_limited',
    'profiled',
    'with_timeout',
    'batch_execute',
    
    # Integration Classes
    'DatabasePerformanceIntegration',
    'FastAPIPerformanceMiddleware',
    'AgentPerformanceTracker',
    'EmbeddingPerformanceOptimizer',
    
    # Setup Functions
    'init_performance',
    'shutdown_performance',
    'get_performance_status',
    'get_optimization_recommendations',
    'integrate_flask_app',
    'integrate_fastapi_app',
    'create_flask_performance_middleware',
]
