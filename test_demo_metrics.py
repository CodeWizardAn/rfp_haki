#!/usr/bin/env python3
"""Quick test of demo data metrics"""

import sys
sys.path.insert(0, '/'.join(__file__.split('/')[:-2]))

from database.db_engine import get_db_manager
from analytics.win_loss_analytics import WinLossAnalytics

db = get_db_manager()
session = db.get_session()

analytics = WinLossAnalytics(session_factory=lambda: db.get_session())
result = analytics.get_win_loss_ratio_by_rfp(session, 'GEM/2025/B/6694421')

print('\n✅ Win/Loss Ratio Calculated:')
print(f'  Status: {result["status"]}')
print(f'  Win %: {result["win_percentage"]}%')
print(f'  Win Ratio: {result["win_ratio"]}:1')
print(f'  Total Bids: {result["total_bids"]}')
print(f'  Won/Lost: {result["won"]}/{result["lost"]}')
print(f'  Competitors: {result["unique_competitors_count"]}')
print(f'  Won Value: ₹{result["bid_value"]["won_value"]:,}')
print(f'  Lost Value: ₹{result["bid_value"]["lost_value"]:,}')
print(f'  Avg Technical: {result["score_analysis"]["avg_technical_score"]}')

print('\n📊 Card will display exactly these metrics!\n')

session.close()
