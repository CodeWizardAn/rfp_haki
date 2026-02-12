"""
Technical Agent - Comprehensive RFP Analysis and Product Matching System

Features (51 total):
1. TechnicalAgent class structure
2. RFP requirement parser
3. LLM integration for understanding specs
4. Product requirement extractor
5. Scope of supply analyzer
6. Multi-item RFP handler
7. Product catalog querier
8. Specification matching orchestrator
9. Vector search integration
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
30. Output to pricing agent
31. Output to main agent
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
"""

import sys
import json
import logging
import hashlib
import threading
import time
import re
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Callable, Set, Union
from enum import Enum
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import uuid

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)


# ============================================================================
# Enums
# ============================================================================

class MatchConfidence(Enum):
    """Confidence levels for matches"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class RiskLevel(Enum):
    """Technical risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ComplianceStatus(Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


class ProcessingMode(Enum):
    """Processing modes"""
    SYNC = "sync"
    ASYNC = "async"
    BATCH = "batch"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class RFPRequirement:
    """Parsed RFP requirement"""
    id: str
    name: str
    description: str
    specifications: Dict[str, Any]
    quantity: float
    unit: str
    priority: str = "normal"
    standards: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductMatch:
    """Product match result"""
    product_id: str
    product_name: str
    manufacturer: str
    category: str
    specifications: Dict[str, Any]
    match_score: float
    confidence: MatchConfidence
    matched_specs: Dict[str, Dict[str, Any]]
    unmatched_specs: List[str]
    partial_matches: List[Dict[str, Any]]
    gap_analysis: Dict[str, Any]
    compliance_notes: List[str]
    risk_level: RiskLevel
    justification: str


@dataclass
class ComparisonRow:
    """Row in comparison table"""
    spec_name: str
    rfp_value: str
    product_values: Dict[str, str]
    match_status: Dict[str, str]


@dataclass
class TechnicalReport:
    """Complete technical analysis report"""
    rfp_id: str
    analysis_date: datetime
    requirements: List[RFPRequirement]
    recommendations: List[Dict[str, Any]]
    comparison_tables: List[List[ComparisonRow]]
    gap_analysis: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    compliance_summary: Dict[str, Any]
    technical_summary: str
    visualization_data: Dict[str, Any]


@dataclass
class AgentMessage:
    """Message for inter-agent communication"""
    id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None


@dataclass 
class WebhookConfig:
    """Webhook configuration"""
    url: str
    events: List[str]
    secret: Optional[str] = None
    enabled: bool = True
    retry_count: int = 3


# ============================================================================
# 35. Technical Agent Logging
# ============================================================================

class TechnicalAgentLogger:
    """Dedicated logger for Technical Agent"""
    
    def __init__(self, agent_id: str, log_dir: Optional[str] = None):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"TechnicalAgent.{agent_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(console)
        
        # File handler if log_dir specified
        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                log_path / f"technical_agent_{agent_id}.log"
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)8s | %(message)s'
            ))
            self.logger.addHandler(file_handler)
    
    def info(self, msg: str): self.logger.info(msg)
    def debug(self, msg: str): self.logger.debug(msg)
    def warning(self, msg: str): self.logger.warning(msg)
    def error(self, msg: str): self.logger.error(msg)
    def critical(self, msg: str): self.logger.critical(msg)


# ============================================================================
# 2. RFP Requirement Parser
# ============================================================================

class RFPRequirementParser:
    """Parses RFP documents to extract requirements"""
    
    # Known specification patterns
    SPEC_PATTERNS = {
        'cross_section': r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*mm|mm2|sqmm)',
        'voltage': r'(\d+(?:\.\d+)?)\s*(?:v|kv|volt)',
        'current': r'(\d+(?:\.\d+)?)\s*(?:a|amp|amps)',
        'temperature': r'(\d+(?:\.\d+)?)\s*(?:°c|deg\s*c|celsius)',
        'cores': r'(\d+)\s*(?:core|c)\b',
        'length': r'(\d+(?:\.\d+)?)\s*(?:m|meter|metre|km)',
    }
    
    # Standard patterns
    STANDARD_PATTERNS = [
        r'IS\s*\d+(?::\d+)?',
        r'IEC\s*\d+(?:-\d+)*',
        r'BS\s*\d+(?::\d+)?',
        r'ASTM\s*[A-Z]?\d+',
        r'IEEE\s*\d+',
    ]
    
    def __init__(self):
        self.logger = logging.getLogger("RFPParser")
    
    def parse(self, rfp_content: Dict[str, Any]) -> List[RFPRequirement]:
        """Parse RFP content and extract requirements"""
        requirements = []
        
        products = rfp_content.get('products_in_scope', [])
        if not products:
            products = rfp_content.get('scope_of_supply', [])
        if not products:
            products = rfp_content.get('items', [])
        
        for idx, product in enumerate(products):
            req = self._parse_product(product, idx)
            requirements.append(req)
        
        return requirements
    
    def _parse_product(self, product: Dict[str, Any], idx: int) -> RFPRequirement:
        """Parse a single product into requirement"""
        req_id = product.get('id', f"REQ_{idx+1:03d}")
        name = product.get('name', product.get('product_name', f"Product {idx+1}"))
        description = product.get('description', name)
        
        # Extract specifications
        specs = product.get('specifications', {})
        if not specs and 'specs' in product:
            specs = product['specs']
        
        # Parse additional specs from description
        parsed_specs = self._extract_specs_from_text(description)
        specs.update(parsed_specs)
        
        # Extract standards
        standards = product.get('standards', [])
        if not standards:
            standards = self._extract_standards(description)
            standards.extend(self._extract_standards(str(specs)))
        
        # Extract certifications
        certs = product.get('certifications', [])
        if not certs:
            certs = self._extract_certifications(description)
        
        return RFPRequirement(
            id=req_id,
            name=name,
            description=description,
            specifications=specs,
            quantity=float(product.get('quantity', 1)),
            unit=product.get('unit', 'Nos'),
            priority=product.get('priority', 'normal'),
            standards=standards,
            certifications=certs,
            metadata=product.get('metadata', {})
        )
    
    def _extract_specs_from_text(self, text: str) -> Dict[str, Any]:
        """Extract specifications from text using patterns"""
        specs = {}
        text_lower = text.lower()
        
        for spec_name, pattern in self.SPEC_PATTERNS.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1))
                    specs[spec_name] = value
                except ValueError:
                    specs[spec_name] = match.group(1)
        
        return specs
    
    def _extract_standards(self, text: str) -> List[str]:
        """Extract standard references from text"""
        standards = []
        for pattern in self.STANDARD_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            standards.extend(matches)
        return list(set(standards))
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certification requirements"""
        certs = []
        cert_keywords = ['BIS', 'ISI', 'ISO', 'CPRI', 'NABL', 'CE', 'UL']
        text_upper = text.upper()
        for cert in cert_keywords:
            if cert in text_upper:
                certs.append(cert)
        return certs


# ============================================================================
# 4. Product Requirement Extractor
# ============================================================================

class ProductRequirementExtractor:
    """Extracts detailed product requirements from RFP"""
    
    # Category detection keywords
    CATEGORY_KEYWORDS = {
        'power_cables': ['power cable', 'ht cable', 'lt cable', 'xlpe cable'],
        'control_cables': ['control cable', 'instrumentation cable'],
        'building_wires': ['building wire', 'house wire', 'pvc wire', 'flexible wire'],
        'specialty_cables': ['fire resistant', 'frls', 'marine cable', 'solar cable'],
    }
    
    # Material keywords
    MATERIAL_KEYWORDS = {
        'copper': ['copper', 'cu', 'electrolytic'],
        'aluminium': ['aluminium', 'aluminum', 'al'],
        'tinned_copper': ['tinned', 'tin plated'],
    }
    
    def __init__(self):
        self.logger = logging.getLogger("RequirementExtractor")
    
    def extract(self, requirement: RFPRequirement) -> Dict[str, Any]:
        """Extract detailed requirements from parsed requirement"""
        extracted = {
            'category': self._detect_category(requirement),
            'conductor_material': self._detect_material(requirement),
            'electrical_requirements': self._extract_electrical(requirement),
            'physical_requirements': self._extract_physical(requirement),
            'environmental_requirements': self._extract_environmental(requirement),
            'compliance_requirements': {
                'standards': requirement.standards,
                'certifications': requirement.certifications,
            },
            'quantity_info': {
                'quantity': requirement.quantity,
                'unit': requirement.unit,
            }
        }
        return extracted
    
    def _detect_category(self, req: RFPRequirement) -> str:
        """Detect product category"""
        text = f"{req.name} {req.description}".lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return "general"
    
    def _detect_material(self, req: RFPRequirement) -> str:
        """Detect conductor material"""
        text = f"{req.name} {req.description} {str(req.specifications)}".lower()
        for material, keywords in self.MATERIAL_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return material
        return "unknown"
    
    def _extract_electrical(self, req: RFPRequirement) -> Dict[str, Any]:
        """Extract electrical requirements"""
        specs = req.specifications
        return {
            'voltage_rating': specs.get('voltage_rating', specs.get('voltage_grade')),
            'current_rating': specs.get('current_rating', specs.get('current_rating_amps')),
            'frequency': specs.get('frequency'),
            'resistance': specs.get('resistance'),
        }
    
    def _extract_physical(self, req: RFPRequirement) -> Dict[str, Any]:
        """Extract physical requirements"""
        specs = req.specifications
        return {
            'cross_section': specs.get('cross_section_sqmm', specs.get('cross_section')),
            'number_of_cores': specs.get('number_of_cores', specs.get('cores')),
            'insulation_type': specs.get('insulation_type', specs.get('insulation')),
            'armour_type': specs.get('armour_type', specs.get('armour')),
            'outer_diameter': specs.get('outer_diameter'),
        }
    
    def _extract_environmental(self, req: RFPRequirement) -> Dict[str, Any]:
        """Extract environmental requirements"""
        specs = req.specifications
        return {
            'temperature_rating': specs.get('temperature_rating', specs.get('max_temp')),
            'flame_retardant': specs.get('flame_retardant', False),
            'uv_resistant': specs.get('uv_resistant', False),
            'oil_resistant': specs.get('oil_resistant', False),
        }


# ============================================================================
# 5. Scope of Supply Analyzer
# ============================================================================

class ScopeOfSupplyAnalyzer:
    """Analyzes scope of supply from RFP"""
    
    def __init__(self):
        self.logger = logging.getLogger("ScopeAnalyzer")
    
    def analyze(self, rfp_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scope of supply"""
        items = rfp_content.get('products_in_scope', [])
        
        analysis = {
            'total_items': len(items),
            'categories': self._categorize_items(items),
            'quantity_summary': self._summarize_quantities(items),
            'complexity_score': self._calculate_complexity(items),
            'estimated_value_range': self._estimate_value_range(items),
            'critical_items': self._identify_critical_items(items),
            'delivery_requirements': self._extract_delivery_requirements(rfp_content),
        }
        
        return analysis
    
    def _categorize_items(self, items: List[Dict]) -> Dict[str, int]:
        """Categorize items by type"""
        categories = {}
        for item in items:
            cat = item.get('category', 'uncategorized')
            categories[cat] = categories.get(cat, 0) + 1
        return categories
    
    def _summarize_quantities(self, items: List[Dict]) -> Dict[str, Any]:
        """Summarize quantities by unit"""
        by_unit = {}
        for item in items:
            unit = item.get('unit', 'Nos')
            qty = item.get('quantity', 1)
            if unit not in by_unit:
                by_unit[unit] = {'count': 0, 'total': 0}
            by_unit[unit]['count'] += 1
            by_unit[unit]['total'] += qty
        return by_unit
    
    def _calculate_complexity(self, items: List[Dict]) -> float:
        """Calculate scope complexity score (0-1)"""
        if not items:
            return 0.0
        
        # Factors: number of items, spec variety, special requirements
        base_score = min(len(items) / 50, 0.5)  # Up to 0.5 for item count
        
        spec_count = sum(len(item.get('specifications', {})) for item in items)
        spec_score = min(spec_count / 200, 0.3)  # Up to 0.3 for spec complexity
        
        special_count = sum(
            1 for item in items 
            if item.get('priority') == 'high' or item.get('special_requirements')
        )
        special_score = min(special_count / 10, 0.2)
        
        return round(base_score + spec_score + special_score, 2)
    
    def _estimate_value_range(self, items: List[Dict]) -> Dict[str, float]:
        """Estimate value range"""
        # Placeholder - would use pricing data in real implementation
        total_qty = sum(item.get('quantity', 1) for item in items)
        return {
            'min_estimate': total_qty * 100,
            'max_estimate': total_qty * 500,
            'currency': 'INR'
        }
    
    def _identify_critical_items(self, items: List[Dict]) -> List[str]:
        """Identify critical items"""
        critical = []
        for item in items:
            if item.get('priority') == 'high':
                critical.append(item.get('name', 'Unknown'))
            elif item.get('quantity', 0) > 10000:
                critical.append(item.get('name', 'Unknown'))
        return critical
    
    def _extract_delivery_requirements(self, rfp_content: Dict) -> Dict[str, Any]:
        """Extract delivery requirements"""
        return {
            'delivery_period': rfp_content.get('delivery_period'),
            'delivery_location': rfp_content.get('delivery_location'),
            'partial_delivery_allowed': rfp_content.get('partial_delivery', True),
        }


