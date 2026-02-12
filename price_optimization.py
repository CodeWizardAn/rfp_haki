"""
Price Optimization & Analytics Module
Real-time price tracking, history analysis, and discount optimization
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import sqlite3
from pathlib import Path


class PriceTrend(Enum):
    """Price trend direction"""
    RISING = "RISING"
    FALLING = "FALLING"
    STABLE = "STABLE"


@dataclass
class PricePoint:
    """Single price data point"""
    product_id: str
    seller_id: str
    seller_name: str
    price: float
    currency: str = "INR"
    timestamp: datetime = field(default_factory=datetime.now)
    quantity_available: int = 0
    delivery_days: int = 0
    seller_rating: float = 4.0


@dataclass
class DiscountTier:
    """Volume discount tier"""
    min_quantity: int
    max_quantity: Optional[int]
    discount_percentage: float
    description: str = ""


@dataclass
class VolumeDiscount:
    """Volume discount configuration for a product"""
    product_id: str
    tiers: List[DiscountTier]
    bulk_purchase_threshold: int  # Minimum for bulk pricing
    negotiation_potential: float  # 0-1, how much room for negotiation


class PriceDatabase:
    """
    Database for storing historical price data
    Enables price trend analysis
    """

    def __init__(self, db_path: str = None):
        """Initialize price database"""
        if db_path is None:
            db_path = Path(__file__).parent / 'price_history.db'
        
        self.db_path = db_path
        self.connection = None
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(str(self.db_path))
        cursor = self.connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                seller_id TEXT NOT NULL,
                seller_name TEXT,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'INR',
                timestamp DATETIME NOT NULL,
                quantity_available INTEGER,
                delivery_days INTEGER,
                seller_rating REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_product_time 
            ON price_history(product_id, timestamp DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_seller_time 
            ON price_history(seller_id, timestamp DESC)
        ''')

        self.connection.commit()
        print(f"✅ Price history database initialized at {self.db_path}")

    def record_price(self, point: PricePoint) -> bool:
        """Record price point in history"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO price_history (
                    product_id, seller_id, seller_name, price, currency,
                    timestamp, quantity_available, delivery_days, seller_rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                point.product_id, point.seller_id, point.seller_name,
                point.price, point.currency, point.timestamp.isoformat(),
                point.quantity_available, point.delivery_days, point.seller_rating
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error recording price: {e}")
            return False

    def get_price_history(
        self,
        product_id: str,
        seller_id: str = None,
        days: int = 30
    ) -> List[Dict]:
        """Get price history for product"""
        cursor = self.connection.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        if seller_id:
            cursor.execute('''
                SELECT * FROM price_history 
                WHERE product_id = ? AND seller_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (product_id, seller_id, start_date))
        else:
            cursor.execute('''
                SELECT * FROM price_history 
                WHERE product_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (product_id, start_date))

        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_latest_prices(self, product_id: str) -> List[Dict]:
        """Get latest price from each seller"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            SELECT DISTINCT ON (seller_id) * FROM price_history 
            WHERE product_id = ?
            ORDER BY seller_id, timestamp DESC
        ''', (product_id,))

        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        """Close database"""
        if self.connection:
            self.connection.close()


class PriceAnalytics:
    """
    Advanced price analytics and forecasting
    """

    def __init__(self, db_path: str = None):
        """Initialize price analytics"""
        self.db = PriceDatabase(db_path)

    def analyze_price_history(self, product_id: str, seller_id: str = None, days: int = 30) -> Dict:
        """Analyze price trends"""
        history = self.db.get_price_history(product_id, seller_id, days)
        
        if not history:
            return {'error': 'No price history available'}

        prices = [float(h['price']) for h in history]
        timestamps = [datetime.fromisoformat(h['timestamp']) for h in history]

        # Calculate statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        
        try:
            std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
        except:
            std_dev = 0

        # Determine trend
        if len(prices) > 1:
            recent_avg = statistics.mean(prices[:len(prices)//2])
            older_avg = statistics.mean(prices[len(prices)//2:])
            
            if recent_avg > older_avg * 1.02:  # 2% threshold
                trend = PriceTrend.RISING
            elif recent_avg < older_avg * 0.98:
                trend = PriceTrend.FALLING
            else:
                trend = PriceTrend.STABLE
        else:
            trend = PriceTrend.STABLE

        # Price volatility
        volatility = (std_dev / avg_price * 100) if avg_price > 0 else 0

        return {
            'product_id': product_id,
            'seller_id': seller_id,
            'period_days': days,
            'data_points': len(prices),
            'statistics': {
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'avg_price': round(avg_price, 2),
                'median_price': round(median_price, 2),
                'std_deviation': round(std_dev, 2),
                'volatility_percentage': round(volatility, 2)
            },
            'trend': trend.value,
            'current_price': round(prices[0], 2),
            'price_change_percentage': round(((prices[0] - prices[-1]) / prices[-1] * 100), 2) if prices[-1] > 0 else 0
        }

    def compare_sellers(self, product_id: str) -> Dict:
        """Compare prices across sellers"""
        # Get latest prices from all sellers
        latest = self.db.get_latest_prices(product_id)
        
        if not latest:
            return {'error': 'No price data available'}

        prices = [(h['seller_name'], float(h['price']), h['seller_rating']) for h in latest]
        prices_sorted = sorted(prices, key=lambda x: x[1])

        return {
            'product_id': product_id,
            'seller_count': len(prices),
            'cheapest': {
                'seller': prices_sorted[0][0],
                'price': round(prices_sorted[0][1], 2),
                'rating': prices_sorted[0][2]
            },
            'most_expensive': {
                'seller': prices_sorted[-1][0],
                'price': round(prices_sorted[-1][1], 2),
                'rating': prices_sorted[-1][2]
            },
            'avg_price': round(statistics.mean([p[1] for p in prices]), 2),
            'price_range': round(prices_sorted[-1][1] - prices_sorted[0][1], 2),
            'all_sellers': [
                {
                    'seller': p[0],
                    'price': round(p[1], 2),
                    'rating': p[2],
                    'price_vs_avg_percentage': round(((p[1] / statistics.mean([pr[1] for pr in prices])) - 1) * 100, 2)
                }
                for p in prices_sorted
            ]
        }

    def predict_price(self, product_id: str, seller_id: str = None, days_ahead: int = 7) -> Dict:
        """Simple price prediction based on trend"""
        history = self.db.get_price_history(product_id, seller_id, days=90)
        
        if len(history) < 2:
            return {'error': 'Insufficient data for prediction'}

        prices = [float(h['price']) for h in history]
        
        # Simple linear regression
        n = len(prices)
        x_vals = list(range(n))
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(prices)
        
        numerator = sum((x_vals[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        # Predict
        predicted_price = intercept + slope * (n + days_ahead)

        return {
            'product_id': product_id,
            'current_price': round(prices[0], 2),
            'predicted_price': round(predicted_price, 2),
            'days_ahead': days_ahead,
            'trend': 'upward' if slope > 0 else 'downward',
            'confidence': 'low'  # Simple linear regression has low confidence
        }

    def close(self):
        """Cleanup"""
        self.db.close()


class VolumeDiscountCalculator:
    """
    Calculates volume discounts and negotiation opportunities
    """

    def __init__(self):
        """Initialize discount calculator"""
        self.discount_configs: Dict[str, VolumeDiscount] = {}

    def set_discount_tiers(self, product_id: str, tiers: List[DiscountTier], bulk_threshold: int = 100):
        """Set volume discount tiers for product"""
        self.discount_configs[product_id] = VolumeDiscount(
            product_id=product_id,
            tiers=sorted(tiers, key=lambda t: t.min_quantity),
            bulk_purchase_threshold=bulk_threshold,
            negotiation_potential=0.1  # Default 10% negotiation room
        )

    def calculate_discount(self, product_id: str, quantity: int) -> Dict:
        """Calculate applicable discount for quantity"""
        if product_id not in self.discount_configs:
            return {
                'product_id': product_id,
                'quantity': quantity,
                'discount_percentage': 0,
                'message': 'No discount tiers configured'
            }

        config = self.discount_configs[product_id]
        
        applicable_tier = None
        for tier in config.tiers:
            if quantity >= tier.min_quantity:
                if tier.max_quantity is None or quantity <= tier.max_quantity:
                    applicable_tier = tier

        if applicable_tier is None:
            discount = 0
        else:
            discount = applicable_tier.discount_percentage

        return {
            'product_id': product_id,
            'quantity': quantity,
            'discount_percentage': discount,
            'applicable_tier': applicable_tier.description if applicable_tier else 'None',
            'bulk_discount_available': quantity >= config.bulk_purchase_threshold
        }

    def calculate_total_cost(self, product_id: str, unit_price: float, quantity: int) -> Dict:
        """Calculate total cost with discount"""
        discount_info = self.calculate_discount(product_id, quantity)
        discount_pct = discount_info['discount_percentage']

        base_cost = unit_price * quantity
        discount_amount = base_cost * (discount_pct / 100)
        final_cost = base_cost - discount_amount

        return {
            'product_id': product_id,
            'unit_price': round(unit_price, 2),
            'quantity': quantity,
            'base_cost': round(base_cost, 2),
            'discount_percentage': discount_pct,
            'discount_amount': round(discount_amount, 2),
            'final_cost': round(final_cost, 2),
            'cost_per_unit_after_discount': round(final_cost / quantity, 2)
        }

    def find_optimal_quantity(self, product_id: str, unit_price: float, budget: float) -> Dict:
        """Find optimal quantity for given budget"""
        if product_id not in self.discount_configs:
            quantity = int(budget / unit_price)
            return {
                'product_id': product_id,
                'budget': budget,
                'optimal_quantity': quantity,
                'cost': round(budget, 2)
            }

        config = self.discount_configs[product_id]
        
        best_quantity = int(budget / unit_price)
        best_cost = budget
        best_discount = 0

        # Check different quantities to find best deal
        for tier in config.tiers:
            test_qty = tier.min_quantity
            while test_qty <= int(budget / unit_price):
                cost_info = self.calculate_total_cost(product_id, unit_price, test_qty)
                if cost_info['final_cost'] <= budget and cost_info['final_cost'] < best_cost:
                    best_quantity = test_qty
                    best_cost = cost_info['final_cost']
                    best_discount = cost_info['discount_percentage']
                test_qty += 10

        return {
            'product_id': product_id,
            'budget': budget,
            'optimal_quantity': best_quantity,
            'final_cost': round(best_cost, 2),
            'savings': round(best_quantity * unit_price - best_cost, 2),
            'discount_achieved': best_discount
        }

    def compare_suppliers_total_cost(self, product_id: str, prices: List[Dict], quantity: int) -> List[Dict]:
        """Compare total cost across suppliers"""
        comparisons = []
        
        for price_info in prices:
            cost_info = self.calculate_total_cost(product_id, price_info['price'], quantity)
            comparisons.append({
                'seller': price_info.get('seller', 'Unknown'),
                'unit_price': round(price_info['price'], 2),
                'total_cost': round(cost_info['final_cost'], 2),
                'savings': round(cost_info['discount_amount'], 2),
                'discount_percentage': cost_info['discount_percentage']
            })

        return sorted(comparisons, key=lambda x: x['total_cost'])


# Example usage
if __name__ == '__main__':
    # Initialize components
    analytics = PriceAnalytics()
    discount_calc = VolumeDiscountCalculator()

    # Set up discount tiers
    tiers = [
        DiscountTier(min_quantity=1, max_quantity=9, discount_percentage=0, description="1-9 units"),
        DiscountTier(min_quantity=10, max_quantity=49, discount_percentage=5, description="10-49 units"),
        DiscountTier(min_quantity=50, max_quantity=99, discount_percentage=10, description="50-99 units"),
        DiscountTier(min_quantity=100, max_quantity=None, discount_percentage=15, description="100+ units"),
    ]
    discount_calc.set_discount_tiers('WIRE-001', tiers, bulk_threshold=50)

    # Record some price data
    for i in range(10):
        price = 150 + (i % 3) * 10  # Varying prices
        point = PricePoint(
            product_id='WIRE-001',
            seller_id='SELLER-001',
            seller_name='Polycab',
            price=price,
            timestamp=datetime.now() - timedelta(days=i)
        )
        analytics.db.record_price(point)

    # Analyze prices
    print("\n📊 Price Analysis:")
    analysis = analytics.analyze_price_history('WIRE-001', days=30)
    print(f"Current Price: ₹{analysis['current_price']}")
    print(f"Avg Price: ₹{analysis['statistics']['avg_price']}")
    print(f"Trend: {analysis['trend']}")

    # Calculate discounts
    print("\n💰 Volume Discounts:")
    cost = discount_calc.calculate_total_cost('WIRE-001', 150, 100)
    print(f"100 units @ ₹150/unit")
    print(f"Discount: {cost['discount_percentage']}%")
    print(f"Total Cost: ₹{cost['final_cost']}")

    analytics.close()
