"""
Audit & Fidelity Test for Core Platform Functions:
1. Spec Extraction (SpecMatcher.parse_rfp_requirements)
2. Spec Matching & Gatekeeper Knockouts (SpecMatcher.find_matching_products)
3. Engineering Calculations (SpecCalculator: Voltage Drop, Power Capacity, Short Circuit, IR)
4. Landed Cost & Commodity Index Pricing (LandedCostCalculator, MetalCommodityPricingModel)
5. Win/Loss Analytics (WinLossAnalytics)
6. Compliance Checking (ComplianceRuleEngine)

Checks for:
- Repetitive outputs (invariance to inputs)
- Hardcoded mock values masquerading as real results
- Inaccurate physics/engineering calculations
"""
import sys
import os
import math
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'spec_comparer'))
sys.path.insert(0, str(ROOT / 'pdf_extraction'))

print("=" * 80)
print("AUDIT & FIDELITY TEST OF CORE PLATFORM FUNCTIONS")
print("=" * 80)

failures = []
warnings = []
passed_tests = 0

# ----------------------------------------------------------------------
# 1. TEST: Spec Extraction from Diverse RFP Texts
# ----------------------------------------------------------------------
print("\n[1] Testing SpecMatcher.parse_rfp_requirements across diverse specifications...")
try:
    from spec_comparer.app import OEMProductDatabase, SpecMatcher, SpecCalculator
    oem_data_path = ROOT / 'wires_cables_data' / 'wires_cables_data'
    db = OEMProductDatabase(str(oem_data_path))
    matcher = SpecMatcher(db)

    test_rfp_texts = [
        ("Line 1: 4C x 50 sq.mm Aluminium XLPE Armoured Cable 1100V conforming to IS 7098", 50.0, 4, "Aluminium", "XLPE", True, 1100.0),
        ("Line 2: 3 core 2.5 sq mm Copper PVC unarmoured flexible wire 650V", 2.5, 3, "Copper", "PVC", False, 650.0),
        ("Line 3: 1 core 630 sq.mm Copper XLPE Armoured cable 33kV", 630.0, 1, "Copper", "XLPE", True, 33000.0),
        ("Line 4: 2C x 1.5 sq mm Cu FRLS PVC wire 1.1 kV", 1.5, 2, "Copper", "FRLS", None, 1100.0),
    ]

    extracted_results = []
    for text, exp_size, exp_cores, exp_mat, exp_ins, exp_arm, exp_volt in test_rfp_texts:
        reqs = matcher.parse_rfp_requirements(text)
        if not reqs:
            failures.append(f"Spec extraction returned empty for: {text}")
            continue
        req = reqs[0]
        extracted_results.append(req)
        print(f"  Input: '{text[:55]}...'")
        print(f"    Extracted: size={req.get('conductor_size')}, cores={req.get('cores')}, mat={req.get('conductor_material')}, ins={req.get('insulation')}, arm={req.get('armoured')}, volt={req.get('voltage')}")

        if req.get('conductor_size') != exp_size:
            failures.append(f"Size mismatch: expected {exp_size}, got {req.get('conductor_size')}")
        if req.get('cores') != exp_cores:
            failures.append(f"Cores mismatch: expected {exp_cores}, got {req.get('cores')}")
        if req.get('conductor_material') != exp_mat:
            failures.append(f"Material mismatch: expected {exp_mat}, got {req.get('conductor_material')}")
        if exp_arm is not None and req.get('armoured') != exp_arm:
            failures.append(f"Armour mismatch: expected {exp_arm}, got {req.get('armoured')}")
        passed_tests += 1

    # Check for repetitive / hardcoded answers across distinct inputs
    sizes = [r.get('conductor_size') for r in extracted_results]
    if len(set(sizes)) == 1 and len(sizes) > 1:
        failures.append("HARDCODED/REPETITIVE: Spec extractor returned identical sizes for all inputs!")
    else:
        print("  ✅ Spec extractor outputs vary dynamically with input specs (No hardcoding detected).")

except Exception as e:
    failures.append(f"Spec extraction test failed with exception: {e}")


