# Backend Systems Engineer — HAKI FMCG 2.0

> Role perspective documentation for the **Backend Systems Engineer** covering the complete backend architecture — how communication works, data storage, user data handling, database choices, frontend-backend integration, performance engineering, and why this is an efficient backend system.

---

## 1. System Architecture Overview

HAKI FMCG 2.0 is a **Python-based procurement intelligence platform** built on **FastAPI** serving as the backbone for an AI-powered RFP (Request for Proposal) processing, product matching, bid generation, and vendor management system.

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (React 19 / Vite)                     │
│                         Port 3000 (dev proxy)                        │
└──────────────────────┬──────────────────────┬────────────────────────┘
                       │  HTTP REST (JSON)    │  SSE (EventSource)
                       ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   FastAPI REST API (rest_api.py)                      │
│                       Port 8000 / Uvicorn                            │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐           │
│  │  Auth    │  │  CORS    │  │  Rate    │  │  Request   │           │
│  │  (JWT)   │  │ Middleware│  │  Limiter │  │  Logger    │           │
│  └────┬─────┘  └──────────┘  └──────────┘  └────────────┘           │
│       ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    ~85 API Endpoints                          │    │
│  │  RFPs │ Bids │ Vendors │ Products │ Agents │ Pipeline │ etc. │    │
│  └───────┬───────────┬──────────┬───────────┬───────────────────┘    │
└──────────┼───────────┼──────────┼───────────┼────────────────────────┘
           │           │          │           │
    ┌──────▼──────┐ ┌──▼────┐ ┌──▼─────┐ ┌──▼──────────────┐
    │  Multi-Agent │ │  PDF  │ │Spec    │ │  Pipeline       │
    │  System      │ │Extract│ │Comparer│ │  Connector      │
    │  (LangChain) │ │       │ │        │ │  (8 pipelines)  │
    └──────┬───────┘ └───────┘ └────────┘ └─────────────────┘
           │
    ┌──────▼──────────────────────────────────────────────────────┐
    │                    DATA LAYER                                │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
    │  │ SQLite   │  │ ChromaDB │  │ JSON     │  │ MongoDB   │  │
    │  │ (Relat.) │  │ (Vector) │  │ (Files)  │  │ (Auth,opt)│  │
    │  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
    └─────────────────────────────────────────────────────────────┘
```

### 1.2 Backend Module Map

**REST API** — api/rest_api.py (5,118 lines). Single monolithic API server with all 85 endpoints.

**Database Layer** — database/. SQLAlchemy models, ChromaDB vectors, CRUD, data loaders, stores.

**Multi-Agent System** — agents/. Master → Sales + Technical + Pricing agents, LangChain LLM agents.

**PDF Extraction** — pdf_extraction/. PyPDF2/pdfplumber text extraction, hyperlink extraction, BOQ parsing.

**Spec Comparer** — spec_comparer/. 22k+ OEM product matching engine with weighted scoring.

**Pipeline Connector** — pipeline_connector.py. 8 end-to-end processing pipelines.

**RFP Processor** — rfp_processor/. CLI pipeline: scrape → download → extract → analyze.

**Performance** — performance/. Connection pooling, caching, rate limiting, load balancing, query optimization.

**Analytics** — analytics/. KPIs, trends, predictive analytics, A/B testing, alerts.

**Compliance** — compliance_and_standards/. Rule engine for IS/IEC/BIS standard validation.

**Audit Trail** — audit_and_trailing/. SHA-256 tamper-proof action logging.

**Vendor Management** — vendor_management/. Vendor profiles, ratings, communication, performance.

**RFP Responser** — rfp_responser/. Bid workflows, approvals, pricing, document generation.

**E-Procurement Portals** — e_procure_portals/. 5 simulated procurement portal Flask apps.

**Price Optimization** — price_optimization.py. Price tracking, history, volume discount tiers.

---

## 2. How Backend Handles Communication

### 2.1 Frontend ↔ Backend Communication

**REST API** — HTTP/JSON, bidirectional. All CRUD operations, data queries, form submissions.

**Server-Sent Events (SSE)** — HTTP streaming, server → client. RFP processing progress, system events, agent activity.

**File Upload** — HTTP multipart/form-data, client → server. RFP PDF uploads, batch document uploads.

**Proxy** — Vite dev proxy. Dev: localhost:3000/api → localhost:8000/api.

**REST API Contract:**
```
Base URL:   /api/v1
Auth:       Authorization: Bearer <JWT>
Content:    application/json (default), multipart/form-data (uploads)
Pagination: ?page=1&size=20
Response:   { "status": "success", "data": {...}, "total": N }
Errors:     { "detail": "message", "error_code": "CODE" }
```

**SSE Endpoints:**
- GET /api/v1/rfps/{rfp_id}/progress/stream — Real-time RFP processing progress
- GET /api/v1/events/stream — System-wide events with heartbeat (keeps connection alive)

SSE format:
```
event: rfp_progress
data: {"rfp_id": "abc", "stage": "matching", "progress": 65, "message": "Matching products..."}

event: heartbeat
data: {"timestamp": "2026-02-23T10:00:00Z"}
```

### 2.2 Internal Module Communication

**API → Agents** — Direct Python function calls. MasterAgent.run_full_workflow(rfp_data).

**API → PDF Extraction** — Direct function calls. PDFExtractionManager.extract(file_path).

**API → Spec Comparer** — Direct function calls. OEMProductDatabase.find_matches(requirements).

**API → Database** — SQLAlchemy ORM. session.query(Product).filter(...).

**API → ChromaDB** — ChromaDB client. collection.query(query_embeddings, n_results=10).

**API → Background Tasks** — FastAPI BackgroundTasks. LLM enrichment, linked-doc extraction run async.

**Master → Worker Agents** — Function calls + PriorityQueue / Redis pub-sub (optional).

**LangChain → LLM** — HTTP API (Groq). ChatGroq(model="llama-3.3-70b-versatile").

**Portal Scraper → Portals** — HTTP REST. requests.get("http://portal:port/api/rfps").

**Agent → Agent** — Shared AgentMessage protocol. 17 message types, 5 priority levels, typed payloads.

### 2.3 Inter-Agent Communication Protocol

The agents use a formal **message-passing protocol** defined in agents/shared/communication_protocol.py:

```python
@dataclass
class AgentMessage:
    id: str
    sender: AgentType       # MASTER, SALES, TECHNICAL, PRICING
    receiver: AgentType
    message_type: MessageType  # 17 types across 4 flows
    priority: MessagePriority  # CRITICAL, HIGH, NORMAL, LOW, BACKGROUND
    payload: dict
    context: MessageContext
    timestamp: datetime
