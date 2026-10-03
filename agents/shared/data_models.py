"""
Agent Data Models
Standardized data structures for multi-agent RFP response system
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class RFPPriority(Enum):
    """Priority levels for RFP processing"""
    CRITICAL = 1      # Due within 7 days
    HIGH = 2          # Due within 14 days
    MEDIUM = 3        # Due within 30 days
    STANDARD = 4      # Due within 90 days
    LOW = 5           # Due after 90 days


class SpecMatchLevel(Enum):
    """Specification match levels"""
    FULL_MATCH = "full"           # 100% match
    EXCEEDS = "exceeds"           # OEM spec exceeds requirement
    PARTIAL_MATCH = "partial"     # >70% match
    MARGINAL = "marginal"         # 50-70% match
    NO_MATCH = "no_match"         # <50% match
    NOT_FOUND = "not_found"       # Spec not in OEM datasheet


class TestType(Enum):
    """Types of tests required"""
    ROUTINE = "routine"           # Per batch/lot
    TYPE = "type"                 # One-time per product type
    ACCEPTANCE = "acceptance"     # Final acceptance at site
    SPECIAL = "special"           # Special/additional tests


class ConstraintType(Enum):
    """Types of engineering & tender constraints"""
    HARD = "hard"                             # Absolute Pass/Fail; failure causes technical disqualification
    DIRECTIONAL_MIN = "directional_min"       # Actual >= Required (e.g. current rating, tensile strength)
    DIRECTIONAL_MAX = "directional_max"       # Actual <= Required (e.g. conductor resistance, smoke density)
    TOLERANCE_BAND = "tolerance_band"         # Must fall within +/- percentage (e.g. outer diameter +/- 5%)
    INFORMATIONAL = "informational"           # Non-blocking attribute (e.g. packaging color, drum length)


@dataclass
class SourceAttribution:
    """Enterprise verifiable citation for an extracted RFP requirement"""
    page_number: Optional[int] = None
    clause_ref: str = ""
    source_snippet: str = ""
    bounding_box: Optional[List[float]] = None  # Normalized [x0, y0, x1, y1]
    confidence_score: float = 1.0
    extraction_method: str = "layout_table"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'page_number': self.page_number,
            'clause_ref': self.clause_ref,
            'source_snippet': self.source_snippet,
            'bounding_box': self.bounding_box,
            'confidence_score': self.confidence_score,
            'extraction_method': self.extraction_method
        }


@dataclass
class RFPProduct:
    """Product in RFP scope of supply"""
    product_id: str
    product_name: str
    category: str
    quantity: float
    unit: str
    specifications: Dict[str, Any]
    mandatory_specs: List[str] = field(default_factory=list)
    preferred_specs: List[str] = field(default_factory=list)
    applicable_standards: List[str] = field(default_factory=list)
    spec_attributions: Dict[str, Any] = field(default_factory=dict)   # Spec key -> SourceAttribution or dict
    spec_constraints: Dict[str, str] = field(default_factory=dict)     # Spec key -> ConstraintType value
    notes: str = ""


@dataclass
class RFPTestRequirement:
    """Test requirement from RFP"""
    test_id: str
    test_name: str
    test_type: TestType
    applicable_products: List[str]  # Product IDs
    standard_reference: str
    parameters: List[str]
    frequency: str  # per lot, per batch, one-time
    mandatory: bool = True
    notes: str = ""


@dataclass
class RFPDocument:
    """Complete RFP document structure"""
    rfp_id: str
    rfp_number: str
    title: str
    issuing_authority: str
    issue_date: datetime
    due_date: datetime
    estimated_value: float
    currency: str = "INR"
    
    # Scope of Supply
    products: List[RFPProduct] = field(default_factory=list)
    
    # Technical Requirements
    technical_specs: Dict[str, Any] = field(default_factory=dict)
    applicable_standards: List[str] = field(default_factory=list)
    
    # Testing Requirements
    tests_required: List[RFPTestRequirement] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    
    # Submission Requirements
    submission_mode: str = ""
    emd_required: float = 0
    documents_required: List[str] = field(default_factory=list)
    
    # Source
    source_url: str = ""
    source_document_path: str = ""
    
    # Metadata
    priority: RFPPriority = RFPPriority.STANDARD
    scanned_at: datetime = field(default_factory=datetime.now)
    
    def days_until_due(self) -> int:
        """Calculate days until RFP is due"""
        return (self.due_date - datetime.now()).days
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rfp_id': self.rfp_id,
            'rfp_number': self.rfp_number,
            'title': self.title,
            'issuing_authority': self.issuing_authority,
            'issue_date': self.issue_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'estimated_value': self.estimated_value,
            'currency': self.currency,
            'products': [self._product_to_dict(p) for p in self.products],
            'tests_required': [self._test_to_dict(t) for t in self.tests_required],
            'days_until_due': self.days_until_due(),
            'priority': self.priority.name
        }
    
    def _product_to_dict(self, p: RFPProduct) -> Dict:
        return {
            'product_id': p.product_id,
            'product_name': p.product_name,
            'category': p.category,
            'quantity': p.quantity,
            'unit': p.unit,
            'specifications': p.specifications,
            'mandatory_specs': p.mandatory_specs,
            'applicable_standards': p.applicable_standards,
            'spec_attributions': {
                k: (v.to_dict() if hasattr(v, 'to_dict') else v)
                for k, v in getattr(p, 'spec_attributions', {}).items()
            },
            'spec_constraints': getattr(p, 'spec_constraints', {})
        }
    
    def _test_to_dict(self, t: RFPTestRequirement) -> Dict:
        return {
            'test_id': t.test_id,
            'test_name': t.test_name,
            'test_type': t.test_type.value,
            'applicable_products': t.applicable_products,
            'standard_reference': t.standard_reference,
            'mandatory': t.mandatory
        }


@dataclass
class OEMProductMatch:
    """OEM product match result with enterprise constraint checking and citations"""
    rank: int
    sku: str
    product_name: str
    manufacturer: str
    category: str
    spec_match_percent: float
    specifications: Dict[str, Any]
    certifications: List[str]
    matched_specs: Dict[str, Dict[str, Any]]
    unmatched_specs: List[str]
    compliance_notes: List[str]
    hard_constraint_passed: bool = True
    hard_constraint_violations: List[Dict[str, Any]] = field(default_factory=list)
    disqualification_risk: str = "LOW"  # "LOW", "MEDIUM", "CRITICAL_DISQUALIFIED"
    citations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ProductRecommendationResult:
    """Recommendation result for a single RFP product"""
    rfp_product_id: str
    rfp_product_name: str
    rfp_specifications: Dict[str, Any]
    quantity: float
    unit: str
    
    # Top 3 OEM recommendations
    top_3_recommendations: List[OEMProductMatch] = field(default_factory=list)
    
    # Selected best match
    selected_sku: str = ""
    selected_product_name: str = ""
    selected_manufacturer: str = ""
    selected_spec_match: float = 0.0
    hard_constraint_passed: bool = True
    hard_constraint_violations: List[Dict[str, Any]] = field(default_factory=list)
    disqualification_risk: str = "LOW"
    citations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Comparison table (RFP spec vs OEM 1, 2, 3)
    comparison_table: List[Dict[str, Any]] = field(default_factory=list)
    
    # Gap analysis
    specification_gaps: List[str] = field(default_factory=list)
    compliance_risks: List[str] = field(default_factory=list)


@dataclass
class TechnicalAgentResponse:
    """Complete response from Technical Agent"""
    rfp_id: str
    processed_date: datetime
    
    # Product recommendations
    recommendations: List[ProductRecommendationResult] = field(default_factory=list)
    
    # Final scope of supply table
    scope_of_supply_table: List[Dict[str, Any]] = field(default_factory=list)
    
    # Overall compliance
    overall_compliance_percent: float = 0.0
    compliance_summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rfp_id': self.rfp_id,
            'processed_date': self.processed_date.isoformat(),
            'recommendations': [
                {
                    'rfp_product_id': r.rfp_product_id,
                    'rfp_product_name': r.rfp_product_name,
                    'quantity': r.quantity,
                    'unit': r.unit,
                    'selected_sku': r.selected_sku,
                    'selected_product_name': r.selected_product_name,
                    'selected_manufacturer': r.selected_manufacturer,
                    'spec_match_percent': r.selected_spec_match,
                    'hard_constraint_passed': r.hard_constraint_passed,
                    'disqualification_risk': r.disqualification_risk,
                    'hard_constraint_violations': r.hard_constraint_violations,
                    'citations': r.citations,
                    'top_3_options': [
                        {
                            'rank': m.rank,
                            'sku': m.sku,
                            'product_name': m.product_name,
                            'manufacturer': m.manufacturer,
                            'spec_match_percent': m.spec_match_percent,
                            'hard_constraint_passed': m.hard_constraint_passed,
                            'disqualification_risk': m.disqualification_risk
                        }
                        for m in r.top_3_recommendations
                    ],
                    'comparison_table': r.comparison_table
                }
                for r in self.recommendations
            ],
            'scope_of_supply_table': self.scope_of_supply_table,
            'overall_compliance_percent': self.overall_compliance_percent
        }


@dataclass
class ProductPricing:
    """Pricing for a single product"""
    product_id: str
    rfp_product_name: str
    oem_sku: str
    oem_product_name: str
    manufacturer: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    bulk_discount_applied: float = 0.0
    notes: str = ""


@dataclass
class TestPricing:
    """Pricing for a test/service"""
    test_id: str
    test_name: str
    test_type: str
    applicable_products: List[str]
    unit_price: float
    quantity: int = 1
    total_price: float = 0.0
    standard_reference: str = ""
    turnaround_days: int = 7


@dataclass
class PricingAgentResponse:
    """Complete response from Pricing Agent"""
    rfp_id: str
    calculated_date: datetime
    
    # Product pricing
    product_prices: List[ProductPricing] = field(default_factory=list)
    total_material_cost: float = 0.0
    
    # Test/Service pricing
    test_prices: List[TestPricing] = field(default_factory=list)
    total_services_cost: float = 0.0
    
    # Taxes and totals
    gst_percent: float = 18.0
    gst_amount: float = 0.0
    grand_total: float = 0.0
    
    # Summary
    pricing_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rfp_id': self.rfp_id,
            'calculated_date': self.calculated_date.isoformat(),
            'product_prices': [
                {
                    'product_id': p.product_id,
                    'rfp_product_name': p.rfp_product_name,
                    'oem_sku': p.oem_sku,
                    'oem_product_name': p.oem_product_name,
                    'manufacturer': p.manufacturer,
                    'quantity': p.quantity,
                    'unit': p.unit,
                    'unit_price': p.unit_price,
                    'total_price': p.total_price
                }
                for p in self.product_prices
            ],
            'total_material_cost': self.total_material_cost,
            'test_prices': [
                {
                    'test_id': t.test_id,
                    'test_name': t.test_name,
                    'test_type': t.test_type,
                    'unit_price': t.unit_price,
                    'total_price': t.total_price
                }
                for t in self.test_prices
            ],
            'total_services_cost': self.total_services_cost,
            'gst_percent': self.gst_percent,
            'gst_amount': self.gst_amount,
            'grand_total': self.grand_total
        }


@dataclass
class ConsolidatedRFPResponse:
    """Final consolidated RFP response from Master Agent"""
    # Response Identification
    response_id: str
    rfp_id: str
    rfp_title: str
    generated_date: datetime
    
    # RFP Summary
    issuing_authority: str
    due_date: datetime
    estimated_value: float
    
    # Scope of Supply with OEM Mapping
    scope_of_supply: List[Dict[str, Any]] = field(default_factory=list)
    # Each item: {rfp_product, quantity, unit, oem_sku, oem_product, manufacturer, spec_match%, unit_price, total_price}
    
    # Test Requirements with Pricing
    test_requirements: List[Dict[str, Any]] = field(default_factory=list)
    # Each item: {test_name, test_type, applicable_products, unit_price, total_price}
    
    # Financial Summary
    total_material_cost: float = 0.0
    total_services_cost: float = 0.0
    subtotal: float = 0.0
    gst_amount: float = 0.0
    grand_total: float = 0.0
    
    # Compliance Summary
    overall_spec_match: float = 0.0
    compliance_status: str = "PENDING"
    compliance_notes: List[str] = field(default_factory=list)
    
    # Recommendation
    recommendation: str = ""
    risks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'response_id': self.response_id,
            'rfp_id': self.rfp_id,
            'rfp_title': self.rfp_title,
            'generated_date': self.generated_date.isoformat(),
            'issuing_authority': self.issuing_authority,
            'due_date': self.due_date.isoformat(),
            'estimated_value': self.estimated_value,
            'scope_of_supply': self.scope_of_supply,
            'test_requirements': self.test_requirements,
            'financial_summary': {
                'total_material_cost': self.total_material_cost,
                'total_services_cost': self.total_services_cost,
                'subtotal': self.subtotal,
                'gst_amount': self.gst_amount,
                'grand_total': self.grand_total
            },
            'compliance': {
                'overall_spec_match': self.overall_spec_match,
                'status': self.compliance_status,
                'notes': self.compliance_notes
            },
            'recommendation': self.recommendation,
            'risks': self.risks
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)