# ----------------------------------------------------------------------
# 2. TEST: Spec Matching & Gatekeeper Knockout Logic
# ----------------------------------------------------------------------
print("\n[2] Testing SpecMatcher Knockout & Dynamic Scoring Engine...")
try:
    # Test requirement: 4C x 50 sq.mm Aluminium XLPE Armoured Cable
    req_al_armoured = {
        'conductor_size': 50.0,
        'cores': 4,
        'conductor_material': 'Aluminium',
        'insulation': 'XLPE',
        'armoured': True,
        'voltage': 1100.0,
        'requirement_type': 'wire_cable'
    }
    matches_al = matcher.find_matching_products(req_al_armoured, top_n=5)
    print(f"  Queried 4C x 50 sq.mm Aluminium Armoured -> Found {len(matches_al)} top candidates.")

    # Test requirement: 3C x 2.5 sq.mm Copper PVC Unarmoured Cable
    req_cu_unarm = {
        'conductor_size': 2.5,
        'cores': 3,
        'conductor_material': 'Copper',
        'insulation': 'PVC',
        'armoured': False,
        'voltage': 1100.0,
        'requirement_type': 'wire_cable'
    }
    matches_cu = matcher.find_matching_products(req_cu_unarm, top_n=5)
    print(f"  Queried 3C x 2.5 sq.mm Copper Unarmoured -> Found {len(matches_cu)} top candidates.")

    if not matches_al or not matches_cu:
        failures.append("Matching engine returned empty product list from OEM database.")
    else:
        # Check that top candidate specs actually differ between the two queries
        top_al = matches_al[0]
        top_cu = matches_cu[0]

        print(f"    Top Al Match: OEM={top_al.get('oem')}, Code={top_al.get('product_code')}, Score={top_al.get('match_score')}, Size={top_al.get('conductor_size')}, Mat={top_al.get('conductor_material')}")
        print(f"    Top Cu Match: OEM={top_cu.get('oem')}, Code={top_cu.get('product_code')}, Score={top_cu.get('match_score')}, Size={top_cu.get('conductor_size')}, Mat={top_cu.get('conductor_material')}")

        if top_al.get('product_code') == top_cu.get('product_code'):
            failures.append("REPETITIVE/STUB: Matching engine returned identical product for two completely different cable requirements!")
        else:
            print("  ✅ Matching engine returns distinct, requirement-tailored products across queries.")

        # Verify Knockout Enforcement: Offer a Copper cable for Aluminium requirement
        # In matches_al, verify that any Copper products are flagged DISQUALIFIED
        for p in matches_al:
            mat = str(p.get('conductor_material', '')).lower()
            if 'copper' in mat or 'cu' in mat:
                if p.get('is_qualified') is True:
                    failures.append(f"INACCURACY: Copper cable ({p.get('product_code')}) was marked qualified for Aluminium requirement!")
                else:
                    print(f"  ✅ Gatekeeper knockout correctly disqualified mismatched material: {p.get('knockout_reasons')}")
                    passed_tests += 1
                    break
        passed_tests += 1

except Exception as e:
    failures.append(f"Spec matching test failed with exception: {e}")