```

**Message Types (17):**
- RFP Flow: RFP_SUBMISSION, RFP_SCAN_RESULT, RFP_SELECTED
- Technical Flow: TECH_ANALYSIS_REQUEST, TECH_SPEC_MATCH, TECH_RECOMMENDATION
- Pricing Flow: PRICING_REQUEST, PRICING_BREAKDOWN, PRICING_APPROVAL
- System Flow: STATUS_UPDATE, ERROR_REPORT, HEALTH_CHECK, ACKNOWLEDGMENT

**Communication Infrastructure** (agents/shared/inter_agent_communication.py):
- **In-memory queue** (default) or **Redis queue** (production)
- **Circuit breaker** — stops retrying after sustained failures
- **Dead letter queue** — undeliverable messages stored for inspection
- **Exponential backoff retry** — failed messages retried with increasing delay
- **Message acknowledgment** — sender knows when receiver processed
- **Priority queuing** — CRITICAL messages processed before NORMAL
- **Broadcast support** — messages to ALL_AGENTS
- **Message tracing** — full trace of message path for debugging

### 2.4 Background Processing

FastAPI BackgroundTasks are used for long-running operations that shouldn't block the HTTP response:

| Task | Trigger |
|---|---|
| LLM enrichment | POST /rfps/analyze |
| Linked doc download | POST /rfps/analyze |
| Portal scraping | POST /portals/scrape |
| Pipeline processing | POST /pipeline/run |

Polling endpoints:

- LLM enrichment — GET /rfps/analyze/{id}/enrichment
- Linked docs — GET /rfps/analyze/{id}/linked-docs
- Portal scrape — GET /portals/scrape/status
- Pipeline — GET /pipeline/runs/{id}/status + SSE

---

## 3. How Data Is Stored

### 3.1 Hybrid Storage Architecture

The system uses a **polyglot persistence** approach — each data type is stored in the format most suited to its access patterns:

| Storage | Technology |
|---|---|
| Relational | SQLite via SQLAlchemy |
| Vector | ChromaDB |
| Document | JSON files |
| Domain relational | SQLite (standalone) |
| User Auth | MongoDB / JSON fallback |
| In-Memory | Python dicts (runtime) |
| Cache | Redis / LRU in-memory |
| Files | Filesystem |

Locations:

- Relational — database/db_main/rfp_system.db (Products, RFPs, requirements, matches, bids, bid items, agent logs, audit trail, test services, OEMs, standards, certifications)
- Vector — database/db_vector/chroma.sqlite3 (Product embeddings, RFP requirement embeddings, agent knowledge, standards embeddings)
- Document — database/db_products/, db_pricing/, db_agents/, db_rfp/ (Product catalogs, pricing tables, agent conversations, workflow logs, compliance rules)
- Domain — database/db_vendors/, db_rfp/, db_audit/ (Vendor data, bid approvals, audit logs)
- User Auth — haki_fmcg.users collection / database/users.json (User accounts)
- In-Memory — Runtime only (RFP processing state, bid store, vendor cache, pipeline state, staging imports)
- Cache — Runtime (Embedding cache, query results, agent operation cache)
- Files — uploads/, RFPs/, pdf_extraction/output/ (Uploaded PDFs, extracted text, generated reports)

### 3.2 SQLite Configuration

```python
# database/db_engine.py — SQLite pragmas for performance
PRAGMA journal_mode = WAL      # Write-Ahead Logging — concurrent readers
PRAGMA cache_size = -64000     # 64MB page cache  
PRAGMA foreign_keys = ON       # Referential integrity enforced
PRAGMA temp_store = MEMORY     # Temp tables in RAM
```

**Why SQLite over PostgreSQL for this deployment:**
- Zero configuration — no separate DB server process
- Single-file databases — easy to backup, version, distribute
- WAL mode enables concurrent reads during writes
- Sufficient throughput for single-server procurement platform
- PostgreSQL support exists (db_engine.py has QueuePool config) for scaling up

### 3.3 JSON File Storage Layout

```
database/
├── db_products/
│   ├── oem_products.json          # 22,000+ OEM wire/cable products
│   ├── oem_datasheets.json        # Product datasheet metadata
│   ├── user_catalog.json          # User-added products (thread-safe, atomic writes)
│   └── product_catalog.json       # Combined catalog
├── db_pricing/
│   ├── product_prices.json        # Unit prices per product
│   ├── service_prices.json        # Test/certification service prices
│   └── compliance_rules.json      # Compliance rule definitions
├── db_agents/
│   ├── conversation_history.json  # Agent chat conversation records
│   └── workflow_logs.json         # Workflow execution logs
├── db_rfp/
│   ├── analysis_history.json      # Saved RFP analysis results
│   ├── bids.db                    # Bid records (SQLite)
│   ├── bid_approvals.db           # Bid approval workflows (SQLite)
│   └── rfp_terms_database_100k_new.json  # 100k+ RFP terms for matching
├── db_vendors/
│   ├── vendors.db                 # Vendor profiles (SQLite)
│   ├── vendor_ratings.db          # Vendor rating history
│   ├── vendor_performance.db      # Performance metrics
│   └── vendor_communications.db   # Communication logs
├── db_audit/
│   ├── audit.db                   # Tamper-proof audit trail (SQLite)
│   └── audit_trail_backup.db      # Backup audit data
└── db_vector/
    └── chroma.sqlite3             # ChromaDB vector store
