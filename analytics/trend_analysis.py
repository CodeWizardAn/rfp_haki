"""
Trend Analysis
Analyzes trends in metrics over time

Features:
- Moving averages
- Trend detection
- Seasonality analysis
- Growth rates
- Anomaly detection
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
import math
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import RFPMetric, MatchAccuracyMetric, WinLossRecord, CostRecord

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Comprehensive trend analysis for analytics metrics
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
    
    # ==================== Moving Averages ====================
    
    def calculate_moving_average(self, data: List[float], 
                                window: int = 7) -> List[float]:
        """Calculate simple moving average"""
        if len(data) < window:
            return data
        
        result = []
        window_data = deque(maxlen=window)
        
        for value in data:
            window_data.append(value)
            if len(window_data) == window:
                result.append(sum(window_data) / window)
            else:
                result.append(sum(window_data) / len(window_data))
        
        return result
    
    def calculate_exponential_moving_average(self, data: List[float],
                                            alpha: float = 0.3) -> List[float]:
        """Calculate exponential moving average"""
        if not data:
            return []
        
        result = [data[0]]
        for i in range(1, len(data)):
            ema = alpha * data[i] + (1 - alpha) * result[i-1]
            result.append(ema)
        
        return result
    
    def calculate_weighted_moving_average(self, data: List[float],
                                         window: int = 7) -> List[float]:
        """Calculate weighted moving average (recent values weighted more)"""
        if len(data) < window:
            return data
        
        weights = list(range(1, window + 1))
        weight_sum = sum(weights)
        
        result = []
        for i in range(len(data)):
            if i < window - 1:
                # Not enough data, use available
                current_weights = list(range(1, i + 2))
                wma = sum(data[j] * current_weights[j] for j in range(i + 1)) / sum(current_weights)
            else:
                window_data = data[i - window + 1:i + 1]
                wma = sum(window_data[j] * weights[j] for j in range(window)) / weight_sum
            result.append(wma)
        
        return result
    
    # ==================== Trend Detection ====================
    
    def detect_trend(self, data: List[float]) -> Dict[str, Any]:
        """
        Detect trend direction and strength using linear regression
        """
        if len(data) < 2:
            return {'direction': 'flat', 'strength': 0, 'slope': 0}
        
        n = len(data)
        x = list(range(n))
        
        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(data) / n
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Calculate R-squared (coefficient of determination)
        y_pred = [slope * x[i] + (y_mean - slope * x_mean) for i in range(n)]
        ss_res = sum((data[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((data[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine direction
        if slope > 0.01:
            direction = 'increasing'
        elif slope < -0.01:
            direction = 'decreasing'
        else:
            direction = 'flat'
        
        # Calculate percent change
        if data[0] != 0:
            percent_change = ((data[-1] - data[0]) / data[0]) * 100
        else:
            percent_change = 0
        
        return {
            'direction': direction,
            'slope': slope,
            'strength': abs(r_squared),
            'r_squared': r_squared,
            'percent_change': percent_change,
            'start_value': data[0],
            'end_value': data[-1]
        }
    
    def detect_trend_changes(self, data: List[float], 
                            window: int = 7,
                            threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Detect points where trend changes direction"""
        if len(data) < window * 2:
            return []
        
        changes = []
        prev_direction = None
        
        for i in range(window, len(data) - window + 1):
            # Trend before this point
            before = self.detect_trend(data[i-window:i])
            # Trend after this point
            after = self.detect_trend(data[i:i+window])
            
            # Check for direction change
            if (before['slope'] > threshold and after['slope'] < -threshold) or \
               (before['slope'] < -threshold and after['slope'] > threshold):
                changes.append({
                    'index': i,
                    'from_direction': before['direction'],
                    'to_direction': after['direction'],
                    'value': data[i],
                    'before_slope': before['slope'],
                    'after_slope': after['slope']
                })
        
        return changes
    
    # ==================== Growth Rates ====================
    
    def calculate_growth_rate(self, current: float, previous: float) -> float:
        """Calculate growth rate between two values"""
        if previous == 0:
            return 0 if current == 0 else 100
        return ((current - previous) / abs(previous)) * 100
    
    def calculate_cagr(self, start_value: float, end_value: float, 
                       periods: int) -> float:
        """Calculate Compound Annual Growth Rate"""
        if start_value <= 0 or end_value <= 0 or periods <= 0:
            return 0
        
        return (pow(end_value / start_value, 1 / periods) - 1) * 100
    
    def calculate_period_over_period_growth(self, data: List[Tuple[datetime, float]],
                                           period_type: str = 'month') -> List[Dict[str, Any]]:
        """Calculate period-over-period growth rates"""
        if len(data) < 2:
            return []
        
        results = []
        for i in range(1, len(data)):
            prev_date, prev_value = data[i-1]
            curr_date, curr_value = data[i]
            
            growth = self.calculate_growth_rate(curr_value, prev_value)
            
            results.append({
                'period': curr_date.isoformat() if isinstance(curr_date, datetime) else curr_date,
                'value': curr_value,
                'previous_value': prev_value,
                'growth_rate': growth,
                'absolute_change': curr_value - prev_value
            })
        
        return results
    
    # ==================== Seasonality Analysis ====================
    
    def detect_seasonality(self, data: List[float], 
                          period: int = 7) -> Dict[str, Any]:
        """Detect seasonal patterns in data"""
        if len(data) < period * 2:
            return {'seasonal': False, 'pattern': []}
        
        # Calculate seasonal indices
        n_periods = len(data) // period
        seasonal_indices = []
        
        for i in range(period):
            values = [data[i + j * period] for j in range(n_periods) 
                     if i + j * period < len(data)]
            if values:
                seasonal_indices.append(sum(values) / len(values))
        
        # Normalize indices
        mean_index = sum(seasonal_indices) / len(seasonal_indices)
        normalized_indices = [idx / mean_index if mean_index != 0 else 1 
                            for idx in seasonal_indices]
        
        # Calculate variance of indices to determine seasonality strength
        variance = sum((idx - 1) ** 2 for idx in normalized_indices) / len(normalized_indices)
        seasonality_strength = math.sqrt(variance)
        
        return {
            'seasonal': seasonality_strength > 0.1,
            'period': period,
            'strength': seasonality_strength,
            'pattern': normalized_indices,
            'peak_index': normalized_indices.index(max(normalized_indices)),
            'trough_index': normalized_indices.index(min(normalized_indices))
        }
    
    # ==================== Anomaly Detection ====================
    
    def detect_anomalies(self, data: List[float],
                        method: str = 'zscore',
                        threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies in time series data"""
        if len(data) < 3:
            return []
        
        anomalies = []
        
        if method == 'zscore':
            mean = sum(data) / len(data)
            std = math.sqrt(sum((x - mean) ** 2 for x in data) / len(data))
            
            if std == 0:
                return []
            
            for i, value in enumerate(data):
                zscore = (value - mean) / std
                if abs(zscore) > threshold:
                    anomalies.append({
                        'index': i,
                        'value': value,
                        'zscore': zscore,
                        'type': 'high' if zscore > 0 else 'low'
                    })
        
        elif method == 'iqr':
            sorted_data = sorted(data)
            q1_idx = int(len(sorted_data) * 0.25)
            q3_idx = int(len(sorted_data) * 0.75)
            q1 = sorted_data[q1_idx]
            q3 = sorted_data[q3_idx]
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            for i, value in enumerate(data):
                if value < lower_bound or value > upper_bound:
                    anomalies.append({
                        'index': i,
                        'value': value,
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound,
                        'type': 'high' if value > upper_bound else 'low'
                    })
        
        return anomalies
    
    # ==================== Database Queries ====================
    
    def get_metric_trend(self, session: Session,
                        metric_type: str,
                        granularity: str = 'day',
                        days: int = 30) -> Dict[str, Any]:
        """Get trend analysis for a specific metric"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        date_trunc = func.date_trunc(granularity, RFPMetric.recorded_at)
        
        # Query based on metric type
        if metric_type == 'rfp_count':
            query = session.query(
                date_trunc.label('period'),
                func.count(RFPMetric.id).label('value')
            ).filter(
                RFPMetric.recorded_at >= start_date
            ).group_by(date_trunc).order_by(date_trunc)
        
        elif metric_type == 'processing_time':
            query = session.query(
                date_trunc.label('period'),
                func.avg(RFPMetric.total_processing_time_ms).label('value')
            ).filter(
                RFPMetric.recorded_at >= start_date
            ).group_by(date_trunc).order_by(date_trunc)
        
        elif metric_type == 'match_accuracy':
            date_trunc = func.date_trunc(granularity, MatchAccuracyMetric.recorded_at)
            query = session.query(
                date_trunc.label('period'),
                (func.sum(func.cast(MatchAccuracyMetric.is_correct, 
                         Integer)) * 100.0 / func.count(MatchAccuracyMetric.id)).label('value')
            ).filter(
                MatchAccuracyMetric.recorded_at >= start_date
            ).group_by(date_trunc).order_by(date_trunc)
        
        elif metric_type == 'win_rate':
            date_trunc = func.date_trunc(granularity, WinLossRecord.recorded_at)
            total_expr = func.count(WinLossRecord.id)
            won_expr = func.sum(func.cast(WinLossRecord.outcome == 'won', Integer))
            query = session.query(
                date_trunc.label('period'),
                (won_expr * 100.0 / func.nullif(total_expr, 0)).label('value')
            ).filter(
                WinLossRecord.recorded_at >= start_date,
                WinLossRecord.outcome.in_(['won', 'lost'])
            ).group_by(date_trunc).order_by(date_trunc)
        
        elif metric_type == 'costs':
            date_trunc = func.date_trunc(granularity, CostRecord.recorded_at)
            query = session.query(
                date_trunc.label('period'),
                func.sum(CostRecord.amount).label('value')
            ).filter(
                CostRecord.recorded_at >= start_date
            ).group_by(date_trunc).order_by(date_trunc)
        
        else:
            return {'error': f'Unknown metric type: {metric_type}'}
        
        results = query.all()
        
        data = [float(r.value or 0) for r in results]
        periods = [r.period.isoformat() if r.period else None for r in results]
        
        # Calculate trend
        trend = self.detect_trend(data) if data else {}
        
        # Calculate moving averages
        ma_7 = self.calculate_moving_average(data, 7) if len(data) >= 7 else data
        ema = self.calculate_exponential_moving_average(data, 0.3)
        
        # Detect anomalies
        anomalies = self.detect_anomalies(data)
        
        return {
            'metric': metric_type,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'granularity': granularity,
                'days': days
            },
            'data': [
                {'period': periods[i], 'value': data[i], 'ma_7': ma_7[i], 'ema': ema[i]}
                for i in range(len(data))
            ],
            'trend': trend,
            'anomalies': anomalies,
            'summary': {
                'current': data[-1] if data else 0,
                'previous': data[-2] if len(data) > 1 else 0,
                'change': data[-1] - data[-2] if len(data) > 1 else 0,
                'min': min(data) if data else 0,
                'max': max(data) if data else 0,
                'avg': sum(data) / len(data) if data else 0
            }
        }
    
    def compare_periods(self, session: Session,
                       metric_type: str,
                       current_start: datetime,
                       current_end: datetime,
                       previous_start: datetime,
                       previous_end: datetime) -> Dict[str, Any]:
        """Compare metrics between two periods"""
        
        # Get data for both periods
        current_trend = self.get_metric_trend(
            session, metric_type, 'day',
            (current_end - current_start).days
        )
        
        previous_trend = self.get_metric_trend(
            session, metric_type, 'day',
            (previous_end - previous_start).days
        )
        
        current_avg = current_trend['summary']['avg']
        previous_avg = previous_trend['summary']['avg']
        
        change = current_avg - previous_avg
        change_percent = self.calculate_growth_rate(current_avg, previous_avg)
        
        return {
            'metric': metric_type,
            'current_period': {
                'start': current_start.isoformat(),
                'end': current_end.isoformat(),
                'avg': current_avg,
                'trend': current_trend['trend']
            },
            'previous_period': {
                'start': previous_start.isoformat(),
                'end': previous_end.isoformat(),
                'avg': previous_avg,
                'trend': previous_trend['trend']
            },
            'comparison': {
                'absolute_change': change,
                'percent_change': change_percent,
                'improved': change > 0 if metric_type in ['match_accuracy', 'win_rate'] else change < 0
            }
        }
    
    def get_comprehensive_trend_report(self, session: Session, 
                                       days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive trend report for all metrics"""
        metrics = ['rfp_count', 'processing_time', 'win_rate', 'costs']
        
        report = {
            'period': {
                'days': days,
                'end': datetime.utcnow().isoformat()
            },
            'trends': {}
        }
        
        for metric in metrics:
            try:
                report['trends'][metric] = self.get_metric_trend(session, metric, 'day', days)
            except Exception as e:
                logger.error(f"Error getting trend for {metric}: {e}")
                report['trends'][metric] = {'error': str(e)}
        
        return report


# Fix missing import
from sqlalchemy import Integer