# ----------------------------------------------------------------------
# 3. TEST: Engineering Calculations Physics & Non-Linearity
# ----------------------------------------------------------------------
print("\n[3] Testing SpecCalculator (Voltage Drop, Power Capacity, Short Circuit)...")
try:
    calc = SpecCalculator()

    # Test 1: Voltage drop scaling with length (should be strictly linear with length)
    vd_100 = calc.calculate_voltage_drop(cable_size=50.0, length=100.0, current=80.0, material='copper', voltage=415.0, cores=3)
    vd_500 = calc.calculate_voltage_drop(cable_size=50.0, length=500.0, current=80.0, material='copper', voltage=415.0, cores=3)
    drop_100 = vd_100['calculation']['voltage_drop_volts']
    drop_500 = vd_500['calculation']['voltage_drop_volts']
    ratio_len = drop_500 / drop_100 if drop_100 else 0
    print(f"  Voltage drop at 100m: {drop_100}V | at 500m: {drop_500}V (Ratio: {ratio_len:.2f}, Expected ~5.00)")
    if abs(ratio_len - 5.0) > 0.05:
        failures.append(f"INACCURACY: Voltage drop does not scale linearly with length (ratio={ratio_len})")
    else:
        passed_tests += 1

    # Test 2: Copper vs Aluminium resistivity ratio (Aluminium should have ~1.6 - 1.7x higher drop)
    vd_cu = calc.calculate_voltage_drop(cable_size=50.0, length=200.0, current=80.0, material='copper', voltage=415.0, cores=3)
    vd_al = calc.calculate_voltage_drop(cable_size=50.0, length=200.0, current=80.0, material='aluminum', voltage=415.0, cores=3)
    cu_drop = vd_cu['calculation']['voltage_drop_volts']
    al_drop = vd_al['calculation']['voltage_drop_volts']
    ratio_mat = al_drop / cu_drop if cu_drop else 0
    print(f"  Copper drop: {cu_drop}V | Aluminium drop: {al_drop}V (Ratio: {ratio_mat:.2f}, Expected ~1.60 - 1.65)")
    if not (1.50 <= ratio_mat <= 1.75):
        failures.append(f"INACCURACY: Aluminium/Copper resistivity ratio is unrealistic ({ratio_mat:.2f})")
    else:
        passed_tests += 1

    # Test 3: Short circuit capacity scaling with cross-section
    sc_16 = calc.calculate_short_circuit_capacity(cable_size=16.0, material='copper')
    sc_50 = calc.calculate_short_circuit_capacity(cable_size=50.0, material='copper')
    ka_16 = sc_16['calculation']['withstand_current_1s_kA']
    ka_50 = sc_50['calculation']['withstand_current_1s_kA']
    ratio_sc = ka_50 / ka_16 if ka_16 else 0
    print(f"  16 sq.mm 1s Isc: {ka_16} kA | 50 sq.mm 1s Isc: {ka_50} kA (Ratio: {ratio_sc:.2f}, Expected 50/16 = 3.125)")
    if abs(ratio_sc - (50.0 / 16.0)) > 0.05:
        failures.append(f"INACCURACY: Short-circuit capacity did not scale with conductor area ({ratio_sc:.2f})")
    else:
        passed_tests += 1

    # Test 4: Insulation resistance inverse length scaling
    ir_100 = calc.calculate_insulation_resistance(cable_size=50.0, length=100.0, insulation_type='XLPE', voltage_rating=1100)
    ir_1000 = calc.calculate_insulation_resistance(cable_size=50.0, length=1000.0, insulation_type='XLPE', voltage_rating=1100)
    res_100 = ir_100['calculation']['expected_ir_mohm']
    res_1000 = ir_1000['calculation']['expected_ir_mohm']
    ratio_ir = res_100 / res_1000 if res_1000 else 0
    print(f"  IR at 100m: {res_100} MΩ | at 1000m: {res_1000} MΩ (Ratio: {ratio_ir:.2f}, Expected 10.0)")
    if abs(ratio_ir - 10.0) > 0.1:
        failures.append(f"INACCURACY: Insulation resistance does not scale inversely with length ({ratio_ir:.2f})")
    else:
        passed_tests += 1

except Exception as e:
    failures.append(f"SpecCalculator test failed with exception: {e}")


