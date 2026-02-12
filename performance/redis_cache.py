"""
Redis Caching Layer

High-performance caching using Redis with:
- Connection management and pooling
- Multiple caching strategies (simple, hash, sorted sets)
- TTL management and cache invalidation
- Serialization/deserialization
- Cache decorators for easy integration
- Cluster support and failover
"""

import json
import pickle
import hashlib
import logging
import functools
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class SerializationType(Enum):
    """Serialization methods for cache values"""
    JSON = "json"
    PICKLE = "pickle"
    STRING = "string"


@dataclass
class RedisCacheConfig:
    """Redis cache configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    max_connections: int = 50
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    default_ttl: int = 3600  # 1 hour
    key_prefix: str = "haki:"
    serialization: SerializationType = SerializationType.JSON
    compression_threshold: int = 1024  # Compress values larger than 1KB
    enable_stats: bool = True


class RedisCache:
    """
    Redis caching layer with advanced features
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config: RedisCacheConfig = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: RedisCacheConfig = None):
        if self._initialized:
            return
        
        self.config = config or RedisCacheConfig()
        self._client = None
        self._pool = None
        self._connected = False
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
        self._connect()
        self._initialized = True
        logger.info(f"RedisCache initialized with host={self.config.host}:{self.config.port}")
    
    def _connect(self):
        """Establish Redis connection"""
        try:
            import redis
            
            self._pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval,
                decode_responses=False  # We handle encoding ourselves
            )
            
            self._client = redis.Redis(connection_pool=self._pool)
            self._client.ping()
            self._connected = True
            logger.info("Redis connection established")
            
        except ImportError:
            logger.warning("redis package not installed, using in-memory fallback")
            self._use_fallback()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory fallback")
            self._use_fallback()
    
    def _use_fallback(self):
        """Use in-memory fallback when Redis unavailable"""
        self._client = InMemoryFallback()
        self._connected = True
    
    def _make_key(self, key: str) -> str:
        """Generate prefixed cache key"""
        return f"{self.config.key_prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if self.config.serialization == SerializationType.JSON:
            return json.dumps(value, default=str).encode('utf-8')
        elif self.config.serialization == SerializationType.PICKLE:
            return pickle.dumps(value)
        else:
            return str(value).encode('utf-8')
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize stored value"""
        if data is None:
            return None
        
        if self.config.serialization == SerializationType.JSON:
            return json.loads(data.decode('utf-8'))
        elif self.config.serialization == SerializationType.PICKLE:
            return pickle.loads(data)
        else:
            return data.decode('utf-8')
    
    # ==================== Basic Operations ====================
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            full_key = self._make_key(key)
            data = self._client.get(full_key)
            
            if data is None:
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return self._deserialize(data)
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            full_key = self._make_key(key)
            data = self._serialize(value)
            ttl = ttl or self.config.default_ttl
            
            result = self._client.setex(full_key, ttl, data)
            self._stats['sets'] += 1
            return bool(result)
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            full_key = self._make_key(key)
            result = self._client.delete(full_key)
            self._stats['deletes'] += 1
            return bool(result)
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            full_key = self._make_key(key)
            return bool(self._client.exists(full_key))
        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get TTL for key (-1 if no expiry, -2 if not exists)"""
        try:
            full_key = self._make_key(key)
            return self._client.ttl(full_key)
        except Exception as e:
            logger.error(f"Cache TTL error for {key}: {e}")
            return -2
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiry on existing key"""
        try:
            full_key = self._make_key(key)
            return bool(self._client.expire(full_key, ttl))
        except Exception as e:
            logger.error(f"Cache expire error for {key}: {e}")
            return False
    
    # ==================== Batch Operations ====================
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values"""
        try:
            full_keys = [self._make_key(k) for k in keys]
            values = self._client.mget(full_keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
                    self._stats['hits'] += 1
                else:
                    self._stats['misses'] += 1
            
            return result
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache mget error: {e}")
            return {}
    
    def mset(self, mapping: Dict[str, Any], ttl: int = None) -> bool:
        """Set multiple values"""
        try:
            ttl = ttl or self.config.default_ttl
            pipe = self._client.pipeline()
            
            for key, value in mapping.items():
                full_key = self._make_key(key)
                data = self._serialize(value)
                pipe.setex(full_key, ttl, data)
            
            pipe.execute()
            self._stats['sets'] += len(mapping)
            return True
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache mset error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            full_pattern = self._make_key(pattern)
            keys = self._client.keys(full_pattern)
            
            if keys:
                deleted = self._client.delete(*keys)
                self._stats['deletes'] += deleted
                return deleted
            return 0
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache delete_pattern error: {e}")
            return 0
    
    # ==================== Hash Operations ====================
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get field from hash"""
        try:
            full_name = self._make_key(name)
            data = self._client.hget(full_name, key)
            
            if data is None:
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return self._deserialize(data)
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache hget error: {e}")
            return None
    
    def hset(self, name: str, key: str, value: Any) -> bool:
        """Set field in hash"""
        try:
            full_name = self._make_key(name)
            data = self._serialize(value)
            self._client.hset(full_name, key, data)
            self._stats['sets'] += 1
            return True
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache hset error: {e}")
            return False
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all fields from hash"""
        try:
            full_name = self._make_key(name)
            data = self._client.hgetall(full_name)
            
            result = {}
            for key, value in data.items():
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                result[key_str] = self._deserialize(value)
            
            if result:
                self._stats['hits'] += 1
            else:
                self._stats['misses'] += 1
            
            return result
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache hgetall error: {e}")
            return {}
    
    # ==================== List Operations ====================
    
    def lpush(self, name: str, *values: Any) -> int:
        """Push values to left of list"""
        try:
            full_name = self._make_key(name)
            serialized = [self._serialize(v) for v in values]
            return self._client.lpush(full_name, *serialized)
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache lpush error: {e}")
            return 0
    
    def rpop(self, name: str) -> Optional[Any]:
        """Pop value from right of list"""
        try:
            full_name = self._make_key(name)
            data = self._client.rpop(full_name)
            return self._deserialize(data) if data else None
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache rpop error: {e}")
            return None
    
    def lrange(self, name: str, start: int, end: int) -> List[Any]:
        """Get range from list"""
        try:
            full_name = self._make_key(name)
            data = self._client.lrange(full_name, start, end)
            return [self._deserialize(d) for d in data]
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache lrange error: {e}")
            return []
    
    # ==================== Sorted Set Operations ====================
    
    def zadd(self, name: str, mapping: Dict[str, float]) -> int:
        """Add members to sorted set with scores"""
        try:
            full_name = self._make_key(name)
            return self._client.zadd(full_name, mapping)
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache zadd error: {e}")
            return 0
    
    def zrange(self, name: str, start: int, end: int, 
               withscores: bool = False) -> List[Any]:
        """Get range from sorted set by index"""
        try:
            full_name = self._make_key(name)
            return self._client.zrange(full_name, start, end, withscores=withscores)
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache zrange error: {e}")
            return []
    
    def zrangebyscore(self, name: str, min_score: float, max_score: float,
                      withscores: bool = False) -> List[Any]:
        """Get range from sorted set by score"""
        try:
            full_name = self._make_key(name)
            return self._client.zrangebyscore(
                full_name, min_score, max_score, withscores=withscores
            )
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache zrangebyscore error: {e}")
            return []
    
    # ==================== Atomic Operations ====================
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increment value"""
        try:
            full_key = self._make_key(key)
            return self._client.incrby(full_key, amount)
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache incr error: {e}")
            return 0
    
    def decr(self, key: str, amount: int = 1) -> int:
        """Atomically decrement value"""
        try:
            full_key = self._make_key(key)
            return self._client.decrby(full_key, amount)
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache decr error: {e}")
            return 0
    
    def setnx(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value only if not exists (for locking)"""
        try:
            full_key = self._make_key(key)
            data = self._serialize(value)
            ttl = ttl or self.config.default_ttl
            
            result = self._client.set(full_key, data, nx=True, ex=ttl)
            return bool(result)
            
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Cache setnx error: {e}")
            return False
    
    # ==================== Cache Patterns ====================
    
    def get_or_set(self, key: str, factory: Callable[[], Any], 
                   ttl: int = None) -> Any:
        """Get from cache or compute and cache value"""
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def cache_aside(self, key: str, loader: Callable[[], Any],
                    ttl: int = None) -> Any:
        """Cache-aside pattern: try cache, load on miss, update cache"""
        value = self.get(key)
        if value is not None:
            return value
        
        value = loader()
        if value is not None:
            self.set(key, value, ttl)
        
        return value
    
    def invalidate_on_update(self, key: str, updater: Callable[[], Any]) -> Any:
        """Invalidate cache before update"""
        self.delete(key)
        result = updater()
        return result
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total if total > 0 else 0
        
        return {
            **self._stats,
            'hit_rate': hit_rate,
            'total_operations': total,
            'connected': self._connected
        }
    
    def reset_stats(self):
        """Reset statistics"""
        for key in self._stats:
            self._stats[key] = 0
    
    def info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        try:
            if hasattr(self._client, 'info'):
                return self._client.info()
            return {}
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            start = datetime.now()
            self._client.ping()
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'latency_ms': latency,
                'connected': self._connected,
                'stats': self.get_stats()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connected': False
            }
    
    def close(self):
        """Close Redis connection"""
        if self._pool:
            self._pool.disconnect()
        self._connected = False


