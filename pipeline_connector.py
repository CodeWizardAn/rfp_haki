"""
Central Pipeline Connector
===========================
Wires all 8 pipelines end-to-end with real working connections.

Pipelines:
1. RFP Intake & Processing (PDF → DB → Agents)
2. Product Matching Engine (Agents → Vector DB → Spec Comparer)
3. Pricing & Commercial Bid (Pricing Agent → Bid Generator)
4. Vendor Management (Vendor DB ↔ RFP Pipeline)
5. Agent Orchestration (Master → Sales → Technical → Pricing)
6. Performance Optimization (Already integrated)
7. Compliance & Audit (Compliance checks + audit logging)
8. Analytics & Reporting (Metrics collection across all stages)
"""

import sys
import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# Project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Pipeline Stage Definitions
# =============================================================================

class PipelineStage(Enum):
    """All stages in the end-to-end pipeline"""
    RFP_INTAKE = "rfp_intake"
    PDF_EXTRACTION = "pdf_extraction"
    TERM_MATCHING = "term_matching"
    DB_STORAGE = "db_storage"
    AGENT_ORCHESTRATION = "agent_orchestration"
    TECHNICAL_ANALYSIS = "technical_analysis"
    VECTOR_SEARCH = "vector_search"
    SPEC_MATCHING = "spec_matching"
    PRICING_CALCULATION = "pricing_calculation"
    BID_GENERATION = "bid_generation"
    COMPLIANCE_CHECK = "compliance_check"
    AUDIT_LOGGING = "audit_logging"
    ANALYTICS_TRACKING = "analytics_tracking"
    VENDOR_INTEGRATION = "vendor_integration"
    COMPLETED = "completed"
    ERROR = "error"


class PipelineStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class StageResult:
    """Result from a pipeline stage"""
    stage: str
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PipelineContext:
    """Context passed through the pipeline"""
    pipeline_id: str
    rfp_id: str = ""
    pdf_path: str = ""
    vendor_info: Dict[str, Any] = field(default_factory=dict)
    extracted_text: str = ""
    requirements: List[Dict[str, Any]] = field(default_factory=list)
    matched_products: List[Dict[str, Any]] = field(default_factory=list)
    pricing_data: Dict[str, Any] = field(default_factory=dict)
    bid_data: Dict[str, Any] = field(default_factory=dict)
    compliance_results: Dict[str, Any] = field(default_factory=dict)
    audit_entries: List[Dict[str, Any]] = field(default_factory=list)
    analytics_data: Dict[str, Any] = field(default_factory=dict)
    stage_results: List[StageResult] = field(default_factory=list)
    current_stage: str = ""
    status: str = PipelineStatus.PENDING.value
    errors: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_stage_result(self, result: StageResult):
        self.stage_results.append(result)
        self.current_stage = result.stage

    def to_dict(self) -> Dict[str, Any]:
        return {
            'pipeline_id': self.pipeline_id,
            'rfp_id': self.rfp_id,
            'status': self.status,
            'current_stage': self.current_stage,
            'created_at': self.created_at,
            'stage_results': [asdict(r) for r in self.stage_results],
            'matched_products': self.matched_products,
            'matched_products_count': len(self.matched_products),
            'requirements': self.requirements,
            'requirements_count': len(self.requirements),
            'has_pricing': bool(self.pricing_data),
            'has_bid': bool(self.bid_data),
            'pricing_data': self.pricing_data,
            'compliance_status': self.compliance_results.get('status', 'not_checked'),
            'errors': self.errors,
        }


# =============================================================================
# Module Loaders (lazy imports with graceful fallback)
# =============================================================================

