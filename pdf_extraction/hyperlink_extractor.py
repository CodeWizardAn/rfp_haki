"""
PDF Hyperlink Extractor - Extracts and processes hyperlinks from PDFs
Handles linked documents like BOQ (Excel/CSV), Specifications (PDF), etc.
"""

import os
import re
import json
import logging
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, urljoin, unquote
from dataclasses import dataclass, field, asdict
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not installed - Excel/CSV parsing will be limited")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed - URL downloading will be disabled")

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not installed - Excel parsing may be limited")


@dataclass
class LinkedDocument:
    """Represents a linked document found in a PDF"""
    name: str
    url: str
    document_type: str
    page_number: int
    link_text: str = ""
    rect: Optional[Tuple[float, float, float, float]] = None
    file_type: str = ""
    is_downloaded: bool = False
    local_path: str = ""
    content_summary: str = ""
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BOQItem:
    """Represents a single BOQ line item"""
    sr_no: str
    description: str
    specification: str = ""
    unit: str = ""
    quantity: float = 0
    unit_rate: float = 0
    total_amount: float = 0
    gst_rate: float = 0
    gst_amount: float = 0
    total_with_gst: float = 0
    hsn_code: str = ""
    make_model: str = ""
    delivery_period: str = ""
    additional_fields: Dict[str, Any] = field(default_factory=dict)