class InMemoryFallback:
    """In-memory fallback when Redis is unavailable"""
    
    def __init__(self):
        self._data = {}
        self._expiry = {}
        self._lock = threading.Lock()
    
    def _check_expiry(self, key: str) -> bool:
        """Check if key is expired"""
        if key in self._expiry:
            if datetime.now() > self._expiry[key]:
                del self._data[key]
                del self._expiry[key]
                return True
        return False
    
    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            self._check_expiry(key)
            return self._data.get(key)
    
    def setex(self, key: str, ttl: int, value: bytes) -> bool:
        with self._lock:
            self._data[key] = value
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
            return True
    
    def set(self, key: str, value: bytes, nx: bool = False, ex: int = None, ttl: int = None) -> bool:
        with self._lock:
            if nx and key in self._data:
                return False
            self._data[key] = value
            expire_time = ex or ttl
            if expire_time:
                self._expiry[key] = datetime.now() + timedelta(seconds=expire_time)
            return True
    
    def mset(self, mapping: Dict[str, Any], ttl: int = None) -> bool:
        """Set multiple key-value pairs"""
        with self._lock:
            for key, value in mapping.items():
                self._data[key] = value
                if ttl:
                    self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
            return True
    
    def delete(self, *keys: str) -> int:
        with self._lock:
            count = 0
            for key in keys:
                if key in self._data:
                    del self._data[key]
                    self._expiry.pop(key, None)
                    count += 1
            return count
    
    def exists(self, key: str) -> bool:
        with self._lock:
            self._check_expiry(key)
            return key in self._data
    
    def ttl(self, key: str) -> int:
        with self._lock:
            if key not in self._data:
                return -2
            if key not in self._expiry:
                return -1
            remaining = (self._expiry[key] - datetime.now()).total_seconds()
            return int(remaining) if remaining > 0 else -2
    
    def expire(self, key: str, ttl: int) -> bool:
        with self._lock:
            if key in self._data:
                self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
                return True
            return False
    
    def mget(self, keys: List[str]) -> List[Optional[bytes]]:
        return [self.get(k) for k in keys]
    
    def keys(self, pattern: str) -> List[str]:
        import fnmatch
        with self._lock:
            return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]
    
    def pipeline(self):
        return InMemoryPipeline(self)
    
    def hget(self, name: str, key: str) -> Optional[bytes]:
        with self._lock:
            hash_data = self._data.get(name, {})
            if isinstance(hash_data, dict):
                return hash_data.get(key)
            return None
    
    def hset(self, name: str, key: str, value: bytes):
        with self._lock:
            if name not in self._data:
                self._data[name] = {}
            self._data[name][key] = value
    
    def hgetall(self, name: str) -> Dict[str, bytes]:
        with self._lock:
            return dict(self._data.get(name, {}))
    
    def lpush(self, name: str, *values: bytes) -> int:
        with self._lock:
            if name not in self._data:
                self._data[name] = []
            for v in values:
                self._data[name].insert(0, v)
            return len(self._data[name])
    
    def rpop(self, name: str) -> Optional[bytes]:
        with self._lock:
            if name in self._data and self._data[name]:
                return self._data[name].pop()
            return None
    
    def lrange(self, name: str, start: int, end: int) -> List[bytes]:
        with self._lock:
            if name not in self._data:
                return []
            if end == -1:
                return self._data[name][start:]
            return self._data[name][start:end+1]
    
    def zadd(self, name: str, mapping: Dict[str, float]) -> int:
        with self._lock:
            if name not in self._data:
                self._data[name] = {}
            for member, score in mapping.items():
                self._data[name][member] = score
            return len(mapping)
    
    def zrange(self, name: str, start: int, end: int, 
               withscores: bool = False) -> List[Any]:
        with self._lock:
            if name not in self._data:
                return []
            sorted_items = sorted(self._data[name].items(), key=lambda x: x[1])
            if end == -1:
                items = sorted_items[start:]
            else:
                items = sorted_items[start:end+1]
            
            if withscores:
                return items
            return [item[0] for item in items]
    
    def zrangebyscore(self, name: str, min_score: float, max_score: float,
                      withscores: bool = False) -> List[Any]:
        with self._lock:
            if name not in self._data:
                return []
            items = [(m, s) for m, s in self._data[name].items() 
                     if min_score <= s <= max_score]
            items.sort(key=lambda x: x[1])
            
            if withscores:
                return items
            return [item[0] for item in items]
    
    def incrby(self, key: str, amount: int) -> int:
        with self._lock:
            if key not in self._data:
                self._data[key] = b'0'
            current = int(self._data[key])
            new_value = current + amount
            self._data[key] = str(new_value).encode()
            return new_value
    
    def decrby(self, key: str, amount: int) -> int:
        return self.incrby(key, -amount)
    
    def ping(self) -> bool:
        return True
    
    def info(self) -> Dict[str, Any]:
        return {'type': 'in_memory_fallback', 'keys': len(self._data)}


