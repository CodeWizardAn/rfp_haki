"""
RFP Responser Performance Integration
=====================================
Integrates performance optimizations into RFP response operations.

Usage:
    from rfp_responser.perf_integration import init_rfp_performance
    
    # Initialize at app startup
    init_rfp_performance(app)
"""

import logging
import time
import functools
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import performance module
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from performance.integration import (
        get_performance_manager,
        init_performance,
        shutdown_performance,
        cached,
        rate_limited,
        profiled,
        integrate_flask_app,
        AgentPerformanceTracker,
        EmbeddingPerformanceOptimizer
    )
    from performance.batch_processor import BatchProcessor, BatchConfig
    from performance.request_queue import PriorityRequestQueue, QueuedRequest, Priority, QueueConfig
    
    PERFORMANCE_AVAILABLE = True
    logger.info("Performance module loaded for RFP Responser")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Performance module not available: {e}")


# =============================================================================
# RFP Processing Optimization
# =============================================================================

class RFPProcessingOptimizer:
    """
    Optimizes RFP processing and bid generation
    """
    
    def __init__(self):
        self.pm = None
        self._bid_cache = {}
        self._match_cache = {}
        self._pricing_cache = {}
        self._request_queue = None
        
        if PERFORMANCE_AVAILABLE:
            self.pm = get_performance_manager()
            try:
                self._request_queue = PriorityRequestQueue(QueueConfig(max_size=1000))
            except Exception as e:
                logger.warning(f"Could not initialize PriorityRequestQueue: {e}")
    
    def cache_bid(self, bid_id: str, bid_data: Dict[str, Any], ttl: int = 1800):
        """
        Cache bid data
        
        Args:
            bid_id: Bid identifier
            bid_data: Bid data dictionary
            ttl: Cache TTL in seconds
        """
        if self.pm:
            self.pm.cache.set(f"rfp:bid:{bid_id}", bid_data, ttl=ttl)
        else:
            self._bid_cache[bid_id] = {
                'data': bid_data,
                'expires': time.time() + ttl
            }
    
    def get_cached_bid(self, bid_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached bid data
        
        Args:
            bid_id: Bid identifier
            
        Returns:
            Bid data or None
        """
        if self.pm:
            return self.pm.cache.get(f"rfp:bid:{bid_id}")
        
        entry = self._bid_cache.get(bid_id)
        if entry and entry['expires'] > time.time():
            return entry['data']
        return None
    
    def cache_product_matches(self, rfp_id: str, matches: List[Dict[str, Any]], ttl: int = 3600):
        """
        Cache product matches for an RFP
        
        Args:
            rfp_id: RFP identifier
            matches: List of product matches
            ttl: Cache TTL in seconds
        """
        if self.pm:
            self.pm.cache.set(f"rfp:matches:{rfp_id}", matches, ttl=ttl)
        else:
            self._match_cache[rfp_id] = {
                'matches': matches,
                'expires': time.time() + ttl
            }
    
    def get_cached_matches(self, rfp_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached product matches
        
        Args:
            rfp_id: RFP identifier
            
        Returns:
            List of matches or None
        """
        if self.pm:
            return self.pm.cache.get(f"rfp:matches:{rfp_id}")
        
        entry = self._match_cache.get(rfp_id)
        if entry and entry['expires'] > time.time():
            return entry['matches']
        return None
    
    def cache_pricing(self, product_id: str, pricing: Dict[str, Any], ttl: int = 7200):
        """
        Cache product pricing
        
        Args:
            product_id: Product identifier
            pricing: Pricing data
            ttl: Cache TTL in seconds
        """
        if self.pm:
            self.pm.cache.set(f"rfp:pricing:{product_id}", pricing, ttl=ttl)
        else:
            self._pricing_cache[product_id] = {
                'pricing': pricing,
                'expires': time.time() + ttl
            }
    
    def get_cached_pricing(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached pricing
        
        Args:
            product_id: Product identifier
            
        Returns:
            Pricing data or None
        """
        if self.pm:
            return self.pm.cache.get(f"rfp:pricing:{product_id}")
        
        entry = self._pricing_cache.get(product_id)
        if entry and entry['expires'] > time.time():
            return entry['pricing']
        return None
    
    def queue_rfp_processing(self, rfp_data: Dict[str, Any], priority: str = 'normal') -> bool:
        """
        Queue RFP for processing
        
        Args:
            rfp_data: RFP data dictionary
            priority: Processing priority
            
        Returns:
            True if queued successfully
        """
        if not self._request_queue:
            return False
        
        priority_map = {
            'critical': Priority.CRITICAL,
            'high': Priority.HIGH,
            'normal': Priority.NORMAL,
            'low': Priority.LOW
        }
        
        request = QueuedRequest(
            id=rfp_data.get('rfp_id', str(time.time())),
            priority=priority_map.get(priority, Priority.NORMAL),
            payload=rfp_data
        )
        
        return self._request_queue.enqueue(request)
    
    def batch_calculate_pricing(self, items: List[Dict[str, Any]], 
                                 pricing_func: Callable) -> List[Dict[str, Any]]:
        """
        Batch calculate pricing for items
        
        Args:
            items: List of items to price
            pricing_func: Function to calculate pricing
            
        Returns:
            List of priced items
        """
        if PERFORMANCE_AVAILABLE:
            batch_processor = BatchProcessor(BatchConfig(batch_size=50, max_workers=4))
            result = batch_processor.process(items, pricing_func)
            return result.results
        
        return [pricing_func(item) for item in items]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RFP processing statistics"""
        stats = {
            'bid_cache_size': len(self._bid_cache),
            'match_cache_size': len(self._match_cache),
            'pricing_cache_size': len(self._pricing_cache)
        }
        
        if self._request_queue:
            stats['queue_size'] = self._request_queue.size()
            stats['queue_stats'] = self._request_queue.get_stats()
        
        return stats


# Global optimizer instance
_rfp_optimizer: Optional[RFPProcessingOptimizer] = None


def get_rfp_optimizer() -> RFPProcessingOptimizer:
    """Get the global RFP processing optimizer"""
    global _rfp_optimizer
    if _rfp_optimizer is None:
        _rfp_optimizer = RFPProcessingOptimizer()
    return _rfp_optimizer


# =============================================================================
# Flask Integration
# =============================================================================

def init_rfp_performance(app):
    """
    Initialize performance optimizations for RFP Responser Flask app
    
    Args:
        app: Flask application instance
    """
    if not PERFORMANCE_AVAILABLE:
        logger.warning("Performance module not available, skipping RFP optimization")
        return None
    
    # Integrate with Flask app
    pm = integrate_flask_app(app)
    
    # Initialize RFP optimizer
    optimizer = get_rfp_optimizer()
    
    # Add RFP-specific performance endpoints
    @app.route('/api/rfp/performance/stats')
    def rfp_performance_stats():
        from flask import jsonify
        
        return jsonify({
            'performance_enabled': True,
            'rfp_optimizer_stats': optimizer.get_stats(),
            'cache_stats': pm.cache.get_stats() if hasattr(pm.cache, 'get_stats') else {},
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/rfp/performance/clear-cache', methods=['POST'])
    def rfp_clear_cache():
        from flask import jsonify
        
        optimizer._bid_cache.clear()
        optimizer._match_cache.clear()
        optimizer._pricing_cache.clear()
        
        return jsonify({
            'status': 'success',
            'message': 'RFP caches cleared'
        })
    
    logger.info("RFP Responser performance integration complete")
    return pm


# =============================================================================
# Decorators for RFP Operations
# =============================================================================

def cache_bid_result(ttl: int = 1800):
    """
    Cache bid generation results
    
    Args:
        ttl: Cache TTL in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(bid_id: str, *args, **kwargs):
            optimizer = get_rfp_optimizer()
            
            # Check cache
            cached = optimizer.get_cached_bid(bid_id)
            if cached:
                logger.debug(f"Cache hit for bid: {bid_id}")
                return cached
            
            # Generate and cache
            result = func(bid_id, *args, **kwargs)
            optimizer.cache_bid(bid_id, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_matches(ttl: int = 3600):
    """
    Cache product match results
    
    Args:
        ttl: Cache TTL in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(rfp_id: str, *args, **kwargs):
            optimizer = get_rfp_optimizer()
            
            # Check cache
            cached = optimizer.get_cached_matches(rfp_id)
            if cached:
                logger.debug(f"Cache hit for matches: {rfp_id}")
                return cached
            
            # Match and cache
            result = func(rfp_id, *args, **kwargs)
            optimizer.cache_product_matches(rfp_id, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def rate_limit_bid_generation(requests_per_minute: int = 20):
    """
    Rate limit bid generation
    
    Args:
        requests_per_minute: Maximum bids per minute
    """
    if not PERFORMANCE_AVAILABLE:
        return lambda f: f
    
    return rate_limited(requests_per_minute=requests_per_minute)


# Export
__all__ = [
    'RFPProcessingOptimizer',
    'get_rfp_optimizer',
    'init_rfp_performance',
    'cache_bid_result',
    'cache_matches',
    'rate_limit_bid_generation',
    'PERFORMANCE_AVAILABLE'
]
