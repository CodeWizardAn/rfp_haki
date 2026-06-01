# AI System Architect — HAKI FMCG 2.0

> Comprehensive deep-dive into the **Agentic AI System** — multi-agent architecture, communication protocols, data extraction pipelines, RFP matching engine, bid response generation, LangChain LLM integration, accuracy metrics, scoring algorithms, and end-to-end orchestration flows.

---

## 1. Agentic AI System — The Big Picture

HAKI FMCG 2.0 is built around a **Tier-based Multi-Agent System** where autonomous agents collaborate to process RFP documents, match products from a 22,000+ OEM catalog, calculate pricing, and generate complete bid responses — all orchestrated through a formal message-passing protocol.

### 1.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER / API REQUEST                              │
│              POST /api/v1/rfps/analyze  (PDF Upload)                │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                TIER 1 — MASTER ORCHESTRATOR                         │
│                                                                     │
│  ┌────────────────────┐  ┌────────────────────┐                    │
│  │  MasterAgent       │  │  MainOrchestrator  │                    │
│  │  (orchestrator.py) │  │  (main_orch.py)    │                    │
│  │  654 lines         │  │  2,103 lines       │                    │
│  └────────┬───────────┘  └─────────┬──────────┘                    │
│           │ Starts conversation     │ State machine                │
│           │ Prepares summaries      │ Quality validation           │
│           │ Consolidates response   │ Document generation          │
│           │ Exports JSON            │ Audit trail                  │
└───────────┼─────────────────────────┼──────────────────────────────┘
            │                         │
  ┌─────────┼─────────────────────────┼─────────────┐
  │         ▼                         ▼             │
  │  TIER 2 — WORKER AGENTS (3 Specialized)         │
  │                                                  │
  │  ┌──────────────┐  ┌─────────────┐  ┌────────┐ │
  │  │ Sales Agent  │  │  Technical  │  │Pricing │ │
  │  │ (Scanner)    │  │  Agent      │  │ Agent  │ │
  │  │              │  │  (Matcher)  │  │(Calc.) │ │
  │  │ rfp_scanner  │  │ spec_matcher│  │price_  │ │
  │  │ .py (552 ln) │  │ .py (816)  │  │calc.py │ │
  │  │              │  │ tech_agent  │  │(441 ln)│ │
  │  │              │  │ .py (2790) │  │        │ │
  │  └──────┬───────┘  └──────┬─────┘  └───┬────┘ │
  │         │                 │             │      │
  └─────────┼─────────────────┼─────────────┼──────┘
            │                 │             │
  ┌─────────┼─────────────────┼─────────────┼──────┐
  │         ▼                 ▼             ▼      │
  │  LANGCHAIN AGENTS (LLM-Powered Parallel)       │
  │                                                 │
  │  ┌──────────────┐  ┌─────────────┐  ┌────────┐│
  │  │ LCSalesAgent │  │LCTechnical  │  │LCPric- ││
  │  │ (metadata)   │  │Agent (reqs  │  │ingAgent││
  │  │              │  │ + analysis) │  │(costs) ││
  │  └──────────────┘  └─────────────┘  └────────┘│
  │              rfp_chain.py (646 lines)          │
  └────────────────────────────────────────────────┘
            │                 │             │
  ┌─────────┼─────────────────┼─────────────┼──────┐
  │         ▼                 ▼             ▼      │
  │  SHARED INFRASTRUCTURE                          │
  │                                                 │
  │  communication_protocol.py (679 lines)          │
  │  inter_agent_communication.py (2,232 lines)     │
  │  matching_engine.py (1,416 lines)               │
  │  workflow_orchestration.py (2,797 lines)         │
  │  data_models.py (394 lines)                     │
  │  agent_performance.py                            │
  └─────────────────────────────────────────────────┘
```

### 1.2 Dual Agent Implementations

The system runs **two parallel agent stacks** — a fast deterministic system and an LLM-powered enrichment system:

**Deterministic Agents** (Primary, always available)

- Location: agents/sales_agent/, technical_agent/, pricing_agent/
- Execution: Rule-based, lookup tables, weighted scoring algorithms
- Speed: Milliseconds per operation
- Accuracy: High for structured data (spec matching, pricing)
- Cost: Free (CPU only, no API calls)
- Always available as the primary response path

**LangChain LLM Agents** (Enrichment, optional)

- Location: agents/langchain_agent/rfp_chain.py
- Execution: Groq API calls to Llama 3.3 70B Versatile
- Speed: 30-45 seconds for full parallel analysis
- Accuracy: Superior for unstructured text understanding
- Cost: API usage charges per call
- Falls back to deterministic if API unavailable

**Key principle**: The deterministic response is the PRIMARY output. LLM enrichment runs in the background and enhances results asynchronously. The user gets a fast response immediately; richer analysis arrives later.

---

## 2. The Sales Agent — RFP Scanner & Selector

### 2.1 Role and Responsibilities

The Sales Agent is the **entry point** of the workflow. It identifies, scans, and selects RFPs for the system to respond to.

**File**: agents/sales_agent/rfp_scanner.py (552 lines)

**Class**: SalesAgent

**Capabilities**:
- Scan web URLs for RFP documents
- Scan local directories for RFP PDF files
- Extract RFP text using PyPDF2 (integrates with pdf_extraction module)
- Parse extracted text for key metadata (due dates, values, authority)
- Categorize and prioritize RFPs
- Select the best RFP for response

### 2.2 RFP Identification Flow

```
Input: URLs or PDF directory
          │
          ▼
┌─────────────────────────┐
│ scan_rfp_urls()         │  For each URL:
│   or                    │  1. Download/access document
│ scan_rfp_directory()    │  2. Extract text (PyPDF2)
│                         │  3. Parse key fields (regex)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ _extract_rfp_from_pdf() │  Creates IdentifiedRFP:
│ _parse_rfp_text()       │  - rfp_id (generated UUID hash)
│                         │  - title, due_date, authority
│                         │  - estimated_value
│                         │  - products[] with specs
│                         │  - tests_required[]
│                         │  - acceptance_criteria[]
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Deadline Filter          │  is_within_deadline(90 days)
│ (3-month window)         │  Reject if due_date > 90 days
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ prioritize_rfps()        │  HIGH: Due in 0-30 days
│                          │  MEDIUM: Due in 30-60 days
│                          │  LOW: Due in 60-90 days
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ select_rfp_for_response()│  Selects highest priority RFP
│                          │  Returns structured dict to
│                          │  Master Agent
└──────────────────────────┘
```

### 2.3 RFP Data Structure (IdentifiedRFP)

Every scanned RFP produces this structured output:

- rfp_id — Unique identifier (hash-based)
- title — Document title
- source_url / source_document — Where it came from
- due_date — Submission deadline
- issuing_authority — Who issued the RFP
- estimated_value — Contract value (INR)
- category — Product category (e.g., "Electrical Equipment")
- products[] — Array of product objects, each with name, specifications dict, quantity, unit
- technical_requirements[] — Array of standard compliance strings
- tests_required[] — Array of test name strings
- acceptance_criteria[] — Array of acceptance requirement strings
- submission_requirements — Format, copies, EMD amount, validity
- priority — HIGH / MEDIUM / LOW
- status — IDENTIFIED → SCANNED → SELECTED

### 2.4 LangChain Sales Agent (LCSalesAgent)

Runs in parallel with the deterministic agent for richer metadata extraction:

**LLM Prompt** — Expert procurement analyst role. Extracts: rfp_title, bid_number, issuing_authority, due_date, estimated_value, emd_amount, bid_validity_days, submission_format, project_description, key_categories, compliance_requirements, tests_required, acceptance_criteria.

**Smart Trim** — Before sending to LLM, text is trimmed to 4,000 chars using keyword scoring. Paragraphs containing cable/wire procurement keywords score higher and are kept.

**Fallback** — If LLM fails, regex-based extraction (bid number, due date, value) runs automatically.

---

## 3. The Technical Agent — Specification Matcher

### 3.1 Role and Responsibilities

The Technical Agent is the **brain** of the system. It takes RFP product requirements and finds the best matching OEM products from a 22,000+ product catalog.

**Files**:
- agents/technical_agent/spec_matcher.py (816 lines) — Core matching engine
- agents/technical_agent/technical_agent.py (2,790 lines) — Full-featured 51-capability agent
- agents/technical_agent/oem_product_repository.py (429 lines) — Product catalog with datasheets

### 3.2 What It Does

1. Receives product specifications from RFP (via Master Agent)
2. Loads 22,000+ OEM products from database (JSON catalog)
3. Loads OEM datasheets for enhanced matching (nested properties)
4. For each RFP product, scores ALL OEM products against it
5. Returns Top 3 matches per product with spec match percentage
6. Builds comparison table (RFP spec vs OEM 1, OEM 2, OEM 3)
7. Selects best match per product
8. Sends results to BOTH Master Agent AND Pricing Agent

### 3.3 Specification Matching Algorithm

**The Spec Match Formula:**

$$MatchScore = \frac{\sum_{i=1}^{n} (ParameterMatch_i \times Weight_i)}{\sum_{i=1}^{n} Weight_i} \times 100$$

Where:
- $ParameterMatch_i$ = 1.0 (full match), 0.0-0.99 (partial), or 0.0 (no match)
- $Weight_i$ = Equal weightage for all specifications (default mode)
- $n$ = Total number of specifications in the RFP requirement

**Matching Flow Per Product:**

```
RFP Product Specifications
          │
          ▼
