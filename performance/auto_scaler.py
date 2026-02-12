"""
Auto Scaler

Automatic scaling with:
- Metrics-based scaling
- Scaling policies
- Cooldown periods
- Predictive scaling
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ScalingDirection(Enum):
    """Scaling direction"""
    UP = "up"
    DOWN = "down"
    NONE = "none"


class ScalingStatus(Enum):
    """Current scaling status"""
    IDLE = "idle"
    SCALING_UP = "scaling_up"
    SCALING_DOWN = "scaling_down"
    COOLDOWN = "cooldown"


@dataclass
class ScalingEvent:
    """A scaling event"""
    timestamp: datetime
    direction: ScalingDirection
    from_count: int
    to_count: int
    trigger_metric: str
    trigger_value: float
    reason: str


@dataclass
class ScalingPolicy:
    """Scaling policy configuration"""
    name: str
    metric: str
    
    # Scale up thresholds
    scale_up_threshold: float
    
    # Scale down thresholds
    scale_down_threshold: float
    
    # Optional fields with defaults
    scale_up_step: int = 1
    scale_up_cooldown: int = 300  # Seconds
    scale_down_step: int = 1
    scale_down_cooldown: int = 300
    
    # Evaluation
    evaluation_periods: int = 3  # Number of periods metric must breach
    period_seconds: int = 60  # Length of each period
    
    # Bounds
    min_instances: int = 1
    max_instances: int = 10


@dataclass
class ScalerConfig:
    """Auto scaler configuration"""
    check_interval: int = 60  # Seconds between checks
    default_cooldown: int = 300  # Default cooldown period
    stabilization_window: int = 300  # Wait before scaling down
    
    # Default policies
    cpu_scale_up: float = 70.0
    cpu_scale_down: float = 30.0
    memory_scale_up: float = 80.0
    memory_scale_down: float = 40.0


class MetricProvider(ABC):
    """Abstract metric provider"""
    
    @abstractmethod
    def get_metric(self, metric_name: str) -> Optional[float]:
        """Get current metric value"""
        pass
    
    @abstractmethod
    def get_metric_average(self, metric_name: str, seconds: int) -> Optional[float]:
        """Get metric average over time period"""
        pass


class InMemoryMetricProvider(MetricProvider):
    """In-memory metric provider for testing"""
    
    def __init__(self):
        self._metrics: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def record(self, metric_name: str, value: float):
        """Record a metric value"""
        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = deque(maxlen=1000)
            self._metrics[metric_name].append({
                'value': value,
                'timestamp': datetime.now()
            })
    
    def get_metric(self, metric_name: str) -> Optional[float]:
        """Get latest metric value"""
        with self._lock:
            if metric_name in self._metrics and self._metrics[metric_name]:
                return self._metrics[metric_name][-1]['value']
            return None
    
    def get_metric_average(self, metric_name: str, seconds: int) -> Optional[float]:
        """Get average metric value over time period"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        
        with self._lock:
            if metric_name not in self._metrics:
                return None
            
            values = [
                m['value'] for m in self._metrics[metric_name]
                if m['timestamp'] > cutoff
            ]
            
            if not values:
                return None
            
            return sum(values) / len(values)


class ScalingExecutor(ABC):
    """Abstract scaling executor"""
    
    @abstractmethod
    def get_current_count(self) -> int:
        """Get current instance/resource count"""
        pass
    
    @abstractmethod
    def scale_to(self, count: int) -> bool:
        """Scale to specified count"""
        pass


class MockScalingExecutor(ScalingExecutor):
    """Mock scaling executor for testing"""
    
    def __init__(self, initial_count: int = 1):
        self._count = initial_count
        self._history: List[int] = [initial_count]
    
    def get_current_count(self) -> int:
        return self._count
    
    def scale_to(self, count: int) -> bool:
        old_count = self._count
        self._count = count
        self._history.append(count)
        logger.info(f"Scaled from {old_count} to {count}")
        return True
    
    def get_history(self) -> List[int]:
        return self._history


