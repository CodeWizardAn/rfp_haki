"""
A/B Testing Framework
Framework for testing algorithm variants and measuring impact

Features:
- Experiment creation and management
- Traffic allocation
- Statistical significance testing
- Result analysis
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math
import logging

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment status"""
    DRAFT = 'draft'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


@dataclass
class Variant:
    """A variant in an experiment"""
    id: str
    name: str
    description: str = ''
    weight: float = 50.0  # Traffic allocation percentage
    is_control: bool = False
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Results for a variant"""
    variant_id: str
    variant_name: str
    sample_size: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    sum_value: float = 0.0
    mean_value: float = 0.0
    variance: float = 0.0
    
    def update(self, converted: bool, value: float = 0.0) -> None:
        """Update results with a new observation"""
        old_mean = self.mean_value
        self.sample_size += 1
        
        if converted:
            self.conversions += 1
        
        self.conversion_rate = self.conversions / self.sample_size
        self.sum_value += value
        
        # Welford's online algorithm for variance
        delta = value - old_mean
        self.mean_value = old_mean + delta / self.sample_size
        delta2 = value - self.mean_value
        self.variance = (
            (self.variance * (self.sample_size - 1) + delta * delta2) 
            / self.sample_size
        ) if self.sample_size > 1 else 0


@dataclass
class Experiment:
    """An A/B test experiment"""
    id: str
    name: str
    description: str
    metric_name: str  # Primary metric being tested
    variants: List[Variant] = field(default_factory=list)
    status: ExperimentStatus = ExperimentStatus.DRAFT
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Configuration
    min_sample_size: int = 100  # Minimum samples per variant
    confidence_level: float = 0.95  # Statistical confidence level
    min_detectable_effect: float = 0.05  # 5% minimum detectable effect
    
    # Results
    results: Dict[str, ExperimentResult] = field(default_factory=dict)
    winner: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'metric_name': self.metric_name,
            'variants': [
                {
                    'id': v.id,
                    'name': v.name,
                    'weight': v.weight,
                    'is_control': v.is_control
                }
                for v in self.variants
            ],
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'winner': self.winner
        }


class StatisticalAnalyzer:
    """
    Statistical analysis for A/B tests
    """
    
    @staticmethod
    def z_score(confidence_level: float) -> float:
        """Get z-score for a confidence level"""
        # Common z-scores
        z_scores = {
            0.90: 1.645,
            0.95: 1.960,
            0.99: 2.576
        }
        return z_scores.get(confidence_level, 1.960)
    
    @staticmethod
    def standard_error(p: float, n: int) -> float:
        """Calculate standard error for a proportion"""
        if n == 0:
            return 0
        return math.sqrt(p * (1 - p) / n)
    
    @staticmethod
    def pooled_standard_error(p1: float, n1: int, 
                             p2: float, n2: int) -> float:
        """Calculate pooled standard error for two proportions"""
        if n1 + n2 == 0:
            return 0
        pooled_p = (p1 * n1 + p2 * n2) / (n1 + n2)
        return math.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
    
    @staticmethod
    def calculate_sample_size(baseline_rate: float,
                             min_detectable_effect: float,
                             confidence_level: float = 0.95,
                             power: float = 0.80) -> int:
        """Calculate required sample size per variant"""
        z_alpha = StatisticalAnalyzer.z_score(confidence_level)
        z_beta = StatisticalAnalyzer.z_score(power)
        
        p1 = baseline_rate
        p2 = baseline_rate * (1 + min_detectable_effect)
        
        pooled_p = (p1 + p2) / 2
        effect = abs(p2 - p1)
        
        if effect == 0:
            return 1000  # Default
        
        n = (2 * pooled_p * (1 - pooled_p) * (z_alpha + z_beta) ** 2) / (effect ** 2)
        return int(math.ceil(n))
    
    @staticmethod
    def two_proportion_z_test(result1: ExperimentResult,
                              result2: ExperimentResult,
                              confidence_level: float = 0.95) -> Dict[str, Any]:
        """Perform two-proportion z-test"""
        p1 = result1.conversion_rate
        n1 = result1.sample_size
        p2 = result2.conversion_rate
        n2 = result2.sample_size
        
        if n1 == 0 or n2 == 0:
            return {
                'statistically_significant': False,
                'z_statistic': 0,
                'p_value': 1.0,
                'confidence_interval': (0, 0),
                'lift': 0
            }
        
        # Calculate z-statistic
        se = StatisticalAnalyzer.pooled_standard_error(p1, n1, p2, n2)
        
        if se == 0:
            z_stat = 0
        else:
            z_stat = (p2 - p1) / se
        
        # Calculate p-value (two-tailed)
        # Using approximation
        p_value = 2 * (1 - StatisticalAnalyzer._normal_cdf(abs(z_stat)))
        
        # Confidence interval for the difference
        z_critical = StatisticalAnalyzer.z_score(confidence_level)
        margin = z_critical * se
        ci_low = (p2 - p1) - margin
        ci_high = (p2 - p1) + margin
        
        # Calculate lift
        lift = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
        
        return {
            'statistically_significant': p_value < (1 - confidence_level),
            'z_statistic': z_stat,
            'p_value': p_value,
            'confidence_interval': (ci_low, ci_high),
            'lift': lift,
            'control_rate': p1,
            'treatment_rate': p2
        }
    
    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximation of normal CDF"""
        # Abramowitz and Stegun approximation
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911
        
        sign = 1 if x >= 0 else -1
        x = abs(x) / math.sqrt(2)
        
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
        
        return 0.5 * (1.0 + sign * y)
    
    @staticmethod
    def t_test_means(result1: ExperimentResult,
                    result2: ExperimentResult,
                    confidence_level: float = 0.95) -> Dict[str, Any]:
        """Perform t-test for means"""
        n1 = result1.sample_size
        n2 = result2.sample_size
        mean1 = result1.mean_value
        mean2 = result2.mean_value
        var1 = result1.variance
        var2 = result2.variance
        
        if n1 < 2 or n2 < 2:
            return {
                'statistically_significant': False,
                't_statistic': 0,
                'p_value': 1.0,
                'difference': mean2 - mean1
            }
        
        # Welch's t-test
        se = math.sqrt(var1/n1 + var2/n2) if (var1/n1 + var2/n2) > 0 else 0
        
        if se == 0:
            t_stat = 0
        else:
            t_stat = (mean2 - mean1) / se
        
        # Degrees of freedom (Welch-Satterthwaite)
        if var1/n1 + var2/n2 > 0:
            df_num = (var1/n1 + var2/n2) ** 2
            df_denom = (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
            df = df_num / df_denom if df_denom > 0 else n1 + n2 - 2
        else:
            df = n1 + n2 - 2
        
        # Approximate p-value using normal distribution for large samples
        p_value = 2 * (1 - StatisticalAnalyzer._normal_cdf(abs(t_stat)))
        
        return {
            'statistically_significant': p_value < (1 - confidence_level),
            't_statistic': t_stat,
            'p_value': p_value,
            'degrees_of_freedom': df,
            'difference': mean2 - mean1,
            'control_mean': mean1,
            'treatment_mean': mean2
        }


class ABTestingFramework:
    """
    Framework for managing A/B tests
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self._experiments: Dict[str, Experiment] = {}
        self._user_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> {exp_id: variant_id}
        self._analyzer = StatisticalAnalyzer()
    
    # ==================== Experiment Management ====================
    
    def create_experiment(self, name: str, description: str,
                         metric_name: str,
                         variants: List[Dict[str, Any]] = None) -> Experiment:
        """Create a new experiment"""
        import uuid
        
        exp_id = str(uuid.uuid4())
        
        # Create default A/B variants if none provided
        if variants is None:
            variants = [
                {'name': 'Control', 'weight': 50, 'is_control': True},
                {'name': 'Treatment', 'weight': 50, 'is_control': False}
            ]
        
        variant_objects = []
        for i, v in enumerate(variants):
            variant_objects.append(Variant(
                id=str(uuid.uuid4()),
                name=v.get('name', f'Variant {i}'),
                description=v.get('description', ''),
                weight=v.get('weight', 100 / len(variants)),
                is_control=v.get('is_control', i == 0),
                config=v.get('config', {})
            ))
        
        experiment = Experiment(
            id=exp_id,
            name=name,
            description=description,
            metric_name=metric_name,
            variants=variant_objects
        )
        
        # Initialize results
        for variant in variant_objects:
            experiment.results[variant.id] = ExperimentResult(
                variant_id=variant.id,
                variant_name=variant.name
            )
        
        self._experiments[exp_id] = experiment
        logger.info(f"Created experiment: {name}")
        return experiment
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        if experiment_id not in self._experiments:
            return False
        
        exp = self._experiments[experiment_id]
        if exp.status != ExperimentStatus.DRAFT:
            return False
        
        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.utcnow()
        logger.info(f"Started experiment: {exp.name}")
        return True
    
    def pause_experiment(self, experiment_id: str) -> bool:
        """Pause an experiment"""
        if experiment_id not in self._experiments:
            return False
        
        exp = self._experiments[experiment_id]
        if exp.status != ExperimentStatus.RUNNING:
            return False
        
        exp.status = ExperimentStatus.PAUSED
        logger.info(f"Paused experiment: {exp.name}")
        return True
    
    def resume_experiment(self, experiment_id: str) -> bool:
        """Resume a paused experiment"""
        if experiment_id not in self._experiments:
            return False
        
        exp = self._experiments[experiment_id]
        if exp.status != ExperimentStatus.PAUSED:
            return False
        
        exp.status = ExperimentStatus.RUNNING
        logger.info(f"Resumed experiment: {exp.name}")
        return True
    
    def complete_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Complete an experiment and analyze results"""
        if experiment_id not in self._experiments:
            return None
        
        exp = self._experiments[experiment_id]
        exp.status = ExperimentStatus.COMPLETED
        exp.ended_at = datetime.utcnow()
        
        # Analyze and determine winner
        analysis = self.analyze_experiment(experiment_id)
        if analysis and analysis.get('winner'):
            exp.winner = analysis['winner']['variant_id']
        
        logger.info(f"Completed experiment: {exp.name}")
        return analysis
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment"""
        return self._experiments.get(experiment_id)
    
    def get_all_experiments(self, status: ExperimentStatus = None) -> List[Experiment]:
        """Get all experiments, optionally filtered by status"""
        experiments = list(self._experiments.values())
        if status:
            experiments = [e for e in experiments if e.status == status]
        return experiments
    
    # ==================== Assignment ====================
    
    def get_variant(self, experiment_id: str, user_id: str) -> Optional[Variant]:
        """Get the variant assignment for a user"""
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return None
        
        # Check for existing assignment
        if user_id in self._user_assignments:
            if experiment_id in self._user_assignments[user_id]:
                variant_id = self._user_assignments[user_id][experiment_id]
                for v in exp.variants:
                    if v.id == variant_id:
                        return v
        
        # Assign new variant based on weights
        variant = self._assign_variant(exp, user_id)
        
        # Store assignment
        if user_id not in self._user_assignments:
            self._user_assignments[user_id] = {}
        self._user_assignments[user_id][experiment_id] = variant.id
        
        return variant
    
    def _assign_variant(self, experiment: Experiment, user_id: str) -> Variant:
        """Assign a variant to a user"""
        # Use deterministic assignment based on user_id for consistency
        hash_val = hash(f"{experiment.id}:{user_id}")
        random.seed(hash_val)
        
        # Weighted random selection
        total_weight = sum(v.weight for v in experiment.variants)
        r = random.uniform(0, total_weight)
        
        cumulative = 0
        for variant in experiment.variants:
            cumulative += variant.weight
            if r <= cumulative:
                return variant
        
        return experiment.variants[-1]
    
    # ==================== Recording Results ====================
    
    def record_event(self, experiment_id: str, user_id: str,
                    converted: bool, value: float = 0.0) -> bool:
        """Record an event (conversion or non-conversion)"""
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return False
        
        # Get user's variant
        if user_id not in self._user_assignments:
            return False
        if experiment_id not in self._user_assignments[user_id]:
            return False
        
        variant_id = self._user_assignments[user_id][experiment_id]
        
        # Update results
        if variant_id in exp.results:
            exp.results[variant_id].update(converted, value)
            return True
        
        return False
    
    def record_conversion(self, experiment_id: str, user_id: str,
                         value: float = 1.0) -> bool:
        """Record a conversion"""
        return self.record_event(experiment_id, user_id, True, value)
    
    # ==================== Analysis ====================
    
    def analyze_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Analyze experiment results"""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None
        
        # Find control variant
        control_result = None
        control_variant = None
        for variant in exp.variants:
            if variant.is_control:
                control_variant = variant
                control_result = exp.results.get(variant.id)
                break
        
        if not control_result:
            # Use first variant as control
            control_variant = exp.variants[0]
            control_result = exp.results.get(control_variant.id)
        
        # Analyze each treatment against control
        comparisons = []
        winner = None
        best_lift = 0
        
        for variant in exp.variants:
            if variant.id == control_variant.id:
                continue
            
            treatment_result = exp.results.get(variant.id)
            if not treatment_result:
                continue
            
            # Statistical test
            stats = self._analyzer.two_proportion_z_test(
                control_result, treatment_result, exp.confidence_level
            )
            
            comparison = {
                'variant_id': variant.id,
                'variant_name': variant.name,
                'sample_size': treatment_result.sample_size,
                'conversions': treatment_result.conversions,
                'conversion_rate': treatment_result.conversion_rate,
                **stats
            }
            comparisons.append(comparison)
            
            # Track winner
            if (stats['statistically_significant'] and 
                stats['lift'] > best_lift):
                best_lift = stats['lift']
                winner = comparison
        
        # Calculate overall statistics
        total_samples = sum(r.sample_size for r in exp.results.values())
        min_samples_reached = all(
            r.sample_size >= exp.min_sample_size 
            for r in exp.results.values()
        )
        
        return {
            'experiment_id': exp.id,
            'experiment_name': exp.name,
            'status': exp.status.value,
            'control': {
                'variant_id': control_variant.id,
                'variant_name': control_variant.name,
                'sample_size': control_result.sample_size,
                'conversions': control_result.conversions,
                'conversion_rate': control_result.conversion_rate
            },
            'comparisons': comparisons,
            'winner': winner,
            'total_samples': total_samples,
            'min_samples_reached': min_samples_reached,
            'confidence_level': exp.confidence_level,
            'duration': self._calculate_duration(exp)
        }
    
    def _calculate_duration(self, exp: Experiment) -> Optional[Dict[str, Any]]:
        """Calculate experiment duration"""
        if not exp.started_at:
            return None
        
        end = exp.ended_at or datetime.utcnow()
        duration = end - exp.started_at
        
        return {
            'days': duration.days,
            'hours': duration.seconds // 3600,
            'total_hours': duration.total_seconds() / 3600
        }
    
    def get_required_sample_size(self, experiment_id: str) -> int:
        """Get the required sample size for statistical significance"""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return 0
        
        # Get current control conversion rate
        control_rate = 0.1  # Default 10%
        for variant in exp.variants:
            if variant.is_control:
                result = exp.results.get(variant.id)
                if result and result.sample_size > 0:
                    control_rate = result.conversion_rate
                break
        
        return self._analyzer.calculate_sample_size(
            control_rate,
            exp.min_detectable_effect,
            exp.confidence_level
        )
    
    # ==================== Reports ====================
    
    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of an experiment"""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None
        
        analysis = self.analyze_experiment(experiment_id)
        required_samples = self.get_required_sample_size(experiment_id)
        
        current_samples = min(
            r.sample_size for r in exp.results.values()
        ) if exp.results else 0
        
        progress = (current_samples / required_samples * 100) if required_samples > 0 else 0
        
        return {
            **exp.to_dict(),
            'analysis': analysis,
            'required_sample_size': required_samples,
            'current_min_samples': current_samples,
            'progress_percent': min(100, progress)
        }
    
    def get_all_experiments_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all experiments"""
        summaries = []
        for exp_id in self._experiments:
            summary = self.get_experiment_summary(exp_id)
            if summary:
                summaries.append(summary)
        return summaries
