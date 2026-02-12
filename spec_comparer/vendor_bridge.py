"""
Spec Comparer - Vendor Management Bridge
Integrates vendor performance into specification comparison workflow
"""

import logging
from typing import Dict, List, Optional

# Import vendor management modules
try:
    from vendor_management.vendor_database import get_vendor_database
    from vendor_management.vendor_performance import get_performance_tracker
    from vendor_management.vendor_rating import get_rating_engine
    HAS_VENDOR_MGT = True
except ImportError:
    HAS_VENDOR_MGT = False

logger = logging.getLogger('spec_vendor_bridge')


class SpecVendorBridge:
    """Bridge spec comparison with vendor management"""

    def __init__(self):
        """Initialize spec vendor bridge"""
        if HAS_VENDOR_MGT:
            self.vendor_db = get_vendor_database()
            self.performance_tracker = get_performance_tracker()
            self.rating_engine = get_rating_engine()
        else:
            self.vendor_db = None
            self.performance_tracker = None
            self.rating_engine = None
            logger.warning("Vendor management modules not available")

    def enrich_comparison_with_vendor_performance(self, comparison_data: Dict,
                                                 vendor_ids: List[str]) -> Dict:
        """Add vendor performance metrics to comparison"""
        if not self.vendor_db or not self.performance_tracker:
            return comparison_data

        try:
            comparison_data['vendor_performance'] = {}
            
            for vendor_id in vendor_ids:
                performance = self.performance_tracker.get_overall_performance(vendor_id, days=90)
                rating = self.rating_engine.get_vendor_rating(vendor_id) if self.rating_engine else None
                
                comparison_data['vendor_performance'][vendor_id] = {
                    'overall_score': performance.get('overall_score', 0),
                    'delivery_score': performance.get('delivery_score', 0),
                    'quality_score': performance.get('quality_score', 0),
                    'response_score': performance.get('response_score', 0),
                    'rating': rating.get('overall_rating') if rating else None,
                    'badges': self.rating_engine.get_vendor_badges(vendor_id) if self.rating_engine else []
                }
            
            return comparison_data
        except Exception as e:
            logger.error(f"Error enriching comparison with vendor performance: {e}")
            return comparison_data

    def get_best_vendor_for_specs(self, spec_comparisons: List[Dict],
                                vendor_ids: List[str]) -> Optional[str]:
        """Determine best vendor based on specs and performance"""
        if not self.performance_tracker:
            return None

        try:
            best_vendor = None
            best_score = -1

            for vendor_id in vendor_ids:
                performance = self.performance_tracker.get_overall_performance(vendor_id)
                score = performance.get('overall_score', 0)

                if score > best_score:
                    best_score = score
                    best_vendor = vendor_id

            return best_vendor
        except Exception as e:
            logger.error(f"Error determining best vendor: {e}")
            return None

    def add_vendor_recommendations_to_specs(self, specs: Dict, vendor_id: str) -> Dict:
        """Add vendor-based recommendations to specifications"""
        if not self.vendor_db or not self.rating_engine:
            return specs

        try:
            vendor = self.vendor_db.get_vendor(vendor_id)
            if not vendor:
                return specs

            rating = self.rating_engine.get_vendor_rating(vendor_id)
            badges = self.rating_engine.get_vendor_badges(vendor_id)

            specs['vendor_recommendation'] = {
                'vendor_id': vendor_id,
                'vendor_name': vendor.get('name'),
                'rating': rating.get('overall_rating') if rating else None,
                'badges': [b.get('badge_name') for b in badges],
                'contact': {
                    'email': vendor.get('email'),
                    'phone': vendor.get('phone')
                },
                'min_order_value': vendor.get('min_order_value', 0),
                'payment_terms': vendor.get('payment_terms', 'Net 30')
            }

            return specs
        except Exception as e:
            logger.error(f"Error adding vendor recommendations: {e}")
            return specs

    def compare_vendors_on_specs(self, spec1: Dict, spec2: Dict,
                                vendor1_id: str, vendor2_id: str) -> Dict:
        """Compare two vendors on specifications"""
        if not self.vendor_db or not self.performance_tracker:
            return {}

        try:
            vendor1 = self.vendor_db.get_vendor(vendor1_id)
            vendor2 = self.vendor_db.get_vendor(vendor2_id)

            perf1 = self.performance_tracker.get_overall_performance(vendor1_id)
            perf2 = self.performance_tracker.get_overall_performance(vendor2_id)

            comparison = {
                'spec_details': {
                    'spec1_compliance': self._check_spec_compliance(spec1, vendor1),
                    'spec2_compliance': self._check_spec_compliance(spec2, vendor2)
                },
                'vendor_performance': {
                    'vendor1': {
                        'id': vendor1_id,
                        'name': vendor1.get('name') if vendor1 else 'Unknown',
                        'performance_score': perf1.get('overall_score', 0),
                        'delivery': perf1.get('delivery_score', 0),
                        'quality': perf1.get('quality_score', 0)
                    },
                    'vendor2': {
                        'id': vendor2_id,
                        'name': vendor2.get('name') if vendor2 else 'Unknown',
                        'performance_score': perf2.get('overall_score', 0),
                        'delivery': perf2.get('delivery_score', 0),
                        'quality': perf2.get('quality_score', 0)
                    }
                },
                'recommendation': None
            }

            # Determine recommendation
            if perf1.get('overall_score', 0) > perf2.get('overall_score', 0):
                comparison['recommendation'] = vendor1_id
            elif perf2.get('overall_score', 0) > perf1.get('overall_score', 0):
                comparison['recommendation'] = vendor2_id

            return comparison
        except Exception as e:
            logger.error(f"Error comparing vendors on specs: {e}")
            return {}

    def _check_spec_compliance(self, spec: Dict, vendor: Dict) -> bool:
        """Check if vendor meets specification requirements"""
        if not vendor:
            return False

        try:
            # Check minimum order value
            min_order = vendor.get('min_order_value', 0)
            spec_quantity = spec.get('quantity', 0)

            if min_order > 0 and spec_quantity < min_order:
                return False

            # Check product categories
            categories = vendor.get('product_categories', [])
            spec_category = spec.get('category')

            if spec_category and categories and spec_category not in categories:
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking spec compliance: {e}")
            return False

    def get_vendor_alternatives_for_specs(self, spec: Dict, exclude_vendor_id: str = None) -> List[Dict]:
        """Find alternative vendors for specifications"""
        if not self.vendor_db:
            return []

        try:
            all_vendors = self.vendor_db.list_vendors(status='ACTIVE', limit=100)
            alternatives = []

            spec_category = spec.get('category')

            for vendor in all_vendors:
                if exclude_vendor_id and vendor.get('vendor_id') == exclude_vendor_id:
                    continue

                # Check if vendor can supply
                categories = vendor.get('product_categories', [])
                
                if spec_category and categories and spec_category not in categories:
                    continue

                # Get performance score
                perf = self.performance_tracker.get_overall_performance(vendor.get('vendor_id'))
                
                alternatives.append({
                    'vendor_id': vendor.get('vendor_id'),
                    'vendor_name': vendor.get('name'),
                    'email': vendor.get('email'),
                    'performance_score': perf.get('overall_score', 0),
                    'min_order_value': vendor.get('min_order_value', 0)
                })

            # Sort by performance score
            alternatives.sort(key=lambda x: x['performance_score'], reverse=True)
            return alternatives[:5]  # Return top 5
        except Exception as e:
            logger.error(f"Error getting vendor alternatives: {e}")
            return []


# Module-level bridge instance
_spec_vendor_bridge = None


def get_spec_vendor_bridge() -> SpecVendorBridge:
    """Get or create spec vendor bridge"""
    global _spec_vendor_bridge
    if _spec_vendor_bridge is None:
        _spec_vendor_bridge = SpecVendorBridge()
    return _spec_vendor_bridge


if __name__ == '__main__':
    bridge = get_spec_vendor_bridge()
    
    # Example: Get vendor alternatives
    spec = {'category': 'Wires', 'quantity': 100}
    alternatives = bridge.get_vendor_alternatives_for_specs(spec)
    if alternatives:
        print(f"✅ Found {len(alternatives)} vendor alternatives")
        for alt in alternatives:
            print(f"  - {alt['vendor_name']}: {alt['performance_score']}")
    else:
        print("⚠️ No alternatives found or service unavailable")
