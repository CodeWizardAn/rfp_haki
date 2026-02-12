"""
Load Balancer

Request distribution with:
- Multiple balancing strategies
- Health checks
- Failover handling
- Weighted distribution
"""

import logging
import threading
import time
import random
import hashlib
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class BalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"


class BackendState(Enum):
    """Backend health state"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"


@dataclass
class Backend:
    """Backend server configuration"""
    id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 100
    health_check_path: str = "/health"
    
    # Runtime state
    state: BackendState = BackendState.HEALTHY
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    
    def is_available(self) -> bool:
        """Check if backend is available for requests"""
        return (
            self.state in (BackendState.HEALTHY, BackendState.DEGRADED) and
            self.active_connections < self.max_connections
        )
    
    def record_request(self, response_time_ms: float, success: bool):
        """Record a completed request"""
        self.total_requests += 1
        
        if success:
            self.consecutive_failures = 0
            # Update running average
            n = self.total_requests
            self.avg_response_time_ms = (
                self.avg_response_time_ms * (n - 1) + response_time_ms
            ) / n
        else:
            self.failed_requests += 1
            self.consecutive_failures += 1
    
    @property
    def error_rate(self) -> float:
        if self.total_requests > 0:
            return self.failed_requests / self.total_requests
        return 0.0


@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    strategy: BalancingStrategy = BalancingStrategy.ROUND_ROBIN
    health_check_interval: int = 10  # Seconds
    health_check_timeout: float = 5.0
    max_failures_before_unhealthy: int = 3
    recovery_time: int = 30  # Seconds before retrying unhealthy backend
    sticky_sessions: bool = False
    session_timeout: int = 1800  # 30 minutes


class LoadBalancer:
    """
    Load balancer with multiple strategies and health checking
    """
    
    def __init__(self, config: LoadBalancerConfig = None):
        """
        Initialize load balancer
        
        Args:
            config: Load balancer configuration
        """
        self.config = config or LoadBalancerConfig()
        
        self._backends: Dict[str, Backend] = {}
        self._lock = threading.RLock()
        self._round_robin_idx = 0
        self._sessions: Dict[str, str] = {}  # session_id -> backend_id
        
        # Health check thread
        self._running = False
        self._health_thread: Optional[threading.Thread] = None
        
        # Request tracking
        self._response_times: Dict[str, deque] = {}  # Recent response times per backend
        
        logger.info(f"LoadBalancer initialized with strategy={self.config.strategy.value}")
    
    def add_backend(self, backend: Backend):
        """Add a backend server"""
        with self._lock:
            self._backends[backend.id] = backend
            self._response_times[backend.id] = deque(maxlen=100)
        logger.info(f"Added backend: {backend.id} ({backend.host}:{backend.port})")
    
    def remove_backend(self, backend_id: str):
        """Remove a backend server"""
        with self._lock:
            if backend_id in self._backends:
                del self._backends[backend_id]
                logger.info(f"Removed backend: {backend_id}")
    
    def get_backend(self, session_id: str = None, 
                    client_ip: str = None) -> Optional[Backend]:
        """
        Get a backend using configured strategy
        
        Args:
            session_id: Session ID for sticky sessions
            client_ip: Client IP for IP hash strategy
            
        Returns:
            Backend or None if no backends available
        """
        with self._lock:
            # Check sticky session first
            if self.config.sticky_sessions and session_id:
                backend_id = self._sessions.get(session_id)
                if backend_id and backend_id in self._backends:
                    backend = self._backends[backend_id]
                    if backend.is_available():
                        return backend
            
            # Get available backends
            available = [b for b in self._backends.values() if b.is_available()]
            
            if not available:
                logger.warning("No available backends")
                return None
            
            # Select based on strategy
            backend = self._select_backend(available, client_ip)
            
            # Record sticky session
            if self.config.sticky_sessions and session_id and backend:
                self._sessions[session_id] = backend.id
            
            return backend
    
    def _select_backend(self, available: List[Backend], 
                       client_ip: str = None) -> Backend:
        """Select a backend based on strategy"""
        strategy = self.config.strategy
        
        if strategy == BalancingStrategy.ROUND_ROBIN:
            return self._round_robin(available)
        
        elif strategy == BalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(available)
        
        elif strategy == BalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(available)
        
        elif strategy == BalancingStrategy.RANDOM:
            return random.choice(available)
        
        elif strategy == BalancingStrategy.IP_HASH:
            return self._ip_hash(available, client_ip or "default")
        
        elif strategy == BalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time(available)
        
        return available[0]
    
    def _round_robin(self, available: List[Backend]) -> Backend:
        """Round-robin selection"""
        backend = available[self._round_robin_idx % len(available)]
        self._round_robin_idx += 1
        return backend
    
    def _weighted_round_robin(self, available: List[Backend]) -> Backend:
        """Weighted round-robin selection"""
        total_weight = sum(b.weight for b in available)
        
        # Create weighted list
        weighted_list = []
        for backend in available:
            weight_ratio = backend.weight / total_weight
            count = max(1, int(weight_ratio * len(available) * 10))
            weighted_list.extend([backend] * count)
        
        backend = weighted_list[self._round_robin_idx % len(weighted_list)]
        self._round_robin_idx += 1
        return backend
    
    def _least_connections(self, available: List[Backend]) -> Backend:
        """Select backend with fewest connections"""
        return min(available, key=lambda b: b.active_connections)
    
    def _ip_hash(self, available: List[Backend], client_ip: str) -> Backend:
        """Select backend based on client IP hash"""
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return available[hash_value % len(available)]
    
    def _least_response_time(self, available: List[Backend]) -> Backend:
        """Select backend with lowest average response time"""
        return min(available, key=lambda b: b.avg_response_time_ms or 0)
    
    def start_connection(self, backend: Backend):
        """Record start of connection"""
        with self._lock:
            backend.active_connections += 1
    
    def end_connection(self, backend: Backend, response_time_ms: float, 
                      success: bool = True):
        """Record end of connection"""
        with self._lock:
            backend.active_connections = max(0, backend.active_connections - 1)
            backend.record_request(response_time_ms, success)
            
            # Track response times
            if backend.id in self._response_times:
                self._response_times[backend.id].append(response_time_ms)
            
            # Check if backend should be marked degraded/unhealthy
            if backend.consecutive_failures >= self.config.max_failures_before_unhealthy:
                backend.state = BackendState.UNHEALTHY
                logger.warning(f"Backend {backend.id} marked unhealthy after {backend.consecutive_failures} failures")
            elif backend.error_rate > 0.1:  # 10% error rate
                backend.state = BackendState.DEGRADED
    
    def start(self):
        """Start health checking"""
        self._running = True
        self._health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_thread.start()
        logger.info("LoadBalancer health checking started")
    
    def stop(self):
        """Stop health checking"""
        self._running = False
        if self._health_thread:
            self._health_thread.join(timeout=5.0)
        logger.info("LoadBalancer stopped")
    
    def _health_check_loop(self):
        """Background health check loop"""
        while self._running:
            time.sleep(self.config.health_check_interval)
            self._perform_health_checks()
    
    def _perform_health_checks(self):
        """Perform health checks on all backends"""
        with self._lock:
            for backend in self._backends.values():
                try:
                    healthy = self._check_backend_health(backend)
                    backend.last_health_check = datetime.now()
                    
                    if healthy:
                        if backend.state == BackendState.UNHEALTHY:
                            logger.info(f"Backend {backend.id} recovered")
                        backend.state = BackendState.HEALTHY
                        backend.consecutive_failures = 0
                    else:
                        backend.consecutive_failures += 1
                        if backend.consecutive_failures >= self.config.max_failures_before_unhealthy:
                            backend.state = BackendState.UNHEALTHY
                            
                except Exception as e:
                    logger.error(f"Health check failed for {backend.id}: {e}")
                    backend.consecutive_failures += 1
    
    def _check_backend_health(self, backend: Backend) -> bool:
        """
        Check if a backend is healthy
        Override this method for actual health checking
        """
        # Simplified health check - in production would make HTTP request
        return backend.error_rate < 0.5 and backend.consecutive_failures < self.config.max_failures_before_unhealthy
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        with self._lock:
            backends_info = []
            for backend in self._backends.values():
                backends_info.append({
                    'id': backend.id,
                    'host': f"{backend.host}:{backend.port}",
                    'state': backend.state.value,
                    'active_connections': backend.active_connections,
                    'total_requests': backend.total_requests,
                    'error_rate': backend.error_rate,
                    'avg_response_time_ms': backend.avg_response_time_ms
                })
            
            return {
                'strategy': self.config.strategy.value,
                'total_backends': len(self._backends),
                'healthy_backends': sum(1 for b in self._backends.values() if b.state == BackendState.HEALTHY),
                'backends': backends_info,
                'active_sessions': len(self._sessions)
            }
    
    def drain_backend(self, backend_id: str):
        """Set backend to draining state (no new connections)"""
        with self._lock:
            if backend_id in self._backends:
                self._backends[backend_id].state = BackendState.DRAINING
                logger.info(f"Backend {backend_id} set to draining")
    
    def activate_backend(self, backend_id: str):
        """Activate a backend"""
        with self._lock:
            if backend_id in self._backends:
                self._backends[backend_id].state = BackendState.HEALTHY
                self._backends[backend_id].consecutive_failures = 0
                logger.info(f"Backend {backend_id} activated")


class ServiceDiscovery:
    """
    Simple service discovery for dynamic backend registration
    """
    
    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self._registered_services: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def register(self, service_id: str, host: str, port: int, 
                 weight: int = 1, metadata: Dict[str, Any] = None):
        """Register a service instance"""
        backend = Backend(
            id=service_id,
            host=host,
            port=port,
            weight=weight
        )
        
        with self._lock:
            self._registered_services[service_id] = {
                'backend': backend,
                'metadata': metadata or {},
                'registered_at': datetime.now()
            }
        
        self.load_balancer.add_backend(backend)
        logger.info(f"Service registered: {service_id}")
    
    def deregister(self, service_id: str):
        """Deregister a service instance"""
        with self._lock:
            if service_id in self._registered_services:
                del self._registered_services[service_id]
        
        self.load_balancer.remove_backend(service_id)
        logger.info(f"Service deregistered: {service_id}")
    
    def get_services(self) -> List[Dict[str, Any]]:
        """Get all registered services"""
        with self._lock:
            return [
                {
                    'id': sid,
                    **info
                }
                for sid, info in self._registered_services.items()
            ]
