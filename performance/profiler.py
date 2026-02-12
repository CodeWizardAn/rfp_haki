"""
Performance Profiler

Code profiling with:
- Function timing
- Memory profiling
- Call graph analysis
- Hot spot detection
"""

import logging
import threading
import time
import functools
import traceback
import sys
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager
import cProfile
import pstats
import io

logger = logging.getLogger(__name__)

# Try to import memory profiler
try:
    import tracemalloc
    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False


@dataclass
class FunctionStats:
    """Statistics for a profiled function"""
    name: str
    module: str
    call_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    last_call_time: Optional[datetime] = None
    error_count: int = 0
    
    def record(self, duration_ms: float, error: bool = False):
        """Record a function call"""
        self.call_count += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        self.avg_time_ms = self.total_time_ms / self.call_count
        self.last_call_time = datetime.now()
        if error:
            self.error_count += 1


@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: datetime
    current_bytes: int
    peak_bytes: int
    traced_objects: int = 0
    top_allocations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CallNode:
    """Node in call graph"""
    function: str
    calls: int = 0
    total_time_ms: float = 0.0
    children: Dict[str, 'CallNode'] = field(default_factory=dict)
    
    def add_child(self, func: str) -> 'CallNode':
        if func not in self.children:
            self.children[func] = CallNode(function=func)
        return self.children[func]


@dataclass 
class ProfilerConfig:
    """Profiler configuration"""
    enabled: bool = True
    trace_memory: bool = False
    track_call_graph: bool = False
    slow_threshold_ms: float = 100.0  # Log slow calls
    sample_rate: float = 1.0  # 0.0-1.0, fraction of calls to profile


