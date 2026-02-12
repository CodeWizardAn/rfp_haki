"""
Error Handling and Utility Decorators
Common decorators for agents

Features:
- Retry decorator with exponential backoff
- Logging decorator
- Timer decorator
- Caching decorator
- Input validation decorator
- Exception handling decorator
- Async retry decorator
- Rate limiting decorator
"""

import time
import functools
import logging
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
from datetime import datetime, timedelta
import asyncio
from collections import OrderedDict
from threading import Lock


logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry (receives exception, attempt number)
    
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        if on_retry:
                            on_retry(e, attempt)
                        
                        logger.warning(
                            f"Retry {attempt}/{max_attempts} for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Async retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional async callback called on each retry
    
    Example:
        @async_retry(max_attempts=3)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        if on_retry:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(e, attempt)
                            else:
                                on_retry(e, attempt)
                        
                        logger.warning(
                            f"Async retry {attempt}/{max_attempts} for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} async attempts failed for {func.__name__}: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def log_execution(
    level: int = logging.INFO,
    log_args: bool = True,
    log_result: bool = True,
    max_arg_length: int = 100
):
    """
    Decorator to log function execution
    
    Args:
        level: Logging level
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        max_arg_length: Maximum length of argument string in log
    
    Example:
        @log_execution(level=logging.DEBUG)
        def process_rfp(rfp_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Log entry
            if log_args:
                args_str = str(args)[:max_arg_length]
                kwargs_str = str(kwargs)[:max_arg_length]
                logger.log(level, f"Entering {func_name}(args={args_str}, kwargs={kwargs_str})")
            else:
                logger.log(level, f"Entering {func_name}()")
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if log_result:
                    result_str = str(result)[:max_arg_length]
                    logger.log(level, f"Exiting {func_name} after {duration:.3f}s. Result: {result_str}")
                else:
                    logger.log(level, f"Exiting {func_name} after {duration:.3f}s")
                
                return result
            
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Exception in {func_name} after {duration:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator


def timer(func: Callable = None, *, threshold: float = None):
    """
    Decorator to time function execution
    
    Args:
        func: Function to decorate
        threshold: Optional threshold in seconds. Only log if execution exceeds this
    
    Example:
        @timer
        def slow_function():
            ...
        
        @timer(threshold=1.0)
        def should_be_fast():
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = fn(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            
            if threshold is None or elapsed >= threshold:
                logger.info(f"{fn.__name__} executed in {elapsed:.4f}s")
            
            return result
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator


class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.maxsize:
                    self.cache.popitem(last=False)
            self.cache[key] = value
    
    def clear(self):
        with self.lock:
            self.cache.clear()


def cached(
    maxsize: int = 128,
    ttl: Optional[float] = None,
    key_func: Optional[Callable] = None
):
    """
    Caching decorator with optional TTL
    
    Args:
        maxsize: Maximum cache size
        ttl: Time to live in seconds
        key_func: Custom function to generate cache key from args/kwargs
    
    Example:
        @cached(maxsize=100, ttl=300)
        def get_product(product_id):
            ...
    """
    cache = LRUCache(maxsize)
    timestamps = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key_data = json.dumps((args, sorted(kwargs.items())), default=str)
                key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            cached_value = cache.get(key)
            if cached_value is not None:
                # Check TTL
                if ttl is None or (time.time() - timestamps.get(key, 0)) < ttl:
                    return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result)
            timestamps[key] = time.time()
            
            return result
        
        wrapper.cache_clear = cache.clear
        return wrapper
    
    return decorator


def validate_input(**validators):
    """
    Input validation decorator
    
    Args:
        **validators: Keyword arguments mapping parameter names to validation functions
    
    Example:
        @validate_input(
            email=lambda x: '@' in x,
            age=lambda x: 0 < x < 150
        )
        def create_user(email, age):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Validation failed for parameter '{param_name}': {value}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def handle_exceptions(
    default_return: Any = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_level: int = logging.ERROR,
    reraise: bool = False
):
    """
    Exception handling decorator
    
    Args:
        default_return: Value to return on exception
        exceptions: Tuple of exceptions to catch
        log_level: Logging level for errors
        reraise: Whether to re-raise the exception after logging
    
    Example:
        @handle_exceptions(default_return=[], reraise=False)
        def risky_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.log(
                    log_level,
                    f"Exception in {func.__name__}: {type(e).__name__}: {str(e)}"
                )
                
                if reraise:
                    raise
                
                if callable(default_return):
                    return default_return()
                return default_return
        
        return wrapper
    return decorator


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: float, burst: int = 1):
        self.rate = rate  # tokens per second
        self.burst = burst
        self.tokens = burst
        self.last_time = time.monotonic()
        self.lock = Lock()
    
    def acquire(self, timeout: float = None) -> bool:
        """Acquire a token, blocking if necessary"""
        deadline = time.monotonic() + timeout if timeout else float('inf')
        
        with self.lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_time
                self.last_time = now
                
                # Add tokens based on elapsed time
                self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                if now >= deadline:
                    return False
                
                # Wait for a token
                wait_time = min((1 - self.tokens) / self.rate, deadline - now)
                time.sleep(wait_time)


def rate_limit(
    calls: int,
    period: float,
    raise_on_limit: bool = True
):
    """
    Rate limiting decorator
    
    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds
        raise_on_limit: Whether to raise exception when rate limited
    
    Example:
        @rate_limit(calls=10, period=60)  # 10 calls per minute
        def api_call():
            ...
    """
    limiter = RateLimiter(rate=calls/period, burst=calls)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.acquire(timeout=period):
                if raise_on_limit:
                    raise RuntimeError(f"Rate limit exceeded for {func.__name__}")
                logger.warning(f"Rate limit exceeded for {func.__name__}, waiting...")
                limiter.acquire()  # Block until available
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def deprecated(message: str = None, version: str = None):
    """
    Mark function as deprecated
    
    Args:
        message: Custom deprecation message
        version: Version when function will be removed
    
    Example:
        @deprecated("Use new_function instead", version="2.0")
        def old_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warning_msg = f"{func.__name__} is deprecated."
            if message:
                warning_msg += f" {message}"
            if version:
                warning_msg += f" Will be removed in version {version}."
            
            import warnings
            warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)
            logger.warning(warning_msg)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def singleton(cls):
    """
    Singleton decorator for classes
    
    Example:
        @singleton
        class DatabaseConnection:
            ...
    """
    instances = {}
    lock = Lock()
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]
    
    return get_instance


def measure_memory(func: Callable) -> Callable:
    """
    Decorator to measure memory usage of a function
    
    Example:
        @measure_memory
        def memory_intensive_function():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            import tracemalloc
            tracemalloc.start()
            
            result = func(*args, **kwargs)
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            logger.info(
                f"{func.__name__} memory usage: "
                f"current={current / 1024 / 1024:.2f}MB, "
                f"peak={peak / 1024 / 1024:.2f}MB"
            )
            
            return result
        except ImportError:
            logger.warning("tracemalloc not available, skipping memory measurement")
            return func(*args, **kwargs)
    
    return wrapper