```

### 3.4 Thread-Safe File Operations

Critical JSON stores (catalog_store.py, analysis_store.py) use:
- threading.RLock() for thread-safe reads/writes
- Atomic writes via temp file + os.replace() to prevent corruption
- In-memory index caches for fast lookups without re-reading files

---

## 4. ChromaDB — Vector Database (Core to the System)

### 4.1 Why ChromaDB

ChromaDB is the **primary intelligence engine** of the platform. It enables:

1. **Semantic product matching** — RFP requirements described in natural language are matched against product descriptions using vector similarity, not just keyword matching
2. **Fuzzy specification matching** — "1100V AC rated XLPE insulated cable" matches "1.1kV cross-linked polyethylene cable" through embedding similarity
3. **Historical learning** — Agent knowledge from past analyses is stored and retrieved for similar future queries
4. **Standards matching** — Technical standards (IS/IEC/BIS) are semantically searchable

### 4.2 ChromaDB Setup

```python
# database/chromadb_setup.py
chroma_client = chromadb.PersistentClient(path="database/db_vector/")
embedding_function = DefaultEmbeddingFunction()  # Built-in model
```

### 4.3 Collections (4)

**products** — Semantic product search

- Docs: Product descriptions + specs concatenated
- Filters: sku, oem, category, conductor_material, insulation_type
- Purpose: Find products matching RFP requirement text

**rfp_requirements** — Knowledge reuse

- Docs: RFP requirement original text
- Filters: rfp_id, requirement_number, product_type
- Purpose: Find similar past requirements

**agent_knowledge** — Agent learning

- Docs: Historical agent analysis responses
- Filters: agent_type, action_type, confidence
- Purpose: Reuse past agent insights

**standards** — Standards matching

- Docs: Technical standard descriptions
- Filters: standard_code, issuing_body, category
- Purpose: Match RFP standards against known standards

### 4.4 Operations

```python
# Semantic search with metadata filtering
results = search_products(
    query_text="4 core 240 sqmm XLPE cable 33kV",
    n_results=10,
    where={"category": "power_cables"},  # Optional metadata filter
    where_document={"$contains": "armoured"}  # Optional text filter
)
# Returns: documents, distances, metadatas, ids
```

**Batch operations** for bulk product ingestion:
```python
add_products(products_list)  # Upserts into ChromaDB with auto-generated IDs
```

### 4.5 Advanced Vector Embeddings

Beyond ChromaDB's built-in embeddings, database/vector_embeddings.py (1,781 lines) provides:

**Models** — all-MiniLM-L6-v2 (384d, default), all-MiniLM-L12-v2, all-mpnet-base-v2 (768d), multi-qa-distilbert-cos-v1, paraphrase-MiniLM-L6-v2.

**Search modes** — Semantic, Keyword, Hybrid (combined).

**Caching** — LRU embedding cache with TTL — avoids re-computing embeddings for repeated queries.

**Batch processing** — Chunk-based embedding generation for 22k+ products.

**Lazy loading** — Model loaded on first use, not at startup.

---

## 5. What User Data Is Stored

### 5.1 User Account Data

| Field | Purpose |
|---|---|
| user_id (UUID/int) | Unique identifier |
| username (string) | Login credential |
| password_hash (SHA-256) | Authentication (never plaintext) |
| email (string) | Contact, notifications |
| full_name (string) | Display name |
| role (enum) | RBAC: admin, manager, analyst, viewer |
| permissions (list) | Computed from role |
| created_at (datetime) | Account age |
| is_active (boolean) | Account enabled/disabled |

Storage: MongoDB (haki_fmcg.users) → JSON file (database/users.json) → In-memory dict fallback.

### 5.2 User Activity Data

| Data | Storage |
|---|---|
| Audit trail | db_audit/audit.db |
| RFP submissions | db_main/rfp_system.db |
| Agent conversations | db_agents/conversation_history.json |
| Saved analyses | db_rfp/analysis_history.json |
| Company profiles | In-memory + persist |

Why stored:

- Audit trail — Every CRUD action logged with user_id, IP address, old/new values, timestamp
- RFP submissions — Which user uploaded/created each RFP
- Agent conversations — Chat history with AI agents
- Saved analyses — User-saved RFP analysis results
- Company profiles — Company info for bid generation (name, address, GST, etc.)

### 5.3 What Is NOT Stored

- **Plain-text passwords** — Only SHA-256 hashes
- **JWT tokens server-side** — Stateless JWT validation (tokens stored client-side only)
- **Browser fingerprints** — No device tracking
- **Personal analytics** — No individual behavior tracking beyond audit trail

---

## 6. SQLAlchemy Data Models (What's in the Relational DB)

### 6.1 Core Models

```
┌──────────┐     ┌──────────────────┐     ┌───────────────┐
│   OEM    │────→│    Product       │←────│  ProductMatch │
│          │  1:N│                  │  1:N │               │
│ code     │     │ sku, name       │      │ overall_score │
│ name     │     │ category        │      │ spec_score    │
│ country  │     │ specifications  │      │ price_score   │
│ gstin    │     │ unit_price      │      │ rank          │
│ rating   │     │ conductor_size  │      │ is_selected   │
└──────────┘     │ voltage_rating  │      └───────┬───────┘
                 │ current_rating  │              │
                 │ insulation_type │              │
                 └────────┬────────┘     ┌───────▼────────┐
                          │              │ RFPRequirement  │
                 ┌────────▼────────┐     │                 │
                 │ Standard (M2M)  │     │ original_text   │
                 │ Certification   │     │ specifications  │
                 │  (M2M)         │     │ quantity        │
                 └─────────────────┘     │ match_confidence│
                                         └───────┬────────┘
                                                  │
                                         ┌───────▼────────┐
                                         │      RFP       │
                                         │                 │
                                         │ title           │
                                         │ issuing_auth.   │
                                         │ due_date        │
                                         │ estimated_value │
                                         │ status (9 enum) │
                                         │ raw_text        │
                                         │ extracted_data  │
                                         └───────┬────────┘
                                                  │
                                         ┌───────▼────────┐
                                         │      Bid       │
                                         │                 │
                                         │ subtotal        │
                                         │ tax (18% GST)   │
                                         │ grand_total     │
                                         │ status (7 enum) │
                                         │ delivery_terms  │
                                         │ warranty_terms  │
                                         └───────┬────────┘
                                                  │
                                         ┌───────▼────────┐
                                         │    BidItem     │
                                         │                 │
                                         │ product_id (FK) │
                                         │ quantity        │
                                         │ unit_price      │
                                         │ discount_%      │
                                         │ total_price     │
                                         │ spec_match_%    │
                                         └────────────────┘
