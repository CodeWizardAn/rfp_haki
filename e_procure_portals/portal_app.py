"""
Generic e-Procurement Portal Flask App.
Each portal instance serves its assigned RFPs with a unique look and feel.
Run with: python portal_app.py --portal portal_1
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
import random
import hashlib
from flask import Flask, render_template, send_file, jsonify, abort, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from portal_config import PORTALS, RFP_DISTRIBUTION, RFP_SOURCE_DIR

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "static"))

# Will be set by CLI arg
CURRENT_PORTAL_ID = None


def get_portal():
    return PORTALS[CURRENT_PORTAL_ID]


def get_rfps():
    """Get enriched RFP data for current portal."""
    rfps = RFP_DISTRIBUTION.get(CURRENT_PORTAL_ID, [])
    enriched = []
    for i, rfp in enumerate(rfps):
        # Generate deterministic metadata from filename
        seed = int(hashlib.md5(rfp["filename"].encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        
        categories = [
            "Electrical Equipment", "Cables & Wires", "Power Infrastructure",
            "Switchgear & Panels", "Lighting Solutions", "Industrial Automation",
            "Safety Equipment", "Transformers", "Cable Management", "FMCG Supplies"
        ]
        statuses = ["Open", "Open", "Open", "Closing Soon"]
        orgs = [
            "Municipal Corporation", "State Electricity Board", 
            "National Highway Authority", "Public Works Department",
            "Railway Procurement Division", "Defense Procurement Agency",
            "Smart City Mission", "Industrial Development Corp"
        ]
        
        base_date = datetime(2026, 1, 15)
        publish_date = base_date + timedelta(days=rng.randint(0, 25))
        deadline = publish_date + timedelta(days=rng.randint(15, 45))
        
        enriched.append({
            "rfp_id": rfp["rfp_id"],
            "filename": rfp["filename"],
            "filepath": rfp["filepath"],
            "title": f"Procurement of {rng.choice(categories)} - {rfp['rfp_id']}",
            "category": rng.choice(categories),
            "organization": rng.choice(orgs),
            "publish_date": publish_date.strftime("%Y-%m-%d"),
            "deadline": deadline.strftime("%Y-%m-%d"),
            "status": rng.choice(statuses),
            "estimated_value": f"₹{rng.randint(5, 500)} Lakhs",
            "location": rng.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata"]),
        })
    return enriched


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    portal = get_portal()
    rfps = get_rfps()
    return render_template("portal_index.html", portal=portal, rfps=rfps, portal_id=CURRENT_PORTAL_ID)


@app.route("/rfp/<rfp_id>")
def rfp_detail(rfp_id):
    portal = get_portal()
    rfps = get_rfps()
    rfp = next((r for r in rfps if r["rfp_id"] == rfp_id), None)
    if not rfp:
        abort(404)
    return render_template("rfp_detail.html", portal=portal, rfp=rfp, portal_id=CURRENT_PORTAL_ID)


@app.route("/download/<rfp_id>")
def download_rfp(rfp_id):
    """Download the actual PDF file."""
    rfps = RFP_DISTRIBUTION.get(CURRENT_PORTAL_ID, [])
    rfp = next((r for r in rfps if r["rfp_id"] == rfp_id), None)
    if not rfp:
        abort(404)
    filepath = rfp["filepath"]
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, as_attachment=True, download_name=rfp["filename"])


# ─── API Endpoints (for scraper) ─────────────────────────────────────────────

@app.route("/api/rfps")
def api_list_rfps():
    """JSON API listing all RFPs on this portal."""
    rfps = get_rfps()
    portal = get_portal()
    return jsonify({
        "portal_name": portal["name"],
        "portal_id": CURRENT_PORTAL_ID,
        "rfp_count": len(rfps),
        "rfps": rfps
    })


@app.route("/api/rfp/<rfp_id>")
def api_rfp_detail(rfp_id):
    """JSON API for single RFP details."""
    rfps = get_rfps()
    rfp = next((r for r in rfps if r["rfp_id"] == rfp_id), None)
    if not rfp:
        return jsonify({"error": "RFP not found"}), 404
    portal = get_portal()
    return jsonify({
        "portal_name": portal["name"],
        "portal_id": CURRENT_PORTAL_ID,
        "rfp": rfp,
        "download_url": f"http://localhost:{portal['port']}/download/{rfp_id}"
    })


@app.route("/api/download/<rfp_id>")
def api_download(rfp_id):
    """Direct PDF download endpoint for scraper."""
    return download_rfp(rfp_id)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    global CURRENT_PORTAL_ID
    parser = argparse.ArgumentParser(description="E-Procurement Portal")
    parser.add_argument("--portal", required=True, choices=PORTALS.keys(),
                        help="Portal ID to run (portal_1 through portal_5)")
    args = parser.parse_args()
    
    CURRENT_PORTAL_ID = args.portal
    portal = PORTALS[CURRENT_PORTAL_ID]
    
    print(f"\n{'='*60}")
    print(f" {portal['logo_icon']}  {portal['name']}")
    print(f" {portal['description']}")
    print(f" Running on http://localhost:{portal['port']}")
    rfps = RFP_DISTRIBUTION.get(CURRENT_PORTAL_ID, [])
    print(f" Hosting {len(rfps)} RFPs: {', '.join(r['filename'] for r in rfps)}")
    print(f"{'='*60}\n")
    
    app.run(host="0.0.0.0", port=portal["port"], debug=False)


if __name__ == "__main__":
    main()
