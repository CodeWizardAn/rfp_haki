"""
Bottleneck Detector

Automated performance bottleneck detection with:
- Pattern recognition
- Threshold-based alerts
- Root cause analysis
- Trend detection
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class BottleneckType(Enum):
    """Types of performance bottlenecks"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_SERVICE = "external_service"
    LOCK_CONTENTION = "lock_contention"
    THREAD_POOL = "thread_pool"
    QUEUE_SATURATION = "queue_saturation"


class Severity(Enum):
    """Bottleneck severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Bottleneck:
    """Detected bottleneck"""
    id: str
    bottleneck_type: BottleneckType
    severity: Severity
    description: str
    detected_at: datetime
    metrics: Dict[str, Any]
    recommendations: List[str]
    affected_components: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MetricSample:
    """A metric sample"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class DetectorConfig:
    """Bottleneck detector configuration"""
    check_interval: float = 10.0  # Seconds
    history_window: int = 300  # Seconds of history
    
    # Thresholds
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    disk_io_threshold: float = 90.0  # % utilization
    response_time_threshold_ms: float = 500.0
    error_rate_threshold: float = 0.05  # 5%
    queue_depth_threshold: int = 1000
    lock_wait_threshold_ms: float = 100.0
    
    # Trend detection
    trend_window: int = 60  # Seconds for trend detection
    degradation_threshold: float = 0.2  # 20% degradation triggers alert


