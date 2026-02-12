"""
Comprehensive Analytics System for RFP Processing

This module provides complete analytics capabilities for:
- RFP processing metrics
- Match accuracy tracking
- Win/loss analytics
- Agent performance monitoring
- System health monitoring
- Response time analytics
- Cost and ROI analysis
- Trend and predictive analytics
- Dashboard data APIs
- Report generation
- Alert and benchmarking systems
- A/B testing framework
"""

from .models import (
    # Core metrics models
    RFPMetric, MatchAccuracyMetric, WinLossRecord, AgentPerformanceMetric,
    SystemHealthMetric, ResponseTimeMetric, CostRecord, ABTestExperiment,
    ABTestVariant, ABTestResult, Benchmark, Alert, ScheduledReport,
    AnalyticsSnapshot
)

from .metrics_collector import (
    MetricsCollector, track_metric, track_timing, metrics_context
)

from .rfp_metrics import RFPMetricsTracker
from .match_accuracy import MatchAccuracyTracker
from .win_loss_analytics import WinLossAnalytics
from .agent_performance import AgentPerformanceTracker
from .system_health import SystemHealthMonitor
from .response_time import ResponseTimeAnalytics
from .cost_analysis import CostAnalyzer
from .roi_calculator import ROICalculator
from .trend_analysis import TrendAnalyzer
from .predictive_analytics import PredictiveAnalytics
from .report_generator import ReportGenerator
from .dashboard_api import DashboardAPI, APIResponse
from .visualization import VisualizationGenerator, ChartData, ColorPalette
from .scheduled_reports import ScheduledReportManager, ReportSchedule
from .alert_system import AlertManager, AlertRule, Alert
from .benchmarking import BenchmarkManager, Benchmark
from .ab_testing import ABTestingFramework, Experiment
from .analytics_export import AnalyticsExporter, ExportBuilder

__all__ = [
    # Models
    'RFPMetric', 'MatchAccuracyMetric', 'WinLossRecord', 'AgentPerformanceMetric',
    'SystemHealthMetric', 'ResponseTimeMetric', 'CostRecord', 'ABTestExperiment',
    'ABTestVariant', 'ABTestResult', 'Benchmark', 'Alert', 'ScheduledReport',
    'AnalyticsSnapshot',
    
    # Core
    'MetricsCollector', 'track_metric', 'track_timing', 'metrics_context',
    
    # Trackers
    'RFPMetricsTracker', 'MatchAccuracyTracker', 'WinLossAnalytics',
    'AgentPerformanceTracker', 'SystemHealthMonitor', 'ResponseTimeAnalytics',
    
    # Analysis
    'CostAnalyzer', 'ROICalculator', 'TrendAnalyzer', 'PredictiveAnalytics',
    
    # Reporting
    'ReportGenerator', 'ScheduledReportManager', 'ReportSchedule',
    'VisualizationGenerator', 'ChartData', 'ColorPalette',
    
    # API
    'DashboardAPI', 'APIResponse',
    
    # Systems
    'AlertManager', 'AlertRule', 'Alert',
    'BenchmarkManager', 'Benchmark',
    'ABTestingFramework', 'Experiment',
    'AnalyticsExporter', 'ExportBuilder'
]