class FunctionProfiler:
    """
    Function-level profiler
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config: ProfilerConfig = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, config: ProfilerConfig = None):
        if self._initialized:
            return
        
        self.config = config or ProfilerConfig()
        
        self._stats: Dict[str, FunctionStats] = {}
        self._call_graph = CallNode(function="root")
        self._call_stack = threading.local()
        self._lock = threading.Lock()
        
        # Memory tracking
        self._memory_snapshots: List[MemorySnapshot] = []
        self._tracking_memory = False
        
        self._initialized = True
        logger.info("FunctionProfiler initialized")
    
    def profile(self, func: Callable = None, name: str = None):
        """
        Decorator to profile a function
        
        Usage:
            @profiler.profile
            def my_function():
                ...
                
            @profiler.profile(name="custom_name")
            def another_function():
                ...
        """
        def decorator(f):
            func_name = name or f"{f.__module__}.{f.__qualname__}"
            
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if not self.config.enabled:
                    return f(*args, **kwargs)
                
                # Sample rate check
                if self.config.sample_rate < 1.0:
                    import random
                    if random.random() > self.config.sample_rate:
                        return f(*args, **kwargs)
                
                start = time.perf_counter()
                error = False
                
                try:
                    # Track call graph
                    if self.config.track_call_graph:
                        self._push_call(func_name)
                    
                    result = f(*args, **kwargs)
                    return result
                    
                except Exception as e:
                    error = True
                    raise
                    
                finally:
                    duration_ms = (time.perf_counter() - start) * 1000
                    self._record(func_name, f.__module__, duration_ms, error)
                    
                    if self.config.track_call_graph:
                        self._pop_call()
                    
                    if duration_ms >= self.config.slow_threshold_ms:
                        logger.warning(f"Slow function: {func_name} took {duration_ms:.2f}ms")
            
            return wrapper
        
        if func is not None:
            return decorator(func)
        return decorator
    
    def _record(self, name: str, module: str, duration_ms: float, error: bool):
        """Record function call statistics"""
        with self._lock:
            if name not in self._stats:
                self._stats[name] = FunctionStats(name=name, module=module)
            self._stats[name].record(duration_ms, error)
    
    def _push_call(self, func_name: str):
        """Push function onto call stack"""
        if not hasattr(self._call_stack, 'stack'):
            self._call_stack.stack = [self._call_graph]
        
        current = self._call_stack.stack[-1]
        child = current.add_child(func_name)
        child.calls += 1
        self._call_stack.stack.append(child)
    
    def _pop_call(self):
        """Pop function from call stack"""
        if hasattr(self._call_stack, 'stack') and len(self._call_stack.stack) > 1:
            self._call_stack.stack.pop()
    
    @contextmanager
    def measure(self, name: str):
        """
        Context manager for timing code blocks
        
        Usage:
            with profiler.measure("my_operation"):
                # code to measure
        """
        start = time.perf_counter()
        error = False
        
        try:
            if self.config.track_call_graph:
                self._push_call(name)
            yield
        except Exception:
            error = True
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._record(name, "__context__", duration_ms, error)
            
            if self.config.track_call_graph:
                self._pop_call()
            
            if duration_ms >= self.config.slow_threshold_ms:
                logger.warning(f"Slow block: {name} took {duration_ms:.2f}ms")
    
    def get_stats(self, top_n: int = 20, 
                  sort_by: str = "total_time") -> List[FunctionStats]:
        """Get top functions by specified metric"""
        with self._lock:
            stats = list(self._stats.values())
        
        if sort_by == "total_time":
            stats.sort(key=lambda s: s.total_time_ms, reverse=True)
        elif sort_by == "avg_time":
            stats.sort(key=lambda s: s.avg_time_ms, reverse=True)
        elif sort_by == "call_count":
            stats.sort(key=lambda s: s.call_count, reverse=True)
        elif sort_by == "max_time":
            stats.sort(key=lambda s: s.max_time_ms, reverse=True)
        
        return stats[:top_n]
    
    def get_call_graph(self) -> CallNode:
        """Get call graph"""
        return self._call_graph
    
    def reset(self):
        """Reset all statistics"""
        with self._lock:
            self._stats.clear()
            self._call_graph = CallNode(function="root")
    
    def start_memory_tracking(self):
        """Start memory tracking"""
        if TRACEMALLOC_AVAILABLE:
            tracemalloc.start()
            self._tracking_memory = True
            logger.info("Memory tracking started")
    
    def stop_memory_tracking(self):
        """Stop memory tracking"""
        if TRACEMALLOC_AVAILABLE and self._tracking_memory:
            tracemalloc.stop()
            self._tracking_memory = False
            logger.info("Memory tracking stopped")
    
    def snapshot_memory(self, top_n: int = 10) -> Optional[MemorySnapshot]:
        """Take memory snapshot"""
        if not TRACEMALLOC_AVAILABLE or not self._tracking_memory:
            return None
        
        snapshot = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        
        # Get top allocations
        stats = snapshot.statistics('lineno')
        top_allocations = []
        
        for stat in stats[:top_n]:
            frame = stat.traceback[0] if stat.traceback else None
            top_allocations.append({
                'file': frame.filename if frame else 'unknown',
                'line': frame.lineno if frame else 0,
                'size_kb': stat.size / 1024,
                'count': stat.count
            })
        
        mem_snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            current_bytes=current,
            peak_bytes=peak,
            traced_objects=sum(s.count for s in stats),
            top_allocations=top_allocations
        )
        
        self._memory_snapshots.append(mem_snapshot)
        return mem_snapshot
    
    def get_report(self) -> Dict[str, Any]:
        """Generate profiling report"""
        top_by_time = self.get_stats(top_n=10, sort_by="total_time")
        top_by_calls = self.get_stats(top_n=10, sort_by="call_count")
        top_by_avg = self.get_stats(top_n=10, sort_by="avg_time")
        
        report = {
            'summary': {
                'total_functions': len(self._stats),
                'total_calls': sum(s.call_count for s in self._stats.values()),
                'total_time_ms': sum(s.total_time_ms for s in self._stats.values()),
                'total_errors': sum(s.error_count for s in self._stats.values())
            },
            'top_by_total_time': [
                {
                    'name': s.name,
                    'calls': s.call_count,
                    'total_ms': s.total_time_ms,
                    'avg_ms': s.avg_time_ms
                }
                for s in top_by_time
            ],
            'top_by_calls': [
                {
                    'name': s.name,
                    'calls': s.call_count,
                    'total_ms': s.total_time_ms
                }
                for s in top_by_calls
            ],
            'top_by_avg_time': [
                {
                    'name': s.name,
                    'calls': s.call_count,
                    'avg_ms': s.avg_time_ms,
                    'max_ms': s.max_time_ms
                }
                for s in top_by_avg
            ]
        }
        
        if self._memory_snapshots:
            latest_mem = self._memory_snapshots[-1]
            report['memory'] = {
                'current_mb': latest_mem.current_bytes / (1024 * 1024),
                'peak_mb': latest_mem.peak_bytes / (1024 * 1024),
                'traced_objects': latest_mem.traced_objects,
                'top_allocations': latest_mem.top_allocations[:5]
            }
        
        return report


class CodeProfiler:
    """
    Code block profiler using cProfile
    """
    
    def __init__(self):
        self._profiles: Dict[str, pstats.Stats] = {}
    
    @contextmanager
    def profile(self, name: str):
        """Profile a code block with cProfile"""
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            yield profiler
        finally:
            profiler.disable()
            
            # Store stats
            stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            self._profiles[name] = stats
    
    def get_stats(self, name: str, sort_by: str = 'cumulative',
                  top_n: int = 20) -> str:
        """Get profile stats as string"""
        if name not in self._profiles:
            return f"No profile found: {name}"
        
        stream = io.StringIO()
        stats = self._profiles[name]
        stats.stream = stream
        stats.sort_stats(sort_by)
        stats.print_stats(top_n)
        
        return stream.getvalue()
    
    def get_callers(self, name: str, func_pattern: str) -> str:
        """Get callers of a function"""
        if name not in self._profiles:
            return f"No profile found: {name}"
        
        stream = io.StringIO()
        stats = self._profiles[name]
        stats.stream = stream
        stats.print_callers(func_pattern)
        
        return stream.getvalue()
    
    def get_callees(self, name: str, func_pattern: str) -> str:
        """Get functions called by a function"""
        if name not in self._profiles:
            return f"No profile found: {name}"
        
        stream = io.StringIO()
        stats = self._profiles[name]
        stats.stream = stream
        stats.print_callees(func_pattern)
        
        return stream.getvalue()


class LineProfiler:
    """
    Line-by-line profiler (simplified version)
    """
    
    def __init__(self):
        self._line_times: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    
    def profile_function(self, func: Callable) -> Callable:
        """Profile a function line by line"""
        source_file = func.__code__.co_filename
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get line numbers in function
            start_line = func.__code__.co_firstlineno
            
            # Simple timing - in production use sys.settrace
            start = time.perf_counter()
            result = func(*args, **kwargs)
            total_time = time.perf_counter() - start
            
            # Record (simplified - records total time to first line)
            self._line_times[source_file][start_line].append(total_time * 1000)
            
            return result
        
        return wrapper
    
    def get_line_stats(self, filepath: str) -> Dict[int, Dict[str, float]]:
        """Get statistics per line"""
        stats = {}
        
        for line_no, times in self._line_times.get(filepath, {}).items():
            if times:
                stats[line_no] = {
                    'hits': len(times),
                    'total_ms': sum(times),
                    'avg_ms': sum(times) / len(times),
                    'max_ms': max(times)
                }
        
        return stats


class HotSpotDetector:
    """
    Detect performance hot spots
    """
    
    def __init__(self, profiler: FunctionProfiler,
                 time_threshold_ms: float = 100.0,
                 call_threshold: int = 1000):
        self.profiler = profiler
        self.time_threshold_ms = time_threshold_ms
        self.call_threshold = call_threshold
    
    def find_hot_spots(self) -> List[Dict[str, Any]]:
        """Find performance hot spots"""
        hot_spots = []
        
        for stats in self.profiler.get_stats(top_n=100, sort_by="total_time"):
            issues = []
            
            # High total time
            if stats.total_time_ms > self.time_threshold_ms * 10:
                issues.append(f"High total time: {stats.total_time_ms:.2f}ms")
            
            # High average time
            if stats.avg_time_ms > self.time_threshold_ms:
                issues.append(f"Slow average: {stats.avg_time_ms:.2f}ms")
            
            # Called too frequently
            if stats.call_count > self.call_threshold:
                issues.append(f"Called {stats.call_count} times")
            
            # High error rate
            if stats.call_count > 0:
                error_rate = stats.error_count / stats.call_count
                if error_rate > 0.1:
                    issues.append(f"High error rate: {error_rate:.1%}")
            
            if issues:
                hot_spots.append({
                    'function': stats.name,
                    'issues': issues,
                    'stats': {
                        'calls': stats.call_count,
                        'total_ms': stats.total_time_ms,
                        'avg_ms': stats.avg_time_ms,
                        'errors': stats.error_count
                    },
                    'severity': 'high' if len(issues) > 2 else 'medium'
                })
        
        return hot_spots
    
    def get_recommendations(self) -> List[str]:
        """Get optimization recommendations"""
        hot_spots = self.find_hot_spots()
        recommendations = []
        
        for spot in hot_spots:
            func = spot['function']
            stats = spot['stats']
            
            if stats['calls'] > self.call_threshold:
                recommendations.append(
                    f"Consider caching results for {func} (called {stats['calls']} times)"
                )
            
            if stats['avg_ms'] > self.time_threshold_ms:
                recommendations.append(
                    f"Optimize {func} - average time {stats['avg_ms']:.2f}ms is above threshold"
                )
            
            if stats['errors'] > 0:
                error_rate = stats['errors'] / stats['calls']
                if error_rate > 0.05:
                    recommendations.append(
                        f"Fix errors in {func} - {error_rate:.1%} failure rate"
                    )
        
        return recommendations


# Global profiler instance
profiler = FunctionProfiler()


def profile(func: Callable = None, name: str = None):
    """Convenience decorator using global profiler"""
    return profiler.profile(func, name)


@contextmanager
def measure(name: str):
    """Convenience context manager using global profiler"""
    with profiler.measure(name):
        yield