# ============================================================================
# 6. Multi-item RFP Handler
# ============================================================================

class MultiItemRFPHandler:
    """Handles RFPs with multiple items"""
    
    def __init__(self, max_parallel: int = 5):
        self.max_parallel = max_parallel
        self.executor = ThreadPoolExecutor(max_workers=max_parallel)
        self.logger = logging.getLogger("MultiItemHandler")
    
    def process_items(
        self, 
        requirements: List[RFPRequirement],
        processor: Callable[[RFPRequirement], Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple items, potentially in parallel"""
        if len(requirements) <= 3:
            # Process sequentially for small lists
            return [processor(req) for req in requirements]
        
        # Process in parallel for larger lists
        futures = [
            self.executor.submit(processor, req)
            for req in requirements
        ]
        
        results = []
        for future in futures:
            try:
                results.append(future.result(timeout=60))
            except Exception as e:
                self.logger.error(f"Error processing item: {e}")
                results.append({'error': str(e)})
        
        return results
    
    def group_by_category(self, requirements: List[RFPRequirement]) -> Dict[str, List[RFPRequirement]]:
        """Group requirements by category"""
        groups = {}
        for req in requirements:
            cat = req.metadata.get('category', 'general')
            if cat not in groups:
                groups[cat] = []
            groups[cat].append(req)
        return groups


# ============================================================================
# 7. Product Catalog Querier
# ============================================================================

class ProductCatalogQuerier:
    """Queries product catalog for matching products"""
    
    def __init__(self):
        self.catalog: List[Dict[str, Any]] = []
        self.index: Dict[str, List[int]] = {}  # category -> product indices
        self.logger = logging.getLogger("CatalogQuerier")
        self._load_catalog()
    
    def _load_catalog(self):
        """Load product catalog from database"""
        try:
            from database.db_config import DatabaseConfig, DatabaseType
            db_path = DatabaseConfig.get_path(DatabaseType.OEM_PRODUCTS)
            if db_path.exists():
                with open(db_path, 'r') as f:
                    data = json.load(f)
                self.catalog = data.get('products', [])
                self._build_index()
                self.logger.info(f"Loaded {len(self.catalog)} products from catalog")
        except Exception as e:
            self.logger.warning(f"Could not load catalog: {e}")
    
    def _build_index(self):
        """Build category index for fast lookup"""
        self.index = {}
        for idx, product in enumerate(self.catalog):
            cat = product.get('category', 'general').lower()
            if cat not in self.index:
                self.index[cat] = []
            self.index[cat].append(idx)
    
    def query(
        self, 
        category: Optional[str] = None,
        specifications: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Query catalog for matching products"""
        candidates = []
        
        if category:
            indices = self.index.get(category.lower(), [])
            candidates = [self.catalog[i] for i in indices]
        else:
            candidates = self.catalog
        
        if specifications:
            candidates = self._filter_by_specs(candidates, specifications)
        
        return candidates[:limit]
    
    def _filter_by_specs(
        self, 
        products: List[Dict], 
        specs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter products by specifications"""
        filtered = []
        for product in products:
            prod_specs = product.get('specifications', {})
            match_count = 0
            for key, value in specs.items():
                if key in prod_specs:
                    match_count += 1
            if match_count > 0:
                filtered.append(product)
        return filtered
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID/SKU"""
        for product in self.catalog:
            if product.get('sku') == product_id or product.get('id') == product_id:
                return product
        return None


# ============================================================================
# 9. Vector Search Integration
# ============================================================================

class VectorSearchIntegration:
    """Integrates vector search for semantic matching"""
    
    def __init__(self):
        self.embedding_system = None
        self.logger = logging.getLogger("VectorSearch")
        self._initialize()
    
    def _initialize(self):
        """Initialize vector embedding system"""
        try:
            from database.vector_embeddings import VectorEmbeddingSystem
            self.embedding_system = VectorEmbeddingSystem()
            self.logger.info("Vector embedding system initialized")
        except ImportError:
            self.logger.warning("Vector embedding system not available")
    
    def search_similar(
        self, 
        query_text: str, 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar products using vector embeddings"""
        if not self.embedding_system:
            return []
        
        try:
            results = self.embedding_system.search(query_text, top_k=top_k)
            return results
        except Exception as e:
            self.logger.error(f"Vector search error: {e}")
            return []
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text"""
        if not self.embedding_system:
            return None
        try:
            return self.embedding_system.get_embedding(text)
        except Exception:
            return None


# ============================================================================
# 8 & 10. Specification Matching Orchestrator with Weighted Matching
# ============================================================================

class SpecificationMatchingOrchestrator:
    """Orchestrates specification matching with weighted scoring"""
    
    # Default specification weights
    DEFAULT_WEIGHTS = {
        'conductor_material': 1.0,
        'cross_section_sqmm': 1.0,
        'voltage_rating': 1.0,
        'insulation_type': 0.9,
        'number_of_cores': 0.9,
        'current_rating': 0.8,
        'armour_type': 0.8,
        'temperature_rating': 0.7,
        'standard': 0.7,
        'outer_sheath': 0.6,
    }
    
    # Semantic equivalence maps
    EQUIVALENCE_MAPS = {
        'conductor_material': {
            'copper': ['copper', 'electrolytic copper', 'etp copper', 'cu'],
            'aluminium': ['aluminium', 'aluminum', 'al', 'ec aluminium'],
        },
        'insulation_type': {
            'pvc': ['pvc', 'pvc type a', 'fr pvc', 'frls pvc'],
            'xlpe': ['xlpe', 'cross-linked polyethylene', 'crosslinked pe'],
        },
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.catalog_querier = ProductCatalogQuerier()
        self.vector_search = VectorSearchIntegration()
        self.logger = logging.getLogger("MatchingOrchestrator")
    
    def find_matches(
        self, 
        requirement: RFPRequirement,
        use_vector_search: bool = True
    ) -> List[ProductMatch]:
        """Find matching products for a requirement"""
        # Get candidates from catalog
        category = requirement.metadata.get('category')
        candidates = self.catalog_querier.query(
            category=category,
            specifications=requirement.specifications,
            limit=100
        )
        
        # Optionally add vector search results
        if use_vector_search:
            query_text = f"{requirement.name} {requirement.description}"
            vector_results = self.vector_search.search_similar(query_text, top_k=20)
            for result in vector_results:
                if result not in candidates:
                    candidates.append(result)
        
        # Score all candidates
        matches = []
        for candidate in candidates:
            match = self._score_candidate(requirement, candidate)
            matches.append(match)
        
        # Sort by score
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        return matches
    
    def _score_candidate(
        self, 
        requirement: RFPRequirement,
        candidate: Dict[str, Any]
    ) -> ProductMatch:
        """Score a candidate product against requirement"""
        rfp_specs = requirement.specifications
        cand_specs = candidate.get('specifications', {})
        
        matched_specs = {}
        unmatched_specs = []
        partial_matches = []
        total_weight = 0
        weighted_score = 0
        
        for spec_key, rfp_value in rfp_specs.items():
            weight = self.weights.get(spec_key, 0.5)
            total_weight += weight
            
            cand_value = cand_specs.get(spec_key)
            
            if cand_value is None:
                unmatched_specs.append(spec_key)
                continue
            
            # Calculate match score for this spec
            spec_score = self._compare_values(spec_key, rfp_value, cand_value)
            
            if spec_score >= 1.0:
                matched_specs[spec_key] = {
                    'rfp_value': rfp_value,
                    'product_value': cand_value,
                    'match': 'FULL'
                }
                weighted_score += weight * 1.0
            elif spec_score > 0:
                partial_matches.append({
                    'spec': spec_key,
                    'rfp_value': rfp_value,
                    'product_value': cand_value,
                    'match_percent': spec_score * 100
                })
                weighted_score += weight * spec_score
            else:
                unmatched_specs.append(spec_key)
        
        # Calculate final score
        final_score = (weighted_score / total_weight * 100) if total_weight > 0 else 0
        
        # Determine confidence
        confidence = self._calculate_confidence(final_score, len(matched_specs), len(unmatched_specs))
        
        # Calculate risk
        risk = self._assess_risk(unmatched_specs, rfp_specs)
        
        # Generate justification
        justification = self._generate_justification(
            matched_specs, unmatched_specs, partial_matches, final_score
        )
        
        # Gap analysis
        gap_analysis = self._analyze_gaps(rfp_specs, cand_specs, unmatched_specs)
        
        return ProductMatch(
            product_id=candidate.get('sku', candidate.get('id', '')),
            product_name=candidate.get('name', candidate.get('product_name', '')),
            manufacturer=candidate.get('manufacturer', ''),
            category=candidate.get('category', ''),
            specifications=cand_specs,
            match_score=round(final_score, 2),
            confidence=confidence,
            matched_specs=matched_specs,
            unmatched_specs=unmatched_specs,
            partial_matches=partial_matches,
            gap_analysis=gap_analysis,
            compliance_notes=candidate.get('certifications', []),
            risk_level=risk,
            justification=justification
        )
    
    def _compare_values(self, spec_key: str, rfp_value: Any, cand_value: Any) -> float:
        """Compare specification values"""
        # Check semantic equivalence
        if spec_key in self.EQUIVALENCE_MAPS:
            rfp_norm = self._normalize_to_category(spec_key, rfp_value)
            cand_norm = self._normalize_to_category(spec_key, cand_value)
            if rfp_norm and cand_norm and rfp_norm == cand_norm:
                return 1.0
        
        # Numeric comparison
        rfp_num = self._extract_numeric(rfp_value)
        cand_num = self._extract_numeric(cand_value)
        
        if rfp_num is not None and cand_num is not None:
            if rfp_num == cand_num:
                return 1.0
            if rfp_num != 0:
                diff_ratio = abs(rfp_num - cand_num) / abs(rfp_num)
                if diff_ratio <= 0.1:
                    return 0.95
                if diff_ratio <= 0.2:
                    return 0.8
            return 0
        
        # String comparison
        rfp_str = str(rfp_value).lower().strip()
        cand_str = str(cand_value).lower().strip()
        
        if rfp_str == cand_str:
            return 1.0
        if rfp_str in cand_str or cand_str in rfp_str:
            return 0.85
        
        return 0
    
    def _normalize_to_category(self, spec_key: str, value: Any) -> Optional[str]:
        """Normalize value to category using equivalence maps"""
        equiv_map = self.EQUIVALENCE_MAPS.get(spec_key, {})
        value_lower = str(value).lower().strip()
        
        for category, equivalents in equiv_map.items():
            if value_lower in equivalents or any(eq in value_lower for eq in equivalents):
                return category
        return None
    
    def _extract_numeric(self, value: Any) -> Optional[float]:
        """Extract numeric value"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r'([\d.]+)', value)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _calculate_confidence(
        self, 
        score: float, 
        matched_count: int, 
        unmatched_count: int
    ) -> MatchConfidence:
        """Calculate match confidence"""
        if score >= 95 and unmatched_count == 0:
            return MatchConfidence.VERY_HIGH
        if score >= 85:
            return MatchConfidence.HIGH
        if score >= 70:
            return MatchConfidence.MEDIUM
        if score >= 50:
            return MatchConfidence.LOW
        return MatchConfidence.VERY_LOW
    
    def _assess_risk(
        self, 
        unmatched: List[str], 
        rfp_specs: Dict[str, Any]
    ) -> RiskLevel:
        """Assess technical risk"""
        critical_specs = ['voltage_rating', 'current_rating', 'cross_section_sqmm']
        critical_unmatched = [s for s in unmatched if s in critical_specs]
        
        if len(critical_unmatched) >= 2:
            return RiskLevel.CRITICAL
        if len(critical_unmatched) == 1:
            return RiskLevel.HIGH
        if len(unmatched) > len(rfp_specs) * 0.3:
            return RiskLevel.MEDIUM
        if unmatched:
            return RiskLevel.LOW
        return RiskLevel.NONE
    
    def _generate_justification(
        self,
        matched: Dict,
        unmatched: List[str],
        partial: List[Dict],
        score: float
    ) -> str:
        """Generate match justification text"""
        parts = []
        
        if score >= 90:
            parts.append(f"Excellent match with {score:.1f}% specification alignment.")
        elif score >= 75:
            parts.append(f"Good match with {score:.1f}% specification alignment.")
        else:
            parts.append(f"Partial match with {score:.1f}% specification alignment.")
        
        if matched:
            parts.append(f"Fully matched: {', '.join(list(matched.keys())[:3])}.")
        
        if unmatched:
            parts.append(f"Unmatched specs: {', '.join(unmatched[:3])}.")
        
        return " ".join(parts)
    
    def _analyze_gaps(
        self,
        rfp_specs: Dict[str, Any],
        cand_specs: Dict[str, Any],
        unmatched: List[str]
    ) -> Dict[str, Any]:
        """Analyze gaps between requirement and product"""
        gaps = {
            'missing_specs': unmatched,
            'deviations': [],
            'recommendations': []
        }
        
        for spec in unmatched:
            if spec in rfp_specs:
                gaps['deviations'].append({
                    'spec': spec,
                    'required': rfp_specs[spec],
                    'available': cand_specs.get(spec, 'Not specified')
                })
        
        if len(unmatched) > 3:
            gaps['recommendations'].append("Consider custom product development")
        elif unmatched:
            gaps['recommendations'].append("Request manufacturer clarification on missing specs")
        
        return gaps


# ============================================================================
# 11. Top-K Selector (K=3)
# ============================================================================

class TopKSelector:
    """Selects top K products from matches"""
    
    def __init__(self, k: int = 3):
        self.k = k
    
    def select(
        self, 
        matches: List[ProductMatch],
        diversify: bool = True
    ) -> List[ProductMatch]:
        """Select top K matches"""
        if not matches:
            return []
        
        if not diversify:
            return matches[:self.k]
        
        # Diversify by manufacturer
        selected = []
        manufacturers_seen = set()
        
        for match in matches:
            if len(selected) >= self.k:
                break
            
            # Prefer diversity if score is close
            if match.manufacturer in manufacturers_seen:
                # Only add if significantly better than alternatives
                if len(selected) < self.k and (
                    not selected or 
                    match.match_score > selected[-1].match_score * 0.95
                ):
                    selected.append(match)
            else:
                selected.append(match)
                manufacturers_seen.add(match.manufacturer)
        
        # Fill remaining slots if needed
        for match in matches:
            if len(selected) >= self.k:
                break
            if match not in selected:
                selected.append(match)
        
        return selected[:self.k]


# ============================================================================
# 12 & 13. Match Score Calculator with Confidence Scoring
# ============================================================================

class MatchScoreCalculator:
    """Calculates comprehensive match scores with confidence"""
    
    def __init__(self):
        self.spec_weights = SpecificationMatchingOrchestrator.DEFAULT_WEIGHTS.copy()
    
    def calculate_composite_score(self, match: ProductMatch) -> Dict[str, Any]:
        """Calculate composite score with breakdown"""
        spec_score = match.match_score
        
        # Compliance bonus
        compliance_bonus = len(match.compliance_notes) * 2
        
        # Risk penalty
        risk_penalties = {
            RiskLevel.CRITICAL: -20,
            RiskLevel.HIGH: -10,
            RiskLevel.MEDIUM: -5,
            RiskLevel.LOW: -2,
            RiskLevel.NONE: 0
        }
        risk_penalty = risk_penalties.get(match.risk_level, 0)
        
        # Confidence adjustment
        confidence_multipliers = {
            MatchConfidence.VERY_HIGH: 1.0,
            MatchConfidence.HIGH: 0.95,
            MatchConfidence.MEDIUM: 0.85,
            MatchConfidence.LOW: 0.70,
            MatchConfidence.VERY_LOW: 0.50
        }
        conf_mult = confidence_multipliers.get(match.confidence, 0.5)
        
        # Final composite score
        composite = min(100, max(0, (spec_score + compliance_bonus + risk_penalty) * conf_mult))
        
        return {
            'spec_score': spec_score,
            'compliance_bonus': compliance_bonus,
            'risk_penalty': risk_penalty,
            'confidence_multiplier': conf_mult,
            'composite_score': round(composite, 2),
            'confidence_level': match.confidence.value
        }


# ============================================================================
# 14. Comparison Table Generator
# ============================================================================

class ComparisonTableGenerator:
    """Generates comparison tables for RFP vs products"""
    
    def generate(
        self,
        requirement: RFPRequirement,
        top_matches: List[ProductMatch]
    ) -> List[ComparisonRow]:
        """Generate comparison table"""
        rows = []
        
        # Header row with product info
        header_row = ComparisonRow(
            spec_name="Product SKU",
            rfp_value="-",
            product_values={f"product_{i+1}": m.product_id for i, m in enumerate(top_matches)},
            match_status={f"product_{i+1}": f"{m.match_score}%" for i, m in enumerate(top_matches)}
        )
        rows.append(header_row)
        
        # Manufacturer row
        mfr_row = ComparisonRow(
            spec_name="Manufacturer",
            rfp_value="-",
            product_values={f"product_{i+1}": m.manufacturer for i, m in enumerate(top_matches)},
            match_status={f"product_{i+1}": "-" for i in range(len(top_matches))}
        )
        rows.append(mfr_row)
        
        # Specification rows
        for spec_key, rfp_value in requirement.specifications.items():
            product_values = {}
            match_status = {}
            
            for i, match in enumerate(top_matches):
                key = f"product_{i+1}"
                prod_value = match.specifications.get(spec_key, 'N/A')
                product_values[key] = str(prod_value)
                
                if spec_key in match.matched_specs:
                    match_status[key] = "✓ Match"
                elif any(p['spec'] == spec_key for p in match.partial_matches):
                    partial = next(p for p in match.partial_matches if p['spec'] == spec_key)
                    match_status[key] = f"~{partial['match_percent']:.0f}%"
                elif spec_key in match.unmatched_specs:
                    match_status[key] = "✗ Gap"
                else:
                    match_status[key] = "-"
            
            rows.append(ComparisonRow(
                spec_name=spec_key,
                rfp_value=str(rfp_value),
                product_values=product_values,
                match_status=match_status
            ))
        
        return rows
    
    def to_dict(self, rows: List[ComparisonRow]) -> List[Dict[str, Any]]:
        """Convert rows to dictionary format"""
        return [
            {
                'specification': row.spec_name,
                'rfp_requirement': row.rfp_value,
                **{f'{k}_value': v for k, v in row.product_values.items()},
                **{f'{k}_status': v for k, v in row.match_status.items()}
            }
            for row in rows
        ]


# ============================================================================
# 15. Gap Analysis Generator
# ============================================================================

class GapAnalysisGenerator:
    """Generates gap analysis between requirements and products"""
    
    def generate(
        self,
        requirement: RFPRequirement,
        match: ProductMatch
    ) -> Dict[str, Any]:
        """Generate comprehensive gap analysis"""
        gaps = {
            'requirement_id': requirement.id,
            'product_id': match.product_id,
            'summary': {
                'total_specs': len(requirement.specifications),
                'matched': len(match.matched_specs),
                'partial': len(match.partial_matches),
                'gaps': len(match.unmatched_specs)
            },
            'critical_gaps': [],
            'non_critical_gaps': [],
            'mitigations': [],
            'recommendations': []
        }
        
        # Critical specs
        critical_specs = ['voltage_rating', 'current_rating', 'cross_section_sqmm', 
                         'conductor_material', 'insulation_type']
        
        for spec in match.unmatched_specs:
            gap_info = {
                'specification': spec,
                'required': requirement.specifications.get(spec),
                'available': match.specifications.get(spec, 'Not specified'),
                'impact': 'HIGH' if spec in critical_specs else 'MEDIUM'
            }
            
            if spec in critical_specs:
                gaps['critical_gaps'].append(gap_info)
            else:
                gaps['non_critical_gaps'].append(gap_info)
        
        # Generate mitigations
        if gaps['critical_gaps']:
            gaps['mitigations'].append({
                'type': 'custom_manufacturing',
                'description': 'Request custom product with required specifications',
                'estimated_lead_time': '4-6 weeks additional'
            })
        
        if gaps['non_critical_gaps']:
            gaps['mitigations'].append({
                'type': 'specification_deviation',
                'description': 'Submit deviation request with technical justification',
                'risk_level': 'LOW'
            })
        
        # Recommendations
        if match.match_score < 70:
            gaps['recommendations'].append('Consider alternative products or manufacturers')
        if len(gaps['critical_gaps']) > 2:
            gaps['recommendations'].append('Escalate to technical review committee')
        
        return gaps


# ============================================================================
# 16. Specification Explanation Generator
# ============================================================================

class SpecificationExplanationGenerator:
    """Generates explanations for specifications"""
    
    SPEC_EXPLANATIONS = {
        'conductor_material': "The material used for the electrical conductor. Copper offers better conductivity while aluminium is lighter and more economical.",
        'cross_section_sqmm': "The cross-sectional area of the conductor in square millimeters. Larger cross-sections allow higher current capacity.",
        'voltage_rating': "Maximum voltage the cable is designed to safely handle. Must meet or exceed application requirements.",
        'insulation_type': "The insulating material around the conductor. PVC is economical, XLPE offers better thermal performance.",
        'number_of_cores': "Number of insulated conductors within the cable. Determined by application requirements.",
        'armour_type': "Protective metallic layer for mechanical protection. Steel wire for heavy duty, unarmoured for light applications.",
        'temperature_rating': "Maximum operating temperature in degrees Celsius. Higher ratings needed for demanding environments.",
    }
    
    def explain_spec(self, spec_name: str, value: Any) -> Dict[str, str]:
        """Generate explanation for a specification"""
        return {
            'specification': spec_name,
            'value': str(value),
            'explanation': self.SPEC_EXPLANATIONS.get(
                spec_name, 
                f"Technical specification: {spec_name}"
            ),
            'importance': self._get_importance(spec_name)
        }
    
    def _get_importance(self, spec_name: str) -> str:
        """Get importance level of specification"""
        critical = ['voltage_rating', 'current_rating', 'cross_section_sqmm']
        important = ['conductor_material', 'insulation_type', 'armour_type']
        
        if spec_name in critical:
            return 'CRITICAL'
        if spec_name in important:
            return 'HIGH'
        return 'NORMAL'
    
    def explain_match(self, match: ProductMatch) -> str:
        """Generate overall match explanation"""
        explanations = []
        
        if match.match_score >= 90:
            explanations.append(f"Excellent match ({match.match_score}%) - Product closely aligns with requirements.")
        elif match.match_score >= 75:
            explanations.append(f"Good match ({match.match_score}%) - Minor deviations may need clarification.")
        else:
            explanations.append(f"Partial match ({match.match_score}%) - Significant gaps require attention.")
        
        if match.matched_specs:
            explanations.append(f"Fully matched specifications: {', '.join(list(match.matched_specs.keys())[:5])}")
        
        if match.unmatched_specs:
            explanations.append(f"Gaps in: {', '.join(match.unmatched_specs[:3])}")
        
        return " ".join(explanations)


# ============================================================================
# 17. Technical Risk Assessor
# ============================================================================

class TechnicalRiskAssessor:
    """Assesses technical risks for product recommendations"""
    
    # Risk factors and weights
    RISK_FACTORS = {
        'spec_gap_ratio': 0.3,
        'critical_spec_missing': 0.25,
        'low_confidence': 0.2,
        'no_certifications': 0.15,
        'unknown_manufacturer': 0.1
    }
    
    def assess(self, match: ProductMatch, requirement: RFPRequirement) -> Dict[str, Any]:
        """Assess technical risks"""
        risks = []
        overall_risk_score = 0
        
        # Specification gap ratio
        gap_ratio = len(match.unmatched_specs) / max(len(requirement.specifications), 1)
        if gap_ratio > 0.3:
            risks.append({
                'factor': 'High specification gap',
                'severity': 'HIGH',
                'description': f'{gap_ratio*100:.0f}% of specifications not matched',
                'mitigation': 'Request detailed spec sheet from manufacturer'
            })
            overall_risk_score += self.RISK_FACTORS['spec_gap_ratio'] * gap_ratio
        
        # Critical specs missing
        critical_specs = ['voltage_rating', 'current_rating', 'cross_section_sqmm']
        missing_critical = [s for s in match.unmatched_specs if s in critical_specs]
        if missing_critical:
            risks.append({
                'factor': 'Critical specifications missing',
                'severity': 'CRITICAL',
                'description': f'Missing: {", ".join(missing_critical)}',
                'mitigation': 'Cannot proceed without critical spec verification'
            })
            overall_risk_score += self.RISK_FACTORS['critical_spec_missing']
        
        # Low confidence
        if match.confidence in [MatchConfidence.LOW, MatchConfidence.VERY_LOW]:
            risks.append({
                'factor': 'Low matching confidence',
                'severity': 'MEDIUM',
                'description': 'Matching algorithm confidence is low',
                'mitigation': 'Manual verification recommended'
            })
            overall_risk_score += self.RISK_FACTORS['low_confidence']
        
        # Determine overall risk level
        if overall_risk_score >= 0.5 or any(r['severity'] == 'CRITICAL' for r in risks):
            risk_level = RiskLevel.CRITICAL
        elif overall_risk_score >= 0.3:
            risk_level = RiskLevel.HIGH
        elif overall_risk_score >= 0.15:
            risk_level = RiskLevel.MEDIUM
        elif risks:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.NONE
        
        return {
            'overall_risk_level': risk_level.value,
            'risk_score': round(overall_risk_score, 3),
            'identified_risks': risks,
            'recommendation': self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: RiskLevel) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            RiskLevel.CRITICAL: "Do not proceed. Requires alternative product or custom solution.",
            RiskLevel.HIGH: "Proceed with caution. Detailed technical review required.",
            RiskLevel.MEDIUM: "Acceptable with mitigations. Document all deviations.",
            RiskLevel.LOW: "Acceptable. Standard verification process.",
            RiskLevel.NONE: "Fully compliant. Proceed with standard workflow."
        }
        return recommendations.get(risk_level, "Unknown risk level")


# ============================================================================
# 18 & 19. Compliance Checker with Standard Verification
# ============================================================================

class ComplianceChecker:
    """Checks compliance with standards and certifications"""
    
    # Standard mappings
    STANDARD_REQUIREMENTS = {
        'IS 694': {'category': 'building_wires', 'certifications': ['BIS']},
        'IS 1554': {'category': 'power_cables', 'certifications': ['BIS', 'CPRI']},
        'IS 7098': {'category': 'control_cables', 'certifications': ['BIS']},
        'IEC 60502': {'category': 'power_cables', 'certifications': []},
    }
    
    def __init__(self):
        self.logger = logging.getLogger("ComplianceChecker")
    
    def check(
        self, 
        requirement: RFPRequirement, 
        match: ProductMatch
    ) -> Dict[str, Any]:
        """Check compliance status"""
        compliance = {
            'status': ComplianceStatus.UNKNOWN,
            'standards_check': [],
            'certification_check': [],
            'overall_compliant': True,
            'notes': []
        }
        
        # Check standards
        for std in requirement.standards:
            std_result = self._check_standard(std, match)
            compliance['standards_check'].append(std_result)
            if std_result['status'] != 'compliant':
                compliance['overall_compliant'] = False
        
        # Check certifications
        for cert in requirement.certifications:
            cert_result = self._check_certification(cert, match)
            compliance['certification_check'].append(cert_result)
            if cert_result['status'] != 'available':
                compliance['overall_compliant'] = False
        
        # Determine overall status
        if compliance['overall_compliant']:
            compliance['status'] = ComplianceStatus.COMPLIANT
        elif any(c['status'] == 'compliant' for c in compliance['standards_check']):
            compliance['status'] = ComplianceStatus.PARTIAL
        else:
            compliance['status'] = ComplianceStatus.NON_COMPLIANT
        
        return compliance
    
    def _check_standard(self, standard: str, match: ProductMatch) -> Dict[str, Any]:
        """Check if product meets standard"""
        product_specs = match.specifications
        
        # Look for standard reference in product specs
        product_standard = product_specs.get('standard', '')
        
        if standard.lower() in str(product_standard).lower():
            return {'standard': standard, 'status': 'compliant', 'note': 'Direct match'}
        
        # Check if product has required certifications for standard
        std_req = self.STANDARD_REQUIREMENTS.get(standard.split(':')[0], {})
        required_certs = std_req.get('certifications', [])
        
        if all(c in match.compliance_notes for c in required_certs):
            return {'standard': standard, 'status': 'likely_compliant', 
                    'note': 'Has required certifications'}
        
        return {'standard': standard, 'status': 'unverified', 
                'note': 'Requires manufacturer confirmation'}
    
    def _check_certification(self, cert: str, match: ProductMatch) -> Dict[str, Any]:
        """Check if product has certification"""
        if cert in match.compliance_notes:
            return {'certification': cert, 'status': 'available'}
        return {'certification': cert, 'status': 'not_found', 
                'note': 'Request from manufacturer'}


# ============================================================================
# 20. Technical Summary Generator
# ============================================================================

class TechnicalSummaryGenerator:
    """Generates technical summaries"""
    
    def generate_summary(
        self,
        requirement: RFPRequirement,
        top_matches: List[ProductMatch]
    ) -> str:
        """Generate technical summary text"""
        lines = []
        
        # Requirement summary
        lines.append(f"## Technical Analysis: {requirement.name}")
        lines.append("")
        lines.append(f"**Requirement ID:** {requirement.id}")
        lines.append(f"**Quantity:** {requirement.quantity} {requirement.unit}")
        lines.append(f"**Specifications:** {len(requirement.specifications)} parameters")
        lines.append("")
        
        # Match summary
        lines.append("### Top Recommendations")
        lines.append("")
        
        for i, match in enumerate(top_matches[:3], 1):
            lines.append(f"**{i}. {match.product_name}** ({match.manufacturer})")
            lines.append(f"   - SKU: {match.product_id}")
            lines.append(f"   - Match Score: {match.match_score}%")
            lines.append(f"   - Confidence: {match.confidence.value}")
            lines.append(f"   - Risk: {match.risk_level.value}")
            lines.append("")
        
        # Overall assessment
        if top_matches:
            best = top_matches[0]
            if best.match_score >= 90:
                lines.append("**Assessment:** Excellent product match found. Recommend proceeding.")
            elif best.match_score >= 75:
                lines.append("**Assessment:** Good match available. Minor clarifications may be needed.")
            else:
                lines.append("**Assessment:** Partial matches only. Review alternatives or custom options.")
        
        return "\n".join(lines)
    
    def generate_brief(self, match: ProductMatch) -> str:
        """Generate brief summary for a match"""
        return (f"{match.product_name} by {match.manufacturer} - "
                f"{match.match_score}% match, {match.confidence.value} confidence")


# ============================================================================
# 21 & 22. Product Recommendation Ranker with Alternative Suggestions
# ============================================================================

class ProductRecommendationRanker:
    """Ranks product recommendations with alternatives"""
    
    def __init__(self):
        self.score_calculator = MatchScoreCalculator()
    
    def rank(self, matches: List[ProductMatch]) -> List[Dict[str, Any]]:
        """Rank matches with composite scoring"""
        ranked = []
        
        for match in matches:
            composite = self.score_calculator.calculate_composite_score(match)
            ranked.append({
                'match': match,
                'composite_score': composite['composite_score'],
                'breakdown': composite
            })
        
        ranked.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # Add rank positions
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
        
        return ranked
    
    def suggest_alternatives(
        self,
        primary_match: ProductMatch,
        all_matches: List[ProductMatch],
        max_alternatives: int = 2
    ) -> List[Dict[str, Any]]:
        """Suggest alternative products"""
        alternatives = []
        
        for match in all_matches:
            if match.product_id == primary_match.product_id:
                continue
            
            # Calculate alternative merit
            merit = self._calculate_alternative_merit(primary_match, match)
            
            if merit['score'] > 0:
                alternatives.append({
                    'product': match,
                    'merit': merit,
                    'reason': merit['reason']
                })
        
        alternatives.sort(key=lambda x: x['merit']['score'], reverse=True)
        return alternatives[:max_alternatives]
    
    def _calculate_alternative_merit(
        self, 
        primary: ProductMatch, 
        alternative: ProductMatch
    ) -> Dict[str, Any]:
        """Calculate merit of alternative over primary"""
        merit = {'score': 0, 'reasons': [], 'reason': ''}
        
        # Different manufacturer (diversity)
        if alternative.manufacturer != primary.manufacturer:
            merit['score'] += 0.2
            merit['reasons'].append('Different manufacturer for vendor diversity')
        
        # Better compliance
        if len(alternative.compliance_notes) > len(primary.compliance_notes):
            merit['score'] += 0.15
            merit['reasons'].append('More certifications available')
        
        # Lower risk
        risk_scores = {RiskLevel.NONE: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, 
                      RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
        if risk_scores.get(alternative.risk_level, 5) < risk_scores.get(primary.risk_level, 5):
            merit['score'] += 0.15
            merit['reasons'].append('Lower technical risk')
        
        # Similar score (viable alternative)
        if alternative.match_score >= primary.match_score * 0.9:
            merit['score'] += 0.1
            merit['reasons'].append('Comparable match score')
        
        merit['reason'] = '; '.join(merit['reasons']) if merit['reasons'] else 'N/A'
        return merit


# ============================================================================
# 23. Custom Product Flagging
# ============================================================================

class CustomProductFlagger:
    """Flags requirements that need custom products"""
    
    # Thresholds
    MIN_MATCH_THRESHOLD = 60
    MIN_CRITICAL_SPECS = 3
    
    def evaluate(
        self, 
        requirement: RFPRequirement,
        top_matches: List[ProductMatch]
    ) -> Dict[str, Any]:
        """Evaluate if custom product is needed"""
        if not top_matches:
            return {
                'needs_custom': True,
                'reason': 'No matching products found',
                'confidence': 1.0,
                'recommendations': ['Engage custom manufacturing partner']
            }
        
        best_match = top_matches[0]
        
        # Check if best match is insufficient
        if best_match.match_score < self.MIN_MATCH_THRESHOLD:
            return {
                'needs_custom': True,
                'reason': f'Best match only {best_match.match_score}%',
                'confidence': 0.9,
                'recommendations': [
                    'Request custom quotation from preferred manufacturers',
                    'Consider specification modifications if possible'
                ],
                'missing_specs': best_match.unmatched_specs
            }
        
        # Check critical spec gaps
        critical_specs = ['voltage_rating', 'current_rating', 'cross_section_sqmm',
                         'conductor_material', 'insulation_type']
        critical_gaps = [s for s in best_match.unmatched_specs if s in critical_specs]
        
        if len(critical_gaps) >= 2:
            return {
                'needs_custom': True,
                'reason': 'Critical specifications not met',
                'confidence': 0.85,
                'critical_gaps': critical_gaps,
                'recommendations': ['Custom manufacturing required for critical specs']
            }
        
        return {
            'needs_custom': False,
            'reason': 'Standard product meets requirements',
            'confidence': best_match.match_score / 100,
            'selected_product': best_match.product_id
        }


# ============================================================================
# 24 & 25. Technical Report Formatter with Visualization Data
# ============================================================================

class TechnicalReportFormatter:
    """Formats technical reports"""
    
    def __init__(self):
        self.summary_generator = TechnicalSummaryGenerator()
        self.comparison_generator = ComparisonTableGenerator()
    
    def format_report(
        self,
        rfp_id: str,
        requirements: List[RFPRequirement],
        all_matches: Dict[str, List[ProductMatch]]
    ) -> TechnicalReport:
        """Format complete technical report"""
        recommendations = []
        comparison_tables = []
        combined_gap_analysis = {'total_gaps': 0, 'by_requirement': {}}
        combined_risk = {'high_risk_items': [], 'risk_distribution': {}}
        
        for req in requirements:
            matches = all_matches.get(req.id, [])
            top_3 = matches[:3]
            
            # Build recommendation
            if top_3:
                recommendations.append({
                    'requirement_id': req.id,
                    'requirement_name': req.name,
                    'selected': {
                        'product_id': top_3[0].product_id,
                        'product_name': top_3[0].product_name,
                        'manufacturer': top_3[0].manufacturer,
                        'match_score': top_3[0].match_score,
                        'confidence': top_3[0].confidence.value
                    },
                    'alternatives': [
                        {
                            'rank': i + 2,
                            'product_id': m.product_id,
                            'match_score': m.match_score
                        }
                        for i, m in enumerate(top_3[1:])
                    ]
                })
            
            # Build comparison table
            if top_3:
                table = self.comparison_generator.generate(req, top_3)
                comparison_tables.append(table)
            
            # Aggregate gaps
            if top_3:
                combined_gap_analysis['by_requirement'][req.id] = {
                    'gaps': top_3[0].unmatched_specs
                }
                combined_gap_analysis['total_gaps'] += len(top_3[0].unmatched_specs)
            
            # Track high risk
            if top_3 and top_3[0].risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                combined_risk['high_risk_items'].append(req.id)
        
        # Compliance summary
        compliance_summary = self._build_compliance_summary(requirements, all_matches)
        
        # Technical summary text
        summary_text = self._generate_overall_summary(
            requirements, recommendations, combined_gap_analysis
        )
        
        # Visualization data
        viz_data = self._generate_visualization_data(
            requirements, recommendations, combined_risk
        )
        
        return TechnicalReport(
            rfp_id=rfp_id,
            analysis_date=datetime.now(),
            requirements=requirements,
            recommendations=recommendations,
            comparison_tables=comparison_tables,
            gap_analysis=combined_gap_analysis,
            risk_assessment=combined_risk,
            compliance_summary=compliance_summary,
            technical_summary=summary_text,
            visualization_data=viz_data
        )
    
    def _build_compliance_summary(
        self,
        requirements: List[RFPRequirement],
        all_matches: Dict[str, List[ProductMatch]]
    ) -> Dict[str, Any]:
        """Build compliance summary"""
        total = len(requirements)
        compliant = 0
        partial = 0
        
        for req in requirements:
            matches = all_matches.get(req.id, [])
            if matches and matches[0].match_score >= 90:
                compliant += 1
            elif matches and matches[0].match_score >= 70:
                partial += 1
        
        return {
            'total_items': total,
            'fully_compliant': compliant,
            'partially_compliant': partial,
            'non_compliant': total - compliant - partial,
            'compliance_rate': round(compliant / total * 100, 1) if total > 0 else 0
        }
    
    def _generate_overall_summary(
        self,
        requirements: List[RFPRequirement],
        recommendations: List[Dict],
        gap_analysis: Dict
    ) -> str:
        """Generate overall summary text"""
        lines = [
            f"# Technical Analysis Summary",
            f"",
            f"**Total Requirements:** {len(requirements)}",
            f"**Recommendations Generated:** {len(recommendations)}",
            f"**Total Specification Gaps:** {gap_analysis['total_gaps']}",
            f"",
        ]
        
        if gap_analysis['total_gaps'] == 0:
            lines.append("All requirements have been matched with catalog products.")
        else:
            lines.append(f"Some requirements have specification gaps. Review recommended.")
        
        return "\n".join(lines)
    
    def _generate_visualization_data(
        self,
        requirements: List[RFPRequirement],
        recommendations: List[Dict],
        risk_data: Dict
    ) -> Dict[str, Any]:
        """Generate data for visualizations"""
        # Match score distribution
        scores = [r['selected']['match_score'] for r in recommendations if 'selected' in r]
        
        score_distribution = {
            '90-100': sum(1 for s in scores if s >= 90),
            '75-89': sum(1 for s in scores if 75 <= s < 90),
            '50-74': sum(1 for s in scores if 50 <= s < 75),
            '0-49': sum(1 for s in scores if s < 50)
        }
        
        return {
            'match_score_distribution': score_distribution,
            'average_match_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'high_risk_count': len(risk_data.get('high_risk_items', [])),
            'requirement_count': len(requirements),
            'chart_data': {
                'type': 'bar',
                'labels': list(score_distribution.keys()),
                'values': list(score_distribution.values())
            }
        }


# ============================================================================
# 26 & 27. Detailed Spec Comparison with Match Justification
# ============================================================================

class DetailedSpecComparison:
    """Provides detailed specification comparisons"""
    
    def __init__(self):
        self.explanation_gen = SpecificationExplanationGenerator()
    
    def compare(
        self,
        requirement: RFPRequirement,
        match: ProductMatch
    ) -> Dict[str, Any]:
        """Generate detailed comparison"""
        comparison = {
            'requirement': requirement.name,
            'product': match.product_name,
            'overall_match': match.match_score,
            'specifications': []
        }
        
        for spec_key, rfp_value in requirement.specifications.items():
            prod_value = match.specifications.get(spec_key, 'Not specified')
            
            spec_comparison = {
                'name': spec_key,
                'rfp_value': rfp_value,
                'product_value': prod_value,
                'status': self._get_match_status(spec_key, match),
                'explanation': self.explanation_gen.explain_spec(spec_key, rfp_value),
                'justification': self._generate_spec_justification(
                    spec_key, rfp_value, prod_value, match
                )
            }
            comparison['specifications'].append(spec_comparison)
        
        return comparison
    
    def _get_match_status(self, spec_key: str, match: ProductMatch) -> str:
        """Get match status for specification"""
        if spec_key in match.matched_specs:
            return 'FULL_MATCH'
        if any(p['spec'] == spec_key for p in match.partial_matches):
            return 'PARTIAL_MATCH'
        if spec_key in match.unmatched_specs:
            return 'NO_MATCH'
        return 'NOT_APPLICABLE'
    
    def _generate_spec_justification(
        self,
        spec_key: str,
        rfp_value: Any,
        prod_value: Any,
        match: ProductMatch
    ) -> str:
        """Generate justification for spec match status"""
        if spec_key in match.matched_specs:
            return f"Product specification '{prod_value}' matches requirement '{rfp_value}'"
        
        if any(p['spec'] == spec_key for p in match.partial_matches):
            partial = next(p for p in match.partial_matches if p['spec'] == spec_key)
            return (f"Partial match ({partial['match_percent']:.0f}%): "
                   f"'{prod_value}' vs required '{rfp_value}'")
        
        if spec_key in match.unmatched_specs:
            if prod_value == 'Not specified':
                return f"Product does not specify {spec_key}. Verification needed."
            return f"Specification gap: '{prod_value}' does not meet '{rfp_value}'"
        
        return "Unable to compare"


# ============================================================================
# 28. Edge Case Handlers
# ============================================================================

class EdgeCaseHandler:
    """Handles edge cases in technical matching"""
    
    def __init__(self):
        self.logger = logging.getLogger("EdgeCaseHandler")
    
    def handle_no_matches(self, requirement: RFPRequirement) -> Dict[str, Any]:
        """Handle case when no matches found"""
        return {
            'status': 'no_matches',
            'requirement_id': requirement.id,
            'suggestions': [
                'Expand search to related categories',
                'Consider custom product manufacturing',
                'Review requirement specifications for flexibility'
            ],
            'escalation_required': True
        }
    
    def handle_ambiguous_specs(
        self, 
        requirement: RFPRequirement,
        ambiguous_specs: List[str]
    ) -> Dict[str, Any]:
        """Handle ambiguous specifications"""
        return {
            'status': 'ambiguous_specs',
            'requirement_id': requirement.id,
            'ambiguous_specifications': ambiguous_specs,
            'action_required': 'Request clarification from RFP issuer',
            'default_assumptions': {
                spec: self._get_default_assumption(spec)
                for spec in ambiguous_specs
            }
        }
    
    def handle_conflicting_specs(
        self,
        requirement: RFPRequirement,
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle conflicting specifications"""
        return {
            'status': 'conflicting_specs',
            'requirement_id': requirement.id,
            'conflicts': conflicts,
            'resolution': 'Manual review required',
            'recommendations': [
                'Consult with technical team',
                'Request RFP clarification'
            ]
        }
    
    def handle_unusual_quantity(
        self,
        requirement: RFPRequirement
    ) -> Dict[str, Any]:
        """Handle unusual quantity requirements"""
        qty = requirement.quantity
        
        if qty < 1:
            return {
                'status': 'invalid_quantity',
                'issue': 'Quantity less than 1',
                'action': 'Verify requirement quantity'
            }
        
        if qty > 1000000:
            return {
                'status': 'large_quantity',
                'quantity': qty,
                'warning': 'Exceptionally large quantity',
                'recommendations': [
                    'Verify quantity is correct',
                    'Consider phased delivery',
                    'Check manufacturer capacity'
                ]
            }
        
        return {'status': 'normal', 'quantity': qty}
    
    def _get_default_assumption(self, spec: str) -> str:
        """Get default assumption for ambiguous spec"""
        defaults = {
            'conductor_material': 'copper',
            'insulation_type': 'pvc',
            'armour_type': 'unarmoured',
            'voltage_rating': '1100V'
        }
        return defaults.get(spec, 'industry_standard')


# ============================================================================
# 29. Technical Validation
# ============================================================================

class TechnicalValidator:
    """Validates technical data and matches"""
    
    def validate_requirement(self, requirement: RFPRequirement) -> Dict[str, Any]:
        """Validate requirement data"""
        errors = []
        warnings = []
        
        # Check required fields
        if not requirement.name:
            errors.append('Requirement name is missing')
        
        if not requirement.specifications:
            errors.append('No specifications provided')
        
        if requirement.quantity <= 0:
            errors.append('Invalid quantity')
        
        # Check specification values
        for key, value in requirement.specifications.items():
            if value is None:
                warnings.append(f'Specification {key} has no value')
            elif isinstance(value, str) and len(value) > 500:
                warnings.append(f'Specification {key} value unusually long')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_match(self, match: ProductMatch) -> Dict[str, Any]:
        """Validate match result"""
        errors = []
        warnings = []
        
        if not match.product_id:
            errors.append('Product ID missing')
        
        if match.match_score < 0 or match.match_score > 100:
            errors.append('Match score out of range')
        
        if match.match_score > 0 and not match.matched_specs and not match.partial_matches:
            warnings.append('Positive score but no matched specs recorded')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


# ============================================================================
# 30 & 31. Output to Pricing Agent and Main Agent
# ============================================================================

class AgentOutputHandler:
    """Handles output to other agents"""
    
    def __init__(self):
        self.message_queue: deque = deque(maxlen=1000)
        self.callbacks: Dict[str, Callable] = {}
        self.logger = logging.getLogger("AgentOutput")
    
    def prepare_pricing_output(
        self,
        rfp_id: str,
        recommendations: List[Dict[str, Any]]
    ) -> AgentMessage:
        """Prepare output for Pricing Agent"""
        payload = {
            'rfp_id': rfp_id,
            'products_for_pricing': [
                {
                    'requirement_id': rec['requirement_id'],
                    'selected_sku': rec['selected']['product_id'],
                    'manufacturer': rec['selected']['manufacturer'],
                    'match_score': rec['selected']['match_score'],
                    'quantity': rec.get('quantity', 1),
                    'unit': rec.get('unit', 'Nos'),
                    'alternatives': rec.get('alternatives', [])
                }
                for rec in recommendations
            ],
            'priority': 'normal',
            'requested_at': datetime.now().isoformat()
        }
        
        return AgentMessage(
            id=str(uuid.uuid4()),
            sender='TECHNICAL_AGENT',
            recipient='PRICING_AGENT',
            message_type='pricing_request',
            payload=payload,
            timestamp=datetime.now()
        )
    
    def prepare_main_output(
        self,
        report: TechnicalReport
    ) -> AgentMessage:
        """Prepare output for Main Agent"""
        payload = {
            'rfp_id': report.rfp_id,
            'analysis_complete': True,
            'analysis_date': report.analysis_date.isoformat(),
            'summary': report.technical_summary,
            'recommendations_count': len(report.recommendations),
            'compliance_summary': report.compliance_summary,
            'risk_assessment': report.risk_assessment,
            'visualization_data': report.visualization_data,
            'requires_review': any(
                rec.get('selected', {}).get('match_score', 0) < 70
                for rec in report.recommendations
            )
        }
        
        return AgentMessage(
            id=str(uuid.uuid4()),
            sender='TECHNICAL_AGENT',
            recipient='MASTER_AGENT',
            message_type='technical_analysis_complete',
            payload=payload,
            timestamp=datetime.now()
        )
    
    def send(self, message: AgentMessage):
        """Send message (queue for processing)"""
        self.message_queue.append(message)
        
        # Invoke callback if registered
        callback = self.callbacks.get(message.recipient)
        if callback:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")
    
    def register_callback(self, recipient: str, callback: Callable):
        """Register callback for recipient"""
        self.callbacks[recipient] = callback


# ============================================================================
# 32-34. Technical Agent Memory, Context, and History
# ============================================================================

class TechnicalAgentMemory:
    """Manages technical agent memory and context"""
    
    def __init__(self, max_history: int = 100):
        self.short_term: Dict[str, Any] = {}  # Current session
        self.long_term: Dict[str, Any] = {}  # Persisted
        self.conversation_history: deque = deque(maxlen=max_history)
        self.context_stack: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def store(self, key: str, value: Any, long_term: bool = False):
        """Store value in memory"""
        with self.lock:
            if long_term:
                self.long_term[key] = value
            else:
                self.short_term[key] = value
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from memory"""
        with self.lock:
            if key in self.short_term:
                return self.short_term[key]
            return self.long_term.get(key)
    
    def add_conversation(self, role: str, content: str):
        """Add to conversation history"""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_conversation_context(self, last_n: int = 10) -> List[Dict]:
        """Get recent conversation context"""
        return list(self.conversation_history)[-last_n:]
    
    def push_context(self, context: Dict[str, Any]):
        """Push context to stack"""
        self.context_stack.append(context)
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from stack"""
        if self.context_stack:
            return self.context_stack.pop()
        return None
    
    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get current context without popping"""
        if self.context_stack:
            return self.context_stack[-1]
        return None
    
    def clear_session(self):
        """Clear short-term memory and context"""
        with self.lock:
            self.short_term.clear()
            self.context_stack.clear()


# ============================================================================
# 36-37. Performance Tracking and Error Recovery
# ============================================================================

class PerformanceTracker:
    """Tracks agent performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            'processing_time_ms': [],
            'match_scores': [],
            'items_processed': [],
        }
        self.counters: Dict[str, int] = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
        self.start_time = datetime.now()
    
    def record_processing_time(self, duration_ms: float):
        """Record processing time"""
        self.metrics['processing_time_ms'].append(duration_ms)
    
    def record_match_score(self, score: float):
        """Record match score"""
        self.metrics['match_scores'].append(score)
    
    def increment(self, counter: str, amount: int = 1):
        """Increment counter"""
        if counter in self.counters:
            self.counters[counter] += amount
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        proc_times = self.metrics['processing_time_ms']
        match_scores = self.metrics['match_scores']
        
        return {
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'total_requests': self.counters['total_requests'],
            'success_rate': (
                self.counters['successful_requests'] / 
                max(self.counters['total_requests'], 1) * 100
            ),
            'avg_processing_time_ms': sum(proc_times) / len(proc_times) if proc_times else 0,
            'avg_match_score': sum(match_scores) / len(match_scores) if match_scores else 0,
            'cache_hit_rate': (
                self.counters['cache_hits'] / 
                max(self.counters['cache_hits'] + self.counters['cache_misses'], 1) * 100
            )
        }


class ErrorRecoveryHandler:
    """Handles error recovery"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.error_counts: Dict[str, int] = {}
        self.logger = logging.getLogger("ErrorRecovery")
    
    def with_retry(
        self, 
        operation: Callable,
        operation_name: str,
        *args, 
        **kwargs
    ) -> Tuple[bool, Any]:
        """Execute operation with retry logic"""
        for attempt in range(self.max_retries):
            try:
                result = operation(*args, **kwargs)
                return True, result
            except Exception as e:
                self.logger.warning(f"{operation_name} attempt {attempt + 1} failed: {e}")
                self.error_counts[operation_name] = self.error_counts.get(operation_name, 0) + 1
                
                if attempt < self.max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        
        return False, None
    
    def get_fallback_result(self, requirement: RFPRequirement) -> Dict[str, Any]:
        """Generate fallback result when all retries fail"""
        return {
            'status': 'fallback',
            'requirement_id': requirement.id,
            'message': 'Unable to process. Manual review required.',
            'recommendations': [],
            'escalated': True
        }


# ============================================================================
# 38-39. Batch Processing and Async Support
# ============================================================================

class BatchProcessor:
    """Handles batch processing of requirements"""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger("BatchProcessor")
    
    def process_batch(
        self,
        items: List[Any],
        processor: Callable[[Any], Any]
    ) -> List[Any]:
        """Process items in batches"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = list(self.executor.map(processor, batch))
            results.extend(batch_results)
            self.logger.info(f"Processed batch {i // self.batch_size + 1}")
        
        return results
    
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get status of batch processing"""
        # Placeholder - would track actual batch status
        return {
            'batch_id': batch_id,
            'status': 'complete',
            'processed': 0,
            'total': 0
        }


class AsyncOperationSupport:
    """Provides async operation support"""
    
    def __init__(self):
        self.pending_operations: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger("AsyncSupport")
    
    async def process_async(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Process operation asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: operation(*args, **kwargs))
    
    async def process_multiple_async(
        self,
        operations: List[Tuple[Callable, tuple, dict]]
    ) -> List[Any]:
        """Process multiple operations concurrently"""
        tasks = [
            self.process_async(op, *args, **kwargs)
            for op, args, kwargs in operations
        ]
        return await asyncio.gather(*tasks)


# ============================================================================
# 40-41. API Interface and Webhook Support
# ============================================================================

class TechnicalAgentAPI:
    """API interface for Technical Agent"""
    
    def __init__(self, agent: 'TechnicalAgent'):
        self.agent = agent
        self.endpoints = {
            'analyze': self.analyze,
            'get_status': self.get_status,
            'get_match': self.get_match,
            'health': self.health_check
        }
    
    def handle_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle API request"""
        if endpoint not in self.endpoints:
            return {'error': 'Unknown endpoint', 'status': 404}
        
        try:
            result = self.endpoints[endpoint](data)
            return {'data': result, 'status': 200}
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze RFP endpoint"""
        return self.agent.process_rfp(data)
    
    def get_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent status"""
        return self.agent.get_status()
    
    def get_match(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get match for single requirement"""
        req_data = data.get('requirement', {})
        requirement = RFPRequirement(
            id=req_data.get('id', 'REQ_001'),
            name=req_data.get('name', ''),
            description=req_data.get('description', ''),
            specifications=req_data.get('specifications', {}),
            quantity=req_data.get('quantity', 1),
            unit=req_data.get('unit', 'Nos')
        )
        matches = self.agent.matching_orchestrator.find_matches(requirement)
        return {'matches': [self._match_to_dict(m) for m in matches[:5]]}
    
    def health_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Health check endpoint"""
        return self.agent.health_check()
    
    def _match_to_dict(self, match: ProductMatch) -> Dict[str, Any]:
        """Convert match to dictionary"""
        return {
            'product_id': match.product_id,
            'product_name': match.product_name,
            'manufacturer': match.manufacturer,
            'match_score': match.match_score,
            'confidence': match.confidence.value
        }


class WebhookManager:
    """Manages webhook notifications"""
    
    def __init__(self):
        self.webhooks: List[WebhookConfig] = []
        self.logger = logging.getLogger("WebhookManager")
    
    def register(self, config: WebhookConfig):
        """Register webhook"""
        self.webhooks.append(config)
    
    def unregister(self, url: str):
        """Unregister webhook"""
        self.webhooks = [w for w in self.webhooks if w.url != url]
    
    def notify(self, event: str, payload: Dict[str, Any]):
        """Send webhook notifications"""
        for webhook in self.webhooks:
            if not webhook.enabled:
                continue
            if event not in webhook.events:
                continue
            
            try:
                self._send_webhook(webhook, event, payload)
            except Exception as e:
                self.logger.error(f"Webhook failed for {webhook.url}: {e}")
    
    def _send_webhook(self, webhook: WebhookConfig, event: str, payload: Dict[str, Any]):
        """Send single webhook notification"""
        # In production, would use requests library
        self.logger.info(f"Webhook sent to {webhook.url}: {event}")


# ============================================================================
# Main Technical Agent Class
# ============================================================================

class TechnicalAgent:
    """
    Comprehensive Technical Agent for RFP Analysis and Product Matching
    
    Features:
    - RFP requirement parsing and extraction
    - Product catalog querying with vector search
    - Weighted specification matching
    - Top-3 product recommendations
    - Comparison table generation
    - Gap analysis and risk assessment
    - Compliance checking
    - Output to Pricing and Master agents
    - Batch and async processing
    - API and webhook support
    """
    
    def __init__(
        self,
        agent_id: str = "TECH_AGENT_001",
        log_dir: Optional[str] = None
    ):
        self.agent_id = agent_id
        
        # Initialize logger
        self.logger = TechnicalAgentLogger(agent_id, log_dir)
        
        # Core components
        self.requirement_parser = RFPRequirementParser()
        self.requirement_extractor = ProductRequirementExtractor()
        self.scope_analyzer = ScopeOfSupplyAnalyzer()
        self.multi_item_handler = MultiItemRFPHandler()
        self.catalog_querier = ProductCatalogQuerier()
        self.matching_orchestrator = SpecificationMatchingOrchestrator()
        self.top_k_selector = TopKSelector(k=3)
        self.score_calculator = MatchScoreCalculator()
        
        # Analysis components
        self.comparison_generator = ComparisonTableGenerator()
        self.gap_generator = GapAnalysisGenerator()
        self.explanation_generator = SpecificationExplanationGenerator()
        self.risk_assessor = TechnicalRiskAssessor()
        self.compliance_checker = ComplianceChecker()
        self.summary_generator = TechnicalSummaryGenerator()
        
        # Recommendation components
        self.ranker = ProductRecommendationRanker()
        self.custom_flagger = CustomProductFlagger()
        self.report_formatter = TechnicalReportFormatter()
        self.spec_comparator = DetailedSpecComparison()
        
        # Support components
        self.edge_handler = EdgeCaseHandler()
        self.validator = TechnicalValidator()
        self.output_handler = AgentOutputHandler()
        self.memory = TechnicalAgentMemory()
        self.performance = PerformanceTracker()
        self.error_handler = ErrorRecoveryHandler()
        
        # Processing modes
        self.batch_processor = BatchProcessor()
        self.async_support = AsyncOperationSupport()
        
        # API and webhooks
        self.api = TechnicalAgentAPI(self)
        self.webhook_manager = WebhookManager()
        
        self.logger.info(f"Technical Agent initialized: {agent_id}")
    
    def process_rfp(self, rfp_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process RFP and generate technical analysis
        
        Args:
            rfp_context: RFP data with products_in_scope
            
        Returns:
            Complete technical analysis with recommendations
        """
        start_time = time.time()
        self.performance.increment('total_requests')
        
        try:
            rfp_id = rfp_context.get('rfp_id', 'UNKNOWN')
            self.logger.info(f"Processing RFP: {rfp_id}")
            
            # Store in memory
            self.memory.store(f'rfp_{rfp_id}', rfp_context)
            self.memory.push_context({'rfp_id': rfp_id, 'stage': 'processing'})
            
            # 1. Parse requirements
            requirements = self.requirement_parser.parse(rfp_context)
            self.logger.info(f"Parsed {len(requirements)} requirements")
            
            # 2. Analyze scope
            scope_analysis = self.scope_analyzer.analyze(rfp_context)
            
            # 3. Process each requirement
            all_matches: Dict[str, List[ProductMatch]] = {}
            
            for req in requirements:
                # Validate requirement
                validation = self.validator.validate_requirement(req)
                if not validation['valid']:
                    self.logger.warning(f"Validation issues for {req.id}: {validation['errors']}")
                
                # Find matches
                matches = self.matching_orchestrator.find_matches(req)
                
                # Handle edge cases
                if not matches:
                    edge_result = self.edge_handler.handle_no_matches(req)
                    self.logger.warning(f"No matches for {req.id}")
                
                # Select top-K
                top_matches = self.top_k_selector.select(matches)
                
                # Store matches
                all_matches[req.id] = top_matches
                
                # Track performance
                for m in top_matches:
                    self.performance.record_match_score(m.match_score)
            
            # 4. Generate report
            report = self.report_formatter.format_report(rfp_id, requirements, all_matches)
            
            # 5. Prepare outputs for other agents
            pricing_message = self.output_handler.prepare_pricing_output(
                rfp_id, report.recommendations
            )
            main_message = self.output_handler.prepare_main_output(report)
            
            # 6. Send messages
            self.output_handler.send(pricing_message)
            self.output_handler.send(main_message)
            
            # 7. Notify webhooks
            self.webhook_manager.notify('analysis_complete', {
                'rfp_id': rfp_id,
                'recommendations_count': len(report.recommendations)
            })
            
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            self.performance.record_processing_time(duration_ms)
            self.performance.increment('successful_requests')
            
            self.logger.info(f"RFP {rfp_id} processed in {duration_ms:.0f}ms")
            
            # Build response
            return self._build_response(rfp_id, report, all_matches)
            
        except Exception as e:
            self.performance.increment('failed_requests')
            self.logger.error(f"Error processing RFP: {e}")
            raise
        finally:
            self.memory.pop_context()
    
    def _build_response(
        self,
        rfp_id: str,
        report: TechnicalReport,
        all_matches: Dict[str, List[ProductMatch]]
    ) -> Dict[str, Any]:
        """Build response dictionary"""
        return {
            'rfp_id': rfp_id,
            'processed_date': report.analysis_date.isoformat(),
            'products_analyzed': len(report.requirements),
            'recommendations': report.recommendations,
            'comparison_tables': [
                self.comparison_generator.to_dict(table)
                for table in report.comparison_tables
            ],
            'gap_analysis': report.gap_analysis,
            'risk_assessment': report.risk_assessment,
            'compliance_summary': report.compliance_summary,
            'technical_summary': report.technical_summary,
            'visualization_data': report.visualization_data
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running',
            'performance': self.performance.get_stats(),
            'memory': {
                'short_term_items': len(self.memory.short_term),
                'long_term_items': len(self.memory.long_term),
                'conversation_history': len(self.memory.conversation_history)
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            'healthy': True,
            'agent_id': self.agent_id,
            'catalog_size': len(self.catalog_querier.catalog),
            'uptime': self.performance.get_stats()['uptime_seconds']
        }
    
    def process_batch(
        self,
        rfp_contexts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple RFPs in batch"""
        return self.batch_processor.process_batch(
            rfp_contexts,
            self.process_rfp
        )
    
    async def process_async(
        self,
        rfp_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process RFP asynchronously"""
        return await self.async_support.process_async(
            self.process_rfp,
            rfp_context
        )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Enums
    'MatchConfidence',
    'RiskLevel',
    'ComplianceStatus',
    'ProcessingMode',
    
    # Data Classes
    'RFPRequirement',
    'ProductMatch',
    'ComparisonRow',
    'TechnicalReport',
    'AgentMessage',
    'WebhookConfig',
    
    # Core Classes
    'TechnicalAgent',
    'TechnicalAgentLogger',
    'RFPRequirementParser',
    'ProductRequirementExtractor',
    'ScopeOfSupplyAnalyzer',
    'MultiItemRFPHandler',
    'ProductCatalogQuerier',
    'VectorSearchIntegration',
    'SpecificationMatchingOrchestrator',
    'TopKSelector',
    'MatchScoreCalculator',
    'ComparisonTableGenerator',
    'GapAnalysisGenerator',
    'SpecificationExplanationGenerator',
    'TechnicalRiskAssessor',
    'ComplianceChecker',
    'TechnicalSummaryGenerator',
    'ProductRecommendationRanker',
    'CustomProductFlagger',
    'TechnicalReportFormatter',
    'DetailedSpecComparison',
    'EdgeCaseHandler',
    'TechnicalValidator',
    'AgentOutputHandler',
    'TechnicalAgentMemory',
    'PerformanceTracker',
    'ErrorRecoveryHandler',
    'BatchProcessor',
    'AsyncOperationSupport',
    'TechnicalAgentAPI',
    'WebhookManager',
]