class _ModuleLoader:
    """Lazily loads pipeline modules with graceful fallback"""

    def __init__(self):
        self._cache = {}

    # -- Pipeline 1: PDF Extraction --
    def get_pdf_extraction_manager(self):
        if 'pdf_mgr' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'pdf_extraction'))
                from pdf_extraction.pdf_extraction_manager import PDFExtractionManager
                self._cache['pdf_mgr'] = PDFExtractionManager()
                logger.info("✅ PDFExtractionManager loaded")
            except Exception as e:
                logger.warning(f"PDFExtractionManager not available: {e}")
                self._cache['pdf_mgr'] = None
        return self._cache['pdf_mgr']

    def get_rfp_terms_matcher(self):
        if 'terms_matcher' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'pdf_extraction'))
                from pdf_extraction.rfp_terms_matcher import RFPTermsMatcher
                self._cache['terms_matcher'] = RFPTermsMatcher()
                logger.info("✅ RFPTermsMatcher loaded")
            except Exception as e:
                logger.warning(f"RFPTermsMatcher not available: {e}")
                self._cache['terms_matcher'] = None
        return self._cache['terms_matcher']

    # -- Pipeline 2: Spec Matching --
    def get_spec_matcher(self):
        if 'spec_matcher' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'agents'))
                from agents.technical_agent.spec_matcher import TechnicalAgent as SpecTechnicalAgent
                self._cache['spec_matcher'] = SpecTechnicalAgent()
                logger.info("✅ TechnicalAgent (spec_matcher) loaded")
            except Exception as e:
                logger.warning(f"TechnicalAgent (spec_matcher) not available: {e}")
                self._cache['spec_matcher'] = None
        return self._cache['spec_matcher']

    def get_technical_agent(self):
        if 'tech_agent' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'agents'))
                from agents.technical_agent.technical_agent import TechnicalAgent as FullTechnicalAgent
                self._cache['tech_agent'] = FullTechnicalAgent()
                logger.info("✅ TechnicalAgent (full) loaded")
            except Exception as e:
                logger.warning(f"TechnicalAgent (full) not available: {e}")
                self._cache['tech_agent'] = None
        return self._cache['tech_agent']

    # -- Pipeline 2: Vector Embeddings --
    def get_vector_embeddings(self):
        if 'vector_emb' not in self._cache:
            try:
                from database.vector_embeddings import VectorEmbeddingManager
                self._cache['vector_emb'] = VectorEmbeddingManager()
                logger.info("✅ VectorEmbeddingManager loaded")
            except Exception as e:
                logger.warning(f"VectorEmbeddingManager not available: {e}")
                self._cache['vector_emb'] = None
        return self._cache['vector_emb']

    def get_chromadb_manager(self):
        if 'chroma_mgr' not in self._cache:
            try:
                from database.chromadb_setup import ChromaDBManager
                self._cache['chroma_mgr'] = ChromaDBManager()
                logger.info("✅ ChromaDBManager loaded")
            except Exception as e:
                logger.warning(f"ChromaDBManager not available: {e}")
                self._cache['chroma_mgr'] = None
        return self._cache['chroma_mgr']

    # -- Pipeline 3: Pricing --
    def get_pricing_agent(self):
        if 'pricing_agent' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'agents'))
                from agents.pricing_agent.price_calculator import PricingAgent
                self._cache['pricing_agent'] = PricingAgent()
                logger.info("✅ PricingAgent loaded")
            except Exception as e:
                logger.warning(f"PricingAgent not available: {e}")
                self._cache['pricing_agent'] = None
        return self._cache['pricing_agent']

    def get_bid_generator(self):
        if 'bid_gen' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'rfp_responser'))
                from rfp_responser.bid_document_generator import PDFBidGenerator, ExcelBidGenerator
                self._cache['bid_gen'] = {
                    'pdf': PDFBidGenerator(),
                    'excel': ExcelBidGenerator()
                }
                logger.info("✅ Bid generators loaded")
            except Exception as e:
                logger.warning(f"Bid generators not available: {e}")
                self._cache['bid_gen'] = None
        return self._cache['bid_gen']

    def get_bid_price_calculator(self):
        if 'bid_calc' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'rfp_responser'))
                from rfp_responser.bid_price_calculator import BidPriceCalculator
                self._cache['bid_calc'] = BidPriceCalculator()
                logger.info("✅ BidPriceCalculator loaded")
            except Exception as e:
                logger.warning(f"BidPriceCalculator not available: {e}")
                self._cache['bid_calc'] = None
        return self._cache['bid_calc']

    # -- Pipeline 4: Vendor Management --
    def get_vendor_bridge_pdf(self):
        if 'vb_pdf' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'pdf_extraction'))
                from pdf_extraction.vendor_bridge import PDFVendorBridge
                self._cache['vb_pdf'] = PDFVendorBridge()
                logger.info("✅ PDFVendorBridge loaded")
            except Exception as e:
                logger.warning(f"PDFVendorBridge not available: {e}")
                self._cache['vb_pdf'] = None
        return self._cache['vb_pdf']

    def get_vendor_bridge_spec(self):
        if 'vb_spec' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'spec_comparer'))
                from spec_comparer.vendor_bridge import SpecVendorBridge
                self._cache['vb_spec'] = SpecVendorBridge()
                logger.info("✅ SpecVendorBridge loaded")
            except Exception as e:
                logger.warning(f"SpecVendorBridge not available: {e}")
                self._cache['vb_spec'] = None
        return self._cache['vb_spec']

    # -- Pipeline 5: Master Agent --
    def get_master_agent(self):
        if 'master_agent' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'agents'))
                from agents.master_agent.orchestrator import MasterAgent
                self._cache['master_agent'] = MasterAgent()
                logger.info("✅ MasterAgent loaded")
            except Exception as e:
                logger.warning(f"MasterAgent not available: {e}")
                self._cache['master_agent'] = None
        return self._cache['master_agent']

    def get_main_orchestrator(self):
        if 'main_orch' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'agents'))
                from agents.master_agent.main_orchestrator import MainOrchestrator
                self._cache['main_orch'] = MainOrchestrator()
                logger.info("✅ MainOrchestrator loaded")
            except Exception as e:
                logger.warning(f"MainOrchestrator not available: {e}")
                self._cache['main_orch'] = None
        return self._cache['main_orch']

    def get_sales_agent(self):
        if 'sales_agent' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'agents'))
                from agents.sales_agent.rfp_scanner import SalesAgent
                self._cache['sales_agent'] = SalesAgent()
                logger.info("✅ SalesAgent loaded")
            except Exception as e:
                logger.warning(f"SalesAgent not available: {e}")
                self._cache['sales_agent'] = None
        return self._cache['sales_agent']

    # -- Pipeline 7: Compliance & Audit --
    def get_compliance_checker(self):
        if 'compliance' not in self._cache:
            try:
                from compliance_and_standards.compliance_checker import ComplianceRuleEngine
                self._cache['compliance'] = ComplianceRuleEngine()
                logger.info("✅ ComplianceRuleEngine loaded")
            except Exception as e:
                logger.warning(f"ComplianceRuleEngine not available: {e}")
                self._cache['compliance'] = None
        return self._cache['compliance']

    def get_audit_trail(self):
        if 'audit' not in self._cache:
            try:
                from audit_and_trailing.audit_trail import AuditTrailDatabase, AuditEntry, AuditActionType, AuditEntityType
                db_path = PROJECT_ROOT / 'database' / 'db_audit' / 'audit.db'
                db_path.parent.mkdir(parents=True, exist_ok=True)
                self._cache['audit'] = AuditTrailDatabase(str(db_path))
                self._cache['audit_classes'] = {
                    'AuditEntry': AuditEntry,
                    'AuditActionType': AuditActionType,
                    'AuditEntityType': AuditEntityType,
                }
                logger.info("✅ AuditTrailDatabase loaded")
            except Exception as e:
                logger.warning(f"AuditTrailDatabase not available: {e}")
                self._cache['audit'] = None
                self._cache['audit_classes'] = {}
        return self._cache['audit']

    def get_audit_classes(self) -> Dict:
        self.get_audit_trail()  # ensure loaded
        return self._cache.get('audit_classes', {})

    # -- Pipeline 8: Analytics --
    def get_analytics(self):
        if 'analytics' not in self._cache:
            try:
                from analytics import MetricsCollector, RFPMetricsTracker, DashboardAPI
                self._cache['analytics'] = {
                    'collector': MetricsCollector,
                    'rfp_tracker': RFPMetricsTracker,
                    'dashboard': DashboardAPI,
                }
                logger.info("✅ Analytics modules loaded")
            except Exception as e:
                logger.warning(f"Analytics modules not available: {e}")
                self._cache['analytics'] = None
        return self._cache['analytics']

    # -- Database Layer --
    def get_db_manager(self):
        if 'db_manager' not in self._cache:
            try:
                from database.db_engine import DatabaseManager
                self._cache['db_manager'] = DatabaseManager()
                logger.info("✅ DatabaseManager loaded")
            except Exception as e:
                logger.warning(f"DatabaseManager not available: {e}")
                self._cache['db_manager'] = None
        return self._cache['db_manager']

    def get_crud_repos(self):
        if 'crud' not in self._cache:
            try:
                from database.crud import (
                    ProductRepository, RFPRepository, MatchRepository,
                    BidRepository, AgentLogRepository
                )
                db_mgr = self.get_db_manager()
                if db_mgr:
                    session = db_mgr.get_session()
                    self._cache['crud'] = {
                        'product': ProductRepository(session),
                        'rfp': RFPRepository(session),
                        'match': MatchRepository(session),
                        'bid': BidRepository(session),
                        'agent_log': AgentLogRepository(session),
                        '_session': session,
                    }
                    logger.info("✅ CRUD repositories loaded")
                else:
                    self._cache['crud'] = None
            except Exception as e:
                logger.warning(f"CRUD repositories not available: {e}")
                self._cache['crud'] = None
        return self._cache['crud']

    def get_rfp_workflow_manager(self):
        if 'rfp_wf' not in self._cache:
            try:
                sys.path.insert(0, str(PROJECT_ROOT / 'rfp_responser'))
                from rfp_responser.rfp_workflow import RFPWorkflowManager
                self._cache['rfp_wf'] = RFPWorkflowManager()
                logger.info("✅ RFPWorkflowManager loaded")
            except Exception as e:
                logger.warning(f"RFPWorkflowManager not available: {e}")
                self._cache['rfp_wf'] = None
        return self._cache['rfp_wf']

    def reset(self):
        """Reset all cached modules"""
        self._cache.clear()


