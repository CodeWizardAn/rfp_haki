"""
Performance Optimizer

Automated optimization recommendations with:
- Best practices analysis
- Configuration optimization
- Code pattern detection
- Actionable recommendations
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class OptimizationCategory(Enum):
    """Categories of optimizations"""
    CACHING = "caching"
    DATABASE = "database"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    CODE_PATTERN = "code_pattern"
    ARCHITECTURE = "architecture"


class Priority(Enum):
    """Optimization priority"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Effort(Enum):
    """Implementation effort"""
    TRIVIAL = "trivial"  # < 1 hour
    SMALL = "small"  # < 1 day
    MEDIUM = "medium"  # < 1 week
    LARGE = "large"  # > 1 week


@dataclass
class Recommendation:
    """A performance optimization recommendation"""
    id: str
    title: str
    description: str
    category: OptimizationCategory
    priority: Priority
    effort: Effort
    
    # Impact estimation
    expected_improvement: str  # e.g., "20-30% reduction in response time"
    confidence: float  # 0.0-1.0
    
    # Details
    current_state: str
    recommended_action: str
    implementation_steps: List[str] = field(default_factory=list)
    code_example: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass 
class AnalysisContext:
    """Context for optimization analysis"""
    # Metrics
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    error_rate: float = 0.0
    requests_per_second: float = 0.0
    
    # Resources
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    
    # Database
    slow_queries_count: int = 0
    cache_hit_rate: float = 0.0
    connection_pool_usage: float = 0.0
    
    # Application
    active_threads: int = 0
    queue_depth: int = 0
    
    # Custom metrics
    custom: Dict[str, Any] = field(default_factory=dict)


class Analyzer(ABC):
    """Base class for performance analyzers"""
    
    @abstractmethod
    def analyze(self, context: AnalysisContext) -> List[Recommendation]:
        """Analyze and return recommendations"""
        pass


class CachingAnalyzer(Analyzer):
    """Analyzes caching opportunities"""
    
    def analyze(self, context: AnalysisContext) -> List[Recommendation]:
        recommendations = []
        
        # Check cache hit rate
        if context.cache_hit_rate < 0.7:
            recommendations.append(Recommendation(
                id="cache-001",
                title="Improve Cache Hit Rate",
                description=f"Current cache hit rate is {context.cache_hit_rate:.1%}, "
                           "below the recommended 70% threshold.",
                category=OptimizationCategory.CACHING,
                priority=Priority.HIGH,
                effort=Effort.MEDIUM,
                expected_improvement="10-20% reduction in response time",
                confidence=0.8,
                current_state=f"Cache hit rate: {context.cache_hit_rate:.1%}",
                recommended_action="Increase cache TTL, add more items to cache, "
                                  "or implement cache warming",
                implementation_steps=[
                    "Identify frequently accessed data patterns",
                    "Increase cache TTL for stable data",
                    "Implement cache warming on startup",
                    "Add caching for database query results",
                    "Monitor cache eviction patterns"
                ],
                code_example='''
# Example: Add caching for database queries
from performance.redis_cache import cache_result

@cache_result(ttl=300)  # Cache for 5 minutes
def get_product_details(product_id: str):
    return db.query(Product).get(product_id)
''',
                tags=["caching", "performance", "database"]
            ))
        
        # Check if caching is being used at all
        if context.cache_hit_rate == 0.0 and context.requests_per_second > 100:
            recommendations.append(Recommendation(
                id="cache-002",
                title="Implement Caching Layer",
                description="No caching detected for a high-traffic application",
                category=OptimizationCategory.CACHING,
                priority=Priority.CRITICAL,
                effort=Effort.MEDIUM,
                expected_improvement="30-50% reduction in response time",
                confidence=0.9,
                current_state="No caching layer detected",
                recommended_action="Implement Redis or in-memory caching",
                implementation_steps=[
                    "Set up Redis or Memcached server",
                    "Add caching library to application",
                    "Identify cacheable endpoints and data",
                    "Implement cache invalidation strategy",
                    "Add cache monitoring"
                ],
                tags=["caching", "architecture"]
            ))
        
        return recommendations