```

### 6.2 Supporting Models

**AgentLog** — Table: agent_logs. Fields: agent_type, action, message, duration_ms, tokens_used, error info. Purpose: Agent execution audit.

**AuditTrail** — Table: audit_trail. Fields: action, entity_type, user_id, ip_address, old_values, new_values. Purpose: Tamper-proof change log.

**TestService** — Table: test_services. Fields: name, price, standard, turnaround_days. Purpose: Lab testing/certification pricing.

### 6.3 Status Enums

**RFPStatus** — draft, uploaded, extracting, extracted, analyzing, matched, completed, failed, cancelled. Used in RFP lifecycle.

**BidStatus** — draft, in_progress, submitted, under_review, approved, rejected, awarded. Used in bid workflow.

**MatchStatus** — pending, matched, partial, no_match, manual. Used in product match results.

**ProductStatus** — active, discontinued, out_of_stock. Used in product availability.

**AgentType** — master, sales, technical, pricing. Used in agent identification.

---

## 7. Authentication & Authorization

### 7.1 JWT Authentication Flow

```
Client                          Server
  │                                │
  ├─POST /auth/login──────────────→│  Verify credentials
  │  {username, password}          │  SHA-256 hash comparison
  │                                │
  │←──────────────────────────────┤  Generate JWT (HS256)
  │  {access_token, refresh_token} │  access: 30min expiry
  │                                │  refresh: 7 day expiry
  │                                │
  ├─GET /rfps ─────────────────────→│  Validate JWT
  │  Authorization: Bearer <token> │  Extract user_id, role
  │                                │  Check permissions
  │                                │
  │←── 200 OK ────────────────────┤  Return data
  │                                │
  ├─POST /auth/refresh─────────────→│  Validate refresh token
  │  {refresh_token}               │  Issue new access token
  │←──────────────────────────────┤  {access_token}
```

### 7.2 RBAC (Role-Based Access Control)

```python
ROLE_PERMISSIONS = {
    "admin":   ["rfp:create", "rfp:read", "rfp:update", "rfp:delete",
                "config:read", "config:write", "user:manage",
                "analytics:read", "analytics:write", "webhook:manage",
                "batch:execute", "file:upload"],
    "manager": ["rfp:create", "rfp:read", "rfp:update",
                "config:read", "analytics:read",
                "batch:execute", "file:upload"],
    "analyst": ["rfp:create", "rfp:read",
                "config:read", "analytics:read", "file:upload"],
    "viewer":  ["rfp:read", "config:read", "analytics:read"],
}
```

**Permission enforcement**: Every protected endpoint uses get_current_user() dependency (JWT decode) + require_permission(perm) decorator.

### 7.3 Demo Accounts (Auto-Seeded)

| Username | Role |
|---|---|
| admin (admin123) | admin |
| user (user1234) | admin |

Seeded on startup via seed_demo_accounts() — checks if already exist before creating.

---

## 8. The Multi-Agent System

### 8.1 Agent Architecture

```
                    ┌─────────────────────┐
                    │   Master Agent      │  ← Tier 1 (Orchestrator)
                    │   (Mediator)        │
                    │                     │
                    │  State Machine:     │
                    │  IDLE → SCANNING →  │
                    │  SELECTED → TECH →  │
                    │  PRICING → DONE     │
                    └──────┬──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌─────────────┐ ┌──────────┐ ┌──────────┐
     │ Sales Agent │ │Technical │ │ Pricing  │  ← Tier 2 (Workers)
     │             │ │  Agent   │ │  Agent   │
     │ • Scan RFPs │ │ • Match  │ │ • Price  │
     │ • Prioritize│ │   specs  │ │   lookup │
     │ • Select    │ │ • Score  │ │ • Test   │
     │             │ │ • Rank   │ │   costs  │
     └─────────────┘ └──────────┘ └──────────┘
```

### 8.2 Deterministic vs. LLM Agents

The system has **two parallel agent implementations**:

| Aspect | Deterministic |
|---|---|
| Location | agents/sales_agent/, etc. |
| How | Rule-based, lookup tables |
| Speed | Milliseconds |
| Accuracy | High for structured data |
| Fallback | Always available |
| Cost | Free (CPU only) |

| Aspect | LangChain (LLM) |
|---|---|
| Location | agents/langchain_agent/ |
| How | LLM via Groq API |
| Speed | 30-45 seconds |
| Accuracy | Better for unstructured text |
| Fallback | Falls back to deterministic |
| Cost | API usage costs |

**LangChain agent execution**:
```python
# Parallel execution of all 3 LLM agents
with ThreadPoolExecutor(max_workers=3) as executor:
    sales_future = executor.submit(lc_sales.analyze, rfp_text)
    tech_future = executor.submit(lc_technical.analyze, rfp_text, products)
    pricing_future = executor.submit(lc_pricing.analyze, rfp_text, products)
```

### 8.3 Workflow Orchestration Engine

agents/shared/workflow_orchestration.py (2,797 lines) provides a complete workflow engine:

**States (10)** — PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED, WAITING_APPROVAL, SKIPPED, ROLLED_BACK, TIMED_OUT.

**Checkpoints** — Save/restore workflow state at any step.

**Rollback** — Undo completed steps on failure.

**Parallel steps** — ThreadPoolExecutor for concurrent step execution.

**Human-in-the-loop** — Approval gates that pause workflow until approved.

**Conditional branching** — Steps can be skipped based on conditions.

**Timeout handling** — Per-step and overall workflow timeouts.

**Notifications** — Observer pattern for logging, metrics, external alerts.

---

## 9. The Pipeline System

### 9.1 Eight End-to-End Pipelines

Defined in pipeline_connector.py, the 8 pipelines cover the complete procurement lifecycle:

| # | Pipeline | Purpose |
|---|---|---|
| 1 | RFP Intake | Ingest and structure raw RFPs |
| 2 | Product Matching | Match reqs to 22k+ OEM products |
| 3 | Pricing & Bid | Create complete bid with financials |
| 4 | Vendor Management | Evaluate and rank vendors |
| 5 | Agent Orchestration | Multi-agent RFP analysis |
| 6 | Performance Optimization | Self-tuning performance |
| 7 | Compliance & Audit | Regulatory compliance |
| 8 | Analytics & Reporting | Business intelligence |

Pipeline stages:

- RFP Intake — Upload → Extract → Parse → Validate
- Product Matching — Embed → Search → Score → Rank → Select
- Pricing & Bid — Price Lookup → Test Costs → Discount → Tax → Total → Generate Doc
- Vendor Management — Profile → Rate → Rank → Compare → Select
- Agent Orchestration — Dispatch → Sales → Technical → Pricing → Consolidate
- Performance Optimization — Profile → Analyze → Recommend → Apply
- Compliance & Audit — Check Standards → Validate → Log → Report
- Analytics & Reporting — Collect → Aggregate → Analyze → Visualize → Export

### 9.2 Pipeline Context Object

```python
@dataclass
class PipelineContext:
    pipeline_id: str
    stages: List[PipelineStage]  # 15 possible stages
    current_stage: PipelineStage
    status: PipelineStatus
    input_data: dict
    stage_results: Dict[PipelineStage, StageResult]
    metadata: dict
    started_at: datetime
    completed_at: Optional[datetime]
