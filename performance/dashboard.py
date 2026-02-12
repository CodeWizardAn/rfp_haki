"""
Performance Dashboard

Real-time performance monitoring dashboard with:
- Metrics aggregation
- Real-time statistics
- Visualization data
- Historical trends
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution
    TIMER = "timer"  # Duration measurements


@dataclass
class MetricDefinition:
    """Definition of a metric"""
    name: str
    metric_type: MetricType
    description: str = ""
    unit: str = ""
    labels: List[str] = field(default_factory=list)


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    refresh_interval: float = 5.0  # Seconds
    history_retention: int = 3600  # Seconds of history to keep
    aggregation_windows: List[int] = field(default_factory=lambda: [60, 300, 900, 3600])


class MetricsRegistry:
    """
    Registry for metrics collection
    """
    
    def __init__(self):
        self._metrics: Dict[str, MetricDefinition] = {}
        self._values: Dict[str, deque] = {}
        self._lock = threading.Lock()
        self._retention = 3600  # 1 hour default
    
    def register(self, definition: MetricDefinition):
        """Register a metric"""
        with self._lock:
            self._metrics[definition.name] = definition
            self._values[definition.name] = deque(maxlen=10000)
    
    def record(self, name: str, value: float, 
               labels: Dict[str, str] = None):
        """Record a metric value"""
        with self._lock:
            if name not in self._values:
                # Auto-register as gauge
                self._metrics[name] = MetricDefinition(
                    name=name, metric_type=MetricType.GAUGE
                )
                self._values[name] = deque(maxlen=10000)
            
            self._values[name].append({
                'timestamp': datetime.now(),
                'value': value,
                'labels': labels or {}
            })
    
    def get_latest(self, name: str) -> Optional[float]:
        """Get latest value for a metric"""
        with self._lock:
            if name in self._values and self._values[name]:
                return self._values[name][-1]['value']
            return None
    
    def get_history(self, name: str, 
                   seconds: int = 60) -> List[Dict]:
        """Get metric history"""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        
        with self._lock:
            if name not in self._values:
                return []
            return [v for v in self._values[name] if v['timestamp'] > cutoff]
    
    def get_aggregated(self, name: str, 
                      window_seconds: int = 60) -> Dict[str, float]:
        """Get aggregated stats for a metric"""
        history = self.get_history(name, window_seconds)
        
        if not history:
            return {}
        
        values = [h['value'] for h in history]
        sorted_values = sorted(values)
        n = len(values)
        
        return {
            'count': n,
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / n,
            'sum': sum(values),
            'p50': sorted_values[int(n * 0.50)],
            'p90': sorted_values[int(n * 0.90)],
            'p99': sorted_values[int(n * 0.99)] if n > 0 else 0
        }
    
    def list_metrics(self) -> List[MetricDefinition]:
        """List all registered metrics"""
        with self._lock:
            return list(self._metrics.values())
    
    def cleanup(self, retention_seconds: int = None):
        """Remove old data"""
        retention = retention_seconds or self._retention
        cutoff = datetime.now() - timedelta(seconds=retention)
        
        with self._lock:
            for name in self._values:
                while self._values[name] and self._values[name][0]['timestamp'] < cutoff:
                    self._values[name].popleft()


class PerformanceDashboard:
    """
    Performance monitoring dashboard
    """
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
        
        self.registry = MetricsRegistry()
        self._panels: Dict[str, 'DashboardPanel'] = {}
        self._alerts: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Register default metrics
        self._register_default_metrics()
        
        logger.info("PerformanceDashboard initialized")
    
    def _register_default_metrics(self):
        """Register default metrics"""
        defaults = [
            MetricDefinition("requests_total", MetricType.COUNTER, "Total requests"),
            MetricDefinition("requests_per_second", MetricType.GAUGE, "Current RPS", "req/s"),
            MetricDefinition("response_time_ms", MetricType.HISTOGRAM, "Response time", "ms"),
            MetricDefinition("error_rate", MetricType.GAUGE, "Error rate", "%"),
            MetricDefinition("cpu_usage", MetricType.GAUGE, "CPU usage", "%"),
            MetricDefinition("memory_usage", MetricType.GAUGE, "Memory usage", "%"),
            MetricDefinition("active_connections", MetricType.GAUGE, "Active connections"),
            MetricDefinition("queue_depth", MetricType.GAUGE, "Queue depth"),
        ]
        
        for metric in defaults:
            self.registry.register(metric)
    
    def add_panel(self, panel: 'DashboardPanel'):
        """Add a dashboard panel"""
        with self._lock:
            self._panels[panel.id] = panel
    
    def remove_panel(self, panel_id: str):
        """Remove a panel"""
        with self._lock:
            if panel_id in self._panels:
                del self._panels[panel_id]
    
    def record(self, metric: str, value: float, 
              labels: Dict[str, str] = None):
        """Record a metric value"""
        self.registry.record(metric, value, labels)
    
    def start(self):
        """Start dashboard refresh"""
        self._running = True
        self._thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._thread.start()
        logger.info("Dashboard started")
    
    def stop(self):
        """Stop dashboard"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Dashboard stopped")
    
    def _refresh_loop(self):
        """Background refresh loop"""
        while self._running:
            try:
                self._refresh_panels()
                self.registry.cleanup(self.config.history_retention)
            except Exception as e:
                logger.error(f"Dashboard refresh error: {e}")
            
            time.sleep(self.config.refresh_interval)
    
    def _refresh_panels(self):
        """Refresh all panels"""
        with self._lock:
            for panel in self._panels.values():
                try:
                    panel.refresh(self.registry)
                except Exception as e:
                    logger.error(f"Panel {panel.id} refresh error: {e}")
    
    def get_overview(self) -> Dict[str, Any]:
        """Get dashboard overview"""
        return {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'requests_per_second': self.registry.get_latest('requests_per_second') or 0,
                'response_time': self.registry.get_aggregated('response_time_ms', 60),
                'error_rate': self.registry.get_latest('error_rate') or 0,
                'cpu_usage': self.registry.get_latest('cpu_usage') or 0,
                'memory_usage': self.registry.get_latest('memory_usage') or 0
            },
            'alerts': self._alerts[-10:],
            'health': self._calculate_health()
        }
    
    def _calculate_health(self) -> str:
        """Calculate overall system health"""
        cpu = self.registry.get_latest('cpu_usage') or 0
        memory = self.registry.get_latest('memory_usage') or 0
        error_rate = self.registry.get_latest('error_rate') or 0
        
        if error_rate > 0.1 or cpu > 90 or memory > 90:
            return 'critical'
        elif error_rate > 0.05 or cpu > 70 or memory > 70:
            return 'warning'
        else:
            return 'healthy'
    
    def get_panel_data(self, panel_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific panel"""
        with self._lock:
            if panel_id in self._panels:
                return self._panels[panel_id].get_data()
            return None
    
    def get_time_series(self, metric: str, 
                       window: int = 3600) -> List[Dict]:
        """Get time series data for graphing"""
        history = self.registry.get_history(metric, window)
        
        # Downsample if too many points
        max_points = 360
        if len(history) > max_points:
            step = len(history) // max_points
            history = history[::step]
        
        return [
            {
                'timestamp': h['timestamp'].isoformat(),
                'value': h['value']
            }
            for h in history
        ]
    
    def get_comparison(self, metric: str) -> Dict[str, Any]:
        """Get metric comparison across time windows"""
        result = {}
        
        for window in self.config.aggregation_windows:
            result[f'{window}s'] = self.registry.get_aggregated(metric, window)
        
        return result
    
    def add_alert(self, level: str, message: str):
        """Add an alert"""
        self._alerts.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        })
        
        # Keep last 100 alerts
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]
    
    def export_data(self, format: str = 'json') -> Any:
        """Export dashboard data"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'panels': {}
        }
        
        # Export all metrics
        for metric in self.registry.list_metrics():
            data['metrics'][metric.name] = {
                'latest': self.registry.get_latest(metric.name),
                'aggregated': self.registry.get_aggregated(metric.name, 3600),
                'history': self.get_time_series(metric.name, 3600)
            }
        
        # Export panel data
        with self._lock:
            for panel_id, panel in self._panels.items():
                data['panels'][panel_id] = panel.get_data()
        
        return data


