"""
Stress Tester

Stress testing with:
- Breaking point detection
- Resource exhaustion tests
- Recovery testing
- Stability testing
"""

import logging
import threading
import time
import random
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class StressTestStatus(Enum):
    """Stress test status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class StressTestConfig:
    """Stress test configuration"""
    name: str
    description: str = ""
    
    # Load parameters
    initial_rate: float = 10.0  # Requests per second
    rate_increment: float = 10.0  # Increase per step
    step_duration: int = 30  # Seconds per step
    max_rate: float = 1000.0
    
    # Limits
    max_duration: int = 600  # Max test duration (seconds)
    max_errors: int = 100  # Stop after this many errors
    max_error_rate: float = 0.5  # Stop if error rate exceeds
    
    # Thresholds
    latency_threshold_ms: float = 1000.0  # Mark as degraded above this
    breaking_point_error_rate: float = 0.1  # 10% errors = breaking point


@dataclass
class StressTestResult:
    """Stress test result"""
    config: StressTestConfig
    status: StressTestStatus
    
    # Timing
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Performance
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    
    # Breaking point
    breaking_point_rate: Optional[float] = None
    breaking_point_reason: Optional[str] = None
    
    # Peak performance
    max_sustainable_rate: float = 0.0
    max_requests_per_second: float = 0.0
    
    # Per-step metrics
    step_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StepResult:
    """Result for a single step"""
    step: int
    rate: float
    duration: float
    requests: int
    errors: int
    avg_latency_ms: float
    p95_latency_ms: float
    error_rate: float


class StressTester:
    """
    Stress testing framework
    """
    
    def __init__(self):
        self._running = False
        self._abort_requested = False
        self._current_test: Optional[StressTestResult] = None
        self._latencies: List[float] = []
        self._lock = threading.Lock()
    
    def run(self, config: StressTestConfig,
            request_func: Callable[[], Any]) -> StressTestResult:
        """
        Run a stress test
        
        Args:
            config: Test configuration
            request_func: Function to call for each request
            
        Returns:
            StressTestResult
        """
        self._running = True
        self._abort_requested = False
        self._latencies = []
        
        result = StressTestResult(
            config=config,
            status=StressTestStatus.RUNNING,
            started_at=datetime.now()
        )
        self._current_test = result
        
        logger.info(f"Starting stress test: {config.name}")
        
        try:
            current_rate = config.initial_rate
            step = 0
            
            while self._running and not self._abort_requested:
                # Check limits
                if current_rate > config.max_rate:
                    logger.info(f"Reached max rate: {config.max_rate}")
                    break
                
                elapsed = (datetime.now() - result.started_at).total_seconds()
                if elapsed > config.max_duration:
                    logger.info(f"Reached max duration: {config.max_duration}s")
                    break
                
                # Run step
                step_result = self._run_step(
                    step, current_rate, config.step_duration, request_func
                )
                result.step_results.append({
                    'step': step,
                    'rate': current_rate,
                    'requests': step_result.requests,
                    'errors': step_result.errors,
                    'error_rate': step_result.error_rate,
                    'avg_latency_ms': step_result.avg_latency_ms,
                    'p95_latency_ms': step_result.p95_latency_ms
                })
                
                result.total_requests += step_result.requests
                result.successful_requests += step_result.requests - step_result.errors
                result.failed_requests += step_result.errors
                
                # Check for breaking point
                if step_result.error_rate >= config.breaking_point_error_rate:
                    result.breaking_point_rate = current_rate
                    result.breaking_point_reason = f"Error rate {step_result.error_rate:.1%} at {current_rate} req/s"
                    logger.warning(f"Breaking point detected: {result.breaking_point_reason}")
                    break
                
                # Update max sustainable rate
                if step_result.error_rate < 0.01:  # Less than 1% errors
                    result.max_sustainable_rate = current_rate
                
                # Check error limit
                if result.failed_requests >= config.max_errors:
                    logger.warning(f"Reached max errors: {config.max_errors}")
                    break
                
                # Increase rate for next step
                current_rate += config.rate_increment
                step += 1
            
            # Calculate final metrics
            self._calculate_final_metrics(result)
            
            result.status = StressTestStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Stress test failed: {e}")
            result.status = StressTestStatus.FAILED
            result.breaking_point_reason = str(e)
        
        finally:
            result.ended_at = datetime.now()
            result.duration_seconds = (result.ended_at - result.started_at).total_seconds()
            self._running = False
        
        logger.info(f"Stress test completed: {result.status.value}")
        return result
    
    def _run_step(self, step: int, rate: float, duration: int,
                  request_func: Callable) -> StepResult:
        """Run a single step at specified rate"""
        logger.info(f"Step {step}: {rate} req/s for {duration}s")
        
        step_latencies = []
        errors = 0
        requests = 0
        
        interval = 1.0 / rate if rate > 0 else 1.0
        end_time = time.time() + duration
        
        with ThreadPoolExecutor(max_workers=min(100, int(rate * 2))) as executor:
            futures = []
            
            while time.time() < end_time and not self._abort_requested:
                future = executor.submit(self._make_request, request_func)
                futures.append(future)
                requests += 1
                
                # Rate limiting
                time.sleep(interval)
            
            # Collect results
            for future in as_completed(futures, timeout=30):
                try:
                    latency, success = future.result()
                    step_latencies.append(latency)
                    
                    with self._lock:
                        self._latencies.append(latency)
                    
                    if not success:
                        errors += 1
                        
                except Exception:
                    errors += 1
        
        # Calculate step metrics
        avg_latency = sum(step_latencies) / len(step_latencies) if step_latencies else 0
        sorted_latencies = sorted(step_latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p95_latency = sorted_latencies[p95_idx] if sorted_latencies else 0
        
        return StepResult(
            step=step,
            rate=rate,
            duration=duration,
            requests=requests,
            errors=errors,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            error_rate=errors / requests if requests > 0 else 0
        )
    
    def _make_request(self, request_func: Callable) -> Tuple[float, bool]:
        """Make a single request and measure latency"""
        start = time.perf_counter()
        success = True
        
        try:
            request_func()
        except Exception:
            success = False
        
        latency_ms = (time.perf_counter() - start) * 1000
        return latency_ms, success
    
    def _calculate_final_metrics(self, result: StressTestResult):
        """Calculate final metrics from collected data"""
        with self._lock:
            latencies = sorted(self._latencies)
        
        if latencies:
            result.avg_latency_ms = sum(latencies) / len(latencies)
            result.max_latency_ms = max(latencies)
            
            result.p50_latency_ms = latencies[int(len(latencies) * 0.50)]
            result.p95_latency_ms = latencies[int(len(latencies) * 0.95)]
            result.p99_latency_ms = latencies[int(len(latencies) * 0.99)]
        
        # Calculate max RPS
        if result.step_results:
            result.max_requests_per_second = max(
                r['rate'] for r in result.step_results
                if r['error_rate'] < 0.1
            ) if any(r['error_rate'] < 0.1 for r in result.step_results) else 0
    
    def abort(self):
        """Abort running test"""
        self._abort_requested = True
        logger.warning("Stress test abort requested")
    
    def get_current_status(self) -> Optional[Dict[str, Any]]:
        """Get current test status"""
        if not self._current_test:
            return None
        
        result = self._current_test
        elapsed = (datetime.now() - result.started_at).total_seconds()
        
        return {
            'name': result.config.name,
            'status': result.status.value,
            'elapsed_seconds': elapsed,
            'total_requests': result.total_requests,
            'failed_requests': result.failed_requests,
            'current_step': len(result.step_results),
            'current_rate': result.step_results[-1]['rate'] if result.step_results else 0
        }


class ResourceExhaustionTester:
    """
    Test resource exhaustion scenarios
    """
    
    def __init__(self):
        self._results: Dict[str, Any] = {}
    
    def test_memory_exhaustion(self, 
                               chunk_size_mb: int = 100,
                               max_gb: float = 2.0) -> Dict[str, Any]:
        """Test memory exhaustion"""
        logger.info(f"Testing memory exhaustion (max {max_gb}GB)")
        
        chunks = []
        total_mb = 0
        max_mb = int(max_gb * 1024)
        
        try:
            while total_mb < max_mb:
                # Allocate chunk
                chunk = bytearray(chunk_size_mb * 1024 * 1024)
                chunks.append(chunk)
                total_mb += chunk_size_mb
                
                logger.debug(f"Allocated {total_mb}MB")
                
        except MemoryError:
            logger.warning(f"Memory exhaustion at {total_mb}MB")
        
        finally:
            # Clean up
            chunks.clear()
        
        result = {
            'max_allocation_mb': total_mb,
            'chunk_size_mb': chunk_size_mb,
            'exhausted': total_mb < max_mb
        }
        
        self._results['memory'] = result
        return result
    
    def test_thread_exhaustion(self, 
                               max_threads: int = 1000) -> Dict[str, Any]:
        """Test thread exhaustion"""
        logger.info(f"Testing thread exhaustion (max {max_threads})")
        
        threads = []
        created = 0
        
        def worker():
            time.sleep(10)
        
        try:
            while created < max_threads:
                t = threading.Thread(target=worker)
                t.start()
                threads.append(t)
                created += 1
                
        except (RuntimeError, OSError) as e:
            logger.warning(f"Thread exhaustion at {created}: {e}")
        
        finally:
            # Signal threads to stop (they're sleeping)
            for t in threads:
                t.join(timeout=0.1)
        
        result = {
            'max_threads_created': created,
            'limit_reached': created < max_threads
        }
        
        self._results['threads'] = result
        return result
    
    def test_connection_exhaustion(self,
                                   connection_factory: Callable,
                                   max_connections: int = 1000) -> Dict[str, Any]:
        """Test connection exhaustion"""
        logger.info(f"Testing connection exhaustion (max {max_connections})")
        
        connections = []
        created = 0
        
        try:
            while created < max_connections:
                conn = connection_factory()
                connections.append(conn)
                created += 1
                
        except Exception as e:
            logger.warning(f"Connection exhaustion at {created}: {e}")
        
        finally:
            # Clean up connections
            for conn in connections:
                try:
                    if hasattr(conn, 'close'):
                        conn.close()
                except Exception:
                    pass
        
        result = {
            'max_connections_created': created,
            'limit_reached': created < max_connections
        }
        
        self._results['connections'] = result
        return result
    
    def get_results(self) -> Dict[str, Any]:
        """Get all exhaustion test results"""
        return self._results


class RecoveryTester:
    """
    Test system recovery after failures
    """
    
    def __init__(self):
        self._results: List[Dict[str, Any]] = []
    
    def test_recovery_after_overload(self,
                                     request_func: Callable,
                                     overload_rate: float = 1000.0,
                                     overload_duration: int = 30,
                                     recovery_timeout: int = 60) -> Dict[str, Any]:
        """
        Test recovery after overload
        
        Generates overload, then measures recovery time
        """
        logger.info(f"Testing recovery after overload ({overload_rate} req/s for {overload_duration}s)")
        
        # Baseline measurement
        baseline = self._measure_latency(request_func, samples=100)
        logger.info(f"Baseline latency: {baseline['avg_ms']:.2f}ms")
        
        # Generate overload
        overload_start = time.time()
        errors = 0
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            interval = 1.0 / overload_rate
            
            while time.time() - overload_start < overload_duration:
                future = executor.submit(request_func)
                futures.append(future)
                time.sleep(interval)
            
            for future in as_completed(futures, timeout=10):
                try:
                    future.result()
                except Exception:
                    errors += 1
        
        overload_error_rate = errors / len(futures) if futures else 0
        logger.info(f"Overload error rate: {overload_error_rate:.1%}")
        
        # Measure recovery
        recovery_start = time.time()
        recovered = False
        recovery_time = None
        
        while time.time() - recovery_start < recovery_timeout:
            current = self._measure_latency(request_func, samples=10)
            
            # Recovered if latency is within 2x baseline
            if current['avg_ms'] < baseline['avg_ms'] * 2:
                recovered = True
                recovery_time = time.time() - recovery_start
                break
            
            time.sleep(1)
        
        result = {
            'baseline_latency_ms': baseline['avg_ms'],
            'overload_rate': overload_rate,
            'overload_duration': overload_duration,
            'overload_error_rate': overload_error_rate,
            'recovered': recovered,
            'recovery_time_seconds': recovery_time,
            'final_latency_ms': current['avg_ms']
        }
        
        self._results.append(result)
        return result
    
    def _measure_latency(self, request_func: Callable, 
                        samples: int = 100) -> Dict[str, float]:
        """Measure request latency"""
        latencies = []
        
        for _ in range(samples):
            start = time.perf_counter()
            try:
                request_func()
                latencies.append((time.perf_counter() - start) * 1000)
            except Exception:
                pass
        
        if not latencies:
            return {'avg_ms': float('inf'), 'p95_ms': float('inf')}
        
        sorted_lat = sorted(latencies)
        return {
            'avg_ms': sum(latencies) / len(latencies),
            'p95_ms': sorted_lat[int(len(sorted_lat) * 0.95)]
        }
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all recovery test results"""
        return self._results


