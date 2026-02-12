"""
Metrics Collection System
Core infrastructure for collecting, storing, and managing metrics

Features:
- Decorators for automatic metric collection
- Context managers for timing operations
- Thread-safe metric aggregation
- Async support
- Metric batching for efficient storage
"""

import time
import functools
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricRecord:
    """Individual metric record"""
    name: str
    value: float
    metric_type: str  # counter, gauge, histogram
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimingContext:
    """Context for timing operations"""
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000
    
    def stop(self):
        self.end_time = time.time()
        return self.duration_ms


class MetricsCollector:
    """
    Central metrics collection system
    Thread-safe collection and aggregation of metrics
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
        self._metrics_buffer: List[MetricRecord] = []
        self._buffer_lock = threading.Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Configuration
        self._buffer_size = 1000
        self._flush_interval = 60  # seconds
        self._enabled = True
        
        # Callbacks
        self._flush_callbacks: List[Callable] = []
        
        # Session tracking
        self._session_id = str(uuid.uuid4())
        self._start_time = datetime.utcnow()
        
        logger.info(f"MetricsCollector initialized with session {self._session_id}")
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)"""
        with cls._lock:
            cls._instance = None
    
    def enable(self):
        """Enable metrics collection"""
        self._enabled = True
    
    def disable(self):
        """Disable metrics collection"""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if metrics collection is enabled"""
        return self._enabled
    
    # ==================== Counter Operations ====================
    
    def increment(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        if not self._enabled:
            return
            
        key = self._make_key(name, tags)
        with self._buffer_lock:
            self._counters[key] += value
        
        self._record_metric(name, value, 'counter', tags)
    
    def decrement(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Decrement a counter metric"""
        self.increment(name, -value, tags)
    
    # ==================== Gauge Operations ====================
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric to a specific value"""
        if not self._enabled:
            return
            
        key = self._make_key(name, tags)
        with self._buffer_lock:
            self._gauges[key] = value
        
        self._record_metric(name, value, 'gauge', tags)
    
    # ==================== Histogram Operations ====================
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a value in a histogram (for distribution analysis)"""
        if not self._enabled:
            return
            
        key = self._make_key(name, tags)
        with self._buffer_lock:
            self._histograms[key].append(value)
            # Keep only last 10000 values per histogram
            if len(self._histograms[key]) > 10000:
                self._histograms[key] = self._histograms[key][-10000:]
        
        self._record_metric(name, value, 'histogram', tags)
    
    def timing(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timing metric (convenience wrapper for histogram)"""
        self.histogram(f"{name}.timing", duration_ms, tags)
    
    # ==================== Context Managers ====================
    
    @contextmanager
    def timer(self, name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations"""
        ctx = TimingContext(operation=name)
        try:
            yield ctx
        finally:
            duration = ctx.stop()
            self.timing(name, duration, tags)
    
    @contextmanager
    def track_operation(self, operation: str, tags: Dict[str, str] = None):
        """
        Context manager for tracking an operation with start, success, and failure counts
        """
        tags = tags or {}
        self.increment(f"{operation}.started", tags=tags)
        
        try:
            yield
            self.increment(f"{operation}.success", tags=tags)
        except Exception as e:
            self.increment(f"{operation}.failed", tags={**tags, 'error_type': type(e).__name__})
            raise
    
    # ==================== Aggregation ====================
    
    def get_counter(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get current counter value"""
        key = self._make_key(name, tags)
        return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> Optional[float]:
        """Get current gauge value"""
        key = self._make_key(name, tags)
        return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            'count': n,
            'sum': sum(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / n,
            'p50': sorted_values[int(n * 0.5)],
            'p90': sorted_values[int(n * 0.9)],
            'p95': sorted_values[int(n * 0.95)],
            'p99': sorted_values[min(int(n * 0.99), n - 1)]
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values"""
        return {
            'counters': dict(self._counters),
            'gauges': dict(self._gauges),
            'histograms': {k: self.get_histogram_stats(k.split(':')[0]) 
                          for k in self._histograms.keys()},
            'session_id': self._session_id,
            'start_time': self._start_time.isoformat(),
            'uptime_seconds': (datetime.utcnow() - self._start_time).total_seconds()
        }
    
    # ==================== Buffer Management ====================
    
    def _record_metric(self, name: str, value: float, metric_type: str, 
                       tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Record a metric to the buffer"""
        record = MetricRecord(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            metadata=metadata or {}
        )
        
        with self._buffer_lock:
            self._metrics_buffer.append(record)
            
            if len(self._metrics_buffer) >= self._buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush the metrics buffer (called automatically or manually)"""
        if not self._metrics_buffer:
            return []
        
        records = self._metrics_buffer.copy()
        self._metrics_buffer.clear()
        
        # Call registered flush callbacks
        for callback in self._flush_callbacks:
            try:
                callback(records)
            except Exception as e:
                logger.error(f"Error in flush callback: {e}")
        
        return records
    
    def flush(self) -> List[MetricRecord]:
        """Manually flush the metrics buffer"""
        with self._buffer_lock:
            return self._flush_buffer()
    
    def register_flush_callback(self, callback: Callable[[List[MetricRecord]], None]):
        """Register a callback to be called when buffer is flushed"""
        self._flush_callbacks.append(callback)
    
    # ==================== Helpers ====================
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a unique key for a metric with tags"""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}:{tag_str}"
    
    def clear(self):
        """Clear all metrics (useful for testing)"""
        with self._buffer_lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._metrics_buffer.clear()


# ==================== Decorators ====================

def track_metric(name: str, metric_type: str = 'counter', 
                 tags: Dict[str, str] = None, increment_by: float = 1.0):
    """
    Decorator to track function calls
    
    Usage:
        @track_metric('api.requests', tags={'endpoint': '/match'})
        def handle_request():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            collector = MetricsCollector()
            
            if metric_type == 'counter':
                collector.increment(name, increment_by, tags)
            
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = MetricsCollector()
            
            if metric_type == 'counter':
                collector.increment(name, increment_by, tags)
            
            return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def track_timing(name: str, tags: Dict[str, str] = None):
    """
    Decorator to track function execution time
    
    Usage:
        @track_timing('api.response_time', tags={'endpoint': '/match'})
        def handle_request():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            collector = MetricsCollector()
            with collector.timer(name, tags):
                return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = MetricsCollector()
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                collector.timing(name, duration_ms, tags)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def track_success_failure(name: str, tags: Dict[str, str] = None):
    """
    Decorator to track success and failure of function calls
    
    Usage:
        @track_success_failure('rfp.processing')
        def process_rfp(rfp_id):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            collector = MetricsCollector()
            base_tags = tags or {}
            
            collector.increment(f"{name}.started", tags=base_tags)
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                collector.increment(f"{name}.success", tags=base_tags)
                return result
            except Exception as e:
                error_tags = {**base_tags, 'error_type': type(e).__name__}
                collector.increment(f"{name}.failed", tags=error_tags)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                collector.timing(name, duration_ms, base_tags)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            collector = MetricsCollector()
            base_tags = tags or {}
            
            collector.increment(f"{name}.started", tags=base_tags)
            start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                collector.increment(f"{name}.success", tags=base_tags)
                return result
            except Exception as e:
                error_tags = {**base_tags, 'error_type': type(e).__name__}
                collector.increment(f"{name}.failed", tags=error_tags)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                collector.timing(name, duration_ms, base_tags)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


# ==================== Context Manager ====================

@contextmanager
def metrics_context(operation: str, tags: Dict[str, str] = None, 
                   track_time: bool = True, track_success: bool = True):
    """
    Comprehensive context manager for tracking metrics
    
    Usage:
        with metrics_context('rfp.matching', tags={'rfp_id': '123'}):
            perform_matching()
    """
    collector = MetricsCollector()
    base_tags = tags or {}
    
    if track_success:
        collector.increment(f"{operation}.started", tags=base_tags)
    
    start = time.time()
    
    try:
        yield collector
        if track_success:
            collector.increment(f"{operation}.success", tags=base_tags)
    except Exception as e:
        if track_success:
            error_tags = {**base_tags, 'error_type': type(e).__name__}
            collector.increment(f"{operation}.failed", tags=error_tags)
        raise
    finally:
        if track_time:
            duration_ms = (time.time() - start) * 1000
            collector.timing(operation, duration_ms, base_tags)


class MetricsAggregator:
    """
    Aggregates metrics over time periods for storage
    """
    
    def __init__(self, collector: MetricsCollector = None):
        self.collector = collector or MetricsCollector()
        self._aggregation_window = timedelta(minutes=1)
    
    def aggregate_to_minute(self, records: List[MetricRecord]) -> Dict[str, Any]:
        """Aggregate metrics into minute buckets"""
        buckets = defaultdict(lambda: defaultdict(list))
        
        for record in records:
            bucket_time = record.timestamp.replace(second=0, microsecond=0)
            key = self.collector._make_key(record.name, record.tags)
            buckets[bucket_time][key].append(record.value)
        
        aggregated = {}
        for bucket_time, metrics in buckets.items():
            aggregated[bucket_time.isoformat()] = {
                key: {
                    'count': len(values),
                    'sum': sum(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values)
                }
                for key, values in metrics.items()
            }
        
        return aggregated
    
    def compute_rates(self, metric_name: str, window_seconds: int = 60) -> float:
        """Compute rate (per second) for a counter over a time window"""
        counter_value = self.collector.get_counter(metric_name)
        return counter_value / window_seconds if window_seconds > 0 else 0


class MetricsPersistence:
    """
    Handles persisting metrics to the database
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._batch_size = 100
    
    def save_rfp_metric(self, session, rfp_metric_data: Dict[str, Any]):
        """Save RFP processing metrics"""
        from .models import RFPMetric
        
        metric = RFPMetric(**rfp_metric_data)
        session.add(metric)
        session.commit()
        return metric
    
    def save_response_time(self, session, response_time_data: Dict[str, Any]):
        """Save response time metrics"""
        from .models import ResponseTimeMetric
        
        metric = ResponseTimeMetric(**response_time_data)
        session.add(metric)
        session.commit()
        return metric
    
    def batch_save_metrics(self, session, records: List[MetricRecord]):
        """Save a batch of metric records"""
        from .models import ResponseTimeMetric
        
        # Group by type and save appropriately
        timing_records = [r for r in records if 'timing' in r.name]
        
        for record in timing_records:
            metric = ResponseTimeMetric(
                endpoint=record.name.replace('.timing', ''),
                total_time_ms=int(record.value),
                is_success=True,
                recorded_at=record.timestamp
            )
            session.add(metric)
        
        session.commit()