class MetricsCollector:
    """
    Collects metrics from various sources
    """
    
    def __init__(self, history_size: int = 1000):
        self._metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self._history_size = history_size
    
    def record(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric"""
        sample = MetricSample(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self._history_size)
            self._metrics[name].append(sample)
    
    def get_latest(self, name: str) -> Optional[MetricSample]:
        """Get latest value for a metric"""
        with self._lock:
            if name in self._metrics and self._metrics[name]:
                return self._metrics[name][-1]
            return None
    
    def get_history(self, name: str, 
                   seconds: int = 60) -> List[MetricSample]:
        """Get metric history"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        
        with self._lock:
            if name not in self._metrics:
                return []
            return [s for s in self._metrics[name] if s.timestamp > cutoff]
    
    def get_average(self, name: str, seconds: int = 60) -> Optional[float]:
        """Get average value over time period"""
        history = self.get_history(name, seconds)
        if not history:
            return None
        return sum(s.value for s in history) / len(history)
    
    def get_percentile(self, name: str, percentile: float, 
                      seconds: int = 60) -> Optional[float]:
        """Get percentile value"""
        history = self.get_history(name, seconds)
        if not history:
            return None
        
        values = sorted(s.value for s in history)
        idx = int(len(values) * percentile / 100)
        return values[min(idx, len(values) - 1)]
    
    def get_trend(self, name: str, seconds: int = 60) -> Optional[float]:
        """
        Get trend (positive = increasing, negative = decreasing)
        Returns rate of change per second
        """
        history = self.get_history(name, seconds)
        if len(history) < 2:
            return None
        
        # Simple linear regression
        n = len(history)
        first_half = history[:n//2]
        second_half = history[n//2:]
        
        first_avg = sum(s.value for s in first_half) / len(first_half)
        second_avg = sum(s.value for s in second_half) / len(second_half)
        
        time_diff = (second_half[-1].timestamp - first_half[0].timestamp).total_seconds()
        if time_diff > 0:
            return (second_avg - first_avg) / time_diff
        return 0.0


class BottleneckDetector:
    """
    Detects performance bottlenecks
    """
    
    def __init__(self, config: DetectorConfig = None):
        self.config = config or DetectorConfig()
        
        self._metrics = MetricsCollector()
        self._bottlenecks: List[Bottleneck] = []
        self._detection_rules: List[Callable] = []
        self._lock = threading.Lock()
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Register default detection rules
        self._register_default_rules()
        
        logger.info("BottleneckDetector initialized")
    
    def _register_default_rules(self):
        """Register default detection rules"""
        self.add_rule(self._detect_cpu_bottleneck)
        self.add_rule(self._detect_memory_bottleneck)
        self.add_rule(self._detect_slow_responses)
        self.add_rule(self._detect_high_error_rate)
        self.add_rule(self._detect_queue_saturation)
        self.add_rule(self._detect_degradation_trend)
    
    def add_rule(self, rule: Callable[['BottleneckDetector'], Optional[Bottleneck]]):
        """Add a detection rule"""
        self._detection_rules.append(rule)
    
    def record_metric(self, name: str, value: float, 
                     tags: Dict[str, str] = None):
        """Record a metric for analysis"""
        self._metrics.record(name, value, tags)
    
    def start(self):
        """Start background detection"""
        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()
        logger.info("BottleneckDetector started")
    
    def stop(self):
        """Stop detection"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("BottleneckDetector stopped")
    
    def _detection_loop(self):
        """Background detection loop"""
        while self._running:
            try:
                self.detect()
            except Exception as e:
                logger.error(f"Detection error: {e}")
            
            time.sleep(self.config.check_interval)
    
    def detect(self) -> List[Bottleneck]:
        """Run all detection rules"""
        detected = []
        
        for rule in self._detection_rules:
            try:
                bottleneck = rule(self)
                if bottleneck:
                    detected.append(bottleneck)
                    self._add_bottleneck(bottleneck)
            except Exception as e:
                logger.error(f"Rule {rule.__name__} failed: {e}")
        
        return detected
    
    def _add_bottleneck(self, bottleneck: Bottleneck):
        """Add detected bottleneck"""
        with self._lock:
            # Check for duplicate/existing bottleneck
            for existing in self._bottlenecks:
                if (existing.bottleneck_type == bottleneck.bottleneck_type and
                    not existing.resolved):
                    # Update existing instead
                    existing.severity = bottleneck.severity
                    existing.metrics = bottleneck.metrics
                    return
            
            self._bottlenecks.append(bottleneck)
            logger.warning(f"Bottleneck detected: {bottleneck.bottleneck_type.value} - {bottleneck.description}")
    
    def resolve_bottleneck(self, bottleneck_id: str):
        """Mark bottleneck as resolved"""
        with self._lock:
            for bottleneck in self._bottlenecks:
                if bottleneck.id == bottleneck_id:
                    bottleneck.resolved = True
                    bottleneck.resolved_at = datetime.now()
                    logger.info(f"Bottleneck resolved: {bottleneck_id}")
                    return
    
    def get_active_bottlenecks(self) -> List[Bottleneck]:
        """Get active (unresolved) bottlenecks"""
        with self._lock:
            return [b for b in self._bottlenecks if not b.resolved]
    
    def get_bottleneck_history(self, 
                               hours: int = 24) -> List[Bottleneck]:
        """Get bottleneck history"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._lock:
            return [b for b in self._bottlenecks if b.detected_at > cutoff]
    
    # Default detection rules
    
    def _detect_cpu_bottleneck(self, detector: 'BottleneckDetector') -> Optional[Bottleneck]:
        """Detect CPU bottleneck"""
        cpu_avg = self._metrics.get_average("cpu.usage_percent", 60)
        
        if cpu_avg is None:
            return None
        
        if cpu_avg >= self.config.cpu_threshold:
            severity = Severity.CRITICAL if cpu_avg >= 95 else Severity.HIGH if cpu_avg >= 90 else Severity.MEDIUM
            
            return Bottleneck(
                id=f"cpu-{int(time.time())}",
                bottleneck_type=BottleneckType.CPU,
                severity=severity,
                description=f"CPU usage at {cpu_avg:.1f}%",
                detected_at=datetime.now(),
                metrics={'cpu_usage_percent': cpu_avg},
                recommendations=[
                    "Consider scaling horizontally (add more instances)",
                    "Review CPU-intensive operations for optimization",
                    "Check for runaway processes or infinite loops",
                    "Consider async/parallel processing for CPU-bound tasks"
                ]
            )
        
        return None
    
    def _detect_memory_bottleneck(self, detector: 'BottleneckDetector') -> Optional[Bottleneck]:
        """Detect memory bottleneck"""
        mem_avg = self._metrics.get_average("memory.usage_percent", 60)
        
        if mem_avg is None:
            return None
        
        if mem_avg >= self.config.memory_threshold:
            severity = Severity.CRITICAL if mem_avg >= 95 else Severity.HIGH if mem_avg >= 90 else Severity.MEDIUM
            
            return Bottleneck(
                id=f"memory-{int(time.time())}",
                bottleneck_type=BottleneckType.MEMORY,
                severity=severity,
                description=f"Memory usage at {mem_avg:.1f}%",
                detected_at=datetime.now(),
                metrics={'memory_usage_percent': mem_avg},
                recommendations=[
                    "Check for memory leaks",
                    "Review object lifecycle and caching strategies",
                    "Consider increasing available memory",
                    "Implement memory-efficient data structures"
                ]
            )
        
        return None
    
    def _detect_slow_responses(self, detector: 'BottleneckDetector') -> Optional[Bottleneck]:
        """Detect slow response times"""
        p95 = self._metrics.get_percentile("response_time_ms", 95, 60)
        
        if p95 is None:
            return None
        
        if p95 >= self.config.response_time_threshold_ms:
            severity = Severity.HIGH if p95 >= self.config.response_time_threshold_ms * 2 else Severity.MEDIUM
            
            avg = self._metrics.get_average("response_time_ms", 60) or p95
            
            return Bottleneck(
                id=f"latency-{int(time.time())}",
                bottleneck_type=BottleneckType.DATABASE,  # Often DB-related
                severity=severity,
                description=f"P95 response time at {p95:.1f}ms (avg: {avg:.1f}ms)",
                detected_at=datetime.now(),
                metrics={'p95_response_ms': p95, 'avg_response_ms': avg},
                recommendations=[
                    "Review database queries for N+1 patterns",
                    "Add database indexes for slow queries",
                    "Consider caching frequently accessed data",
                    "Review external service call patterns"
                ]
            )
        
        return None
    
    def _detect_high_error_rate(self, detector: 'BottleneckDetector') -> Optional[Bottleneck]:
        """Detect high error rate"""
        error_rate = self._metrics.get_average("error_rate", 60)
        
        if error_rate is None:
            return None
        
        if error_rate >= self.config.error_rate_threshold:
            severity = Severity.CRITICAL if error_rate >= 0.2 else Severity.HIGH if error_rate >= 0.1 else Severity.MEDIUM
            
            return Bottleneck(
                id=f"errors-{int(time.time())}",
                bottleneck_type=BottleneckType.EXTERNAL_SERVICE,
                severity=severity,
                description=f"Error rate at {error_rate:.1%}",
                detected_at=datetime.now(),
                metrics={'error_rate': error_rate},
                recommendations=[
                    "Review error logs for patterns",
                    "Check external service health",
                    "Implement circuit breakers for failing services",
                    "Add retry logic with exponential backoff"
                ]
            )
        
        return None
    
    def _detect_queue_saturation(self, detector: 'BottleneckDetector') -> Optional[Bottleneck]:
        """Detect queue saturation"""
        queue_depth = self._metrics.get_average("queue.depth", 60)
        
        if queue_depth is None:
            return None
        
        if queue_depth >= self.config.queue_depth_threshold:
            severity = Severity.HIGH if queue_depth >= self.config.queue_depth_threshold * 2 else Severity.MEDIUM
            
            return Bottleneck(
                id=f"queue-{int(time.time())}",
                bottleneck_type=BottleneckType.QUEUE_SATURATION,
                severity=severity,
                description=f"Queue depth at {queue_depth:.0f}",
                detected_at=datetime.now(),
                metrics={'queue_depth': queue_depth},
                recommendations=[
                    "Increase number of workers",
                    "Review worker processing time",
                    "Consider sharding/partitioning queues",
                    "Implement backpressure mechanisms"
                ]
            )
        
        return None
    
    def _detect_degradation_trend(self, detector: 'BottleneckDetector') -> Optional[Bottleneck]:
        """Detect performance degradation trend"""
        trend = self._metrics.get_trend("response_time_ms", self.config.trend_window)
        
        if trend is None:
            return None
        
        # Check if response time is increasing significantly
        current_avg = self._metrics.get_average("response_time_ms", 30)
        baseline_avg = self._metrics.get_average("response_time_ms", 300)
        
        if current_avg and baseline_avg and baseline_avg > 0:
            degradation = (current_avg - baseline_avg) / baseline_avg
            
            if degradation >= self.config.degradation_threshold:
                return Bottleneck(
                    id=f"degradation-{int(time.time())}",
                    bottleneck_type=BottleneckType.DATABASE,
                    severity=Severity.MEDIUM,
                    description=f"Performance degrading: {degradation:.1%} increase in response time",
                    detected_at=datetime.now(),
                    metrics={
                        'current_avg_ms': current_avg,
                        'baseline_avg_ms': baseline_avg,
                        'degradation_percent': degradation * 100
                    },
                    recommendations=[
                        "Check for increasing load",
                        "Review recent deployments",
                        "Monitor resource utilization trends",
                        "Check database query plan changes"
                    ]
                )
        
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get bottleneck summary"""
        active = self.get_active_bottlenecks()
        history = self.get_bottleneck_history(24)
        
        by_type = {}
        for b in history:
            t = b.bottleneck_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        by_severity = {}
        for b in active:
            s = b.severity.value
            by_severity[s] = by_severity.get(s, 0) + 1
        
        return {
            'active_count': len(active),
            'last_24h_count': len(history),
            'by_type': by_type,
            'by_severity': by_severity,
            'active_bottlenecks': [
                {
                    'id': b.id,
                    'type': b.bottleneck_type.value,
                    'severity': b.severity.value,
                    'description': b.description,
                    'detected_at': b.detected_at.isoformat()
                }
                for b in active
            ]
        }


class RootCauseAnalyzer:
    """
    Analyzes root causes of bottlenecks
    """
    
    def __init__(self, detector: BottleneckDetector):
        self.detector = detector
    
    def analyze(self, bottleneck: Bottleneck) -> Dict[str, Any]:
        """Analyze root cause of a bottleneck"""
        analysis = {
            'bottleneck': bottleneck.bottleneck_type.value,
            'possible_causes': [],
            'correlations': [],
            'suggested_investigations': []
        }
        
        # Analyze based on type
        if bottleneck.bottleneck_type == BottleneckType.CPU:
            analysis['possible_causes'] = [
                "High computational load",
                "Inefficient algorithms",
                "Excessive garbage collection",
                "Busy loop or spin wait"
            ]
            analysis['suggested_investigations'] = [
                "Profile CPU usage per function",
                "Check garbage collection metrics",
                "Review hot code paths"
            ]
            
        elif bottleneck.bottleneck_type == BottleneckType.MEMORY:
            analysis['possible_causes'] = [
                "Memory leak",
                "Large in-memory caches",
                "Unbounded data structures",
                "Large file processing"
            ]
            analysis['suggested_investigations'] = [
                "Take heap dump and analyze",
                "Review cache eviction policies",
                "Check for growing collections"
            ]
            
        elif bottleneck.bottleneck_type == BottleneckType.DATABASE:
            analysis['possible_causes'] = [
                "Slow or missing indexes",
                "N+1 query patterns",
                "Lock contention",
                "Connection pool exhaustion"
            ]
            analysis['suggested_investigations'] = [
                "Analyze slow query log",
                "Review query execution plans",
                "Check connection pool metrics"
            ]
        
        # Look for correlations
        analysis['correlations'] = self._find_correlations(bottleneck)
        
        return analysis
    
    def _find_correlations(self, bottleneck: Bottleneck) -> List[str]:
        """Find correlated metrics"""
        correlations = []
        
        # Check if other metrics spiked at similar time
        metrics_to_check = [
            "cpu.usage_percent",
            "memory.usage_percent",
            "response_time_ms",
            "error_rate",
            "queue.depth"
        ]
        
        window = 60  # Look at last 60 seconds
        
        for metric in metrics_to_check:
            trend = self.detector._metrics.get_trend(metric, window)
            if trend and trend > 0.1:  # Increasing trend
                correlations.append(f"{metric} increasing")
        
        return correlations
