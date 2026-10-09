"""
Pricing Agent - Comprehensive Commercial Pricing System
Receives technical recommendations, calculates all costs, applies margins,
and generates commercial bid documents.

Features (51 total):
1. PricingAgent class structure
2. Product list receiver
3. Price lookup integration
4. Quantity aggregation
5. Unit price calculator
6. Volume discount applier
7. Test requirement parser
8. Test cost calculator
9. Test frequency analyzer
10. Sample testing cost
11. Type test cost allocator
12. Routine test cost calculator
13. Acceptance test cost
14. Certification cost adder
15. Logistics cost calculator
16. Transportation cost by distance
17. Insurance cost calculator
18. Packaging cost adder
19. Handling charges
20. Customs/duties calculator
21. Subtotal aggregator
22. Contingency buffer
23. Margin calculator
24. Final price generator
25. Competitive analysis
26. Pricing recommendation engine
27. Price optimization
28. Win probability estimator
29. Pricing breakdown generator
30. Commercial terms formatter
31. Payment terms generator
32. Pricing table creator
33. Cost comparison generator
34. Sensitivity analysis
35. What-if scenario generator
36. Pricing summary
37. Detailed line-item breakdown
38. Pricing validation
39. Pricing approval workflow
40. Pricing history tracker
41. Pricing analytics
42. Pricing agent logging
43. Error handling
44. Pricing agent tests (separate file)
45. Mock data handlers
46. Integration tests (separate file)
47. Pricing agent metrics
48. Pricing agent dashboard
49. Real-time updates
50. Pricing agent documentation
51. API interface
"""

import sys
import json
import logging
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from enum import Enum
from threading import Lock
import re
import math
import uuid

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import database config
try:
    from database.db_config import DatabaseConfig, DatabaseType
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

try:
    from price_optimization import LandedCostCalculator
    LANDED_CALCULATOR_AVAILABLE = True
except ImportError:
    LANDED_CALCULATOR_AVAILABLE = False


# ============================================================================
# Enums
# ============================================================================

class ApprovalStatus(Enum):
    """Pricing approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class PriceConfidence(Enum):
    """Confidence level for pricing"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ESTIMATED = "estimated"


class CostCategory(Enum):
    """Cost categories"""
    MATERIAL = "material"
    TESTING = "testing"
    CERTIFICATION = "certification"
    LOGISTICS = "logistics"
    OVERHEAD = "overhead"
    CONTINGENCY = "contingency"
    MARGIN = "margin"


class TestType(Enum):
    """Types of tests"""
    TYPE_TEST = "type_test"
    ROUTINE_TEST = "routine_test"
    ACCEPTANCE_TEST = "acceptance_test"
    SAMPLE_TEST = "sample_test"
    SPECIAL_TEST = "special_test"