┌─────────────────────────────────┐
│  For each OEM product (22k+):  │
│                                 │
│  1. _calculate_spec_match()     │
│     ├─ Direct OEM spec lookup   │
│     ├─ Datasheet nested lookup  │
│     └─ Enhanced value compare   │
│                                 │
│  2. _compare_spec_values_       │
│     enhanced()                  │
│     ├─ Semantic matching        │
│     ├─ Numeric extraction       │
│     ├─ Value normalization      │
│     ├─ String containment       │
│     └─ Boolean comparison       │
│                                 │
│  3. Score = matched / total     │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│  Sort by spec_match_percent     │
│  Select Top 3                   │
│  Best = top_3[0]                │
│  Build comparison table         │
└─────────────────────────────────┘
```

### 3.4 Enhanced Value Comparison

The spec matching engine handles these comparison types:

**Semantic Matching** — Maps equivalent terms to canonical categories:

- Conductor Material: "Copper", "Electrolytic Grade Copper", "ETP Copper", "CU", "99.97% Pure Electrolytic Copper" → all map to canonical category "copper"
- Insulation Type: "XLPE", "Cross-linked Polyethylene", "Crosslinked PE" → all map to "xlpe"
- Conductor Type: "Class 1", "Solid", "Single Wire" → all map to "solid"
- Armour Type: "SWA", "Galvanized Steel Wire", "Steel Wire Armoured" → all map to "steel wire armoured"
- Voltage Rating: "1100V", "1100V AC", "1.1kV", "650/1100V" → all map to "1100v"

Semantic matching uses a **3-priority system**:
1. Exact match with any equivalent in the category
2. Value contained in an equivalent (longer match preferred)
3. Equivalent contained in value (longer equivalent preferred)

If both RFP and OEM values map to the **same canonical category** → Score = 1.0 (full match).
If they map to **different categories** → Score = 0.0 (no match).

**Numeric Comparison** — Extracts numbers from strings and compares:
- Exact numeric match → Score = 1.0
- Within 10% tolerance → Score = 0.95
- Within 20% tolerance → Score = 0.80
- Beyond 20% → Score = 0.0

**Value Normalization** — Before comparison, values are cleaned:
- Remove unit suffixes: "AC", "DC", "°C", "A", "V", "sq mm", "approx"
- Type conversion: string → int/float where possible
- Case normalization: all lowercase for string comparison

**String Comparison** — For non-semantic, non-numeric values:
- Exact string match → 1.0
- Containment (rfp in oem or oem in rfp) → 0.9
- Partial word overlap → (common words / max words)

**Boolean Comparison** — Direct equality check → 1.0 or 0.0

### 3.5 Datasheet-Level Matching

Beyond direct OEM product specs, the agent queries **nested datasheet properties**:

Key Mapping (datasheet path → normalized key):
- electrical_properties.rated_voltage → rated_voltage
- electrical_properties.max_conductor_temp → temperature_rating_celsius
- electrical_properties.current_carrying_capacity → current_rating_amps
- physical_properties.conductor_material → conductor_material
- physical_properties.conductor_class → conductor_type
- physical_properties.nominal_area → cross_section_sqmm
- physical_properties.number_of_cores → number_of_cores
- physical_properties.insulation_type → insulation_type
- physical_properties.armour_type → armour_type

If a spec is not found in the product's flat specifications dict, the system traverses the datasheet's nested structure using dot-notation key paths.

### 3.6 Comparison Table Output

For each RFP product, a comparison table is generated:

```
Specification  | RFP Requirement | OEM 1 (SKU)    | OEM 2 (SKU)    | OEM 3 (SKU)
Product SKU    | -               | POL-PVC-1.5-R  | HAV-LIFE-1.5   | KEI-FR-1.5
               |                 | 92.5%          | 88.3%          | 85.1%
conductor_mat  | Copper          | ETP Copper     | Annealed Cu    | Copper
               |                 | Full Match     | Full Match     | Full Match
cross_section  | 1.5             | 1.5            | 1.5            | 1.5
               |                 | Full Match     | Full Match     | Full Match
voltage_rating | 1100V           | 1100V AC       | 1.1kV          | 1100V
               |                 | Full Match     | Full Match     | Full Match
insulation     | PVC             | FR PVC Type A  | HRFR PVC       | FR PVC
               |                 | Full Match     | Full Match     | Full Match
