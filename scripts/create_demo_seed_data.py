#!/usr/bin/env python3
"""
Demo Account Seed Data
Populates historical bid outcomes for demo RFP so win/loss analytics display working metrics
Only runs for demo accounts, not for new user accounts
"""

import sys
sys.path.insert(0, '/'.join(__file__.split('/')[:-2]))

from database.db_engine import get_db_manager
from analytics.models import WinLossRecord
from datetime import datetime, timedelta

def create_demo_bid_history():
    """Create historical bid outcomes for demo RFP"""
    
    print("\n" + "="*70)
    print("DEMO ACCOUNT SEED DATA - Creating Historical Win/Loss Records")
    print("="*70)
    
    # Demo RFP from the screenshot
    demo_rfp_id = "GEM/2025/B/6694421"
    
    # Sample historical bid outcomes showing realistic win/loss pattern
    demo_records = [
        {
            "rfp_id": demo_rfp_id,
            "bid_id": "BID-DEM-001",
            "outcome": "won",
            "our_bid_amount": 915000,
            "winning_bid_amount": 915000,
            "technical_score": 92.5,
            "commercial_score": 88.0,
            "overall_score": 90.25,
            "winning_factors": ["Competitive pricing", "Technical expertise", "Fast delivery"],
            "losing_factors": [],
            "customer_name": "Power Grid Corporation Of India Limited",
            "customer_segment": "Government",
            "customer_region": "India",
            "rfp_category": "Power Distribution Equipment",
            "days_ago": 45
        },
        {
            "rfp_id": demo_rfp_id,
            "bid_id": "BID-DEM-002",
            "outcome": "lost",
            "our_bid_amount": 875000,
            "winning_bid_amount": 850000,
            "winning_competitor": "Competitor A",
            "competitor_names": ["Competitor A", "Competitor B"],
            "technical_score": 88.0,
            "commercial_score": 82.0,
            "overall_score": 85.0,
            "winning_factors": [],
            "losing_factors": ["Price too high", "Delivery timeline too long"],
            "customer_name": "Ministry of Power",
            "customer_segment": "Government",
            "customer_region": "India",
            "rfp_category": "Power Distribution Equipment",
            "days_ago": 30
        },
        {
            "rfp_id": demo_rfp_id,
            "bid_id": "BID-DEM-003",
            "outcome": "won",
            "our_bid_amount": 1050000,
            "winning_bid_amount": 1050000,
            "technical_score": 95.0,
            "commercial_score": 90.0,
            "overall_score": 92.5,
            "winning_factors": ["Superior technical specs", "Best price", "Warranty coverage"],
            "losing_factors": [],
            "customer_name": "State Electricity Board",
            "customer_segment": "Government",
            "customer_region": "India",
            "rfp_category": "Power Distribution Equipment",
            "days_ago": 20
        },
        {
            "rfp_id": demo_rfp_id,
            "bid_id": "BID-DEM-004",
            "outcome": "no_bid",
            "customer_name": "Private Power Distributor",
            "customer_segment": "Private",
            "customer_region": "India",
            "days_ago": 15
        },
        {
            "rfp_id": demo_rfp_id,
            "bid_id": "BID-DEM-005",
            "outcome": "won",
            "our_bid_amount": 1200000,
            "winning_bid_amount": 1200000,
            "technical_score": 93.0,
            "commercial_score": 91.0,
            "overall_score": 92.0,
            "winning_factors": ["Technical excellence", "Proven track record"],
            "losing_factors": [],
            "customer_name": "Northern Power Grid",
            "customer_segment": "Government",
            "customer_region": "India",
            "rfp_category": "Power Distribution Equipment",
            "days_ago": 10
        },
        {
            "rfp_id": demo_rfp_id,
            "bid_id": "BID-DEM-006",
            "outcome": "lost",
            "our_bid_amount": 950000,
            "winning_bid_amount": 900000,
            "winning_competitor": "Competitor C",
            "competitor_names": ["Competitor C", "Competitor D"],
            "technical_score": 89.0,
            "commercial_score": 85.0,
            "overall_score": 87.0,
            "winning_factors": [],
            "losing_factors": ["Competitor offered lower price", "Established relationship advantage"],
            "customer_name": "Central Electricity Authority",
            "customer_segment": "Government",
            "customer_region": "India",
            "rfp_category": "Power Distribution Equipment",
            "days_ago": 5
        }
    ]
    
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        # Check if demo data already exists
        existing = session.query(WinLossRecord).filter(
            WinLossRecord.rfp_id == demo_rfp_id,
            WinLossRecord.bid_id.like("BID-DEM-%")
        ).count()
        
        if existing > 0:
            print(f"\n✓ Demo data already exists ({existing} records)")
            print("  Skipping creation to avoid duplicates")
            session.close()
            return True
        
        # Create records with timestamp offset
        records = []
        for record_data in demo_records:
            days_ago = record_data.pop("days_ago", 0)
            recorded_at = datetime.utcnow() - timedelta(days=days_ago)
            
            record = WinLossRecord(
                rfp_id=record_data["rfp_id"],
                bid_id=record_data.get("bid_id"),
                outcome=record_data["outcome"],
                our_bid_amount=record_data.get("our_bid_amount"),
                winning_bid_amount=record_data.get("winning_bid_amount"),
                winning_competitor=record_data.get("winning_competitor"),
                competitor_names=record_data.get("competitor_names", []),
                technical_score=record_data.get("technical_score"),
                commercial_score=record_data.get("commercial_score"),
                overall_score=record_data.get("overall_score"),
                winning_factors=record_data.get("winning_factors", []),
                losing_factors=record_data.get("losing_factors", []),
                customer_name=record_data.get("customer_name"),
                customer_segment=record_data.get("customer_segment"),
                customer_region=record_data.get("customer_region"),
                rfp_category=record_data.get("rfp_category"),
                recorded_at=recorded_at,
                recorded_by="demo_seed"
            )
            records.append(record)
        
        # Add all records
        session.add_all(records)
        session.commit()
        session.close()
        
        print(f"\n✅ Created {len(records)} historical bid records for demo account")
        print(f"   RFP ID: {demo_rfp_id}")
        print(f"   Win rate: 3 Won / 2 Lost / 1 No Bid")
        print(f"   Win %: 60% (3 wins out of 5 participated)")
        print(f"   Win Ratio: 1.5:1")
        
        print("\n📊 Expected Card Metrics:")
        print("   - Win Rate: 60.0%")
        print("   - Win Ratio: 1.5:1")
        print("   - Total Bids: 6")
        print("   - Won/Lost: 3/2")
        print("   - Competitors faced: 4")
        print("   - Avg Technical Score: 91.3")
        print("   - Avg Commercial Score: 87.2")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating demo data: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = create_demo_bid_history()
    print("\n" + "="*70 + "\n")
    sys.exit(0 if success else 1)
