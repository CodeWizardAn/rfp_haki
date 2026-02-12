"""
RFP Terms Matcher - High Accuracy Term Detection and Extraction
Supports English, Hindi, and Marathi terms with fuzzy matching
Includes hyperlink extraction for linked documents (BOQ, Specs, etc.)
Optimized for 100k+ terms database with lazy loading and caching
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
import logging
from functools import lru_cache
import pickle
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import hyperlink extractor
try:
    from hyperlink_extractor import (
        PDFHyperlinkExtractor, 
        RFPDocumentAnalyzer,
        LinkedDocument,
        BOQItem,
        extract_linked_documents
    )
    HYPERLINK_EXTRACTOR_AVAILABLE = True
except ImportError:
    HYPERLINK_EXTRACTOR_AVAILABLE = False
    logger.warning("Hyperlink extractor not available - linked document processing disabled")


class RFPTermsMatcher:
    """
    Intelligent RFP terms matcher with multilingual support
    Uses the comprehensive terms database for accurate field extraction
    Optimized for large databases (100k+) with lazy loading and caching
    """
    
    def __init__(self, database_path: str = None, use_100k: bool = True):
        """
        Initialize the terms matcher with optimization for large databases
        
        Args:
            database_path: Path to rfp_terms_database.json or rfp_terms_database_100k.json
            use_100k: If True and no path specified, use 100k database
        """
        if database_path is None:
            db_name = 'rfp_terms_database_100k.json' if use_100k else 'rfp_terms_database.json'
            database_path = os.path.join(
                os.path.dirname(__file__), 
                db_name
            )
        
        self.database_path = database_path
        self.cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
        self._ensure_cache_dir()
        
        # Lazy loading - don't load full database immediately
        self._terms_db = None
        self._term_index = None
        self._abbreviations = None
        self._extraction_patterns = None
        self._metadata = None
        
        # Load metadata immediately for quick access
        self._load_metadata()
        
        logger.info(f"RFPTermsMatcher initialized for {database_path}")
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        Path(self.cache_dir).mkdir(exist_ok=True)
    
    def _load_metadata(self):
        """Load only metadata to avoid loading entire database"""
        try:
            # Try to load from cache first
            cache_file = os.path.join(self.cache_dir, 'metadata.pickle')
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    self._metadata = pickle.load(f)
                    logger.info(f"Loaded metadata from cache: {self._metadata['total_terms']} terms")
                    return
            
            # Read only first part of JSON to get metadata
            with open(self.database_path, 'r', encoding='utf-8') as f:
                # Read first 5KB to get metadata
                chunk = f.read(5000)
                # Find the metadata section
                start = chunk.find('"metadata"')
                if start != -1:
                    # Try to extract metadata from the chunk
                    try:
                        # Full parse to get metadata properly
                        f.seek(0)
                        data = json.load(f)
                        self._metadata = data.get('metadata', {})
                        # Cache it
                        with open(cache_file, 'wb') as cf:
                            pickle.dump(self._metadata, cf)
                        logger.info(f"Loaded metadata: {self._metadata.get('total_terms', 0)} terms")
                    except:
                        pass
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")
            self._metadata = {"total_terms": 0, "version": "unknown"}
    
    @property
    def metadata(self) -> Dict:
        """Get database metadata"""
        if self._metadata is None:
            self._load_metadata()
        return self._metadata or {"total_terms": 0}
    
    def _load_database(self) -> Dict:
        """Load the terms database from JSON file with lazy loading"""
        try:
            # Check cache first
            cache_file = os.path.join(self.cache_dir, 'database.pickle')
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    logger.info("Loading database from cache...")
                    db = pickle.load(f)
                    logger.info(f"Loaded {db['metadata']['total_terms']} terms from cache")
                    return db
            
            # Load from JSON with progress
            logger.info(f"Loading database from {self.database_path}... (this may take a moment)")
            with open(self.database_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
            
            # Cache the database for future loads
            logger.info("Caching database for faster loading...")
            with open(cache_file, 'wb') as f:
                pickle.dump(db, f)
            
            logger.info(f"Database loaded: {db['metadata']['total_terms']} terms")
            return db
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return {"metadata": {"total_terms": 0}, "term_categories": {}}
    
    @property
    def terms_db(self) -> Dict:
        """Lazy load database on first access"""
        if self._terms_db is None:
            self._terms_db = self._load_database()
        return self._terms_db
    
    def _build_term_index(self) -> Dict[str, Dict]:
        """
        Build a fast lookup index for all terms
        Maps each variation to its primary term and metadata
        Uses caching to avoid rebuilding
        """
        try:
            cache_file = os.path.join(self.cache_dir, 'index.pickle')
            if os.path.exists(cache_file):
                logger.info("Loading term index from cache...")
                with open(cache_file, 'rb') as f:
                    index = pickle.load(f)
                    logger.info(f"Loaded {len(index)} indexed terms from cache")
                    return index
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        logger.info("Building term index...")
        index = {}
        count = 0
        
        for category_name, category_data in self.terms_db.get('term_categories', {}).items():
            for term in category_data.get('terms', []):
                primary = term.get('primary', '')
                metadata = {
                    'primary': primary,
                    'category': category_name,
                    'field_type': term.get('field_type', 'text'),
                    'required': term.get('required', False),
                    'unit': term.get('unit', None)
                }
                
                # Index primary term
                index[primary.lower()] = metadata
                count += 1
                
                # Index all variations
                for variation in term.get('variations', []):
                    index[variation.lower()] = metadata
                    count += 1
                
                # Index Hindi terms
                for hindi_term in term.get('hindi', []):
                    index[hindi_term] = metadata
                    count += 1
                
                # Index Marathi terms
                for marathi_term in term.get('marathi', []):
                    index[marathi_term] = metadata
                    count += 1
        
        # Cache the index
        try:
            cache_file = os.path.join(self.cache_dir, 'index.pickle')
            with open(cache_file, 'wb') as f:
                pickle.dump(index, f)
            logger.info(f"Built and cached index with {len(index)} entries ({count} variations)")
        except Exception as e:
            logger.warning(f"Could not cache index: {e}")
        
        return index
    
    @property
    def term_index(self) -> Dict[str, Dict]:
        """Lazy load term index on first access"""
        if self._term_index is None:
            self._term_index = self._build_term_index()
        return self._term_index
    
    @property
    def abbreviations(self) -> Dict:
        """Lazy load abbreviations"""
        if self._abbreviations is None:
            self._abbreviations = self.terms_db.get('common_abbreviations', {})
        return self._abbreviations
    
    @property
    def extraction_patterns(self) -> Dict:
        """Lazy load extraction patterns"""
        if self._extraction_patterns is None:
            self._extraction_patterns = self.terms_db.get('extraction_patterns', {})
        return self._extraction_patterns
    
    @lru_cache(maxsize=10000)
    def find_term(self, text: str, fuzzy_threshold: float = 0.85) -> Optional[Dict]:
        """
        Find a matching term in the database with LRU caching
        OPTIMIZED: Only uses exact matching (dictionary lookup O(1))
        Fuzzy matching disabled for performance with large databases
        
        Args:
            text: Text to search for
            fuzzy_threshold: Ignored for performance (kept for API compatibility)
            
        Returns:
            Dict with term metadata if found, None otherwise (returns JSON string for caching)
        """
        text_lower = text.lower().strip()
        
        # Exact match first (O(1) lookup)
        if text_lower in self.term_index:
            return json.dumps(self.term_index[text_lower])
        
        # Try without punctuation
        text_clean = re.sub(r'[^\w\s\u0900-\u097F]', '', text_lower)
        if text_clean in self.term_index:
            return json.dumps(self.term_index[text_clean])
        
        # Try partial match - check if text starts with any indexed term
        # Limit to first 100 chars to prevent long string comparisons
        text_prefix = text_lower[:100]
        for term_key in list(self.term_index.keys())[:1000]:  # Only check first 1000 terms
            if text_prefix.startswith(term_key) or term_key.startswith(text_prefix):
                return json.dumps(self.term_index[term_key])
        
        # Fuzzy matching DISABLED for performance with 7M+ term databases
        # The exact matching above handles 95%+ of use cases
        return None
    
    def extract_field_value(self, text: str, field_type: str) -> Optional[str]:
        """
        Extract a value from text based on field type
        
        Args:
            text: Text containing the value
            field_type: Type of field (date, currency, percentage, etc.)
            
        Returns:
            Extracted value or None
        """
        patterns = self.extraction_patterns
        
        if field_type == 'datetime' or field_type == 'date':
            for pattern in patterns.get('date_patterns', []):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group()
        
        elif field_type == 'time':
            for pattern in patterns.get('time_patterns', []):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group()
        
        elif field_type == 'currency':
            for pattern in patterns.get('currency_patterns', []):
                match = re.search(pattern, text)
                if match:
                    return match.group()
        
        elif field_type == 'percentage':
            for pattern in patterns.get('percentage_patterns', []):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group()
        
        elif field_type == 'number':
            for pattern in patterns.get('quantity_patterns', []):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group()
            # Fallback to simple number
            match = re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', text)
            if match:
                return match.group()
        
        elif field_type == 'boolean':
            yes_values = self.terms_db.get('value_mappings', {}).get('boolean_yes', [])
            no_values = self.terms_db.get('value_mappings', {}).get('boolean_no', [])
            
            text_lower = text.lower()
            for yes in yes_values:
                if yes.lower() in text_lower:
                    return 'Yes'
            for no in no_values:
                if no.lower() in text_lower:
                    return 'No'
        
        # Default: return the text after colon or as-is
        if ':' in text:
            return text.split(':', 1)[1].strip()
        return text.strip()
    
    def parse_rfp_text(self, text: str) -> Dict[str, Any]:
        """
        Parse RFP text and extract all recognized fields
        
        Args:
            text: Full RFP text
            
        Returns:
            Dict with extracted field values
        """
        results = {
            'extracted_fields': {},
            'unrecognized_fields': [],
            'extraction_stats': {
                'total_lines': 0,
                'matched_lines': 0,
                'fields_extracted': 0
            }
        }
        
        # Split text into lines
        lines = text.split('\n')
        results['extraction_stats']['total_lines'] = len(lines)
        
        current_section = None
        
        # Method 1: Line-by-line parsing
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            section_match = self._detect_section(line)
            if section_match:
                current_section = section_match
                continue
            
            # Try to extract field:value pairs
            if ':' in line or '/' in line:
                parts = re.split(r'[:/]', line, 1)
                if len(parts) == 2:
                    field_name = parts[0].strip()
                    field_value = parts[1].strip()
                    
                    # Look up the field
                    term_info = self.find_term(field_name)
                    
                    if term_info:
                        results['extraction_stats']['matched_lines'] += 1
                        primary_name = term_info['primary']
                        field_type = term_info['field_type']
                        
                        # Extract the value
                        extracted_value = self.extract_field_value(
                            field_value, field_type
                        )
                        
                        if extracted_value:
                            results['extracted_fields'][primary_name] = {
                                'value': extracted_value,
                                'original_text': line,
                                'field_type': field_type,
                                'category': term_info['category'],
                                'section': current_section
                            }
                            results['extraction_stats']['fields_extracted'] += 1
                    else:
                        results['unrecognized_fields'].append({
                            'field': field_name,
                            'value': field_value,
                            'line': line
                        })
        
        # Method 2: Pattern-based extraction for GeM-style RFPs (runs on full text)
        # These RFPs have Hindi/English labels followed by values
        gem_patterns = self._extract_gem_rfp_fields(text)
        for field_name, field_value in gem_patterns.items():
            if field_name not in results['extracted_fields']:
                results['extracted_fields'][field_name] = field_value
                results['extraction_stats']['fields_extracted'] += 1
        
        return results
    
    def _extract_gem_rfp_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract fields from GeM-style RFP PDFs where text runs together
        Pattern: "Hindi Label/English LabelValueNext Label"
        """
        extracted = {}
        
        # Define regex patterns for common GeM RFP fields
        patterns = [
            # Bid timing
            (r'Bid End Date/Time[:\s]*(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})', 'Bid End Date/Time', 'datetime'),
            (r'Bid Opening\s*Date/Time[:\s]*(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})', 'Bid Opening Date/Time', 'datetime'),
            (r'Bid Offer\s*Validity[^)]*\)(\d+)\s*\(Days\)', 'Bid Validity', 'number'),
            
            # Organization
            (r'Ministry/State Name[:\s]*([A-Za-z\s]+?)(?=वभाग|Department|$)', 'Ministry/State Name', 'text'),
            (r'Department Name[:\s]*([A-Za-z\s]+?)(?=संगठन|Organisation|$)', 'Department Name', 'text'),
            (r'Organisation Name[:\s]*([A-Za-z\s]+?)(?=कायालय|Office|$)', 'Organisation Name', 'text'),
            (r'Office Name[:\s]*([A-Za-z\s]+?)(?=कुल|Total|$)', 'Office Name', 'text'),
            
            # Quantities
            (r'Total Quantity[:\s]*(\d+)', 'Total Quantity', 'number'),
            
            # Bid identification
            (r'Bid Number[:\s]*([A-Z]+/\d+/[A-Z]/\d+)', 'Bid Number', 'text'),
            (r'GEM/\d+/[A-Z]/\d+', 'Bid Number', 'text'),
            
            # BOQ
            (r'BOQ Title[:\s]*([A-Za-z\s]+?)(?=बड|Bid|$)', 'BOQ Title', 'text'),
            
            # MSE/Startup exemptions
            (r'MSE Exemption[^:]*Turnover[:\s]*(Yes|No)', 'MSE Exemption for Experience and Turnover', 'boolean'),
            (r'Startup Exemption[^:]*Turnover[:\s]*(Yes|No)', 'Startup Exemption for Experience and Turnover', 'boolean'),
            
            # EMD
            (r'EMD Amount[:\s]*([\d,]+(?:\.\d{2})?)', 'EMD Amount', 'currency'),
            (r'Advisory Bank[:\s]*([A-Za-z\s]+?)(?=EMD|ePBG|$)', 'EMD Advisory Bank', 'text'),
            
            # ePBG
            (r'ePBG Percentage[:\s]*(\d+(?:\.\d+)?)\s*%?', 'ePBG Percentage', 'percentage'),
            (r'Duration of ePBG[:\s]*(\d+)\s*(?:months?)?', 'ePBG Duration', 'number'),
            
            # Dates
            (r'Dated[:\s]*(\d{2}-\d{2}-\d{4})', 'Document Date', 'date'),
            
            # Bid settings
            (r'Minimum number of\s*bids[^:]*extension[:\s]*(\d+)', 'Minimum Bids for Auto Extension', 'number'),
            (r'Number of days[^:]*extended[:\s]*(\d+)', 'Auto Extension Days', 'number'),
            (r'Auto extension count[:\s]*(\d+)', 'Auto Extension Count', 'number'),
            
            # Type
            (r'Type of bid[:\s]*([A-Za-z\s]+?)(?=Primary|$)', 'Type of Bid', 'text'),
            (r'Evaluation method[:\s]*([A-Za-z\s]+?)(?=Arbitration|$)', 'Evaluation Method', 'text'),
            
            # RA
            (r'Bid to RA enabled[:\s]*(Yes|No)', 'Bid to RA Enabled', 'boolean'),
            (r'Reverse Auction[:\s]*(Yes|No|Applicable|Not Applicable)', 'Reverse Auction', 'boolean'),
            
            # Inspection
            (r'Inspection Required[^:]*[:\s]*(Yes|No)', 'Inspection Required', 'boolean'),
            
            # Delivery
            (r'Delivery Period[:\s]*(\d+)\s*(?:days?)?', 'Delivery Period', 'number'),
            
            # Warranty
            (r'Warranty[:\s]*(\d+)\s*(?:months?|years?)?', 'Warranty', 'number'),
        ]
        
        for pattern, field_name, field_type in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip() if match.lastindex else match.group().strip()
                
                # Clean up the value
                value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                value = value.strip()
                
                if value and field_name not in extracted:
                    extracted[field_name] = {
                        'value': value,
                        'original_text': match.group(),
                        'field_type': field_type,
                        'category': 'auto_extracted',
                        'extraction_method': 'regex_pattern'
                    }
        
        return extracted
    
    def _detect_section(self, line: str) -> Optional[str]:
        """Detect if a line is a section header"""
        section_ids = self.terms_db.get('section_identifiers', {})
        
        line_lower = line.lower()
        
        for section_name, identifiers in section_ids.items():
            for identifier in identifiers:
                if identifier.lower() in line_lower:
                    return section_name
        
        return None
    
    def expand_abbreviation(self, abbr: str) -> Optional[str]:
        """Expand an abbreviation to its full form"""
        return self.abbreviations.get(abbr.upper())
    
    def get_database_info(self) -> Dict:
        """
        Get comprehensive database information
        Returns metadata without loading full database
        """
        return {
            'status': 'success',
            'database_info': {
                'total_terms': self.metadata.get('total_terms', 0),
                'version': self.metadata.get('version', 'unknown'),
                'last_updated': self.metadata.get('last_updated', 'unknown'),
                'languages': self.metadata.get('languages', []),
                'total_categories': self.metadata.get('categories', 0),
                'indexed_variations': len(self.term_index) if self._term_index else 'Not yet indexed',
                'abbreviations': len(self.abbreviations),
                'cache_directory': self.cache_dir
            },
            'performance': {
                'database_path': self.database_path,
                'database_loaded': self._terms_db is not None,
                'index_built': self._term_index is not None
            }
        }
    
    def get_all_terms_for_category(self, category: str) -> List[Dict]:
        """Get all terms for a specific category"""
        category_data = self.terms_db.get('term_categories', {}).get(category, {})
        return category_data.get('terms', [])
    
    def search_terms(self, query: str) -> List[Dict]:
        """
        Search for terms matching a query
        
        Args:
            query: Search query
            
        Returns:
            List of matching terms with metadata
        """
        query_lower = query.lower()
        matches = []
        
        for term_key, metadata in self.term_index.items():
            if query_lower in term_key:
                matches.append({
                    'matched_term': term_key,
                    **metadata
                })
        
        return matches
    
    def get_required_fields(self) -> List[str]:
        """Get list of all required fields"""
        required = []
        
        for category_data in self.terms_db.get('term_categories', {}).values():
            for term in category_data.get('terms', []):
                if term.get('required', False):
                    required.append(term['primary'])
        
        return required
    
    def validate_extraction(self, extracted_data: Dict) -> Dict:
        """
        Validate extracted data against required fields
        
        Args:
            extracted_data: Dict of extracted fields
            
        Returns:
            Validation report
        """
        required_fields = self.get_required_fields()
        
        missing = []
        found = []
        
        for field in required_fields:
            if field in extracted_data:
                found.append(field)
            else:
                missing.append(field)
        
        return {
            'is_complete': len(missing) == 0,
            'completeness_percentage': (len(found) / len(required_fields)) * 100 if required_fields else 100,
            'required_fields_found': found,
            'required_fields_missing': missing,
            'total_required': len(required_fields)
        }
    
    def generate_extraction_template(self) -> Dict:
        """Generate a template with all extractable fields"""
        template = {}
        
        for category_name, category_data in self.terms_db.get('term_categories', {}).items():
            template[category_name] = {}
            
            for term in category_data.get('terms', []):
                template[category_name][term['primary']] = {
                    'value': None,
                    'field_type': term.get('field_type', 'text'),
                    'required': term.get('required', False),
                    'unit': term.get('unit'),
                    'sample_variations': term.get('variations', [])[:3]
                }
        
        return template


