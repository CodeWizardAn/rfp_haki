"""
Analytics Database Models
SQLAlchemy models for comprehensive analytics data storage

Models for tracking:
- RFP processing metrics
- Match accuracy metrics
- Win/loss records
- Agent performance
- System health
- Response times
- Costs
- A/B testing
- Benchmarks
- Alerts
- Scheduled reports
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import Base


# ==================== ENUMS ====================

class MetricType(PyEnum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TimeGranularity(PyEnum):
    """Time granularity for aggregations"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class AlertSeverity(PyEnum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(PyEnum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class ReportFrequency(PyEnum):
    """Scheduled report frequency"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ExperimentStatus(PyEnum):
    """A/B test experiment status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ==================== RFP METRICS ====================

class RFPMetric(Base):
    """
    RFP Processing Metrics
    Tracks processing time, status changes, and outcomes for each RFP
    """
    __tablename__ = 'analytics_rfp_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rfp_id = Column(String(50), nullable=False, index=True)
    
    # Timing Metrics
    extraction_time_ms = Column(Integer)  # PDF extraction time
    parsing_time_ms = Column(Integer)  # Requirement parsing time
    matching_time_ms = Column(Integer)  # Product matching time
    bid_generation_time_ms = Column(Integer)  # Bid document generation time
    total_processing_time_ms = Column(Integer)  # Total end-to-end time
    
    # Volume Metrics
    requirements_count = Column(Integer, default=0)
    products_matched = Column(Integer, default=0)
    matches_generated = Column(Integer, default=0)
    
    # Quality Metrics
    avg_match_confidence = Column(Float, default=0.0)
    manual_overrides_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Status Tracking
    initial_status = Column(String(50))
    final_status = Column(String(50))
    status_changes = Column(JSON, default=[])  # List of status transitions
    
    # Outcome
    outcome = Column(String(50))  # won, lost, cancelled, pending
    outcome_reason = Column(Text)
    
    # Financial
    estimated_value = Column(Float)
    bid_value = Column(Float)
    actual_value = Column(Float)  # If won
    margin_percent = Column(Float)
    
    # Metadata
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_rfp_metric_time', 'recorded_at'),
        Index('idx_rfp_metric_outcome', 'outcome', 'recorded_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rfp_id': self.rfp_id,
            'total_processing_time_ms': self.total_processing_time_ms,
            'requirements_count': self.requirements_count,
            'products_matched': self.products_matched,
            'avg_match_confidence': self.avg_match_confidence,
            'outcome': self.outcome,
            'estimated_value': self.estimated_value,
            'bid_value': self.bid_value,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


# ==================== MATCH ACCURACY ====================

class MatchAccuracyMetric(Base):
    """
    Match Accuracy Tracking
    Tracks the accuracy of product matching algorithms
    """
    __tablename__ = 'analytics_match_accuracy'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference
    rfp_id = Column(String(50), index=True)
    requirement_id = Column(Integer, index=True)
    
    # Algorithm Info
    algorithm_version = Column(String(50))
    algorithm_config = Column(JSON, default={})
    
    # Match Details
    predicted_product_id = Column(Integer)
    predicted_confidence = Column(Float)
    
    # Validation
    actual_product_id = Column(Integer)  # Human-validated selection
    is_correct = Column(Boolean)
    was_in_top_3 = Column(Boolean)
    was_in_top_5 = Column(Boolean)
    actual_rank = Column(Integer)  # Where correct product appeared in ranking
    
    # Detailed Scores
    spec_match_accuracy = Column(Float)  # How well specs matched
    semantic_accuracy = Column(Float)  # Semantic similarity accuracy
    
    # Feedback
    feedback_source = Column(String(50))  # human, system, auto
    feedback_notes = Column(Text)
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_match_accuracy_time', 'recorded_at'),
        Index('idx_match_accuracy_correct', 'is_correct', 'recorded_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rfp_id': self.rfp_id,
            'predicted_confidence': self.predicted_confidence,
            'is_correct': self.is_correct,
            'was_in_top_3': self.was_in_top_3,
            'actual_rank': self.actual_rank,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


# ==================== WIN/LOSS ANALYTICS ====================

class WinLossRecord(Base):
    """
    Win/Loss Analytics
    Comprehensive tracking of bid outcomes
    """
    __tablename__ = 'analytics_win_loss'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # References
    rfp_id = Column(String(50), nullable=False, index=True)
    bid_id = Column(String(50), index=True)
    
    # Outcome
    outcome = Column(String(20), nullable=False, index=True)  # won, lost, no_bid
    outcome_date = Column(DateTime)
    outcome_reason = Column(String(200))
    outcome_details = Column(Text)
    
    # Competition Analysis
    competitors_count = Column(Integer)
    competitor_names = Column(JSON, default=[])
    winning_competitor = Column(String(200))  # If lost
    winning_bid_amount = Column(Float)  # If known
    
    # Our Bid Analysis
    our_bid_amount = Column(Float)
    price_difference_percent = Column(Float)  # vs winning bid
    
    # Scoring
    technical_score = Column(Float)
    commercial_score = Column(Float)
    overall_score = Column(Float)
    
    # Factors (why we won/lost)
    winning_factors = Column(JSON, default=[])
    losing_factors = Column(JSON, default=[])
    
    # Customer
    customer_name = Column(String(200), index=True)
    customer_segment = Column(String(100))
    customer_region = Column(String(100))
    
    # Category
    rfp_category = Column(String(100), index=True)
    contract_duration_months = Column(Integer)
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    recorded_by = Column(String(100))
    
    __table_args__ = (
        Index('idx_win_loss_outcome_time', 'outcome', 'recorded_at'),
        Index('idx_win_loss_customer', 'customer_name', 'outcome'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rfp_id': self.rfp_id,
            'outcome': self.outcome,
            'our_bid_amount': self.our_bid_amount,
            'winning_bid_amount': self.winning_bid_amount,
            'customer_name': self.customer_name,
            'rfp_category': self.rfp_category,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


# ==================== AGENT PERFORMANCE ====================

class AgentPerformanceMetric(Base):
    """
    Agent Performance Metrics
    Tracks individual agent performance over time
    """
    __tablename__ = 'analytics_agent_performance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Agent Identification
    agent_type = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(100))
    agent_version = Column(String(20))
    
    # Time Period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    granularity = Column(Enum(TimeGranularity), default=TimeGranularity.HOUR)
    
    # Volume Metrics
    requests_total = Column(Integer, default=0)
    requests_successful = Column(Integer, default=0)
    requests_failed = Column(Integer, default=0)
    
    # Timing Metrics
    avg_response_time_ms = Column(Float)
    p50_response_time_ms = Column(Float)
    p95_response_time_ms = Column(Float)
    p99_response_time_ms = Column(Float)
    max_response_time_ms = Column(Float)
    
    # Resource Usage
    avg_tokens_used = Column(Float)  # For LLM agents
    total_tokens_used = Column(Integer)
    avg_memory_mb = Column(Float)
    peak_memory_mb = Column(Float)
    
    # Quality Metrics
    accuracy_rate = Column(Float)  # Correct responses / total
    confidence_avg = Column(Float)
    user_satisfaction_avg = Column(Float)  # If feedback collected
    
    # Error Analysis
    error_types = Column(JSON, default={})  # Error type -> count
    retry_count = Column(Integer, default=0)
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_agent_perf_type_time', 'agent_type', 'period_start'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'agent_type': self.agent_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'requests_total': self.requests_total,
            'requests_successful': self.requests_successful,
            'avg_response_time_ms': self.avg_response_time_ms,
            'accuracy_rate': self.accuracy_rate,
            'total_tokens_used': self.total_tokens_used
        }


# ==================== SYSTEM HEALTH ====================

class SystemHealthMetric(Base):
    """
    System Health Monitoring
    Tracks overall system health and resource usage
    """
    __tablename__ = 'analytics_system_health'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Component
    component = Column(String(100), nullable=False, index=True)  # api, database, agent, etc.
    instance_id = Column(String(100))  # For distributed systems
    
    # CPU Metrics
    cpu_usage_percent = Column(Float)
    cpu_load_1m = Column(Float)
    cpu_load_5m = Column(Float)
    cpu_load_15m = Column(Float)
    
    # Memory Metrics
    memory_used_mb = Column(Float)
    memory_available_mb = Column(Float)
    memory_percent = Column(Float)
    swap_used_mb = Column(Float)
    
    # Disk Metrics
    disk_used_gb = Column(Float)
    disk_available_gb = Column(Float)
    disk_percent = Column(Float)
    disk_io_read_mb = Column(Float)
    disk_io_write_mb = Column(Float)
    
    # Network Metrics
    network_bytes_sent = Column(Float)
    network_bytes_recv = Column(Float)
    network_connections = Column(Integer)
    
    # Database Metrics
    db_connections_active = Column(Integer)
    db_connections_idle = Column(Integer)
    db_queries_per_second = Column(Float)
    db_slow_queries = Column(Integer)
    
    # Application Metrics
    active_requests = Column(Integer)
    queued_requests = Column(Integer)
    error_rate_percent = Column(Float)
    
    # Health Status
    health_status = Column(String(20))  # healthy, degraded, unhealthy
    health_checks = Column(JSON, default={})  # Individual check results
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_health_component_time', 'component', 'recorded_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'component': self.component,
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_percent': self.memory_percent,
            'disk_percent': self.disk_percent,
            'health_status': self.health_status,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


# ==================== RESPONSE TIME ====================

class ResponseTimeMetric(Base):
    """
    Response Time Analytics
    Detailed tracking of response times across the system
    """
    __tablename__ = 'analytics_response_time'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identification
    endpoint = Column(String(200), nullable=False, index=True)  # API endpoint or operation
    method = Column(String(10))  # GET, POST, etc.
    operation_type = Column(String(50))  # extract, match, generate, etc.
    
    # Request Details
    request_id = Column(String(100), index=True)
    rfp_id = Column(String(50), index=True)
    
    # Timing Breakdown
    total_time_ms = Column(Integer, nullable=False)
    queue_time_ms = Column(Integer)  # Time waiting to be processed
    processing_time_ms = Column(Integer)  # Actual processing
    db_time_ms = Column(Integer)  # Database operations
    external_api_time_ms = Column(Integer)  # External API calls
    serialization_time_ms = Column(Integer)  # Response serialization
    
    # Request Size
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    
    # Status
    status_code = Column(Integer)
    is_success = Column(Boolean)
    error_type = Column(String(100))
    
    # Context
    user_id = Column(String(100))
    client_ip = Column(String(50))
    user_agent = Column(String(500))
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_response_endpoint_time', 'endpoint', 'recorded_at'),
        Index('idx_response_success', 'is_success', 'recorded_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'total_time_ms': self.total_time_ms,
            'status_code': self.status_code,
            'is_success': self.is_success,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


# ==================== COST RECORDS ====================

class CostRecord(Base):
    """
    Cost Tracking
    Tracks costs associated with RFP processing
    """
    __tablename__ = 'analytics_costs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference
    rfp_id = Column(String(50), index=True)
    operation_id = Column(String(100))
    
    # Cost Category
    cost_category = Column(String(50), nullable=False, index=True)  # llm, compute, storage, api
    cost_subcategory = Column(String(50))  # openai, azure, aws, etc.
    
    # Cost Details
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    
    # Resource Usage
    units_consumed = Column(Float)
    unit_type = Column(String(50))  # tokens, requests, gb-hours, etc.
    unit_cost = Column(Float)
    
    # Context
    agent_type = Column(String(50))
    operation_type = Column(String(50))
    
    # Time Period
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_cost_category_time', 'cost_category', 'recorded_at'),
        Index('idx_cost_rfp', 'rfp_id', 'recorded_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'rfp_id': self.rfp_id,
            'cost_category': self.cost_category,
            'amount': self.amount,
            'currency': self.currency,
            'units_consumed': self.units_consumed,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }


# ==================== A/B TESTING ====================

class ABTestExperiment(Base):
    """
    A/B Test Experiment Definition
    """
    __tablename__ = 'analytics_ab_experiments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Configuration
    target_metric = Column(String(100), nullable=False)  # What we're measuring
    success_criteria = Column(JSON, default={})  # How to determine winner
    
    # Traffic Split
    traffic_percent = Column(Float, default=100.0)  # % of traffic in experiment
    
    # Status
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, index=True)
    
    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Results
    winner_variant_id = Column(Integer)
    statistical_significance = Column(Float)
    conclusion = Column(Text)
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    variants = relationship('ABTestVariant', back_populates='experiment', cascade='all, delete-orphan')
    results = relationship('ABTestResult', back_populates='experiment', cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'experiment_id': self.experiment_id,
            'name': self.name,
            'target_metric': self.target_metric,
            'status': self.status.value if self.status else None,
            'variants_count': len(self.variants) if self.variants else 0
        }


class ABTestVariant(Base):
    """
    A/B Test Variant Configuration
    """
    __tablename__ = 'analytics_ab_variants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference
    experiment_id = Column(Integer, ForeignKey('analytics_ab_experiments.id', ondelete='CASCADE'), 
                          nullable=False, index=True)
    
    # Variant Details
    variant_name = Column(String(50), nullable=False)  # control, treatment_a, etc.
    variant_description = Column(Text)
    
    # Configuration
    config = Column(JSON, default={})  # Variant-specific settings
    traffic_weight = Column(Float, default=50.0)  # % of experiment traffic
    
    # Status
    is_control = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    experiment = relationship('ABTestExperiment', back_populates='variants')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'variant_name': self.variant_name,
            'is_control': self.is_control,
            'traffic_weight': self.traffic_weight,
            'config': self.config
        }


class ABTestResult(Base):
    """
    A/B Test Result Recording
    """
    __tablename__ = 'analytics_ab_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # References
    experiment_id = Column(Integer, ForeignKey('analytics_ab_experiments.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey('analytics_ab_variants.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    
    # Subject
    subject_id = Column(String(100))  # rfp_id, user_id, etc.
    subject_type = Column(String(50))
    
    # Metrics
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    
    # Context
    context = Column(JSON, default={})
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    experiment = relationship('ABTestExperiment', back_populates='results')
    
    __table_args__ = (
        Index('idx_ab_result_exp_variant', 'experiment_id', 'variant_id'),
    )


# ==================== BENCHMARKS ====================

class Benchmark(Base):
    """
    Performance Benchmarks
    Stores baseline and comparison benchmarks
    """
    __tablename__ = 'analytics_benchmarks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Benchmark Type
    benchmark_type = Column(String(50), index=True)  # baseline, target, industry
    metric_name = Column(String(100), nullable=False, index=True)
    
    # Values
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    
    # Thresholds
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    is_higher_better = Column(Boolean, default=True)
    
    # Validity
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    
    # Source
    source = Column(String(100))  # historical, external, manual
    source_details = Column(Text)
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'benchmark_id': self.benchmark_id,
            'name': self.name,
            'metric_name': self.metric_name,
            'value': self.value,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'is_active': self.is_active
        }


# ==================== ALERTS ====================

class Alert(Base):
    """
    Alert Records
    Stores generated alerts and their status
    """
    __tablename__ = 'analytics_alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Alert Details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    
    # Source
    source_component = Column(String(100))
    source_metric = Column(String(100))
    
    # Trigger
    trigger_condition = Column(Text)
    trigger_value = Column(Float)
    threshold_value = Column(Float)
    
    # Status
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, index=True)
    
    # Timeline
    triggered_at = Column(DateTime, nullable=False, index=True)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    
    # Resolution
    resolution_notes = Column(Text)
    root_cause = Column(Text)
    
    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSON, default=[])  # email, slack, etc.
    
    # Metadata
    tags = Column(JSON, default=[])
    alert_metadata = Column(JSON, default={})
    
    __table_args__ = (
        Index('idx_alert_severity_status', 'severity', 'status'),
        Index('idx_alert_triggered', 'triggered_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'name': self.name,
            'severity': self.severity.value if self.severity else None,
            'status': self.status.value if self.status else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None
        }


# ==================== SCHEDULED REPORTS ====================

class ScheduledReport(Base):
    """
    Scheduled Report Configuration
    """
    __tablename__ = 'analytics_scheduled_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Report Configuration
    report_type = Column(String(50), nullable=False)  # rfp_summary, performance, costs, etc.
    report_config = Column(JSON, default={})  # Filters, date ranges, etc.
    output_format = Column(String(20), default='pdf')  # pdf, xlsx, csv
    
    # Schedule
    frequency = Column(Enum(ReportFrequency), nullable=False, index=True)
    schedule_time = Column(String(20))  # HH:MM
    schedule_day = Column(Integer)  # Day of week (0-6) or month (1-31)
    timezone = Column(String(50), default='UTC')
    
    # Delivery
    recipients = Column(JSON, default=[])  # Email addresses
    delivery_channels = Column(JSON, default=['email'])
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    last_run_at = Column(DateTime)
    last_run_status = Column(String(50))
    next_run_at = Column(DateTime)
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'report_id': self.report_id,
            'name': self.name,
            'report_type': self.report_type,
            'frequency': self.frequency.value if self.frequency else None,
            'is_active': self.is_active,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None
        }


# ==================== ANALYTICS SNAPSHOTS ====================

class AnalyticsSnapshot(Base):
    """
    Point-in-time analytics snapshots
    Pre-computed aggregations for fast dashboard loading
    """
    __tablename__ = 'analytics_snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Snapshot Identification
    snapshot_type = Column(String(50), nullable=False, index=True)  # daily_summary, weekly_kpis, etc.
    snapshot_date = Column(DateTime, nullable=False, index=True)
    granularity = Column(Enum(TimeGranularity), default=TimeGranularity.DAY)
    
    # Aggregated Metrics
    metrics = Column(JSON, nullable=False)  # All aggregated metrics
    
    # Dimensions
    dimensions = Column(JSON, default={})  # Filter dimensions for this snapshot
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    generation_time_ms = Column(Integer)
    
    __table_args__ = (
        UniqueConstraint('snapshot_type', 'snapshot_date', 'granularity', name='uq_snapshot'),
        Index('idx_snapshot_type_date', 'snapshot_type', 'snapshot_date'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'snapshot_type': self.snapshot_type,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'metrics': self.metrics,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }
