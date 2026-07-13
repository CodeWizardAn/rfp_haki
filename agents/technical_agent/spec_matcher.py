"""
Technical Agent - Specification Matcher
Analyzes RFP products and recommends OEM products with spec matching

Enhanced Features:
- Datasheet-level matching with nested property support
- Value normalization for different formats (e.g., "1100V" vs "1100V AC")
- Semantic matching for equivalent terms (e.g., "Copper" vs "Electrolytic Grade Copper")
"""

import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
import math
import re

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import database config
try:
    from database.db_config import DatabaseConfig, DatabaseType
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Value Normalization Maps for Semantic Matching
# ============================================================================

# Conductor material equivalents (with detailed grades)
CONDUCTOR_MATERIAL_MAP = {
    'copper': [
        'copper', 'electrolytic grade copper', 'electrolytic copper', 
        '99.97% pure electrolytic copper', 'etp copper', 'pure copper',
        'cu', 'ofc copper', 'oxygen free copper', 'electrolytic grade copper (etp)',
        'electrolytic grade annealed copper', 'annealed copper'
    ],
    'aluminium': [
        'aluminium', 'aluminum', 'ec grade aluminium', 'al', 'ec aluminium',
        'ec grade aluminium (99.5% purity)', '99.5% aluminium'
    ],
    'tinned copper': [
        'tinned copper', 'tin plated copper', 'sn-cu', 'tin coated copper',
        'tin plated electrolytic copper'
    ],
    'copper clad steel': [
        'copper clad steel', 'ccs', 'copper clad steel (ccs)', 
        'steel core copper', 'copper coated steel'
    ]
}

# Insulation type equivalents (with detailed subtypes)
INSULATION_TYPE_MAP = {
    'pvc': [
        'pvc', 'pvc type a', 'pvc type a (fr/frls/frlsh)', 'fr pvc', 
        'frls pvc', 'frlsh pvc', 'hrfr pvc', 'pvc (fr)', 'pvc insulated',
        'pvc type st2', 'flame retardant pvc', 'hr pvc', 'heat resistant pvc'
    ],
    'xlpe': [
        'xlpe', 'cross-linked polyethylene', 'xlpe (cross-linked polyethylene)',
        'crosslinked pe', 'xlpe insulated', 'cross linked polyethylene'
    ],
    'rubber': [
        'rubber', 'epr', 'silicone rubber', 'natural rubber', 
        'ethylene propylene rubber', 'ep rubber', 'epdm'
    ],
    'lshf': [
        'lshf', 'lszh', 'low smoke halogen free', 'low smoke zero halogen',
        'fr lsh', 'frlsh', 'lsoh', 'fr lsh pvc'
    ]
}

# Conductor type/class equivalents (with detailed subtypes)
CONDUCTOR_TYPE_MAP = {
    'solid/stranded': [
        'solid/stranded', 'solid or stranded', 'class 1 (solid) / class 2 (stranded)',
        'class 1/class 2', 'solid', 'stranded', 'class 1', 'class 2'
    ],
    'stranded': [
        'stranded', 'class 2 (stranded)', 'class 2', 'multi-strand',
        'multistranded', 'multi strand'
    ],
    'flexible stranded': [
        'flexible stranded', 'flexible', 'class 5', 'class 5 (flexible)',
        'highly flexible', 'extra flexible', 'superflex', 'class 6'
    ],
    'solid': [
        'solid', 'class 1 (solid)', 'class 1', 'single wire', 'single strand'
    ]
}

# Armour type equivalents (with detailed subtypes)
ARMOUR_TYPE_MAP = {
    'steel wire armoured': [
        'steel wire armoured', 'swa', 'galvanized steel wire',
        'galvanised steel wire', 'gs wire armoured', 'steel wire armor',
        'single wire armour', 'gswa'
    ],
    'steel tape armoured': [
        'steel tape armoured', 'sta', 'steel tape', 'double steel tape',
        'steel tape armor', 'dst armour'
    ],
    'aluminium wire armoured': [
        'aluminium wire armoured', 'awa', 'aluminum wire armoured',
        'aluminium armour', 'al wire armoured'
    ],
    'unarmoured': [
        'unarmoured', 'unarmored', 'none', 'na', 'no armour', 'without armour'
    ]
}

