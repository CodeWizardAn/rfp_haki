# NLP & Data Engineer — HAKI FMCG 2.0

> Role perspective documentation for the **NLP & Data Engineer** covering vector embeddings, semantic search, LLM-powered text processing, specification matching, data pipelines, normalization, scoring algorithms, and analytics data processing.

---

## 1. What Has Been Built

### 1.1 NLP & Data Engineering Scope

The NLP & Data Engineering work in HAKI FMCG 2.0 spans five core pillars:

**Vector Embeddings & Semantic Search**

- Modules: vector_embeddings.py, chromadb_setup.py, embedding_cache.py
- Converts product specs and RFP requirements into 384/768-dim vectors
- Stores in ChromaDB; performs semantic similarity search

**LLM-Powered Text Extraction**

- Module: rfp_chain.py (LangChain agent)
- LangChain chains with Groq LLM (Llama 3.3 70B)
- Extracts structured data from unstructured RFP text

**Specification Matching & Normalization**

- Modules: matching_engine.py, spec_matcher.py, shared/utils
- 6 domain equivalence maps, 10-step scoring pipeline
- Gap analysis and critical failure detection

**Data Pipelines & ETL**

- Modules: data_loaders.py, generate_optimizations.py, catalog_store.py
- Loads 22k+ OEM products from CSV
- Validates, normalizes columns, enriches with computed fields

**Analytics Data Processing**

- Modules: predictive_analytics.py, trend_analysis.py, match_accuracy.py
- Linear regression, Naive Bayes classification
- Time-series analysis, match accuracy tracking

### 1.2 Data Assets

| Asset | Size |
|---|---|
| OEM Product Catalog (CSV) | 22,000+ products |
| Marketplace Products (CSV) | ~2,000 products |
| Optimized Products (CSV) | 22,000+ enriched |
| ChromaDB Vector Store | 4 collections |
| Pricing Tables (JSON) | Per-product |
| Service Prices (JSON) | Lab testing/cert |
| Saved Analyses (JSON) | Per-RFP |
| User Products (JSON) | User-added |

Storage locations:

- OEM CSVs — wires_cables_data/ (Polycab, Havells, Finolex, KEI, RR Kabel)
- Marketplace — wires_cables_data/moglix_*.csv
- Optimized — *_optimized_*.csv (10 computed columns)
- Vectors — database/db_vector/chroma.sqlite3
- Pricing — database/db_pricing/
- Analyses — database/db_rfp/analysis_history.json
- User catalog — database/db_products/user_catalog.json

---

## 2. Vector Embeddings & Semantic Search

### 2.1 Embedding Model Stack

Source: vector_embeddings.py (1,781 lines) — full embedding pipeline built on Sentence Transformers + ChromaDB.

| Model | Dims | Speed |
|---|---|---|
| all-MiniLM-L6-v2 (default) | 384 | Fast |
| all-MiniLM-L12-v2 | 384 | Medium |
| all-mpnet-base-v2 | 768 | Slow |
| multi-qa-distilbert-cos-v1 | 768 | Medium |
| paraphrase-MiniLM-L6-v2 | 384 | Fast |

Use cases:

- all-MiniLM-L6-v2 — General product/requirement matching (good quality)
- all-MiniLM-L12-v2 — Higher-quality matching (better quality)
- all-mpnet-base-v2 — Maximum accuracy matching (best quality)
- multi-qa-distilbert-cos-v1 — Question-answer retrieval (best for Q&A)
- paraphrase-MiniLM-L6-v2 — Paraphrase/duplicate detection

**Model management**: Singleton EmbeddingModelManager with lazy loading — models loaded on first use, not at startup. Supports hot-swapping via unload_model() + load_model().

### 2.2 Product Text Generation

ProductTextGenerator converts raw product dictionaries into searchable text representations:

```
Input:  {"name": "Polycab 4C×16 XLPE Cable", "conductor_material": "Copper", 
         "conductor_size_sqmm": 16, "voltage_rating": "1100V", ...}

Output: "Polycab 4C×16 XLPE Cable | Conductor Material: Copper | 
         Size: 16 sqmm | Insulation: XLPE | Voltage: 1100V | Cores: 4"
```

**Field maps**: 14 priority-ordered product fields and 10 RFP fields, each with a formatting template. Fields are pipe-delimited, truncated to 1,000 characters.

### 2.3 Embedding Pipeline

```
Raw Product Dict
    │
    ▼
ProductTextGenerator.generate_product_text()
    │  → "Polycab 4C×16 XLPE Cable | Conductor Material: Copper | ..."
    ▼
EmbeddingPipeline.generate_embedding()
    │  → SentenceTransformer.encode(text)
    │  → L2 normalization (unit vector)
    ▼
384-dimensional float vector
    │
    ▼
ChromaDBEmbeddingStore.add_embeddings()
    │  → Metadata sanitized (str/int/float/bool only)
    │  → Upsert with dedup by ID
    ▼
Persisted in ChromaDB (HNSW cosine space)
```

