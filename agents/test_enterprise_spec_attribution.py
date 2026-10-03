"""
Test Enterprise Spec Attribution & Hard-Constraint Matching
Tests:
1. Verifiable Source Citations (page numbers, clause references, snippets)
2. Mandatory Hard-Constraint Validation (Pass/Fail disqualification prevention)
3. Directional Limits (MIN/MAX requirements)
4. Integration with Full Multi-Agent Workflow
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from agents.technical_agent.spec_matcher import TechnicalAgent, OEMProduct
from agents.master_agent.orchestrator import MasterAgent
from agents.shared.data_models import ConstraintType, SourceAttribution

print("="*80)
print("1. TESTING UNIT SPEC MATCHING WITH HARD CONSTRAINTS & ATTRIBUTION")
print("="*80)

tech = TechnicalAgent()

# Create a test OEM product with Aluminium conductor and 650V rating
sample_oem = OEMProduct(
    sku="TEST-AL-650V",
    product_name="Aluminium Wire 1.5 sq mm 650V",
    manufacturer="TestOEM",
    category="Wires & Cables",
    specifications={
        'conductor_material': 'Aluminium',
        'rated_voltage': '650V',
        'insulation_type': 'PVC',
        'cross_section_sqmm': 1.5,
        'current_rating_amps': 10
    }
)

# RFP specifications requiring Copper and 1100V with exact tender citations
rfp_specs = {
    'conductor_material': 'Copper',
    'rated_voltage': '1100V',
    'insulation_type': 'PVC',
    'cross_section_sqmm': 1.5,
    'current_rating_amps': 14
}

spec_attributions = {
    'conductor_material': SourceAttribution(
        page_number=12,
        clause_ref="Sec. III, Cl. 4.1",
        source_snippet="Conductor shall be annealed electrolytic copper as per IS 8130.",
        confidence_score=0.99
    ),
    'rated_voltage': SourceAttribution(
        page_number=13,
        clause_ref="Sec. III, Cl. 4.2",
        source_snippet="Operating voltage grade shall be 1100V AC.",
        confidence_score=0.98
    )
}

spec_constraints = {
    'conductor_material': 'hard',
    'rated_voltage': 'hard',
    'insulation_type': 'hard',
    'cross_section_sqmm': 'hard',
    'current_rating_amps': 'directional_min'
}

match_res = tech._calculate_spec_match(rfp_specs, sample_oem, spec_attributions, spec_constraints)

print(f"OEM SKU: {match_res.oem_product.sku}")
print(f"Spec Match %: {match_res.spec_match_percent}%")
print(f"Hard Constraint Passed: {match_res.hard_constraint_passed}")
print(f"Disqualification Risk: {match_res.disqualification_risk}")
print(f"Violations Count: {len(match_res.hard_constraint_violations)}")

assert match_res.hard_constraint_passed is False, "Expected hard constraint to fail for Aluminium vs Copper"
assert match_res.disqualification_risk == "CRITICAL_DISQUALIFIED", "Expected CRITICAL_DISQUALIFIED risk"
assert match_res.spec_match_percent <= 45.0, "Expected match percent to be capped at <= 45%"
print("✅ Hard-constraint failure test passed! Disqualification prevented.")

print("\n" + "="*80)
print("2. TESTING FULL MASTER AGENT WORKFLOW WITH ENTERPRISE CITATIONS")
print("="*80)

master = MasterAgent()
response = master.run_full_workflow()

print(master.print_scope_of_supply_table(response))

# Verify citations are present in the response
total_citations = sum(len(item.get('citations', [])) for item in response.scope_of_supply)
print(f"\n✅ Total Verified Citations in Response: {total_citations}")
assert total_citations > 0, "Expected citations to be linked in scope of supply"

for item in response.scope_of_supply:
    print(f"  • Item {item['sl_no']}: {item['rfp_product_name'][:30]} -> {len(item.get('citations', []))} citations | Risk: {item.get('disqualification_risk')}")

print("\n" + "="*80)
print("ALL ENTERPRISE ACCURACY & ATTRIBUTION TESTS PASSED SUCCESSFULLY!")
print("="*80)