class AutoScaler:
    """
    Automatic resource scaler
    """
    
    def __init__(self,
                 config: ScalerConfig = None,
                 metric_provider: MetricProvider = None,
                 executor: ScalingExecutor = None):
        self.config = config or ScalerConfig()
        self.metrics = metric_provider or InMemoryMetricProvider()
        self.executor = executor or MockScalingExecutor()
        
        self._policies: Dict[str, ScalingPolicy] = {}
        self._status = ScalingStatus.IDLE
        self._last_scale_up: Optional[datetime] = None
        self._last_scale_down: Optional[datetime] = None
        self._events: List[ScalingEvent] = []
        self._breach_counts: Dict[str, int] = {}
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info("AutoScaler initialized")
    
    def add_policy(self, policy: ScalingPolicy):
        """Add a scaling policy"""
        self._policies[policy.name] = policy
        logger.info(f"Added scaling policy: {policy.name}")
    
    def remove_policy(self, name: str):
        """Remove a scaling policy"""
        if name in self._policies:
            del self._policies[name]
    
    def start(self):
        """Start auto scaling"""
        self._running = True
        self._thread = threading.Thread(target=self._scaling_loop, daemon=True)
        self._thread.start()
        logger.info("AutoScaler started")
    
    def stop(self):
        """Stop auto scaling"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10.0)
        logger.info("AutoScaler stopped")
    
    def _scaling_loop(self):
        """Main scaling loop"""
        while self._running:
            try:
                self.evaluate()
            except Exception as e:
                logger.error(f"Scaling error: {e}")
            
            time.sleep(self.config.check_interval)
    
    def evaluate(self) -> Optional[ScalingDirection]:
        """Evaluate scaling policies and take action"""
        with self._lock:
            # Check if in cooldown
            if self._is_in_cooldown():
                return ScalingDirection.NONE
            
            current_count = self.executor.get_current_count()
            
            # Evaluate each policy
            scale_up_triggered = False
            scale_down_triggered = False
            trigger_policy = None
            trigger_value = 0.0
            
            for name, policy in self._policies.items():
                direction = self._evaluate_policy(policy)
                
                if direction == ScalingDirection.UP:
                    scale_up_triggered = True
                    trigger_policy = policy
                    trigger_value = self.metrics.get_metric_average(
                        policy.metric, policy.period_seconds
                    ) or 0
                    
                elif direction == ScalingDirection.DOWN:
                    scale_down_triggered = True
                    if not trigger_policy:
                        trigger_policy = policy
                        trigger_value = self.metrics.get_metric_average(
                            policy.metric, policy.period_seconds
                        ) or 0
            
            # Scale up takes priority
            if scale_up_triggered and trigger_policy:
                new_count = min(
                    current_count + trigger_policy.scale_up_step,
                    trigger_policy.max_instances
                )
                
                if new_count > current_count:
                    self._perform_scaling(
                        ScalingDirection.UP,
                        current_count,
                        new_count,
                        trigger_policy,
                        trigger_value
                    )
                    return ScalingDirection.UP
            
            elif scale_down_triggered and trigger_policy:
                # Check stabilization window
                if self._last_scale_up:
                    time_since_scale_up = (datetime.now() - self._last_scale_up).total_seconds()
                    if time_since_scale_up < self.config.stabilization_window:
                        return ScalingDirection.NONE
                
                new_count = max(
                    current_count - trigger_policy.scale_down_step,
                    trigger_policy.min_instances
                )
                
                if new_count < current_count:
                    self._perform_scaling(
                        ScalingDirection.DOWN,
                        current_count,
                        new_count,
                        trigger_policy,
                        trigger_value
                    )
                    return ScalingDirection.DOWN
            
            return ScalingDirection.NONE
    
    def _evaluate_policy(self, policy: ScalingPolicy) -> ScalingDirection:
        """Evaluate a single policy"""
        avg = self.metrics.get_metric_average(policy.metric, policy.period_seconds)
        
        if avg is None:
            return ScalingDirection.NONE
        
        # Check breach counts for sustained conditions
        breach_key = f"{policy.name}:{policy.metric}"
        
        if avg >= policy.scale_up_threshold:
            self._breach_counts[breach_key] = self._breach_counts.get(breach_key, 0) + 1
            
            if self._breach_counts[breach_key] >= policy.evaluation_periods:
                return ScalingDirection.UP
                
        elif avg <= policy.scale_down_threshold:
            self._breach_counts[breach_key] = self._breach_counts.get(breach_key, 0) + 1
            
            if self._breach_counts[breach_key] >= policy.evaluation_periods:
                return ScalingDirection.DOWN
        else:
            # Reset breach count if not breaching
            self._breach_counts[breach_key] = 0
        
        return ScalingDirection.NONE
    
    def _perform_scaling(self, direction: ScalingDirection,
                        from_count: int, to_count: int,
                        policy: ScalingPolicy, value: float):
        """Perform scaling action"""
        self._status = ScalingStatus.SCALING_UP if direction == ScalingDirection.UP else ScalingStatus.SCALING_DOWN
        
        success = self.executor.scale_to(to_count)
        
        if success:
            if direction == ScalingDirection.UP:
                self._last_scale_up = datetime.now()
            else:
                self._last_scale_down = datetime.now()
            
            event = ScalingEvent(
                timestamp=datetime.now(),
                direction=direction,
                from_count=from_count,
                to_count=to_count,
                trigger_metric=policy.metric,
                trigger_value=value,
                reason=f"Policy '{policy.name}': {policy.metric} = {value:.2f}"
            )
            self._events.append(event)
            
            logger.info(f"Scaled {direction.value}: {from_count} -> {to_count} ({event.reason})")
        
        self._status = ScalingStatus.COOLDOWN if success else ScalingStatus.IDLE
        
        # Reset breach counts after scaling
        for key in list(self._breach_counts.keys()):
            if key.startswith(policy.name):
                self._breach_counts[key] = 0
    
    def _is_in_cooldown(self) -> bool:
        """Check if currently in cooldown period"""
        now = datetime.now()
        
        if self._last_scale_up:
            cooldown = self.config.default_cooldown
            if (now - self._last_scale_up).total_seconds() < cooldown:
                return True
        
        if self._last_scale_down:
            cooldown = self.config.default_cooldown
            if (now - self._last_scale_down).total_seconds() < cooldown:
                return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get scaler status"""
        with self._lock:
            return {
                'status': self._status.value,
                'current_count': self.executor.get_current_count(),
                'last_scale_up': self._last_scale_up.isoformat() if self._last_scale_up else None,
                'last_scale_down': self._last_scale_down.isoformat() if self._last_scale_down else None,
                'in_cooldown': self._is_in_cooldown(),
                'policies': list(self._policies.keys()),
                'breach_counts': dict(self._breach_counts)
            }
    
    def get_events(self, hours: int = 24) -> List[ScalingEvent]:
        """Get scaling events"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._lock:
            return [e for e in self._events if e.timestamp > cutoff]
    
    def force_scale(self, count: int, reason: str = "Manual"):
        """Force scaling to specific count"""
        with self._lock:
            current = self.executor.get_current_count()
            
            if count == current:
                return
            
            direction = ScalingDirection.UP if count > current else ScalingDirection.DOWN
            
            success = self.executor.scale_to(count)
            
            if success:
                event = ScalingEvent(
                    timestamp=datetime.now(),
                    direction=direction,
                    from_count=current,
                    to_count=count,
                    trigger_metric="manual",
                    trigger_value=0,
                    reason=reason
                )
                self._events.append(event)
                
                if direction == ScalingDirection.UP:
                    self._last_scale_up = datetime.now()
                else:
                    self._last_scale_down = datetime.now()
                
                logger.info(f"Manual scale {direction.value}: {current} -> {count}")


class PredictiveScaler:
    """
    Predictive auto scaler using historical patterns
    """
    
    def __init__(self, auto_scaler: AutoScaler,
                 history_hours: int = 168):  # 1 week
        self.auto_scaler = auto_scaler
        self.history_hours = history_hours
        
        self._patterns: Dict[int, Dict[int, float]] = {}  # day -> hour -> avg_count
        self._enabled = False
    
    def learn_patterns(self, events: List[ScalingEvent]):
        """Learn patterns from historical events"""
        # Group by day of week and hour
        for event in events:
            day = event.timestamp.weekday()
            hour = event.timestamp.hour
            
            if day not in self._patterns:
                self._patterns[day] = {}
            
            if hour not in self._patterns[day]:
                self._patterns[day][hour] = []
            
            self._patterns[day][hour].append(event.to_count)
        
        # Calculate averages
        for day in self._patterns:
            for hour in self._patterns[day]:
                values = self._patterns[day][hour]
                if isinstance(values, list):
                    self._patterns[day][hour] = sum(values) / len(values)
    
    def predict(self, ahead_hours: int = 1) -> Optional[int]:
        """Predict required capacity"""
        target = datetime.now() + timedelta(hours=ahead_hours)
        day = target.weekday()
        hour = target.hour
        
        if day in self._patterns and hour in self._patterns[day]:
            predicted = self._patterns[day][hour]
            return int(round(predicted))
        
        return None
    
    def enable_predictive_scaling(self):
        """Enable predictive scaling"""
        self._enabled = True
        logger.info("Predictive scaling enabled")
    
    def disable_predictive_scaling(self):
        """Disable predictive scaling"""
        self._enabled = False
        logger.info("Predictive scaling disabled")
    
    def pre_scale(self, ahead_hours: int = 1):
        """Pre-scale based on prediction"""
        if not self._enabled:
            return
        
        predicted = self.predict(ahead_hours)
        current = self.auto_scaler.executor.get_current_count()
        
        if predicted and predicted > current:
            logger.info(f"Predictive scaling: {current} -> {predicted}")
            self.auto_scaler.force_scale(
                predicted,
                reason=f"Predictive scaling for {ahead_hours}h ahead"
            )


class TargetTrackingScaler:
    """
    Target tracking auto scaler
    
    Maintains a target metric value by adjusting capacity
    """
    
    def __init__(self,
                 metric_provider: MetricProvider,
                 executor: ScalingExecutor,
                 target_metric: str,
                 target_value: float,
                 min_capacity: int = 1,
                 max_capacity: int = 10):
        self.metrics = metric_provider
        self.executor = executor
        self.target_metric = target_metric
        self.target_value = target_value
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self, check_interval: int = 60):
        """Start target tracking"""
        self._running = True
        self._check_interval = check_interval
        self._thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop target tracking"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
    
    def _tracking_loop(self):
        """Target tracking loop"""
        while self._running:
            try:
                self._adjust_capacity()
            except Exception as e:
                logger.error(f"Target tracking error: {e}")
            
            time.sleep(self._check_interval)
    
    def _adjust_capacity(self):
        """Adjust capacity to maintain target"""
        current_value = self.metrics.get_metric_average(self.target_metric, 60)
        
        if current_value is None:
            return
        
        current_capacity = self.executor.get_current_count()
        
        # Calculate required capacity
        # If metric is above target, scale up proportionally
        # If metric is below target, scale down proportionally
        
        ratio = current_value / self.target_value if self.target_value > 0 else 1.0
        
        if ratio > 1.1:  # 10% above target
            # Scale up
            new_capacity = min(
                int(current_capacity * ratio),
                self.max_capacity
            )
        elif ratio < 0.9:  # 10% below target
            # Scale down
            new_capacity = max(
                int(current_capacity * ratio),
                self.min_capacity
            )
        else:
            # Within tolerance
            return
        
        if new_capacity != current_capacity:
            self.executor.scale_to(new_capacity)
            logger.info(
                f"Target tracking: {current_capacity} -> {new_capacity} "
                f"(metric={current_value:.2f}, target={self.target_value})"
            )