class DatabaseAnalyzer(Analyzer):
    """Analyzes database performance"""
    
    def analyze(self, context: AnalysisContext) -> List[Recommendation]:
        recommendations = []
        
        # Check for slow queries
        if context.slow_queries_count > 10:
            recommendations.append(Recommendation(
                id="db-001",
                title="Optimize Slow Database Queries",
                description=f"{context.slow_queries_count} slow queries detected",
                category=OptimizationCategory.DATABASE,
                priority=Priority.HIGH,
                effort=Effort.MEDIUM,
                expected_improvement="20-40% reduction in query time",
                confidence=0.85,
                current_state=f"Slow queries: {context.slow_queries_count}",
                recommended_action="Add indexes, optimize query structure, "
                                  "or consider query caching",
                implementation_steps=[
                    "Enable slow query logging",
                    "Analyze EXPLAIN plans for slow queries",
                    "Add missing indexes",
                    "Refactor N+1 query patterns",
                    "Consider query result caching"
                ],
                code_example='''
# Example: Add index for frequently filtered column
# SQL: CREATE INDEX idx_orders_status ON orders(status);

# Using SQLAlchemy
from performance.db_indexing import IndexManager

index_manager = IndexManager(engine)
index_manager.create_index('orders', ['status'])
''',
                tags=["database", "queries", "indexing"]
            ))
        
        # Check connection pool usage
        if context.connection_pool_usage > 0.8:
            recommendations.append(Recommendation(
                id="db-002",
                title="Increase Connection Pool Size",
                description="Connection pool is near capacity",
                category=OptimizationCategory.DATABASE,
                priority=Priority.HIGH,
                effort=Effort.TRIVIAL,
                expected_improvement="Prevent connection wait times",
                confidence=0.9,
                current_state=f"Pool usage: {context.connection_pool_usage:.1%}",
                recommended_action="Increase pool size or optimize connection usage",
                implementation_steps=[
                    "Increase max pool size by 50%",
                    "Ensure connections are properly released",
                    "Consider connection pooling middleware"
                ],
                tags=["database", "connections"]
            ))
        
        return recommendations


class ResourceAnalyzer(Analyzer):
    """Analyzes resource utilization"""
    
    def analyze(self, context: AnalysisContext) -> List[Recommendation]:
        recommendations = []
        
        # High CPU usage
        if context.cpu_usage > 80:
            recommendations.append(Recommendation(
                id="cpu-001",
                title="Address High CPU Usage",
                description=f"CPU usage at {context.cpu_usage:.1f}%",
                category=OptimizationCategory.CPU,
                priority=Priority.HIGH,
                effort=Effort.MEDIUM,
                expected_improvement="Improved system stability",
                confidence=0.8,
                current_state=f"CPU: {context.cpu_usage:.1f}%",
                recommended_action="Profile CPU usage, optimize hot paths, "
                                  "or scale horizontally",
                implementation_steps=[
                    "Profile application to find CPU hotspots",
                    "Optimize identified hot code paths",
                    "Consider async processing for CPU-bound tasks",
                    "Evaluate horizontal scaling options"
                ],
                tags=["cpu", "scaling", "profiling"]
            ))
        
        # High memory usage
        if context.memory_usage > 85:
            recommendations.append(Recommendation(
                id="mem-001",
                title="Address High Memory Usage",
                description=f"Memory usage at {context.memory_usage:.1f}%",
                category=OptimizationCategory.MEMORY,
                priority=Priority.HIGH,
                effort=Effort.MEDIUM,
                expected_improvement="Reduced risk of OOM errors",
                confidence=0.8,
                current_state=f"Memory: {context.memory_usage:.1f}%",
                recommended_action="Profile memory, check for leaks, "
                                  "optimize data structures",
                implementation_steps=[
                    "Enable memory profiling",
                    "Check for memory leaks",
                    "Review large object allocations",
                    "Consider streaming for large data sets",
                    "Optimize cache eviction policies"
                ],
                tags=["memory", "leaks", "optimization"]
            ))
        
        return recommendations


class ResponseTimeAnalyzer(Analyzer):
    """Analyzes response time patterns"""
    
    def analyze(self, context: AnalysisContext) -> List[Recommendation]:
        recommendations = []
        
        # High response time
        if context.avg_response_time_ms > 500:
            recommendations.append(Recommendation(
                id="latency-001",
                title="Reduce Average Response Time",
                description=f"Average response time is {context.avg_response_time_ms:.0f}ms",
                category=OptimizationCategory.CODE_PATTERN,
                priority=Priority.HIGH,
                effort=Effort.MEDIUM,
                expected_improvement="50%+ reduction in response time",
                confidence=0.75,
                current_state=f"Avg response: {context.avg_response_time_ms:.0f}ms",
                recommended_action="Profile endpoints, add caching, "
                                  "optimize database queries",
                implementation_steps=[
                    "Profile slowest endpoints",
                    "Add response caching where appropriate",
                    "Optimize N+1 database queries",
                    "Consider async processing for heavy operations",
                    "Implement connection pooling"
                ],
                tags=["latency", "response-time", "profiling"]
            ))
        
        # High P95/P50 ratio indicates inconsistent performance
        if context.p95_response_time_ms > 0 and context.avg_response_time_ms > 0:
            ratio = context.p95_response_time_ms / context.avg_response_time_ms
            
            if ratio > 3:
                recommendations.append(Recommendation(
                    id="latency-002",
                    title="Address Response Time Variability",
                    description=f"P95 ({context.p95_response_time_ms:.0f}ms) is {ratio:.1f}x "
                               f"higher than average ({context.avg_response_time_ms:.0f}ms)",
                    category=OptimizationCategory.CODE_PATTERN,
                    priority=Priority.MEDIUM,
                    effort=Effort.MEDIUM,
                    expected_improvement="More consistent response times",
                    confidence=0.7,
                    current_state=f"P95/Avg ratio: {ratio:.1f}x",
                    recommended_action="Identify and fix outlier requests",
                    implementation_steps=[
                        "Log slow request patterns",
                        "Check for intermittent external service issues",
                        "Review garbage collection patterns",
                        "Investigate lock contention"
                    ],
                    tags=["latency", "consistency", "outliers"]
                ))
        
        return recommendations


