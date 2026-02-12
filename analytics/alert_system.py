"""
Alert System
Anomaly detection and alerting for analytics

Features:
- Threshold-based alerts
- Anomaly detection
- Multi-channel notifications
- Alert escalation
- Alert history and management
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'
    EMERGENCY = 'emergency'


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = 'active'
    ACKNOWLEDGED = 'acknowledged'
    RESOLVED = 'resolved'
    SUPPRESSED = 'suppressed'


class AlertChannel(Enum):
    """Notification channels"""
    EMAIL = 'email'
    SLACK = 'slack'
    WEBHOOK = 'webhook'
    SMS = 'sms'
    LOG = 'log'


@dataclass
class AlertRule:
    """Configuration for an alert rule"""
    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # 'gt', 'lt', 'eq', 'gte', 'lte', 'anomaly'
    threshold: float
    severity: AlertSeverity
    channels: List[AlertChannel] = field(default_factory=lambda: [AlertChannel.LOG])
    cooldown_minutes: int = 15  # Minimum time between alerts
    enabled: bool = True
    
    # Advanced options
    aggregation_window: int = 5  # Minutes to aggregate data
    min_occurrences: int = 1  # Minimum threshold breaches before alerting
    
    # State
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class Alert:
    """An individual alert instance"""
    id: str
    rule_id: str
    rule_name: str
    metric_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    value: float
    threshold: float
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'metric_name': self.metric_name,
            'severity': self.severity.value,
            'status': self.status.value,
            'message': self.message,
            'value': self.value,
            'threshold': self.threshold,
            'created_at': self.created_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolution_notes': self.resolution_notes,
            'metadata': self.metadata
        }


class AnomalyDetector:
    """
    Detects anomalies in metric data using statistical methods
    """
    
    def __init__(self, sensitivity: float = 2.0):
        """
        Args:
            sensitivity: Number of standard deviations for anomaly threshold
        """
        self.sensitivity = sensitivity
        self._baselines: Dict[str, Dict[str, float]] = {}
    
    def update_baseline(self, metric_name: str, values: List[float]) -> None:
        """Update the baseline statistics for a metric"""
        if not values:
            return
        
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = variance ** 0.5
        
        self._baselines[metric_name] = {
            'mean': mean,
            'std': std,
            'min': min(values),
            'max': max(values),
            'count': n
        }
    
    def is_anomaly(self, metric_name: str, value: float) -> tuple:
        """
        Check if a value is anomalous
        
        Returns:
            (is_anomaly: bool, z_score: float, direction: str)
        """
        if metric_name not in self._baselines:
            return False, 0.0, 'unknown'
        
        baseline = self._baselines[metric_name]
        mean = baseline['mean']
        std = baseline['std']
        
        if std == 0:
            return False, 0.0, 'flat'
        
        z_score = (value - mean) / std
        is_anomalous = abs(z_score) > self.sensitivity
        
        direction = 'high' if z_score > 0 else 'low'
        
        return is_anomalous, z_score, direction
    
    def detect_trend_anomaly(self, values: List[float], 
                            window: int = 5) -> tuple:
        """
        Detect if recent trend is anomalous
        
        Returns:
            (is_anomaly: bool, trend_change: float)
        """
        if len(values) < window * 2:
            return False, 0.0
        
        recent = values[-window:]
        previous = values[-window*2:-window]
        
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        
        if previous_avg == 0:
            return False, 0.0
        
        trend_change = (recent_avg - previous_avg) / previous_avg
        
        # More than 50% change is considered anomalous
        is_anomalous = abs(trend_change) > 0.5
        
        return is_anomalous, trend_change


class AlertManager:
    """
    Manages alert rules, detection, and notifications
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: List[Alert] = []
        self._handlers: Dict[AlertChannel, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._anomaly_detector = AnomalyDetector()
        
        # Default log handler
        self._handlers[AlertChannel.LOG] = self._log_handler
    
    # ==================== Rule Management ====================
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule"""
        with self._lock:
            self._rules[rule.id] = rule
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule"""
        with self._lock:
            if rule_id in self._rules:
                del self._rules[rule_id]
                return True
            return False
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a specific rule"""
        return self._rules.get(rule_id)
    
    def get_all_rules(self) -> List[AlertRule]:
        """Get all rules"""
        return list(self._rules.values())
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            return True
        return False
    
    # ==================== Handler Registration ====================
    
    def register_handler(self, channel: AlertChannel, 
                        handler: Callable[[Alert], bool]) -> None:
        """Register a notification handler for a channel"""
        self._handlers[channel] = handler
    
    def _log_handler(self, alert: Alert) -> bool:
        """Default log handler"""
        log_method = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.CRITICAL: logger.error,
            AlertSeverity.EMERGENCY: logger.critical
        }.get(alert.severity, logger.warning)
        
        log_method(f"ALERT [{alert.severity.value.upper()}]: {alert.message}")
        return True
    
    # ==================== Alert Checking ====================
    
    def check_metric(self, metric_name: str, value: float,
                    metadata: Dict[str, Any] = None) -> List[Alert]:
        """Check a metric value against all relevant rules"""
        triggered_alerts = []
        
        for rule in self._rules.values():
            if not rule.enabled or rule.metric_name != metric_name:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue
            
            # Check condition
            triggered = self._check_condition(rule, value)
            
            if triggered:
                alert = self._create_alert(rule, value, metadata)
                self._alerts.append(alert)
                triggered_alerts.append(alert)
                
                # Update rule state
                rule.last_triggered = datetime.utcnow()
                rule.trigger_count += 1
                
                # Send notifications
                self._notify(alert, rule.channels)
        
        return triggered_alerts
    
    def _check_condition(self, rule: AlertRule, value: float) -> bool:
        """Check if a value triggers a rule condition"""
        if rule.condition == 'gt':
            return value > rule.threshold
        elif rule.condition == 'lt':
            return value < rule.threshold
        elif rule.condition == 'gte':
            return value >= rule.threshold
        elif rule.condition == 'lte':
            return value <= rule.threshold
        elif rule.condition == 'eq':
            return abs(value - rule.threshold) < 0.001
        elif rule.condition == 'anomaly':
            is_anomaly, _, _ = self._anomaly_detector.is_anomaly(
                rule.metric_name, value
            )
            return is_anomaly
        return False
    
    def _create_alert(self, rule: AlertRule, value: float,
                     metadata: Dict[str, Any] = None) -> Alert:
        """Create an alert instance"""
        import uuid
        
        condition_text = {
            'gt': 'above',
            'lt': 'below',
            'gte': 'at or above',
            'lte': 'at or below',
            'eq': 'equal to',
            'anomaly': 'anomalous compared to'
        }.get(rule.condition, 'triggered at')
        
        message = (
            f"{rule.name}: {rule.metric_name} is {condition_text} "
            f"threshold ({value:.2f} vs {rule.threshold:.2f})"
        )
        
        return Alert(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            rule_name=rule.name,
            metric_name=rule.metric_name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=message,
            value=value,
            threshold=rule.threshold,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
    
    def _notify(self, alert: Alert, channels: List[AlertChannel]) -> None:
        """Send notifications through specified channels"""
        for channel in channels:
            if channel in self._handlers:
                try:
                    self._handlers[channel](alert)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    # ==================== Alert Management ====================
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return [a for a in self._alerts if a.status == AlertStatus.ACTIVE]
    
    def get_alerts(self, status: AlertStatus = None,
                  severity: AlertSeverity = None,
                  since: datetime = None,
                  limit: int = 100) -> List[Alert]:
        """Get alerts with optional filtering"""
        alerts = self._alerts
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if since:
            alerts = [a for a in alerts if a.created_at >= since]
        
        return alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: str, 
                         acknowledged_by: str = None) -> bool:
        """Acknowledge an alert"""
        for alert in self._alerts:
            if alert.id == alert_id and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                return True
        return False
    
    def resolve_alert(self, alert_id: str, 
                     resolution_notes: str = None) -> bool:
        """Resolve an alert"""
        for alert in self._alerts:
            if alert.id == alert_id and alert.status in [
                AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED
            ]:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.resolution_notes = resolution_notes
                return True
        return False
    
    def suppress_alert(self, alert_id: str) -> bool:
        """Suppress an alert"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.status = AlertStatus.SUPPRESSED
                return True
        return False
    
    # ==================== Monitoring Loop ====================
    
    def start_monitoring(self, check_interval: int = 60) -> None:
        """Start the background monitoring loop"""
        if self._running:
            return
        
        self._running = True
        self._check_interval = check_interval
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        logger.info("Alert monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring loop"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Alert monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                self._collect_and_check_metrics()
            except Exception as e:
                logger.exception(f"Error in monitoring loop: {e}")
            
            time.sleep(self._check_interval)
    
    def _collect_and_check_metrics(self) -> None:
        """Collect current metrics and check against rules"""
        from .system_health import SystemHealthMonitor
        from .metrics_collector import MetricsCollector
        
        # Check system health metrics
        monitor = SystemHealthMonitor()
        metrics = monitor.get_system_metrics()
        
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                self.check_metric(metric_name, value)
        
        # Check collected metrics
        collector = MetricsCollector()
        for metric_name in self._get_monitored_metrics():
            value = collector.get_gauge(metric_name)
            if value is not None:
                self.check_metric(metric_name, value)
    
    def _get_monitored_metrics(self) -> List[str]:
        """Get list of metrics being monitored by rules"""
        return list(set(rule.metric_name for rule in self._rules.values()))
    
    # ==================== Statistics ====================
    
    def get_alert_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get alert statistics"""
        since = datetime.utcnow() - timedelta(days=days)
        recent_alerts = [a for a in self._alerts if a.created_at >= since]
        
        by_severity = {}
        by_status = {}
        by_rule = {}
        
        for alert in recent_alerts:
            severity = alert.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            status = alert.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            rule_id = alert.rule_id
            by_rule[rule_id] = by_rule.get(rule_id, 0) + 1
        
        # Calculate MTTA (Mean Time To Acknowledge)
        acknowledged = [a for a in recent_alerts if a.acknowledged_at]
        if acknowledged:
            tta_seconds = [
                (a.acknowledged_at - a.created_at).total_seconds()
                for a in acknowledged
            ]
            mtta = sum(tta_seconds) / len(tta_seconds)
        else:
            mtta = None
        
        # Calculate MTTR (Mean Time To Resolve)
        resolved = [a for a in recent_alerts if a.resolved_at]
        if resolved:
            ttr_seconds = [
                (a.resolved_at - a.created_at).total_seconds()
                for a in resolved
            ]
            mttr = sum(ttr_seconds) / len(ttr_seconds)
        else:
            mttr = None
        
        return {
            'total_alerts': len(recent_alerts),
            'by_severity': by_severity,
            'by_status': by_status,
            'by_rule': by_rule,
            'mtta_seconds': mtta,
            'mttr_seconds': mttr,
            'active_count': len(self.get_active_alerts()),
            'period_days': days
        }


# ==================== Predefined Rules ====================

def create_cpu_alert_rule(threshold: float = 90,
                         severity: AlertSeverity = AlertSeverity.WARNING) -> AlertRule:
    """Create a CPU usage alert rule"""
    import uuid
    return AlertRule(
        id=str(uuid.uuid4()),
        name='High CPU Usage',
        description=f'Alert when CPU usage exceeds {threshold}%',
        metric_name='cpu_percent',
        condition='gt',
        threshold=threshold,
        severity=severity
    )


def create_memory_alert_rule(threshold: float = 85,
                            severity: AlertSeverity = AlertSeverity.WARNING) -> AlertRule:
    """Create a memory usage alert rule"""
    import uuid
    return AlertRule(
        id=str(uuid.uuid4()),
        name='High Memory Usage',
        description=f'Alert when memory usage exceeds {threshold}%',
        metric_name='memory_percent',
        condition='gt',
        threshold=threshold,
        severity=severity
    )


def create_error_rate_alert_rule(threshold: float = 5,
                                severity: AlertSeverity = AlertSeverity.CRITICAL) -> AlertRule:
    """Create an error rate alert rule"""
    import uuid
    return AlertRule(
        id=str(uuid.uuid4()),
        name='High Error Rate',
        description=f'Alert when error rate exceeds {threshold}%',
        metric_name='error_rate',
        condition='gt',
        threshold=threshold,
        severity=severity
    )


def create_response_time_alert_rule(threshold: float = 5000,
                                   severity: AlertSeverity = AlertSeverity.WARNING) -> AlertRule:
    """Create a response time alert rule"""
    import uuid
    return AlertRule(
        id=str(uuid.uuid4()),
        name='Slow Response Time',
        description=f'Alert when response time exceeds {threshold}ms',
        metric_name='response_time_ms',
        condition='gt',
        threshold=threshold,
        severity=severity
    )
