"""
Database Path Helper for RFP Responser
Provides centralized database paths
"""

import sys
from pathlib import Path

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from database.db_config import DatabaseConfig, DatabaseType
    DB_CONFIG_AVAILABLE = True
except ImportError:
    DB_CONFIG_AVAILABLE = False


def get_bids_db_path() -> Path:
    """Get path to bids database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.BIDS)
    return Path(__file__).parent / 'bids.db'


def get_bid_approvals_db_path() -> Path:
    """Get path to bid approvals database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.BID_APPROVALS)
    return Path(__file__).parent / 'bid_approvals.db'


def get_oem_bids_db_path() -> Path:
    """Get path to OEM bids database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.OEM_BIDS)
    return Path(__file__).parent / 'oem_bids.db'


def get_rfp_terms_db_path() -> Path:
    """Get path to RFP terms database (JSON)"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.RFP_TERMS)
    return Path(__file__).parent.parent / 'pdf_extraction' / 'rfp_terms_database_100k_new.json'


# Vendor database paths (bridged to prevent sys.path shadowing)
def get_vendors_db_path() -> Path:
    """Get path to vendors database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDORS)
    return Path(__file__).parent.parent / 'database' / 'db_vendors' / 'vendors.db'


def get_vendor_ratings_db_path() -> Path:
    """Get path to vendor ratings database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDOR_RATINGS)
    return Path(__file__).parent.parent / 'database' / 'db_vendors' / 'vendor_ratings.db'


def get_vendor_performance_db_path() -> Path:
    """Get path to vendor performance database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDOR_PERFORMANCE)
    return Path(__file__).parent.parent / 'database' / 'db_vendors' / 'vendor_performance.db'


def get_vendor_communications_db_path() -> Path:
    """Get path to vendor communications database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDOR_COMMUNICATIONS)
    return Path(__file__).parent.parent / 'database' / 'db_vendors' / 'vendor_communications.db'