**Batch processing**: Default batch size of 32 for encoding. ChromaDB upsert batch size of 100.

**Cosine similarity**: NumPy-optimized dot(a, b) / (norm(a) × norm(b)) with pure-Python fallback.

### 2.4 ChromaDB Collections

Four vector collections in chromadb_setup.py:

**products** — Semantic product search

- Document: name, description, material, size, insulation, cores, voltage
- Metadata: sku, oem, category, conductor_material, insulation_type
- Purpose: Match RFP requirements against 22k+ products

**rfp_requirements** — Knowledge reuse

- Document: Original requirement text
- Metadata: rfp_id, requirement_number, product_type
- Purpose: Find similar past requirements

**agent_knowledge** — Agent learning

- Document: Historical agent analysis text
- Metadata: agent_type, action_type, confidence
- Purpose: Retrieve past analyses for similar queries

**standards** — Standards matching

- Document: Standard description text
- Metadata: standard_code, issuing_body, category
- Purpose: Match RFP-referenced standards against known standards

**Search operations**:
```python
results = search_products(
    query="4 core 240 sqmm XLPE cable 33kV",
    n_results=10,
    where={"category": "power_cables"},
    where_document={"$contains": "armoured"}
)
# Returns: documents, distances → similarity = 1 - distance
```

ChromaDB filters compose via $and / $or for multi-criteria filtering.

### 2.5 Embedding Cache

Source: embedding_cache.py (578 lines) — Thread-safe LRU cache avoiding re-computation.

| Feature | Details |
|---|---|
| Eviction | LRU via OrderedDict |
| Count limit | max_size = 1000 entries |
| Memory limit | max_memory_mb = 100 MB |
| TTL | Per-entry or default TTL |
| Size estimation | NumPy nbytes fallback |
| Thread safety | threading.RLock on all ops |
| Stats | hits, misses, evictions |

---

## 3. LLM-Powered Text Extraction (LangChain)

### 3.1 Architecture

Source: rfp_chain.py (646 lines) — Three LLM agents orchestrated by a master, using LangChain Core + Groq (Llama 3.3 70B Versatile).

```
Unstructured RFP Text
    │
    ├──→ _smart_trim(text, max_chars=6000)
    │
    ├──→ LCSalesAgent (metadata extraction)
    │       └──→ ChatPromptTemplate → ChatGroq → JSON
    │
    ├──→ LCTechnicalAgent (requirement extraction)
    │       ├──→ TECH_EXTRACT_PROMPT → ChatGroq → JSON array
    │       └──→ _normalize() (numeric conversion)
    │
    ├──→ LCPricingAgent (cost estimation)
    │       └──→ PRICING_PROMPT → ChatGroq → JSON
    │
    └──→ LCMasterAgent (parallel orchestration)
            └──→ ThreadPoolExecutor(max_workers=4)
                 Total pipeline: 30-45 seconds
```

### 3.2 Smart Text Trimming

_smart_trim(text, max_chars=6000) solves the LLM context window problem:

1. Split text into paragraphs by double newline
2. Score each paragraph by domain keyword density — 38 procurement/wire-cable keywords (cable, wire, conductor, sqmm, voltage, insulation, xlpe, pvc, armoured, core, copper, aluminium, specification, boq, tender, etc.)
3. Sort paragraphs by score descending
4. Greedily select top-scoring paragraphs until max_chars reached
5. Re-order selected paragraphs by original position (preserves document flow)

**Why**: Raw RFP PDFs can be 50-100 pages. LLMs have fixed context windows. Smart trimming keeps the most relevant 6,000 characters while maintaining document coherence.

### 3.3 LLM Prompt Engineering

**Sales Agent Prompt** — Metadata extraction:
```
Extract these fields from the RFP text:
- rfp_title, bid_number, issuing_authority, due_date
- emd_amount (Earnest Money Deposit)
- compliance_requirements, tests_required
Return as JSON.
```

**Technical Agent Prompt** — Requirement extraction with inline NLP instructions:
```
Extract cable/wire requirements as a JSON array. Each item:
{conductor_size, cores, voltage, conductor_material, insulation, 
 standard, armoured, fire_resistant, quantity}

NORMALIZATION RULES:
- Sizes: "2.5mm²" → 2.5, "4 sq mm" → 4
- Voltage: "1.1kV" → 1100, "650/1100V" → 1100
- Abbreviations: Cu=Copper, Al=Aluminium, SWA=Steel Wire Armoured
- Booleans: "fire-retardant" → fire_resistant=true
- Extract from BOQ tables line-by-line
```

**Pricing Agent Prompt** — Indian market cable pricing estimation with 18% GST calculation.

### 3.4 Output Parsing & Robustness

**_safe_json_parse(text)** — Handles messy LLM output:

