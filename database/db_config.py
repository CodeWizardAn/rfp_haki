"""
Database Configuration Module
Centralized path management for all database files

Database Folder Structure:
database/
├── db_vendors/          # Vendor management databases
│   ├── vendors.db       # Main vendor profiles
│   ├── vendor_ratings.db
│   ├── vendor_performance.db
│   └── vendor_communications.db
├── db_rfp/              # RFP and bid related databases
│   ├── bids.db          # Main bids database
│   ├── bid_approvals.db
│   ├── oem_bids.db
│   └── rfp_terms.json   # RFP terms database (100k entries)
├── db_products/         # Product catalogs and OEM data
│   ├── oem_products.json
│   ├── oem_datasheets.json
│   └── product_catalog.json
├── db_pricing/          # Pricing tables
│   ├── product_prices.json
│   ├── service_prices.json
│   └── compliance_rules.json
├── db_audit/            # Audit and logging
│   └── audit.db
└── db_agents/           # Agent-specific data
    ├── conversation_history.json
    └── workflow_logs.json
"""

import os
from pathlib import Path
from typing import Dict, Optional
from enum import Enum


class DatabaseType(Enum):
    """Database type enumeration"""
    # Vendor Management
    VENDORS = "vendors"
    VENDOR_RATINGS = "vendor_ratings"
    VENDOR_PERFORMANCE = "vendor_performance"
    VENDOR_COMMUNICATIONS = "vendor_communications"
    
    # RFP & Bids
    BIDS = "bids"
    BID_APPROVALS = "bid_approvals"
    OEM_BIDS = "oem_bids"
    RFP_TERMS = "rfp_terms"
    
    # Products
    OEM_PRODUCTS = "oem_products"
    OEM_DATASHEETS = "oem_datasheets"
    PRODUCT_CATALOG = "product_catalog"
    
    # Pricing
    PRODUCT_PRICES = "product_prices"
    SERVICE_PRICES = "service_prices"
    COMPLIANCE_RULES = "compliance_rules"
    
    # Audit
    AUDIT = "audit"
    
    # Agents
    CONVERSATION_HISTORY = "conversation_history"
    WORKFLOW_LOGS = "workflow_logs"


class DatabaseConfig:
    """
    Centralized database configuration manager
    Handles all database paths and ensures folder structure exists
    """
    
    # Base database directory (relative to project root)
    BASE_DIR = Path(__file__).parent
    
    # Subfolder mappings
    SUBFOLDERS = {
        'vendors': 'db_vendors',
        'rfp': 'db_rfp',
        'products': 'db_products',
        'pricing': 'db_pricing',
        'audit': 'db_audit',
        'agents': 'db_agents',
    }
    
    # Database file mappings (type -> (subfolder, filename, extension))
    DATABASE_MAPPING: Dict[DatabaseType, tuple] = {
        # Vendor databases (SQLite)
        DatabaseType.VENDORS: ('vendors', 'vendors', '.db'),
        DatabaseType.VENDOR_RATINGS: ('vendors', 'vendor_ratings', '.db'),
        DatabaseType.VENDOR_PERFORMANCE: ('vendors', 'vendor_performance', '.db'),
        DatabaseType.VENDOR_COMMUNICATIONS: ('vendors', 'vendor_communications', '.db'),
        
        # RFP databases (SQLite & JSON)
        DatabaseType.BIDS: ('rfp', 'bids', '.db'),
        DatabaseType.BID_APPROVALS: ('rfp', 'bid_approvals', '.db'),
        DatabaseType.OEM_BIDS: ('rfp', 'oem_bids', '.db'),
        DatabaseType.RFP_TERMS: ('rfp', 'rfp_terms_database_100k_new', '.json'),
        
        # Product databases (JSON)
        DatabaseType.OEM_PRODUCTS: ('products', 'oem_products', '.json'),
        DatabaseType.OEM_DATASHEETS: ('products', 'oem_datasheets', '.json'),
        DatabaseType.PRODUCT_CATALOG: ('products', 'product_catalog', '.json'),
        
        # Pricing databases (JSON)
        DatabaseType.PRODUCT_PRICES: ('pricing', 'product_prices', '.json'),
        DatabaseType.SERVICE_PRICES: ('pricing', 'service_prices', '.json'),
        DatabaseType.COMPLIANCE_RULES: ('pricing', 'compliance_rules', '.json'),
        
        # Audit database (SQLite)
        DatabaseType.AUDIT: ('audit', 'audit', '.db'),
        
        # Agent databases (JSON)
        DatabaseType.CONVERSATION_HISTORY: ('agents', 'conversation_history', '.json'),
        DatabaseType.WORKFLOW_LOGS: ('agents', 'workflow_logs', '.json'),
    }
    
    @classmethod
    def ensure_structure(cls) -> None:
        """Create all database subfolders if they don't exist"""
        for subfolder in cls.SUBFOLDERS.values():
            folder_path = cls.BASE_DIR / subfolder
            folder_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_path(cls, db_type: DatabaseType) -> Path:
        """
        Get the full path for a database file
        
        Args:
            db_type: DatabaseType enum value
            
        Returns:
            Full path to the database file
        """
        cls.ensure_structure()
        
        subfolder_key, filename, extension = cls.DATABASE_MAPPING[db_type]
        subfolder = cls.SUBFOLDERS[subfolder_key]
        
        return cls.BASE_DIR / subfolder / f"{filename}{extension}"
    
    @classmethod
    def get_subfolder_path(cls, subfolder_key: str) -> Path:
        """
        Get path to a specific subfolder
        
        Args:
            subfolder_key: Key from SUBFOLDERS dict (e.g., 'vendors', 'rfp')
            
        Returns:
            Full path to the subfolder
        """
        cls.ensure_structure()
        return cls.BASE_DIR / cls.SUBFOLDERS[subfolder_key]
    
    @classmethod
    def get_all_paths(cls) -> Dict[str, Path]:
        """Get all database paths as a dictionary"""
        return {
            db_type.value: cls.get_path(db_type)
            for db_type in DatabaseType
        }
    
    @classmethod
    def print_structure(cls) -> None:
        """Print the database folder structure"""
        print("\n📁 Database Folder Structure:")
        print("=" * 50)
        
        for subfolder_key, subfolder_name in cls.SUBFOLDERS.items():
            folder_path = cls.BASE_DIR / subfolder_name
            print(f"\n📂 {subfolder_name}/")
            
            # Find databases in this subfolder
            for db_type, (key, filename, ext) in cls.DATABASE_MAPPING.items():
                if key == subfolder_key:
                    db_path = folder_path / f"{filename}{ext}"
                    exists = "✅" if db_path.exists() else "⬜"
                    print(f"   {exists} {filename}{ext}")


def get_db_path(db_type: DatabaseType) -> str:
    """
    Convenience function to get database path as string
    
    Args:
        db_type: DatabaseType enum value
        
    Returns:
        Full path to database file as string
    """
    return str(DatabaseConfig.get_path(db_type))


# Initialize folder structure on import
DatabaseConfig.ensure_structure()


if __name__ == "__main__":
    # Print current structure
    DatabaseConfig.print_structure()
    
    print("\n\n📊 All Database Paths:")
    print("=" * 50)
    for name, path in DatabaseConfig.get_all_paths().items():
        exists = "✅" if path.exists() else "⬜"
        print(f"{exists} {name}: {path}")
