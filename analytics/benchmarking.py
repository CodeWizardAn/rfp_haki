"""
Benchmarking
Performance benchmarking against baselines and historical data

Features:
- Baseline establishment
- Performance comparison
- Trend benchmarking
- Industry comparison
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of benchmarks"""
    HISTORICAL = 'historical'  # Compare to own history
    BASELINE = 'baseline'      # Compare to established baseline
    TARGET = 'target'          # Compare to target goals
    INDUSTRY = 'industry'      # Compare to industry standards


@dataclass
class Benchmark:
    """A benchmark definition"""
    id: str
    name: str
    metric_name: str
    benchmark_type: BenchmarkType
    baseline_value: float
    unit: str = ''
    description: str = ''
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Target thresholds
    good_threshold: Optional[float] = None  # Value considered "good"
    excellent_threshold: Optional[float] = None  # Value considered "excellent"
    
    # Direction: True = higher is better, False = lower is better
    higher_is_better: bool = True


@dataclass
class BenchmarkResult:
    """Result of a benchmark comparison"""
    benchmark_id: str
    benchmark_name: str
    metric_name: str
    current_value: float
    baseline_value: float
    difference: float
    percentage_change: float
    rating: str  # 'excellent', 'good', 'average', 'poor'
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'benchmark_id': self.benchmark_id,
            'benchmark_name': self.benchmark_name,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'baseline_value': self.baseline_value,
            'difference': self.difference,
            'percentage_change': self.percentage_change,
            'rating': self.rating,
            'timestamp': self.timestamp.isoformat()
        }


