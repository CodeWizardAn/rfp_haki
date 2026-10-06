"""
Unit tests for enterprise compliance standards and regulatory validation
Verifies LT (1.1kV), HT (11kV), industrial currents (>200A), and operating temperatures (70-90°C).
"""

import pytest
from compliance_checker import ComplianceRuleEngine, ComplianceStatus

def test_lt_1100v_cable_compliance():
    """Verify standard 1100V LT cable passes voltage compliance without false negatives"""
    engine = ComplianceRuleEngine()
    product_data = {
        'voltage_rating': '1100V',
        'current_rating': 320,  # 320A feeder cable
        'conductor_material': 'copper',
        'insulation_material': 'xlpe',
        'temperature_rating': 90,  # 90°C continuous operating temperature
        'has_bis_certification': True,
        'has_iec_certification': True,
        'complies_with_is_standard': True,
        'rohs_compliant': True
    }

    findings = engine.check_compliance(product_data)
    voltage_finding = next((f for f in findings if f.rule_id == 'voltage_001'), None)
    current_finding = next((f for f in findings if f.rule_id == 'current_001'), None)
    temp_finding = next((f for f in findings if f.rule_id == 'temperature_001'), None)

    assert voltage_finding is not None
    assert voltage_finding.status == ComplianceStatus.FULLY_COMPLIANT, f"Voltage failed: {voltage_finding.message}"

    assert current_finding is not None
    assert current_finding.status == ComplianceStatus.FULLY_COMPLIANT, f"Current failed: {current_finding.message}"

    assert temp_finding is not None
    assert temp_finding.status == ComplianceStatus.FULLY_COMPLIANT, f"Temp failed: {temp_finding.message}"

    score = engine.get_compliance_score(findings)
    assert score == 100.0, f"Expected 100% compliance, got {score}"


def test_ht_11kv_cable_compliance():
    """Verify standard 11kV HT cable passes voltage compliance"""
    engine = ComplianceRuleEngine()
    product_data = {
        'voltage_rating': 11000,
        'current_rating': 450,
        'conductor_material': 'aluminium',
        'insulation_material': 'xlpe',
        'temperature_rating': 90,
        'has_bis_certification': True,
        'complies_with_is_standard': True,
        'rohs_compliant': True
    }

    findings = engine.check_compliance(product_data)
    voltage_finding = next((f for f in findings if f.rule_id == 'voltage_001'), None)
    assert voltage_finding.status == ComplianceStatus.FULLY_COMPLIANT


def test_missing_mandatory_certification():
    """Verify missing certification triggers critical non-compliance"""
    engine = ComplianceRuleEngine()
    product_data = {
        'voltage_rating': 1100,
        'current_rating': 100,
        'conductor_material': 'copper',
        'insulation_material': 'pvc',
        'temperature_rating': 70,
        'has_bis_certification': False,
        'has_iec_certification': False,
        'complies_with_is_standard': True,
        'rohs_compliant': True
    }

    findings = engine.check_compliance(product_data)
    cert_finding = next((f for f in findings if f.rule_id == 'cert_001'), None)
    assert cert_finding.status == ComplianceStatus.NON_COMPLIANT
    assert cert_finding.severity == 'critical'
