#!/usr/bin/env python3
"""
Enhanced PDF Extraction Manager
- Better PDF processing
- JSON metadata storage
- Organized folder structure with random identifiers
- Comprehensive metadata tracking
"""

import os
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
import shutil
from typing import Dict, List, Any, Tuple
import PyPDF2
import re

class PDFExtractionManager:
    """Manages PDF uploads, extraction, and metadata storage"""
    
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)
    
    def generate_unique_id(self, filename: str) -> str:
        """Generate unique ID with timestamp and hash"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        unique_id = f"{timestamp}_{file_hash}_{str(uuid.uuid4())[:8]}"
        return unique_id
    
    def create_upload_structure(self, filename: str, unique_id: str) -> Dict[str, Path]:
        """Create organized folder structure for PDF"""
        # Create main folder with unique ID
        upload_dir = self.upload_folder / unique_id
        upload_dir.mkdir(exist_ok=True)
        
        # Create subfolders
        paths = {
            'root': upload_dir,
            'pdf': upload_dir / 'pdf',
            'metadata': upload_dir / 'metadata',
            'extracted': upload_dir / 'extracted',
            'json': upload_dir / 'metadata'  # JSON files go here
        }
        
        for path in paths.values():
            path.mkdir(exist_ok=True)
        
        return paths
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF with page information
        Returns: (full_text, page_info)
        """
        try:
            full_text = ""
            page_info = {}
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        full_text += f"\n--- PAGE {page_num} ---\n{text}"
                        
                        page_info[f'page_{page_num}'] = {
                            'text': text,
                            'char_count': len(text),
                            'word_count': len(text.split()),
                            'line_count': len([l for l in text.split('\n') if l.strip()])
                        }
                    except Exception as e:
                        page_info[f'page_{page_num}'] = {
                            'error': str(e),
                            'status': 'failed'
                        }
            
            extraction_stats = {
                'total_pages': num_pages,
                'total_chars': len(full_text),
                'total_words': len(full_text.split()),
                'pages_extracted': len([p for p in page_info if 'error' not in page_info[p]]),
                'pages_failed': len([p for p in page_info if 'error' in page_info[p]])
            }
            
            return full_text, {
                'extraction_stats': extraction_stats,
                'page_details': page_info
            }
        
        except Exception as e:
            return "", {'error': str(e)}
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\.\-,;:()\[\]/&@#$%]', '', text)
        return text.strip()
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract common RFP sections from text"""
        sections = {}
        
        # Common RFP section patterns
        patterns = {
            'requirements': r'(?:requirements|specifications|required|must)[\s\S]{0,1000}?(?=\n(?:section|page|\d+\.|$))',
            'scope': r'(?:scope|overview|introduction)[\s\S]{0,1000}?(?=\n(?:section|page|\d+\.|$))',
            'deliverables': r'(?:deliverables|outputs|deliverable)[\s\S]{0,1000}?(?=\n(?:section|page|\d+\.|$))',
            'timeline': r'(?:timeline|schedule|dates|duration)[\s\S]{0,500}?(?=\n(?:section|page|\d+\.|$))',
            'budget': r'(?:budget|cost|price|amount|financial)[\s\S]{0,500}?(?=\n(?:section|page|\d+\.|$))',
            'terms': r'(?:terms|conditions|t&c|agreement)[\s\S]{0,1000}?(?=\n(?:section|page|\d+\.|$))',
            'evaluation': r'(?:evaluation|criteria|scoring|assessment)[\s\S]{0,1000}?(?=\n(?:section|page|\d+\.|$))',
            'contact': r'(?:contact|point of contact|poc|contact information)[\s\S]{0,500}?(?=\n(?:section|page|\d+\.|$))'
        }
        
        text_lower = text.lower()
        
        for section_name, pattern in patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                sections[section_name] = match.group(0)[:500]  # First 500 chars
        
        return sections
    
    def save_metadata_json(self, metadata_path: Path, metadata: Dict[str, Any]) -> bool:
        """Save comprehensive metadata to JSON"""
        try:
            json_file = metadata_path / 'metadata.json'
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving metadata JSON: {e}")
            return False
    
    def save_extracted_text(self, extracted_path: Path, filename: str, text: str) -> bool:
        """Save extracted text to file"""
        try:
            text_file = extracted_path / f"{filename.rsplit('.', 1)[0]}_extracted.txt"
            
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            return True
        except Exception as e:
            print(f"Error saving extracted text: {e}")
            return False
    
    def process_pdf(self, pdf_file_path: str, original_filename: str) -> Dict[str, Any]:
        """
        Main processing function
        Returns: Complete metadata with all extracted information
        """
        try:
            # Generate unique ID and create folder structure
            unique_id = self.generate_unique_id(original_filename)
            paths = self.create_upload_structure(original_filename, unique_id)
            
            # Copy PDF to organized folder
            dest_pdf = paths['pdf'] / secure_filename(original_filename)
            shutil.copy2(pdf_file_path, dest_pdf)
            
            # Extract text from PDF
            full_text, extraction_info = self.extract_text_from_pdf(str(dest_pdf))
            
            # Clean and process text
            cleaned_text = self.clean_text(full_text)
            
            # Extract sections
            sections = self.extract_sections(full_text)
            
            # Create comprehensive metadata
            metadata = {
                'upload_metadata': {
                    'unique_id': unique_id,
                    'original_filename': original_filename,
                    'secure_filename': secure_filename(original_filename),
                    'upload_timestamp': datetime.now().isoformat(),
                    'folder_path': str(paths['root']),
                    'file_size_bytes': os.path.getsize(dest_pdf),
                    'file_hash_md5': self._calculate_file_hash(str(dest_pdf))
                },
                'extraction_info': extraction_info,
                'sections_found': {k: v[:200] for k, v in sections.items()},  # First 200 chars of each
                'text_stats': {
                    'total_chars': len(cleaned_text),
                    'total_words': len(cleaned_text.split()),
                    'estimated_reading_time_minutes': len(cleaned_text.split()) // 200,
                    'unique_words': len(set(cleaned_text.lower().split()))
                },
                'processing_status': 'success',
                'processing_timestamp': datetime.now().isoformat()
            }
            
            # Save extracted text
            self.save_extracted_text(paths['extracted'], original_filename, full_text)
            
            # Save metadata JSON
            self.save_metadata_json(paths['metadata'], metadata)
            
            return {
                'success': True,
                'unique_id': unique_id,
                'metadata': metadata,
                'full_text': cleaned_text,
                'sections': sections,
                'paths': {k: str(v) for k, v in paths.items()}
            }
        
        except Exception as e:
            error_metadata = {
                'error': str(e),
                'processing_timestamp': datetime.now().isoformat(),
                'original_filename': original_filename,
                'processing_status': 'failed'
            }
            return {
                'success': False,
                'error': str(e),
                'metadata': error_metadata
            }
    
    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate MD5 hash of file"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def get_upload_info(self, unique_id: str) -> Dict[str, Any]:
        """Retrieve upload information and metadata"""
        try:
            metadata_file = self.upload_folder / unique_id / 'metadata' / 'metadata.json'
            
            if not metadata_file.exists():
                return {'error': 'Metadata not found'}
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return {
                'success': True,
                'metadata': metadata,
                'unique_id': unique_id
            }
        
        except Exception as e:
            return {'error': str(e)}


def secure_filename(filename):
    """Secure filename (from werkzeug)"""
    import re
    filename = str(filename)
    # Remove path separators
    for sep in ['/', '\\']:
        if sep in filename:
            filename = filename.split(sep)[-1]
    # Keep only safe characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    return filename.strip()
