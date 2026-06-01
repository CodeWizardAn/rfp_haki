# Haki_FMCG_2.0 — Complete Metrics & Methods Catalog

> **Generated:** February 22, 2026  
> **Total Modules:** 14 major directories, 100+ files  
> **Total Classes:** ~450+  
> **Total Methods/Functions:** ~1,800+  
> **Total Unique Metrics Tracked:** ~200+

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Analytics Module (21 files)](#2-analytics-module)
3. [Performance Module (20 files)](#3-performance-module)
4. [Agents Module (27 files)](#4-agents-module)
5. [API Module (5 files)](#5-api-module)
6. [Database Module (12+ files)](#6-database-module)
7. [PDF Extraction Module (8 files)](#7-pdf-extraction-module)
8. [RFP Processor Module (5 files)](#8-rfp-processor-module)
9. [RFP Responser Module (10 files)](#9-rfp-responser-module)
10. [Spec Comparer Module (2 files)](#10-spec-comparer-module)
11. [Vendor Management Module (11 files)](#11-vendor-management-module)
12. [E-Procurement Portals Module (4 files)](#12-e-procurement-portals-module)
13. [Top-Level Modules (5 files)](#13-top-level-modules)
14. [Master Metrics Summary](#14-master-metrics-summary)
15. [Methods by Category](#15-methods-by-category)

---

## 1. Project Overview

Haki_FMCG_2.0 is an **AI-powered RFP (Request for Proposal) processing and bid generation platform** for the wires & cables / FMCG industry. It encompasses:

- **Multi-agent AI system** (Sales, Technical, Pricing, Master orchestrator)
- **PDF extraction** and RFP term matching (100K+ terms database)
- **Product catalog** with OEM datasheets and vector embeddings
- **Specification matching** with weighted scoring algorithms
- **Automated bid generation** with pricing optimization
- **Comprehensive analytics** (A/B testing, ROI, win/loss, trends, forecasting)
- **Performance engineering** (caching, rate limiting, load balancing, profiling)
- **Vendor management** with ratings, communications, and compliance tracking
- **E-procurement portal** scraping and integration

---

## 2. Analytics Module

**Directory:** `analytics/` — 21 files, ~9,000+ lines

### 2.1 A/B Testing (`ab_testing.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `StatisticalAnalyzer` | 7 methods | Statistical testing engine |
| `ABTestingFramework` | 17 methods | Full experiment lifecycle |

**Metrics:**
- Conversion rate, Lift (%), Z-statistic, P-value
- Confidence interval, Statistical significance
- Mean value, Variance (Welford's online algorithm)
- Required sample size, Experiment progress %

**Statistical Methods:**
- Two-proportion Z-test
- Welch's T-test for means
- Normal CDF approximation (Abramowitz–Stegun)
- Deterministic weighted variant assignment

---

### 2.2 Agent Performance (`agent_performance.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `AgentPerformanceTracker` | 11 methods | Track agent request lifecycle |

**Metrics:**
- Requests: total / successful / failed
- Success rate (%)
- Response time: avg / p50 / p95 / p99 / max (ms)
- Token usage: total, avg per request, distribution
- Accuracy rate, Confidence average
- Error type counts & percentages

---

### 2.3 Alert System (`alert_system.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `AnomalyDetector` | 3 methods | Z-score & trend-based anomaly detection |
| `AlertManager` | 15 methods | Rule-based alerting with channels |

**Metrics:**
- Z-score anomaly detection
- Trend change % (>50% triggers anomaly)
- MTTA (Mean Time To Acknowledge)
- MTTR (Mean Time To Resolve)
- Alert counts by severity / status / rule

**Alert Channels:** EMAIL, SLACK, WEBHOOK, SMS, LOG

---

### 2.4 Analytics Export (`analytics_export.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `AnalyticsExporter` | 12 methods | Multi-format data export |
| `ExportBuilder` | 6 methods | Fluent builder pattern |

**Export Formats:** JSON, CSV, Excel, PDF  
**Data Types:** RFP, Win/Loss, Agent, Cost, System Health

---

### 2.5 Benchmarking (`benchmarking.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `BenchmarkManager` | 14 methods | Performance benchmarking |

**Industry Standards:**
| Metric | Baseline | Good | Excellent |
|--------|----------|------|-----------|
| RFP Response Time | 24h | 12h | 6h |
| Win Rate | 25% | 35% | 50% |
| Match Accuracy | 70% | 85% | 95% |
| Cost per RFP | $500 | $300 | $150 |

**Metrics:** Percentage change, Rating (excellent/good/average/poor), Overall score (0-100), Trend direction

---

### 2.6 Cost Analysis (`cost_analysis.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `CostAnalyzer` | 12 methods | Cost tracking & budgeting |

**Default Cost Rates:**
| Category | Item | Rate |
|----------|------|------|
| LLM | GPT-4 | $0.03/1K tokens |
| LLM | GPT-3.5 | $0.002/1K tokens |
| Compute | CPU | $0.05/hr |
| Compute | GPU | $2.50/hr |
| Storage | Standard | $0.023/GB-month |

**Metrics:** Total cost, Cost by category (%), Cost per RFP (avg/min/max/median), Daily burn rate, Projected total, Budget status

---

### 2.7 Dashboard API (`dashboard_api.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `DashboardAPI` | 20 methods | Unified dashboard data provider |

**Chart Types Generated:** Line (time series), Pie (win rate), Bar (cost breakdown)  
**Endpoints:** Overview, KPIs, RFP metrics, Win/Loss, Agent metrics, Cost, System health, Predictions, ROI, What-if analysis

---

### 2.8 Match Accuracy (`match_accuracy.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `MatchAccuracyTracker` | 11 methods | Product matching accuracy tracking |

**Metrics:**
- Top-1 / Top-3 / Top-5 accuracy
- Mean Reciprocal Rank (MRR)
- Average confidence
- Accuracy by confidence bucket (calibration)
- Per-algorithm-version accuracy comparison
- Confusion pair analysis

---

### 2.9 Metrics Collector (`metrics_collector.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `MetricsCollector` (Singleton) | 16 methods | Core metric collection engine |
| `MetricsAggregator` | 2 methods | Time-based aggregation |
| `MetricsPersistence` | 3 methods | Database persistence |

**Metric Types:** Counter, Gauge, Histogram  
**Histogram Stats:** count, sum, min, max, mean, p50, p90, p95, p99  
**Decorators:** `@track_metric`, `@track_timing`, `@track_success_failure`

---

### 2.10 Data Models (`models.py`)

**14 SQLAlchemy ORM Models:**

| Model | Table | Key Metrics Stored |
|-------|-------|--------------------|
| `RFPMetric` | `analytics_rfp_metrics` | extraction/parsing/matching/bid time, requirements count, match confidence, margin % |
| `MatchAccuracyMetric` | `analytics_match_accuracy` | predicted vs actual product, is_correct, top-3/5, spec & semantic accuracy |
| `WinLossRecord` | `analytics_win_loss` | outcome, competitors, bid amounts, price difference %, technical/commercial scores |
| `AgentPerformanceMetric` | `analytics_agent_performance` | response times (p50-p99), tokens, accuracy, confidence, errors |
| `SystemHealthMetric` | `analytics_system_health` | CPU, memory, disk, network, DB connections, error rate |
| `ResponseTimeMetric` | `analytics_response_time` | queue/processing/DB/API/serialization time breakdown |
| `CostRecord` | `analytics_costs` | category, amount, units, agent_type |
| `ABTestExperiment` | `analytics_ab_experiments` | status, winner, significance |
| `ABTestVariant` | `analytics_ab_variants` | config, traffic weight |
| `ABTestResult` | `analytics_ab_results` | metric name & value |
| `Benchmark` | `analytics_benchmarks` | value, thresholds, higher_is_better |
| `Alert` | `analytics_alerts` | severity, trigger value, threshold, resolution |
| `ScheduledReport` | `analytics_scheduled_reports` | frequency, recipients, config |
| `AnalyticsSnapshot` | `analytics_snapshots` | metrics JSON, dimensions |

---

### 2.11 Predictive Analytics (`predictive_analytics.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `SimpleLinearRegression` | 2 methods | Linear regression (fit + predict) |
| `NaiveBayesClassifier` | 3 methods | Gaussian Naive Bayes |
| `PredictiveAnalytics` | 10 methods | ML-powered predictions |

**ML Models:**
- **Win Predictor:** Naive Bayes classifier (features: bid_amount, competitors, technical_score, commercial_score, contract_duration)
- **Processing Time Model:** Linear regression (feature: requirements_count)
- **Match Quality Model:** Linear regression (feature: confidence_score)

**Metrics:** Win probability, Processing time estimate, Match correctness probability, Forecast with confidence intervals (±20%), Risk score (0-10), Risk level (low/medium/high), R²

---

### 2.12 Report Generator (`report_generator.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `ReportGenerator` | 15 methods | Multi-format report generation |

**Templates:** Executive Summary, Detailed Analytics, RFP Performance, Agent Performance, Cost Analysis, Win/Loss  
**Formats:** PDF (ReportLab), Excel (openpyxl), JSON, CSV

---

### 2.13 Response Time Analytics (`response_time.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `ResponseTimeAnalytics` | 11 methods | API response time analysis |

**SLA Thresholds:**
| Level | Threshold |
|-------|-----------|
| Excellent | 100ms |
| Good | 500ms |
| Acceptable | 1000ms |
| Poor | 3000ms |

**Metrics:** avg/min/max/p50/p95/p99, Latency breakdown (queue/processing/DB/external/serialization), SLA compliance %, Error rate, Anomaly detection

---

### 2.14 RFP Metrics (`rfp_metrics.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `RFPMetricsTracker` | 10 methods | RFP processing lifecycle tracking |

**Metrics:** Total RFPs, Daily average, Processing time (avg/min/max), Per-stage timing (extraction, parsing, matching, bid_generation), Match confidence, Success/error rate, Outcome breakdown

---

### 2.15 ROI Calculator (`roi_calculator.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `ROICalculator` | 9 methods | Return on investment analysis |

**Default Assumptions:**
| Parameter | Value |
|-----------|-------|
| Avg margin | 15% |
| Manual processing cost | $500 |
| Manual processing hours | 8h |
| Hourly labor cost | $50 |

**Metrics:** ROI %, Net benefit, Cost per win/bid/RFP, Profit per RFP, Automation savings, Time saved (hours), Labor savings ($), Efficiency ratio, What-if projections

---

### 2.16 Scheduled Reports (`scheduled_reports.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `ScheduledReportManager` | 16 methods | Automated report scheduling |

**Frequencies:** Hourly, Daily, Weekly, Monthly, Custom

---

### 2.17 System Health (`system_health.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `HealthCheck` | 1 method | Individual health check runner |
| `SystemHealthMonitor` | 12 methods | System resource monitoring |

**Thresholds:**
| Resource | Warning | Critical |
|----------|---------|----------|
| CPU | 70% | 90% |
| Memory | 75% | 90% |
| Disk | 80% | 95% |

**Metrics:** CPU usage/load (1m/5m/15m), Memory used/available/percent + swap, Disk used/available/percent + I/O, Network bytes sent/recv, Process memory/CPU/threads, DB latency, Uptime %, Availability

---

### 2.18 Trend Analysis (`trend_analysis.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `TrendAnalyzer` | 13 methods | Statistical trend analysis |

**Methods:**
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Weighted Moving Average (WMA)
- Linear regression trend detection (slope, R², direction)
- Compound Annual Growth Rate (CAGR)
- Period-over-period growth
- Seasonal pattern detection (indices, strength, peak/trough)
- Anomaly detection: Z-score method, IQR method

---

### 2.19 Visualization (`visualization.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `ColorPalette` | 2 static methods | Chart.js color management |
| `VisualizationGenerator` | 16 methods | Chart.js data generation |

**Chart Types:**
- Line / Area (time series)
- Pie / Doughnut (distributions)
- Bar (horizontal/stacked)
- Sparkline (mini-charts)
- Gauge (CPU/memory/disk)
- Radar (multi-dimensional performance)
- Heatmap (hourly activity)

---

### 2.20 Win/Loss Analytics (`win_loss_analytics.py`)

| Class | Methods | Description |
|-------|---------|-------------|
| `WinLossAnalytics` | 9 methods | Bid outcome analysis |

**Metrics:** Win rate, Participation rate, Won/lost value, Win rate by dimension (segment/region/category/customer), Competitor win/loss ratio, Price difference %, Win rate by price bucket, Top winning/losing factors, Technical/commercial/overall scores, Loyal & high-value customers

---

## 3. Performance Module

**Directory:** `performance/` — 20 files, ~8,000+ lines

### 3.1 Async Operations (`async_ops.py`)
**Classes:** `AsyncExecutor`, `TaskManager`, `AsyncContextManager`  
**Functions:** `run_concurrent`, `run_with_timeout`, `retry_async`, `make_async`  
**Decorator:** `@async_task`

### 3.2 Auto Scaler (`auto_scaler.py`)
**Classes:** `AutoScaler`, `PredictiveScaler`, `TargetTrackingScaler`  
**Methods:** Policy-based scaling, Pattern learning, Predictive pre-scaling

### 3.3 Batch Processor (`batch_processor.py`)
**Classes:** `BatchProcessor[T,R]`, `Pipeline`, `BatchInsertBuilder`, `StreamProcessor`  
**Metrics:** `duration_seconds`, `items_per_second`, `success_rate`

### 3.4 Bottleneck Detector (`bottleneck_detector.py`)
**Classes:** `BottleneckDetector`, `RootCauseAnalyzer`  
**Detection Types:** CPU, Memory, Slow responses, High error rate, Queue saturation, Degradation trend  
**Methods:** Percentile analysis, Trend detection, Correlation-based root cause analysis

### 3.5 Connection Pool (`connection_pool.py`)
**Classes:** `BaseConnectionPool`, `DatabasePool`, `RedisPool`, `ConnectionPoolManager` (Singleton)  
**Metrics:** Pool stats (active/idle/total connections, wait time, errors)

### 3.6 Performance Dashboard (`dashboard.py`)
**Classes:** `MetricsRegistry`, `PerformanceDashboard`, `RealTimeStream`, `AlertManager`  
**Features:** Real-time streaming, Health calculation, Time series export

### 3.7 Database Indexing (`db_indexing.py`)
**Classes:** `IndexManager`  
**Methods:** Query analysis for index recommendations, Unused/duplicate index detection, Index health reporting

### 3.8 Embedding Cache (`embedding_cache.py`)
**Classes:** `LRUCache`, `EmbeddingCache`, `MultiTierCache`  
**Methods:** LRU eviction, Cosine similarity search, Multi-tier (memory + disk) caching

### 3.9 Integration (`integration.py`)
**Classes:** `PerformanceManager` (Singleton), `FastAPIPerformanceMiddleware`  
**Decorators:** `@cached`, `@rate_limited`, `@profiled`, `@with_timeout`, `@batch_execute`

### 3.10 Load Balancer (`load_balancer.py`)
**Strategies:** Round Robin, Weighted Round Robin, Least Connections, IP Hash, Least Response Time  
**Classes:** `LoadBalancer`, `ServiceDiscovery`

### 3.11 Load Tester (`load_tester.py`)
**Classes:** `VirtualUser`, `LoadTester`, `LoadTestRunner`  
**Patterns:** Constant, Ramp-up, Spike, Wave  
**Metrics:** Throughput, Error rate, Response time percentiles

### 3.12 Optimizer (`optimizer.py`)
**Analyzers:** CachingAnalyzer, DatabaseAnalyzer, ResourceAnalyzer, ResponseTimeAnalyzer, ErrorRateAnalyzer  
**Output:** Prioritized recommendations with effort estimation

### 3.13 Parallel Matcher (`parallel_matcher.py`)
**Strategies:** Exact, Fuzzy, Semantic, Hybrid  
**Methods:** Thread-pool-based parallel matching, Simple ratio fuzzy matching

### 3.14 Profiler (`profiler.py`)
**Classes:** `FunctionProfiler`, `CodeProfiler`, `LineProfiler`, `HotSpotDetector`  
**Metrics:** Call count, Total/avg time, Memory snapshots, Line-level profiling, Hot spot detection

### 3.15 Query Optimizer (`query_optimizer.py`)
**Classes:** `QueryOptimizer`, `QueryProfiler`  
**Detection:** N+1 query detection, Slow query analysis, Query optimization hints

### 3.16 Rate Limiter (`rate_limiter.py`)
**Algorithms:** Token Bucket, Sliding Window, Fixed Window, Leaky Bucket  
**Classes:** `CompositeRateLimiter`, `PerClientRateLimiter`, `RateLimitMiddleware`

### 3.17 Redis Cache (`redis_cache.py`)
**Classes:** `RedisCache` (Singleton), `InMemoryFallback`  
**Patterns:** Cache-aside, Get-or-set, Invalidate-on-update  
**Data Structures:** String, Hash, List, Sorted Set

### 3.18 Request Queue (`request_queue.py`)
**Classes:** `PriorityRequestQueue`, `RequestQueueWorker`, `FairScheduler`, `BackpressureController`, `AsyncRequestQueue`  
**Priorities:** CRITICAL(0), HIGH(1), NORMAL(2), LOW(3), BACKGROUND(4)

### 3.19 Resource Monitor (`resource_monitor.py`)
**Classes:** `ResourceMonitor`, `ResourceThrottler`  
**Metrics:** CPU (per-core + avg), Memory (virtual + swap), Disk (usage + I/O), Network, Process-level metrics

### 3.20 Stress Tester (`stress_tester.py`)
**Classes:** `StressTester`, `ResourceExhaustionTester`, `RecoveryTester`, `StabilityTester`  
**Tests:** Stepped load increase, Memory/thread/connection exhaustion, Recovery after overload

---

## 4. Agents Module

**Directory:** `agents/` — 27 files across 7 subdirectories

### 4.1 LangChain Agent (`langchain_agent/rfp_chain.py`)
**Classes:** `LCSalesAgent`, `LCTechnicalAgent`, `LCPricingAgent`, `LCMasterAgent`, `LangChainRFPAgent`  
**Methods:** LLM-powered parallel extraction, Batch match analysis, Pricing estimation, Full RFP analysis

### 4.2 Master Agent (`master_agent/`)

**`main_orchestrator.py`** — `MainOrchestrator`, `AgentRegistry`, `WorkflowStateMachine`  
- 6 workflow states, Agent registration/discovery by type & capability, State machine transitions

**`orchestrator.py`** — `MasterAgent`  
- Conversation management, Agent coordination (Sales → Technical → Pricing), Response consolidation, Compliance checklist generation, Scope of supply table

### 4.3 Pricing Agent (`pricing_agent/`)

**`price_calculator.py`** — `PricingAgent`  
- Product pricing, Test cost calculation, Tax calculation, Quote generation

**`pricing_agent.py`** — 40+ specialized classes including:
- `UnitPriceCalculator`, `VolumeDiscountApplier`
- `TestCostCalculator`, `TestFrequencyAnalyzer`, `SampleTestingCost`, `RoutineTestCostCalculator`
- `LogisticsCostCalculator`, `TransportationCostCalculator`, `InsuranceCostCalculator`
- `MarginCalculator`, `FinalPriceGenerator`
- `CompetitiveAnalysis`, `WinProbabilityEstimator`
- `SensitivityAnalysis`, `WhatIfScenarioGenerator`
- `PricingValidator`, `PricingApprovalWorkflow`

### 4.4 Sales Agent (`sales_agent/`)

**`rfp_scanner.py`** — `SalesAgent`  
- URL scanning, PDF scanning, Priority scoring, Deadline tracking

**`sales_agent.py`** — `SalesAgent` (enhanced)  
- 25+ classes: `WebScraper`, `RFPDetector`, `PriorityScorer`, `DuplicateDetector`, `Scheduler`
- Stateful agent lifecycle (start/stop/pause/resume)

### 4.5 Technical Agent (`technical_agent/`)

**`oem_product_repository.py`** — `OEMProductRepository`  
- Product CRUD, Category/manufacturer search

**`spec_matcher.py`** — `TechnicalAgent`  
- Specification matching with scoring, Semantic matching, Comparison table generation

**`technical_agent.py`** — 30+ classes including:
- `RFPRequirementParser`, `ProductCatalogQuerier`, `VectorSearchIntegration`
- `SpecificationMatchingOrchestrator`, `MatchScoreCalculator`
- `GapAnalysisGenerator`, `TechnicalRiskAssessor`, `ComplianceChecker`
- `ProductRecommendationRanker`, `CustomProductFlagger`

### 4.6 Shared Utilities (`shared/`)

| File | Key Classes/Functions |
|------|----------------------|
| `agent_performance.py` | `AgentPerformanceManager`, decorators: `@track_agent_operation`, `@cache_agent_result`, `@rate_limit_agent`, `@timeout_agent` |
| `communication_protocol.py` | `MessageBroker` (pub/sub), 10 message factory functions |
| `data_models.py` | Shared dataclasses: `RFPDocument`, `OEMProductMatch`, `TechnicalAgentResponse`, `PricingAgentResponse`, `ConsolidatedRFPResponse` |
| `inter_agent_communication.py` | `InterAgentCommunicationSystem` with Circuit Breaker, Retry, Dead Letter Queue, Message Tracing, Analytics |
| `matching_engine.py` | `MatchingEngine`: Standard equivalence, Weighted scoring, Confidence calculation, Gap analysis, Critical failure detection |
| `workflow_orchestration.py` | `WorkflowOrchestrationEngine`: 20+ methods, Checkpoints, Rollback, Parallel execution, Human tasks, Approvals |

### 4.7 Shared Utilities — Utils (`shared/utils/`)

| File | Purpose |
|------|---------|
| `config_loader.py` | Singleton config from YAML/JSON/ENV with type conversion |
| `date_utils.py` | Date parsing, Business days, Deadline calculation |
| `decorators.py` | `@retry`, `@timer`, `@cached`, `@validate_input`, `@rate_limit`, `@singleton`, `@measure_memory` |
| `logging_utils.py` | Structured JSON logging, Colored console, Agent action logging |
| `param_extractor.py` | Extract conductor specs, voltage, dimensions, quantity, standards from text |
| `spec_normalizer.py` | Normalize conductor size, voltage, temperature, material |
| `standard_mapper.py` | IEC↔IS↔BS↔ASTM standard equivalence mapping |
| `text_utils.py` | Text cleaning, Fuzzy matching, Tokenization, Key-value extraction |
| `unit_converter.py` | Convert length, area, weight, voltage, current, temperature |
| `validators.py` | Validate SKU, email, phone, GSTIN, PAN, specifications, price, quantity |

---

## 5. API Module

**Directory:** `api/` — 5 files, ~7,000+ lines

### 5.1 REST API (`rest_api.py` — 5,118 lines)

**Authentication:** JWT-based with MongoDB + JSON fallback  
**Authorization:** Role-based (ADMIN, MANAGER, ANALYST, VIEWER)  
**Rate Limiting:** Per-client request throttling

**70+ API Endpoints across 15 categories:**

| Category | Endpoints | Key Operations |
|----------|-----------|----------------|
| Auth | 6 | Login, Register, JWT refresh, Logout |
| RFP | 17 | Submit, Upload, Analyze, Process, Track linked docs |
| Pipeline | 8 | Full pipeline, Upload, Start, Cancel, Retry |
| Products | 12 | Search, Import catalog, Compare, CRUD |
| Bids | 10 | Create, Update, Submit, Approve/Reject |
| Bid Documents | 11 | Generate PDF, Company profiles, Email |
| Analysis | 4 | Save, List, Get, Delete analysis results |
| Vendors | 5 | CRUD, Rankings |
| Portals | 4 | Scrape, Status, List RFPs, Download PDF |
| Config | 4 | Get, Update, Reset |
| Analytics | 5 | Overview, RFP, Performance, Query, Export |
| Webhooks | 6 | CRUD, Toggle, Logs |
| Batch | 2 | Submit batch, Get status |
| Streaming | 2 | SSE progress, Event stream |
| System | 5 | Health, Rate limit status, Version |

### 5.2 API Performance (`api_performance.py`)

**Rate Limiters:**
| Limiter | Rate |
|---------|------|
| General API | 100/min |
| Search | 20/min |
| Upload | 5/min |

**Metrics:** Exponential moving average response time, Requests by endpoint/status

### 5.3 Bid Document Generator (`bid_document_generator.py`)

**Financial Metrics in Generated Bids:**
- Subtotal, Discount %, GST rate/amount, Grand total
- AI pricing comparison (material + test costs)
- OEM-wise and category-wise cost breakdown
- Margin analysis (margin vs AI, margin % vs AI)

### 5.4 Bid PDF Generator (`bid_pdf_generator.py`)

**PDF Sections:** Cover, Bidder Info, RFP Reference, Terms & Conditions, BOQ/Price Schedule, Financial Summary, Technical Compliance, OEM Summary, Bank Details, Declaration

---

## 6. Database Module

**Directory:** `database/` — 12+ files, ~5,000+ lines

### 6.1 ORM Models (`models.py`)

| Model | Key Fields |
|-------|-----------|
| `Product` | SKU, specs, price, OEM, status |
| `OEM` | Name, code, country, products |
| `RFP` | rfp_id, title, authority, due_date, requirements |
| `ProductMatch` | match_score, match_details |
| `Bid` | status, items, totals |
| `AgentLog` | agent_type, action, metrics |
| `AuditTrail` | user, action, entity, old/new values |
| `TestService` | category, price, standard |

### 6.2 CRUD Operations (`crud.py`)

**8 Repository Classes:** Product, OEM, RFP, Requirement, Match, AgentLog, Bid, Audit, TestService  
**Base Operations:** Create, Get, Update, Delete, Count, Exists, Bulk create/delete

### 6.3 Vector Embeddings (`vector_embeddings.py` — 1,500+ lines)

| Class | Purpose |
|-------|---------|
| `EmbeddingModelManager` | Model lifecycle management |
| `EmbeddingPipeline` | Generate embeddings, Compute similarity |
| `ChromaDBEmbeddingStore` | ChromaDB CRUD operations |
| `SemanticSearch` | Vector-based similarity search |
| `HybridSearch` | Combined keyword + semantic search |
| `SimilarityRanker` | Score-based ranking with diversity re-ranking |
| `EmbeddingCache` | LRU cache with disk persistence |
| `EmbeddingUpdater` | Incremental embedding updates |

**Embedding Models:** Sentence Transformers (configurable)  
**Search Modes:** Semantic, Keyword, Hybrid

### 6.4 ChromaDB Setup (`chromadb_setup.py`)

**Collections:** Products, RFP Requirements, Agent Knowledge  
**Operations:** Semantic search, Similarity queries, Collection statistics

### 6.5 Database Performance (`db_performance.py`)

**Features:** Connection pooling, Query caching (TTL-based), Batch insert/update, Query performance tracking  
**Decorators:** `@cached_query`, `@track_query_performance`, `@batch_operation`

### 6.6 Migrations (`migrations.py`)

**Operations:** Version tracking, Schema change detection, Upgrade/downgrade, Auto-migration generation

---

## 7. PDF Extraction Module

**Directory:** `pdf_extraction/` — 8 files, ~4,000+ lines

| File | Key Classes | Purpose |
|------|-------------|---------|
| `pdf_text_extractor.py` | `PDFTextExtractor` | Page-level text/table extraction, Metadata, Batch processing |
| `pdf_extraction_manager.py` | `PDFExtractionManager` | Upload management, Section extraction, File hashing |
| `rfp_terms_matcher.py` | `RFPTermsMatcher`, `RFPExtractorEnhanced`, `RFPCompleteAnalyzer` | 100K+ term database, Field extraction, Section detection, Abbreviation expansion |
| `hyperlink_extractor.py` | `PDFHyperlinkExtractor`, `RFPDocumentAnalyzer` | Link extraction, BOQ parsing (Excel/CSV/PDF), Document classification |
| `multilingual_extractor.py` | `MultilingualExtractor` | Language detection, Unicode integrity, OCR fallback, Layout/char mode extraction |
| `perf_integration.py` | `PDFProcessingOptimizer` | Caching, Parallel term matching, Batch page processing |
| `app.py` | `OEMProductDatabase`, `SpecMatcher`, `SpecCalculator`, `ProductRecommender` | Flask app with 30+ routes |

**SpecCalculator Methods:**
- Cable size calculation (IEC 60228)
- Voltage drop calculation
- Short circuit capacity (adiabatic equation)
- Power capacity with derating factors
- Testing cost calculation
- Insulation resistance calculation
- Hi-pot test calculation
- Conductor resistance calculation

---

## 8. RFP Processor Module

**Directory:** `rfp_processor/` — 5 files

| File | Class | Methods |
|------|-------|---------|
| `scraper.py` | `PortalScraper` | Scrape portals (API + HTML), Download PDFs |
| `analyzer.py` | `RFPAnalyzer` | Text extraction, Term analysis, Summary generation, Master report |
| `pipeline.py` | — | End-to-end pipeline (scrape → download → analyze) |
| `dashboard.py` | — | Flask dashboard for viewing results |

---

## 9. RFP Responser Module

**Directory:** `rfp_responser/` — 10 files, ~5,000+ lines

| File | Key Classes | Purpose |
|------|-------------|---------|
| `rfp_workflow.py` | `RFPWorkflowManager` | Full RFP processing workflow (extract → parse → match → price → bid) |
| `bid_templates.py` | `BidTemplateManager`, `BidBuilder` | Bid document templates, Builder pattern |
| `bid_price_calculator.py` | `PriceCalculator` | Item pricing, Volume discounts, Shipping, Tax (GST/IGST/custom) |
| `bid_oem_pricing.py` | `OEMPriceCalculator` | OEM pricing models: Per-unit, Volume-tiered, NRE+unit, Hybrid |
| `bid_approval_workflow.py` | `ApprovalWorkflow` | Multi-level approval (Manager → Director → VP → C-Level) |
| `bid_document_generator.py` | `PDFBidGenerator`, `ExcelBidGenerator` | PDF and Excel bid document generation |
| `oem_bid_routes.py` | — | 11 Flask API routes for OEM bid management |
| `perf_integration.py` | `RFPProcessingOptimizer` | Bid/match/pricing caching, Rate limiting |
| `app.py` | — | Flask app with 40+ routes |

---

## 10. Spec Comparer Module

**Directory:** `spec_comparer/` — 2 files

| Class | Key Methods |
|-------|-------------|
| `SpecMatcher` | `parse_rfp_requirements`, `find_matching_products`, `_calculate_match_score` |
| `SpecCalculator` | Cable sizing, Voltage drop, Short circuit, Power capacity, Testing costs, Insulation resistance, Hi-pot, Conductor resistance |
| `OEMProductDatabase` | Load multi-OEM data, Search, Stats |
| `ProductRecommender` | By application, By budget, Best quality, OEM comparison |
| `SpecVendorBridge` | Vendor-enriched comparisons, Best vendor selection, Compliance checking |

---

## 11. Vendor Management Module

**Directory:** `vendor_management/` — 11 files, ~3,000+ lines

| Component | Class | Key Metrics |
|-----------|-------|-------------|
| Database | `VendorDatabase` | CRUD, Search, Bulk import/export |
| Performance | `VendorPerformanceTracker` | Delivery (on-time %), Quality (defect rate, rework), Response time, Complaints |
| Ratings | `VendorRatingEngine` | Badges: PLATINUM/GOLD/SILVER/BRONZE/UNRATED, Weighted scoring, Trend analysis |
| Communications | `VendorCommunicationManager` | Email templates, Message threading, Follow-ups |
| OEM Profiles | `OEMVendorProfile` | Capacity utilization, Certification status, Capability score, Readiness score |
| OEM Performance | `OEMVendorPerformanceReport` | Quality/Capacity/Delivery/Responsiveness/Technical/Compliance scores |
| Integration | `VendorIntegrationBridge` | Audit logging, Compliance verification, Pricing analysis, Holistic evaluation |

**Rating Criteria Weights:**
| Criterion | Default Weight |
|-----------|---------------|
| Quality | configurable |
| Delivery | configurable |
| Price competitiveness | configurable |
| Responsiveness | configurable |
| Technical capability | configurable |
| Compliance | configurable |

---

## 12. E-Procurement Portals Module

**Directory:** `e_procure_portals/` — 4 files

- **4 Simulated Government Portals** (GeM, CPPP, IREPS, State Portal)
- PDF distribution across portals
- Flask-based portal apps with API + HTML views
- RFP listing, Detail view, PDF download

---

## 13. Top-Level Modules

### 13.1 Audit Trail (`audit_trail.py`)
**Action Types:** CREATE, READ, UPDATE, DELETE, EXPORT, IMPORT, LOGIN, LOGOUT, SEARCH, DOWNLOAD, APPROVE, REJECT, VERIFY, ERROR  
**Entity Types:** USER, RFP, PRODUCT, BID, VENDOR, COMPLIANCE, PRICE, NOTIFICATION, REPORT, SYSTEM

### 13.2 Compliance Checker (`compliance_checker.py`)
**8 Default Rules:** Voltage, Current, Material, Insulation, Temperature, Certification, IS standard, Environmental  
**Scoring:** Per-rule + overall compliance score with risk levels (LOW/MEDIUM/HIGH/CRITICAL)

### 13.3 Pipeline Connector (`pipeline_connector.py`)
**16 Pipeline Stages:** RFP_INTAKE → TEXT_EXTRACTION → TERM_MATCHING → REQUIREMENT_PARSING → VECTOR_SEARCH → SPEC_MATCHING → PRODUCT_RECOMMENDATION → PRICING_CALCULATION → BID_GENERATION → COMPLIANCE_CHECK → AUDIT_LOGGING → ANALYTICS → AGENT_ORCHESTRATION → VENDOR_ENRICHMENT → COMPLETED / ERROR

**5 Sub-Pipelines:** RFPIntake, ProductMatching, PricingBid, ComplianceAudit, Analytics

### 13.4 Price Optimization (`price_optimization.py`)
**Methods:** Price history analysis (min/max/avg/median/std_dev/trend), Seller comparison, Price prediction (linear regression), Volume discount optimization, Optimal quantity finder

---

## 14. Master Metrics Summary

### Business Metrics
| Metric | Source | Type |
|--------|--------|------|
| Win Rate (%) | Win/Loss Analytics | KPI |
| Participation Rate | Win/Loss Analytics | KPI |
| Won/Lost Value ($) | Win/Loss Analytics | Financial |
| ROI (%) | ROI Calculator | Financial |
| Net Benefit ($) | ROI Calculator | Financial |
| Cost per RFP/Bid/Win | ROI Calculator, Cost Analysis | Financial |
| Profit per RFP | ROI Calculator | Financial |
| Automation Savings ($) | ROI Calculator | Efficiency |
| Time Saved (hours) | ROI Calculator | Efficiency |
| Labor Savings ($) | ROI Calculator | Efficiency |
| Margin % (vs AI) | Bid Document Generator | Financial |

### Processing Metrics
| Metric | Source | Type |
|--------|--------|------|
| Total RFPs Processed | RFP Metrics | Volume |
| Daily Average | RFP Metrics | Volume |
| Processing Time (avg/p95) | RFP Metrics | Performance |
| Per-Stage Timing | RFP Metrics | Performance |
| Match Confidence (avg) | RFP Metrics | Quality |
| Success/Error Rate | RFP Metrics | Reliability |

### Accuracy Metrics
| Metric | Source | Type |
|--------|--------|------|
| Top-1/3/5 Accuracy | Match Accuracy | Quality |
| Mean Reciprocal Rank (MRR) | Match Accuracy | Quality |
| Confidence Calibration | Match Accuracy | Quality |
| Algorithm Version Comparison | Match Accuracy | Quality |
| Confusion Pairs | Match Accuracy | Diagnostics |

### Agent Metrics
| Metric | Source | Type |
|--------|--------|------|
| Request Success Rate | Agent Performance | Reliability |
| Response Time (p50/p95/p99) | Agent Performance | Performance |
| Token Usage (total/avg) | Agent Performance | Cost |
| Accuracy Rate | Agent Performance | Quality |
| Error Type Distribution | Agent Performance | Diagnostics |

### Infrastructure Metrics
| Metric | Source | Type |
|--------|--------|------|
| CPU Usage/Load | System Health | Infrastructure |
| Memory Usage/Available | System Health | Infrastructure |
| Disk Usage/I/O | System Health | Infrastructure |
| Network I/O | System Health | Infrastructure |
| DB Latency (ms) | System Health | Infrastructure |
| Uptime/Availability (%) | System Health | Infrastructure |
| SLA Compliance (%) | Response Time | SLA |

### Predictive Metrics
| Metric | Source | Type |
|--------|--------|------|
| Win Probability | Predictive Analytics | Prediction |
| Processing Time Estimate | Predictive Analytics | Prediction |
| Match Correctness Probability | Predictive Analytics | Prediction |
| Metric Forecasts (±20% CI) | Predictive Analytics | Prediction |
| Risk Score (0-10) | Predictive Analytics | Assessment |

### Vendor Metrics
| Metric | Source | Type |
|--------|--------|------|
| On-Time Delivery % | Vendor Performance | Quality |
| Defect Rate | Vendor Performance | Quality |
| Response Time | Vendor Performance | Service |
| Complaint Count | Vendor Performance | Service |
| Rating Badge (Platinum→Unrated) | Vendor Rating | Composite |
| OEM Readiness Score | OEM Vendor Profile | Assessment |
| Capability Score | OEM Vendor Profile | Assessment |

---

## 15. Methods by Category

### Statistical & ML Methods
- Two-proportion Z-test
- Welch's T-test
- Simple Linear Regression (with R²)
- Gaussian Naive Bayes Classifier
- Z-score Anomaly Detection
- IQR Anomaly Detection
- Simple/Exponential/Weighted Moving Averages
- Compound Annual Growth Rate (CAGR)
- Seasonal Pattern Detection
- Confidence Interval Estimation

### Matching & Scoring Methods
- Cosine Similarity (vector embeddings)
- Fuzzy String Matching (Levenshtein-based)
- Semantic Search (sentence transformers + ChromaDB)
- Hybrid Search (keyword + semantic)
- Weighted Multi-criteria Scoring
- Standard Equivalence Mapping (IEC↔IS↔BS↔ASTM)
- Specification Normalization (voltage, conductor, material)
- Gap Analysis & Critical Failure Detection

### Performance Engineering Methods
- Token Bucket Rate Limiting
- Sliding Window Rate Limiting
- Fixed Window Rate Limiting
- Leaky Bucket Rate Limiting
- LRU Cache (memory + disk tiers)
- Connection Pooling (database + Redis)
- Batch Processing (with parallelism)
- Load Balancing (5 strategies)
- Circuit Breaker Pattern
- Backpressure Control
- N+1 Query Detection
- Hot Spot Detection
- Function/Line-level Profiling

### Document Processing Methods
- PDF Text Extraction (layout + character mode)
- OCR Fallback (for scanned PDFs)
- Multilingual Support with Unicode integrity
- Hyperlink Extraction & Document Classification
- BOQ Parsing (Excel/CSV/PDF)
- 100K+ RFP Terms Database Matching
- Section Detection & Field Extraction
- Abbreviation Expansion

### Engineering Calculations
- Cable Size Calculation (IEC 60228)
- Voltage Drop Calculation
- Short Circuit Capacity (Adiabatic equation)
- Power Capacity with Derating Factors
- Insulation Resistance Calculation
- Hi-Pot Test Calculation
- Conductor Resistance Calculation
- Testing Cost Estimation

### Pricing Methods
- Volume Discount Tiers
- OEM Pricing Models (Per-unit, Volume-tiered, NRE+unit, Hybrid)
- Tax Calculation (GST, IGST, Custom)
- Shipping Cost Estimation
- Competitive Analysis
- Win Probability Estimation
- Sensitivity Analysis
- What-If Scenario Generation
- Margin Calculation
- Price Trend Analysis (Rising/Falling/Stable)
- Optimal Quantity Finder

### Workflow & Orchestration Methods
- State Machine Transitions (16 pipeline stages)
- Multi-agent Orchestration (Sales → Technical → Pricing → Master)
- Checkpoint & Rollback
- Parallel Step Execution
- Human Task Management
- Multi-level Approval Workflow (Manager → Director → VP → C-Level)
- Dead Letter Queue
- Message Tracing & Analytics

---

> **Total Unique Metrics:** ~200+  
> **Total Methods/Functions:** ~1,800+  
> **Total Classes:** ~450+  
> **Statistical/ML Methods:** 10+  
> **Engineering Calculations:** 8  
> **Pricing Models:** 6  
> **Rate Limiting Algorithms:** 4  
> **Load Balancing Strategies:** 5  
> **Chart Types:** 7  
> **Export Formats:** 4 (JSON, CSV, Excel, PDF)  
> **API Endpoints:** 70+  