1. Strip markdown code fences
2. Attempt json.loads()
3. Fallback: regex extract first [{...}] or {...} block
4. Return empty dict/list on failure

**_normalize() in LCTechnicalAgent**:

- _safe_num(val): Convert string to float, handle "N/A", null, empty
- Filter out requirements missing all 5 core spec fields
- Ensure consistent data types across all extracted requirements

### 3.5 Deterministic Fallbacks

Every LLM agent has a deterministic fallback that activates when the Groq API key is missing, the LLM request times out (25s limit), or the LLM returns unparseable output.

**LCSalesAgent fallback** — Regex extraction for bid number, date patterns, EMD amounts

**LCTechnicalAgent fallback** — Rule-based requirement parsing (regex for sizes, cores, voltage, materials)

**LCPricingAgent fallback** — Deterministic pricing at Rs 50/meter default, Rs 10,000/test, 18% GST

---

## 4. Specification Matching & Normalization

### 4.1 Domain Equivalence Maps

Source: spec_matcher.py — defines 6 semantic equivalence dictionaries for the wire/cable domain.

**CONDUCTOR_MATERIAL_MAP** (5 categories, 25+ aliases):
```
copper      ≡ "electrolytic grade copper" ≡ "99.97% pure electrolytic copper" 
            ≡ "etp copper" ≡ "ofc copper" ≡ "cu"
aluminium   ≡ "ec grade aluminium" ≡ "electrical grade aluminium" ≡ "al"
tinned_copper ≡ "tin coated copper" ≡ "sn-cu"
```

**INSULATION_TYPE_MAP** (8 categories, 30+ aliases):
```
pvc   ≡ "pvc type a (fr/frls/frlsh)" ≡ "fr pvc" ≡ "hrfr pvc"
xlpe  ≡ "cross-linked polyethylene" ≡ "tr-xlpe" ≡ "silane xlpe"
lshf  ≡ "low smoke halogen free" ≡ "lszh" ≡ "ls0h"
```

**VOLTAGE_RATING_MAP** (6 categories):
```
1100v ≡ "1100v ac" ≡ "1.1kv" ≡ "650/1100v" ≡ "600/1000v"
3300v ≡ "3.3kv" ≡ "1900/3300v"
```

Also: CONDUCTOR_TYPE_MAP (solid/stranded/flexible), ARMOUR_TYPE_MAP (SWA/STA/AWA/unarmoured), DATASHEET_KEY_MAP (nested JSON key to flat spec key mapping).

### 4.2 Semantic Matching Algorithm

The _semantic_match function:

```
1. Select equivalence map based on spec_key
2. find_category(value, map):
   Priority 1: Exact match in equivalents list        → direct hit
   Priority 2: Value contained within an equivalent    → longest match wins
   Priority 3: Equivalent contained within value       → longest match wins
3. If both values → same category      → score 1.0
   If both values → different categories → score 0.0
   Partial fallback: keyword containment → score 0.9
```

**Why priority-based**: RFP text is messy. "Electrolytic Grade Copper as per IS 8130" should match "Copper" — Priority 2 catches this. "PVC" should match "PVC Type A (FR/FRLS/FRLSH)" — Priority 3 catches this.

### 4.3 Value Normalization

_normalize_value(value):

1. Strip unit suffixes: AC, DC, °C, A, V, sq mm, sqmm, approx, ±
2. Attempt float conversion
3. Return cleaned string if not numeric

### 4.4 Enhanced Spec Comparison Pipeline

```
Step 1: Normalize both values
Step 2: Try semantic matching (equivalence maps)
         → If mapped: return map score (1.0 or 0.0)
Step 3: If both numeric:
         → Exact match → 1.0
         → ≤10% difference → 0.95
         → ≤20% difference → 0.8
         → >20% → 0.0
Step 4: String containment → 0.9
Step 5: Word overlap scoring → proportional
Step 6: No match → 0.0
```

### 4.5 Datasheet-Level Matching

Products with detailed datasheets (nested JSON from manufacturer PDFs) are matched using DATASHEET_KEY_MAP:

```python
DATASHEET_KEY_MAP = {
    "electrical_properties.rated_voltage":    "voltage_rating",
    "physical_properties.conductor_material": "conductor_material",
    "physical_properties.insulation_type":    "insulation_type",
    "dimensions.conductor_size_sqmm":         "conductor_size_sqmm",
}
```

This traverses nested product datasheet JSON to extract flat spec values for comparison.

---

## 5. The 10-Step Matching Engine

Source: matching_engine.py (1,416 lines) — the core scoring pipeline that produces final match results.

### 5.1 Specification Categories & Weights

**CRITICAL (2.0x weight) — Must match:**

- voltage_rating, rated_voltage
- conductor_material, insulation_type
- temperature_rating, current_rating, fire_rating

**IMPORTANT (1.5x weight) — Should match:**

