"""
Response Time Analytics
Detailed tracking and analysis of response times

Features:
- Endpoint-level tracking
- Percentile analysis
- Latency breakdown
- SLA monitoring
- Anomaly detection
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from .models import ResponseTimeMetric
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class ResponseTimeAnalytics:
    """
    Comprehensive response time tracking and analysis
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.collector = MetricsCollector()
        
        # SLA thresholds in milliseconds
        self._sla_thresholds = {
            'excellent': 100,
            'good': 500,
            'acceptable': 1000,
            'poor': 3000
        }
    
    def set_sla_threshold(self, level: str, threshold_ms: int):
        """Set SLA threshold"""
        self._sla_thresholds[level] = threshold_ms
    
    # ==================== Recording ====================
    
    def record(self, endpoint: str, total_time_ms: int,
              method: str = None, operation_type: str = None,
              request_id: str = None, rfp_id: str = None,
              queue_time_ms: int = None, processing_time_ms: int = None,
              db_time_ms: int = None, external_api_time_ms: int = None,
              request_size_bytes: int = None, response_size_bytes: int = None,
              status_code: int = None, is_success: bool = True,
              error_type: str = None, user_id: str = None) -> ResponseTimeMetric:
        """Record a response time metric"""
        
        metric_data = {
            'endpoint': endpoint,
            'method': method,
            'operation_type': operation_type,
            'request_id': request_id,
            'rfp_id': rfp_id,
            'total_time_ms': total_time_ms,
            'queue_time_ms': queue_time_ms,
            'processing_time_ms': processing_time_ms,
            'db_time_ms': db_time_ms,
            'external_api_time_ms': external_api_time_ms,
            'request_size_bytes': request_size_bytes,
            'response_size_bytes': response_size_bytes,
            'status_code': status_code,
            'is_success': is_success,
            'error_type': error_type,
            'user_id': user_id,
            'recorded_at': datetime.utcnow()
        }
        
        # Record to collector
        self.collector.timing(f'response.{endpoint}', total_time_ms)
        if is_success:
            self.collector.increment(f'response.{endpoint}.success')
        else:
            self.collector.increment(f'response.{endpoint}.failed')
        
        if self.session_factory:
            return self._save_metric(metric_data)
        
        return metric_data
    
    def _save_metric(self, metric_data: Dict[str, Any]) -> ResponseTimeMetric:
        """Save metric to database"""
        session = self.session_factory()
        try:
            metric = ResponseTimeMetric(**metric_data)
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()
    
    def _get_in_memory_stats(self, endpoint: str = None) -> Dict[str, Any]:
        """Get statistics from in-memory collector (for testing without database)"""
        metric_key = f'response.{endpoint}.timing' if endpoint else 'response.timing'
        
        # Get histogram stats from collector (timing uses histogram internally)
        timing_stats = self.collector.get_histogram_stats(metric_key)
        success_key = f'response.{endpoint}.success' if endpoint else 'response.success'
        failed_key = f'response.{endpoint}.failed' if endpoint else 'response.failed'
        
        return {
            'endpoint': endpoint,
            'timing': timing_stats,
            'success_count': self.collector.get_counter(success_key),
            'failed_count': self.collector.get_counter(failed_key)
        }
    
    # ==================== Analysis ====================
    
    def get_endpoint_stats(self, session: Session,
                          endpoint: str = None,
                          start_date: datetime = None,
                          end_date: datetime = None) -> Dict[str, Any]:
        """Get statistics for an endpoint or all endpoints"""
        query = session.query(
            ResponseTimeMetric.endpoint,
            func.count(ResponseTimeMetric.id).label('request_count'),
            func.avg(ResponseTimeMetric.total_time_ms).label('avg_time'),
            func.min(ResponseTimeMetric.total_time_ms).label('min_time'),
            func.max(ResponseTimeMetric.total_time_ms).label('max_time'),
            func.percentile_cont(0.5).within_group(
                ResponseTimeMetric.total_time_ms
            ).label('p50'),
            func.percentile_cont(0.95).within_group(
                ResponseTimeMetric.total_time_ms
            ).label('p95'),
            func.percentile_cont(0.99).within_group(
                ResponseTimeMetric.total_time_ms
            ).label('p99'),
            func.sum(case((ResponseTimeMetric.is_success == True, 1), else_=0)).label('success_count')
        ).group_by(ResponseTimeMetric.endpoint)
        
        if endpoint:
            query = query.filter(ResponseTimeMetric.endpoint == endpoint)
        if start_date:
            query = query.filter(ResponseTimeMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(ResponseTimeMetric.recorded_at <= end_date)
        
        results = []
        for row in query.all():
            results.append({
                'endpoint': row.endpoint,
                'request_count': row.request_count,
                'avg_time_ms': float(row.avg_time or 0),
                'min_time_ms': float(row.min_time or 0),
                'max_time_ms': float(row.max_time or 0),
                'p50_ms': float(row.p50 or 0) if hasattr(row, 'p50') else 0,
                'p95_ms': float(row.p95 or 0) if hasattr(row, 'p95') else 0,
                'p99_ms': float(row.p99 or 0) if hasattr(row, 'p99') else 0,
                'success_rate': row.success_count / row.request_count if row.request_count > 0 else 0
            })
        
        return results[0] if endpoint and results else {'endpoints': results}
    
    def get_latency_breakdown(self, session: Session,
                             endpoint: str = None,
                             start_date: datetime = None,
                             end_date: datetime = None) -> Dict[str, Any]:
        """Get breakdown of latency components"""
        query = session.query(
            func.avg(ResponseTimeMetric.queue_time_ms).label('avg_queue'),
            func.avg(ResponseTimeMetric.processing_time_ms).label('avg_processing'),
            func.avg(ResponseTimeMetric.db_time_ms).label('avg_db'),
            func.avg(ResponseTimeMetric.external_api_time_ms).label('avg_external'),
            func.avg(ResponseTimeMetric.serialization_time_ms).label('avg_serialization'),
            func.avg(ResponseTimeMetric.total_time_ms).label('avg_total')
        )
        
        if endpoint:
            query = query.filter(ResponseTimeMetric.endpoint == endpoint)
        if start_date:
            query = query.filter(ResponseTimeMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(ResponseTimeMetric.recorded_at <= end_date)
        
        row = query.first()
        
        total = float(row.avg_total or 1)
        
        return {
            'queue_time_ms': float(row.avg_queue or 0),
            'queue_percent': (float(row.avg_queue or 0) / total) * 100,
            'processing_time_ms': float(row.avg_processing or 0),
            'processing_percent': (float(row.avg_processing or 0) / total) * 100,
            'db_time_ms': float(row.avg_db or 0),
            'db_percent': (float(row.avg_db or 0) / total) * 100,
            'external_api_time_ms': float(row.avg_external or 0),
            'external_percent': (float(row.avg_external or 0) / total) * 100,
            'serialization_time_ms': float(row.avg_serialization or 0),
            'serialization_percent': (float(row.avg_serialization or 0) / total) * 100,
            'total_time_ms': total
        }
    
    def get_response_time_trend(self, session: Session,
                               endpoint: str = None,
                               granularity: str = 'hour',
                               start_date: datetime = None,
                               end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get response time trend over time"""
        date_trunc = func.date_trunc(granularity, ResponseTimeMetric.recorded_at)
        
        query = session.query(
            date_trunc.label('period'),
            func.avg(ResponseTimeMetric.total_time_ms).label('avg_time'),
            func.percentile_cont(0.95).within_group(
                ResponseTimeMetric.total_time_ms
            ).label('p95'),
            func.count(ResponseTimeMetric.id).label('count')
        ).group_by(date_trunc).order_by(date_trunc)
        
        if endpoint:
            query = query.filter(ResponseTimeMetric.endpoint == endpoint)
        if start_date:
            query = query.filter(ResponseTimeMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(ResponseTimeMetric.recorded_at <= end_date)
        
        return [
            {
                'period': row.period.isoformat() if row.period else None,
                'avg_time_ms': float(row.avg_time or 0),
                'p95_ms': float(row.p95 or 0) if hasattr(row, 'p95') else 0,
                'request_count': row.count
            }
            for row in query.all()
        ]
    
    def get_sla_compliance(self, session: Session,
                          start_date: datetime = None,
                          end_date: datetime = None) -> Dict[str, Any]:
        """Calculate SLA compliance"""
        query = session.query(ResponseTimeMetric)
        
        if start_date:
            query = query.filter(ResponseTimeMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(ResponseTimeMetric.recorded_at <= end_date)
        
        total = query.count()
        
        if total == 0:
            return {
                'total_requests': 0,
                'compliance': {},
                'sla_met': True
            }
        
        compliance = {}
        for level, threshold in sorted(self._sla_thresholds.items(), 
                                       key=lambda x: x[1]):
            count = session.query(func.count(ResponseTimeMetric.id)).filter(
                ResponseTimeMetric.total_time_ms <= threshold,
                ResponseTimeMetric.recorded_at >= start_date if start_date else True,
                ResponseTimeMetric.recorded_at <= end_date if end_date else True
            ).scalar() or 0
            
            compliance[level] = {
                'threshold_ms': threshold,
                'count': count,
                'percentage': (count / total) * 100
            }
        
        return {
            'total_requests': total,
            'compliance': compliance,
            'sla_thresholds': self._sla_thresholds
        }
    
    def get_slow_requests(self, session: Session,
                         threshold_ms: int = 1000,
                         limit: int = 50,
                         start_date: datetime = None,
                         end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get slowest requests"""
        query = session.query(ResponseTimeMetric).filter(
            ResponseTimeMetric.total_time_ms >= threshold_ms
        ).order_by(ResponseTimeMetric.total_time_ms.desc()).limit(limit)
        
        if start_date:
            query = query.filter(ResponseTimeMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(ResponseTimeMetric.recorded_at <= end_date)
        
        return [
            {
                'endpoint': r.endpoint,
                'method': r.method,
                'total_time_ms': r.total_time_ms,
                'request_id': r.request_id,
                'rfp_id': r.rfp_id,
                'recorded_at': r.recorded_at.isoformat() if r.recorded_at else None
            }
            for r in query.all()
        ]
    
    def get_error_analysis(self, session: Session,
                          start_date: datetime = None,
                          end_date: datetime = None) -> Dict[str, Any]:
        """Analyze errors and their response times"""
        # Error rate by endpoint
        error_by_endpoint = session.query(
            ResponseTimeMetric.endpoint,
            func.count(ResponseTimeMetric.id).label('total'),
            func.sum(case((ResponseTimeMetric.is_success == False, 1), else_=0)).label('errors'),
            func.avg(case(
                (ResponseTimeMetric.is_success == False, ResponseTimeMetric.total_time_ms),
                else_=None
            )).label('avg_error_time')
        ).group_by(ResponseTimeMetric.endpoint)
        
        if start_date:
            error_by_endpoint = error_by_endpoint.filter(ResponseTimeMetric.recorded_at >= start_date)
        if end_date:
            error_by_endpoint = error_by_endpoint.filter(ResponseTimeMetric.recorded_at <= end_date)
        
        endpoint_errors = [
            {
                'endpoint': row.endpoint,
                'total_requests': row.total,
                'error_count': row.errors,
                'error_rate': row.errors / row.total if row.total > 0 else 0,
                'avg_error_time_ms': float(row.avg_error_time or 0)
            }
            for row in error_by_endpoint.all()
        ]
        
        # Error types breakdown
        error_types = session.query(
            ResponseTimeMetric.error_type,
            func.count(ResponseTimeMetric.id).label('count')
        ).filter(
            ResponseTimeMetric.is_success == False,
            ResponseTimeMetric.error_type.isnot(None),
            ResponseTimeMetric.recorded_at >= start_date if start_date else True,
            ResponseTimeMetric.recorded_at <= end_date if end_date else True
        ).group_by(ResponseTimeMetric.error_type).all()
        
        return {
            'by_endpoint': endpoint_errors,
            'by_error_type': {row.error_type: row.count for row in error_types}
        }
    
    def detect_anomalies(self, session: Session,
                        endpoint: str = None,
                        window_hours: int = 24,
                        threshold_stddev: float = 2.0) -> List[Dict[str, Any]]:
        """Detect response time anomalies"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=window_hours)
        
        # Get baseline stats
        baseline = session.query(
            func.avg(ResponseTimeMetric.total_time_ms).label('mean'),
            func.stddev(ResponseTimeMetric.total_time_ms).label('stddev')
        ).filter(
            ResponseTimeMetric.recorded_at >= start_date,
            ResponseTimeMetric.recorded_at <= end_date
        )
        
        if endpoint:
            baseline = baseline.filter(ResponseTimeMetric.endpoint == endpoint)
        
        baseline = baseline.first()
        mean = float(baseline.mean or 0)
        stddev = float(baseline.stddev or 0)
        
        if stddev == 0:
            return []
        
        # Find anomalies
        threshold = mean + (threshold_stddev * stddev)
        
        anomalies = session.query(ResponseTimeMetric).filter(
            ResponseTimeMetric.total_time_ms > threshold,
            ResponseTimeMetric.recorded_at >= start_date,
            ResponseTimeMetric.recorded_at <= end_date
        )
        
        if endpoint:
            anomalies = anomalies.filter(ResponseTimeMetric.endpoint == endpoint)
        
        return [
            {
                'endpoint': a.endpoint,
                'total_time_ms': a.total_time_ms,
                'deviation': (a.total_time_ms - mean) / stddev,
                'request_id': a.request_id,
                'recorded_at': a.recorded_at.isoformat() if a.recorded_at else None
            }
            for a in anomalies.limit(100).all()
        ]
    
    def get_performance_report(self, session: Session, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive response time report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours)
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'hours': hours
            },
            'endpoints': self.get_endpoint_stats(session, start_date=start_date, end_date=end_date),
            'latency_breakdown': self.get_latency_breakdown(session, start_date=start_date, end_date=end_date),
            'sla_compliance': self.get_sla_compliance(session, start_date, end_date),
            'trend': self.get_response_time_trend(session, granularity='hour', 
                                                  start_date=start_date, end_date=end_date),
            'slow_requests': self.get_slow_requests(session, limit=10, 
                                                    start_date=start_date, end_date=end_date),
            'errors': self.get_error_analysis(session, start_date, end_date),
            'anomalies': self.detect_anomalies(session, window_hours=hours)
        }