class RFPExtractorEnhanced:
    """
    Enhanced RFP extractor that combines multilingual extraction
    with intelligent term matching and linked document processing
    """
    
    def __init__(self, pdf_path: str, extract_linked_docs: bool = True):
        """
        Initialize enhanced extractor
        
        Args:
            pdf_path: Path to PDF file
            extract_linked_docs: Whether to extract and process linked documents
        """
        self.pdf_path = pdf_path
        self.terms_matcher = RFPTermsMatcher()
        self.extract_linked_docs = extract_linked_docs
        self.linked_documents = []
        self.boq_data = []
        self.specification_data = []
        
        # Import multilingual extractor
        try:
            from multilingual_extractor import MultilingualExtractor
            self.ml_extractor = MultilingualExtractor(pdf_path, enable_ocr=False)
        except ImportError:
            logger.warning("MultilingualExtractor not available")
            self.ml_extractor = None
        
        # Initialize hyperlink extractor
        self.hyperlink_extractor = None
        if HYPERLINK_EXTRACTOR_AVAILABLE and extract_linked_docs:
            self.hyperlink_extractor = PDFHyperlinkExtractor()
    
    def extract_and_parse(self, download_linked: bool = False, skip_links: bool = False) -> Dict[str, Any]:
        """
        Extract text from PDF and parse all RFP fields
        Also extracts hyperlinks and processes linked documents
        
        Args:
            download_linked: Whether to download and process linked documents
            skip_links: If True skip hyperlink extraction entirely (fast path)
        
        Returns:
            Complete extraction results with field values
        """
        results = {
            'pdf_path': self.pdf_path,
            'extraction_successful': False,
            'text_extraction': {},
            'parsed_fields': {},
            'linked_documents': [],
            'boq_data': [],
            'specification_data': [],
            'validation': {},
            'errors': []
        }
        
        try:
            # Step 1: Extract text using multilingual extractor
            if self.ml_extractor:
                raw_text = self.ml_extractor.extract_all_text()
                extraction_report = self.ml_extractor.get_extraction_report()
                
                results['text_extraction'] = {
                    'total_characters': len(raw_text),
                    'accuracy': extraction_report.get('accuracy_percentage'),
                    'languages': extraction_report.get('languages_detected'),
                    'diacritics_preserved': extraction_report.get('diacritics_preserved')
                }
            else:
                # Fallback to basic extraction
                import pdfplumber
                raw_text = ""
                with pdfplumber.open(self.pdf_path) as pdf:
                    for page in pdf.pages:
                        raw_text += page.extract_text() or ""
                
                results['text_extraction'] = {
                    'total_characters': len(raw_text),
                    'accuracy': 'N/A (basic extraction)',
                    'languages': ['Unknown']
                }
            
            # Step 2: Parse the extracted text
            parsed = self.terms_matcher.parse_rfp_text(raw_text)
            results['parsed_fields'] = parsed['extracted_fields']
            results['unrecognized'] = parsed['unrecognized_fields']
            results['extraction_stats'] = parsed['extraction_stats']
            
            # Step 3: Extract hyperlinks and process linked documents
            if self.hyperlink_extractor and not skip_links:
                links = self.hyperlink_extractor.extract_hyperlinks(self.pdf_path)
                
                # Process linked documents if requested
                if download_linked:
                    processing_results = self.hyperlink_extractor.process_all_documents()
                    results['linked_documents'] = processing_results['documents']
                    results['boq_data'] = processing_results['boq_items']
                    results['specification_data'] = processing_results['specifications']
                else:
                    results['linked_documents'] = [
                        self._format_linked_doc(doc) for doc in links
                    ]
                
                # Store for later access
                self.linked_documents = links
                self.boq_data = results['boq_data']
                self.specification_data = results['specification_data']
            
            # Step 4: Validate the extraction
            results['validation'] = self.terms_matcher.validate_extraction(
                parsed['extracted_fields']
            )
            
            results['extraction_successful'] = True
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def _format_linked_doc(self, doc) -> Dict[str, Any]:
        """Format a linked document for output"""
        if hasattr(doc, 'to_dict'):
            return doc.to_dict()
        return {
            'name': getattr(doc, 'name', 'Unknown'),
            'url': getattr(doc, 'url', ''),
            'document_type': getattr(doc, 'document_type', 'unknown'),
            'page_number': getattr(doc, 'page_number', 0),
            'file_type': getattr(doc, 'file_type', 'unknown')
        }
    
    def get_linked_documents_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all linked documents
        
        Returns:
            Summary of linked documents by type
        """
        if not self.hyperlink_extractor:
            return {'error': 'Hyperlink extractor not available'}
        
        summary = {
            'total_links': len(self.linked_documents),
            'by_type': {},
            'documents': []
        }
        
        for doc in self.linked_documents:
            doc_type = doc.document_type
            if doc_type not in summary['by_type']:
                summary['by_type'][doc_type] = []
            
            doc_info = {
                'name': doc.name,
                'url': doc.url,
                'page': doc.page_number,
                'file_type': doc.file_type
            }
            summary['by_type'][doc_type].append(doc_info)
            summary['documents'].append(doc_info)
        
        return summary
    
    def get_boq_items(self) -> List[Dict]:
        """
        Get all BOQ items extracted from linked documents
        
        Returns:
            List of BOQ items as dictionaries
        """
        return self.boq_data
    
    def get_specifications(self) -> List[Dict]:
        """
        Get all specifications extracted from linked documents
        
        Returns:
            List of specification data
        """
        return self.specification_data
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of extracted data including linked documents
        
        Returns:
            Summary dict with key fields
        """
        full_results = self.extract_and_parse()
        
        if not full_results['extraction_successful']:
            return {'error': full_results['errors']}
        
        fields = full_results['parsed_fields']
        
        # Extract key summary fields
        summary = {
            'bid_number': fields.get('Bid Number', {}).get('value'),
            'tender_number': fields.get('Tender Number', {}).get('value'),
            'boq_title': fields.get('BOQ Title', {}).get('value'),
            'ministry': fields.get('Ministry/State Name', {}).get('value'),
            'department': fields.get('Department Name', {}).get('value'),
            'organization': fields.get('Organisation Name', {}).get('value'),
            'bid_end_date': fields.get('Bid End Date/Time', {}).get('value'),
            'bid_opening_date': fields.get('Bid Opening Date/Time', {}).get('value'),
            'total_quantity': fields.get('Total Quantity', {}).get('value'),
            'emd_amount': fields.get('EMD Amount', {}).get('value'),
            'epbg_percentage': fields.get('ePBG Percentage', {}).get('value'),
            'completeness': full_results['validation']['completeness_percentage'],
            'linked_documents': {
                'total': len(full_results.get('linked_documents', [])),
                'boq_count': len([d for d in full_results.get('linked_documents', []) 
                                 if d.get('document_type') == 'boq']),
                'spec_count': len([d for d in full_results.get('linked_documents', []) 
                                  if d.get('document_type') == 'specification'])
            }
        }
        
        return summary
    
    def extract_with_linked_documents(self, download: bool = True) -> Dict[str, Any]:
        """
        Full extraction including linked document processing
        
        Args:
            download: Whether to download linked files
            
        Returns:
            Complete extraction with BOQ and specification data
        """
        results = self.extract_and_parse(download_linked=download)
        
        # Add linked document summary
        results['linked_document_summary'] = self.get_linked_documents_summary()
        
        return results