- conductor_size, cross_section_sqmm
- number_of_cores, armour_type
- outer_sheath, standard

**STANDARD (1.0x weight) — Nice to match:**

- conductor_type, conductor_class
- color, certifications

**INFORMATIONAL (0.5x weight) — Reference only:**

- manufacturer, brand, moq, lead_time

### 5.2 The 10-Step Pipeline

```
Input: (rfp_requirement, candidate_product)
    │
    ▼ Step 1: Spec-by-Spec Scoring
    │  For each shared spec key:
    │    score = compare_spec_values(key, rfp_val, product_val)
    │    weight = SPEC_CATEGORIES[key].weight
    │
    ▼ Step 2: Standard Equivalence Check
    │  IS 7098 ≈ IEC 60502? → StandardMapper
    │  Direct equivalence, indirect (bridge), base code matching
    │
    ▼ Step 3: Critical Failure Detection (5 checks)
    │  ✗ Voltage mismatch (>10% below requirement)
    │  ✗ Temperature rating insufficient (margin <10°C)
    │  ✗ Conductor size mismatch (>20%)
    │  ✗ Material incompatibility (copper vs aluminium)
    │  ✗ Missing critical certifications (BIS, ISI, CPRI)
    │  → Any failure = hard penalty on final score
    │
    ▼ Step 4: Gap Analysis
    │  Classify each gap: MISSING | INSUFFICIENT | OVER_SPECIFIED
    │  Impact level: CRITICAL | HIGH | MEDIUM | LOW
    │
    ▼ Step 5: Data Completeness
    │  How many spec fields present in both requirement & product
    │
    ▼ Step 6: Score Aggregation
    │  OVERALL = weighted_avg × 0.50
    │          + standard_score × 0.25
    │          + certification_score × 0.15
    │          + critical_only × 0.10
    │
    ▼ Step 7: Confidence Calculation
    │  data_completeness:    30%
    │  match_consistency:    25%
    │  verification_status:  20%
    │  critical_specs_avg:   15%
    │  standard_confidence:  10%
    │
    ▼ Step 8: Quality Classification
    │  EXCELLENT ≥ 95%  |  GOOD ≥ 85%
    │  FAIR ≥ 70%  |  POOR ≥ 50%  |  DISQUALIFIED < 50%
    │
    ▼ Step 9: Recommendation Level
    │  HIGHLY_RECOMMENDED | RECOMMENDED
    │  CONDITIONAL | NOT_RECOMMENDED
    │
    ▼ Step 10: Explanation Generation
    │  ✓ matched / △ partial / ✗ failed per spec
    │
    ▼
Output: MatchResult {
    overall_score, weighted_score, confidence,
    quality, recommendation, spec_scores,
    critical_failures, gaps, explanation
}
```

### 5.3 Batch Matching

For each RFP requirement, the engine evaluates all candidate products:

1. Score all products against the requirement
2. Sort by overall_score descending
3. Keep top-N per requirement
4. Generate quality distribution summary
5. Return BatchMatchResult with per-requirement top matches

---

## 6. NLP Utilities (Shared Toolkit)

### 6.1 Standard Mapper

Source: standard_mapper.py (520 lines) — **16 equivalence groups** covering Indian and international electrical standards.

| Group | Standards |
|---|---|
| LT Power Cables | IS 7098-1, IEC 60502-1, BS 6346 |
| HT Power Cables | IS 7098-2, IEC 60502-2, BS 6622 |
| Control Cables | IS 1554-1, IEC 60227, BS 6004 |
| Flexible Cables | IS 694, IEC 60227-5, BS 6500 |
| Fire Resistant | IS 10810, IEC 60332, BS 4066 |
| Instrumentation | IS 1554-2, IEC 60092, BS 5308 |
| Conductor | IS 8130, IEC 60228, ASTM B8 |
| Insulation | IS 5831, IEC 60811, ASTM D150 |
| Testing | IS 10810-3, IEC 60331, BS 6387 |

StandardInfo dataclass: code, name, issuing_body, description, year, category, scope.

Issuing bodies: BIS, IEC, ISO, BS, ASTM, IEEE, NEMA, UL, DIN, JIS.

Functions: is_standard_equivalent(), get_equivalent_standards(), get_standard_info().

### 6.2 Specification Normalizer

Source: spec_normalizer.py (525 lines).

**Material normalization**

- Input examples: "Cu", "ETP Copper", "99.97% pure electrolytic copper"
- Output: MaterialType.COPPER (confidence 0.95-1.0)

**Insulation normalization**

- Input examples: "XLPE", "Cross-linked polyethylene", "TR-XLPE"
- Output: InsulationType.XLPE (confidence 0.95-1.0)

**Conductor size normalization**

- Input examples: "2.5mm²", "14 AWG", "250 kcmil"
- Output: 2.5 sqmm, 2.08 sqmm, 126.7 sqmm