class StabilityTester:
    """
    Long-running stability tests
    """
    
    def __init__(self):
        self._running = False
        self._metrics: deque = deque(maxlen=10000)
    
    def run(self, request_func: Callable,
            rate: float = 100.0,
            duration_hours: float = 1.0,
            report_interval: int = 60) -> Dict[str, Any]:
        """
        Run stability test
        
        Args:
            request_func: Function to call
            rate: Target requests per second
            duration_hours: Test duration in hours
            report_interval: Seconds between reports
        """
        logger.info(f"Starting stability test: {rate} req/s for {duration_hours}h")
        
        self._running = True
        self._metrics.clear()
        
        duration_seconds = int(duration_hours * 3600)
        start_time = time.time()
        last_report = start_time
        
        total_requests = 0
        total_errors = 0
        
        try:
            with ThreadPoolExecutor(max_workers=min(100, int(rate * 2))) as executor:
                interval = 1.0 / rate if rate > 0 else 1.0
                
                while self._running and (time.time() - start_time) < duration_seconds:
                    # Make request
                    req_start = time.perf_counter()
                    
                    try:
                        request_func()
                        latency = (time.perf_counter() - req_start) * 1000
                        success = True
                    except Exception:
                        latency = (time.perf_counter() - req_start) * 1000
                        success = False
                        total_errors += 1
                    
                    total_requests += 1
                    
                    self._metrics.append({
                        'timestamp': time.time(),
                        'latency_ms': latency,
                        'success': success
                    })
                    
                    # Report progress
                    if time.time() - last_report >= report_interval:
                        self._report_progress(
                            time.time() - start_time,
                            total_requests,
                            total_errors
                        )
                        last_report = time.time()
                    
                    # Rate limiting
                    time.sleep(interval)
        
        finally:
            self._running = False
        
        # Calculate results
        return self._calculate_results(
            start_time, total_requests, total_errors
        )
    
    def _report_progress(self, elapsed: float, requests: int, errors: int):
        """Report test progress"""
        recent = list(self._metrics)[-1000:]
        
        if recent:
            avg_latency = sum(m['latency_ms'] for m in recent) / len(recent)
            recent_errors = sum(1 for m in recent if not m['success'])
            error_rate = recent_errors / len(recent)
        else:
            avg_latency = 0
            error_rate = 0
        
        logger.info(
            f"Stability test progress: {elapsed/3600:.2f}h, "
            f"{requests} requests, {errors} errors, "
            f"avg latency: {avg_latency:.2f}ms, "
            f"recent error rate: {error_rate:.2%}"
        )
    
    def _calculate_results(self, start_time: float, 
                          total_requests: int,
                          total_errors: int) -> Dict[str, Any]:
        """Calculate final results"""
        metrics = list(self._metrics)
        duration = time.time() - start_time
        
        if not metrics:
            return {
                'duration_hours': duration / 3600,
                'total_requests': total_requests,
                'error_rate': 0
            }
        
        latencies = sorted(m['latency_ms'] for m in metrics)
        
        return {
            'duration_hours': duration / 3600,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / total_requests if total_requests > 0 else 0,
            'avg_latency_ms': sum(latencies) / len(latencies),
            'p50_latency_ms': latencies[int(len(latencies) * 0.50)],
            'p95_latency_ms': latencies[int(len(latencies) * 0.95)],
            'p99_latency_ms': latencies[int(len(latencies) * 0.99)],
            'max_latency_ms': max(latencies),
            'requests_per_second': total_requests / duration if duration > 0 else 0
        }
    
    def stop(self):
        """Stop stability test"""
        self._running = False
        logger.info("Stability test stop requested")
