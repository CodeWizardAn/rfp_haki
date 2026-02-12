"""
Async Operations

Asynchronous task execution with:
- Event loop management
- Task scheduling and cancellation
- Async context managers
- Coroutine utilities
"""

import asyncio
import logging
import threading
import functools
import time
from typing import Any, Dict, List, Optional, Callable, Coroutine, TypeVar, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskState(Enum):
    """Task execution state"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Information about an async task"""
    task_id: str
    name: str
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AsyncExecutor:
    """
    Async task executor with event loop management
    """
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize async executor
        
        Args:
            max_workers: Maximum concurrent tasks
        """
        self.max_workers = max_workers
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._running = False
        
        self._tasks: Dict[str, TaskInfo] = {}
        self._task_counter = 0
        self._lock = threading.Lock()
        
        logger.info(f"AsyncExecutor initialized with max_workers={max_workers}")
    
    def start(self):
        """Start the executor with its own event loop"""
        if self._running:
            return
        
        self._running = True
        self._loop = asyncio.new_event_loop()
        self._semaphore = asyncio.Semaphore(self.max_workers)
        
        def run_loop():
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        
        logger.info("AsyncExecutor started")
    
    def stop(self):
        """Stop the executor"""
        if not self._running:
            return
        
        self._running = False
        
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if self._loop_thread:
            self._loop_thread.join(timeout=5.0)
        
        self._executor.shutdown(wait=True)
        
        logger.info("AsyncExecutor stopped")
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        with self._lock:
            self._task_counter += 1
            return f"task_{self._task_counter}_{int(time.time())}"
    
    def submit(self, coro: Coroutine, name: str = None) -> str:
        """
        Submit a coroutine for execution
        
        Args:
            coro: Coroutine to execute
            name: Optional task name
            
        Returns:
            Task ID
        """
        if not self._running:
            self.start()
        
        task_id = self._generate_task_id()
        task_info = TaskInfo(
            task_id=task_id,
            name=name or coro.__name__ if hasattr(coro, '__name__') else "anonymous"
        )
        
        with self._lock:
            self._tasks[task_id] = task_info
        
        async def wrapped():
            task_info.state = TaskState.RUNNING
            task_info.started_at = datetime.now()
            
            try:
                async with self._semaphore:
                    result = await coro
                    task_info.result = result
                    task_info.state = TaskState.COMPLETED
            except asyncio.CancelledError:
                task_info.state = TaskState.CANCELLED
            except Exception as e:
                task_info.error = str(e)
                task_info.state = TaskState.FAILED
                logger.error(f"Task {task_id} failed: {e}")
            finally:
                task_info.completed_at = datetime.now()
            
            return task_info.result
        
        asyncio.run_coroutine_threadsafe(wrapped(), self._loop)
        
        return task_id
    
    def submit_sync(self, func: Callable[..., T], *args, **kwargs) -> str:
        """
        Submit a synchronous function to run in thread pool
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Task ID
        """
        async def wrapper():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor,
                lambda: func(*args, **kwargs)
            )
        
        return self.submit(wrapper(), name=func.__name__ if hasattr(func, '__name__') else None)
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task info"""
        return self._tasks.get(task_id)
    
    def get_result(self, task_id: str, timeout: float = None) -> Any:
        """
        Wait for and get task result
        
        Args:
            task_id: Task ID
            timeout: Maximum wait time
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        start = time.time()
        
        while True:
            task_info = self._tasks.get(task_id)
            
            if not task_info:
                raise ValueError(f"Unknown task: {task_id}")
            
            if task_info.state == TaskState.COMPLETED:
                return task_info.result
            
            if task_info.state == TaskState.FAILED:
                raise Exception(task_info.error)
            
            if task_info.state == TaskState.CANCELLED:
                raise asyncio.CancelledError()
            
            if timeout and (time.time() - start) > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
            
            time.sleep(0.1)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        task_info = self._tasks.get(task_id)
        if task_info and task_info.state in (TaskState.PENDING, TaskState.RUNNING):
            task_info.state = TaskState.CANCELLED
            return True
        return False
    
    def run_many(self, coros: List[Coroutine], 
                 gather: bool = True) -> List[str]:
        """
        Submit multiple coroutines
        
        Args:
            coros: List of coroutines
            gather: Whether to wait for all
            
        Returns:
            List of task IDs
        """
        task_ids = [self.submit(coro) for coro in coros]
        return task_ids
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics"""
        with self._lock:
            states = {}
            for task in self._tasks.values():
                state = task.state.value
                states[state] = states.get(state, 0) + 1
            
            return {
                'total_tasks': len(self._tasks),
                'by_state': states,
                'max_workers': self.max_workers,
                'running': self._running
            }


