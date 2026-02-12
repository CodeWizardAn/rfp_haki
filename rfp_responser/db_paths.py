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