# Voltage rating equivalents
VOLTAGE_RATING_MAP = {
    '1100v': [
        '1100v', '1100v ac', '1100 v', '1100 volts', '1.1kv', '1.1 kv',
        'up to 1100v', '650/1100v'
    ],
    '650v': [
        '650v', '650v ac', '650 v', '650 volts', '0.65kv'
    ],
    '3300v': [
        '3300v', '3.3kv', '3.3 kv', '3300 volts'
    ],
    '11000v': [
        '11000v', '11kv', '11 kv', '11000 volts'
    ]
}

# Datasheet key mapping (datasheet key -> normalized key used in oem_products)
DATASHEET_KEY_MAP = {
    # electrical_properties mappings
    'electrical_properties.rated_voltage': 'rated_voltage',
    'electrical_properties.max_conductor_temp': 'temperature_rating_celsius',
    'electrical_properties.current_carrying_capacity': 'current_rating_amps',
    
    # physical_properties mappings
    'physical_properties.conductor_material': 'conductor_material',
    'physical_properties.conductor_class': 'conductor_type',
    'physical_properties.nominal_area': 'cross_section_sqmm',
    'physical_properties.number_of_cores': 'number_of_cores',
    'physical_properties.insulation_type': 'insulation_type',
    'physical_properties.armour_type': 'armour_type',
    'physical_properties.outer_sheath': 'outer_sheath'
}


@dataclass
class OEMProduct:
    """OEM Product from repository"""
    sku: str
    product_name: str
    manufacturer: str
    category: str
    specifications: Dict[str, Any]
    datasheet_url: str = ""
    price_range: Tuple[float, float] = (0, 0)
    lead_time_days: int = 14
    moq: int = 1
    certifications: List[str] = field(default_factory=list)


@dataclass
class SpecMatchResult:
    """Result of specification matching"""
    oem_product: OEMProduct
    spec_match_percent: float
    matched_specs: Dict[str, Dict[str, Any]]
    unmatched_specs: List[str]
    partial_matches: List[Dict[str, Any]]
    compliance_notes: List[str]


@dataclass
class ProductRecommendation:
    """Product recommendation with top 3 OEM options"""
    rfp_product_name: str
    rfp_specifications: Dict[str, Any]
    quantity: int
    unit: str
    top_recommendations: List[SpecMatchResult]
    selected_recommendation: SpecMatchResult
    comparison_table: List[Dict[str, Any]]


