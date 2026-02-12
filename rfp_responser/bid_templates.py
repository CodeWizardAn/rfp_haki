"""
Bid Template Manager
Manages bid document templates and formats
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class BidFormat(Enum):
    """Bid document formats"""
    STANDARD = "STANDARD"  # Standard bid with pricing
    COMPARATIVE = "COMPARATIVE"  # Multi-vendor comparison
    DETAILED = "DETAILED"  # Detailed breakdown with specs
    OEM_TECHNICAL = "OEM_TECHNICAL"  # OEM with technical specs & certifications
    OEM_MANUFACTURING = "OEM_MANUFACTURING"  # OEM with capacity & NRE


class BidStatus(Enum):
    """Bid lifecycle status"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISED = "REVISED"


@dataclass
class BidTemplate:
    """Template structure for bids"""
    template_id: str
    name: str
    description: str
    bid_format: BidFormat
    sections: List[str]
    branding_elements: Dict = None
    terms_and_conditions: str = None
    payment_terms: str = None
    delivery_terms: str = None
    # OEM-specific fields
    is_oem_template: bool = False
    include_nre: bool = False
    include_capacity: bool = False
    include_certifications: bool = False
    include_lead_times: bool = False
    include_moq: bool = False


@dataclass
class BidItem:
    """Single line item in bid"""
    item_id: str
    description: str
    product_id: str
    quantity: int
    unit: str
    unit_price: float
    tax_rate: float = 18.0  # GST default 18%
    discount_percent: float = 0.0
    # OEM-specific fields
    moq: int = 0  # Minimum Order Quantity for OEM
    lead_time_days: int = 0  # Manufacturing lead time
    nre_cost: float = 0.0  # Non-Recurring Engineering cost
    technical_spec_id: str = None  # Reference to technical spec
    
    def calculate_line_total(self) -> float:
        """Calculate total for this line item"""
        subtotal = self.quantity * self.unit_price
        discount_amount = subtotal * (self.discount_percent / 100)
        subtotal_after_discount = subtotal - discount_amount
        tax_amount = subtotal_after_discount * (self.tax_rate / 100)
        return subtotal_after_discount + tax_amount


@dataclass
class OEMCapacity:
    """OEM manufacturing capacity"""
    capacity_id: str
    product_id: str
    monthly_capacity: int  # Units per month
    shift_count: int  # Single or Multiple shifts
    equipment: List[str] = None
    facility_certification: str = None
    utilization_percent: int = 0


@dataclass
class OEMCertification:
    """OEM certifications and compliance"""
    cert_id: str
    cert_name: str  # ISO 9001, ISO 14001, etc.
    cert_body: str  # Certifying organization
    issue_date: str
    expiry_date: str
    compliance_level: str  # GOLD, SILVER, BRONZE


@dataclass
class OEMLeadTime:
    """OEM lead time information"""
    lead_time_id: str
    product_id: str
    quantity_range: str  # "100-500", "500-1000", "1000+"
    standard_lead_days: int
    expedited_lead_days: int
    expedited_cost_percent: float  # Additional cost percentage


@dataclass
class NREBreakdown:
    """Non-Recurring Engineering cost breakdown"""
    nre_id: str
    engineering_hours: int
    hourly_rate: float
    tooling_cost: float
    setup_cost: float
    testing_cost: float
    documentation_cost: float
    total_nre: float = 0.0
    
    def calculate_total(self):
        """Calculate total NRE cost"""
        self.total_nre = (self.engineering_hours * self.hourly_rate + 
                         self.tooling_cost + self.setup_cost + 
                         self.testing_cost + self.documentation_cost)
        return self.total_nre


@dataclass
class BidDocument:
    """Complete bid document"""
    bid_id: str
    rfp_id: str
    vendor_id: str
    vendor_name: str
    template_id: str
    bid_format: BidFormat
    status: BidStatus
    items: List[BidItem]
    
    # Document metadata
    issued_date: datetime = None
    valid_until_date: datetime = None
    created_by: str = None
    version: int = 1
    
    # Totals
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_cost: float = 0.0
    discount_amount: float = 0.0
    
    # Additional sections
    delivery_timeline: str = None
    payment_terms: str = None
    terms_conditions: str = None
    notes: str = None
    
    # OEM-specific fields
    oem_capacity: OEMCapacity = None
    certifications: List[OEMCertification] = None
    lead_times: List[OEMLeadTime] = None
    nre_breakdown: NREBreakdown = None
    total_nre: float = 0.0
    unit_price_after_nre: float = 0.0


