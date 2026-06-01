# HAKI FMCG 2.0 — Team Roles, Real Metrics & Method Advantage
### 3-Slide Presentation Content

---

## SLIDE 1 — What We Built & Why It's Faster

### Headline
**From 2–3 Weeks to 4–6 Hours Per RFP — Here's How**

### Sub-Headline
*22,000+ Products · 100,000+ RFP Terms · 16-Stage Parallel Pipeline · 5 Engineering Roles*

---

### Left Column — Speed: Before vs After

> **Visualize as a horizontal bar chart or before/after comparison**

| Stage | Manual Process | Our System |
|---|---|---|
| Read & understand RFP | 1–2 days | ~30 sec (PDF extraction + 100K-term matching) |
| Find matching products | 2–3 days | ~2–5 sec (22K catalog, weighted scoring) |
| Build pricing table | 1–2 days | ~1 sec (price table lookup + GST auto-calc) |
| Write bid document | 3–5 days | ~10 sec (PDF + Excel auto-generated) |
| Compliance check | 1 day | ~1 sec (8-rule engine, instant flag) |
| **Total** | **2–3 weeks** | **4–6 hours (including human review)** |

> **Efficiency Gain: 5–10× throughput improvement for the same team size**
> 90% of wins correlate to responding within the first 48 hours — this system eliminates that bottleneck.

---

### Center Column — Pipeline at a Glance

```
PDF Upload
    │
    ▼  [~30s]  PDF Extraction + 100K RFP Term Match
    │
    ▼  [~2s]   Sales Agent → Scans, prioritizes, selects RFP
    │
    ▼            Master Orchestrator
               ↙               ↘  ← PARALLEL (biggest time save)
   Technical Agent        Pricing Agent
   22K-product match      Price lookup + GST
   10-step scoring        Volume discounts
               ↘               ↙
    ▼  [~10s]  Consolidated Bid Document
               (PDF · Excel · Audit Trail)
```

**Key parallel processing fact:** Technical Agent and Pricing Agent run simultaneously.
Without parallelism, sequential processing would add ~40–60% more time per RFP.

---

### Right Column — Scale Numbers (Slide KPI Cards)

> **Visualize as 6 large KPI tiles**

| KPI | Value |
|---|---|
| 🗂 OEM Products in Catalog | **22,000+** |
| 📄 RFP Terms Database | **100,000+** |
| ⚡ Spec Match Speed | **<5 seconds** |
| 🔗 API Endpoints | **70+** |
| 📊 Live Metrics Tracked | **200+** |
| 🏗 Pipeline Stages | **16** |

---

---

## SLIDE 2 — The 5 Roles: Who Built What and What It Produces

### Headline
**5 Roles · 14 Modules · Real Outputs at Every Layer**

---

### Role Card 1 — AI System Architect
**"Designed the 4-Agent Orchestration Core"**

**What it produces concretely:**
- A ranked list of Top 3 OEM products per RFP item — with a % match score per product
- A color-coded comparison table: RFP Spec vs OEM 1 vs OEM 2 vs OEM 3
- An overall bid recommendation: HIGHLY RECOMMENDED / RECOMMENDED / CONDITIONAL / REVIEW REQUIRED

**Accuracy tiers built into the engine:**

| Score | Label | Meaning |
|---|---|---|
| ≥ 95% | EXCELLENT | Sell with full confidence |
| ≥ 85% | GOOD | Minor gaps, document them |
| ≥ 70% | FAIR | Gaps exist, conditional bid |
| ≥ 50% | POOR | Significant risk |
| < 50% or critical fail | DISQUALIFIED | Hard reject — do not bid |

**Why this is different from a simple keyword match:**
A keyword system would match "copper" to "copper" and stop.
Our system detects that **"ETP Copper" = "Electrolytic Grade Copper" = "Cu" = "99.97% pure copper"** — all the same material — and gives a full match score of 1.0. A naive system would score these as 0 (no match), causing false negatives on 30–40% of valid product matches.

**Critical failure gate (hard disqualifier — not averaged away):**
- Voltage mismatch >10% → DISQUALIFIED regardless of other scores
- Conductor size mismatch >20% → DISQUALIFIED
- Wrong material (copper vs aluminium) → DISQUALIFIED
- Missing BIS/ISI/CPRI certification → DISQUALIFIED

**Dual speed modes:**

| Mode | Speed | When |
|---|---|---|
| Deterministic engine | Milliseconds | Always — primary response path |
| LLM enrichment (Llama 3.3 70B) | 30–45 seconds | Async background, enriches output |

---

### Role Card 2 — NLP & Data Engineer
**"Made 22,000 Products and Messy RFP Text Talk to Each Other"**

**What it produces concretely:**
- Semantic search results: query "4 core 240 sqmm XLPE 33kV" → returns top-10 matching products by cosine similarity even if the product description uses completely different phrasing
- Normalized specs: "1.1kV", "1100V AC", "650/1100V" all resolve to the same canonical `1100v` before matching — eliminates false mismatches
- AWG↔sqmm conversion: "14 AWG" → 2.08 sqmm, "250 kcmil" → 126.7 sqmm automatically

