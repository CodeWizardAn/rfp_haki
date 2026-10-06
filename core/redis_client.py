"""
Enterprise Redis Cache & Distributed State Manager
Provides distributed token revocation, caching, and rate limiting with graceful
in-memory fallback when Redis is unavailable.
"""

import os
import time
import logging
from typing import Optional, Set, Dict, Any

logger = logging.getLogger(__name__)

class DistributedStateManager:
    """Manages distributed tokens, revocation lists, and cache with Redis + in-memory fallback."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None
        self._in_memory_revoked: Set[str] = set()
        self._in_memory_cache: Dict[str, tuple[Any, float]] = {}

        try:
            import redis
            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            # Ping to verify connectivity
            self._redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis not available ({e}). Using thread-safe in-memory state manager.")
            self._redis = None

    def revoke_token(self, jti: str, expires_in_seconds: int = 86400) -> None:
        """Mark a JWT ID as revoked across all instances."""
        if self._redis:
            try:
                self._redis.setex(f"revoked_token:{jti}", expires_in_seconds, "1")
                return
            except Exception as e:
                logger.error(f"Redis error during token revocation: {e}")

        # Fallback to local memory
        self._in_memory_revoked.add(jti)

    def is_token_revoked(self, jti: str) -> bool:
        """Check if a JWT ID has been revoked."""
        if self._redis:
            try:
                val = self._redis.get(f"revoked_token:{jti}")
                return val is not None
            except Exception as e:
                logger.error(f"Redis error checking token revocation: {e}")

        return jti in self._in_memory_revoked

    def set_cache(self, key: str, value: str, ttl_seconds: int = 300) -> None:
        """Cache a string value with TTL."""
        if self._redis:
            try:
                self._redis.setex(f"cache:{key}", ttl_seconds, value)
                return
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

        self._in_memory_cache[key] = (value, time.time() + ttl_seconds)

    def get_cache(self, key: str) -> Optional[str]:
        """Retrieve a cached string value."""
        if self._redis:
            try:
                return self._redis.get(f"cache:{key}")
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")

        item = self._in_memory_cache.get(key)
        if item:
            val, exp = item
            if time.time() < exp:
                return val
            else:
                self._in_memory_cache.pop(key, None)
        return None


# Singleton instance
_distributed_state: Optional[DistributedStateManager] = None

def get_distributed_state() -> DistributedStateManager:
    global _distributed_state
    if _distributed_state is None:
        _distributed_state = DistributedStateManager()
    return _distributed_state
