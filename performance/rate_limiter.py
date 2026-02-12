"""
Rate Limiter

Request rate limiting with:
- Token bucket algorithm
- Sliding window limiter
- Per-client limits
- Distributed rate limiting
"""

import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    remaining: int
    reset_time: float  # Seconds until reset
    retry_after: Optional[float] = None  # Seconds to wait if not allowed


class RateLimiter(ABC):
    """Base rate limiter interface"""
    
    @abstractmethod
    def is_allowed(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check if request is allowed"""
        pass
    
    @abstractmethod
    def reset(self, key: str):
        """Reset rate limit for a key"""
        pass


@dataclass
class TokenBucketConfig:
    """Token bucket configuration"""
    capacity: int = 100  # Maximum tokens
    refill_rate: float = 10.0  # Tokens per second
    initial_tokens: Optional[int] = None  # Initial tokens (defaults to capacity)


class TokenBucket:
    """
    Token bucket rate limiter
    
    Allows bursts up to capacity, then limits to refill_rate
    """
    
    def __init__(self, config: TokenBucketConfig = None):
        self.config = config or TokenBucketConfig()
        
        self._buckets: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()
        
        logger.info(f"TokenBucket initialized: capacity={self.config.capacity}, rate={self.config.refill_rate}/s")
    
    def _get_bucket(self, key: str) -> Dict[str, float]:
        """Get or create bucket for key"""
        if key not in self._buckets:
            initial = self.config.initial_tokens
            if initial is None:
                initial = self.config.capacity
            
            self._buckets[key] = {
                'tokens': float(initial),
                'last_update': time.time()
            }
        return self._buckets[key]
    
    def _refill(self, bucket: Dict[str, float]):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - bucket['last_update']
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.config.refill_rate
        bucket['tokens'] = min(
            self.config.capacity,
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_update'] = now
    
    def is_allowed(self, key: str, cost: int = 1) -> RateLimitResult:
        """
        Check if request is allowed
        
        Args:
            key: Identifier for rate limit bucket
            cost: Number of tokens to consume
            
        Returns:
            RateLimitResult
        """
        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)
            
            if bucket['tokens'] >= cost:
                bucket['tokens'] -= cost
                
                # Calculate time until bucket is full
                tokens_needed = self.config.capacity - bucket['tokens']
                reset_time = tokens_needed / self.config.refill_rate if self.config.refill_rate > 0 else 0
                
                return RateLimitResult(
                    allowed=True,
                    remaining=int(bucket['tokens']),
                    reset_time=reset_time
                )
            else:
                # Calculate time until we have enough tokens
                tokens_needed = cost - bucket['tokens']
                retry_after = tokens_needed / self.config.refill_rate if self.config.refill_rate > 0 else float('inf')
                
                return RateLimitResult(
                    allowed=False,
                    remaining=int(bucket['tokens']),
                    reset_time=self.config.capacity / self.config.refill_rate if self.config.refill_rate > 0 else 0,
                    retry_after=retry_after
                )
    
    def reset(self, key: str):
        """Reset bucket for key"""
        with self._lock:
            if key in self._buckets:
                self._buckets[key] = {
                    'tokens': float(self.config.capacity),
                    'last_update': time.time()
                }
    
    def get_tokens(self, key: str) -> int:
        """Get current token count for key"""
        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)
            return int(bucket['tokens'])


@dataclass
class SlidingWindowConfig:
    """Sliding window configuration"""
    window_size: int = 60  # Window size in seconds
    max_requests: int = 100  # Max requests per window


class SlidingWindowLimiter(RateLimiter):
    """
    Sliding window rate limiter
    
    Tracks exact request times within window
    """
    
    def __init__(self, config: SlidingWindowConfig = None):
        self.config = config or SlidingWindowConfig()
        
        self._windows: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        
        logger.info(f"SlidingWindowLimiter initialized: window={self.config.window_size}s, max={self.config.max_requests}")
    
    def _cleanup_window(self, key: str, now: float):
        """Remove expired entries from window"""
        cutoff = now - self.config.window_size
        self._windows[key] = [t for t in self._windows[key] if t > cutoff]
    
    def is_allowed(self, key: str, cost: int = 1) -> RateLimitResult:
        """
        Check if request is allowed
        
        Args:
            key: Identifier for rate limit window
            cost: Number of requests to record
            
        Returns:
            RateLimitResult
        """
        with self._lock:
            now = time.time()
            self._cleanup_window(key, now)
            
            current_count = len(self._windows[key])
            remaining = max(0, self.config.max_requests - current_count)
            
            if current_count + cost <= self.config.max_requests:
                # Add request timestamps
                for _ in range(cost):
                    self._windows[key].append(now)
                
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining - cost,
                    reset_time=self.config.window_size
                )
            else:
                # Calculate when oldest request expires
                if self._windows[key]:
                    oldest = min(self._windows[key])
                    retry_after = oldest + self.config.window_size - now
                else:
                    retry_after = 0
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=self.config.window_size,
                    retry_after=max(0, retry_after)
                )
    
    def reset(self, key: str):
        """Reset window for key"""
        with self._lock:
            self._windows[key] = []
    
    def get_count(self, key: str) -> int:
        """Get current request count for key"""
        with self._lock:
            now = time.time()
            self._cleanup_window(key, now)
            return len(self._windows[key])


@dataclass
class FixedWindowConfig:
    """Fixed window configuration"""
    window_size: int = 60  # Window size in seconds
    max_requests: int = 100  # Max requests per window


class FixedWindowLimiter(RateLimiter):
    """
    Fixed window rate limiter
    
    Simple counter per fixed time window
    """
    
    def __init__(self, config: FixedWindowConfig = None):
        self.config = config or FixedWindowConfig()
        
        self._counters: Dict[str, Tuple[int, int]] = {}  # key -> (count, window_start)
        self._lock = threading.Lock()
        
        logger.info(f"FixedWindowLimiter initialized: window={self.config.window_size}s, max={self.config.max_requests}")
    
    def _get_window(self, now: float) -> int:
        """Get current window number"""
        return int(now // self.config.window_size)
    
    def is_allowed(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check if request is allowed"""
        with self._lock:
            now = time.time()
            current_window = self._get_window(now)
            
            if key in self._counters:
                count, window = self._counters[key]
                if window != current_window:
                    # New window, reset counter
                    count = 0
            else:
                count = 0
            
            remaining = max(0, self.config.max_requests - count)
            
            # Calculate time until window resets
            window_end = (current_window + 1) * self.config.window_size
            reset_time = window_end - now
            
            if count + cost <= self.config.max_requests:
                self._counters[key] = (count + cost, current_window)
                
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining - cost,
                    reset_time=reset_time
                )
            else:
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=reset_time
                )
    
    def reset(self, key: str):
        """Reset counter for key"""
        with self._lock:
            if key in self._counters:
                del self._counters[key]