```

Each pipeline stage receives the context, performs its work, writes results to stage_results, and passes context to the next stage.

### 9.3 RFP Analysis Pipeline (The Core Feature)

The crown jewel endpoint POST /api/v1/rfps/analyze:

```
PDF Upload
    │
    ▼
┌─────────────────────┐
│ 1. PDF Extraction   │  PyPDF2 / pdfplumber
│    (text + tables)  │  → raw_text
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 2. Requirement      │  Regex + NLP parsing
│    Parsing          │  → structured requirements[]
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 3. Product Matching │  ChromaDB semantic search
│    (22k+ OEM DB)    │  + spec-level scoring
│                     │  → Top 3 matches per req
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│ 4. Multi-Agent Analysis (parallel)          │
│   ┌─────────┐ ┌──────────┐ ┌──────────┐   │
│   │ Sales   │ │Technical │ │ Pricing  │   │
│   │ Agent   │ │ Agent    │ │ Agent    │   │
│   └────┬────┘ └────┬─────┘ └────┬─────┘   │
│        └────────────┼────────────┘          │
│                     ▼                       │
│              Master Agent                   │
│           (consolidation)                   │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────┐
│ 5. Response         │  BOQ, comparisons, rankings,
│    Assembly         │  engineering calcs, budget,
│                     │  recommendations
└─────────┬───────────┘
          │
          ▼ (background)
┌─────────────────────┐  ┌─────────────────────┐
│ 6. LLM Enrichment  │  │ 7. Linked Doc       │
│    (Groq/LangChain)│  │    Extraction        │
│    Match analysis   │  │    Hyperlinks → PDFs │
│    Pricing insights │  │    BOQ parsing       │
└─────────────────────┘  └─────────────────────┘
```

---

## 10. Performance Engineering

### 10.1 Performance Module Suite

The performance/ directory contains a comprehensive performance engineering toolkit:

**connection_pool.py** — DB/Redis connection pooling. Object Pool pattern — pre-allocate connections, health checks, auto-reconnect.

**rate_limiter.py** — Request rate limiting. Token Bucket (1000/min, 10000/hr) + Sliding Window.

**embedding_cache.py** — Vector embedding cache. LRU + TTL — avoids re-computing embeddings, memory-bounded.

**load_balancer.py** — Request distribution. 6 strategies: Round Robin, Weighted RR, Least Connections, Random, IP Hash, Least Response Time.

**redis_cache.py** — Redis caching layer. Singleton cache with compression, TTL, hash/sorted-set ops.

**batch_processor.py** — Chunked batch operations. Generic batch with retries, progress tracking, parallel execution.

**query_optimizer.py** — SQL query analysis. Index recommendations, N+1 detection, slow query identification.

**optimizer.py** — Auto performance advisor. 8 categories of recommendations with priority/effort scoring.

**parallel_matcher.py** — Parallel product matching. ThreadPoolExecutor for concurrent spec matching.

**async_ops.py** — Async operation executor. Non-blocking I/O for API calls, file reads.

**profiler.py** — Code profiling. Function-level timing, memory tracking.

**resource_monitor.py** — System resource monitoring. CPU, memory, disk, network utilization.

**bottleneck_detector.py** — Performance bottleneck detection. Automatic identification of slow paths.

**auto_scaler.py** — Auto-scaling logic. Threshold-based resource scaling recommendations.

**load_tester.py** — Load testing. Automated load/stress testing framework.

**stress_tester.py** — Stress testing. Extreme load scenarios.

### 10.2 Cross-Cutting Performance Decorators

```python
from performance.integration import cached, profiled, with_timeout

@cached(ttl=300)          # Cache result for 5 minutes
@profiled                 # Log execution time
@with_timeout(30)         # Kill if exceeds 30 seconds
def match_products(rfp_requirements):
    ...
```

These decorators are applied throughout the agent and pipeline systems. They use **graceful degradation** — if the performance module isn't available, they become no-ops:

```python
try:
    from performance.integration import cached, profiled, with_timeout
except ImportError:
    def cached(**kw): return lambda f: f      # No-op
    def profiled(f): return f                  # No-op
    def with_timeout(t): return lambda f: f    # No-op
