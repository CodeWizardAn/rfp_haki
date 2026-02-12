"""
OEM Vendor Profile
Enhanced vendor profile for OEM (Original Equipment Manufacturer) vendors
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class VendorType(Enum):
    """Vendor classification"""
    TRADER = "TRADER"
    MANUFACTURER = "MANUFACTURER"
    OEM = "OEM"
    CONTRACT_MANUFACTURER = "CONTRACT_MANUFACTURER"
    DISTRIBUTOR = "DISTRIBUTOR"


class ManufacturingCapability(Enum):
    """OEM manufacturing capabilities"""
    DESIGN_ENGINEERING = "DESIGN_ENGINEERING"
    PROTOTYPING = "PROTOTYPING"
    TOOLING_DESIGN = "TOOLING_DESIGN"
    PRODUCTION_SETUP = "PRODUCTION_SETUP"
    QUALITY_ASSURANCE = "QUALITY_ASSURANCE"
    PACKAGING = "PACKAGING"
    ASSEMBLY = "ASSEMBLY"
    TESTING = "TESTING"


class CertificationType(Enum):
    """Certification types for OEM"""
    ISO_9001 = "ISO_9001"  # Quality Management
    ISO_14001 = "ISO_14001"  # Environmental Management
    ISO_45001 = "ISO_45001"  # Occupational Health & Safety
    ISO_26262 = "ISO_26262"  # Functional Safety
    RoHS = "RoHS"  # Restriction of Hazardous Substances
    REACH = "REACH"  # Chemical Regulation
    ISO_27001 = "ISO_27001"  # Information Security
    CUSTOM = "CUSTOM"


@dataclass
class OEMCapacity:
    """OEM manufacturing capacity details"""
    capacity_id: str
    product_category: str
    monthly_capacity_units: int  # Units per month
    annual_capacity_units: int
    shift_count: int  # 1, 2, or 3 shifts
    machines_available: int
    skilled_workers: int
    facility_sq_ft: int
    current_utilization_percent: float = 0.0
    max_batch_size: int = 0
    min_batch_size: int = 0
    updated_date: datetime = None
    
    def __post_init__(self):
        if self.updated_date is None:
            self.updated_date = datetime.now()


@dataclass
class OEMCertification:
    """OEM certification record"""
    cert_id: str
    cert_type: CertificationType
    cert_body: str  # Certifying organization (e.g., TÜV, DNV)
    issue_date: datetime
    expiry_date: datetime
    certificate_number: str
    compliance_level: str = "COMPLIANT"  # COMPLIANT, NON_COMPLIANT, UNDER_AUDIT
    scope: str = ""  # What the certification covers
    audit_frequency_months: int = 12
    last_audit_date: Optional[datetime] = None
    next_audit_due: Optional[datetime] = None


@dataclass
class OEMTechnicalCapability:
    """OEM technical capabilities"""
    capability_id: str
    capability_type: ManufacturingCapability
    description: str
    expertise_level: str  # BASIC, INTERMEDIATE, ADVANCED, EXPERT
    experience_years: int
    equipment_list: List[str] = field(default_factory=list)
    team_size: int = 0
    recent_projects: int = 0  # Number of recent successful projects


@dataclass
class OEMLeadTime:
    """OEM lead time information"""
    lead_time_id: str
    product_category: str
    quantity_range: str  # "1-100", "100-500", "500-1000", "1000+"
    standard_lead_days: int
    expedited_lead_days: int
    expedited_cost_percent: float = 0.0  # Extra charge percentage
    express_lead_days: int = 0
    express_cost_percent: float = 0.0  # Extra charge percentage


@dataclass
class OEMQualityMetrics:
    """OEM quality performance metrics"""
    metric_id: str
    measurement_date: datetime
    defect_rate_percent: float  # PPM (parts per million) converted to %
    on_time_delivery_percent: float
    rework_rate_percent: float
    first_pass_yield_percent: float
    customer_complaints: int
    corrective_actions_open: int
    corrective_actions_closed: int
    audit_score: float  # 0-100
    quality_level: str = "ACCEPTABLE"  # EXCELLENT, GOOD, ACCEPTABLE, POOR


@dataclass
class NRECapability:
    """OEM NRE (Non-Recurring Engineering) capability"""
    nre_id: str
    description: str
    nre_cost_range_min: float
    nre_cost_range_max: float
    typical_nre_hours: int
    engineering_hourly_rate: float
    tooling_cost_typical: float
    design_review_capability: bool = True
    prototyping_capability: bool = True
    testing_capability: bool = True
    certification_support: bool = True
    design_support_languages: List[str] = field(default_factory=lambda: ["HINDI", "ENGLISH"])


@dataclass
class OEMVendorProfile:
    """Complete OEM vendor profile"""
    # Basic vendor info
    vendor_id: str
    name: str
    vendor_type: VendorType
    email: str
    phone: str
    address: str
    city: str
    state: str
    pincode: str
    country: str = "INDIA"
    
    # Registration & Compliance
    gst_number: str
    pan_number: str
    cin_number: str = ""  # Corporate Identification Number
    registration_date: datetime = None
    status: str = "ACTIVE"  # ACTIVE, INACTIVE, SUSPENDED, PROBATION
    
    # OEM-Specific Information
    manufacturing_facilities_count: int = 1
    years_in_business: int = 0
    previous_clients: List[str] = field(default_factory=list)
    
    # Products & Services
    product_categories: List[str] = field(default_factory=list)
    specialization: str = ""  # Main area of expertise
    
    # Financial Terms
    min_order_value: float = 0.0
    average_order_value: float = 0.0
    max_order_value: float = 0.0
    payment_terms: str = "Net 30"
    preferred_payment_method: str = "BANK_TRANSFER"
    
    # Manufacturing Details
    oem_capacities: List[OEMCapacity] = field(default_factory=list)
    technical_capabilities: List[OEMTechnicalCapability] = field(default_factory=list)
    lead_times: List[OEMLeadTime] = field(default_factory=list)
    nre_capability: Optional[NRECapability] = None
    
    # Certifications
    certifications: List[OEMCertification] = field(default_factory=list)
    quality_metrics: Optional[OEMQualityMetrics] = None
    
    # Delivery
    delivery_locations: List[str] = field(default_factory=list)
    logistics_partner: str = ""
    
    # Additional
    website: str = ""
    notes: str = ""
    contact_person_name: str = ""
    contact_person_designation: str = ""
    contact_person_email: str = ""
    contact_person_phone: str = ""
    
    # Metadata
    last_updated: datetime = None
    last_audit_date: Optional[datetime] = None
    risk_rating: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    
    def __post_init__(self):
        if self.registration_date is None:
            self.registration_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def get_total_capacity(self) -> int:
        """Get total monthly capacity across all products"""
        return sum(cap.monthly_capacity_units for cap in self.oem_capacities)
    
    def get_average_utilization(self) -> float:
        """Get average capacity utilization"""
        if not self.oem_capacities:
            return 0.0
        return sum(cap.current_utilization_percent for cap in self.oem_capacities) / len(self.oem_capacities)
    
    def get_certifications_summary(self) -> Dict:
        """Get summary of certifications"""
        summary = {
            'total_certifications': len(self.certifications),
            'active_certifications': 0,
            'expiring_soon': 0,
            'expired': 0,
            'by_type': {}
        }
        
        today = datetime.now()
        for cert in self.certifications:
            if cert.expiry_date < today:
                summary['expired'] += 1
            elif (cert.expiry_date - today).days < 90:
                summary['expiring_soon'] += 1
            else:
                summary['active_certifications'] += 1
            
            cert_type = cert.cert_type.value
            if cert_type not in summary['by_type']:
                summary['by_type'][cert_type] = 0
            summary['by_type'][cert_type] += 1
        
        return summary
    
    def is_certified(self, cert_type: CertificationType) -> bool:
        """Check if vendor has specific certification"""
        for cert in self.certifications:
            if cert.cert_type == cert_type and cert.expiry_date > datetime.now():
                return True
        return False
    
    def get_capability_score(self) -> float:
        """Calculate overall capability score (0-100)"""
        if not self.technical_capabilities:
            return 0.0
        
        score = 0
        weights = {
            "BASIC": 20,
            "INTERMEDIATE": 50,
            "ADVANCED": 75,
            "EXPERT": 100
        }
        
        for cap in self.technical_capabilities:
            score += weights.get(cap.expertise_level, 0)
        
        return score / len(self.technical_capabilities) if self.technical_capabilities else 0
    
    def get_oem_readiness_score(self) -> Dict:
        """Calculate OEM readiness score (0-100)"""
        score_components = {
            'capacity_score': 0,
            'certification_score': 0,
            'quality_score': 0,
            'capability_score': 0,
            'overall_score': 0
        }
        
        # Capacity Score (0-25 points)
        if self.oem_capacities:
            score_components['capacity_score'] = min(25, len(self.oem_capacities) * 5)
        
        # Certification Score (0-25 points)
        cert_count = len(self.certifications)
        score_components['certification_score'] = min(25, cert_count * 5)
        
        # Quality Score (0-25 points)
        if self.quality_metrics:
            quality_score = (self.quality_metrics.audit_score + 
                           self.quality_metrics.on_time_delivery_percent) / 2
            score_components['quality_score'] = (quality_score / 100) * 25
        
        # Capability Score (0-25 points)
        capability_pct = self.get_capability_score() / 100
        score_components['capability_score'] = capability_pct * 25
        
        # Overall Score
        score_components['overall_score'] = (
            score_components['capacity_score'] +
            score_components['certification_score'] +
            score_components['quality_score'] +
            score_components['capability_score']
        )
        
        return score_components


# Database integration helpers
def vendor_profile_to_dict(profile: OEMVendorProfile) -> Dict:
    """Convert OEM vendor profile to dictionary for storage"""
    profile_dict = asdict(profile)
    
    # Convert datetime objects to strings
    if profile_dict['registration_date']:
        profile_dict['registration_date'] = profile_dict['registration_date'].isoformat()
    if profile_dict['last_updated']:
        profile_dict['last_updated'] = profile_dict['last_updated'].isoformat()
    if profile_dict['last_audit_date']:
        profile_dict['last_audit_date'] = profile_dict['last_audit_date'].isoformat()
    
    # Convert enum values
    profile_dict['vendor_type'] = profile.vendor_type.value if isinstance(profile.vendor_type, VendorType) else profile.vendor_type
    
    # Convert nested dataclasses
    if profile_dict['oem_capacities']:
        profile_dict['oem_capacities'] = [asdict(cap) for cap in profile.oem_capacities]
    if profile_dict['technical_capabilities']:
        profile_dict['technical_capabilities'] = [asdict(cap) for cap in profile.technical_capabilities]
    if profile_dict['lead_times']:
        profile_dict['lead_times'] = [asdict(lt) for lt in profile.lead_times]
    if profile_dict['certifications']:
        profile_dict['certifications'] = [asdict(cert) for cert in profile.certifications]
    if profile_dict['nre_capability']:
        profile_dict['nre_capability'] = asdict(profile.nre_capability)
    if profile_dict['quality_metrics']:
        profile_dict['quality_metrics'] = asdict(profile.quality_metrics)
    
    return profile_dict


# Example OEM Vendor Creation
def create_sample_oem_vendor() -> OEMVendorProfile:
    """Create sample OEM vendor for testing"""
    
    vendor = OEMVendorProfile(
        vendor_id='OEM_VENDOR_001',
        name='ABC Manufacturing Ltd.',
        vendor_type=VendorType.OEM,
        email='contact@abcmfg.com',
        phone='+91-9876543210',
        address='Plot No. 123, Industrial Area',
        city='Bangalore',
        state='Karnataka',
        pincode='560001',
        gst_number='18AABCT1234G1Z0',
        pan_number='AABCT1234G',
        cin_number='U29299KA2010PTC050123',
        years_in_business=15,
        product_categories=['Wires', 'Cables', 'Connectors'],
        specialization='Electrical Wire & Cable Manufacturing',
        min_order_value=100000,
        payment_terms='Net 45'
    )
    
    # Add manufacturing capacity
    vendor.oem_capacities.append(
        OEMCapacity(
            capacity_id='CAP_001',
            product_category='Wires',
            monthly_capacity_units=5000000,
            annual_capacity_units=60000000,
            shift_count=3,
            machines_available=25,
            skilled_workers=150,
            facility_sq_ft=50000,
            current_utilization_percent=75.0,
            min_batch_size=1000,
            max_batch_size=100000
        )
    )
    
    # Add certifications
    vendor.certifications.extend([
        OEMCertification(
            cert_id='CERT_001',
            cert_type=CertificationType.ISO_9001,
            cert_body='TÜV India',
            issue_date=datetime(2023, 1, 15),
            expiry_date=datetime(2026, 1, 15),
            certificate_number='TUV-2023-001',
            compliance_level='COMPLIANT',
            scope='Design, Manufacturing, Testing'
        ),
        OEMCertification(
            cert_id='CERT_002',
            cert_type=CertificationType.RoHS,
            cert_body='DNV GL',
            issue_date=datetime(2023, 6, 1),
            expiry_date=datetime(2026, 6, 1),
            certificate_number='DNV-2023-RoHS-001',
            compliance_level='COMPLIANT'
        )
    ])
    
    # Add technical capabilities
    vendor.technical_capabilities.extend([
        OEMTechnicalCapability(
            capability_id='TC_001',
            capability_type=ManufacturingCapability.DESIGN_ENGINEERING,
            description='Custom design and engineering for wire products',
            expertise_level='ADVANCED',
            experience_years=12,
            team_size=20
        ),
        OEMTechnicalCapability(
            capability_id='TC_002',
            capability_type=ManufacturingCapability.TOOLING_DESIGN,
            description='Tooling and dies design',
            expertise_level='EXPERT',
            experience_years=15,
            team_size=10
        )
    ])
    
    # Add lead times
    vendor.lead_times.extend([
        OEMLeadTime(
            lead_time_id='LT_001',
            product_category='Wires',
            quantity_range='1000-10000',
            standard_lead_days=21,
            expedited_lead_days=14,
            expedited_cost_percent=10.0
        ),
        OEMLeadTime(
            lead_time_id='LT_002',
            product_category='Wires',
            quantity_range='10000+',
            standard_lead_days=14,
            expedited_lead_days=7,
            expedited_cost_percent=15.0
        )
    ])
    
    # Add quality metrics
    vendor.quality_metrics = OEMQualityMetrics(
        metric_id='QM_001',
        measurement_date=datetime.now(),
        defect_rate_percent=0.5,
        on_time_delivery_percent=98.5,
        rework_rate_percent=0.3,
        first_pass_yield_percent=99.2,
        customer_complaints=2,
        corrective_actions_open=1,
        corrective_actions_closed=5,
        audit_score=94.5,
        quality_level='EXCELLENT'
    )
    
    # Add NRE capability
    vendor.nre_capability = NRECapability(
        nre_id='NRE_001',
        description='Complete NRE support for custom wire products',
        nre_cost_range_min=50000,
        nre_cost_range_max=500000,
        typical_nre_hours=200,
        engineering_hourly_rate=1500,
        tooling_cost_typical=150000,
        design_review_capability=True,
        prototyping_capability=True,
        testing_capability=True,
        certification_support=True
    )
    
    return vendor