class BenchmarkManager:
    """
    Manages benchmarks and performance comparisons
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self._benchmarks: Dict[str, Benchmark] = {}
        self._results_history: List[BenchmarkResult] = []
        
        # Industry standard benchmarks (can be overridden)
        self._industry_standards: Dict[str, Dict[str, float]] = {
            'rfp_response_time_hours': {'baseline': 24, 'good': 12, 'excellent': 6},
            'win_rate_percent': {'baseline': 25, 'good': 35, 'excellent': 50},
            'match_accuracy_percent': {'baseline': 70, 'good': 85, 'excellent': 95},
            'cost_per_rfp_usd': {'baseline': 500, 'good': 300, 'excellent': 150},
        }
    
    # ==================== Benchmark Management ====================
    
    def create_benchmark(self, name: str, metric_name: str,
                        baseline_value: float,
                        benchmark_type: BenchmarkType = BenchmarkType.BASELINE,
                        higher_is_better: bool = True,
                        unit: str = '',
                        good_threshold: float = None,
                        excellent_threshold: float = None) -> Benchmark:
        """Create a new benchmark"""
        import uuid
        
        benchmark = Benchmark(
            id=str(uuid.uuid4()),
            name=name,
            metric_name=metric_name,
            benchmark_type=benchmark_type,
            baseline_value=baseline_value,
            unit=unit,
            higher_is_better=higher_is_better,
            good_threshold=good_threshold,
            excellent_threshold=excellent_threshold
        )
        
        self._benchmarks[benchmark.id] = benchmark
        logger.info(f"Created benchmark: {name}")
        return benchmark
    
    def update_baseline(self, benchmark_id: str, new_value: float) -> bool:
        """Update a benchmark's baseline value"""
        if benchmark_id in self._benchmarks:
            self._benchmarks[benchmark_id].baseline_value = new_value
            self._benchmarks[benchmark_id].updated_at = datetime.utcnow()
            return True
        return False
    
    def get_benchmark(self, benchmark_id: str) -> Optional[Benchmark]:
        """Get a specific benchmark"""
        return self._benchmarks.get(benchmark_id)
    
    def get_all_benchmarks(self) -> List[Benchmark]:
        """Get all benchmarks"""
        return list(self._benchmarks.values())
    
    def delete_benchmark(self, benchmark_id: str) -> bool:
        """Delete a benchmark"""
        if benchmark_id in self._benchmarks:
            del self._benchmarks[benchmark_id]
            return True
        return False
    
    # ==================== Baseline Establishment ====================
    
    def establish_baseline_from_history(self, session, metric_name: str,
                                        days: int = 30,
                                        aggregation: str = 'mean') -> float:
        """Establish a baseline from historical data"""
        from .models import AnalyticsSnapshot
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = session.query(
            AnalyticsSnapshot.value
        ).filter(
            AnalyticsSnapshot.metric_name == metric_name,
            AnalyticsSnapshot.timestamp >= start_date
        )
        
        values = [r.value for r in query.all()]
        
        if not values:
            return 0.0
        
        if aggregation == 'mean':
            return sum(values) / len(values)
        elif aggregation == 'median':
            sorted_values = sorted(values)
            n = len(sorted_values)
            mid = n // 2
            if n % 2 == 0:
                return (sorted_values[mid - 1] + sorted_values[mid]) / 2
            return sorted_values[mid]
        elif aggregation == 'min':
            return min(values)
        elif aggregation == 'max':
            return max(values)
        elif aggregation == 'p90':
            sorted_values = sorted(values)
            idx = int(len(sorted_values) * 0.9)
            return sorted_values[idx]
        else:
            return sum(values) / len(values)
    
    def auto_create_baselines(self, session, days: int = 30) -> List[Benchmark]:
        """Automatically create baselines from historical data"""
        from .models import AnalyticsSnapshot
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get distinct metric names
        metrics = session.query(
            AnalyticsSnapshot.metric_name
        ).filter(
            AnalyticsSnapshot.timestamp >= start_date
        ).distinct().all()
        
        created_benchmarks = []
        
        for (metric_name,) in metrics:
            baseline = self.establish_baseline_from_history(session, metric_name, days)
            
            benchmark = self.create_benchmark(
                name=f"{metric_name} Baseline",
                metric_name=metric_name,
                baseline_value=baseline,
                benchmark_type=BenchmarkType.HISTORICAL
            )
            created_benchmarks.append(benchmark)
        
        return created_benchmarks
    
    # ==================== Comparison ====================
    
    def compare(self, benchmark_id: str, current_value: float) -> BenchmarkResult:
        """Compare a current value against a benchmark"""
        benchmark = self._benchmarks.get(benchmark_id)
        if not benchmark:
            raise ValueError(f"Benchmark not found: {benchmark_id}")
        
        baseline = benchmark.baseline_value
        difference = current_value - baseline
        percentage_change = (difference / baseline * 100) if baseline != 0 else 0
        
        # Determine rating
        rating = self._calculate_rating(benchmark, current_value)
        
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            benchmark_name=benchmark.name,
            metric_name=benchmark.metric_name,
            current_value=current_value,
            baseline_value=baseline,
            difference=difference,
            percentage_change=percentage_change,
            rating=rating
        )
        
        self._results_history.append(result)
        return result
    
    def _calculate_rating(self, benchmark: Benchmark, value: float) -> str:
        """Calculate the rating for a value against a benchmark"""
        if benchmark.excellent_threshold is not None:
            if benchmark.higher_is_better:
                if value >= benchmark.excellent_threshold:
                    return 'excellent'
            else:
                if value <= benchmark.excellent_threshold:
                    return 'excellent'
        
        if benchmark.good_threshold is not None:
            if benchmark.higher_is_better:
                if value >= benchmark.good_threshold:
                    return 'good'
            else:
                if value <= benchmark.good_threshold:
                    return 'good'
        
        # Compare to baseline
        baseline = benchmark.baseline_value
        if benchmark.higher_is_better:
            if value >= baseline:
                return 'average'
            return 'poor'
        else:
            if value <= baseline:
                return 'average'
            return 'poor'
    
    def compare_to_industry(self, metric_name: str, 
                           current_value: float) -> Optional[BenchmarkResult]:
        """Compare a value against industry standards"""
        if metric_name not in self._industry_standards:
            return None
        
        standards = self._industry_standards[metric_name]
        baseline = standards['baseline']
        good = standards.get('good', baseline)
        excellent = standards.get('excellent', good)
        
        difference = current_value - baseline
        percentage_change = (difference / baseline * 100) if baseline != 0 else 0
        
        # Determine rating based on industry standards
        higher_is_better = self._is_higher_better(metric_name)
        
        if higher_is_better:
            if current_value >= excellent:
                rating = 'excellent'
            elif current_value >= good:
                rating = 'good'
            elif current_value >= baseline:
                rating = 'average'
            else:
                rating = 'poor'
        else:
            if current_value <= excellent:
                rating = 'excellent'
            elif current_value <= good:
                rating = 'good'
            elif current_value <= baseline:
                rating = 'average'
            else:
                rating = 'poor'
        
        return BenchmarkResult(
            benchmark_id='industry',
            benchmark_name=f'{metric_name} Industry Standard',
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline,
            difference=difference,
            percentage_change=percentage_change,
            rating=rating
        )
    
    def _is_higher_better(self, metric_name: str) -> bool:
        """Determine if higher values are better for a metric"""
        lower_is_better = ['time', 'cost', 'error', 'latency', 'duration']
        return not any(term in metric_name.lower() for term in lower_is_better)
    
    # ==================== Batch Comparison ====================
    
    def compare_all(self, session, days: int = 7) -> List[BenchmarkResult]:
        """Compare all benchmarks against current values"""
        results = []
        
        for benchmark in self._benchmarks.values():
            current_value = self._get_current_metric_value(
                session, benchmark.metric_name, days
            )
            
            if current_value is not None:
                result = self.compare(benchmark.id, current_value)
                results.append(result)
        
        return results
    
    def _get_current_metric_value(self, session, metric_name: str,
                                  days: int = 7) -> Optional[float]:
        """Get the current value for a metric"""
        from .models import AnalyticsSnapshot
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = session.query(
            func.avg(AnalyticsSnapshot.value)
        ).filter(
            AnalyticsSnapshot.metric_name == metric_name,
            AnalyticsSnapshot.timestamp >= start_date
        ).scalar()
        
        return result
    
    # ==================== Trend Benchmarking ====================
    
    def benchmark_trend(self, session, metric_name: str,
                       current_period_days: int = 7,
                       baseline_period_days: int = 30) -> Dict[str, Any]:
        """Compare current trend against baseline trend"""
        from .models import AnalyticsSnapshot
        from sqlalchemy import func
        
        now = datetime.utcnow()
        current_start = now - timedelta(days=current_period_days)
        baseline_end = current_start
        baseline_start = baseline_end - timedelta(days=baseline_period_days)
        
        # Get current period data
        current_result = session.query(
            func.avg(AnalyticsSnapshot.value).label('avg'),
            func.min(AnalyticsSnapshot.value).label('min'),
            func.max(AnalyticsSnapshot.value).label('max'),
            func.count(AnalyticsSnapshot.id).label('count')
        ).filter(
            AnalyticsSnapshot.metric_name == metric_name,
            AnalyticsSnapshot.timestamp >= current_start
        ).first()
        
        # Get baseline period data
        baseline_result = session.query(
            func.avg(AnalyticsSnapshot.value).label('avg'),
            func.min(AnalyticsSnapshot.value).label('min'),
            func.max(AnalyticsSnapshot.value).label('max'),
            func.count(AnalyticsSnapshot.id).label('count')
        ).filter(
            AnalyticsSnapshot.metric_name == metric_name,
            AnalyticsSnapshot.timestamp >= baseline_start,
            AnalyticsSnapshot.timestamp < baseline_end
        ).first()
        
        current_avg = current_result.avg or 0
        baseline_avg = baseline_result.avg or 0
        
        change = current_avg - baseline_avg
        percentage_change = (change / baseline_avg * 100) if baseline_avg != 0 else 0
        
        return {
            'metric_name': metric_name,
            'current_period': {
                'days': current_period_days,
                'avg': current_avg,
                'min': current_result.min,
                'max': current_result.max,
                'count': current_result.count
            },
            'baseline_period': {
                'days': baseline_period_days,
                'avg': baseline_avg,
                'min': baseline_result.min,
                'max': baseline_result.max,
                'count': baseline_result.count
            },
            'change': change,
            'percentage_change': percentage_change,
            'trend': 'improving' if (
                (self._is_higher_better(metric_name) and change > 0) or
                (not self._is_higher_better(metric_name) and change < 0)
            ) else 'declining' if change != 0 else 'stable'
        }
    
    # ==================== Reports ====================
    
    def get_benchmark_report(self, session, days: int = 7) -> Dict[str, Any]:
        """Generate a comprehensive benchmark report"""
        results = self.compare_all(session, days)
        
        # Categorize by rating
        by_rating = {'excellent': [], 'good': [], 'average': [], 'poor': []}
        for result in results:
            by_rating[result.rating].append(result.to_dict())
        
        # Calculate overall score
        rating_scores = {'excellent': 4, 'good': 3, 'average': 2, 'poor': 1}
        if results:
            total_score = sum(rating_scores[r.rating] for r in results)
            max_score = len(results) * 4
            overall_score = (total_score / max_score) * 100
        else:
            overall_score = 0
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'period_days': days,
            'total_benchmarks': len(results),
            'overall_score': round(overall_score, 1),
            'summary': {
                'excellent': len(by_rating['excellent']),
                'good': len(by_rating['good']),
                'average': len(by_rating['average']),
                'poor': len(by_rating['poor'])
            },
            'results': [r.to_dict() for r in results],
            'by_rating': by_rating
        }
    
    def get_improvement_recommendations(self, session, 
                                        days: int = 7) -> List[Dict[str, Any]]:
        """Get recommendations for improvement based on benchmarks"""
        results = self.compare_all(session, days)
        recommendations = []
        
        for result in results:
            if result.rating in ['poor', 'average']:
                benchmark = self._benchmarks.get(result.benchmark_id)
                if benchmark:
                    improvement_needed = benchmark.baseline_value - result.current_value
                    if not benchmark.higher_is_better:
                        improvement_needed = result.current_value - benchmark.baseline_value
                    
                    recommendations.append({
                        'metric': result.metric_name,
                        'current_value': result.current_value,
                        'target_value': benchmark.baseline_value,
                        'improvement_needed': abs(improvement_needed),
                        'priority': 'high' if result.rating == 'poor' else 'medium',
                        'suggestion': self._generate_suggestion(
                            result.metric_name, result.rating
                        )
                    })
        
        # Sort by priority
        recommendations.sort(key=lambda x: 0 if x['priority'] == 'high' else 1)
        return recommendations
    
    def _generate_suggestion(self, metric_name: str, rating: str) -> str:
        """Generate improvement suggestion based on metric"""
        suggestions = {
            'win_rate': 'Review pricing strategy and proposal quality',
            'response_time': 'Optimize processing pipeline and reduce manual steps',
            'cost': 'Analyze cost drivers and identify optimization opportunities',
            'accuracy': 'Improve matching algorithms and training data',
            'error': 'Review error logs and implement additional validation'
        }
        
        for key, suggestion in suggestions.items():
            if key in metric_name.lower():
                return suggestion
        
        return f'Review and optimize {metric_name} processes'