**Why this matters — the "vocabulary problem":**

| RFP says | Product catalog says | Naive system | Our system |
|---|---|---|---|
| "Cross-linked polyethylene" | "XLPE" | ❌ No match | ✅ Match (1.0) |
| "1.1kV" | "1100V AC" | ❌ No match | ✅ Match (1.0) |
| "Galvanized steel wire" | "SWA" | ❌ No match | ✅ Match (1.0) |
| "14 AWG copper" | "2.5 sqmm copper" | ❌ No match | ✅ ~0.95 (within 10%) |
| "2.6 sqmm conductor" | "2.5 sqmm conductor" | ❌ No match | ✅ 0.95 (±10% tolerance) |

**Numeric tolerance scoring (not binary pass/fail):**

| Difference | Score | Effect |
|---|---|---|
| Exact match | 1.00 | Full credit |
| ≤ 10% off | 0.95 | Near-full credit |
| ≤ 20% off | 0.80 | Partial credit |
| > 20% off | 0.00 | Fail |

**Standards equivalence (real cross-body mapping):**
IS 7098-1 ↔ IEC 60502-1 ↔ BS 6346 — the system knows these are the same standard from different bodies. 16 such equivalence groups covering BIS, IEC, BS, ASTM, IEEE.

---

### Role Card 3 — Backend Systems Engineer
**"Built the Server That Never Blocks and Never Loses Data"**

**What it produces concretely:**
- A FastAPI server (`rest_api.py`, 5,118 lines) answering 70+ endpoints with <100ms target response
- A 16-stage pipeline that logs every step, can be retried, cancelled, and monitored in real time via SSE
- Thread-safe atomic file writes and WAL-mode SQLite — zero data corruption even under concurrent requests

**Real performance numbers built into the system:**

| SLA Level | Threshold | Action if breached |
|---|---|---|
| Excellent | < 100ms | ✅ Green |
| Good | < 500ms | ✅ Yellow |
| Acceptable | < 1,000ms | ⚠ Alert |
| Poor | > 3,000ms | 🔴 Alert + log |

**Rate limits enforced:**

| Endpoint Type | Limit |
|---|---|
| General API | 100 requests / min |
| Search endpoints | 20 requests / min |
| File upload | 5 requests / min |

**Why SQLite + WAL over a naive setup:**
PRAGMA WAL mode allows concurrent reads during writes — no read lock contention.
PRAGMA cache_size = -64000 keeps 64MB of hot data in memory. For a single-server procurement platform, this eliminates a separate DB server while giving near-PostgreSQL throughput.

---

### Role Card 4 — Frontend Engineer
**"Built 70+ Pages That Any Procurement Manager Can Use Today"**

**What it produces concretely:**
- A live dashboard showing agent activity, pipeline progress %, and KPI cards — all updating in real time via SSE without page refresh
- A bid builder with a pricing editor, approval workflow, and PDF/Excel export — end-to-end in-browser
- A product comparison page: side-by-side OEM specs, match scores, and price per unit

**Architecture advantage — why the UI never shows stale data:**

```
Component → React Query (cache) → Service → Axios → FastAPI
                  ↑
          On mutation success:
          invalidateQueries() → auto-refetch
                  ↑
          useEventStream (SSE) → live push for pipeline progress
```

- Exponential backoff reconnection on SSE drop (retryBaseMs × 2^retryCount, capped at retryMaxMs)
- Silent JWT refresh: concurrent requests queue during token refresh — user never sees a logout

---

### Role Card 5 — UI/UX Engineer
**"Built a Design System That Communicates Compliance Status at a Glance"**

**What it produces concretely:**
- Color-coded match score badges: 🟢 EXCELLENT (≥95%) · 🔵 GOOD (≥85%) · 🟡 FAIR (≥70%) · 🔴 POOR (<50%)
- A compliance table where every spec row is green (pass) / amber (partial) / red (fail) — reviewers see gaps instantly without reading text
- A glassmorphism dark-mode dashboard that remains readable in dimly-lit procurement rooms and on projector screens

**Design tokens that map directly to system states:**

| Color Token | Hex | Used For |
|---|---|---|
| neon-emerald | #00E68A | Match EXCELLENT / Compliance PASS |
| electric-cyan | #00D4FF | Primary actions, scores |
| amber-glow | #FFB224 | FAIR match / Warning |
| coral-flame | #FF4757 | DISQUALIFIED / Critical fail |
| violet-pulse | #7C3AED | AI agent activity |

---

---

## SLIDE 3 — Real Metrics, Method Comparison & Why It Works

### Headline
**Our Method vs Conventional Approaches — Scored, Compared, Justified**

---

### Panel 1 — Matching Method: Us vs Alternatives

> **Visualize as a feature comparison matrix**

