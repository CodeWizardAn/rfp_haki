"""
RFP Processing Metrics Tracker
Tracks and analyzes RFP processing performance

Features:
- Processing time tracking by stage
- Volume metrics
- Status transition tracking
- Error rate monitoring
- Trend analysis
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from .models import RFPMetric, TimeGranularity
from .metrics_collector import MetricsCollector, track_timing, track_success_failure

logger = logging.getLogger(__name__)


class RFPMetricsTracker:
    """
    Comprehensive RFP processing metrics tracking
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.collector = MetricsCollector()
        
        # In-memory tracking for current session
        self._active_rfps: Dict[str, Dict[str, Any]] = {}
    
    # ==================== Event Tracking ====================
    
    def start_processing(self, rfp_id: str, rfp_data: Dict[str, Any] = None):
        """Mark start of RFP processing"""
        self._active_rfps[rfp_id] = {
            'start_time': datetime.utcnow(),
            'stages': {},
            'status_history': [{'status': 'processing_started', 'timestamp': datetime.utcnow()}],
            'errors': [],
            'rfp_data': rfp_data or {}
        }
        
        self.collector.increment('rfp.processing.started')
        self.collector.gauge('rfp.processing.active', len(self._active_rfps))
    
    def start_stage(self, rfp_id: str, stage: str):
        """Mark start of a processing stage"""
        if rfp_id not in self._active_rfps:
            return
            
        self._active_rfps[rfp_id]['stages'][stage] = {
            'start_time': datetime.utcnow(),
            'end_time': None,
            'duration_ms': None
        }
        
        self.collector.increment(f'rfp.stage.{stage}.started')
    
    def end_stage(self, rfp_id: str, stage: str, success: bool = True, 
                  metadata: Dict[str, Any] = None):
        """Mark end of a processing stage"""
        if rfp_id not in self._active_rfps:
            return
            
        if stage not in self._active_rfps[rfp_id]['stages']:
            return
        
        stage_data = self._active_rfps[rfp_id]['stages'][stage]
        stage_data['end_time'] = datetime.utcnow()
        stage_data['duration_ms'] = (
            stage_data['end_time'] - stage_data['start_time']
        ).total_seconds() * 1000
        stage_data['success'] = success
        stage_data['metadata'] = metadata or {}
        
        # Record timing
        self.collector.timing(f'rfp.stage.{stage}', stage_data['duration_ms'])
        
        if success:
            self.collector.increment(f'rfp.stage.{stage}.success')
        else:
            self.collector.increment(f'rfp.stage.{stage}.failed')
    
    def record_status_change(self, rfp_id: str, old_status: str, new_status: str):
        """Record a status transition"""
        if rfp_id in self._active_rfps:
            self._active_rfps[rfp_id]['status_history'].append({
                'from': old_status,
                'to': new_status,
                'timestamp': datetime.utcnow()
            })
        
        self.collector.increment('rfp.status_change', tags={
            'from': old_status,
            'to': new_status
        })
    
    def record_error(self, rfp_id: str, error_type: str, error_message: str):
        """Record an error during processing"""
        if rfp_id in self._active_rfps:
            self._active_rfps[rfp_id]['errors'].append({
                'type': error_type,
                'message': error_message,
                'timestamp': datetime.utcnow()
            })
        
        self.collector.increment('rfp.errors', tags={'error_type': error_type})
    
    def complete_processing(self, rfp_id: str, outcome: str = 'completed',
                           requirements_count: int = 0, products_matched: int = 0,
                           matches_generated: int = 0, avg_match_confidence: float = 0.0,
                           bid_value: float = None, estimated_value: float = None):
        """Mark completion of RFP processing and save metrics"""
        if rfp_id not in self._active_rfps:
            logger.warning(f"No active tracking for RFP {rfp_id}")
            return None
        
        rfp_data = self._active_rfps.pop(rfp_id)
        end_time = datetime.utcnow()
        
        # Calculate total time
        total_time_ms = (end_time - rfp_data['start_time']).total_seconds() * 1000
        
        # Extract stage timings
        stages = rfp_data['stages']
        extraction_time = stages.get('extraction', {}).get('duration_ms')
        parsing_time = stages.get('parsing', {}).get('duration_ms')
        matching_time = stages.get('matching', {}).get('duration_ms')
        bid_generation_time = stages.get('bid_generation', {}).get('duration_ms')
        
        # Build metric record
        metric_data = {
            'rfp_id': rfp_id,
            'extraction_time_ms': int(extraction_time) if extraction_time else None,
            'parsing_time_ms': int(parsing_time) if parsing_time else None,
            'matching_time_ms': int(matching_time) if matching_time else None,
            'bid_generation_time_ms': int(bid_generation_time) if bid_generation_time else None,
            'total_processing_time_ms': int(total_time_ms),
            'requirements_count': requirements_count,
            'products_matched': products_matched,
            'matches_generated': matches_generated,
            'avg_match_confidence': avg_match_confidence,
            'manual_overrides_count': 0,
            'errors_count': len(rfp_data['errors']),
            'initial_status': rfp_data['status_history'][0]['status'] if rfp_data['status_history'] else None,
            'final_status': outcome,
            'status_changes': rfp_data['status_history'],
            'outcome': outcome,
            'estimated_value': estimated_value,
            'bid_value': bid_value,
            'processing_started_at': rfp_data['start_time'],
            'processing_completed_at': end_time
        }
        
        # Record metrics
        self.collector.timing('rfp.processing.total', total_time_ms)
        self.collector.increment('rfp.processing.completed', tags={'outcome': outcome})
        self.collector.gauge('rfp.processing.active', len(self._active_rfps))
        
        # Save to database if session available
        if self.session_factory:
            return self._save_metric(metric_data)
        
        return metric_data
    
    def _save_metric(self, metric_data: Dict[str, Any]) -> RFPMetric:
        """Save metric to database"""
        session = self.session_factory()
        try:
            metric = RFPMetric(**metric_data)
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()
    
    # ==================== Analytics Queries ====================
    
    def get_processing_stats(self, session: Session, 
                            start_date: datetime = None,
                            end_date: datetime = None) -> Dict[str, Any]:
        """Get aggregate processing statistics"""
        query = session.query(RFPMetric)
        
        if start_date:
            query = query.filter(RFPMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(RFPMetric.recorded_at <= end_date)
        
        # Aggregate stats
        stats = session.query(
            func.count(RFPMetric.id).label('total_rfps'),
            func.avg(RFPMetric.total_processing_time_ms).label('avg_processing_time'),
            func.min(RFPMetric.total_processing_time_ms).label('min_processing_time'),
            func.max(RFPMetric.total_processing_time_ms).label('max_processing_time'),
            func.avg(RFPMetric.requirements_count).label('avg_requirements'),
            func.avg(RFPMetric.avg_match_confidence).label('avg_confidence'),
            func.sum(RFPMetric.errors_count).label('total_errors')
        ).filter(
            RFPMetric.recorded_at >= start_date if start_date else True,
            RFPMetric.recorded_at <= end_date if end_date else True
        ).first()
        
        # Outcome breakdown
        outcomes = session.query(
            RFPMetric.outcome,
            func.count(RFPMetric.id).label('count')
        ).group_by(RFPMetric.outcome).all()
        
        return {
            'total_rfps': stats.total_rfps or 0,
            'avg_processing_time_ms': float(stats.avg_processing_time or 0),
            'min_processing_time_ms': float(stats.min_processing_time or 0),
            'max_processing_time_ms': float(stats.max_processing_time or 0),
            'avg_requirements_per_rfp': float(stats.avg_requirements or 0),
            'avg_match_confidence': float(stats.avg_confidence or 0),
            'total_errors': int(stats.total_errors or 0),
            'outcomes': {o.outcome: o.count for o in outcomes if o.outcome}
        }
    
    def get_stage_timing_breakdown(self, session: Session,
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Dict[str, float]]:
        """Get timing breakdown by processing stage"""
        query = session.query(RFPMetric)
        
        if start_date:
            query = query.filter(RFPMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(RFPMetric.recorded_at <= end_date)
        
        stats = session.query(
            func.avg(RFPMetric.extraction_time_ms).label('avg_extraction'),
            func.avg(RFPMetric.parsing_time_ms).label('avg_parsing'),
            func.avg(RFPMetric.matching_time_ms).label('avg_matching'),
            func.avg(RFPMetric.bid_generation_time_ms).label('avg_bid_gen'),
            func.percentile_cont(0.95).within_group(
                RFPMetric.extraction_time_ms
            ).label('p95_extraction'),
            func.percentile_cont(0.95).within_group(
                RFPMetric.parsing_time_ms
            ).label('p95_parsing'),
            func.percentile_cont(0.95).within_group(
                RFPMetric.matching_time_ms
            ).label('p95_matching'),
            func.percentile_cont(0.95).within_group(
                RFPMetric.bid_generation_time_ms
            ).label('p95_bid_gen')
        ).filter(
            RFPMetric.recorded_at >= start_date if start_date else True,
            RFPMetric.recorded_at <= end_date if end_date else True
        ).first()
        
        return {
            'extraction': {
                'avg_ms': float(stats.avg_extraction or 0),
                'p95_ms': float(stats.p95_extraction or 0) if hasattr(stats, 'p95_extraction') else 0
            },
            'parsing': {
                'avg_ms': float(stats.avg_parsing or 0),
                'p95_ms': float(stats.p95_parsing or 0) if hasattr(stats, 'p95_parsing') else 0
            },
            'matching': {
                'avg_ms': float(stats.avg_matching or 0),
                'p95_ms': float(stats.p95_matching or 0) if hasattr(stats, 'p95_matching') else 0
            },
            'bid_generation': {
                'avg_ms': float(stats.avg_bid_gen or 0),
                'p95_ms': float(stats.p95_bid_gen or 0) if hasattr(stats, 'p95_bid_gen') else 0
            }
        }
    
    def get_time_series(self, session: Session,
                       metric: str = 'count',
                       granularity: TimeGranularity = TimeGranularity.DAY,
                       start_date: datetime = None,
                       end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get time series data for RFP metrics"""
        # Build date truncation based on granularity
        if granularity == TimeGranularity.HOUR:
            date_trunc = func.date_trunc('hour', RFPMetric.recorded_at)
        elif granularity == TimeGranularity.DAY:
            date_trunc = func.date_trunc('day', RFPMetric.recorded_at)
        elif granularity == TimeGranularity.WEEK:
            date_trunc = func.date_trunc('week', RFPMetric.recorded_at)
        elif granularity == TimeGranularity.MONTH:
            date_trunc = func.date_trunc('month', RFPMetric.recorded_at)
        else:
            date_trunc = func.date_trunc('day', RFPMetric.recorded_at)
        
        # Select appropriate metric
        if metric == 'count':
            metric_col = func.count(RFPMetric.id)
        elif metric == 'avg_processing_time':
            metric_col = func.avg(RFPMetric.total_processing_time_ms)
        elif metric == 'avg_confidence':
            metric_col = func.avg(RFPMetric.avg_match_confidence)
        elif metric == 'total_value':
            metric_col = func.sum(RFPMetric.bid_value)
        else:
            metric_col = func.count(RFPMetric.id)
        
        query = session.query(
            date_trunc.label('period'),
            metric_col.label('value')
        ).group_by(date_trunc).order_by(date_trunc)
        
        if start_date:
            query = query.filter(RFPMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(RFPMetric.recorded_at <= end_date)
        
        return [
            {'period': row.period.isoformat() if row.period else None, 'value': float(row.value or 0)}
            for row in query.all()
        ]
    
    def get_error_analysis(self, session: Session,
                          start_date: datetime = None,
                          end_date: datetime = None) -> Dict[str, Any]:
        """Analyze errors in RFP processing"""
        query = session.query(RFPMetric).filter(RFPMetric.errors_count > 0)
        
        if start_date:
            query = query.filter(RFPMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(RFPMetric.recorded_at <= end_date)
        
        error_rfps = query.all()
        
        # Aggregate error types from status_changes JSON
        error_types = defaultdict(int)
        for rfp in error_rfps:
            if rfp.status_changes:
                for change in rfp.status_changes:
                    if 'error' in str(change.get('to', '')).lower():
                        error_types['status_error'] += 1
        
        total_count = session.query(func.count(RFPMetric.id)).filter(
            RFPMetric.recorded_at >= start_date if start_date else True,
            RFPMetric.recorded_at <= end_date if end_date else True
        ).scalar() or 0
        
        error_count = len(error_rfps)
        
        return {
            'total_rfps': total_count,
            'rfps_with_errors': error_count,
            'error_rate': error_count / total_count if total_count > 0 else 0,
            'error_types': dict(error_types),
            'avg_errors_per_failed_rfp': (
                sum(r.errors_count for r in error_rfps) / error_count
                if error_count > 0 else 0
            )
        }
    
    def get_performance_summary(self, session: Session, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive performance summary for last N days"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = self.get_processing_stats(session, start_date, end_date)
        stage_timing = self.get_stage_timing_breakdown(session, start_date, end_date)
        errors = self.get_error_analysis(session, start_date, end_date)
        
        # Calculate additional metrics
        success_rate = 0
        if 'outcomes' in stats and stats['total_rfps'] > 0:
            successful = stats['outcomes'].get('completed', 0) + stats['outcomes'].get('bid_generated', 0)
            success_rate = successful / stats['total_rfps']
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'volume': {
                'total_rfps': stats['total_rfps'],
                'daily_average': stats['total_rfps'] / days if days > 0 else 0
            },
            'performance': {
                'avg_processing_time_ms': stats['avg_processing_time_ms'],
                'avg_processing_time_seconds': stats['avg_processing_time_ms'] / 1000,
                'stage_breakdown': stage_timing
            },
            'quality': {
                'avg_match_confidence': stats['avg_match_confidence'],
                'success_rate': success_rate,
                'error_rate': errors['error_rate']
            },
            'outcomes': stats.get('outcomes', {})
        }