class InMemoryPipeline:
    """Pipeline implementation for in-memory fallback"""
    
    def __init__(self, cache: InMemoryFallback):
        self.cache = cache
        self.commands = []
    
    def setex(self, key: str, ttl: int, value: bytes):
        self.commands.append(('setex', key, ttl, value))
        return self
    
    def execute(self) -> List[bool]:
        results = []
        for cmd in self.commands:
            if cmd[0] == 'setex':
                result = self.cache.setex(cmd[1], cmd[2], cmd[3])
                results.append(result)
        self.commands = []
        return results


def cache_result(key_template: str = None, ttl: int = None, 
                 key_builder: Callable = None):
    """
    Decorator for caching function results
    
    Args:
        key_template: Template for cache key (e.g., "user:{user_id}")
        ttl: Cache TTL in seconds
        key_builder: Custom function to build cache key from args/kwargs
    
    Example:
        @cache_result("user:{user_id}", ttl=3600)
        def get_user(user_id):
            return db.query(User).filter_by(id=user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = RedisCache()
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            elif key_template:
                # Build key from template and kwargs
                key_kwargs = {**kwargs}
                # Add positional args as arg_0, arg_1, etc.
                for i, arg in enumerate(args):
                    key_kwargs[f'arg_{i}'] = arg
                cache_key = key_template.format(**key_kwargs)
            else:
                # Auto-generate key from function name and args
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Add cache control methods
        wrapper.cache_invalidate = lambda *args, **kwargs: RedisCache().delete(
            key_template.format(**kwargs) if key_template else None
        )
        
        return wrapper
    return decorator


def generate_cache_key(*parts: Any) -> str:
    """Generate a cache key from multiple parts"""
    key_str = ":".join(str(p) for p in parts)
    return hashlib.md5(key_str.encode()).hexdigest()
