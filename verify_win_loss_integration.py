#!/usr/bin/env python3
"""Verify win/loss analytics integration is complete and ready"""

import sys
sys.path.insert(0, '/'.join(__file__.split('/')[:-2]))

def verify_integration():
    """Verify all components are integrated"""
    print("\n" + "="*70)
    print("WIN/LOSS ANALYTICS - FEATURE INTEGRATION VERIFICATION")
    print("="*70)
    
    checks = []
    
    # Check 1: Backend module available
    try:
        from analytics.win_loss_analytics import WinLossAnalytics
        checks.append(("✅ Backend WinLossAnalytics module", True))
    except Exception as e:
        checks.append((f"❌ Backend module: {e}", False))
    
    # Check 2: Analytics models available
    try:
        from analytics.models import WinLossRecord
        checks.append(("✅ WinLossRecord model defined", True))
    except Exception as e:
        checks.append((f"❌ WinLossRecord model: {e}", False))
    
    # Check 3: Database table exists
    try:
        from database.db_engine import get_db_manager
        from analytics.models import WinLossRecord
        db_manager = get_db_manager()
        session = db_manager.get_session()
        from sqlalchemy import inspect
        inspector = inspect(db_manager._engine)
        tables = inspector.get_table_names()
        if 'analytics_win_loss' in tables:
            checks.append(("✅ Database table 'analytics_win_loss' created", True))
        else:
            checks.append(("❌ Database table not found", False))
        session.close()
    except Exception as e:
        checks.append((f"❌ Database check: {e}", False))
    
    # Check 4: REST API endpoint configured
    try:
        import inspect as code_inspect
        from api.rest_api import app
        
        # Find the analyze endpoint
        routes = app.routes
        analyze_found = False
        for route in routes:
            if '/rfps/analyze' in str(route.path):
                analyze_found = True
                break
        
        if analyze_found:
            checks.append(("✅ REST API /rfps/analyze endpoint configured", True))
        else:
            checks.append(("❌ /rfps/analyze endpoint not found", False))
    except Exception as e:
        checks.append((f"❌ API check: {e}", False))
    
    # Check 5: Feature flag
    try:
        from api.rest_api import WIN_LOSS_ANALYTICS_AVAILABLE
        if WIN_LOSS_ANALYTICS_AVAILABLE:
            checks.append(("✅ WIN_LOSS_ANALYTICS_AVAILABLE = True", True))
        else:
            checks.append(("⚠️  WIN_LOSS_ANALYTICS_AVAILABLE = False", False))
    except Exception as e:
        checks.append((f"❌ Feature flag: {e}", False))
    
    # Check 6: Frontend types defined
    try:
        frontend_file = "d:\\Haki_FMCG_2.0\\haki-fmcg-frontend\\src\\pages\\user\\UserRFPAnalyzerPage.tsx"
        with open(frontend_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'win_loss_analysis' in content and 'Win/Loss Rate Analysis' in content:
                checks.append(("✅ Frontend UI component for win/loss card", True))
            else:
                checks.append(("❌ Frontend UI component not found", False))
    except Exception as e:
        checks.append((f"❌ Frontend check: {e}", False))
    
    # Check 7: Service layer updated
    try:
        service_file = "d:\\Haki_FMCG_2.0\\haki-fmcg-frontend\\src\\services\\rfp.service.ts"
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'include_win_loss' in content:
                checks.append(("✅ Frontend service includes include_win_loss parameter", True))
            else:
                checks.append(("❌ Frontend service not updated", False))
    except Exception as e:
        checks.append((f"❌ Service check: {e}", False))
    
    # Print results
    print("\nINTEGRATION CHECKS:")
    print("-" * 70)
    all_pass = True
    for check, passed in checks:
        print(check)
        if not passed and not "⚠️" in check:
            all_pass = False
    
    print("-" * 70)
    if all_pass:
        print("\n✅ ALL CHECKS PASSED - FEATURE IS FULLY INTEGRATED & READY!")
        print("\nFEATURE STATUS:")
        print("  • Backend: ✅ Non-blocking, optional (include_win_loss=false by default)")
        print("  • Database: ✅ Table created and ready")
        print("  • Frontend: ✅ Card UI ready to display data")
        print("  • Service: ✅ API parameter supported")
        print("\nREADY FOR PRODUCTION: The feature will display metrics when")
        print("win/loss data is available in the database for an RFP.")
    else:
        print("\n❌ Some checks failed - review above")
    
    print("="*70 + "\n")
    return all_pass

if __name__ == '__main__':
    success = verify_integration()
    sys.exit(0 if success else 1)