class ErrorRateAnalyzer(Analyzer):
    """Analyzes error patterns"""
    
    def analyze(self, context: AnalysisContext) -> List[Recommendation]:
        recommendations = []
        
        if context.error_rate > 0.01:  # > 1%
            priority = Priority.CRITICAL if context.error_rate > 0.05 else Priority.HIGH
            
            recommendations.append(Recommendation(
                id="error-001",
                title="Reduce Error Rate",
                description=f"Error rate is {context.error_rate:.2%}",
                category=OptimizationCategory.CODE_PATTERN,
                priority=priority,
                effort=Effort.MEDIUM,
                expected_improvement="Improved reliability",
                confidence=0.9,
                current_state=f"Error rate: {context.error_rate:.2%}",
                recommended_action="Analyze error logs, implement retry logic, "
                                  "add circuit breakers",
                implementation_steps=[
                    "Analyze error patterns by type",
                    "Implement retry with exponential backoff",
                    "Add circuit breakers for external services",
                    "Improve error handling and recovery",
                    "Add health checks for dependencies"
                ],
                code_example='''
# Example: Circuit breaker pattern
from performance.rate_limiter import TokenBucket

circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30
)

def call_external_service():
    if not circuit_breaker.is_closed():
        raise ServiceUnavailable("Circuit open")
    try:
        result = external_api.call()
        circuit_breaker.record_success()
        return result
    except Exception as e:
        circuit_breaker.record_failure()
        raise
''',
                tags=["errors", "reliability", "circuit-breaker"]
            ))
        
        return recommendations


