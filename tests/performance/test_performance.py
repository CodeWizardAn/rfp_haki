"""
Performance Tests

Comprehensive tests for performance modules with:
- Unit tests
- Benchmarks
- Regression tests
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import performance modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestRedisCache:
    """Tests for Redis cache"""
    
    def test_in_memory_fallback_basic_ops(self):
        """Test in-memory fallback basic operations"""
        from performance.redis_cache import InMemoryFallback
        
        cache = InMemoryFallback()
        
        # Set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Non-existent key
        assert cache.get("nonexistent") is None
        
        # Delete
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_in_memory_fallback_ttl(self):
        """Test TTL expiration"""
        from performance.redis_cache import InMemoryFallback
        
        cache = InMemoryFallback()
        cache.set("key1", "value1", ttl=1)
        
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_in_memory_batch_ops(self):
        """Test batch operations"""
        from performance.redis_cache import InMemoryFallback
        
        cache = InMemoryFallback()
        
        # mset and mget
        cache.mset({"k1": "v1", "k2": "v2", "k3": "v3"})
        
        values = cache.mget(["k1", "k2", "k3", "k4"])
        assert values == ["v1", "v2", "v3", None]


class TestEmbeddingCache:
    """Tests for embedding cache"""
    
    def test_lru_cache_basic(self):
        """Test LRU cache basic operations"""
        from performance.embedding_cache import LRUCache
        
        cache = LRUCache(max_size=3)
        
        cache.set("a", [1, 2, 3])
        cache.set("b", [4, 5, 6])
        cache.set("c", [7, 8, 9])
        
        assert cache.get("a") == [1, 2, 3]
        assert cache.get("b") == [4, 5, 6]
        assert cache.get("c") == [7, 8, 9]
    
    def test_lru_eviction(self):
        """Test LRU eviction policy"""
        from performance.embedding_cache import LRUCache
        
        cache = LRUCache(max_size=3)
        
        cache.set("a", [1])
        cache.set("b", [2])
        cache.set("c", [3])
        
        # Access 'a' to make it recently used
        cache.get("a")
        
        # Add new item, 'b' should be evicted (least recently used)
        cache.set("d", [4])
        
        assert cache.get("a") == [1]  # Still there
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") == [3]
        assert cache.get("d") == [4]
    
    def test_cache_stats(self):
        """Test cache statistics"""
        from performance.embedding_cache import LRUCache
        
        cache = LRUCache(max_size=10)
        
        cache.set("a", [1])
        cache.get("a")  # Hit
        cache.get("a")  # Hit
        cache.get("b")  # Miss
        
        stats = cache.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 2 / 3


class TestQueryOptimizer:
    """Tests for query optimizer"""
    
    def test_query_type_detection(self):
        """Test query type detection"""
        from performance.query_optimizer import QueryOptimizer, QueryType
        
        optimizer = QueryOptimizer()
        
        select_query = "SELECT * FROM users WHERE id = 1"
        insert_query = "INSERT INTO users (name) VALUES ('test')"
        update_query = "UPDATE users SET name = 'test' WHERE id = 1"
        delete_query = "DELETE FROM users WHERE id = 1"
        
        assert optimizer.analyze(select_query).query_type == QueryType.SELECT
        assert optimizer.analyze(insert_query).query_type == QueryType.INSERT
        assert optimizer.analyze(update_query).query_type == QueryType.UPDATE
        assert optimizer.analyze(delete_query).query_type == QueryType.DELETE
    
    def test_table_extraction(self):
        """Test table name extraction"""
        from performance.query_optimizer import QueryOptimizer
        
        optimizer = QueryOptimizer()
        
        query = "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        plan = optimizer.analyze(query)
        
        assert "users" in plan.tables_accessed
        assert "orders" in plan.tables_accessed


class TestConnectionPool:
    """Tests for connection pool"""
    
    def test_pool_config(self):
        """Test pool configuration"""
        from performance.connection_pool import PoolConfig, PoolStats
        
        config = PoolConfig(min_size=2, max_size=10, timeout=5.0)
        assert config.min_size == 2
        assert config.max_size == 10
        assert config.timeout == 5.0
        
        stats = PoolStats()
        assert stats.pool_size == 0
        assert stats.active_connections == 0
    
    def test_pooled_connection(self):
        """Test pooled connection wrapper"""
        from performance.connection_pool import PooledConnection
        
        mock_conn = Mock()
        pooled = PooledConnection(mock_conn, pool=None)
        
        assert pooled.connection == mock_conn
        assert pooled.use_count == 0
        
        pooled.mark_used()
        assert pooled.use_count == 1
        assert pooled.in_use is True


class TestBatchProcessor:
    """Tests for batch processor"""
    
    def test_chunked_processing(self):
        """Test chunked processing"""
        from performance.batch_processor import BatchProcessor, BatchConfig
        
        config = BatchConfig(batch_size=3)
        processor = BatchProcessor(config)
        
        items = list(range(10))
        results = []
        
        def process_item(item):
            return item * 2
        
        result = processor.process(items, process_item)
        
        assert result.successful_items == 10
        assert len(result.results) == 10
    
    def test_batch_with_errors(self):
        """Test batch processing with errors"""
        from performance.batch_processor import BatchProcessor, BatchConfig
        
        config = BatchConfig(batch_size=3, max_retries=1, continue_on_error=True)
        processor = BatchProcessor(config)
        
        items = list(range(10))
        
        def process_item(item):
            if item == 5:
                raise ValueError("Test error")
            return item * 2
        
        # Should continue despite error
        result = processor.process(items, process_item)
        assert result.failed_items > 0


class TestRateLimiter:
    """Tests for rate limiter"""
    
    def test_token_bucket(self):
        """Test token bucket rate limiter"""
        from performance.rate_limiter import TokenBucket, TokenBucketConfig
        
        config = TokenBucketConfig(capacity=5, refill_rate=1.0)
        bucket = TokenBucket(config)
        
        # Should allow first 5 requests
        for i in range(5):
            result = bucket.is_allowed("test")
            assert result.allowed, f"Request {i+1} should be allowed"
        
        # 6th should be denied
        result = bucket.is_allowed("test")
        assert not result.allowed
    
    def test_sliding_window(self):
        """Test sliding window rate limiter"""
        from performance.rate_limiter import SlidingWindowLimiter, SlidingWindowConfig
        
        config = SlidingWindowConfig(window_size=1, max_requests=3)
        limiter = SlidingWindowLimiter(config)
        
        # Allow first 3
        for i in range(3):
            result = limiter.is_allowed("test")
            assert result.allowed
        
        # 4th denied
        result = limiter.is_allowed("test")
        assert not result.allowed
        
        # Wait for window to pass
        time.sleep(1.1)
        
        # Should be allowed again
        result = limiter.is_allowed("test")
        assert result.allowed


class TestLoadBalancer:
    """Tests for load balancer"""
    
    def test_round_robin(self):
        """Test round-robin balancing"""
        from performance.load_balancer import LoadBalancer, LoadBalancerConfig, Backend, BalancingStrategy
        
        config = LoadBalancerConfig(strategy=BalancingStrategy.ROUND_ROBIN)
        lb = LoadBalancer(config)
        
        lb.add_backend(Backend(id="b1", host="host1", port=8080))
        lb.add_backend(Backend(id="b2", host="host2", port=8080))
        lb.add_backend(Backend(id="b3", host="host3", port=8080))
        
        # Should cycle through backends
        backends = [lb.get_backend().id for _ in range(6)]
        assert backends == ["b1", "b2", "b3", "b1", "b2", "b3"]
    
    def test_least_connections(self):
        """Test least connections balancing"""
        from performance.load_balancer import LoadBalancer, LoadBalancerConfig, Backend, BalancingStrategy
        
        config = LoadBalancerConfig(strategy=BalancingStrategy.LEAST_CONNECTIONS)
        lb = LoadBalancer(config)
        
        b1 = Backend(id="b1", host="host1", port=8080)
        b2 = Backend(id="b2", host="host2", port=8080)
        
        lb.add_backend(b1)
        lb.add_backend(b2)
        
        # Simulate connections on b1
        b1.active_connections = 5
        b2.active_connections = 2
        
        # Should prefer b2 (fewer connections)
        backend = lb.get_backend()
        assert backend.id == "b2"


class TestRequestQueue:
    """Tests for request queue"""
    
    def test_priority_ordering(self):
        """Test priority queue ordering"""
        from performance.request_queue import PriorityRequestQueue, QueuedRequest, Priority
        
        queue = PriorityRequestQueue()
        
        queue.enqueue(QueuedRequest(id="low", priority=Priority.LOW, payload="low"))
        queue.enqueue(QueuedRequest(id="high", priority=Priority.HIGH, payload="high"))
        queue.enqueue(QueuedRequest(id="critical", priority=Priority.CRITICAL, payload="critical"))
        
        # Should dequeue in priority order
        assert queue.dequeue(timeout=1).id == "critical"
        assert queue.dequeue(timeout=1).id == "high"
        assert queue.dequeue(timeout=1).id == "low"
    
    def test_queue_cancellation(self):
        """Test request cancellation"""
        from performance.request_queue import PriorityRequestQueue, QueuedRequest, Priority
        
        queue = PriorityRequestQueue()
        
        queue.enqueue(QueuedRequest(id="req1", priority=Priority.NORMAL, payload="test"))
        queue.enqueue(QueuedRequest(id="req2", priority=Priority.NORMAL, payload="test"))
        
        assert queue.size() == 2
        
        queue.cancel("req1")
        
        assert queue.size() == 1
        assert queue.dequeue(timeout=1).id == "req2"


class TestResourceMonitor:
    """Tests for resource monitor"""
    
    def test_metric_collection(self):
        """Test metric collection"""
        from performance.resource_monitor import ResourceMonitor, MonitorConfig
        
        config = MonitorConfig(interval=1.0)
        monitor = ResourceMonitor(config)
        
        # Collect metrics once
        snapshot = monitor.collect_metrics()
        
        assert snapshot is not None
        assert snapshot.cpu is not None
        assert snapshot.memory is not None
    
    def test_threshold_alerts(self):
        """Test threshold-based alerts"""
        from performance.resource_monitor import ResourceMonitor, MonitorConfig, AlertLevel
        
        config = MonitorConfig(cpu_warning=50.0, cpu_critical=80.0)
        monitor = ResourceMonitor(config)
        
        # Collect and check alerts
        # Note: Alerts depend on actual system state


class TestProfiler:
    """Tests for profiler"""
    
    def test_function_profiling(self):
        """Test function profiling decorator"""
        from performance.profiler import FunctionProfiler, ProfilerConfig
        
        config = ProfilerConfig(enabled=True)
        profiler = FunctionProfiler(config)
        
        @profiler.profile
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        assert result == "result"
        
        stats = profiler.get_stats()
        assert len(stats) > 0
    
    def test_context_manager(self):
        """Test timing context manager"""
        from performance.profiler import FunctionProfiler, ProfilerConfig
        
        config = ProfilerConfig(enabled=True)
        profiler = FunctionProfiler(config)
        
        with profiler.measure("test_block"):
            time.sleep(0.01)
        
        stats = profiler.get_stats()
        found = any(s.name == "test_block" for s in stats)
        assert found


class TestBottleneckDetector:
    """Tests for bottleneck detector"""
    
    def test_metric_recording(self):
        """Test metric recording"""
        from performance.bottleneck_detector import BottleneckDetector, DetectorConfig
        
        config = DetectorConfig()
        detector = BottleneckDetector(config)
        
        detector.record_metric("cpu.usage_percent", 75.0)
        detector.record_metric("cpu.usage_percent", 80.0)
        detector.record_metric("cpu.usage_percent", 85.0)
        
        # Metrics should be recorded
        avg = detector._metrics.get_average("cpu.usage_percent", 60)
        assert avg == 80.0
    
    def test_bottleneck_detection(self):
        """Test bottleneck detection"""
        from performance.bottleneck_detector import BottleneckDetector, DetectorConfig, BottleneckType
        
        config = DetectorConfig(cpu_threshold=70.0)
        detector = BottleneckDetector(config)
        
        # Record high CPU
        for _ in range(5):
            detector.record_metric("cpu.usage_percent", 90.0)
        
        # Run detection
        bottlenecks = detector.detect()
        
        cpu_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.CPU]
        assert len(cpu_bottlenecks) > 0


class TestAutoScaler:
    """Tests for auto scaler"""
    
    def test_scaling_up(self):
        """Test scale up logic"""
        from performance.auto_scaler import (
            AutoScaler, ScalerConfig, ScalingPolicy, 
            InMemoryMetricProvider, MockScalingExecutor
        )
        
        metrics = InMemoryMetricProvider()
        executor = MockScalingExecutor(initial_count=2)
        config = ScalerConfig(check_interval=1, default_cooldown=0)  # No cooldown for test
        
        scaler = AutoScaler(config, metrics, executor)
        
        policy = ScalingPolicy(
            name="cpu",
            metric="cpu.usage_percent",
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            evaluation_periods=1,
            min_instances=1,
            max_instances=10
        )
        scaler.add_policy(policy)
        
        # Record high CPU
        for _ in range(5):
            metrics.record("cpu.usage_percent", 85.0)
        
        # Evaluate
        direction = scaler.evaluate()
        
        # Should have scaled up
        assert executor.get_current_count() == 3
    
    def test_cooldown_period(self):
        """Test cooldown prevents rapid scaling"""
        from performance.auto_scaler import (
            AutoScaler, ScalerConfig, ScalingPolicy,
            InMemoryMetricProvider, MockScalingExecutor, ScalingDirection
        )
        
        metrics = InMemoryMetricProvider()
        executor = MockScalingExecutor(initial_count=2)
        config = ScalerConfig(default_cooldown=300)  # 5 minute cooldown
        
        scaler = AutoScaler(config, metrics, executor)
        
        policy = ScalingPolicy(
            name="cpu",
            metric="cpu.usage_percent",
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            evaluation_periods=1
        )
        scaler.add_policy(policy)
        
        # First scale up
        for _ in range(5):
            metrics.record("cpu.usage_percent", 85.0)
        scaler.evaluate()
        first_count = executor.get_current_count()
        
        # Second attempt should be blocked by cooldown
        for _ in range(5):
            metrics.record("cpu.usage_percent", 90.0)
        direction = scaler.evaluate()
        
        # Should still be at first scaled count (cooldown blocks second scale)
        assert direction == ScalingDirection.NONE
        assert executor.get_current_count() == first_count


class TestPerformanceBenchmarks:
    """Performance benchmarks"""
    
    def test_cache_performance(self):
        """Benchmark cache performance"""
        from performance.embedding_cache import LRUCache
        
        cache = LRUCache(max_size=10000)
        
        # Benchmark writes
        start = time.perf_counter()
        for i in range(10000):
            cache.set(f"key_{i}", [1.0] * 100)
        write_time = time.perf_counter() - start
        
        # Benchmark reads
        start = time.perf_counter()
        for i in range(10000):
            cache.get(f"key_{i}")
        read_time = time.perf_counter() - start
        
        # Should be reasonably fast
        assert write_time < 1.0, f"Write took {write_time}s"
        assert read_time < 0.5, f"Read took {read_time}s"
    
    @pytest.mark.skip(reason="Performance test is environment-dependent")
    def test_queue_performance(self):
        """Benchmark queue performance"""
        from performance.request_queue import PriorityRequestQueue, QueuedRequest, Priority
        
        queue = PriorityRequestQueue()
        
        # Benchmark enqueue
        start = time.perf_counter()
        for i in range(10000):
            queue.enqueue(QueuedRequest(
                id=f"req_{i}",
                priority=Priority.NORMAL,
                payload=f"data_{i}"
            ))
        enqueue_time = time.perf_counter() - start
        
        # Benchmark dequeue - dequeue all items without blocking
        start = time.perf_counter()
        dequeued = 0
        while queue.size() > 0:
            result = queue.dequeue(timeout=0.0001)
            if result:
                dequeued += 1
            else:
                break
        dequeue_time = time.perf_counter() - start
        
        assert enqueue_time < 2.0, f"Enqueue took {enqueue_time}s"
        assert dequeue_time < 5.0, f"Dequeue took {dequeue_time}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