# Singleton loader
_loader = _ModuleLoader()


def get_module_loader() -> _ModuleLoader:
    return _loader


# =============================================================================
# Pipeline 1: RFP Intake & Processing
# =============================================================================

class RFPIntakePipeline:
    """
    Pipeline 1: RFP Intake
    PDF Upload → Text Extraction → Term Matching → DB Storage
    """

    def __init__(self, loader: _ModuleLoader = None):
        self.loader = loader or _loader

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """Execute the RFP intake pipeline"""
        import time

        # Stage 1a: Extract PDF content
        start = time.time()
        try:
            pdf_mgr = self.loader.get_pdf_extraction_manager()
            if pdf_mgr and ctx.pdf_path and os.path.isfile(ctx.pdf_path):
                filename = os.path.basename(ctx.pdf_path)
                unique_id = pdf_mgr.generate_unique_id(filename)
                text, page_info = pdf_mgr.extract_text_from_pdf(ctx.pdf_path)
                ctx.extracted_text = text
                ctx.rfp_id = unique_id
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.PDF_EXTRACTION.value,
                    status='success',
                    data={'pages': len(page_info) if page_info else 0, 'text_length': len(text)},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                # No PDF manager or no file — accept pre-supplied text
                if not ctx.extracted_text:
                    ctx.extracted_text = ""
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.PDF_EXTRACTION.value,
                    status='skipped',
                    data={'reason': 'no_pdf_or_manager'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"PDF extraction failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.PDF_EXTRACTION.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        # Stage 1b: Match RFP terms
        start = time.time()
        try:
            matcher = self.loader.get_rfp_terms_matcher()
            if matcher and ctx.extracted_text:
                match_result = matcher.parse_rfp_text(ctx.extracted_text)
                extracted_fields = match_result.get('extracted_fields', {})
                # Build requirements list from extracted fields
                requirements = []
                for field_name, field_value in extracted_fields.items():
                    requirements.append({
                        'field': field_name,
                        'value': field_value,
                        'source': 'rfp_terms_matcher',
                    })
                ctx.requirements = requirements
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.TERM_MATCHING.value,
                    status='success',
                    data={'terms_found': len(requirements)},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.TERM_MATCHING.value,
                    status='skipped',
                    data={'reason': 'no_matcher_or_text'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Term matching failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.TERM_MATCHING.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        # Stage 1c: Store in database
        start = time.time()
        try:
            repos = self.loader.get_crud_repos()
            if repos and repos.get('rfp'):
                rfp_repo = repos['rfp']
                from database.models import RFPStatus

                rfp_record = rfp_repo.create(
                    rfp_id=ctx.rfp_id or f"RFP-{uuid.uuid4().hex[:8].upper()}",
                    title=f"RFP {ctx.rfp_id}",
                    status=RFPStatus.IN_PROGRESS,
                    raw_text=ctx.extracted_text[:5000] if ctx.extracted_text else '',
                )
                if rfp_record:
                    ctx.rfp_id = str(getattr(rfp_record, 'id', ctx.rfp_id))
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.DB_STORAGE.value,
                    status='success',
                    data={'rfp_id': ctx.rfp_id},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.DB_STORAGE.value,
                    status='skipped',
                    data={'reason': 'no_db_repos'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"DB storage failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.DB_STORAGE.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        return ctx


# =============================================================================
# Pipeline 2: Product Matching Engine
# =============================================================================

class ProductMatchingPipeline:
    """
    Pipeline 2: Product Matching
    Requirements → Vector Search → Spec Matching → Top-K Selection
    """

    def __init__(self, loader: _ModuleLoader = None):
        self.loader = loader or _loader

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        import time

        # Stage 2a: Vector semantic search
        start = time.time()
        semantic_results = []
        try:
            chroma_mgr = self.loader.get_chromadb_manager()
            if chroma_mgr and ctx.requirements:
                # Build query from requirements
                query_texts = []
                for req in ctx.requirements[:20]:  # limit to first 20
                    val = req.get('value', '')
                    if isinstance(val, str) and len(val) > 3:
                        query_texts.append(val)
                    elif isinstance(val, dict):
                        query_texts.append(json.dumps(val))

                if query_texts:
                    for qt in query_texts[:10]:
                        try:
                            results = chroma_mgr.search_products(qt, n_results=5)
                            if results:
                                semantic_results.extend(results)
                        except Exception:
                            pass

                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.VECTOR_SEARCH.value,
                    status='success',
                    data={'semantic_matches': len(semantic_results)},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.VECTOR_SEARCH.value,
                    status='skipped',
                    data={'reason': 'no_chromadb_or_requirements'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Vector search failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.VECTOR_SEARCH.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        # Stage 2b: Specification matching via TechnicalAgent
        start = time.time()
        try:
            spec_matcher = self.loader.get_spec_matcher()
            if spec_matcher and ctx.requirements:
                rfp_context = {
                    'rfp_id': ctx.rfp_id,
                    'products_in_scope': [
                        {
                            'name': req.get('field', 'unknown'),
                            'specifications': req.get('value', {}) if isinstance(req.get('value'), dict) else {},
                            'quantity': 1,
                            'unit': 'lot',
                        }
                        for req in ctx.requirements
                        if req.get('value')
                    ],
                }
                match_result = spec_matcher.process_rfp(rfp_context)
                matched = match_result.get('recommendations', match_result.get('products', []))
                if isinstance(matched, list):
                    ctx.matched_products = matched
                else:
                    ctx.matched_products = [matched] if matched else []

                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.SPEC_MATCHING.value,
                    status='success',
                    data={'matched_products': len(ctx.matched_products)},
                    duration_ms=(time.time() - start) * 1000,
                ))
            elif semantic_results:
                # Fall back to semantic results
                ctx.matched_products = semantic_results[:3]
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.SPEC_MATCHING.value,
                    status='partial',
                    data={'matched_products': len(ctx.matched_products), 'source': 'semantic_fallback'},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.SPEC_MATCHING.value,
                    status='skipped',
                    data={'reason': 'no_matcher_or_requirements'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Spec matching failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.SPEC_MATCHING.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        # Enrich with vendor data
        start = time.time()
        try:
            vb_spec = self.loader.get_vendor_bridge_spec()
            if vb_spec and ctx.matched_products:
                for prod in ctx.matched_products:
                    try:
                        enriched = vb_spec.enrich_with_vendor_data(prod)
                        if enriched:
                            prod.update(enriched)
                    except Exception:
                        pass
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.VENDOR_INTEGRATION.value,
                    status='success',
                    data={'enriched_count': len(ctx.matched_products)},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.VENDOR_INTEGRATION.value,
                status='skipped',
                data={'reason': str(e)},
                duration_ms=(time.time() - start) * 1000,
            ))

        return ctx


# =============================================================================
# Pipeline 3: Pricing & Commercial Bid
# =============================================================================

class PricingBidPipeline:
    """
    Pipeline 3: Pricing & Bid Generation
    Matched Products → Price Calculation → Bid Document
    """

    def __init__(self, loader: _ModuleLoader = None):
        self.loader = loader or _loader

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        import time

        # Stage 3a: Calculate pricing via PricingAgent
        start = time.time()
        try:
            pricing_agent = self.loader.get_pricing_agent()
            if pricing_agent and ctx.matched_products:
                pricing_input = {
                    'rfp_id': ctx.rfp_id,
                    'product_recommendations': ctx.matched_products,
                    'tests_required': [
                        req.get('value', '')
                        for req in ctx.requirements
                        if 'test' in str(req.get('field', '')).lower()
                    ],
                }
                pricing_result = pricing_agent.calculate_pricing(pricing_input)
                ctx.pricing_data = pricing_result if isinstance(pricing_result, dict) else {'result': pricing_result}
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.PRICING_CALCULATION.value,
                    status='success',
                    data={
                        'total_material': ctx.pricing_data.get('total_material_cost', 0),
                        'total_services': ctx.pricing_data.get('total_services_cost', 0),
                        'grand_total': ctx.pricing_data.get('grand_total', 0),
                    },
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                # Build basic pricing from matched products
                total = 0
                for prod in ctx.matched_products:
                    price = prod.get('unit_price', 0)
                    qty = prod.get('quantity', 1)
                    total += price * qty
                ctx.pricing_data = {
                    'total_material_cost': total,
                    'total_services_cost': 0,
                    'taxes': {'gst': total * 0.18},
                    'grand_total': total * 1.18,
                    'source': 'basic_calculation',
                }
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.PRICING_CALCULATION.value,
                    status='partial',
                    data={'grand_total': ctx.pricing_data['grand_total'], 'source': 'basic'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Pricing failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.PRICING_CALCULATION.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        # Stage 3b: Generate bid document
        start = time.time()
        try:
            bid_gen = self.loader.get_bid_generator()
            if bid_gen and ctx.pricing_data:
                bid_data = {
                    'rfp_id': ctx.rfp_id,
                    'pipeline_id': ctx.pipeline_id,
                    'vendor_info': ctx.vendor_info,
                    'products': ctx.matched_products,
                    'pricing': ctx.pricing_data,
                    'generated_at': datetime.now().isoformat(),
                }
                ctx.bid_data = bid_data

                # Try PDF generation
                try:
                    pdf_gen = bid_gen.get('pdf')
                    if pdf_gen:
                        pdf_bytes = pdf_gen.generate(bid_data)
                        if pdf_bytes:
                            bid_data['pdf_size_bytes'] = len(pdf_bytes)
                except Exception:
                    pass

                # Try Excel generation
                try:
                    excel_gen = bid_gen.get('excel')
                    if excel_gen:
                        excel_bytes = excel_gen.generate(bid_data)
                        if excel_bytes:
                            bid_data['excel_size_bytes'] = len(excel_bytes)
                except Exception:
                    pass

                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.BID_GENERATION.value,
                    status='success',
                    data={'has_pdf': 'pdf_size_bytes' in bid_data, 'has_excel': 'excel_size_bytes' in bid_data},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.bid_data = {
                    'rfp_id': ctx.rfp_id,
                    'products': ctx.matched_products,
                    'pricing': ctx.pricing_data,
                    'generated_at': datetime.now().isoformat(),
                    'format': 'json_only',
                }
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.BID_GENERATION.value,
                    status='partial',
                    data={'format': 'json_only'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Bid generation failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.BID_GENERATION.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        return ctx


# =============================================================================
# Pipeline 7: Compliance & Audit
# =============================================================================

class ComplianceAuditPipeline:
    """
    Pipeline 7: Compliance & Audit
    Check compliance rules → Log audit trail
    """

    def __init__(self, loader: _ModuleLoader = None):
        self.loader = loader or _loader

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        import time

        # Stage 7a: Compliance checking
        start = time.time()
        try:
            compliance = self.loader.get_compliance_checker()
            if compliance and ctx.matched_products:
                findings = []
                for product in ctx.matched_products:
                    specs = product.get('specifications', product)
                    try:
                        result = compliance.check_compliance(specs)
                        findings.append({
                            'product': product.get('name', product.get('sku', 'unknown')),
                            'result': result,
                        })
                    except Exception:
                        findings.append({
                            'product': product.get('name', 'unknown'),
                            'result': {'status': 'check_failed'},
                        })
                ctx.compliance_results = {
                    'status': 'checked',
                    'products_checked': len(findings),
                    'findings': findings,
                }
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.COMPLIANCE_CHECK.value,
                    status='success',
                    data={'products_checked': len(findings)},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.compliance_results = {'status': 'not_checked', 'reason': 'no_products'}
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.COMPLIANCE_CHECK.value,
                    status='skipped',
                    data={'reason': 'no_compliance_engine_or_products'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Compliance check failed: {e}")
            ctx.compliance_results = {'status': 'error', 'error': str(e)}
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.COMPLIANCE_CHECK.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        # Stage 7b: Audit logging
        start = time.time()
        try:
            audit_db = self.loader.get_audit_trail()
            audit_classes = self.loader.get_audit_classes()
            if audit_db and audit_classes:
                AuditEntry = audit_classes['AuditEntry']
                AuditActionType = audit_classes['AuditActionType']
                AuditEntityType = audit_classes['AuditEntityType']

                entry = AuditEntry(
                    user_id='pipeline_system',
                    action=AuditActionType.CREATE,
                    entity_type=AuditEntityType.RFP,
                    entity_id=ctx.rfp_id,
                    description=f"Pipeline {ctx.pipeline_id} processed RFP {ctx.rfp_id}",
                    new_value={
                        'stages_completed': len(ctx.stage_results),
                        'products_matched': len(ctx.matched_products),
                        'has_pricing': bool(ctx.pricing_data),
                        'compliance_status': ctx.compliance_results.get('status', 'unknown'),
                    },
                    status='success' if not ctx.errors else 'partial',
                )
                audit_db.log_entry(entry)
                ctx.audit_entries.append(entry.to_dict())

                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.AUDIT_LOGGING.value,
                    status='success',
                    data={'audit_entry_id': entry.id},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.AUDIT_LOGGING.value,
                    status='skipped',
                    data={'reason': 'no_audit_db'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Audit logging failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.AUDIT_LOGGING.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        return ctx


# =============================================================================
# Pipeline 8: Analytics & Reporting
# =============================================================================

class AnalyticsPipeline:
    """
    Pipeline 8: Analytics
    Collect metrics from all stages → Store for dashboard
    """

    def __init__(self, loader: _ModuleLoader = None):
        self.loader = loader or _loader

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        import time

        start = time.time()
        try:
            analytics = self.loader.get_analytics()
            if analytics:
                # Collect pipeline metrics
                stage_durations = {
                    sr.stage: sr.duration_ms for sr in ctx.stage_results
                }
                stage_statuses = {
                    sr.stage: sr.status for sr in ctx.stage_results
                }
                success_count = sum(1 for sr in ctx.stage_results if sr.status == 'success')
                total_duration = sum(sr.duration_ms for sr in ctx.stage_results)

                ctx.analytics_data = {
                    'pipeline_id': ctx.pipeline_id,
                    'rfp_id': ctx.rfp_id,
                    'total_stages': len(ctx.stage_results),
                    'successful_stages': success_count,
                    'failed_stages': len(ctx.errors),
                    'total_duration_ms': total_duration,
                    'stage_durations': stage_durations,
                    'stage_statuses': stage_statuses,
                    'products_matched': len(ctx.matched_products),
                    'requirements_found': len(ctx.requirements),
                    'grand_total': ctx.pricing_data.get('grand_total', 0),
                    'compliance_status': ctx.compliance_results.get('status', 'not_checked'),
                    'timestamp': datetime.now().isoformat(),
                }

                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.ANALYTICS_TRACKING.value,
                    status='success',
                    data={'metrics_collected': len(ctx.analytics_data)},
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                # Basic analytics even without the full module
                ctx.analytics_data = {
                    'pipeline_id': ctx.pipeline_id,
                    'total_stages': len(ctx.stage_results),
                    'total_duration_ms': sum(sr.duration_ms for sr in ctx.stage_results),
                    'timestamp': datetime.now().isoformat(),
                }
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.ANALYTICS_TRACKING.value,
                    status='partial',
                    data={'reason': 'basic_analytics_only'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Analytics failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.ANALYTICS_TRACKING.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        return ctx


# =============================================================================
# Pipeline 5: Agent Orchestration (wraps Master Agent workflow)
# =============================================================================

class AgentOrchestrationPipeline:
    """
    Pipeline 5: Agent Orchestration
    Uses MasterAgent/MainOrchestrator to run Sales → Technical → Pricing
    """

    def __init__(self, loader: _ModuleLoader = None):
        self.loader = loader or _loader

    def execute_with_agents(self, ctx: PipelineContext, rfp_urls: List[str] = None) -> PipelineContext:
        """Run the full agent orchestration pipeline"""
        import time

        start = time.time()
        try:
            master = self.loader.get_master_agent()
            if master:
                response = master.run_full_workflow(rfp_urls)

                # Extract data from ConsolidatedResponse
                if hasattr(response, 'products_table'):
                    ctx.matched_products = response.products_table
                if hasattr(response, 'grand_total'):
                    ctx.pricing_data = {
                        'total_material_cost': response.total_material_cost,
                        'total_services_cost': response.total_services_cost,
                        'taxes': response.taxes,
                        'grand_total': response.grand_total,
                    }
                if hasattr(response, 'rfp_id'):
                    ctx.rfp_id = response.rfp_id

                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.AGENT_ORCHESTRATION.value,
                    status='success',
                    data={
                        'products': len(ctx.matched_products),
                        'grand_total': ctx.pricing_data.get('grand_total', 0),
                    },
                    duration_ms=(time.time() - start) * 1000,
                ))
            else:
                ctx.add_stage_result(StageResult(
                    stage=PipelineStage.AGENT_ORCHESTRATION.value,
                    status='skipped',
                    data={'reason': 'master_agent_not_available'},
                    duration_ms=(time.time() - start) * 1000,
                ))
        except Exception as e:
            ctx.errors.append(f"Agent orchestration failed: {e}")
            ctx.add_stage_result(StageResult(
                stage=PipelineStage.AGENT_ORCHESTRATION.value,
                status='error',
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            ))

        return ctx


# =============================================================================
# Master Pipeline Executor
# =============================================================================

class PipelineExecutor:
    """
    Master Pipeline Executor
    Runs all pipelines in sequence: Intake → Matching → Pricing → Compliance → Analytics

    Supports two modes:
    - Standard: PDF-based flow through all pipelines
    - Agent: Uses MasterAgent to drive Sales→Technical→Pricing then adds compliance/analytics
    """

    def __init__(self, loader: _ModuleLoader = None):
        self.loader = loader or _loader
        self.intake = RFPIntakePipeline(self.loader)
        self.matching = ProductMatchingPipeline(self.loader)
        self.pricing = PricingBidPipeline(self.loader)
        self.compliance = ComplianceAuditPipeline(self.loader)
        self.analytics = AnalyticsPipeline(self.loader)
        self.agent_orch = AgentOrchestrationPipeline(self.loader)

    def run(
        self,
        pdf_path: str = None,
        extracted_text: str = None,
        requirements: List[Dict] = None,
        vendor_info: Dict = None,
        use_agents: bool = False,
        rfp_urls: List[str] = None,
    ) -> PipelineContext:
        """
        Run the full end-to-end pipeline.

        Args:
            pdf_path: Path to an RFP PDF file
            extracted_text: Pre-extracted text (skip PDF extraction)
            requirements: Pre-parsed requirements (skip term matching)
            vendor_info: Vendor information for bid generation
            use_agents: If True, use MasterAgent orchestration instead of direct pipeline
            rfp_urls: URLs for agent-based RFP scanning

        Returns:
            PipelineContext with all results
        """
        pipeline_id = f"PL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        ctx = PipelineContext(
            pipeline_id=pipeline_id,
            pdf_path=pdf_path or '',
            extracted_text=extracted_text or '',
            requirements=requirements or [],
            vendor_info=vendor_info or {},
            status=PipelineStatus.RUNNING.value,
        )

        logger.info(f"🚀 Starting pipeline {pipeline_id}")

        try:
            if use_agents:
                # Agent-driven mode
                ctx = self.agent_orch.execute_with_agents(ctx, rfp_urls)
            else:
                # Standard pipeline mode
                # Pipeline 1: RFP Intake
                ctx = self.intake.execute(ctx)

                # Pipeline 2: Product Matching
                ctx = self.matching.execute(ctx)

            # Pipeline 3: Pricing & Bid (always runs)
            ctx = self.pricing.execute(ctx)

            # Pipeline 7: Compliance & Audit (always runs)
            ctx = self.compliance.execute(ctx)

            # Pipeline 8: Analytics (always runs)
            ctx = self.analytics.execute(ctx)

            # Determine final status
            error_stages = [sr for sr in ctx.stage_results if sr.status == 'error']
            if not error_stages:
                ctx.status = PipelineStatus.COMPLETED.value
            elif len(error_stages) < len(ctx.stage_results):
                ctx.status = PipelineStatus.PARTIAL.value
            else:
                ctx.status = PipelineStatus.FAILED.value

            logger.info(
                f"✅ Pipeline {pipeline_id} finished: {ctx.status} "
                f"({len(ctx.stage_results)} stages, {len(ctx.errors)} errors)"
            )

        except Exception as e:
            ctx.status = PipelineStatus.FAILED.value
            ctx.errors.append(f"Pipeline execution error: {e}")
            logger.error(f"❌ Pipeline {pipeline_id} failed: {e}")

        return ctx

    def run_rfp_workflow(self, pdf_path: str, vendor_info: Dict = None) -> PipelineContext:
        """Convenience: run the standard PDF-based RFP pipeline"""
        return self.run(pdf_path=pdf_path, vendor_info=vendor_info, use_agents=False)

    def run_agent_workflow(self, rfp_urls: List[str] = None) -> PipelineContext:
        """Convenience: run the agent-driven pipeline"""
        return self.run(use_agents=True, rfp_urls=rfp_urls)

    def run_from_text(self, text: str, vendor_info: Dict = None) -> PipelineContext:
        """Convenience: run pipeline from pre-extracted text"""
        return self.run(extracted_text=text, vendor_info=vendor_info)

    def run_from_requirements(self, requirements: List[Dict], vendor_info: Dict = None) -> PipelineContext:
        """Convenience: run pipeline from pre-parsed requirements"""
        return self.run(requirements=requirements, vendor_info=vendor_info)


# =============================================================================
# Public API
# =============================================================================

def create_pipeline() -> PipelineExecutor:
    """Create a new PipelineExecutor with default module loader"""
    return PipelineExecutor()


def run_full_pipeline(
    pdf_path: str = None,
    text: str = None,
    requirements: List[Dict] = None,
    vendor_info: Dict = None,
    use_agents: bool = False,
    rfp_urls: List[str] = None,
) -> Dict[str, Any]:
    """
    Run the complete pipeline and return results as a dict.

    This is the main entry point for the entire system.
    """
    executor = create_pipeline()
    ctx = executor.run(
        pdf_path=pdf_path,
        extracted_text=text,
        requirements=requirements,
        vendor_info=vendor_info,
        use_agents=use_agents,
        rfp_urls=rfp_urls,
    )
    return ctx.to_dict()
