"""
Resource Monitor

System resource monitoring with:
- CPU usage tracking
- Memory monitoring
- Disk I/O metrics
- Network statistics
- Alerts and thresholds
"""

import logging
import threading
import time
import os
import platform
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import psutil for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, using limited resource monitoring")


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceAlert:
    """Resource alert"""
    timestamp: datetime
    resource: str
    level: AlertLevel
    message: str
    value: float
    threshold: float


@dataclass
class CPUMetrics:
    """CPU metrics"""
    usage_percent: float
    per_core_percent: List[float]
    load_avg_1m: float
    load_avg_5m: float
    load_avg_15m: float
    context_switches: int = 0
    interrupts: int = 0


@dataclass
class MemoryMetrics:
    """Memory metrics"""
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0
    swap_percent: float = 0.0


@dataclass
class DiskMetrics:
    """Disk metrics"""
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    read_bytes_per_sec: float = 0.0
    write_bytes_per_sec: float = 0.0
    read_count_per_sec: float = 0.0
    write_count_per_sec: float = 0.0


@dataclass
class NetworkMetrics:
    """Network metrics"""
    bytes_sent_per_sec: float
    bytes_recv_per_sec: float
    packets_sent_per_sec: float
    packets_recv_per_sec: float
    errors_in: int = 0
    errors_out: int = 0
    drops_in: int = 0
    drops_out: int = 0


@dataclass
class ProcessMetrics:
    """Process metrics"""
    pid: int
    cpu_percent: float
    memory_percent: float
    memory_bytes: int
    num_threads: int
    num_fds: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0


@dataclass
class SystemSnapshot:
    """Complete system snapshot"""
    timestamp: datetime
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: List[DiskMetrics]
    network: NetworkMetrics
    process: Optional[ProcessMetrics] = None


@dataclass
class MonitorConfig:
    """Resource monitor configuration"""
    interval: float = 5.0  # Seconds between samples
    history_size: int = 720  # 1 hour at 5s interval
    
    # Thresholds
    cpu_warning: float = 70.0
    cpu_critical: float = 90.0
    memory_warning: float = 70.0
    memory_critical: float = 90.0
    disk_warning: float = 80.0
    disk_critical: float = 95.0
    
    # Disk paths to monitor
    disk_paths: List[str] = field(default_factory=lambda: ["/"])