**Voltage normalization**

- Input examples: "1.1kV", "1100V AC", "650/1100V"
- Output: 1100.0 (confidence 0.95)

**Temperature normalization**

- Input examples: "90°C", "90 deg C"
- Output: 90.0 (confidence 0.95)

AWG conversion table: 30-entry lookup from AWG 0000 (107.2 sqmm) to AWG 26 (0.128 sqmm).

Standard size snapping: 24 standard conductor sizes (0.5, 0.75, 1.0, 1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400, 500, 630, 800, 1000 sqmm). Non-standard sizes snap to the nearest standard value with a warning.

Returns NormalizedSpec with value, confidence, warnings[].

### 6.3 Unit Converter

Source: unit_converter.py (412 lines).

| Category | Base Unit |
|---|---|
| Length | meter |
| Area | sq meter |
| Temperature | Celsius |
| Voltage | Volt |
| Current | Ampere |
| Weight | kilogram |
| Power | Watt |
| Frequency | Hertz |
| Resistance | Ohm |

Supported units per category:

- Length — mm, cm, m, km, in, ft, μm
- Area — sqmm, sqcm, sqm, sqin, sqft, circular mil, kcmil
- Temperature — °C, °F, K
- Voltage — mV, V, kV
- Current — mA, A, kA
- Weight — mg, g, kg, lb, oz
- Power — W, kW, MW, HP, VA, kVA
- Frequency — Hz, kHz, MHz
- Resistance — mΩ, Ω, kΩ, MΩ

All conversions go through a canonical base unit. Comprehensive alias maps for each unit type.

### 6.4 Text Cleaner

Source: text_utils.py (425 lines).

| Feature | Details |
|---|---|
| Abbreviation expansion | 30 industry abbreviations |
| Stopword removal | Non-informative words |
| Unicode normalization | NFKD for consistent text |
| Number extraction | Decimals, negatives, sci |
| Fuzzy matching | SequenceMatcher-based |
| Tokenization | Word-level, technical |

Abbreviation examples: sqmm → sq mm, cond → conductor, ins → insulation, temp → temperature, cert → certification, spec → specification.

### 6.5 Parameter Extractor

Source: param_extractor.py (488 lines) — Regex-based entity extraction from unstructured text.

**Conductor Spec extraction**

- Input: "4C × 16 sqmm copper stranded"
- Output: material=copper, size=16, cores=4

**Voltage Spec extraction**

- Input: "650/1100V AC"
- Output: rated=1100, system=AC

**Dimension Spec extraction**

- Input: "OD: 25.4mm"
- Output: diameter=25.4, unit=mm

**Quantity Spec extraction**

- Input: "approx 500 meters"
- Output: value=500, unit=meters, approximate=True

**Standards extraction**

- Input: "as per IS 7098 and IEC 60502"
- Output: ["IS 7098", "IEC 60502"]

Regex patterns cover IS, IEC, BS, ASTM standards.

---

## 7. Data Pipelines — ETL for 22k+ OEM Products

### 7.1 Data Loading

Source: data_loaders.py (1,252 lines).

- Source formats: CSV (OEM products) and JSON (pricing, services, configs)
- CSV handling: UTF-8 with latin-1 fallback, whitespace stripping, empty-key column removal
- JSON auto-detection: Looks for data under keys — products, services, prices, rfps, data, items, records

### 7.2 Field Normalization

ProductDataLoader.FIELD_MAPPINGS maps messy CSV column names to standard names:

| Raw CSV Column | Standard Field |
|---|---|
| Product_Code | sku |
| Product_Name | name |
| Company | manufacturer |
| Voltage_Rating | voltage_rating |
| Conductor_Material | conductor_material |
| Conductor_Size_sqmm | conductor_size_sqmm |
| Number_of_Cores | number_of_cores |
| Insulation_Type | insulation_type |

Alternate field name resolution: uppercase, title case, spaced title case.

### 7.3 Type Conversion

_convert_type(value):

- Currency stripping: Rs, $, EUR symbols and commas → float
- Boolean parsing: "true", "1", "yes", "y", "active" → True
- List splitting: comma-separated strings → List
- Numeric casting when possible

### 7.4 Validation System

```python
class ValidationSeverity(Enum):
    ERROR = "error"       # Critical — blocks import
    WARNING = "warning"   # Important — logged but continues
    INFO = "info"         # Minor — informational
```

- Required fields: sku, name, manufacturer — missing = ERROR
- Important fields: category, specifications, certifications — missing = WARNING
- Result: ValidationResult.summary() reports PASSED/FAILED with counts

### 7.5 Indexing

Post-load, builds O(1) lookup dictionaries:

- products_by_sku — Dict[str, Product]
- products_by_oem — Dict[str, List[Product]]

### 7.6 OEM Data Files

5 OEM manufacturers + marketplace data in wires_cables_data/:

