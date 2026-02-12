"""
Agent Performance Integration
=============================
Integrates performance optimizations into the agent system.

Provides:
- Agent operation caching
- Performance tracking per agent
- Parallel agent execution
- Rate limiting for agent calls
"""

import logging
import time
import functools
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Try to import performance module
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from performance.integration import (
        get_performance_manager,
        cached,
        rate_limited,
        profiled,
        with_timeout,
        AgentPerformanceTracker,
        EmbeddingPerformanceOptimizer
    )
    from performance.batch_processor import BatchProcessor, BatchConfig
    from performance.async_ops import AsyncExecutor
    
    PERFORMANCE_AVAILABLE = True
    logger.info("Performance module loaded for agents")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Performance module not available: {e}")


class AgentPerformanceManager:
    """
    Manages performance tracking and optimization for all agents
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._agent_trackers: Dict[str, 'AgentPerformanceTracker'] = {}
        self._embedding_optimizer = None
        self._batch_processor = None
        self._async_executor = None
        
        if PERFORMANCE_AVAILABLE:
            try:
                self._embedding_optimizer = EmbeddingPerformanceOptimizer()
            except Exception as e:
                logger.warning(f"Could not initialize EmbeddingPerformanceOptimizer: {e}")
            try:
                self._batch_processor = BatchProcessor(BatchConfig(batch_size=50, max_workers=4))
            except Exception as e:
                logger.warning(f"Could not initialize BatchProcessor: {e}")
            try:
                self._async_executor = AsyncExecutor(max_workers=8)
                self._async_executor.start()
            except Exception as e:
                logger.warning(f"Could not initialize AsyncExecutor: {e}")
        
        logger.info("AgentPerformanceManager initialized")
    
    def get_tracker(self, agent_name: str) -> Optional['AgentPerformanceTracker']:
        """Get or create a performance tracker for an agent"""
        if not PERFORMANCE_AVAILABLE:
            return None
        
        if agent_name not in self._agent_trackers:
            self._agent_trackers[agent_name] = AgentPerformanceTracker(agent_name)
        
        return self._agent_trackers[agent_name]
    
    def get_embedding_optimizer(self) -> Optional['EmbeddingPerformanceOptimizer']:
        """Get embedding optimizer"""
        return self._embedding_optimizer
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get stats for all agents"""
        stats = {}
        for name, tracker in self._agent_trackers.items():
            stats[name] = tracker.get_stats()
        return stats
    
    def batch_process(self, items: List[Any], processor: Callable) -> Any:
        """Process items in batches"""
        if self._batch_processor:
            return self._batch_processor.process(items, processor)
        
        # Fallback to sequential processing
        return [processor(item) for item in items]
    
    def async_execute(self, func: Callable, *args, **kwargs):
        """Execute function asynchronously"""
        if self._async_executor:
            return self._async_executor.submit(func, *args, **kwargs)
        
        # Fallback to sync execution
        return func(*args, **kwargs)
    
    def shutdown(self):
        """Shutdown the performance manager"""
        if self._async_executor:
            self._async_executor.stop()


# Global instance
_agent_perf_manager: Optional[AgentPerformanceManager] = None


def get_agent_perf_manager() -> AgentPerformanceManager:
    """Get the global agent performance manager"""
    global _agent_perf_manager
    if _agent_perf_manager is None:
        _agent_perf_manager = AgentPerformanceManager()
    return _agent_perf_manager


# =============================================================================
# Decorators for Agent Methods
# =============================================================================

def track_agent_operation(operation_name: str = None):
    """
    Decorator to track agent operation performance
    
    Args:
        operation_name: Name of the operation (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            op_name = operation_name or func.__name__
            
            # Get agent name from self
            agent_name = getattr(self, 'name', None) or \
                         getattr(self, 'agent_name', None) or \
                         self.__class__.__name__
            
            manager = get_agent_perf_manager()
            tracker = manager.get_tracker(agent_name)
            
            if tracker:
                with tracker.track_operation(op_name):
                    return func(self, *args, **kwargs)
            else:
                return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def cache_agent_result(ttl: int = 3600, key_func: Callable = None):
    """
    Decorator to cache agent results
    
    Args:
        ttl: Cache TTL in seconds
        key_func: Function to generate cache key from args
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not PERFORMANCE_AVAILABLE:
                return func(self, *args, **kwargs)
            
            # Get agent name
            agent_name = getattr(self, 'name', None) or \
                         getattr(self, 'agent_name', None) or \
                         self.__class__.__name__
            
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            manager = get_agent_perf_manager()
            tracker = manager.get_tracker(agent_name)
            
            if tracker:
                # Check cache
                cached = tracker.get_cached_result(key)
                if cached is not None:
                    return cached
                
                # Execute and cache
                result = func(self, *args, **kwargs)
                tracker.cache_result(key, result, ttl)
                return result
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_agent(calls_per_minute: int = 60):
    """
    Rate limit agent calls
    
    Args:
        calls_per_minute: Maximum calls per minute
    """
    if not PERFORMANCE_AVAILABLE:
        return lambda f: f
    
    return rate_limited(requests_per_minute=calls_per_minute)