@dataclass
class LeakyBucketConfig:
    """Leaky bucket configuration"""
    capacity: int = 100  # Maximum queue size
    leak_rate: float = 10.0  # Requests processed per second


class LeakyBucket(RateLimiter):
    """
    Leaky bucket rate limiter
    
    Requests are queued and processed at a constant rate
    """
    
    def __init__(self, config: LeakyBucketConfig = None):
        self.config = config or LeakyBucketConfig()
        
        self._buckets: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()
        
        logger.info(f"LeakyBucket initialized: capacity={self.config.capacity}, rate={self.config.leak_rate}/s")
    
    def _get_bucket(self, key: str) -> Dict[str, float]:
        """Get or create bucket for key"""
        if key not in self._buckets:
            self._buckets[key] = {
                'water': 0.0,
                'last_leak': time.time()
            }
        return self._buckets[key]
    
    def _leak(self, bucket: Dict[str, float]):
        """Leak water based on elapsed time"""
        now = time.time()
        elapsed = now - bucket['last_leak']
        
        # Remove water based on elapsed time
        leaked = elapsed * self.config.leak_rate
        bucket['water'] = max(0, bucket['water'] - leaked)
        bucket['last_leak'] = now
    
    def is_allowed(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check if request is allowed"""
        with self._lock:
            bucket = self._get_bucket(key)
            self._leak(bucket)
            
            if bucket['water'] + cost <= self.config.capacity:
                bucket['water'] += cost
                remaining = int(self.config.capacity - bucket['water'])
                
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_time=bucket['water'] / self.config.leak_rate if self.config.leak_rate > 0 else 0
                )
            else:
                # Calculate time until there's room
                overflow = bucket['water'] + cost - self.config.capacity
                retry_after = overflow / self.config.leak_rate if self.config.leak_rate > 0 else float('inf')
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=bucket['water'] / self.config.leak_rate if self.config.leak_rate > 0 else 0,
                    retry_after=retry_after
                )
    
    def reset(self, key: str):
        """Reset bucket for key"""
        with self._lock:
            if key in self._buckets:
                self._buckets[key] = {
                    'water': 0.0,
                    'last_leak': time.time()
                }


class CompositeRateLimiter(RateLimiter):
    """
    Composite rate limiter that applies multiple limits
    
    Useful for layered limits (e.g., per-second and per-minute)
    """
    
    def __init__(self, limiters: list = None):
        self._limiters: list = limiters or []
    
    def add_limiter(self, limiter: RateLimiter, name: str = None):
        """Add a rate limiter"""
        self._limiters.append((name or f"limiter_{len(self._limiters)}", limiter))
    
    def is_allowed(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check all limiters - request allowed only if all allow"""
        results = []
        
        for name, limiter in self._limiters:
            result = limiter.is_allowed(key, cost)
            results.append((name, result))
            
            if not result.allowed:
                return RateLimitResult(
                    allowed=False,
                    remaining=result.remaining,
                    reset_time=result.reset_time,
                    retry_after=result.retry_after
                )
        
        # All allowed - return minimum remaining
        min_remaining = min(r.remaining for _, r in results)
        min_reset = min(r.reset_time for _, r in results)
        
        return RateLimitResult(
            allowed=True,
            remaining=min_remaining,
            reset_time=min_reset
        )
    
    def reset(self, key: str):
        """Reset all limiters for key"""
        for _, limiter in self._limiters:
            limiter.reset(key)


class PerClientRateLimiter:
    """
    Per-client rate limiting with different tiers
    """
    
    def __init__(self, default_limiter: RateLimiter = None):
        self._default = default_limiter or TokenBucket(TokenBucketConfig(capacity=100, refill_rate=10))
        self._client_limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()
    
    def set_client_limiter(self, client_id: str, limiter: RateLimiter):
        """Set custom limiter for a client"""
        with self._lock:
            self._client_limiters[client_id] = limiter
    
    def remove_client_limiter(self, client_id: str):
        """Remove custom limiter for a client"""
        with self._lock:
            if client_id in self._client_limiters:
                del self._client_limiters[client_id]
    
    def is_allowed(self, client_id: str, resource: str = "default", 
                   cost: int = 1) -> RateLimitResult:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Client identifier
            resource: Optional resource identifier
            cost: Request cost
        """
        with self._lock:
            limiter = self._client_limiters.get(client_id, self._default)
        
        key = f"{client_id}:{resource}"
        return limiter.is_allowed(key, cost)
    
    def reset(self, client_id: str, resource: str = "default"):
        """Reset limit for client"""
        with self._lock:
            limiter = self._client_limiters.get(client_id, self._default)
        
        key = f"{client_id}:{resource}"
        limiter.reset(key)


class RateLimitMiddleware:
    """
    Rate limiting middleware for web applications
    """
    
    def __init__(self, limiter: RateLimiter,
                 key_func=None,
                 on_limited=None):
        """
        Initialize middleware
        
        Args:
            limiter: Rate limiter to use
            key_func: Function to extract key from request (default: client IP)
            on_limited: Callback when rate limited
        """
        self.limiter = limiter
        self.key_func = key_func or (lambda req: req.get('client_ip', 'unknown'))
        self.on_limited = on_limited
    
    def __call__(self, request: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Process request through rate limiter
        
        Args:
            request: Request dictionary
            
        Returns:
            Tuple of (allowed, headers/info)
        """
        key = self.key_func(request)
        result = self.limiter.is_allowed(key)
        
        headers = {
            'X-RateLimit-Remaining': str(result.remaining),
            'X-RateLimit-Reset': str(int(result.reset_time))
        }
        
        if not result.allowed:
            headers['Retry-After'] = str(int(result.retry_after))
            
            if self.on_limited:
                self.on_limited(key, request)
        
        return result.allowed, headers


def rate_limit(limiter: RateLimiter, key_func=None, cost: int = 1):
    """
    Decorator for rate limiting functions
    
    Args:
        limiter: Rate limiter to use
        key_func: Function to extract key from args (default: uses first arg)
        cost: Request cost
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            elif args:
                key = str(args[0])
            else:
                key = "default"
            
            result = limiter.is_allowed(key, cost)
            
            if not result.allowed:
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Retry after {result.retry_after:.1f}s",
                    retry_after=result.retry_after
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after