class TaskManager:
    """
    High-level task manager for async operations
    """
    
    def __init__(self):
        self._executor = AsyncExecutor()
        self._scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def start(self):
        """Start the task manager"""
        self._executor.start()
    
    def stop(self):
        """Stop the task manager"""
        self._executor.stop()
    
    def run_async(self, coro: Coroutine, name: str = None) -> str:
        """Run an async coroutine"""
        return self._executor.submit(coro, name)
    
    def run_in_background(self, func: Callable, *args, **kwargs) -> str:
        """Run a function in background thread"""
        return self._executor.submit_sync(func, *args, **kwargs)
    
    def schedule_periodic(self, func: Callable, interval: float,
                         name: str = None) -> str:
        """
        Schedule a function to run periodically
        
        Args:
            func: Function to run
            interval: Interval in seconds
            name: Task name
            
        Returns:
            Schedule ID
        """
        schedule_id = self._executor._generate_task_id()
        
        async def periodic_runner():
            while schedule_id in self._scheduled_tasks:
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        await asyncio.get_event_loop().run_in_executor(None, func)
                except Exception as e:
                    logger.error(f"Periodic task {schedule_id} error: {e}")
                
                await asyncio.sleep(interval)
        
        with self._lock:
            self._scheduled_tasks[schedule_id] = {
                'name': name or func.__name__,
                'interval': interval,
                'started_at': datetime.now()
            }
        
        self._executor.submit(periodic_runner(), name=name)
        
        return schedule_id
    
    def cancel_scheduled(self, schedule_id: str) -> bool:
        """Cancel a scheduled task"""
        with self._lock:
            if schedule_id in self._scheduled_tasks:
                del self._scheduled_tasks[schedule_id]
                return True
            return False
    
    def wait_for(self, task_id: str, timeout: float = None) -> Any:
        """Wait for a task to complete"""
        return self._executor.get_result(task_id, timeout)
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information"""
        return self._executor.get_task(task_id)


def async_task(name: str = None, timeout: float = None):
    """
    Decorator to run a function as an async task
    
    Args:
        name: Task name
        timeout: Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = TaskManager()
            manager.start()
            
            if asyncio.iscoroutinefunction(func):
                task_id = manager.run_async(func(*args, **kwargs), name)
            else:
                task_id = manager.run_in_background(func, *args, **kwargs)
            
            return manager.wait_for(task_id, timeout)
        
        return wrapper
    return decorator


async def run_concurrent(*coros: Coroutine, 
                         return_exceptions: bool = False) -> List[Any]:
    """
    Run multiple coroutines concurrently
    
    Args:
        *coros: Coroutines to run
        return_exceptions: Whether to return exceptions instead of raising
        
    Returns:
        List of results
    """
    return await asyncio.gather(*coros, return_exceptions=return_exceptions)


async def run_with_timeout(coro: Coroutine, timeout: float) -> Any:
    """
    Run a coroutine with timeout
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        
    Returns:
        Coroutine result
        
    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    return await asyncio.wait_for(coro, timeout=timeout)


async def retry_async(coro_func: Callable[[], Coroutine],
                      max_retries: int = 3,
                      delay: float = 1.0,
                      backoff: float = 2.0) -> Any:
    """
    Retry an async operation with exponential backoff
    
    Args:
        coro_func: Function that returns a coroutine
        max_retries: Maximum retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        
    Returns:
        Result from successful execution
    """
    last_error = None
    current_delay = delay
    
    for attempt in range(max_retries):
        try:
            return await coro_func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff
    
    raise last_error


class AsyncContextManager:
    """
    Async context manager for resource management
    """
    
    def __init__(self, setup: Callable[[], Awaitable] = None,
                 cleanup: Callable[[], Awaitable] = None):
        self._setup = setup
        self._cleanup = cleanup
        self._resource = None
    
    async def __aenter__(self):
        if self._setup:
            self._resource = await self._setup()
        return self._resource
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._cleanup:
            await self._cleanup()
        return False


def make_async(func: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Convert a synchronous function to async
    
    Args:
        func: Synchronous function
        
    Returns:
        Async wrapper function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    return wrapper