def timeout_agent(seconds: float = 30.0):
    """
    Add timeout to agent operation
    
    Args:
        seconds: Timeout in seconds
    """
    if not PERFORMANCE_AVAILABLE:
        return lambda f: f
    
    return with_timeout(seconds)


# =============================================================================
# Optimized Embedding Operations for Agents
# =============================================================================

class AgentEmbeddingHelper:
    """
    Helper class for optimized embedding operations in agents
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.manager = get_agent_perf_manager()
        self.optimizer = self.manager.get_embedding_optimizer()
    
    def get_embedding(self, text: str, embed_func: Callable) -> List[float]:
        """
        Get or compute embedding with caching
        
        Args:
            text: Text to embed
            embed_func: Function to compute embedding
            
        Returns:
            Embedding vector
        """
        if self.optimizer:
            return self.optimizer.get_or_compute_embedding(text, embed_func)
        
        return embed_func(text)
    
    def batch_embed(self, texts: List[str], embed_func: Callable) -> List[List[float]]:
        """
        Batch compute embeddings with caching
        
        Args:
            texts: List of texts
            embed_func: Function to compute embeddings
            
        Returns:
            List of embeddings
        """
        if self.optimizer:
            return self.optimizer.batch_embed(texts, embed_func)
        
        return embed_func(texts)
    
    def similarity_search(self, query_embedding: List[float],
                          embeddings: List[List[float]],
                          top_k: int = 10) -> List[int]:
        """
        Parallel similarity search
        
        Args:
            query_embedding: Query vector
            embeddings: List of vectors to search
            top_k: Number of top results
            
        Returns:
            Indices of top_k most similar
        """
        if self.optimizer:
            return self.optimizer.parallel_similarity_search(
                query_embedding, embeddings, top_k
            )
        
        # Fallback to sequential search
        def cosine_sim(emb):
            dot = sum(a * b for a, b in zip(query_embedding, emb))
            norm_q = sum(a * a for a in query_embedding) ** 0.5
            norm_e = sum(a * a for a in emb) ** 0.5
            return dot / (norm_q * norm_e) if norm_q and norm_e else 0
        
        scores = [(i, cosine_sim(emb)) for i, emb in enumerate(embeddings)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in scores[:top_k]]


# =============================================================================
# Agent Communication Performance
# =============================================================================

class OptimizedMessageQueue:
    """
    Performance-optimized message queue for inter-agent communication
    """
    
    def __init__(self):
        self.manager = get_agent_perf_manager()
        
        if PERFORMANCE_AVAILABLE:
            from performance.request_queue import PriorityRequestQueue, Priority
            self._queue = PriorityRequestQueue(max_size=10000)
            self._priority_map = {
                'critical': Priority.CRITICAL,
                'high': Priority.HIGH,
                'normal': Priority.NORMAL,
                'low': Priority.LOW,
                'background': Priority.BACKGROUND
            }
        else:
            self._queue = None
            self._priority_map = {}
    
    def enqueue(self, message: Dict[str, Any], priority: str = 'normal') -> bool:
        """
        Enqueue a message with priority
        
        Args:
            message: Message to enqueue
            priority: Priority level (critical, high, normal, low, background)
            
        Returns:
            True if enqueued successfully
        """
        if not self._queue:
            return False
        
        from performance.request_queue import QueuedRequest
        
        request = QueuedRequest(
            id=message.get('id', str(time.time())),
            priority=self._priority_map.get(priority, self._priority_map['normal']),
            payload=message
        )
        
        return self._queue.enqueue(request)
    
    def dequeue(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Dequeue a message
        
        Args:
            timeout: Max time to wait
            
        Returns:
            Message or None
        """
        if not self._queue:
            return None
        
        request = self._queue.dequeue(timeout=timeout)
        return request.payload if request else None
    
    def size(self) -> int:
        """Get queue size"""
        return self._queue.size() if self._queue else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        if self._queue:
            return self._queue.get_stats()
        return {}


# Export
__all__ = [
    'AgentPerformanceManager',
    'get_agent_perf_manager',
    'get_agent_performance_manager',  # Alias
    'track_agent_operation',
    'cache_agent_result',
    'rate_limit_agent',
    'timeout_agent',
    'AgentEmbeddingHelper',
    'OptimizedMessageQueue',
    'PERFORMANCE_AVAILABLE'
]

# Alias for compatibility
get_agent_performance_manager = get_agent_perf_manager