```

### 10.3 API-Level Performance

**Rate Limiting** — Token bucket per IP: 1000 requests/min, 10000/hr. 429 Too Many Requests with Retry-After header.

**Request Timing** — Middleware adds X-Process-Time header to every response.

**Request Tracking** — Every request gets a unique X-Request-ID for tracing.

**Connection Pooling** — SQLAlchemy QueuePool (PostgreSQL mode): pool_size=5, max_overflow=10, pool_recycle=3600.

**Lazy Loading** — OEM product database (22k+ rows) loaded on first access, not at startup.

**Code Splitting** — Large modules imported conditionally (try/except ImportError).

---

## 11. Why This Is an Efficient Backend System

### 11.1 Architectural Efficiency

**Polyglot Persistence** — SQLite (relational), ChromaDB (vectors), JSON (documents), Redis (cache). Each data type stored optimally for its access pattern.

**Zero-Config Databases** — SQLite + ChromaDB + JSON files. No external DB servers to configure, deploy, or maintain.

**Stateless API** — JWT auth (no server-side sessions). Horizontally scalable — any instance can handle any request.

**Background Processing** — FastAPI BackgroundTasks for LLM enrichment, linked-doc extraction. User gets immediate response; heavy processing continues async.

**Lazy Loading** — 22k+ product DB loaded on first access. Fast startup — sub-second cold start.

**Graceful Degradation** — Every module uses try/except ImportError. System works with reduced features if optional dependencies are missing.

### 11.2 Data Processing Efficiency

**Vector Search** — ChromaDB product matching. O(log n) approximate nearest neighbor vs O(n) brute-force string matching on 22k products.

**Embedding Cache** — performance/embedding_cache.py. Avoid re-computing 384-dim vectors for repeated queries.

**Batch Processing** — Product ingestion, RFP batch uploads. Chunk-based with parallelism — 10x faster than sequential.

**Parallel Agent Execution** — ThreadPoolExecutor(max_workers=3). Sales + Technical + Pricing agents run simultaneously.

**WAL Journal Mode** — SQLite pragma. Readers don't block writers — concurrent access without locks.

**In-Memory Caching** — RFP store, bid store, vendor store. Hot data served from RAM — no disk I/O for active items.

**Atomic File Writes** — temp file + os.replace(). No data corruption during write — crash-safe.

### 11.3 API Efficiency

**Pagination** — ?page=1&size=20 on all list endpoints. Bounded response size — no accidental 22k product dumps.

**Selective filtering** — Query params on every list endpoint. Backend filters — only matching data crosses the network.

**SSE over Polling** — EventSource for progress/events. No wasted requests — server pushes only when there's an update.

**Streaming responses** — StreamingResponse for SSE. Immediate partial updates vs. waiting for complete processing.

**Token refresh queue** — Concurrent 401s queued; single refresh. Prevents refresh token stampede under concurrent requests.

**CORS wildcard (dev)** — allow_origins=["*"]. Zero config during development.

### 11.4 Agent System Efficiency

**Deterministic-first** — Rule-based matching runs in milliseconds. LLM called only for enrichment (optional, background).

**LLM as enrichment, not dependency** — Initial response is deterministic; LLM polishes async. User gets results in ~2s, enriched results arrive later.

**Smart text trimming** — Keyword-scored paragraph selection for LLM context. Fits relevant content within LLM context window — no truncation.

**Message priority queue** — CRITICAL messages processed before NORMAL. Time-sensitive operations (error handling) aren't stuck behind routine messages.

**Circuit breaker** — Stops retrying after sustained failures. Prevents cascade failures when a service is down.

### 11.5 Scalability Path

The system is designed to scale from single-server to distributed:

| Current | Scale-Up Path |
|---|---|
| SQLite (WAL) | PostgreSQL (supported) |
| In-memory queue | Redis queue (implemented) |
| In-memory cache | Redis cache (implemented) |
| ThreadPoolExecutor | Celery task queue |
| Single Uvicorn | Gunicorn + Nginx |
| Local ChromaDB | ChromaDB cloud / Pinecone |
| JSON file stores | PostgreSQL JSONB / MongoDB |

---

## 12. PDF Extraction Pipeline

### 12.1 Multi-Layered Extraction

```
PDF File
    │
    ├──→ PyPDF2 (fast, basic text)
    ├──→ pdfplumber (tables + structured text)
    ├──→ PyMuPDF/fitz (hyperlink extraction)
    │
    ├──→ Hyperlink Extractor
    │      │
    │      ├──→ Download linked PDFs
    │      ├──→ Parse linked Excel/CSV (BOQ)
    │      └──→ Extract BOQ items (product, qty, unit)
    │
    └──→ RFP Terms Matcher
           │
           └──→ Match against 100k+ term database
                (rfp_terms_database_100k_new.json)
```

### 12.2 File Organization

Each uploaded PDF gets a unique extraction directory:
```
pdf_extraction/output/{unique_id}/
├── pdf/           # Original uploaded PDF
├── metadata/      # Extraction metadata JSON
└── extracted/     # Extracted text, tables, linked docs
```

---

## 13. Compliance & Audit System

### 13.1 Compliance Rule Engine

compliance_and_standards/compliance_checker.py:

```python
@dataclass
class ComplianceRule:
    id: str
    name: str
    standard: str           # IS 3961, IEC 60364, BIS
    condition: Callable     # Python function: (product) → bool
    weight: float           # Importance (0-1)
    severity: RiskLevel     # CRITICAL, HIGH, MEDIUM, LOW
    is_mandatory: bool      # Hard fail or soft warning
