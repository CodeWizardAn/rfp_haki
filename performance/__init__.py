"""
Performance Optimization Package

Comprehensive performance optimization tools including:
- Caching (Redis, LRU)
- Database optimization (indexing, query optimization, connection pooling)
- Parallel processing (batch processing, async operations, parallel matching)
- Load management (load balancing, rate limiting, request queuing)
- Monitoring (resource monitoring, profiling, bottleneck detection)
- Testing (stress testing, load testing, performance tests)
- Auto-scaling and optimization recommendations
"""

# Caching
from .redis_cache import RedisCache, RedisCacheConfig, cache_result, InMemoryFallback
from .embedding_cache import EmbeddingCache, LRUCache, MultiTierCache

# Database Optimization
from .query_optimizer import QueryOptimizer, QueryPlan, QueryProfiler
from .db_indexing import IndexManager, IndexRecommendation, IndexInfo
from .connection_pool import ConnectionPoolManager, DatabasePool, RedisPool

# Parallel Processing
from .batch_processor import BatchProcessor, BatchConfig, BatchResult, Pipeline
from .async_ops import AsyncExecutor, TaskManager, async_task
from .parallel_matcher import ParallelMatcher, MatchTask, MatchResult, MatcherPool

# Load Management
from .load_balancer import LoadBalancer, Backend, BalancingStrategy, LoadBalancerConfig
from .rate_limiter import (
    TokenBucket, TokenBucketConfig,
    SlidingWindowLimiter, SlidingWindowConfig,
    FixedWindowLimiter, LeakyBucket,
    CompositeRateLimiter, PerClientRateLimiter,
    RateLimitResult, rate_limit
)
from .request_queue import (
    PriorityRequestQueue, QueuedRequest, Priority,
    RequestQueueWorker, FairScheduler, BackpressureController,
    AsyncRequestQueue, QueueConfig
)

# Monitoring
from .resource_monitor import (
    ResourceMonitor, MonitorConfig,
    CPUMetrics, MemoryMetrics, DiskMetrics, NetworkMetrics,
    SystemSnapshot, ResourceAlert, ResourceThrottler
)
from .profiler import (
    FunctionProfiler, ProfilerConfig, FunctionStats,
    CodeProfiler, LineProfiler, HotSpotDetector,
    profile, measure
)
from .bottleneck_detector import (
    BottleneckDetector, DetectorConfig,
    Bottleneck, BottleneckType, Severity,
    MetricsCollector, RootCauseAnalyzer
)

# Scaling and Optimization
from .auto_scaler import (
    AutoScaler, ScalerConfig, ScalingPolicy,
    ScalingDirection, ScalingEvent,
    PredictiveScaler, TargetTrackingScaler,
    MetricProvider, InMemoryMetricProvider, ScalingExecutor
)
from .optimizer import (
    PerformanceOptimizer, Recommendation,
    OptimizationCategory, Effort, AnalysisContext,
    analyze_and_recommend
)

# Testing
from .stress_tester import (
    StressTester, StressTestConfig, StressTestResult,
    ResourceExhaustionTester, RecoveryTester, StabilityTester
)
from .load_tester import (
    LoadTester, LoadTestConfig, LoadTestResult,
    UserScenario, VirtualUser, ScenarioBuilder,
    LoadPattern, LoadTestRunner
)

# Dashboard
from .dashboard import (
    PerformanceDashboard, DashboardConfig, DashboardPanel,
    MetricsRegistry, MetricType, MetricDefinition,
    DashboardBuilder, create_default_dashboard,
    RealTimeStream, AlertManager
)

# Integration (lazy import to avoid circular dependencies)
def get_integration_module():
    """Get the integration module (lazy loaded)"""
    from . import integration
    return integration

__all__ = [
    # Caching
    'RedisCache', 'RedisCacheConfig', 'cache_result', 'InMemoryFallback',
    'EmbeddingCache', 'LRUCache', 'MultiTierCache',
    
    # Database
    'QueryOptimizer', 'QueryPlan', 'QueryProfiler',
    'IndexManager', 'IndexRecommendation', 'IndexInfo',
    'ConnectionPoolManager', 'DatabasePool', 'RedisPool',
    
    # Parallel
    'BatchProcessor', 'BatchConfig', 'BatchResult', 'Pipeline',
    'AsyncExecutor', 'TaskManager', 'async_task',
    'ParallelMatcher', 'MatchTask', 'MatchResult', 'MatcherPool',
    
    # Load Management
    'LoadBalancer', 'Backend', 'BalancingStrategy', 'LoadBalancerConfig',
    'TokenBucket', 'TokenBucketConfig',
    'SlidingWindowLimiter', 'SlidingWindowConfig',
    'FixedWindowLimiter', 'LeakyBucket',
    'CompositeRateLimiter', 'PerClientRateLimiter',
    'RateLimitResult', 'rate_limit',
    'PriorityRequestQueue', 'QueuedRequest', 'Priority',
    'RequestQueueWorker', 'FairScheduler', 'BackpressureController',
    'AsyncRequestQueue', 'QueueConfig',
    
    # Monitoring
    'ResourceMonitor', 'MonitorConfig',
    'CPUMetrics', 'MemoryMetrics', 'DiskMetrics', 'NetworkMetrics',
    'SystemSnapshot', 'ResourceAlert', 'ResourceThrottler',
    'FunctionProfiler', 'ProfilerConfig', 'FunctionStats',
    'CodeProfiler', 'LineProfiler', 'HotSpotDetector',
    'profile', 'measure',
    'BottleneckDetector', 'DetectorConfig',
    'Bottleneck', 'BottleneckType', 'Severity',
    'MetricsCollector', 'RootCauseAnalyzer',
    
    # Scaling
    'AutoScaler', 'ScalerConfig', 'ScalingPolicy',
    'ScalingDirection', 'ScalingEvent',
    'PredictiveScaler', 'TargetTrackingScaler',
    'MetricProvider', 'InMemoryMetricProvider', 'ScalingExecutor',
    'PerformanceOptimizer', 'Recommendation',
    'OptimizationCategory', 'Effort', 'AnalysisContext',
    'analyze_and_recommend',
    
    # Testing
    'StressTester', 'StressTestConfig', 'StressTestResult',
    'ResourceExhaustionTester', 'RecoveryTester', 'StabilityTester',
    'LoadTester', 'LoadTestConfig', 'LoadTestResult',
    'UserScenario', 'VirtualUser', 'ScenarioBuilder',
    'LoadPattern', 'LoadTestRunner',
    
    # Dashboard
    'PerformanceDashboard', 'DashboardConfig', 'DashboardPanel',
    'MetricsRegistry', 'MetricType', 'MetricDefinition',
    'DashboardBuilder', 'create_default_dashboard',
    'RealTimeStream', 'AlertManager',
]
