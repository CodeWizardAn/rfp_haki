"""
Bid PDF Generator — produces a professional tender‑response PDF from a bid document dict.
Uses ReportLab for pixel‑perfect layout.
"""

import io
import os
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ── Colours ──────────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0B1120")
DARK_BG = colors.HexColor("#111827")
CYAN = colors.HexColor("#06B6D4")
EMERALD = colors.HexColor("#10B981")
AMBER = colors.HexColor("#F59E0B")
WHITE = colors.white
LIGHT_GREY = colors.HexColor("#F3F4F6")
MEDIUM_GREY = colors.HexColor("#9CA3AF")
BORDER_GREY = colors.HexColor("#D1D5DB")
ROW_ALT = colors.HexColor("#F9FAFB")
HEADER_BG = colors.HexColor("#1E3A5F")
SECTION_BG = colors.HexColor("#EFF6FF")
TABLE_HEADER = colors.HexColor("#1E3A5F")

PAGE_W, PAGE_H = A4


# ── Styles ───────────────────────────────────────────────────────────────

def _styles():
    ss = getSampleStyleSheet()

    title = ParagraphStyle(
        "BidTitle", parent=ss["Title"],
        fontSize=22, leading=28, alignment=TA_CENTER,
        textColor=HEADER_BG, spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    subtitle = ParagraphStyle(
        "BidSubtitle", parent=ss["Normal"],
        fontSize=11, leading=14, alignment=TA_CENTER,
        textColor=MEDIUM_GREY, spaceAfter=10,
        fontName="Helvetica",
    )
    section = ParagraphStyle(
        "SectionHeading", parent=ss["Heading2"],
        fontSize=13, leading=18, textColor=WHITE,
        fontName="Helvetica-Bold",
        spaceBefore=14, spaceAfter=4,
        backColor=HEADER_BG,
        borderPadding=(6, 8, 6, 8),
        leftIndent=0,
    )
    body = ParagraphStyle(
        "BidBody", parent=ss["Normal"],
        fontSize=9.5, leading=13, textColor=colors.HexColor("#1F2937"),
        fontName="Helvetica",
    )
    body_bold = ParagraphStyle(
        "BidBodyBold", parent=body,
        fontName="Helvetica-Bold",
    )
    small = ParagraphStyle(
        "SmallText", parent=body,
        fontSize=8, leading=10, textColor=MEDIUM_GREY,
    )
    right = ParagraphStyle(
        "RightAlign", parent=body,
        alignment=TA_RIGHT,
    )
    center = ParagraphStyle(
        "CenterAlign", parent=body,
        alignment=TA_CENTER,
    )
    table_header = ParagraphStyle(
        "TableHeader", parent=body_bold,
        fontSize=8.5, textColor=WHITE, alignment=TA_CENTER,
    )
    table_cell = ParagraphStyle(
        "TableCell", parent=body,
        fontSize=8.5, leading=11,
    )
    table_cell_r = ParagraphStyle(
        "TableCellR", parent=table_cell,
        alignment=TA_RIGHT,
    )
    table_cell_c = ParagraphStyle(
        "TableCellC", parent=table_cell,
        alignment=TA_CENTER,
    )
    footer_style = ParagraphStyle(
        "FooterStyle", parent=small,
        alignment=TA_CENTER,
        textColor=MEDIUM_GREY,
    )
    return {
        "title": title, "subtitle": subtitle, "section": section,
        "body": body, "body_bold": body_bold, "small": small,
        "right": right, "center": center,
        "th": table_header, "td": table_cell, "td_r": table_cell_r, "td_c": table_cell_c,
        "footer": footer_style,
    }


# ── Helpers ──────────────────────────────────────────────────────────────

def _p(text, style):
    """Wrap text into a Paragraph safely."""
    return Paragraph(str(text or "—"), style)


def _fmt_inr(val):
    try:
        v = float(val)
        if v < 0.01:
            return "—"
        # Indian formatting
        s = f"{v:,.2f}"
        return f"₹{s}"
    except (TypeError, ValueError):
        return "—"


def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER_GREY, spaceAfter=6, spaceBefore=6)


def _section_heading(text, st):
    """Section heading with coloured background."""
    return _p(f"&nbsp;&nbsp;{text}", st["section"])


