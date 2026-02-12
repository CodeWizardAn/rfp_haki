"""
PDF Text Extraction Tool using pdfplumber
Designed to extract all text from RFP and other document types
Handles various PDF structures, layouts, and formatting
"""

import pdfplumber
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """
    Comprehensive PDF text extractor using pdfplumber
    Handles various PDF layouts including tables, text blocks, and mixed content
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDF extractor
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.document_name = os.path.basename(pdf_path)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Initializing extractor for: {self.document_name}")
    
    def extract_text_from_page(self, page) -> str:
        """
        Extract all text from a single page
        
        Args:
            page: pdfplumber page object
            
        Returns:
            str: Extracted text from the page
        """
        text = ""
        
        # Extract direct text
        if page.extract_text():
            text += page.extract_text()
        
        return text
    
    def extract_tables_from_page(self, page) -> List[List[List[str]]]:
        """
        Extract all tables from a single page
        
        Args:
            page: pdfplumber page object
            
        Returns:
            List of tables (each table is a list of rows)
        """
        tables = []
        
        try:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
        except Exception as e:
            logger.warning(f"Error extracting tables: {e}")
        
        return tables
    
    def extract_structured_data(self, page) -> Dict:
        """
        Extract structured data from a page (text, tables, metadata)
        
        Args:
            page: pdfplumber page object
            
        Returns:
            Dictionary with structured page data
        """
        structured_data = {
            'page_number': page.page_number,
            'page_height': page.height,
            'page_width': page.width,
            'text': self.extract_text_from_page(page),
            'tables': self.extract_tables_from_page(page),
            'text_count': len(page.extract_text()) if page.extract_text() else 0
        }
        
        return structured_data
    
    def extract_all_text(self, include_tables: bool = True) -> str:
        """
        Extract all text from the entire PDF
        
        Args:
            include_tables (bool): Whether to include table content
            
        Returns:
            str: Complete text from all pages
        """
        all_text = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Total pages: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.info(f"Extracting text from page {page_num}/{total_pages}")
                    
                    # Extract regular text
                    text = self.extract_text_from_page(page)
                    if text:
                        all_text.append(f"\n--- PAGE {page_num} ---\n")
                        all_text.append(text)
                    
                    # Extract tables if requested
                    if include_tables:
                        tables = self.extract_tables_from_page(page)
                        if tables:
                            all_text.append(f"\n--- TABLES ON PAGE {page_num} ---\n")
                            for table_num, table in enumerate(tables, 1):
                                all_text.append(f"\nTable {table_num}:\n")
                                for row in table:
                                    all_text.append(" | ".join(str(cell) if cell else "" for cell in row))
                                    all_text.append("\n")
                    
                    all_text.append(f"\n--- END PAGE {page_num} ---\n")
            
            logger.info("Text extraction completed successfully")
            return "".join(all_text)
        
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise
    
    def extract_to_file(self, output_path: Optional[str] = None, 
                       include_tables: bool = True) -> str:
        """
        Extract all text and save to a file
        
        Args:
            output_path (str): Output file path (if None, creates one from PDF name)
            include_tables (bool): Whether to include table content
            
        Returns:
            str: Path to the output file
        """
        if output_path is None:
            base_name = Path(self.pdf_path).stem
            output_path = f"{base_name}_extracted.txt"
        
        extracted_text = self.extract_all_text(include_tables=include_tables)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        logger.info(f"Text saved to: {output_path}")
        return output_path
    
    def extract_as_json(self, include_tables: bool = True) -> Dict:
        """
        Extract all data and return as structured JSON
        
        Args:
            include_tables (bool): Whether to include table content
            
        Returns:
            Dictionary with all extracted data
        """
        all_data = {
            'document_name': self.document_name,
            'document_path': self.pdf_path,
            'pages': []
        }
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Total pages: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.info(f"Processing page {page_num}/{total_pages}")
                    
                    page_data = self.extract_structured_data(page)
                    
                    if not include_tables:
                        page_data.pop('tables', None)
                    
                    all_data['pages'].append(page_data)
            
            all_data['total_pages'] = total_pages
            logger.info("JSON extraction completed successfully")
            return all_data
        
        except Exception as e:
            logger.error(f"Error extracting to JSON: {e}")
            raise
    
    def extract_json_to_file(self, output_path: Optional[str] = None,
                            include_tables: bool = True) -> str:
        """
        Extract all data as JSON and save to file
        
        Args:
            output_path (str): Output file path (if None, creates one from PDF name)
            include_tables (bool): Whether to include table content
            
        Returns:
            str: Path to the output file
        """
        if output_path is None:
            base_name = Path(self.pdf_path).stem
            output_path = f"{base_name}_extracted.json"
        
        extracted_data = self.extract_as_json(include_tables=include_tables)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON data saved to: {output_path}")
        return output_path
    
    def extract_metadata(self) -> Dict:
        """
        Extract metadata from the PDF
        
        Returns:
            Dictionary with PDF metadata
        """
        metadata = {}
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Document metadata
                metadata['document_name'] = self.document_name
                metadata['total_pages'] = len(pdf.pages)
                metadata['pdf_metadata'] = pdf.metadata
                
                # Get first and last page dimensions
                if pdf.pages:
                    metadata['page_width'] = pdf.pages[0].width
                    metadata['page_height'] = pdf.pages[0].height
                
                logger.info("Metadata extraction completed")
        
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
        
        return metadata
    
    def extract_with_filter(self, page_numbers: Optional[List[int]] = None,
                           include_tables: bool = True) -> str:
        """
        Extract text from specific pages
        
        Args:
            page_numbers (List[int]): List of page numbers to extract (1-indexed)
            include_tables (bool): Whether to include table content
            
        Returns:
            str: Extracted text from specified pages
        """
        all_text = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                if page_numbers is None:
                    page_numbers = list(range(1, total_pages + 1))
                
                for page_num in page_numbers:
                    if 1 <= page_num <= total_pages:
                        page = pdf.pages[page_num - 1]
                        logger.info(f"Extracting text from page {page_num}")
                        
                        text = self.extract_text_from_page(page)
                        if text:
                            all_text.append(f"\n--- PAGE {page_num} ---\n")
                            all_text.append(text)
                        
                        if include_tables:
                            tables = self.extract_tables_from_page(page)
                            if tables:
                                all_text.append(f"\n--- TABLES ON PAGE {page_num} ---\n")
                                for table_num, table in enumerate(tables, 1):
                                    all_text.append(f"\nTable {table_num}:\n")
                                    for row in table:
                                        all_text.append(" | ".join(str(cell) if cell else "" for cell in row))
                                        all_text.append("\n")
                        
                        all_text.append(f"\n--- END PAGE {page_num} ---\n")
                    else:
                        logger.warning(f"Page {page_num} out of range (1-{total_pages})")
            
            logger.info("Filtered text extraction completed")
            return "".join(all_text)
        
        except Exception as e:
            logger.error(f"Error during filtered extraction: {e}")
            raise


def batch_extract_pdfs(pdf_directory: str, output_format: str = 'txt',
                       include_tables: bool = True) -> List[str]:
    """
    Extract text from all PDFs in a directory
    
    Args:
        pdf_directory (str): Directory containing PDF files
        output_format (str): Output format ('txt' or 'json')
        include_tables (bool): Whether to include table content
        
    Returns:
        List[str]: List of output file paths
    """
    output_files = []
    
    if not os.path.isdir(pdf_directory):
        logger.error(f"Directory not found: {pdf_directory}")
        return output_files
    
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    logger.info(f"Found {len(pdf_files)} PDF files in {pdf_directory}")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        logger.info(f"Processing: {pdf_file}")
        
        try:
            extractor = PDFTextExtractor(pdf_path)
            
            if output_format.lower() == 'json':
                output_file = extractor.extract_json_to_file(
                    include_tables=include_tables
                )
            else:
                output_file = extractor.extract_to_file(
                    include_tables=include_tables
                )
            
            output_files.append(output_file)
        
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            continue
    
    logger.info(f"Batch extraction completed. {len(output_files)} files processed")
    return output_files


# Example usage
if __name__ == "__main__":
    # Example 1: Extract from a single PDF file
    # pdf_path = "path/to/your/rfp_document.pdf"
    # extractor = PDFTextExtractor(pdf_path)
    
    # Extract and save as text file
    # extractor.extract_to_file()
    
    # Extract and save as JSON
    # extractor.extract_json_to_file()
    
    # Extract metadata
    # metadata = extractor.extract_metadata()
    # print(json.dumps(metadata, indent=2))
    
    # Example 2: Extract specific pages
    # text = extractor.extract_with_filter(page_numbers=[1, 2, 5])
    # print(text)
    
    # Example 3: Batch extract all PDFs in a directory
    # batch_extract_pdfs("path/to/pdf/directory", output_format='txt', include_tables=True)
    
    print("PDF Text Extractor module loaded successfully")
    print("Use PDFTextExtractor class or batch_extract_pdfs function to extract text")