| Source | Products |
|---|---|
| Polycab | ~5,000 |
| Havells | ~4,000 |
| Finolex | ~3,500 |
| KEI | ~4,500 |
| RR Kabel | ~4,000 |
| Moglix (marketplace) | ~2,000 |

Each manufacturer provides cables, wires, and complete product CSVs. Also contains by_category/, pdfs/, and summary text files. Moglix data comes in moglix_1.csv and moglix_2.csv.

---

## 8. Data Enrichment & Column Optimization

Source: generate_optimizations.py (893 lines) — Pre-computes 10 new columns on all 22k+ products for faster matching.

### 8.1 Enriched Columns

**Voltage_Normalized** — Regex extraction bucketed into 230V, 400V, 660V, 1000V, 1100V+

**Conductor_Material_Normalized** — Keyword matching to Copper, Aluminium, or Other

**Insulation_Type_Normalized** — Keyword matching to PVC, XLPE, EPR, RUBBER, or Other

**Conductor_Size_Range** — Numeric bucketing into ≤1.5, 1.5-4, 4-16, 16-50, 50-150, >150 sqmm

**Cores_Category** — Numeric mapping to Single Core, Twin, Three Core, Four Core, Multi Core

**Armour_Type_Normalized** — Keyword matching to standardized armour type

**Fire_Rating_Extracted** — Regex extraction of fire-rating keywords

**Application_Domain** — Keyword classification of application domain

**Current_Capacity_Range** — Numeric bucketing into ≤20A, 20-32A, 32-63A, 63-125A, 125-250A, >250A

**RFP_Matching_Tags** — All normalized fields concatenated lowercase for tag-based search

**Matching_Confidence** — Data quality score 0-100 (10 pts per present field)

**RFP_Fit_Score** — Pre-computed composite readiness score

### 8.2 Optimized Match Scoring

```
Matching_Confidence score → 20 points
RFP_Fit_Score            → 30 points
Voltage exact match      → 15 points
Size range match         → 15 points
Cores category match     → 10 points
Material match           → 10 points
Fire rating match        → 10 points
                         ─────────
Maximum                   110 points (normalized to 0-100)
```

Fallback: If no exact column matches, uses RFP_Matching_Tags for flexible substring search.

Output files: *_optimized_YYYYMMDD_HHMMSS.csv alongside original CSVs.

---

## 9. Spec Comparer Scoring Engine

Source: spec_comparer/app.py (2,056 lines) — the production matching engine used for API responses.

### 9.1 Weighted Scoring

| Specification | Weight |
|---|---|
| Conductor_Size_sqmm | 25 |
| No_of_Cores | 20 |
| Voltage_Rating | 15 |
| Conductor_Material | 10 |
| Insulation_Type | 10 |
| Current_Rating_Amps | 8 |
| Standard | 5 |
| Fire_Rating | 4 |
| Is_Armoured | 3 |
| **Total** | **100** |

Rationale:

- Conductor size (25) — Primary sizing parameter; wrong size = wrong cable
- Core count (20) — Determines application compatibility
- Voltage (15) — Safety-critical; undersized voltage = dangerous
- Material (10) — Affects conductivity and cost
- Insulation (10) — Thermal and chemical performance
- Current rating (8) — Load carrying capacity
- Standard (5) — Compliance with IS/IEC requirement
- Fire rating (4) — Fire safety classification
- Armour (3) — Mechanical protection

### 9.2 Engineering Calculations (IS 3961 / IEC 60364-5-52)

| Calculation | Purpose |
|---|---|
| Current carrying capacity | Verify cable handles load |
| Temperature derating | Adjust for ambient temp |
| Grouping derating | Adjust for heat buildup |
| Installation method | Adjust for ventilation |
| Conductor resistance | Ohmic loss calculation |
| Hi-Pot test voltage | Testing requirement |
| Insulation resistance | Temp-corrected quality |

Data sources: Cu tables (20 sizes), Al tables (18 sizes), PVC/XLPE derating at 7 temperature points, 1-20 cables grouping factors, 8 installation methods.

### 9.3 Requirement Extraction from Text

Regex-based extraction (used when LLM is unavailable):

| Pattern | Example Match |
|---|---|
| Size + Core | "16 sq mm × 4 core" |
| Core + Size | "4C × 16 sqmm" |
| Voltage | "1.1kV" or "1100V" |
| Armoured | "Steel Wire Armoured" |
| Insulation | "XLPE insulated" |
| Material | "Copper conductor" |
| Standard | "IS 7098" |

Line-by-line scanning with keyword triggers: wire, cable, sq mm, sqmm, core, conductor.

Deduplication by (conductor_size, cores, voltage, insulation) tuple — prevents duplicate requirements from repeated mentions.

### 9.4 OEM-Diverse Selection

When returning top-N matches, the engine ensures OEM diversity:

1. Best product per OEM first (1 from each manufacturer)
2. Fill remaining top-N slots from highest-scoring products regardless of OEM
3. Result: User sees competitive options across manufacturers

---

## 10. Analytics Data Processing

### 10.1 Predictive Analytics

Source: predictive_analytics.py (513 lines).

**SimpleLinearRegression** — From-scratch implementation with gradient calculation and R² score. Used for price trends and processing time estimation.

**NaiveBayesClassifier** — Feature statistics per class with Gaussian likelihood. Used for bid win probability prediction.

Features computed:

- Win probability based on historical bid data
- Processing time estimation via linear regression
- Match quality prediction from requirement characteristics
- Price/demand trend forecasting

### 10.2 Time-Series Analysis

Source: trend_analysis.py (472 lines).

| Method | Algorithm |
|---|---|
| Simple Moving Average | Window-based mean |
| Exponential Moving Average | Weighted decay (alpha) |
| Weighted Moving Average | Linear weight increase |
| Trend Detection | Linear regression on series |
| Anomaly Detection | Z-score based |
| Seasonality Analysis | Periodic decomposition |
| Growth Rate | Period-over-period change |

### 10.3 Match Accuracy Tracking

Source: match_accuracy.py (418 lines).

| Metric | Measures |
|---|---|
| Precision | Correct / flagged matches |
| Recall | Found / actual matches |
| F1 Score | Harmonic mean of P and R |
| Top-K Accuracy | Correct in top K results |
| Algorithm comparison | Side-by-side accuracy |
| Confidence histogram | Score distribution |

Workflow: Record prediction → Record validation → Calculate ranking metrics.

---

## 11. Parallel Matching Architecture

Source: parallel_matcher.py (476 lines).

| Feature | Implementation |
|---|---|
| Execution modes | ThreadPool or ProcessPool |
| Worker count | CPU count - 1 (default) |
| Chunking | 100 candidates per chunk |
| Strategies | EXACT, FUZZY, SEMANTIC |
| Result aggregation | Sort, top-K, dedup |
| Statistics | Thread-safe tracking |

Used for batch RFP processing where hundreds of requirements are matched against 22k+ products.

---

## 12. How Raw Text Becomes Structured Data (End-to-End)

### 12.1 The Complete NLP Pipeline

```
RAW PDF TEXT (50-100 pages)
         │
         ▼
STAGE 1: Smart Text Trimming
  - Score paragraphs by 38 keywords
  - Keep highest-scoring paragraphs
  - Re-order by document position
  - Output: 6,000 chars max
         │
         ▼
STAGE 2: Entity Extraction
  LLM Path (30-45s):
    - LCSalesAgent → metadata JSON
    - LCTechnicalAgent → requirements[]
    - LCPricingAgent → cost estimates
  Deterministic Path (instant):
    - ParameterExtractor → regexes
    - Spec Comparer → line-by-line scan
         │
         ▼
STAGE 3: Normalization
  - SpecificationNormalizer
    Material: "ETP Copper" → copper
    Insulation: "FR PVC"  → pvc
    Size: "14 AWG" → 2.08 sqmm
    Voltage: "1.1kV" → 1100
  - UnitConverter (kV→V, AWG→sqmm)
  - TextCleaner (abbreviation expansion)
         │
         ▼
STAGE 4: Embedding & Storage
  - ProductTextGenerator → text repr
  - EmbeddingPipeline → 384d vector
  - ChromaDB upsert (HNSW cosine)
         │
         ▼
STAGE 5: Semantic Search
  - ChromaDB.query(requirement_vec)
  - n_results=10 candidates
  - Metadata filters (category, etc.)
         │
         ▼
STAGE 6: 10-Step Matching Engine
  1. Spec-by-spec scoring
  2. Standard equivalence check
  3. Critical failure detection (5)
  4. Gap analysis
  5. Data completeness
  6. Score aggregation (weighted)
  7. Confidence calculation (5-dim)
  8. Quality classification
  9. Recommendation level
  10. Explanation generation
         │
         ▼
OUTPUT: MatchResult per product
  overall_score: 92.5
  quality: "EXCELLENT"
  recommendation: "HIGHLY_RECOMMENDED"
  confidence: 0.88
  spec_scores: {per field}
  critical_failures: []
  gaps: [...]
  explanation: "✓ Voltage: exact..."
```

---

## 13. Why These NLP & Data Choices

### 13.1 Why Sentence Transformers over OpenAI Embeddings

| Factor | Sentence Transformers |
|---|---|
| Cost | Free (local CPU/GPU) |
| Latency | Under 50ms per embed |
| Privacy | On-premise data only |
| Offline | No internet needed |
| Quality | Good for domain text |

| Factor | OpenAI Embeddings |
|---|---|
| Cost | $0.0001 per 1K tokens |
| Latency | 100-500ms (API call) |
| Privacy | Data sent externally |
| Offline | Requires connectivity |
| Quality | Better for general text |