| Capability | Keyword Match (Basic) | Pure LLM (GPT-4 only) | **Our Hybrid System** |
|---|---|---|---|
| "ETP Copper" = "Cu" | ❌ Miss | ✅ Correct | ✅ Correct |
| "1.1kV" = "1100V" | ❌ Miss | ✅ Correct | ✅ Correct |
| "2.6 sqmm" vs "2.5 sqmm" | ❌ Fail (not exact) | ⚠ Inconsistent | ✅ 0.95 score (±10%) |
| Voltage mismatch hard-block | ❌ No gate | ⚠ Soft warning only | ✅ Hard DISQUALIFIED |
| Response speed | ✅ Instant | ❌ 30–60s per product | ✅ ms (deterministic) + async LLM |
| Works without internet | ✅ Yes | ❌ No (API required) | ✅ Yes (LLM is optional layer) |
| Explainable output | ❌ No rationale | ⚠ Text only | ✅ Per-spec breakdown + score |
| Cost per query | ✅ Free | ❌ API cost per call | ✅ Free (LLM enrichment optional) |
| Mis-match rate (estimated) | ~35–40% false miss | ~5–10% hallucination risk | **<5% with domain maps** |

---

### Panel 2 — Accuracy Benchmarks Built Into the System

> **Visualize as grouped bar chart: Baseline / Good / Excellent**

| Metric | Baseline (Industry) | Good | Excellent | Our Target |
|---|---|---|---|---|
| RFP Response Time | 24 hours | 12 hours | 6 hours | **4–6 hours** ✅ |
| Spec Match Accuracy | 70% | 85% | 95% | **≥85% (GOOD tier)** |
| Win Rate | 25% | 35% | 50% | **35–50%** |
| Cost per RFP Processed | $500 | $300 | $150 | **$150–$300** ✅ |

**Match confidence score breakdown (how we measure our own accuracy):**

| Confidence Factor | Weight | What It Checks |
|---|---|---|
| Data completeness | 30% | How many spec fields actually have data |
| Score consistency | 25% | Low variance across specs = more trustworthy |
| Verification status | 20% | Verified datasheet vs estimated |
| Critical specs avg | 15% | Voltage, material, insulation scores specifically |
| Standard confidence | 10% | IS/IEC equivalence certainty |

> A match with 95% score but only 2 specs available gets a **low confidence** — the system flags it for human review. This is what prevents overconfident wrong recommendations.

---

### Panel 3 — Business Metrics Dashboard (Live in the Product)

> **Visualize as a live dashboard mockup with these KPI cards**

**Operational KPIs (tracked per RFP, per day, per month):**

| KPI | What It Measures | Why It Matters |
|---|---|---|
| Processing Time p95 | 95th percentile end-to-end RFP time | Catches slow outliers, not just averages |
| Top-1 Match Accuracy | Did the #1 recommendation get accepted? | Directly measures engine quality |
| Mean Reciprocal Rank (MRR) | Average rank of the correct product | Measures ranking quality, not just top-1 |
| Win Rate % | Won bids / submitted bids | Core business outcome |
| Cost per Win | Total platform cost / wins | ROI efficiency |
| Automation Savings ($) | Manual hours saved × hourly rate | Justifies the investment |

**Example ROI math (built into `roi_calculator.py`):**
- Manual cost per RFP: $500 (8 hours × $50/hr + overhead)
- System cost per RFP: ~$150 (compute + LLM API when used)
- Savings per RFP: **$350**
- At 3–5× more RFPs per month capacity: **3–5× revenue potential, no headcount increase**

**Predictive analytics outputs (Naive Bayes + Linear Regression, live):**
- **Win probability score** per bid before submission (0–100%)
  - Features: bid amount vs market, # competitors, technical score, commercial score
- **Processing time estimate** per new RFP based on requirement count
- **Risk score** (0–10): LOW < 3 · MEDIUM 3–6 · HIGH > 6

**Alert thresholds (auto-triggered, no manual monitoring needed):**

| Resource | Warning | Critical |
|---|---|---|
| CPU Usage | 70% | 90% |
| Memory | 75% | 90% |
| API Error Rate | Z-score anomaly | Z-score > 3σ |
| Response Time | > 1,000ms | > 3,000ms |

---

### Bottom Row — One-Line Summary Per Role Contribution

| Role | Concrete Output | Measurable Result |
|---|---|---|
| **AI System Architect** | 4-agent system, 10-step scoring, 21 message types | <5% false mismatch rate with domain equivalence maps |
| **NLP & Data Engineer** | 6 equivalence maps, 16 standard groups, 24 size snap values | Keyword miss rate ~35–40% → reduced to <5% |
| **Backend Engineer** | 70+ endpoints, 16-stage pipeline, <100ms SLA target | 5–10× throughput vs manual, zero data loss |
| **Frontend Engineer** | 70+ pages, SSE real-time, full bid workflow in-browser | Procurement team fully self-serve, no CLI needed |
| **UI/UX Engineer** | Color-coded compliance tables, glassmorphism design system | Reviewers detect spec gaps in seconds, not minutes |

---

*HAKI FMCG 2.0 — February 2026*
