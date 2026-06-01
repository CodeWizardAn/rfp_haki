#!/usr/bin/env python3
"""
Test script to verify Win/Loss Analytics integration with RFP Analysis

This script tests:
1. WinLossAnalytics imports and methods
2. Database connectivity
3. Integration with REST API
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        from analytics.win_loss_analytics import WinLossAnalytics
        logger.info("✓ WinLossAnalytics imported successfully")
    except Exception as e:
        logger.error(f"✗ Failed to import WinLossAnalytics: {e}")
        return False
    
    try:
        from database.db_engine import get_db_manager
        logger.info("✓ get_db_manager imported successfully")
    except Exception as e:
        logger.error(f"✗ Failed to import get_db_manager: {e}")
        return False
    
    try:
        from api.rest_api import app
        logger.info("✓ FastAPI app imported successfully")
    except Exception as e:
        logger.error(f"✗ Failed to import FastAPI app: {e}")
        return False
    
    return True

def test_method_exists():
    """Test that the new method exists in WinLossAnalytics"""
    logger.info("Testing method existence...")
    
    try:
        from analytics.win_loss_analytics import WinLossAnalytics
        import inspect
        
        if not hasattr(WinLossAnalytics, 'get_win_loss_ratio_by_rfp'):
            logger.error("✗ get_win_loss_ratio_by_rfp method not found")
            return False
        
        logger.info("✓ get_win_loss_ratio_by_rfp method exists")
        
        # Check method signature
        method = getattr(WinLossAnalytics, 'get_win_loss_ratio_by_rfp')
        sig = inspect.signature(method)
        logger.info(f"  Method signature: {sig}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error checking method: {e}")
        return False

def test_database_connectivity():
    """Test that database can be initialized"""
    logger.info("Testing database connectivity...")
    
    try:
        from database.db_engine import get_db_manager
        
        db_manager = get_db_manager()
        logger.info("✓ Database manager initialized successfully")
        
        # Try to get a session
        session = db_manager.get_session()
        logger.info("✓ Database session created successfully")
        session.close()
        
        return True
    except Exception as e:
        logger.error(f"✗ Database connectivity error: {e}")
        return False

def test_win_loss_analytics_initialization():
    """Test that WinLossAnalytics can be initialized"""
    logger.info("Testing WinLossAnalytics initialization...")
    
    try:
        from analytics.win_loss_analytics import WinLossAnalytics
        from database.db_engine import get_db_manager
        
        db_manager = get_db_manager()
        
        # Initialize with session factory
        wl_analytics = WinLossAnalytics(session_factory=lambda: db_manager.get_session())
        logger.info("✓ WinLossAnalytics initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ WinLossAnalytics initialization error: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Win/Loss Analytics Integration Test Suite")
    logger.info("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Method Existence": test_method_exists(),
        "Database Connectivity": test_database_connectivity(),
        "WinLossAnalytics Initialization": test_win_loss_analytics_initialization(),
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
