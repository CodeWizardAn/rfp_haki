"""
Load Tester

Load testing with:
- Concurrent user simulation
- Scenario-based testing
- Ramp-up patterns
- Result analysis
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
import statistics

logger = logging.getLogger(__name__)


class LoadPattern(Enum):
    """Load patterns"""
    CONSTANT = "constant"  # Fixed number of users
    RAMP_UP = "ramp_up"  # Gradually increase users
    RAMP_DOWN = "ramp_down"  # Gradually decrease users
    SPIKE = "spike"  # Sudden spike in users
    WAVE = "wave"  # Oscillating load
    STEP = "step"  # Step-wise increases


@dataclass
class UserScenario:
    """A user scenario to execute"""
    name: str
    steps: List[Callable]
    think_time_range: Tuple[float, float] = (1.0, 3.0)  # Min, max seconds
    weight: float = 1.0  # Relative weight for scenario selection


@dataclass
class LoadTestConfig:
    """Load test configuration"""
    name: str
    description: str = ""
    
    # User configuration
    users: int = 10
    ramp_up_time: int = 30  # Seconds to reach full users
    duration: int = 300  # Total test duration
    
    # Pattern
    pattern: LoadPattern = LoadPattern.CONSTANT
    
    # Thresholds
    target_rps: Optional[float] = None
    max_response_time_ms: float = 1000.0
    max_error_rate: float = 0.05
    
    # Reporting
    report_interval: int = 10  # Seconds


@dataclass
class RequestMetric:
    """Metrics for a single request"""
    timestamp: datetime
    scenario: str
    step: str
    latency_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class LoadTestResult:
    """Load test result"""
    config: LoadTestConfig
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Latency stats
    avg_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p90_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    std_dev_latency_ms: float = 0.0
    
    # Throughput
    requests_per_second: float = 0.0
    peak_rps: float = 0.0
    
    # Error stats
    error_rate: float = 0.0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Per-scenario stats
    scenario_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Time series (for graphs)
    time_series: List[Dict[str, Any]] = field(default_factory=list)
    
    # Pass/fail
    passed: bool = True
    failure_reasons: List[str] = field(default_factory=list)


class VirtualUser:
    """
    Virtual user that executes scenarios
    """
    
    def __init__(self, user_id: int, scenarios: List[UserScenario]):
        self.user_id = user_id
        self.scenarios = scenarios
        self._weights = [s.weight for s in scenarios]
        self._total_weight = sum(self._weights)
        self._running = False
    
    def run(self, duration: float, 
           on_request: Callable[[RequestMetric], None]):
        """Run user for specified duration"""
        self._running = True
        end_time = time.time() + duration
        
        while self._running and time.time() < end_time:
            scenario = self._select_scenario()
            self._execute_scenario(scenario, on_request)
    
    def stop(self):
        """Stop user"""
        self._running = False
    
    def _select_scenario(self) -> UserScenario:
        """Select a scenario based on weights"""
        r = random.uniform(0, self._total_weight)
        cumulative = 0
        
        for i, weight in enumerate(self._weights):
            cumulative += weight
            if r <= cumulative:
                return self.scenarios[i]
        
        return self.scenarios[-1]
    
    def _execute_scenario(self, scenario: UserScenario,
                         on_request: Callable):
        """Execute a scenario"""
        for i, step in enumerate(scenario.steps):
            if not self._running:
                break
            
            start = time.perf_counter()
            error = None
            success = True
            
            try:
                step()
            except Exception as e:
                success = False
                error = str(e)
            
            latency_ms = (time.perf_counter() - start) * 1000
            
            metric = RequestMetric(
                timestamp=datetime.now(),
                scenario=scenario.name,
                step=f"step_{i}",
                latency_ms=latency_ms,
                success=success,
                error=error
            )
            
            on_request(metric)
            
            # Think time between steps
            if i < len(scenario.steps) - 1 and self._running:
                think_time = random.uniform(*scenario.think_time_range)
                time.sleep(think_time)


class LoadTester:
    """
    Load testing framework
    """
    
    def __init__(self):
        self._running = False
        self._metrics: List[RequestMetric] = []
        self._metrics_lock = threading.Lock()
        self._users: List[VirtualUser] = []
        self._current_result: Optional[LoadTestResult] = None
    
    def run(self, config: LoadTestConfig,
            scenarios: List[UserScenario]) -> LoadTestResult:
        """
        Run load test
        
        Args:
            config: Test configuration
            scenarios: User scenarios to execute
            
        Returns:
            LoadTestResult
        """
        self._running = True
        self._metrics.clear()
        
        result = LoadTestResult(
            config=config,
            started_at=datetime.now()
        )
        self._current_result = result
        
        logger.info(f"Starting load test: {config.name} ({config.users} users)")
        
        try:
            # Start users based on pattern
            self._start_users(config, scenarios)
            
            # Run for duration
            self._run_test(config)
            
            # Calculate results
            self._calculate_results(result)
            
            # Check thresholds
            self._check_thresholds(result, config)
            
        except Exception as e:
            logger.error(f"Load test failed: {e}")
            result.failure_reasons.append(str(e))
            result.passed = False
        
        finally:
            self._stop_users()
            result.ended_at = datetime.now()
            self._running = False
        
        logger.info(f"Load test completed: {'PASSED' if result.passed else 'FAILED'}")
        return result
    
    def _start_users(self, config: LoadTestConfig,
                    scenarios: List[UserScenario]):
        """Start virtual users based on pattern"""
        if config.pattern == LoadPattern.CONSTANT:
            self._start_users_constant(config.users, scenarios, config.duration)
            
        elif config.pattern == LoadPattern.RAMP_UP:
            self._start_users_ramp_up(config.users, scenarios, 
                                      config.ramp_up_time, config.duration)
        else:
            # Default to constant
            self._start_users_constant(config.users, scenarios, config.duration)
    
    def _start_users_constant(self, num_users: int,
                             scenarios: List[UserScenario],
                             duration: float):
        """Start all users at once"""
        executor = ThreadPoolExecutor(max_workers=num_users)
        
        for i in range(num_users):
            user = VirtualUser(i, scenarios)
            self._users.append(user)
            executor.submit(user.run, duration, self._record_metric)
    
    def _start_users_ramp_up(self, num_users: int,
                            scenarios: List[UserScenario],
                            ramp_up_time: float,
                            duration: float):
        """Start users gradually"""
        executor = ThreadPoolExecutor(max_workers=num_users)
        interval = ramp_up_time / num_users if num_users > 0 else 0
        
        for i in range(num_users):
            if not self._running:
                break
            
            user = VirtualUser(i, scenarios)
            self._users.append(user)
            
            # Remaining duration for this user
            remaining = duration - (i * interval)
            if remaining > 0:
                executor.submit(user.run, remaining, self._record_metric)
            
            time.sleep(interval)
    
    def _stop_users(self):
        """Stop all users"""
        for user in self._users:
            user.stop()
        self._users.clear()
    
    def _run_test(self, config: LoadTestConfig):
        """Run test and report progress"""
        start_time = time.time()
        last_report = start_time
        
        while self._running and (time.time() - start_time) < config.duration:
            # Report progress
            if time.time() - last_report >= config.report_interval:
                self._report_progress(time.time() - start_time)
                last_report = time.time()
            
            time.sleep(1)
    
    def _record_metric(self, metric: RequestMetric):
        """Record a request metric"""
        with self._metrics_lock:
            self._metrics.append(metric)
    
    def _report_progress(self, elapsed: float):
        """Report test progress"""
        with self._metrics_lock:
            metrics = list(self._metrics)
        
        if not metrics:
            return
        
        recent = [m for m in metrics if (datetime.now() - m.timestamp).total_seconds() < 10]
        
        if recent:
            avg_latency = sum(m.latency_ms for m in recent) / len(recent)
            errors = sum(1 for m in recent if not m.success)
            rps = len(recent) / 10
        else:
            avg_latency = 0
            errors = 0
            rps = 0
        
        logger.info(
            f"Load test progress: {elapsed:.0f}s, "
            f"RPS: {rps:.1f}, "
            f"Avg latency: {avg_latency:.2f}ms, "
            f"Errors: {errors}"
        )
        
        # Add to time series
        if self._current_result:
            self._current_result.time_series.append({
                'timestamp': datetime.now().isoformat(),
                'elapsed_seconds': elapsed,
                'rps': rps,
                'avg_latency_ms': avg_latency,
                'errors': errors,
                'active_users': len(self._users)
            })
    
    def _calculate_results(self, result: LoadTestResult):
        """Calculate final results"""
        with self._metrics_lock:
            metrics = list(self._metrics)
        
        if not metrics:
            return
        
        result.total_requests = len(metrics)
        result.successful_requests = sum(1 for m in metrics if m.success)
        result.failed_requests = sum(1 for m in metrics if not m.success)
        
        # Latency calculations
        latencies = [m.latency_ms for m in metrics]
        sorted_latencies = sorted(latencies)
        
        result.avg_latency_ms = statistics.mean(latencies)
        result.min_latency_ms = min(latencies)
        result.max_latency_ms = max(latencies)
        result.std_dev_latency_ms = statistics.stdev(latencies) if len(latencies) > 1 else 0
        
        n = len(sorted_latencies)
        result.p50_latency_ms = sorted_latencies[int(n * 0.50)]
        result.p90_latency_ms = sorted_latencies[int(n * 0.90)]
        result.p95_latency_ms = sorted_latencies[int(n * 0.95)]
        result.p99_latency_ms = sorted_latencies[int(n * 0.99)]
        
        # Throughput
        duration = (result.ended_at - result.started_at).total_seconds() if result.ended_at else 1
        result.requests_per_second = result.total_requests / duration
        
        # Calculate peak RPS
        if result.time_series:
            result.peak_rps = max(p['rps'] for p in result.time_series)
        
        # Error rate
        result.error_rate = result.failed_requests / result.total_requests if result.total_requests > 0 else 0
        
        # Errors by type
        for metric in metrics:
            if metric.error:
                error_type = metric.error.split(':')[0] if ':' in metric.error else metric.error
                result.errors_by_type[error_type] = result.errors_by_type.get(error_type, 0) + 1
        
        # Per-scenario stats
        scenarios = set(m.scenario for m in metrics)
        for scenario in scenarios:
            scenario_metrics = [m for m in metrics if m.scenario == scenario]
            scenario_latencies = [m.latency_ms for m in scenario_metrics]
            
            result.scenario_stats[scenario] = {
                'total_requests': len(scenario_metrics),
                'error_rate': sum(1 for m in scenario_metrics if not m.success) / len(scenario_metrics),
                'avg_latency_ms': statistics.mean(scenario_latencies),
                'p95_latency_ms': sorted(scenario_latencies)[int(len(scenario_latencies) * 0.95)]
            }
    
    def _check_thresholds(self, result: LoadTestResult, 
                         config: LoadTestConfig):
        """Check if results meet thresholds"""
        # Check error rate
        if result.error_rate > config.max_error_rate:
            result.passed = False
            result.failure_reasons.append(
                f"Error rate {result.error_rate:.1%} exceeds threshold {config.max_error_rate:.1%}"
            )
        
        # Check response time
        if result.p95_latency_ms > config.max_response_time_ms:
            result.passed = False
            result.failure_reasons.append(
                f"P95 latency {result.p95_latency_ms:.1f}ms exceeds threshold {config.max_response_time_ms:.1f}ms"
            )
        
        # Check target RPS
        if config.target_rps and result.requests_per_second < config.target_rps:
            result.passed = False
            result.failure_reasons.append(
                f"RPS {result.requests_per_second:.1f} below target {config.target_rps:.1f}"
            )
    
    def abort(self):
        """Abort running test"""
        self._running = False
        self._stop_users()
        logger.warning("Load test aborted")
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current test status"""
        if not self._current_result:
            return None
        
        with self._metrics_lock:
            total = len(self._metrics)
            errors = sum(1 for m in self._metrics if not m.success)
        
        elapsed = (datetime.now() - self._current_result.started_at).total_seconds()
        
        return {
            'name': self._current_result.config.name,
            'running': self._running,
            'elapsed_seconds': elapsed,
            'total_requests': total,
            'failed_requests': errors,
            'active_users': len(self._users),
            'error_rate': errors / total if total > 0 else 0
        }


