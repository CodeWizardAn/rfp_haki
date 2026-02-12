"""
Predictive Analytics
Machine learning based predictions for RFP processing

Features:
- Win probability prediction
- Processing time estimation
- Match quality prediction
- Trend forecasting
- Risk assessment
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import math
import logging
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import RFPMetric, MatchAccuracyMetric, WinLossRecord
from .trend_analysis import TrendAnalyzer

logger = logging.getLogger(__name__)


class SimpleLinearRegression:
    """Simple linear regression implementation"""
    
    def __init__(self):
        self.slope = 0
        self.intercept = 0
        self.r_squared = 0
    
    def fit(self, X: List[float], y: List[float]):
        """Fit the model"""
        if len(X) != len(y) or len(X) < 2:
            return self
        
        n = len(X)
        x_mean = sum(X) / n
        y_mean = sum(y) / n
        
        numerator = sum((X[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((X[i] - x_mean) ** 2 for i in range(n))
        
        self.slope = numerator / denominator if denominator != 0 else 0
        self.intercept = y_mean - self.slope * x_mean
        
        # Calculate R-squared
        y_pred = [self.predict(x) for x in X]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return self
    
    def predict(self, x: float) -> float:
        """Predict y for given x"""
        return self.slope * x + self.intercept


class NaiveBayesClassifier:
    """Simple Naive Bayes classifier for win prediction"""
    
    def __init__(self):
        self.class_priors = {}
        self.feature_stats = {}
    
    def fit(self, features: List[Dict[str, float]], labels: List[str]):
        """Fit the classifier"""
        if not features or not labels:
            return self
        
        # Calculate class priors
        label_counts = defaultdict(int)
        for label in labels:
            label_counts[label] += 1
        
        total = len(labels)
        self.class_priors = {k: v / total for k, v in label_counts.items()}
        
        # Calculate feature statistics per class
        self.feature_stats = {label: {} for label in self.class_priors.keys()}
        
        for label in self.class_priors.keys():
            label_features = [f for f, l in zip(features, labels) if l == label]
            
            if not label_features:
                continue
            
            # Get all feature names
            feature_names = set()
            for f in label_features:
                feature_names.update(f.keys())
            
            for feature_name in feature_names:
                values = [f.get(feature_name, 0) for f in label_features]
                if values:
                    mean = sum(values) / len(values)
                    variance = sum((v - mean) ** 2 for v in values) / len(values)
                    self.feature_stats[label][feature_name] = {
                        'mean': mean,
                        'variance': max(variance, 0.001)  # Avoid zero variance
                    }
        
        return self
    
    def _gaussian_probability(self, x: float, mean: float, variance: float) -> float:
        """Calculate Gaussian probability"""
        if variance == 0:
            return 1.0 if x == mean else 0.0
        
        exponent = -((x - mean) ** 2) / (2 * variance)
        return (1 / math.sqrt(2 * math.pi * variance)) * math.exp(exponent)
    
    def predict_proba(self, features: Dict[str, float]) -> Dict[str, float]:
        """Predict class probabilities"""
        if not self.class_priors:
            return {}
        
        probabilities = {}
        
        for label, prior in self.class_priors.items():
            prob = prior
            
            for feature_name, value in features.items():
                if feature_name in self.feature_stats.get(label, {}):
                    stats = self.feature_stats[label][feature_name]
                    prob *= self._gaussian_probability(
                        value, stats['mean'], stats['variance']
                    )
            
            probabilities[label] = prob
        
        # Normalize
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v / total for k, v in probabilities.items()}
        
        return probabilities
    
    def predict(self, features: Dict[str, float]) -> str:
        """Predict class"""
        probs = self.predict_proba(features)
        if not probs:
            return 'unknown'
        return max(probs.keys(), key=lambda k: probs[k])


class PredictiveAnalytics:
    """
    Comprehensive predictive analytics for RFP processing
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.trend_analyzer = TrendAnalyzer(session_factory)
        
        # Models
        self._win_classifier = NaiveBayesClassifier()
        self._processing_time_model = SimpleLinearRegression()
        self._match_quality_model = SimpleLinearRegression()
        
        # Model state
        self._models_trained = False
        self._last_training = None
    
    # ==================== Model Training ====================
    
    def train_models(self, session: Session, days: int = 180):
        """Train all prediction models"""
        logger.info("Training predictive models...")
        
        self._train_win_predictor(session, days)
        self._train_processing_time_model(session, days)
        self._train_match_quality_model(session, days)
        
        self._models_trained = True
        self._last_training = datetime.utcnow()
        
        logger.info("Model training complete")
    
    def _train_win_predictor(self, session: Session, days: int):
        """Train win/loss prediction model"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        records = session.query(WinLossRecord).filter(
            WinLossRecord.recorded_at >= start_date,
            WinLossRecord.outcome.in_(['won', 'lost'])
        ).all()
        
        if len(records) < 10:
            logger.warning("Insufficient data for win predictor training")
            return
        
        features = []
        labels = []
        
        for record in records:
            feature = {
                'bid_amount': record.our_bid_amount or 0,
                'competitors_count': record.competitors_count or 0,
                'technical_score': record.technical_score or 0,
                'commercial_score': record.commercial_score or 0,
                'contract_duration': record.contract_duration_months or 0
            }
            features.append(feature)
            labels.append(record.outcome)
        
        self._win_classifier.fit(features, labels)
        logger.info(f"Win predictor trained on {len(records)} records")
    
    def _train_processing_time_model(self, session: Session, days: int):
        """Train processing time prediction model"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        records = session.query(RFPMetric).filter(
            RFPMetric.recorded_at >= start_date,
            RFPMetric.total_processing_time_ms.isnot(None),
            RFPMetric.requirements_count.isnot(None)
        ).all()
        
        if len(records) < 10:
            logger.warning("Insufficient data for processing time model")
            return
        
        X = [float(r.requirements_count or 0) for r in records]
        y = [float(r.total_processing_time_ms or 0) for r in records]
        
        self._processing_time_model.fit(X, y)
        logger.info(f"Processing time model trained (R²={self._processing_time_model.r_squared:.3f})")
    
    def _train_match_quality_model(self, session: Session, days: int):
        """Train match quality prediction model"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        records = session.query(MatchAccuracyMetric).filter(
            MatchAccuracyMetric.recorded_at >= start_date,
            MatchAccuracyMetric.predicted_confidence.isnot(None)
        ).all()
        
        if len(records) < 10:
            logger.warning("Insufficient data for match quality model")
            return
        
        # Use confidence as predictor of actual correctness
        X = [float(r.predicted_confidence or 0) for r in records]
        y = [1.0 if r.is_correct else 0.0 for r in records]
        
        self._match_quality_model.fit(X, y)
        logger.info(f"Match quality model trained (R²={self._match_quality_model.r_squared:.3f})")
    
    # ==================== Predictions ====================
    
    def predict_win_probability(self, bid_amount: float = None,
                               competitors_count: int = None,
                               technical_score: float = None,
                               commercial_score: float = None,
                               contract_duration: int = None) -> Dict[str, Any]:
        """Predict probability of winning a bid"""
        if not self._models_trained:
            return {
                'error': 'Models not trained',
                'win_probability': 0.5,
                'confidence': 0
            }
        
        features = {
            'bid_amount': bid_amount or 0,
            'competitors_count': competitors_count or 0,
            'technical_score': technical_score or 0,
            'commercial_score': commercial_score or 0,
            'contract_duration': contract_duration or 0
        }
        
        probabilities = self._win_classifier.predict_proba(features)
        
        return {
            'win_probability': probabilities.get('won', 0.5),
            'loss_probability': probabilities.get('lost', 0.5),
            'predicted_outcome': self._win_classifier.predict(features),
            'confidence': abs(probabilities.get('won', 0.5) - 0.5) * 2,
            'factors': features
        }
    
    def predict_processing_time(self, requirements_count: int) -> Dict[str, Any]:
        """Predict processing time based on requirements count"""
        if not self._models_trained:
            # Use default estimate
            estimated_time_ms = requirements_count * 1000  # 1 second per requirement
        else:
            estimated_time_ms = self._processing_time_model.predict(requirements_count)
        
        # Convert to readable format
        seconds = estimated_time_ms / 1000
        minutes = seconds / 60
        
        return {
            'estimated_time_ms': max(0, estimated_time_ms),
            'estimated_seconds': max(0, seconds),
            'estimated_minutes': max(0, minutes),
            'requirements_count': requirements_count,
            'model_r_squared': self._processing_time_model.r_squared,
            'confidence': min(0.9, self._processing_time_model.r_squared)
        }
    
    def predict_match_quality(self, confidence_score: float) -> Dict[str, Any]:
        """Predict whether a match is likely to be correct"""
        if not self._models_trained:
            # Use confidence directly
            probability = confidence_score
        else:
            probability = self._match_quality_model.predict(confidence_score)
            probability = max(0, min(1, probability))  # Clamp to [0, 1]
        
        return {
            'correct_probability': probability,
            'is_reliable': probability > 0.7,
            'confidence_score': confidence_score,
            'recommendation': 'accept' if probability > 0.7 else 'review' if probability > 0.5 else 'reject'
        }
    
    # ==================== Forecasting ====================
    
    def forecast_metric(self, session: Session,
                       metric_type: str,
                       periods_ahead: int = 7,
                       granularity: str = 'day') -> Dict[str, Any]:
        """Forecast future values for a metric"""
        # Get historical data
        trend_data = self.trend_analyzer.get_metric_trend(
            session, metric_type, granularity, days=90
        )
        
        if 'error' in trend_data or not trend_data.get('data'):
            return {
                'error': 'Insufficient historical data',
                'forecast': []
            }
        
        historical = [d['value'] for d in trend_data['data']]
        
        # Fit linear model on historical data
        X = list(range(len(historical)))
        model = SimpleLinearRegression()
        model.fit(X, historical)
        
        # Generate forecasts
        forecasts = []
        last_date = datetime.utcnow()
        
        for i in range(periods_ahead):
            future_x = len(historical) + i
            predicted_value = model.predict(future_x)
            
            if granularity == 'day':
                forecast_date = last_date + timedelta(days=i + 1)
            elif granularity == 'week':
                forecast_date = last_date + timedelta(weeks=i + 1)
            else:
                forecast_date = last_date + timedelta(days=i + 1)
            
            forecasts.append({
                'period': forecast_date.isoformat(),
                'predicted_value': max(0, predicted_value),
                'confidence_interval': {
                    'lower': max(0, predicted_value * 0.8),
                    'upper': predicted_value * 1.2
                }
            })
        
        return {
            'metric': metric_type,
            'historical_trend': trend_data['trend'],
            'model_r_squared': model.r_squared,
            'forecast': forecasts,
            'methodology': 'linear_regression'
        }
    
    def forecast_win_rate(self, session: Session,
                         periods_ahead: int = 4) -> Dict[str, Any]:
        """Forecast future win rate"""
        return self.forecast_metric(session, 'win_rate', periods_ahead, 'week')
    
    def forecast_costs(self, session: Session,
                      periods_ahead: int = 4) -> Dict[str, Any]:
        """Forecast future costs"""
        return self.forecast_metric(session, 'costs', periods_ahead, 'week')
    
    # ==================== Risk Assessment ====================
    
    def assess_rfp_risk(self, session: Session,
                       estimated_value: float,
                       requirements_count: int,
                       customer_name: str = None,
                       category: str = None) -> Dict[str, Any]:
        """Assess risk factors for an RFP"""
        risks = []
        risk_score = 0
        
        # Check processing time risk
        processing_prediction = self.predict_processing_time(requirements_count)
        if processing_prediction['estimated_minutes'] > 30:
            risks.append({
                'factor': 'processing_time',
                'level': 'medium',
                'description': f"High processing time expected ({processing_prediction['estimated_minutes']:.1f} min)",
                'score': 2
            })
            risk_score += 2
        
        # Check historical win rate with customer
        if customer_name:
            customer_history = session.query(
                func.count(WinLossRecord.id).label('total'),
                func.sum(func.cast(WinLossRecord.outcome == 'won', Integer)).label('wins')
            ).filter(
                WinLossRecord.customer_name == customer_name
            ).first()
            
            if customer_history.total and customer_history.total > 0:
                win_rate = (customer_history.wins or 0) / customer_history.total
                if win_rate < 0.3:
                    risks.append({
                        'factor': 'customer_history',
                        'level': 'high',
                        'description': f"Low historical win rate with customer ({win_rate:.1%})",
                        'score': 3
                    })
                    risk_score += 3
        
        # Check category performance
        if category:
            category_history = session.query(
                func.count(WinLossRecord.id).label('total'),
                func.sum(func.cast(WinLossRecord.outcome == 'won', Integer)).label('wins')
            ).filter(
                WinLossRecord.rfp_category == category
            ).first()
            
            if category_history.total and category_history.total > 0:
                win_rate = (category_history.wins or 0) / category_history.total
                if win_rate < 0.4:
                    risks.append({
                        'factor': 'category_performance',
                        'level': 'medium',
                        'description': f"Below average win rate in category ({win_rate:.1%})",
                        'score': 2
                    })
                    risk_score += 2
        
        # Determine overall risk level
        if risk_score >= 5:
            overall_level = 'high'
        elif risk_score >= 3:
            overall_level = 'medium'
        else:
            overall_level = 'low'
        
        return {
            'overall_risk_level': overall_level,
            'risk_score': risk_score,
            'max_score': 10,
            'risk_factors': risks,
            'recommendations': self._generate_risk_recommendations(risks)
        }
    
    def _generate_risk_recommendations(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on identified risks"""
        recommendations = []
        
        for risk in risks:
            if risk['factor'] == 'processing_time':
                recommendations.append("Consider prioritizing this RFP earlier to allow for processing time")
            elif risk['factor'] == 'customer_history':
                recommendations.append("Review past proposals to understand customer preferences")
            elif risk['factor'] == 'category_performance':
                recommendations.append("Analyze successful bids in this category for insights")
        
        if not recommendations:
            recommendations.append("No specific risk mitigations required")
        
        return recommendations
    
    def get_predictions_report(self, session: Session) -> Dict[str, Any]:
        """Generate comprehensive predictions report"""
        # Ensure models are trained
        if not self._models_trained:
            self.train_models(session)
        
        return {
            'model_status': {
                'trained': self._models_trained,
                'last_training': self._last_training.isoformat() if self._last_training else None
            },
            'forecasts': {
                'win_rate': self.forecast_win_rate(session),
                'costs': self.forecast_costs(session),
                'rfp_volume': self.forecast_metric(session, 'rfp_count', 7, 'day')
            },
            'model_performance': {
                'processing_time_r_squared': self._processing_time_model.r_squared,
                'match_quality_r_squared': self._match_quality_model.r_squared,
                'win_predictor_classes': list(self._win_classifier.class_priors.keys())
            }
        }


# Fix missing import
from sqlalchemy import Integer
