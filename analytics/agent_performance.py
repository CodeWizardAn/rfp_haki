"""
Agent Performance Tracker
Tracks and analyzes performance of AI agents

Features:
- Response time tracking
- Success/failure rates
- Resource usage monitoring
- Token consumption tracking
- Quality metrics
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging
import time

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, desc

from .models import AgentPerformanceMetric, TimeGranularity
from .metrics_collector import MetricsCollector, track_timing

logger = logging.getLogger(__name__)


class AgentPerformanceTracker:
    """
    Comprehensive agent performance tracking and analysis
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.collector = MetricsCollector()
        
        # In-memory tracking for current session
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        self._agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'requests_total': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'response_times': [],
            'tokens_used': 0,
            'errors': defaultdict(int)
        })
        self._aggregation_start = datetime.utcnow()
    
    # ==================== Request Tracking ====================
    
    def start_request(self, request_id: str, agent_type: str, 
                     agent_name: str = None) -> str:
        """Start tracking an agent request"""
        self._active_requests[request_id] = {
            'agent_type': agent_type,
            'agent_name': agent_name,
            'start_time': time.time(),
            'start_timestamp': datetime.utcnow()
        }
        
        self.collector.increment(f'agent.{agent_type}.requests.started')
        return request_id
    
    def end_request(self, request_id: str, success: bool = True,
                   tokens_used: int = 0, error_type: str = None,
                   confidence: float = None, metadata: Dict[str, Any] = None):
        """End tracking an agent request"""
        if request_id not in self._active_requests:
            logger.warning(f"No active request found for {request_id}")
            return
        
        request_data = self._active_requests.pop(request_id)
        duration_ms = (time.time() - request_data['start_time']) * 1000
        agent_type = request_data['agent_type']
        
        # Update in-memory stats
        stats = self._agent_stats[agent_type]
        stats['requests_total'] += 1
        stats['response_times'].append(duration_ms)
        stats['tokens_used'] += tokens_used
        
        if success:
            stats['requests_successful'] += 1
            self.collector.increment(f'agent.{agent_type}.requests.success')
        else:
            stats['requests_failed'] += 1
            self.collector.increment(f'agent.{agent_type}.requests.failed')
            if error_type:
                stats['errors'][error_type] += 1
        
        # Record metrics
        self.collector.timing(f'agent.{agent_type}.response_time', duration_ms)
        if tokens_used:
            self.collector.histogram(f'agent.{agent_type}.tokens', tokens_used)
        if confidence is not None:
            self.collector.histogram(f'agent.{agent_type}.confidence', confidence)
        
        # Keep response times limited
        if len(stats['response_times']) > 10000:
            stats['response_times'] = stats['response_times'][-10000:]
    
    def record_agent_metric(self, agent_type: str, 
                           period_start: datetime,
                           period_end: datetime,
                           requests_total: int = 0,
                           requests_successful: int = 0,
                           requests_failed: int = 0,
                           avg_response_time_ms: float = None,
                           p50_response_time_ms: float = None,
                           p95_response_time_ms: float = None,
                           p99_response_time_ms: float = None,
                           max_response_time_ms: float = None,
                           total_tokens_used: int = 0,
                           accuracy_rate: float = None,
                           confidence_avg: float = None,
                           error_types: Dict[str, int] = None,
                           agent_name: str = None,
                           agent_version: str = None,
                           granularity: TimeGranularity = TimeGranularity.HOUR) -> AgentPerformanceMetric:
        """Record aggregated agent performance metric"""
        
        metric_data = {
            'agent_type': agent_type,
            'agent_name': agent_name,
            'agent_version': agent_version,
            'period_start': period_start,
            'period_end': period_end,
            'granularity': granularity,
            'requests_total': requests_total,
            'requests_successful': requests_successful,
            'requests_failed': requests_failed,
            'avg_response_time_ms': avg_response_time_ms,
            'p50_response_time_ms': p50_response_time_ms,
            'p95_response_time_ms': p95_response_time_ms,
            'p99_response_time_ms': p99_response_time_ms,
            'max_response_time_ms': max_response_time_ms,
            'total_tokens_used': total_tokens_used,
            'accuracy_rate': accuracy_rate,
            'confidence_avg': confidence_avg,
            'error_types': error_types or {},
            'recorded_at': datetime.utcnow()
        }
        
        if self.session_factory:
            return self._save_metric(metric_data)
        
        return metric_data
    
    def _save_metric(self, metric_data: Dict[str, Any]) -> AgentPerformanceMetric:
        """Save metric to database"""
        session = self.session_factory()
        try:
            metric = AgentPerformanceMetric(**metric_data)
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()
    
    def flush_stats(self, granularity: TimeGranularity = TimeGranularity.HOUR):
        """Flush in-memory stats to database"""
        now = datetime.utcnow()
        
        for agent_type, stats in self._agent_stats.items():
            if stats['requests_total'] == 0:
                continue
            
            response_times = sorted(stats['response_times'])
            n = len(response_times)
            
            self.record_agent_metric(
                agent_type=agent_type,
                period_start=self._aggregation_start,
                period_end=now,
                granularity=granularity,
                requests_total=stats['requests_total'],
                requests_successful=stats['requests_successful'],
                requests_failed=stats['requests_failed'],
                avg_response_time_ms=sum(response_times) / n if n > 0 else None,
                p50_response_time_ms=response_times[int(n * 0.5)] if n > 0 else None,
                p95_response_time_ms=response_times[int(n * 0.95)] if n > 0 else None,
                p99_response_time_ms=response_times[min(int(n * 0.99), n - 1)] if n > 0 else None,
                max_response_time_ms=max(response_times) if response_times else None,
                total_tokens_used=stats['tokens_used'],
                error_types=dict(stats['errors'])
            )
        
        # Reset stats
        self._agent_stats.clear()
        self._aggregation_start = now
    
    # ==================== Analysis ====================
    
    def get_agent_summary(self, session: Session,
                         agent_type: str = None,
                         start_date: datetime = None,
                         end_date: datetime = None) -> Dict[str, Any]:
        """Get summary of agent performance"""
        query = session.query(AgentPerformanceMetric)
        
        if agent_type:
            query = query.filter(AgentPerformanceMetric.agent_type == agent_type)
        if start_date:
            query = query.filter(AgentPerformanceMetric.period_start >= start_date)
        if end_date:
            query = query.filter(AgentPerformanceMetric.period_end <= end_date)
        
        # Aggregate stats
        stats = session.query(
            func.sum(AgentPerformanceMetric.requests_total).label('total_requests'),
            func.sum(AgentPerformanceMetric.requests_successful).label('successful'),
            func.sum(AgentPerformanceMetric.requests_failed).label('failed'),
            func.avg(AgentPerformanceMetric.avg_response_time_ms).label('avg_response_time'),
            func.avg(AgentPerformanceMetric.p95_response_time_ms).label('avg_p95'),
            func.max(AgentPerformanceMetric.max_response_time_ms).label('max_response_time'),
            func.sum(AgentPerformanceMetric.total_tokens_used).label('total_tokens'),
            func.avg(AgentPerformanceMetric.accuracy_rate).label('avg_accuracy'),
            func.avg(AgentPerformanceMetric.confidence_avg).label('avg_confidence')
        ).filter(
            AgentPerformanceMetric.agent_type == agent_type if agent_type else True,
            AgentPerformanceMetric.period_start >= start_date if start_date else True,
            AgentPerformanceMetric.period_end <= end_date if end_date else True
        ).first()
        
        total = int(stats.total_requests or 0)
        successful = int(stats.successful or 0)
        failed = int(stats.failed or 0)
        
        return {
            'agent_type': agent_type,
            'total_requests': total,
            'successful_requests': successful,
            'failed_requests': failed,
            'success_rate': successful / total if total > 0 else 0,
            'avg_response_time_ms': float(stats.avg_response_time or 0),
            'p95_response_time_ms': float(stats.avg_p95 or 0),
            'max_response_time_ms': float(stats.max_response_time or 0),
            'total_tokens_used': int(stats.total_tokens or 0),
            'avg_accuracy': float(stats.avg_accuracy or 0),
            'avg_confidence': float(stats.avg_confidence or 0)
        }
    
    def get_all_agents_comparison(self, session: Session,
                                  start_date: datetime = None,
                                  end_date: datetime = None) -> List[Dict[str, Any]]:
        """Compare performance across all agents"""
        query = session.query(
            AgentPerformanceMetric.agent_type,
            func.sum(AgentPerformanceMetric.requests_total).label('total'),
            func.sum(AgentPerformanceMetric.requests_successful).label('successful'),
            func.avg(AgentPerformanceMetric.avg_response_time_ms).label('avg_time'),
            func.avg(AgentPerformanceMetric.p95_response_time_ms).label('p95_time'),
            func.sum(AgentPerformanceMetric.total_tokens_used).label('tokens'),
            func.avg(AgentPerformanceMetric.accuracy_rate).label('accuracy')
        ).group_by(AgentPerformanceMetric.agent_type)
        
        if start_date:
            query = query.filter(AgentPerformanceMetric.period_start >= start_date)
        if end_date:
            query = query.filter(AgentPerformanceMetric.period_end <= end_date)
        
        return [
            {
                'agent_type': row.agent_type,
                'total_requests': int(row.total or 0),
                'success_rate': int(row.successful or 0) / int(row.total) if row.total else 0,
                'avg_response_time_ms': float(row.avg_time or 0),
                'p95_response_time_ms': float(row.p95_time or 0),
                'total_tokens': int(row.tokens or 0),
                'avg_accuracy': float(row.accuracy or 0)
            }
            for row in query.all()
        ]
    
    def get_performance_trend(self, session: Session,
                             agent_type: str = None,
                             metric: str = 'requests',
                             granularity: str = 'day',
                             start_date: datetime = None,
                             end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get performance trend over time"""
        date_trunc = func.date_trunc(granularity, AgentPerformanceMetric.period_start)
        
        # Select metric
        if metric == 'requests':
            metric_col = func.sum(AgentPerformanceMetric.requests_total)
        elif metric == 'success_rate':
            metric_col = func.sum(AgentPerformanceMetric.requests_successful) / \
                        func.nullif(func.sum(AgentPerformanceMetric.requests_total), 0)
        elif metric == 'response_time':
            metric_col = func.avg(AgentPerformanceMetric.avg_response_time_ms)
        elif metric == 'tokens':
            metric_col = func.sum(AgentPerformanceMetric.total_tokens_used)
        else:
            metric_col = func.sum(AgentPerformanceMetric.requests_total)
        
        query = session.query(
            date_trunc.label('period'),
            metric_col.label('value')
        ).group_by(date_trunc).order_by(date_trunc)
        
        if agent_type:
            query = query.filter(AgentPerformanceMetric.agent_type == agent_type)
        if start_date:
            query = query.filter(AgentPerformanceMetric.period_start >= start_date)
        if end_date:
            query = query.filter(AgentPerformanceMetric.period_end <= end_date)
        
        return [
            {
                'period': row.period.isoformat() if row.period else None,
                'value': float(row.value or 0)
            }
            for row in query.all()
        ]
    
    def get_error_breakdown(self, session: Session,
                           agent_type: str = None,
                           start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """Get breakdown of errors by type"""
        query = session.query(AgentPerformanceMetric).filter(
            AgentPerformanceMetric.requests_failed > 0
        )
        
        if agent_type:
            query = query.filter(AgentPerformanceMetric.agent_type == agent_type)
        if start_date:
            query = query.filter(AgentPerformanceMetric.period_start >= start_date)
        if end_date:
            query = query.filter(AgentPerformanceMetric.period_end <= end_date)
        
        records = query.all()
        
        # Aggregate error types
        error_counts = defaultdict(int)
        total_errors = 0
        
        for record in records:
            if record.error_types:
                for error_type, count in record.error_types.items():
                    error_counts[error_type] += count
                    total_errors += count
        
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_errors': total_errors,
            'error_breakdown': [
                {
                    'error_type': e_type,
                    'count': count,
                    'percentage': count / total_errors if total_errors > 0 else 0
                }
                for e_type, count in sorted_errors
            ]
        }
    
    def get_token_usage_analysis(self, session: Session,
                                agent_type: str = None,
                                start_date: datetime = None,
                                end_date: datetime = None) -> Dict[str, Any]:
        """Analyze token usage patterns"""
        query = session.query(
            AgentPerformanceMetric.agent_type,
            func.sum(AgentPerformanceMetric.total_tokens_used).label('total_tokens'),
            func.sum(AgentPerformanceMetric.requests_total).label('total_requests'),
            func.avg(AgentPerformanceMetric.avg_tokens_used).label('avg_per_request')
        ).group_by(AgentPerformanceMetric.agent_type)
        
        if agent_type:
            query = query.filter(AgentPerformanceMetric.agent_type == agent_type)
        if start_date:
            query = query.filter(AgentPerformanceMetric.period_start >= start_date)
        if end_date:
            query = query.filter(AgentPerformanceMetric.period_end <= end_date)
        
        by_agent = [
            {
                'agent_type': row.agent_type,
                'total_tokens': int(row.total_tokens or 0),
                'total_requests': int(row.total_requests or 0),
                'avg_tokens_per_request': int(row.total_tokens or 0) / int(row.total_requests) 
                    if row.total_requests else 0
            }
            for row in query.all()
        ]
        
        total_tokens = sum(a['total_tokens'] for a in by_agent)
        
        return {
            'total_tokens': total_tokens,
            'by_agent': by_agent,
            'token_distribution': {
                a['agent_type']: a['total_tokens'] / total_tokens if total_tokens > 0 else 0
                for a in by_agent
            }
        }
    
    def get_performance_report(self, session: Session, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive agent performance report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'agent_comparison': self.get_all_agents_comparison(session, start_date, end_date),
            'error_analysis': self.get_error_breakdown(session, start_date=start_date, end_date=end_date),
            'token_usage': self.get_token_usage_analysis(session, start_date=start_date, end_date=end_date),
            'trends': {
                'requests': self.get_performance_trend(session, metric='requests', 
                                                       start_date=start_date, end_date=end_date),
                'success_rate': self.get_performance_trend(session, metric='success_rate',
                                                          start_date=start_date, end_date=end_date),
                'response_time': self.get_performance_trend(session, metric='response_time',
                                                           start_date=start_date, end_date=end_date)
            }
        }