# ----------------------------------------------------------------------
# 4. TEST: Commodity-Driven Landed Cost Optimization Engine
# ----------------------------------------------------------------------
print("\n[4] Testing LandedCostCalculator & Metal Index Pricing Physics...")
try:
    from price_optimization import CommodityRates, CommodityRatesManager, MetalCommodityPricingModel, LandedCostCalculator

    model = MetalCommodityPricingModel()

    # Physics test: Bare metal conductor weight for 4C x 50 sq.mm
    # Cu density = 8.89 g/cm3, stranding factor = 1.02 -> 4 * 50 * 0.00889 * 1.02 * 1000 = ~1813.56 kg/km
    wt_cu = model.calculate_conductor_weight_per_km(50.0, 4, 'copper')
    wt_al = model.calculate_conductor_weight_per_km(50.0, 4, 'aluminium')
    print(f"  4C x 50 sq.mm Weight: Copper = {wt_cu:.2f} kg/km | Aluminium = {wt_al:.2f} kg/km")
    if not (1800.0 <= wt_cu <= 1830.0):
        failures.append(f"INACCURACY: Copper weight calculation inaccurate ({wt_cu})")
    if not (540.0 <= wt_al <= 560.0):
        failures.append(f"INACCURACY: Aluminium weight calculation inaccurate ({wt_al})")
    passed_tests += 2

    # Dynamic pricing test: Changing spot rate should directly alter line cost
    rates_standard = CommodityRates(copper_inr_per_kg=780.0, aluminium_inr_per_kg=240.0)
    rates_high_copper = CommodityRates(copper_inr_per_kg=950.0, aluminium_inr_per_kg=240.0)

    calc_std = LandedCostCalculator(commodity_engine=MetalCommodityPricingModel(rates=rates_standard))
    calc_high = LandedCostCalculator(commodity_engine=MetalCommodityPricingModel(rates=rates_high_copper))

    boq_std = calc_std.calculate_boq_line_cost(conductor_size_sqmm=50.0, no_of_cores=4, material='copper', quantity_meters=1000.0)
    boq_high = calc_high.calculate_boq_line_cost(conductor_size_sqmm=50.0, no_of_cores=4, material='copper', quantity_meters=1000.0)

    cost_std = boq_std['totals']['final_landed_total']
    cost_high = boq_high['totals']['final_landed_total']
    diff_metal = cost_high - cost_std
    print(f"  Landed cost at Cu ₹780/kg: ₹{cost_std:,.2f} | at Cu ₹950/kg: ₹{cost_high:,.2f} (Diff: +₹{diff_metal:,.2f})")

    # Metal difference should be approx: 1.81356 tonnes * (950 - 780) * 1000 * 1.12 margin * 1.18 gst = ~407,000 INR
    expected_diff = (wt_cu) * (950.0 - 780.0) * 1.12 * 1.18
    print(f"  Expected dynamic difference: ₹{expected_diff:,.2f}")
    if abs(diff_metal - expected_diff) > 20000.0:
        failures.append(f"INACCURACY: Landed cost does not accurately reflect metal commodity index variation (diff={diff_metal}, exp={expected_diff})")
    else:
        print("  ✅ Landed cost calculations are mathematically rigorous and dynamically index-tied.")
        passed_tests += 1

except Exception as e:
    failures.append(f"Landed cost test failed with exception: {e}")


# ----------------------------------------------------------------------
# 5. TEST: Win/Loss Analytics Engine
# ----------------------------------------------------------------------
print("\n[5] Testing Win/Loss Analytics Cohort Generation & Win Ratio Math...")
try:
    from analytics.win_loss_analytics import WinLossAnalytics
    from database.db_engine import DatabaseManager

    db_m = DatabaseManager()
    session = db_m.get_session()
    wl = WinLossAnalytics(session_factory=lambda: db_m.get_session())

    # Test truthful response when no bids exist (production accounting mode)
    truthful_res = wl.get_win_loss_ratio_by_rfp(session, "UNSEEN_RFP_999", allow_synthetic_fallback=False)
    assert truthful_res['status'] == 'no_data' and truthful_res['total_bids'] == 0
    print("  [PASS] Audited production mode truthfully reports no_data when no historical bids exist.")
    passed_tests += 1

    # Test deterministic demo cohorts when explicitly requested
    rfp_a = "GEM/2025/B/9991111"
    rfp_b = "GEM/2025/B/8882222"

    res_a = wl.get_win_loss_ratio_by_rfp(session, rfp_a, allow_synthetic_fallback=True)
    res_b = wl.get_win_loss_ratio_by_rfp(session, rfp_b, allow_synthetic_fallback=True)

    win_pct_a = res_a['win_percentage']
    win_pct_b = res_b['win_percentage']
    total_val_a = res_a['bid_value']['total_value']
    total_val_b = res_b['bid_value']['total_value']

    print(f"  RFP A ({rfp_a}): Win Rate = {win_pct_a}%, Total Bid Value = ₹{total_val_a:,.2f}, Wins/Loss = {res_a['won']}/{res_a['lost']}")
    print(f"  RFP B ({rfp_b}): Win Rate = {win_pct_b}%, Total Bid Value = ₹{total_val_b:,.2f}, Wins/Loss = {res_b['won']}/{res_b['lost']}")

    # Check mathematical consistency: win_ratio = won / lost
    if res_a['lost'] > 0:
        expected_ratio_a = round(res_a['won'] / res_a['lost'], 2)
        if abs(res_a['win_ratio'] - expected_ratio_a) > 0.05:
            failures.append(f"INACCURACY: Win ratio math wrong for RFP A: {res_a['win_ratio']} != {expected_ratio_a}")
        else:
            passed_tests += 1

    # Check value consistency: total_value = won_value + lost_value
    expected_total_a = round(res_a['bid_value']['won_value'] + res_a['bid_value']['lost_value'], 2)
    if abs(total_val_a - expected_total_a) > 1.0:
        failures.append(f"INACCURACY: Total bid value ({total_val_a}) does not match won+lost sum ({expected_total_a})")
    else:
        passed_tests += 1

    # Check variation across RFPs
    if total_val_a == total_val_b and win_pct_a == win_pct_b:
        warnings.append("SUSPICIOUS: Win/loss analytics generated identical total value for two different RFPs.")
    else:
        print("  ✅ Win/loss analytics metrics vary dynamically and maintain internal algebraic consistency.")
        passed_tests += 1

    session.close()

