"""
Data Visualization
Chart data generation and visualization support

Features:
- Multiple chart types (line, bar, pie, area, scatter)
- Time series visualization
- Comparative charts
- Dashboard-ready data formats
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChartDataset:
    """Dataset for chart visualization"""
    label: str
    data: List[float]
    backgroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    fill: bool = False
    tension: float = 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'label': self.label,
            'data': self.data,
            'fill': self.fill,
            'tension': self.tension
        }
        if self.backgroundColor:
            result['backgroundColor'] = self.backgroundColor
        if self.borderColor:
            result['borderColor'] = self.borderColor
        return result


@dataclass
class ChartData:
    """Complete chart data structure (Chart.js compatible)"""
    chart_type: str
    labels: List[str]
    datasets: List[ChartDataset] = field(default_factory=list)
    title: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.chart_type,
            'data': {
                'labels': self.labels,
                'datasets': [ds.to_dict() for ds in self.datasets]
            },
            'options': self.options,
            'title': self.title
        }


class ColorPalette:
    """Color palette for charts"""
    
    # Primary colors
    PRIMARY = [
        'rgba(54, 162, 235, 1)',   # Blue
        'rgba(255, 99, 132, 1)',   # Red
        'rgba(75, 192, 192, 1)',   # Teal
        'rgba(255, 206, 86, 1)',   # Yellow
        'rgba(153, 102, 255, 1)', # Purple
        'rgba(255, 159, 64, 1)',  # Orange
        'rgba(199, 199, 199, 1)', # Gray
        'rgba(83, 102, 255, 1)',  # Indigo
    ]
    
    # Transparent versions for fills
    PRIMARY_LIGHT = [
        'rgba(54, 162, 235, 0.2)',
        'rgba(255, 99, 132, 0.2)',
        'rgba(75, 192, 192, 0.2)',
        'rgba(255, 206, 86, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(255, 159, 64, 0.2)',
        'rgba(199, 199, 199, 0.2)',
        'rgba(83, 102, 255, 0.2)',
    ]
    
    # Status colors
    SUCCESS = 'rgba(40, 167, 69, 1)'
    WARNING = 'rgba(255, 193, 7, 1)'
    DANGER = 'rgba(220, 53, 69, 1)'
    INFO = 'rgba(23, 162, 184, 1)'
    
    @classmethod
    def get_color(cls, index: int, light: bool = False) -> str:
        """Get color by index"""
        colors = cls.PRIMARY_LIGHT if light else cls.PRIMARY
        return colors[index % len(colors)]
    
    @classmethod
    def get_gradient_pair(cls, index: int) -> Tuple[str, str]:
        """Get border and fill color pair"""
        return cls.PRIMARY[index % len(cls.PRIMARY)], cls.PRIMARY_LIGHT[index % len(cls.PRIMARY_LIGHT)]


class VisualizationGenerator:
    """
    Generates visualization data for analytics dashboards
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
    
    # ==================== Time Series Charts ====================
    
    def create_time_series_chart(self, data: List[Dict[str, Any]],
                                 x_field: str, y_fields: List[str],
                                 title: str = None,
                                 chart_type: str = 'line') -> ChartData:
        """Create a time series chart from data"""
        labels = [str(item.get(x_field, '')) for item in data]
        
        datasets = []
        for i, y_field in enumerate(y_fields):
            border_color, bg_color = ColorPalette.get_gradient_pair(i)
            datasets.append(ChartDataset(
                label=y_field.replace('_', ' ').title(),
                data=[item.get(y_field, 0) for item in data],
                borderColor=border_color,
                backgroundColor=bg_color,
                fill=chart_type == 'area'
            ))
        
        return ChartData(
            chart_type='line' if chart_type == 'area' else chart_type,
            labels=labels,
            datasets=datasets,
            title=title,
            options={
                'responsive': True,
                'maintainAspectRatio': False,
                'scales': {
                    'x': {'display': True, 'title': {'display': True, 'text': x_field.title()}},
                    'y': {'display': True, 'title': {'display': True, 'text': 'Value'}}
                }
            }
        )
    
    def get_rfp_volume_chart(self, session, days: int = 30) -> ChartData:
        """Get RFP volume over time chart"""
        from .models import RFPMetric
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            func.date(RFPMetric.timestamp).label('date'),
            func.count(RFPMetric.id).label('count')
        ).filter(
            RFPMetric.timestamp >= start_date
        ).group_by(func.date(RFPMetric.timestamp)).order_by('date').all()
        
        labels = [str(r.date) for r in results]
        data = [r.count for r in results]
        
        return ChartData(
            chart_type='line',
            labels=labels,
            datasets=[ChartDataset(
                label='RFPs Processed',
                data=data,
                borderColor=ColorPalette.PRIMARY[0],
                backgroundColor=ColorPalette.PRIMARY_LIGHT[0],
                fill=True
            )],
            title='RFP Volume Over Time',
            options={
                'responsive': True,
                'plugins': {'legend': {'display': True}},
                'scales': {
                    'y': {'beginAtZero': True}
                }
            }
        )
    
    # ==================== Distribution Charts ====================
    
    def create_pie_chart(self, labels: List[str], values: List[float],
                        title: str = None) -> ChartData:
        """Create a pie chart"""
        colors = [ColorPalette.get_color(i) for i in range(len(labels))]
        
        return ChartData(
            chart_type='pie',
            labels=labels,
            datasets=[ChartDataset(
                label='Distribution',
                data=values,
                backgroundColor=colors
            )],
            title=title,
            options={
                'responsive': True,
                'plugins': {
                    'legend': {'position': 'right'}
                }
            }
        )
    
    def create_doughnut_chart(self, labels: List[str], values: List[float],
                             title: str = None) -> ChartData:
        """Create a doughnut chart"""
        chart = self.create_pie_chart(labels, values, title)
        chart.chart_type = 'doughnut'
        chart.options['cutout'] = '60%'
        return chart
    
    def get_win_loss_pie_chart(self, session, days: int = 30) -> ChartData:
        """Get win/loss distribution pie chart"""
        from .models import WinLossRecord
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            WinLossRecord.outcome,
            func.count(WinLossRecord.id).label('count')
        ).filter(
            WinLossRecord.outcome_date >= start_date
        ).group_by(WinLossRecord.outcome).all()
        
        labels = [r.outcome.title() for r in results]
        values = [r.count for r in results]
        
        # Use status colors for win/loss
        colors = []
        for label in labels:
            if label.lower() == 'won':
                colors.append(ColorPalette.SUCCESS)
            elif label.lower() == 'lost':
                colors.append(ColorPalette.DANGER)
            else:
                colors.append(ColorPalette.WARNING)
        
        return ChartData(
            chart_type='doughnut',
            labels=labels,
            datasets=[ChartDataset(
                label='Outcomes',
                data=values,
                backgroundColor=colors
            )],
            title='Win/Loss Distribution',
            options={
                'responsive': True,
                'cutout': '60%',
                'plugins': {
                    'legend': {'position': 'bottom'}
                }
            }
        )
    
    # ==================== Bar Charts ====================
    
    def create_bar_chart(self, labels: List[str], 
                        datasets: List[Tuple[str, List[float]]],
                        title: str = None,
                        horizontal: bool = False,
                        stacked: bool = False) -> ChartData:
        """Create a bar chart"""
        chart_datasets = []
        for i, (name, data) in enumerate(datasets):
            chart_datasets.append(ChartDataset(
                label=name,
                data=data,
                backgroundColor=ColorPalette.get_color(i, light=True),
                borderColor=ColorPalette.get_color(i)
            ))
        
        options = {
            'responsive': True,
            'indexAxis': 'y' if horizontal else 'x',
            'plugins': {'legend': {'display': len(datasets) > 1}}
        }
        
        if stacked:
            options['scales'] = {
                'x': {'stacked': True},
                'y': {'stacked': True}
            }
        
        return ChartData(
            chart_type='bar',
            labels=labels,
            datasets=chart_datasets,
            title=title,
            options=options
        )
    
    def get_cost_breakdown_chart(self, session, days: int = 30) -> ChartData:
        """Get cost breakdown bar chart"""
        from .models import CostRecord
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            CostRecord.category,
            func.sum(CostRecord.amount).label('total')
        ).filter(
            CostRecord.timestamp >= start_date
        ).group_by(CostRecord.category).order_by(func.sum(CostRecord.amount).desc()).all()
        
        labels = [r.category for r in results]
        values = [float(r.total) for r in results]
        
        return self.create_bar_chart(
            labels=labels,
            datasets=[('Cost (USD)', values)],
            title='Cost Breakdown by Category'
        )
    
    def get_agent_performance_chart(self, session, days: int = 7) -> ChartData:
        """Get agent performance comparison chart"""
        from .models import AgentPerformanceMetric
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            AgentPerformanceMetric.agent_type,
            func.avg(AgentPerformanceMetric.response_time_ms).label('avg_response'),
            func.avg(AgentPerformanceMetric.success_rate).label('avg_success')
        ).filter(
            AgentPerformanceMetric.timestamp >= start_date
        ).group_by(AgentPerformanceMetric.agent_type).all()
        
        labels = [r.agent_type for r in results]
        response_times = [round(r.avg_response or 0, 2) for r in results]
        success_rates = [round((r.avg_success or 0) * 100, 1) for r in results]
        
        return ChartData(
            chart_type='bar',
            labels=labels,
            datasets=[
                ChartDataset(
                    label='Avg Response Time (ms)',
                    data=response_times,
                    backgroundColor=ColorPalette.PRIMARY_LIGHT[0],
                    borderColor=ColorPalette.PRIMARY[0]
                ),
                ChartDataset(
                    label='Success Rate (%)',
                    data=success_rates,
                    backgroundColor=ColorPalette.PRIMARY_LIGHT[1],
                    borderColor=ColorPalette.PRIMARY[1]
                )
            ],
            title='Agent Performance Comparison',
            options={
                'responsive': True,
                'plugins': {'legend': {'display': True}}
            }
        )
    
    # ==================== Trend Charts ====================
    
    def create_sparkline(self, data: List[float], color: str = None) -> Dict[str, Any]:
        """Create a sparkline mini-chart"""
        return {
            'type': 'sparkline',
            'data': data,
            'color': color or ColorPalette.PRIMARY[0],
            'options': {
                'width': 100,
                'height': 30,
                'lineWidth': 2
            }
        }
    
    def get_metric_sparklines(self, session, days: int = 7) -> Dict[str, Any]:
        """Get sparkline data for key metrics"""
        from .models import RFPMetric, WinLossRecord, CostRecord
        from sqlalchemy import func
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        sparklines = {}
        
        # RFP count sparkline
        rfp_results = session.query(
            func.date(RFPMetric.timestamp).label('date'),
            func.count(RFPMetric.id).label('count')
        ).filter(
            RFPMetric.timestamp >= start_date
        ).group_by(func.date(RFPMetric.timestamp)).order_by('date').all()
        
        sparklines['rfp_volume'] = self.create_sparkline(
            [r.count for r in rfp_results],
            ColorPalette.PRIMARY[0]
        )
        
        # Daily costs sparkline
        cost_results = session.query(
            func.date(CostRecord.timestamp).label('date'),
            func.sum(CostRecord.amount).label('total')
        ).filter(
            CostRecord.timestamp >= start_date
        ).group_by(func.date(CostRecord.timestamp)).order_by('date').all()
        
        sparklines['costs'] = self.create_sparkline(
            [float(r.total) for r in cost_results],
            ColorPalette.PRIMARY[1]
        )
        
        return sparklines
    
    # ==================== Gauge Charts ====================
    
    def create_gauge_chart(self, value: float, max_value: float = 100,
                          title: str = None,
                          thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """Create a gauge chart data"""
        if thresholds is None:
            thresholds = {'danger': 25, 'warning': 50, 'success': 75}
        
        # Determine color based on thresholds
        if value >= thresholds.get('success', 75):
            color = ColorPalette.SUCCESS
        elif value >= thresholds.get('warning', 50):
            color = ColorPalette.WARNING
        else:
            color = ColorPalette.DANGER
        
        return {
            'type': 'gauge',
            'value': value,
            'max': max_value,
            'color': color,
            'title': title,
            'percentage': round(value / max_value * 100, 1)
        }
    
    def get_health_gauges(self, session = None) -> Dict[str, Any]:
        """Get system health gauge charts"""
        from .system_health import SystemHealthMonitor
        
        monitor = SystemHealthMonitor()
        metrics = monitor.get_system_metrics()
        
        return {
            'cpu': self.create_gauge_chart(
                metrics.get('cpu_percent', 0),
                100,
                'CPU Usage',
                {'danger': 90, 'warning': 70, 'success': 0}  # Inverted for resource usage
            ),
            'memory': self.create_gauge_chart(
                metrics.get('memory_percent', 0),
                100,
                'Memory Usage',
                {'danger': 90, 'warning': 70, 'success': 0}
            ),
            'disk': self.create_gauge_chart(
                metrics.get('disk_percent', 0),
                100,
                'Disk Usage',
                {'danger': 95, 'warning': 80, 'success': 0}
            )
        }
    
    # ==================== Comparison Charts ====================
    
    def create_radar_chart(self, labels: List[str],
                          datasets: List[Tuple[str, List[float]]],
                          title: str = None) -> ChartData:
        """Create a radar chart for multi-dimensional comparison"""
        chart_datasets = []
        for i, (name, data) in enumerate(datasets):
            chart_datasets.append(ChartDataset(
                label=name,
                data=data,
                backgroundColor=ColorPalette.get_color(i, light=True),
                borderColor=ColorPalette.get_color(i),
                fill=True
            ))
        
        return ChartData(
            chart_type='radar',
            labels=labels,
            datasets=chart_datasets,
            title=title,
            options={
                'responsive': True,
                'plugins': {'legend': {'position': 'top'}},
                'scales': {
                    'r': {
                        'beginAtZero': True,
                        'max': 100
                    }
                }
            }
        )
    
    def get_performance_radar(self, session, days: int = 30) -> ChartData:
        """Get performance radar chart"""
        # This would typically aggregate various performance metrics
        dimensions = ['Win Rate', 'Response Time', 'Cost Efficiency', 
                     'Accuracy', 'Throughput']
        
        # Current period scores (0-100)
        current_scores = [75, 85, 60, 90, 70]
        # Previous period for comparison
        previous_scores = [70, 80, 55, 85, 75]
        
        return self.create_radar_chart(
            dimensions,
            [
                ('Current Period', current_scores),
                ('Previous Period', previous_scores)
            ],
            'Performance Comparison'
        )
    
    # ==================== Heatmap ====================
    
    def create_heatmap(self, x_labels: List[str], y_labels: List[str],
                      data: List[List[float]], title: str = None) -> Dict[str, Any]:
        """Create a heatmap visualization"""
        # Normalize data for color intensity
        flat_data = [v for row in data for v in row]
        min_val = min(flat_data) if flat_data else 0
        max_val = max(flat_data) if flat_data else 1
        range_val = max_val - min_val or 1
        
        cells = []
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                intensity = (value - min_val) / range_val
                cells.append({
                    'x': j,
                    'y': i,
                    'value': value,
                    'intensity': intensity
                })
        
        return {
            'type': 'heatmap',
            'x_labels': x_labels,
            'y_labels': y_labels,
            'cells': cells,
            'title': title,
            'min_value': min_val,
            'max_value': max_val
        }
    
    def get_hourly_activity_heatmap(self, session, days: int = 7) -> Dict[str, Any]:
        """Get hourly activity heatmap (hour vs day of week)"""
        from .models import RFPMetric
        from sqlalchemy import func, extract
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = session.query(
            extract('dow', RFPMetric.timestamp).label('day_of_week'),
            extract('hour', RFPMetric.timestamp).label('hour'),
            func.count(RFPMetric.id).label('count')
        ).filter(
            RFPMetric.timestamp >= start_date
        ).group_by('day_of_week', 'hour').all()
        
        # Build heatmap data
        days_of_week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        hours = [f'{h:02d}:00' for h in range(24)]
        
        data = [[0] * 24 for _ in range(7)]
        for r in results:
            dow = int(r.day_of_week or 0)
            hour = int(r.hour or 0)
            data[dow][hour] = r.count
        
        return self.create_heatmap(hours, days_of_week, data, 'Activity by Hour and Day')
    
    # ==================== Dashboard Layouts ====================
    
    def get_dashboard_layout(self, session, days: int = 30) -> Dict[str, Any]:
        """Get complete dashboard layout with all charts"""
        return {
            'overview': {
                'rfp_volume': self.get_rfp_volume_chart(session, days).to_dict(),
                'win_loss': self.get_win_loss_pie_chart(session, days).to_dict(),
                'sparklines': self.get_metric_sparklines(session, min(days, 7))
            },
            'performance': {
                'costs': self.get_cost_breakdown_chart(session, days).to_dict(),
                'agents': self.get_agent_performance_chart(session, min(days, 7)).to_dict(),
                'radar': self.get_performance_radar(session, days).to_dict()
            },
            'health': {
                'gauges': self.get_health_gauges(),
                'activity_heatmap': self.get_hourly_activity_heatmap(session, min(days, 7))
            }
        }
