"""
Database Performance Integration
================================
Integrates performance optimizations into database operations.

Provides:
- Optimized connection pooling
- Query caching and optimization
- Index recommendations
- Batch database operations
"""

import logging
import time
import functools
from typing import Any, Callable, Dict, List, Optional, Generator
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Try to import performance module
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from performance.integration import (
        get_performance_manager,
        DatabasePerformanceIntegration,
        cached,
        profiled
    )
    from performance.query_optimizer import QueryOptimizer, QueryPlan
    from performance.db_indexing import IndexManager, IndexRecommendation
    from performance.connection_pool import (
        DatabasePool, PoolConfig, PoolStats, ConnectionPoolManager
    )
    from performance.batch_processor import BatchProcessor, BatchConfig
    
    PERFORMANCE_AVAILABLE = True
    logger.info("Performance module loaded for database")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Performance module not available: {e}")


class OptimizedDatabaseManager:
    """
    Enhanced database manager with performance optimizations
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
        self._pools: Dict[str, DatabasePool] = {}
        self._query_optimizer = None
        self._index_manager = None
        self._query_cache = {}
        self._query_stats = {
            'total_queries': 0,
            'cached_queries': 0,
            'slow_queries': 0,
            'avg_query_time_ms': 0
        }
        
        if PERFORMANCE_AVAILABLE:
            self._query_optimizer = QueryOptimizer(slow_query_threshold=100.0)
            self._index_manager = IndexManager()
        
        logger.info("OptimizedDatabaseManager initialized")
    
    def create_pool(self, name: str, db_url: str,
                    min_size: int = 2, max_size: int = 10) -> Optional['DatabasePool']:
        """
        Create an optimized connection pool
        
        Args:
            name: Pool name
            db_url: Database URL
            min_size: Minimum connections
            max_size: Maximum connections
            
        Returns:
            DatabasePool instance or None
        """
        if not PERFORMANCE_AVAILABLE:
            logger.warning("Performance not available, using standard connections")
            return None
        
        config = PoolConfig(
            min_size=min_size,
            max_size=max_size,
            max_overflow=5,
            timeout=30.0,
            recycle=3600,
            pre_ping=True
        )
        
        pool = DatabasePool(db_url, config)
        pool.start()
        self._pools[name] = pool
        
        logger.info(f"Created connection pool '{name}' with {min_size}-{max_size} connections")
        return pool
    
    def get_pool(self, name: str) -> Optional['DatabasePool']:
        """Get a connection pool by name"""
        return self._pools.get(name)
    
    @contextmanager
    def connection(self, pool_name: str = 'default'):
        """
        Get a connection from the pool
        
        Args:
            pool_name: Name of the connection pool
            
        Yields:
            Database connection
        """
        pool = self._pools.get(pool_name)
        
        if not pool:
            raise ValueError(f"Pool '{pool_name}' not found")
        
        start = time.time()
        conn = pool.get()
        
        try:
            yield conn.connection
        finally:
            pool.put(conn)
            elapsed = (time.time() - start) * 1000
            logger.debug(f"Connection used for {elapsed:.2f}ms")
    
    def analyze_query(self, query: str) -> Optional['QueryPlan']:
        """
        Analyze a SQL query for optimization
        
        Args:
            query: SQL query to analyze
            
        Returns:
            QueryPlan with optimization hints
        """
        if not self._query_optimizer:
            return None
        
        return self._query_optimizer.analyze(query)
    
    def execute_optimized(self, conn, query: str, params: tuple = None,
                          cache_ttl: int = 0) -> Any:
        """
        Execute a query with optimization and optional caching
        
        Args:
            conn: Database connection
            query: SQL query
            params: Query parameters
            cache_ttl: Cache TTL in seconds (0 = no cache)
            
        Returns:
            Query result
        """
        self._query_stats['total_queries'] += 1
        
        # Check cache for SELECT queries
        if cache_ttl > 0 and query.strip().upper().startswith('SELECT'):
            cache_key = f"{query}:{str(params)}"
            cached = self._query_cache.get(cache_key)
            
            if cached and cached['expires'] > time.time():
                self._query_stats['cached_queries'] += 1
                return cached['result']
        
        # Analyze query
        if self._query_optimizer:
            plan = self._query_optimizer.analyze(query)
            
            if plan.warnings:
                logger.warning(f"Query warnings: {plan.warnings}")
        
        # Execute query
        start = time.time()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        elapsed = (time.time() - start) * 1000
        
        # Track slow queries
        if elapsed > 100:
            self._query_stats['slow_queries'] += 1
            logger.warning(f"Slow query ({elapsed:.2f}ms): {query[:100]}...")
        
        # Update average
        alpha = 0.1
        self._query_stats['avg_query_time_ms'] = (
            alpha * elapsed + (1 - alpha) * self._query_stats['avg_query_time_ms']
        )
        
        # Cache result
        if cache_ttl > 0 and query.strip().upper().startswith('SELECT'):
            cache_key = f"{query}:{str(params)}"
            self._query_cache[cache_key] = {
                'result': result,
                'expires': time.time() + cache_ttl
            }
        
        return result
    
    def get_index_recommendations(self, table_name: str = None) -> List[Dict[str, Any]]:
        """
        Get index recommendations
        
        Args:
            table_name: Specific table or None for all
            
        Returns:
            List of index recommendations
        """
        if not self._index_manager:
            return []
        
        recommendations = self._index_manager.recommend(table_name)
        
        return [
            {
                'table': rec.table_name,
                'columns': rec.columns,
                'type': rec.index_type,
                'reason': rec.reason,
                'estimated_improvement': rec.estimated_improvement
            }
            for rec in recommendations
        ]
    
    def batch_insert(self, conn, table: str, rows: List[Dict[str, Any]],
                     batch_size: int = 100) -> int:
        """
        Batch insert rows with optimization
        
        Args:
            conn: Database connection
            table: Table name
            rows: List of row dictionaries
            batch_size: Rows per batch
            
        Returns:
            Number of rows inserted
        """
        if not rows:
            return 0
        
        # Get columns from first row
        columns = list(rows[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join(columns)
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        cursor = conn.cursor()
        total_inserted = 0
        
        # Process in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            values = [tuple(row[col] for col in columns) for row in batch]
            
            cursor.executemany(query, values)
            total_inserted += len(batch)
        
        conn.commit()
        logger.info(f"Batch inserted {total_inserted} rows into {table}")
        
        return total_inserted
    
    def batch_update(self, conn, table: str, updates: List[Dict[str, Any]],
                     key_column: str, batch_size: int = 100) -> int:
        """
        Batch update rows with optimization
        
        Args:
            conn: Database connection
            table: Table name
            updates: List of update dictionaries (must include key column)
            key_column: Primary key column name
            batch_size: Rows per batch
            
        Returns:
            Number of rows updated
        """
        if not updates:
            return 0
        
        cursor = conn.cursor()
        total_updated = 0
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            for row in batch:
                key_value = row[key_column]
                set_columns = [f"{col} = ?" for col in row.keys() if col != key_column]
                set_values = [row[col] for col in row.keys() if col != key_column]
                
                query = f"UPDATE {table} SET {', '.join(set_columns)} WHERE {key_column} = ?"
                cursor.execute(query, (*set_values, key_value))
                total_updated += 1
        
        conn.commit()
        logger.info(f"Batch updated {total_updated} rows in {table}")
        
        return total_updated
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        stats = dict(self._query_stats)
        stats['pools'] = {}
        
        for name, pool in self._pools.items():
            pool_stats = pool.get_stats()
            stats['pools'][name] = pool_stats
        
        stats['cache_size'] = len(self._query_cache)
        
        return stats
    
    def clear_cache(self):
        """Clear query cache"""
        self._query_cache.clear()
        logger.info("Query cache cleared")
    
    def close_all(self):
        """Close all connection pools"""
        for name, pool in self._pools.items():
            pool.close()
            logger.info(f"Closed pool '{name}'")
        
        self._pools.clear()


# Global instance
_db_perf_manager: Optional[OptimizedDatabaseManager] = None


def get_optimized_db_manager() -> OptimizedDatabaseManager:
    """Get the global optimized database manager"""
    global _db_perf_manager
    if _db_perf_manager is None:
        _db_perf_manager = OptimizedDatabaseManager()
    return _db_perf_manager


# =============================================================================
# Decorators for Database Operations
# =============================================================================

def cached_query(ttl: int = 300):
    """
    Cache query results decorator
    
    Args:
        ttl: Cache TTL in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            if key in cache:
                entry = cache[key]
                if entry['expires'] > time.time():
                    return entry['result']
            
            # Execute and cache
            result = func(*args, **kwargs)
            cache[key] = {
                'result': result,
                'expires': time.time() + ttl
            }
            
            return result
        
        return wrapper
    return decorator


