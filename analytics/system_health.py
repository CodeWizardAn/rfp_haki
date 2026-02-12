"""
System Health Monitor
Monitors overall system health and resource usage

Features:
- CPU, memory, disk monitoring
- Database connection monitoring
- API health checks
- Custom health check registration
- Alert triggering
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import deque
import logging
import platform

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from sqlalchemy.orm import Session
from sqlalchemy import func, text

from .models import SystemHealthMetric
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class HealthCheck:
    """Individual health check definition"""
    
    def __init__(self, name: str, check_fn: Callable[[], Dict[str, Any]],
                 timeout: float = 5.0, critical: bool = True):
        self.name = name
        self.check_fn = check_fn
        self.timeout = timeout
        self.critical = critical
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_check: Optional[datetime] = None
    
    def run(self) -> Dict[str, Any]:
        """Run the health check"""
        start = time.time()
        try:
            result = self.check_fn()
            duration = (time.time() - start) * 1000
            
            self.last_result = {
                'status': 'healthy' if result.get('healthy', True) else 'unhealthy',
                'duration_ms': duration,
                'details': result,
                'error': None
            }
        except Exception as e:
            self.last_result = {
                'status': 'unhealthy',
                'duration_ms': (time.time() - start) * 1000,
                'details': {},
                'error': str(e)
            }
        
        self.last_check = datetime.utcnow()
        return self.last_result


class SystemHealthMonitor:
    """
    Comprehensive system health monitoring
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.collector = MetricsCollector()
        
        # Health checks registry
        self._health_checks: Dict[str, HealthCheck] = {}
        
        # Historical data for trend analysis
        self._history: Dict[str, deque] = {
            'cpu': deque(maxlen=60),
            'memory': deque(maxlen=60),
            'disk': deque(maxlen=60)
        }
        
        # Thresholds for alerts
        self._thresholds = {
            'cpu_warning': 70,
            'cpu_critical': 90,
            'memory_warning': 75,
            'memory_critical': 90,
            'disk_warning': 80,
            'disk_critical': 95
        }
        
        # Monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = 60  # seconds
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        # System resources check
        if PSUTIL_AVAILABLE:
            self.register_check('system_resources', self._check_system_resources)
        
        # Database check (if session factory available)
        if self.session_factory:
            self.register_check('database', self._check_database)
    
    def register_check(self, name: str, check_fn: Callable[[], Dict[str, Any]],
                      timeout: float = 5.0, critical: bool = True):
        """Register a custom health check"""
        self._health_checks[name] = HealthCheck(name, check_fn, timeout, critical)
    
    def set_threshold(self, metric: str, warning: float = None, critical: float = None):
        """Set alert thresholds"""
        if warning is not None:
            self._thresholds[f'{metric}_warning'] = warning
        if critical is not None:
            self._thresholds[f'{metric}_critical'] = critical
    
    # ==================== System Metrics ====================
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'platform': platform.system(),
            'python_version': platform.python_version()
        }
        
        if PSUTIL_AVAILABLE:
            # CPU
            metrics['cpu'] = {
                'usage_percent': psutil.cpu_percent(interval=0.1),
                'load_1m': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None,
                'load_5m': psutil.getloadavg()[1] if hasattr(psutil, 'getloadavg') else None,
                'load_15m': psutil.getloadavg()[2] if hasattr(psutil, 'getloadavg') else None,
                'core_count': psutil.cpu_count()
            }
            
            # Memory
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            metrics['memory'] = {
                'total_mb': mem.total / (1024 * 1024),
                'available_mb': mem.available / (1024 * 1024),
                'used_mb': mem.used / (1024 * 1024),
                'percent': mem.percent,
                'swap_used_mb': swap.used / (1024 * 1024),
                'swap_percent': swap.percent
            }
            
            # Disk
            disk = psutil.disk_usage('/')
            metrics['disk'] = {
                'total_gb': disk.total / (1024 * 1024 * 1024),
                'used_gb': disk.used / (1024 * 1024 * 1024),
                'free_gb': disk.free / (1024 * 1024 * 1024),
                'percent': disk.percent
            }
            
            # Network
            net = psutil.net_io_counters()
            metrics['network'] = {
                'bytes_sent': net.bytes_sent,
                'bytes_recv': net.bytes_recv,
                'packets_sent': net.packets_sent,
                'packets_recv': net.packets_recv
            }
            
            # Process info
            process = psutil.Process()
            metrics['process'] = {
                'memory_mb': process.memory_info().rss / (1024 * 1024),
                'cpu_percent': process.cpu_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files())
            }
        
        return metrics
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Health check for system resources"""
        if not PSUTIL_AVAILABLE:
            return {'healthy': True, 'message': 'psutil not available'}
        
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        issues = []
        
        if cpu > self._thresholds['cpu_critical']:
            issues.append(f'CPU critical: {cpu}%')
        elif cpu > self._thresholds['cpu_warning']:
            issues.append(f'CPU warning: {cpu}%')
        
        if mem > self._thresholds['memory_critical']:
            issues.append(f'Memory critical: {mem}%')
        elif mem > self._thresholds['memory_warning']:
            issues.append(f'Memory warning: {mem}%')
        
        if disk > self._thresholds['disk_critical']:
            issues.append(f'Disk critical: {disk}%')
        elif disk > self._thresholds['disk_warning']:
            issues.append(f'Disk warning: {disk}%')
        
        return {
            'healthy': len([i for i in issues if 'critical' in i]) == 0,
            'cpu_percent': cpu,
            'memory_percent': mem,
            'disk_percent': disk,
            'issues': issues
        }
    
    def _check_database(self) -> Dict[str, Any]:
        """Health check for database connectivity"""
        try:
            session = self.session_factory()
            start = time.time()
            session.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000
            session.close()
            
            return {
                'healthy': True,
                'latency_ms': latency,
                'message': 'Database connection successful'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    # ==================== Health Checks ====================
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_healthy = True
        
        for name, check in self._health_checks.items():
            result = check.run()
            results[name] = result
            
            if result['status'] != 'healthy' and check.critical:
                overall_healthy = False
        
        return {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': results
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        checks = self.run_all_checks()
        metrics = self.get_system_metrics()
        
        # Determine overall status
        status = 'healthy'
        if checks['status'] != 'healthy':
            status = 'unhealthy'
        elif PSUTIL_AVAILABLE:
            cpu = metrics.get('cpu', {}).get('usage_percent', 0)
            mem = metrics.get('memory', {}).get('percent', 0)
            
            if cpu > self._thresholds['cpu_warning'] or mem > self._thresholds['memory_warning']:
                status = 'degraded'
        
        return {
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'health_checks': checks,
            'system_metrics': metrics,
            'thresholds': self._thresholds
        }
    
    # ==================== Monitoring ====================
    
    def start_monitoring(self, interval: int = 60):
        """Start background monitoring"""
        if self._monitoring:
            return
        
        self._monitor_interval = interval
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Started health monitoring with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Stopped health monitoring")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                self._collect_and_store_metrics()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(self._monitor_interval)
    
    def _collect_and_store_metrics(self):
        """Collect and store health metrics"""
        metrics = self.get_system_metrics()
        health = self.run_all_checks()
        
        # Update history
        if PSUTIL_AVAILABLE:
            self._history['cpu'].append(metrics.get('cpu', {}).get('usage_percent', 0))
            self._history['memory'].append(metrics.get('memory', {}).get('percent', 0))
            self._history['disk'].append(metrics.get('disk', {}).get('percent', 0))
        
        # Record to collector
        if PSUTIL_AVAILABLE:
            self.collector.gauge('system.cpu.usage', metrics.get('cpu', {}).get('usage_percent', 0))
            self.collector.gauge('system.memory.percent', metrics.get('memory', {}).get('percent', 0))
            self.collector.gauge('system.disk.percent', metrics.get('disk', {}).get('percent', 0))
        
        # Store to database
        if self.session_factory:
            self._store_health_metric(metrics, health)
    
    def _store_health_metric(self, metrics: Dict[str, Any], health: Dict[str, Any]):
        """Store health metric to database"""
        session = self.session_factory()
        try:
            metric = SystemHealthMetric(
                component='system',
                cpu_usage_percent=metrics.get('cpu', {}).get('usage_percent'),
                cpu_load_1m=metrics.get('cpu', {}).get('load_1m'),
                cpu_load_5m=metrics.get('cpu', {}).get('load_5m'),
                cpu_load_15m=metrics.get('cpu', {}).get('load_15m'),
                memory_used_mb=metrics.get('memory', {}).get('used_mb'),
                memory_available_mb=metrics.get('memory', {}).get('available_mb'),
                memory_percent=metrics.get('memory', {}).get('percent'),
                disk_used_gb=metrics.get('disk', {}).get('used_gb'),
                disk_available_gb=metrics.get('disk', {}).get('free_gb'),
                disk_percent=metrics.get('disk', {}).get('percent'),
                network_bytes_sent=metrics.get('network', {}).get('bytes_sent'),
                network_bytes_recv=metrics.get('network', {}).get('bytes_recv'),
                health_status=health['status'],
                health_checks=health['checks'],
                recorded_at=datetime.utcnow()
            )
            session.add(metric)
            session.commit()
        finally:
            session.close()
    
    # ==================== Analysis ====================
    
    def get_health_history(self, session: Session,
                          component: str = 'system',
                          hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for a component"""
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        records = session.query(SystemHealthMetric).filter(
            SystemHealthMetric.component == component,
            SystemHealthMetric.recorded_at >= start_date
        ).order_by(SystemHealthMetric.recorded_at).all()
        
        return [
            {
                'timestamp': r.recorded_at.isoformat(),
                'cpu_percent': r.cpu_usage_percent,
                'memory_percent': r.memory_percent,
                'disk_percent': r.disk_percent,
                'health_status': r.health_status
            }
            for r in records
        ]
    
    def get_resource_trends(self, session: Session,
                           hours: int = 24,
                           metric: str = 'cpu') -> Dict[str, Any]:
        """Get resource usage trends"""
        start_date = datetime.utcnow() - timedelta(hours=hours)
        
        if metric == 'cpu':
            col = SystemHealthMetric.cpu_usage_percent
        elif metric == 'memory':
            col = SystemHealthMetric.memory_percent
        elif metric == 'disk':
            col = SystemHealthMetric.disk_percent
        else:
            col = SystemHealthMetric.cpu_usage_percent
        
        stats = session.query(
            func.avg(col).label('avg'),
            func.min(col).label('min'),
            func.max(col).label('max'),
            func.stddev(col).label('stddev')
        ).filter(
            SystemHealthMetric.recorded_at >= start_date
        ).first()
        
        return {
            'metric': metric,
            'period_hours': hours,
            'average': float(stats.avg or 0),
            'minimum': float(stats.min or 0),
            'maximum': float(stats.max or 0),
            'std_deviation': float(stats.stddev or 0)
        }
    
    def get_uptime_stats(self, session: Session, days: int = 30) -> Dict[str, Any]:
        """Calculate uptime statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total = session.query(func.count(SystemHealthMetric.id)).filter(
            SystemHealthMetric.recorded_at >= start_date
        ).scalar() or 0
        
        healthy = session.query(func.count(SystemHealthMetric.id)).filter(
            SystemHealthMetric.recorded_at >= start_date,
            SystemHealthMetric.health_status == 'healthy'
        ).scalar() or 0
        
        degraded = session.query(func.count(SystemHealthMetric.id)).filter(
            SystemHealthMetric.recorded_at >= start_date,
            SystemHealthMetric.health_status == 'degraded'
        ).scalar() or 0
        
        unhealthy = session.query(func.count(SystemHealthMetric.id)).filter(
            SystemHealthMetric.recorded_at >= start_date,
            SystemHealthMetric.health_status == 'unhealthy'
        ).scalar() or 0
        
        uptime = healthy / total if total > 0 else 1.0
        
        return {
            'period_days': days,
            'total_checks': total,
            'healthy_count': healthy,
            'degraded_count': degraded,
            'unhealthy_count': unhealthy,
            'uptime_percentage': uptime * 100,
            'availability': uptime
        }
    
    def get_health_report(self, session: Session = None) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        current = self.get_health_status()
        
        report = {
            'current_status': current,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if session:
            report['history_24h'] = self.get_health_history(session, hours=24)
            report['cpu_trend'] = self.get_resource_trends(session, hours=24, metric='cpu')
            report['memory_trend'] = self.get_resource_trends(session, hours=24, metric='memory')
            report['uptime'] = self.get_uptime_stats(session, days=30)
        
        return report
