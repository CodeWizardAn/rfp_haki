"""
Sales Agent - RFP Scanner and Selector
Identifies, scans, and selects RFPs for response
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import logging
import re

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RFPPriority(Enum):
    """Priority levels for RFPs"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RFPStatus(Enum):
    """Status of RFP in pipeline"""
    IDENTIFIED = "identified"
    SCANNED = "scanned"
    SELECTED = "selected"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


@dataclass
class IdentifiedRFP:
    """RFP identified by Sales Agent"""
    rfp_id: str
    title: str
    source_url: str
    due_date: datetime
    issuing_authority: str
    estimated_value: float
    category: str
    products: List[Dict[str, Any]]
    technical_requirements: List[str]
    tests_required: List[str]
    acceptance_criteria: List[str]
    submission_requirements: Dict[str, Any]
    priority: RFPPriority
    status: RFPStatus
    scanned_date: datetime = field(default_factory=datetime.now)
    source_document: str = ""
    
    def days_until_due(self) -> int:
        """Calculate days until RFP is due"""
        return (self.due_date - datetime.now()).days
    
    def is_within_deadline(self, days: int = 90) -> bool:
        """Check if RFP is due within specified days"""
        return 0 < self.days_until_due() <= days


class SalesAgent:
    """
    Sales Agent - RFP Scanner
    
    Responsibilities:
    - Identifies RFPs due for submission in next 3 months
    - Scans web URLs to summarize RFPs
    - Selects one RFP for response
    - Sends selected RFP to Master Agent
    """
    
    def __init__(self):
        self.agent_id = "SALES_AGENT"
        self.identified_rfps: List[IdentifiedRFP] = []
        self.selected_rfp: Optional[IdentifiedRFP] = None
        self.scan_window_days = 90  # 3 months
        
        # Try to import PDF extraction module (store class reference, not instance)
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'pdf_extraction'))
            # pyrefly: ignore [missing-import]
            from pdf_text_extractor import PDFTextExtractor
            self.PDFTextExtractor = PDFTextExtractor  # Store class, not instance
            self._pdf_extractor_available = True
        except ImportError:
            self.PDFTextExtractor = None
            self._pdf_extractor_available = False
            logger.warning("PDF extractor not available")
        
        logger.info(f"✅ Sales Agent initialized")
    
    def scan_rfp_urls(self, urls: List[str]) -> List[IdentifiedRFP]:
        """
        Scan provided URLs to identify and summarize RFPs
        
        Args:
            urls: List of URLs to scan for RFPs
            
        Returns:
            List of identified RFPs with summaries
        """
        identified = []
        
        for url in urls:
            try:
                rfp = self._extract_rfp_from_url(url)
                if rfp and rfp.is_within_deadline(self.scan_window_days):
                    identified.append(rfp)
                    logger.info(f"📋 Identified RFP: {rfp.rfp_id} - Due: {rfp.due_date.strftime('%Y-%m-%d')}")
            except Exception as e:
                logger.error(f"Error scanning URL {url}: {e}")
        
        self.identified_rfps.extend(identified)
        return identified
    
    def _extract_rfp_from_url(self, url: str) -> Optional[IdentifiedRFP]:
        """Extract RFP information from a URL"""
        # This would integrate with pdf_extraction module
        # For now, create a sample RFP structure
        
        rfp_id = f"RFP_{datetime.now().strftime('%Y%m%d')}_{hash(url) % 10000:04d}"
        
        # Simulate extraction - in production, this would use pdf_extraction
        sample_rfp = IdentifiedRFP(
            rfp_id=rfp_id,
            title=f"Supply of Electrical Wires and Cables",
            source_url=url,
            due_date=datetime.now() + timedelta(days=45),
            issuing_authority="Sample Authority",
            estimated_value=5000000.0,
            category="Electrical Equipment",
            products=[
                {
                    'name': 'PVC Insulated Copper Wire 1.5 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Solid/Stranded',
                        'insulation_type': 'PVC',
                        'cross_section_sqmm': 1.5,
                        'rated_voltage': '1100V',
                        'temperature_rating_celsius': 70,
                        'flame_retardant': True
                    },
                    'quantity': 50000,
                    'unit': 'meters'
                },
                {
                    'name': 'PVC Insulated Copper Wire 2.5 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Solid/Stranded',
                        'insulation_type': 'PVC',
                        'cross_section_sqmm': 2.5,
                        'rated_voltage': '1100V',
                        'temperature_rating_celsius': 70,
                        'flame_retardant': True
                    },
                    'quantity': 30000,
                    'unit': 'meters'
                },
                {
                    'name': 'XLPE Armoured Cable 4C x 16 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Stranded',
                        'insulation_type': 'XLPE',
                        'cross_section_sqmm': 16,
                        'number_of_cores': 4,
                        'armour_type': 'Steel Wire Armoured',
                        'rated_voltage': '1100V',
                        'temperature_rating_celsius': 90,
                        'flame_retardant': True
                    },
                    'quantity': 10000,
                    'unit': 'meters'
                },
                {
                    'name': 'Flexible Cable 3C x 2.5 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Flexible Stranded',
                        'insulation_type': 'PVC',
                        'cross_section_sqmm': 2.5,
                        'number_of_cores': 3,
                        'rated_voltage': '1100V',
                        'temperature_rating_celsius': 70,
                        'flame_retardant': True
                    },
                    'quantity': 5000,
                    'unit': 'meters'
                }
            ],
            technical_requirements=[
                'IS 694:2010 compliance for PVC wires',
                'IS 7098 Part 1 compliance for XLPE cables',
                'Flame retardant properties required',
                'Temperature rating: -10°C to 70°C'
            ],
            tests_required=[
                'Conductor resistance test',
                'Insulation resistance test',
                'High voltage test (3.5 kV for 5 min)',
                'Flame retardancy test (IEC 60332)',
                'Thermal stability test',
                'Tensile strength test'
            ],
            acceptance_criteria=[
                'Type test certificate required',
                'Routine test certificate per batch',
                'Third party inspection certification',
                'BIS certification mandatory'
            ],
            submission_requirements={
                'format': 'PDF',
                'copies': 2,
                'emd_amount': 100000,
                'validity_period': 90
            },
            priority=RFPPriority.HIGH,
            status=RFPStatus.SCANNED,
            source_document=url
        )
        
        return sample_rfp
    
    def scan_rfp_directory(self, directory: str) -> List[IdentifiedRFP]:
        """
        Scan a directory for RFP PDF files
        
        Args:
            directory: Path to directory containing RFP PDFs
            
        Returns:
            List of identified RFPs
        """
        rfp_dir = Path(directory)
        if not rfp_dir.exists():
            logger.warning(f"Directory not found: {directory}")
            return []
        
        identified = []
        pdf_files = list(rfp_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            try:
                rfp = self._extract_rfp_from_pdf(str(pdf_file))
                if rfp and rfp.is_within_deadline(self.scan_window_days):
                    identified.append(rfp)
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
        
        self.identified_rfps.extend(identified)
        return identified
    
    def _extract_rfp_from_pdf(self, pdf_path: str) -> Optional[IdentifiedRFP]:
        """Extract RFP information from a PDF file"""
        if self._pdf_extractor_available and self.PDFTextExtractor:
            # Use pdf_extraction module
            try:
                extractor = self.PDFTextExtractor(pdf_path)  # Create instance with path
                extracted_text = extractor.extract_all_text()
                # Parse extracted text to create RFP
                return self._parse_rfp_text(extracted_text, pdf_path)
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
        
        # Fallback: Create sample RFP from filename
        return self._create_sample_rfp_from_file(pdf_path)
    
    def _parse_rfp_text(self, text: str, source: str) -> Optional[IdentifiedRFP]:
        """Parse extracted text to create RFP structure"""
        # Extract key information using patterns
        due_date_match = re.search(r'due\s*(?:date|by)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text, re.I)
        value_match = re.search(r'(?:estimated|approximate)\s*value[:\s]*(?:Rs\.?|INR)?\s*([\d,]+)', text, re.I)
        
        due_date = datetime.now() + timedelta(days=60)  # Default
        if due_date_match:
            try:
                due_date = datetime.strptime(due_date_match.group(1), '%d-%m-%Y')
            except:
                pass
        
        estimated_value = 1000000.0
        if value_match:
            try:
                estimated_value = float(value_match.group(1).replace(',', ''))
            except:
                pass
        
        return self._create_sample_rfp_from_file(source, due_date, estimated_value)
    
    def _create_sample_rfp_from_file(self, file_path: str, due_date: datetime = None, 
                                      estimated_value: float = None) -> IdentifiedRFP:
        """Create a sample RFP from file information"""
        file_name = Path(file_path).stem
        
        return IdentifiedRFP(
            rfp_id=f"RFP_{file_name}_{datetime.now().strftime('%H%M%S')}",
            title=f"RFP: {file_name.replace('_', ' ').title()}",
            source_url=file_path,
            due_date=due_date or (datetime.now() + timedelta(days=45)),
            issuing_authority="Extracted Authority",
            estimated_value=estimated_value or 2000000.0,
            category="General",
            products=[],
            technical_requirements=[],
            tests_required=[],
            acceptance_criteria=[],
            submission_requirements={},
            priority=RFPPriority.MEDIUM,
            status=RFPStatus.SCANNED,
            source_document=file_path
        )
    
    def get_rfps_due_within(self, days: int = 90) -> List[IdentifiedRFP]:
        """Get all RFPs due within specified days"""
        return [rfp for rfp in self.identified_rfps if rfp.is_within_deadline(days)]
    
    def prioritize_rfps(self) -> List[IdentifiedRFP]:
        """
        Prioritize RFPs based on:
        - Days until due (urgency)
        - Estimated value
        - Priority level
        """
        def priority_score(rfp: IdentifiedRFP) -> float:
            urgency_score = max(0, 100 - rfp.days_until_due())  # Higher for sooner deadlines
            value_score = min(100, rfp.estimated_value / 100000)  # Scale value
            priority_multiplier = {'high': 1.5, 'medium': 1.0, 'low': 0.5}
            
            return (urgency_score * 0.4 + value_score * 0.4) * priority_multiplier.get(rfp.priority.value, 1.0)
        
        return sorted(self.identified_rfps, key=priority_score, reverse=True)
    
    def select_rfp_for_response(self, urls: List[str] = None) -> Dict[str, Any]:
        """
        Select one RFP for response
        
        This is sent to the Master Agent
        """
        # Scan URLs if provided
        if urls:
            self.scan_rfp_urls(urls)
        
        # If no RFPs identified, create a sample one
        if not self.identified_rfps:
            self.identified_rfps.append(self._create_default_sample_rfp())
        
        # Get prioritized list
        prioritized = self.prioritize_rfps()
        
        if not prioritized:
            raise ValueError("No RFPs available for selection")
        
        # Select top priority RFP
        self.selected_rfp = prioritized[0]
        self.selected_rfp.status = RFPStatus.SELECTED
        
        logger.info(f"✅ Selected RFP: {self.selected_rfp.rfp_id} - {self.selected_rfp.title}")
        
        # Return in format expected by Master Agent
        return {
            'rfp_id': self.selected_rfp.rfp_id,
            'title': self.selected_rfp.title,
            'due_date': self.selected_rfp.due_date.isoformat(),
            'issuing_authority': self.selected_rfp.issuing_authority,
            'estimated_value': self.selected_rfp.estimated_value,
            'products': self.selected_rfp.products,
            'technical_requirements': self.selected_rfp.technical_requirements,
            'tests_required': self.selected_rfp.tests_required,
            'acceptance_criteria': self.selected_rfp.acceptance_criteria,
            'submission_requirements': self.selected_rfp.submission_requirements,
            'source_document': self.selected_rfp.source_document,
            'days_until_due': self.selected_rfp.days_until_due()
        }
    
    def _create_default_sample_rfp(self) -> IdentifiedRFP:
        """
        Create a default sample RFP for testing
        
        IMPORTANT: Specification keys MUST match OEM product specification keys
        for proper spec matching. See database/db_products/oem_products.json
        """
        return IdentifiedRFP(
            rfp_id=f"RFP_SAMPLE_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title="Supply of Wires and Cables for Power Distribution Project",
            source_url="https://sample-rfp-portal.gov.in/rfp/12345",
            due_date=datetime.now() + timedelta(days=45),
            issuing_authority="State Electricity Board",
            estimated_value=7500000.0,
            category="Electrical Equipment - Wires & Cables",
            products=[
                {
                    'name': 'PVC Insulated Copper Wire 1.5 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Solid/Stranded',
                        'insulation_type': 'PVC',
                        'cross_section_sqmm': 1.5,
                        'rated_voltage': '1100V',
                        'current_rating_amps': 14,
                        'temperature_rating_celsius': 70,
                        'flame_retardant': True
                    },
                    'spec_attributions': {
                        'conductor_material': {
                            'page_number': 8,
                            'clause_ref': 'Sec. III, Cl. 4.1.1',
                            'source_snippet': 'Conductor shall be high conductivity electrolytic grade annealed copper conforming to IS 8130 Class 2.',
                            'confidence_score': 0.99
                        },
                        'conductor_type': {
                            'page_number': 8,
                            'clause_ref': 'Sec. III, Cl. 4.1.2',
                            'source_snippet': 'Conductor construction shall be solid or stranded suitable for fixed installation.',
                            'confidence_score': 0.97
                        },
                        'insulation_type': {
                            'page_number': 9,
                            'clause_ref': 'Sec. III, Cl. 4.2',
                            'source_snippet': 'Insulation shall be PVC Type A compound conforming to IS 5831 with fire retardant properties.',
                            'confidence_score': 0.98
                        },
                        'cross_section_sqmm': {
                            'page_number': 6,
                            'clause_ref': 'BoQ Item 1',
                            'source_snippet': 'Nominal cross-sectional area: 1.5 sq mm single core insulated cable.',
                            'confidence_score': 1.0
                        },
                        'rated_voltage': {
                            'page_number': 8,
                            'clause_ref': 'Sec. III, Cl. 4.0',
                            'source_snippet': 'Cables shall be suitable for continuous operation at 1100V AC nominal system voltage.',
                            'confidence_score': 0.99
                        },
                        'current_rating_amps': {
                            'page_number': 11,
                            'clause_ref': 'Tech Spec Annex A',
                            'source_snippet': 'Current rating in conduit/casing shall be at least 14 Amperes at 40°C ambient.',
                            'confidence_score': 0.94
                        },
                        'temperature_rating_celsius': {
                            'page_number': 9,
                            'clause_ref': 'Sec. III, Cl. 4.3',
                            'source_snippet': 'Continuous operating conductor temperature limit: 70°C.',
                            'confidence_score': 0.96
                        },
                        'flame_retardant': {
                            'page_number': 14,
                            'clause_ref': 'Sec. IV, Cl. 2.1',
                            'source_snippet': 'Must pass flammability test on single cable in accordance with IS 10810 (Part 61).',
                            'confidence_score': 0.98
                        }
                    },
                    'spec_constraints': {
                        'conductor_material': 'hard',
                        'rated_voltage': 'hard',
                        'insulation_type': 'hard',
                        'cross_section_sqmm': 'hard',
                        'current_rating_amps': 'directional_min',
                        'temperature_rating_celsius': 'directional_min',
                        'flame_retardant': 'hard'
                    },
                    'quantity': 50000,
                    'unit': 'meters'
                },
                {
                    'name': 'PVC Insulated Copper Wire 2.5 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Solid/Stranded',
                        'insulation_type': 'PVC',
                        'cross_section_sqmm': 2.5,
                        'rated_voltage': '1100V',
                        'current_rating_amps': 18,
                        'temperature_rating_celsius': 70,
                        'flame_retardant': True
                    },
                    'spec_attributions': {
                        'conductor_material': {
                            'page_number': 8,
                            'clause_ref': 'Sec. III, Cl. 4.1.1',
                            'source_snippet': 'High conductivity electrolytic copper conductor annealed as per IS 8130.',
                            'confidence_score': 0.99
                        },
                        'insulation_type': {
                            'page_number': 9,
                            'clause_ref': 'Sec. III, Cl. 4.2',
                            'source_snippet': 'PVC Type A insulation with flame retardant characteristics.',
                            'confidence_score': 0.98
                        },
                        'cross_section_sqmm': {
                            'page_number': 6,
                            'clause_ref': 'BoQ Item 2',
                            'source_snippet': 'Nominal cross-sectional area: 2.5 sq mm single core.',
                            'confidence_score': 1.0
                        },
                        'rated_voltage': {
                            'page_number': 8,
                            'clause_ref': 'Sec. III, Cl. 4.0',
                            'source_snippet': 'Voltage rating: 1100V AC grade.',
                            'confidence_score': 0.99
                        },
                        'current_rating_amps': {
                            'page_number': 11,
                            'clause_ref': 'Tech Spec Annex A',
                            'source_snippet': 'Current rating shall not be less than 18 Amps.',
                            'confidence_score': 0.95
                        }
                    },
                    'spec_constraints': {
                        'conductor_material': 'hard',
                        'rated_voltage': 'hard',
                        'insulation_type': 'hard',
                        'cross_section_sqmm': 'hard',
                        'current_rating_amps': 'directional_min'
                    },
                    'quantity': 30000,
                    'unit': 'meters'
                },
                {
                    'name': 'XLPE Armoured Cable 4C x 16 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Stranded',
                        'insulation_type': 'XLPE',
                        'cross_section_sqmm': 16,
                        'number_of_cores': 4,
                        'armour_type': 'Steel Wire Armoured',
                        'outer_sheath': 'PVC',
                        'rated_voltage': '1100V',
                        'current_rating_amps': 68,
                        'temperature_rating_celsius': 90,
                        'flame_retardant': True
                    },
                    'spec_attributions': {
                        'conductor_material': {
                            'page_number': 15,
                            'clause_ref': 'Sec. III, Cl. 5.1',
                            'source_snippet': 'Plain copper conductor, compacted circular stranded as per IS 8130 Class 2.',
                            'confidence_score': 0.99
                        },
                        'insulation_type': {
                            'page_number': 15,
                            'clause_ref': 'Sec. III, Cl. 5.2',
                            'source_snippet': 'Insulation shall be cross-linked polyethylene (XLPE) as per IS 7098 (Part 1).',
                            'confidence_score': 0.99
                        },
                        'armour_type': {
                            'page_number': 16,
                            'clause_ref': 'Sec. III, Cl. 5.4',
                            'source_snippet': 'Armour shall be single layer of galvanised steel wire conforming to IS 3975.',
                            'confidence_score': 0.97
                        },
                        'rated_voltage': {
                            'page_number': 15,
                            'clause_ref': 'Sec. III, Cl. 5.0',
                            'source_snippet': 'Working voltage grade: 1100 Volts (1.1 kV).',
                            'confidence_score': 1.0
                        },
                        'current_rating_amps': {
                            'page_number': 17,
                            'clause_ref': 'Tech Spec Annex B',
                            'source_snippet': 'Continuous current rating in ground at 30°C: not less than 68 Amperes.',
                            'confidence_score': 0.95
                        },
                        'temperature_rating_celsius': {
                            'page_number': 15,
                            'clause_ref': 'Sec. III, Cl. 5.2.1',
                            'source_snippet': 'Maximum continuous conductor operating temperature: 90°C.',
                            'confidence_score': 0.98
                        }
                    },
                    'spec_constraints': {
                        'conductor_material': 'hard',
                        'insulation_type': 'hard',
                        'armour_type': 'hard',
                        'number_of_cores': 'hard',
                        'rated_voltage': 'hard',
                        'current_rating_amps': 'directional_min',
                        'temperature_rating_celsius': 'directional_min'
                    },
                    'quantity': 10000,
                    'unit': 'meters'
                },
                {
                    'name': 'Flexible Cable 3C x 2.5 sq mm',
                    'specifications': {
                        'conductor_material': 'Copper',
                        'conductor_type': 'Flexible Stranded',
                        'insulation_type': 'PVC',
                        'cross_section_sqmm': 2.5,
                        'number_of_cores': 3,
                        'rated_voltage': '1100V',
                        'temperature_rating_celsius': 70,
                        'flame_retardant': True
                    },
                    'spec_attributions': {
                        'conductor_material': {
                            'page_number': 22,
                            'clause_ref': 'Sec. III, Cl. 7.1',
                            'source_snippet': 'High conductivity annealed copper Class 5 flexible conductor as per IS 8130.',
                            'confidence_score': 0.99
                        },
                        'number_of_cores': {
                            'page_number': 7,
                            'clause_ref': 'BoQ Item 4',
                            'source_snippet': '3 Core flexible copper cable for industrial machinery power cord.',
                            'confidence_score': 1.0
                        },
                        'rated_voltage': {
                            'page_number': 22,
                            'clause_ref': 'Sec. III, Cl. 7.0',
                            'source_snippet': 'Rated voltage: 1100V AC nominal.',
                            'confidence_score': 0.98
                        }
                    },
                    'spec_constraints': {
                        'conductor_material': 'hard',
                        'number_of_cores': 'hard',
                        'rated_voltage': 'hard',
                        'insulation_type': 'hard'
                    },
                    'quantity': 5000,
                    'unit': 'meters'
                }
            ],
            technical_requirements=[
                'IS 694:2010 compliance for PVC insulated cables',
                'IS 7098 Part 1 compliance for XLPE power cables',
                'Flame retardant low smoke (FRLS) properties as per IEC 60332',
                'Operating temperature range: -10°C to 70°C',
                'Conductor resistance as per IS 8130',
                'Minimum insulation thickness compliance',
                'BIS certification mandatory (ISI Mark)'
            ],
            tests_required=[
                'Conductor Resistance Test (IS 8130)',
                'Insulation Resistance Test (Min 100 MΩ-km)',
                'High Voltage Test (3.5 kV AC for 5 min)',
                'Spark Test during manufacturing',
                'Flame Retardancy Test (IEC 60332-1)',
                'Smoke Density Test (IEC 61034)',
                'Hot Set Test for XLPE',
                'Tensile Strength Test',
                'Elongation at Break Test',
                'Thermal Stability Test'
            ],
            acceptance_criteria=[
                'Type Test Certificate from NABL accredited lab',
                'Routine Test Certificate for each batch',
                'Third Party Inspection by approved agency',
                'BIS License copy for each product',
                'Manufacturer Authorization Certificate',
                'ISO 9001:2015 certification'
            ],
            submission_requirements={
                'format': 'PDF with digital signature',
                'hard_copies': 2,
                'emd_amount': 150000,
                'bid_validity_days': 120,
                'pre_bid_meeting': '2026-02-15',
                'site_visit_required': True
            },
            priority=RFPPriority.HIGH,
            status=RFPStatus.SCANNED,
            source_document="sample_rfp_document.pdf"
        )
    
    def get_rfp_summary(self, rfp_id: str) -> Dict[str, Any]:
        """Get summary of a specific RFP"""
        rfp = next((r for r in self.identified_rfps if r.rfp_id == rfp_id), None)
        if not rfp:
            return {}
        
        return {
            'rfp_id': rfp.rfp_id,
            'title': rfp.title,
            'due_date': rfp.due_date.strftime('%Y-%m-%d'),
            'days_remaining': rfp.days_until_due(),
            'estimated_value': f"₹{rfp.estimated_value:,.2f}",
            'products_count': len(rfp.products),
            'tests_count': len(rfp.tests_required),
            'priority': rfp.priority.value,
            'status': rfp.status.value
        }
    
    def export_identified_rfps(self) -> str:
        """Export all identified RFPs to JSON"""
        rfps_data = []
        for rfp in self.identified_rfps:
            rfps_data.append({
                'rfp_id': rfp.rfp_id,
                'title': rfp.title,
                'due_date': rfp.due_date.isoformat(),
                'days_until_due': rfp.days_until_due(),
                'estimated_value': rfp.estimated_value,
                'products_count': len(rfp.products),
                'priority': rfp.priority.value,
                'status': rfp.status.value
            })
        
        return json.dumps(rfps_data, indent=2)


# Example usage
if __name__ == "__main__":
    sales = SalesAgent()
    
    # Select an RFP (will create sample if none found)
    selected = sales.select_rfp_for_response()
    print(f"\nSelected RFP: {selected['rfp_id']}")
    print(f"Title: {selected['title']}")
    print(f"Due in: {selected['days_until_due']} days")
    print(f"Products: {len(selected['products'])}")