```

### 3.7 Compliance Summary Output

After matching all products, the Technical Agent produces:

- total_products — Number of RFP products analyzed
- average_spec_match — Average match % across all products
- fully_compliant — Count with spec match >= 90%
- partially_compliant — Count with 70% <= spec match < 90%
- needs_review — Count with spec match < 70%

### 3.8 LangChain Technical Agent (LCTechnicalAgent)

Two LLM chains for deeper analysis:

**Extraction Chain** — Extracts ALL cable/wire requirements from raw text:
- conductor_size (sq mm), cores, voltage (volts), conductor_material
- insulation, current_rating, standard, armoured (bool), fire_resistant
- quantity, unit, requirement_type
- Normalizes: "2.5mm²" → 2.5, "1.1kV" → 1100, "SWA" → armoured=true

**Analysis Chain** — Evaluates product matches with expert rationale:
- For each matched product: suitability rating, strengths, deviations
- Overall recommendation with reasoning
- Alternative suggestion if no product is ideal

---

## 4. The Enhanced Matching Engine

### 4.1 Overview

**File**: agents/shared/matching_engine.py (1,416 lines)

The Enhanced Matching Engine is a comprehensive specification matching system with weighted scoring, confidence calculation, critical failure detection, gap analysis, and human-readable explanations.

### 4.2 Specification Categories and Weights

Specs are classified into 4 categories with different weights:

**CRITICAL (Weight: 2.0x)** — Must match for product to be viable
- voltage_rating, rated_voltage, voltage_grade
- conductor_material
- insulation_type
- temperature_rating
- current_rating
- fire_rating

**IMPORTANT (Weight: 1.5x)** — Should match for good recommendation
- conductor_size, cross_section_sqmm
- number_of_cores
- armour_type
- outer_sheath
- standard

**STANDARD (Weight: 1.0x)** — Nice to match
- conductor_type, conductor_class
- color
- certifications

**INFORMATIONAL (Weight: 0.5x)** — Reference only
- manufacturer
- brand
- moq
- lead_time

### 4.3 Overall Score Aggregation

The overall score combines multiple dimensions:

$$Overall = (WeightedScore \times 0.5) + (StandardScore \times 0.25) + (CertificationScore \times 0.15) + (CriticalOnlyScore \times 0.10)$$

Where:
- WeightedScore = Sum of (raw_score * weight) / Sum of weights
- StandardScore = Fraction of standards with equivalents found
- CertificationScore = Fraction of required certifications present
- CriticalOnlyScore = Average score of CRITICAL category specs only

### 4.4 Confidence Score Calculation

Confidence measures how trustworthy the match score is:

$$Confidence = (Completeness \times 0.30) + (Consistency \times 0.25) + (Verification \times 0.20) + (CriticalFactor \times 0.15) + (StandardConfidence \times 0.10)$$

Where:
- Completeness = Ratio of specs with data available (0.0-1.0)
- Consistency = 1.0 - min(standard_deviation_of_scores, 0.5)
- Verification = 1.0 (verified), 0.7 (partially), 0.5 (unverified)
- CriticalFactor = Average score of CRITICAL specs
- StandardConfidence = Confidence from standard equivalence mapping

### 4.5 Critical Failure Detection

Certain mismatches immediately disqualify a product:

- Voltage mismatch > 10% — Product unsafe for the application
- Size out of range > 20% — Product physically incompatible
- Temperature rating margin < 10C — Insufficient thermal safety
- Current capacity margin < 10% — Insufficient electrical capacity
- Standard non-compliance — Product fails mandatory standard
- Material incompatible — Fundamentally wrong material
- Certification missing — Required certification absent
- Safety requirement — Safety-critical spec not met

In **strict mode**, any single critical failure sets the product to DISQUALIFIED regardless of other scores.

### 4.6 Match Quality Tiers

| Score | Quality Tier |
|---|---|
| >= 95% | EXCELLENT |
| >= 85% | GOOD |
| >= 70% | FAIR |
| >= 50% | POOR |
| < 50% or critical fail | DISQUALIFIED |

### 4.7 Recommendation Levels

Based on quality tier and critical failures:

- HIGHLY_RECOMMENDED — EXCELLENT quality, no critical failures
- RECOMMENDED — GOOD quality, no critical failures
- CONDITIONAL — FAIR quality, gaps can be addressed
- NOT_RECOMMENDED — POOR/DISQUALIFIED, should not be selected

### 4.8 Standard Equivalence Checking

The engine checks if different standard codes are actually equivalent:

**Direct equivalence** — IS 694 = IEC 60227 (same standard, different body)
**Indirect equivalence** — IS 7098 → IEC 60502 → EN 60502 (through common equivalent)
**Same family** — IS 7098 Part 1 ≈ IS 7098 Part 2 (same standard family)

Uses StandardMapper utility with pre-loaded equivalence groups for Indian (IS/BIS), International (IEC), European (EN), and American (ASTM) standards.

### 4.9 Gap Analysis

For each unmet specification:
- gap_type: missing (spec not in product), insufficient (below requirement), over_specified (exceeds but wrong direction)
- gap_magnitude: Numeric difference where applicable
- impact: high / medium / low
- remediation_options: Suggestions to close the gap

### 4.10 Match Explanation Generation

Every match produces a human-readable MatchExplanation:

- summary — One-line quality assessment
- strengths[] — Specs that matched well
- weaknesses[] — Specs with partial or poor matches
- critical_issues[] — Critical failures
- spec_details[] — Per-spec breakdown (rfp value, product value, match %, type)
- overall_assessment — Recommendation text

---

## 5. The Pricing Agent — Cost Calculator

### 5.1 Role and Responsibilities

The Pricing Agent receives product recommendations from the Technical Agent and calculates the complete financial package.

**File**: agents/pricing_agent/price_calculator.py (441 lines)

**Class**: PricingAgent

### 5.2 Data Sources

**Product Price Table** — Loaded from database/db_pricing/product_prices.json
- SKU → unit_price (INR), MOQ, bulk_discount_percent

**Services Price Table** — Loaded from database/db_pricing/service_prices.json
- service_id → price, standard, turnaround_days

### 5.3 Pricing Flow

```
Input from Technical Agent:
  product_recommendations[] (selected SKUs + quantities)

Input from Master Agent:
  tests_required[] (test names from RFP)
          │
          ▼
┌─────────────────────────────────┐
│ _calculate_product_prices()     │
│                                 │
│ For each recommended product:   │
│   1. Look up SKU in price table │
│   2. Get unit_price             │
│   3. Apply bulk discount if     │
│      quantity >= MOQ * 10       │
│   4. discounted_price =         │
│      unit * (1 - discount/100)  │
│   5. total = discounted * qty   │
│                                 │
│ If SKU not found:               │
│   → Estimated price of 50.00   │
│   → Flagged as "estimated"     │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ _calculate_test_costs()         │
│                                 │
│ For each test_required:         │
│   1. Fuzzy match test name →    │
│      test_id using keyword map  │
│   2. Look up in services table  │
│   3. Get unit_cost              │
│                                 │
│ Test Mapping (partial list):    │
│   "conductor resistance"        │
│     → TEST_CONDUCTOR_RES        │
│   "insulation resistance"       │
│     → TEST_INSULATION_RES       │
│   "high voltage"                │
│     → TEST_HV                   │
│   "flame retardancy"            │
│     → TEST_FLAME_IEC60332       │
│   "smoke density"               │
│     → TEST_SMOKE_IEC61034       │
│   "tensile" → TEST_TENSILE      │
│   "thermal" → TEST_THERMAL      │
│   "third party"/"inspection"    │
│     → SVC_TPI                   │
│   "type test certificate"       │
│     → SVC_TYPE_CERT             │
│                                 │
│ If test not mapped:             │
│   → Estimated cost of 10,000   │
│   → Flagged as "estimated"     │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ _calculate_taxes()              │
│                                 │
│ Material GST = 18% of material  │
│ Services GST = 18% of services  │
│ Total Tax = material + services │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ Grand Total =                   │
│   Material Cost                 │
│ + Services Cost                 │
│ + Total Tax                     │
│                                 │
│ Pricing Summary:                │
│   material_percent of total     │
│   services_percent of total     │
│   tax_percent of total          │
└─────────────────────────────────┘
```

### 5.4 Pricing Notes (Auto-Generated)

Every quotation includes:
- Count of products with estimated prices (not in price table)
- Count of tests with estimated costs
- Validity: 30 days from quote date
- Bulk discounts applied where applicable
- GST at 18% included in grand total
- Test costs for one set of samples per product
- Transportation costs not included
- Payment terms: 30% advance, 70% on delivery

### 5.5 LangChain Pricing Agent (LCPricingAgent)

Uses LLM for market-aware cost estimation:
- Indian market cable price ranges per meter
- Quantity discount estimation
- Test cost ranges (e.g., Flame retardancy IEC 60332: 10,000-25,000 INR)
- Type test certificate: 30,000-75,000 INR
- Third party inspection: 15,000-40,000 INR
- GST calculation at 18%
- Generates pricing rationale for each estimate

Falls back to deterministic if LLM unavailable: default 50.00/meter, 10,000/test.

---

## 6. The Master Orchestrator — Central Coordinator

### 6.1 Two Orchestrator Implementations

**MasterAgent** (orchestrator.py, 654 lines) — Core workflow coordinator
- Conversation state machine (9 states)
- Context-specific summary preparation
- Response consolidation
- JSON export

**MainOrchestrator** (main_orchestrator.py, 2,103 lines) — Full-featured orchestrator
- Agent registry with status tracking
- Message queue system with priority
- Quality validation (3 validators)
- Document generation (PDF reports, executive summaries)
- Audit trail generation
- Performance metrics tracking

### 6.2 Conversation State Machine

```
IDLE
  │
  ▼ start_conversation()
SCANNING_RFPS
  │
  ▼ receive_sales_response()
RFP_SELECTED
  │
  ▼ prepare_technical_summary() + prepare_pricing_summary()
PREPARING_SUMMARIES
  │
  ▼ technical_agent.process_rfp()
TECHNICAL_ANALYSIS
  │
  ▼ receive_technical_response()
PRICING_ANALYSIS
  │
  ▼ receive_pricing_response()
CONSOLIDATING
  │
  ▼ consolidate_response()
