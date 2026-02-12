"""
Connection Pool Management

Database and Redis connection pooling with:
- Pool sizing and management
- Health checks
- Automatic reconnection
- Connection lifecycle management
"""

import threading
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
from queue import Queue, Empty, Full
from enum import Enum

logger = logging.getLogger(__name__)


class PoolState(Enum):
    """Connection pool state"""
    STARTING = "starting"
    RUNNING = "running"
    DRAINING = "draining"
    STOPPED = "stopped"


@dataclass
class PoolConfig:
    """Connection pool configuration"""
    min_size: int = 5
    max_size: int = 20
    max_overflow: int = 10
    timeout: float = 30.0
    recycle: int = 3600  # Recycle connections after 1 hour
    max_idle_time: int = 300  # Close idle connections after 5 min
    health_check_interval: int = 30
    pre_ping: bool = True  # Ping before returning connection


@dataclass
class PoolStats:
    """Connection pool statistics"""
    pool_size: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    overflow_connections: int = 0
    total_connections_created: int = 0
    total_connections_closed: int = 0
    failed_checkouts: int = 0
    successful_checkouts: int = 0
    avg_wait_time_ms: float = 0.0
    max_wait_time_ms: float = 0.0


class PooledConnection:
    """Wrapper for pooled connections"""
    
    def __init__(self, connection: Any, pool: 'BaseConnectionPool'):
        self.connection = connection
        self.pool = pool
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.use_count = 0
        self.in_use = False
    
    def is_expired(self) -> bool:
        """Check if connection should be recycled"""
        if self.pool.config.recycle > 0:
            age = (datetime.now() - self.created_at).total_seconds()
            return age > self.pool.config.recycle
        return False
    
    def is_idle_too_long(self) -> bool:
        """Check if connection has been idle too long"""
        if self.pool.config.max_idle_time > 0:
            idle_time = (datetime.now() - self.last_used).total_seconds()
            return idle_time > self.pool.config.max_idle_time
        return False
    
    def mark_used(self):
        """Mark connection as used"""
        self.last_used = datetime.now()
        self.use_count += 1
        self.in_use = True
    
    def mark_released(self):
        """Mark connection as released"""
        self.in_use = False
        self.last_used = datetime.now()


