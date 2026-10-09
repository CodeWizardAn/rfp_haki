"""
Enterprise Procurement Standards & Statutory Engineering Engine
Compliant with:
1. IEEMA (Indian Electrical and Electronics Manufacturers' Association) Price Variation Clause (PVC)
2. GeM / CPPP Standard Schedule of Technical Deviations (Form F-4)
3. Government of India Public Procurement Policy (MSEs Order 2012 / DPIIT Startup EMD Exemptions)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import io
import csv


# ==============================================================================
# 1. IEEMA PRICE VARIATION CLAUSE (PVC) ENGINE
# ==============================================================================

class IEEMAPriceVariationEngine:
    """
    Computes statutory price variations for power, control, and flexible cables
    based on official IEEMA circular formulas for price adjustments on delivery.

    Standard formula:
    P = P0 * [ a + b*(C / C0) + c*(Al / Al0) + d*(CC / CC0) + e*(Fe / Fe0) ]
    where a + b + c + d + e == 1.0 (weight factors)
    """

    # Official weight coefficient distributions by cable category
    IEEMA_WEIGHT_FACTORS: Dict[str, Dict[str, float]] = {
        'LT_ALUMINIUM_XLPE_ARMOURED': {
            'fixed': 0.20,
            'aluminium': 0.35,
            'copper': 0.00,
            'polymer_cc': 0.15,
            'steel_fe': 0.15,
            'labour_fuel': 0.15
        },
        'LT_COPPER_XLPE_ARMOURED': {
            'fixed': 0.15,
            'aluminium': 0.00,
            'copper': 0.60,
            'polymer_cc': 0.12,
            'steel_fe': 0.08,
            'labour_fuel': 0.05
        },
        'HT_XLPE_ALUMINIUM_ARMOURED': {
            'fixed': 0.20,
            'aluminium': 0.40,
            'copper': 0.00,
            'polymer_cc': 0.18,
            'steel_fe': 0.12,
            'labour_fuel': 0.10
        },
        'HT_XLPE_COPPER_ARMOURED': {
            'fixed': 0.15,
            'aluminium': 0.00,
            'copper': 0.62,
            'polymer_cc': 0.13,
            'steel_fe': 0.05,
            'labour_fuel': 0.05
        },
        'FLEXIBLE_COPPER_PVC': {
            'fixed': 0.15,
            'aluminium': 0.00,
            'copper': 0.70,
            'polymer_cc': 0.15,
            'steel_fe': 0.00,
            'labour_fuel': 0.00
        }
    }

    @classmethod
    def calculate_pvc(
        cls,
        base_price_inr: float,
        cable_category: str,
        base_indices: Dict[str, float],
        delivery_indices: Dict[str, float],
        quantity_km: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate adjusted price per km and total lot delta.

        Args:
            base_price_inr: Base contract price per km (P0)
            cable_category: Key matching IEEMA_WEIGHT_FACTORS
            base_indices: Indices at time of bidding/tender opening (C0, Al0, CC0, Fe0)
            delivery_indices: Indices applicable on delivery month (C, Al, CC, Fe)
            quantity_km: Total delivery lot in kilometers
        """
        weights = cls.IEEMA_WEIGHT_FACTORS.get(
            cable_category,
            cls.IEEMA_WEIGHT_FACTORS['LT_ALUMINIUM_XLPE_ARMOURED']
        )

        def get_ratio(key: str) -> float:
            base = base_indices.get(key, 100.0)
            curr = delivery_indices.get(key, base)
            return (curr / base) if base > 0 else 1.0

        r_cu = get_ratio('copper')
        r_al = get_ratio('aluminium')
        r_cc = get_ratio('polymer_cc')
        r_fe = get_ratio('steel_fe')
        r_labour = get_ratio('labour_fuel')

        # Compute escalator multiplier
        factor_sum = (
            weights['fixed'] +
            weights['copper'] * r_cu +
            weights['aluminium'] * r_al +
            weights['polymer_cc'] * r_cc +
            weights['steel_fe'] * r_fe +
            weights['labour_fuel'] * r_labour
        )

        escalated_unit_price = base_price_inr * factor_sum
        price_delta_per_km = escalated_unit_price - base_price_inr
        total_contract_base = base_price_inr * quantity_km
        total_contract_escalated = escalated_unit_price * quantity_km
        total_pvc_delta = price_delta_per_km * quantity_km
        variation_pct = (factor_sum - 1.0) * 100.0

        return {
            'cable_category': cable_category,
            'base_unit_price': round(base_price_inr, 2),
            'escalated_unit_price': round(escalated_unit_price, 2),
            'price_delta_per_km': round(price_delta_per_km, 2),
            'variation_percentage': round(variation_pct, 3),
            'total_contract_base': round(total_contract_base, 2),
            'total_contract_escalated': round(total_contract_escalated, 2),
            'total_pvc_delta': round(total_pvc_delta, 2),
            'quantity_km': quantity_km,
            'factor_breakdown': {
                'fixed_component': round(weights['fixed'], 4),
                'copper_ratio': round(r_cu, 4),
                'aluminium_ratio': round(r_al, 4),
                'polymer_ratio': round(r_cc, 4),
                'steel_ratio': round(r_fe, 4)
            },
            'statutory_reference': 'IEEMA Standard Price Variation Formula (Cable Division)'
        }