COMPLETED ─── or ─── ERROR
```

### 6.3 Context-Specific Summaries

The Master Agent prepares **different summaries** for each worker agent — each agent only gets the information relevant to its role:

**Technical Summary** (Master → Technical):
- products_in_scope (product names + specifications)
- technical_requirements (standards, compliance)
- acceptance_criteria
- Expected output: Top 3 OEM products per item, spec match %, comparison table
- Spec match formula reference

**Pricing Summary** (Master → Pricing):
- tests_required (test names from RFP)
- acceptance_criteria
- estimated_value (contract value)
- Expected output: unit prices, test costs, material total, services total, grand total
- Note: "Will receive product recommendations from Technical Agent"

### 6.4 Response Consolidation

The consolidate_response() method merges outputs from all agents:

```
Technical Response           Pricing Response
(recommendations[],         (product_prices[],
 comparison_table[],         test_costs[],
 compliance_summary)         taxes, grand_total)
        │                          │
        └──────────┬───────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│ Scope of Supply Table (Per Product):         │
│   sl_no                                      │
│   rfp_product_name                           │
│   rfp_specifications                         │
│   quantity, unit                             │
│   recommended_oem_sku (from Technical)       │
│   oem_product_name (from Technical)          │
│   manufacturer (from Technical)              │
│   spec_match_percent (from Technical)        │
│   unit_price (from Pricing)                  │
│   discount_percent (from Pricing)            │
│   total_price (from Pricing)                 │
│   top_3_options (from Technical)             │
└──────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│ Overall Assessment:                          │
│   overall_spec_match (average across all)    │
│                                              │
│   >= 90%  → HIGHLY RECOMMENDED               │
│   >= 75%  → RECOMMENDED                      │
│   >= 60%  → CONDITIONALLY RECOMMENDED        │
│   < 60%   → REVIEW REQUIRED                 │
│                                              │
│   compliance_checklist (7 items)             │
│   grand_total (material + services + tax)    │
│   response_status = READY_FOR_REVIEW         │
└──────────────────────────────────────────────┘
```

### 6.5 MainOrchestrator Extended Workflow

The MainOrchestrator adds 3 additional steps after consolidation:

**Step 6 — Validation**:
- QualityValidator — Score quality checks
- CompletenessChecker — All required fields present
- ConsistencyValidator — Cross-reference consistency

**Step 7 — Document Generation**:
- ExecutiveSummaryWriter — One-page executive summary
- DetailedResponseCompiler — Full technical response
- PDFReportGenerator — Formatted PDF output
- AuditTrailGenerator — Complete action log

Quality Levels:
- EXCELLENT — All validations pass, high scores
- GOOD — Minor issues
- ACCEPTABLE — Some gaps
- NEEDS_REVIEW — Significant issues
- FAILED — Critical failures

---

## 7. Inter-Agent Communication Protocol

### 7.1 Message Architecture

The system implements a full message-passing protocol with two layers:

**Layer 1** — communication_protocol.py (679 lines): High-level message definitions and factory functions for the 4 communication flows.

**Layer 2** — inter_agent_communication.py (2,232 lines): Infrastructure layer with queue backends, serialization, routing, state management, circuit breaker, dead letter queue, and monitoring.

### 7.2 Agent Types (4 + Broadcast)

| Agent | Role |
|---|---|
| MASTER_ORCHESTRATOR | Central coordinator |
| SALES_AGENT | RFP scanner/selector |
| TECHNICAL_AGENT | Spec matcher/recommender |
| PRICING_AGENT | Cost calculator |
| ALL_AGENTS | Broadcast target |

### 7.3 Message Priority Levels (5)

| Priority | Level | Use Case |
|---|---|---|
| 1 | CRITICAL | Errors, system emergencies |
| 2 | HIGH | RFP selections, urgent updates |
| 3 | MEDIUM | Technical/pricing context |
| 4 | STANDARD | Normal operations |
| 5 | LOW | Status updates, heartbeats |

### 7.4 Message Types (21)

**RFP Workflow**:
- RFP_SCAN_REQUEST, RFP_SCAN_RESPONSE
- RFP_IDENTIFIED, RFP_SELECTED, RFP_LIST

**Technical Analysis**:
- RFP_TECHNICAL_SUMMARY (Master → Technical)
- TECHNICAL_ANALYSIS_REQUEST, TECHNICAL_ANALYSIS_RESPONSE
- PRODUCT_RECOMMENDATIONS (Technical → Master + Pricing)
- SPEC_COMPARISON, COMPLIANCE_REPORT

**Pricing**:
- RFP_PRICING_SUMMARY (Master → Pricing)
- PRICING_REQUEST, PRICING_RESPONSE
- PRICING_CALCULATION (Pricing → Master)
- QUOTE_GENERATED

**Consolidation**:
- CONSOLIDATION_REQUEST, CONSOLIDATED_RESPONSE

**System**:
- HEARTBEAT, STATUS_UPDATE, ERROR, ACKNOWLEDGMENT

**Control**:
- WORKFLOW_START, WORKFLOW_END, CANCEL, PAUSE, RESUME

### 7.5 Message Envelope Structure

Every message contains:

**Header**:
- message_id — Unique identifier (MSG_<16-char-hex>)
- correlation_id — Links related messages
- conversation_id — Groups messages in a workflow
- timestamp — When created
- expiry — Optional TTL
- priority — 1-5 priority level
- message_type — One of 21 types
- delivery_mode — point_to_point / broadcast / pubsub / multicast
- reply_to — Expected response destination
- trace_id — Distributed tracing (TRACE_<12-char-hex>)
- span_id — Operation span (SPAN_<8-char-hex>)

**Body**:
- from_agent — Sender agent type
- to_agent — Single or list of recipients
- payload — Actual data (dict)
- status — CREATED → QUEUED → SENT → DELIVERED → PROCESSING → ACKNOWLEDGED
- retry_count / max_retries — Retry tracking
- acknowledgment_required — Whether ACK is expected
- timeout_seconds — Per-message timeout
- metadata — Additional context

**Integrity**: SHA-256 hash of (message_id + payload + from_agent + to_agent) for tamper detection.

### 7.6 The 4 Communication Flows

**Flow 1 — RFP Identification → Analysis**:
```
Sales Agent ──[RFP_IDENTIFIED]──→ Master Agent
Master Agent ──(selects)──
Sales Agent ──[RFP_SELECTED]──→ Master Agent
```

**Flow 2 — Technical Analysis**:
```
Master Agent ──[RFP_TECHNICAL_SUMMARY]──→ Technical Agent
  Payload: products_in_scope, technical_requirements,
           acceptance_criteria, spec_match_formula

Technical Agent ──[PRODUCT_RECOMMENDATIONS]──→ Master + Pricing
  Payload: recommendations[], comparison_table[],
           compliance_summary, scope_of_supply_table
```

**Flow 3 — Pricing Estimation**:
```
Master Agent ──[RFP_PRICING_SUMMARY]──→ Pricing Agent
  Payload: tests_required, acceptance_criteria,
           estimated_value, expected_output format

Pricing Agent ──[PRICING_CALCULATION]──→ Master Agent
  Payload: product_prices[], test_costs[],
           total_material_cost, total_services_cost,
           taxes, grand_total
```

**Flow 4 — Final Consolidation**:
```
Master Agent ──[CONSOLIDATED_RESPONSE]──→ (self/output)
  Payload: scope_of_supply[], test_requirements[],
           totals, overall_spec_match, recommendation
```

### 7.7 Message Queue Infrastructure

**InMemoryQueueBackend** (Default):
- Per-agent priority queues using Python heapq
- Thread-safe with RLock
- Push/pop/peek/size/clear operations
- Priority ordering (lower number = higher priority)

**RedisQueueBackend** (Production):
- Redis sorted sets for priority queuing
- Persistent across restarts
- Higher throughput for distributed deployment

### 7.8 Message Lifecycle States

```
CREATED → QUEUED → SENT → DELIVERED → PROCESSING → ACKNOWLEDGED
                                 │
                                 ├──→ FAILED → RETRYING → (loop)
                                 │                    │
                                 │                    └──→ DEAD_LETTERED
                                 └──→ EXPIRED
