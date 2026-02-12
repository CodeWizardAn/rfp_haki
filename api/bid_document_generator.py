"""
Bid Document Generator & Company Profiles Manager
Generates formatted RFP response / bid documents using analysis results + company profiles.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── In-memory stores ──

company_profiles: Dict[str, Dict[str, Any]] = {
    "CP-001": {
        "id": "CP-001",
        "company_name": "Haki Cables & Electrical Ltd",
        "trading_name": "Haki Cables",
        "registration_number": "C-2019/048271",
        "tax_id": "A029384756B",
        "gst_number": "29ABCDE1234F1Z5",
        "pan_number": "ABCDE1234F",
        "incorporation_date": "2019-03-15",
        "company_type": "Private Limited",
        "industry": "Electrical Cables & Wires",
        "website": "https://hakicables.com",
        "email": "bids@hakicables.com",
        "phone": "+91 80 4567 8900",
        "fax": "+91 80 4567 8901",
        "address_line1": "Plot 42, Industrial Area Phase II",
        "address_line2": "Peenya Industrial Estate",
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India",
        "postal_code": "560058",
        "authorized_signatory": "Rajesh Kumar",
        "signatory_designation": "Managing Director",
        "signatory_email": "rajesh.kumar@hakicables.com",
        "signatory_phone": "+91 98451 23456",
        "bank_name": "State Bank of India",
        "bank_branch": "Peenya Industrial Branch",
        "bank_account": "39876543210",
        "bank_ifsc": "SBIN0004321",
        "bank_swift": "SBININBB456",
        "annual_turnover": "₹85,00,00,000",
        "employee_count": 250,
        "iso_certifications": ["ISO 9001:2015", "ISO 14001:2015", "ISO 45001:2018"],
        "bis_license": "CM/L-1234567",
        "other_certifications": ["BIS ISI Mark", "NABL Accredited Lab", "CE Mark"],
        "experience_years": 7,
        "key_clients": ["BSES Rajdhani", "Tata Projects", "L&T Construction", "PGCIL"],
        "logo_url": "",
        "is_default": True,
        "created_at": "2026-01-15T10:00:00",
        "updated_at": "2026-02-10T14:30:00",
    }
}
_profile_counter = 2

generated_bids: Dict[str, Dict[str, Any]] = {}
_gen_bid_counter = 1


def get_all_profiles() -> List[Dict]:
    return list(company_profiles.values())


def get_profile(profile_id: str) -> Optional[Dict]:
    return company_profiles.get(profile_id)


def create_profile(data: Dict) -> Dict:
    global _profile_counter
    pid = f"CP-{_profile_counter:03d}"
    _profile_counter += 1
    profile = {
        "id": pid,
        **data,
        "is_default": len(company_profiles) == 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    company_profiles[pid] = profile
    return profile


def update_profile(profile_id: str, data: Dict) -> Optional[Dict]:
    if profile_id not in company_profiles:
        return None
    company_profiles[profile_id].update(data)
    company_profiles[profile_id]["updated_at"] = datetime.now().isoformat()
    return company_profiles[profile_id]


def delete_profile(profile_id: str) -> bool:
    return company_profiles.pop(profile_id, None) is not None


def set_default_profile(profile_id: str) -> Optional[Dict]:
    if profile_id not in company_profiles:
        return None
    for p in company_profiles.values():
        p["is_default"] = False
    company_profiles[profile_id]["is_default"] = True
    return company_profiles[profile_id]


# ── Bid Document Generation ──

def generate_bid_document(
    analysis_result: Dict,
    profile_id: str,
    bid_options: Dict,
) -> Dict:
    """Generate a formatted bid / RFP response document from analysis + company profile."""
    global _gen_bid_counter

    profile = company_profiles.get(profile_id)
    if not profile:
        raise ValueError(f"Company profile {profile_id} not found")

    bid_id = f"GENBID-{_gen_bid_counter:04d}"
    _gen_bid_counter += 1

    now = datetime.now()
    validity_days = bid_options.get("validity_days", 90)
    valid_until = now + timedelta(days=validity_days)

    comparisons = analysis_result.get("comparisons", [])
    rfp_summary = analysis_result.get("rfp_summary", {})
    oem_summary = analysis_result.get("oem_summary", {})
    boq = analysis_result.get("boq", {})
    pricing = analysis_result.get("pricing_estimate", {})
    requirement_summary = analysis_result.get("requirement_summary", {})

    # Build line items
    line_items = []
    total_value = 0.0
    for idx, comp in enumerate(comparisons):
        req = comp.get("requirement", {})
        matches = comp.get("top_matches", [])
        best = matches[0] if matches else None
        if not best:
            continue

        qty = 1000  # default
        boq_items = boq.get("items", [])
        if idx < len(boq_items):
            qty = boq_items[idx].get("quantity", 1000) or 1000
            try:
                qty = float(str(qty).replace(",", ""))
            except (ValueError, TypeError):
                qty = 1000

        unit_price = best.get("price_per_meter", 0) or 0
        discount = bid_options.get("discount_percentage", 0)
        disc_price = unit_price * (1 - discount / 100)
        item_total = disc_price * qty
        total_value += item_total

        line_items.append({
            "sr_no": idx + 1,
            "description": req.get("original_text", "")[:200],
            "product_code": best.get("product_code", ""),
            "product_name": best.get("product_name", ""),
            "oem": best.get("oem", ""),
            "specification": f"{best.get('conductor_size', '')}mm² {best.get('cores', '')}C "
                           f"{best.get('voltage_rating', '')}V {best.get('insulation_type', '')}",
            "match_score": best.get("match_score", 0),
            "quantity": qty,
            "unit": "meters",
            "unit_price": unit_price,
            "discount_percent": discount,
            "discounted_price": round(disc_price, 2),
            "total_price": round(item_total, 2),
            "warranty_years": best.get("warranty_years", 0),
        })

    gst_rate = bid_options.get("gst_rate", 18)
    gst_amount = total_value * gst_rate / 100
    grand_total = total_value + gst_amount

    # Pricing from analysis pricing agent
    pricing_summary = pricing.get("summary", {}) if pricing else {}

    bid_doc = {
        "id": bid_id,
        "status": "generated",
        "generated_at": now.isoformat(),
        "valid_until": valid_until.isoformat(),

        # Company
        "company": {
            "name": profile.get("company_name", ""),
            "trading_name": profile.get("trading_name", ""),
            "registration_number": profile.get("registration_number", ""),
            "tax_id": profile.get("tax_id", ""),
            "gst_number": profile.get("gst_number", ""),
            "pan_number": profile.get("pan_number", ""),
            "address": f"{profile.get('address_line1', '')}, {profile.get('address_line2', '')}, "
                      f"{profile.get('city', '')}, {profile.get('state', '')} — {profile.get('postal_code', '')}",
            "phone": profile.get("phone", ""),
            "email": profile.get("email", ""),
            "website": profile.get("website", ""),
            "authorized_signatory": profile.get("authorized_signatory", ""),
            "signatory_designation": profile.get("signatory_designation", ""),
            "industry": profile.get("industry", ""),
            "experience_years": profile.get("experience_years", 0),
            "annual_turnover": profile.get("annual_turnover", ""),
            "certifications": profile.get("iso_certifications", []) + profile.get("other_certifications", []),
            "key_clients": profile.get("key_clients", []),
            "bank_details": {
                "name": profile.get("bank_name", ""),
                "branch": profile.get("bank_branch", ""),
                "account": profile.get("bank_account", ""),
                "ifsc": profile.get("bank_ifsc", ""),
                "swift": profile.get("bank_swift", ""),
            },
        },

        # RFP Reference
        "rfp_reference": {
            "bid_number": rfp_summary.get("bid_number", ""),
            "title": rfp_summary.get("boq_title", "") or analysis_result.get("filename", ""),
            "organization": rfp_summary.get("organization", ""),
            "ministry": rfp_summary.get("ministry", ""),
            "department": rfp_summary.get("department", ""),
            "bid_end_date": rfp_summary.get("bid_end_date", ""),
            "emd_amount": rfp_summary.get("emd_amount", ""),
            "source_file": analysis_result.get("filename", ""),
            "total_requirements": analysis_result.get("total_requirements", 0),
            "matched_requirements": len(line_items),
            "detected_application": analysis_result.get("detected_application", ""),
        },

        # Bid Terms
        "bid_terms": {
            "validity_days": validity_days,
            "delivery_timeline": bid_options.get("delivery_timeline", "6-8 weeks from PO"),
            "payment_terms": bid_options.get("payment_terms", "Net 30 days from delivery"),
            "warranty": bid_options.get("warranty_period", "As per manufacturer standards"),
            "discount_percentage": bid_options.get("discount_percentage", 0),
            "gst_rate": gst_rate,
            "freight_terms": bid_options.get("freight_terms", "FOR Destination"),
            "inspection_terms": bid_options.get("inspection_terms", "At manufacturer premises before dispatch"),
            "packing_forwarding": bid_options.get("packing_forwarding", "Included in unit price"),
            "liquidated_damages": bid_options.get("liquidated_damages", "0.5% per week, max 5%"),
            "force_majeure": "As per standard ICC clause",
            "arbitration": bid_options.get("arbitration", "Subject to jurisdiction of local courts"),
            "notes": bid_options.get("notes", ""),
        },

        # Line Items
        "line_items": line_items,

        # Financial Summary
        "financial_summary": {
            "subtotal": round(total_value, 2),
            "discount_percentage": bid_options.get("discount_percentage", 0),
            "gst_rate": gst_rate,
            "gst_amount": round(gst_amount, 2),
            "grand_total": round(grand_total, 2),
            "currency": bid_options.get("currency", "INR"),
            "amount_in_words": _amount_in_words(grand_total),
            "ai_pricing_available": bool(pricing_summary),
            "ai_material_cost": pricing_summary.get("total_material_cost", 0),
            "ai_test_cost": pricing_summary.get("total_test_cost", 0),
            "ai_grand_total": pricing_summary.get("grand_total", 0),
        },

        # OEM Summary
        "oem_summary": {
            "total_oems": oem_summary.get("total_oems", 0),
            "best_oem": oem_summary.get("best_oem", ""),
            "rankings": (oem_summary.get("oem_rankings", []) or [])[:5],
        },

        # Budget Breakdown
        "budget_breakdown": _build_budget_breakdown(
            line_items, total_value, gst_amount, grand_total,
            gst_rate, rfp_summary, pricing, analysis_result,
        ),

        # Technical compliance
        "technical_compliance": {
            "total_requirements": requirement_summary.get("total", 0),
            "wire_cable_specs": requirement_summary.get("wire_cable_specs", 0),
            "matched_products": len(line_items),
            "average_match_score": round(
                sum(li["match_score"] for li in line_items) / max(len(line_items), 1), 1
            ),
            "standards_offered": list(set(
                m.get("standard", "") for c in comparisons
                for m in c.get("top_matches", [])[:1] if m.get("standard")
            )),
        },

        # Send options
        "send_options": {
            "email_to": bid_options.get("email_to", ""),
            "email_cc": bid_options.get("email_cc", ""),
            "email_subject": f"Bid Submission — {rfp_summary.get('bid_number', bid_id)} | {profile.get('company_name', '')}",
        },
    }

    generated_bids[bid_id] = bid_doc
    return bid_doc


def get_generated_bid(bid_id: str) -> Optional[Dict]:
    return generated_bids.get(bid_id)


def list_generated_bids() -> List[Dict]:
    return sorted(generated_bids.values(), key=lambda b: b["generated_at"], reverse=True)


def send_bid_email(bid_id: str, email_to: str, email_cc: str = "", message: str = "") -> Dict:
    """Simulate sending bid via email."""
    bid = generated_bids.get(bid_id)
    if not bid:
        raise ValueError(f"Bid {bid_id} not found")

    bid["status"] = "sent"
    bid["sent_at"] = datetime.now().isoformat()
    bid["sent_to"] = email_to
    bid["sent_cc"] = email_cc

    return {
        "success": True,
        "message": f"Bid {bid_id} sent successfully to {email_to}",
        "bid_id": bid_id,
        "sent_at": bid["sent_at"],
        "recipients": {"to": email_to, "cc": email_cc},
    }


def _build_budget_breakdown(
    line_items: list,
    subtotal: float,
    gst_amount: float,
    grand_total: float,
    gst_rate: float,
    rfp_summary: dict,
    pricing: dict,
    analysis_result: dict,
) -> dict:
    """Compute a detailed budget/cost breakdown for the bid response."""

    # ── RFP-level budget signals ──
    estimated_value_raw = rfp_summary.get("estimated_cost") or rfp_summary.get("total_quantity") or ""
    emd_raw = rfp_summary.get("emd_amount") or ""
    # Also try extracted_fields if present
    ef = analysis_result.get("extracted_fields") or {}
    if not estimated_value_raw:
        ev = ef.get("Estimated Cost") or ef.get("Estimated Value") or ef.get("Contract Value") or {}
        estimated_value_raw = ev.get("value", "") if isinstance(ev, dict) else ev
    if not emd_raw:
        em = ef.get("EMD Amount") or ef.get("Earnest Money Deposit") or ef.get("Bid Security") or {}
        emd_raw = em.get("value", "") if isinstance(em, dict) else em

    # ── OEM-wise cost breakdown ──
    oem_costs: Dict[str, Dict] = {}
    for li in line_items:
        oem = li.get("oem") or "Unknown"
        if oem not in oem_costs:
            oem_costs[oem] = {"items": 0, "total": 0.0}
        oem_costs[oem]["items"] += 1
        oem_costs[oem]["total"] += li.get("total_price", 0)

    oem_breakdown = [
        {
            "oem": k,
            "items": v["items"],
            "total": round(v["total"], 2),
            "percentage": round(v["total"] / max(subtotal, 1) * 100, 1),
        }
        for k, v in sorted(oem_costs.items(), key=lambda x: -x[1]["total"])
    ]

    # ── Per-unit stats ──
    total_qty = sum(li.get("quantity", 0) for li in line_items)
    avg_unit_price = round(subtotal / max(total_qty, 1), 2)
    min_unit = min((li.get("unit_price", 0) for li in line_items), default=0)
    max_unit = max((li.get("unit_price", 0) for li in line_items), default=0)

    # ── Discount savings ──
    total_before_discount = sum(
        (li.get("unit_price", 0) * li.get("quantity", 0)) for li in line_items
    )
    discount_savings = round(total_before_discount - subtotal, 2)

    # ── Cost category breakdown (by voltage/specification type) ──
    cat_costs: Dict[str, float] = {}
    for li in line_items:
        spec = li.get("specification", "")
        # Bucket by voltage class
        if "1100" in spec or "1.1" in spec:
            cat = "LT (≤1.1kV)"
        elif "3300" in spec or "6600" in spec or "11000" in spec or "33000" in spec:
            cat = "HT/MV (3.3-33kV)"
        elif "415" in spec or "440" in spec or "650" in spec:
            cat = "Control / Power (≤1kV)"
        else:
            cat = "General / Other"
        cat_costs[cat] = cat_costs.get(cat, 0) + li.get("total_price", 0)

    category_breakdown = [
        {"category": k, "total": round(v, 2), "percentage": round(v / max(subtotal, 1) * 100, 1)}
        for k, v in sorted(cat_costs.items(), key=lambda x: -x[1])
    ]

    # ── AI pricing comparison ──
    pricing_summary = (pricing or {}).get("summary", {})
    ai_total = pricing_summary.get("grand_total", 0) or 0
    margin_vs_ai = round(grand_total - ai_total, 2) if ai_total > 0 else None
    margin_pct_vs_ai = round((margin_vs_ai / max(ai_total, 1)) * 100, 1) if margin_vs_ai is not None else None

    return {
        "rfp_estimated_value": str(estimated_value_raw) if estimated_value_raw else None,
        "emd_amount": str(emd_raw) if emd_raw else None,
        "total_line_items": len(line_items),
        "total_quantity": total_qty,
        "subtotal_before_tax": round(subtotal, 2),
        "discount_savings": discount_savings,
        "gst_rate": gst_rate,
        "gst_amount": round(gst_amount, 2),
        "grand_total": round(grand_total, 2),
        "avg_unit_price": avg_unit_price,
        "min_unit_price": round(min_unit, 2),
        "max_unit_price": round(max_unit, 2),
        "oem_breakdown": oem_breakdown,
        "category_breakdown": category_breakdown,
        "ai_estimated_total": ai_total if ai_total > 0 else None,
        "ai_material_cost": pricing_summary.get("total_material_cost", 0) or None,
        "ai_test_cost": pricing_summary.get("total_test_cost", 0) or None,
        "margin_vs_ai": margin_vs_ai,
        "margin_pct_vs_ai": margin_pct_vs_ai,
    }


def _amount_in_words(amount: float) -> str:
    """Simple amount to words converter."""
    if amount <= 0:
        return "Zero"
    crores = int(amount / 10000000)
    lakhs = int((amount % 10000000) / 100000)
    thousands = int((amount % 100000) / 1000)

    parts = []
    if crores:
        parts.append(f"{crores} Crore{'s' if crores > 1 else ''}")
    if lakhs:
        parts.append(f"{lakhs} Lakh{'s' if lakhs > 1 else ''}")
    if thousands:
        parts.append(f"{thousands} Thousand")

    remaining = int(amount % 1000)
    if remaining:
        parts.append(str(remaining))

    return "Rupees " + " ".join(parts) + " Only" if parts else "Zero"
