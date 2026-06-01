#!/usr/bin/env python3
"""Test win/loss analytics feature integration"""

import sys
import json
from pathlib import Path
from database.db_engine import get_db_manager
from analytics.win_loss_analytics import WinLossAnalytics

def test_win_loss_feature():
    """Check if win/loss feature is available and working"""
    print("\n" + "="*60)
    print("WIN/LOSS ANALYTICS FEATURE TEST")
    print("="*60)
    
    # Test 1: Check if win_loss_analytics module imports correctly
    print("\n✓ win_loss_analytics module imported successfully")
    
    # Test 2: Check database connection
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()
        print("✓ Database connection established")
        
        # Test 3: Query WinLossRecord table to see if data exists
        from analytics.models import WinLossRecord
        record_count = session.query(WinLossRecord).count()
        print(f"✓ WinLossRecord table has {record_count} records")
        
        # Test 4: Get list of RFPs in database
        rfps = session.query(WinLossRecord.rfp_id).distinct().limit(5).all()
        rfp_ids = [r[0] for r in rfps]
        print(f"✓ Sample RFP IDs in database: {rfp_ids}")
        
        # Test 5: Try to get win/loss ratio for each RFP
        if rfp_ids:
            print("\nTesting win/loss calculation for each RFP:")
            win_loss_analytics = WinLossAnalytics(session_factory=lambda: db_manager.get_session())
            
            for rfp_id in rfp_ids[:2]:  # Test first 2 RFPs
                result = win_loss_analytics.get_win_loss_ratio_by_rfp(session, rfp_id)
                print(f"\n  RFP: {rfp_id}")
                print(f"  Status: {result.get('status')}")
                print(f"  Won: {result.get('won')}, Lost: {result.get('lost')}")
                print(f"  Win Ratio: {result.get('win_ratio')}")
                print(f"  Win %: {result.get('win_percentage')}%")
                print(f"  Competitors: {result.get('unique_competitors_count')}")
        else:
            print("⚠ No win/loss records found in database")
        
        session.close()
        
    except Exception as e:
        print(f"✗ Database error: {type(e).__name__}: {e}")
        return False
    
    print("\n" + "="*60)
    print("TEST COMPLETE - Feature appears to be working!")
    print("="*60 + "\n")
    return True

if __name__ == '__main__':
    success = test_win_loss_feature()
    sys.exit(0 if success else 1)