```

### 7.9 Reliability Patterns

**Message Acknowledgment** — Sender tracks pending_responses. Receiver sends ACK. If no ACK within timeout, message is retried.

**Retry with Exponential Backoff** — Failed messages retried up to max_retries (default: 3) with increasing delays.

**Dead Letter Queue** — Messages that exceed max retries are moved to a dead letter queue for manual inspection.

**Circuit Breaker** — After sustained delivery failures to an agent, the circuit opens and messages are immediately failed without attempting delivery. After cooldown period, circuit moves to half-open and tries a single message.

**Message Tracing** — Every message gets a trace_id and span_id. Full message flow can be reconstructed by querying trace_id.

**Broadcast Support** — Messages to ALL_AGENTS are delivered to every agent except the sender.

**Priority Queuing** — CRITICAL messages (priority 1) are always processed before STANDARD (priority 4) messages.

---

## 8. Data Extraction Pipeline

### 8.1 PDF Extraction Stack

**File**: pdf_extraction/pdf_extraction_manager.py (275 lines)

The extraction pipeline uses multiple tools for maximum coverage:

```
PDF File
  │
  ├──→ PyPDF2 (pdf_extraction_manager.py)
  │      Fast basic text extraction
  │      Page-by-page with stats
  │
  ├──→ pdfplumber (pdf_text_extractor.py)
  │      Table extraction
  │      Layout-aware text
  │
  ├──→ PyMuPDF/fitz (hyperlink_extractor.py)
  │      Hyperlink extraction
  │      URL collection from pages
  │
  └──→ Multilingual (multilingual_extractor.py)
         Handles non-English RFPs
```

### 8.2 Extraction Process

```
1. Upload → Generate unique ID
   (timestamp_hash_uuid)

2. Create folder structure:
   uploads/{unique_id}/
   ├── pdf/          (original)
   ├── metadata/     (JSON metadata)
   └── extracted/    (output text/tables)

3. Extract text page by page:
   For each page:
     - Extract text (PyPDF2)
     - Count chars, words, lines
     - Track extraction success/failure
   
   Output: full_text + page_info dict

4. Track extraction stats:
   - total_pages
   - total_chars
   - total_words
   - pages_extracted (success count)
   - pages_failed (error count)

5. Save metadata JSON:
   - file_info (name, size, hash, pages)
   - extraction_stats
   - page_details
   - processing timestamps
```

### 8.3 Hyperlink Extraction

For RFPs that reference external documents (BOQ spreadsheets, drawing PDFs):

1. PyMuPDF extracts all hyperlinks from each PDF page
2. Linked documents are downloaded (PDF, Excel, CSV)
3. Excel/CSV files are parsed for BOQ (Bill of Quantities) items
4. BOQ items are extracted: product name, quantity, unit, specifications
5. Linked PDFs are recursively extracted for additional requirements

### 8.4 RFP Terms Matching

**Database**: pdf_extraction/rfp_terms_database_100k_new.json (100,000+ procurement terms)

After extraction, the raw text is matched against the terms database to identify:
- Product types and categories
- Technical specifications
- Standard references
- Test requirements
- Compliance needs

### 8.5 Smart Text Trimming for LLM

Before sending to LangChain agents, text is intelligently trimmed:

```python
Keywords scored (higher = more relevant):
  cable, wire, conductor, sqmm, voltage,
  insulation, xlpe, pvc, frls, armour, core,
  copper, aluminium, is 694, iec, boq,
  scope of supply, bid, tender, emd,
  due date, price, test, quantity

Algorithm:
  1. Split text into paragraphs
  2. Score each paragraph by keyword count
  3. Sort paragraphs by score (descending)
  4. Take top paragraphs until max_chars reached
  5. Result: Most relevant content within LLM context window
```

---

## 9. The Spec Comparer Engine

### 9.1 OEM Product Repository

**File**: agents/technical_agent/oem_product_repository.py (429 lines)

**ProductDatasheet** structure for each OEM product:
- sku, product_name, manufacturer, brand
- category, sub_category
- specifications (flat dict)
- physical_properties (nested)
- electrical_properties (nested)
- standards_compliance (list)
- certifications (list), bis_license_number
- type_test_report (dict)
- packaging_info (dict)
- price_per_unit, currency, moq, lead_time_days

**Sample OEM Vendors in catalog**: Polycab, Havells, KEI, Finolex, RR Kabel

**Sample Product**: Polycab Optima Plus FR PVC Insulated Industrial Cable
- SKU: POL-PVC-1.5-R
- conductor_material: Electrolytic Grade Copper
- conductor_type: Solid/Stranded
- insulation_material: FR PVC Type A
- cross_section: 1.5 sq mm
- voltage: 1100V
- current_rating: 15A
- standard: IS 694:2010
- certifications: BIS (ISI Mark), ISO 9001:2015, ISO 14001:2015
- electrical: conductor_resistance 12.1 ohm/km, insulation_resistance 100 Mohm.km, voltage test 3.5kV
- physical: weight 25 kg/km, insulation_thickness 0.7mm
- price: INR 17.50/meter

### 9.2 The Full Technical Agent (51 Features)

**File**: agents/technical_agent/technical_agent.py (2,790 lines)

This is the comprehensive implementation with 51 capabilities:

1. TechnicalAgent class structure
2. RFP requirement parser
3. LLM integration for understanding specs
4. Product requirement extractor
5. Scope of supply analyzer
6. Multi-item RFP handler
7. Product catalog querier
8. Specification matching orchestrator
9. Vector search integration (ChromaDB)
10. Weighted matching
11. Top-K selector (K=3)
12. Match score calculator
13. Confidence scoring
14. Comparison table generator
15. Gap analysis generator
16. Specification explanation generator
17. Technical risk assessor
18. Compliance checker
19. Standard verification
20. Technical summary generator
21. Product recommendation ranker
22. Alternative suggestion logic
23. Custom product flagging
24. Technical report formatter
25. Visualization data generator
26. Detailed spec comparison
27. Match justification writer
28. Edge case handlers
29. Technical validation
30. Output to Pricing Agent
31. Output to Master Agent
32. Technical agent memory
33. Context management
34. Conversation history
35. Technical agent logging
36. Performance tracking
37. Error recovery mechanisms
38. Batch processing mode
39. Async operation support
40. API interface
41. Webhook support

**Key Enums**:
- MatchConfidence: VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW
- RiskLevel: CRITICAL, HIGH, MEDIUM, LOW, NONE
- ComplianceStatus: COMPLIANT, PARTIAL, NON_COMPLIANT, UNKNOWN
- ProcessingMode: SYNC, ASYNC, BATCH

---

## 10. The RFP Responser — Bid Generation

### 10.1 Bid Response Output Format

The consolidated response produces a **Scope of Supply Table**:

```
Sl | RFP Product        | OEM SKU        | Spec% | Qty    | Unit Price | Total
 1 | PVC Wire 1.5 sqmm  | POL-PVC-1.5-R  | 92.5  | 50,000 | 17.50      | 875,000
 2 | PVC Wire 2.5 sqmm  | HAV-LIFE-2.5   | 88.3  | 30,000 | 28.50      | 855,000
 3 | XLPE Cable 4Cx16    | POL-XLPE-4C16  | 95.1  | 10,000 | 485.00     | 4,850,000
 4 | Flex Cable 3Cx2.5   | KEI-FLEX-3C25  | 85.7  | 5,000  | 65.00      | 325,000

                                                MATERIAL COST: 6,905,000
                                                SERVICES COST:   185,000
                                                TAX (18% GST):   1,276,200
                                                GRAND TOTAL:     8,366,200