def track_query_performance(func: Callable) -> Callable:
    """Track query performance decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            raise
        finally:
            elapsed = (time.time() - start) * 1000
            
            if elapsed > 100:
                logger.warning(f"Slow database operation: {func.__name__} took {elapsed:.2f}ms")
        
        return result
    
    return wrapper


def batch_operation(batch_size: int = 100):
    """
    Batch database operations decorator
    
    Args:
        batch_size: Number of items per batch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(items: List, *args, **kwargs):
            results = []
            total = len(items) if hasattr(items, '__len__') else 0
            
            # Process in batches
            for i in range(0, total, batch_size):
                batch = items[i:i + batch_size]
                try:
                    batch_result = func(batch, *args, **kwargs)
                    if batch_result:
                        results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
                except Exception as e:
                    logger.error(f"Batch operation failed at index {i}: {e}")
                    raise
            
            return results
        return wrapper
    return decorator


def get_db_performance():
    """Get the database performance manager singleton"""
    return get_optimized_db_manager()


# =============================================================================
# SQLAlchemy Integration
# =============================================================================

def create_optimized_engine(db_url: str, **kwargs):
    """
    Create an optimized SQLAlchemy engine
    
    Args:
        db_url: Database URL
        **kwargs: Additional engine arguments
        
    Returns:
        SQLAlchemy engine
    """
    from sqlalchemy import create_engine, event
    
    # Default optimized settings
    engine_kwargs = {
        'pool_size': kwargs.get('pool_size', 5),
        'max_overflow': kwargs.get('max_overflow', 10),
        'pool_timeout': kwargs.get('pool_timeout', 30),
        'pool_recycle': kwargs.get('pool_recycle', 3600),
        'pool_pre_ping': kwargs.get('pool_pre_ping', True),
        'echo': kwargs.get('echo', False)
    }
    
    # SQLite doesn't support connection pooling args
    if 'sqlite' in db_url:
        engine_kwargs = {
            'echo': kwargs.get('echo', False)
        }
    
    engine = create_engine(db_url, **engine_kwargs)
    
    # Add query timing listener
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters,
                               context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters,
                              context, executemany):
        start_times = conn.info.get('query_start_time', [])
        if start_times:
            elapsed = (time.time() - start_times.pop()) * 1000
            
            if elapsed > 100:
                logger.warning(f"Slow query ({elapsed:.2f}ms): {statement[:100]}...")
    
    logger.info(f"Created optimized SQLAlchemy engine for {db_url.split('?')[0]}")
    return engine


# Export
__all__ = [
    'OptimizedDatabaseManager',
    'get_optimized_db_manager',
    'get_db_performance',
    'cached_query',
    'batch_operation',
    'track_query_performance',
    'create_optimized_engine',
    'PERFORMANCE_AVAILABLE'
]