class TransportMode(Enum):
    """Transportation modes"""
    ROAD = "road"
    RAIL = "rail"
    AIR = "air"
    SEA = "sea"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ProductPriceEntry:
    """Product price entry"""
    sku: str
    product_name: str
    manufacturer: str
    base_price: float
    currency: str = "INR"
    unit: str = "unit"
    moq: int = 1
    lead_time_days: int = 7
    price_valid_until: Optional[str] = None
    discount_tiers: Dict[int, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCostEntry:
    """Test cost entry"""
    test_id: str
    test_name: str
    test_type: TestType
    base_cost: float
    samples_required: int = 1
    turnaround_days: int = 7
    lab_name: str = ""
    standard_reference: str = ""
    currency: str = "INR"
    frequency: str = "per_lot"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LineItem:
    """Individual line item in pricing"""
    item_id: str
    description: str
    category: CostCategory
    quantity: float
    unit: str
    unit_price: float
    discount_percent: float = 0
    net_unit_price: float = 0
    total_price: float = 0
    confidence: PriceConfidence = PriceConfidence.HIGH
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PricingBreakdown:
    """Complete pricing breakdown"""
    breakdown_id: str
    rfp_id: str
    created_at: datetime
    material_costs: List[LineItem]
    testing_costs: List[LineItem]
    certification_costs: List[LineItem]
    logistics_costs: List[LineItem]
    overhead_costs: List[LineItem]
    subtotals: Dict[str, float]
    contingency: float
    margin: float
    taxes: Dict[str, float]
    grand_total: float
    currency: str = "INR"


@dataclass
class CommercialTerms:
    """Commercial terms for bid"""
    payment_terms: str
    delivery_terms: str
    warranty_period: str
    validity_period: str
    price_escalation_clause: str
    penalties: List[str]
    exclusions: List[str]
    special_conditions: List[str]


@dataclass 
class PricingApproval:
    """Pricing approval record"""
    approval_id: str
    pricing_id: str
    rfp_id: str
    status: ApprovalStatus
    requested_by: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    comments: str = ""
    revision_notes: str = ""


@dataclass
class AgentMessage:
    """Message for inter-agent communication"""
    id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 5


# ============================================================================
# Feature 42: Pricing Agent Logging
# ============================================================================

class PricingAgentLogger:
    """Centralized logging for Pricing Agent"""
    
    def __init__(self, agent_id: str, log_dir: Optional[str] = None):
        self.agent_id = agent_id
        self.log_dir = Path(log_dir) if log_dir else Path("logs/pricing_agent")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger(f"pricing_agent.{agent_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


# ============================================================================
# Feature 2: Product List Receiver
# ============================================================================

class ProductListReceiver:
    """Receives product recommendations from Technical Agent"""
    
    def __init__(self):
        self.received_products: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def receive(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Receive product list from Technical Agent"""
        products = []
        
        recommendations = message.get('recommendations', [])
        for rec in recommendations:
            product = {
                'requirement_id': rec.get('requirement_id', ''),
                'rfp_product_name': rec.get('rfp_product_name', ''),
                'selected_sku': rec.get('product_id', rec.get('selected_sku', '')),
                'product_name': rec.get('product_name', ''),
                'manufacturer': rec.get('manufacturer', ''),
                'quantity': rec.get('quantity', 1),
                'unit': rec.get('unit', 'units'),
                'match_score': rec.get('match_score', 0),
                'specifications': rec.get('specifications', {}),
                'alternatives': rec.get('alternatives', [])
            }
            products.append(product)
        
        self.received_products = products
        self.logger.info(f"Received {len(products)} product recommendations")
        return products
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get received products"""
        return self.received_products


# ============================================================================
# Feature 3: Price Lookup Integration
# ============================================================================

class PriceLookupIntegration:
    """Integrates with price database for lookups"""
    
    def __init__(self):
        self.price_table: Dict[str, ProductPriceEntry] = {}
        self.logger = logging.getLogger(__name__)
        self._load_prices()
    
    def _load_prices(self):
        """Load prices from database"""
        if not DB_AVAILABLE:
            self.logger.warning("Database not available, using empty price table")
            return
        
        try:
            db_path = DatabaseConfig.get_path(DatabaseType.PRODUCT_PRICES)
            if db_path.exists():
                with open(db_path, 'r') as f:
                    data = json.load(f)
                
                for product in data.get('products', []):
                    if product.get('active', True):
                        self.price_table[product['sku']] = ProductPriceEntry(
                            sku=product['sku'],
                            product_name=product['product_name'],
                            manufacturer=product.get('manufacturer', ''),
                            base_price=product['unit_price'],
                            moq=product.get('moq', 1),
                            lead_time_days=product.get('lead_time_days', 7),
                            discount_tiers=product.get('discount_tiers', {})
                        )
                self.logger.info(f"Loaded {len(self.price_table)} product prices")
        except Exception as e:
            self.logger.error(f"Error loading prices: {e}")
    
    def lookup(self, sku: str) -> Optional[ProductPriceEntry]:
        """Lookup price by SKU"""
        return self.price_table.get(sku)
    
    def lookup_by_name(self, product_name: str) -> Optional[ProductPriceEntry]:
        """Lookup price by product name (fuzzy)"""
        name_lower = product_name.lower()
        for entry in self.price_table.values():
            if name_lower in entry.product_name.lower():
                return entry
        return None
    
    def get_all_prices(self) -> Dict[str, ProductPriceEntry]:
        """Get all price entries"""
        return self.price_table


# ============================================================================
# Feature 4: Quantity Aggregation
# ============================================================================

class QuantityAggregator:
    """Aggregates quantities across products"""
    
    def __init__(self):
        self.aggregated: Dict[str, Dict[str, Any]] = {}
    
    def aggregate(self, products: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Aggregate quantities by SKU"""
        self.aggregated = {}
        
        for product in products:
            sku = product.get('selected_sku', '')
            if not sku:
                continue
            
            if sku in self.aggregated:
                self.aggregated[sku]['total_quantity'] += product.get('quantity', 0)
                self.aggregated[sku]['requirements'].append(product.get('requirement_id', ''))
            else:
                self.aggregated[sku] = {
                    'sku': sku,
                    'product_name': product.get('product_name', ''),
                    'manufacturer': product.get('manufacturer', ''),
                    'total_quantity': product.get('quantity', 0),
                    'unit': product.get('unit', 'units'),
                    'requirements': [product.get('requirement_id', '')]
                }
        
        return self.aggregated
    
    def get_total_quantity(self, sku: str) -> float:
        """Get total quantity for a SKU"""
        return self.aggregated.get(sku, {}).get('total_quantity', 0)


# ============================================================================
# Feature 5: Unit Price Calculator
# ============================================================================

class UnitPriceCalculator:
    """Calculates unit prices with various factors"""
    
    def __init__(self, price_lookup: PriceLookupIntegration):
        self.price_lookup = price_lookup
        self.markup_percent = 0  # Base markup
        self.currency = "INR"
        self.landed_calc = LandedCostCalculator() if LANDED_CALCULATOR_AVAILABLE else None
    
    def _estimate_landed_price(self, sku: str, quantity: float = 1, product_details: Optional[Dict[str, Any]] = None) -> Tuple[float, Optional[Dict[str, Any]]]:
        """Dynamically compute unit cost via physical specifications and commodity rates"""
        text = f"{sku} {(product_details or {}).get('product_name', '')}".lower()
        
        # Conductor size
        m_size = re.search(r'(\d+(?:\.\d+)?)\s*(?:sq\.?mm|sqmm)', text)
        size_sqmm = float(m_size.group(1)) if m_size else 4.0
        
        # Number of cores
        m_cores = re.search(r'(\d+)\s*c(?:ore)?', text)
        cores = int(m_cores.group(1)) if m_cores else 3
        
        # Material
        mat = 'aluminium' if any(w in text for w in ['al', 'aluminium', 'aluminum']) else 'copper'
        insulation = 'XLPE' if 'xlpe' in text else 'PVC'
        is_armoured = 'armour' in text or 'armored' in text
        
        if self.landed_calc:
            try:
                res = self.landed_calc.calculate_turnkey_landed_cost(
                    conductor_size_sqmm=size_sqmm,
                    no_of_cores=cores,
                    material=mat,
                    insulation=insulation,
                    is_armoured=is_armoured,
                    quantity_meters=max(1.0, float(quantity))
                )
                return res['unit_costs']['landed_unit_price_inclusive_gst'], res
            except Exception:
                pass
        
        # Physics fallback
        density = 8.89 if mat == 'copper' else 2.70
        rate = 880.0 if mat == 'copper' else 235.0
        conductor_wt = (size_sqmm * cores * 1.05 * density) / 1000.0
        return max(35.0, round((conductor_wt * rate + 40.0) * 1.18, 2)), None

    def calculate(self, sku: str, quantity: float = 1, product_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate unit price for a SKU"""
        price_entry = self.price_lookup.lookup(sku)
        cost_breakdown = None
        
        if price_entry:
            base_price = price_entry.base_price
            confidence = PriceConfidence.HIGH
        else:
            # Estimate price dynamically using engineering/commodity calculation
            base_price, cost_breakdown = self._estimate_landed_price(sku, quantity, product_details)
            confidence = PriceConfidence.ESTIMATED
        
        # Apply markup
        final_price = base_price * (1 + self.markup_percent / 100)
        
        result = {
            'sku': sku,
            'base_price': base_price,
            'markup_percent': self.markup_percent,
            'unit_price': round(final_price, 2),
            'currency': self.currency,
            'confidence': confidence.value,
            'price_found': price_entry is not None
        }
        if cost_breakdown:
            result['cost_breakdown'] = cost_breakdown
        return result
    
    def set_markup(self, percent: float):
        """Set base markup percentage"""
        self.markup_percent = percent


# ============================================================================
# Feature 6: Volume Discount Applier
# ============================================================================

class VolumeDiscountApplier:
    """Applies volume-based discounts"""
    
    def __init__(self):
        # Default discount tiers (quantity -> discount %)
        self.default_tiers = {
            100: 2.0,
            500: 5.0,
            1000: 8.0,
            5000: 10.0,
            10000: 12.0,
            50000: 15.0
        }
    
    def apply(self, unit_price: float, quantity: float, 
              custom_tiers: Optional[Dict[int, float]] = None) -> Dict[str, Any]:
        """Apply volume discount"""
        tiers = custom_tiers or self.default_tiers
        
        # Find applicable discount
        discount_percent = 0
        for tier_qty, tier_discount in sorted(tiers.items()):
            if quantity >= tier_qty:
                discount_percent = tier_discount
        
        discounted_price = unit_price * (1 - discount_percent / 100)
        total_discount = (unit_price - discounted_price) * quantity
        
        return {
            'original_unit_price': unit_price,
            'discount_percent': discount_percent,
            'discounted_unit_price': round(discounted_price, 2),
            'quantity': quantity,
            'total_before_discount': round(unit_price * quantity, 2),
            'total_discount': round(total_discount, 2),
            'total_after_discount': round(discounted_price * quantity, 2)
        }


# ============================================================================
# Feature 7: Test Requirement Parser
# ============================================================================

class TestRequirementParser:
    """Parses test requirements from RFP"""
    
    def __init__(self):
        self.test_patterns = {
            'type_test': [
                r'type\s*test', r'type\s*approval', r'initial\s*test',
                r'qualification\s*test', r'certification\s*test'
            ],
            'routine_test': [
                r'routine\s*test', r'production\s*test', r'batch\s*test',
                r'lot\s*test', r'regular\s*test'
            ],
            'acceptance_test': [
                r'acceptance\s*test', r'fat', r'site\s*test',
                r'commissioning\s*test', r'customer\s*witness'
            ],
            'sample_test': [
                r'sample\s*test', r'sampling', r'random\s*test'
            ]
        }
    
    def parse(self, test_requirements: List[str]) -> List[Dict[str, Any]]:
        """Parse test requirements and categorize"""
        parsed = []
        
        for req in test_requirements:
            req_lower = req.lower()
            
            # Determine test type
            test_type = self._detect_test_type(req_lower)
            
            # Extract test name
            test_name = self._clean_test_name(req)
            
            # Extract standard reference
            standard = self._extract_standard(req)
            
            parsed.append({
                'original_requirement': req,
                'test_name': test_name,
                'test_type': test_type.value,
                'standard_reference': standard,
                'parsed': True
            })
        
        return parsed
    
    def _detect_test_type(self, text: str) -> TestType:
        """Detect test type from text"""
        for test_type, patterns in self.test_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return TestType(test_type)
        return TestType.ROUTINE_TEST
    
    def _clean_test_name(self, text: str) -> str:
        """Clean and standardize test name"""
        # Remove common prefixes
        text = re.sub(r'^(as per|per|ref\.?|reference)\s+', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _extract_standard(self, text: str) -> str:
        """Extract standard reference (IS, IEC, etc.)"""
        patterns = [
            r'(IS\s*\d+[-:]\d+)',
            r'(IEC\s*\d+[-:]\d+)',
            r'(IEEE\s*\d+)',
            r'(ASTM\s*[A-Z]?\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""


# ============================================================================
# Feature 8: Test Cost Calculator
# ============================================================================

class TestCostCalculator:
    """Calculates costs for various tests"""
    
    def __init__(self):
        self.test_costs: Dict[str, TestCostEntry] = {}
        self._load_test_costs()
    
    def _load_test_costs(self):
        """Load test costs from database"""
        if not DB_AVAILABLE:
            return
        
        try:
            db_path = DatabaseConfig.get_path(DatabaseType.SERVICE_PRICES)
            if db_path.exists():
                with open(db_path, 'r') as f:
                    data = json.load(f)
                
                for service in data.get('services', []):
                    test_type = TestType.ROUTINE_TEST
                    category = service.get('category', '').upper()
                    if 'TYPE' in category:
                        test_type = TestType.TYPE_TEST
                    elif 'ACCEPTANCE' in category:
                        test_type = TestType.ACCEPTANCE_TEST
                    
                    self.test_costs[service['service_id']] = TestCostEntry(
                        test_id=service['service_id'],
                        test_name=service['service_name'],
                        test_type=test_type,
                        base_cost=service['price'],
                        samples_required=service.get('samples_required', 1),
                        turnaround_days=service.get('turnaround_days', 7),
                        standard_reference=service.get('standard', '')
                    )
        except Exception as e:
            logging.error(f"Error loading test costs: {e}")
    
    def calculate(self, test_name: str, test_type: TestType,
                  samples: int = 1) -> Dict[str, Any]:
        """Calculate cost for a test"""
        # Try to find matching test
        matching_entry = self._find_matching_test(test_name)
        
        if matching_entry:
            base_cost = matching_entry.base_cost
            confidence = PriceConfidence.HIGH
        else:
            # Estimate based on test type
            base_cost = self._estimate_cost(test_type)
            confidence = PriceConfidence.ESTIMATED
        
        total_cost = base_cost * samples
        
        return {
            'test_name': test_name,
            'test_type': test_type.value,
            'base_cost': base_cost,
            'samples': samples,
            'total_cost': round(total_cost, 2),
            'confidence': confidence.value,
            'matched': matching_entry is not None
        }
    
    def _find_matching_test(self, test_name: str) -> Optional[TestCostEntry]:
        """Find matching test in cost table"""
        name_lower = test_name.lower()
        
        for entry in self.test_costs.values():
            if name_lower in entry.test_name.lower():
                return entry
        
        return None
    
    def _estimate_cost(self, test_type: TestType) -> float:
        """Estimate cost based on test type"""
        estimates = {
            TestType.TYPE_TEST: 25000.0,
            TestType.ROUTINE_TEST: 5000.0,
            TestType.ACCEPTANCE_TEST: 15000.0,
            TestType.SAMPLE_TEST: 3000.0,
            TestType.SPECIAL_TEST: 20000.0
        }
        return estimates.get(test_type, 10000.0)


# ============================================================================
# Feature 9: Test Frequency Analyzer
# ============================================================================

class TestFrequencyAnalyzer:
    """Analyzes test frequency requirements"""
    
    def __init__(self):
        self.frequency_patterns = {
            'per_lot': ['per lot', 'each lot', 'every lot', 'per batch'],
            'per_order': ['per order', 'per consignment', 'per shipment'],
            'one_time': ['one time', 'once', 'initial', 'type test'],
            'periodic': ['periodic', 'quarterly', 'monthly', 'annual']
        }
    
    def analyze(self, test_requirement: str, quantity: float,
                lot_size: float = 1000) -> Dict[str, Any]:
        """Analyze test frequency"""
        freq = self._detect_frequency(test_requirement)
        
        # Calculate number of tests required
        if freq == 'per_lot':
            num_lots = math.ceil(quantity / lot_size)
            test_count = num_lots
        elif freq == 'per_order':
            test_count = 1
        elif freq == 'one_time':
            test_count = 1
        else:
            test_count = 1
        
        return {
            'test_requirement': test_requirement,
            'frequency': freq,
            'quantity': quantity,
            'lot_size': lot_size,
            'test_count': test_count,
            'explanation': self._get_explanation(freq, test_count)
        }
    
    def _detect_frequency(self, text: str) -> str:
        """Detect frequency from text"""
        text_lower = text.lower()
        
        for freq, patterns in self.frequency_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return freq
        
        return 'per_lot'  # Default
    
    def _get_explanation(self, freq: str, count: int) -> str:
        """Get explanation for frequency"""
        if freq == 'per_lot':
            return f"Test required for each lot ({count} lots)"
        elif freq == 'per_order':
            return "Test required once per order"
        elif freq == 'one_time':
            return "One-time test (type test/certification)"
        else:
            return f"Test count: {count}"


# ============================================================================
# Features 10-13: Sample, Type, Routine, Acceptance Test Cost Calculators
# ============================================================================

class SampleTestingCost:
    """Calculates sample testing costs"""
    
    def __init__(self, test_calculator: TestCostCalculator):
        self.test_calculator = test_calculator
    
    def calculate(self, tests: List[str], samples_per_test: int = 3) -> Dict[str, Any]:
        """Calculate sample testing costs"""
        costs = []
        total = 0
        
        for test in tests:
            result = self.test_calculator.calculate(
                test, TestType.SAMPLE_TEST, samples_per_test
            )
            costs.append(result)
            total += result['total_cost']
        
        return {
            'test_type': 'sample_testing',
            'tests': costs,
            'samples_per_test': samples_per_test,
            'total_cost': round(total, 2)
        }


class TypeTestCostAllocator:
    """Allocates type test costs across order"""
    
    def __init__(self, test_calculator: TestCostCalculator):
        self.test_calculator = test_calculator
    
    def allocate(self, tests: List[str], total_quantity: float,
                 allocation_method: str = 'per_unit') -> Dict[str, Any]:
        """Allocate type test costs"""
        costs = []
        total = 0
        
        for test in tests:
            result = self.test_calculator.calculate(test, TestType.TYPE_TEST, 1)
            costs.append(result)
            total += result['total_cost']
        
        # Calculate per-unit allocation
        if allocation_method == 'per_unit' and total_quantity > 0:
            per_unit = total / total_quantity
        else:
            per_unit = 0
        
        return {
            'test_type': 'type_test',
            'tests': costs,
            'total_cost': round(total, 2),
            'allocation_method': allocation_method,
            'total_quantity': total_quantity,
            'cost_per_unit': round(per_unit, 4)
        }


class RoutineTestCostCalculator:
    """Calculates routine test costs"""
    
    def __init__(self, test_calculator: TestCostCalculator):
        self.test_calculator = test_calculator
        self.frequency_analyzer = TestFrequencyAnalyzer()
    
    def calculate(self, tests: List[str], quantity: float,
                  lot_size: float = 1000) -> Dict[str, Any]:
        """Calculate routine test costs"""
        costs = []
        total = 0
        
        for test in tests:
            # Analyze frequency
            freq = self.frequency_analyzer.analyze(test, quantity, lot_size)
            test_count = freq['test_count']
            
            # Calculate cost
            result = self.test_calculator.calculate(
                test, TestType.ROUTINE_TEST, test_count
            )
            result['frequency'] = freq['frequency']
            result['test_count'] = test_count
            
            costs.append(result)
            total += result['total_cost']
        
        return {
            'test_type': 'routine_test',
            'tests': costs,
            'quantity': quantity,
            'lot_size': lot_size,
            'total_cost': round(total, 2)
        }


class AcceptanceTestCost:
    """Calculates acceptance test costs"""
    
    def __init__(self, test_calculator: TestCostCalculator):
        self.test_calculator = test_calculator
    
    def calculate(self, tests: List[str], witness_required: bool = True) -> Dict[str, Any]:
        """Calculate acceptance test costs"""
        costs = []
        total = 0
        
        for test in tests:
            result = self.test_calculator.calculate(test, TestType.ACCEPTANCE_TEST, 1)
            costs.append(result)
            total += result['total_cost']
        
        # Add witness charges if required
        witness_cost = 0
        if witness_required:
            witness_cost = 15000.0  # Standard witness charge
            total += witness_cost
        
        return {
            'test_type': 'acceptance_test',
            'tests': costs,
            'witness_required': witness_required,
            'witness_cost': witness_cost,
            'total_cost': round(total, 2)
        }


# ============================================================================
# Feature 14: Certification Cost Adder
# ============================================================================

class CertificationCostAdder:
    """Adds certification costs"""
    
    def __init__(self):
        self.certification_costs = {
            'BIS': 50000.0,
            'ISI': 45000.0,
            'CE': 75000.0,
            'UL': 100000.0,
            'ISO': 35000.0,
            'NABL': 25000.0,
            'TPI': 15000.0
        }
    
    def calculate(self, certifications_required: List[str]) -> Dict[str, Any]:
        """Calculate certification costs"""
        costs = []
        total = 0
        
        for cert in certifications_required:
            cert_upper = cert.upper()
            
            # Find matching certification
            cost = 0
            matched = False
            for key, value in self.certification_costs.items():
                if key in cert_upper:
                    cost = value
                    matched = True
                    break
            
            if not matched:
                cost = 30000.0  # Default estimate
            
            costs.append({
                'certification': cert,
                'cost': cost,
                'matched': matched
            })
            total += cost
        
        return {
            'certifications': costs,
            'total_cost': round(total, 2)
        }


# ============================================================================
# Features 15-20: Logistics, Transportation, Insurance, Packaging, Handling, Customs
# ============================================================================

class LogisticsCostCalculator:
    """Calculates overall logistics costs"""
    
    def __init__(self):
        self.transport_calc = TransportationCostCalculator()
        self.insurance_calc = InsuranceCostCalculator()
        self.packaging_calc = PackagingCostAdder()
        self.handling_calc = HandlingChargesCalculator()
        self.customs_calc = CustomsDutiesCalculator()
    
    def calculate(self, material_value: float, weight_kg: float,
                  distance_km: float, destination: str = 'domestic',
                  transport_mode: TransportMode = TransportMode.ROAD) -> Dict[str, Any]:
        """Calculate all logistics costs"""
        # Transportation
        transport = self.transport_calc.calculate(weight_kg, distance_km, transport_mode)
        
        # Insurance
        insurance = self.insurance_calc.calculate(material_value, destination)
        
        # Packaging
        packaging = self.packaging_calc.calculate(weight_kg)
        
        # Handling
        handling = self.handling_calc.calculate(weight_kg)
        
        # Customs (if international)
        customs = {'total_cost': 0}
        if destination.lower() in ['international', 'export']:
            customs = self.customs_calc.calculate(material_value, destination)
        
        total = (transport['total_cost'] + insurance['total_cost'] +
                 packaging['total_cost'] + handling['total_cost'] +
                 customs['total_cost'])
        
        return {
            'transportation': transport,
            'insurance': insurance,
            'packaging': packaging,
            'handling': handling,
            'customs': customs,
            'total_logistics_cost': round(total, 2)
        }


class TransportationCostCalculator:
    """Calculates transportation costs by distance"""
    
    def __init__(self):
        # Cost per kg per km for different modes
        self.rates = {
            TransportMode.ROAD: 0.05,
            TransportMode.RAIL: 0.03,
            TransportMode.AIR: 0.50,
            TransportMode.SEA: 0.02
        }
        self.minimum_charge = 500.0
    
    def calculate(self, weight_kg: float, distance_km: float,
                  mode: TransportMode = TransportMode.ROAD) -> Dict[str, Any]:
        """Calculate transportation cost"""
        rate = self.rates.get(mode, 0.05)
        calculated_cost = weight_kg * distance_km * rate
        
        # Apply minimum charge
        cost = max(calculated_cost, self.minimum_charge)
        
        return {
            'mode': mode.value,
            'weight_kg': weight_kg,
            'distance_km': distance_km,
            'rate_per_kg_km': rate,
            'calculated_cost': round(calculated_cost, 2),
            'minimum_charge': self.minimum_charge,
            'total_cost': round(cost, 2)
        }


class InsuranceCostCalculator:
    """Calculates insurance costs"""
    
    def __init__(self):
        self.domestic_rate = 0.002  # 0.2% of value
        self.international_rate = 0.005  # 0.5% of value
        self.minimum_premium = 500.0
    
    def calculate(self, material_value: float, destination: str = 'domestic') -> Dict[str, Any]:
        """Calculate insurance cost"""
        if destination.lower() in ['international', 'export']:
            rate = self.international_rate
        else:
            rate = self.domestic_rate
        
        premium = material_value * rate
        premium = max(premium, self.minimum_premium)
        
        return {
            'material_value': material_value,
            'destination': destination,
            'rate': rate * 100,  # As percentage
            'minimum_premium': self.minimum_premium,
            'total_cost': round(premium, 2)
        }


class PackagingCostAdder:
    """Adds packaging costs"""
    
    def __init__(self):
        self.cost_per_kg = 5.0
        self.minimum_cost = 200.0
    
    def calculate(self, weight_kg: float) -> Dict[str, Any]:
        """Calculate packaging cost"""
        cost = max(weight_kg * self.cost_per_kg, self.minimum_cost)
        
        return {
            'weight_kg': weight_kg,
            'cost_per_kg': self.cost_per_kg,
            'minimum_cost': self.minimum_cost,
            'total_cost': round(cost, 2)
        }


class HandlingChargesCalculator:
    """Calculates handling charges"""
    
    def __init__(self):
        self.base_charge = 500.0
        self.per_kg_charge = 2.0
    
    def calculate(self, weight_kg: float) -> Dict[str, Any]:
        """Calculate handling charges"""
        cost = self.base_charge + (weight_kg * self.per_kg_charge)
        
        return {
            'weight_kg': weight_kg,
            'base_charge': self.base_charge,
            'per_kg_charge': self.per_kg_charge,
            'total_cost': round(cost, 2)
        }


class CustomsDutiesCalculator:
    """Calculates customs and duties"""
    
    def __init__(self):
        self.duty_rates = {
            'default': 0.10,  # 10% import duty
            'electrical': 0.075,
            'cables': 0.08
        }
        self.igst_rate = 0.18  # 18% IGST
    
    def calculate(self, material_value: float, product_type: str = 'default') -> Dict[str, Any]:
        """Calculate customs duties"""
        # Get duty rate
        duty_rate = self.duty_rates.get(product_type.lower(), self.duty_rates['default'])
        
        # Basic customs duty
        bcd = material_value * duty_rate
        
        # Assessable value
        assessable_value = material_value + bcd
        
        # IGST on assessable value
        igst = assessable_value * self.igst_rate
        
        total = bcd + igst
        
        return {
            'material_value': material_value,
            'product_type': product_type,
            'duty_rate': duty_rate * 100,
            'basic_customs_duty': round(bcd, 2),
            'assessable_value': round(assessable_value, 2),
            'igst_rate': self.igst_rate * 100,
            'igst': round(igst, 2),
            'total_cost': round(total, 2)
        }


# ============================================================================
# Features 21-24: Subtotal, Contingency, Margin, Final Price
# ============================================================================

class SubtotalAggregator:
    """Aggregates subtotals from all cost categories"""
    
    def aggregate(self, costs: Dict[str, float]) -> Dict[str, Any]:
        """Aggregate all costs into subtotals"""
        # Material costs
        material = costs.get('material', 0)
        
        # Testing costs
        testing = (costs.get('sample_testing', 0) + 
                   costs.get('type_testing', 0) +
                   costs.get('routine_testing', 0) +
                   costs.get('acceptance_testing', 0))
        
        # Certification
        certification = costs.get('certification', 0)
        
        # Logistics
        logistics = costs.get('logistics', 0)
        
        # Calculate subtotals
        gross_total = material + testing + certification + logistics
        
        return {
            'material_subtotal': round(material, 2),
            'testing_subtotal': round(testing, 2),
            'certification_subtotal': round(certification, 2),
            'logistics_subtotal': round(logistics, 2),
            'gross_total': round(gross_total, 2),
            'cost_breakdown': {
                'material_percent': round((material / gross_total) * 100, 1) if gross_total > 0 else 0,
                'testing_percent': round((testing / gross_total) * 100, 1) if gross_total > 0 else 0,
                'certification_percent': round((certification / gross_total) * 100, 1) if gross_total > 0 else 0,
                'logistics_percent': round((logistics / gross_total) * 100, 1) if gross_total > 0 else 0
            }
        }


class ContingencyBuffer:
    """Adds contingency buffer to pricing"""
    
    def __init__(self, default_percent: float = 5.0):
        self.default_percent = default_percent
    
    def calculate(self, subtotal: float, percent: Optional[float] = None,
                  risk_factors: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculate contingency buffer"""
        base_percent = percent or self.default_percent
        
        # Adjust for risk factors
        if risk_factors:
            for factor in risk_factors:
                if 'high' in factor.lower():
                    base_percent += 2.0
                elif 'volatile' in factor.lower():
                    base_percent += 1.5
        
        contingency = subtotal * (base_percent / 100)
        
        return {
            'subtotal': subtotal,
            'contingency_percent': round(base_percent, 2),
            'contingency_amount': round(contingency, 2),
            'risk_factors': risk_factors or [],
            'total_with_contingency': round(subtotal + contingency, 2)
        }


class MarginCalculator:
    """Calculates margin on pricing"""
    
    def __init__(self, default_margin: float = 15.0):
        self.default_margin = default_margin
        self.min_margin = 5.0
        self.max_margin = 35.0
    
    def calculate(self, cost: float, target_margin: Optional[float] = None,
                  competitive_factor: float = 1.0) -> Dict[str, Any]:
        """Calculate margin"""
        margin_percent = target_margin or self.default_margin
        
        # Adjust for competitive factor
        margin_percent *= competitive_factor
        
        # Clamp to min/max
        margin_percent = max(self.min_margin, min(margin_percent, self.max_margin))
        
        margin_amount = cost * (margin_percent / 100)
        selling_price = cost + margin_amount
        
        return {
            'cost': cost,
            'margin_percent': round(margin_percent, 2),
            'margin_amount': round(margin_amount, 2),
            'selling_price': round(selling_price, 2),
            'competitive_factor': competitive_factor
        }


class FinalPriceGenerator:
    """Generates final price with taxes"""
    
    def __init__(self):
        self.gst_rate = 18.0  # Default GST rate
    
    def generate(self, selling_price: float, gst_rate: Optional[float] = None,
                 include_gst: bool = True) -> Dict[str, Any]:
        """Generate final price"""
        rate = gst_rate or self.gst_rate
        
        if include_gst:
            gst_amount = selling_price * (rate / 100)
            final_price = selling_price + gst_amount
        else:
            gst_amount = 0
            final_price = selling_price
        
        return {
            'selling_price': round(selling_price, 2),
            'gst_rate': rate,
            'gst_amount': round(gst_amount, 2),
            'include_gst': include_gst,
            'final_price': round(final_price, 2),
            'currency': 'INR'
        }


# ============================================================================
# Features 25-28: Competitive Analysis, Recommendations, Optimization, Win Probability
# ============================================================================

class CompetitiveAnalysis:
    """Analyzes pricing competitiveness"""
    
    def __init__(self):
        self.market_data: Dict[str, Dict[str, float]] = {}
    
    def analyze(self, our_price: float, product_category: str,
                competitor_prices: Optional[List[float]] = None) -> Dict[str, Any]:
        """Analyze competitive position"""
        # Use provided prices or estimates
        if competitor_prices:
            comp_prices = competitor_prices
        else:
            # Estimate based on category
            comp_prices = self._estimate_competitor_prices(our_price, product_category)
        
        if not comp_prices:
            return {'status': 'no_data', 'our_price': our_price}
        
        avg_competitor = sum(comp_prices) / len(comp_prices)
        min_competitor = min(comp_prices)
        max_competitor = max(comp_prices)
        
        # Calculate position
        if our_price < min_competitor:
            position = 'lowest'
            competitiveness = 'highly_competitive'
        elif our_price < avg_competitor:
            position = 'below_average'
            competitiveness = 'competitive'
        elif our_price < max_competitor:
            position = 'above_average'
            competitiveness = 'moderate'
        else:
            position = 'highest'
            competitiveness = 'low'
        
        price_index = (our_price / avg_competitor) * 100 if avg_competitor > 0 else 100
        
        return {
            'our_price': our_price,
            'competitor_prices': comp_prices,
            'average_competitor_price': round(avg_competitor, 2),
            'min_competitor_price': round(min_competitor, 2),
            'max_competitor_price': round(max_competitor, 2),
            'position': position,
            'competitiveness': competitiveness,
            'price_index': round(price_index, 1),
            'gap_to_lowest': round(our_price - min_competitor, 2)
        }
    
    def _estimate_competitor_prices(self, our_price: float, category: str) -> List[float]:
        """Estimate competitor prices based on market knowledge"""
        # Simplified estimation
        return [our_price * 0.95, our_price * 1.05, our_price * 1.10]


class PricingRecommendationEngine:
    """Generates pricing recommendations"""
    
    def __init__(self):
        self.competitive_analysis = CompetitiveAnalysis()
    
    def recommend(self, cost: float, current_margin: float,
                  competitive_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate pricing recommendations"""
        recommendations = []
        
        # Base price at current margin
        base_price = cost * (1 + current_margin / 100)
        
        # Aggressive (lower margin)
        aggressive_margin = max(5, current_margin - 5)
        aggressive_price = cost * (1 + aggressive_margin / 100)
        recommendations.append({
            'strategy': 'aggressive',
            'margin_percent': aggressive_margin,
            'price': round(aggressive_price, 2),
            'description': 'Lower margin for competitive advantage'
        })
        
        # Standard
        recommendations.append({
            'strategy': 'standard',
            'margin_percent': current_margin,
            'price': round(base_price, 2),
            'description': 'Standard margin pricing'
        })
        
        # Premium (higher margin)
        premium_margin = min(35, current_margin + 5)
        premium_price = cost * (1 + premium_margin / 100)
        recommendations.append({
            'strategy': 'premium',
            'margin_percent': premium_margin,
            'price': round(premium_price, 2),
            'description': 'Higher margin for quality positioning'
        })
        
        # Value-based (if competitive data available)
        if competitive_data:
            avg_comp = competitive_data.get('average_competitor_price', base_price)
            value_price = avg_comp * 0.98  # Slightly below average
            value_margin = ((value_price / cost) - 1) * 100 if cost > 0 else 0
            recommendations.append({
                'strategy': 'value_based',
                'margin_percent': round(value_margin, 2),
                'price': round(value_price, 2),
                'description': 'Priced to match market value'
            })
        
        return {
            'cost': cost,
            'current_margin': current_margin,
            'recommendations': recommendations,
            'recommended_strategy': 'standard'
        }


class PriceOptimization:
    """Optimizes pricing for objectives"""
    
    def optimize(self, cost: float, min_margin: float = 5.0,
                 max_margin: float = 25.0, objective: str = 'profit',
                 constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize price for given objective"""
        constraints = constraints or {}
        
        # Max price constraint
        max_price = constraints.get('max_price', cost * (1 + max_margin / 100))
        
        # Target win rate
        target_win_rate = constraints.get('target_win_rate', 0.5)
        
        if objective == 'profit':
            # Maximize margin
            optimal_margin = max_margin
            optimal_price = min(cost * (1 + optimal_margin / 100), max_price)
        elif objective == 'volume':
            # Lower margin for higher volume
            optimal_margin = min_margin + 2
            optimal_price = cost * (1 + optimal_margin / 100)
        elif objective == 'balanced':
            # Middle ground
            optimal_margin = (min_margin + max_margin) / 2
            optimal_price = cost * (1 + optimal_margin / 100)
        else:
            optimal_margin = 15.0
            optimal_price = cost * (1 + optimal_margin / 100)
        
        actual_margin = ((optimal_price / cost) - 1) * 100 if cost > 0 else 0
        
        return {
            'cost': cost,
            'objective': objective,
            'min_margin': min_margin,
            'max_margin': max_margin,
            'optimal_price': round(optimal_price, 2),
            'optimal_margin': round(actual_margin, 2),
            'constraints_applied': list(constraints.keys())
        }


class WinProbabilityEstimator:
    """Estimates probability of winning bid"""
    
    def estimate(self, our_price: float, estimated_competitor_avg: float,
                 quality_score: float = 0.8,
                 relationship_score: float = 0.5) -> Dict[str, Any]:
        """Estimate win probability"""
        # Price competitiveness (0 to 1)
        if estimated_competitor_avg > 0:
            price_ratio = our_price / estimated_competitor_avg
            if price_ratio <= 0.9:
                price_score = 1.0
            elif price_ratio <= 1.0:
                price_score = 1.0 - (price_ratio - 0.9) * 2
            elif price_ratio <= 1.1:
                price_score = 0.8 - (price_ratio - 1.0) * 4
            else:
                price_score = max(0.2, 0.4 - (price_ratio - 1.1) * 2)
        else:
            price_score = 0.5
        
        # Weighted probability
        weights = {'price': 0.5, 'quality': 0.35, 'relationship': 0.15}
        
        probability = (
            weights['price'] * price_score +
            weights['quality'] * quality_score +
            weights['relationship'] * relationship_score
        )
        
        # Determine confidence
        if probability >= 0.7:
            confidence = 'high'
        elif probability >= 0.5:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'our_price': our_price,
            'competitor_avg': estimated_competitor_avg,
            'price_score': round(price_score, 3),
            'quality_score': quality_score,
            'relationship_score': relationship_score,
            'win_probability': round(probability, 3),
            'win_probability_percent': round(probability * 100, 1),
            'confidence': confidence,
            'recommendation': 'proceed' if probability >= 0.4 else 'review_pricing'
        }


# ============================================================================
# Features 29-33: Breakdown, Terms, Payment, Tables, Comparison
# ============================================================================

class PricingBreakdownGenerator:
    """Generates detailed pricing breakdown"""
    
    def generate(self, pricing_data: Dict[str, Any]) -> PricingBreakdown:
        """Generate complete pricing breakdown"""
        breakdown_id = f"BRK_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Convert to line items
        material_items = self._create_line_items(
            pricing_data.get('products', []), CostCategory.MATERIAL
        )
        
        testing_items = self._create_line_items(
            pricing_data.get('tests', []), CostCategory.TESTING
        )
        
        certification_items = self._create_line_items(
            pricing_data.get('certifications', []), CostCategory.CERTIFICATION
        )
        
        logistics_items = self._create_line_items(
            pricing_data.get('logistics', []), CostCategory.LOGISTICS
        )
        
        # Calculate subtotals
        subtotals = {
            'material': sum(item.total_price for item in material_items),
            'testing': sum(item.total_price for item in testing_items),
            'certification': sum(item.total_price for item in certification_items),
            'logistics': sum(item.total_price for item in logistics_items)
        }
        
        return PricingBreakdown(
            breakdown_id=breakdown_id,
            rfp_id=pricing_data.get('rfp_id', ''),
            created_at=datetime.now(),
            material_costs=material_items,
            testing_costs=testing_items,
            certification_costs=certification_items,
            logistics_costs=logistics_items,
            overhead_costs=[],
            subtotals=subtotals,
            contingency=pricing_data.get('contingency', 0),
            margin=pricing_data.get('margin', 0),
            taxes=pricing_data.get('taxes', {}),
            grand_total=pricing_data.get('grand_total', 0)
        )
    
    def _create_line_items(self, items: List[Dict[str, Any]], 
                           category: CostCategory) -> List[LineItem]:
        """Create line items from data"""
        line_items = []
        
        for i, item in enumerate(items):
            line_items.append(LineItem(
                item_id=item.get('id', f"{category.value}_{i+1}"),
                description=item.get('name', item.get('description', '')),
                category=category,
                quantity=item.get('quantity', 1),
                unit=item.get('unit', 'unit'),
                unit_price=item.get('unit_price', item.get('cost', 0)),
                discount_percent=item.get('discount', 0),
                net_unit_price=item.get('net_price', item.get('unit_price', 0)),
                total_price=item.get('total', item.get('total_cost', 0))
            ))
        
        return line_items


class CommercialTermsFormatter:
    """Formats commercial terms for bid"""
    
    def format(self, terms_config: Optional[Dict[str, Any]] = None) -> CommercialTerms:
        """Format commercial terms"""
        config = terms_config or {}
        
        return CommercialTerms(
            payment_terms=config.get('payment_terms', '30% advance, 70% on delivery'),
            delivery_terms=config.get('delivery_terms', 'Ex-works, delivery to site extra'),
            warranty_period=config.get('warranty_period', '12 months from commissioning or 18 months from dispatch'),
            validity_period=config.get('validity_period', '30 days from quote date'),
            price_escalation_clause=config.get('escalation', 'Prices subject to revision for orders beyond validity'),
            penalties=[
                'Delay penalty: 0.5% per week, max 5%',
                'Performance guarantee: As per RFP terms'
            ],
            exclusions=[
                'Taxes as applicable',
                'Site preparation by customer',
                'Civil works not included'
            ],
            special_conditions=config.get('special_conditions', [])
        )


class PaymentTermsGenerator:
    """Generates payment terms options"""
    
    def generate(self, order_value: float, customer_type: str = 'government') -> Dict[str, Any]:
        """Generate payment terms"""
        terms_options = []
        
        if customer_type == 'government':
            terms_options = [
                {
                    'option': 'standard_govt',
                    'description': '100% payment within 30 days of delivery',
                    'advance': 0,
                    'on_delivery': 100,
                    'credit_days': 30
                },
                {
                    'option': 'partial_advance',
                    'description': '10% advance, 90% on delivery',
                    'advance': 10,
                    'on_delivery': 90,
                    'credit_days': 30
                }
            ]
        else:
            terms_options = [
                {
                    'option': 'standard',
                    'description': '30% advance, 70% on delivery',
                    'advance': 30,
                    'on_delivery': 70,
                    'credit_days': 0
                },
                {
                    'option': 'milestone',
                    'description': '30% advance, 40% on dispatch, 30% on delivery',
                    'advance': 30,
                    'mid_payment': 40,
                    'on_delivery': 30,
                    'credit_days': 0
                },
                {
                    'option': 'credit',
                    'description': '100% payment with 30 days credit',
                    'advance': 0,
                    'on_delivery': 100,
                    'credit_days': 30
                }
            ]
        
        return {
            'order_value': order_value,
            'customer_type': customer_type,
            'recommended': terms_options[0]['option'],
            'options': terms_options
        }


class PricingTableCreator:
    """Creates formatted pricing tables"""
    
    def create(self, breakdown: PricingBreakdown) -> Dict[str, Any]:
        """Create pricing table"""
        rows = []
        
        # Material costs
        for item in breakdown.material_costs:
            rows.append({
                'sl_no': len(rows) + 1,
                'category': 'Material',
                'description': item.description,
                'quantity': item.quantity,
                'unit': item.unit,
                'unit_rate': item.unit_price,
                'discount': f"{item.discount_percent}%",
                'net_rate': item.net_unit_price,
                'amount': item.total_price
            })
        
        # Testing costs
        for item in breakdown.testing_costs:
            rows.append({
                'sl_no': len(rows) + 1,
                'category': 'Testing',
                'description': item.description,
                'quantity': item.quantity,
                'unit': 'test',
                'unit_rate': item.unit_price,
                'discount': '-',
                'net_rate': item.unit_price,
                'amount': item.total_price
            })
        
        # Certification costs
        for item in breakdown.certification_costs:
            rows.append({
                'sl_no': len(rows) + 1,
                'category': 'Certification',
                'description': item.description,
                'quantity': 1,
                'unit': 'LS',
                'unit_rate': item.total_price,
                'discount': '-',
                'net_rate': item.total_price,
                'amount': item.total_price
            })
        
        # Logistics
        for item in breakdown.logistics_costs:
            rows.append({
                'sl_no': len(rows) + 1,
                'category': 'Logistics',
                'description': item.description,
                'quantity': 1,
                'unit': 'LS',
                'unit_rate': item.total_price,
                'discount': '-',
                'net_rate': item.total_price,
                'amount': item.total_price
            })
        
        return {
            'headers': ['Sl.No', 'Category', 'Description', 'Qty', 'Unit', 
                       'Unit Rate', 'Discount', 'Net Rate', 'Amount'],
            'rows': rows,
            'subtotals': breakdown.subtotals,
            'contingency': breakdown.contingency,
            'margin': breakdown.margin,
            'taxes': breakdown.taxes,
            'grand_total': breakdown.grand_total
        }


class CostComparisonGenerator:
    """Generates cost comparisons"""
    
    def generate(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate cost comparison across scenarios"""
        if not scenarios:
            return {'comparison': [], 'summary': {}}
        
        comparison = []
        for scenario in scenarios:
            comparison.append({
                'scenario_name': scenario.get('name', ''),
                'material_cost': scenario.get('material', 0),
                'testing_cost': scenario.get('testing', 0),
                'logistics_cost': scenario.get('logistics', 0),
                'margin': scenario.get('margin', 0),
                'total': scenario.get('total', 0)
            })
        
        # Find best scenario
        min_total = min(s.get('total', float('inf')) for s in scenarios)
        max_total = max(s.get('total', 0) for s in scenarios)
        
        return {
            'comparison': comparison,
            'summary': {
                'lowest_price': min_total,
                'highest_price': max_total,
                'price_range': round(max_total - min_total, 2),
                'scenario_count': len(scenarios)
            }
        }


# ============================================================================
# Features 34-37: Sensitivity, What-if, Summary, Line-item Breakdown
# ============================================================================

class SensitivityAnalysis:
    """Performs sensitivity analysis on pricing"""
    
    def analyze(self, base_cost: float, base_margin: float,
                variables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze price sensitivity to variables"""
        variables = variables or ['material_cost', 'margin', 'logistics']
        
        base_price = base_cost * (1 + base_margin / 100)
        results = []
        
        for var in variables:
            # Test -10%, -5%, +5%, +10% changes
            variations = []
            for change in [-10, -5, 0, 5, 10]:
                if var == 'margin':
                    new_margin = base_margin + change
                    new_price = base_cost * (1 + new_margin / 100)
                else:
                    new_cost = base_cost * (1 + change / 100)
                    new_price = new_cost * (1 + base_margin / 100)
                
                variations.append({
                    'change_percent': change,
                    'new_price': round(new_price, 2),
                    'price_impact': round(new_price - base_price, 2),
                    'price_impact_percent': round(((new_price - base_price) / base_price) * 100, 2)
                })
            
            results.append({
                'variable': var,
                'variations': variations
            })
        
        return {
            'base_cost': base_cost,
            'base_margin': base_margin,
            'base_price': round(base_price, 2),
            'sensitivity_results': results
        }


class WhatIfScenarioGenerator:
    """Generates what-if scenarios"""
    
    def generate(self, base_pricing: Dict[str, Any],
                 scenarios: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Generate what-if scenarios"""
        if scenarios:
            return self._apply_custom_scenarios(base_pricing, scenarios)
        
        # Generate default scenarios
        base_total = base_pricing.get('grand_total', 0)
        base_margin = base_pricing.get('margin_percent', 15)
        
        results = []
        
        # Scenario 1: Lower margin
        results.append({
            'scenario': 'aggressive_pricing',
            'description': 'Reduce margin to 10%',
            'margin_percent': 10,
            'estimated_total': round(base_total * 0.95, 2),
            'price_impact': round(base_total * -0.05, 2),
            'win_probability_change': '+15%'
        })
        
        # Scenario 2: Volume discount
        results.append({
            'scenario': 'volume_discount',
            'description': 'Apply 5% volume discount',
            'discount_percent': 5,
            'estimated_total': round(base_total * 0.95, 2),
            'price_impact': round(base_total * -0.05, 2),
            'win_probability_change': '+10%'
        })
        
        # Scenario 3: Premium pricing
        results.append({
            'scenario': 'premium_positioning',
            'description': 'Premium brand with higher margin',
            'margin_percent': 25,
            'estimated_total': round(base_total * 1.10, 2),
            'price_impact': round(base_total * 0.10, 2),
            'win_probability_change': '-20%'
        })
        
        return results
    
    def _apply_custom_scenarios(self, base_pricing: Dict[str, Any],
                                 scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply custom scenarios"""
        results = []
        base_total = base_pricing.get('grand_total', 0)
        
        for scenario in scenarios:
            multiplier = 1 + (scenario.get('adjustment_percent', 0) / 100)
            results.append({
                'scenario': scenario.get('name', 'custom'),
                'description': scenario.get('description', ''),
                'adjustment_percent': scenario.get('adjustment_percent', 0),
                'estimated_total': round(base_total * multiplier, 2)
            })
        
        return results


class PricingSummaryGenerator:
    """Generates pricing summary"""
    
    def generate(self, breakdown: PricingBreakdown) -> str:
        """Generate markdown summary"""
        lines = [
            "# Pricing Summary",
            "",
            f"**RFP ID:** {breakdown.rfp_id}",
            f"**Date:** {breakdown.created_at.strftime('%Y-%m-%d')}",
            f"**Breakdown ID:** {breakdown.breakdown_id}",
            "",
            "## Cost Summary",
            "",
            "| Category | Amount (INR) |",
            "|----------|-------------|",
            f"| Materials | {breakdown.subtotals.get('material', 0):,.2f} |",
            f"| Testing | {breakdown.subtotals.get('testing', 0):,.2f} |",
            f"| Certification | {breakdown.subtotals.get('certification', 0):,.2f} |",
            f"| Logistics | {breakdown.subtotals.get('logistics', 0):,.2f} |",
            f"| **Subtotal** | **{sum(breakdown.subtotals.values()):,.2f}** |",
            f"| Contingency | {breakdown.contingency:,.2f} |",
            f"| Margin | {breakdown.margin:,.2f} |",
            f"| GST | {breakdown.taxes.get('gst', 0):,.2f} |",
            f"| **Grand Total** | **{breakdown.grand_total:,.2f}** |",
            ""
        ]
        
        return "\n".join(lines)


class DetailedLineItemBreakdown:
    """Creates detailed line-item breakdown"""
    
    def create(self, breakdown: PricingBreakdown) -> Dict[str, Any]:
        """Create detailed line-item breakdown"""
        all_items = []
        
        # Add all categories
        for item in breakdown.material_costs:
            all_items.append(self._item_to_dict(item, 'Material'))
        
        for item in breakdown.testing_costs:
            all_items.append(self._item_to_dict(item, 'Testing'))
        
        for item in breakdown.certification_costs:
            all_items.append(self._item_to_dict(item, 'Certification'))
        
        for item in breakdown.logistics_costs:
            all_items.append(self._item_to_dict(item, 'Logistics'))
        
        # Add summary items
        subtotal = sum(breakdown.subtotals.values())
        
        summary_items = [
            {'description': 'Subtotal', 'amount': subtotal},
            {'description': 'Contingency', 'amount': breakdown.contingency},
            {'description': 'Margin', 'amount': breakdown.margin},
            {'description': 'GST', 'amount': breakdown.taxes.get('gst', 0)},
            {'description': 'Grand Total', 'amount': breakdown.grand_total}
        ]
        
        return {
            'line_items': all_items,
            'summary': summary_items,
            'item_count': len(all_items)
        }
    
    def _item_to_dict(self, item: LineItem, category: str) -> Dict[str, Any]:
        """Convert line item to dictionary"""
        return {
            'id': item.item_id,
            'category': category,
            'description': item.description,
            'quantity': item.quantity,
            'unit': item.unit,
            'unit_price': item.unit_price,
            'discount': item.discount_percent,
            'net_price': item.net_unit_price,
            'total': item.total_price,
            'confidence': item.confidence.value
        }


# ============================================================================
# Features 38-41: Validation, Approval, History, Analytics
# ============================================================================

class PricingValidator:
    """Validates pricing data"""
    
    def validate(self, pricing: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pricing"""
        errors = []
        warnings = []
        
        # Check required fields
        required = ['rfp_id', 'grand_total']
        for field in required:
            if field not in pricing:
                errors.append(f"Missing required field: {field}")
        
        # Validate grand total
        grand_total = pricing.get('grand_total', 0)
        if grand_total <= 0:
            errors.append("Grand total must be positive")
        
        # Check margin
        margin = pricing.get('margin_percent', 0)
        if margin < 5:
            warnings.append("Margin below 5% - review required")
        elif margin > 30:
            warnings.append("Margin above 30% - may not be competitive")
        
        # Check for missing prices
        products = pricing.get('products', [])
        estimated_count = sum(1 for p in products if p.get('estimated', False))
        if estimated_count > 0:
            warnings.append(f"{estimated_count} product(s) have estimated prices")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'checks_passed': len(required) - len(errors),
            'total_checks': len(required)
        }


class PricingApprovalWorkflow:
    """Manages pricing approval workflow"""
    
    def __init__(self):
        self.approvals: Dict[str, PricingApproval] = {}
        self.approval_thresholds = {
            'auto_approve': 100000,  # Auto-approve below this
            'manager_approve': 1000000,  # Manager approval up to this
            'director_approve': 10000000  # Director approval up to this
        }
    
    def submit_for_approval(self, pricing_id: str, rfp_id: str,
                           grand_total: float, requester: str) -> PricingApproval:
        """Submit pricing for approval"""
        approval_id = f"APR_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determine approval level
        if grand_total < self.approval_thresholds['auto_approve']:
            status = ApprovalStatus.APPROVED
            approved_by = 'SYSTEM_AUTO'
            approved_at = datetime.now()
        else:
            status = ApprovalStatus.PENDING
            approved_by = None
            approved_at = None
        
        approval = PricingApproval(
            approval_id=approval_id,
            pricing_id=pricing_id,
            rfp_id=rfp_id,
            status=status,
            requested_by=requester,
            requested_at=datetime.now(),
            approved_by=approved_by,
            approved_at=approved_at
        )
        
        self.approvals[approval_id] = approval
        return approval
    
    def approve(self, approval_id: str, approver: str, 
                comments: str = "") -> PricingApproval:
        """Approve pricing"""
        if approval_id not in self.approvals:
            raise ValueError(f"Approval not found: {approval_id}")
        
        approval = self.approvals[approval_id]
        approval.status = ApprovalStatus.APPROVED
        approval.approved_by = approver
        approval.approved_at = datetime.now()
        approval.comments = comments
        
        return approval
    
    def reject(self, approval_id: str, approver: str,
               reason: str) -> PricingApproval:
        """Reject pricing"""
        if approval_id not in self.approvals:
            raise ValueError(f"Approval not found: {approval_id}")
        
        approval = self.approvals[approval_id]
        approval.status = ApprovalStatus.REJECTED
        approval.approved_by = approver
        approval.approved_at = datetime.now()
        approval.comments = reason
        
        return approval
    
    def get_status(self, approval_id: str) -> Optional[ApprovalStatus]:
        """Get approval status"""
        approval = self.approvals.get(approval_id)
        return approval.status if approval else None


class PricingHistoryTracker:
    """Tracks pricing history"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
    
    def record(self, event_type: str, pricing_id: str,
               data: Dict[str, Any]) -> str:
        """Record pricing event"""
        event_id = f"EVT_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'pricing_id': pricing_id,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        self.history.append(event)
        return event_id
    
    def get_history(self, pricing_id: str) -> List[Dict[str, Any]]:
        """Get history for a pricing"""
        return [e for e in self.history if e['pricing_id'] == pricing_id]
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events"""
        return self.history[-limit:]


class PricingAnalytics:
    """Provides pricing analytics"""
    
    def __init__(self):
        self.pricing_data: List[Dict[str, Any]] = []
    
    def add_data(self, pricing: Dict[str, Any]):
        """Add pricing data for analytics"""
        self.pricing_data.append({
            'rfp_id': pricing.get('rfp_id'),
            'grand_total': pricing.get('grand_total', 0),
            'margin_percent': pricing.get('margin_percent', 0),
            'timestamp': datetime.now().isoformat(),
            'won': pricing.get('won', None)
        })
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get pricing analytics"""
        if not self.pricing_data:
            return {'status': 'no_data'}
        
        totals = [p['grand_total'] for p in self.pricing_data]
        margins = [p['margin_percent'] for p in self.pricing_data if p['margin_percent']]
        
        won = [p for p in self.pricing_data if p.get('won') is True]
        lost = [p for p in self.pricing_data if p.get('won') is False]
        
        return {
            'total_quotes': len(self.pricing_data),
            'average_quote_value': round(sum(totals) / len(totals), 2) if totals else 0,
            'min_quote_value': min(totals) if totals else 0,
            'max_quote_value': max(totals) if totals else 0,
            'average_margin': round(sum(margins) / len(margins), 2) if margins else 0,
            'win_count': len(won),
            'loss_count': len(lost),
            'win_rate': round(len(won) / (len(won) + len(lost)) * 100, 1) if (won or lost) else 0
        }


# ============================================================================
# Features 43, 45-49: Error Handling, Mocks, Metrics, Dashboard, Real-time
# ============================================================================

class PricingErrorHandler:
    """Handles errors in pricing operations"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.errors: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def with_retry(self, operation: Callable, operation_name: str) -> Tuple[bool, Any]:
        """Execute operation with retry"""
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                result = operation()
                return True, result
            except Exception as e:
                last_error = e
                self.logger.warning(f"{operation_name} attempt {attempt} failed: {e}")
                self._record_error(operation_name, str(e), attempt)
        
        return False, None
    
    def _record_error(self, operation: str, error: str, attempt: int):
        """Record error"""
        self.errors.append({
            'operation': operation,
            'error': error,
            'attempt': attempt,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Get recorded errors"""
        return self.errors


class MockDataHandler:
    """Handles mock data for testing"""
    
    @staticmethod
    def get_mock_products() -> List[Dict[str, Any]]:
        """Get mock product list"""
        return [
            {
                'requirement_id': 'REQ_001',
                'selected_sku': 'SKU_WIRE_001',
                'product_name': 'PVC Copper Wire 1.5 sqmm',
                'manufacturer': 'Polycab',
                'quantity': 5000,
                'unit': 'meters'
            },
            {
                'requirement_id': 'REQ_002',
                'selected_sku': 'SKU_CABLE_001',
                'product_name': 'XLPE Power Cable 4 sqmm',
                'manufacturer': 'KEI',
                'quantity': 2000,
                'unit': 'meters'
            }
        ]
    
    @staticmethod
    def get_mock_tests() -> List[str]:
        """Get mock test requirements"""
        return [
            'Conductor Resistance Test',
            'Insulation Resistance Test',
            'High Voltage Test',
            'Flame Retardancy Test per IEC 60332'
        ]
    
    @staticmethod
    def get_mock_pricing_input() -> Dict[str, Any]:
        """Get complete mock pricing input"""
        return {
            'rfp_id': 'RFP_MOCK_001',
            'recommendations': MockDataHandler.get_mock_products(),
            'tests_required': MockDataHandler.get_mock_tests(),
            'certifications': ['BIS', 'ISI'],
            'delivery_location': 'Mumbai',
            'distance_km': 500
        }


class PricingMetrics:
    """Tracks pricing agent metrics"""
    
    def __init__(self):
        self.metrics = {
            'total_quotes': 0,
            'total_value': 0,
            'processing_times': [],
            'errors': 0,
            'approvals': 0,
            'rejections': 0
        }
        self._lock = Lock()
    
    def record_quote(self, value: float, processing_time: float):
        """Record a quote"""
        with self._lock:
            self.metrics['total_quotes'] += 1
            self.metrics['total_value'] += value
            self.metrics['processing_times'].append(processing_time)
    
    def record_error(self):
        """Record an error"""
        with self._lock:
            self.metrics['errors'] += 1
    
    def record_approval(self, approved: bool):
        """Record approval decision"""
        with self._lock:
            if approved:
                self.metrics['approvals'] += 1
            else:
                self.metrics['rejections'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get metrics stats"""
        times = self.metrics['processing_times']
        
        return {
            'total_quotes': self.metrics['total_quotes'],
            'total_value': round(self.metrics['total_value'], 2),
            'avg_processing_time_ms': round(sum(times) / len(times), 2) if times else 0,
            'error_count': self.metrics['errors'],
            'approval_rate': round(
                self.metrics['approvals'] / 
                (self.metrics['approvals'] + self.metrics['rejections']) * 100, 1
            ) if (self.metrics['approvals'] + self.metrics['rejections']) > 0 else 0
        }


class PricingDashboard:
    """Dashboard for pricing agent"""
    
    def __init__(self, metrics: PricingMetrics, analytics: PricingAnalytics):
        self.metrics = metrics
        self.analytics = analytics
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.get_stats(),
            'analytics': self.analytics.get_analytics(),
            'recent_activity': self._get_recent_activity()
        }
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity"""
        # Placeholder for recent activity
        return []


class RealTimeUpdater:
    """Handles real-time updates"""
    
    def __init__(self):
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self.update_queue: List[Dict[str, Any]] = []
    
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to updates"""
        self.subscribers.append(callback)
    
    def publish(self, update: Dict[str, Any]):
        """Publish update to subscribers"""
        update['timestamp'] = datetime.now().isoformat()
        self.update_queue.append(update)
        
        for subscriber in self.subscribers:
            try:
                subscriber(update)
            except Exception:
                pass
    
    def get_recent_updates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent updates"""
        return self.update_queue[-limit:]


# ============================================================================
# Feature 51: API Interface
# ============================================================================

class PricingAgentAPI:
    """API interface for Pricing Agent"""
    
    def __init__(self, agent: 'PricingAgent'):
        self.agent = agent
        self.endpoints = {
            'calculate': self._handle_calculate,
            'get_breakdown': self._handle_get_breakdown,
            'get_status': self._handle_get_status,
            'health': self._handle_health,
            'submit_approval': self._handle_submit_approval,
            'get_analytics': self._handle_get_analytics
        }
    
    def handle_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle API request"""
        handler = self.endpoints.get(endpoint)
        
        if not handler:
            return {'status': 404, 'error': f"Unknown endpoint: {endpoint}"}
        
        try:
            result = handler(payload)
            return {'status': 200, 'data': result}
        except Exception as e:
            return {'status': 500, 'error': str(e)}
    
    def _handle_calculate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calculate request"""
        return self.agent.calculate_pricing(payload)
    
    def _handle_get_breakdown(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle breakdown request"""
        pricing_id = payload.get('pricing_id')
        return self.agent.get_breakdown(pricing_id)
    
    def _handle_get_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request"""
        return self.agent.get_status()
    
    def _handle_health(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health request"""
        return self.agent.health_check()
    
    def _handle_submit_approval(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle approval submission"""
        return self.agent.submit_for_approval(
            payload.get('pricing_id'),
            payload.get('requester', 'api_user')
        )
    
    def _handle_get_analytics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics request"""
        return self.agent.analytics.get_analytics()


# ============================================================================
# Feature 1: PricingAgent Class - Main Class
# ============================================================================

class PricingAgent:
    """
    Comprehensive Pricing Agent
    
    Receives technical recommendations and testing requirements,
    calculates all costs, applies margins, and generates commercial bid documents.
    """
    
    def __init__(self, agent_id: str = "PRICING_AGENT", 
                 log_dir: Optional[str] = None):
        self.agent_id = agent_id
        self.created_at = datetime.now()
        
        # Initialize logger (Feature 42)
        self.logger = PricingAgentLogger(agent_id, log_dir)
        
        # Initialize components
        self.product_receiver = ProductListReceiver()  # Feature 2
        self.price_lookup = PriceLookupIntegration()  # Feature 3
        self.quantity_aggregator = QuantityAggregator()  # Feature 4
        self.unit_price_calculator = UnitPriceCalculator(self.price_lookup)  # Feature 5
        self.volume_discount_applier = VolumeDiscountApplier()  # Feature 6
        
        # Testing cost components
        self.test_parser = TestRequirementParser()  # Feature 7
        self.test_cost_calculator = TestCostCalculator()  # Feature 8
        self.frequency_analyzer = TestFrequencyAnalyzer()  # Feature 9
        self.sample_test_cost = SampleTestingCost(self.test_cost_calculator)  # Feature 10
        self.type_test_allocator = TypeTestCostAllocator(self.test_cost_calculator)  # Feature 11
        self.routine_test_calculator = RoutineTestCostCalculator(self.test_cost_calculator)  # Feature 12
        self.acceptance_test_cost = AcceptanceTestCost(self.test_cost_calculator)  # Feature 13
        self.certification_cost = CertificationCostAdder()  # Feature 14
        
        # Logistics components (Features 15-20)
        self.logistics_calculator = LogisticsCostCalculator()
        
        # Pricing components (Features 21-24)
        self.subtotal_aggregator = SubtotalAggregator()
        self.contingency_buffer = ContingencyBuffer()
        self.margin_calculator = MarginCalculator()
        self.final_price_generator = FinalPriceGenerator()
        
        # Analysis components (Features 25-28)
        self.competitive_analysis = CompetitiveAnalysis()
        self.recommendation_engine = PricingRecommendationEngine()
        self.price_optimization = PriceOptimization()
        self.win_probability = WinProbabilityEstimator()
        
        # Output components (Features 29-33)
        self.breakdown_generator = PricingBreakdownGenerator()
        self.terms_formatter = CommercialTermsFormatter()
        self.payment_terms_generator = PaymentTermsGenerator()
        self.table_creator = PricingTableCreator()
        self.comparison_generator = CostComparisonGenerator()
        
        # Analysis tools (Features 34-37)
        self.sensitivity_analysis = SensitivityAnalysis()
        self.whatif_generator = WhatIfScenarioGenerator()
        self.summary_generator = PricingSummaryGenerator()
        self.lineitem_breakdown = DetailedLineItemBreakdown()
        
        # Workflow components (Features 38-41)
        self.validator = PricingValidator()
        self.approval_workflow = PricingApprovalWorkflow()
        self.history_tracker = PricingHistoryTracker()
        self.analytics = PricingAnalytics()
        
        # Infrastructure (Features 43, 45-49)
        self.error_handler = PricingErrorHandler()  # Feature 43
        self.metrics = PricingMetrics()  # Feature 47
        self.dashboard = PricingDashboard(self.metrics, self.analytics)  # Feature 48
        self.realtime_updater = RealTimeUpdater()  # Feature 49
        
        # API (Feature 51)
        self.api = PricingAgentAPI(self)
        
        # State
        self.breakdowns: Dict[str, PricingBreakdown] = {}
        
        self.logger.info(f"Pricing Agent initialized: {agent_id}")
    
    def calculate_pricing(self, pricing_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complete pricing for RFP
        
        Main entry point for pricing calculations.
        """
        start_time = datetime.now()
        rfp_id = pricing_input.get('rfp_id', f"RFP_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        self.logger.info(f"Calculating pricing for RFP: {rfp_id}")
        
        try:
            # Feature 2: Receive products
            products = self.product_receiver.receive(pricing_input)
            
            # Feature 4: Aggregate quantities
            aggregated = self.quantity_aggregator.aggregate(products)
            
            # Calculate material costs (Features 3, 5, 6)
            material_costs = self._calculate_material_costs(products)
            
            # Calculate testing costs (Features 7-13)
            tests_required = pricing_input.get('tests_required', [])
            testing_costs = self._calculate_testing_costs(tests_required, products)
            
            # Feature 14: Certification costs
            certifications = pricing_input.get('certifications', [])
            cert_result = self.certification_cost.calculate(certifications)
            
            # Features 15-20: Logistics costs
            material_value = sum(p['total'] for p in material_costs)
            logistics_result = self.logistics_calculator.calculate(
                material_value=material_value,
                weight_kg=pricing_input.get('weight_kg', material_value / 100),
                distance_km=pricing_input.get('distance_km', 500),
                destination=pricing_input.get('destination', 'domestic')
            )
            
            # Feature 21: Aggregate subtotals
            costs = {
                'material': material_value,
                'sample_testing': testing_costs.get('sample_total', 0),
                'type_testing': testing_costs.get('type_total', 0),
                'routine_testing': testing_costs.get('routine_total', 0),
                'acceptance_testing': testing_costs.get('acceptance_total', 0),
                'certification': cert_result['total_cost'],
                'logistics': logistics_result['total_logistics_cost']
            }
            subtotals = self.subtotal_aggregator.aggregate(costs)
            
            # Feature 22: Add contingency
            contingency_result = self.contingency_buffer.calculate(
                subtotals['gross_total'],
                percent=pricing_input.get('contingency_percent', 5)
            )
            
            # Feature 23: Calculate margin
            margin_percent = pricing_input.get('margin_percent', 15)
            margin_result = self.margin_calculator.calculate(
                contingency_result['total_with_contingency'],
                target_margin=margin_percent
            )
            
            # Feature 24: Generate final price
            final_result = self.final_price_generator.generate(
                margin_result['selling_price'],
                include_gst=pricing_input.get('include_gst', True)
            )
            
            # Build response
            pricing_id = f"PRC_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            response = {
                'pricing_id': pricing_id,
                'rfp_id': rfp_id,
                'pricing_date': datetime.now().isoformat(),
                'products': material_costs,
                'tests': testing_costs.get('all_tests', []),
                'certifications': cert_result,
                'logistics': logistics_result,
                'subtotals': subtotals,
                'contingency': contingency_result['contingency_amount'],
                'contingency_percent': contingency_result['contingency_percent'],
                'margin': margin_result['margin_amount'],
                'margin_percent': margin_result['margin_percent'],
                'taxes': {
                    'gst_rate': final_result['gst_rate'],
                    'gst': final_result['gst_amount']
                },
                'grand_total': final_result['final_price'],
                'currency': 'INR'
            }
            
            # Feature 38: Validate
            validation = self.validator.validate(response)
            response['validation'] = validation
            
            # Feature 41: Record analytics
            self.analytics.add_data(response)
            
            # Feature 40: Track history
            self.history_tracker.record('pricing_calculated', pricing_id, {
                'rfp_id': rfp_id,
                'grand_total': response['grand_total']
            })
            
            # Feature 47: Record metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_quote(response['grand_total'], processing_time)
            
            # Feature 49: Publish update
            self.realtime_updater.publish({
                'event': 'pricing_calculated',
                'pricing_id': pricing_id,
                'rfp_id': rfp_id
            })
            
            self.logger.info(f"Pricing calculated: {pricing_id} - Total: {response['grand_total']}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error calculating pricing: {e}")
            self.metrics.record_error()
            raise
    
    def _calculate_material_costs(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate material costs for products"""
        costs = []
        
        for product in products:
            sku = product.get('selected_sku', '')
            quantity = product.get('quantity', 1)
            
            # Feature 5: Get unit price
            price_result = self.unit_price_calculator.calculate(sku, quantity)
            unit_price = price_result['unit_price']
            
            # Feature 6: Apply volume discount
            discount_result = self.volume_discount_applier.apply(unit_price, quantity)
            
            costs.append({
                'id': product.get('requirement_id', ''),
                'sku': sku,
                'name': product.get('product_name', ''),
                'manufacturer': product.get('manufacturer', ''),
                'quantity': quantity,
                'unit': product.get('unit', 'units'),
                'unit_price': unit_price,
                'discount': discount_result['discount_percent'],
                'net_price': discount_result['discounted_unit_price'],
                'total': discount_result['total_after_discount'],
                'confidence': price_result['confidence']
            })
        
        return costs
    
    def _calculate_testing_costs(self, tests_required: List[str],
                                  products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate all testing costs"""
        total_quantity = sum(p.get('quantity', 0) for p in products)
        
        # Feature 7: Parse test requirements
        parsed_tests = self.test_parser.parse(tests_required)
        
        # Categorize tests
        type_tests = [t['test_name'] for t in parsed_tests if t['test_type'] == 'type_test']
        routine_tests = [t['test_name'] for t in parsed_tests if t['test_type'] == 'routine_test']
        acceptance_tests = [t['test_name'] for t in parsed_tests if t['test_type'] == 'acceptance_test']
        sample_tests = [t['test_name'] for t in parsed_tests if t['test_type'] == 'sample_test']
        
        # Feature 10: Sample testing costs
        sample_result = self.sample_test_cost.calculate(sample_tests) if sample_tests else {'total_cost': 0}
        
        # Feature 11: Type test costs
        type_result = self.type_test_allocator.allocate(type_tests, total_quantity) if type_tests else {'total_cost': 0}
        
        # Feature 12: Routine test costs
        routine_result = self.routine_test_calculator.calculate(routine_tests, total_quantity) if routine_tests else {'total_cost': 0}
        
        # Feature 13: Acceptance test costs
        acceptance_result = self.acceptance_test_cost.calculate(acceptance_tests) if acceptance_tests else {'total_cost': 0}
        
        # Combine all test costs
        all_tests = []
        for result in [sample_result, type_result, routine_result, acceptance_result]:
            all_tests.extend(result.get('tests', []))
        
        return {
            'parsed_tests': parsed_tests,
            'sample_total': sample_result['total_cost'],
            'type_total': type_result['total_cost'],
            'routine_total': routine_result['total_cost'],
            'acceptance_total': acceptance_result['total_cost'],
            'all_tests': all_tests,
            'total': (sample_result['total_cost'] + type_result['total_cost'] +
                     routine_result['total_cost'] + acceptance_result['total_cost'])
        }
    
    def get_breakdown(self, pricing_id: str) -> Optional[Dict[str, Any]]:
        """Get pricing breakdown"""
        breakdown = self.breakdowns.get(pricing_id)
        if breakdown:
            return self.lineitem_breakdown.create(breakdown)
        return None
    
    def submit_for_approval(self, pricing_id: str, requester: str) -> Dict[str, Any]:
        """Submit pricing for approval"""
        # Get pricing data (simplified)
        approval = self.approval_workflow.submit_for_approval(
            pricing_id=pricing_id,
            rfp_id='',
            grand_total=0,
            requester=requester
        )
        
        return {
            'approval_id': approval.approval_id,
            'status': approval.status.value
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'created_at': self.created_at.isoformat(),
            'status': 'active',
            'metrics': self.metrics.get_stats(),
            'components': {
                'price_lookup': len(self.price_lookup.price_table),
                'test_costs': len(self.test_cost_calculator.test_costs)
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            'healthy': True,
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_commercial_terms(self, order_value: float,
                                   customer_type: str = 'government') -> Dict[str, Any]:
        """Generate commercial terms"""
        terms = self.terms_formatter.format()
        payment = self.payment_terms_generator.generate(order_value, customer_type)
        
        return {
            'terms': {
                'payment': terms.payment_terms,
                'delivery': terms.delivery_terms,
                'warranty': terms.warranty_period,
                'validity': terms.validity_period
            },
            'payment_options': payment['options']
        }
    
    def perform_competitive_analysis(self, our_price: float,
                                      category: str) -> Dict[str, Any]:
        """Perform competitive analysis"""
        return self.competitive_analysis.analyze(our_price, category)
    
    def estimate_win_probability(self, our_price: float,
                                  competitor_avg: float) -> Dict[str, Any]:
        """Estimate win probability"""
        return self.win_probability.estimate(our_price, competitor_avg)
    
    def generate_summary(self, pricing: Dict[str, Any]) -> str:
        """Generate pricing summary"""
        breakdown = self.breakdown_generator.generate(pricing)
        return self.summary_generator.generate(breakdown)
    
    def run_sensitivity_analysis(self, base_cost: float,
                                  base_margin: float) -> Dict[str, Any]:
        """Run sensitivity analysis"""
        return self.sensitivity_analysis.analyze(base_cost, base_margin)
    
    def generate_scenarios(self, base_pricing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate what-if scenarios"""
        return self.whatif_generator.generate(base_pricing)
    
    def get_recommendations(self, cost: float, margin: float) -> Dict[str, Any]:
        """Get pricing recommendations"""
        return self.recommendation_engine.recommend(cost, margin)
    
    def optimize_price(self, cost: float, objective: str = 'balanced') -> Dict[str, Any]:
        """Optimize price for objective"""
        return self.price_optimization.optimize(cost, objective=objective)
