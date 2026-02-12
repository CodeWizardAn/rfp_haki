"""
Query Optimization

SQL query analysis and optimization with:
- Query plan analysis
- Index usage recommendations
- Query rewriting
- N+1 detection
- Slow query identification
"""

import re
import time
import logging
import hashlib
import threading
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of SQL queries"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    OTHER = "other"


class OptimizationHint(Enum):
    """Query optimization hints"""
    ADD_INDEX = "add_index"
    USE_COVERING_INDEX = "use_covering_index"
    AVOID_SELECT_STAR = "avoid_select_star"
    USE_LIMIT = "use_limit"
    AVOID_SUBQUERY = "avoid_subquery"
    USE_JOIN = "use_join"
    USE_EXISTS = "use_exists"
    ADD_WHERE_CLAUSE = "add_where_clause"
    PAGINATE_RESULTS = "paginate_results"
    USE_BATCH_INSERT = "use_batch_insert"
    AVOID_DISTINCT = "avoid_distinct"
    USE_UNION_ALL = "use_union_all"


@dataclass
class QueryPlan:
    """Query execution plan"""
    query: str
    query_type: QueryType
    estimated_rows: int = 0
    estimated_cost: float = 0.0
    uses_index: bool = True
    index_names: List[str] = field(default_factory=list)
    tables_accessed: List[str] = field(default_factory=list)
    join_types: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    hints: List[OptimizationHint] = field(default_factory=list)
    
    def is_optimal(self) -> bool:
        """Check if query plan is optimal"""
        return self.uses_index and len(self.warnings) == 0


@dataclass
class QueryStats:
    """Statistics for a query pattern"""
    query_hash: str
    query_pattern: str
    execution_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    last_executed: Optional[datetime] = None
    
    def add_execution(self, time_ms: float):
        """Record query execution"""
        self.execution_count += 1
        self.total_time_ms += time_ms
        self.min_time_ms = min(self.min_time_ms, time_ms)
        self.max_time_ms = max(self.max_time_ms, time_ms)
        self.avg_time_ms = self.total_time_ms / self.execution_count
        self.last_executed = datetime.now()


