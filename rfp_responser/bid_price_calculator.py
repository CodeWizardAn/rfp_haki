"""
Bid Price Calculator
Calculates pricing for bid items with discounts, taxes, and shipping
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class TaxType(Enum):
    """Tax types"""
    GST = "GST"  # India GST
    VAT = "VAT"  # European VAT
    NO_TAX = "NO_TAX"


@dataclass
class ShippingCost:
    """Shipping cost calculation"""
    base_shipping: float
    weight_unit: str  # kg, ton
    weight: float
    shipping_rate_per_unit: float = 10.0  # ₹ per kg
    insurance_percent: float = 0.5  # 0.5% of value


@dataclass
class PricingBreakdown:
    """Complete pricing breakdown"""
    item_count: int
    unit_prices: Dict[str, float]
    subtotal: float
    discounts: Dict[str, float]  # Discount type -> amount
    total_discount: float
    subtotal_after_discount: float
    
    tax_type: TaxType
    tax_rate: float
    tax_amount: float
    
    shipping_cost: float
    insurance_cost: float
    
    grand_total: float
    cost_per_unit: float


class PriceCalculator:
    """Calculates bid pricing"""
    
    def __init__(self):
        """Initialize calculator"""
        self.tax_type = TaxType.GST
        self.tax_rate = 18.0  # Default 18% GST
    
    def set_tax_type(self, tax_type: TaxType, rate: float):
        """Set tax type and rate"""
        self.tax_type = tax_type
        self.tax_rate = rate
    
    def calculate_item_price(
        self,
        unit_price: float,
        quantity: int,
        discount_percent: float = 0.0,
        tax_rate: float = None
    ) -> Dict:
        """Calculate price for single item"""
        if tax_rate is None:
            tax_rate = self.tax_rate
        
        # Calculate subtotal
        subtotal = unit_price * quantity
        
        # Apply discount
        discount_amount = subtotal * (discount_percent / 100)
        subtotal_after_discount = subtotal - discount_amount
        
        # Apply tax
        tax_amount = subtotal_after_discount * (tax_rate / 100)
        
        # Final total
        total = subtotal_after_discount + tax_amount
        
        return {
            'quantity': quantity,
            'unit_price': unit_price,
            'subtotal': round(subtotal, 2),
            'discount_percent': discount_percent,
            'discount_amount': round(discount_amount, 2),
            'subtotal_after_discount': round(subtotal_after_discount, 2),
            'tax_rate': tax_rate,
            'tax_amount': round(tax_amount, 2),
            'total': round(total, 2),
            'cost_per_unit': round(total / quantity, 4)
        }
    
    def calculate_volume_discount(
        self,
        total_quantity: int,
        tiers: List[Tuple[int, float]]
    ) -> Dict:
        """Calculate volume discount
        
        Args:
            total_quantity: Total quantity ordered
            tiers: List of (min_qty, discount_percent) tuples
                  [(100, 5), (500, 10), (1000, 15)]
        """
        applicable_discount = 0.0
        applicable_tier = None
        
        # Sort tiers by quantity
        sorted_tiers = sorted(tiers, key=lambda x: x[0], reverse=True)
        
        for min_qty, discount in sorted_tiers:
            if total_quantity >= min_qty:
                applicable_discount = discount
                applicable_tier = min_qty
                break
        
        return {
            'total_quantity': total_quantity,
            'applicable_tier': applicable_tier,
            'discount_percent': applicable_discount,
            'tier_description': f"{applicable_tier}+ units: {applicable_discount}% off" if applicable_tier else "No volume discount"
        }
    
    def calculate_shipping(
        self,
        base_weight: float,
        weight_unit: str = 'kg',
        rate_per_unit: float = 10.0,
        order_value: float = 0.0,
        insurance_percent: float = 0.5
    ) -> Dict:
        """Calculate shipping and insurance costs"""
        
        # Calculate shipping
        shipping_cost = base_weight * rate_per_unit
        
        # Calculate insurance
        insurance_cost = order_value * (insurance_percent / 100)
        
        # Total
        total_shipping_insurance = shipping_cost + insurance_cost
        
        return {
            'weight': base_weight,
            'weight_unit': weight_unit,
            'rate_per_unit': rate_per_unit,
            'shipping_cost': round(shipping_cost, 2),
            'order_value': round(order_value, 2),
            'insurance_percent': insurance_percent,
            'insurance_cost': round(insurance_cost, 2),
            'total': round(total_shipping_insurance, 2)
        }
    
    def calculate_complete_pricing(
        self,
        items: List[Dict],  # [{product_id, quantity, unit_price, discount_percent}, ...]
        volume_discount_tiers: List[Tuple[int, float]] = None,
        shipping_weight: float = 0.0,
        shipping_rate: float = 10.0,
        include_insurance: bool = False
    ) -> PricingBreakdown:
        """Calculate complete bid pricing
        
        Args:
            items: List of item dicts
            volume_discount_tiers: Volume discount tier list
            shipping_weight: Total weight in kg
            shipping_rate: Shipping rate per kg
            include_insurance: Include insurance in calculation
        """
        
        # Calculate individual items
        item_subtotals = []
        unit_prices = {}
        total_quantity = 0
        
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            unit_price = item['unit_price']
            discount_percent = item.get('discount_percent', 0.0)
            
            unit_prices[product_id] = unit_price
            total_quantity += quantity
            
            item_calc = self.calculate_item_price(
                unit_price, quantity, discount_percent, self.tax_rate
            )
            item_subtotals.append(item_calc)
        
        # Sum all items (before additional discounts)
        subtotal = sum(ic['subtotal'] for ic in item_subtotals)
        total_item_discount = sum(ic['discount_amount'] for ic in item_subtotals)
        subtotal_after_item_discount = subtotal - total_item_discount
        
        # Apply volume discount if applicable
        volume_discount_info = {}
        additional_volume_discount = 0.0
        
        if volume_discount_tiers:
            volume_discount_info = self.calculate_volume_discount(
                total_quantity, volume_discount_tiers
            )
            additional_volume_discount = subtotal_after_item_discount * \
                (volume_discount_info['discount_percent'] / 100)
        
        total_discount = total_item_discount + additional_volume_discount
        subtotal_after_discount = subtotal - total_discount
        
        # Apply tax
        tax_amount = subtotal_after_discount * (self.tax_rate / 100)
        
        # Calculate shipping
        shipping_info = {}
        shipping_cost = 0.0
        insurance_cost = 0.0
        
        if shipping_weight > 0:
            shipping_info = self.calculate_shipping(
                shipping_weight, 
                shipping_rate_per_unit=shipping_rate,
                order_value=subtotal_after_discount if include_insurance else 0.0
            )
            shipping_cost = shipping_info['shipping_cost']
            insurance_cost = shipping_info['insurance_cost']
        
        # Calculate grand total
        grand_total = subtotal_after_discount + tax_amount + shipping_cost + insurance_cost
        cost_per_unit = grand_total / total_quantity if total_quantity > 0 else 0
        
        return PricingBreakdown(
            item_count=len(items),
            unit_prices=unit_prices,
            subtotal=round(subtotal, 2),
            discounts={
                'item_discounts': round(total_item_discount, 2),
                'volume_discount': round(additional_volume_discount, 2)
            },
            total_discount=round(total_discount, 2),
            subtotal_after_discount=round(subtotal_after_discount, 2),
            tax_type=self.tax_type,
            tax_rate=self.tax_rate,
            tax_amount=round(tax_amount, 2),
            shipping_cost=round(shipping_cost, 2),
            insurance_cost=round(insurance_cost, 2),
            grand_total=round(grand_total, 2),
            cost_per_unit=round(cost_per_unit, 4)
        )


# Example usage
if __name__ == '__main__':
    calculator = PriceCalculator()
    
    # Example bid
    items = [
        {
            'product_id': 'WIRE_001',
            'quantity': 1000,
            'unit_price': 15.50,
            'discount_percent': 5.0
        },
        {
            'product_id': 'WIRE_002',
            'quantity': 500,
            'unit_price': 25.75,
            'discount_percent': 0.0
        }
    ]
    
    # Volume discount tiers
    volume_tiers = [
        (100, 5),     # 100+ units: 5% off
        (500, 10),    # 500+ units: 10% off
        (1000, 15)    # 1000+ units: 15% off
    ]
    
    # Calculate pricing
    pricing = calculator.calculate_complete_pricing(
        items=items,
        volume_discount_tiers=volume_tiers,
        shipping_weight=50,  # 50 kg
        shipping_rate=10.0,  # ₹10 per kg
        include_insurance=True
    )
    
    print(f"\n💰 Pricing Breakdown:")
    print(f"Items: {pricing.item_count}")
    print(f"Subtotal: ₹{pricing.subtotal:,.2f}")
    print(f"Discounts: ₹{pricing.total_discount:,.2f}")
    print(f"Tax ({pricing.tax_rate}%): ₹{pricing.tax_amount:,.2f}")
    print(f"Shipping: ₹{pricing.shipping_cost:,.2f}")
    print(f"Insurance: ₹{pricing.insurance_cost:,.2f}")
    print(f"GRAND TOTAL: ₹{pricing.grand_total:,.2f}")
    print(f"Cost per unit: ₹{pricing.cost_per_unit:,.4f}")