```

### 10.2 Compliance Checklist

The response includes a 7-point compliance checklist:

- All products in scope addressed (has technical response)
- OEM recommendations provided (recommendations array not empty)
- Spec match metrics calculated (technical response present)
- Comparison tables generated (comparison_table array not empty)
- Unit prices assigned (pricing response present)
- Test costs included (test_costs array not empty)
- Total pricing calculated (grand_total > 0)

### 10.3 Bid Document Generation

The API (api/bid_document_generator.py, api/bid_pdf_generator.py) produces:
- Complete bid PDF with cover page, scope of supply, pricing, compliance
- Executive summary (one-page overview)
- Detailed technical response
- Company profile integration
- Digital signature support

---

## 11. LangChain Multi-Agent Orchestration

### 11.1 LCMasterAgent — Parallel Execution

The LangChain Master Agent orchestrates LLM analysis in a specific parallel pattern:

```
Phase 1 (Parallel, ~8-12 seconds):
  ├─ LCSalesAgent.extract_metadata(rfp_text)
  └─ LCTechnicalAgent.extract_requirements(rfp_text)
  
  ThreadPoolExecutor(max_workers=4):
    future_sales = submit(sales.extract_metadata, text)
    future_tech = submit(tech.extract_requirements, text)
    results = [f.result(timeout=20) for f in futures]

Phase 2 (Sequential, milliseconds):
  Deterministic product matching against CSV/JSON database
  (No LLM needed — rule-based weighted scoring)

Phase 3 (Sequential, ~5-8 seconds):
  LCPricingAgent.estimate_costs(matched_products, tests)

Phase 4 (Parallel, ~8-12 seconds):
  For each comparison/match:
    LCTechnicalAgent.analyze_matches(requirement, products)
  
  All comparisons analyzed in parallel via ThreadPoolExecutor

Total ETA: 30-45 seconds
```

### 11.2 LLM Configuration

- Provider: Groq (cloud API)
- Model: llama-3.3-70b-versatile
- Temperature: 0.05 (near-deterministic for consistency)
- Max tokens: 4,096 per response
- Request timeout: 25 seconds
- Singleton pattern: Single LLM instance shared across all agents

### 11.3 LangChain Chain Structure

Each agent uses a simple chain:

```python
ChatPromptTemplate → ChatGroq LLM → StrOutputParser
```

- ChatPromptTemplate: System + Human message pair
- ChatGroq: Groq API call to Llama 3.3 70B
- StrOutputParser: Raw string output
- Post-processing: _safe_json_parse() strips markdown fences, extracts JSON

### 11.4 Graceful Degradation

Every LangChain component checks availability:

```python
LANGCHAIN_AVAILABLE = False
try:
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    ...

GROQ_AVAILABLE = False
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    ...
```

If not available, all agents fall back to deterministic methods:
- LCSalesAgent → regex extraction
- LCTechnicalAgent → no LLM analysis (just deterministic matching)
- LCPricingAgent → default pricing (50/meter, 10000/test)

### 11.5 Legacy Compatibility

LangChainRFPAgent wraps LCMasterAgent for backward compatibility with the API:

```python
class LangChainRFPAgent:
    def extract_requirements(rfp_text) → tech agent
    def analyze_matches(req, products) → tech agent
    def get_sales_metadata(rfp_text) → sales agent
    def estimate_pricing(products, tests) → pricing agent
    def run_full_analysis(rfp_text) → parallel extraction
    def analyze_matches_batch(comparisons) → parallel analysis
```

---

## 12. Workflow Orchestration Engine

### 12.1 Overview

**File**: agents/shared/workflow_orchestration.py (2,797 lines)

A complete workflow engine with state tracking, checkpoints, rollback, parallel execution, human-in-the-loop gates, and observability.

### 12.2 Workflow States (10)

| State | Description |
|---|---|
| DRAFT | Workflow defined but not started |
| PENDING | Queued for execution |
| RUNNING | Currently executing |
| PAUSED | Temporarily halted |
| WAITING_APPROVAL | Human approval required |
| WAITING_INPUT | Human input required |
| COMPLETED | Successfully finished |
| FAILED | Failed with errors |
| CANCELLED | Manually cancelled |
| ROLLED_BACK | Reverted to prior state |

### 12.3 Step Types (8)

| Type | Description |
|---|---|
| TASK | Regular executable step |
| DECISION | Conditional branching point |
| PARALLEL | Multiple steps in parallel |
| APPROVAL | Human approval gate |
| HUMAN_INPUT | Wait for user input |
| NOTIFICATION | Send alert/notification |
| CHECKPOINT | Save workflow state |
| SUBWORKFLOW | Nested workflow |

### 12.4 Step Definition

Each workflow step includes:
- step_id, name, step_type
- handler (callable function)
- dependencies (list of step_ids that must complete first)
- timeout_seconds (default: 300)
- retry_count (default: 3), retry_delay_seconds (default: 5)
- is_checkpoint (save state after this step)
- approval_required, approvers
- on_success, on_failure (branching)

### 12.5 Checkpoint System

At any checkpoint-flagged step, the workflow state is serialized:
- checkpoint_id, workflow_id, step_id
- state_snapshot (all workflow variables)
- context_snapshot (current context)
- step_results (all completed step results)

On failure, the workflow can be **resumed from the last checkpoint** instead of restarting from scratch.

### 12.6 Rollback Mechanism

When a step fails:
1. Current step marked as FAILED
2. If rollback is enabled, completed steps are reversed in order
3. Each step's rollback handler is called (if defined)
4. Workflow status → ROLLED_BACK

### 12.7 Parallel Processing

Steps with no mutual dependencies can run in parallel:

```python
ThreadPoolExecutor(max_workers=N):
    for step in parallel_steps:
        future = executor.submit(step.handler, context)
    
    for future in as_completed(futures):
        result = future.result(timeout=step.timeout)
```

### 12.8 Conditional Branching

Decisions based on step outputs:

Condition types: EQUALS, NOT_EQUALS, GREATER_THAN, LESS_THAN, CONTAINS, NOT_CONTAINS, REGEX_MATCH, CUSTOM (callable).

```
Step A completed
     │
     ▼
Decision: spec_match > 70%?
  ├── YES → Step B (Generate bid)
  └── NO  → Step C (Review required)
```

### 12.9 Approval Workflows

When approval_required is set on a step:
1. Workflow pauses (WAITING_APPROVAL)
2. ApprovalRequest created with: requester, approvers, title, description, data
3. Notification sent to approvers
4. Status: PENDING → APPROVED / REJECTED / EXPIRED / ESCALATED
5. On APPROVED: workflow resumes
6. On REJECTED: workflow stops or takes on_failure branch
7. On EXPIRED: auto-escalate or fail

---

## 13. End-to-End Pipeline Connector

### 13.1 The 8 Pipelines

**File**: pipeline_connector.py (1,246 lines)

The pipeline connector wires all system components into 8 end-to-end pipelines:

**Pipeline 1 — RFP Intake and Processing**
```
PDF Upload → PDFExtractionManager → PyPDF2 text extraction →
RFPTermsMatcher (100k terms DB) → DB storage (SQLAlchemy) →
ChromaDB vector embedding
```

**Pipeline 2 — Product Matching Engine**
```
RFP Requirements → ChromaDB vector search →
VectorEmbeddingManager (sentence-transformers) →
TechnicalAgent spec matching → Weighted scoring →
Top 3 selection per product
```

**Pipeline 3 — Pricing and Commercial Bid**
```
Product recommendations + Tests required →
PricingAgent (price tables + test costs) →
Tax calculation → BidDocumentGenerator →
PDF bid document output
```

**Pipeline 4 — Vendor Management**
```
Vendor profiles → Rating system →
Performance history → RFP response integration
```

**Pipeline 5 — Agent Orchestration**
```
MasterAgent → SalesAgent (scan) →
TechnicalAgent (match) → PricingAgent (price) →
Consolidation → Validation → Output
```

**Pipeline 6 — Performance Optimization**
```
Profiling → Bottleneck detection →
Recommendation generation → Auto-apply
```

**Pipeline 7 — Compliance and Audit**
```
Compliance rules → Standard validation →
Audit logging (SHA-256) → Report generation
```

**Pipeline 8 — Analytics and Reporting**
```
Metrics collection → Aggregation →
Trend analysis → Predictive analytics →
Dashboard API → Export (JSON/CSV)
```

### 13.2 Pipeline Stage Enum (15 Stages)

RFP_INTAKE → PDF_EXTRACTION → TERM_MATCHING → DB_STORAGE → AGENT_ORCHESTRATION → TECHNICAL_ANALYSIS → VECTOR_SEARCH → SPEC_MATCHING → PRICING_CALCULATION → BID_GENERATION → COMPLIANCE_CHECK → AUDIT_LOGGING → ANALYTICS_TRACKING → VENDOR_INTEGRATION → COMPLETED

### 13.3 Pipeline Context Object

Passed through every stage, accumulating results:

- pipeline_id — Unique run identifier
- rfp_id — RFP being processed
- pdf_path — Uploaded file location
- extracted_text — Raw text from PDF
- requirements[] — Parsed requirements
- matched_products[] — Product matches
- pricing_data — Pricing breakdown
- bid_data — Generated bid
- compliance_results — Compliance check results
- audit_entries[] — Audit log entries
- analytics_data — Metrics
- stage_results[] — Per-stage results (status, data, error, duration)
- errors[] — Accumulated errors

### 13.4 Module Lazy Loading

All pipeline modules are loaded lazily with graceful fallback:

```python
class _ModuleLoader:
    def get_pdf_extraction_manager():    # pdf_extraction/
    def get_rfp_terms_matcher():         # pdf_extraction/
    def get_spec_matcher():              # agents/technical_agent/
    def get_technical_agent():           # agents/technical_agent/
    def get_vector_embeddings():         # database/vector_embeddings
    def get_chromadb_manager():          # database/chromadb_setup
    def get_pricing_agent():             # agents/pricing_agent/
    def get_bid_generator():             # api/bid_document_generator
    def get_compliance_checker():        # compliance_and_standards/
    def get_audit_trail():               # audit_and_trailing/
    # ... etc.