def _kv_table(rows: List[tuple], st, col_widths=None):
    """Key–value table (label | value)."""
    if not col_widths:
        col_widths = [5 * cm, 12 * cm]
    data = [[_p(f"<b>{k}</b>", st["td"]), _p(v, st["td"])] for k, v in rows]
    tbl = Table(data, colWidths=col_widths, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (0, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, BORDER_GREY),
        ("BACKGROUND", (0, 0), (0, -1), SECTION_BG),
    ]))
    return tbl


# ── Page callbacks ───────────────────────────────────────────────────────

def _header_footer(canvas, doc, bid_doc):
    """Draw page header / footer on every page."""
    canvas.saveState()

    # Header line
    canvas.setStrokeColor(HEADER_BG)
    canvas.setLineWidth(1.5)
    canvas.line(1.5 * cm, PAGE_H - 1.2 * cm, PAGE_W - 1.5 * cm, PAGE_H - 1.2 * cm)

    # Header text
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(HEADER_BG)
    company_name = bid_doc.get("company", {}).get("name", "")
    canvas.drawString(1.5 * cm, PAGE_H - 1.0 * cm, company_name)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MEDIUM_GREY)
    canvas.drawRightString(PAGE_W - 1.5 * cm, PAGE_H - 1.0 * cm, f"Bid Ref: {bid_doc.get('id', '')}")

    # Footer
    canvas.setStrokeColor(BORDER_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, 1.5 * cm, PAGE_W - 1.5 * cm, 1.5 * cm)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MEDIUM_GREY)
    canvas.drawString(1.5 * cm, 1.0 * cm, f"Generated: {datetime.now().strftime('%d-%b-%Y %H:%M')}")
    canvas.drawCentredString(PAGE_W / 2, 1.0 * cm, "CONFIDENTIAL — For Addressee Only")
    canvas.drawRightString(PAGE_W - 1.5 * cm, 1.0 * cm, f"Page {doc.page}")

    canvas.restoreState()


# ── Main builder ─────────────────────────────────────────────────────────