For 22k+ products embedded in batch, local models avoid $2+ per full re-index and keep procurement data private.

### 13.2 Why ChromaDB over Pinecone/Weaviate

| Factor | ChromaDB |
|---|---|
| Deployment | Embedded (single file) |
| Config | Zero |
| Cost | Free |
| Latency | Under 5ms (local disk) |
| Scale limit | ~1M vectors |

| Factor | Pinecone / Weaviate |
|---|---|
| Deployment | Hosted or container |
| Config | API keys, cluster |
| Cost | Paid tiers |
| Latency | 20-100ms (network) |
| Scale limit | Billions |

22k products is well within ChromaDB's single-node limit — managed services would be overkill.

### 13.3 Why Hybrid LLM + Deterministic

| Approach | Strengths |
|---|---|
| LLM only | Handles ambiguity well |
| Deterministic only | Fast, free, predictable |
| Hybrid (chosen) | Fast initial + LLM enrichment |

| Approach | Weaknesses |
|---|---|
| LLM only | Slow, costly, hallucination |
| Deterministic only | Brittle with variations |
| Hybrid (chosen) | More complex architecture |

The system returns deterministic results immediately (user sees products in ~2s), then enriches with LLM analysis asynchronously. Users never wait for LLM; they get progressively better results.

### 13.4 Why 6 Equivalence Maps Instead of Embeddings for Spec Matching

Vector similarity alone cannot reliably distinguish "Copper" from "Aluminium" (they are both conductor materials → high semantic similarity). Equivalence maps provide exact categorical matching where needed:

- "Electrolytic Grade Copper" → copper (100% certainty, no hallucination)
- "PVC Type A (FR/FRLS/FRLSH)" → pvc (domain-specific knowledge encoded)
- "1.1kV" → 1100V category (numeric normalization + grouping)

Embeddings handle the **discovery** (find candidate products); equivalence maps handle the **verification** (confirm specs actually match).

### 13.5 Why Pre-Computed Column Enrichment

Running normalization + scoring on every query against 22k products is expensive. Pre-computing 10 enriched columns means:

- Matching reduces to column equality checks (O(1) per field)
- RFP_Matching_Tags enables fast substring search as a fallback
- Matching_Confidence and RFP_Fit_Score pre-rank products

---

## 14. Methods & Algorithms Summary

| Method | Algorithm |
|---|---|
| Semantic Search | HNSW nearest neighbor |
| Text Embedding | MiniLM-L6-v2 (384d) |
| Smart Trimming | Keyword-density scoring |
| Entity Extraction | LLM + regex fallback |
| Semantic Matching | Category lookup (maps) |
| Numeric Matching | Tolerance bands (10/20%) |
| Weighted Scoring | 4-tier category weights |
| Confidence Scoring | 5-factor weighted avg |
| Gap Analysis | Missing/insufficient class |
| Failure Detection | 5 hard safety rules |
| Standard Equivalence | 16-group + bridges |
| Linear Regression | Least squares (scratch) |
| Naive Bayes | Gaussian class features |
| Moving Averages | SMA, EMA, WMA |
| LRU Caching | OrderedDict + TTL + mem |
| Fuzzy Matching | SequenceMatcher ratio |

Where used:

- Semantic Search — ChromaDB product/requirement matching
- Text Embedding — Product text to 384d vectors
- Smart Trimming — LLM context window optimization
- Entity Extraction — RFP requirement parsing
- Semantic Matching — Spec equivalence (material, insulation, voltage)
- Numeric Matching — Conductor size, voltage, current rating
- Weighted Scoring — Product match ranking
- Confidence Scoring — Match result trustworthiness
- Gap Analysis — Identifying product shortcomings
- Failure Detection — Safety-critical disqualification
- Standard Equivalence — IS / IEC / BS cross-referencing
- Linear Regression — Price trends, processing time prediction
- Naive Bayes — Bid win probability
- Moving Averages — Time-series trend analysis
- LRU Caching — Embedding cache to avoid recomputation
- Fuzzy Matching — Approximate text matching

---

## 15. Data Flow Diagram

```
OEM CSVs (22k+)         DataLoader (ETL)         Pandas DataFrame
wires_cables_data/  ───→ Field mapping      ───→  (in-memory)
5 OEMs + Moglix         Type conversion              │
                        Validation                    │
                                                      ├──→ ChromaDB (vector index)
                                                      │
generate_optimizations.py ───→ Enriched CSVs ─────────┘
  10 new columns               *_optimized_*.csv
  Matching tags                Normalized cols
  Confidence score             Pre-scored

User-Added Products ───→ user_catalog.json (thread-safe, atomic)

RFP PDF Text ───→ NLP Pipeline ───→ Structured Requirements + Match Results
(post-extraction)    Smart trim         → analysis_history.json
                     LLM / Regex
                     Normalize
                     Embed
                     Match (10-step)
```
