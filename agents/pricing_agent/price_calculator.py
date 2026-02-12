"""
Pricing Agent - Price Calculator
Assigns prices and consolidates costs for RFP response
"""

import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import logging

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import database config
try:
    from database.db_config import DatabaseConfig, DatabaseType
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProductPrice:
    """Price entry for a product"""
    sku: str
    product_name: str
    unit_price: float
    currency: str = "INR"
    price_valid_until: str = ""
    moq: int = 1
    bulk_discount_percent: float = 0
    price_tier: str = "STANDARD"


@dataclass
class TestPrice:
    """Price entry for a test/service"""
    test_id: str
    test_name: str
    test_type: str  # TYPE_TEST, ROUTINE_TEST, ACCEPTANCE_TEST
    unit_price: float
    currency: str = "INR"
    standard_reference: str = ""
    lab_name: str = ""
    turnaround_days: int = 7


@dataclass
class PricingBreakdown:
    """Complete pricing breakdown for an RFP"""
    rfp_id: str
    product_prices: List[Dict[str, Any]]
    test_costs: List[Dict[str, Any]]
    total_material_cost: float
    total_services_cost: float
    taxes: Dict[str, float]
    grand_total: float
    pricing_notes: List[str]


class PricingAgent:
    """
    Pricing Agent - Price Calculator
    
    Responsibilities:
    - Receives test summary from Master Agent
    - Receives product recommendations from Technical Agent
    - Assigns unit prices from pricing table
    - Assigns test costs from services price table
    - Consolidates material and services costs
    - Sends pricing to Master Agent
    """
    
    def __init__(self):
        self.agent_id = "PRICING_AGENT"
        self.product_price_table: Dict[str, ProductPrice] = {}
        self.services_price_table: Dict[str, TestPrice] = {}
        
        # Load price tables from database
        self._load_product_prices()
        self._load_services_prices()
        
        logger.info(f"✅ Pricing Agent initialized")
        logger.info(f"   - Product prices loaded: {len(self.product_price_table)}")
        logger.info(f"   - Service prices loaded: {len(self.services_price_table)}")
    
    def _load_product_prices(self):
        """Load product pricing table from database"""
        if not DB_AVAILABLE:
            raise RuntimeError("Database configuration not available. Cannot load product prices.")
        
        db_path = DatabaseConfig.get_path(DatabaseType.PRODUCT_PRICES)
        if not db_path.exists():
            raise FileNotFoundError(f"Product prices database not found: {db_path}")
        
        with open(db_path, 'r') as f:
            data = json.load(f)
        
        for product in data.get('products', []):
            if product.get('active', True):
                self.product_price_table[product['sku']] = ProductPrice(
                    sku=product['sku'],
                    product_name=product['product_name'],
                    unit_price=product['unit_price'],
                    moq=product.get('moq', 1),
                    bulk_discount_percent=product.get('bulk_discount_percent', 0)
                )
        logger.info(f"📦 Loaded product prices from database: {db_path}")
    
    def _load_services_prices(self):
        """Load services/tests pricing table from database"""
        if not DB_AVAILABLE:
            raise RuntimeError("Database configuration not available. Cannot load service prices.")
        
        db_path = DatabaseConfig.get_path(DatabaseType.SERVICE_PRICES)
        if not db_path.exists():
            raise FileNotFoundError(f"Service prices database not found: {db_path}")
        
        with open(db_path, 'r') as f:
            data = json.load(f)
        
        for service in data.get('services', []):
            if service.get('active', True):
                self.services_price_table[service['service_id']] = TestPrice(
                    test_id=service['service_id'],
                    test_name=service['service_name'],
                    test_type=service.get('category', 'ROUTINE_TEST'),
                    unit_price=service['price'],
                    standard_reference=service.get('standard', ''),
                    lab_name="NABL Accredited Lab",
                    turnaround_days=service.get('turnaround_days', 7)
                )
        logger.info(f"🧪 Loaded service prices from database: {db_path}")
    
    def calculate_pricing(self, pricing_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complete pricing for RFP
        
        Args:
            pricing_input: Contains RFP info, tests required, and product recommendations
            
        Returns:
            Complete pricing breakdown
        """
        rfp_id = pricing_input.get('rfp_id')
        tests_required = pricing_input.get('tests_required', [])
        product_recommendations = pricing_input.get('product_recommendations', [])
        
        logger.info(f"💰 Calculating pricing for RFP {rfp_id}")
        
        # Calculate product prices
        product_prices = self._calculate_product_prices(product_recommendations)
        total_material_cost = sum(p['total_price'] for p in product_prices)
        
        # Calculate test/service costs
        test_costs = self._calculate_test_costs(tests_required)
        total_services_cost = sum(t['total_cost'] for t in test_costs)
        
        # Calculate taxes
        taxes = self._calculate_taxes(total_material_cost, total_services_cost)
        
        # Calculate grand total
        grand_total = total_material_cost + total_services_cost + taxes['total_tax']
        
        # Build response
        response = {
            'rfp_id': rfp_id,
            'pricing_date': datetime.now().isoformat(),
            'product_prices': product_prices,
            'test_costs': test_costs,
            'total_material_cost': round(total_material_cost, 2),
            'total_services_cost': round(total_services_cost, 2),
            'taxes': taxes,
            'grand_total': round(grand_total, 2),
            'pricing_summary': {
                'material_percent': round((total_material_cost / grand_total) * 100, 1) if grand_total > 0 else 0,
                'services_percent': round((total_services_cost / grand_total) * 100, 1) if grand_total > 0 else 0,
                'tax_percent': round((taxes['total_tax'] / grand_total) * 100, 1) if grand_total > 0 else 0
            },
            'pricing_notes': self._generate_pricing_notes(product_prices, test_costs)
        }
        
        logger.info(f"✅ Pricing calculated - Grand Total: ₹{grand_total:,.2f}")
        return response
    
    def _calculate_product_prices(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate prices for recommended products"""
        product_prices = []
        
        for rec in recommendations:
            sku = rec.get('selected_sku')
            quantity = rec.get('quantity', 1)
            
            # Get price from table
            price_entry = self.product_price_table.get(sku)
            
            if price_entry:
                unit_price = price_entry.unit_price
                
                # Apply bulk discount if quantity exceeds MOQ significantly
                discount = 0
                if quantity >= price_entry.moq * 10:
                    discount = price_entry.bulk_discount_percent
                
                discounted_price = unit_price * (1 - discount / 100)
                total_price = discounted_price * quantity
                
                product_prices.append({
                    'sku': sku,
                    'product_name': price_entry.product_name,
                    'rfp_product': rec.get('rfp_product', ''),
                    'quantity': quantity,
                    'unit_price': round(unit_price, 2),
                    'discount_percent': discount,
                    'discounted_unit_price': round(discounted_price, 2),
                    'total_price': round(total_price, 2)
                })
            else:
                # SKU not found, use estimated price
                estimated_price = 50.0  # Default estimate
                product_prices.append({
                    'sku': sku,
                    'product_name': rec.get('product_name', 'Unknown Product'),
                    'rfp_product': rec.get('rfp_product', ''),
                    'quantity': quantity,
                    'unit_price': estimated_price,
                    'discount_percent': 0,
                    'discounted_unit_price': estimated_price,
                    'total_price': estimated_price * quantity,
                    'note': 'Price estimated - not in price table'
                })
        
        return product_prices
    
    def _calculate_test_costs(self, tests_required: List[str]) -> List[Dict[str, Any]]:
        """Calculate costs for required tests"""
        test_costs = []
        
        # Map test names to test IDs
        test_mapping = {
            'conductor resistance': 'TEST_CONDUCTOR_RES',
            'insulation resistance': 'TEST_INSULATION_RES',
            'high voltage': 'TEST_HV',
            'spark': 'TEST_SPARK',
            'flame retardancy': 'TEST_FLAME_IEC60332',
            'flame': 'TEST_FLAME_IEC60332',
            'smoke density': 'TEST_SMOKE_IEC61034',
            'smoke': 'TEST_SMOKE_IEC61034',
            'hot set': 'TEST_HOT_SET',
            'tensile': 'TEST_TENSILE',
            'elongation': 'TEST_ELONGATION',
            'thermal stability': 'TEST_THERMAL_STABILITY',
            'thermal': 'TEST_THERMAL_STABILITY',
            'third party': 'SVC_TPI',
            'inspection': 'SVC_TPI',
            'type test certificate': 'SVC_TYPE_CERT',
            'routine test': 'SVC_ROUTINE_CERT'
        }
        
        for test_name in tests_required:
            test_lower = test_name.lower()
            
            # Find matching test
            test_id = None
            for key, value in test_mapping.items():
                if key in test_lower:
                    test_id = value
                    break
            
            if test_id and test_id in self.services_price_table:
                price_entry = self.services_price_table[test_id]
                test_costs.append({
                    'test_id': test_id,
                    'test_name': price_entry.test_name,
                    'rfp_test_requirement': test_name,
                    'test_type': price_entry.test_type,
                    'unit_cost': price_entry.unit_price,
                    'quantity': 1,
                    'total_cost': price_entry.unit_price,
                    'standard_reference': price_entry.standard_reference,
                    'lab': price_entry.lab_name,
                    'turnaround_days': price_entry.turnaround_days
                })
            else:
                # Test not found in price table, estimate
                test_costs.append({
                    'test_id': f"TEST_CUSTOM_{len(test_costs)}",
                    'test_name': test_name,
                    'rfp_test_requirement': test_name,
                    'test_type': 'TYPE_TEST',
                    'unit_cost': 10000.00,  # Default estimate
                    'quantity': 1,
                    'total_cost': 10000.00,
                    'standard_reference': 'As per RFP',
                    'lab': 'TBD',
                    'turnaround_days': 7,
                    'note': 'Cost estimated - test not in price table'
                })
        
        return test_costs
    
    def _calculate_taxes(self, material_cost: float, services_cost: float) -> Dict[str, float]:
        """Calculate applicable taxes"""
        # GST rates
        material_gst_rate = 18.0  # 18% GST on materials
        services_gst_rate = 18.0  # 18% GST on services
        
        material_gst = material_cost * (material_gst_rate / 100)
        services_gst = services_cost * (services_gst_rate / 100)
        
        return {
            'material_gst_rate': material_gst_rate,
            'material_gst_amount': round(material_gst, 2),
            'services_gst_rate': services_gst_rate,
            'services_gst_amount': round(services_gst, 2),
            'total_tax': round(material_gst + services_gst, 2)
        }
    
    def _generate_pricing_notes(self, product_prices: List[Dict[str, Any]], 
                                 test_costs: List[Dict[str, Any]]) -> List[str]:
        """Generate pricing notes and caveats"""
        notes = []
        
        # Check for estimated prices
        estimated_products = [p for p in product_prices if 'note' in p]
        if estimated_products:
            notes.append(f"{len(estimated_products)} product(s) have estimated prices")
        
        estimated_tests = [t for t in test_costs if 'note' in t]
        if estimated_tests:
            notes.append(f"{len(estimated_tests)} test(s) have estimated costs")
        
        # Add standard notes
        notes.extend([
            "Prices are valid for 30 days from quote date",
            "Bulk discounts applied where applicable",
            "GST @ 18% included in grand total",
            "Test costs are for one set of samples per product",
            "Additional samples will incur extra charges",
            "Transportation costs not included",
            "Payment terms: 30% advance, 70% on delivery"
        ])
        
        return notes
    
    def get_product_price(self, sku: str) -> Optional[ProductPrice]:
        """Get price for a specific SKU"""
        return self.product_price_table.get(sku)
    
    def get_test_price(self, test_id: str) -> Optional[TestPrice]:
        """Get price for a specific test"""
        return self.services_price_table.get(test_id)
    
    def update_product_price(self, sku: str, new_price: float):
        """Update price for a product"""
        if sku in self.product_price_table:
            self.product_price_table[sku].unit_price = new_price
            logger.info(f"Updated price for {sku}: ₹{new_price}")
    
    def export_pricing_to_json(self, pricing: Dict[str, Any]) -> str:
        """Export pricing breakdown to JSON"""
        return json.dumps(pricing, indent=2)
    
    def generate_quote_summary(self, pricing: Dict[str, Any]) -> str:
        """Generate human-readable quote summary"""
        summary = []
        summary.append("=" * 60)
        summary.append("QUOTATION SUMMARY")
        summary.append("=" * 60)
        summary.append(f"RFP ID: {pricing.get('rfp_id')}")
        summary.append(f"Date: {pricing.get('pricing_date', '')[:10]}")
        summary.append("")
        
        summary.append("MATERIAL COSTS:")
        summary.append("-" * 40)
        for product in pricing.get('product_prices', []):
            summary.append(f"  {product['product_name'][:30]}")
            summary.append(f"    Qty: {product['quantity']:,} x ₹{product['discounted_unit_price']:.2f} = ₹{product['total_price']:,.2f}")
        summary.append(f"  SUBTOTAL MATERIALS: ₹{pricing.get('total_material_cost', 0):,.2f}")
        summary.append("")
        
        summary.append("SERVICE COSTS (Tests & Certification):")
        summary.append("-" * 40)
        for test in pricing.get('test_costs', []):
            summary.append(f"  {test['test_name'][:35]}: ₹{test['total_cost']:,.2f}")
        summary.append(f"  SUBTOTAL SERVICES: ₹{pricing.get('total_services_cost', 0):,.2f}")
        summary.append("")
        
        taxes = pricing.get('taxes', {})
        summary.append("TAXES:")
        summary.append("-" * 40)
        summary.append(f"  GST on Materials ({taxes.get('material_gst_rate', 18)}%): ₹{taxes.get('material_gst_amount', 0):,.2f}")
        summary.append(f"  GST on Services ({taxes.get('services_gst_rate', 18)}%): ₹{taxes.get('services_gst_amount', 0):,.2f}")
        summary.append(f"  TOTAL TAX: ₹{taxes.get('total_tax', 0):,.2f}")
        summary.append("")
        
        summary.append("=" * 60)
        summary.append(f"GRAND TOTAL: ₹{pricing.get('grand_total', 0):,.2f}")
        summary.append("=" * 60)
        
        return "\n".join(summary)


# Example usage
if __name__ == "__main__":
    pricing = PricingAgent()
    
    # Sample input
    sample_input = {
        'rfp_id': 'RFP_SAMPLE_001',
        'tests_required': [
            'Conductor Resistance Test',
            'Insulation Resistance Test',
            'High Voltage Test',
            'Flame Retardancy Test'
        ],
        'product_recommendations': [
            {
                'rfp_product': 'PVC Wire 1.5 sq mm',
                'selected_sku': 'POL-PVC-1.5-R',
                'product_name': 'Polycab Optima Plus PVC Wire 1.5 sq mm',
                'quantity': 50000
            },
            {
                'rfp_product': 'PVC Wire 2.5 sq mm',
                'selected_sku': 'HAV-LIFELINE-2.5',
                'product_name': 'Havells Lifeline Plus PVC Wire 2.5 sq mm',
                'quantity': 30000
            }
        ]
    }
    
    result = pricing.calculate_pricing(sample_input)
    print(pricing.generate_quote_summary(result))