class TechnicalAgent:
    """
    Technical Agent - Specification Matcher
    
    Responsibilities:
    - Receives RFP summary and document from Master Agent
    - Summarizes products in scope of supply
    - Recommends top 3 OEM products with "Spec Match" metric
    - Prepares comparison table (RFP spec vs OEM specs)
    - Selects best matching OEM product
    - Sends results to Master Agent and Pricing Agent
    
    Enhanced Features:
    - Datasheet-level matching with nested properties
    - Value normalization (e.g., "1100V" matches "1100V AC")
    - Semantic matching (e.g., "Copper" matches "Electrolytic Grade Copper")
    """
    
    def __init__(self, use_datasheets: bool = True):
        self.agent_id = "TECHNICAL_AGENT"
        self.oem_repository: List[OEMProduct] = []
        self.oem_datasheets: Dict[str, Dict[str, Any]] = {}  # SKU -> datasheet
        self.spec_weightages: Dict[str, float] = {}  # Equal weightage by default
        self.use_datasheets = use_datasheets
        
        # Load OEM product repository
        self._load_oem_repository()
        
        # Load datasheets for enhanced matching
        if self.use_datasheets:
            self._load_oem_datasheets()
        
        # Try to import spec_comparer module
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'spec_comparer'))
            # Import spec comparison utilities if available
        except ImportError:
            pass
        
        logger.info(f"✅ Technical Agent initialized with {len(self.oem_repository)} OEM products")
        if self.use_datasheets:
            logger.info(f"   📋 Datasheets loaded: {len(self.oem_datasheets)}")
    
    def _load_oem_repository(self):
        """Load OEM product repository from database"""
        if not DB_AVAILABLE:
            raise RuntimeError("Database configuration not available. Cannot load OEM products.")
        
        db_path = DatabaseConfig.get_path(DatabaseType.OEM_PRODUCTS)
        if not db_path.exists():
            raise FileNotFoundError(f"OEM products database not found: {db_path}")
        
        with open(db_path, 'r') as f:
            data = json.load(f)
        
        for product in data.get('products', []):
            self.oem_repository.append(OEMProduct(
                sku=product['sku'],
                product_name=product['name'],
                manufacturer=product['manufacturer'],
                category=product['category'],
                specifications=product.get('specifications', {}),
                certifications=product.get('certifications', []),
                price_range=(0, 0),
                lead_time_days=14
            ))
        logger.info(f"📦 Loaded OEM products from database: {db_path}")
    
    def _load_oem_datasheets(self):
        """Load OEM product datasheets for enhanced matching"""
        if not DB_AVAILABLE:
            return
        
        db_path = DatabaseConfig.get_path(DatabaseType.OEM_DATASHEETS)
        if not db_path.exists():
            logger.warning(f"Datasheets not found: {db_path}")
            return
        
        with open(db_path, 'r') as f:
            data = json.load(f)
        
        for datasheet in data.get('datasheets', []):
            sku = datasheet.get('sku')
            if sku:
                self.oem_datasheets[sku] = datasheet
        
        logger.info(f"📋 Loaded OEM datasheets from database: {db_path}")
    
    def process_rfp(self, rfp_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process RFP from Master Agent
        
        Args:
            rfp_context: Technical context from Master Agent
            
        Returns:
            Technical response with recommendations
        """
        rfp_id = rfp_context.get('rfp_id')
        products_in_scope = rfp_context.get('products_in_scope', [])
        
        logger.info(f"🔧 Processing RFP {rfp_id} with {len(products_in_scope)} products")
        
        recommendations = []
        comparison_tables = []
        
        for product in products_in_scope:
            recommendation = self._recommend_oem_products(product)
            recommendations.append(recommendation)
            comparison_tables.append(recommendation.comparison_table)
        
        # Build response for Master and Pricing agents
        response = {
            'rfp_id': rfp_id,
            'processed_date': datetime.now().isoformat(),
            'products_analyzed': len(products_in_scope),
            'recommendations': [
                (
                    {
                        'rfp_product': rec.rfp_product_name,
                        'quantity': rec.quantity,
                        'unit': rec.unit,
                        'selected_sku': rec.selected_recommendation.oem_product.sku,
                        'product_name': rec.selected_recommendation.oem_product.product_name,
                        'manufacturer': rec.selected_recommendation.oem_product.manufacturer,
                        'spec_match_percent': rec.selected_recommendation.spec_match_percent,
                        'top_3_options': [
                            {
                                'rank': idx + 1,
                                'sku': r.oem_product.sku,
                                'product_name': r.oem_product.product_name,
                                'manufacturer': r.oem_product.manufacturer,
                                'spec_match_percent': r.spec_match_percent
                            }
                            for idx, r in enumerate(rec.top_recommendations[:3])
                        ]
                    }
                    if rec.selected_recommendation else
                    {
                        'rfp_product': rec.rfp_product_name,
                        'quantity': rec.quantity,
                        'unit': rec.unit,
                        'selected_sku': None,
                        'product_name': None,
                        'manufacturer': None,
                        'spec_match_percent': 0,
                        'top_3_options': [],
                        'note': 'No OEM product met the minimum spec-match threshold for this item',
                    }
                )
                for rec in recommendations
            ],
            'comparison_table': comparison_tables,
            'compliance_summary': self._build_compliance_summary(recommendations)
        }
        
        logger.info(f"✅ Technical analysis complete for RFP {rfp_id}")
        return response
    
    def _recommend_oem_products(self, rfp_product: Dict[str, Any]) -> ProductRecommendation:
        """
        Recommend top 3 OEM products for an RFP product
        """
        product_name = rfp_product.get('name', '')
        rfp_specs = rfp_product.get('specifications', {})
        quantity = rfp_product.get('quantity', 1)
        unit = rfp_product.get('unit', 'Nos')
        
        # Find matching products from repository
        match_results = []
        
        for oem_product in self.oem_repository:
            match_result = self._calculate_spec_match(rfp_specs, oem_product)
            if match_result.spec_match_percent > 0:
                match_results.append(match_result)
        
        # Sort by spec match percentage
        match_results.sort(key=lambda x: x.spec_match_percent, reverse=True)
        
        # Get top 3
        top_3 = match_results[:3] if match_results else []
        
        # Select best match
        selected = top_3[0] if top_3 else None
        
        # Build comparison table
        comparison_table = self._build_comparison_table(rfp_specs, top_3)
        
        return ProductRecommendation(
            rfp_product_name=product_name,
            rfp_specifications=rfp_specs,
            quantity=quantity,
            unit=unit,
            top_recommendations=top_3,
            selected_recommendation=selected,
            comparison_table=comparison_table
        )
    
    def _calculate_spec_match(self, rfp_specs: Dict[str, Any], 
                               oem_product: OEMProduct) -> SpecMatchResult:
        """
        Calculate specification match percentage using enhanced matching
        
        Features:
        - Direct OEM product spec matching
        - Datasheet-level matching with nested properties
        - Value normalization and semantic matching
        - All specs have equal weightage
        """
        oem_specs = oem_product.specifications
        
        # Get datasheet for enhanced matching
        datasheet = self.oem_datasheets.get(oem_product.sku, {}) if self.use_datasheets else {}
        
        matched_specs = {}
        unmatched_specs = []
        partial_matches = []
        compliance_notes = []
        
        total_specs = len(rfp_specs)
        if total_specs == 0:
            return SpecMatchResult(
                oem_product=oem_product,
                spec_match_percent=0,
                matched_specs={},
                unmatched_specs=[],
                partial_matches=[],
                compliance_notes=[]
            )
        
        match_score = 0
        
        for spec_key, rfp_value in rfp_specs.items():
            # Try direct OEM spec match first
            oem_value = oem_specs.get(spec_key)
            
            # If not found, try datasheet matching
            if oem_value is None and datasheet:
                oem_value = self._get_datasheet_value(datasheet, spec_key)
            
            if oem_value is None:
                unmatched_specs.append(spec_key)
                continue
            
            # Calculate match using enhanced comparison
            spec_match = self._compare_spec_values_enhanced(spec_key, rfp_value, oem_value)
            
            if spec_match >= 1.0:
                matched_specs[spec_key] = {
                    'rfp_value': rfp_value,
                    'oem_value': oem_value,
                    'match': 'FULL',
                    'source': 'datasheet' if spec_key not in oem_specs else 'product'
                }
                match_score += 1
            elif spec_match > 0:
                partial_matches.append({
                    'spec': spec_key,
                    'rfp_value': rfp_value,
                    'oem_value': oem_value,
                    'match_percent': spec_match * 100,
                    'source': 'datasheet' if spec_key not in oem_specs else 'product'
                })
                match_score += spec_match
            else:
                unmatched_specs.append(spec_key)
        
        # Equal weightage for all specs
        spec_match_percent = (match_score / total_specs) * 100 if total_specs > 0 else 0
        
        # Add compliance notes from certifications
        if 'BIS' in oem_product.certifications:
            compliance_notes.append("BIS certified")
        if 'ISI' in oem_product.certifications:
            compliance_notes.append("ISI marked")
        if 'CPRI' in oem_product.certifications:
            compliance_notes.append("CPRI approved")
        if 'ISO 9001' in oem_product.certifications:
            compliance_notes.append("ISO 9001 compliant")
        
        # Add datasheet compliance notes
        if datasheet:
            certs = datasheet.get('certifications', {})
            if certs.get('cpri_approved'):
                compliance_notes.append("CPRI test report available")
            if certs.get('fire_rating'):
                compliance_notes.append(f"Fire rated: {certs['fire_rating']}")
        
        return SpecMatchResult(
            oem_product=oem_product,
            spec_match_percent=round(spec_match_percent, 2),
            matched_specs=matched_specs,
            unmatched_specs=unmatched_specs,
            partial_matches=partial_matches,
            compliance_notes=compliance_notes
        )
    
    def _get_datasheet_value(self, datasheet: Dict[str, Any], spec_key: str) -> Any:
        """
        Get value from datasheet using key mapping
        Handles nested properties like electrical_properties.rated_voltage
        """
        # Check direct mapping
        for ds_key, norm_key in DATASHEET_KEY_MAP.items():
            if norm_key == spec_key:
                # Parse nested key
                parts = ds_key.split('.')
                value = datasheet
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        value = None
                        break
                if value is not None:
                    return value
        
        # Try common datasheet sections
        sections = ['electrical_properties', 'physical_properties']
        for section in sections:
            section_data = datasheet.get(section, {})
            if spec_key in section_data:
                return section_data[spec_key]
        
        return None
    
    def _compare_spec_values_enhanced(self, spec_key: str, rfp_value: Any, oem_value: Any) -> float:
        """
        Enhanced specification value comparison with:
        - Semantic matching for equivalent terms
        - Value normalization for different formats
        - Numeric extraction from strings
        """
        # Normalize values first
        rfp_normalized = self._normalize_value(spec_key, rfp_value)
        oem_normalized = self._normalize_value(spec_key, oem_value)
        
        # Try semantic matching for specific keys
        semantic_score = self._semantic_match(spec_key, rfp_normalized, oem_normalized)
        if semantic_score is not None:
            return semantic_score
        
        # Handle numeric comparisons
        rfp_numeric = self._extract_numeric(rfp_normalized)
        oem_numeric = self._extract_numeric(oem_normalized)
        
        if rfp_numeric is not None and oem_numeric is not None:
            if rfp_numeric == oem_numeric:
                return 1.0
            # Allow 10% tolerance for numeric values
            if rfp_numeric != 0:
                tolerance = abs(rfp_numeric) * 0.1
                if abs(rfp_numeric - oem_numeric) <= tolerance:
                    return 0.95
                # Partial match if within 20%
                if abs(rfp_numeric - oem_numeric) <= abs(rfp_numeric) * 0.2:
                    return 0.8
            return 0
        
        # Handle string comparisons
        if isinstance(rfp_normalized, str) and isinstance(oem_normalized, str):
            rfp_lower = rfp_normalized.lower().strip()
            oem_lower = oem_normalized.lower().strip()
            
            if rfp_lower == oem_lower:
                return 1.0
            if rfp_lower in oem_lower or oem_lower in rfp_lower:
                return 0.9
            # Check for partial word matches
            rfp_words = set(rfp_lower.split())
            oem_words = set(oem_lower.split())
            common_words = rfp_words.intersection(oem_words)
            if common_words:
                return len(common_words) / max(len(rfp_words), len(oem_words))
            return 0
        
        # Handle boolean comparisons
        if isinstance(rfp_normalized, bool) and isinstance(oem_normalized, bool):
            return 1.0 if rfp_normalized == oem_normalized else 0
        
        # Default: check equality
        return 1.0 if rfp_normalized == oem_normalized else 0
    
    def _normalize_value(self, spec_key: str, value: Any) -> Any:
        """
        Normalize a specification value for comparison
        """
        if value is None:
            return None
        
        # Convert to string for processing if needed
        str_value = str(value).strip()
        
        # Remove common suffixes/units for comparison
        str_value = re.sub(r'\s*(AC|DC)\s*$', '', str_value, flags=re.IGNORECASE)
        str_value = re.sub(r'\s*°C\s*$', '', str_value)
        str_value = re.sub(r'\s*A\s*$', '', str_value)
        str_value = re.sub(r'\s*V\s*$', '', str_value)
        str_value = re.sub(r'\s*sq\s*mm\s*$', '', str_value, flags=re.IGNORECASE)
        str_value = re.sub(r'\s*approx\.?\s*$', '', str_value, flags=re.IGNORECASE)
        
        # Try to convert back to original type
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        
        # Try to extract numeric
        try:
            if '.' in str_value:
                return float(str_value)
            return int(str_value)
        except (ValueError, TypeError):
            return str_value.strip()
    
    def _extract_numeric(self, value: Any) -> Optional[float]:
        """
        Extract numeric value from various formats
        e.g., "14A" -> 14, "70°C" -> 70, "1100V AC" -> 1100
        """
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Extract first number from string
            match = re.search(r'([\d.]+)', value)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _semantic_match(self, spec_key: str, rfp_value: Any, oem_value: Any) -> Optional[float]:
        """
        Perform semantic matching for known equivalent terms
        Returns None if no semantic mapping exists for this key
        
        Uses priority-based matching:
        1. Exact match with equivalent
        2. Value contained in equivalent
        3. Equivalent contained in value
        """
        spec_key_lower = spec_key.lower()
        
        # Select appropriate mapping
        mapping = None
        if 'conductor_material' in spec_key_lower or spec_key_lower == 'conductor':
            mapping = CONDUCTOR_MATERIAL_MAP
        elif 'insulation' in spec_key_lower:
            mapping = INSULATION_TYPE_MAP
        elif 'conductor_type' in spec_key_lower or 'conductor_class' in spec_key_lower:
            mapping = CONDUCTOR_TYPE_MAP
        elif 'armour' in spec_key_lower or 'armor' in spec_key_lower:
            mapping = ARMOUR_TYPE_MAP
        elif 'voltage' in spec_key_lower and 'rating' in spec_key_lower:
            mapping = VOLTAGE_RATING_MAP
        
        if mapping is None:
            return None
        
        # Normalize values
        rfp_lower = str(rfp_value).lower().strip() if rfp_value else ''
        oem_lower = str(oem_value).lower().strip() if oem_value else ''
        
        def find_category(value: str, mapping: dict) -> Optional[str]:
            """Find the best matching category for a value using priority matching"""
            if not value:
                return None
            
            # Priority 1: Exact match with any equivalent
            for category, equivalents in mapping.items():
                if value in equivalents:
                    return category
            
            # Priority 2: Value is contained in an equivalent (longer match preferred)
            best_match = None
            best_match_len = 0
            for category, equivalents in mapping.items():
                for equiv in equivalents:
                    if value in equiv and len(equiv) > best_match_len:
                        best_match = category
                        best_match_len = len(equiv)
            if best_match:
                return best_match
            
            # Priority 3: An equivalent is contained in value (longer equiv preferred)
            best_match = None
            best_match_len = 0
            for category, equivalents in mapping.items():
                for equiv in equivalents:
                    if equiv in value and len(equiv) > best_match_len:
                        best_match = category
                        best_match_len = len(equiv)
            
            return best_match
        
        # Find categories for both values
        rfp_category = find_category(rfp_lower, mapping)
        oem_category = find_category(oem_lower, mapping)
        
        # If both belong to same category, it's a match
        if rfp_category and oem_category:
            if rfp_category == oem_category:
                return 1.0
            else:
                return 0.0
        
        # If one is found but not the other, check if the unfound one contains keywords
        if rfp_category and not oem_category:
            # Check if oem_lower contains any word from the category
            if rfp_category in oem_lower or any(word in oem_lower for word in rfp_category.split()):
                return 0.9
        if oem_category and not rfp_category:
            if oem_category in rfp_lower or any(word in rfp_lower for word in oem_category.split()):
                return 0.9
        
        return None  # Let default comparison handle it
    
    def _build_comparison_table(self, rfp_specs: Dict[str, Any], 
                                 top_matches: List[SpecMatchResult]) -> List[Dict[str, Any]]:
        """
        Build comparison table of RFP specs vs OEM specs
        """
        comparison = []
        
        for spec_key, rfp_value in rfp_specs.items():
            row = {
                'specification': spec_key,
                'rfp_requirement': str(rfp_value),
                'oem_1': '',
                'oem_1_match': '',
                'oem_2': '',
                'oem_2_match': '',
                'oem_3': '',
                'oem_3_match': ''
            }
            
            for idx, match_result in enumerate(top_matches[:3]):
                oem_value = match_result.oem_product.specifications.get(spec_key, 'N/A')
                match_status = 'N/A'
                
                if spec_key in match_result.matched_specs:
                    match_status = '✓ Full Match'
                elif any(p['spec'] == spec_key for p in match_result.partial_matches):
                    partial = next(p for p in match_result.partial_matches if p['spec'] == spec_key)
                    match_status = f'~{partial["match_percent"]:.0f}%'
                elif spec_key in match_result.unmatched_specs:
                    match_status = '✗ No Match'
                
                row[f'oem_{idx+1}'] = str(oem_value)
                row[f'oem_{idx+1}_match'] = match_status
            
            comparison.append(row)
        
        # Add product info row
        comparison.insert(0, {
            'specification': 'Product SKU',
            'rfp_requirement': '-',
            'oem_1': top_matches[0].oem_product.sku if len(top_matches) > 0 else '',
            'oem_1_match': f'{top_matches[0].spec_match_percent}%' if len(top_matches) > 0 else '',
            'oem_2': top_matches[1].oem_product.sku if len(top_matches) > 1 else '',
            'oem_2_match': f'{top_matches[1].spec_match_percent}%' if len(top_matches) > 1 else '',
            'oem_3': top_matches[2].oem_product.sku if len(top_matches) > 2 else '',
            'oem_3_match': f'{top_matches[2].spec_match_percent}%' if len(top_matches) > 2 else ''
        })
        
        return comparison
    
    def _build_compliance_summary(self, recommendations: List[ProductRecommendation]) -> Dict[str, Any]:
        """Build compliance summary for all recommendations"""
        total_products = len(recommendations)
        avg_match = sum(r.selected_recommendation.spec_match_percent for r in recommendations if r.selected_recommendation) / total_products if total_products > 0 else 0
        
        return {
            'total_products': total_products,
            'average_spec_match': round(avg_match, 2),
            'fully_compliant': sum(1 for r in recommendations if r.selected_recommendation and r.selected_recommendation.spec_match_percent >= 90),
            'partially_compliant': sum(1 for r in recommendations if r.selected_recommendation and 70 <= r.selected_recommendation.spec_match_percent < 90),
            'needs_review': sum(1 for r in recommendations if r.selected_recommendation and r.selected_recommendation.spec_match_percent < 70)
        }
    
    def add_oem_product(self, product: OEMProduct):
        """Add OEM product to repository"""
        self.oem_repository.append(product)
    
    def get_products_by_category(self, category: str) -> List[OEMProduct]:
        """Get OEM products by category"""
        return [p for p in self.oem_repository if p.category.lower() == category.lower()]
    
    def export_recommendations_to_json(self, recommendations: List[ProductRecommendation]) -> str:
        """Export recommendations to JSON format"""
        data = []
        for rec in recommendations:
            data.append({
                'rfp_product': rec.rfp_product_name,
                'quantity': rec.quantity,
                'unit': rec.unit,
                'selected': {
                    'sku': rec.selected_recommendation.oem_product.sku if rec.selected_recommendation else None,
                    'name': rec.selected_recommendation.oem_product.product_name if rec.selected_recommendation else None,
                    'spec_match': rec.selected_recommendation.spec_match_percent if rec.selected_recommendation else 0
                },
                'alternatives': [
                    {'sku': r.oem_product.sku, 'spec_match': r.spec_match_percent}
                    for r in rec.top_recommendations[1:3]
                ]
            })
        return json.dumps(data, indent=2)


# Example usage
if __name__ == "__main__":
    tech = TechnicalAgent()
    
    # Sample RFP context
    sample_context = {
        'rfp_id': 'RFP_SAMPLE_001',
        'products_in_scope': [
            {
                'name': 'PVC Insulated Wire 1.5 sq mm',
                'specifications': {
                    'conductor': 'Electrolytic Grade Copper',
                    'insulation': 'PVC',
                    'cross_section_sqmm': 1.5,
                    'voltage_grade': '1100V',
                    'standard': 'IS 694:2010'
                },
                'quantity': 10000,
                'unit': 'meters'
            }
        ]
    }
    
    result = tech.process_rfp(sample_context)
    print(json.dumps(result, indent=2))