class QueryOptimizer:
    """
    SQL Query Optimizer with analysis and recommendations
    """
    
    def __init__(self, slow_query_threshold_ms: float = 100.0,
                 enable_query_logging: bool = True):
        """
        Initialize query optimizer
        
        Args:
            slow_query_threshold_ms: Threshold for slow query detection
            enable_query_logging: Enable query execution logging
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.enable_query_logging = enable_query_logging
        
        self._query_stats: Dict[str, QueryStats] = {}
        self._slow_queries: List[Tuple[str, float, datetime]] = []
        self._n_plus_one_patterns: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
        
        # Patterns for query analysis
        self._patterns = {
            'select_star': re.compile(r'\bSELECT\s+\*\s+FROM', re.IGNORECASE),
            'no_where': re.compile(r'\bFROM\s+\w+\s*(?:;|$)', re.IGNORECASE),
            'subquery': re.compile(r'\(\s*SELECT', re.IGNORECASE),
            'like_leading_wildcard': re.compile(r"LIKE\s+['\"]%", re.IGNORECASE),
            'or_condition': re.compile(r'\bOR\b', re.IGNORECASE),
            'not_in': re.compile(r'\bNOT\s+IN\b', re.IGNORECASE),
            'distinct': re.compile(r'\bSELECT\s+DISTINCT\b', re.IGNORECASE),
            'order_by': re.compile(r'\bORDER\s+BY\b', re.IGNORECASE),
            'group_by': re.compile(r'\bGROUP\s+BY\b', re.IGNORECASE),
            'having': re.compile(r'\bHAVING\b', re.IGNORECASE),
            'join': re.compile(r'\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b', re.IGNORECASE),
            'limit': re.compile(r'\bLIMIT\b', re.IGNORECASE),
            'union': re.compile(r'\bUNION\b', re.IGNORECASE),
        }
        
        logger.info(f"QueryOptimizer initialized with slow_threshold={slow_query_threshold_ms}ms")
    
    def _get_query_type(self, query: str) -> QueryType:
        """Determine query type"""
        query_upper = query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        elif query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        else:
            return QueryType.OTHER
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query"""
        tables = []
        
        # FROM clause
        from_match = re.search(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        if from_match:
            tables.append(from_match.group(1))
        
        # JOIN clauses
        join_matches = re.findall(r'\bJOIN\s+(\w+)', query, re.IGNORECASE)
        tables.extend(join_matches)
        
        # INTO clause (for INSERT)
        into_match = re.search(r'\bINTO\s+(\w+)', query, re.IGNORECASE)
        if into_match:
            tables.append(into_match.group(1))
        
        # UPDATE clause
        update_match = re.search(r'\bUPDATE\s+(\w+)', query, re.IGNORECASE)
        if update_match:
            tables.append(update_match.group(1))
        
        return list(set(tables))
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query pattern"""
        # Normalize query: remove specific values
        normalized = re.sub(r"'[^']*'", "'?'", query)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip().lower()
        
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def analyze(self, query: str) -> QueryPlan:
        """
        Analyze a SQL query and provide optimization recommendations
        
        Args:
            query: SQL query to analyze
            
        Returns:
            QueryPlan with analysis results
        """
        query_type = self._get_query_type(query)
        tables = self._extract_tables(query)
        
        plan = QueryPlan(
            query=query,
            query_type=query_type,
            tables_accessed=tables
        )
        
        # Check for common issues
        hints = []
        warnings = []
        
        # SELECT * detection
        if self._patterns['select_star'].search(query):
            hints.append(OptimizationHint.AVOID_SELECT_STAR)
            warnings.append("SELECT * used - consider selecting specific columns")
        
        # Missing WHERE clause
        if query_type == QueryType.SELECT:
            if not re.search(r'\bWHERE\b', query, re.IGNORECASE):
                if not self._patterns['limit'].search(query):
                    hints.append(OptimizationHint.ADD_WHERE_CLAUSE)
                    warnings.append("No WHERE clause - may return too many rows")
        
        # Subquery detection
        if self._patterns['subquery'].search(query):
            hints.append(OptimizationHint.AVOID_SUBQUERY)
            warnings.append("Subquery detected - consider using JOIN")
        
        # LIKE with leading wildcard
        if self._patterns['like_leading_wildcard'].search(query):
            warnings.append("LIKE with leading wildcard cannot use index")
            plan.uses_index = False
        
        # NOT IN detection
        if self._patterns['not_in'].search(query):
            hints.append(OptimizationHint.USE_EXISTS)
            warnings.append("NOT IN detected - consider using NOT EXISTS")
        
        # Missing LIMIT
        if query_type == QueryType.SELECT and not self._patterns['limit'].search(query):
            hints.append(OptimizationHint.USE_LIMIT)
            warnings.append("Consider adding LIMIT for large result sets")
        
        # DISTINCT detection
        if self._patterns['distinct'].search(query):
            hints.append(OptimizationHint.AVOID_DISTINCT)
            warnings.append("DISTINCT may indicate data model issue")
        
        # Detect join types
        join_matches = re.findall(
            r'\b(INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\b', 
            query, 
            re.IGNORECASE
        )
        plan.join_types = [j[0].upper() if j[0] else 'INNER' for j in join_matches if j]
        
        plan.hints = hints
        plan.warnings = warnings
        
        return plan
    
    def record_execution(self, query: str, execution_time_ms: float):
        """
        Record query execution for statistics
        
        Args:
            query: Executed query
            execution_time_ms: Execution time in milliseconds
        """
        if not self.enable_query_logging:
            return
        
        query_hash = self._hash_query(query)
        
        with self._lock:
            if query_hash not in self._query_stats:
                self._query_stats[query_hash] = QueryStats(
                    query_hash=query_hash,
                    query_pattern=query[:200]  # Truncate for storage
                )
            
            self._query_stats[query_hash].add_execution(execution_time_ms)
            
            # Track slow queries
            if execution_time_ms > self.slow_query_threshold_ms:
                self._slow_queries.append((query, execution_time_ms, datetime.now()))
                # Keep only last 100 slow queries
                if len(self._slow_queries) > 100:
                    self._slow_queries = self._slow_queries[-100:]
                
                logger.warning(f"Slow query ({execution_time_ms:.2f}ms): {query[:100]}...")
    
    def detect_n_plus_one(self, query: str, context_id: str = None):
        """
        Detect N+1 query patterns
        
        Args:
            query: Query to check
            context_id: Request/transaction context ID
        """
        if context_id is None:
            return
        
        query_hash = self._hash_query(query)
        pattern_key = f"{context_id}:{query_hash}"
        
        with self._lock:
            self._n_plus_one_patterns[pattern_key] += 1
            
            # N+1 pattern if same query executed many times in same context
            if self._n_plus_one_patterns[pattern_key] == 5:
                logger.warning(
                    f"Possible N+1 query detected in context {context_id}: {query[:100]}..."
                )
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slowest queries"""
        with self._lock:
            sorted_stats = sorted(
                self._query_stats.values(),
                key=lambda x: x.avg_time_ms,
                reverse=True
            )
            
            return [
                {
                    'query_pattern': s.query_pattern,
                    'execution_count': s.execution_count,
                    'avg_time_ms': s.avg_time_ms,
                    'max_time_ms': s.max_time_ms,
                    'total_time_ms': s.total_time_ms
                }
                for s in sorted_stats[:limit]
            ]
    
    def get_frequent_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most frequently executed queries"""
        with self._lock:
            sorted_stats = sorted(
                self._query_stats.values(),
                key=lambda x: x.execution_count,
                reverse=True
            )
            
            return [
                {
                    'query_pattern': s.query_pattern,
                    'execution_count': s.execution_count,
                    'avg_time_ms': s.avg_time_ms,
                    'total_time_ms': s.total_time_ms
                }
                for s in sorted_stats[:limit]
            ]
    
    def optimize_query(self, query: str) -> Tuple[str, List[str]]:
        """
        Attempt to optimize a query
        
        Args:
            query: Original query
            
        Returns:
            Tuple of (optimized_query, applied_optimizations)
        """
        optimizations = []
        optimized = query
        
        # Remove SELECT * and replace with column list placeholder
        if self._patterns['select_star'].search(query):
            # Note: In real implementation, would need schema info
            optimizations.append("Consider replacing SELECT * with specific columns")
        
        # Add LIMIT if missing on SELECT
        if self._get_query_type(query) == QueryType.SELECT:
            if not self._patterns['limit'].search(query):
                if not self._patterns['group_by'].search(query):
                    optimized = optimized.rstrip(';') + ' LIMIT 1000;'
                    optimizations.append("Added LIMIT 1000")
        
        # Suggest index for WHERE columns
        where_match = re.search(r'\bWHERE\s+(\w+)', query, re.IGNORECASE)
        if where_match:
            column = where_match.group(1)
            optimizations.append(f"Consider index on column: {column}")
        
        return optimized, optimizations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        with self._lock:
            return {
                'total_queries_logged': len(self._query_stats),
                'slow_queries_count': len(self._slow_queries),
                'n_plus_one_patterns': len(self._n_plus_one_patterns),
                'slow_query_threshold_ms': self.slow_query_threshold_ms
            }
    
    def reset_stats(self):
        """Reset all statistics"""
        with self._lock:
            self._query_stats.clear()
            self._slow_queries.clear()
            self._n_plus_one_patterns.clear()


class QueryProfiler:
    """Context manager for profiling query execution"""
    
    def __init__(self, optimizer: QueryOptimizer, query: str, context_id: str = None):
        self.optimizer = optimizer
        self.query = query
        self.context_id = context_id
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.optimizer.record_execution(self.query, elapsed_ms)
        self.optimizer.detect_n_plus_one(self.query, self.context_id)
        return False


def profile_query(optimizer: QueryOptimizer = None, context_id: str = None):
    """
    Decorator for profiling database query functions
    
    Args:
        optimizer: QueryOptimizer instance
        context_id: Optional context ID for N+1 detection
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            opt = optimizer or QueryOptimizer()
            
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            # Try to get query from args or result
            query = kwargs.get('query', str(args[0]) if args else 'unknown')
            
            opt.record_execution(query, elapsed_ms)
            opt.detect_n_plus_one(query, context_id)
            
            return result
        
        return wrapper
    return decorator