```

If any module fails to load, the pipeline continues with that stage producing a "not available" result instead of crashing.

---

## 14. Vector Search Integration

### 14.1 ChromaDB Collections

4 vector collections power semantic search:

**products** — 22,000+ product descriptions embedded as 384-dim vectors.
Query: RFP requirement text → Top N similar products.

**rfp_requirements** — Historical RFP requirements embedded for reuse.
Query: New requirement text → Similar past requirements (knowledge reuse).

**agent_knowledge** — Past agent analysis responses.
Query: Current analysis context → Relevant past insights.

**standards** — Technical standard descriptions.
Query: RFP standard reference → Matching known standards.

### 14.2 Embedding Models

| Model | Dimensions | Use Case |
|---|---|---|
| all-MiniLM-L6-v2 | 384 | Default (fast) |
| all-MiniLM-L12-v2 | 384 | Better accuracy |
| all-mpnet-base-v2 | 768 | Highest accuracy |
| multi-qa-distilbert-cos-v1 | 768 | Question-answer |
| paraphrase-MiniLM-L6-v2 | 384 | Paraphrase detection |

### 14.3 Search Modes

- Semantic — Pure vector similarity search
- Keyword — Traditional text filtering
- Hybrid — Combined vector + keyword (best results)

### 14.4 Embedding Cache

LRU cache with TTL prevents re-computing vectors:
- Repeated queries return cached embeddings instantly
- Memory-bounded to prevent unbounded growth
- TTL-based expiry for freshness

---

## 15. Accuracy and Scoring Deep Dive

### 15.1 Spec Match Accuracy

The spec matching system has been designed with multiple accuracy-boosting techniques:

**Semantic Equivalence Maps** — 5 domain-specific maps with 30+ equivalents each ensure that "Electrolytic Grade Copper" matches "ETP Copper" with 100% confidence.

**3-Priority Matching** — For each spec, the system tries exact equivalence first, then containment matching, then keyword matching. This layered approach minimizes false negatives.

**Numeric Tolerance** — 10% tolerance for exact match (0.95 score), 20% for partial match (0.80 score). Prevents rejection due to minor measurement differences.

**Datasheet Deep Search** — If a spec isn't in the flat product dict, the nested datasheet (electrical_properties, physical_properties) is searched. This catches specs that are stored in different structures across OEMs.

### 15.2 Confidence Scoring Factors

| Factor | Weight | What It Measures |
|---|---|---|
| Data Completeness | 30% | How many specs have data |
| Match Consistency | 25% | Score variance (low = good) |
| Verification Status | 20% | Is data verified by OEM |
| Critical Specs Score | 15% | Are safety specs matched |
| Standard Confidence | 10% | Standard equivalence trust |

### 15.3 Quality Assurance

**Cross-validation**: Comparison tables show RFP requirement alongside all 3 OEM values, making manual verification easy.

**Critical failure detection**: Products with dangerous mismatches (voltage, temperature, current) are immediately flagged regardless of overall score.

**Gap analysis**: For every unmet spec, the system explains what's missing, how big the gap is, and what remediation options exist.

**Audit trail**: Every matching decision is logged with the full scoring breakdown for post-analysis.

### 15.4 LLM Enrichment Accuracy

The LLM adds qualitative analysis that deterministic matching cannot:

- Suitability ratings (excellent/good/fair/poor) with reasoning
- Strengths and deviations per product
- Overall recommendation with engineering rationale
- Alternative suggestions when no product is ideal
- Handles ambiguous specifications that rule-based systems miss

LLM temperature is set to 0.05 (near-deterministic) for consistency across repeated analyses.

---

## 16. Agent Performance Tracking

### 16.1 Performance Integration

**File**: agents/shared/agent_performance.py

Every agent operation is tracked:

```python
@track_agent_operation("technical_agent", "spec_matching")
def process_rfp(rfp_context):
    ...
```

Metrics collected:
- Execution time per operation (ms)
- Tokens used (LLM operations)
- Error counts and types
- Cache hit/miss ratios
- Message processing throughput

### 16.2 Performance Decorators

Applied throughout the agent system:

- @cached(ttl=300) — Cache results for 5 minutes
- @profiled — Log execution time
- @with_timeout(30) — Kill if exceeds 30 seconds
- @track_agent_operation — Record to metrics
- @cache_agent_result — Agent-specific caching
- @rate_limit_agent — Prevent API overload

### 16.3 Graceful Degradation

All performance decorators use try/except ImportError:

```python
try:
    from performance.integration import cached, profiled, with_timeout
except ImportError:
    def cached(**kw): return lambda f: f    # No-op
    def profiled(f): return f               # No-op
    def with_timeout(t): return lambda f: f # No-op