except Exception as e:
    failures.append(f"Win/loss analytics test failed with exception: {e}")


# ----------------------------------------------------------------------
# 6. TEST: Compliance Checker Rule Engine
# ----------------------------------------------------------------------
print("\n[6] Testing ComplianceRuleEngine (IS 694, IS 7098, IEC 60502)...")
try:
    from compliance_and_standards.compliance_checker import ComplianceRuleEngine
    checker = ComplianceRuleEngine()

    # Conforming Cable: Standard Copper PVC wire with BIS certification
    conforming_product = {
        'conductor_material': 'copper',
        'insulation_material': 'pvc',
        'voltage_rating': 1100,
        'current_rating': 50,
        'temperature_rating': 70,
        'has_bis_certification': True,
        'complies_with_is_standard': True,
        'rohs_compliant': True,
        'standard': 'IS 694'
    }
    # Non-Conforming Cable: Invalid conductor, insulation, voltage, current and certifications
    non_conforming_product = {
        'conductor_material': 'iron',
        'insulation_material': 'paper',
        'voltage_rating': 999999,
        'current_rating': 9000,
        'temperature_rating': 250,
        'has_bis_certification': False,
        'has_iec_certification': False
    }

    findings_good = checker.check_compliance(conforming_product)
    score_good = checker.get_compliance_score(findings_good)

    findings_bad = checker.check_compliance(non_conforming_product)
    score_bad = checker.get_compliance_score(findings_bad)

    print(f"  Conforming product score:     {score_good:.1f}%")
    print(f"  Non-conforming product score: {score_bad:.1f}%")

    # Verify score differentiation
    if score_bad >= score_good or score_good < 90 or score_bad > 10:
        failures.append(f"INACCURACY: Compliance checker gave scores (good={score_good}, bad={score_bad}) that do not reflect compliance!")
    else:
        print("  [PASS] Compliance checker correctly validates standard specs and rejects non-conforming parameters.")
        passed_tests += 1

except Exception as e:
    failures.append(f"ComplianceRuleEngine test failed with exception: {e}")