def generate_bid_pdf(bid_doc: Dict[str, Any]) -> bytes:
    """
    Accepts a bid document dict (as returned by generate_bid_document)
    and returns a PDF as bytes.
    """
    buf = io.BytesIO()
    st = _styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=f"Bid Response — {bid_doc.get('id', '')}",
        author=bid_doc.get("company", {}).get("name", ""),
    )

    elements: list = []
    company = bid_doc.get("company", {})
    rfp_ref = bid_doc.get("rfp_reference", {})
    bid_terms = bid_doc.get("bid_terms", {})
    line_items = bid_doc.get("line_items", [])
    fin = bid_doc.get("financial_summary", {})
    tech = bid_doc.get("technical_compliance", {})
    oem = bid_doc.get("oem_summary", {})

    # ────────────────── Cover / Title Block ──────────────────
    elements.append(Spacer(1, 1.5 * cm))

    # Company name
    elements.append(_p(company.get("name", "Company Name"), st["title"]))
    elements.append(_p(company.get("address", ""), st["subtitle"]))
    elements.append(Spacer(1, 0.3 * cm))

    # Contact row
    contact_text = " | ".join(filter(None, [
        company.get("phone", ""),
        company.get("email", ""),
        company.get("website", ""),
    ]))
    elements.append(_p(contact_text, st["subtitle"]))
    reg_text = " | ".join(filter(None, [
        f"Reg: {company.get('registration_number', '')}",
        f"GST: {company.get('gst_number', '')}",
        f"PAN: {company.get('pan_number', '')}",
    ]))
    elements.append(_p(reg_text, st["small"]))
    elements.append(Spacer(1, 0.6 * cm))

    elements.append(_hr())
    elements.append(Spacer(1, 0.2 * cm))

    # Bid-title box
    bid_title = rfp_ref.get("title", "") or "Tender Response"
    elements.append(_p(f"<b>BID / TENDER RESPONSE</b>", st["title"]))
    elements.append(_p(bid_title, st["subtitle"]))
    elements.append(Spacer(1, 0.3 * cm))

    # Quick reference key-value
    ref_rows = [
        ("Bid Reference", bid_doc.get("id", "")),
        ("RFP / Bid No.", rfp_ref.get("bid_number", "") or "—"),
        ("Organization", rfp_ref.get("organization", "") or "—"),
        ("Date", datetime.now().strftime("%d %B %Y")),
        ("Valid Until", bid_doc.get("valid_until", "")[:10] if bid_doc.get("valid_until") else "—"),
    ]
    elements.append(_kv_table(ref_rows, st))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(_hr())

    # ────────────────── 1. Company Information ──────────────────
    elements.append(_section_heading("1. BIDDER INFORMATION", st))
    elements.append(Spacer(1, 4))

    co_rows = [
        ("Company Name", company.get("name", "")),
        ("Trading Name", company.get("trading_name", "")),
        ("Registration No.", company.get("registration_number", "")),
        ("GST Number", company.get("gst_number", "")),
        ("PAN", company.get("pan_number", "")),
        ("Industry", company.get("industry", "")),
        ("Address", company.get("address", "")),
        ("Phone", company.get("phone", "")),
        ("Email", company.get("email", "")),
        ("Website", company.get("website", "")),
        ("Experience", f"{company.get('experience_years', 0)} years"),
        ("Annual Turnover", company.get("annual_turnover", "")),
    ]
    elements.append(_kv_table(co_rows, st))

    # Certifications
    certs = company.get("certifications", [])
    if certs:
        elements.append(Spacer(1, 4))
        elements.append(_p(f"<b>Certifications:</b> {', '.join(certs)}", st["body"]))

    # Key Clients
    clients = company.get("key_clients", [])
    if clients:
        elements.append(_p(f"<b>Key Clients:</b> {', '.join(clients)}", st["body"]))

    elements.append(Spacer(1, 6))

    # ────────────────── 2. RFP Reference ──────────────────
    elements.append(_section_heading("2. RFP REFERENCE DETAILS", st))
    elements.append(Spacer(1, 4))

    rfp_rows = [
        ("Bid / Tender No.", rfp_ref.get("bid_number", "") or "—"),
        ("Title", rfp_ref.get("title", "")),
        ("Organization", rfp_ref.get("organization", "") or "—"),
        ("Ministry / Dept", f"{rfp_ref.get('ministry', '—')} / {rfp_ref.get('department', '—')}"),
        ("Bid End Date", rfp_ref.get("bid_end_date", "") or "—"),
        ("EMD Amount", rfp_ref.get("emd_amount", "") or "—"),
        ("Source File", rfp_ref.get("source_file", "")),
        ("Total Requirements", str(rfp_ref.get("total_requirements", 0))),
        ("Matched Requirements", str(rfp_ref.get("matched_requirements", 0))),
        ("Detected Application", rfp_ref.get("detected_application", "")),
    ]
    elements.append(_kv_table(rfp_rows, st))
    elements.append(Spacer(1, 6))

    # ────────────────── 3. Terms & Conditions ──────────────────
    elements.append(_section_heading("3. BID TERMS & CONDITIONS", st))
    elements.append(Spacer(1, 4))

    terms_rows = [
        ("Validity", f"{bid_terms.get('validity_days', 90)} days from date of submission"),
        ("Delivery", bid_terms.get("delivery_timeline", "")),
        ("Payment Terms", bid_terms.get("payment_terms", "")),
        ("Warranty", bid_terms.get("warranty", "")),
        ("Freight", bid_terms.get("freight_terms", "")),
        ("Packing & Forwarding", bid_terms.get("packing_forwarding", "")),
        ("Inspection", bid_terms.get("inspection_terms", "")),
        ("Liquidated Damages", bid_terms.get("liquidated_damages", "")),
        ("Force Majeure", bid_terms.get("force_majeure", "")),
        ("Arbitration", bid_terms.get("arbitration", "")),
    ]
    elements.append(_kv_table(terms_rows, st))
    notes = bid_terms.get("notes", "")
    if notes:
        elements.append(Spacer(1, 4))
        elements.append(_p(f"<b>Special Notes:</b> {notes}", st["body"]))
    elements.append(Spacer(1, 6))

    # ────────────────── 4. Product Line Items (Bill of Quantities) ──────────────────
    elements.append(PageBreak())
    elements.append(_section_heading("4. BILL OF QUANTITIES / PRICE SCHEDULE", st))
    elements.append(Spacer(1, 6))

    if line_items:
        # Table header
        hdr = [
            _p("Sr.", st["th"]),
            _p("Product / Description", st["th"]),
            _p("OEM", st["th"]),
            _p("Specification", st["th"]),
            _p("Match", st["th"]),
            _p("Qty", st["th"]),
            _p("Unit Price", st["th"]),
            _p("Disc %", st["th"]),
            _p("Total (₹)", st["th"]),
        ]
        col_ws = [1.0*cm, 4.2*cm, 2.0*cm, 3.5*cm, 1.2*cm, 1.5*cm, 1.8*cm, 1.0*cm, 2.0*cm]

        rows_data = [hdr]
        for li in line_items:
            desc = li.get("product_name", "") or li.get("description", "")
            if len(desc) > 60:
                desc = desc[:57] + "..."
            spec = li.get("specification", "")
            if len(spec) > 45:
                spec = spec[:42] + "..."
            rows_data.append([
                _p(str(li.get("sr_no", "")), st["td_c"]),
                _p(f"{desc}<br/><font size=6 color='#6B7280'>{li.get('product_code', '')}</font>", st["td"]),
                _p(li.get("oem", ""), st["td_c"]),
                _p(spec, st["td"]),
                _p(f"{li.get('match_score', 0):.0f}%", st["td_c"]),
                _p(f"{li.get('quantity', 0):,.0f}", st["td_r"]),
                _p(_fmt_inr(li.get("unit_price", 0)), st["td_r"]),
                _p(f"{li.get('discount_percent', 0)}%", st["td_c"]),
                _p(_fmt_inr(li.get("total_price", 0)), st["td_r"]),
            ])

        tbl = Table(rows_data, colWidths=col_ws, repeatRows=1, hAlign="LEFT")
        tbl_style = [
            # header
            ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            # grid
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]
        # Alternate row colouring
        for i in range(1, len(rows_data)):
            if i % 2 == 0:
                tbl_style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))

        tbl.setStyle(TableStyle(tbl_style))
        elements.append(tbl)
    else:
        elements.append(_p("<i>No line items matched.</i>", st["body"]))

    elements.append(Spacer(1, 8))

    # ────────────────── 5. Financial Summary ──────────────────
    elements.append(_section_heading("5. FINANCIAL SUMMARY", st))
    elements.append(Spacer(1, 6))

    fin_data = [
        [_p("<b>Description</b>", st["td"]), _p("<b>Amount</b>", st["td_r"])],
        [_p("Subtotal (before tax)", st["td"]), _p(_fmt_inr(fin.get("subtotal", 0)), st["td_r"])],
        [_p(f"Discount ({fin.get('discount_percentage', 0)}%)", st["td"]),
         _p(f"{fin.get('discount_percentage', 0)}%", st["td_r"])],
        [_p(f"GST @ {fin.get('gst_rate', 18)}%", st["td"]),
         _p(_fmt_inr(fin.get("gst_amount", 0)), st["td_r"])],
    ]
    # Grand-total row
    fin_data.append([
        _p("<b>GRAND TOTAL</b>", st["body_bold"]),
        _p(f"<b>{_fmt_inr(fin.get('grand_total', 0))}</b>", ParagraphStyle("GTR", parent=st["td_r"], fontName="Helvetica-Bold", fontSize=11)),
    ])

    fin_tbl = Table(fin_data, colWidths=[12 * cm, 5.5 * cm], hAlign="LEFT")
    fin_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ECFDF5")),
    ]))
    elements.append(fin_tbl)

    # Amount in words
    words = fin.get("amount_in_words", "")
    if words:
        elements.append(Spacer(1, 4))
        elements.append(_p(f"<b>Amount in words:</b> <i>{words}</i>", st["body"]))

    # AI pricing note
    if fin.get("ai_pricing_available") and fin.get("ai_grand_total", 0) > 0:
        elements.append(Spacer(1, 4))
        elements.append(_p(
            f"<font color='#7C3AED'><b>AI Pricing Agent Estimate:</b> {_fmt_inr(fin['ai_grand_total'])} "
            f"(Material: {_fmt_inr(fin.get('ai_material_cost', 0))} + Testing: {_fmt_inr(fin.get('ai_test_cost', 0))})</font>",
            st["body"],
        ))

    elements.append(Spacer(1, 8))

    # ────────────────── 6. Technical Compliance ──────────────────
    elements.append(_section_heading("6. TECHNICAL COMPLIANCE SUMMARY", st))
    elements.append(Spacer(1, 4))

    tc_rows = [
        ("Total Requirements", str(tech.get("total_requirements", 0))),
        ("Wire & Cable Specifications", str(tech.get("wire_cable_specs", 0))),
        ("Products Matched", str(tech.get("matched_products", 0))),
        ("Average Match Score", f"{tech.get('average_match_score', 0)}%"),
    ]
    elements.append(_kv_table(tc_rows, st))

    standards = tech.get("standards_offered", [])
    if standards:
        elements.append(Spacer(1, 4))
        elements.append(_p(f"<b>Standards Offered:</b> {', '.join(standards)}", st["body"]))

    elements.append(Spacer(1, 8))

    # ────────────────── 7. OEM Summary ──────────────────
    if oem.get("total_oems", 0) > 0:
        elements.append(_section_heading("7. OEM / MANUFACTURER SUMMARY", st))
        elements.append(Spacer(1, 4))
        elements.append(_p(f"<b>Total OEMs:</b> {oem.get('total_oems', 0)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                           f"<b>Best OEM:</b> {oem.get('best_oem', '—')}", st["body"]))

        rankings = oem.get("rankings", [])
        if rankings:
            oem_hdr = [_p("<b>#</b>", st["th"]), _p("<b>OEM</b>", st["th"]),
                       _p("<b>Products</b>", st["th"]), _p("<b>Avg Score</b>", st["th"])]
            oem_rows = [oem_hdr]
            for idx, r in enumerate(rankings[:5], 1):
                oem_rows.append([
                    _p(str(idx), st["td_c"]),
                    _p(r.get("oem", ""), st["td"]),
                    _p(str(r.get("product_count", 0)), st["td_c"]),
                    _p(f"{r.get('average_score', 0):.1f}%", st["td_c"]),
                ])
            oem_tbl = Table(oem_rows, colWidths=[1.5*cm, 6*cm, 3*cm, 3*cm], hAlign="LEFT")
            oem_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GREY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(Spacer(1, 4))
            elements.append(oem_tbl)

        elements.append(Spacer(1, 8))

    # ────────────────── 8. Bank Details ──────────────────
    bank = company.get("bank_details", {})
    if bank and bank.get("name"):
        elements.append(_section_heading("8. BANK DETAILS (For Payment Reference)", st))
        elements.append(Spacer(1, 4))
        bank_rows = [
            ("Bank Name", bank.get("name", "")),
            ("Branch", bank.get("branch", "")),
            ("Account Number", bank.get("account", "")),
            ("IFSC Code", bank.get("ifsc", "")),
            ("SWIFT Code", bank.get("swift", "")),
        ]
        elements.append(_kv_table(bank_rows, st))
        elements.append(Spacer(1, 8))

    # ────────────────── 9. Declaration & Signature ──────────────────
    elements.append(_section_heading("9. DECLARATION & AUTHORIZED SIGNATORY", st))
    elements.append(Spacer(1, 6))

    declaration = (
        "We hereby declare that the information furnished above is true and correct to the best of our "
        "knowledge and belief. We agree to abide by the terms and conditions mentioned in this bid document "
        "and the tender/RFP referenced herein. This bid is valid for the period stated above from the date of "
        "submission."
    )
    elements.append(_p(declaration, ParagraphStyle("Decl", parent=st["body"], alignment=TA_JUSTIFY)))
    elements.append(Spacer(1, 1.5 * cm))

    # Signature block
    sig_data = [
        [_p("For and on behalf of", st["body"]), _p("", st["body"])],
        [_p(f"<b>{company.get('name', '')}</b>", st["body_bold"]), _p("", st["body"])],
        [_p("", st["body"]), _p("", st["body"])],
        [_p("", st["body"]), _p("", st["body"])],
        [_p("_______________________________", st["body"]), _p(f"Date: {datetime.now().strftime('%d/%m/%Y')}", st["body"])],
        [_p(f"<b>{company.get('authorized_signatory', '')}</b>", st["body_bold"]), _p("", st["body"])],
        [_p(company.get("signatory_designation", ""), st["body"]), _p("", st["body"])],
    ]
    sig_tbl = Table(sig_data, colWidths=[10 * cm, 7 * cm], hAlign="LEFT")
    sig_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    elements.append(sig_tbl)

    elements.append(Spacer(1, 1.0 * cm))
    elements.append(_p(
        f"<font color='#6B7280' size=7>Seal / Stamp of the Company &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Place: {company.get('address', '').split(',')[-2].strip() if ',' in company.get('address', '') else '—'}</font>",
        st["center"],
    ))

    # ────────── Build ──────────
    def on_page(canvas, doc_):
        _header_footer(canvas, doc_, bid_doc)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