@dataclass
class DashboardPanel:
    """Dashboard panel configuration"""
    id: str
    title: str
    panel_type: str  # 'chart', 'gauge', 'stat', 'table'
    metrics: List[str]
    options: Dict[str, Any] = field(default_factory=dict)
    
    _data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    def refresh(self, registry: MetricsRegistry):
        """Refresh panel data"""
        self._data = {
            'id': self.id,
            'title': self.title,
            'type': self.panel_type,
            'updated': datetime.now().isoformat(),
            'data': {}
        }
        
        for metric in self.metrics:
            if self.panel_type == 'chart':
                # Get time series data
                self._data['data'][metric] = [
                    {'x': h['timestamp'].isoformat(), 'y': h['value']}
                    for h in registry.get_history(metric, self.options.get('window', 300))
                ]
            elif self.panel_type == 'gauge':
                self._data['data'][metric] = registry.get_latest(metric) or 0
            elif self.panel_type == 'stat':
                self._data['data'][metric] = registry.get_aggregated(
                    metric, self.options.get('window', 60)
                )
            else:
                self._data['data'][metric] = registry.get_latest(metric)
    
    def get_data(self) -> Dict[str, Any]:
        """Get current panel data"""
        return self._data


class DashboardBuilder:
    """
    Builder for creating dashboards
    """
    
    def __init__(self, name: str):
        self.name = name
        self._config = DashboardConfig()
        self._panels: List[DashboardPanel] = []
    
    def with_config(self, config: DashboardConfig) -> 'DashboardBuilder':
        """Set dashboard configuration"""
        self._config = config
        return self
    
    def add_chart(self, id: str, title: str, 
                 metrics: List[str], window: int = 300) -> 'DashboardBuilder':
        """Add a chart panel"""
        self._panels.append(DashboardPanel(
            id=id,
            title=title,
            panel_type='chart',
            metrics=metrics,
            options={'window': window}
        ))
        return self
    
    def add_gauge(self, id: str, title: str, 
                 metric: str, max_value: float = 100) -> 'DashboardBuilder':
        """Add a gauge panel"""
        self._panels.append(DashboardPanel(
            id=id,
            title=title,
            panel_type='gauge',
            metrics=[metric],
            options={'max': max_value}
        ))
        return self
    
    def add_stat(self, id: str, title: str, 
                metric: str, window: int = 60) -> 'DashboardBuilder':
        """Add a stat panel"""
        self._panels.append(DashboardPanel(
            id=id,
            title=title,
            panel_type='stat',
            metrics=[metric],
            options={'window': window}
        ))
        return self
    
    def build(self) -> PerformanceDashboard:
        """Build the dashboard"""
        dashboard = PerformanceDashboard(self._config)
        
        for panel in self._panels:
            dashboard.add_panel(panel)
        
        return dashboard