class BaseConnectionPool:
    """
    Base class for connection pools
    """
    
    def __init__(self, config: PoolConfig = None,
                 connection_factory: Callable[[], Any] = None,
                 close_func: Callable[[Any], None] = None,
                 ping_func: Callable[[Any], bool] = None):
        """
        Initialize connection pool
        
        Args:
            config: Pool configuration
            connection_factory: Function to create new connections
            close_func: Function to close connections
            ping_func: Function to check connection health
        """
        self.config = config or PoolConfig()
        self._connection_factory = connection_factory
        self._close_func = close_func or (lambda c: c.close() if hasattr(c, 'close') else None)
        self._ping_func = ping_func or (lambda c: True)
        
        self._pool: Queue = Queue(maxsize=self.config.max_size)
        self._all_connections: List[PooledConnection] = []
        self._lock = threading.Lock()
        self._state = PoolState.STOPPED
        
        self._stats = PoolStats()
        self._wait_times: List[float] = []
        
        logger.info(f"ConnectionPool created: min={self.config.min_size}, max={self.config.max_size}")
    
    def start(self):
        """Start the connection pool"""
        self._state = PoolState.STARTING
        
        # Create minimum connections
        for _ in range(self.config.min_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn)
            except Exception as e:
                logger.error(f"Failed to create initial connection: {e}")
        
        self._state = PoolState.RUNNING
        
        # Start health check thread
        self._health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_thread.start()
        
        logger.info(f"ConnectionPool started with {self._pool.qsize()} connections")
    
    def _create_connection(self) -> PooledConnection:
        """Create a new pooled connection"""
        if not self._connection_factory:
            raise ValueError("No connection factory provided")
        
        connection = self._connection_factory()
        pooled = PooledConnection(connection, self)
        
        with self._lock:
            self._all_connections.append(pooled)
            self._stats.total_connections_created += 1
            self._stats.pool_size = len(self._all_connections)
        
        return pooled
    
    def _close_connection(self, pooled: PooledConnection):
        """Close a pooled connection"""
        try:
            self._close_func(pooled.connection)
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
        
        with self._lock:
            if pooled in self._all_connections:
                self._all_connections.remove(pooled)
            self._stats.total_connections_closed += 1
            self._stats.pool_size = len(self._all_connections)
    
    def get(self, timeout: float = None) -> PooledConnection:
        """
        Get a connection from the pool
        
        Args:
            timeout: Maximum time to wait for connection
            
        Returns:
            PooledConnection
            
        Raises:
            TimeoutError: If no connection available within timeout
        """
        if self._state != PoolState.RUNNING:
            raise RuntimeError(f"Pool is not running: {self._state}")
        
        timeout = timeout or self.config.timeout
        start_time = time.time()
        
        while True:
            try:
                # Try to get from pool
                pooled = self._pool.get(timeout=0.1)
                
                # Check if connection is healthy
                if pooled.is_expired() or pooled.is_idle_too_long():
                    self._close_connection(pooled)
                    continue
                
                # Pre-ping if enabled
                if self.config.pre_ping:
                    try:
                        if not self._ping_func(pooled.connection):
                            self._close_connection(pooled)
                            continue
                    except Exception:
                        self._close_connection(pooled)
                        continue
                
                pooled.mark_used()
                self._record_wait_time(time.time() - start_time)
                self._stats.successful_checkouts += 1
                
                with self._lock:
                    self._stats.active_connections += 1
                    self._stats.idle_connections = self._pool.qsize()
                
                return pooled
                
            except Empty:
                # No connection available, check if we can create more
                elapsed = time.time() - start_time
                
                if elapsed >= timeout:
                    self._stats.failed_checkouts += 1
                    raise TimeoutError(f"Could not get connection within {timeout}s")
                
                with self._lock:
                    total = len(self._all_connections)
                    max_allowed = self.config.max_size + self.config.max_overflow
                    
                    if total < max_allowed:
                        try:
                            pooled = self._create_connection()
                            pooled.mark_used()
                            self._record_wait_time(time.time() - start_time)
                            self._stats.successful_checkouts += 1
                            self._stats.active_connections += 1
                            
                            if total >= self.config.max_size:
                                self._stats.overflow_connections += 1
                            
                            return pooled
                        except Exception as e:
                            logger.error(f"Failed to create overflow connection: {e}")
    
    def put(self, pooled: PooledConnection):
        """
        Return a connection to the pool
        
        Args:
            pooled: Connection to return
        """
        pooled.mark_released()
        
        with self._lock:
            self._stats.active_connections = max(0, self._stats.active_connections - 1)
        
        # Check if overflow connection that should be closed
        if len(self._all_connections) > self.config.max_size:
            self._close_connection(pooled)
            with self._lock:
                self._stats.overflow_connections = max(0, self._stats.overflow_connections - 1)
            return
        
        # Check if connection is still healthy
        if pooled.is_expired():
            self._close_connection(pooled)
            return
        
        try:
            self._pool.put_nowait(pooled)
            with self._lock:
                self._stats.idle_connections = self._pool.qsize()
        except Full:
            self._close_connection(pooled)
    
    @contextmanager
    def connection(self, timeout: float = None):
        """
        Context manager for getting a connection
        
        Usage:
            with pool.connection() as conn:
                conn.execute(...)
        """
        pooled = self.get(timeout)
        try:
            yield pooled.connection
        finally:
            self.put(pooled)
    
    def _record_wait_time(self, wait_time: float):
        """Record connection wait time"""
        wait_ms = wait_time * 1000
        self._wait_times.append(wait_ms)
        
        # Keep only last 1000 wait times
        if len(self._wait_times) > 1000:
            self._wait_times = self._wait_times[-1000:]
        
        self._stats.avg_wait_time_ms = sum(self._wait_times) / len(self._wait_times)
        self._stats.max_wait_time_ms = max(self._wait_times)
    
    def _health_check_loop(self):
        """Background thread for health checks"""
        while self._state == PoolState.RUNNING:
            time.sleep(self.config.health_check_interval)
            self._perform_health_check()
    
    def _perform_health_check(self):
        """Perform health check on idle connections"""
        checked = 0
        removed = 0
        
        # Check connections in pool
        temp_connections = []
        
        while True:
            try:
                pooled = self._pool.get_nowait()
                
                if pooled.is_expired() or pooled.is_idle_too_long():
                    self._close_connection(pooled)
                    removed += 1
                elif self.config.pre_ping:
                    try:
                        if self._ping_func(pooled.connection):
                            temp_connections.append(pooled)
                        else:
                            self._close_connection(pooled)
                            removed += 1
                    except Exception:
                        self._close_connection(pooled)
                        removed += 1
                else:
                    temp_connections.append(pooled)
                
                checked += 1
                
            except Empty:
                break
        
        # Put healthy connections back
        for pooled in temp_connections:
            try:
                self._pool.put_nowait(pooled)
            except Full:
                self._close_connection(pooled)
        
        # Ensure minimum connections
        while self._pool.qsize() < self.config.min_size:
            try:
                pooled = self._create_connection()
                self._pool.put_nowait(pooled)
            except Exception as e:
                logger.error(f"Failed to replenish pool: {e}")
                break
        
        if removed > 0:
            logger.debug(f"Health check: checked={checked}, removed={removed}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            return {
                'pool_size': self._stats.pool_size,
                'active': self._stats.active_connections,
                'idle': self._pool.qsize(),
                'overflow': self._stats.overflow_connections,
                'total_created': self._stats.total_connections_created,
                'total_closed': self._stats.total_connections_closed,
                'successful_checkouts': self._stats.successful_checkouts,
                'failed_checkouts': self._stats.failed_checkouts,
                'avg_wait_ms': self._stats.avg_wait_time_ms,
                'max_wait_ms': self._stats.max_wait_time_ms,
                'state': self._state.value
            }
    
    def close(self):
        """Close the pool and all connections"""
        self._state = PoolState.DRAINING
        
        # Close all connections
        while True:
            try:
                pooled = self._pool.get_nowait()
                self._close_connection(pooled)
            except Empty:
                break
        
        # Close any active connections
        with self._lock:
            for pooled in list(self._all_connections):
                self._close_connection(pooled)
        
        self._state = PoolState.STOPPED
        logger.info("ConnectionPool closed")


