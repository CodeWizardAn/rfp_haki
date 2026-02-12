"""
OEM Vendor Performance Metrics
Manufacturing and technical performance tracking for OEM vendors
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class MetricCategory(Enum):
    """Performance metric categories"""
    QUALITY = "QUALITY"
    CAPACITY = "CAPACITY"
    DELIVERY = "DELIVERY"
    RESPONSIVENESS = "RESPONSIVENESS"
    TECHNICAL = "TECHNICAL"
    COMPLIANCE = "COMPLIANCE"


@dataclass
class QualityMetric:
    """Quality performance metric"""
    metric_id: str
    measurement_date: datetime
    product_category: str
    
    # Quality indicators
    defect_rate_ppm: float  # Parts per million
    first_pass_yield_percent: float  # % of products passing first test
    rework_rate_percent: float
    scrap_rate_percent: float
    
    # Corrective Actions
    open_capa_count: int  # Corrective & Preventive Actions
    closed_capa_count: int
    capa_resolution_days: float
    
    # Audits
    internal_audit_score: float  # 0-100
    external_audit_score: float
    compliance_issues: int
    
    def get_quality_score(self) -> float:
        """Calculate overall quality score (0-100)"""
        # Weighten average of metrics
        weights = {
            'defect_rate': 0.25,
            'first_pass_yield': 0.25,
            'audit_score': 0.30,
            'capa_effectiveness': 0.20
        }
        
        # Normalize defect rate (lower is better)
        defect_score = max(0, 100 - (self.defect_rate_ppm / 100))
        
        # First pass yield is already %
        yield_score = self.first_pass_yield_percent
        
        # Average of audit scores
        audit_score = (self.internal_audit_score + self.external_audit_score) / 2
        
        # CAPA effectiveness (more closed = better)
        capa_score = (self.closed_capa_count / (self.open_capa_count + self.closed_capa_count + 1)) * 100
        
        overall = (
            defect_score * weights['defect_rate'] +
            yield_score * weights['first_pass_yield'] +
            audit_score * weights['audit_score'] +
            capa_score * weights['capa_effectiveness']
        )
        
        return round(overall, 2)


@dataclass
class CapacityMetric:
    """Manufacturing capacity metric"""
    metric_id: str
    measurement_date: datetime
    product_category: str
    
    # Capacity details
    total_capacity_monthly_units: int
    current_utilization_units: int
    utilization_percent: float
    
    # Equipment
    machines_operational: int
    machines_total: int
    equipment_downtime_percent: float
    
    # Workforce
    skilled_workers_available: int
    skilled_workers_total: int
    worker_efficiency_percent: float
    
    # Production
    average_daily_production: int
    peak_capacity_achieved_percent: float  # Has vendor reached peak?
    scalability_rating: str  # LOW, MEDIUM, HIGH
    
    def get_capacity_score(self) -> float:
        """Calculate capacity score (0-100)"""
        weights = {
            'utilization': 0.30,
            'equipment': 0.25,
            'workforce': 0.25,
            'scalability': 0.20
        }
        
        # Utilization score (optimal around 75-85%)
        if self.utilization_percent <= 85:
            util_score = (self.utilization_percent / 85) * 100
        else:
            util_score = max(0, 100 - ((self.utilization_percent - 85) / 15) * 100)
        
        # Equipment score
        equipment_score = (self.machines_operational / max(1, self.machines_total)) * 100
        
        # Workforce score
        workforce_score = (self.skilled_workers_available / max(1, self.skilled_workers_total)) * 100
        
        # Scalability score
        scalability_scores = {"LOW": 30, "MEDIUM": 70, "HIGH": 100}
        scalability_score = scalability_scores.get(self.scalability_rating, 50)
        
        overall = (
            util_score * weights['utilization'] +
            equipment_score * weights['equipment'] +
            workforce_score * weights['workforce'] +
            scalability_score * weights['scalability']
        )
        
        return round(overall, 2)


@dataclass
class DeliveryMetric:
    """Delivery performance metric"""
    metric_id: str
    measurement_date: datetime
    product_category: str
    
    # Delivery performance
    total_orders: int
    on_time_orders: int
    early_orders: int
    late_orders: int
    
    # Lead time
    average_lead_time_days: float
    promised_vs_actual_variance_days: float  # Negative = early, positive = late
    
    # Shipping
    total_shipments: int
    damaged_shipments: int
    incomplete_shipments: int
    
    # Documentation
    complete_documentation_percent: float  # 0-100
    invoice_accuracy_percent: float
    
    def get_delivery_score(self) -> float:
        """Calculate delivery score (0-100)"""
        weights = {
            'on_time_percent': 0.40,
            'lead_time_variance': 0.20,
            'shipment_quality': 0.20,
            'documentation': 0.20
        }
        
        # On-time percentage
        on_time_percent = (self.on_time_orders + self.early_orders) / max(1, self.total_orders) * 100
        on_time_score = min(100, on_time_percent)
        
        # Lead time variance (ideally 0)
        variance_score = max(0, 100 - (abs(self.promised_vs_actual_variance_days) * 5))
        
        # Shipment quality
        good_shipments = self.total_shipments - self.damaged_shipments - self.incomplete_shipments
        shipment_score = (good_shipments / max(1, self.total_shipments)) * 100
        
        # Documentation
        doc_score = (self.complete_documentation_percent + self.invoice_accuracy_percent) / 2
        
        overall = (
            on_time_score * weights['on_time_percent'] +
            variance_score * weights['lead_time_variance'] +
            shipment_score * weights['shipment_quality'] +
            doc_score * weights['documentation']
        )
        
        return round(overall, 2)


@dataclass
class ResponsivenessMetric:
    """Responsiveness and communication metric"""
    metric_id: str
    measurement_date: datetime
    
    # Communication
    average_response_time_hours: float
    response_within_24h_percent: float
    
    # Issue resolution
    open_issues: int
    issues_resolved_within_sla: int
    average_resolution_time_days: float
    
    # Flexibility
    design_change_requests_handled: int
    urgent_order_fulfillment_percent: float
    
    # Support
    technical_support_availability: str  # 24x7, BUSINESS_HOURS, LIMITED
    dedicated_account_manager: bool
    support_team_size: int
    
    def get_responsiveness_score(self) -> float:
        """Calculate responsiveness score (0-100)"""
        weights = {
            'response_time': 0.35,
            'issue_resolution': 0.35,
            'flexibility': 0.20,
            'support': 0.10
        }
        
        # Response time (target < 4 hours)
        if self.average_response_time_hours <= 4:
            response_score = 100
        else:
            response_score = max(0, 100 - ((self.average_response_time_hours - 4) / 4) * 50)
        
        # Issue resolution
        if self.open_issues + self.issues_resolved_within_sla > 0:
            resolution_score = (self.issues_resolved_within_sla / 
                              (self.open_issues + self.issues_resolved_within_sla)) * 100
        else:
            resolution_score = 100
        
        # Flexibility
        flexibility_score = self.urgent_order_fulfillment_percent
        
        # Support
        support_scores = {"24x7": 100, "BUSINESS_HOURS": 70, "LIMITED": 40}
        support_score = support_scores.get(self.technical_support_availability, 50)
        if self.dedicated_account_manager:
            support_score += 10
        
        overall = (
            response_score * weights['response_time'] +
            resolution_score * weights['issue_resolution'] +
            flexibility_score * weights['flexibility'] +
            min(100, support_score) * weights['support']
        )
        
        return round(overall, 2)


@dataclass
class TechnicalMetric:
    """Technical capability metric"""
    metric_id: str
    measurement_date: datetime
    
    # Engineering
    design_capability_rating: str  # BASIC, INTERMEDIATE, ADVANCED, EXPERT
    prototyping_capability: bool
    testing_capability: bool
    documentation_quality: str  # POOR, ACCEPTABLE, GOOD, EXCELLENT
    
    # Compliance
    active_certifications: int
    key_certifications_count: int  # ISO 9001, RoHS, etc.
    compliance_audit_score: float
    
    # Innovation
    design_improvements_last_year: int
    patent_applications: int
    industry_awards: int
    
    def get_technical_score(self) -> float:
        """Calculate technical score (0-100)"""
        weights = {
            'capability': 0.35,
            'certifications': 0.35,
            'innovation': 0.30
        }
        
        # Capability score
        capability_scores = {"BASIC": 30, "INTERMEDIATE": 60, "ADVANCED": 80, "EXPERT": 100}
        capability_score = capability_scores.get(self.design_capability_rating, 50)
        
        # Add bonus for capabilities
        if self.prototyping_capability:
            capability_score += 5
        if self.testing_capability:
            capability_score += 5
        
        capability_score = min(100, capability_score)
        
        # Certification score
        cert_score = min(100, (self.active_certifications * 10) + 
                        (self.key_certifications_count * 15))
        cert_score = (cert_score + self.compliance_audit_score) / 2
        
        # Innovation score
        innovation_score = (self.design_improvements_last_year * 5) + \
                          (self.patent_applications * 10) + \
                          (self.industry_awards * 15)
        innovation_score = min(100, innovation_score)
        
        overall = (
            capability_score * weights['capability'] +
            cert_score * weights['certifications'] +
            innovation_score * weights['innovation']
        )
        
        return round(overall, 2)


@dataclass
class ComplianceMetric:
    """Regulatory and compliance metric"""
    metric_id: str
    measurement_date: datetime
    
    # Certifications
    iso_9001_valid: bool
    iso_14001_valid: bool
    iso_45001_valid: bool
    rohs_compliant: bool
    reach_compliant: bool
    
    # Regulatory
    government_inspections_last_year: int
    inspection_violations: int
    environmental_violations: int
    safety_incidents: int
    
    # Documentation
    documented_processes_percent: float
    quality_manual_updated: bool
    audit_trail_maintained: bool
    
    def get_compliance_score(self) -> float:
        """Calculate compliance score (0-100)"""
        score = 0
        
        # Certification points (max 40)
        certs = [self.iso_9001_valid, self.iso_14001_valid, 
                self.iso_45001_valid, self.rohs_compliant, self.reach_compliant]
        cert_count = sum(1 for c in certs if c)
        score += (cert_count / 5) * 40
        
        # Regulatory compliance (max 40)
        violations = self.inspection_violations + self.environmental_violations + self.safety_incidents
        if violations == 0:
            score += 40
        else:
            score += max(0, 40 - (violations * 10))
        
        # Documentation (max 20)
        doc_score = self.documented_processes_percent * 0.1
        if self.quality_manual_updated:
            doc_score += 5
        if self.audit_trail_maintained:
            doc_score += 5
        score += doc_score
        
        return round(min(100, score), 2)


@dataclass
class OEMVendorPerformanceReport:
    """Comprehensive OEM vendor performance report"""
    report_id: str
    vendor_id: str
    vendor_name: str
    report_period: str  # "Q1_2026", "JAN_2026", etc.
    report_date: datetime
    
    # Individual metrics
    quality_metric: Optional[QualityMetric] = None
    capacity_metric: Optional[CapacityMetric] = None
    delivery_metric: Optional[DeliveryMetric] = None
    responsiveness_metric: Optional[ResponsivenessMetric] = None
    technical_metric: Optional[TechnicalMetric] = None
    compliance_metric: Optional[ComplianceMetric] = None
    
    # Trends
    month_over_month_improvement: Dict[str, float] = field(default_factory=dict)  # Category -> % change
    quarter_over_quarter_trend: Dict[str, float] = field(default_factory=dict)
    
    # Overall assessment
    overall_score: float = 0.0
    performance_rating: str = "ACCEPTABLE"  # EXCELLENT, GOOD, ACCEPTABLE, POOR
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    
    def calculate_overall_score(self) -> float:
        """Calculate weighted overall performance score"""
        scores = {}
        weights = {
            'quality': 0.25,
            'capacity': 0.15,
            'delivery': 0.25,
            'responsiveness': 0.15,
            'technical': 0.12,
            'compliance': 0.08
        }
        
        if self.quality_metric:
            scores['quality'] = self.quality_metric.get_quality_score()
        if self.capacity_metric:
            scores['capacity'] = self.capacity_metric.get_capacity_score()
        if self.delivery_metric:
            scores['delivery'] = self.delivery_metric.get_delivery_score()
        if self.responsiveness_metric:
            scores['responsiveness'] = self.responsiveness_metric.get_responsiveness_score()
        if self.technical_metric:
            scores['technical'] = self.technical_metric.get_technical_score()
        if self.compliance_metric:
            scores['compliance'] = self.compliance_metric.get_compliance_score()
        
        # Calculate weighted average
        overall = 0
        total_weight = 0
        for category, weight in weights.items():
            if category in scores:
                overall += scores[category] * weight
                total_weight += weight
        
        self.overall_score = round(overall / total_weight, 2) if total_weight > 0 else 0
        
        # Set rating
        if self.overall_score >= 90:
            self.performance_rating = "EXCELLENT"
        elif self.overall_score >= 75:
            self.performance_rating = "GOOD"
        elif self.overall_score >= 60:
            self.performance_rating = "ACCEPTABLE"
        else:
            self.performance_rating = "POOR"
        
        # Set risk level
        if self.overall_score >= 85:
            self.risk_level = "LOW"
        elif self.overall_score >= 70:
            self.risk_level = "MEDIUM"
        elif self.overall_score >= 50:
            self.risk_level = "HIGH"
        else:
            self.risk_level = "CRITICAL"
        
        return self.overall_score
    
    def get_scores_by_category(self) -> Dict[str, float]:
        """Get all category scores"""
        scores = {}
        if self.quality_metric:
            scores['Quality'] = self.quality_metric.get_quality_score()
        if self.capacity_metric:
            scores['Capacity'] = self.capacity_metric.get_capacity_score()
        if self.delivery_metric:
            scores['Delivery'] = self.delivery_metric.get_delivery_score()
        if self.responsiveness_metric:
            scores['Responsiveness'] = self.responsiveness_metric.get_responsiveness_score()
        if self.technical_metric:
            scores['Technical'] = self.technical_metric.get_technical_score()
        if self.compliance_metric:
            scores['Compliance'] = self.compliance_metric.get_compliance_score()
        return scores


def create_sample_oem_performance_report() -> OEMVendorPerformanceReport:
    """Create sample OEM performance report"""
    
    report = OEMVendorPerformanceReport(
        report_id='PERF_001',
        vendor_id='OEM_VENDOR_001',
        vendor_name='ABC Manufacturing Ltd.',
        report_period='Q1_2026',
        report_date=datetime.now()
    )
    
    # Add quality metric
    report.quality_metric = QualityMetric(
        metric_id='QM_001',
        measurement_date=datetime.now(),
        product_category='Wires',
        defect_rate_ppm=500,  # 0.05%
        first_pass_yield_percent=99.2,
        rework_rate_percent=0.3,
        scrap_rate_percent=0.5,
        open_capa_count=2,
        closed_capa_count=8,
        capa_resolution_days=15.5,
        internal_audit_score=94.0,
        external_audit_score=92.5,
        compliance_issues=0
    )
    
    # Add capacity metric
    report.capacity_metric = CapacityMetric(
        metric_id='CAP_001',
        measurement_date=datetime.now(),
        product_category='Wires',
        total_capacity_monthly_units=5000000,
        current_utilization_units=3750000,
        utilization_percent=75.0,
        machines_operational=24,
        machines_total=25,
        equipment_downtime_percent=4.0,
        skilled_workers_available=145,
        skilled_workers_total=150,
        worker_efficiency_percent=96.7,
        average_daily_production=156250,
        peak_capacity_achieved_percent=88.0,
        scalability_rating='HIGH'
    )
    
    # Add delivery metric
    report.delivery_metric = DeliveryMetric(
        metric_id='DM_001',
        measurement_date=datetime.now(),
        product_category='Wires',
        total_orders=250,
        on_time_orders=242,
        early_orders=3,
        late_orders=5,
        average_lead_time_days=14.2,
        promised_vs_actual_variance_days=0.3,
        total_shipments=248,
        damaged_shipments=1,
        incomplete_shipments=0,
        complete_documentation_percent=99.2,
        invoice_accuracy_percent=98.8
    )
    
    # Add responsiveness metric
    report.responsiveness_metric = ResponsivenessMetric(
        metric_id='RM_001',
        measurement_date=datetime.now(),
        average_response_time_hours=2.5,
        response_within_24h_percent=99.5,
        open_issues=2,
        issues_resolved_within_sla=198,
        average_resolution_time_days=1.8,
        design_change_requests_handled=45,
        urgent_order_fulfillment_percent=92.0,
        technical_support_availability='24x7',
        dedicated_account_manager=True,
        support_team_size=8
    )
    
    # Calculate overall score
    report.calculate_overall_score()
    
    return report