```

Pre-loaded rules validate:
- Voltage ratings against IS 3961 / IEC 60364-5-52
- Conductor material compliance
- Insulation type ratings
- Temperature derating factors
- Flame retardance requirements

### 13.2 Tamper-Proof Audit Trail

audit_and_trailing/audit_trail.py:

**Action types (14)** — CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, IMPORT, APPROVE, REJECT, SUBMIT, CANCEL, CONFIGURE, ALERT.

**Entity types (10)** — RFP, BID, PRODUCT, VENDOR, USER, AGENT, PIPELINE, WEBHOOK, CONFIG, SYSTEM.

**Integrity** — SHA-256 hash of entry content as entry ID for tamper detection.

**Data captured** — user_id, user_name, IP address, old_values (JSON), new_values (JSON), description.

**Storage** — SQLite (db_audit/audit.db) with backup (audit_trail_backup.db).

---

## 14. E-Procurement Portal Simulation

### 14.1 Architecture

5 simulated procurement portals for testing the scraper pipeline:

| Portal | Port |
|---|---|
| gem_portal | 5001 |
| cppp_portal | 5002 |
| state_portal | 5003 |
| defence_portal | 5004 |
| railways_portal | 5005 |

Portal themes:

- GEM — Blue (#1a73e8), Government E-Marketplace
- CPPP — Dark Blue (#003876), Central Public Procurement
- State — Green (#2e7d32), State Procurement
- Defence — Olive (#556b2f), Defence Procurement
- Railways — Red (#b71c1c), Railway Procurement

### 14.2 How It Works

1. portal_config.py discovers all PDFs in RFPs/ directory
2. Round-robin distributes PDFs equally across 5 portals
3. Each portal is a Flask app serving assigned PDFs with deterministic fake metadata (title, department, deadline, EMD — generated from filename MD5 hash)
4. The scraper (rfp_processor/scraper.py) hits all 5 portals' /api/rfps endpoints in parallel, downloads PDFs, and creates a manifest

---

## 15. Spec Comparer Engine

### 15.1 OEM Product Database

- **22,000+ wire/cable products** loaded from CSV files in wires_cables_data/
- Loaded into a **pandas DataFrame** for fast filtering and matching
- Products from OEMs: Havells, Polycab, KEI, Finolex, RR Kabel, etc.
- Specifications: conductor material, size (sqmm), cores, voltage rating, insulation type, current rating, temperature rating, armour type

### 15.2 Weighted Scoring Algorithm

```python
SCORING_WEIGHTS = {
    "Type_of_Cable": 0.20,
    "Conductor_Material": 0.15,
    "Conductor_Size_sqmm": 0.15,
    "Number_of_Cores": 0.10,
    "Voltage_Rating": 0.15,
    "Insulation_Type": 0.10,
    "Current_Rating_Amps": 0.10,
    "Armour_Type": 0.05,
}
```

Each RFP requirement is scored against all products; top 3 matches returned per requirement.

### 15.3 Specification Normalization

The Technical Agent normalizes varied specification formats:

| Raw Value | Normalized |
|---|---|
| "Copper", "CU", "ETP Copper" | copper |
| "XLPE", "Cross-linked PE" | xlpe |
| "1100V", "1.1kV", "1100V AC" | 1100 |

Mapping: CONDUCTOR_MATERIAL_MAP, INSULATION_TYPE_MAP, and value extraction + unit conversion.

---

## 16. API Endpoint Catalog (Complete)

### System (4 endpoints)

- GET /health — Health check (no auth)
- GET /api/v1/health — Versioned health check (no auth)
- GET /api/v1/version — API version info (no auth)
- GET /api/v1/rate-limit/status — Rate limit stats (auth required)

### Authentication (6 endpoints)

- POST /api/v1/auth/token — OAuth2 form login
- POST /api/v1/auth/login — JSON login
- POST /api/v1/auth/refresh — Token refresh
- POST /api/v1/auth/logout — Revoke token (auth required)
- POST /api/v1/auth/register — Create account
- GET /api/v1/auth/me — Current user profile (auth required)

### RFPs (14 endpoints)

- POST /api/v1/rfps — Create RFP
- GET /api/v1/rfps — List RFPs (paginated)
- GET /api/v1/rfps/{id} — Get RFP
- PUT /api/v1/rfps/{id} — Update RFP
- DELETE /api/v1/rfps/{id} — Delete RFP (admin)
- GET /api/v1/rfps/{id}/status — Processing status
- GET /api/v1/rfps/{id}/results — Processing results
- GET /api/v1/rfps/{id}/requirements — RFP requirements
- POST /api/v1/rfps/{id}/process — Start processing
- POST /api/v1/rfps/{id}/cancel — Cancel processing
- POST /api/v1/rfps/upload — Upload PDF
- POST /api/v1/rfps/analyze — **Full analysis pipeline**
- GET /api/v1/rfps/analyze/{id}/linked-docs — Linked doc status
- GET /api/v1/rfps/analyze/{id}/enrichment — LLM enrichment status

### Pipeline (8 endpoints)

- POST /api/v1/pipeline/run — Run pipeline (text)
- POST /api/v1/pipeline/upload — Run pipeline (PDF)
- POST /api/v1/pipeline/start — Start pipeline
- GET /api/v1/pipeline/runs — List runs
- GET /api/v1/pipeline/runs/{id} — Run details
- GET /api/v1/pipeline/runs/{id}/status — Run status
- POST /api/v1/pipeline/runs/{id}/cancel — Cancel run
- POST /api/v1/pipeline/runs/{id}/retry — Retry failed run

### Products (12 endpoints)

- GET /api/v1/products — List products
- POST /api/v1/products/search — Semantic search
- GET /api/v1/products/categories — Category list
- GET /api/v1/products/catalog — Full OEM catalog
- GET /api/v1/products/catalog/stats — Catalog statistics
- POST /api/v1/products/add — Add product
- POST /api/v1/products/import-catalog — Import from PDF/URL
- POST /api/v1/products/import-catalog/confirm — Confirm import
- DELETE /api/v1/products/import-catalog/{code} — Delete imported
- GET /api/v1/products/import-history — Import history
- GET /api/v1/products/{id} — Get product
- POST /api/v1/products/compare — Compare products

### Vendors (5 endpoints)

- GET /api/v1/vendors — List vendors
- GET /api/v1/vendors/rankings — Vendor rankings
- GET /api/v1/vendors/{id} — Get vendor
- POST /api/v1/vendors — Create vendor
- PUT /api/v1/vendors/{id} — Update vendor

### Bids (9 endpoints)

- GET /api/v1/bids — List bids
- GET /api/v1/bids/{id} — Get bid
- POST /api/v1/bids — Create bid
- PUT /api/v1/bids/{id} — Update bid
- DELETE /api/v1/bids/{id} — Delete bid
- POST /api/v1/bids/{id}/items — Add bid item
- POST /api/v1/bids/{id}/submit — Submit bid
- POST /api/v1/bids/{id}/approval/request — Request approval
- POST /api/v1/bids/{id}/approval/{action} — Approve/reject

### Company Profiles & Bid Documents (11 endpoints)

- GET /api/v1/company-profiles — List profiles
- GET /api/v1/company-profiles/{id} — Get profile
- POST /api/v1/company-profiles — Create profile
- PUT /api/v1/company-profiles/{id} — Update profile
- DELETE /api/v1/company-profiles/{id} — Delete profile
- POST /api/v1/company-profiles/{id}/default — Set default
- POST /api/v1/bid-documents/generate — Generate bid doc
- GET /api/v1/bid-documents — List bid docs
- GET /api/v1/bid-documents/{id} — Get bid doc
- POST /api/v1/bid-documents/{id}/send — Send via email
- GET /api/v1/bid-documents/{id}/pdf — Download PDF

### Saved Analyses (4 endpoints)

- POST /api/v1/saved-analyses — Save analysis
- GET /api/v1/saved-analyses — List analyses
- GET /api/v1/saved-analyses/{id} — Get analysis
- DELETE /api/v1/saved-analyses/{id} — Delete analysis

### Portals (4 endpoints)

- POST /api/v1/portals/scrape — Trigger scrape
- GET /api/v1/portals/scrape/status — Scrape status
- GET /api/v1/portals/rfps — List scraped RFPs
- GET /api/v1/portals/rfps/{id}/pdf — Serve scraped PDF

### Analytics (9 endpoints)

- GET /api/v1/analytics/overview — Summary stats
- GET /api/v1/analytics/rfps — RFP analytics
- GET /api/v1/analytics/performance — System performance
- POST /api/v1/analytics/query — Custom query
- GET /api/v1/analytics/export — Export (JSON/CSV)
- GET /api/v1/analytics/dashboard — Dashboard stats
- GET /api/v1/analytics/bids — Bid analytics
- GET /api/v1/analytics/activity — Activity feed
- GET /api/v1/analytics/system-health — System health

### Config (4 endpoints)

- GET /api/v1/config — All config
- GET /api/v1/config/{key} — Get config
- PUT /api/v1/config/{key} — Update config (admin)
- POST /api/v1/config/reset — Reset to defaults (admin)

### Webhooks (6 endpoints)

- POST /api/v1/webhooks — Register webhook (admin)
- GET /api/v1/webhooks — List webhooks (admin)
- GET /api/v1/webhooks/{id} — Get webhook (admin)
- DELETE /api/v1/webhooks/{id} — Delete webhook (admin)
- PATCH /api/v1/webhooks/{id} — Toggle active (admin)
- GET /api/v1/webhooks/{id}/logs — Delivery logs (admin)

### Batch & Upload (4 endpoints)

- POST /api/v1/batch/rfps — Batch RFP submit
- GET /api/v1/batch/{id} — Batch status
- POST /api/v1/upload/rfp-document — Upload document (50MB max)
- POST /api/v1/upload/batch — Batch file upload

### Agents (5 endpoints)

- GET /api/v1/agents/status — All agent statuses
- GET /api/v1/agents/conversations — List conversations
- GET /api/v1/agents/conversations/{id} — Get conversation
- POST /api/v1/agents/conversations/{id}/messages — Send message
- POST /api/v1/agents/workflow/start — Start workflow

### SSE Streaming (2 endpoints)

- GET /api/v1/rfps/{id}/progress/stream — RFP progress stream
- GET /api/v1/events/stream — System event stream

**Total: ~95 endpoints**

---

## 17. Technology Stack Summary

| Layer | Technology |
|---|---|
| Web Framework | FastAPI |
| ASGI Server | Uvicorn |
| ORM | SQLAlchemy 2.x |
| Relational DB | SQLite (WAL) |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |
| LLM | Groq (Llama 3.3 70B) |
| LLM Framework | LangChain |
| PDF Processing | PyPDF2, pdfplumber, PyMuPDF |
| Data Processing | pandas |
| Auth | PyJWT (HS256) |
| User DB | MongoDB / JSON fallback |
| Caching | Redis / In-memory LRU |
| API Docs | Swagger UI / ReDoc (auto) |
| Validation | Pydantic v2 |
| Concurrency | ThreadPoolExecutor, asyncio |
| Portal Sim | Flask |

Why each:

- FastAPI — Async support, auto OpenAPI docs, dependency injection, type hints
- Uvicorn — High-performance async server, auto-reload for dev
- SQLAlchemy — Industry standard, supports SQLite + PostgreSQL, relationship mapping
- SQLite — Zero-config, embedded, sufficient for single-server
- ChromaDB — Embedded vector store, semantic search, metadata filtering
- sentence-transformers — all-MiniLM-L6-v2 — fast, accurate 384-dim embeddings
- Groq — Fast inference, large context window, via LangChain
- LangChain — Prompt templates, output parsers, chain composition
- PyPDF2/pdfplumber/PyMuPDF — Multiple extractors for maximum coverage
- pandas — DataFrame operations on 22k+ product catalog
- PyJWT — Stateless JWT, no server session storage
- MongoDB — Flexible schema for user accounts, JSON fallback
- Redis — Production caching with in-memory fallback
- Swagger/ReDoc — Auto-generated from FastAPI type hints
- Pydantic v2 — Request/response validation, automatic error messages
- ThreadPoolExecutor/asyncio — Parallel agent execution, async I/O
- Flask — Lightweight HTTP servers for e-procurement portals

---

## 18. Design Patterns Catalog

**Repository** — database/crud.py (BaseRepository, ProductRepository, etc.). Abstract database access behind a clean interface.

**Singleton** — RedisCache, AgentPerformanceManager, get_llm(), DatabaseManager. Single instance for shared resources.

**Facade** — pipeline_connector.py, rfp_processor/analyzer.py. Simplify complex subsystem interactions.

**State Machine** — ConversationState, WorkflowState, PipelineStage. Enforce valid state transitions.

**Mediator** — MasterAgent. Central coordinator between worker agents.

**Strategy** — Load balancer (6 strategies), rate limiter (token bucket/sliding window), serialization (JSON/Pickle). Interchangeable algorithms.

**Observer** — Workflow notifications, message tracing, audit trail. React to events without tight coupling.

**Circuit Breaker** — inter_agent_communication.py. Prevent cascade failures.

**Decorator** — @cached, @profiled, @with_timeout, @track_agent_operation. Cross-cutting concerns (caching, timing, timeouts).

**Pipeline/Chain** — 8 application pipelines, PDF extraction pipeline. Sequential stage processing.

**Object Pool** — connection_pool.py. Reuse expensive connections.

**Priority Queue** — Agent message passing, workflow step ordering. Process important items first.

**Graceful Degradation** — Every module uses try/except ImportError. System works with reduced features.

**Canonical Data Model** — agents/shared/data_models.py. Shared types across all agents.

**Dead Letter Queue** — inter_agent_communication.py. Store undeliverable messages for inspection.

**Token Bucket** — rate_limiter.py, API middleware. Control request throughput.

---

## 19. Error Handling Strategy

**API** — Custom HTTPException handler + generic Exception handler. All errors return structured JSON with detail, never raw stack traces.

**Auth** — 401 Unauthorized → client triggers refresh → retry. Silent token refresh, no user disruption.

**Rate Limit** — 429 Too Many Requests + Retry-After header. Client retries after specified delay.

**Agent Failures** — Circuit breaker + dead letter queue + exponential backoff. Failed agents don't crash the system.

**DB Failures** — SQLAlchemy session_scope() context manager with auto-rollback. Transactions rolled back on any exception.

**Import Failures** — try/except ImportError on every optional module. System starts with reduced features, doesn't crash.

**File Operations** — Atomic writes (temp file + os.replace()). No data corruption on crash.

**Pipeline Failures** — Per-stage error capture in StageResult. Failed stages don't kill the entire pipeline.

**LLM Failures** — Deterministic fallback when Groq API unavailable. Results always returned, just without LLM enrichment.

---

## 20. Security Measures

**Password hashing** — SHA-256 (never stored in plaintext).

**JWT tokens** — HS256 signed, 30-min access expiry, 7-day refresh.

**RBAC** — 4 roles with 12 distinct permissions.

**Rate limiting** — 1000 req/min, 10000 req/hr per IP.

**Audit trail** — SHA-256 integrity hashes, all actions logged with user/IP.

**Input validation** — Pydantic models validate all request bodies.

**File upload limits** — 50MB max file size, allowed extensions (PDF/DOC/XLSX).

**SQL injection prevention** — SQLAlchemy ORM (parameterized queries).

**CORS** — Configurable origins (wildcard in dev).

**Request tracing** — Unique X-Request-ID per request for forensics.
