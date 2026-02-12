"""
Dashboard API
REST API endpoints for analytics dashboard data consumption

Features:
- Real-time metrics endpoints
- Historical data queries
- Aggregated statistics
- Chart data generation
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from functools import wraps
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standard API response format"""
    success: bool
    data: Any = None
    error: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


def api_error_handler(func):
    """Decorator for consistent error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return APIResponse(success=True, data=result)
        except Exception as e:
            logger.exception(f"API error in {func.__name__}")
            return APIResponse(success=False, error=str(e))
    return wrapper


class DashboardAPI:
    """
    Dashboard API providing endpoints for analytics data
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self._cache = {}
        self._cache_ttl = 60  # seconds
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.utcnow() - timestamp).total_seconds() < self._cache_ttl:
                return data
        return None
    
    def _set_cached(self, key: str, data: Any):
        """Cache data with timestamp"""
        self._cache[key] = (data, datetime.utcnow())
    
    # ==================== Overview Endpoints ====================
    
    @api_error_handler
    def get_dashboard_overview(self, session, days: int = 30) -> Dict[str, Any]:
        """Get high-level dashboard overview data"""
        from .rfp_metrics import RFPMetricsTracker
        from .win_loss_analytics import WinLossAnalytics
        from .cost_analysis import CostAnalyzer
        from .system_health import SystemHealthMonitor
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        rfp_tracker = RFPMetricsTracker()
        win_loss = WinLossAnalytics()
        cost_analyzer = CostAnalyzer()
        health_monitor = SystemHealthMonitor()
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'rfp_stats': rfp_tracker.get_performance_summary(session, days),
            'win_rate': win_loss.get_overall_win_rate(session, start_date, end_date),
            'costs': cost_analyzer.get_total_costs(session, start_date, end_date),
            'system_health': health_monitor.get_health_status()
        }
    
    @api_error_handler
    def get_key_metrics(self, session, days: int = 7) -> Dict[str, Any]:
        """Get key performance metrics for dashboard cards"""
        from .models import RFPMetric, WinLossRecord, CostRecord
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # RFP count
        rfp_count = session.query(RFPMetric).filter(
            RFPMetric.timestamp >= start_date
        ).count()
        
        # Win rate
        wins = session.query(WinLossRecord).filter(
            WinLossRecord.outcome_date >= start_date,
            WinLossRecord.outcome == 'won'
        ).count()
        
        total_outcomes = session.query(WinLossRecord).filter(
            WinLossRecord.outcome_date >= start_date
        ).count()
        
        win_rate = (wins / total_outcomes * 100) if total_outcomes > 0 else 0
        
        # Total costs
        from sqlalchemy import func
        total_cost = session.query(
            func.sum(CostRecord.amount)
        ).filter(
            CostRecord.timestamp >= start_date
        ).scalar() or 0
        
        # Calculate trends (compare to previous period)
        prev_start = start_date - timedelta(days=days)
        prev_rfp_count = session.query(RFPMetric).filter(
            RFPMetric.timestamp >= prev_start,
            RFPMetric.timestamp < start_date
        ).count()
        
        rfp_trend = ((rfp_count - prev_rfp_count) / prev_rfp_count * 100) if prev_rfp_count > 0 else 0
        
        return {
            'rfp_count': {
                'value': rfp_count,
                'trend': rfp_trend,
                'trend_direction': 'up' if rfp_trend > 0 else 'down' if rfp_trend < 0 else 'flat'
            },
            'win_rate': {
                'value': round(win_rate, 1),
                'unit': '%'
            },
            'total_cost': {
                'value': round(total_cost, 2),
                'unit': 'USD'
            },
            'total_outcomes': total_outcomes
        }
    
    # ==================== RFP Endpoints ====================
    
    @api_error_handler
    def get_rfp_metrics(self, session, days: int = 30) -> Dict[str, Any]:
        """Get RFP processing metrics"""
        from .rfp_metrics import RFPMetricsTracker
        
        tracker = RFPMetricsTracker()
        return {
            'summary': tracker.get_performance_summary(session, days),
            'time_series': tracker.get_time_series(session, days, 'day')
        }
    
    @api_error_handler
    def get_rfp_processing_times(self, session, days: int = 30) -> Dict[str, Any]:
        """Get RFP processing time breakdown"""
        from .models import RFPMetric
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            RFPMetric.stage,
            func.avg(RFPMetric.duration_seconds).label('avg_duration'),
            func.min(RFPMetric.duration_seconds).label('min_duration'),
            func.max(RFPMetric.duration_seconds).label('max_duration'),
            func.count(RFPMetric.id).label('count')
        ).filter(
            RFPMetric.timestamp >= start_date,
            RFPMetric.duration_seconds.isnot(None)
        ).group_by(RFPMetric.stage).all()
        
        return {
            'stages': [
                {
                    'stage': r.stage,
                    'avg_duration': round(r.avg_duration, 2),
                    'min_duration': round(r.min_duration, 2),
                    'max_duration': round(r.max_duration, 2),
                    'count': r.count
                }
                for r in results
            ]
        }
    
    # ==================== Win/Loss Endpoints ====================
    
    @api_error_handler
    def get_win_loss_metrics(self, session, days: int = 30) -> Dict[str, Any]:
        """Get win/loss analytics"""
        from .win_loss_analytics import WinLossAnalytics
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analyzer = WinLossAnalytics()
        
        return {
            'overall': analyzer.get_overall_win_rate(session, start_date, end_date),
            'by_industry': analyzer.get_win_rate_by_dimension(session, 'industry', start_date, end_date),
            'by_size': analyzer.get_win_rate_by_dimension(session, 'rfp_size', start_date, end_date),
            'success_factors': analyzer.get_success_factors(session, start_date, end_date)
        }
    
    @api_error_handler
    def get_competitor_analysis(self, session, days: int = 90) -> Dict[str, Any]:
        """Get competitor analysis data"""
        from .win_loss_analytics import WinLossAnalytics
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analyzer = WinLossAnalytics()
        return analyzer.get_competitor_analysis(session, start_date, end_date)
    
    # ==================== Agent Performance Endpoints ====================
    
    @api_error_handler
    def get_agent_metrics(self, session, days: int = 7) -> Dict[str, Any]:
        """Get agent performance metrics"""
        from .agent_performance import AgentPerformanceTracker
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        tracker = AgentPerformanceTracker()
        return {
            'comparison': tracker.get_all_agents_comparison(session, start_date, end_date),
            'token_usage': tracker.get_token_usage_analysis(session, start_date, end_date)
        }
    
    @api_error_handler
    def get_agent_details(self, session, agent_type: str, days: int = 7) -> Dict[str, Any]:
        """Get detailed metrics for a specific agent"""
        from .agent_performance import AgentPerformanceTracker
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        tracker = AgentPerformanceTracker()
        return tracker.get_agent_summary(session, agent_type, start_date, end_date)
    
    # ==================== Cost Endpoints ====================
    
    @api_error_handler
    def get_cost_metrics(self, session, days: int = 30) -> Dict[str, Any]:
        """Get cost analysis metrics"""
        from .cost_analysis import CostAnalyzer
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analyzer = CostAnalyzer()
        
        return {
            'total': analyzer.get_total_costs(session, start_date, end_date),
            'by_category': analyzer.get_costs_by_category(session, start_date, end_date),
            'cost_per_rfp': analyzer.get_cost_per_rfp(session, start_date, end_date),
            'recommendations': analyzer.get_optimization_recommendations(session, start_date, end_date)
        }
    
    @api_error_handler
    def get_budget_status(self, session, budget: float, days: int = 30) -> Dict[str, Any]:
        """Get budget utilization status"""
        from .cost_analysis import CostAnalyzer
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analyzer = CostAnalyzer()
        return analyzer.get_budget_status(session, budget, start_date, end_date)
    
    # ==================== System Health Endpoints ====================
    
    @api_error_handler
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        cache_key = 'system_health'
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        from .system_health import SystemHealthMonitor
        
        monitor = SystemHealthMonitor()
        health_data = {
            'status': monitor.get_health_status(),
            'metrics': monitor.get_system_metrics(),
            'checks': monitor.run_all_checks()
        }
        
        self._set_cached(cache_key, health_data)
        return health_data
    
    @api_error_handler
    def get_response_times(self, session, days: int = 7) -> Dict[str, Any]:
        """Get response time analytics"""
        from .response_time import ResponseTimeAnalyzer
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analyzer = ResponseTimeAnalyzer()
        return {
            'endpoints': analyzer.get_all_endpoints_summary(session, start_date, end_date),
            'sla': analyzer.get_sla_compliance(session, start_date, end_date)
        }
    
    # ==================== Trend Endpoints ====================
    
    @api_error_handler
    def get_metric_trends(self, session, metric_name: str, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis for a specific metric"""
        from .trend_analysis import TrendAnalyzer
        
        analyzer = TrendAnalyzer()
        return analyzer.get_metric_trend(session, metric_name, days)
    
    @api_error_handler
    def get_predictions(self, session, days: int = 30) -> Dict[str, Any]:
        """Get predictive analytics data"""
        from .predictive_analytics import PredictiveAnalytics
        
        analytics = PredictiveAnalytics()
        analytics.train_models(session, days)
        
        return {
            'forecast': analytics.forecast_metric(session, 'rfp_count', 7),
            'model_accuracy': {
                'win_prediction': 0.75,  # Placeholder
                'time_prediction': 0.80
            }
        }
    
    # ==================== Chart Data Endpoints ====================
    
    @api_error_handler
    def get_rfp_timeline_chart(self, session, days: int = 30) -> Dict[str, Any]:
        """Get data for RFP timeline chart"""
        from .models import RFPMetric
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            func.date(RFPMetric.timestamp).label('date'),
            func.count(RFPMetric.id).label('count')
        ).filter(
            RFPMetric.timestamp >= start_date
        ).group_by(func.date(RFPMetric.timestamp)).order_by('date').all()
        
        return {
            'chart_type': 'line',
            'labels': [str(r.date) for r in results],
            'datasets': [{
                'label': 'RFPs Processed',
                'data': [r.count for r in results]
            }]
        }
    
    @api_error_handler
    def get_win_rate_chart(self, session, days: int = 30) -> Dict[str, Any]:
        """Get data for win rate pie chart"""
        from .models import WinLossRecord
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            WinLossRecord.outcome,
            func.count(WinLossRecord.id).label('count')
        ).filter(
            WinLossRecord.outcome_date >= start_date
        ).group_by(WinLossRecord.outcome).all()
        
        return {
            'chart_type': 'pie',
            'labels': [r.outcome.capitalize() for r in results],
            'data': [r.count for r in results]
        }
    
    @api_error_handler
    def get_cost_breakdown_chart(self, session, days: int = 30) -> Dict[str, Any]:
        """Get data for cost breakdown chart"""
        from .models import CostRecord
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            CostRecord.category,
            func.sum(CostRecord.amount).label('total')
        ).filter(
            CostRecord.timestamp >= start_date
        ).group_by(CostRecord.category).all()
        
        return {
            'chart_type': 'bar',
            'labels': [r.category for r in results],
            'datasets': [{
                'label': 'Cost (USD)',
                'data': [float(r.total) for r in results]
            }]
        }
    
    # ==================== ROI Endpoints ====================
    
    @api_error_handler
    def get_roi_metrics(self, session, days: int = 90) -> Dict[str, Any]:
        """Get ROI calculations"""
        from .roi_calculator import ROICalculator
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        calculator = ROICalculator()
        return {
            'roi': calculator.calculate_roi(session, start_date, end_date),
            'efficiency': calculator.calculate_efficiency_metrics(session, start_date, end_date),
            'cost_per_win': calculator.calculate_cost_per_win(session, start_date, end_date)
        }
    
    @api_error_handler
    def get_what_if_analysis(self, session, win_rate_change: float = None,
                            cost_reduction: float = None, days: int = 90) -> Dict[str, Any]:
        """Get what-if scenario analysis"""
        from .roi_calculator import ROICalculator
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        calculator = ROICalculator()
        
        results = {}
        if win_rate_change is not None:
            results['win_rate_scenario'] = calculator.what_if_win_rate_change(
                session, win_rate_change, start_date, end_date
            )
        if cost_reduction is not None:
            results['cost_reduction_scenario'] = calculator.what_if_cost_reduction(
                session, cost_reduction, start_date, end_date
            )
        
        return results
    
    # ==================== Export Endpoints ====================
    
    @api_error_handler
    def export_data(self, session, data_type: str, format: str = 'json',
                   days: int = 30) -> Dict[str, Any]:
        """Export analytics data in specified format"""
        from .report_generator import ReportGenerator
        
        generator = ReportGenerator(self.session_factory)
        
        # Collect data based on type
        if data_type == 'overview':
            data = self.get_dashboard_overview(session, days)
        elif data_type == 'rfp':
            data = self.get_rfp_metrics(session, days)
        elif data_type == 'win_loss':
            data = self.get_win_loss_metrics(session, days)
        elif data_type == 'costs':
            data = self.get_cost_metrics(session, days)
        else:
            data = {'error': f'Unknown data type: {data_type}'}
        
        # Get the data from the APIResponse if it's a success
        if isinstance(data, APIResponse) and data.success:
            data = data.data
        
        if format == 'json':
            return {'content': generator.generate_json(data), 'content_type': 'application/json'}
        elif format == 'csv' and isinstance(data, list):
            return {'content': generator.generate_csv(data), 'content_type': 'text/csv'}
        else:
            return {'error': f'Unsupported format: {format}'}


# Flask/FastAPI integration helpers
def register_flask_routes(app, dashboard_api: DashboardAPI, session_factory):
    """Register Flask routes for the dashboard API"""
    from flask import jsonify, request
    
    @app.route('/api/dashboard/overview')
    def dashboard_overview():
        days = request.args.get('days', 30, type=int)
        with session_factory() as session:
            response = dashboard_api.get_dashboard_overview(session, days)
            return jsonify(response.to_dict())
    
    @app.route('/api/dashboard/key-metrics')
    def key_metrics():
        days = request.args.get('days', 7, type=int)
        with session_factory() as session:
            response = dashboard_api.get_key_metrics(session, days)
            return jsonify(response.to_dict())
    
    @app.route('/api/dashboard/health')
    def system_health():
        response = dashboard_api.get_system_health()
        return jsonify(response.to_dict())
    
    # Add more routes as needed


def create_fastapi_router(dashboard_api: DashboardAPI, session_factory):
    """Create FastAPI router for the dashboard API"""
    from fastapi import APIRouter, Query, Depends
    
    router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
    
    @router.get("/overview")
    async def dashboard_overview(days: int = Query(30, ge=1, le=365)):
        with session_factory() as session:
            response = dashboard_api.get_dashboard_overview(session, days)
            return response.to_dict()
    
    @router.get("/key-metrics")
    async def key_metrics(days: int = Query(7, ge=1, le=90)):
        with session_factory() as session:
            response = dashboard_api.get_key_metrics(session, days)
            return response.to_dict()
    
    @router.get("/health")
    async def system_health():
        response = dashboard_api.get_system_health()
        return response.to_dict()
    
    return router