class ScenarioBuilder:
    """
    Builder for creating user scenarios
    """
    
    def __init__(self, name: str):
        self.name = name
        self._steps: List[Callable] = []
        self._think_time = (1.0, 3.0)
        self._weight = 1.0
    
    def add_step(self, step: Callable) -> 'ScenarioBuilder':
        """Add a step to the scenario"""
        self._steps.append(step)
        return self
    
    def add_request(self, request_func: Callable, *args, **kwargs) -> 'ScenarioBuilder':
        """Add a request step"""
        self._steps.append(lambda: request_func(*args, **kwargs))
        return self
    
    def with_think_time(self, min_seconds: float, 
                       max_seconds: float) -> 'ScenarioBuilder':
        """Set think time range"""
        self._think_time = (min_seconds, max_seconds)
        return self
    
    def with_weight(self, weight: float) -> 'ScenarioBuilder':
        """Set scenario weight"""
        self._weight = weight
        return self
    
    def build(self) -> UserScenario:
        """Build the scenario"""
        return UserScenario(
            name=self.name,
            steps=self._steps,
            think_time_range=self._think_time,
            weight=self._weight
        )


class LoadTestRunner:
    """
    High-level load test runner
    """
    
    def __init__(self):
        self.tester = LoadTester()
        self._results: List[LoadTestResult] = []
    
    def run_simple_test(self, 
                       request_func: Callable,
                       users: int = 10,
                       duration: int = 60) -> LoadTestResult:
        """
        Run a simple load test
        
        Args:
            request_func: Function to call for each request
            users: Number of concurrent users
            duration: Test duration in seconds
        """
        scenario = ScenarioBuilder("simple") \
            .add_step(request_func) \
            .with_think_time(0.5, 1.5) \
            .build()
        
        config = LoadTestConfig(
            name="Simple Load Test",
            users=users,
            duration=duration
        )
        
        result = self.tester.run(config, [scenario])
        self._results.append(result)
        return result
    
    def run_scenario_test(self,
                         scenarios: List[UserScenario],
                         config: LoadTestConfig) -> LoadTestResult:
        """Run test with multiple scenarios"""
        result = self.tester.run(config, scenarios)
        self._results.append(result)
        return result
    
    def compare_results(self) -> Dict[str, Any]:
        """Compare all test results"""
        if not self._results:
            return {}
        
        return {
            'tests': [
                {
                    'name': r.config.name,
                    'users': r.config.users,
                    'rps': r.requests_per_second,
                    'avg_latency_ms': r.avg_latency_ms,
                    'p95_latency_ms': r.p95_latency_ms,
                    'error_rate': r.error_rate,
                    'passed': r.passed
                }
                for r in self._results
            ],
            'best_rps': max(r.requests_per_second for r in self._results),
            'best_latency': min(r.avg_latency_ms for r in self._results)
        }
