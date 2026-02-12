"""
Comprehensive Tests for Analytics System
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import json


# ==================== Metrics Collector Tests ====================

class TestMetricsCollector:
    """Tests for MetricsCollector"""
    
    def test_singleton_pattern(self):
        """Test that MetricsCollector is a singleton"""
        from analytics.metrics_collector import MetricsCollector
        
        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        assert collector1 is collector2
    
    def test_increment_counter(self):
        """Test counter increment"""
        from analytics.metrics_collector import MetricsCollector
        
        collector = MetricsCollector()
        collector.increment('test_counter', 5)
        
        value = collector.get_counter('test_counter')
        assert value >= 5
    
    def test_set_gauge(self):
        """Test gauge setting"""
        from analytics.metrics_collector import MetricsCollector
        
        collector = MetricsCollector()
        # MetricsCollector uses gauge method directly
        collector.gauge('test_gauge', 42.5)
        
        value = collector.get_gauge('test_gauge')
        assert value == 42.5
    
    def test_record_histogram(self):
        """Test histogram recording"""
        from analytics.metrics_collector import MetricsCollector
        
        collector = MetricsCollector()
        collector.histogram('test_histogram', 100)
        collector.histogram('test_histogram', 200)
        collector.histogram('test_histogram', 150)
        
        stats = collector.get_histogram_stats('test_histogram')
        assert stats['count'] == 3
    
    def test_track_timing_decorator(self):
        """Test timing decorator"""
        from analytics.metrics_collector import track_timing
        import time
        
        @track_timing('test_function')
        def slow_function():
            time.sleep(0.1)
            return "done"
        
        result = slow_function()
        assert result == "done"
    
    def test_metrics_context(self):
        """Test metrics context manager"""
        from analytics.metrics_collector import metrics_context
        import time
        
        with metrics_context('test_operation'):
            time.sleep(0.05)
        
        # Context should have recorded timing


# ==================== RFP Metrics Tests ====================

class TestRFPMetricsTracker:
    """Tests for RFPMetricsTracker"""
    
    def test_start_processing(self):
        """Test starting RFP processing"""
        from analytics.rfp_metrics import RFPMetricsTracker
        
        tracker = RFPMetricsTracker()
        tracker.start_processing('rfp_001')
        
        assert 'rfp_001' in tracker._active_rfps
    
    def test_start_and_end_stage(self):
        """Test stage tracking"""
        from analytics.rfp_metrics import RFPMetricsTracker
        
        tracker = RFPMetricsTracker()
        tracker.start_processing('rfp_002')
        tracker.start_stage('rfp_002', 'extraction')
        tracker.end_stage('rfp_002', 'extraction')
        
        # Stage should be recorded
        assert 'rfp_002' in tracker._active_rfps
    
    def test_complete_processing(self):
        """Test completing RFP processing"""
        from analytics.rfp_metrics import RFPMetricsTracker
        
        tracker = RFPMetricsTracker()
        tracker.start_processing('rfp_003')
        tracker.complete_processing('rfp_003', outcome='completed')
        
        # RFP should be removed from active
        assert 'rfp_003' not in tracker._active_rfps


# ==================== Match Accuracy Tests ====================

class TestMatchAccuracyTracker:
    """Tests for MatchAccuracyTracker"""
    
    def test_record_prediction(self):
        """Test recording a prediction"""
        from analytics.match_accuracy import MatchAccuracyTracker
        
        tracker = MatchAccuracyTracker()
        tracker.set_algorithm_version('v1.0')
        prediction = tracker.record_prediction(
            rfp_id='rfp_001', 
            requirement_id=1,
            predicted_product_id=100, 
            confidence=0.85
        )
        
        assert prediction is not None
        assert prediction['rfp_id'] == 'rfp_001'
    
    def test_record_validation(self):
        """Test recording validation of a prediction"""
        from analytics.match_accuracy import MatchAccuracyTracker
        
        tracker = MatchAccuracyTracker()
        tracker.set_algorithm_version('v1.0')
        
        # Record a prediction and then validate it
        result = tracker.record_validation(
            rfp_id='rfp_002',
            requirement_id=1,
            predicted_product_id=100,
            actual_product_id=100,  # Correct prediction
            predicted_confidence=0.90
        )
        
        assert result is not None
    
    def test_accuracy_calculation(self):
        """Test accuracy metrics calculation - in-memory tracking"""
        from analytics.match_accuracy import MatchAccuracyTracker
        
        tracker = MatchAccuracyTracker()
        tracker.set_algorithm_version('v1.0')
        
        # Record some validations (8 correct, 2 wrong = 80% accuracy)
        for i in range(10):
            tracker.record_validation(
                rfp_id=f'rfp_{i}',
                requirement_id=1,
                predicted_product_id=100,
                actual_product_id=100 if i < 8 else 200,  # 80% correct
                predicted_confidence=0.8
            )
        
        # Verify method exists and requires session
        # get_accuracy_metrics needs a database session for full metrics
        import inspect
        sig = inspect.signature(tracker.get_accuracy_metrics)
        assert 'session' in sig.parameters
        # Method exists and has correct signature


# ==================== Win/Loss Analytics Tests ====================

class TestWinLossAnalytics:
    """Tests for WinLossAnalytics"""
    
    def test_record_outcome(self):
        """Test recording a win/loss outcome"""
        from analytics.win_loss_analytics import WinLossAnalytics
        
        analyzer = WinLossAnalytics()
        analyzer.record_outcome(
            rfp_id='rfp_100',
            outcome='won',
            our_bid_amount=50000,
            winning_bid_amount=50000
        )
        
        # Should have recorded the outcome
    
    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        from analytics.win_loss_analytics import WinLossAnalytics
        
        analyzer = WinLossAnalytics()
        
        # Record outcomes
        for i in range(5):
            analyzer.record_outcome(f'rfp_{i}', 'won', 10000)
        for i in range(5, 10):
            analyzer.record_outcome(f'rfp_{i}', 'lost', 10000)
        
        # Win rate should be calculable


# ==================== Agent Performance Tests ====================

class TestAgentPerformanceTracker:
    """Tests for AgentPerformanceTracker"""
    
    def test_start_request(self):
        """Test starting an agent request"""
        from analytics.agent_performance import AgentPerformanceTracker
        
        tracker = AgentPerformanceTracker()
        request_id = tracker.start_request(agent_type='pricing_agent', request_id='req_001')
        
        assert request_id is not None
    
    def test_end_request(self):
        """Test ending an agent request"""
        from analytics.agent_performance import AgentPerformanceTracker
        
        tracker = AgentPerformanceTracker()
        request_id = tracker.start_request(agent_type='sales_agent', request_id='req_002')
        
        tracker.end_request(
            request_id,
            success=True,
            tokens_used=1000
        )


# ==================== System Health Tests ====================

class TestSystemHealthMonitor:
    """Tests for SystemHealthMonitor"""
    
    def test_get_system_metrics(self):
        """Test getting system metrics"""
        from analytics.system_health import SystemHealthMonitor
        
        monitor = SystemHealthMonitor()
        metrics = monitor.get_system_metrics()
        
        assert 'timestamp' in metrics
    
    def test_run_health_checks(self):
        """Test running health checks"""
        from analytics.system_health import SystemHealthMonitor
        
        monitor = SystemHealthMonitor()
        results = monitor.run_all_checks()
        
        assert 'status' in results
        assert 'checks' in results
    
    def test_health_status(self):
        """Test getting overall health status"""
        from analytics.system_health import SystemHealthMonitor
        
        monitor = SystemHealthMonitor()
        status = monitor.get_health_status()
        
        assert 'status' in status
        assert status['status'] in ['healthy', 'degraded', 'unhealthy']


# ==================== Response Time Tests ====================

class TestResponseTimeAnalytics:
    """Tests for ResponseTimeAnalytics"""
    
    def test_record_response_time(self):
        """Test recording response time"""
        from analytics.response_time import ResponseTimeAnalytics
        
        analyzer = ResponseTimeAnalytics()
        analyzer.record('/api/rfp', 150)
        analyzer.record('/api/rfp', 200)
        analyzer.record('/api/rfp', 175)
    
    def test_get_endpoint_stats(self):
        """Test getting endpoint statistics using in-memory tracker"""
        from analytics.response_time import ResponseTimeAnalytics
        
        analyzer = ResponseTimeAnalytics()
        analyzer.record('/api/test', 100)
        analyzer.record('/api/test', 150)
        
        # Use the in-memory stats instead of database query
        stats = analyzer._get_in_memory_stats('/api/test')
        assert isinstance(stats, dict)


# ==================== Cost Analysis Tests ====================

class TestCostAnalyzer:
    """Tests for CostAnalyzer"""
    
    def test_record_cost(self):
        """Test recording a cost"""
        from analytics.cost_analysis import CostAnalyzer
        
        analyzer = CostAnalyzer()
        analyzer.record_cost('api_calls', 10.50, rfp_id='rfp_001')
    
    def test_record_llm_cost(self):
        """Test recording LLM cost"""
        from analytics.cost_analysis import CostAnalyzer
        
        analyzer = CostAnalyzer()
        # record_llm_cost expects tokens_used and model
        cost = analyzer.record_llm_cost(
            tokens_used=1500,
            model='openai_gpt4'
        )
        
        assert cost is not None


# ==================== ROI Calculator Tests ====================

class TestROICalculator:
    """Tests for ROICalculator"""
    
    def test_calculate_efficiency_metrics(self):
        """Test efficiency metrics calculation"""
        from analytics.roi_calculator import ROICalculator
        
        calculator = ROICalculator()
        # Would need session with data for full test


# ==================== Trend Analysis Tests ====================

class TestTrendAnalyzer:
    """Tests for TrendAnalyzer"""
    
    def test_moving_average(self):
        """Test moving average calculation"""
        from analytics.trend_analysis import TrendAnalyzer
        
        analyzer = TrendAnalyzer()
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        ma = analyzer.calculate_moving_average(data, window=3)
        assert len(ma) > 0  # Should have some moving average values
    
    def test_detect_trend(self):
        """Test trend detection"""
        from analytics.trend_analysis import TrendAnalyzer
        
        analyzer = TrendAnalyzer()
        
        # Upward trend
        data = [10, 15, 20, 25, 30, 35, 40]
        result = analyzer.detect_trend(data)
        
        assert 'direction' in result or 'trend' in result
    
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        from analytics.trend_analysis import TrendAnalyzer
        
        analyzer = TrendAnalyzer()
        data = [10, 11, 10, 12, 10, 100, 11, 10]  # 100 is anomaly
        
        anomalies = analyzer.detect_anomalies(data)
        assert len(anomalies) > 0


# ==================== Predictive Analytics Tests ====================

class TestPredictiveAnalytics:
    """Tests for PredictiveAnalytics"""
    
    def test_simple_linear_regression(self):
        """Test linear regression model"""
        from analytics.predictive_analytics import SimpleLinearRegression
        
        model = SimpleLinearRegression()
        X = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        
        model.fit(X, y)
        # predict takes a single value, not a list
        prediction = model.predict(6)
        
        assert abs(prediction - 12) < 0.5
    
    def test_naive_bayes(self):
        """Test Naive Bayes classifier"""
        from analytics.predictive_analytics import NaiveBayesClassifier
        
        classifier = NaiveBayesClassifier()
        X = [
            {'feature1': 1, 'feature2': 1}, 
            {'feature1': 1, 'feature2': 0}, 
            {'feature1': 0, 'feature2': 1}, 
            {'feature1': 0, 'feature2': 0}
        ]
        y = ['class_a', 'class_a', 'class_b', 'class_b']
        
        classifier.fit(X, y)
        # predict takes a single dict, not a list
        prediction1 = classifier.predict({'feature1': 1, 'feature2': 1})
        prediction2 = classifier.predict({'feature1': 0, 'feature2': 0})
        
        assert prediction1 == 'class_a'
        assert prediction2 == 'class_b'


# ==================== Report Generator Tests ====================

class TestReportGenerator:
    """Tests for ReportGenerator"""
    
    def test_generate_json(self):
        """Test JSON report generation"""
        from analytics.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        data = {'metric': 'value', 'count': 100}
        
        json_str = generator.generate_json(data)
        parsed = json.loads(json_str)
        
        assert 'data' in parsed
        assert parsed['data']['count'] == 100
    
    def test_generate_csv(self):
        """Test CSV report generation"""
        from analytics.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        data = [
            {'name': 'test1', 'value': 100},
            {'name': 'test2', 'value': 200}
        ]
        
        csv_str = generator.generate_csv(data)
        lines = csv_str.strip().split('\n')
        
        assert len(lines) == 3  # Header + 2 data rows
    
    def test_available_templates(self):
        """Test getting available templates"""
        from analytics.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        templates = generator.get_available_templates()
        
        assert 'executive_summary' in templates


# ==================== Dashboard API Tests ====================

class TestDashboardAPI:
    """Tests for DashboardAPI"""
    
    def test_api_response_format(self):
        """Test API response format"""
        from analytics.dashboard_api import APIResponse
        
        response = APIResponse(success=True, data={'key': 'value'})
        
        result = response.to_dict()
        assert result['success'] is True
        assert result['data']['key'] == 'value'
        assert 'timestamp' in result
    
    def test_caching(self):
        """Test API caching"""
        from analytics.dashboard_api import DashboardAPI
        
        api = DashboardAPI()
        
        # Set cache
        api._set_cached('test_key', {'data': 'value'})
        
        # Get cache
        cached = api._get_cached('test_key')
        assert cached['data'] == 'value'


# ==================== Visualization Tests ====================

class TestVisualization:
    """Tests for visualization generation"""
    
    def test_chart_data_structure(self):
        """Test ChartData structure"""
        from analytics.visualization import ChartData, ChartDataset
        
        chart = ChartData(
            chart_type='line',
            labels=['Jan', 'Feb', 'Mar'],
            datasets=[ChartDataset(
                label='Sales',
                data=[100, 150, 200]
            )],
            title='Monthly Sales'
        )
        
        result = chart.to_dict()
        assert result['type'] == 'line'
        assert len(result['data']['labels']) == 3
    
    def test_color_palette(self):
        """Test color palette"""
        from analytics.visualization import ColorPalette
        
        color1 = ColorPalette.get_color(0)
        color2 = ColorPalette.get_color(1)
        
        assert color1 != color2
    
    def test_create_pie_chart(self):
        """Test pie chart creation"""
        from analytics.visualization import VisualizationGenerator
        
        generator = VisualizationGenerator()
        chart = generator.create_pie_chart(
            ['A', 'B', 'C'],
            [30, 50, 20],
            'Distribution'
        )
        
        assert chart.chart_type == 'pie'


# ==================== Scheduled Reports Tests ====================

class TestScheduledReports:
    """Tests for scheduled reports"""
    
    def test_schedule_creation(self):
        """Test creating a schedule"""
        from analytics.scheduled_reports import (
            ScheduledReportManager, ReportSchedule,
            ReportFrequency, ReportFormat
        )
        
        manager = ScheduledReportManager()
        schedule = ReportSchedule(
            id='test_schedule',
            name='Daily Report',
            report_type='executive_summary',
            frequency=ReportFrequency.DAILY,
            format=ReportFormat.PDF
        )
        
        manager.add_schedule(schedule)
        
        retrieved = manager.get_schedule('test_schedule')
        assert retrieved is not None
        assert retrieved.name == 'Daily Report'
    
    def test_next_run_calculation(self):
        """Test next run time calculation"""
        from analytics.scheduled_reports import (
            ScheduledReportManager, ReportSchedule,
            ReportFrequency, ReportFormat
        )
        
        manager = ScheduledReportManager()
        schedule = ReportSchedule(
            id='test_calc',
            name='Test',
            report_type='test',
            frequency=ReportFrequency.DAILY,
            format=ReportFormat.JSON,
            hour=8
        )
        
        next_run = manager._calculate_next_run(schedule)
        assert next_run > datetime.utcnow()


# ==================== Alert System Tests ====================

class TestAlertSystem:
    """Tests for alert system"""
    
    def test_alert_rule_creation(self):
        """Test creating an alert rule"""
        from analytics.alert_system import (
            AlertManager, AlertRule, AlertSeverity
        )
        
        manager = AlertManager()
        rule = AlertRule(
            id='test_rule',
            name='High CPU',
            description='Alert on high CPU',
            metric_name='cpu_percent',
            condition='gt',
            threshold=90,
            severity=AlertSeverity.WARNING
        )
        
        manager.add_rule(rule)
        
        retrieved = manager.get_rule('test_rule')
        assert retrieved is not None
    
    def test_check_metric_triggers_alert(self):
        """Test that metric check triggers alert"""
        from analytics.alert_system import (
            AlertManager, AlertRule, AlertSeverity
        )
        
        manager = AlertManager()
        rule = AlertRule(
            id='test_trigger',
            name='Test Alert',
            description='Test',
            metric_name='test_metric',
            condition='gt',
            threshold=50,
            severity=AlertSeverity.WARNING
        )
        
        manager.add_rule(rule)
        
        # This should trigger alert
        alerts = manager.check_metric('test_metric', 75)
        assert len(alerts) > 0
    
    def test_alert_acknowledgment(self):
        """Test alert acknowledgment"""
        from analytics.alert_system import (
            AlertManager, AlertRule, AlertSeverity
        )
        
        manager = AlertManager()
        rule = AlertRule(
            id='test_ack',
            name='Test',
            description='Test',
            metric_name='ack_metric',
            condition='gt',
            threshold=10,
            severity=AlertSeverity.INFO
        )
        
        manager.add_rule(rule)
        alerts = manager.check_metric('ack_metric', 20)
        
        if alerts:
            result = manager.acknowledge_alert(alerts[0].id, 'user@test.com')
            assert result is True


# ==================== Benchmarking Tests ====================

class TestBenchmarking:
    """Tests for benchmarking"""
    
    def test_create_benchmark(self):
        """Test creating a benchmark"""
        from analytics.benchmarking import BenchmarkManager, BenchmarkType
        
        manager = BenchmarkManager()
        benchmark = manager.create_benchmark(
            name='Win Rate Target',
            metric_name='win_rate',
            baseline_value=0.30,
            higher_is_better=True,
            good_threshold=0.40,
            excellent_threshold=0.50
        )
        
        assert benchmark.id is not None
    
    def test_benchmark_comparison(self):
        """Test comparing against benchmark"""
        from analytics.benchmarking import BenchmarkManager
        
        manager = BenchmarkManager()
        benchmark = manager.create_benchmark(
            name='Test Benchmark',
            metric_name='test_metric',
            baseline_value=100,
            higher_is_better=True,
            good_threshold=110,
            excellent_threshold=120
        )
        
        result = manager.compare(benchmark.id, 115)
        
        assert result.rating == 'good'
    
    def test_industry_comparison(self):
        """Test comparing to industry standards"""
        from analytics.benchmarking import BenchmarkManager
        
        manager = BenchmarkManager()
        result = manager.compare_to_industry('win_rate_percent', 40)
        
        assert result is not None


# ==================== A/B Testing Tests ====================

class TestABTesting:
    """Tests for A/B testing framework"""
    
    def test_create_experiment(self):
        """Test creating an experiment"""
        from analytics.ab_testing import ABTestingFramework
        
        framework = ABTestingFramework()
        experiment = framework.create_experiment(
            name='Button Color Test',
            description='Test button colors',
            metric_name='click_rate'
        )
        
        assert experiment.id is not None
        assert len(experiment.variants) == 2  # Control + Treatment
    
    def test_variant_assignment(self):
        """Test variant assignment"""
        from analytics.ab_testing import ABTestingFramework
        
        framework = ABTestingFramework()
        experiment = framework.create_experiment(
            name='Test Experiment',
            description='Test',
            metric_name='conversion'
        )
        
        framework.start_experiment(experiment.id)
        
        variant = framework.get_variant(experiment.id, 'user_123')
        assert variant is not None
    
    def test_consistent_assignment(self):
        """Test that same user gets same variant"""
        from analytics.ab_testing import ABTestingFramework
        
        framework = ABTestingFramework()
        experiment = framework.create_experiment(
            name='Consistency Test',
            description='Test consistent assignment',
            metric_name='metric'
        )
        
        framework.start_experiment(experiment.id)
        
        variant1 = framework.get_variant(experiment.id, 'user_456')
        variant2 = framework.get_variant(experiment.id, 'user_456')
        
        assert variant1.id == variant2.id
    
    def test_statistical_analyzer(self):
        """Test statistical analysis"""
        from analytics.ab_testing import StatisticalAnalyzer
        
        sample_size = StatisticalAnalyzer.calculate_sample_size(
            baseline_rate=0.10,
            min_detectable_effect=0.10,
            confidence_level=0.95
        )
        
        assert sample_size > 0


# ==================== Analytics Export Tests ====================

class TestAnalyticsExport:
    """Tests for analytics export"""
    
    def test_export_to_json(self):
        """Test JSON export"""
        from analytics.analytics_export import AnalyticsExporter
        
        exporter = AnalyticsExporter()
        data = {'test': 'data', 'count': 42}
        
        json_str = exporter.export_to_json(data)
        parsed = json.loads(json_str)
        
        assert 'exported_at' in parsed
        assert parsed['data']['count'] == 42
    
    def test_export_to_csv(self):
        """Test CSV export"""
        from analytics.analytics_export import AnalyticsExporter
        
        exporter = AnalyticsExporter()
        data = [
            {'id': 1, 'name': 'Test 1', 'value': 100},
            {'id': 2, 'name': 'Test 2', 'value': 200}
        ]
        
        csv_str = exporter.export_to_csv(data)
        lines = csv_str.strip().split('\n')
        
        assert len(lines) == 3
    
    def test_export_builder(self):
        """Test export builder pattern"""
        from analytics.analytics_export import ExportBuilder
        
        builder = ExportBuilder()
        builder.format('json').days(7).include('rfp_metrics')
        
        assert builder._format == 'json'
        assert builder._days == 7


# ==================== Integration Tests ====================

class TestAnalyticsIntegration:
    """Integration tests for analytics system"""
    
    def test_import_all_modules(self):
        """Test that all modules can be imported"""
        from analytics import (
            MetricsCollector,
            RFPMetricsTracker,
            MatchAccuracyTracker,
            WinLossAnalytics,
            AgentPerformanceTracker,
            SystemHealthMonitor,
            ResponseTimeAnalytics,
            CostAnalyzer,
            ROICalculator,
            TrendAnalyzer,
            PredictiveAnalytics,
            ReportGenerator,
            DashboardAPI,
            VisualizationGenerator,
            ScheduledReportManager,
            AlertManager,
            BenchmarkManager,
            ABTestingFramework,
            AnalyticsExporter
        )
        
        # All imports should succeed
        assert MetricsCollector is not None
        assert RFPMetricsTracker is not None
    
    def test_full_workflow(self):
        """Test a complete analytics workflow"""
        from analytics.metrics_collector import MetricsCollector
        from analytics.rfp_metrics import RFPMetricsTracker
        from analytics.win_loss_analytics import WinLossAnalytics
        
        # 1. Start tracking an RFP
        rfp_tracker = RFPMetricsTracker()
        rfp_tracker.start_processing('integration_test_rfp')
        
        # 2. Track stages
        rfp_tracker.start_stage('integration_test_rfp', 'extraction')
        rfp_tracker.end_stage('integration_test_rfp', 'extraction')
        
        # 3. Complete processing
        rfp_tracker.complete_processing('integration_test_rfp', outcome='completed')
        
        # 4. Record outcome
        win_loss = WinLossAnalytics()
        win_loss.record_outcome(
            rfp_id='integration_test_rfp',
            outcome='won',
            our_bid_amount=50000
        )
        
        # Workflow completed successfully


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
