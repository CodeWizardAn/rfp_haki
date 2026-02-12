# E-Procure Portals

## Overview
5 simulated e-procurement portal websites, each hosting a portion of the RFPs from the `RFPs/` folder.

## Portals

| Portal | Name | Port | RFPs |
|--------|------|------|------|
| portal_1 | 🏛️ GovProcure India | 5001 | RFP2, RFP22, RFP27 |
| portal_2 | 🛒 TenderBazaar | 5002 | RFP17, RFP23, RFP28 |
| portal_3 | 📋 eProcure Central | 5003 | RFP18, RFP24, RFP29 |
| portal_4 | 🤝 BidConnect | 5004 | RFP19, RFP25, RFP30 |
| portal_5 | 🧠 SmartTender Hub | 5005 | RFP20, RFP26 |

## Usage

### Launch All Portals
```bash
python e_procure_portals/launch_all_portals.py
```

### Launch Single Portal
```bash
python e_procure_portals/portal_app.py --portal portal_1
```

### API Endpoints
Each portal exposes:
- `GET /` - Portal homepage with RFP listings
- `GET /rfp/<rfp_id>` - RFP detail page
- `GET /download/<rfp_id>` - Download RFP PDF
- `GET /api/rfps` - JSON listing of all RFPs
- `GET /api/rfp/<rfp_id>` - JSON detail for single RFP
- `GET /api/download/<rfp_id>` - Direct download for scraper

## Architecture
```
e_procure_portals/
├── portal_config.py       # Portal definitions & RFP distribution
├── portal_app.py          # Flask app (shared by all 5 portals)
├── launch_all_portals.py  # Launches all 5 simultaneously
├── templates/
│   ├── portal_index.html  # Portal homepage template
│   └── rfp_detail.html    # RFP detail page template
└── static/                # Static assets
```