class PDFHyperlinkExtractor:
    """
    Extracts hyperlinks from PDF documents and processes linked files
    Handles BOQ documents, specification sheets, and other attachments
    """
    
    # Document type patterns for classification
    DOCUMENT_TYPE_PATTERNS = {
        "boq": [
            r"boq", r"bill\s*of\s*quantit", r"price\s*schedule", r"rate\s*schedule",
            r"quantity\s*schedule", r"item\s*list", r"price\s*bid", r"commercial\s*bid",
            r"financial\s*bid", r"pricing"
        ],
        "specification": [
            r"spec", r"technical\s*specification", r"product\s*specification",
            r"tech\s*spec", r"detailed\s*specification", r"technical\s*requirement",
            r"technical\s*detail"
        ],
        "drawing": [
            r"drawing", r"diagram", r"layout", r"plan", r"design", r"schematic",
            r"blueprint", r"cad"
        ],
        "terms": [
            r"terms", r"condition", r"gtc", r"stc", r"general\s*terms",
            r"special\s*terms", r"contract\s*terms"
        ],
        "annexure": [
            r"annexure", r"appendix", r"annex", r"attachment", r"enclosure"
        ],
        "eligibility": [
            r"eligibility", r"qualification", r"pre[-\s]?qualification",
            r"bidder\s*requirement", r"vendor\s*requirement"
        ],
        "corrigendum": [
            r"corrigendum", r"amendment", r"addendum", r"modification", r"revision"
        ],
        "sample_format": [
            r"format", r"proforma", r"template", r"form", r"declaration\s*format",
            r"undertaking\s*format"
        ]
    }
    
    # File type mappings
    FILE_TYPE_EXTENSIONS = {
        "excel": [".xlsx", ".xls", ".xlsm", ".xlsb"],
        "csv": [".csv", ".tsv"],
        "pdf": [".pdf"],
        "word": [".doc", ".docx", ".rtf"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
        "cad": [".dwg", ".dxf"],
        "archive": [".zip", ".rar", ".7z"]
    }
    
    def __init__(self, base_url: str = None, download_folder: str = None):
        """
        Initialize the hyperlink extractor
        
        Args:
            base_url: Base URL for resolving relative links
            download_folder: Folder to save downloaded files
        """
        self.base_url = base_url
        self.download_folder = download_folder or tempfile.mkdtemp()
        self.linked_documents: List[LinkedDocument] = []
        self.boq_items: List[BOQItem] = []
        
        # Ensure download folder exists
        os.makedirs(self.download_folder, exist_ok=True)
    
    def extract_hyperlinks(self, pdf_path: str) -> List[LinkedDocument]:
        """
        Extract all hyperlinks from a PDF document
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of LinkedDocument objects
        """
        self.linked_documents = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get all links on the page
                links = page.get_links()
                
                for link in links:
                    link_info = self._process_link(link, page, page_num + 1)
                    if link_info:
                        self.linked_documents.append(link_info)
                
                # Also extract URLs from text
                text = page.get_text()
                text_links = self._extract_urls_from_text(text, page_num + 1)
                
                for text_link in text_links:
                    # Avoid duplicates
                    if not any(ld.url == text_link.url for ld in self.linked_documents):
                        self.linked_documents.append(text_link)
            
            doc.close()
            
            # Classify documents by type
            self._classify_documents()
            
            logger.info(f"Extracted {len(self.linked_documents)} links from {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error extracting hyperlinks from {pdf_path}: {e}")
        
        return self.linked_documents
    
    def _process_link(self, link: Dict, page, page_num: int) -> Optional[LinkedDocument]:
        """Process a single link from PyMuPDF"""
        try:
            # Get link destination
            uri = link.get('uri', '')
            file_path = link.get('file', '')
            
            if not uri and not file_path:
                return None
            
            url = uri or file_path
            
            # Get link rectangle
            rect = link.get('from')
            rect_tuple = None
            if rect:
                rect_tuple = (rect.x0, rect.y0, rect.x1, rect.y1)
            
            # Try to get link text from the page
            link_text = ""
            if rect:
                try:
                    link_text = page.get_text("text", clip=rect).strip()
                except:
                    pass
            
            # Determine file type from URL
            file_type = self._get_file_type(url)
            
            # Create document name from URL or link text
            name = link_text or self._generate_name_from_url(url)
            
            return LinkedDocument(
                name=name,
                url=url,
                document_type="unknown",  # Will be classified later
                page_number=page_num,
                link_text=link_text,
                rect=rect_tuple,
                file_type=file_type
            )
            
        except Exception as e:
            logger.debug(f"Error processing link: {e}")
            return None
    
    def _extract_urls_from_text(self, text: str, page_num: int) -> List[LinkedDocument]:
        """Extract URLs mentioned in text"""
        documents = []
        
        # URL patterns
        url_patterns = [
            r'https?://[^\s<>"\']+',
            r'www\.[^\s<>"\']+',
            r'ftp://[^\s<>"\']+',
        ]
        
        for pattern in url_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                url = match.group()
                
                # Clean up URL (remove trailing punctuation)
                url = re.sub(r'[.,;:!?\'")\]]+$', '', url)
                
                # Add http:// if missing
                if url.startswith('www.'):
                    url = 'http://' + url
                
                name = self._generate_name_from_url(url)
                file_type = self._get_file_type(url)
                
                documents.append(LinkedDocument(
                    name=name,
                    url=url,
                    document_type="unknown",
                    page_number=page_num,
                    link_text=url,
                    file_type=file_type
                ))
        
        return documents
    
    def _get_file_type(self, url: str) -> str:
        """Determine file type from URL"""
        parsed = urlparse(url.lower())
        path = parsed.path
        
        for file_type, extensions in self.FILE_TYPE_EXTENSIONS.items():
            for ext in extensions:
                if path.endswith(ext):
                    return file_type
        
        return "unknown"
    
    def _generate_name_from_url(self, url: str) -> str:
        """Generate a readable name from URL"""
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            
            # Get filename from path
            filename = os.path.basename(path)
            if filename:
                # Remove extension for cleaner name
                name = os.path.splitext(filename)[0]
                # Replace underscores and hyphens with spaces
                name = re.sub(r'[_-]+', ' ', name)
                return name.strip() or "Unnamed Document"
            
            return "Unnamed Document"
            
        except:
            return "Unnamed Document"
    
    def _classify_documents(self):
        """Classify linked documents by their type"""
        for doc in self.linked_documents:
            doc_type = self._determine_document_type(doc)
            doc.document_type = doc_type
    
    def _determine_document_type(self, doc: LinkedDocument) -> str:
        """Determine the type of a linked document"""
        # Combine name, link text, and URL for classification
        text_to_check = f"{doc.name} {doc.link_text} {doc.url}".lower()
        
        for doc_type, patterns in self.DOCUMENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    return doc_type
        
        # Use file type as fallback
        if doc.file_type in ["excel", "csv"]:
            return "boq"  # Excel/CSV files are often BOQ
        elif doc.file_type == "pdf":
            return "document"
        elif doc.file_type in ["image", "cad"]:
            return "drawing"
        
        return "other"
    
    def download_document(self, doc: LinkedDocument) -> bool:
        """
        Download a linked document
        
        Args:
            doc: LinkedDocument to download
            
        Returns:
            True if successful, False otherwise
        """
        if not REQUESTS_AVAILABLE:
            doc.error = "requests library not available"
            return False
        
        try:
            # Resolve URL if relative
            url = doc.url
            if self.base_url and not url.startswith(('http://', 'https://', 'ftp://')):
                url = urljoin(self.base_url, url)
            
            # Download file
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Generate filename
            filename = self._generate_safe_filename(doc)
            filepath = os.path.join(self.download_folder, filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            doc.local_path = filepath
            doc.is_downloaded = True
            
            logger.info(f"Downloaded: {doc.name} -> {filepath}")
            return True
            
        except Exception as e:
            doc.error = str(e)
            logger.error(f"Error downloading {doc.url}: {e}")
            return False
    
    def _generate_safe_filename(self, doc: LinkedDocument) -> str:
        """Generate a safe filename for downloaded document"""
        # Get extension from URL
        parsed = urlparse(doc.url)
        ext = os.path.splitext(parsed.path)[1].lower()
        
        if not ext:
            # Guess extension from document type
            if doc.document_type == "boq" and doc.file_type == "unknown":
                ext = ".xlsx"
            elif doc.file_type == "excel":
                ext = ".xlsx"
            elif doc.file_type == "csv":
                ext = ".csv"
            elif doc.file_type == "pdf":
                ext = ".pdf"
            else:
                ext = ".bin"
        
        # Clean name for use as filename
        safe_name = re.sub(r'[^\w\s-]', '', doc.name)
        safe_name = re.sub(r'\s+', '_', safe_name)
        safe_name = safe_name[:50]  # Limit length
        
        if not safe_name:
            safe_name = f"document_{doc.page_number}"
        
        return f"{safe_name}{ext}"
    
    def process_boq_document(self, doc: LinkedDocument) -> List[BOQItem]:
        """
        Process a BOQ document and extract line items
        
        Args:
            doc: LinkedDocument containing BOQ
            
        Returns:
            List of BOQItem objects
        """
        if not doc.is_downloaded or not doc.local_path:
            # Try to download first
            if not self.download_document(doc):
                return []
        
        file_ext = os.path.splitext(doc.local_path)[1].lower()
        
        if file_ext in ['.xlsx', '.xls', '.xlsm']:
            return self._parse_excel_boq(doc.local_path, doc)
        elif file_ext == '.csv':
            return self._parse_csv_boq(doc.local_path, doc)
        elif file_ext == '.pdf':
            return self._parse_pdf_boq(doc.local_path, doc)
        else:
            logger.warning(f"Unsupported BOQ format: {file_ext}")
            return []
    
    def _parse_excel_boq(self, filepath: str, doc: LinkedDocument) -> List[BOQItem]:
        """Parse BOQ from Excel file"""
        if not PANDAS_AVAILABLE:
            doc.error = "pandas not available for Excel parsing"
            return []
        
        items = []
        
        try:
            # Read all sheets
            xl = pd.ExcelFile(filepath)
            
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                
                # Try to find header row
                header_row = self._find_boq_header_row(df)
                
                if header_row is not None:
                    # Re-read with correct header
                    df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)
                    
                    # Normalize column names
                    df.columns = [self._normalize_column_name(str(c)) for c in df.columns]
                    
                    # Parse rows
                    sheet_items = self._parse_boq_dataframe(df)
                    items.extend(sheet_items)
            
            # Store summary
            doc.content_summary = f"BOQ with {len(items)} line items"
            doc.extracted_data = {
                "total_items": len(items),
                "items": [self._boq_item_to_dict(item) for item in items]
            }
            
            self.boq_items.extend(items)
            
        except Exception as e:
            doc.error = f"Excel parsing error: {e}"
            logger.error(f"Error parsing Excel BOQ {filepath}: {e}")
        
        return items
    
    def _parse_csv_boq(self, filepath: str, doc: LinkedDocument) -> List[BOQItem]:
        """Parse BOQ from CSV file"""
        if not PANDAS_AVAILABLE:
            doc.error = "pandas not available for CSV parsing"
            return []
        
        items = []
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except:
                    continue
            
            # Normalize column names
            df.columns = [self._normalize_column_name(str(c)) for c in df.columns]
            
            # Parse rows
            items = self._parse_boq_dataframe(df)
            
            # Store summary
            doc.content_summary = f"BOQ with {len(items)} line items"
            doc.extracted_data = {
                "total_items": len(items),
                "items": [self._boq_item_to_dict(item) for item in items]
            }
            
            self.boq_items.extend(items)
            
        except Exception as e:
            doc.error = f"CSV parsing error: {e}"
            logger.error(f"Error parsing CSV BOQ {filepath}: {e}")
        
        return items
    
    def _parse_pdf_boq(self, filepath: str, doc: LinkedDocument) -> List[BOQItem]:
        """Parse BOQ from PDF file"""
        items = []
        
        try:
            pdf_doc = fitz.open(filepath)
            full_text = ""
            
            for page in pdf_doc:
                full_text += page.get_text()
            
            pdf_doc.close()
            
            # Try to extract table structure from text
            items = self._extract_boq_from_text(full_text)
            
            doc.content_summary = f"BOQ PDF with {len(items)} items extracted"
            doc.extracted_data = {
                "total_items": len(items),
                "items": [self._boq_item_to_dict(item) for item in items],
                "raw_text": full_text[:5000]  # Store first 5000 chars
            }
            
            self.boq_items.extend(items)
            
        except Exception as e:
            doc.error = f"PDF BOQ parsing error: {e}"
            logger.error(f"Error parsing PDF BOQ {filepath}: {e}")
        
        return items
    
    def _find_boq_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Find the header row in a BOQ DataFrame"""
        header_keywords = [
            'sr', 'sno', 's.no', 'sl', 'item', 'description', 'particulars',
            'specification', 'unit', 'uom', 'quantity', 'qty', 'rate', 'amount',
            'total', 'gst', 'tax'
        ]
        
        for idx in range(min(20, len(df))):  # Check first 20 rows
            row = df.iloc[idx]
            row_text = ' '.join(str(v).lower() for v in row if pd.notna(v))
            
            matches = sum(1 for kw in header_keywords if kw in row_text)
            if matches >= 3:  # At least 3 header keywords found
                return idx
        
        return 0  # Default to first row
    
    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name for consistent access"""
        name = name.lower().strip()
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', '_', name)
        
        # Map common variations
        mappings = {
            'sno': 'sr_no', 's_no': 'sr_no', 'sl_no': 'sr_no', 'sr_no': 'sr_no',
            'serial_no': 'sr_no', 'item_no': 'sr_no',
            'desc': 'description', 'item_description': 'description', 'particulars': 'description',
            'spec': 'specification', 'technical_specification': 'specification',
            'uom': 'unit', 'unit_of_measurement': 'unit',
            'qty': 'quantity', 'quantiy': 'quantity',
            'rate': 'unit_rate', 'unit_price': 'unit_rate', 'price': 'unit_rate',
            'amt': 'total_amount', 'amount': 'total_amount', 'total': 'total_amount',
            'gst_percent': 'gst_rate', 'gst': 'gst_rate', 'tax': 'gst_rate',
            'gst_amt': 'gst_amount', 'tax_amount': 'gst_amount',
            'total_with_tax': 'total_with_gst', 'grand_total': 'total_with_gst',
            'hsn': 'hsn_code', 'hsn_sac': 'hsn_code',
            'make': 'make_model', 'brand': 'make_model', 'make_model': 'make_model',
            'delivery': 'delivery_period', 'delivery_days': 'delivery_period'
        }
        
        return mappings.get(name, name)
    
    def _parse_boq_dataframe(self, df: pd.DataFrame) -> List[BOQItem]:
        """Parse BOQ items from a DataFrame"""
        items = []
        
        for idx, row in df.iterrows():
            try:
                # Skip empty rows
                if row.isna().all():
                    continue
                
                # Extract values
                sr_no = str(row.get('sr_no', idx + 1))
                description = str(row.get('description', ''))
                
                # Skip if no meaningful description
                if not description or description == 'nan':
                    continue
                
                item = BOQItem(
                    sr_no=sr_no,
                    description=description,
                    specification=str(row.get('specification', '')),
                    unit=str(row.get('unit', '')),
                    quantity=self._safe_float(row.get('quantity', 0)),
                    unit_rate=self._safe_float(row.get('unit_rate', 0)),
                    total_amount=self._safe_float(row.get('total_amount', 0)),
                    gst_rate=self._safe_float(row.get('gst_rate', 0)),
                    gst_amount=self._safe_float(row.get('gst_amount', 0)),
                    total_with_gst=self._safe_float(row.get('total_with_gst', 0)),
                    hsn_code=str(row.get('hsn_code', '')),
                    make_model=str(row.get('make_model', '')),
                    delivery_period=str(row.get('delivery_period', ''))
                )
                
                # Store any additional columns
                standard_cols = {'sr_no', 'description', 'specification', 'unit', 'quantity',
                               'unit_rate', 'total_amount', 'gst_rate', 'gst_amount',
                               'total_with_gst', 'hsn_code', 'make_model', 'delivery_period'}
                
                for col in df.columns:
                    if col not in standard_cols and pd.notna(row.get(col)):
                        item.additional_fields[col] = str(row[col])
                
                items.append(item)
                
            except Exception as e:
                logger.debug(f"Error parsing BOQ row {idx}: {e}")
        
        return items
    
    def _extract_boq_from_text(self, text: str) -> List[BOQItem]:
        """Extract BOQ items from plain text (PDF content)"""
        items = []
        
        # Look for numbered items with descriptions
        patterns = [
            # Pattern: 1. Description ... Quantity ... Rate ... Amount
            r'(\d+)\.\s*(.+?)\s+(\d+(?:\.\d+)?)\s*(?:Nos?|Units?|KG|MT|Sqm)?\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)',
            # Pattern: Sr.No | Description | Qty | Rate | Amount (table-like)
            r'(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*\|\s*(\d+(?:,\d{3})*(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    groups = match.groups()
                    item = BOQItem(
                        sr_no=groups[0],
                        description=groups[1].strip(),
                        quantity=self._safe_float(groups[2]),
                        unit_rate=self._safe_float(groups[3].replace(',', '')),
                        total_amount=self._safe_float(groups[4].replace(',', ''))
                    )
                    items.append(item)
                except:
                    continue
        
        return items
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        if pd.isna(value) if PANDAS_AVAILABLE else value is None:
            return 0.0
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(value)
        except:
            return 0.0
    
    def _boq_item_to_dict(self, item: BOQItem) -> Dict:
        """Convert BOQItem to dictionary"""
        return {
            'sr_no': item.sr_no,
            'description': item.description,
            'specification': item.specification,
            'unit': item.unit,
            'quantity': item.quantity,
            'unit_rate': item.unit_rate,
            'total_amount': item.total_amount,
            'gst_rate': item.gst_rate,
            'gst_amount': item.gst_amount,
            'total_with_gst': item.total_with_gst,
            'hsn_code': item.hsn_code,
            'make_model': item.make_model,
            'delivery_period': item.delivery_period,
            'additional_fields': item.additional_fields
        }
    
    def process_specification_document(self, doc: LinkedDocument) -> Dict[str, Any]:
        """
        Process a specification document and extract key details
        
        Args:
            doc: LinkedDocument containing specifications
            
        Returns:
            Dictionary with extracted specification data
        """
        if not doc.is_downloaded or not doc.local_path:
            if not self.download_document(doc):
                return {}
        
        specs = {
            "title": doc.name,
            "source": doc.url,
            "specifications": [],
            "technical_requirements": [],
            "make_model": [],
            "standards": [],
            "dimensions": [],
            "materials": []
        }
        
        file_ext = os.path.splitext(doc.local_path)[1].lower()
        
        if file_ext == '.pdf':
            specs = self._parse_pdf_specifications(doc.local_path, specs)
        elif file_ext in ['.doc', '.docx']:
            specs = self._parse_word_specifications(doc.local_path, specs)
        
        doc.content_summary = f"Specifications: {len(specs['specifications'])} items"
        doc.extracted_data = specs
        
        return specs
    
    def _parse_pdf_specifications(self, filepath: str, specs: Dict) -> Dict:
        """Parse specifications from PDF"""
        try:
            pdf_doc = fitz.open(filepath)
            full_text = ""
            
            for page in pdf_doc:
                full_text += page.get_text()
            
            pdf_doc.close()
            
            # Extract specification patterns
            spec_patterns = [
                # Pattern: Specification: Value
                r'(?:specification|spec)\s*[:\-]\s*(.+?)(?:\n|$)',
                # Pattern: Technical Requirement: Value
                r'technical\s+requirement\s*[:\-]\s*(.+?)(?:\n|$)',
                # Pattern: Make/Model: Value
                r'(?:make|model|brand)\s*[:\-]\s*(.+?)(?:\n|$)',
                # Pattern: Standard: IS/ISO/IEC number
                r'(?:standard|conforming\s+to)\s*[:\-]?\s*((?:IS|ISO|IEC|BS|ASTM)\s*[\d\-:]+)',
                # Pattern: Dimensions: LxWxH
                r'(?:dimension|size)\s*[:\-]\s*([\d\.\sx×\*]+\s*(?:mm|cm|m|inch|ft)?)',
                # Pattern: Material: Value
                r'material\s*[:\-]\s*(.+?)(?:\n|$)'
            ]
            
            for pattern in spec_patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1).strip()
                    if 'specification' in pattern.lower():
                        specs['specifications'].append(value)
                    elif 'requirement' in pattern.lower():
                        specs['technical_requirements'].append(value)
                    elif 'make|model' in pattern.lower():
                        specs['make_model'].append(value)
                    elif 'standard' in pattern.lower():
                        specs['standards'].append(value)
                    elif 'dimension' in pattern.lower():
                        specs['dimensions'].append(value)
                    elif 'material' in pattern.lower():
                        specs['materials'].append(value)
            
            # Store raw text excerpt
            specs['raw_text_excerpt'] = full_text[:3000]
            
        except Exception as e:
            logger.error(f"Error parsing PDF specifications: {e}")
            specs['error'] = str(e)
        
        return specs
    
    def _parse_word_specifications(self, filepath: str, specs: Dict) -> Dict:
        """Parse specifications from Word document"""
        try:
            # Try python-docx if available
            from docx import Document
            doc = Document(filepath)
            
            full_text = '\n'.join([para.text for para in doc.paragraphs])
            
            # Use same patterns as PDF
            specs = self._parse_pdf_specifications.__wrapped__(self, filepath, specs)
            
        except ImportError:
            specs['error'] = "python-docx not available"
        except Exception as e:
            specs['error'] = str(e)
        
        return specs
    
    def process_all_documents(self, download: bool = True) -> Dict[str, Any]:
        """
        Process all extracted linked documents
        
        Args:
            download: Whether to download documents
            
        Returns:
            Summary of all processed documents
        """
        summary = {
            "total_links": len(self.linked_documents),
            "by_type": {},
            "boq_items": [],
            "specifications": [],
            "documents": []
        }
        
        # Count by type
        for doc in self.linked_documents:
            doc_type = doc.document_type
            if doc_type not in summary["by_type"]:
                summary["by_type"][doc_type] = 0
            summary["by_type"][doc_type] += 1
        
        # Process each document
        for doc in self.linked_documents:
            if download:
                self.download_document(doc)
            
            if doc.is_downloaded:
                if doc.document_type == "boq":
                    items = self.process_boq_document(doc)
                    summary["boq_items"].extend([self._boq_item_to_dict(item) for item in items])
                
                elif doc.document_type == "specification":
                    specs = self.process_specification_document(doc)
                    if specs:
                        summary["specifications"].append(specs)
            
            summary["documents"].append(doc.to_dict())
        
        return summary
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all extracted links and processed documents"""
        return {
            "total_links": len(self.linked_documents),
            "documents": [doc.to_dict() for doc in self.linked_documents],
            "by_type": self._count_by_type(),
            "boq_summary": {
                "total_items": len(self.boq_items),
                "items": [self._boq_item_to_dict(item) for item in self.boq_items[:50]]  # First 50
            }
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count documents by type"""
        counts = {}
        for doc in self.linked_documents:
            doc_type = doc.document_type
            counts[doc_type] = counts.get(doc_type, 0) + 1
        return counts


class RFPDocumentAnalyzer:
    """
    Complete RFP document analyzer that combines hyperlink extraction
    with BOQ and specification processing
    """
    
    def __init__(self, pdf_path: str, base_url: str = None):
        """
        Initialize the analyzer
        
        Args:
            pdf_path: Path to the main RFP PDF
            base_url: Base URL for resolving relative links
        """
        self.pdf_path = pdf_path
        self.base_url = base_url
        self.hyperlink_extractor = PDFHyperlinkExtractor(base_url)
        self.analysis_results = {}
    
    def analyze(self, download_linked: bool = True) -> Dict[str, Any]:
        """
        Perform complete analysis of RFP document
        
        Args:
            download_linked: Whether to download and process linked documents
            
        Returns:
            Complete analysis results
        """
        results = {
            "main_document": self.pdf_path,
            "linked_documents": [],
            "boq_data": [],
            "specification_data": [],
            "summary": {}
        }
        
        # Extract hyperlinks
        links = self.hyperlink_extractor.extract_hyperlinks(self.pdf_path)
        
        # Process linked documents
        if download_linked:
            processing_results = self.hyperlink_extractor.process_all_documents()
            results["linked_documents"] = processing_results["documents"]
            results["boq_data"] = processing_results["boq_items"]
            results["specification_data"] = processing_results["specifications"]
        else:
            results["linked_documents"] = [doc.to_dict() for doc in links]
        
        # Create summary
        results["summary"] = {
            "total_links_found": len(links),
            "links_by_type": self.hyperlink_extractor._count_by_type(),
            "boq_items_extracted": len(results["boq_data"]),
            "specifications_extracted": len(results["specification_data"])
        }
        
        self.analysis_results = results
        return results
    
    def export_to_json(self, output_path: str):
        """Export analysis results to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        logger.info(f"Results exported to {output_path}")
    
    def get_boq_as_dataframe(self):
        """Get BOQ items as pandas DataFrame"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for DataFrame export")
        
        return pd.DataFrame(self.analysis_results.get("boq_data", []))


# Convenience function for quick extraction
def extract_linked_documents(pdf_path: str, base_url: str = None, 
                            download: bool = False) -> Dict[str, Any]:
    """
    Quick function to extract linked documents from a PDF
    
    Args:
        pdf_path: Path to PDF file
        base_url: Optional base URL for relative links
        download: Whether to download linked files
        
    Returns:
        Dictionary with extracted links and data
    """
    extractor = PDFHyperlinkExtractor(base_url)
    extractor.extract_hyperlinks(pdf_path)
    
    if download:
        return extractor.process_all_documents()
    else:
        return extractor.get_summary()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        results = extract_linked_documents(pdf_path, download=False)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("Usage: python hyperlink_extractor.py <pdf_path>")
