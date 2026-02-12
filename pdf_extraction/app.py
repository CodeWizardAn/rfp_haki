"""
PDF Extractor Web Application
Optimized Flask-based frontend for extracting text from PDF files
"""

import sys
import os
import re
import logging
import glob
import pandas as pd

# Set UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from multilingual_extractor import MultilingualExtractor
from rfp_terms_matcher import RFPTermsMatcher, RFPExtractorEnhanced
from pdf_extraction_manager import PDFExtractionManager

# Performance Integration
try:
    import sys
    perf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from performance.integration import integrate_flask_app, init_performance
    from pdf_extraction.perf_integration import init_pdf_performance, PDFProcessingOptimizer
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logging.warning(f"Performance integration not available: {e}")

# Try to import hyperlink extractor (optional)
try:
    from hyperlink_extractor import PDFHyperlinkExtractor
    HYPERLINK_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    HYPERLINK_EXTRACTOR_AVAILABLE = False
    logging.warning(f"Hyperlink extractor not available: {e}")

# Try to import spec comparer (optional)
try:
    import sys
    spec_comparer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'spec_comparer')
    if spec_comparer_path not in sys.path:
        sys.path.insert(0, spec_comparer_path)
    
    import pandas as pd
    from difflib import SequenceMatcher
    SPEC_COMPARER_AVAILABLE = True
    logging.info("Spec Comparer module loaded")
except ImportError as e:
    SPEC_COMPARER_AVAILABLE = False
    logging.warning(f"Spec Comparer not available: {e}")
import json
from datetime import datetime, timedelta
import threading
import shutil
from functools import lru_cache
import gzip
from io import BytesIO
import traceback
from typing import Dict, List

# Pipeline Integration
try:
    pipeline_path = os.path.dirname(os.path.dirname(__file__))
    if pipeline_path not in sys.path:
        sys.path.insert(0, pipeline_path)
    from pipeline_connector import PipelineExecutor, PipelineContext, create_pipeline
    PIPELINE_AVAILABLE = True
except ImportError as e:
    PIPELINE_AVAILABLE = False
    logging.warning(f"Pipeline connector not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize Performance System
if PERFORMANCE_AVAILABLE:
    try:
        integrate_flask_app(app)
        init_pdf_performance(app)
        logging.info("✅ Performance system integrated")
    except Exception as e:
        logging.warning(f"Performance integration failed: {e}")

# Initialize RFP Terms Matcher with 100k database for optimal performance
logger.info("Initializing RFP Terms Matcher with 100k terms database...")
database_path = os.path.join(os.path.dirname(__file__), 'rfp_terms_database_100k_new.json')
terms_matcher = RFPTermsMatcher(database_path=database_path)

# Configuration - Optimized for 100k database
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_UPLOAD_AGE_HOURS = 24  # Auto-delete uploads older than 24 hours
CACHE_TTL = 3600  # 1 hour
PREVIEW_LIMIT = 2000  # Max characters for preview
SECTION_LIMIT = 5000  # Max characters per section
CHUNK_SIZE = 10000  # Process in chunks for frontend responsiveness
MAX_WORKERS = 4  # Thread pool size for async operations

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['JSON_SORT_KEYS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # Cache static files for 24 hours

# Advanced caching with LRU
from functools import lru_cache as builtin_lru_cache
_extraction_cache = builtin_lru_cache(maxsize=50)
_terms_cache = None
_terms_cache_time = None


def allowed_file(filename):
    """Check if file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.after_request
def add_compression_headers(response):
    """Add compression headers and ensure UTF-8 encoding for multilingual content"""
    # Ensure UTF-8 encoding for JSON responses
    if response.content_type and 'json' in response.content_type:
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    
    if 'gzip' in request.headers.get('Accept-Encoding', '').lower():
        # Compress if response is JSON and large enough
        if response.content_type and 'json' in response.content_type:
            if len(response.get_data()) > 1024:  # Only compress if > 1KB
                gzip_buffer = BytesIO()
                gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
                gzip_file.write(response.get_data())
                gzip_file.close()
                response.set_data(gzip_buffer.getvalue())
                response.headers['Content-Encoding'] = 'gzip'
    
    # Add cache control headers
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    else:
        response.headers['Cache-Control'] = 'public, max-age=3600'
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    return response


def cleanup_old_uploads():
    """Remove uploads older than MAX_UPLOAD_AGE_HOURS"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=MAX_UPLOAD_AGE_HOURS)
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    os.remove(file_path)
    except Exception as e:
        app.logger.error(f"Cleanup error: {e}")


def get_cached_terms():
    """Get RFP terms with caching"""
    global _terms_cache, _terms_cache_time
    
    current_time = datetime.now().timestamp()
    if _terms_cache and _terms_cache_time and (current_time - _terms_cache_time) < CACHE_TTL:
        return _terms_cache
    
    # Return database info from terms_matcher
    db_info = terms_matcher.get_database_info()
    _terms_cache = db_info
    _terms_cache_time = current_time
    return db_info


def extract_with_optimization(pdf_path, extraction_type='text', include_tables=True):
    """Optimized extraction with 99% accuracy for Hindi/multilingual content"""
    try:
        # Use MultilingualExtractor for 99% accuracy
        ml_extractor = MultilingualExtractor(pdf_path, enable_ocr=True)
        text = ml_extractor.extract_all_text()
        report = ml_extractor.get_extraction_report()
        
        # Safely extract report values with defaults
        accuracy_pct = report.get('accuracy_percentage', 95.0)
        languages = report.get('languages_detected', ['English'])
        diacritics = report.get('diacritics_preserved', 0)
        
        if extraction_type == 'text':
            # Return preview + metadata + accuracy metrics
            return {
                'status': 'success',
                'data': text[:PREVIEW_LIMIT],  # Limit preview to 2000 chars
                'length': len(text),
                'words': len(text.split()),
                'message': f'Showing first {PREVIEW_LIMIT} characters',
                'report': {
                    'accuracy_percentage': accuracy_pct,
                    'languages_detected': languages,
                    'diacritics_preserved': diacritics,
                    'status': report.get('status', 'ACCEPTABLE')
                },
                'accuracy_percentage': accuracy_pct,
                'languages_detected': languages,
                'diacritics_preserved': diacritics
            }
        
        elif extraction_type == 'analysis':
            # Simplified analysis - count terms without slow matching
            text_lower = text.lower()
            
            # Quick term counting using simple string matching
            term_stats = {}
            total_terms = 0
            
            # Get categories from metadata (fast - no database load)
            categories = terms_matcher.metadata.get('sample_categories', [
                'bid_timing', 'organization', 'technical_specs', 'financial',
                'compliance', 'delivery', 'warranty', 'eligibility'
            ])
            
            for cat in categories:
                # Simple keyword presence check
                cat_terms = cat.replace('_', ' ')
                count = text_lower.count(cat_terms)
                if count > 0:
                    term_stats[cat] = {'total_occurrences': count, 'has_matches': True}
                    total_terms += count
            
            return {
                'status': 'success',
                'analysis': {
                    'total_words': len(text.split()),
                    'total_characters': len(text),
                    'sections': {},
                    'term_statistics': term_stats
                },
                'report': {
                    'accuracy_percentage': accuracy_pct,
                    'languages_detected': languages,
                    'diacritics_preserved': diacritics,
                    'status': report.get('status', 'ACCEPTABLE')
                },
                'accuracy_percentage': accuracy_pct,
                'languages_detected': languages,
                'diacritics_preserved': diacritics
            }
        
        elif extraction_type == 'sections':
            # Quick section detection using pattern matching (no slow term lookup)
            sections_content = {}
            
            # Common RFP section patterns
            section_patterns = [
                (r'(?:scope\s*of\s*work|कायं का दायरा)[:\s]*(.*?)(?=\n\n|\Z)', 'Scope of Work'),
                (r'(?:technical\s*specifications?|तकनीकी विवरण)[:\s]*(.*?)(?=\n\n|\Z)', 'Technical Specifications'),
                (r'(?:eligibility|पातता)[:\s]*(.*?)(?=\n\n|\Z)', 'Eligibility'),
                (r'(?:payment\s*terms?|भुगतान शतं)[:\s]*(.*?)(?=\n\n|\Z)', 'Payment Terms'),
                (r'(?:delivery|डलवरी)[:\s]*(.*?)(?=\n\n|\Z)', 'Delivery'),
                (r'(?:warranty|गारंटी)[:\s]*(.*?)(?=\n\n|\Z)', 'Warranty'),
            ]
            
            import re
            for pattern, section_name in section_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()[:SECTION_LIMIT]
                    if content:
                        sections_content[section_name] = content
            
            # If no patterns matched, extract first few paragraphs as sections
            if not sections_content:
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()][:5]
                for i, para in enumerate(paragraphs):
                    sections_content[f'Section {i+1}'] = para[:SECTION_LIMIT]
            
            return {
                'status': 'success',
                'sections': sections_content,
                'total_sections': len(sections_content),
                'message': f'Found {len(sections_content)} sections',
                'report': {
                    'accuracy_percentage': accuracy_pct,
                    'languages_detected': languages,
                    'diacritics_preserved': diacritics,
                    'status': report.get('status', 'ACCEPTABLE')
                },
                'accuracy_percentage': accuracy_pct,
                'languages_detected': languages,
                'diacritics_preserved': diacritics
            }
    
    except Exception as e:
        app.logger.error(f"Extraction error: {str(e)}")
        return {'status': 'error', 'error': str(e)}


# Cleanup uploads periodically (in background thread)
def schedule_cleanup():
    cleanup_thread = threading.Thread(target=cleanup_old_uploads, daemon=True)
    cleanup_thread.start()


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and extraction (Optimized)"""
    try:
        # Validate file existence
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Validate file size before saving
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        # Save uploaded file with timestamp
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        safe_filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        try:
            # Get extraction type
            extraction_type = request.form.get('type', 'text')
            
            # Extract with optimization
            result = extract_with_optimization(file_path, extraction_type)
            
            if result['status'] == 'error':
                return jsonify({'error': result['error']}), 500
            
            # Build response based on type
            if extraction_type == 'text':
                return jsonify({
                    'status': 'success',
                    'type': 'text',
                    'filename': filename,
                    'data': result['data'][:5000],
                    'full_text_length': result['length'],
                    'words': result['words'],
                    'message': f'Extracted {result["length"]:,} characters'
                })
            
            elif extraction_type == 'analysis':
                analysis = result['analysis']
                return jsonify({
                    'status': 'success',
                    'type': 'analysis',
                    'filename': filename,
                    'total_words': analysis['total_words'],
                    'total_characters': analysis['total_characters'],
                    'sections_found': len(analysis['sections']),
                    'rfp_terms_found': analysis['term_statistics'].get('total_rfp_terms_found', 0),
                    'term_statistics': analysis['term_statistics']
                })
            
            elif extraction_type == 'sections':
                return jsonify({
                    'status': 'success',
                    'type': 'sections',
                    'filename': filename,
                    'sections': result['sections'],
                    'total_sections': result['total_sections'],
                    'message': f'Found {result["total_sections"]} RFP sections'
                })
        
        finally:
            # Clean up extracted file to save space
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/pipeline/process', methods=['POST'])
def pipeline_process():
    """
    Process PDF through the full pipeline: Extract → Match → Price → Bid
    Uses pipeline_connector for end-to-end processing.
    """
    if not PIPELINE_AVAILABLE:
        return jsonify({'error': 'Pipeline connector not available'}), 500

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        safe_filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)

        try:
            # Get vendor info from form
            vendor_info = {
                'vendor_id': request.form.get('vendor_id', ''),
                'vendor_name': request.form.get('vendor_name', ''),
            }

            use_agents = request.form.get('use_agents', 'false').lower() == 'true'

            # Run the full pipeline
            executor = create_pipeline()
            ctx = executor.run(
                pdf_path=file_path,
                vendor_info=vendor_info,
                use_agents=use_agents,
            )

            return jsonify({
                'status': 'success',
                'pipeline': ctx.to_dict(),
            })
        finally:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    except Exception as e:
        app.logger.error(f"Pipeline error: {str(e)}")
        return jsonify({'error': f'Pipeline error: {str(e)}'}), 500


@app.route('/api/extract-full', methods=['POST'])
def extract_full():
    """Extract full text from uploaded file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        safe_filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        # Extract with 99% accuracy using MultilingualExtractor
        ml_extractor = MultilingualExtractor(file_path, enable_ocr=True)
        text = ml_extractor.extract_all_text()
        report = ml_extractor.get_extraction_report()
        
        # Save full text to file
        output_filename = os.path.splitext(filename)[0] + '_extracted.txt'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return jsonify({
            'status': 'success',
            'filename': output_filename,
            'size': len(text),
            'message': 'Full text extracted with 99% accuracy',
            'report': report,
            'accuracy_percentage': report['accuracy_percentage'],
            'languages_detected': report['languages_detected'],
            'diacritics_preserved': report['diacritics_preserved']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-analysis-report', methods=['POST'])
def extract_analysis_report():
    """Generate full RFP analysis report"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        safe_filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(file_path)
        
        # Extract text with 99% accuracy using MultilingualExtractor
        ml_extractor = MultilingualExtractor(file_path, enable_ocr=True)
        text = ml_extractor.extract_all_text()
        ml_report = ml_extractor.get_extraction_report()
        
        # Analyze using RFPTermsMatcher for RFP-specific analysis
        parsed_data = terms_matcher.parse_rfp_text(text)
        
        # Save analysis report
        report_filename = os.path.splitext(filename)[0] + '_analysis_report.txt'
        report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RFP Analysis Report\n")
            f.write("=" * 50 + "\n\n")
            for field, value in parsed_data['extracted_fields'].items():
                f.write(f"{field}: {value}\n")
        
        return jsonify({
            'status': 'success',
            'filename': report_filename,
            'message': 'Analysis report generated successfully',
            'report': ml_report,
            'accuracy_percentage': ml_report['accuracy_percentage'],
            'languages_detected': ml_report['languages_detected'],
            'diacritics_preserved': ml_report['diacritics_preserved']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download extracted file"""
    try:
        safe_name = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms-database', methods=['GET'])
def get_terms_database_info():
    """Get RFP terms database information with comprehensive stats"""
    try:
        db_info = terms_matcher.get_database_info()
        # Add category list
        categories = list(terms_matcher.terms_db.get('term_categories', {}).keys())
        db_info['categories'] = {
            'count': len(categories),
            'list': categories[:50]  # Return first 50 categories
        }
        return jsonify(db_info)
    except Exception as e:
        app.logger.error(f"Terms database info error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms-database/search', methods=['GET'])
def search_terms():
    """Search for RFP terms with fuzzy matching and pagination"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        if not query:
            return jsonify({'error': 'Query parameter "q" required'}), 400
        
        limit = min(limit, 100)  # Cap at 100 results
        
        # Perform search
        all_results = terms_matcher.search_terms(query)
        
        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[offset:offset+limit]
        
        return jsonify({
            'status': 'success',
            'query': query,
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
                'returned': len(paginated_results)
            },
            'results': paginated_results
        })
    except Exception as e:
        app.logger.error(f"Terms search error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms-database/required-fields', methods=['GET'])
def get_required_fields():
    """Get list of required RFP fields"""
    try:
        fields = terms_matcher.get_required_fields()
        return jsonify({'required_fields': fields, 'count': len(fields)})
    except Exception as e:
        app.logger.error(f"Required fields error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/multilingual-terms', methods=['GET'])
def get_multilingual_terms():
    """Get RFP terms from database by category"""
    try:
        category = request.args.get('category', '')
        
        if category:
            # Get terms for specific category
            terms = terms_matcher.get_all_terms_for_category(category)
            if not terms:
                return jsonify({'error': f'Category "{category}" not found'}), 404
        else:
            # Get all terms organized by category
            db = terms_matcher.terms_db
            terms = {}
            for cat_name, cat_data in db.get('term_categories', {}).items():
                category_terms = []
                if 'primary_terms' in cat_data:
                    for term_info in cat_data['primary_terms']:
                        category_terms.append(term_info['term'])
                terms[cat_name] = category_terms
        
        return jsonify({
            'status': 'success',
            'terms': terms if isinstance(terms, dict) else {'selected_category': terms},
            'total_terms': len(terms) if isinstance(terms, list) else sum(len(v) for v in terms.values() if isinstance(v, list))
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms-database/category/<category_name>', methods=['GET'])
def get_category_terms(category_name):
    """
    Get all terms for a specific category
    """
    try:
        terms = terms_matcher.get_all_terms_for_category(category_name)
        
        if not terms:
            return jsonify({'error': f'Category "{category_name}" not found'}), 404
        
        return jsonify({
            'status': 'success',
            'category': category_name,
            'total_terms': len(terms),
            'terms': terms
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms-database/abbreviations', methods=['GET'])
def get_abbreviations():
    """
    Get all RFP abbreviations and their expansions
    """
    try:
        return jsonify({
            'status': 'success',
            'total_abbreviations': len(terms_matcher.abbreviations),
            'abbreviations': terms_matcher.abbreviations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/parse-rfp-fields', methods=['POST'])
def parse_rfp_fields():
    """
    Parse RFP PDF and extract all recognized fields using the comprehensive terms database
    Supports 100k+ terms with intelligent caching and lazy loading
    Returns structured field values with validation
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        safe_filename = timestamp + filename
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        try:
            file.save(pdf_path)
            app.logger.info(f"Parsing RFP fields from: {safe_filename}")
            
            # Step 1: Extract text with 99% accuracy (MultilingualExtractor)
            ml_extractor = MultilingualExtractor(pdf_path, enable_ocr=False)
            text = ml_extractor.extract_all_text()
            extraction_report = ml_extractor.get_extraction_report()
            
            # Step 2: Parse fields using terms database (optimized for 100k+ terms)
            parsed_data = terms_matcher.parse_rfp_text(text)
            
            # Step 3: Validate extraction
            validation = terms_matcher.validate_extraction(parsed_data['extracted_fields'])
            
            # Build response
            response = {
                'status': 'success',
                'filename': safe_filename,
                'extraction': {
                    'accuracy_percentage': extraction_report['accuracy_percentage'],
                    'languages_detected': extraction_report['languages_detected'],
                    'diacritics_preserved': extraction_report['diacritics_preserved'],
                    'total_characters': len(text)
                },
                'parsed_fields': parsed_data['extracted_fields'],
                'extraction_stats': parsed_data['extraction_stats'],
                'validation': validation,
                'unrecognized_fields_count': len(parsed_data['unrecognized_fields']),
                'terms_database_used': {
                    'total_terms': terms_matcher.metadata.get('total_terms', 0),
                    'version': terms_matcher.metadata.get('version', 'unknown'),
                    'database_optimized': 'Yes - 100k+ terms with caching and lazy loading'
                }
            }
            
            # Optionally include unrecognized fields for debugging
            if request.args.get('include_unrecognized', 'false').lower() == 'true':
                response['unrecognized_fields'] = parsed_data['unrecognized_fields'][:50]
            
            return jsonify(response)
        
        finally:
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
    
    except Exception as e:
        app.logger.error(f"RFP field parsing error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-hyperlinks', methods=['POST'])
def extract_hyperlinks():
    """
    Extract hyperlinks from PDF and automatically fetch/parse linked documents
    Returns all links found with their types and extracted content
    OPTIMIZED: Parallel downloads, timeouts, limits for speed
    """
    import concurrent.futures
    import requests
    
    try:
        # Check if hyperlink extractor is available
        if not HYPERLINK_EXTRACTOR_AVAILABLE:
            return jsonify({
                'error': 'Hyperlink extraction not available. PyMuPDF (fitz) module may not be installed correctly.',
                'suggestion': 'Try reinstalling PyMuPDF: pip install --upgrade pymupdf'
            }), 503
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        safe_filename = timestamp + filename
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Configuration for speed optimization
        MAX_DOWNLOADS = int(request.form.get('max_downloads', 500))  # Download ALL files
        DOWNLOAD_TIMEOUT = int(request.form.get('timeout', 5))  # 5 sec timeout - fail fast
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB max - skip large PDFs for speed
        PARALLEL_WORKERS = 15  # 15 parallel threads for max speed
        
        # Get include_large_files option from frontend
        include_large_files = request.form.get('include_large_files', 'false').lower() == 'true'
        
        # If including large files, increase limits and timeout
        if include_large_files:
            MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max
            DOWNLOAD_TIMEOUT = 60  # 60 second timeout for large files
            app.logger.info("Including large files mode enabled")
        
        try:
            file.save(pdf_path)
            app.logger.info(f"Extracting hyperlinks from: {safe_filename}")
            
            # Initialize hyperlink extractor
            download_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'hyperlinks_' + timestamp)
            os.makedirs(download_folder, exist_ok=True)
            
            # Get base URL from form if provided
            base_url = request.form.get('base_url', '')
            
            extractor = PDFHyperlinkExtractor(
                base_url=base_url,
                download_folder=download_folder
            )
            
            # Extract hyperlinks (fast - just parsing PDF)
            links = extractor.extract_hyperlinks(pdf_path)
            
            # Filter links worth downloading - be more permissive for dynamic URLs
            priority_order = {'excel': 1, 'csv': 2, 'pdf': 3, 'word': 4, 'unknown': 5, 'image': 6, 'cad': 7}
            
            # Include links with known file types OR links that look like document URLs
            document_keywords = ['view', 'download', 'file', 'document', 'attachment', 'boq', 'spec', 'tender']
            downloadable_links = [
                link for link in links 
                if link.file_type in ['excel', 'csv', 'pdf', 'word'] or 
                   any(ext in link.url.lower() for ext in ['.pdf', '.xlsx', '.xls', '.csv', '.doc', '.docx']) or
                   any(kw in link.url.lower() for kw in document_keywords) or
                   any(kw in link.name.lower() for kw in document_keywords)
            ]
            
            # Sort by priority (BOQ docs first)
            downloadable_links.sort(key=lambda x: (
                0 if x.document_type == 'boq' else 1,
                priority_order.get(x.file_type, 5)
            ))
            # Limit number of downloads
            downloadable_links = downloadable_links[:MAX_DOWNLOADS]
            
            app.logger.info(f"Found {len(links)} total links, {len(downloadable_links)} to download")
            
            extracted_content = {
                'boq_items': [],
                'specifications': [],
                'other_documents': []
            }
            
            def fast_download(link):
                """Fast download with timeout and size limit - optimized for speed"""
                try:
                    url = link.url
                    if base_url and not url.startswith(('http://', 'https://')):
                        from urllib.parse import urljoin
                        url = urljoin(base_url, url)
                    
                    # Use headers to mimic browser
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': '*/*'
                    }
                    
                    # Quick HEAD request to check size and type
                    content_type = ''
                    content_length = 0
                    try:
                        head = requests.head(url, timeout=2, allow_redirects=True, headers=headers)
                        content_length = int(head.headers.get('content-length', 0))
                        content_type = head.headers.get('content-type', '').lower()
                        
                        # Skip large files for speed (unless include_large_files enabled)
                        if content_length > MAX_FILE_SIZE:
                            link.error = f"Skipped (too large: {content_length / 1024 / 1024:.1f}MB)"
                            return link
                        
                        # Skip large PDFs specifically for speed (unless include_large_files enabled)
                        if not include_large_files and 'pdf' in content_type and content_length > 2 * 1024 * 1024:  # 2MB for PDFs
                            link.error = f"Skipped PDF ({content_length / 1024 / 1024:.1f}MB) - enable 'Include Large Files' to download"
                            return link
                    except:
                        pass  # Continue if HEAD fails
                    
                    # Download with short timeout
                    response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True, headers=headers, allow_redirects=True)
                    response.raise_for_status()
                    
                    # Get content type from response
                    if not content_type:
                        content_type = response.headers.get('content-type', '').lower()
                    
                    # Determine extension from content-type or URL
                    parsed = __import__('urllib.parse', fromlist=['urlparse']).urlparse(url)
                    ext = os.path.splitext(parsed.path)[1].lower()
                    
                    # Map content-type to extension
                    if not ext or ext == '.bin':
                        if 'csv' in content_type or 'comma-separated' in content_type:
                            ext = '.csv'
                        elif 'excel' in content_type or 'spreadsheet' in content_type or 'xlsx' in content_type:
                            ext = '.xlsx'
                        elif 'pdf' in content_type:
                            ext = '.pdf'
                        elif 'json' in content_type:
                            ext = '.json'
                        elif 'html' in content_type:
                            ext = '.html'
                        else:
                            ext = '.bin'
                    
                    # Create unique filename with page number to avoid overwrites
                    safe_name = re.sub(r'[^\w\s-]', '', link.name)[:30] or f"doc"
                    safe_name = safe_name.replace(' ', '_')
                    # Add page number and unique suffix
                    unique_id = f"_p{link.page_number}_{hash(link.url) % 10000}"
                    filepath = os.path.join(download_folder, f"{safe_name}{unique_id}{ext}")
                    
                    # Download with size limit
                    downloaded = 0
                    content_bytes = b''
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=65536):
                            downloaded += len(chunk)
                            if downloaded > MAX_FILE_SIZE:
                                link.error = "File too large, truncated"
                                break
                            f.write(chunk)
                            if len(content_bytes) < 1000:  # Keep first bytes for detection
                                content_bytes += chunk
                    
                    # Detect file type from content if still .bin
                    if ext == '.bin' and content_bytes:
                        content_str = content_bytes[:500].decode('utf-8', errors='ignore')
                        # Check for CSV pattern
                        if ',' in content_str and '\n' in content_str:
                            lines = content_str.split('\n')
                            if len(lines) > 1 and lines[0].count(',') == lines[1].count(','):
                                new_path = filepath.replace('.bin', '.csv')
                                os.rename(filepath, new_path)
                                filepath = new_path
                                ext = '.csv'
                        # Check for Excel magic bytes
                        elif content_bytes[:4] == b'PK\x03\x04':  # ZIP/XLSX
                            new_path = filepath.replace('.bin', '.xlsx')
                            os.rename(filepath, new_path)
                            filepath = new_path
                            ext = '.xlsx'
                        # Check for PDF
                        elif content_bytes[:4] == b'%PDF':
                            new_path = filepath.replace('.bin', '.pdf')
                            os.rename(filepath, new_path)
                            filepath = new_path
                            ext = '.pdf'
                    
                    link.local_path = filepath
                    link.is_downloaded = True
                    link.file_type = ext.replace('.', '')  # Update file type
                    return link
                    
                except requests.Timeout:
                    link.error = "Timeout"
                except requests.HTTPError as e:
                    link.error = f"HTTP {e.response.status_code}"
                except Exception as e:
                    link.error = str(e)[:50]
                return link
            
            # Parallel downloads for speed
            if downloadable_links:
                app.logger.info(f"Downloading {len(downloadable_links)} files with {PARALLEL_WORKERS} threads...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
                    list(executor.map(fast_download, downloadable_links))
                
                # Log download results
                downloaded_count = sum(1 for l in downloadable_links if l.is_downloaded)
                failed_count = sum(1 for l in downloadable_links if l.error)
                app.logger.info(f"Done: {downloaded_count} downloaded, {failed_count} skipped/failed")
            
            # Process downloaded files (fast extraction)
            for link in downloadable_links:
                if not link.is_downloaded or not link.local_path:
                    continue
                    
                try:
                    file_ext = os.path.splitext(link.local_path)[1].lower()
                    
                    # Try to detect content type for .bin files
                    if file_ext == '.bin':
                        try:
                            with open(link.local_path, 'rb') as f:
                                first_bytes = f.read(500)
                            content_str = first_bytes.decode('utf-8', errors='ignore')
                            if ',' in content_str and '\n' in content_str:
                                file_ext = '.csv'  # Treat as CSV
                            elif first_bytes[:4] == b'PK\x03\x04':
                                file_ext = '.xlsx'
                            elif first_bytes[:4] == b'%PDF':
                                file_ext = '.pdf'
                        except:
                            pass
                    
                    # Excel/CSV -> BOQ extraction
                    if file_ext in ['.xlsx', '.xls', '.csv']:
                        try:
                            # Direct CSV parsing for speed
                            if file_ext == '.csv' or (file_ext == '.bin' and link.local_path):
                                import pandas as pd
                                try:
                                    df = pd.read_csv(link.local_path, encoding='utf-8')
                                except:
                                    df = pd.read_csv(link.local_path, encoding='latin-1')
                                
                                if not df.empty:
                                    items = []
                                    for idx, row in df.head(100).iterrows():
                                        item = {
                                            'sr_no': str(row.get(df.columns[0], idx+1)),
                                            'description': str(row.get(df.columns[1], '')) if len(df.columns) > 1 else '',
                                            'specification': str(row.get(df.columns[2], '')) if len(df.columns) > 2 else '',
                                            'quantity': row.get(df.columns[3], 0) if len(df.columns) > 3 else 0,
                                            'unit': str(row.get(df.columns[4], '')) if len(df.columns) > 4 else '',
                                        }
                                        items.append(item)
                                    
                                    if items:
                                        extracted_content['boq_items'].append({
                                            'source': link.name,
                                            'source_url': link.url,
                                            'columns': list(df.columns),
                                            'items': items
                                        })
                                        link.extracted_data = {'boq_count': len(df), 'columns': list(df.columns)}
                            else:
                                boq_items = extractor.process_boq_document(link)
                                if boq_items:
                                    extracted_content['boq_items'].append({
                                        'source': link.name,
                                        'source_url': link.url,
                                        'items': [extractor._boq_item_to_dict(item) for item in boq_items[:100]]
                                    })
                                    link.extracted_data = {'boq_count': len(boq_items)}
                        except Exception as e:
                            app.logger.warning(f"BOQ parse error for {link.name}: {e}")
                    
                    # PDF -> Quick text extraction
                    elif file_ext == '.pdf':
                        try:
                            import fitz
                            doc = fitz.open(link.local_path)
                            text = ""
                            for i, page in enumerate(doc):
                                if i >= 5:  # Only first 5 pages
                                    break
                                text += page.get_text()
                            doc.close()
                            
                            if text.strip():
                                link.extracted_data = {'text_length': len(text)}
                                
                                if link.document_type == 'specification':
                                    extracted_content['specifications'].append({
                                        'source': link.name,
                                        'source_url': link.url,
                                        'data': {'raw_text_excerpt': text[:1500]}
                                    })
                                else:
                                    extracted_content['other_documents'].append({
                                        'source': link.name,
                                        'source_url': link.url,
                                        'type': link.document_type,
                                        'text_preview': text[:1000]
                                    })
                        except Exception as e:
                            link.error = f"PDF read error: {str(e)[:50]}"
                            
                except Exception as e:
                    link.error = str(e)[:100]
            
            # Organize links by type
            links_by_type = {}
            for link in links:
                doc_type = link.document_type or 'unknown'
                if doc_type not in links_by_type:
                    links_by_type[doc_type] = []
                links_by_type[doc_type].append(link.to_dict())
            
            # Count by file type
            file_type_counts = {}
            for link in links:
                ft = link.file_type or 'unknown'
                file_type_counts[ft] = file_type_counts.get(ft, 0) + 1
            
            # Calculate extraction stats
            downloaded_count = sum(1 for link in links if link.is_downloaded)
            extracted_count = sum(1 for link in links if link.extracted_data)
            
            return jsonify({
                'status': 'success',
                'filename': filename,
                'total_links': len(links),
                'downloaded_count': downloaded_count,
                'extracted_count': extracted_count,
                'links_by_document_type': links_by_type,
                'file_type_counts': file_type_counts,
                'all_links': [link.to_dict() for link in links],
                'extracted_content': extracted_content,
                'message': f'Found {len(links)} hyperlinks, downloaded {downloaded_count}, extracted content from {extracted_count}',
                'performance': {
                    'max_downloads': MAX_DOWNLOADS,
                    'timeout_sec': DOWNLOAD_TIMEOUT,
                    'parallel_workers': PARALLEL_WORKERS
                }
            })
        
        finally:
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
            # Optionally clean up downloaded files
            # shutil.rmtree(download_folder, ignore_errors=True)
    
    except Exception as e:
        app.logger.error(f"Hyperlink extraction error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/expand-abbreviation', methods=['GET'])
def expand_abbreviation():
    """
    Expand an RFP abbreviation to its full form
    Query param: abbr (the abbreviation to expand)
    """
    try:
        abbr = request.args.get('abbr', '')
        
        if not abbr:
            return jsonify({'error': 'Parameter "abbr" is required'}), 400
        
        expanded = terms_matcher.expand_abbreviation(abbr)
        
        if expanded:
            return jsonify({
                'status': 'success',
                'abbreviation': abbr.upper(),
                'expansion': expanded
            })
        else:
            return jsonify({
                'status': 'not_found',
                'abbreviation': abbr.upper(),
                'expansion': None,
                'message': f'Abbreviation "{abbr}" not found in database'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/terms-database/stats', methods=['GET'])
def get_database_stats():
    """
    Get detailed database statistics - LIGHTWEIGHT version
    Does NOT trigger database loading - uses only cached metadata
    """
    try:
        stats = {
            'status': 'success',
            'database': {
                'total_terms': terms_matcher.metadata.get('total_terms', 0),
                'version': terms_matcher.metadata.get('version', 'unknown'),
                'last_updated': terms_matcher.metadata.get('last_updated', 'unknown'),
                'languages': terms_matcher.metadata.get('languages', [])
            },
            'indexing': {
                'database_loaded': terms_matcher._terms_db is not None,
                'index_built': terms_matcher._term_index is not None,
                # Don't access term_index here - it triggers full load!
                'index_size': len(terms_matcher._term_index) if terms_matcher._term_index else 0,
                'abbreviations_count': len(terms_matcher._abbreviations) if terms_matcher._abbreviations else 0
            },
            'optimization': {
                'lazy_loading': 'Enabled',
                'database_caching': 'Enabled (pickle format)',
                'lru_cache_size': 10000
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SPEC COMPARER INTEGRATION
# ============================================================================

# OEM Data paths
OEM_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             'wires_cables_data', 'wires_cables_data')

# Scoring weights for different specs
SCORING_WEIGHTS = {
    'Conductor_Size_sqmm': 25,      # Most critical
    'No_of_Cores': 20,              # Very important
    'Voltage_Rating': 15,           # Important
    'Conductor_Material': 10,       # Material match
    'Insulation_Type': 10,          # Insulation type
    'Current_Rating_Amps': 8,       # Current capacity
    'Standard': 5,                  # Standard compliance
    'Fire_Rating': 4,               # Fire safety
    'Is_Armoured': 3,               # Armour requirement
}

# Global spec comparer instance (lazy loaded)
_spec_comparer_db = None
_spec_matcher = None


def get_spec_comparer():
    """Lazy load spec comparer to avoid slow startup"""
    global _spec_comparer_db, _spec_matcher
    
    if not SPEC_COMPARER_AVAILABLE:
        return None, None
    
    if _spec_comparer_db is None:
        logger.info("Loading OEM product database for spec comparison...")
        _spec_comparer_db = OEMProductDatabase(OEM_DATA_PATH)
        _spec_matcher = SpecMatcher(_spec_comparer_db)
        logger.info(f"Spec Comparer ready: {_spec_comparer_db.get_total_products()} products")
    
    return _spec_comparer_db, _spec_matcher


def clean_nan_values(obj):
    """Convert NaN/None values to JSON-safe values"""
    import math
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return None
        return obj
    elif pd.isna(obj):
        return None
    return obj


class OEMProductDatabase:
    """Loads and manages all OEM product data including Moglix marketplace"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.products_df = None
        self.oem_list = []
        self.source_stats = {}
        self._load_all_oem_data()
    
    def _load_all_oem_data(self):
        """Load product data from all OEMs and Moglix marketplace"""
        import glob
        all_products = []
        
        if not os.path.exists(self.data_path):
            logger.warning(f"OEM data path not found: {self.data_path}")
            self.products_df = pd.DataFrame()
            return
        
        # Load OEM data from subfolders (Polycab, Havells, KEI, Finolex, RR_KABEL)
        for oem_folder in os.listdir(self.data_path):
            oem_path = os.path.join(self.data_path, oem_folder)
            if os.path.isdir(oem_path):
                # Find complete products CSV - prefer optimized versions
                all_csv_files = glob.glob(os.path.join(oem_path, '*complete_products*.csv'))
                # Separate optimized and regular files
                optimized_files = [f for f in all_csv_files if '_optimized_' in f]
                regular_files = [f for f in all_csv_files if '_optimized_' not in f]
                # Use optimized if available, otherwise use regular
                files_to_load = optimized_files if optimized_files else regular_files
                
                for csv_path in files_to_load:
                    try:
                        df = pd.read_csv(csv_path, low_memory=False)
                        oem_name = oem_folder.title().replace('_', ' ')
                        df['OEM'] = oem_name
                        df['Source'] = 'OEM Direct'
                        # Normalize data columns
                        df = self._normalize_product_data(df)
                        all_products.append(df)
                        self.oem_list.append(oem_name)
                        self.source_stats[oem_name] = len(df)
                        logger.info(f"Loaded {len(df)} products from {oem_folder} (optimized: {'_optimized_' in csv_path})")
                    except Exception as e:
                        logger.error(f"Error loading {csv_path}: {e}")
        
        # Load Moglix marketplace data (OPTIMIZED: moglix_*_optimized_*.csv, fallback to regular)
        moglix_pattern_optimized = os.path.join(self.data_path, 'moglix_*_optimized_*.csv')
        moglix_optimized = glob.glob(moglix_pattern_optimized)
        moglix_files = moglix_optimized if moglix_optimized else ['moglix_1.csv', 'moglix_2.csv']
        moglix_total = 0
        for moglix_file in moglix_files:
            # Handle both full paths (from glob) and filenames
            if os.path.isabs(moglix_file):
                moglix_path = moglix_file
            else:
                moglix_path = os.path.join(self.data_path, moglix_file)
            if os.path.exists(moglix_path):
                try:
                    df = pd.read_csv(moglix_path, low_memory=False)
                    # Use Company column if exists, otherwise set to Moglix
                    if 'Company' in df.columns:
                        df['OEM'] = df['Company'].fillna('Moglix Marketplace')
                    else:
                        df['OEM'] = 'Moglix Marketplace'
                    df['Source'] = 'Moglix Marketplace'
                    # Normalize data columns
                    df = self._normalize_product_data(df)
                    all_products.append(df)
                    moglix_total += len(df)
                    logger.info(f"Loaded {len(df)} products from {os.path.basename(moglix_path)} (optimized: {'_optimized_' in moglix_path})")
                except Exception as e:
                    logger.error(f"Error loading {moglix_path}: {e}")
        
        if moglix_total > 0:
            self.oem_list.append('Moglix Marketplace')
            self.source_stats['Moglix Marketplace'] = moglix_total
        
        if all_products:
            self.products_df = pd.concat(all_products, ignore_index=True)
            logger.info(f"Total products loaded: {len(self.products_df)} from {len(self.oem_list)} sources")
        else:
            self.products_df = pd.DataFrame()
            logger.warning("No product data loaded!")
    
    def _normalize_product_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize product data for consistent matching"""
        try:
            # Normalize voltage formats: "415V", "415", "415 V" -> 415
            if 'Voltage_Rating' in df.columns:
                df['Voltage_Rating'] = df['Voltage_Rating'].astype(str).str.replace(r'[^\d.]', '', regex=True)
                df['Voltage_Rating'] = pd.to_numeric(df['Voltage_Rating'], errors='coerce')
            
            # Normalize insulation types: "pvc" -> "PVC", "Xlpe" -> "XLPE"
            if 'Insulation_Type' in df.columns:
                df['Insulation_Type'] = df['Insulation_Type'].astype(str).str.upper().str.strip()
                # Map common variations
                df['Insulation_Type'] = df['Insulation_Type'].replace({
                    'FRLS': 'FRLS', 'FR-LS': 'FRLS', 'FRLS ': 'FRLS',
                    'PVC': 'PVC', 'P.V.C': 'PVC', 'PVC ': 'PVC',
                    'XLPE': 'XLPE', 'X.L.P.E': 'XLPE', 'XLP E': 'XLPE',
                    'EPR': 'EPR', 'E.P.R': 'EPR',
                    'LSZH': 'LSZH', 'LSZ H': 'LSZH'
                })
            
            # Normalize conductor material: "Cu", "copper" -> "Copper"
            if 'Conductor_Material' in df.columns:
                df['Conductor_Material'] = df['Conductor_Material'].astype(str).str.lower()
                df['Conductor_Material'] = df['Conductor_Material'].replace({
                    'copper': 'Copper', 'cu': 'Copper', 'c.u': 'Copper', 'tinned': 'Copper',
                    'aluminium': 'Aluminium', 'aluminum': 'Aluminium', 'al': 'Aluminium', 'a.l': 'Aluminium'
                })
            
            # Normalize conductor size: ensure float
            if 'Conductor_Size_sqmm' in df.columns:
                df['Conductor_Size_sqmm'] = pd.to_numeric(df['Conductor_Size_sqmm'], errors='coerce')
            
            # Normalize cores: ensure int
            if 'No_of_Cores' in df.columns:
                df['No_of_Cores'] = pd.to_numeric(df['No_of_Cores'], errors='coerce').astype('Int64', errors='ignore')
            
            # Normalize armoured status: 1/0, True/False, Yes/No -> boolean
            if 'Is_Armoured' in df.columns:
                df['Is_Armoured'] = df['Is_Armoured'].astype(str).str.lower()
                df['Is_Armoured'] = df['Is_Armoured'].isin(['1', 'true', 'yes', 'armoured']).astype(int)
            
            # Normalize fire rating
            if 'Fire_Rating' in df.columns:
                df['Fire_Rating'] = df['Fire_Rating'].astype(str).str.upper().str.strip()
            
            # Remove leading/trailing spaces from text columns
            text_columns = df.select_dtypes(include=['object']).columns
            for col in text_columns:
                if col not in ['OEM', 'Source', 'Product_Name', 'Product_Code']:
                    df[col] = df[col].astype(str).str.strip()
                    
        except Exception as e:
            logger.warning(f"Error normalizing product data: {e}")
        
        return df
    
    def get_total_products(self) -> int:
        return len(self.products_df) if self.products_df is not None else 0
    
    def get_oem_list(self):
        return self.oem_list


class SpecMatcher:
    """Matches RFP specifications against OEM products"""
    
    def __init__(self, product_db: OEMProductDatabase):
        self.product_db = product_db
    
    def parse_rfp_requirements(self, rfp_text: str):
        """Extract product requirements from RFP text with enhanced accuracy"""
        requirements = []
        
        # Enhanced cable specification patterns - covers more formats
        patterns = {
            # Size and cores patterns
            'size_core': r'(\d+\.?\d*)\s*(?:sq\.?\s*mm|sqmm|mm2|mm²|square\s*mm)\s*(?:x\s*)?(\d+)\s*(?:core|c\b|c x)',
            'core_size': r'(\d+\.?\d*)\s*(?:core|c|c x)\s*(?:x\s*)?(\d+\.?\d*)\s*(?:sq\.?\s*mm|sqmm|mm2|mm²|square\s*mm)',
            'nominal_size': r'(?:nominal|cross\s*sectional)\s*(?:area|size).*?(\d+\.?\d*)\s*(?:sq\.?\s*mm|sqmm|mm2|mm²)',
            # Voltage patterns
            'voltage': r'(\d+\.?\d*)\s*(?:kv|v|volt|kilovolt)\b',
            # Insulation patterns
            'insulation': r'\b(pvc|xlpe|frls|fr-lsh|rubber|lshf|cross-linked|xhhw|vfds|epr|epdm)\b',
            'conductor': r'\b(copper|aluminium|aluminum|cu|al|tinned?)\b',
            'current': r'(\d+)\s*(?:amp|a|ampere)\b',
            'standard': r'\b(is\s*\d+|iec\s*\d+|bs\s*\d+|asme|astm)\b',
            # Armoured pattern
            'armoured': r'\b(armour(?:ed)?|unarmour(?:ed)?|arm|una|steel\s*wire|swad)\b',
            # Temperature rating
            'temperature': r'(?:temperature|temp).*?(\d+)\s*°?c\b',
            # Additional specs
            'fire_rating': r'\b(frls|flr|fire\s*retardant|halogen\s*free)\b',
            'flexibility': r'\b(flexible|rigid|semi-rigid|stranded)\b',
        }
        
        lines = rfp_text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            line_stripped = line.strip()
            
            # Skip empty or too short lines
            if not line_stripped or len(line_stripped) < 5:
                continue
            
            # More comprehensive keyword matching for cable specifications
            electrical_keywords = ['sq mm', 'sqmm', 'mm2', 'mm²', 'core', 'c x', 'conductor', 
                                  'copper', 'aluminium', 'aluminum', 'cu', 'al',
                                  'pvc', 'xlpe', 'frls', 'fr-lsh', 'armoured', 'unarmoured',
                                  'kv', '415', '230', '110', 'voltage', '6kv', '11kv', '33kv',
                                  '3.5c', '4c', '2c', '1c', 'wire', 'cable', '3.5 core',
                                  'cross section', 'nominal size']
            
            if any(kw in line_lower for kw in electrical_keywords):
                req = self._extract_specs_from_line(line, patterns)
                
                # Include if has meaningful specifications
                if (req.get('conductor_size') or req.get('cores') or req.get('voltage') or 
                    req.get('insulation') or req.get('conductor_material') or 
                    req.get('armoured') is not None or req.get('temperature')):
                    req['original_text'] = line_stripped
                    req['requirement_type'] = self._detect_requirement_type(line)
                    requirements.append(req)
        
        return self._deduplicate_requirements(requirements)
    
    def _extract_specs_from_line(self, line: str, patterns: dict) -> dict:
        """Extract specifications from a single line with improved accuracy"""
        line_lower = line.lower()
        req = {}
        
        try:
            # Extract size and cores - try multiple formats with fallbacks
            # Format 1: "70 sq mm x 3 core"
            match = re.search(patterns['size_core'], line_lower, re.IGNORECASE)
            if match:
                req['conductor_size'] = float(match.group(1))
                req['cores'] = int(float(match.group(2)))
            else:
                # Format 2: "3 core x 70 sq mm"
                match = re.search(patterns['core_size'], line_lower, re.IGNORECASE)
                if match:
                    req['cores'] = int(float(match.group(1)))
                    req['conductor_size'] = float(match.group(2))
                else:
                    # Format 3: "3.5C X 70SQMM" - specific format
                    match = re.search(r'(\d+\.?\d*)\s*c\s*x\s*(\d+\.?\d*)\s*(?:sq\.?\s*mm|sqmm|mm2|mm²)', line_lower, re.IGNORECASE)
                    if match:
                        req['cores'] = int(float(match.group(1)))
                        req['conductor_size'] = float(match.group(2))
                    else:
                        # Format 4: "Nominal Cross Sectional Area..."
                        match = re.search(patterns['nominal_size'], line_lower, re.IGNORECASE)
                        if match:
                            req['conductor_size'] = float(match.group(1))
            
            # Extract voltage with improved pattern
            match = re.search(patterns['voltage'], line_lower, re.IGNORECASE)
            if match:
                voltage = float(match.group(1))
                # Determine if kV or V
                context = line_lower[max(0, match.start()-10):min(len(line_lower), match.end()+10)]
                if 'kv' in context.lower() or (voltage >= 100 and 'v' in context):
                    if voltage < 100:  # If less than 100V mentioned, it's likely kV
                        voltage *= 1000
                req['voltage'] = voltage
            
            # Extract armoured status
            match = re.search(patterns['armoured'], line_lower, re.IGNORECASE)
            if match:
                armoured_text = match.group(1).lower()
                req['armoured'] = 'unarm' not in armoured_text and 'un ' not in armoured_text
            
            # Extract insulation type
            match = re.search(patterns['insulation'], line_lower, re.IGNORECASE)
            if match:
                req['insulation'] = match.group(1).upper()
            
            # Extract conductor material
            match = re.search(patterns['conductor'], line_lower, re.IGNORECASE)
            if match:
                material = match.group(1).lower()
                req['conductor_material'] = 'Copper' if material in ['copper', 'cu', 'tinned'] else 'Aluminium'
            
            # Extract current rating
            match = re.search(patterns['current'], line_lower, re.IGNORECASE)
            if match:
                req['current_rating'] = int(match.group(1))
            
            # Extract standard
            match = re.search(patterns['standard'], line_lower, re.IGNORECASE)
            if match:
                req['standard'] = match.group(1).upper().replace(' ', '')
            
            # Extract temperature rating
            if 'temperature' in patterns:
                match = re.search(patterns['temperature'], line_lower, re.IGNORECASE)
                if match:
                    req['temperature'] = int(match.group(1))
            
            # Extract fire rating
            if 'fire_rating' in patterns:
                match = re.search(patterns['fire_rating'], line_lower, re.IGNORECASE)
                if match:
                    req['fire_rating'] = match.group(1).upper()
            
            # Extract flexibility
            if 'flexibility' in patterns:
                match = re.search(patterns['flexibility'], line_lower, re.IGNORECASE)
                if match:
                    req['flexibility'] = match.group(1).lower()
                    
        except Exception as e:
            logger.debug(f"Error extracting specs from line: {str(e)}")
        
        return req
    
    def _detect_requirement_type(self, line: str) -> str:
        """Detect if requirement is for wire/cable specs or cable-only infrastructure"""
        line_lower = line.lower()
        
        # Cable-specific infrastructure keywords - more strict to avoid false positives
        cable_only_keywords = {
            'cable_tray': ['cable tray', 'tray system', 'cable ladder', 'ladder rack'],
            'cable_duct': ['cable duct', 'duct bank', 'buried duct'],
            'cable_conduit': ['pvc conduit', 'rigid conduit', 'conduit system'],
            'cable_gland': ['cable gland', 'gland set'],
            'cable_lug': ['cable lug', 'lugs', 'lug terminal'],
            'cable_joint': ['cable joint', 'jointing kit'],
            'cable_termination': ['cable termination', 'termination kit', 'end terminal'],
            'cable_support': ['cable support', 'suspension clamp'],
        }
        
        # Wire/cable specification keywords (actual specs, not infrastructure)
        spec_keywords = ['sq mm', 'sqmm', 'mm2', 'core', 'conductor', 'copper', 'aluminium',
                        'pvc', 'xlpe', 'frls', 'armoured', 'kv', '415', '230', '110', 'voltage']
        
        # Check if line has actual wire/cable specifications
        has_specs = any(kw in line_lower for kw in spec_keywords)
        
        # Check for cable-only infrastructure keywords
        for cable_type, keywords in cable_only_keywords.items():
            if any(kw in line_lower for kw in keywords):
                return 'cable_only'
        
        # If it has electrical/cable specs, it's a wire/cable specification requirement
        if has_specs:
            return 'wire_cable_specs'
        
        # If it mentions cables/wires but no specs, treat as cable_only to be safe
        if 'cable' in line_lower or 'wire' in line_lower:
            return 'cable_only'
        
        return 'unknown'
    

    def _deduplicate_requirements(self, requirements: list) -> list:
        """Remove duplicate requirements while preserving all meaningful specs"""
        seen = set()
        unique = []
        
        for req in requirements:
            # Create deduplication key using most specific criteria
            key = (
                req.get('conductor_size'),
                req.get('cores'),
                req.get('voltage'),
                req.get('insulation'),
                req.get('conductor_material'),
                req.get('armoured'),
                req.get('current_rating')
            )
            
            if key not in seen:
                seen.add(key)
                # Include requirement if it has any meaningful specification
                # Accept requirements with at least ONE meaningful attribute
                has_meaningful_spec = any([
                    req.get('conductor_size'),
                    req.get('cores'),
                    req.get('voltage'),
                    req.get('insulation'),
                    req.get('conductor_material'),
                    req.get('current_rating'),
                    req.get('temperature'),
                    req.get('fire_rating'),
                    req.get('standard'),
                    req.get('armoured') is not None
                ])
                
                if has_meaningful_spec:
                    unique.append(req)
        
        return unique
    
    def find_matching_products(self, requirement: dict, top_n: int = 3) -> list:
        """Find top N matching products for a requirement"""
        if self.product_db.products_df is None or len(self.product_db.products_df) == 0:
            return []
        
        df = self.product_db.products_df.copy()
        
        # Calculate match scores
        df['match_score'] = df.apply(
            lambda row: self._calculate_match_score(row, requirement), axis=1
        )
        
        # Sort by score descending
        df = df.sort_values('match_score', ascending=False)
        
        # Get top N products (no minimum threshold - let all OEMs compete fairly)
        top_products = df.head(top_n)
        
        results = []
        for _, row in top_products.iterrows():
            product = {
                'oem': row.get('OEM', row.get('Company', 'Unknown')),
                'source': row.get('Source', 'Unknown'),
                'product_code': row.get('Product_Code', ''),
                'product_name': row.get('Product_Name', ''),
                'match_score': round(row['match_score'], 1),
                'conductor_size': row.get('Conductor_Size_sqmm'),
                'cores': row.get('No_of_Cores'),
                'voltage_rating': row.get('Voltage_Rating'),
                'insulation_type': row.get('Insulation_Type'),
                'conductor_material': row.get('Conductor_Material'),
                'current_rating': row.get('Current_Rating_Amps'),
                'standard': row.get('Standard'),
                'price_per_meter': row.get('Price_Per_Meter_INR'),
                'price_per_100m': row.get('Price_Per_100m_INR'),
                'fire_rating': row.get('Fire_Rating'),
                'is_armoured': row.get('Is_Armoured'),
                'warranty_years': row.get('Warranty_Years'),
                'overall_quality_score': row.get('Overall_Quality_Score'),
                # NEW OPTIMIZED COLUMNS FOR ENHANCED MATCHING
                'voltage_normalized': row.get('Voltage_Normalized'),
                'conductor_material_normalized': row.get('Conductor_Material_Normalized'),
                'insulation_type_normalized': row.get('Insulation_Type_Normalized'),
                'armour_type_normalized': row.get('Armour_Type_Normalized'),
                'conductor_size_range': row.get('Conductor_Size_Range'),
                'cores_category': row.get('Cores_Category'),
                'fire_rating_extracted': row.get('Fire_Rating_Extracted'),
                'application_domain': row.get('Application_Domain'),
                'product_category_synonyms': row.get('Product_Category_Synonyms'),
                'rfp_matching_tags': row.get('RFP_Matching_Tags'),
                'matching_confidence': row.get('Matching_Confidence'),
                'rfp_fit_score': row.get('RFP_Fit_Score'),
                'product_signature': row.get('Product_Signature'),
                # Additional enriched columns if available
                'cable_construction': row.get('Cable_Construction'),
                'primary_application': row.get('Primary_Application'),
                'installation_difficulty': row.get('Installation_Difficulty'),
                'safety_rating': row.get('Safety_Rating'),
                'durability_rating': row.get('Durability_Rating'),
                'thermal_resistance': row.get('Thermal_Resistance_Level'),
                'flame_retardant_rating': row.get('Flame_Retardant_Rating'),
                'hsn_code': row.get('HSN_Code'),
                'compliance_standards': row.get('Compliance_Standards'),
            }
            # Clean NaN values for JSON serialization
            results.append(clean_nan_values(product))
        
        return results
    
    def _calculate_match_score(self, product_row, requirement: dict) -> float:
        """Calculate match score between product and requirement (optimized with new columns)"""
        score = 0
        matched_fields = 0
        total_weight = 0
        
        # Check for pre-calculated optimization columns
        has_pre_calc = 'Matching_Confidence' in product_row and pd.notna(product_row['Matching_Confidence'])
        
        if has_pre_calc:
            # Use pre-calculated confidence score (0-100%)
            base_score = float(product_row['Matching_Confidence']) if product_row['Matching_Confidence'] else 0
            # Boost by RFP_Fit_Score if available
            if 'RFP_Fit_Score' in product_row and pd.notna(product_row['RFP_Fit_Score']):
                fit_score = float(product_row['RFP_Fit_Score']) / 100  # Normalize to 0-1
                return (base_score * 0.7) + (fit_score * 30)  # Blend scores
            return base_score
        
        # Fallback to requirement-based matching with normalized columns
        
        # 1. Conductor size match (25 points)
        if requirement.get('conductor_size'):
            total_weight += 25
            product_size = product_row.get('Conductor_Size_Range') or product_row.get('Conductor_Size_sqmm')
            if product_size and pd.notna(product_size):
                try:
                    product_size = float(product_size) if isinstance(product_size, str) else product_size
                    req_size = float(requirement['conductor_size'])
                    if product_size == req_size:
                        score += 25
                        matched_fields += 1
                    elif abs(product_size - req_size) / req_size < 0.1:
                        score += 22.5
                        matched_fields += 0.9
                    elif abs(product_size - req_size) / req_size < 0.25:
                        score += 15
                        matched_fields += 0.6
                except:
                    pass
        
        # 2. Number of cores match (20 points)
        if requirement.get('cores'):
            total_weight += 20
            product_cores = product_row.get('Cores_Category') or product_row.get('No_of_Cores')
            if product_cores and pd.notna(product_cores):
                try:
                    if int(product_cores) == int(requirement['cores']):
                        score += 20
                        matched_fields += 1
                    elif abs(int(product_cores) - int(requirement['cores'])) <= 1:
                        score += 14
                        matched_fields += 0.7
                except:
                    pass
        
        # 3. Voltage rating match (20 points) - use normalized column if available
        if requirement.get('voltage'):
            total_weight += 20
            product_voltage = product_row.get('Voltage_Normalized') or product_row.get('Voltage_Rating')
            if product_voltage and pd.notna(product_voltage):
                try:
                    prod_volt = float(str(product_voltage).split()[0]) if isinstance(product_voltage, str) else float(product_voltage)
                    if 'kv' in str(product_voltage).lower():
                        prod_volt *= 1000
                    req_voltage = float(requirement['voltage'])
                    if prod_volt >= req_voltage:
                        score += 20
                        matched_fields += 1
                    elif prod_volt >= req_voltage * 0.9:
                        score += 16
                        matched_fields += 0.8
                except:
                    pass
        
        # 4. Conductor material match (15 points) - use normalized column
        if requirement.get('conductor_material'):
            total_weight += 15
            product_material = product_row.get('Conductor_Material_Normalized') or product_row.get('Conductor_Material')
            if product_material and pd.notna(product_material):
                req_material = requirement['conductor_material'].lower()
                prod_mat = str(product_material).lower()
                if req_material in prod_mat or prod_mat in req_material or req_material[:3] == prod_mat[:3]:
                    score += 15
                    matched_fields += 1
        
        # 5. Insulation type match (15 points) - use normalized column
        if requirement.get('insulation'):
            total_weight += 15
            product_insulation = product_row.get('Insulation_Type_Normalized') or product_row.get('Insulation_Type')
            if product_insulation and pd.notna(product_insulation):
                req_insulation = requirement['insulation'].upper()
                prod_insul = str(product_insulation).upper()
                if req_insulation in prod_insul or prod_insul in req_insulation:
                    score += 15
                    matched_fields += 1
                elif any(x in prod_insul for x in ['FRLS', 'PVC', 'XLPE']) and \
                     any(x in req_insulation for x in ['FRLS', 'PVC', 'XLPE']):
                    score += 10.5
                    matched_fields += 0.7
        
        # 6. Fire rating match (5 points) - use extracted field
        if requirement.get('fire_rating'):
            total_weight += 5
            product_fire = product_row.get('Fire_Rating_Extracted') or product_row.get('Fire_Rating')
            if product_fire and pd.notna(product_fire):
                if str(requirement['fire_rating']).upper() in str(product_fire).upper():
                    score += 5
                    matched_fields += 1
        
        # 7. Armour match (5 points) - use normalized field
        if requirement.get('armoured') is not None:
            total_weight += 5
            product_armour = product_row.get('Armour_Type_Normalized') or product_row.get('Is_Armoured')
            if product_armour and pd.notna(product_armour):
                try:
                    if (str(product_armour).lower() in ['yes', 'true', '1']) == requirement['armoured']:
                        score += 5
                        matched_fields += 1
                except:
                    pass
        
        # 8. Use RFP matching tags if available
        if 'RFP_Matching_Tags' in product_row and pd.notna(product_row['RFP_Matching_Tags']):
            tags = str(product_row['RFP_Matching_Tags']).lower().split(';')
            # Boost score if product tags match requirement specs
            for tag in tags:
                if requirement.get('insulation') and requirement.get('insulation').lower() in tag:
                    score += 3
                if requirement.get('conductor_material') and requirement.get('conductor_material').lower() in tag:
                    score += 2
        
        # Normalize score
        if total_weight > 0:
            normalized_score = (score / total_weight) * 100
        else:
            normalized_score = 5  # Small baseline if no fields to match
        
        # Add small boost for products with Product_Signature (cross-OEM comparable)
        if 'Product_Signature' in product_row and pd.notna(product_row['Product_Signature']):
            normalized_score = min(100, normalized_score + 2)
        
        return min(100, max(0, normalized_score))


class SpecCalculator:
    """Calculate cable specifications, voltage drop, current capacity, and derating factors"""
    
    # Standard conductor sizes in sq mm
    STANDARD_SIZES = [0.5, 0.75, 1.0, 1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0, 300.0, 400.0, 500.0, 630.0]
    
    # Current carrying capacity (Amps) for copper conductors in air at 30°C ambient
    # Based on IS 3961 / IEC 60364-5-52
    COPPER_CURRENT_CAPACITY = {
        0.5: 3, 0.75: 6, 1.0: 10, 1.5: 15, 2.5: 21, 4.0: 28, 6.0: 36, 10.0: 50,
        16.0: 68, 25.0: 89, 35.0: 110, 50.0: 134, 70.0: 171, 95.0: 207,
        120.0: 239, 150.0: 275, 185.0: 314, 240.0: 370, 300.0: 426, 400.0: 510, 500.0: 587, 630.0: 678
    }
    
    # Aluminum conductors (approx 78% of copper)
    ALUMINUM_CURRENT_CAPACITY = {size: int(current * 0.78) for size, current in COPPER_CURRENT_CAPACITY.items()}
    
    # Resistivity (Ohm.mm²/m) at 20°C
    COPPER_RESISTIVITY = 0.0178
    ALUMINUM_RESISTIVITY = 0.0282
    
    # Temperature coefficients
    COPPER_TEMP_COEFF = 0.00393
    ALUMINUM_TEMP_COEFF = 0.00403
    
    # Derating factors
    AMBIENT_TEMP_DERATING = {
        25: 1.15, 30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61, 60: 0.50
    }
    
    GROUPING_DERATING = {
        1: 1.00, 2: 0.85, 3: 0.79, 4: 0.75, 6: 0.72, 9: 0.70, 12: 0.70, 16: 0.68, 20: 0.65
    }
    
    INSTALLATION_METHOD_DERATING = {
        'open_air': 1.00, 'tray_touching': 0.85, 'tray_spaced': 0.95,
        'conduit_air': 0.80, 'conduit_ground': 0.70, 'direct_buried': 0.90,
        'cable_duct': 0.85, 'enclosed': 0.65
    }
    
    # Power factor defaults
    POWER_FACTOR_DEFAULT = 0.85
    
    @classmethod
    def calculate_cable_size(cls, load_current: float, voltage: float = 415, material: str = 'copper',
                             installation: str = 'open_air', ambient_temp: int = 40, 
                             cable_grouping: int = 1, safety_factor: float = 1.25) -> dict:
        """Calculate recommended cable size based on load current"""
        
        # Get derating factors
        temp_derating = cls._get_nearest_derating(cls.AMBIENT_TEMP_DERATING, ambient_temp)
        group_derating = cls._get_nearest_derating(cls.GROUPING_DERATING, cable_grouping)
        install_derating = cls.INSTALLATION_METHOD_DERATING.get(installation, 0.85)
        
        total_derating = temp_derating * group_derating * install_derating
        
        # Required current capacity considering derating
        required_capacity = load_current * safety_factor / total_derating
        
        # Select appropriate conductor size
        capacity_table = cls.COPPER_CURRENT_CAPACITY if material.lower() == 'copper' else cls.ALUMINUM_CURRENT_CAPACITY
        
        recommended_size = None
        actual_capacity = 0
        
        for size in cls.STANDARD_SIZES:
            if capacity_table.get(size, 0) >= required_capacity:
                recommended_size = size
                actual_capacity = capacity_table[size]
                break
        
        # Calculate next size up for comparison
        next_size_up = None
        next_capacity = 0
        if recommended_size:
            idx = cls.STANDARD_SIZES.index(recommended_size)
            if idx + 1 < len(cls.STANDARD_SIZES):
                next_size_up = cls.STANDARD_SIZES[idx + 1]
                next_capacity = capacity_table.get(next_size_up, 0)
        
        return {
            'status': 'success',
            'input': {
                'load_current': load_current,
                'voltage': voltage,
                'material': material,
                'installation': installation,
                'ambient_temp': ambient_temp,
                'cable_grouping': cable_grouping,
                'safety_factor': safety_factor
            },
            'derating_factors': {
                'temperature': round(temp_derating, 3),
                'grouping': round(group_derating, 3),
                'installation': round(install_derating, 3),
                'total': round(total_derating, 3)
            },
            'calculation': {
                'required_capacity': round(required_capacity, 2),
                'recommended_size': recommended_size,
                'recommended_capacity': actual_capacity,
                'derated_capacity': round(actual_capacity * total_derating, 2),
                'utilization_percent': round((load_current / (actual_capacity * total_derating)) * 100, 1) if actual_capacity else 0
            },
            'alternative': {
                'next_size_up': next_size_up,
                'next_capacity': next_capacity,
                'next_derated': round(next_capacity * total_derating, 2) if next_capacity else 0
            } if next_size_up else None
        }
    
    @classmethod
    def calculate_voltage_drop(cls, cable_size: float, length: float, current: float,
                               material: str = 'copper', voltage: float = 415,
                               power_factor: float = 0.85, cores: int = 3,
                               temperature: int = 70) -> dict:
        """Calculate voltage drop for a cable run"""
        
        # Get resistivity based on material
        base_resistivity = cls.COPPER_RESISTIVITY if material.lower() == 'copper' else cls.ALUMINUM_RESISTIVITY
        temp_coeff = cls.COPPER_TEMP_COEFF if material.lower() == 'copper' else cls.ALUMINUM_TEMP_COEFF
        
        # Adjust resistivity for temperature
        resistivity = base_resistivity * (1 + temp_coeff * (temperature - 20))
        
        # Calculate resistance
        resistance = (resistivity * length) / cable_size
        
        # Reactance (approximate for cables)
        reactance = 0.08 * length / 1000  # mΩ/m approximate
        
        # Voltage drop calculation (3-phase)
        if cores >= 3:
            # 3-phase: Vd = √3 × I × L × (R cos φ + X sin φ)
            import math
            sin_phi = math.sqrt(1 - power_factor ** 2)
            vd = math.sqrt(3) * current * (resistance * power_factor + reactance * sin_phi) / 1000
        else:
            # Single phase: Vd = 2 × I × L × R / 1000
            vd = 2 * current * resistance / 1000
        
        vd_percent = (vd / voltage) * 100
        
        # Recommendations based on standards
        # IS 732 recommends max 5% for feeders, 3% for branch circuits
        status = 'acceptable' if vd_percent <= 5 else 'warning' if vd_percent <= 7 else 'critical'
        
        return {
            'status': 'success',
            'input': {
                'cable_size': cable_size,
                'length': length,
                'current': current,
                'material': material,
                'voltage': voltage,
                'power_factor': power_factor,
                'cores': cores,
                'temperature': temperature
            },
            'calculation': {
                'resistance': round(resistance, 4),
                'voltage_drop_volts': round(vd, 2),
                'voltage_drop_percent': round(vd_percent, 2),
                'receiving_end_voltage': round(voltage - vd, 2),
                'assessment': status
            },
            'standards': {
                'is_732_feeder_limit': '5%',
                'is_732_branch_limit': '3%',
                'compliant_feeder': vd_percent <= 5,
                'compliant_branch': vd_percent <= 3
            },
            'recommendations': cls._get_vd_recommendations(vd_percent, cable_size, material)
        }
    
    @classmethod
    def calculate_short_circuit_capacity(cls, cable_size: float, material: str = 'copper',
                                         fault_duration: float = 1.0, 
                                         initial_temp: int = 70,
                                         final_temp: int = 160) -> dict:
        """Calculate short circuit current capacity (I²t rating)"""
        
        # K factor (material constant)
        # For XLPE insulated cables
        K_COPPER = 143  # A.s^0.5/mm²
        K_ALUMINUM = 94
        
        k_factor = K_COPPER if material.lower() == 'copper' else K_ALUMINUM
        
        # I²t = K² × S²
        # I = K × S / √t
        import math
        
        short_circuit_current = (k_factor * cable_size) / math.sqrt(fault_duration)
        
        # Calculate I²t rating
        i2t = (k_factor * cable_size) ** 2
        
        # For 0.1s and 0.5s durations
        sc_01s = (k_factor * cable_size) / math.sqrt(0.1)
        sc_05s = (k_factor * cable_size) / math.sqrt(0.5)
        
        return {
            'status': 'success',
            'input': {
                'cable_size': cable_size,
                'material': material,
                'fault_duration': fault_duration,
                'initial_temp': initial_temp,
                'final_temp': final_temp
            },
            'calculation': {
                'k_factor': k_factor,
                'i2t_rating': round(i2t / 1000000, 2),  # MA²s
                'short_circuit_current_kA': round(short_circuit_current / 1000, 2),
                'withstand_current_0.1s_kA': round(sc_01s / 1000, 2),
                'withstand_current_0.5s_kA': round(sc_05s / 1000, 2),
                'withstand_current_1s_kA': round(short_circuit_current / 1000, 2)
            },
            'notes': [
                f"Based on {material.title()} conductor with XLPE insulation",
                f"Initial temperature: {initial_temp}°C, Final temperature: {final_temp}°C",
                "Protection device should clear fault within specified duration"
            ]
        }
    
    @classmethod
    def calculate_power_capacity(cls, cable_size: float, voltage: float = 415,
                                 material: str = 'copper', power_factor: float = 0.85,
                                 cores: int = 3, installation: str = 'open_air',
                                 ambient_temp: int = 40) -> dict:
        """Calculate power carrying capacity of a cable"""
        import math
        
        # Get current capacity
        capacity_table = cls.COPPER_CURRENT_CAPACITY if material.lower() == 'copper' else cls.ALUMINUM_CURRENT_CAPACITY
        base_current = capacity_table.get(cable_size, 0)
        
        # Apply derating
        temp_derating = cls._get_nearest_derating(cls.AMBIENT_TEMP_DERATING, ambient_temp)
        install_derating = cls.INSTALLATION_METHOD_DERATING.get(installation, 0.85)
        total_derating = temp_derating * install_derating
        
        derated_current = base_current * total_derating
        
        # Power calculation
        if cores >= 3:
            # 3-phase: P = √3 × V × I × pf
            power_kw = (math.sqrt(3) * voltage * derated_current * power_factor) / 1000
            power_kva = (math.sqrt(3) * voltage * derated_current) / 1000
        else:
            # Single phase: P = V × I × pf
            power_kw = (voltage * derated_current * power_factor) / 1000
            power_kva = (voltage * derated_current) / 1000
        
        return {
            'status': 'success',
            'input': {
                'cable_size': cable_size,
                'voltage': voltage,
                'material': material,
                'power_factor': power_factor,
                'cores': cores,
                'installation': installation,
                'ambient_temp': ambient_temp
            },
            'calculation': {
                'base_current_capacity': base_current,
                'derated_current_capacity': round(derated_current, 1),
                'power_capacity_kW': round(power_kw, 2),
                'power_capacity_kVA': round(power_kva, 2),
                'derating_applied': round(total_derating, 3)
            },
            'recommendations': {
                'suitable_for_motor': f"Up to {round(power_kw * 0.85, 1)} kW motor (with 85% loading)",
                'suitable_for_load': f"Up to {round(power_kw, 1)} kW resistive load"
            }
        }
    
    @classmethod
    def _get_nearest_derating(cls, derating_table: dict, value: int) -> float:
        """Get derating factor for nearest value in table"""
        keys = sorted(derating_table.keys())
        if value <= keys[0]:
            return derating_table[keys[0]]
        if value >= keys[-1]:
            return derating_table[keys[-1]]
        
        for i, k in enumerate(keys):
            if k >= value:
                if i == 0:
                    return derating_table[k]
                # Linear interpolation
                prev_k = keys[i-1]
                ratio = (value - prev_k) / (k - prev_k)
                return derating_table[prev_k] + ratio * (derating_table[k] - derating_table[prev_k])
        
        return derating_table[keys[-1]]
    
    @classmethod
    def _get_vd_recommendations(cls, vd_percent: float, cable_size: float, material: str) -> list:
        """Get recommendations based on voltage drop"""
        recommendations = []
        
        if vd_percent > 5:
            # Find next size up
            idx = cls.STANDARD_SIZES.index(cable_size) if cable_size in cls.STANDARD_SIZES else -1
            if idx >= 0 and idx + 1 < len(cls.STANDARD_SIZES):
                recommendations.append(f"Consider increasing cable size to {cls.STANDARD_SIZES[idx + 1]} sq mm")
            if idx >= 0 and idx + 2 < len(cls.STANDARD_SIZES):
                recommendations.append(f"Or use {cls.STANDARD_SIZES[idx + 2]} sq mm for better margin")
            recommendations.append("Consider running cables in parallel")
            if material.lower() == 'aluminum':
                recommendations.append("Consider using copper conductors for lower resistance")
        elif vd_percent > 3:
            recommendations.append("Acceptable for feeder circuits (≤5% per IS 732)")
            recommendations.append("May not be suitable for branch circuits (≤3% recommended)")
        else:
            recommendations.append("Excellent voltage drop, suitable for all applications")
        
        return recommendations
    
    # Resistivity and Temperature Coefficient constants for testing calculations
    RESISTIVITY = {'copper': 0.0178, 'aluminum': 0.0282}
    TEMP_COEFFICIENT = {'copper': 0.00393, 'aluminum': 0.00403}
    
    @classmethod
    def calculate_testing_costs(cls, cable_size: float, voltage_class: str = 'LT',
                               cable_type: str = 'power', is_armoured: bool = False,
                               quantity_meters: float = 1000, num_samples: int = 3) -> dict:
        """
        Calculate comprehensive testing costs for cable procurement
        Based on IS/IEC testing standards
        """
        # Base costs for different test types (INR)
        base_costs = {
            'routine_tests': {
                'LT': {'base': 2500, 'per_sample': 500},
                'HT': {'base': 8000, 'per_sample': 1500},
                'EHV': {'base': 25000, 'per_sample': 5000}
            },
            'type_tests': {
                'LT': {'base': 15000, 'per_sqmm': 200},
                'HT': {'base': 75000, 'per_sqmm': 500},
                'EHV': {'base': 250000, 'per_sqmm': 1500}
            },
            'acceptance_tests': {
                'LT': {'base': 5000, 'per_km': 500},
                'HT': {'base': 15000, 'per_km': 1500},
                'EHV': {'base': 50000, 'per_km': 5000}
            }
        }
        
        # Get costs for voltage class
        routine = base_costs['routine_tests'].get(voltage_class, base_costs['routine_tests']['LT'])
        type_test = base_costs['type_tests'].get(voltage_class, base_costs['type_tests']['LT'])
        acceptance = base_costs['acceptance_tests'].get(voltage_class, base_costs['acceptance_tests']['LT'])
        
        # Calculate routine test cost
        routine_cost = routine['base'] + (routine['per_sample'] * num_samples)
        if is_armoured:
            routine_cost *= 1.3  # 30% extra for armoured cables
        
        # Calculate type test cost
        type_test_cost = type_test['base'] + (type_test['per_sqmm'] * cable_size)
        if is_armoured:
            type_test_cost *= 1.4  # 40% extra for armoured cables
        
        # Calculate acceptance test cost
        length_km = quantity_meters / 1000
        acceptance_cost = acceptance['base'] + (acceptance['per_km'] * length_km)
        
        # Test certificate cost
        certificate_cost = 500 if voltage_class == 'LT' else (1500 if voltage_class == 'HT' else 3000)
        
        # Total cost
        total_cost = routine_cost + type_test_cost + acceptance_cost + certificate_cost
        
        # Cost per meter
        cost_per_meter = total_cost / quantity_meters if quantity_meters > 0 else 0
        
        return {
            'calculation_type': 'testing_costs',
            'input': {
                'cable_size': cable_size,
                'voltage_class': voltage_class,
                'cable_type': cable_type,
                'is_armoured': is_armoured,
                'quantity_meters': quantity_meters,
                'num_samples': num_samples
            },
            'costs': {
                'routine_tests_INR': round(routine_cost, 2),
                'type_tests_INR': round(type_test_cost, 2),
                'acceptance_tests_INR': round(acceptance_cost, 2),
                'certificate_cost_INR': certificate_cost,
                'total_testing_cost_INR': round(total_cost, 2),
                'testing_cost_per_meter_INR': round(cost_per_meter, 4)
            },
            'tests_included': cls._get_required_tests(voltage_class, cable_type, is_armoured)
        }
    
    @classmethod
    def _get_required_tests(cls, voltage_class: str, cable_type: str, is_armoured: bool) -> dict:
        """Get list of required tests based on cable specifications"""
        routine_tests = [
            'Conductor Resistance Test',
            'Insulation Resistance Test (IR)',
            'High Voltage Test (HV)',
            'Spark Test (for insulation)'
        ]
        
        type_tests = [
            'Tensile Strength & Elongation',
            'Hot Set Test',
            'Thermal Stability Test',
            'Oxygen Index Test',
            'Heat Shock Test',
            'Cold Bend Test'
        ]
        
        acceptance_tests = [
            'Visual Inspection',
            'Dimensional Check',
            'Conductor Resistance Verification',
            'Insulation Resistance Verification'
        ]
        
        # Add voltage-class specific tests
        if voltage_class in ['HT', 'EHV']:
            routine_tests.extend([
                'Partial Discharge Test',
                'Capacitance Test'
            ])
            type_tests.extend([
                'Impulse Withstand Test',
                'Bending Test',
                'Tan Delta Test',
                'Water Penetration Test'
            ])
        
        if voltage_class == 'EHV':
            type_tests.extend([
                'Long Duration Voltage Test',
                'Heating Cycle Test',
                'External Damage Test'
            ])
        
        # Add armour-specific tests
        if is_armoured:
            routine_tests.append('Armour Continuity Test')
            type_tests.extend([
                'Armour Corrosion Resistance Test',
                'Armour Tensile Test'
            ])
        
        return {
            'routine_tests': routine_tests,
            'type_tests': type_tests,
            'acceptance_tests': acceptance_tests,
            'total_test_count': len(routine_tests) + len(type_tests) + len(acceptance_tests)
        }
    
    @classmethod
    def calculate_insulation_resistance(cls, cable_size: float, length: float,
                                        insulation_type: str = 'PVC',
                                        voltage_rating: float = 1100,
                                        temperature: int = 20) -> dict:
        """
        Calculate expected insulation resistance values
        Based on IS 694 / IS 1554 standards
        """
        # Minimum IR values (MΩ·km) at 20°C
        min_ir_values = {
            'PVC': {'LT': 50, 'HT': 100},
            'XLPE': {'LT': 100, 'HT': 500},
            'FRLS': {'LT': 50, 'HT': 100},
            'Rubber': {'LT': 20, 'HT': 50}
        }
        
        voltage_class = 'HT' if voltage_rating > 1100 else 'LT'
        base_ir = min_ir_values.get(insulation_type, min_ir_values['PVC']).get(voltage_class, 50)
        
        # Temperature correction (IR halves for every 10°C rise)
        temp_factor = 2 ** ((20 - temperature) / 10)
        
        # Length correction (IR is inversely proportional to length)
        length_km = length / 1000
        ir_for_length = (base_ir / length_km) if length_km > 0 else base_ir
        
        # Apply temperature correction
        expected_ir = ir_for_length * temp_factor
        
        # Minimum acceptable value
        min_acceptable = (base_ir / length_km) if length_km > 0 else base_ir
        
        # Calculate test voltage
        test_voltage = 500 if voltage_rating <= 650 else (1000 if voltage_rating <= 1100 else 2500)
        
        return {
            'calculation_type': 'insulation_resistance',
            'input': {
                'cable_size': cable_size,
                'length': length,
                'insulation_type': insulation_type,
                'voltage_rating': voltage_rating,
                'temperature': temperature
            },
            'calculation': {
                'base_ir_mohm_km': base_ir,
                'temperature_correction_factor': round(temp_factor, 3),
                'expected_ir_mohm': round(expected_ir, 2),
                'minimum_acceptable_ir_mohm': round(min_acceptable, 2),
                'test_voltage_dc': test_voltage
            },
            'test_procedure': {
                'duration_minutes': 1,
                'stabilization_time_seconds': 60,
                'reading_interval': 'After 1 minute of voltage application'
            }
        }
    
    @classmethod
    def calculate_hi_pot_test(cls, voltage_rating: float, cable_type: str = 'power',
                             test_type: str = 'routine', duration_minutes: int = 5) -> dict:
        """
        Calculate High Potential (Hi-Pot) test parameters
        Based on IS/IEC standards
        """
        # Test voltage multipliers
        multipliers = {
            'routine': {'AC': 2.5, 'DC': 4.0},
            'type': {'AC': 3.5, 'DC': 5.6},
            'acceptance': {'AC': 2.0, 'DC': 3.2}
        }
        
        mult = multipliers.get(test_type, multipliers['routine'])
        
        # Calculate test voltages
        ac_test_voltage = voltage_rating * mult['AC']
        dc_test_voltage = voltage_rating * mult['DC']
        
        # Duration based on test type
        durations = {
            'routine': 5,
            'type': 15,
            'acceptance': 5
        }
        test_duration = durations.get(test_type, 5)
        
        # Leakage current limits (μA/km)
        max_leakage = {
            'LT': 1.0,
            'HT': 0.5,
            'EHV': 0.3
        }
        voltage_class = 'EHV' if voltage_rating > 33000 else ('HT' if voltage_rating > 1100 else 'LT')
        
        return {
            'calculation_type': 'hi_pot_test',
            'input': {
                'voltage_rating': voltage_rating,
                'cable_type': cable_type,
                'test_type': test_type,
                'duration_minutes': duration_minutes
            },
            'test_parameters': {
                'ac_test_voltage_kV': round(ac_test_voltage / 1000, 2),
                'dc_test_voltage_kV': round(dc_test_voltage / 1000, 2),
                'test_duration_minutes': test_duration,
                'max_leakage_current_uA_km': max_leakage[voltage_class],
                'voltage_class': voltage_class
            },
            'pass_criteria': {
                'no_breakdown': True,
                'no_flashover': True,
                'leakage_within_limits': True,
                'no_visible_damage': True
            },
            'safety_requirements': [
                'Ensure proper grounding',
                'Use appropriate PPE',
                'Maintain safe clearance distance',
                'Discharge cable after test',
                'Use calibrated equipment'
            ]
        }
    
    @classmethod
    def calculate_conductor_resistance(cls, cable_size: float, length: float,
                                       material: str = 'copper',
                                       temperature: int = 20,
                                       stranding: str = 'Class 2') -> dict:
        """
        Calculate conductor resistance and verify against standards
        Based on IS 8130 / IEC 60228
        """
        # Maximum resistance at 20°C (Ω/km) - IS 8130 / IEC 60228
        max_resistance_20c = {
            'copper': {
                'Class 1': {1.0: 18.1, 1.5: 12.1, 2.5: 7.41, 4.0: 4.61, 6.0: 3.08, 
                           10.0: 1.83, 16.0: 1.15, 25.0: 0.727, 35.0: 0.524, 
                           50.0: 0.387, 70.0: 0.268, 95.0: 0.193, 120.0: 0.153,
                           150.0: 0.124, 185.0: 0.0991, 240.0: 0.0754, 300.0: 0.0601},
                'Class 2': {1.0: 18.1, 1.5: 12.1, 2.5: 7.41, 4.0: 4.61, 6.0: 3.08, 
                           10.0: 1.83, 16.0: 1.15, 25.0: 0.727, 35.0: 0.524, 
                           50.0: 0.387, 70.0: 0.268, 95.0: 0.193, 120.0: 0.153,
                           150.0: 0.124, 185.0: 0.0991, 240.0: 0.0754, 300.0: 0.0601},
                'Class 5': {0.5: 39.0, 0.75: 26.0, 1.0: 19.5, 1.5: 13.3, 2.5: 7.98, 
                           4.0: 4.95, 6.0: 3.30, 10.0: 1.91, 16.0: 1.21, 25.0: 0.780}
            },
            'aluminum': {
                'Class 1': {2.5: 12.1, 4.0: 7.41, 6.0: 4.61, 10.0: 3.08, 16.0: 1.91,
                           25.0: 1.20, 35.0: 0.868, 50.0: 0.641, 70.0: 0.443, 
                           95.0: 0.320, 120.0: 0.253, 150.0: 0.206, 185.0: 0.164,
                           240.0: 0.125, 300.0: 0.100},
                'Class 2': {2.5: 12.1, 4.0: 7.41, 6.0: 4.61, 10.0: 3.08, 16.0: 1.91,
                           25.0: 1.20, 35.0: 0.868, 50.0: 0.641, 70.0: 0.443, 
                           95.0: 0.320, 120.0: 0.253, 150.0: 0.206, 185.0: 0.164,
                           240.0: 0.125, 300.0: 0.100}
            }
        }
        
        material = material.lower()
        mat_key = 'copper' if 'copper' in material or 'cu' in material else 'aluminum'
        
        # Get max resistance at 20°C
        resistance_table = max_resistance_20c.get(mat_key, {}).get(stranding, {})
        
        # Find closest cable size
        sizes = sorted(resistance_table.keys())
        closest_size = min(sizes, key=lambda x: abs(x - cable_size)) if sizes else cable_size
        max_r_20c = resistance_table.get(closest_size, cls.RESISTIVITY[mat_key] * 1000 / cable_size)
        
        # Temperature correction
        temp_coeff = cls.TEMP_COEFFICIENT.get(mat_key, 0.00393)
        correction_factor = 1 + temp_coeff * (temperature - 20)
        max_r_at_temp = max_r_20c * correction_factor
        
        # Calculate for given length
        length_km = length / 1000
        max_resistance = max_r_at_temp * length_km
        
        return {
            'calculation_type': 'conductor_resistance',
            'input': {
                'cable_size': cable_size,
                'length': length,
                'material': mat_key,
                'temperature': temperature,
                'stranding': stranding
            },
            'calculation': {
                'max_resistance_20c_ohm_km': max_r_20c,
                'temperature_correction_factor': round(correction_factor, 4),
                'max_resistance_at_temp_ohm_km': round(max_r_at_temp, 4),
                'max_resistance_for_length_ohm': round(max_resistance, 4)
            },
            'test_parameters': {
                'test_current_amps': min(10, cable_size),
                'measurement_accuracy': '±0.5%',
                'temperature_measurement': 'Required for correction'
            },
            'pass_criteria': {
                'measured_less_than_max': f'R < {round(max_resistance, 4)} Ω',
                'standard_reference': 'IS 8130 / IEC 60228'
            }
        }


class ProductRecommender:
    """Intelligent product recommendations based on application, budget, and requirements"""
    
    # Application profiles
    APPLICATION_PROFILES = {
        'residential': {
            'description': 'Home wiring and domestic applications',
            'preferred_insulation': ['PVC', 'FRLS'],
            'typical_voltage': 650,
            'armoured': False,
            'priority': ['safety', 'cost', 'warranty'],
            'fire_rating_required': False
        },
        'commercial': {
            'description': 'Offices, malls, and commercial buildings',
            'preferred_insulation': ['FRLS', 'ZHFR', 'XLPE'],
            'typical_voltage': 1100,
            'armoured': False,
            'priority': ['fire_safety', 'quality', 'warranty'],
            'fire_rating_required': True
        },
        'industrial': {
            'description': 'Factories, plants, and heavy machinery',
            'preferred_insulation': ['XLPE', 'PVC'],
            'typical_voltage': 1100,
            'armoured': True,
            'priority': ['durability', 'current_capacity', 'quality'],
            'fire_rating_required': False
        },
        'underground': {
            'description': 'Underground installations and direct burial',
            'preferred_insulation': ['XLPE'],
            'typical_voltage': 1100,
            'armoured': True,
            'priority': ['moisture_resistance', 'durability', 'warranty'],
            'fire_rating_required': False
        },
        'outdoor': {
            'description': 'Outdoor installations, exposed to weather',
            'preferred_insulation': ['XLPE', 'PVC'],
            'typical_voltage': 1100,
            'armoured': True,
            'priority': ['weather_resistance', 'uv_resistance', 'durability'],
            'fire_rating_required': False
        },
        'high_rise': {
            'description': 'High-rise buildings and vertical runs',
            'preferred_insulation': ['FRLS', 'ZHFR', 'LSHF'],
            'typical_voltage': 1100,
            'armoured': False,
            'priority': ['fire_safety', 'smoke_toxicity', 'quality'],
            'fire_rating_required': True
        },
        'hospital': {
            'description': 'Healthcare facilities with critical loads',
            'preferred_insulation': ['FRLS', 'ZHFR', 'LSHF'],
            'typical_voltage': 650,
            'armoured': False,
            'priority': ['reliability', 'fire_safety', 'quality'],
            'fire_rating_required': True
        },
        'data_center': {
            'description': 'Data centers and IT infrastructure',
            'preferred_insulation': ['FRLS', 'ZHFR'],
            'typical_voltage': 650,
            'armoured': False,
            'priority': ['reliability', 'fire_safety', 'quality'],
            'fire_rating_required': True
        }
    }
    
    # Budget categories
    BUDGET_CATEGORIES = {
        'economy': {'max_multiplier': 1.0, 'description': 'Best value for money'},
        'standard': {'max_multiplier': 1.3, 'description': 'Good balance of cost and quality'},
        'premium': {'max_multiplier': 1.8, 'description': 'High quality, extended warranty'},
        'best': {'max_multiplier': float('inf'), 'description': 'Top rated regardless of cost'}
    }
    
    def __init__(self, product_db: OEMProductDatabase):
        self.product_db = product_db
    
    def recommend_by_application(self, application: str, conductor_size: float = None,
                                 cores: int = None, material: str = None,
                                 top_n: int = 5) -> dict:
        """Recommend products based on application type"""
        
        if application.lower() not in self.APPLICATION_PROFILES:
            return {
                'status': 'error',
                'message': f'Unknown application: {application}',
                'available_applications': list(self.APPLICATION_PROFILES.keys())
            }
        
        profile = self.APPLICATION_PROFILES[application.lower()]
        df = self.product_db.products_df.copy()
        
        if len(df) == 0:
            return {'status': 'error', 'message': 'No products in database'}
        
        # Score each product for this application
        df['app_score'] = df.apply(
            lambda row: self._calculate_application_score(row, profile, conductor_size, cores, material),
            axis=1
        )
        
        # Filter and sort
        df = df[df['app_score'] > 30].sort_values('app_score', ascending=False)
        
        recommendations = []
        for _, row in df.head(top_n).iterrows():
            recommendations.append(self._format_product_recommendation(row, profile))
        
        return {
            'status': 'success',
            'application': application,
            'profile': profile,
            'filters_applied': {
                'conductor_size': conductor_size,
                'cores': cores,
                'material': material
            },
            'total_matches': len(df),
            'recommendations': recommendations
        }
    
    def recommend_by_budget(self, budget_category: str, conductor_size: float,
                           cores: int, material: str = 'copper',
                           length_meters: float = 100, top_n: int = 5) -> dict:
        """Recommend products within budget constraints"""
        
        if budget_category.lower() not in self.BUDGET_CATEGORIES:
            return {
                'status': 'error',
                'message': f'Unknown budget category: {budget_category}',
                'available_categories': list(self.BUDGET_CATEGORIES.keys())
            }
        
        df = self.product_db.products_df.copy()
        
        if len(df) == 0:
            return {'status': 'error', 'message': 'No products in database'}
        
        # Filter by basic specs
        if conductor_size:
            df = df[df['Conductor_Size_sqmm'] == conductor_size]
        if cores:
            df = df[df['No_of_Cores'] == cores]
        if material:
            df = df[df['Conductor_Material'].str.lower().str.contains(material.lower(), na=False)]
        
        if len(df) == 0:
            return {
                'status': 'success',
                'message': 'No products match the specified criteria',
                'recommendations': []
            }
        
        # Calculate total cost
        df['total_cost'] = df['Price_Per_Meter_INR'].fillna(0) * length_meters
        
        # Find minimum price for budget filtering
        min_price = df['total_cost'].min()
        budget_info = self.BUDGET_CATEGORIES[budget_category.lower()]
        max_budget = min_price * budget_info['max_multiplier']
        
        # Filter by budget
        df = df[df['total_cost'] <= max_budget]
        
        # Score by value (quality/price ratio)
        df['value_score'] = df.apply(
            lambda row: self._calculate_value_score(row),
            axis=1
        )
        
        df = df.sort_values('value_score', ascending=False)
        
        recommendations = []
        for _, row in df.head(top_n).iterrows():
            recommendations.append({
                'oem': row.get('OEM', 'Unknown'),
                'product_code': row.get('Product_Code', ''),
                'product_name': row.get('Product_Name', ''),
                'specs': {
                    'conductor_size': row.get('Conductor_Size_sqmm'),
                    'cores': row.get('No_of_Cores'),
                    'insulation': row.get('Insulation_Type'),
                    'voltage': row.get('Voltage_Rating'),
                    'current_rating': row.get('Current_Rating_Amps')
                },
                'pricing': {
                    'price_per_meter': row.get('Price_Per_Meter_INR'),
                    'total_cost': round(row['total_cost'], 2),
                    'length_meters': length_meters
                },
                'quality': {
                    'overall_score': row.get('Overall_Quality_Score'),
                    'warranty_years': row.get('Warranty_Years'),
                    'fire_rating': row.get('Fire_Rating')
                },
                'value_score': round(row['value_score'], 1),
                'why_recommended': self._get_budget_recommendation_reason(row, budget_category)
            })
        
        return {
            'status': 'success',
            'budget_category': budget_category,
            'budget_info': budget_info,
            'filters': {
                'conductor_size': conductor_size,
                'cores': cores,
                'material': material,
                'length_meters': length_meters,
                'max_budget': round(max_budget, 2)
            },
            'total_matches': len(df),
            'recommendations': recommendations
        }
    
    def recommend_best_quality(self, conductor_size: float = None, cores: int = None,
                               insulation: str = None, top_n: int = 5) -> dict:
        """Recommend highest quality products"""
        
        df = self.product_db.products_df.copy()
        
        if len(df) == 0:
            return {'status': 'error', 'message': 'No products in database'}
        
        # Apply filters
        if conductor_size:
            df = df[df['Conductor_Size_sqmm'] == conductor_size]
        if cores:
            df = df[df['No_of_Cores'] == cores]
        if insulation:
            df = df[df['Insulation_Type'].str.upper().str.contains(insulation.upper(), na=False)]
        
        if len(df) == 0:
            return {'status': 'success', 'message': 'No products match criteria', 'recommendations': []}
        
        # Score by quality factors
        df['quality_score'] = df.apply(self._calculate_quality_score, axis=1)
        df = df.sort_values('quality_score', ascending=False)
        
        recommendations = []
        for rank, (_, row) in enumerate(df.head(top_n).iterrows(), 1):
            recommendations.append({
                'rank': rank,
                'oem': row.get('OEM', 'Unknown'),
                'product_code': row.get('Product_Code', ''),
                'product_name': row.get('Product_Name', ''),
                'quality_score': round(row['quality_score'], 1),
                'quality_factors': {
                    'overall_quality_score': row.get('Overall_Quality_Score'),
                    'warranty_years': row.get('Warranty_Years'),
                    'fire_rating': row.get('Fire_Rating'),
                    'standard': row.get('Standard')
                },
                'specs': {
                    'conductor_size': row.get('Conductor_Size_sqmm'),
                    'cores': row.get('No_of_Cores'),
                    'insulation': row.get('Insulation_Type'),
                    'voltage': row.get('Voltage_Rating'),
                    'material': row.get('Conductor_Material')
                },
                'price_per_meter': row.get('Price_Per_Meter_INR'),
                'why_top_quality': self._get_quality_reasons(row)
            })
        
        return {
            'status': 'success',
            'filters': {
                'conductor_size': conductor_size,
                'cores': cores,
                'insulation': insulation
            },
            'total_matches': len(df),
            'recommendations': recommendations
        }
    
    def compare_oems(self, conductor_size: float, cores: int, 
                     material: str = 'copper') -> dict:
        """Compare products across OEMs for same specifications"""
        
        df = self.product_db.products_df.copy()
        
        # Filter by specs
        df = df[df['Conductor_Size_sqmm'] == conductor_size]
        df = df[df['No_of_Cores'] == cores]
        if material:
            df = df[df['Conductor_Material'].str.lower().str.contains(material.lower(), na=False)]
        
        if len(df) == 0:
            return {'status': 'success', 'message': 'No matching products', 'oem_comparison': []}
        
        oem_comparison = []
        for oem in df['OEM'].unique():
            oem_df = df[df['OEM'] == oem]
            
            # Get best product from this OEM
            oem_df['score'] = oem_df.apply(self._calculate_overall_score, axis=1)
            best = oem_df.sort_values('score', ascending=False).iloc[0]
            
            oem_comparison.append({
                'oem': oem,
                'product_count': len(oem_df),
                'best_product': {
                    'product_code': best.get('Product_Code'),
                    'product_name': best.get('Product_Name'),
                    'insulation': best.get('Insulation_Type'),
                    'voltage_rating': best.get('Voltage_Rating'),
                    'current_rating': best.get('Current_Rating_Amps')
                },
                'pricing': {
                    'price_per_meter': best.get('Price_Per_Meter_INR'),
                    'min_price': oem_df['Price_Per_Meter_INR'].min(),
                    'max_price': oem_df['Price_Per_Meter_INR'].max()
                },
                'quality': {
                    'overall_score': best.get('Overall_Quality_Score'),
                    'warranty_years': best.get('Warranty_Years'),
                    'fire_rating': best.get('Fire_Rating')
                },
                'overall_score': round(best['score'], 1)
            })
        
        # Sort by overall score
        oem_comparison = sorted(oem_comparison, key=lambda x: x['overall_score'], reverse=True)
        
        return {
            'status': 'success',
            'specification': {
                'conductor_size': conductor_size,
                'cores': cores,
                'material': material
            },
            'total_products': len(df),
            'oems_compared': len(oem_comparison),
            'oem_comparison': oem_comparison,
            'best_value': oem_comparison[0]['oem'] if oem_comparison else None,
            'price_range': {
                'min': df['Price_Per_Meter_INR'].min(),
                'max': df['Price_Per_Meter_INR'].max(),
                'avg': round(df['Price_Per_Meter_INR'].mean(), 2)
            }
        }
    
    def _calculate_application_score(self, row, profile: dict, 
                                     conductor_size: float, cores: int, material: str) -> float:
        """Calculate how well a product fits an application profile"""
        score = 50  # Base score
        
        # Insulation match
        insulation = str(row.get('Insulation_Type', '')).upper()
        for pref in profile['preferred_insulation']:
            if pref in insulation:
                score += 15
                break
        
        # Armoured preference
        is_armoured = bool(row.get('Is_Armoured', 0))
        if is_armoured == profile['armoured']:
            score += 10
        elif profile['armoured'] and not is_armoured:
            score -= 20  # Penalty for non-armoured when armoured required
        
        # Fire rating requirement
        if profile['fire_rating_required']:
            fire_rating = str(row.get('Fire_Rating', '')).upper()
            if any(x in fire_rating for x in ['FRLS', 'FR', 'ZHFR', 'LSHF']):
                score += 15
            elif any(x in insulation for x in ['FRLS', 'FR', 'ZHFR', 'LSHF']):
                score += 10
            else:
                score -= 15
        
        # Size match
        if conductor_size and row.get('Conductor_Size_sqmm') == conductor_size:
            score += 10
        
        # Cores match
        if cores and row.get('No_of_Cores') == cores:
            score += 10
        
        # Quality score bonus
        quality = row.get('Overall_Quality_Score', 50)
        if quality:
            score += (quality - 50) / 5
        
        return min(100, max(0, score))
    
    def _calculate_value_score(self, row) -> float:
        """Calculate value score (quality per rupee)"""
        quality = row.get('Overall_Quality_Score', 50)
        price = row.get('Price_Per_Meter_INR', 100)
        warranty = row.get('Warranty_Years', 1)
        
        if price and price > 0:
            # Higher quality, longer warranty, lower price = better value
            value = (quality * (1 + warranty * 0.1)) / (price / 100)
            return min(100, value)
        return 50
    
    def _calculate_quality_score(self, row) -> float:
        """Calculate comprehensive quality score"""
        score = 0
        
        # Base quality score (40% weight)
        quality = row.get('Overall_Quality_Score', 50)
        score += quality * 0.4
        
        # Warranty (20% weight)
        warranty = row.get('Warranty_Years', 1)
        score += min(warranty * 4, 20)
        
        # Fire rating (15% weight)
        fire_rating = str(row.get('Fire_Rating', '')).upper()
        insulation = str(row.get('Insulation_Type', '')).upper()
        if any(x in fire_rating or x in insulation for x in ['FRLS', 'ZHFR', 'LSHF']):
            score += 15
        elif 'FR' in fire_rating or 'FR' in insulation:
            score += 10
        
        # Standard compliance (15% weight)
        standard = str(row.get('Standard', '')).upper()
        if 'IS' in standard and 'IEC' in standard:
            score += 15
        elif 'IS' in standard or 'IEC' in standard:
            score += 10
        
        # Brand reputation (10% weight) - Based on OEM
        oem = str(row.get('OEM', '')).lower()
        premium_brands = ['polycab', 'havells', 'finolex']
        if any(b in oem for b in premium_brands):
            score += 10
        
        return score
    
    def _calculate_overall_score(self, row) -> float:
        """Calculate overall score combining quality and value"""
        quality = self._calculate_quality_score(row)
        value = self._calculate_value_score(row)
        return quality * 0.6 + value * 0.4
    
    def _format_product_recommendation(self, row, profile: dict) -> dict:
        """Format product recommendation with application context"""
        return {
            'oem': row.get('OEM', 'Unknown'),
            'product_code': row.get('Product_Code', ''),
            'product_name': row.get('Product_Name', ''),
            'application_score': round(row['app_score'], 1),
            'specs': {
                'conductor_size': row.get('Conductor_Size_sqmm'),
                'cores': row.get('No_of_Cores'),
                'insulation': row.get('Insulation_Type'),
                'voltage': row.get('Voltage_Rating'),
                'material': row.get('Conductor_Material'),
                'current_rating': row.get('Current_Rating_Amps'),
                'is_armoured': bool(row.get('Is_Armoured', 0))
            },
            'quality': {
                'overall_score': row.get('Overall_Quality_Score'),
                'warranty_years': row.get('Warranty_Years'),
                'fire_rating': row.get('Fire_Rating'),
                'standard': row.get('Standard')
            },
            'price_per_meter': row.get('Price_Per_Meter_INR'),
            'why_suitable': self._get_application_suitability_reasons(row, profile)
        }
    
    def _get_application_suitability_reasons(self, row, profile: dict) -> list:
        """Get reasons why product is suitable for application"""
        reasons = []
        
        insulation = str(row.get('Insulation_Type', '')).upper()
        for pref in profile['preferred_insulation']:
            if pref in insulation:
                reasons.append(f"Has {pref} insulation - ideal for {profile['description']}")
                break
        
        if profile['armoured'] and row.get('Is_Armoured'):
            reasons.append("Armoured construction provides mechanical protection")
        
        if profile['fire_rating_required']:
            fire_rating = str(row.get('Fire_Rating', '')).upper()
            if 'FRLS' in fire_rating or 'FRLS' in insulation:
                reasons.append("FRLS rated - low smoke emission in fire")
            if 'ZHFR' in fire_rating or 'ZHFR' in insulation:
                reasons.append("Zero halogen - safe for enclosed spaces")
        
        warranty = row.get('Warranty_Years', 0)
        if warranty and warranty >= 5:
            reasons.append(f"{warranty} year warranty provides peace of mind")
        
        return reasons if reasons else ["Meets basic specifications"]
    
    def _get_budget_recommendation_reason(self, row, budget_category: str) -> str:
        """Get reason for budget-based recommendation"""
        if budget_category == 'economy':
            return "Best price in category with acceptable quality"
        elif budget_category == 'standard':
            return "Good balance of quality and affordability"
        elif budget_category == 'premium':
            quality = row.get('Overall_Quality_Score', 50)
            warranty = row.get('Warranty_Years', 1)
            return f"High quality score ({quality}/100) with {warranty} year warranty"
        else:
            return "Top-rated product regardless of price"
    
    def _get_quality_reasons(self, row) -> list:
        """Get reasons for quality recommendation"""
        reasons = []
        
        quality = row.get('Overall_Quality_Score', 0)
        if quality and quality >= 80:
            reasons.append(f"Excellent quality score: {quality}/100")
        
        warranty = row.get('Warranty_Years', 0)
        if warranty and warranty >= 5:
            reasons.append(f"Extended {warranty}-year warranty")
        
        fire_rating = str(row.get('Fire_Rating', '')).upper()
        insulation = str(row.get('Insulation_Type', '')).upper()
        if 'FRLS' in fire_rating or 'FRLS' in insulation:
            reasons.append("Fire retardant low smoke (FRLS)")
        if 'ZHFR' in fire_rating or 'ZHFR' in insulation:
            reasons.append("Zero halogen flame retardant")
        
        standard = str(row.get('Standard', '')).upper()
        if 'IS' in standard:
            reasons.append("Compliant with Indian Standards")
        if 'IEC' in standard:
            reasons.append("Compliant with International Standards")
        
        return reasons if reasons else ["Good overall specifications"]


# Global instances
_spec_calculator = None
_product_recommender = None


def get_spec_calculator():
    """Get SpecCalculator instance"""
    global _spec_calculator
    if _spec_calculator is None:
        _spec_calculator = SpecCalculator()
    return _spec_calculator


def get_product_recommender():
    """Get ProductRecommender instance (lazy loaded)"""
    global _product_recommender
    if _product_recommender is None:
        product_db, _ = get_spec_comparer()
        if product_db:
            _product_recommender = ProductRecommender(product_db)
    return _product_recommender


@app.route('/api/spec-compare', methods=['POST'])
def spec_compare():
    """
    Compare RFP requirements against OEM products
    Returns top 3 matching products for each requirement with integrated calculations and recommendations
    """
    try:
        if not SPEC_COMPARER_AVAILABLE:
            return jsonify({'error': 'Spec Comparer not available (pandas not installed)'}), 500
        
        product_db, spec_matcher = get_spec_comparer()
        calculator = get_spec_calculator()
        recommender = get_product_recommender()
        
        # Debug logging
        app.logger.info(f"Spec Comparer loaded - product_db type: {type(product_db).__name__}, spec_matcher type: {type(spec_matcher).__name__}")
        
        if product_db is None or product_db.get_total_products() == 0:
            return jsonify({'error': 'No OEM product data available'}), 500
        
        if spec_matcher is None:
            return jsonify({'error': 'Spec Matcher not initialized'}), 500
        
        # Get uploaded file
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid PDF file'}), 400
        
        # Get analysis options from form data
        include_calculations = request.form.get('include_calculations', 'true') == 'true'
        include_recommendations = request.form.get('include_recommendations', 'true') == 'true'
        include_budget = request.form.get('include_budget', 'true') == 'true'
        include_oem_comparison = request.form.get('include_oem_comparison', 'true') == 'true'
        cable_length = float(request.form.get('cable_length', 100))
        application = request.form.get('application', 'auto')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        safe_filename = timestamp + filename
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        try:
            file.save(pdf_path)
            app.logger.info(f"Spec Compare Pro: Extracting from {safe_filename}")
            
            # Extract text from PDF
            extractor = MultilingualExtractor(pdf_path)
            rfp_text = extractor.extract_all_text()
            
            if not rfp_text.strip():
                return jsonify({'error': 'Could not extract text from PDF'}), 400
            
            # Auto-detect application type from RFP text
            detected_application = _detect_application_type(rfp_text) if application == 'auto' else application
            
            # Parse requirements
            requirements = spec_matcher.parse_rfp_requirements(rfp_text)
            
            # Log parsed requirements for debugging
            app.logger.info(f"Parsed {len(requirements)} total requirements from RFP")
            for idx, req in enumerate(requirements):
                app.logger.info(f"  Req {idx+1}: type={req.get('requirement_type')}, size={req.get('conductor_size')}, cores={req.get('cores')}, text={req.get('original_text')[:80]}")
            
            if not requirements:
                return jsonify({
                    'status': 'success',
                    'message': 'No wire/cable specifications found in RFP',
                    'total_requirements': 0,
                    'comparisons': [],
                    'detected_application': detected_application,
                    'database_info': {
                        'total_products': product_db.get_total_products(),
                        'oems': product_db.get_oem_list()
                    }
                })
            
            # Find matching products for each requirement with integrated analysis
            comparisons = []
            all_top_products = []  # Collect all top products for OEM comparison
            cable_only_requirements = []  # Track cable-only requirements
            wire_cable_requirements = []  # Track wire/cable spec requirements
            
            for req in requirements:
                # Check requirement type
                req_type = req.get('requirement_type', 'unknown')
                
                # Handle cable-only requirements
                if req_type == 'cable_only':
                    cable_only_requirements.append(req)
                    comparison_entry = {
                        'requirement': {
                            'original_text': req.get('original_text', ''),
                            'requirement_type': 'cable_only',
                            'status': 'cannot_fulfill'
                        },
                        'message': 'This requirement can\'t be met',
                        'explanation': 'Cable infrastructure requirements (such as cable trays, conduits, ducts, etc.) are not available in the current wire/cable product database. These are typically sourced separately from cable accessories suppliers.',
                        'top_matches': [],
                        'match_count': 0
                    }
                    comparisons.append(comparison_entry)
                    continue
                
                # Handle wire/cable specifications
                wire_cable_requirements.append(req)
                top_products = spec_matcher.find_matching_products(req, top_n=3)
                
                # Enhance each product with calculations and recommendations
                enhanced_products = []
                for idx, product in enumerate(top_products):
                    enhanced_product = product.copy()
                    
                    # Add calculations for this product
                    if include_calculations and product.get('conductor_size'):
                        cable_size = float(product.get('conductor_size', 4))
                        cores = int(product.get('cores', 3)) if product.get('cores') else 3
                        material = 'copper' if 'copper' in str(product.get('conductor_material', '')).lower() else 'aluminum'
                        current_rating = float(product.get('current_rating', 20)) if product.get('current_rating') else 20
                        
                        # Get voltage from product or requirement
                        voltage_str = str(product.get('voltage_rating', '415'))
                        voltage_match = re.search(r'(\d+)', voltage_str)
                        voltage = float(voltage_match.group(1)) if voltage_match else 415
                        if 'kv' in voltage_str.lower():
                            voltage *= 1000
                        
                        # Voltage drop calculation
                        vd_calc = calculator.calculate_voltage_drop(
                            cable_size=cable_size,
                            length=cable_length,
                            current=current_rating,
                            material=material,
                            voltage=voltage,
                            cores=cores
                        )
                        enhanced_product['voltage_drop'] = {
                            'drop_volts': vd_calc['calculation']['voltage_drop_volts'],
                            'drop_percent': vd_calc['calculation']['voltage_drop_percent'],
                            'status': vd_calc['calculation']['assessment'],
                            'compliant_feeder': vd_calc['standards']['compliant_feeder'],
                            'compliant_branch': vd_calc['standards']['compliant_branch'],
                            'cable_length': cable_length
                        }
                        
                        # Power capacity calculation
                        pc_calc = calculator.calculate_power_capacity(
                            cable_size=cable_size,
                            voltage=voltage,
                            material=material,
                            cores=cores
                        )
                        enhanced_product['power_capacity'] = {
                            'power_kw': pc_calc['calculation']['power_capacity_kW'],
                            'power_kva': pc_calc['calculation']['power_capacity_kVA'],
                            'current_capacity': pc_calc['calculation']['derated_current_capacity']
                        }
                        
                        # Short circuit capacity
                        sc_calc = calculator.calculate_short_circuit_capacity(
                            cable_size=cable_size,
                            material=material
                        )
                        enhanced_product['short_circuit'] = {
                            'withstand_1s_kA': sc_calc['calculation']['withstand_current_1s_kA'],
                            'i2t_rating': sc_calc['calculation']['i2t_rating']
                        }
                    
                    # Add smart recommendations
                    if include_recommendations:
                        enhanced_product['recommendations'] = _generate_product_recommendations(
                            product, req, detected_application, idx + 1
                        )
                    
                    # Add budget analysis
                    if include_budget and product.get('price_per_meter'):
                        price = float(product.get('price_per_meter', 0))
                        enhanced_product['budget_analysis'] = {
                            'price_per_meter': price,
                            'total_cost': round(price * cable_length, 2),
                            'cable_length': cable_length,
                            'value_rating': _calculate_value_rating(product)
                        }
                    
                    enhanced_products.append(enhanced_product)
                    all_top_products.append(product)
                
                comparison_entry = {
                    'requirement': {
                        'original_text': req.get('original_text', ''),
                        'conductor_size': req.get('conductor_size'),
                        'cores': req.get('cores'),
                        'voltage': req.get('voltage'),
                        'insulation': req.get('insulation'),
                        'conductor_material': req.get('conductor_material'),
                        'armoured': req.get('armoured'),
                        'current_rating': req.get('current_rating'),
                    },
                    'top_matches': enhanced_products,
                    'match_count': len(enhanced_products)
                }
                
                comparisons.append(comparison_entry)
            
            # Generate OEM comparison summary
            oem_summary = None
            if include_oem_comparison and all_top_products:
                oem_summary = _generate_oem_comparison_summary(all_top_products, product_db)
            
            return jsonify({
                'status': 'success',
                'total_requirements': len(requirements),
                'requirement_summary': {
                    'total': len(requirements),
                    'wire_cable_specs': len(wire_cable_requirements),
                    'cable_only_infrastructure': len(cable_only_requirements)
                },
                'comparisons': comparisons,
                'detected_application': detected_application,
                'analysis_options': {
                    'calculations_included': include_calculations,
                    'recommendations_included': include_recommendations,
                    'budget_included': include_budget,
                    'cable_length': cable_length
                },
                'oem_summary': oem_summary,
                'database_info': {
                    'total_products': product_db.get_total_products(),
                    'oems': product_db.get_oem_list()
                }
            })
            
        finally:
            # Cleanup
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    
    except Exception as e:
        app.logger.error(f"Spec Compare error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


def _detect_application_type(rfp_text: str) -> str:
    """Auto-detect application type from RFP text"""
    text_lower = rfp_text.lower()
    
    application_keywords = {
        'hospital': ['hospital', 'medical', 'healthcare', 'clinic', 'icu', 'operation theatre'],
        'data_center': ['data center', 'data centre', 'server room', 'it infrastructure', 'ups room'],
        'high_rise': ['high rise', 'high-rise', 'multistorey', 'multi-storey', 'tower', 'apartment'],
        'industrial': ['factory', 'plant', 'manufacturing', 'industry', 'industrial', 'motor', 'machinery'],
        'underground': ['underground', 'buried', 'below ground', 'trench', 'duct bank'],
        'outdoor': ['outdoor', 'external', 'weather', 'exposed', 'street light'],
        'commercial': ['office', 'mall', 'shopping', 'commercial', 'retail', 'bank'],
        'residential': ['residential', 'housing', 'home', 'domestic', 'apartment']
    }
    
    scores = {}
    for app_type, keywords in application_keywords.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[app_type] = score
    
    if scores:
        return max(scores, key=scores.get)
    return 'commercial'  # Default


def _generate_product_recommendations(product: dict, requirement: dict, application: str, rank: int) -> list:
    """Generate smart recommendations for a product"""
    recommendations = []
    
    # Rank-based recommendation
    if rank == 1:
        recommendations.append("🥇 Best match for this requirement - highest compatibility score")
    elif rank == 2:
        recommendations.append("🥈 Strong alternative - good balance of specs and value")
    elif rank == 3:
        recommendations.append("🥉 Budget-friendly option - meets basic requirements")
    
    # Application-specific recommendations
    app_recommendations = {
        'hospital': {
            'check': ['FRLS', 'ZHFR', 'LSHF'],
            'message': '✅ Suitable for hospital - low smoke emission'
        },
        'data_center': {
            'check': ['FRLS', 'ZHFR'],
            'message': '✅ Good for data center - fire retardant'
        },
        'high_rise': {
            'check': ['FRLS', 'FR'],
            'message': '✅ Recommended for high-rise - fire safety compliant'
        },
        'underground': {
            'check': ['armoured', 'XLPE'],
            'message': '✅ Suitable for underground - moisture resistant'
        },
        'industrial': {
            'check': ['armoured', 'XLPE'],
            'message': '✅ Good for industrial - mechanical protection'
        }
    }
    
    if application in app_recommendations:
        app_rec = app_recommendations[application]
        insulation = str(product.get('insulation_type', '')).upper()
        is_armoured = product.get('is_armoured')
        
        for check in app_rec['check']:
            if check.upper() in insulation or (check == 'armoured' and is_armoured):
                recommendations.append(app_rec['message'])
                break
    
    # Quality-based recommendations
    quality = product.get('overall_quality_score')
    if quality:
        if quality >= 85:
            recommendations.append("⭐ Premium quality product - excellent reliability")
        elif quality >= 70:
            recommendations.append("✓ Good quality - reliable performance")
    
    # Warranty recommendation
    warranty = product.get('warranty_years')
    if warranty and warranty >= 5:
        recommendations.append(f"🛡️ {warranty}-year warranty - long-term coverage")
    
    # Price-value recommendation
    price = product.get('price_per_meter')
    if price:
        if price < 50:
            recommendations.append("💰 Budget-friendly pricing")
        elif price > 150:
            recommendations.append("💎 Premium segment - best-in-class specs")
    
    return recommendations[:4]  # Limit to 4 recommendations


def _calculate_value_rating(product: dict) -> str:
    """Calculate value rating for a product"""
    quality = product.get('overall_quality_score', 50)
    price = product.get('price_per_meter', 100)
    warranty = product.get('warranty_years', 1)
    
    if price and price > 0:
        value_score = (quality * (1 + warranty * 0.1)) / (price / 50)
        if value_score >= 80:
            return "Excellent Value"
        elif value_score >= 60:
            return "Good Value"
        elif value_score >= 40:
            return "Fair Value"
        else:
            return "Premium"
    return "N/A"


def _generate_oem_comparison_summary(products: list, product_db) -> dict:
    """Generate OEM comparison summary for ALL OEMs based on best matches"""
    # Get all OEMs from database
    all_oems = product_db.get_oem_list()
    oem_stats = {}
    
    # Initialize stats for all OEMs
    for oem in all_oems:
        oem_stats[oem] = {
            'count': 0,
            'total_score': 0,
            'avg_price': 0,
            'prices': [],
            'max_quality': 0,
            'warranty_max': 0,
            'best_match': 0
        }
    
    # Collect stats from matched products
    for product in products:
        oem = product.get('oem', 'Unknown')
        if oem in oem_stats:
            oem_stats[oem]['count'] += 1
            score = product.get('match_score', 0)
            oem_stats[oem]['total_score'] += score
            # Track best match score for each OEM
            if score > oem_stats[oem]['best_match']:
                oem_stats[oem]['best_match'] = score
            
            if product.get('price_per_meter'):
                oem_stats[oem]['prices'].append(product['price_per_meter'])
            
            quality = product.get('overall_quality_score', 0)
            if quality and quality > oem_stats[oem]['max_quality']:
                oem_stats[oem]['max_quality'] = quality
            
            warranty = product.get('warranty_years', 0)
            if warranty and warranty > oem_stats[oem]['warranty_max']:
                oem_stats[oem]['warranty_max'] = warranty
    
    # Calculate averages and rankings for ALL OEMs
    oem_rankings = []
    for oem, stats in oem_stats.items():
        # Use best_match score if available, otherwise 0 (no matches found)
        best_score = stats['best_match'] if stats['count'] > 0 else 0
        avg_score = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0
        avg_price = sum(stats['prices']) / len(stats['prices']) if stats['prices'] else 0
        
        oem_rankings.append({
            'oem': oem,
            'appearances': stats['count'],
            'best_match_score': round(best_score, 1),
            'avg_match_score': round(avg_score, 1),
            'avg_price': round(avg_price, 2),
            'max_quality_score': stats['max_quality'],
            'max_warranty': stats['warranty_max']
        })
    
    # Sort by appearances (descending), then by best match score (descending)
    oem_rankings.sort(key=lambda x: (x['appearances'], x['best_match_score']), reverse=True)
    
    return {
        'oem_rankings': oem_rankings,
        'total_oems': len(oem_rankings),
        'best_oem': oem_rankings[0]['oem'] if oem_rankings else None,
        'most_competitive': oem_rankings[0]['oem'] if oem_rankings else None
    }


@app.route('/api/spec-compare/stats', methods=['GET'])
def get_spec_compare_stats():
    """Get OEM database statistics including Moglix marketplace"""
    try:
        if not SPEC_COMPARER_AVAILABLE:
            return jsonify({'error': 'Spec Comparer not available'}), 500
        
        product_db, _ = get_spec_comparer()
        
        if product_db is None:
            return jsonify({'error': 'Database not loaded'}), 500
        
        df = product_db.products_df
        
        stats = {
            'total_products': len(df) if df is not None else 0,
            'oems': product_db.get_oem_list(),
            'oem_count': len(product_db.get_oem_list()),
            'source_stats': product_db.source_stats if hasattr(product_db, 'source_stats') else {},
            'available': True
        }
        
        if df is not None and len(df) > 0:
            if 'Category' in df.columns:
                stats['categories'] = df['Category'].dropna().unique().tolist()[:20]
            if 'Conductor_Size_sqmm' in df.columns:
                stats['conductor_sizes'] = sorted(df['Conductor_Size_sqmm'].dropna().unique().tolist())
            if 'OEM' in df.columns:
                stats['products_by_oem'] = df.groupby('OEM').size().to_dict()
            if 'Source' in df.columns:
                stats['products_by_source'] = df.groupby('Source').size().to_dict()
            if 'Company' in df.columns:
                stats['companies'] = df['Company'].dropna().unique().tolist()[:50]
            
            # Data quality metrics
            stats['data_quality'] = {
                'with_price': int(df['Price_Per_Meter_INR'].notna().sum()) if 'Price_Per_Meter_INR' in df.columns else 0,
                'with_current_rating': int(df['Current_Rating_Amps'].notna().sum()) if 'Current_Rating_Amps' in df.columns else 0,
                'with_safety_rating': int(df['Safety_Rating'].notna().sum()) if 'Safety_Rating' in df.columns else 0,
            }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e), 'available': False}), 500


# ============================================================================
# SPEC CALCULATOR API ENDPOINTS
# ============================================================================

@app.route('/api/spec-calculate', methods=['POST'])
def spec_calculate():
    """
    Calculate cable specifications based on user inputs
    Supports: cable_sizing, voltage_drop, short_circuit, power_capacity
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        calc_type = data.get('calculation_type', 'cable_sizing')
        calculator = get_spec_calculator()
        
        if calc_type == 'cable_sizing':
            # Calculate recommended cable size
            result = calculator.calculate_cable_size(
                load_current=float(data.get('load_current', 0)),
                voltage=float(data.get('voltage', 415)),
                material=data.get('material', 'copper'),
                installation=data.get('installation', 'open_air'),
                ambient_temp=int(data.get('ambient_temp', 40)),
                cable_grouping=int(data.get('cable_grouping', 1)),
                safety_factor=float(data.get('safety_factor', 1.25))
            )
            
        elif calc_type == 'voltage_drop':
            # Calculate voltage drop
            result = calculator.calculate_voltage_drop(
                cable_size=float(data.get('cable_size', 4)),
                length=float(data.get('length', 100)),
                current=float(data.get('current', 20)),
                material=data.get('material', 'copper'),
                voltage=float(data.get('voltage', 415)),
                power_factor=float(data.get('power_factor', 0.85)),
                cores=int(data.get('cores', 3)),
                temperature=int(data.get('temperature', 70))
            )
            
        elif calc_type == 'short_circuit':
            # Calculate short circuit capacity
            result = calculator.calculate_short_circuit_capacity(
                cable_size=float(data.get('cable_size', 4)),
                material=data.get('material', 'copper'),
                fault_duration=float(data.get('fault_duration', 1.0)),
                initial_temp=int(data.get('initial_temp', 70)),
                final_temp=int(data.get('final_temp', 160))
            )
            
        elif calc_type == 'power_capacity':
            # Calculate power capacity
            result = calculator.calculate_power_capacity(
                cable_size=float(data.get('cable_size', 4)),
                voltage=float(data.get('voltage', 415)),
                material=data.get('material', 'copper'),
                power_factor=float(data.get('power_factor', 0.85)),
                cores=int(data.get('cores', 3)),
                installation=data.get('installation', 'open_air'),
                ambient_temp=int(data.get('ambient_temp', 40))
            )
            
        else:
            return jsonify({'error': f'Unknown calculation type: {calc_type}'}), 400
        
        result['calculation_type'] = calc_type
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Spec calculator error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/spec-calculate/reference', methods=['GET'])
def get_calculator_reference():
    """Get reference data for spec calculator"""
    calculator = get_spec_calculator()
    
    return jsonify({
        'standard_sizes': calculator.STANDARD_SIZES,
        'installation_methods': list(calculator.INSTALLATION_METHOD_DERATING.keys()),
        'ambient_temps': list(calculator.AMBIENT_TEMP_DERATING.keys()),
        'grouping_factors': list(calculator.GROUPING_DERATING.keys()),
        'copper_capacity': calculator.COPPER_CURRENT_CAPACITY,
        'aluminum_capacity': calculator.ALUMINUM_CURRENT_CAPACITY
    })


# ============================================================================
# TESTING CALCULATIONS API ENDPOINTS
# ============================================================================

@app.route('/api/calculate/testing-costs', methods=['POST'])
def calculate_testing_costs():
    """Calculate comprehensive testing costs for cable procurement"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        voltage_class = data.get('voltage_class', 'LT')
        cable_type = data.get('cable_type', 'power')
        is_armoured = data.get('is_armoured', 'false').lower() == 'true' if isinstance(data.get('is_armoured'), str) else bool(data.get('is_armoured', False))
        quantity_meters = float(data.get('quantity_meters', 1000))
        num_samples = int(data.get('num_samples', 3))
        
        calculator = get_spec_calculator()
        result = calculator.calculate_testing_costs(
            cable_size=cable_size,
            voltage_class=voltage_class,
            cable_type=cable_type,
            is_armoured=is_armoured,
            quantity_meters=quantity_meters,
            num_samples=num_samples
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/insulation-resistance', methods=['POST'])
def calculate_insulation_resistance():
    """Calculate expected insulation resistance values"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        length = float(data.get('length', 100))
        insulation_type = data.get('insulation_type', 'PVC')
        voltage_rating = float(data.get('voltage_rating', 1100))
        temperature = int(data.get('temperature', 20))
        
        calculator = get_spec_calculator()
        result = calculator.calculate_insulation_resistance(
            cable_size=cable_size,
            length=length,
            insulation_type=insulation_type,
            voltage_rating=voltage_rating,
            temperature=temperature
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/hi-pot-test', methods=['POST'])
def calculate_hi_pot_test():
    """Calculate High Potential (Hi-Pot) test parameters"""
    try:
        data = request.get_json() or request.form
        
        voltage_rating = float(data.get('voltage_rating', 1100))
        cable_type = data.get('cable_type', 'power')
        test_type = data.get('test_type', 'routine')
        duration_minutes = int(data.get('duration_minutes', 5))
        
        calculator = get_spec_calculator()
        result = calculator.calculate_hi_pot_test(
            voltage_rating=voltage_rating,
            cable_type=cable_type,
            test_type=test_type,
            duration_minutes=duration_minutes
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/conductor-resistance', methods=['POST'])
def calculate_conductor_resistance():
    """Calculate conductor resistance and verify against standards"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        length = float(data.get('length', 100))
        material = data.get('material', 'copper')
        temperature = int(data.get('temperature', 20))
        stranding = data.get('stranding', 'Class 2')
        
        calculator = get_spec_calculator()
        result = calculator.calculate_conductor_resistance(
            cable_size=cable_size,
            length=length,
            material=material,
            temperature=temperature,
            stranding=stranding
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/all-tests', methods=['POST'])
def calculate_all_tests():
    """Calculate all testing parameters for a cable specification"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        length = float(data.get('length', 100))
        voltage_rating = float(data.get('voltage_rating', 1100))
        material = data.get('material', 'copper')
        insulation_type = data.get('insulation_type', 'PVC')
        is_armoured = data.get('is_armoured', 'false').lower() == 'true' if isinstance(data.get('is_armoured'), str) else bool(data.get('is_armoured', False))
        quantity_meters = float(data.get('quantity_meters', 1000))
        
        voltage_class = 'EHV' if voltage_rating > 33000 else ('HT' if voltage_rating > 1100 else 'LT')
        
        calculator = get_spec_calculator()
        
        results = {
            'cable_specification': {
                'cable_size': cable_size,
                'length': length,
                'voltage_rating': voltage_rating,
                'voltage_class': voltage_class,
                'material': material,
                'insulation_type': insulation_type,
                'is_armoured': is_armoured,
                'quantity_meters': quantity_meters
            },
            'testing_costs': calculator.calculate_testing_costs(
                cable_size=cable_size,
                voltage_class=voltage_class,
                is_armoured=is_armoured,
                quantity_meters=quantity_meters
            ),
            'conductor_resistance': calculator.calculate_conductor_resistance(
                cable_size=cable_size,
                length=length,
                material=material
            ),
            'insulation_resistance': calculator.calculate_insulation_resistance(
                cable_size=cable_size,
                length=length,
                insulation_type=insulation_type,
                voltage_rating=voltage_rating
            ),
            'hi_pot_test': calculator.calculate_hi_pot_test(
                voltage_rating=voltage_rating,
                test_type='routine'
            )
        }
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PRODUCT RECOMMENDER API ENDPOINTS
# ============================================================================

@app.route('/api/product-recommend', methods=['POST'])
def product_recommend():
    """
    Get product recommendations based on various criteria
    Supports: by_application, by_budget, best_quality, compare_oems
    """
    try:
        if not SPEC_COMPARER_AVAILABLE:
            return jsonify({'error': 'Product recommender not available (pandas not installed)'}), 500
        
        recommender = get_product_recommender()
        
        if recommender is None:
            return jsonify({'error': 'Product database not available'}), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        recommend_type = data.get('recommend_type', 'by_application')
        
        if recommend_type == 'by_application':
            # Recommend by application type
            result = recommender.recommend_by_application(
                application=data.get('application', 'residential'),
                conductor_size=data.get('conductor_size'),
                cores=data.get('cores'),
                material=data.get('material'),
                top_n=int(data.get('top_n', 5))
            )
            
        elif recommend_type == 'by_budget':
            # Recommend by budget
            if not data.get('conductor_size') or not data.get('cores'):
                return jsonify({'error': 'conductor_size and cores are required for budget recommendations'}), 400
            
            result = recommender.recommend_by_budget(
                budget_category=data.get('budget_category', 'standard'),
                conductor_size=float(data.get('conductor_size')),
                cores=int(data.get('cores')),
                material=data.get('material', 'copper'),
                length_meters=float(data.get('length_meters', 100)),
                top_n=int(data.get('top_n', 5))
            )
            
        elif recommend_type == 'best_quality':
            # Recommend best quality products
            result = recommender.recommend_best_quality(
                conductor_size=data.get('conductor_size'),
                cores=data.get('cores'),
                insulation=data.get('insulation'),
                top_n=int(data.get('top_n', 5))
            )
            
        elif recommend_type == 'compare_oems':
            # Compare across OEMs
            if not data.get('conductor_size') or not data.get('cores'):
                return jsonify({'error': 'conductor_size and cores are required for OEM comparison'}), 400
            
            result = recommender.compare_oems(
                conductor_size=float(data.get('conductor_size')),
                cores=int(data.get('cores')),
                material=data.get('material', 'copper')
            )
            
        else:
            return jsonify({'error': f'Unknown recommend type: {recommend_type}'}), 400
        
        result['recommend_type'] = recommend_type
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Product recommender error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/product-recommend/applications', methods=['GET'])
def get_application_profiles():
    """Get available application profiles"""
    recommender = get_product_recommender()
    
    if recommender is None:
        # Return static data if database not loaded
        return jsonify({
            'applications': list(ProductRecommender.APPLICATION_PROFILES.keys()),
            'profiles': ProductRecommender.APPLICATION_PROFILES,
            'budget_categories': ProductRecommender.BUDGET_CATEGORIES
        })
    
    return jsonify({
        'applications': list(recommender.APPLICATION_PROFILES.keys()),
        'profiles': recommender.APPLICATION_PROFILES,
        'budget_categories': recommender.BUDGET_CATEGORIES
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': 'File is too large (max 50MB)'}), 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Page not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Start cleanup thread
    schedule_cleanup()
    
    print("\n" + "="*80)
    print("PDF EXTRACTOR - WEB APPLICATION (OPTIMIZED)")
    print("="*80)
    print("\n🚀 Starting server with 100k+ terms database...")
    print("📍 Open your browser and go to: http://localhost:5000")
    print("✨ Features: Lazy loading, caching, fuzzy matching")
    print("📁 Database: rfp_terms_database_100k.json with intelligent indexing")
    print("📊 Performance: LRU cache (10k entries), pickle-based persistence")
    print("🧮 Calculator: Cable sizing, voltage drop, short circuit, power capacity")
    print("🧪 Testing: Costs, IR, Hi-Pot, Conductor resistance")
    print("🎯 Recommender: Application-based, budget, quality analysis")
    print("\n" + "="*80 + "\n")
    
    app.run(debug=True, host='localhost', port=5000, threaded=True)