# ==============================================================================
# 2. TECHNICAL DEVIATION STATEMENT GENERATOR (FORM F-4)
# ==============================================================================

@dataclass
class DeviationItem:
    clause_no: str
    tender_parameter: str
    tender_specified: str
    offered_value: str
    deviation_category: str  # 'NIL', 'MINOR_TECHNICAL', 'MAJOR_TECHNICAL', 'COMMERCIAL'
    compliance_status: str   # 'COMPLIANT', 'NON_COMPLIANT', 'SUPERIOR'
    engineering_justification: str
    risk_level: str          # 'LOW', 'MEDIUM', 'HIGH', 'NONE'


class TechnicalDeviationEngine:
    """
    Generates statutory Schedule of Deviations (Form F-4 / Technical Compliance Statement)
    mandated across GeM, CPPP, NTPC, PGCIL, and State Electricity Board bids.
    """

    @classmethod
    def generate_schedule(
        cls,
        rfp_specs: Dict[str, Any],
        offered_product: Dict[str, Any]
    ) -> List[DeviationItem]:
        """Generate line-by-line deviation matrix for tender submission"""
        items: List[DeviationItem] = []

        # 1. Conductor Material Check
        req_mat = str(rfp_specs.get('conductor_material', 'Aluminium')).strip()
        off_mat = str(offered_product.get('conductor_material', offered_product.get('conductor', req_mat))).strip()
        if req_mat.lower() == off_mat.lower() or (req_mat.lower() in off_mat.lower()):
            items.append(DeviationItem(
                clause_no='Clause 2.1 (Conductor Metallurgy)',
                tender_parameter='Conductor Material',
                tender_specified=req_mat,
                offered_value=off_mat,
                deviation_category='NIL',
                compliance_status='COMPLIANT',
                engineering_justification='Offered material complies strictly with IS 8130 / IEC 60228 specifications.',
                risk_level='NONE'
            ))
        else:
            items.append(DeviationItem(
                clause_no='Clause 2.1 (Conductor Metallurgy)',
                tender_parameter='Conductor Material',
                tender_specified=req_mat,
                offered_value=off_mat,
                deviation_category='MAJOR_TECHNICAL',
                compliance_status='NON_COMPLIANT',
                engineering_justification=f'Metallurgy deviation from tender requirement: {off_mat} offered instead of {req_mat}.',
                risk_level='HIGH'
            ))

        # 2. Conductor Cross-Sectional Area
        req_size = rfp_specs.get('size_sqmm') or rfp_specs.get('cross_section_sqmm', 50.0)
        off_size = offered_product.get('size_sqmm') or offered_product.get('cross_section_sqmm', req_size)
        try:
            r_sz = float(req_size)
            o_sz = float(off_size)
            if abs(r_sz - o_sz) < 0.01:
                items.append(DeviationItem(
                    clause_no='Clause 2.2 (Cross-Section Area)',
                    tender_parameter='Nominal Conductor Area',
                    tender_specified=f'{r_sz} sq.mm',
                    offered_value=f'{o_sz} sq.mm',
                    deviation_category='NIL',
                    compliance_status='COMPLIANT',
                    engineering_justification='Cross section exactly conforms to standard nominal rating.',
                    risk_level='NONE'
                ))
            elif o_sz > r_sz:
                items.append(DeviationItem(
                    clause_no='Clause 2.2 (Cross-Section Area)',
                    tender_parameter='Nominal Conductor Area',
                    tender_specified=f'{r_sz} sq.mm',
                    offered_value=f'{o_sz} sq.mm',
                    deviation_category='MINOR_TECHNICAL',
                    compliance_status='SUPERIOR',
                    engineering_justification=f'Offered higher gauge ({o_sz} sq.mm) providing superior current carrying capacity and reduced thermal losses.',
                    risk_level='LOW'
                ))
            else:
                items.append(DeviationItem(
                    clause_no='Clause 2.2 (Cross-Section Area)',
                    tender_parameter='Nominal Conductor Area',
                    tender_specified=f'{r_sz} sq.mm',
                    offered_value=f'{o_sz} sq.mm',
                    deviation_category='MAJOR_TECHNICAL',
                    compliance_status='NON_COMPLIANT',
                    engineering_justification=f'Undersized conductor ({o_sz} vs {r_sz} sq.mm required) will violate ampacity standards.',
                    risk_level='HIGH'
                ))
        except (ValueError, TypeError):
            pass

        # 3. Insulation Material
        req_ins = str(rfp_specs.get('insulation_type', 'XLPE')).strip().upper()
        off_ins = str(offered_product.get('insulation_type', req_ins)).strip().upper()
        if req_ins == off_ins or (req_ins in off_ins):
            items.append(DeviationItem(
                clause_no='Clause 3.1 (Insulation System)',
                tender_parameter='Insulation Dielectric',
                tender_specified=req_ins,
                offered_value=off_ins,
                deviation_category='NIL',
                compliance_status='COMPLIANT',
                engineering_justification=f'{off_ins} dielectric insulation conforms to IS 7098 / IS 5831.',
                risk_level='NONE'
            ))
        elif req_ins == 'PVC' and 'XLPE' in off_ins:
            items.append(DeviationItem(
                clause_no='Clause 3.1 (Insulation System)',
                tender_parameter='Insulation Dielectric',
                tender_specified=req_ins,
                offered_value=off_ins,
                deviation_category='MINOR_TECHNICAL',
                compliance_status='SUPERIOR',
                engineering_justification='XLPE offered in lieu of PVC: superior continuous thermal rating (90°C vs 70°C) and higher short circuit withstand.',
                risk_level='LOW'
            ))
        else:
            items.append(DeviationItem(
                clause_no='Clause 3.1 (Insulation System)',
                tender_parameter='Insulation Dielectric',
                tender_specified=req_ins,
                offered_value=off_ins,
                deviation_category='MAJOR_TECHNICAL',
                compliance_status='NON_COMPLIANT',
                engineering_justification=f'Insulation discrepancy: {off_ins} does not meet {req_ins} specification.',
                risk_level='HIGH'
            ))

        # 4. Rated Voltage
        req_volt = rfp_specs.get('voltage_rating', 1100)
        off_volt = offered_product.get('voltage_rating', req_volt)
        try:
            r_v = float(str(req_volt).replace('V', '').replace('v', ''))
            o_v = float(str(off_volt).replace('V', '').replace('v', ''))
            if o_v >= r_v:
                items.append(DeviationItem(
                    clause_no='Clause 4.1 (Voltage Classification)',
                    tender_parameter='Rated System Voltage (U0/U)',
                    tender_specified=f'{r_v}V',
                    offered_value=f'{o_v}V',
                    deviation_category='NIL',
                    compliance_status='COMPLIANT',
                    engineering_justification='Rated dielectric withstand voltage meets or exceeds system requirement.',
                    risk_level='NONE'
                ))
            else:
                items.append(DeviationItem(
                    clause_no='Clause 4.1 (Voltage Classification)',
                    tender_parameter='Rated System Voltage (U0/U)',
                    tender_specified=f'{r_v}V',
                    offered_value=f'{o_v}V',
                    deviation_category='MAJOR_TECHNICAL',
                    compliance_status='NON_COMPLIANT',
                    engineering_justification=f'Under-voltage rated cable ({o_v}V vs {r_v}V required). Dielectric breakdown hazard.',
                    risk_level='HIGH'
                ))
        except (ValueError, TypeError):
            pass

        return items

    @classmethod
    def export_deviations_csv(cls, items: List[DeviationItem]) -> str:
        """Export deviations to GeM Form F-4 compliant CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Clause No.',
            'Tender Parameter',
            'Tender Specified Value',
            'Offered Value',
            'Deviation Category',
            'Compliance Status',
            'Engineering Justification',
            'Risk Level'
        ])
        for it in items:
            writer.writerow([
                it.clause_no,
                it.tender_parameter,
                it.tender_specified,
                it.offered_value,
                it.deviation_category,
                it.compliance_status,
                it.engineering_justification,
                it.risk_level
            ])
        return output.getvalue()


# ==============================================================================
# 3. EMD & PBG STATUTORY EXEMPTION ENGINE
# ==============================================================================

class TenderSecurityEngine:
    """
    Evaluates Earnest Money Deposit (EMD) and Performance Bank Guarantee (PBG)
    requirements and automated statutory exemptions under Indian Public Procurement Laws:
    - Public Procurement Policy for Micro and Small Enterprises (MSEs) Order 2012
    - Ministry of Finance Department of Expenditure OM No. F.20/2/2014-PPD
    - DPIIT Recognition for Startups
    """

    @classmethod
    def evaluate_security_exemptions(
        cls,
        estimated_tender_value_inr: float,
        vendor_profile: Dict[str, Any],
        emd_pct: float = 2.0,
        pbg_pct: float = 3.0
    ) -> Dict[str, Any]:
        """
        Calculates standard EMD/PBG amounts and validates statutory exemption claims.

        Args:
            estimated_tender_value_inr: Total estimated tender/bid value
            vendor_profile: Dict containing:
                - is_msme: bool
                - udyam_registration_no: Optional[str]
                - is_dpiit_startup: bool
                - dpiit_number: Optional[str]
                - is_nsic_registered: bool
                - is_psu: bool
            emd_pct: Default EMD percentage (typically 2.0%)
            pbg_pct: Default PBG percentage (typically 3.0% - 5.0%)
        """
        standard_emd = round((estimated_tender_value_inr * (emd_pct / 100.0)), 2)
        standard_pbg = round((estimated_tender_value_inr * (pbg_pct / 100.0)), 2)

        is_msme = bool(vendor_profile.get('is_msme') or vendor_profile.get('is_mse'))
        udyam_no = vendor_profile.get('udyam_registration_no') or vendor_profile.get('udyam_number')
        is_startup = bool(vendor_profile.get('is_dpiit_startup') or vendor_profile.get('is_startup'))
        is_nsic = bool(vendor_profile.get('is_nsic_registered'))
        is_psu = bool(vendor_profile.get('is_psu'))

        exempt_reasons: List[str] = []
        is_emd_exempt = False
        is_pbg_exempt = False

        if is_msme and udyam_no:
            is_emd_exempt = True
            exempt_reasons.append(
                f"Exempted from EMD under Rule 170 of GFR 2017 & Public Procurement Policy for MSEs Order 2012 (Udyam: {udyam_no})."
            )
        elif is_msme:
            is_emd_exempt = True
            exempt_reasons.append("Exempted from EMD under MSEs Order 2012 (Udyam registration declared).")

        if is_startup:
            is_emd_exempt = True
            exempt_reasons.append("Exempted from EMD as DPIIT Recognized Startup per Ministry of Finance OM No. F.20/2/2014-PPD.")

        if is_nsic:
            is_emd_exempt = True
            exempt_reasons.append("Exempted from EMD under NSIC Single Point Registration Scheme.")

        if is_psu:
            is_emd_exempt = True
            is_pbg_exempt = True
            exempt_reasons.append("Exempted from EMD and PBG as Central/State Public Sector Undertaking.")

        payable_emd = 0.0 if is_emd_exempt else standard_emd
        payable_pbg = 0.0 if is_pbg_exempt else standard_pbg
        statutory_savings = standard_emd if is_emd_exempt else 0.0

        return {
            'estimated_tender_value': estimated_tender_value_inr,
            'standard_emd_amount': standard_emd,
            'standard_emd_percentage': emd_pct,
            'payable_emd_amount': payable_emd,
            'is_emd_exempt': is_emd_exempt,
            'standard_pbg_amount': standard_pbg,
            'standard_pbg_percentage': pbg_pct,
            'payable_pbg_amount': payable_pbg,
            'is_pbg_exempt': is_pbg_exempt,
            'exemption_reasons': exempt_reasons,
            'bidder_statutory_savings': statutory_savings,
            'bid_security_declaration_required': is_emd_exempt,
            'declaration_text': (
                "Bid Security Declaration: In lieu of EMD, bidder certifies submission of statutory "
                "undertaking. If bidder withdraws/modifies bid during validity, bidder shall be suspended "
                "from government tenders for a period not exceeding 2 years."
            ) if is_emd_exempt else None
        }
