"""
Compliance Checker Module
Validates products against standards and regulations
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import re


class ComplianceStatus(Enum):
    """Compliance status levels"""
    FULLY_COMPLIANT = "FULLY_COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    UNKNOWN = "UNKNOWN"


class RiskLevel(Enum):
    """Risk classification"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ComplianceRule:
    """Single compliance rule"""
    rule_id: str
    name: str
    description: str
    standard: str  # IS, IEC, BIS, etc.
    condition: str  # Rule condition (field, operator, value)
    weight: float = 1.0  # Importance weight (0-1)
    mandatory: bool = False
    severity: str = "warning"  # warning, error, critical


@dataclass
class ComplianceFinding:
    """Single compliance finding"""
    rule_id: str
    rule_name: str
    status: ComplianceStatus
    message: str
    evidence: str = None
    recommendation: str = None
    severity: str = "warning"
    weight: float = 1.0


class ComplianceRuleEngine:
    """
    Rule engine for validating compliance
    Evaluates products against defined compliance rules
    """

    def __init__(self):
        """Initialize rule engine"""
        self.rules: Dict[str, ComplianceRule] = {}
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default compliance rules"""
        default_rules = [
            # Voltage compliance
            ComplianceRule(
                rule_id='voltage_001',
                name='Rated Voltage Compliance',
                description='Product voltage must match standard ranges',
                standard='IEC 60364',
                condition='voltage_rating in [110, 220, 240, 440, 660]',
                mandatory=True,
                severity='critical'
            ),
            # Current capacity
            ComplianceRule(
                rule_id='current_001',
                name='Current Capacity Check',
                description='Current rating must be within safe limits',
                standard='IS 1554',
                condition='current_rating > 0 and current_rating <= 200',
                weight=0.9,
                mandatory=True,
                severity='error'
            ),
            # Material compliance
            ComplianceRule(
                rule_id='material_001',
                name='Conductor Material Compliance',
                description='Conductor must be copper or aluminum',
                standard='IS 1554 Part 1',
                condition='conductor_material in ["copper", "aluminum"]',
                mandatory=True,
                severity='critical'
            ),
            # Insulation compliance
            ComplianceRule(
                rule_id='insulation_001',
                name='Insulation Material Check',
                description='Insulation must be PVC, XLPE, or EPR',
                standard='IS 1554 Part 1',
                condition='insulation_material in ["pvc", "xlpe", "epr"]',
                mandatory=True,
                severity='critical'
            ),
            # Temperature rating
            ComplianceRule(
                rule_id='temperature_001',
                name='Temperature Rating Check',
                description='Operating temperature within safe range',
                standard='IS 1554',
                condition='temperature_rating >= -5 and temperature_rating <= 50',
                weight=0.8,
                severity='error'
            ),
            # Safety certification
            ComplianceRule(
                rule_id='cert_001',
                name='Safety Certification Required',
                description='Product must have BIS/IEC certification',
                standard='BIS',
                condition='has_bis_certification or has_iec_certification',
                mandatory=True,
                severity='critical'
            ),
            # IS compliance
            ComplianceRule(
                rule_id='is_001',
                name='Indian Standards Compliance',
                description='Product must comply with IS standards',
                standard='IS 1554',
                condition='complies_with_is_standard',
                weight=0.9,
                severity='error'
            ),
            # Environmental compliance
            ComplianceRule(
                rule_id='env_001',
                name='Environmental Compliance',
                description='Product must meet RoHS requirements',
                standard='RoHS 2015',
                condition='rohs_compliant',
                weight=0.7,
                severity='warning'
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def add_rule(self, rule: ComplianceRule):
        """Add compliance rule"""
        self.rules[rule.rule_id] = rule

    def evaluate_condition(self, condition: str, product_data: Dict) -> bool:
        """
        Evaluate a compliance condition
        Supports: field in [value1, value2], field > value, etc.
        """
        try:
            # Create safe evaluation context
            context = product_data.copy()
            
            # Support 'in' operator
            if ' in [' in condition:
                field, values_str = condition.split(' in [')
                field = field.strip()
                values = [v.strip().strip('"\'') for v in values_str.rstrip(']').split(',')]
                return context.get(field) in values

            # Support comparison operators
            if '>=' in condition:
                field, value = condition.split('>=')
                return float(context.get(field.strip(), -1)) >= float(value.strip())
            
            if '<=' in condition:
                field, value = condition.split('<=')
                return float(context.get(field.strip(), 999)) <= float(value.strip())
            
            if '>' in condition:
                field, value = condition.split('>')
                return float(context.get(field.strip(), -1)) > float(value.strip())
            
            if '<' in condition:
                field, value = condition.split('<')
                return float(context.get(field.strip(), 999)) < float(value.strip())

            # Support 'or' conditions
            if ' or ' in condition:
                parts = condition.split(' or ')
                return any(self.evaluate_condition(p.strip(), product_data) for p in parts)

            # Support 'and' conditions
            if ' and ' in condition:
                parts = condition.split(' and ')
                return all(self.evaluate_condition(p.strip(), product_data) for p in parts)

            return False
        except Exception as e:
            return False

    def check_compliance(self, product_data: Dict) -> List[ComplianceFinding]:
        """Check product compliance against all rules"""
        findings = []

        for rule in self.rules.values():
            result = self.evaluate_condition(rule.condition, product_data)
            
            if result:
                status = ComplianceStatus.FULLY_COMPLIANT
                message = f"✅ {rule.name}: Product complies with {rule.standard}"
            else:
                status = ComplianceStatus.NON_COMPLIANT
                message = f"❌ {rule.name}: Product does not comply with {rule.standard}"

            finding = ComplianceFinding(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                status=status,
                message=message,
                severity=rule.severity,
                weight=rule.weight
            )
            findings.append(finding)

        return findings

    def get_compliance_score(self, findings: List[ComplianceFinding]) -> float:
        """Calculate overall compliance score (0-100)"""
        if not findings:
            return 0

        total_weight = sum(f.weight for f in findings)
        compliant_weight = sum(
            f.weight for f in findings 
            if f.status == ComplianceStatus.FULLY_COMPLIANT
        )

        if total_weight == 0:
            return 0

        return (compliant_weight / total_weight) * 100


class CertificateVerifier:
    """
    Verifies product certificates
    Validates BIS, IEC, and other certifications
    """

    def __init__(self):
        """Initialize certificate verifier"""
        self.certificates = {}

    def add_certificate(
        self,
        product_id: str,
        certificate_type: str,  # BIS, IEC, UL, etc.
        certificate_number: str,
        issue_date: datetime,
        expiry_date: datetime,
        issuer: str,
        valid: bool = True
    ):
        """Register product certificate"""
        self.certificates[product_id] = {
            'certificate_type': certificate_type,
            'certificate_number': certificate_number,
            'issue_date': issue_date,
            'expiry_date': expiry_date,
            'issuer': issuer,
            'valid': valid,
            'is_expired': expiry_date < datetime.now()
        }

    def verify_certificate(self, product_id: str) -> Dict:
        """Verify product certificate"""
        if product_id not in self.certificates:
            return {
                'verified': False,
                'message': 'No certificate found',
                'status': ComplianceStatus.UNKNOWN
            }

        cert = self.certificates[product_id]

        if not cert['valid']:
            return {
                'verified': False,
                'message': f"Certificate {cert['certificate_number']} is invalid",
                'status': ComplianceStatus.NON_COMPLIANT
            }

        if cert['is_expired']:
            return {
                'verified': False,
                'message': f"Certificate expired on {cert['expiry_date'].date()}",
                'status': ComplianceStatus.NON_COMPLIANT,
                'expiry_date': cert['expiry_date']
            }

        return {
            'verified': True,
            'message': f"✅ {cert['certificate_type']} certified",
            'status': ComplianceStatus.FULLY_COMPLIANT,
            'certificate_number': cert['certificate_number'],
            'issuer': cert['issuer'],
            'expiry_date': cert['expiry_date']
        }

    def check_expiry_upcoming(self, product_id: str, days: int = 30) -> bool:
        """Check if certificate expires within N days"""
        if product_id not in self.certificates:
            return False

        cert = self.certificates[product_id]
        cutoff_date = datetime.now() + timedelta(days=days)
        return cert['expiry_date'] <= cutoff_date

    def get_expiring_certificates(self, days: int = 30) -> List[Dict]:
        """Get all certificates expiring within N days"""
        expiring = []
        for product_id, cert in self.certificates.items():
            if self.check_expiry_upcoming(product_id, days):
                expiring.append({
                    'product_id': product_id,
                    'certificate_type': cert['certificate_type'],
                    'expiry_date': cert['expiry_date'],
                    'days_remaining': (cert['expiry_date'] - datetime.now()).days
                })
        return sorted(expiring, key=lambda x: x['days_remaining'])


class ComplianceScorer:
    """
    Comprehensive compliance scoring system
    Calculates risk levels and compliance ratings
    """

    def __init__(self):
        """Initialize compliance scorer"""
        self.rule_engine = ComplianceRuleEngine()
        self.cert_verifier = CertificateVerifier()

    def score_product(self, product_data: Dict) -> Dict:
        """
        Generate comprehensive compliance score for product
        Returns: compliance_score, risk_level, findings, recommendations
        """
        # Run compliance checks
        findings = self.rule_engine.check_compliance(product_data)
        
        # Calculate compliance score
        compliance_score = self.rule_engine.get_compliance_score(findings)

        # Verify certificates
        product_id = product_data.get('product_id', 'unknown')
        cert_result = self.cert_verifier.verify_certificate(product_id)

        # Count violations
        critical_violations = sum(
            1 for f in findings 
            if f.status == ComplianceStatus.NON_COMPLIANT and f.severity == 'critical'
        )
        error_violations = sum(
            1 for f in findings 
            if f.status == ComplianceStatus.NON_COMPLIANT and f.severity == 'error'
        )
        warning_violations = sum(
            1 for f in findings 
            if f.status == ComplianceStatus.NON_COMPLIANT and f.severity == 'warning'
        )

        # Determine risk level
        if critical_violations > 0 or not cert_result['verified']:
            risk_level = RiskLevel.CRITICAL
        elif error_violations > 0:
            risk_level = RiskLevel.HIGH
        elif warning_violations > 0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Generate recommendations
        recommendations = []
        if critical_violations > 0:
            recommendations.append("🔴 CRITICAL: Do not use this product. Major compliance violations.")
        if not cert_result['verified']:
            recommendations.append("⚠️ Missing or invalid certification. Verify with manufacturer.")
        if warning_violations > 0:
            recommendations.append("🟡 Address warning-level compliance issues.")

        return {
            'product_id': product_id,
            'compliance_score': round(compliance_score, 2),
            'risk_level': risk_level.value,
            'certificate_status': cert_result.get('status', ComplianceStatus.UNKNOWN).value,
            'total_findings': len(findings),
            'violations': {
                'critical': critical_violations,
                'error': error_violations,
                'warning': warning_violations
            },
            'findings': [
                {
                    'rule_id': f.rule_id,
                    'rule_name': f.rule_name,
                    'status': f.status.value,
                    'message': f.message,
                    'severity': f.severity
                }
                for f in findings
            ],
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }

    def generate_compliance_report(
        self,
        products: List[Dict],
        title: str = "Compliance Report"
    ) -> Dict:
        """Generate compliance report for multiple products"""
        scores = [self.score_product(p) for p in products]

        total_compliant = sum(1 for s in scores if s['risk_level'] == 'LOW')
        total_at_risk = sum(1 for s in scores if s['risk_level'] in ['HIGH', 'CRITICAL'])

        return {
            'title': title,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_products': len(products),
                'compliant': total_compliant,
                'at_risk': total_at_risk,
                'avg_compliance_score': round(sum(s['compliance_score'] for s in scores) / len(scores), 2),
                'critical_violations': sum(s['violations']['critical'] for s in scores)
            },
            'product_scores': scores
        }


# Example usage
if __name__ == '__main__':
    scorer = ComplianceScorer()

    # Example product data
    product = {
        'product_id': 'WIRE-001',
        'name': '1.5 sqmm 3-core PVC Wire',
        'voltage_rating': 240,
        'current_rating': 16,
        'conductor_material': 'copper',
        'insulation_material': 'pvc',
        'temperature_rating': 40,
        'has_bis_certification': True,
        'has_iec_certification': True,
        'complies_with_is_standard': True,
        'rohs_compliant': True
    }

    # Add certificate
    scorer.cert_verifier.add_certificate(
        'WIRE-001',
        'BIS',
        'BIS/L-18789',
        datetime(2020, 1, 1),
        datetime(2030, 1, 1),
        'Bureau of Indian Standards'
    )

    # Score product
    score = scorer.score_product(product)
    print("\n📊 Compliance Score:")
    print(f"Product: {score['product_id']}")
    print(f"Compliance Score: {score['compliance_score']}/100")
    print(f"Risk Level: {score['risk_level']}")
    print(f"Violations: Critical={score['violations']['critical']}, Error={score['violations']['error']}")
    
    if score['recommendations']:
        print("Recommendations:")
        for rec in score['recommendations']:
            print(f"  {rec}")
