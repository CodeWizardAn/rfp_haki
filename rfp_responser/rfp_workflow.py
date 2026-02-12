"""
RFP Workflow Integration Module
Integrates PDF extraction, spec matching, and bid generation
Connects with agents for intelligent processing
"""

import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import shutil

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import PDF extraction modules
try:
    from pdf_extraction.pdf_extraction_manager import PDFExtractionManager
    from pdf_extraction.rfp_terms_matcher import RFPTermsMatcher
    PDF_EXTRACTION_AVAILABLE = True
except ImportError as e:
    PDF_EXTRACTION_AVAILABLE = False
    print(f"PDF extraction not available: {e}")

# Import spec comparer modules
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'spec_comparer'))
    from spec_comparer.app import SpecMatcher, OEMProductDatabase, SpecCalculator
    # OEM data path
    OEM_DATA_PATH = str(Path(__file__).parent.parent / 'wires_cables_data' / 'wires_cables_data')
    SPEC_COMPARER_AVAILABLE = True
except ImportError as e:
    SPEC_COMPARER_AVAILABLE = False
    OEM_DATA_PATH = None
    print(f"Spec comparer not available: {e}")

# Import agent modules
try:
    from agents.master_agent import MasterAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    print(f"Agents not available: {e}")

# Import bid modules
from bid_templates import BidTemplateManager, BidBuilder, BidStatus
from bid_price_calculator import PriceCalculator, TaxType
from bid_document_generator import PDFBidGenerator, ExcelBidGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RFPWorkflowManager:
    """
    Complete RFP Workflow Manager
    
    Workflow:
    1. Upload RFP PDF
    2. Extract text and metadata from PDF
    3. Parse RFP terms and requirements
    4. Match specs against OEM products (Top 3)
    5. Calculate pricing and costs
    6. Auto-fill any forms found in RFP
    7. Generate bid document
    8. Use agents for intelligent processing (optional)
    """
    
    def __init__(self, upload_folder: str = None):
        self.upload_folder = Path(upload_folder or os.path.join(os.path.dirname(__file__), 'uploads'))
        self.upload_folder.mkdir(exist_ok=True)
        
        # Initialize managers
        self.pdf_manager = PDFExtractionManager(str(self.upload_folder)) if PDF_EXTRACTION_AVAILABLE else None
        self.terms_matcher = RFPTermsMatcher() if PDF_EXTRACTION_AVAILABLE else None
        
        # Initialize product database and spec matcher
        self.product_db = None
        self.spec_matcher = None
        self.spec_calculator = None
        if SPEC_COMPARER_AVAILABLE and OEM_DATA_PATH:
            try:
                self.product_db = OEMProductDatabase(OEM_DATA_PATH)
                self.spec_matcher = SpecMatcher(self.product_db)
                self.spec_calculator = SpecCalculator()
            except Exception as e:
                logger.warning(f"Could not initialize spec comparer: {e}")
        
        # Initialize bid managers
        self.bid_template_manager = BidTemplateManager()
        self.price_calculator = PriceCalculator()
        self.pdf_generator = PDFBidGenerator()
        self.excel_generator = ExcelBidGenerator()
        
        # Initialize master agent (optional)
        self.master_agent = MasterAgent() if AGENTS_AVAILABLE else None
        
        # Current workflow state
        self.current_workflow: Dict[str, Any] = {}
        
        logger.info("✅ RFP Workflow Manager initialized")
        logger.info(f"   PDF Extraction: {'✅' if PDF_EXTRACTION_AVAILABLE else '❌'}")
        logger.info(f"   Spec Comparer: {'✅' if SPEC_COMPARER_AVAILABLE else '❌'}")
        logger.info(f"   Agents: {'✅' if AGENTS_AVAILABLE else '❌'}")
    
    def process_rfp(self, pdf_path: str, vendor_info: Dict = None, 
                    use_agents: bool = False) -> Dict[str, Any]:
        """
        Complete RFP processing workflow
        
        Args:
            pdf_path: Path to uploaded RFP PDF
            vendor_info: Vendor information for bid generation
            use_agents: Whether to use AI agents for processing
        
        Returns:
            Complete workflow result with matched products and generated bid
        """
        workflow_id = f"WF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.current_workflow = {
            'workflow_id': workflow_id,
            'status': 'processing',
            'started_at': datetime.now().isoformat(),
            'pdf_path': pdf_path,
            'vendor_info': vendor_info or {},
            'stages': {}
        }
        
        try:
            # Stage 1: Extract PDF content
            logger.info(f"[{workflow_id}] Stage 1: Extracting PDF content...")
            extraction_result = self._extract_pdf(pdf_path)
            self.current_workflow['stages']['extraction'] = extraction_result
            
            if not extraction_result.get('success'):
                raise Exception(f"PDF extraction failed: {extraction_result.get('error')}")
            
            # Stage 2: Parse RFP terms and requirements
            logger.info(f"[{workflow_id}] Stage 2: Parsing RFP terms...")
            parsed_rfp = self._parse_rfp_terms(extraction_result['text'])
            self.current_workflow['stages']['parsing'] = parsed_rfp
            
            # Stage 3: Extract form fields (if any)
            logger.info(f"[{workflow_id}] Stage 3: Extracting form fields...")
            form_fields = self._extract_form_fields(extraction_result['text'])
            self.current_workflow['stages']['form_fields'] = form_fields
            
            # Stage 4: Match specs against OEM products
            logger.info(f"[{workflow_id}] Stage 4: Matching specifications...")
            matched_products = self._match_specifications(parsed_rfp['requirements'])
            self.current_workflow['stages']['matching'] = matched_products
            
            # Stage 5: Calculate pricing and costs
            logger.info(f"[{workflow_id}] Stage 5: Calculating pricing...")
            pricing = self._calculate_pricing(matched_products, parsed_rfp)
            self.current_workflow['stages']['pricing'] = pricing
            
            # Stage 6: Use agents (optional)
            if use_agents and AGENTS_AVAILABLE:
                logger.info(f"[{workflow_id}] Stage 6: Agent processing...")
                agent_result = self._process_with_agents(parsed_rfp, matched_products)
                self.current_workflow['stages']['agents'] = agent_result
            
            # Stage 7: Generate bid document
            logger.info(f"[{workflow_id}] Stage 7: Generating bid document...")
            bid_result = self._generate_bid(
                workflow_id=workflow_id,
                rfp_data=parsed_rfp,
                matched_products=matched_products,
                pricing=pricing,
                vendor_info=vendor_info or {},
                form_fields=form_fields
            )
            self.current_workflow['stages']['bid_generation'] = bid_result
            
            # Complete workflow
            self.current_workflow['status'] = 'completed'
            self.current_workflow['completed_at'] = datetime.now().isoformat()
            
            return self.current_workflow
            
        except Exception as e:
            logger.error(f"[{workflow_id}] Workflow failed: {e}")
            self.current_workflow['status'] = 'failed'
            self.current_workflow['error'] = str(e)
            return self.current_workflow
    
    def _extract_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text and metadata from PDF"""
        if not PDF_EXTRACTION_AVAILABLE or not self.pdf_manager:
            # Fallback basic extraction
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return {
                    'success': True,
                    'text': text,
                    'pages': len(reader.pages),
                    'method': 'fallback'
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        try:
            # Use PDF extraction manager
            filename = os.path.basename(pdf_path)
            unique_id = self.pdf_manager.generate_unique_id(filename)
            
            # Extract text
            text, page_info = self.pdf_manager.extract_text_from_pdf(pdf_path)
            
            return {
                'success': True,
                'text': text,
                'unique_id': unique_id,
                'page_info': page_info,
                'method': 'pdf_extraction_manager'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_rfp_terms(self, text: str) -> Dict[str, Any]:
        """Parse RFP text to extract terms and requirements"""
        result = {
            'rfp_id': None,
            'title': None,
            'issuing_authority': None,
            'due_date': None,
            'requirements': [],
            'tests_required': [],
            'standards': [],
            'terms_found': []
        }
        
        # Use terms matcher if available
        if self.terms_matcher:
            try:
                match_result = self.terms_matcher.parse_rfp_text(text)
                # parse_rfp_text returns {'extracted_fields': {...}, 'unrecognized_fields': [...], 'extraction_stats': {...}}
                extracted = match_result.get('extracted_fields', {})
                result['terms_found'] = list(extracted.keys())
                
                # Try to get RFP ID from extracted fields
                if 'Bid Number' in extracted:
                    result['rfp_id'] = extracted['Bid Number'].get('value') if isinstance(extracted['Bid Number'], dict) else extracted['Bid Number']
                elif 'RFP Number' in extracted:
                    result['rfp_id'] = extracted['RFP Number'].get('value') if isinstance(extracted['RFP Number'], dict) else extracted['RFP Number']
                
                # Try to get title
                if 'BOQ Title' in extracted:
                    result['title'] = extracted['BOQ Title'].get('value') if isinstance(extracted['BOQ Title'], dict) else extracted['BOQ Title']
                
                result['extracted_fields'] = extracted
            except Exception as e:
                logger.warning(f"Terms matcher error: {e}")
        
        # Use spec matcher to parse requirements
        if self.spec_matcher:
            try:
                requirements = self.spec_matcher.parse_rfp_requirements(text)
                result['requirements'] = requirements
            except Exception as e:
                logger.warning(f"Spec parsing error: {e}")
        
        # Extract additional info using patterns
        result.update(self._extract_rfp_metadata(text))
        
        return result
    
    def _extract_rfp_metadata(self, text: str) -> Dict[str, Any]:
        """Extract RFP metadata using patterns"""
        import re
        
        metadata = {}
        
        # RFP ID patterns
        rfp_patterns = [
            r'(?:rfp|rfq|tender|bid)\s*(?:no|number|id|ref)?\s*[:\-]?\s*([A-Z0-9\-/]+)',
            r'reference\s*[:\-]?\s*([A-Z0-9\-/]+)',
        ]
        for pattern in rfp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['rfp_id'] = match.group(1)
                break
        
        # Due date patterns
        date_patterns = [
            r'(?:due|submission|deadline)\s*(?:date)?[:\-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(?:by|before)\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['due_date'] = match.group(1)
                break
        
        # Standards
        standard_patterns = [
            r'\b(IS\s*\d+)\b',
            r'\b(IEC\s*\d+)\b',
            r'\b(BS\s*\d+)\b',
            r'\b(ASTM\s*[A-Z]?\d+)\b',
        ]
        standards = set()
        for pattern in standard_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            standards.update([m.upper().replace(' ', '') for m in matches])
        metadata['standards'] = list(standards)
        
        # Tests required
        test_keywords = [
            'routine test', 'type test', 'acceptance test', 'special test',
            'hi-pot test', 'insulation test', 'conductor resistance',
            'voltage test', 'flame test', 'fire test'
        ]
        tests_found = []
        text_lower = text.lower()
        for test in test_keywords:
            if test in text_lower:
                tests_found.append(test.title())
        metadata['tests_required'] = tests_found
        
        return metadata
    
    def _extract_form_fields(self, text: str) -> Dict[str, Any]:
        """Extract fillable form fields from RFP"""
        import re
        
        form_fields = {
            'fields': [],
            'tables_detected': False,
            'boq_detected': False
        }
        
        # Common form field patterns
        field_patterns = [
            # "Field: ________" or "Field: _____"
            (r'([A-Za-z\s]+)\s*:\s*_{3,}', 'text_field'),
            # "Field: [ ]" checkbox
            (r'([A-Za-z\s]+)\s*:\s*\[\s*\]', 'checkbox'),
            # "1. ________" numbered blanks
            (r'(\d+)\.\s*_{3,}', 'numbered_field'),
            # Table headers like "Sl.No | Description | Qty | Unit | Rate"
            (r'(?:sl\.?\s*no|sr\.?\s*no|item)\s*\|', 'table_header'),
        ]
        
        for pattern, field_type in field_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                form_fields['fields'].append({
                    'label': match.strip() if isinstance(match, str) else str(match),
                    'type': field_type,
                    'value': None
                })
        
        # Detect BOQ (Bill of Quantities)
        boq_keywords = ['bill of quantities', 'boq', 'schedule of quantities', 'price schedule']
        if any(kw in text.lower() for kw in boq_keywords):
            form_fields['boq_detected'] = True
        
        # Detect tables
        if '|' in text or '\t' in text or form_fields['boq_detected']:
            form_fields['tables_detected'] = True
        
        return form_fields
    
    def _match_specifications(self, requirements: List[Dict]) -> Dict[str, Any]:
        """Match requirements against OEM products"""
        result = {
            'matched_requirements': [],
            'total_requirements': len(requirements),
            'match_summary': {}
        }
        
        if not SPEC_COMPARER_AVAILABLE or not self.spec_matcher:
            logger.warning("Spec comparer not available")
            return result
        
        for i, req in enumerate(requirements):
            try:
                # Find top 3 matching products
                matches = self.spec_matcher.find_matching_products(req, top_n=3)
                
                req_result = {
                    'requirement_id': i + 1,
                    'original_requirement': req,
                    'top_3_matches': matches,
                    'best_match_score': matches[0]['match_score'] if matches else 0,
                    'recommended_product': matches[0] if matches else None
                }
                result['matched_requirements'].append(req_result)
                
            except Exception as e:
                logger.error(f"Error matching requirement {i+1}: {e}")
                result['matched_requirements'].append({
                    'requirement_id': i + 1,
                    'original_requirement': req,
                    'top_3_matches': [],
                    'error': str(e)
                })
        
        # Summary
        total_matched = sum(1 for r in result['matched_requirements'] if r.get('top_3_matches'))
        avg_score = sum(r.get('best_match_score', 0) for r in result['matched_requirements']) / max(len(requirements), 1)
        
        result['match_summary'] = {
            'total_requirements': len(requirements),
            'requirements_matched': total_matched,
            'average_match_score': round(avg_score, 1),
            'match_rate': round(total_matched / max(len(requirements), 1) * 100, 1)
        }
        
        return result
    
    def _calculate_pricing(self, matched_products: Dict, rfp_data: Dict) -> Dict[str, Any]:
        """Calculate pricing for matched products"""
        pricing = {
            'line_items': [],
            'subtotal': 0,
            'tax_amount': 0,
            'testing_costs': 0,
            'total': 0,
            'currency': 'INR'
        }
        
        for match in matched_products.get('matched_requirements', []):
            product = match.get('recommended_product')
            if not product:
                continue
            
            req = match.get('original_requirement', {})
            quantity = req.get('quantity', 1000)  # Default 1000 meters
            unit_price = product.get('price_per_meter', 0) or 0
            
            line_total = quantity * unit_price
            
            # Calculate with tax
            pricing_result = self.price_calculator.calculate_item_price(
                unit_price=unit_price,
                quantity=quantity,
                tax_rate=18.0  # GST
            )
            
            line_item = {
                'requirement_id': match.get('requirement_id'),
                'product_code': product.get('product_code'),
                'product_name': product.get('product_name'),
                'oem': product.get('oem'),
                'match_score': product.get('match_score'),
                'quantity': quantity,
                'unit': 'Meters',
                'unit_price': unit_price,
                'line_total': line_total,
                'tax_amount': pricing_result.get('tax_amount', 0),
                'final_total': pricing_result.get('total', line_total)
            }
            pricing['line_items'].append(line_item)
            pricing['subtotal'] += line_total
            pricing['tax_amount'] += pricing_result.get('tax_amount', 0)
        
        # Calculate testing costs if spec calculator available
        if self.spec_calculator and rfp_data.get('tests_required'):
            for req_match in matched_products.get('matched_requirements', []):
                product = req_match.get('recommended_product')
                if product:
                    try:
                        test_costs = self.spec_calculator.calculate_testing_costs(
                            cable_size=product.get('conductor_size', 4),
                            voltage_class='LT',
                            quantity_meters=1000
                        )
                        pricing['testing_costs'] += test_costs.get('costs', {}).get('total_testing_cost_INR', 0)
                    except:
                        pass
        
        pricing['total'] = pricing['subtotal'] + pricing['tax_amount'] + pricing['testing_costs']
        
        return pricing
    
    def _process_with_agents(self, rfp_data: Dict, matched_products: Dict) -> Dict[str, Any]:
        """
        Process RFP through the multi-agent architecture
        
        Agent Flow (per specification):
        1. Master Agent: Prepares contextual summaries for Technical and Pricing agents
        2. Sales Agent: Identifies and selects RFP (already done - PDF uploaded)
        3. Technical Agent: Analyzes products, recommends top 3 OEMs with spec match %
        4. Pricing Agent: Assigns prices from tables, calculates costs
        5. Master Agent: Consolidates overall response
        """
        if not self.master_agent:
            return {'available': False}
        
        try:
            # Start conversation through Master Agent
            conversation_id = self.master_agent.start_conversation({
                'rfp_id': rfp_data.get('rfp_id', 'RFP_UNKNOWN'),
                'source': 'rfp_workflow',
                'has_matched_products': len(matched_products.get('matched_requirements', [])) > 0
            })
            
            # Prepare RFP summary from extracted data
            rfp_summary = self._create_agent_rfp_summary(rfp_data, matched_products)
            
            # Receive the RFP as if from Sales Agent
            self.master_agent.receive_sales_response(rfp_summary)
            
            # ================================================================
            # STAGE 1: Master prepares contextual summaries
            # ================================================================
            # Technical summary: products, specifications, standards
            tech_summary = self.master_agent.prepare_technical_summary(self.master_agent.current_rfp)
            
            # Pricing summary: tests, acceptance criteria, expected outputs
            pricing_summary = self.master_agent.prepare_pricing_summary(self.master_agent.current_rfp)
            
            # ================================================================
            # STAGE 2: Technical Agent processes and recommends
            # ================================================================
            tech_response = self._run_technical_agent(rfp_data, matched_products)
            self.master_agent.receive_technical_response(tech_response)
            
            # ================================================================
            # STAGE 3: Pricing Agent calculates costs
            # ================================================================
            pricing_response = self._run_pricing_agent(
                rfp_data, 
                matched_products,
                tech_response
            )
            self.master_agent.receive_pricing_response(pricing_response)
            
            # ================================================================
            # STAGE 4: Master Agent consolidates response
            # ================================================================
            consolidated = self.master_agent.consolidate_response()
            
            # End conversation
            self.master_agent.end_conversation(conversation_id, 'completed')
            
            return {
                'available': True,
                'conversation_id': conversation_id,
                'scope_of_supply': consolidated.scope_of_supply,
                'oem_recommendations': consolidated.oem_recommendations,
                'test_costs': consolidated.test_costs,
                'total_material_cost': consolidated.total_material_cost,
                'total_services_cost': consolidated.total_services_cost,
                'grand_total': consolidated.grand_total,
                'overall_spec_match': consolidated.overall_spec_match,
                'recommendation': consolidated.recommendation,
                'compliance_checklist': consolidated.compliance_checklist
            }
            
        except Exception as e:
            logger.error(f"Agent processing error: {e}")
            return {'available': True, 'error': str(e)}
    
    def _create_agent_rfp_summary(self, rfp_data: Dict, matched_products: Dict) -> Dict:
        """Create RFP summary in format expected by agents"""
        products_in_scope = []
        for req in rfp_data.get('requirements', []):
            product = {
                'name': req.get('original_text', req.get('product_type', 'Unknown Product')),
                'specifications': {
                    'conductor_material': req.get('conductor_material', 'copper'),
                    'conductor_type': req.get('conductor_type', 'stranded'),
                    'insulation_type': req.get('insulation_type', 'PVC'),
                    'cross_section_sqmm': req.get('conductor_size', 2.5),
                    'rated_voltage': req.get('voltage_grade', '1100V'),
                    'number_of_cores': req.get('cores', 1),
                },
                'quantity': req.get('quantity', 1000),
                'unit': 'Meters'
            }
            products_in_scope.append(product)
        
        return {
            'rfp_id': rfp_data.get('rfp_id', 'RFP_UNKNOWN'),
            'title': rfp_data.get('title', 'Electrical Wires and Cables Supply'),
            'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'issuing_authority': rfp_data.get('issuing_authority', 'Government Authority'),
            'estimated_value': rfp_data.get('estimated_value', 5000000),
            'products': products_in_scope,
            'technical_requirements': rfp_data.get('standards', []),
            'tests_required': rfp_data.get('tests_required', [
                'Conductor Resistance Test', 
                'Insulation Resistance Test',
                'High Voltage Test',
                'Flame Retardant Test'
            ]),
            'acceptance_criteria': rfp_data.get('acceptance_criteria', [
                'Compliance with IS standards',
                'All tests passed',
                'Complete documentation'
            ]),
            'submission_requirements': {},
            'source_document': rfp_data.get('source_document', '')
        }
    
    def _run_technical_agent(self, rfp_data: Dict, matched_products: Dict) -> Dict:
        """
        Run Technical Agent analysis
        
        Technical Agent responsibilities:
        - Summarize products in scope of supply
        - Recommend top 3 OEM products with spec match %
        - Prepare comparison table (RFP spec vs OEM 1, 2, 3)
        - Select best matching OEM product per item
        - Send final table to Master and Pricing agents
        """
        recommendations = []
        comparison_table = []
        
        for match in matched_products.get('matched_requirements', []):
            req = match.get('original_requirement', {})
            top_3 = match.get('top_3_matches', [])
            
            if not top_3:
                continue
            
            # Build recommendation entry
            best_match = top_3[0] if top_3 else {}
            rec = {
                'rfp_product': req.get('original_text', 'Unknown'),
                'quantity': req.get('quantity', 1000),
                'unit': 'Meters',
                'selected_sku': best_match.get('product_code', ''),
                'product_name': best_match.get('product_name', ''),
                'manufacturer': best_match.get('oem', ''),
                'spec_match_percent': best_match.get('match_score', 0),
                'top_3_options': [
                    {
                        'rank': i + 1,
                        'sku': p.get('product_code', ''),
                        'product_name': p.get('product_name', ''),
                        'oem': p.get('oem', ''),
                        'spec_match_percent': p.get('match_score', 0),
                        'price_per_unit': p.get('price_per_meter', 0)
                    }
                    for i, p in enumerate(top_3[:3])
                ]
            }
            recommendations.append(rec)
            
            # Build comparison table entry
            comparison = {
                'rfp_product': req.get('original_text', 'Unknown'),
                'specs': []
            }
            
            # Get spec parameters
            spec_params = [
                ('Conductor Material', 'conductor_material'),
                ('Conductor Size', 'conductor_size'),
                ('Number of Cores', 'cores'),
                ('Insulation Type', 'insulation_type'),
                ('Voltage Rating', 'voltage_grade'),
                ('Standard', 'standard')
            ]
            
            for param_name, param_key in spec_params:
                spec_row = {
                    'parameter': param_name,
                    'rfp_requirement': req.get(param_key, '-'),
                    'oem_1': top_3[0].get(param_key, '-') if len(top_3) > 0 else '-',
                    'oem_2': top_3[1].get(param_key, '-') if len(top_3) > 1 else '-',
                    'oem_3': top_3[2].get(param_key, '-') if len(top_3) > 2 else '-'
                }
                comparison['specs'].append(spec_row)
            
            comparison_table.append(comparison)
        
        # Calculate overall compliance
        total_match = sum(r['spec_match_percent'] for r in recommendations) if recommendations else 0
        avg_match = total_match / len(recommendations) if recommendations else 0
        
        return {
            'recommendations': recommendations,
            'comparison_table': comparison_table,
            'compliance_summary': {
                'products_analyzed': len(recommendations),
                'average_spec_match': round(avg_match, 2),
                'fully_compliant': sum(1 for r in recommendations if r['spec_match_percent'] >= 90),
                'partially_compliant': sum(1 for r in recommendations if 60 <= r['spec_match_percent'] < 90),
                'non_compliant': sum(1 for r in recommendations if r['spec_match_percent'] < 60)
            }
        }
    
    def _run_pricing_agent(self, rfp_data: Dict, matched_products: Dict, 
                          tech_response: Dict) -> Dict:
        """
        Run Pricing Agent calculations
        
        Pricing Agent responsibilities:
        - Receive test summary from Master Agent
        - Receive product recommendations from Technical Agent
        - Assign unit prices from pricing table
        - Assign test costs from services price table
        - Consolidate total material and services costs
        - Send consolidated pricing to Master Agent
        """
        product_prices = []
        test_costs = []
        total_material_cost = 0
        total_services_cost = 0
        
        recommendations = tech_response.get('recommendations', [])
        
        # Calculate product prices
        for rec in recommendations:
            quantity = rec.get('quantity', 1000)
            
            # Get price from top option
            top_options = rec.get('top_3_options', [])
            if top_options:
                unit_price = top_options[0].get('price_per_unit', 0)
            else:
                unit_price = 50  # Default fallback price per meter
            
            total_price = unit_price * quantity
            
            # Apply bulk discount (for large quantities)
            discount_percent = 0
            if quantity >= 10000:
                discount_percent = 10
            elif quantity >= 5000:
                discount_percent = 5
            elif quantity >= 1000:
                discount_percent = 2
            
            discounted_price = total_price * (1 - discount_percent / 100)
            
            price_entry = {
                'sku': rec.get('selected_sku', ''),
                'product_name': rec.get('product_name', ''),
                'quantity': quantity,
                'unit_price': unit_price,
                'discount_percent': discount_percent,
                'discounted_unit_price': unit_price * (1 - discount_percent / 100),
                'total_price': round(discounted_price, 2)
            }
            product_prices.append(price_entry)
            total_material_cost += discounted_price
        
        # Calculate test costs from services price table
        tests_required = rfp_data.get('tests_required', [
            'Conductor Resistance Test',
            'Insulation Resistance Test', 
            'High Voltage Test',
            'Flame Retardant Test'
        ])
        
        # Test pricing table (dummy prices per specification)
        test_price_table = {
            'Conductor Resistance Test': {'price': 2500, 'type': 'ROUTINE_TEST'},
            'Insulation Resistance Test': {'price': 3000, 'type': 'ROUTINE_TEST'},
            'High Voltage Test': {'price': 5000, 'type': 'TYPE_TEST'},
            'Flame Retardant Test': {'price': 8000, 'type': 'TYPE_TEST'},
            'Oxygen Index Test': {'price': 6000, 'type': 'TYPE_TEST'},
            'Smoke Density Test': {'price': 7500, 'type': 'TYPE_TEST'},
            'Acid Gas Emission Test': {'price': 4500, 'type': 'TYPE_TEST'},
            'Halogen Content Test': {'price': 4000, 'type': 'TYPE_TEST'},
            'Tensile Strength Test': {'price': 3500, 'type': 'ACCEPTANCE_TEST'},
            'Hot Set Test': {'price': 4000, 'type': 'TYPE_TEST'},
            'Cold Bend Test': {'price': 3000, 'type': 'TYPE_TEST'},
            'Thermal Stability Test': {'price': 5500, 'type': 'TYPE_TEST'}
        }
        
        for test_name in tests_required:
            # Find matching test in price table
            test_info = None
            for table_test, info in test_price_table.items():
                if test_name.lower() in table_test.lower() or table_test.lower() in test_name.lower():
                    test_info = {'name': table_test, **info}
                    break
            
            if not test_info:
                # Default test cost
                test_info = {'name': test_name, 'price': 5000, 'type': 'TYPE_TEST'}
            
            test_costs.append({
                'test_name': test_info['name'],
                'test_type': test_info['type'],
                'unit_price': test_info['price'],
                'quantity': 1,
                'total_cost': test_info['price']
            })
            total_services_cost += test_info['price']
        
        # Calculate taxes
        gst_rate = 18  # 18% GST
        material_gst = total_material_cost * (gst_rate / 100)
        services_gst = total_services_cost * (gst_rate / 100)
        
        taxes = {
            'material_gst': round(material_gst, 2),
            'services_gst': round(services_gst, 2),
            'total_tax': round(material_gst + services_gst, 2),
            'gst_rate_percent': gst_rate
        }
        
        grand_total = total_material_cost + total_services_cost + taxes['total_tax']
        
        return {
            'product_prices': product_prices,
            'test_costs': test_costs,
            'total_material_cost': round(total_material_cost, 2),
            'total_services_cost': round(total_services_cost, 2),
            'taxes': taxes,
            'grand_total': round(grand_total, 2),
            'pricing_notes': [
                f'Material prices include bulk discount where applicable',
                f'Test costs based on standard services price table',
                f'GST @ {gst_rate}% applied on material and services',
                f'Prices valid for 30 days from quotation date'
            ]
        }
    
    def _generate_bid(self, workflow_id: str, rfp_data: Dict, matched_products: Dict,
                     pricing: Dict, vendor_info: Dict, form_fields: Dict) -> Dict[str, Any]:
        """Generate bid document with auto-filled content"""
        
        bid_id = f"BID_{workflow_id}"
        
        # Prepare bid data
        bid_data = {
            'bid_id': bid_id,
            'rfp_id': rfp_data.get('rfp_id', 'N/A'),
            'vendor_id': vendor_info.get('vendor_id', 'VENDOR_001'),
            'vendor_name': vendor_info.get('vendor_name', 'Default Vendor'),
            'vendor_address': vendor_info.get('address', ''),
            'vendor_contact': vendor_info.get('contact', ''),
            'issued_date': datetime.now().isoformat(),
            'valid_until_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'version': 1,
            'status': 'DRAFT',
            
            # Products from matching
            'items': [],
            
            # Pricing
            'subtotal': pricing.get('subtotal', 0),
            'tax_amount': pricing.get('tax_amount', 0),
            'testing_costs': pricing.get('testing_costs', 0),
            'total_cost': pricing.get('total', 0),
            
            # Terms
            'delivery_timeline': '15-30 days from order confirmation',
            'payment_terms': 'Net 30 days',
            'warranty': '12 months from delivery',
            
            # Compliance
            'standards_compliance': rfp_data.get('standards', []),
            'tests_included': rfp_data.get('tests_required', []),
            
            # Auto-filled form fields
            'form_responses': self._auto_fill_forms(form_fields, vendor_info, pricing)
        }
        
        # Add items from matched products
        for i, line_item in enumerate(pricing.get('line_items', [])):
            bid_data['items'].append({
                'item_id': f"ITEM_{i+1:03d}",
                'description': line_item.get('product_name', ''),
                'product_id': line_item.get('product_code', ''),
                'oem': line_item.get('oem', ''),
                'match_score': line_item.get('match_score', 0),
                'quantity': line_item.get('quantity', 0),
                'unit': line_item.get('unit', 'Meters'),
                'unit_price': line_item.get('unit_price', 0),
                'total': line_item.get('final_total', 0)
            })
        
        # Generate documents
        output_folder = self.upload_folder / workflow_id
        output_folder.mkdir(exist_ok=True)
        
        result = {
            'bid_id': bid_id,
            'bid_data': bid_data,
            'documents': {}
        }
        
        # Generate PDF
        try:
            pdf_bytes = self.pdf_generator.generate(bid_data)
            pdf_path = output_folder / f"{bid_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            result['documents']['pdf'] = str(pdf_path)
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
        
        # Generate Excel
        try:
            excel_bytes = self.excel_generator.generate(bid_data)
            excel_path = output_folder / f"{bid_id}.xlsx"
            with open(excel_path, 'wb') as f:
                f.write(excel_bytes)
            result['documents']['excel'] = str(excel_path)
        except Exception as e:
            logger.error(f"Excel generation error: {e}")
        
        # Save JSON data
        try:
            json_path = output_folder / f"{bid_id}.json"
            with open(json_path, 'w') as f:
                json.dump(bid_data, f, indent=2, default=str)
            result['documents']['json'] = str(json_path)
        except Exception as e:
            logger.error(f"JSON save error: {e}")
        
        return result
    
    def _auto_fill_forms(self, form_fields: Dict, vendor_info: Dict, pricing: Dict) -> List[Dict]:
        """Auto-fill detected form fields"""
        filled_fields = []
        
        # Common field mappings
        field_mappings = {
            'company': vendor_info.get('vendor_name', ''),
            'vendor': vendor_info.get('vendor_name', ''),
            'name': vendor_info.get('vendor_name', ''),
            'address': vendor_info.get('address', ''),
            'contact': vendor_info.get('contact', ''),
            'phone': vendor_info.get('phone', ''),
            'email': vendor_info.get('email', ''),
            'gstin': vendor_info.get('gstin', ''),
            'pan': vendor_info.get('pan', ''),
            'total': f"₹{pricing.get('total', 0):,.2f}",
            'amount': f"₹{pricing.get('total', 0):,.2f}",
            'date': datetime.now().strftime('%d/%m/%Y'),
            'validity': '30 days',
            'delivery': '15-30 days'
        }
        
        for field in form_fields.get('fields', []):
            label = field.get('label', '').lower().strip()
            
            # Try to match field with known values
            filled_value = None
            for key, value in field_mappings.items():
                if key in label:
                    filled_value = value
                    break
            
            filled_fields.append({
                'label': field.get('label'),
                'type': field.get('type'),
                'auto_filled': filled_value is not None,
                'value': filled_value
            })
        
        return filled_fields
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow"""
        if self.current_workflow.get('workflow_id') == workflow_id:
            return self.current_workflow
        return {'error': 'Workflow not found'}
    
    def list_oem_products(self, filters: Dict = None) -> List[Dict]:
        """List available OEM products with optional filters"""
        if not self.product_db:
            return []
        
        try:
            df = self.product_db.products_df
            if df is None or len(df) == 0:
                return []
            
            # Apply filters
            if filters:
                if filters.get('conductor_size'):
                    df = df[df['Conductor_Size_sqmm'] == filters['conductor_size']]
                if filters.get('cores'):
                    df = df[df['No_of_Cores'] == filters['cores']]
                if filters.get('oem'):
                    df = df[df['OEM'].str.contains(filters['oem'], case=False, na=False)]
            
            # Return as list of dicts
            return df.head(100).to_dict('records')
        except Exception as e:
            logger.error(f"Error listing products: {e}")
            return []


# Singleton instance
_workflow_manager = None

def get_workflow_manager() -> RFPWorkflowManager:
    """Get singleton workflow manager instance"""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = RFPWorkflowManager()
    return _workflow_manager