class DatabasePool(BaseConnectionPool):
    """
    SQLAlchemy database connection pool
    """
    
    def __init__(self, database_url: str = None, config: PoolConfig = None):
        """
        Initialize database pool
        
        Args:
            database_url: SQLAlchemy database URL
            config: Pool configuration
        """
        self.database_url = database_url
        self._engine = None
        
        super().__init__(
            config=config,
            connection_factory=self._create_db_connection,
            close_func=self._close_db_connection,
            ping_func=self._ping_db_connection
        )
    
    def _create_db_connection(self) -> Any:
        """Create database connection"""
        if self._engine is None:
            from sqlalchemy import create_engine
            self._engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=self.config.recycle
            )
        
        return self._engine.connect()
    
    def _close_db_connection(self, connection: Any):
        """Close database connection"""
        if hasattr(connection, 'close'):
            connection.close()
    
    def _ping_db_connection(self, connection: Any) -> bool:
        """Ping database connection"""
        try:
            connection.execute("SELECT 1")
            return True
        except Exception:
            return False


class RedisPool(BaseConnectionPool):
    """
    Redis connection pool
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379,
                 db: int = 0, password: str = None, config: PoolConfig = None):
        """
        Initialize Redis pool
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            config: Pool configuration
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        super().__init__(
            config=config,
            connection_factory=self._create_redis_connection,
            close_func=self._close_redis_connection,
            ping_func=self._ping_redis_connection
        )
    
    def _create_redis_connection(self) -> Any:
        """Create Redis connection"""
        import redis
        return redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            socket_timeout=self.config.timeout,
            socket_connect_timeout=5.0
        )
    
    def _close_redis_connection(self, connection: Any):
        """Close Redis connection"""
        if hasattr(connection, 'close'):
            connection.close()
    
    def _ping_redis_connection(self, connection: Any) -> bool:
        """Ping Redis connection"""
        try:
            return connection.ping()
        except Exception:
            return False


class ConnectionPoolManager:
    """
    Manager for multiple connection pools
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._pools: Dict[str, BaseConnectionPool] = {}
        self._initialized = True
        logger.info("ConnectionPoolManager initialized")
    
    def register_pool(self, name: str, pool: BaseConnectionPool):
        """Register a connection pool"""
        self._pools[name] = pool
        logger.info(f"Registered pool: {name}")
    
    def get_pool(self, name: str) -> Optional[BaseConnectionPool]:
        """Get a registered pool"""
        return self._pools.get(name)
    
    def create_database_pool(self, name: str, database_url: str,
                            config: PoolConfig = None) -> DatabasePool:
        """Create and register a database pool"""
        pool = DatabasePool(database_url, config)
        pool.start()
        self.register_pool(name, pool)
        return pool
    
    def create_redis_pool(self, name: str, host: str = "localhost",
                         port: int = 6379, config: PoolConfig = None) -> RedisPool:
        """Create and register a Redis pool"""
        pool = RedisPool(host, port, config=config)
        pool.start()
        self.register_pool(name, pool)
        return pool
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools"""
        return {name: pool.get_stats() for name, pool in self._pools.items()}
    
    def close_all(self):
        """Close all pools"""
        for name, pool in self._pools.items():
            logger.info(f"Closing pool: {name}")
            pool.close()
        self._pools.clear()
