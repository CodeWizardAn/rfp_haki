"""
Database Path Helper for Vendor Management
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


def get_vendors_db_path() -> Path:
    """Get path to vendors database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDORS)
    return Path(__file__).parent / 'vendors.db'


def get_vendor_ratings_db_path() -> Path:
    """Get path to vendor ratings database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDOR_RATINGS)
    return Path(__file__).parent / 'vendor_ratings.db'


def get_vendor_performance_db_path() -> Path:
    """Get path to vendor performance database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDOR_PERFORMANCE)
    return Path(__file__).parent / 'vendor_performance.db'


def get_vendor_communications_db_path() -> Path:
    """Get path to vendor communications database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.VENDOR_COMMUNICATIONS)
    return Path(__file__).parent / 'vendor_communications.db'


def get_audit_db_path() -> Path:
    """Get path to audit database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.AUDIT)
    return Path(__file__).parent.parent / 'audit.db'


# For OEM vendor management
def get_oem_vendors_db_path() -> Path:
    """Get path to OEM vendors database"""
    if DB_CONFIG_AVAILABLE:
        return DatabaseConfig.get_path(DatabaseType.OEM_BIDS)
    return Path(__file__).parent / 'oem_vendors.db'
