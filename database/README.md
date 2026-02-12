# Database Organization

Centralized database management for the Haki FMCG 2.0 system. All databases are organized in structured subfolders with clear naming conventions.

## 📁 Folder Structure

```
database/
├── db_config.py           # Central configuration module
├── __init__.py            # Package initialization
├── README.md              # This file
│
├── db_vendors/            # Vendor Management Databases
│   ├── vendors.db         # Main vendor profiles (SQLite)
│   ├── vendor_ratings.db  # Vendor rating history
│   ├── vendor_performance.db  # Delivery & quality metrics
│   └── vendor_communications.db  # Email/message history
│
├── db_rfp/                # RFP & Bid Databases
│   ├── bids.db            # Main bids database
│   ├── bid_approvals.db   # Approval workflow
│   ├── oem_bids.db        # OEM-specific bid data
│   └── rfp_terms_database_100k_new.json  # 100K+ RFP terms
│
├── db_products/           # Product Catalogs
│   ├── oem_products.json  # OEM product catalog (15+ products)
│   ├── oem_datasheets.json  # Detailed product datasheets
│   └── product_catalog.json  # Full product catalog
│
├── db_pricing/            # Pricing Tables
│   ├── product_prices.json  # Product pricing (15+ SKUs)
│   ├── service_prices.json  # Test & service pricing (13+ services)
│   └── compliance_rules.json  # Compliance validation rules
│
├── db_audit/              # Audit & Logging
│   └── audit.db           # Comprehensive audit trail
│
└── db_agents/             # Agent System Data
    ├── conversation_history.json  # Agent conversation logs
    └── workflow_logs.json  # Workflow execution history
```

## 🔧 Usage

### Python Import

```python
from database import DatabaseConfig, get_db_path
from database.db_config import DatabaseType

# Get path to a specific database
vendors_db = get_db_path(DatabaseType.VENDORS)
product_prices = get_db_path(DatabaseType.PRODUCT_PRICES)

# Get all database paths
all_paths = DatabaseConfig.get_all_paths()

# Print current structure
DatabaseConfig.print_structure()
```

### Database Types Available

| Type | File | Format |
|------|------|--------|
| VENDORS | vendors.db | SQLite |
| VENDOR_RATINGS | vendor_ratings.db | SQLite |
| VENDOR_PERFORMANCE | vendor_performance.db | SQLite |
| VENDOR_COMMUNICATIONS | vendor_communications.db | SQLite |
| BIDS | bids.db | SQLite |
| BID_APPROVALS | bid_approvals.db | SQLite |
| OEM_BIDS | oem_bids.db | SQLite |
| RFP_TERMS | rfp_terms_database_100k_new.json | JSON |
| OEM_PRODUCTS | oem_products.json | JSON |
| OEM_DATASHEETS | oem_datasheets.json | JSON |
| PRODUCT_CATALOG | product_catalog.json | JSON |
| PRODUCT_PRICES | product_prices.json | JSON |
| SERVICE_PRICES | service_prices.json | JSON |
| COMPLIANCE_RULES | compliance_rules.json | JSON |
| AUDIT | audit.db | SQLite |
| CONVERSATION_HISTORY | conversation_history.json | JSON |
| WORKFLOW_LOGS | workflow_logs.json | JSON |

## 📊 Data Content Summary

### db_products/oem_products.json
- **15 OEM products** from 5 manufacturers
- Polycab, Havells, KEI Industries, Finolex, RR Kabel
- Categories: PVC Insulated Wire, XLPE Armoured Cable, Flexible Cable
- Full specifications, certifications, and standards compliance

### db_pricing/product_prices.json
- **15+ product SKUs** with pricing
- Unit prices, MOQ, bulk discounts
- Lead times and categories

### db_pricing/service_prices.json
- **13+ testing services** with pricing
- Routine tests, type tests, inspections
- Turnaround times and standards

### db_pricing/compliance_rules.json
- **10 compliance rules** for spec matching
- Electrical, material, physical, certification checks
- Severity levels and comparison types

## 🔄 Migration Notes

The database folder centralizes all data previously scattered across:
- `vendor_management/` - SQLite databases
- `rfp_responser/` - Bids database
- `pdf_extraction/` - RFP terms JSON
- `agents/` - Hardcoded pricing and product data

## 📝 Updating Data

### Add New Product
Edit `db_products/oem_products.json`:
```json
{
  "sku": "NEW-SKU-001",
  "name": "New Product Name",
  "manufacturer": "Manufacturer",
  ...
}
```

### Add New Price
Edit `db_pricing/product_prices.json`:
```json
{
  "sku": "NEW-SKU-001",
  "product_name": "New Product",
  "unit_price": 100.00,
  ...
}
```

### Add New Test/Service
Edit `db_pricing/service_prices.json`:
```json
{
  "service_id": "TEST_NEW",
  "service_name": "New Test",
  "price": 5000.00,
  ...
}
```