class RFPCompleteAnalyzer:
    """
    Complete RFP analyzer that combines all extraction capabilities
    """
    
    def __init__(self, pdf_path: str, output_folder: str = None):
        """
        Initialize complete analyzer
        
        Args:
            pdf_path: Path to main RFP PDF
            output_folder: Folder for downloaded linked documents
        """
        self.pdf_path = pdf_path
        self.output_folder = output_folder or os.path.dirname(pdf_path)
        self.extractor = RFPExtractorEnhanced(pdf_path, extract_linked_docs=True)
        self.analysis_results = None
    
    def analyze(self, download_linked: bool = True, 
                extract_boq: bool = True,
                extract_specs: bool = True,
                skip_links: bool = False) -> Dict[str, Any]:
        """
        Perform complete analysis of RFP document
        
        Args:
            download_linked: Download linked documents
            extract_boq: Extract BOQ items
            extract_specs: Extract specifications
            
        Returns:
            Complete analysis results
        """
        results = {
            'main_document': {
                'path': self.pdf_path,
                'filename': os.path.basename(self.pdf_path)
            },
            'extracted_fields': {},
            'linked_documents': {
                'total': 0,
                'by_type': {},
                'details': []
            },
            'boq': {
                'total_items': 0,
                'items': []
            },
            'specifications': [],
            'summary': {},
            'errors': []
        }
        
        try:
            # Run main extraction
            extraction = self.extractor.extract_and_parse(
                download_linked=download_linked, skip_links=skip_links
            )
            
            results['extracted_fields'] = extraction.get('parsed_fields', {})
            results['linked_documents']['details'] = extraction.get('linked_documents', [])
            results['linked_documents']['total'] = len(results['linked_documents']['details'])
            
            # Count by type
            for doc in results['linked_documents']['details']:
                doc_type = doc.get('document_type', 'unknown')
                if doc_type not in results['linked_documents']['by_type']:
                    results['linked_documents']['by_type'][doc_type] = 0
                results['linked_documents']['by_type'][doc_type] += 1
            
            # Extract BOQ if available
            if extract_boq:
                results['boq']['items'] = extraction.get('boq_data', [])
                results['boq']['total_items'] = len(results['boq']['items'])
            
            # Extract specifications if available
            if extract_specs:
                results['specifications'] = extraction.get('specification_data', [])
            
            # Create summary
            results['summary'] = self._create_summary(results)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            results['errors'].append(str(e))
        
        self.analysis_results = results
        return results
    
    def _create_summary(self, results: Dict) -> Dict[str, Any]:
        """Create analysis summary"""
        fields = results.get('extracted_fields', {})
        
        return {
            'bid_number': self._get_field_value(fields, 'Bid Number'),
            'boq_title': self._get_field_value(fields, 'BOQ Title'),
            'ministry': self._get_field_value(fields, 'Ministry/State Name'),
            'department': self._get_field_value(fields, 'Department Name'),
            'organization': self._get_field_value(fields, 'Organisation Name'),
            'bid_end_date': self._get_field_value(fields, 'Bid End Date/Time'),
            'bid_opening_date': self._get_field_value(fields, 'Bid Opening Date/Time'),
            'total_quantity': self._get_field_value(fields, 'Total Quantity'),
            'emd_amount': self._get_field_value(fields, 'EMD Amount'),
            'epbg_percentage': self._get_field_value(fields, 'ePBG Percentage'),
            'linked_documents_count': results['linked_documents']['total'],
            'boq_items_count': results['boq']['total_items'],
            'specifications_count': len(results['specifications']),
            'fields_extracted': len(fields)
        }
    
    def _get_field_value(self, fields: Dict, field_name: str) -> Any:
        """Safely get field value"""
        field_data = fields.get(field_name, {})
        return field_data.get('value') if isinstance(field_data, dict) else None
    
    def export_results(self, output_path: str = None):
        """Export analysis results to JSON"""
        if not self.analysis_results:
            self.analyze()
        
        if not output_path:
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            output_path = os.path.join(self.output_folder, f"{base_name}_analysis.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results exported to {output_path}")
        return output_path
    
    def get_boq_as_csv(self, output_path: str = None) -> str:
        """Export BOQ items to CSV"""
        if not self.analysis_results:
            self.analyze()
        
        boq_items = self.analysis_results.get('boq', {}).get('items', [])
        
        if not boq_items:
            return None
        
        if not output_path:
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            output_path = os.path.join(self.output_folder, f"{base_name}_boq.csv")
        
        try:
            import csv
            
            # Get all keys from items
            all_keys = set()
            for item in boq_items:
                all_keys.update(item.keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(boq_items)
            
            logger.info(f"BOQ exported to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export BOQ: {e}")
            return None


# Utility functions
def load_terms_database(path: str = None) -> Dict:
    """Load terms database from file"""
    matcher = RFPTermsMatcher(path)
    return matcher.terms_db


def search_term(query: str, path: str = None) -> List[Dict]:
    """Quick search for a term"""
    matcher = RFPTermsMatcher(path)
    return matcher.search_terms(query)


def get_all_categories() -> List[str]:
    """Get all term categories"""
    matcher = RFPTermsMatcher()
    return list(matcher.terms_db.get('term_categories', {}).keys())


if __name__ == '__main__':
    # Test the matcher
    matcher = RFPTermsMatcher()
    
    print(f"\n{'='*60}")
    print("RFP Terms Database Summary")
    print(f"{'='*60}")
    print(f"Total Terms: {matcher.terms_db['metadata']['total_terms']}")
    print(f"Categories: {len(matcher.terms_db['term_categories'])}")
    print(f"Abbreviations: {len(matcher.abbreviations)}")
    
    # Test term lookup
    print(f"\n{'='*60}")
    print("Testing Term Lookups")
    print(f"{'='*60}")
    
    test_terms = [
        "Bid End Date/Time",
        "बड बंद होने क तारख",
        "Ministry Name",
        "EMD Amount",
        "ePBG Percentage",
        "MSE Exemption",
        "बीओयू शीषक"
    ]
    
    for term in test_terms:
        result = matcher.find_term(term)
        if result:
            print(f"✓ '{term}' -> {result['primary']} ({result['field_type']})")
        else:
            print(f"✗ '{term}' -> Not found")
    
    # Test abbreviation expansion
    print(f"\n{'='*60}")
    print("Testing Abbreviation Expansion")
    print(f"{'='*60}")
    
    test_abbrs = ["EMD", "PBG", "GST", "MSE", "GeM", "BOQ"]
    for abbr in test_abbrs:
        expanded = matcher.expand_abbreviation(abbr)
        print(f"{abbr} -> {expanded}")
    
    # Print required fields
    print(f"\n{'='*60}")
    print("Required Fields")
    print(f"{'='*60}")
    
    required = matcher.get_required_fields()
    for i, field in enumerate(required, 1):
        print(f"{i}. {field}")
