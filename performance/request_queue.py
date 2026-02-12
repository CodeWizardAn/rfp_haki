"""
Request Queue

Priority-based request queuing with:
- Multiple priority levels
- Fair scheduling
- Backpressure handling
- Queue monitoring
"""

import logging
import threading
import queue
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from concurrent.futures import ThreadPoolExecutor, Future
import heapq

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    """Request priority levels (lower number = higher priority)"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class QueuedRequest:
    """A queued request"""
    id: str
    priority: Priority
    payload: Any
    callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None  # Max wait time in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if request has exceeded deadline"""
        if self.deadline is None:
            return False
        return time.time() - self.created_at > self.deadline
    
    def __lt__(self, other):
        """Compare for priority queue ordering"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at


@dataclass
class QueueStats:
    """Queue statistics"""
    total_queued: int = 0
    total_processed: int = 0
    total_rejected: int = 0
    total_expired: int = 0
    current_size: int = 0
    avg_wait_time_ms: float = 0.0
    max_wait_time_ms: float = 0.0
    by_priority: Dict[str, int] = field(default_factory=dict)


@dataclass
class QueueConfig:
    """Request queue configuration"""
    max_size: int = 10000
    max_size_per_priority: Dict[Priority, int] = None
    default_deadline: Optional[float] = 30.0  # 30 seconds
    reject_on_full: bool = True  # Reject or block when full
    num_workers: int = 4
    worker_timeout: float = 60.0


class PriorityRequestQueue:
    """
    Priority-based request queue
    """
    
    def __init__(self, config: QueueConfig = None):
        self.config = config or QueueConfig()
        
        self._queue: List[QueuedRequest] = []
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        
        # Stats
        self._stats = QueueStats()
        self._priority_counts: Dict[Priority, int] = {p: 0 for p in Priority}
        self._wait_times: List[float] = []
        
        # Request tracking
        self._requests: Dict[str, QueuedRequest] = {}
        
        logger.info(f"PriorityRequestQueue initialized: max_size={self.config.max_size}")
    
    def enqueue(self, request: QueuedRequest, timeout: float = None) -> bool:
        """
        Add request to queue
        
        Args:
            request: Request to queue
            timeout: Max time to wait if queue is full
            
        Returns:
            True if enqueued, False if rejected
        """
        with self._not_full:
            # Check size limits
            if len(self._queue) >= self.config.max_size:
                if self.config.reject_on_full:
                    self._stats.total_rejected += 1
                    logger.warning(f"Queue full, rejecting request {request.id}")
                    return False
                
                # Wait for space
                if not self._not_full.wait(timeout):
                    self._stats.total_rejected += 1
                    return False
            
            # Check per-priority limits
            if self.config.max_size_per_priority:
                limit = self.config.max_size_per_priority.get(request.priority)
                if limit and self._priority_counts.get(request.priority, 0) >= limit:
                    self._stats.total_rejected += 1
                    return False
            
            # Set default deadline
            if request.deadline is None and self.config.default_deadline:
                request.deadline = self.config.default_deadline
            
            # Add to queue
            heapq.heappush(self._queue, request)
            self._requests[request.id] = request
            self._priority_counts[request.priority] = \
                self._priority_counts.get(request.priority, 0) + 1
            
            self._stats.total_queued += 1
            self._stats.current_size = len(self._queue)
            self._stats.by_priority[request.priority.name] = \
                self._priority_counts[request.priority]
            
            self._not_empty.notify()
            
            logger.debug(f"Enqueued request {request.id} with priority {request.priority.name}")
            return True
    
    def dequeue(self, timeout: float = None) -> Optional[QueuedRequest]:
        """
        Get next request from queue
        
        Args:
            timeout: Max time to wait for request
            
        Returns:
            QueuedRequest or None
        """
        with self._not_empty:
            while True:
                # Remove expired requests
                self._cleanup_expired()
                
                if self._queue:
                    request = heapq.heappop(self._queue)
                    
                    if request.id in self._requests:
                        del self._requests[request.id]
                    
                    self._priority_counts[request.priority] = \
                        max(0, self._priority_counts.get(request.priority, 1) - 1)
                    
                    # Record wait time
                    wait_time = (time.time() - request.created_at) * 1000
                    self._wait_times.append(wait_time)
                    if len(self._wait_times) > 1000:
                        self._wait_times = self._wait_times[-1000:]
                    
                    self._stats.total_processed += 1
                    self._stats.current_size = len(self._queue)
                    self._stats.avg_wait_time_ms = sum(self._wait_times) / len(self._wait_times)
                    self._stats.max_wait_time_ms = max(self._wait_times) if self._wait_times else 0
                    
                    self._not_full.notify()
                    return request
                
                if not self._not_empty.wait(timeout):
                    return None
    
    def _cleanup_expired(self):
        """Remove expired requests"""
        expired = [r for r in self._queue if r.is_expired()]
        
        for request in expired:
            self._queue.remove(request)
            if request.id in self._requests:
                del self._requests[request.id]
            self._priority_counts[request.priority] = \
                max(0, self._priority_counts.get(request.priority, 1) - 1)
            self._stats.total_expired += 1
            logger.debug(f"Request {request.id} expired")
        
        if expired:
            heapq.heapify(self._queue)
    
    def cancel(self, request_id: str) -> bool:
        """Cancel a queued request"""
        with self._lock:
            if request_id in self._requests:
                request = self._requests[request_id]
                self._queue.remove(request)
                heapq.heapify(self._queue)
                del self._requests[request_id]
                self._priority_counts[request.priority] = \
                    max(0, self._priority_counts.get(request.priority, 1) - 1)
                self._stats.current_size = len(self._queue)
                logger.debug(f"Cancelled request {request_id}")
                return True
            return False
    
    def get_position(self, request_id: str) -> Optional[int]:
        """Get position of request in queue"""
        with self._lock:
            if request_id not in self._requests:
                return None
            
            request = self._requests[request_id]
            sorted_queue = sorted(self._queue)
            
            for i, r in enumerate(sorted_queue):
                if r.id == request_id:
                    return i
            return None
    
    def peek(self) -> Optional[QueuedRequest]:
        """Peek at next request without removing"""
        with self._lock:
            if self._queue:
                return self._queue[0]
            return None
    
    def size(self) -> int:
        """Get current queue size"""
        with self._lock:
            return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.size() == 0
    
    def clear(self):
        """Clear all queued requests"""
        with self._lock:
            self._queue.clear()
            self._requests.clear()
            self._priority_counts = {p: 0 for p in Priority}
            self._stats.current_size = 0
    
    def get_stats(self) -> QueueStats:
        """Get queue statistics"""
        with self._lock:
            return QueueStats(
                total_queued=self._stats.total_queued,
                total_processed=self._stats.total_processed,
                total_rejected=self._stats.total_rejected,
                total_expired=self._stats.total_expired,
                current_size=len(self._queue),
                avg_wait_time_ms=self._stats.avg_wait_time_ms,
                max_wait_time_ms=self._stats.max_wait_time_ms,
                by_priority={p.name: c for p, c in self._priority_counts.items()}
            )


class RequestQueueWorker:
    """
    Worker that processes requests from queue
    """
    
    def __init__(self, request_queue: PriorityRequestQueue,
                 handler: Callable[[QueuedRequest], Any],
                 config: QueueConfig = None):
        self.queue = request_queue
        self.handler = handler
        self.config = config or QueueConfig()
        
        self._running = False
        self._workers: List[threading.Thread] = []
        self._results: Dict[str, Any] = {}
    
    def start(self):
        """Start worker threads"""
        self._running = True
        
        for i in range(self.config.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"QueueWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
        
        logger.info(f"Started {self.config.num_workers} queue workers")
    
    def stop(self, timeout: float = 10.0):
        """Stop worker threads"""
        self._running = False
        
        for worker in self._workers:
            worker.join(timeout=timeout / len(self._workers))
        
        self._workers.clear()
        logger.info("Queue workers stopped")
    
    def _worker_loop(self):
        """Worker thread loop"""
        while self._running:
            try:
                request = self.queue.dequeue(timeout=1.0)
                
                if request:
                    self._process_request(request)
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def _process_request(self, request: QueuedRequest):
        """Process a single request"""
        try:
            result = self.handler(request)
            self._results[request.id] = result
            
            if request.callback:
                request.callback(request, result, None)
                
        except Exception as e:
            logger.error(f"Error processing request {request.id}: {e}")
            
            if request.callback:
                request.callback(request, None, e)
    
    def get_result(self, request_id: str) -> Optional[Any]:
        """Get result for a processed request"""
        return self._results.get(request_id)


class FairScheduler:
    """
    Fair scheduler that prevents starvation
    
    Uses aging to promote old low-priority requests
    """
    
    def __init__(self, aging_interval: float = 5.0,
                 max_age_promotions: int = 2):
        """
        Initialize fair scheduler
        
        Args:
            aging_interval: Seconds before priority bump
            max_age_promotions: Max number of priority bumps
        """
        self.aging_interval = aging_interval
        self.max_age_promotions = max_age_promotions
        
        self._queues: Dict[Priority, List[QueuedRequest]] = {
            p: [] for p in Priority
        }
        self._lock = threading.Lock()
        self._promotions: Dict[str, int] = {}
    
    def enqueue(self, request: QueuedRequest):
        """Add request to fair scheduler"""
        with self._lock:
            heapq.heappush(self._queues[request.priority], request)
            self._promotions[request.id] = 0
    
    def dequeue(self) -> Optional[QueuedRequest]:
        """Get next request with aging applied"""
        with self._lock:
            self._apply_aging()
            
            for priority in Priority:
                if self._queues[priority]:
                    request = heapq.heappop(self._queues[priority])
                    if request.id in self._promotions:
                        del self._promotions[request.id]
                    return request
            
            return None
    
    def _apply_aging(self):
        """Promote old requests to higher priority"""
        now = time.time()
        
        for priority in list(Priority)[1:]:  # Skip CRITICAL
            to_promote = []
            
            for request in self._queues[priority]:
                age = now - request.created_at
                promotions = self._promotions.get(request.id, 0)
                
                expected_promotions = int(age / self.aging_interval)
                
                if expected_promotions > promotions and promotions < self.max_age_promotions:
                    to_promote.append(request)
            
            for request in to_promote:
                self._queues[priority].remove(request)
                
                new_priority = Priority(priority.value - 1)
                self._queues[new_priority].append(request)
                heapq.heapify(self._queues[new_priority])
                
                self._promotions[request.id] = self._promotions.get(request.id, 0) + 1
                
                logger.debug(f"Promoted request {request.id} to {new_priority.name}")
            
            if to_promote:
                heapq.heapify(self._queues[priority])


class BackpressureController:
    """
    Backpressure controller for managing load
    """
    
    def __init__(self, 
                 low_threshold: float = 0.5,
                 high_threshold: float = 0.8,
                 critical_threshold: float = 0.95):
        """
        Initialize backpressure controller
        
        Args:
            low_threshold: Queue fill ratio for low load
            high_threshold: Queue fill ratio for high load
            critical_threshold: Queue fill ratio for critical load
        """
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.critical_threshold = critical_threshold
        
        self._on_pressure_change: List[Callable] = []
    
    def on_pressure_change(self, callback: Callable):
        """Register callback for pressure changes"""
        self._on_pressure_change.append(callback)
    
    def check_pressure(self, current_size: int, max_size: int) -> str:
        """
        Check current backpressure level
        
        Returns:
            'low', 'medium', 'high', or 'critical'
        """
        fill_ratio = current_size / max_size if max_size > 0 else 0
        
        if fill_ratio >= self.critical_threshold:
            level = 'critical'
        elif fill_ratio >= self.high_threshold:
            level = 'high'
        elif fill_ratio >= self.low_threshold:
            level = 'medium'
        else:
            level = 'low'
        
        return level
    
    def should_accept(self, current_size: int, max_size: int,
                     request_priority: Priority) -> bool:
        """
        Check if a request should be accepted based on backpressure
        
        Higher priority requests are accepted even under pressure
        """
        level = self.check_pressure(current_size, max_size)
        
        if level == 'low':
            return True
        elif level == 'medium':
            return request_priority <= Priority.NORMAL
        elif level == 'high':
            return request_priority <= Priority.HIGH
        else:  # critical
            return request_priority == Priority.CRITICAL


class AsyncRequestQueue:
    """
    Async request queue with Future-based results
    """
    
    def __init__(self, config: QueueConfig = None):
        self.config = config or QueueConfig()
        
        self._queue = PriorityRequestQueue(config)
        self._executor = ThreadPoolExecutor(max_workers=self.config.num_workers)
        self._futures: Dict[str, Future] = {}
        self._lock = threading.Lock()
        
        self._running = False
        self._dispatcher: Optional[threading.Thread] = None
    
    def submit(self, request_id: str, priority: Priority,
               task: Callable, *args, **kwargs) -> Future:
        """
        Submit an async request
        
        Args:
            request_id: Unique request ID
            priority: Request priority
            task: Callable to execute
            *args, **kwargs: Arguments for task
            
        Returns:
            Future for the result
        """
        future = Future()
        
        request = QueuedRequest(
            id=request_id,
            priority=priority,
            payload={'task': task, 'args': args, 'kwargs': kwargs}
        )
        
        with self._lock:
            self._futures[request_id] = future
        
        if not self._queue.enqueue(request):
            future.set_exception(Exception("Queue full"))
        
        return future
    
    def start(self):
        """Start processing queue"""
        self._running = True
        self._dispatcher = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._dispatcher.start()
    
    def stop(self):
        """Stop processing"""
        self._running = False
        if self._dispatcher:
            self._dispatcher.join(timeout=5.0)
        self._executor.shutdown(wait=False)
    
    def _dispatch_loop(self):
        """Dispatch requests to executor"""
        while self._running:
            request = self._queue.dequeue(timeout=1.0)
            
            if request:
                self._executor.submit(self._process, request)
    
    def _process(self, request: QueuedRequest):
        """Process a request and set future result"""
        future = self._futures.get(request.id)
        if not future:
            return
        
        try:
            payload = request.payload
            result = payload['task'](*payload['args'], **payload['kwargs'])
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            with self._lock:
                if request.id in self._futures:
                    del self._futures[request.id]