```

System works at full functionality without performance module — just without monitoring.

---

## 17. Complete RFP Analysis Flow (API Endpoint)

### 17.1 POST /api/v1/rfps/analyze — The Core Feature

This is the complete end-to-end flow when a user uploads an RFP PDF:

```
User uploads PDF
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ STAGE 1: PDF EXTRACTION (~1-3 seconds)                       │
│                                                              │
│ PDFExtractionManager.extract_text_from_pdf(pdf_path)        │
│   → PyPDF2 page-by-page extraction                          │
│   → Text stats (pages, words, chars)                         │
│   → Metadata JSON                                            │
│                                                              │
│ RFPTermsMatcher.match(text)                                  │
│   → Match against 100k+ terms database                       │
│   → Identify products, specs, standards, tests               │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ STAGE 2: DETERMINISTIC ANALYSIS (~2-5 seconds)               │
│                                                              │
│ Requirement Parsing:                                         │
│   → Extract products with specifications                     │
│   → Parse quantities, units, standards                       │
│   → Identify tests and acceptance criteria                   │
│                                                              │
│ Product Matching (for each requirement):                     │
│   → Query ChromaDB for semantic matches                      │
│   → Score against 22k+ OEM products                          │
│   → Enhanced matching (semantic + numeric + datasheet)       │
│   → Select Top 3, build comparison tables                    │
│                                                              │
│ Pricing Calculation:                                         │
│   → Look up product prices by SKU                            │
│   → Calculate test costs                                     │
│   → Apply bulk discounts                                     │
│   → Calculate taxes (18% GST)                                │
│   → Compute grand total                                      │
│                                                              │
│ Response Consolidation:                                      │
│   → Scope of Supply table                                    │
│   → Test costs breakdown                                     │
│   → Compliance checklist                                     │
│   → Overall recommendation                                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
           IMMEDIATE RESPONSE RETURNED TO USER
           (Deterministic results in ~3-8 seconds)
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ STAGE 3: LLM ENRICHMENT (Background, ~30-45 seconds)        │
│                                                              │
│ Phase 1 — Parallel extraction (~8-12s):                      │
│   ├─ LCSalesAgent: RFP metadata, bid details                 │
│   └─ LCTechnicalAgent: Cable/wire requirements               │
│                                                              │
│ Phase 2 — Pricing estimation (~5-8s):                        │
│   └─ LCPricingAgent: Market-aware cost estimates             │
│                                                              │
│ Phase 3 — Match analysis (~8-12s):                           │
│   └─ LCTechnicalAgent.analyze_matches() for each comparison  │
│       ├─ Suitability rating with reasoning                   │
│       ├─ Strengths and deviations                            │
│       ├─ Recommendation rationale                            │
│       └─ Alternative suggestions                             │
│                                                              │
│ Results polled via:                                           │
│   GET /rfps/analyze/{id}/enrichment                          │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ STAGE 4: LINKED DOCUMENT EXTRACTION (Background)             │
│                                                              │
│ Extract hyperlinks from PDF                                  │
│   → Download linked PDFs, Excel, CSV                         │
│   → Parse BOQ (Bill of Quantities)                           │
│   → Extract additional requirements                          │
│                                                              │
│ Results polled via:                                           │
│   GET /rfps/analyze/{id}/linked-docs                         │
└──────────────────────────────────────────────────────────────┘
```

### 17.2 Why This Architecture Is Efficient

**User gets results in ~3-8 seconds** — The deterministic pipeline (extraction + matching + pricing) runs completely without any API calls, using pre-loaded data and algorithmic scoring.

**LLM enriches in background** — 30-45 seconds of LLM processing happens after the user already has their results. Client polls for enrichment data and updates the UI when available.

**Parallel agent execution** — Sales and Technical LLM agents run simultaneously (ThreadPoolExecutor), cutting ~50% of sequential time.

**Smart text trimming** — Only the most relevant paragraphs are sent to the LLM, keeping within context window limits while maximizing signal.

**Singleton LLM** — One ChatGroq instance reused across all agents. Connection reuse makes 2nd+ calls faster.

**Lazy loading** — OEM database (22k+ products), LLM models, and pipeline modules are loaded on first use, not at startup. Server starts in under a second.

---

## 18. Data Models and Shared Types

### 18.1 Canonical Data Models

**File**: agents/shared/data_models.py (394 lines)

Shared types used across all agents for consistency:

**RFPDocument** — Complete RFP structure:
- rfp_id, rfp_number, title, issuing_authority
- issue_date, due_date, estimated_value
- products (RFPProduct[])
- tests_required (RFPTestRequirement[])
- acceptance_criteria, submission_mode, emd_required

**RFPProduct** — Single product in scope:
- product_id, product_name, category
- quantity, unit, specifications
- mandatory_specs, preferred_specs
- applicable_standards

**RFPTestRequirement** — Test requirement:
- test_id, test_name, test_type (ROUTINE/TYPE/ACCEPTANCE/SPECIAL)
- applicable_products, standard_reference
- parameters, frequency, mandatory

**ProductRecommendationResult** — Per-product output:
- rfp_product_id, rfp_specifications, quantity
- top_3_recommendations (OEMProductMatch[])
- selected_sku, selected_spec_match
- comparison_table, specification_gaps

**OEMProductMatch** — Single product match:
- rank, sku, product_name, manufacturer
- spec_match_percent, specifications
- matched_specs, unmatched_specs
- compliance_notes

### 18.2 Spec Match Levels

| Level | Meaning |
|---|---|
| FULL_MATCH | 100% match on this spec |
| EXCEEDS | OEM spec exceeds requirement |
| PARTIAL_MATCH | Greater than 70% match |
| MARGINAL | 50-70% match |
| NO_MATCH | Less than 50% match |
| NOT_FOUND | Spec not in OEM datasheet |

### 18.3 RFP Priority Levels

| Priority | Deadline |
|---|---|
| CRITICAL (1) | Due within 7 days |
| HIGH (2) | Due within 14 days |
| MEDIUM (3) | Due within 30 days |
| STANDARD (4) | Due within 90 days |
| LOW (5) | Due after 90 days |

---

## 19. E-Procurement Portal Integration

### 19.1 How the Scraper Pipeline Works

5 simulated procurement portals serve RFPs:

```
┌───────────────────────────────────────────────────────┐
│ portal_config.py                                      │
│   → Discovers all PDFs in RFPs/ directory            │
│   → Round-robin distributes across 5 portals          │
│   → Each PDF gets deterministic metadata              │
│     (title, dept, deadline — from filename MD5 hash) │
└───────────────────────────┬───────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ GEM      │ │ CPPP     │ │ State    │ ... (5 portals)
        │ Port 5001│ │ Port 5002│ │ Port 5003│
        │ Flask app│ │ Flask app│ │ Flask app│
        │ /api/rfps│ │ /api/rfps│ │ /api/rfps│
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│ rfp_processor/scraper.py                                 │
│   → Hits all 5 portals in parallel                       │
│   → GET /api/rfps for listings                           │
│   → Downloads PDFs                                       │
│   → Creates manifest of all discovered RFPs              │
│   → Feeds into RFP Intake Pipeline                       │
└──────────────────────────────────────────────────────────┘
```

---

## 20. System Architecture Summary

### 20.1 Complete Data Flow

```
                    ┌──────────────────┐
                    │  RFP PDF Upload  │
                    │  or Portal Scrape│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ PDF Extraction    │ PyPDF2/pdfplumber/PyMuPDF
                    │ + Term Matching   │ 100k+ terms database
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Master Agent    │ Orchestrator
                    │  (Tier 1)        │ State Machine
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌───▼──────┐ ┌────▼──────┐
     │  Sales Agent   │ │Technical │ │ Pricing   │
     │  Scan + Select │ │Match     │ │ Calculate │
     │                │ │22k+ OEM  │ │ Price +   │
     │  (Tier 2)      │ │products  │ │ Tests     │
     └────────┬───────┘ └───┬──────┘ └────┬──────┘
              │              │              │
              │    ┌─────────┘              │
              │    │    ┌──────────────────┘
              ▼    ▼    ▼
     ┌──────────────────────────────────────┐
     │  Consolidation                       │
     │  Scope of Supply + Pricing + Tests   │
     │  Compliance Checklist                │
     │  Recommendation                      │
     └────────────────┬─────────────────────┘
                      │
              ┌───────┼───────┐
              ▼       ▼       ▼
         ┌────────┐ ┌─────┐ ┌──────┐
         │ Bid    │ │Audit│ │LLM   │
         │ PDF    │ │Trail│ │Enrich│
         │ Report │ │     │ │(bg)  │
         └────────┘ └─────┘ └──────┘
```

### 20.2 Key Metrics at a Glance

| Metric | Value |
|---|---|
| Total agent code | ~10,000 lines |
| Shared infrastructure | ~7,500 lines |
| OEM products in catalog | 22,000+ |
| RFP terms database | 100,000+ |
| Message types | 21 |
| Priority levels | 5 |
| Workflow states | 10 |
| Pipeline stages | 15 |
| Semantic equivalence maps | 5 |
| Spec categories | 4 (weighted) |
| Critical failure types | 8 |
| Match quality tiers | 5 |
| Deterministic response | 3-8 seconds |
| LLM enrichment | 30-45 seconds |
| LLM model | Llama 3.3 70B |
| Embedding model | all-MiniLM-L6-v2 (384d) |
| Vector collections | 4 |
| API endpoints | ~95 |
| End-to-end pipelines | 8 |
