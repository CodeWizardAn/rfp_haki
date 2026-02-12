"""
Configuration for all 5 e-procurement portals.
Distributes RFPs equally across portals.
"""
import os
import math
import glob

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
RFP_SOURCE_DIR = os.path.join(PROJECT_ROOT, "RFPs")

# Portal definitions
PORTALS = {
    "portal_1": {
        "name": "GovProcure India",
        "description": "Government e-Procurement portal for Infrastructure & Electrical supplies",
        "port": 5001,
        "theme_color": "#1a5276",
        "logo_icon": "🏛️",
    },
    "portal_2": {
        "name": "TenderBazaar",
        "description": "Online marketplace for public & private sector tenders",
        "port": 5002,
        "theme_color": "#117a65",
        "logo_icon": "🛒",
    },
    "portal_3": {
        "name": "eProcure Central",
        "description": "Centralized procurement platform for enterprise buyers",
        "port": 5003,
        "theme_color": "#6c3483",
        "logo_icon": "📋",
    },
    "portal_4": {
        "name": "BidConnect",
        "description": "Connecting vendors with procurement opportunities nationwide",
        "port": 5004,
        "theme_color": "#b9770e",
        "logo_icon": "🤝",
    },
    "portal_5": {
        "name": "SmartTender Hub",
        "description": "AI-powered smart tendering and procurement platform",
        "port": 5005,
        "theme_color": "#c0392b",
        "logo_icon": "🧠",
    },
}


def get_rfp_files():
    """Get all RFP PDF files sorted by number."""
    pattern = os.path.join(RFP_SOURCE_DIR, "RFP*.pdf")
    files = glob.glob(pattern)
    # Sort by numeric part
    def sort_key(f):
        name = os.path.basename(f)
        num = ''.join(c for c in name.replace('.pdf', '').replace('RFP', '') if c.isdigit())
        return int(num) if num else 0
    return sorted(files, key=sort_key)


def distribute_rfps():
    """Distribute RFPs equally across 5 portals."""
    rfp_files = get_rfp_files()
    portal_ids = list(PORTALS.keys())
    num_portals = len(portal_ids)
    
    distribution = {pid: [] for pid in portal_ids}
    
    for idx, rfp_path in enumerate(rfp_files):
        portal_id = portal_ids[idx % num_portals]
        distribution[portal_id].append({
            "filename": os.path.basename(rfp_path),
            "filepath": rfp_path,
            "rfp_id": os.path.basename(rfp_path).replace('.pdf', ''),
        })
    
    return distribution


def get_portal_rfps(portal_id):
    """Get RFPs assigned to a specific portal."""
    dist = distribute_rfps()
    return dist.get(portal_id, [])


# Pre-compute distribution
RFP_DISTRIBUTION = distribute_rfps()

if __name__ == "__main__":
    print("=== RFP Distribution Across Portals ===\n")
    dist = distribute_rfps()
    for pid, rfps in dist.items():
        portal = PORTALS[pid]
        print(f"{portal['logo_icon']} {portal['name']} (port {portal['port']}):")
        for r in rfps:
            print(f"   - {r['filename']}")
        print()