class ResourceMonitor:
    """
    System resource monitor
    """
    
    def __init__(self, config: MonitorConfig = None):
        self.config = config or MonitorConfig()
        
        self._history: deque = deque(maxlen=self.config.history_size)
        self._alerts: List[ResourceAlert] = []
        self._alert_callbacks: List[Callable[[ResourceAlert], None]] = []
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Previous values for rate calculations
        self._prev_disk_io: Dict[str, Dict] = {}
        self._prev_net_io: Dict = {}
        self._prev_sample_time: float = 0
        
        logger.info(f"ResourceMonitor initialized: interval={self.config.interval}s")
    
    def start(self):
        """Start monitoring"""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("ResourceMonitor started")
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10.0)
        logger.info("ResourceMonitor stopped")
    
    def on_alert(self, callback: Callable[[ResourceAlert], None]):
        """Register alert callback"""
        self._alert_callbacks.append(callback)
    
    def _monitor_loop(self):
        """Monitoring loop"""
        while self._running:
            try:
                snapshot = self.collect_metrics()
                
                with self._lock:
                    self._history.append(snapshot)
                
                self._check_thresholds(snapshot)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            time.sleep(self.config.interval)
    
    def collect_metrics(self) -> SystemSnapshot:
        """Collect current system metrics"""
        now = time.time()
        elapsed = now - self._prev_sample_time if self._prev_sample_time > 0 else 1.0
        self._prev_sample_time = now
        
        cpu = self._collect_cpu()
        memory = self._collect_memory()
        disks = self._collect_disk(elapsed)
        network = self._collect_network(elapsed)
        process = self._collect_process()
        
        return SystemSnapshot(
            timestamp=datetime.now(),
            cpu=cpu,
            memory=memory,
            disks=disks,
            network=network,
            process=process
        )
    
    def _collect_cpu(self) -> CPUMetrics:
        """Collect CPU metrics"""
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=None)
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            
            if hasattr(os, 'getloadavg'):
                load = os.getloadavg()
            else:
                load = (0.0, 0.0, 0.0)
            
            cpu_times = psutil.cpu_stats()
            
            return CPUMetrics(
                usage_percent=cpu_percent,
                per_core_percent=per_core,
                load_avg_1m=load[0],
                load_avg_5m=load[1],
                load_avg_15m=load[2],
                context_switches=cpu_times.ctx_switches if cpu_times else 0,
                interrupts=cpu_times.interrupts if cpu_times else 0
            )
        else:
            return CPUMetrics(
                usage_percent=0.0,
                per_core_percent=[],
                load_avg_1m=0.0,
                load_avg_5m=0.0,
                load_avg_15m=0.0
            )
    
    def _collect_memory(self) -> MemoryMetrics:
        """Collect memory metrics"""
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return MemoryMetrics(
                total_bytes=mem.total,
                available_bytes=mem.available,
                used_bytes=mem.used,
                usage_percent=mem.percent,
                swap_total_bytes=swap.total,
                swap_used_bytes=swap.used,
                swap_percent=swap.percent
            )
        else:
            return MemoryMetrics(
                total_bytes=0,
                available_bytes=0,
                used_bytes=0,
                usage_percent=0.0
            )
    
    def _collect_disk(self, elapsed: float) -> List[DiskMetrics]:
        """Collect disk metrics"""
        disks = []
        
        if PSUTIL_AVAILABLE:
            # Disk usage
            for path in self.config.disk_paths:
                try:
                    usage = psutil.disk_usage(path)
                    
                    disk_metric = DiskMetrics(
                        path=path,
                        total_bytes=usage.total,
                        used_bytes=usage.used,
                        free_bytes=usage.free,
                        usage_percent=usage.percent
                    )
                    
                    disks.append(disk_metric)
                except Exception:
                    pass
            
            # Disk I/O rates
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io and self._prev_disk_io:
                    for disk in disks:
                        disk.read_bytes_per_sec = (disk_io.read_bytes - self._prev_disk_io.get('read_bytes', 0)) / elapsed
                        disk.write_bytes_per_sec = (disk_io.write_bytes - self._prev_disk_io.get('write_bytes', 0)) / elapsed
                        disk.read_count_per_sec = (disk_io.read_count - self._prev_disk_io.get('read_count', 0)) / elapsed
                        disk.write_count_per_sec = (disk_io.write_count - self._prev_disk_io.get('write_count', 0)) / elapsed
                
                if disk_io:
                    self._prev_disk_io = {
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count
                    }
            except Exception:
                pass
        
        return disks
    
    def _collect_network(self, elapsed: float) -> NetworkMetrics:
        """Collect network metrics"""
        if PSUTIL_AVAILABLE:
            try:
                net_io = psutil.net_io_counters()
                
                bytes_sent_per_sec = 0.0
                bytes_recv_per_sec = 0.0
                packets_sent_per_sec = 0.0
                packets_recv_per_sec = 0.0
                
                if self._prev_net_io:
                    bytes_sent_per_sec = (net_io.bytes_sent - self._prev_net_io.get('bytes_sent', 0)) / elapsed
                    bytes_recv_per_sec = (net_io.bytes_recv - self._prev_net_io.get('bytes_recv', 0)) / elapsed
                    packets_sent_per_sec = (net_io.packets_sent - self._prev_net_io.get('packets_sent', 0)) / elapsed
                    packets_recv_per_sec = (net_io.packets_recv - self._prev_net_io.get('packets_recv', 0)) / elapsed
                
                self._prev_net_io = {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                }
                
                return NetworkMetrics(
                    bytes_sent_per_sec=bytes_sent_per_sec,
                    bytes_recv_per_sec=bytes_recv_per_sec,
                    packets_sent_per_sec=packets_sent_per_sec,
                    packets_recv_per_sec=packets_recv_per_sec,
                    errors_in=net_io.errin,
                    errors_out=net_io.errout,
                    drops_in=net_io.dropin,
                    drops_out=net_io.dropout
                )
            except Exception:
                pass
        
        return NetworkMetrics(
            bytes_sent_per_sec=0.0,
            bytes_recv_per_sec=0.0,
            packets_sent_per_sec=0.0,
            packets_recv_per_sec=0.0
        )
    
    def _collect_process(self) -> Optional[ProcessMetrics]:
        """Collect current process metrics"""
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                
                io_counters = process.io_counters() if hasattr(process, 'io_counters') else None
                
                return ProcessMetrics(
                    pid=process.pid,
                    cpu_percent=process.cpu_percent(),
                    memory_percent=process.memory_percent(),
                    memory_bytes=process.memory_info().rss,
                    num_threads=process.num_threads(),
                    num_fds=process.num_fds() if hasattr(process, 'num_fds') else 0,
                    io_read_bytes=io_counters.read_bytes if io_counters else 0,
                    io_write_bytes=io_counters.write_bytes if io_counters else 0
                )
            except Exception:
                pass
        
        return None
    
    def _check_thresholds(self, snapshot: SystemSnapshot):
        """Check thresholds and generate alerts"""
        # CPU
        if snapshot.cpu.usage_percent >= self.config.cpu_critical:
            self._alert(ResourceAlert(
                timestamp=datetime.now(),
                resource="cpu",
                level=AlertLevel.CRITICAL,
                message=f"CPU usage critical: {snapshot.cpu.usage_percent:.1f}%",
                value=snapshot.cpu.usage_percent,
                threshold=self.config.cpu_critical
            ))
        elif snapshot.cpu.usage_percent >= self.config.cpu_warning:
            self._alert(ResourceAlert(
                timestamp=datetime.now(),
                resource="cpu",
                level=AlertLevel.WARNING,
                message=f"CPU usage high: {snapshot.cpu.usage_percent:.1f}%",
                value=snapshot.cpu.usage_percent,
                threshold=self.config.cpu_warning
            ))
        
        # Memory
        if snapshot.memory.usage_percent >= self.config.memory_critical:
            self._alert(ResourceAlert(
                timestamp=datetime.now(),
                resource="memory",
                level=AlertLevel.CRITICAL,
                message=f"Memory usage critical: {snapshot.memory.usage_percent:.1f}%",
                value=snapshot.memory.usage_percent,
                threshold=self.config.memory_critical
            ))
        elif snapshot.memory.usage_percent >= self.config.memory_warning:
            self._alert(ResourceAlert(
                timestamp=datetime.now(),
                resource="memory",
                level=AlertLevel.WARNING,
                message=f"Memory usage high: {snapshot.memory.usage_percent:.1f}%",
                value=snapshot.memory.usage_percent,
                threshold=self.config.memory_warning
            ))
        
        # Disk
        for disk in snapshot.disks:
            if disk.usage_percent >= self.config.disk_critical:
                self._alert(ResourceAlert(
                    timestamp=datetime.now(),
                    resource=f"disk:{disk.path}",
                    level=AlertLevel.CRITICAL,
                    message=f"Disk {disk.path} usage critical: {disk.usage_percent:.1f}%",
                    value=disk.usage_percent,
                    threshold=self.config.disk_critical
                ))
            elif disk.usage_percent >= self.config.disk_warning:
                self._alert(ResourceAlert(
                    timestamp=datetime.now(),
                    resource=f"disk:{disk.path}",
                    level=AlertLevel.WARNING,
                    message=f"Disk {disk.path} usage high: {disk.usage_percent:.1f}%",
                    value=disk.usage_percent,
                    threshold=self.config.disk_warning
                ))
    
    def _alert(self, alert: ResourceAlert):
        """Generate an alert"""
        self._alerts.append(alert)
        
        # Keep last 1000 alerts
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
        
        logger.warning(f"Resource alert: {alert.message}")
        
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def get_current(self) -> Optional[SystemSnapshot]:
        """Get most recent snapshot"""
        with self._lock:
            if self._history:
                return self._history[-1]
            return None
    
    def get_history(self, minutes: int = 60) -> List[SystemSnapshot]:
        """Get historical snapshots"""
        with self._lock:
            samples = int((minutes * 60) / self.config.interval)
            return list(self._history)[-samples:]
    
    def get_alerts(self, level: AlertLevel = None, 
                  last_minutes: int = 60) -> List[ResourceAlert]:
        """Get recent alerts"""
        cutoff = datetime.now().timestamp() - (last_minutes * 60)
        
        alerts = [a for a in self._alerts if a.timestamp.timestamp() > cutoff]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        current = self.get_current()
        
        if not current:
            return {}
        
        history = list(self._history)
        
        # Calculate averages
        if history:
            avg_cpu = sum(s.cpu.usage_percent for s in history) / len(history)
            avg_memory = sum(s.memory.usage_percent for s in history) / len(history)
            max_cpu = max(s.cpu.usage_percent for s in history)
            max_memory = max(s.memory.usage_percent for s in history)
        else:
            avg_cpu = avg_memory = max_cpu = max_memory = 0
        
        return {
            'current': {
                'cpu_percent': current.cpu.usage_percent,
                'memory_percent': current.memory.usage_percent,
                'memory_used_gb': current.memory.used_bytes / (1024**3),
                'memory_available_gb': current.memory.available_bytes / (1024**3)
            },
            'averages': {
                'cpu_percent': avg_cpu,
                'memory_percent': avg_memory
            },
            'peaks': {
                'cpu_percent': max_cpu,
                'memory_percent': max_memory
            },
            'alerts': {
                'total': len(self._alerts),
                'critical': len([a for a in self._alerts if a.level == AlertLevel.CRITICAL]),
                'warning': len([a for a in self._alerts if a.level == AlertLevel.WARNING])
            },
            'samples': len(history)
        }