def create_default_dashboard() -> PerformanceDashboard:
    """Create a default performance dashboard"""
    return DashboardBuilder("Performance Dashboard") \
        .add_chart("rps_chart", "Requests/Second", ["requests_per_second"]) \
        .add_chart("latency_chart", "Response Time", ["response_time_ms"]) \
        .add_gauge("cpu_gauge", "CPU Usage", "cpu_usage") \
        .add_gauge("memory_gauge", "Memory Usage", "memory_usage") \
        .add_stat("error_stat", "Error Rate", "error_rate") \
        .add_stat("connections_stat", "Connections", "active_connections") \
        .build()


class RealTimeStream:
    """
    Real-time metric streaming
    """
    
    def __init__(self, dashboard: PerformanceDashboard):
        self.dashboard = dashboard
        self._subscribers: List[Callable[[Dict], None]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def subscribe(self, callback: Callable[[Dict], None]):
        """Subscribe to real-time updates"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from updates"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def start(self, interval: float = 1.0):
        """Start streaming"""
        self._running = True
        self._interval = interval
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop streaming"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
    
    def _stream_loop(self):
        """Streaming loop"""
        while self._running:
            try:
                data = self.dashboard.get_overview()
                
                for callback in self._subscribers:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"Stream callback error: {e}")
                        
            except Exception as e:
                logger.error(f"Stream error: {e}")
            
            time.sleep(self._interval)


class AlertManager:
    """
    Manages performance alerts
    """
    
    def __init__(self, dashboard: PerformanceDashboard):
        self.dashboard = dashboard
        self._rules: List[Dict[str, Any]] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def add_rule(self, name: str, metric: str, 
                condition: str, threshold: float,
                severity: str = 'warning'):
        """
        Add an alert rule
        
        Args:
            name: Rule name
            metric: Metric to monitor
            condition: 'gt', 'lt', 'gte', 'lte', 'eq'
            threshold: Threshold value
            severity: Alert severity
        """
        self._rules.append({
            'name': name,
            'metric': metric,
            'condition': condition,
            'threshold': threshold,
            'severity': severity,
            'triggered': False
        })
    
    def start(self, check_interval: float = 10.0):
        """Start alert monitoring"""
        self._running = True
        self._interval = check_interval
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
    
    def _check_loop(self):
        """Alert checking loop"""
        while self._running:
            try:
                self._check_rules()
            except Exception as e:
                logger.error(f"Alert check error: {e}")
            
            time.sleep(self._interval)
    
    def _check_rules(self):
        """Check all alert rules"""
        for rule in self._rules:
            value = self.dashboard.registry.get_latest(rule['metric'])
            
            if value is None:
                continue
            
            triggered = self._evaluate_condition(
                value, rule['condition'], rule['threshold']
            )
            
            if triggered and not rule['triggered']:
                # New alert
                rule['triggered'] = True
                self.dashboard.add_alert(
                    rule['severity'],
                    f"{rule['name']}: {rule['metric']} {rule['condition']} {rule['threshold']} (current: {value:.2f})"
                )
                logger.warning(f"Alert triggered: {rule['name']}")
                
            elif not triggered and rule['triggered']:
                # Alert cleared
                rule['triggered'] = False
                logger.info(f"Alert cleared: {rule['name']}")
    
    def _evaluate_condition(self, value: float, 
                           condition: str, threshold: float) -> bool:
        """Evaluate a condition"""
        if condition == 'gt':
            return value > threshold
        elif condition == 'lt':
            return value < threshold
        elif condition == 'gte':
            return value >= threshold
        elif condition == 'lte':
            return value <= threshold
        elif condition == 'eq':
            return value == threshold
        return False
