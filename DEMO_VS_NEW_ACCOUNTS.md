# Demo vs New Accounts - Data Initialization

## 📋 Demo Account (admin/admin123, user/user1234)

**Demo account includes:**
- ✅ **Historical RFP bid outcomes** - Pre-populated with 6 sample bid records for demo RFP `GEM/2025/B/6694421`
- ✅ **Product database** - Full 22,000+ OEM product catalog
- ✅ **Sample metrics** - Win/loss analytics showing realistic data

### Demo Account Metrics (for RFP GEM/2025/B/6694421):
- **Win Rate**: 60.0%
- **Win Ratio**: 1.5:1 (3 wins to 2 losses)
- **Total Bids**: 6
- **Won/Lost**: 3/2
- **No Bid**: 1
- **Avg Technical Score**: 91.3
- **Avg Commercial Score**: 87.2
- **Competitors Faced**: 4

### To See Demo Data:
1. Log in with: `admin/admin123` or `user/user1234`
2. Go to **RFP Analyzer**
3. Upload any RFP document (demo data tied to `GEM/2025/B/6694421`)
4. Scroll down to see **"Win/Loss Rate Analysis"** card populated with metrics

---

## 🆕 New User Accounts

**New accounts start with:**
- ✅ **Product database** - Full 22,000+ OEM catalog (shared across all users)
- ❌ **NO historical bid data** - Empty `analytics_win_loss` table
- ❌ **NO pre-populated RFPs** - Users upload their own

### For New Users:
1. Create new account with username/password
2. Log in to RFP Analyzer
3. Upload RFP document
4. **Win/Loss card shows**: "No win/loss historical data available for this RFP yet"
5. To populate metrics, use endpoints:
   - `POST /api/v1/analytics/record-bid-outcome` - Record single outcome
   - `POST /api/v1/analytics/bulk-record-outcomes` - Import historical data
   - `GET /api/v1/analytics/win-loss-ratio/{rfp_id}` - Get calculated metrics

### New User Workflow:
```
1. Upload RFP
   ↓
2. See "No data" placeholder in card
   ↓
3. Record bid outcomes via API/UI
   ↓
4. Re-analyze same RFP
   ↓
5. See calculated metrics appear! 📊
```

---

## 🛠️ Database Reset

To reset demo account to initial state:

```bash
# Clear all win/loss records
python -c "
from database.db_engine import get_db_manager
from analytics.models import WinLossRecord

db = get_db_manager()
session = db.get_session()
session.query(WinLossRecord).delete()
session.commit()
session.close()
print('✓ All win/loss records cleared')
"

# Re-create demo data
python scripts/create_demo_seed_data.py
```

---

## 📊 Comparing Demo vs New Account

| Feature | Demo Account | New Account |
|---------|-------------|------------|
| Product Database | ✅ Full 22k+ catalog | ✅ Full 22k+ catalog |
| Historical Bid Data | ✅ 6 sample records | ❌ Empty |
| Win/Loss Analytics | ✅ Shows metrics | ❌ Shows placeholder |
| Can Record Bids | ✅ Yes | ✅ Yes |
| Can Upload RFPs | ✅ Yes | ✅ Yes |

---

## 🎯 Key Points

- **Demo data is isolated** - Only affects demo RFP `GEM/2025/B/6694421`
- **Product DB is shared** - All users see same 22k+ products
- **New users can quickly populate** - Use bulk import endpoint
- **No automatic reset** - Demo data persists unless manually cleared
- **Each user's data is separate** - Win/loss records tied to user/bid submissions

---

## 🚀 Next Steps

1. **For Demo**: Log in and see working Win/Loss card immediately
2. **For New Users**: Record some bid outcomes to see metrics populate
3. **For Data Import**: Use bulk endpoint to import from CSV/Excel

Done! ✅