class ResourceThrottler:
    """
    Throttle operations based on resource usage
    """
    
    def __init__(self, monitor: ResourceMonitor,
                 cpu_limit: float = 80.0,
                 memory_limit: float = 85.0):
        self.monitor = monitor
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
    
    def should_throttle(self) -> bool:
        """Check if operations should be throttled"""
        current = self.monitor.get_current()
        
        if not current:
            return False
        
        return (
            current.cpu.usage_percent >= self.cpu_limit or
            current.memory.usage_percent >= self.memory_limit
        )
    
    def wait_for_resources(self, timeout: float = 30.0,
                          check_interval: float = 1.0) -> bool:
        """
        Wait until resources are available
        
        Returns:
            True if resources available, False if timeout
        """
        start = time.time()
        
        while time.time() - start < timeout:
            if not self.should_throttle():
                return True
            time.sleep(check_interval)
        
        return False
    
    def get_throttle_reason(self) -> Optional[str]:
        """Get reason for throttling"""
        current = self.monitor.get_current()
        
        if not current:
            return None
        
        reasons = []
        
        if current.cpu.usage_percent >= self.cpu_limit:
            reasons.append(f"CPU: {current.cpu.usage_percent:.1f}% >= {self.cpu_limit}%")
        
        if current.memory.usage_percent >= self.memory_limit:
            reasons.append(f"Memory: {current.memory.usage_percent:.1f}% >= {self.memory_limit}%")
        
        return ", ".join(reasons) if reasons else None