# ----------------------------------------------------------------------
# 7. TEST: IEEMA Price Variation Clause (PVC) Engine
# ----------------------------------------------------------------------
print("\n[7] Testing IEEMA Price Variation Clause (PVC) Engine...")
try:
    from core.procurement_standards import IEEMAPriceVariationEngine, TechnicalDeviationEngine, TenderSecurityEngine

    base_p0 = 1000000.0  # 10 Lakh INR / km
    base_indices = {'copper': 750.0, 'aluminium': 220.0, 'polymer_cc': 110.0, 'steel_fe': 65.0, 'labour_fuel': 100.0}
    delivery_indices = {'copper': 900.0, 'aluminium': 264.0, 'polymer_cc': 121.0, 'steel_fe': 71.5, 'labour_fuel': 105.0}

    # Test Aluminium Cable: Al price surged +20% (264/220 = 1.20)
    pvc_al = IEEMAPriceVariationEngine.calculate_pvc(
        base_price_inr=base_p0,
        cable_category='LT_ALUMINIUM_XLPE_ARMOURED',
        base_indices=base_indices,
        delivery_indices=delivery_indices,
        quantity_km=5.0
    )
    print(f"  Al Cable Base: ₹{pvc_al['base_unit_price']:,.2f} -> Escalated: ₹{pvc_al['escalated_unit_price']:,.2f} (+{pvc_al['variation_percentage']}%)")
    print(f"  Total PVC Delta for 5km: +₹{pvc_al['total_pvc_delta']:,.2f}")

    if pvc_al['escalated_unit_price'] <= base_p0 or pvc_al['variation_percentage'] <= 0:
        failures.append("INACCURACY: IEEMA PVC failed to escalate price upon metal index surge!")
    else:
        print("  [PASS] IEEMA PVC calculates statutory price variations and lot deltas accurately.")
        passed_tests += 1

    # ------------------------------------------------------------------
    # 8. TEST: Schedule of Technical Deviations (Form F-4)
    # ------------------------------------------------------------------
    print("\n[8] Testing Technical Deviation Statement Generator (Form F-4)...")
    rfp_req = {'conductor_material': 'Aluminium', 'size_sqmm': 50.0, 'insulation_type': 'XLPE', 'voltage_rating': 1100}
    offered_sup = {'conductor_material': 'Aluminium', 'size_sqmm': 70.0, 'insulation_type': 'XLPE', 'voltage_rating': 1100} # Superior gauge
    offered_bad = {'conductor_material': 'Copper', 'size_sqmm': 25.0, 'insulation_type': 'PVC', 'voltage_rating': 650}    # Non-compliant

    dev_sup = TechnicalDeviationEngine.generate_schedule(rfp_req, offered_sup)
    dev_bad = TechnicalDeviationEngine.generate_schedule(rfp_req, offered_bad)

    has_superior = any(d.compliance_status == 'SUPERIOR' for d in dev_sup)
    has_high_risk = any(d.risk_level == 'HIGH' for d in dev_bad)

    if not has_superior or not has_high_risk:
        failures.append("INACCURACY: Technical deviation engine failed to classify superior vs high-risk deviations properly!")
    else:
        print(f"  Generated {len(dev_sup)} clauses for compliant bid; identified superior gauge: {has_superior}")
        print(f"  Identified critical high-risk clauses for non-compliant bid: {has_high_risk}")
        csv_str = TechnicalDeviationEngine.export_deviations_csv(dev_sup)
        assert 'Clause No.' in csv_str and 'Deviation Category' in csv_str
        print("  [PASS] Schedule of Deviations correctly evaluates clause risks and exports Form F-4 CSV.")
        passed_tests += 1

    # ------------------------------------------------------------------
    # 9. TEST: EMD / PBG Statutory Exemption Rules Engine
    # ------------------------------------------------------------------
    print("\n[9] Testing Tender Guarantee & Exemption Engine (MSME / DPIIT Startup)...")
    tender_val = 50000000.0  # 5 Crore INR tender (Standard EMD 2% = 10 Lakhs)
    msme_vendor = {'is_msme': True, 'udyam_registration_no': 'UDYAM-MH-01-0012345'}
    regular_vendor = {'is_msme': False}

    res_msme = TenderSecurityEngine.evaluate_security_exemptions(tender_val, msme_vendor)
    res_reg = TenderSecurityEngine.evaluate_security_exemptions(tender_val, regular_vendor)

    print(f"  Regular Bidder EMD Payable: ₹{res_reg['payable_emd_amount']:,.2f} (Exempt: {res_reg['is_emd_exempt']})")
    print(f"  MSME Bidder EMD Payable:    ₹{res_msme['payable_emd_amount']:,.2f} (Savings: ₹{res_msme['bidder_statutory_savings']:,.2f})")

    if not res_msme['is_emd_exempt'] or res_msme['payable_emd_amount'] != 0.0 or res_reg['payable_emd_amount'] != 1000000.0:
        failures.append("INACCURACY: Tender guarantee engine failed to enforce statutory MSME EMD exemption!")
    else:
        print("  [PASS] EMD / PBG rules engine correctly enforces statutory public procurement exemptions.")
        passed_tests += 1

except Exception as e:
    failures.append(f"Procurement standards test failed with exception: {e}")
# ----------------------------------------------------------------------
print("\n" + "=" * 80)
print("TEST AUDIT SUMMARY")
print("=" * 80)
print(f"Passed Checks: {passed_tests}")
print(f"Warnings:      {len(warnings)}")
for w in warnings:
    print(f"  [WARN] {w}")
print(f"Failures:      {len(failures)}")
for f in failures:
    print(f"  [FAIL] {f}")

if not failures:
    print("\n[SUCCESS] ALL CORE FUNCTIONS VALIDATED: NO HARDCODED OR INACCURATE STUBS DETECTED!")
    sys.exit(0)
else:
    print("\n[ALERT] AUDIT IDENTIFIED ISSUES TO RESOLVE.")
    sys.exit(1)

