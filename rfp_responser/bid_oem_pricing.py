"""
OEM Pricing Calculator
Specialized pricing for OEM vendors including NRE, MOQ, and lead time costs
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class OEMPricingModel(Enum):
    """OEM pricing models"""
    NRE_PLUS_UNIT = "NRE_PLUS_UNIT"  # Non-Recurring Engineering + Per-unit cost
    VOLUME_TIERED = "VOLUME_TIERED"  # Different pricing per volume tier
    HYBRID = "HYBRID"  # Combination of NRE + tiered pricing


@dataclass
class VolumeTier:
    """Volume-based pricing tier"""
    min_qty: int
    max_qty: int
    unit_price: float
    moq: int = 0  # Minimum order quantity for this tier
    lead_time_days: int = 0  # Standard lead time
    expedited_cost_percent: float = 0.0  # Extra charge for expedited delivery


@dataclass
class NRECost:
    """NRE (Non-Recurring Engineering) cost breakdown"""
    engineering_hours: int = 0
    hourly_rate: float = 1000.0  # ₹ per hour
    tooling_cost: float = 0.0
    setup_cost: float = 0.0
    testing_cost: float = 0.0
    documentation_cost: float = 0.0
    design_cost: float = 0.0
    certification_cost: float = 0.0
    
    def calculate_total(self) -> float:
        """Calculate total NRE cost"""
        return (
            (self.engineering_hours * self.hourly_rate) +
            self.tooling_cost +
            self.setup_cost +
            self.testing_cost +
            self.documentation_cost +
            self.design_cost +
            self.certification_cost
        )


class OEMPriceCalculator:
    """OEM pricing calculator with NRE, MOQ, and lead time"""
    
    def __init__(self, default_tax_rate: float = 18.0):
        """Initialize OEM calculator"""
        self.default_tax_rate = default_tax_rate
        self.volume_tiers: Dict[str, List[VolumeTier]] = {}
    
    def add_volume_tier(self, product_id: str, tier: VolumeTier):
        """Add volume tier for product"""
        if product_id not in self.volume_tiers:
            self.volume_tiers[product_id] = []
        self.volume_tiers[product_id].append(tier)
        # Sort by min_qty
        self.volume_tiers[product_id].sort(key=lambda x: x.min_qty)
    
    def get_applicable_tier(self, product_id: str, quantity: int) -> VolumeTier:
        """Get applicable pricing tier for quantity"""
        if product_id not in self.volume_tiers:
            return None
        
        for tier in self.volume_tiers[product_id]:
            if tier.min_qty <= quantity <= tier.max_qty:
                return tier
        
        # Return highest tier if quantity exceeds all
        return self.volume_tiers[product_id][-1] if self.volume_tiers[product_id] else None
    
    def calculate_nre_plus_unit(self,
                               product_id: str,
                               quantity: int,
                               unit_price: float,
                               nre_cost: NRECost = None,
                               discount_percent: float = 0.0,
                               tax_percent: float = None) -> Dict:
        """Calculate NRE + Unit pricing model (typical for OEM)"""
        
        if tax_percent is None:
            tax_percent = self.default_tax_rate
        
        # Get applicable tier
        tier = self.get_applicable_tier(product_id, quantity)
        
        # MOQ Check
        if tier and tier.moq > 0 and quantity < tier.moq:
            return {
                'error': f'MOQ {tier.moq} not met. Requested: {quantity}',
                'moq_required': tier.moq,
                'quantity_requested': quantity,
                'status': 'INVALID'
            }
        
        # Use tier price if available
        if tier and tier.unit_price > 0:
            unit_price = tier.unit_price
        
        # Calculate unit cost
        unit_subtotal = unit_price * quantity
        unit_discount = unit_subtotal * (discount_percent / 100)
        unit_subtotal_after_discount = unit_subtotal - unit_discount
        
        # Calculate NRE (typically one-time, not taxed separately)
        total_nre = 0.0
        nre_details = {}
        if nre_cost:
            total_nre = nre_cost.calculate_total()
            nre_details = {
                'engineering_hours': nre_cost.engineering_hours,
                'hourly_rate': nre_cost.hourly_rate,
                'tooling_cost': nre_cost.tooling_cost,
                'setup_cost': nre_cost.setup_cost,
                'testing_cost': nre_cost.testing_cost,
                'documentation_cost': nre_cost.documentation_cost,
                'total_nre': total_nre
            }
        
        # Total before tax (NRE is added before tax as it's cost component)
        total_before_tax = unit_subtotal_after_discount + total_nre
        
        # Apply tax
        tax_amount = total_before_tax * (tax_percent / 100)
        grand_total = total_before_tax + tax_amount
        
        # Cost per unit (excluding NRE for comparison)
        cost_per_unit_base = (unit_price * (1 - discount_percent/100)) * (1 + tax_percent/100)
        
        # Cost per unit including NRE spread
        cost_per_unit_with_nre = grand_total / quantity if quantity > 0 else 0
        
        lead_time = tier.lead_time_days if tier else 0
        
        return {
            'status': 'VALID',
            'product_id': product_id,
            'pricing_model': 'NRE_PLUS_UNIT',
            
            # Unit pricing
            'quantity': quantity,
            'unit_price': unit_price,
            'unit_subtotal': round(unit_subtotal, 2),
            'discount_percent': discount_percent,
            'unit_discount_amount': round(unit_discount, 2),
            'unit_subtotal_after_discount': round(unit_subtotal_after_discount, 2),
            
            # NRE
            'nre_cost': round(total_nre, 2),
            'nre_details': nre_details,
            
            # Taxes
            'tax_percent': tax_percent,
            'tax_amount': round(tax_amount, 2),
            
            # Totals
            'total_before_tax': round(total_before_tax, 2),
            'grand_total': round(grand_total, 2),
            
            # Per-unit costs
            'cost_per_unit_base': round(cost_per_unit_base, 4),
            'cost_per_unit_with_nre': round(cost_per_unit_with_nre, 4),
            'nre_cost_per_unit': round(total_nre / quantity, 4) if quantity > 0 else 0,
            
            # OEM-specific
            'moq': tier.moq if tier else 0,
            'lead_time_days': lead_time,
            'tier_min': tier.min_qty if tier else 0,
            'tier_max': tier.max_qty if tier else 0
        }
    
    def calculate_volume_tiered(self,
                               product_id: str,
                               quantity: int,
                               discount_percent: float = 0.0,
                               tax_percent: float = None) -> Dict:
        """Calculate volume-tiered pricing"""
        
        if tax_percent is None:
            tax_percent = self.default_tax_rate
        
        tier = self.get_applicable_tier(product_id, quantity)
        
        if not tier:
            return {'error': f'No pricing tier found for product {product_id}'}
        
        # MOQ Check
        if tier.moq > 0 and quantity < tier.moq:
            return {
                'error': f'MOQ {tier.moq} not met. Requested: {quantity}',
                'moq_required': tier.moq,
                'quantity_requested': quantity,
                'status': 'INVALID'
            }
        
        # Calculate pricing
        subtotal = tier.unit_price * quantity
        discount_amount = subtotal * (discount_percent / 100)
        subtotal_after_discount = subtotal - discount_amount
        tax_amount = subtotal_after_discount * (tax_percent / 100)
        grand_total = subtotal_after_discount + tax_amount
        
        cost_per_unit = (tier.unit_price * (1 - discount_percent/100)) * (1 + tax_percent/100)
        
        return {
            'status': 'VALID',
            'product_id': product_id,
            'pricing_model': 'VOLUME_TIERED',
            'quantity': quantity,
            'unit_price': tier.unit_price,
            'subtotal': round(subtotal, 2),
            'discount_percent': discount_percent,
            'discount_amount': round(discount_amount, 2),
            'subtotal_after_discount': round(subtotal_after_discount, 2),
            'tax_percent': tax_percent,
            'tax_amount': round(tax_amount, 2),
            'grand_total': round(grand_total, 2),
            'cost_per_unit': round(cost_per_unit, 4),
            'tier_min': tier.min_qty,
            'tier_max': tier.max_qty,
            'moq': tier.moq,
            'lead_time_days': tier.lead_time_days
        }
    
    def calculate_hybrid(self,
                        product_id: str,
                        quantity: int,
                        unit_price: float,
                        nre_cost: NRECost = None,
                        discount_percent: float = 0.0,
                        tax_percent: float = None) -> Dict:
        """Calculate hybrid pricing (NRE + tiered units)"""
        
        # Start with NRE + Unit calculation
        result = self.calculate_nre_plus_unit(
            product_id, quantity, unit_price, nre_cost, discount_percent, tax_percent
        )
        
        result['pricing_model'] = 'HYBRID'
        
        return result
    
    def calculate_complete_oem_pricing(self,
                                      items: List[Dict],
                                      shipping_weight: float = 0.0,
                                      include_insurance: bool = False,
                                      expedited_delivery: bool = False,
                                      tax_percent: float = None) -> Dict:
        """Calculate complete OEM pricing with all items and shipping"""
        
        if tax_percent is None:
            tax_percent = self.default_tax_rate
        
        total_subtotal = 0.0
        total_discount = 0.0
        total_nre = 0.0
        total_tax = 0.0
        items_breakdown = []
        total_moq = 0
        max_lead_time = 0
        
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            unit_price = item.get('unit_price')
            nre_cost_data = item.get('nre_cost')
            discount_percent = item.get('discount_percent', 0.0)
            
            # Create NRE object if provided
            nre_obj = None
            if nre_cost_data:
                nre_obj = NRECost(**nre_cost_data)
            
            # Calculate item pricing
            item_pricing = self.calculate_nre_plus_unit(
                product_id, quantity, unit_price, nre_obj, discount_percent, tax_percent
            )
            
            if item_pricing.get('status') == 'INVALID':
                return item_pricing  # Return error immediately
            
            items_breakdown.append(item_pricing)
            
            total_subtotal += item_pricing['unit_subtotal']
            total_discount += item_pricing['unit_discount_amount']
            total_nre += item_pricing['nre_cost']
            total_moq += item_pricing['moq']
            max_lead_time = max(max_lead_time, item_pricing.get('lead_time_days', 0))
        
        # Subtotal after discounts and NRE
        subtotal_after_discount = total_subtotal - total_discount
        total_before_nre_tax = subtotal_after_discount
        total_before_tax = total_before_nre_tax + total_nre
        
        # Shipping
        shipping_cost = 0.0
        insurance_cost = 0.0
        if shipping_weight > 0:
            shipping_cost = shipping_weight * 10.0  # ₹10 per kg
            if include_insurance:
                insurance_cost = total_before_tax * 0.02  # 2% insurance
        
        # Expedited delivery charges
        expedited_charges = 0.0
        if expedited_delivery:
            expedited_charges = (total_before_tax + shipping_cost) * 0.15  # 15% extra
        
        # Calculate tax on everything except NRE (NRE is already included)
        tax_on_items = subtotal_after_discount * (tax_percent / 100)
        tax_on_shipping = shipping_cost * (tax_percent / 100)
        total_tax = tax_on_items + tax_on_shipping
        
        # Grand total
        grand_total = (subtotal_after_discount + tax_on_items + 
                      shipping_cost + tax_on_shipping + 
                      insurance_cost + expedited_charges)
        
        # With NRE (NRE typically added on top)
        grand_total_with_nre = grand_total + total_nre
        
        return {
            'status': 'VALID',
            'items_count': len(items),
            'items_breakdown': items_breakdown,
            
            # Subtotals
            'total_unit_subtotal': round(total_subtotal, 2),
            'total_discount': round(total_discount, 2),
            'subtotal_after_discount': round(subtotal_after_discount, 2),
            
            # NRE
            'total_nre': round(total_nre, 2),
            'total_moq_sum': total_moq,
            'max_lead_time_days': max_lead_time,
            
            # Tax & Shipping
            'tax_percent': tax_percent,
            'tax_amount': round(total_tax, 2),
            'shipping_weight_kg': shipping_weight,
            'shipping_cost': round(shipping_cost, 2),
            'insurance_cost': round(insurance_cost, 2),
            'expedited_charges': round(expedited_charges, 2),
            
            # Totals
            'total_without_nre': round(grand_total, 2),
            'grand_total': round(grand_total, 2),
            'grand_total_with_nre': round(grand_total_with_nre, 2),
            
            # Analysis
            'cost_breakdown_percent': {
                'unit_cost_percent': round((subtotal_after_discount / grand_total_with_nre) * 100, 2),
                'nre_percent': round((total_nre / grand_total_with_nre) * 100, 2),
                'tax_percent': round((total_tax / grand_total_with_nre) * 100, 2),
                'shipping_percent': round((shipping_cost / grand_total_with_nre) * 100, 2)
            }
        }


# Example usage and default OEM pricing setup
def setup_default_oem_pricing() -> OEMPriceCalculator:
    """Setup calculator with default OEM pricing for wires/cables"""
    calc = OEMPriceCalculator()
    
    # Example: Wires product line
    tiers = [
        VolumeTier(1, 99, 20.00, moq=10, lead_time_days=21),
        VolumeTier(100, 499, 18.50, moq=100, lead_time_days=14),
        VolumeTier(500, 999, 17.00, moq=500, lead_time_days=10),
        VolumeTier(1000, 999999, 15.50, moq=1000, lead_time_days=7),
    ]
    
    for tier in tiers:
        calc.add_volume_tier('WIRE_001', tier)
    
    return calc


if __name__ == '__main__':
    # Example usage
    calc = setup_default_oem_pricing()
    
    # Define NRE for custom order
    nre = NRECost(
        engineering_hours=40,
        hourly_rate=1500,
        tooling_cost=50000,
        setup_cost=10000,
        testing_cost=5000
    )
    
    # Calculate pricing for 500 units with NRE
    result = calc.calculate_nre_plus_unit(
        'WIRE_001',
        500,
        15.50,
        nre,
        discount_percent=5.0
    )
    
    print(f"Pricing for 500 units:")
    print(f"Unit Subtotal: ₹{result['unit_subtotal']}")
    print(f"NRE Cost: ₹{result['nre_cost']}")
    print(f"Tax: ₹{result['tax_amount']}")
    print(f"Grand Total: ₹{result['grand_total']}")
    print(f"Cost per unit (with NRE): ₹{result['cost_per_unit_with_nre']}")
    print(f"Lead Time: {result['lead_time_days']} days")
