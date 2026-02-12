"""
Vendor Management Integration Module
Bridges vendor management with audit_trail, compliance_checker, and price_optimization
"""

import logging
from typing import Dict, Optional
from datetime import datetime

# Import core modules (handling missing imports gracefully)
try:
    from audit_trail import get_audit_logger, AuditEntityType, AuditAction
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False

try:
    from compliance_checker import get_compliance_scorer
    HAS_COMPLIANCE = True
except ImportError:
    HAS_COMPLIANCE = False

try:
    from price_optimization import get_price_analytics
    HAS_PRICE_OPT = True
except ImportError:
    HAS_PRICE_OPT = False

logger = logging.getLogger('vendor_integration')


class VendorIntegrationBridge:
    """Bridge vendor management with other modules"""

    def __init__(self):
        """Initialize integration bridge"""
        self.audit_logger = get_audit_logger() if HAS_AUDIT else None
        self.compliance_scorer = get_compliance_scorer() if HAS_COMPLIANCE else None
        self.price_analytics = get_price_analytics() if HAS_PRICE_OPT else None
        
        self.logger = logging.getLogger('vendor_bridge')
        self.logger.info("✅ Vendor integration bridge initialized")

    # ========= AUDIT TRAIL INTEGRATION =========

    def log_vendor_created(self, vendor_id: str, vendor_data: Dict, user_id: str = None):
        """Log vendor creation"""
        if not self.audit_logger:
            self.logger.warning("Audit logger not available")
            return
        
        try:
            self.audit_logger.log_create(
                user_id=user_id or 'system',
                entity_type=AuditEntityType.VENDOR,
                entity_id=vendor_id,
                new_value=vendor_data
            )
            self.logger.info(f"✅ Logged vendor creation: {vendor_id}")
        except Exception as e:
            self.logger.error(f"Failed to log vendor creation: {e}")

    def log_vendor_updated(self, vendor_id: str, old_data: Dict, new_data: Dict, user_id: str = None):
        """Log vendor update"""
        if not self.audit_logger:
            self.logger.warning("Audit logger not available")
            return
        
        try:
            self.audit_logger.log_update(
                user_id=user_id or 'system',
                entity_type=AuditEntityType.VENDOR,
                entity_id=vendor_id,
                old_value=old_data,
                new_value=new_data
            )
            self.logger.info(f"✅ Logged vendor update: {vendor_id}")
        except Exception as e:
            self.logger.error(f"Failed to log vendor update: {e}")

    def log_vendor_approved(self, vendor_id: str, reason: str = "", user_id: str = None):
        """Log vendor approval"""
        if not self.audit_logger:
            self.logger.warning("Audit logger not available")
            return
        
        try:
            self.audit_logger.log_action(
                user_id=user_id or 'system',
                entity_type=AuditEntityType.VENDOR,
                entity_id=vendor_id,
                action=AuditAction.APPROVE,
                details=reason
            )
            self.logger.info(f"✅ Logged vendor approval: {vendor_id}")
        except Exception as e:
            self.logger.error(f"Failed to log vendor approval: {e}")

    def log_vendor_rejected(self, vendor_id: str, reason: str = "", user_id: str = None):
        """Log vendor rejection"""
        if not self.audit_logger:
            self.logger.warning("Audit logger not available")
            return
        
        try:
            self.audit_logger.log_action(
                user_id=user_id or 'system',
                entity_type=AuditEntityType.VENDOR,
                entity_id=vendor_id,
                action=AuditAction.REJECT,
                details=reason
            )
            self.logger.info(f"✅ Logged vendor rejection: {vendor_id}")
        except Exception as e:
            self.logger.error(f"Failed to log vendor rejection: {e}")

    # ========= COMPLIANCE INTEGRATION =========

    def verify_vendor_compliance(self, vendor_id: str, vendor_data: Dict) -> Dict:
        """Verify vendor compliance"""
        if not self.compliance_scorer:
            self.logger.warning("Compliance scorer not available")
            return {'compliant': True, 'score': 0, 'reason': 'Compliance not available'}
        
        try:
            # Extract compliance-relevant data
            compliance_data = {
                'gst_number': vendor_data.get('gst_number'),
                'pan_number': vendor_data.get('pan_number'),
                'registration': vendor_data.get('registration_date'),
                'status': vendor_data.get('status', 'ACTIVE')
            }
            
            # Check basic compliance
            is_compliant = bool(
                compliance_data.get('gst_number') and
                compliance_data.get('pan_number') and
                compliance_data.get('status') == 'ACTIVE'
            )
            
            self.logger.info(f"✅ Verified vendor compliance: {vendor_id} - {is_compliant}")
            
            return {
                'vendor_id': vendor_id,
                'compliant': is_compliant,
                'score': 85 if is_compliant else 40,
                'checks': {
                    'gst_valid': bool(compliance_data.get('gst_number')),
                    'pan_valid': bool(compliance_data.get('pan_number')),
                    'active_status': compliance_data.get('status') == 'ACTIVE'
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to verify vendor compliance: {e}")
            return {'compliant': False, 'score': 0, 'error': str(e)}

    # ========= PRICE OPTIMIZATION INTEGRATION =========

    def analyze_vendor_pricing(self, vendor_id: str, price_history: list) -> Dict:
        """Analyze vendor pricing trends"""
        if not self.price_analytics:
            self.logger.warning("Price analytics not available")
            return {'trend': 'UNKNOWN', 'analysis': 'Price analysis not available'}
        
        try:
            if not price_history or len(price_history) == 0:
                return {
                    'vendor_id': vendor_id,
                    'trend': 'INSUFFICIENT_DATA',
                    'message': 'No pricing history available'
                }
            
            # Extract prices
            prices = [p.get('price') for p in price_history if p.get('price')]
            
            if len(prices) < 2:
                return {
                    'vendor_id': vendor_id,
                    'trend': 'INSUFFICIENT_DATA',
                    'prices_analyzed': len(prices)
                }
            
            # Analyze trend
            if prices[-1] > prices[-2]:
                trend = 'RISING'
            elif prices[-1] < prices[-2]:
                trend = 'FALLING'
            else:
                trend = 'STABLE'
            
            avg_price = sum(prices) / len(prices)
            
            self.logger.info(f"✅ Analyzed vendor pricing: {vendor_id} - {trend}")
            
            return {
                'vendor_id': vendor_id,
                'trend': trend,
                'avg_price': round(avg_price, 2),
                'latest_price': prices[-1],
                'min_price': min(prices),
                'max_price': max(prices),
                'price_volatility': round((max(prices) - min(prices)) / avg_price * 100, 2) if avg_price > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze vendor pricing: {e}")
            return {'vendor_id': vendor_id, 'error': str(e)}

    # ========= INTEGRATED VENDOR EVALUATION =========

    def evaluate_vendor_holistically(self, vendor_id: str, vendor_data: Dict,
                                    performance_data: Dict = None,
                                    price_data: list = None) -> Dict:
        """Comprehensive vendor evaluation"""
        try:
            evaluation = {
                'vendor_id': vendor_id,
                'evaluation_date': datetime.now().isoformat(),
                'vendor_name': vendor_data.get('name'),
                'sections': {}
            }

            # 1. Compliance check
            compliance = self.verify_vendor_compliance(vendor_id, vendor_data)
            evaluation['sections']['compliance'] = compliance

            # 2. Performance analysis
            if performance_data:
                evaluation['sections']['performance'] = {
                    'overall_score': performance_data.get('overall_score', 0),
                    'delivery_score': performance_data.get('delivery_score', 0),
                    'quality_score': performance_data.get('quality_score', 0),
                    'response_score': performance_data.get('response_score', 0)
                }

            # 3. Price analysis
            if price_data:
                price_analysis = self.analyze_vendor_pricing(vendor_id, price_data)
                evaluation['sections']['pricing'] = price_analysis

            # Calculate overall recommendation
            scores = []
            
            if compliance.get('score'):
                scores.append(compliance['score'])
            
            if performance_data and performance_data.get('overall_score'):
                scores.append(performance_data['overall_score'])

            if scores:
                overall_score = sum(scores) / len(scores)
            else:
                overall_score = 0

            # Generate recommendation
            if overall_score >= 85:
                recommendation = "HIGHLY RECOMMENDED"
            elif overall_score >= 70:
                recommendation = "RECOMMENDED"
            elif overall_score >= 50:
                recommendation = "ACCEPTABLE"
            else:
                recommendation = "NOT RECOMMENDED"

            evaluation['overall_score'] = round(overall_score, 2)
            evaluation['recommendation'] = recommendation

            self.logger.info(f"✅ Completed holistic vendor evaluation: {vendor_id} - {recommendation}")

            return evaluation
        except Exception as e:
            self.logger.error(f"Failed to evaluate vendor: {e}")
            return {'vendor_id': vendor_id, 'error': str(e)}

    # ========= REPORTING =========

    def generate_vendor_scorecard(self, vendor_id: str, vendor_data: Dict,
                                 performance_data: Dict = None) -> Dict:
        """Generate comprehensive vendor scorecard"""
        try:
            scorecard = {
                'vendor_id': vendor_id,
                'vendor_name': vendor_data.get('name'),
                'generated_date': datetime.now().isoformat(),
                'scores': {},
                'recommendations': []
            }

            # Compliance score
            compliance = self.verify_vendor_compliance(vendor_id, vendor_data)
            scorecard['scores']['compliance'] = compliance.get('score', 0)
            
            if not compliance.get('compliant'):
                scorecard['recommendations'].append("Complete compliance requirements before onboarding")

            # Performance scores
            if performance_data:
                scorecard['scores']['delivery'] = performance_data.get('delivery_score', 0)
                scorecard['scores']['quality'] = performance_data.get('quality_score', 0)
                scorecard['scores']['response'] = performance_data.get('response_score', 0)

                if performance_data.get('delivery_score', 0) < 70:
                    scorecard['recommendations'].append("Improve on-time delivery performance")
                
                if performance_data.get('quality_score', 0) < 75:
                    scorecard['recommendations'].append("Enhance quality control processes")

            # Calculate average
            if scorecard['scores']:
                scorecard['overall_score'] = round(
                    sum(scorecard['scores'].values()) / len(scorecard['scores']),
                    2
                )

            self.logger.info(f"✅ Generated vendor scorecard: {vendor_id}")
            return scorecard
        except Exception as e:
            self.logger.error(f"Failed to generate scorecard: {e}")
            return {'vendor_id': vendor_id, 'error': str(e)}


# Singleton instance
_integration_bridge = None


def get_integration_bridge() -> VendorIntegrationBridge:
    """Get or create integration bridge"""
    global _integration_bridge
    if _integration_bridge is None:
        _integration_bridge = VendorIntegrationBridge()
    return _integration_bridge


if __name__ == '__main__':
    bridge = get_integration_bridge()

    # Example vendor data
    vendor_data = {
        'name': 'Polycab Industries',
        'gst_number': '27AAFCT1234H1Z0',
        'pan_number': 'AAACT1234H',
        'status': 'ACTIVE'
    }

    # Verify compliance
    compliance = bridge.verify_vendor_compliance('V001', vendor_data)
    print(f"✅ Compliance verified: {compliance}")

    # Generate scorecard
    performance_data = {
        'delivery_score': 92,
        'quality_score': 88,
        'response_score': 95
    }
    scorecard = bridge.generate_vendor_scorecard('V001', vendor_data, performance_data)
    print(f"✅ Scorecard generated: {scorecard['overall_score']}")