class BidTemplateManager:
    """Manages bid templates"""
    
    def __init__(self):
        """Initialize template manager"""
        self.templates: Dict[str, BidTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default bid templates"""
        
        # Standard Bid Template
        standard_template = BidTemplate(
            template_id='BID_STANDARD_001',
            name='Standard Bid Format',
            description='Professional bid with pricing breakdown',
            bid_format=BidFormat.STANDARD,
            sections=[
                'Header',
                'RFP Details',
                'Line Items',
                'Pricing Summary',
                'Delivery Terms',
                'Payment Terms',
                'Terms & Conditions',
                'Authorization'
            ],
            payment_terms='Net 30 days from invoice',
            delivery_terms='FOB Destination',
            terms_and_conditions=self._get_default_terms()
        )
        self.templates['BID_STANDARD_001'] = standard_template
        
        # Comparative Bid Template
        comparative_template = BidTemplate(
            template_id='BID_COMPARATIVE_001',
            name='Comparative Analysis Format',
            description='Multi-vendor comparison format',
            bid_format=BidFormat.COMPARATIVE,
            sections=[
                'Executive Summary',
                'Vendor Comparison Table',
                'Cost Analysis',
                'Quality Metrics',
                'Delivery Schedule',
                'Risk Assessment',
                'Recommendation'
            ],
            payment_terms='Net 45 days',
            delivery_terms='As per RFP requirements'
        )
        self.templates['BID_COMPARATIVE_001'] = comparative_template
        
        # Detailed Bid Template
        detailed_template = BidTemplate(
            template_id='BID_DETAILED_001',
            name='Detailed Bid Format',
            description='Comprehensive bid with specifications and detailed breakdown',
            bid_format=BidFormat.DETAILED,
            sections=[
                'Cover Letter',
                'Executive Summary',
                'Company Profile',
                'Detailed Specifications',
                'Line Items with Details',
                'Cost Breakdown',
                'Quality Assurance',
                'Timeline & Milestones',
                'Payment Schedule',
                'Terms & Conditions',
                'Appendices'
            ],
            payment_terms='As per RFP milestone schedule',
            delivery_terms='Phased delivery as per RFP'
        )
        self.templates['BID_DETAILED_001'] = detailed_template
        
        # OEM TECHNICAL BID TEMPLATE
        oem_technical_template = BidTemplate(
            template_id='BID_OEM_TECHNICAL_001',
            name='OEM Technical Bid Format',
            description='OEM bid with technical specifications, certifications & compliance',
            bid_format=BidFormat.OEM_TECHNICAL,
            sections=[
                'Company Profile',
                'Technical Capabilities',
                'Certifications & Compliance',
                'Design & Engineering',
                'Product Specifications',
                'Quality Assurance Process',
                'Line Items & Pricing',
                'Delivery & Support',
                'Terms & Conditions'
            ],
            is_oem_template=True,
            include_certifications=True,
            payment_terms='Net 30-60 days based on volume',
            delivery_terms='FOB Factory / CIF Port'
        )
        self.templates['BID_OEM_TECHNICAL_001'] = oem_technical_template
        
        # OEM MANUFACTURING BID TEMPLATE
        oem_manufacturing_template = BidTemplate(
            template_id='BID_OEM_MANUFACTURING_001',
            name='OEM Manufacturing Bid Format',
            description='OEM bid with capacity, NRE costs, MOQ & lead times',
            bid_format=BidFormat.OEM_MANUFACTURING,
            sections=[
                'Company Overview',
                'Manufacturing Facilities',
                'Production Capacity & Timeline',
                'NRE Cost Breakdown',
                'Unit Pricing & Volume Tiers',
                'Minimum Order Quantity (MOQ)',
                'Lead Times',
                'Quality Control',
                'Regulatory Compliance',
                'Terms & Conditions'
            ],
            is_oem_template=True,
            include_nre=True,
            include_capacity=True,
            include_lead_times=True,
            include_moq=True,
            payment_terms='Initial NRE + Advance for Production + Balance on Delivery',
            delivery_terms='Partial shipments allowed as per production schedule'
        )
        self.templates['BID_OEM_MANUFACTURING_001'] = oem_manufacturing_template
    
    def _get_default_terms(self) -> str:
        """Get default terms and conditions"""
        return """
TERMS AND CONDITIONS

1. VALIDITY: This bid is valid for 30 days from the date of submission.

2. ACCEPTANCE: This bid constitutes an offer by the vendor to provide 
goods/services as specified in the RFP.

3. PAYMENT: Payment shall be made within 30 days of invoice submission, 
subject to satisfactory delivery and quality.

4. DELIVERY: All goods shall be delivered as per the specified timeline. 
Delays may result in penalties.

5. WARRANTIES: All goods come with standard manufacturer warranties. 
Extended warranty available upon request.

6. LIABILITY: In no event shall the vendor's liability exceed the total 
bid amount.

7. CONFIDENTIALITY: All information in this bid is confidential.

8. DISPUTE RESOLUTION: All disputes shall be resolved through arbitration 
as per Indian Arbitration Act, 1996.
        """
    
    def get_template(self, template_id: str) -> Optional[BidTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[BidTemplate]:
        """List all available templates"""
        return list(self.templates.values())
    
    def add_template(self, template: BidTemplate) -> bool:
        """Add custom template"""
        if template.template_id in self.templates:
            return False
        self.templates[template.template_id] = template
        return True
    
    def get_templates_by_format(self, bid_format: BidFormat) -> List[BidTemplate]:
        """Get templates by format"""
        return [t for t in self.templates.values() if t.bid_format == bid_format]


class BidBuilder:
    """Builder for creating bid documents"""
    
    def __init__(self, template_manager: BidTemplateManager):
        """Initialize bid builder"""
        self.template_manager = template_manager
        self.bid: Optional[BidDocument] = None
    
    def create_bid(
        self,
        bid_id: str,
        rfp_id: str,
        vendor_id: str,
        vendor_name: str,
        template_id: str
    ) -> 'BidBuilder':
        """Create new bid document"""
        template = self.template_manager.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        self.bid = BidDocument(
            bid_id=bid_id,
            rfp_id=rfp_id,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            template_id=template_id,
            bid_format=template.bid_format,
            status=BidStatus.DRAFT,
            items=[],
            issued_date=datetime.now(),
            valid_until_date=None
        )
        return self
    
    def add_item(
        self,
        item_id: str,
        description: str,
        product_id: str,
        quantity: int,
        unit: str,
        unit_price: float,
        tax_rate: float = 18.0,
        discount_percent: float = 0.0
    ) -> 'BidBuilder':
        """Add line item to bid"""
        if not self.bid:
            raise ValueError("Bid not created yet")
        
        item = BidItem(
            item_id=item_id,
            description=description,
            product_id=product_id,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            tax_rate=tax_rate,
            discount_percent=discount_percent
        )
        self.bid.items.append(item)
        return self
    
    def add_delivery_timeline(self, timeline: str) -> 'BidBuilder':
        """Add delivery timeline"""
        if self.bid:
            self.bid.delivery_timeline = timeline
        return self
    
    def add_payment_terms(self, terms: str) -> 'BidBuilder':
        """Add payment terms"""
        if self.bid:
            self.bid.payment_terms = terms
        return self
    
    def add_notes(self, notes: str) -> 'BidBuilder':
        """Add notes/special instructions"""
        if self.bid:
            self.bid.notes = notes
        return self
    
    def set_valid_until(self, days: int = 30) -> 'BidBuilder':
        """Set bid validity period"""
        if self.bid:
            from datetime import timedelta
            self.bid.valid_until_date = self.bid.issued_date + timedelta(days=days)
        return self
    
    def calculate_totals(self) -> 'BidBuilder':
        """Calculate bid totals"""
        if not self.bid or not self.bid.items:
            return self
        
        subtotal = 0.0
        tax_total = 0.0
        discount_total = 0.0
        
        for item in self.bid.items:
            item_subtotal = item.quantity * item.unit_price
            discount_total += item_subtotal * (item.discount_percent / 100)
            item_after_discount = item_subtotal - discount_total
            tax_total += item_after_discount * (item.tax_rate / 100)
            subtotal += item_subtotal
        
        self.bid.subtotal = subtotal
        self.bid.discount_amount = discount_total
        self.bid.tax_amount = tax_total
        self.bid.total_cost = (subtotal - discount_total) + tax_total
        
        return self
    
    def build(self) -> BidDocument:
        """Return completed bid document"""
        if not self.bid:
            raise ValueError("No bid created")
        self.calculate_totals()
        return self.bid


# Example usage
if __name__ == '__main__':
    # Initialize
    manager = BidTemplateManager()
    builder = BidBuilder(manager)
    
    # Create bid
    bid = (builder
        .create_bid(
            bid_id='BID_2026_001',
            rfp_id='RFP_2026_001',
            vendor_id='VENDOR_001',
            vendor_name='ABC Wires Ltd',
            template_id='BID_STANDARD_001'
        )
        .add_item(
            item_id='ITEM_001',
            description='1.5 sqmm 3-core PVC Wire',
            product_id='WIRE_001',
            quantity=1000,
            unit='Meter',
            unit_price=15.50,
            discount_percent=5.0
        )
        .add_item(
            item_id='ITEM_002',
            description='2.5 sqmm 3-core PVC Wire',
            product_id='WIRE_002',
            quantity=500,
            unit='Meter',
            unit_price=25.75
        )
        .add_delivery_timeline('15 days from order confirmation')
        .add_payment_terms('Net 30 days from invoice')
        .set_valid_until(30)
        .build()
    )
    
    print(f"\n✅ Bid Created: {bid.bid_id}")
    print(f"Items: {len(bid.items)}")
    print(f"Subtotal: ₹{bid.subtotal:,.2f}")
    print(f"Tax: ₹{bid.tax_amount:,.2f}")
    print(f"Total: ₹{bid.total_cost:,.2f}")