class PerformanceOptimizer:
    """
    Main optimizer that coordinates all analyzers
    """
    
    def __init__(self):
        self._analyzers: List[Analyzer] = [
            CachingAnalyzer(),
            DatabaseAnalyzer(),
            ResourceAnalyzer(),
            ResponseTimeAnalyzer(),
            ErrorRateAnalyzer()
        ]
        self._recommendations: List[Recommendation] = []
        self._lock = threading.Lock()
        
        logger.info("PerformanceOptimizer initialized")
    
    def add_analyzer(self, analyzer: Analyzer):
        """Add a custom analyzer"""
        self._analyzers.append(analyzer)
    
    def analyze(self, context: AnalysisContext) -> List[Recommendation]:
        """
        Run all analyzers and return recommendations
        
        Args:
            context: Current system metrics
            
        Returns:
            List of recommendations sorted by priority
        """
        all_recommendations = []
        
        for analyzer in self._analyzers:
            try:
                recs = analyzer.analyze(context)
                all_recommendations.extend(recs)
            except Exception as e:
                logger.error(f"Analyzer {type(analyzer).__name__} failed: {e}")
        
        # Sort by priority
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        
        all_recommendations.sort(key=lambda r: priority_order.get(r.priority, 99))
        
        with self._lock:
            self._recommendations = all_recommendations
        
        logger.info(f"Generated {len(all_recommendations)} recommendations")
        return all_recommendations
    
    def get_recommendations(self, 
                           category: OptimizationCategory = None,
                           min_priority: Priority = None) -> List[Recommendation]:
        """Get filtered recommendations"""
        with self._lock:
            recs = list(self._recommendations)
        
        if category:
            recs = [r for r in recs if r.category == category]
        
        if min_priority:
            priority_order = {
                Priority.CRITICAL: 0,
                Priority.HIGH: 1,
                Priority.MEDIUM: 2,
                Priority.LOW: 3
            }
            min_order = priority_order.get(min_priority, 99)
            recs = [r for r in recs if priority_order.get(r.priority, 99) <= min_order]
        
        return recs
    
    def get_summary(self) -> Dict[str, Any]:
        """Get optimization summary"""
        with self._lock:
            recs = list(self._recommendations)
        
        by_category = {}
        for rec in recs:
            cat = rec.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        by_priority = {}
        for rec in recs:
            pri = rec.priority.value
            by_priority[pri] = by_priority.get(pri, 0) + 1
        
        return {
            'total_recommendations': len(recs),
            'by_category': by_category,
            'by_priority': by_priority,
            'top_recommendations': [
                {
                    'id': r.id,
                    'title': r.title,
                    'category': r.category.value,
                    'priority': r.priority.value,
                    'effort': r.effort.value,
                    'expected_improvement': r.expected_improvement
                }
                for r in recs[:5]
            ]
        }
    
    def get_action_plan(self) -> List[Dict[str, Any]]:
        """Generate prioritized action plan"""
        with self._lock:
            recs = list(self._recommendations)
        
        # Group by effort for sprint planning
        quick_wins = [r for r in recs if r.effort == Effort.TRIVIAL and r.priority in (Priority.CRITICAL, Priority.HIGH)]
        short_term = [r for r in recs if r.effort == Effort.SMALL and r.priority in (Priority.CRITICAL, Priority.HIGH)]
        medium_term = [r for r in recs if r.effort in (Effort.MEDIUM, Effort.SMALL) and r.priority == Priority.MEDIUM]
        long_term = [r for r in recs if r.effort == Effort.LARGE]
        
        return [
            {
                'phase': 'Quick Wins (This Week)',
                'items': [{'id': r.id, 'title': r.title, 'effort': r.effort.value} for r in quick_wins]
            },
            {
                'phase': 'Short Term (Next Sprint)',
                'items': [{'id': r.id, 'title': r.title, 'effort': r.effort.value} for r in short_term]
            },
            {
                'phase': 'Medium Term (Next Quarter)',
                'items': [{'id': r.id, 'title': r.title, 'effort': r.effort.value} for r in medium_term]
            },
            {
                'phase': 'Long Term (Roadmap)',
                'items': [{'id': r.id, 'title': r.title, 'effort': r.effort.value} for r in long_term]
            }
        ]
    
    def export_report(self, format: str = 'markdown') -> str:
        """Export recommendations as report"""
        with self._lock:
            recs = list(self._recommendations)
        
        if format == 'markdown':
            return self._export_markdown(recs)
        else:
            return str(recs)
    
    def _export_markdown(self, recs: List[Recommendation]) -> str:
        """Export as markdown"""
        lines = [
            "# Performance Optimization Report",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"\nTotal Recommendations: {len(recs)}",
            "\n## Summary",
        ]
        
        # Summary stats
        summary = self.get_summary()
        lines.append("\n### By Priority")
        for pri, count in summary['by_priority'].items():
            lines.append(f"- **{pri}**: {count}")
        
        lines.append("\n### By Category")
        for cat, count in summary['by_category'].items():
            lines.append(f"- **{cat}**: {count}")
        
        # Detailed recommendations
        lines.append("\n## Recommendations\n")
        
        for i, rec in enumerate(recs, 1):
            lines.extend([
                f"### {i}. {rec.title}",
                f"\n**ID:** {rec.id}",
                f"**Category:** {rec.category.value}",
                f"**Priority:** {rec.priority.value}",
                f"**Effort:** {rec.effort.value}",
                f"\n**Description:** {rec.description}",
                f"\n**Current State:** {rec.current_state}",
                f"\n**Recommended Action:** {rec.recommended_action}",
                f"\n**Expected Improvement:** {rec.expected_improvement}",
                f"**Confidence:** {rec.confidence:.0%}",
                "\n**Implementation Steps:**"
            ])
            
            for step in rec.implementation_steps:
                lines.append(f"1. {step}")
            
            if rec.code_example:
                lines.extend([
                    "\n**Code Example:**",
                    "```python",
                    rec.code_example.strip(),
                    "```"
                ])
            
            lines.append("\n---\n")
        
        return "\n".join(lines)


def analyze_and_recommend(metrics: Dict[str, float]) -> List[Recommendation]:
    """
    Convenience function to analyze metrics and get recommendations
    
    Args:
        metrics: Dictionary of metric values
        
    Returns:
        List of recommendations
    """
    context = AnalysisContext(
        avg_response_time_ms=metrics.get('avg_response_time_ms', 0),
        p95_response_time_ms=metrics.get('p95_response_time_ms', 0),
        error_rate=metrics.get('error_rate', 0),
        requests_per_second=metrics.get('requests_per_second', 0),
        cpu_usage=metrics.get('cpu_usage', 0),
        memory_usage=metrics.get('memory_usage', 0),
        slow_queries_count=metrics.get('slow_queries_count', 0),
        cache_hit_rate=metrics.get('cache_hit_rate', 0),
        connection_pool_usage=metrics.get('connection_pool_usage', 0)
    )
    
    optimizer = PerformanceOptimizer()
    return optimizer.analyze(context)
