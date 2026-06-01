# Win/Loss Analytics Calculation Guide

## 🎯 How to Populate Win/Loss Data

There are 3 ways to calculate and populate win/loss metrics:

---

## **METHOD 1: Record Individual Bid Outcomes** (Manual)
After submitting a bid, record whether you won or lost.

### Endpoint:
```
POST /api/v1/analytics/record-bid-outcome
```

### Example Request:
```json
{
  "rfp_id": "GEM/2025/B/6694421",
  "bid_id": "BID-001",
  "outcome": "won",
  "our_bid_amount": 915000,
  "winning_bid_amount": 915000,
  "technical_score": 92.5,
  "commercial_score": 88.0,
  "winning_factors": ["Competitive pricing", "Technical expertise"],
  "losing_factors": [],
  "customer_name": "Power Grid Corporation",
  "customer_segment": "Government",
  "customer_region": "India"
}
```

### Using cURL:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/record-bid-outcome \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_id": "GEM/2025/B/6694421",
    "bid_id": "BID-001", 
    "outcome": "won",
    "our_bid_amount": 915000,
    "technical_score": 92.5
  }'
```

---

## **METHOD 2: Bulk Import Historical Data** (CSV/Excel)
Import multiple bid records from your CRM or historical system at once.

### Endpoint:
```
POST /api/v1/analytics/bulk-record-outcomes
```

### Example Request:
```json
[
  {
    "rfp_id": "GEM/2025/B/6694421",
    "outcome": "won",
    "our_bid_amount": 915000,
    "technical_score": 92.5
  },
  {
    "rfp_id": "GEM/2025/B/6694420",
    "outcome": "lost",
    "our_bid_amount": 850000,
    "winning_competitor": "Competitor A",
    "losing_factors": ["Price too high"]
  },
  {
    "rfp_id": "GEM/2025/B/6694422",
    "outcome": "no_bid"
  }
]
```

### Using cURL:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/bulk-record-outcomes \
  -H "Content-Type: application/json" \
  -d '[
    {"rfp_id": "GEM/2025/B/6694421", "outcome": "won", "our_bid_amount": 915000},
    {"rfp_id": "GEM/2025/B/6694420", "outcome": "lost", "our_bid_amount": 850000}
  ]'
```

---

## **METHOD 3: Get Calculated Ratio**
After recording outcomes, retrieve the calculated win/loss metrics.

### Endpoint:
```
GET /api/v1/analytics/win-loss-ratio/{rfp_id}
```

### Example Request:
```bash
curl http://localhost:8000/api/v1/analytics/win-loss-ratio/GEM/2025/B/6694421
```

### Example Response:
```json
{
  "success": true,
  "data": {
    "rfp_id": "GEM/2025/B/6694421",
    "status": "success",
    "win_percentage": 75.0,
    "win_ratio": 3.0,
    "won": 3,
    "lost": 1,
    "total_bids": 4,
    "bid_value": {
      "won_value": 2745000,
      "lost_value": 850000,
      "total_value": 3595000
    },
    "unique_competitors_count": 5,
    "score_analysis": {
      "avg_technical_score": 91.25,
      "avg_commercial_score": 87.5,
      "avg_overall_score": 89.375
    }
  }
}
```

---

## 📊 Field Reference

### Bid Outcome Fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rfp_id` | string | ✅ Yes | RFP ID (e.g., "GEM/2025/B/6694421") |
| `bid_id` | string | ❌ No | Internal bid identifier |
| `outcome` | string | ✅ Yes | "won", "lost", or "no_bid" |
| `our_bid_amount` | number | ❌ No | Our bid amount |
| `winning_bid_amount` | number | ❌ No | Winning bid amount |
| `winning_competitor` | string | ❌ No | Name of competitor who won |
| `competitor_names` | array | ❌ No | List of competing companies |
| `technical_score` | number | ❌ No | Technical evaluation score (0-100) |
| `commercial_score` | number | ❌ No | Commercial evaluation score (0-100) |
| `overall_score` | number | ❌ No | Overall score (0-100) |
| `winning_factors` | array | ❌ No | Reasons we won |
| `losing_factors` | array | ❌ No | Reasons we lost |
| `customer_name` | string | ❌ No | Customer/buyer name |
| `customer_segment` | string | ❌ No | Segment (e.g., "Government", "Private") |
| `customer_region` | string | ❌ No | Region (e.g., "India", "Europe") |
| `rfp_category` | string | ❌ No | RFP category |

---

## 🔄 How It Works

1. **Record outcomes** using any of the three methods above
2. **Backend processes** the data and stores in `analytics_win_loss` table
3. **Next RFP analysis** automatically calculates win/loss ratio
4. **Win/Loss card displays** with populated metrics

### Win/Loss Card Then Shows:
- ✅ Win Rate % (in emerald green)
- ✅ Win Ratio (e.g., 3.0:1)
- ✅ Won/Lost counts
- ✅ Competitors faced
- ✅ Bid value analysis (won vs lost)
- ✅ Score averages

---

## 🚀 Quick Start Example

### Step 1: Record a win
```bash
curl -X POST http://localhost:8000/api/v1/analytics/record-bid-outcome \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_id": "GEM/2025/B/6694421",
    "outcome": "won",
    "our_bid_amount": 915000
  }'
```

### Step 2: Record a loss  
```bash
curl -X POST http://localhost:8000/api/v1/analytics/record-bid-outcome \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_id": "GEM/2025/B/6694421",
    "outcome": "lost",
    "our_bid_amount": 850000
  }'
```

### Step 3: Check calculated ratio
```bash
curl http://localhost:8000/api/v1/analytics/win-loss-ratio/GEM/2025/B/6694421
```

### Step 4: Analyze RFP again
- Go to RFP Analyzer
- Upload same RFP or new one with same ID
- **Win/Loss card will now show calculated metrics!** 📊

---

## 💾 For Importing from CSV

Create a CSV like:
```
rfp_id,bid_id,outcome,our_bid_amount,technical_score,customer_name
GEM/2025/B/6694421,BID-001,won,915000,92.5,Power Grid
GEM/2025/B/6694420,BID-002,lost,850000,88.0,Ministry of Power
GEM/2025/B/6694422,BID-003,won,1200000,95.0,State Electricity
```

Convert to JSON and POST to `/bulk-record-outcomes` endpoint.

---

## 🎯 Next Steps

1. **Record some bid outcomes** using the endpoint
2. **Analyze an RFP** with the matching RFP ID
3. **See the metrics populate** on the Win/Loss card!

The calculation is now ready. You just need to feed it bid outcome data! 🚀
