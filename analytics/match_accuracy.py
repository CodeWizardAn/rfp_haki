"""
Match Accuracy Tracker
Tracks and analyzes product matching algorithm accuracy

Features:
- Track predicted vs actual matches
- Calculate accuracy metrics (precision, recall, F1)
- Top-K accuracy tracking
- Algorithm version comparison
- Feedback integration
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case

from .models import MatchAccuracyMetric
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class MatchAccuracyTracker:
    """
    Comprehensive match accuracy tracking and analysis
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.collector = MetricsCollector()
        
        # Cache for algorithm versions
        self._current_algorithm_version = "1.0.0"
    
    def set_algorithm_version(self, version: str):
        """Set current algorithm version for tracking"""
        self._current_algorithm_version = version
    
    # ==================== Recording ====================
    
    def record_prediction(self, rfp_id: str, requirement_id: int,
                         predicted_product_id: int, confidence: float,
                         ranking: List[int] = None,
                         algorithm_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Record a prediction for later validation
        
        Args:
            rfp_id: RFP identifier
            requirement_id: Requirement ID within the RFP
            predicted_product_id: Top predicted product
            confidence: Confidence score (0-1)
            ranking: Full ranking of product IDs
            algorithm_config: Algorithm configuration used
        """
        record = {
            'rfp_id': rfp_id,
            'requirement_id': requirement_id,
            'predicted_product_id': predicted_product_id,
            'predicted_confidence': confidence,
            'algorithm_version': self._current_algorithm_version,
            'algorithm_config': algorithm_config or {},
            'ranking': ranking or [predicted_product_id],
            'recorded_at': datetime.utcnow()
        }
        
        self.collector.increment('match.predictions.total')
        self.collector.histogram('match.confidence', confidence)
        
        return record
    
    def record_validation(self, rfp_id: str, requirement_id: int,
                         predicted_product_id: int, actual_product_id: int,
                         predicted_confidence: float,
                         ranking: List[int] = None,
                         feedback_source: str = 'human',
                         feedback_notes: str = None,
                         algorithm_version: str = None,
                         algorithm_config: Dict[str, Any] = None) -> MatchAccuracyMetric:
        """
        Record a validated match result
        
        Args:
            rfp_id: RFP identifier
            requirement_id: Requirement ID
            predicted_product_id: What the algorithm predicted
            actual_product_id: What was actually selected/correct
            predicted_confidence: Confidence of prediction
            ranking: Full ranking of products
            feedback_source: Source of validation (human, system, auto)
            feedback_notes: Additional notes
        """
        ranking = ranking or [predicted_product_id]
        is_correct = predicted_product_id == actual_product_id
        
        # Calculate ranking metrics
        was_in_top_3 = actual_product_id in ranking[:3]
        was_in_top_5 = actual_product_id in ranking[:5]
        actual_rank = ranking.index(actual_product_id) + 1 if actual_product_id in ranking else None
        
        metric_data = {
            'rfp_id': rfp_id,
            'requirement_id': requirement_id,
            'algorithm_version': algorithm_version or self._current_algorithm_version,
            'algorithm_config': algorithm_config or {},
            'predicted_product_id': predicted_product_id,
            'predicted_confidence': predicted_confidence,
            'actual_product_id': actual_product_id,
            'is_correct': is_correct,
            'was_in_top_3': was_in_top_3,
            'was_in_top_5': was_in_top_5,
            'actual_rank': actual_rank,
            'feedback_source': feedback_source,
            'feedback_notes': feedback_notes,
            'recorded_at': datetime.utcnow()
        }
        
        # Update metrics
        self.collector.increment('match.validations.total')
        if is_correct:
            self.collector.increment('match.validations.correct')
        else:
            self.collector.increment('match.validations.incorrect')
        
        if was_in_top_3:
            self.collector.increment('match.top3.hits')
        if was_in_top_5:
            self.collector.increment('match.top5.hits')
        
        if actual_rank:
            self.collector.histogram('match.actual_rank', actual_rank)
        
        # Save to database
        if self.session_factory:
            return self._save_validation(metric_data)
        
        return metric_data
    
    def _save_validation(self, metric_data: Dict[str, Any]) -> MatchAccuracyMetric:
        """Save validation to database"""
        session = self.session_factory()
        try:
            metric = MatchAccuracyMetric(**metric_data)
            session.add(metric)
            session.commit()
            session.refresh(metric)
            return metric
        finally:
            session.close()
    
    # ==================== Analysis ====================
    
    def get_accuracy_metrics(self, session: Session,
                            start_date: datetime = None,
                            end_date: datetime = None,
                            algorithm_version: str = None) -> Dict[str, Any]:
        """
        Get comprehensive accuracy metrics
        
        Returns:
            Dict containing accuracy, precision, recall, F1, top-K accuracy
        """
        query = session.query(MatchAccuracyMetric)
        
        if start_date:
            query = query.filter(MatchAccuracyMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(MatchAccuracyMetric.recorded_at <= end_date)
        if algorithm_version:
            query = query.filter(MatchAccuracyMetric.algorithm_version == algorithm_version)
        
        # Basic counts
        total = query.count()
        if total == 0:
            return self._empty_metrics()
        
        correct = query.filter(MatchAccuracyMetric.is_correct == True).count()
        top_3 = query.filter(MatchAccuracyMetric.was_in_top_3 == True).count()
        top_5 = query.filter(MatchAccuracyMetric.was_in_top_5 == True).count()
        
        # Average confidence
        avg_confidence = session.query(
            func.avg(MatchAccuracyMetric.predicted_confidence)
        ).filter(
            MatchAccuracyMetric.recorded_at >= start_date if start_date else True,
            MatchAccuracyMetric.recorded_at <= end_date if end_date else True
        ).scalar() or 0
        
        # Mean Reciprocal Rank (MRR)
        ranks = session.query(MatchAccuracyMetric.actual_rank).filter(
            MatchAccuracyMetric.actual_rank.isnot(None),
            MatchAccuracyMetric.recorded_at >= start_date if start_date else True,
            MatchAccuracyMetric.recorded_at <= end_date if end_date else True
        ).all()
        
        mrr = sum(1.0 / r[0] for r in ranks) / len(ranks) if ranks else 0
        
        return {
            'total_validations': total,
            'accuracy': correct / total,
            'top_1_accuracy': correct / total,
            'top_3_accuracy': top_3 / total,
            'top_5_accuracy': top_5 / total,
            'mean_reciprocal_rank': mrr,
            'avg_confidence': float(avg_confidence),
            'correct_count': correct,
            'incorrect_count': total - correct
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'total_validations': 0,
            'accuracy': 0.0,
            'top_1_accuracy': 0.0,
            'top_3_accuracy': 0.0,
            'top_5_accuracy': 0.0,
            'mean_reciprocal_rank': 0.0,
            'avg_confidence': 0.0,
            'correct_count': 0,
            'incorrect_count': 0
        }
    
    def get_accuracy_by_confidence(self, session: Session,
                                   buckets: int = 10,
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get accuracy broken down by confidence buckets
        Helps identify if confidence scores are well-calibrated
        """
        bucket_size = 1.0 / buckets
        results = []
        
        for i in range(buckets):
            lower = i * bucket_size
            upper = (i + 1) * bucket_size
            
            query = session.query(MatchAccuracyMetric).filter(
                MatchAccuracyMetric.predicted_confidence >= lower,
                MatchAccuracyMetric.predicted_confidence < upper
            )
            
            if start_date:
                query = query.filter(MatchAccuracyMetric.recorded_at >= start_date)
            if end_date:
                query = query.filter(MatchAccuracyMetric.recorded_at <= end_date)
            
            total = query.count()
            correct = query.filter(MatchAccuracyMetric.is_correct == True).count()
            
            results.append({
                'confidence_range': f"{lower:.1f}-{upper:.1f}",
                'lower_bound': lower,
                'upper_bound': upper,
                'total': total,
                'correct': correct,
                'accuracy': correct / total if total > 0 else 0
            })
        
        return results
    
    def get_accuracy_trend(self, session: Session,
                          granularity: str = 'day',
                          start_date: datetime = None,
                          end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get accuracy trend over time"""
        if granularity == 'hour':
            date_trunc = func.date_trunc('hour', MatchAccuracyMetric.recorded_at)
        elif granularity == 'day':
            date_trunc = func.date_trunc('day', MatchAccuracyMetric.recorded_at)
        elif granularity == 'week':
            date_trunc = func.date_trunc('week', MatchAccuracyMetric.recorded_at)
        else:
            date_trunc = func.date_trunc('day', MatchAccuracyMetric.recorded_at)
        
        query = session.query(
            date_trunc.label('period'),
            func.count(MatchAccuracyMetric.id).label('total'),
            func.sum(case((MatchAccuracyMetric.is_correct == True, 1), else_=0)).label('correct'),
            func.sum(case((MatchAccuracyMetric.was_in_top_3 == True, 1), else_=0)).label('top_3'),
            func.avg(MatchAccuracyMetric.predicted_confidence).label('avg_confidence')
        ).group_by(date_trunc).order_by(date_trunc)
        
        if start_date:
            query = query.filter(MatchAccuracyMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(MatchAccuracyMetric.recorded_at <= end_date)
        
        return [
            {
                'period': row.period.isoformat() if row.period else None,
                'total': row.total,
                'correct': row.correct,
                'accuracy': row.correct / row.total if row.total > 0 else 0,
                'top_3_accuracy': row.top_3 / row.total if row.total > 0 else 0,
                'avg_confidence': float(row.avg_confidence or 0)
            }
            for row in query.all()
        ]
    
    def compare_algorithm_versions(self, session: Session,
                                   versions: List[str] = None,
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Dict[str, Any]]:
        """Compare accuracy across algorithm versions"""
        if versions is None:
            # Get all versions
            versions_query = session.query(
                MatchAccuracyMetric.algorithm_version
            ).distinct().all()
            versions = [v[0] for v in versions_query if v[0]]
        
        results = {}
        for version in versions:
            metrics = self.get_accuracy_metrics(
                session,
                start_date=start_date,
                end_date=end_date,
                algorithm_version=version
            )
            results[version] = metrics
        
        return results
    
    def get_confusion_analysis(self, session: Session,
                              start_date: datetime = None,
                              end_date: datetime = None,
                              limit: int = 20) -> Dict[str, Any]:
        """
        Analyze common confusion patterns
        Shows which products are commonly confused with each other
        """
        query = session.query(
            MatchAccuracyMetric.predicted_product_id,
            MatchAccuracyMetric.actual_product_id,
            func.count(MatchAccuracyMetric.id).label('count')
        ).filter(
            MatchAccuracyMetric.is_correct == False,
            MatchAccuracyMetric.actual_product_id.isnot(None)
        ).group_by(
            MatchAccuracyMetric.predicted_product_id,
            MatchAccuracyMetric.actual_product_id
        ).order_by(func.count(MatchAccuracyMetric.id).desc()).limit(limit)
        
        if start_date:
            query = query.filter(MatchAccuracyMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(MatchAccuracyMetric.recorded_at <= end_date)
        
        confusions = [
            {
                'predicted_product_id': row.predicted_product_id,
                'actual_product_id': row.actual_product_id,
                'count': row.count
            }
            for row in query.all()
        ]
        
        return {
            'total_confusions': sum(c['count'] for c in confusions),
            'top_confusions': confusions
        }
    
    def get_feedback_summary(self, session: Session,
                            start_date: datetime = None,
                            end_date: datetime = None) -> Dict[str, Any]:
        """Get summary of feedback sources"""
        query = session.query(
            MatchAccuracyMetric.feedback_source,
            func.count(MatchAccuracyMetric.id).label('count'),
            func.avg(case(
                (MatchAccuracyMetric.is_correct == True, 1.0),
                else_=0.0
            )).label('accuracy')
        ).group_by(MatchAccuracyMetric.feedback_source)
        
        if start_date:
            query = query.filter(MatchAccuracyMetric.recorded_at >= start_date)
        if end_date:
            query = query.filter(MatchAccuracyMetric.recorded_at <= end_date)
        
        return {
            row.feedback_source or 'unknown': {
                'count': row.count,
                'accuracy': float(row.accuracy or 0)
            }
            for row in query.all()
        }
    
    def get_performance_report(self, session: Session, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive accuracy performance report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        metrics = self.get_accuracy_metrics(session, start_date, end_date)
        calibration = self.get_accuracy_by_confidence(session, 5, start_date, end_date)
        trend = self.get_accuracy_trend(session, 'day', start_date, end_date)
        versions = self.compare_algorithm_versions(session, start_date=start_date, end_date=end_date)
        confusions = self.get_confusion_analysis(session, start_date, end_date, 10)
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'overall_metrics': metrics,
            'calibration': calibration,
            'trend': trend,
            'version_comparison': versions,
            'confusion_analysis': confusions
        }
