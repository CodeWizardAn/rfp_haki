"""
RFP Responser Flask Application
Main web interface for:
- RFP Upload and Processing
- Automatic Spec Matching to OEM Products (Top 3)
- Auto-fill RFP Forms
- Bid Generation and Management
- Approval Workflow
- Agent Integration
"""

from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import sqlite3
import os
import json
from functools import wraps
import logging
import io
import sys
from pathlib import Path

# Performance Integration
try:
    perf_path = str(Path(__file__).parent.parent)
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from performance.integration import integrate_flask_app, init_performance
    from rfp_responser.perf_integration import init_rfp_performance, RFPProcessingOptimizer
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    print(f"Performance integration not available: {e}")

# Import bid management modules
from bid_templates import BidTemplateManager, BidBuilder, BidStatus
from bid_price_calculator import PriceCalculator, TaxType
from bid_document_generator import PDFBidGenerator, ExcelBidGenerator
from bid_approval_workflow import ApprovalWorkflow, ApprovalLevel, ApprovalAction
from oem_bid_routes import oem_bid_bp, create_oem_bid_database

# Import RFP workflow manager
try:
    from rfp_workflow import RFPWorkflowManager, get_workflow_manager
    WORKFLOW_AVAILABLE = True
except ImportError as e:
    WORKFLOW_AVAILABLE = False
    print(f"Workflow manager not available: {e}")

# Pipeline Connector Integration
try:
    pipeline_root = str(Path(__file__).parent.parent)
    if pipeline_root not in sys.path:
        sys.path.insert(0, pipeline_root)
    from pipeline_connector import PipelineExecutor, create_pipeline, run_full_pipeline
    PIPELINE_AVAILABLE = True
except ImportError as e:
    PIPELINE_AVAILABLE = False
    print(f"Pipeline connector not available: {e}")

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['SECRET_KEY'] = 'rfp-responser-secret-2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Initialize Performance System
if PERFORMANCE_AVAILABLE:
    try:
        integrate_flask_app(app)
        init_rfp_performance(app)
        print("✅ Performance system integrated")
    except Exception as e:
        print(f"Performance integration failed: {e}")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Register OEM blueprint
app.register_blueprint(oem_bid_bp)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize managers
bid_template_manager = BidTemplateManager()
price_calculator = PriceCalculator()
approval_workflow = ApprovalWorkflow()
pdf_generator = PDFBidGenerator()
excel_generator = ExcelBidGenerator()

# Initialize workflow manager
workflow_manager = get_workflow_manager() if WORKFLOW_AVAILABLE else None

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_bid_database():
    """Get SQLite connection for bids"""
    conn = sqlite3.connect('bids.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_bid_database():
    """Initialize bid database"""
    conn = get_bid_database()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            bid_id TEXT PRIMARY KEY,
            rfp_id TEXT,
            vendor_id TEXT,
            vendor_name TEXT,
            template_id TEXT,
            status TEXT,
            issued_date TIMESTAMP,
            valid_until_date TIMESTAMP,
            total_cost REAL,
            subtotal REAL,
            discount_amount REAL,
            tax_amount REAL,
            shipping_cost REAL,
            version INTEGER,
            created_by TEXT,
            created_date TIMESTAMP,
            last_modified TIMESTAMP,
            items_json TEXT,
            delivery_timeline TEXT,
            payment_terms TEXT,
            notes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Initialize OEM bid database
    try:
        create_oem_bid_database()
    except Exception as e:
        logger.warning(f"OEM bid database initialization: {e}")


# Initialize database at startup
with app.app_context():
    init_bid_database()
    logger.info("✅ RFP Responser initialized")
    logger.info(f"   Workflow Manager: {'✅' if WORKFLOW_AVAILABLE else '❌'}")


# ==================== RFP UPLOAD & PROCESSING ENDPOINTS ====================

@app.route('/api/rfp/upload', methods=['POST'])
def upload_rfp():
    """
    Upload RFP document and process it
    
    Process:
    1. Upload PDF
    2. Extract text
    3. Parse requirements
    4. Match to top 3 OEM products
    5. Calculate pricing
    6. Auto-fill forms
    7. Generate bid document
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed. Please upload PDF'}), 400
        
        # Get vendor info from form
        vendor_info = {
            'vendor_id': request.form.get('vendor_id', 'VENDOR_001'),
            'vendor_name': request.form.get('vendor_name', 'Default Vendor'),
            'address': request.form.get('address', ''),
            'contact': request.form.get('contact', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'gstin': request.form.get('gstin', ''),
        }
        
        use_agents = request.form.get('use_agents', 'false').lower() == 'true'
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Check if workflow manager is available
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({
                'success': False, 
                'error': 'Workflow manager not available'
            }), 500
        
        # Process RFP through workflow
        result = workflow_manager.process_rfp(
            pdf_path=upload_path,
            vendor_info=vendor_info,
            use_agents=use_agents
        )
        
        return jsonify({
            'success': result.get('status') == 'completed',
            'workflow_id': result.get('workflow_id'),
            'status': result.get('status'),
            'result': result
        }), 200 if result.get('status') == 'completed' else 400
        
    except Exception as e:
        logger.error(f"Error processing RFP upload: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rfp/workflow/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """Get status of an RFP workflow"""
    if not WORKFLOW_AVAILABLE or not workflow_manager:
        return jsonify({'error': 'Workflow manager not available'}), 500
    
    status = workflow_manager.get_workflow_status(workflow_id)
    return jsonify(status), 200


@app.route('/api/rfp/match', methods=['POST'])
def match_specifications():
    """
    Match specifications from RFP text against OEM products
    Returns top 3 matching products for each requirement
    """
    try:
        data = request.json
        rfp_text = data.get('rfp_text', '')
        
        if not rfp_text:
            return jsonify({'error': 'No RFP text provided'}), 400
        
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({'error': 'Workflow manager not available'}), 500
        
        # Parse requirements
        if workflow_manager.spec_matcher:
            requirements = workflow_manager.spec_matcher.parse_rfp_requirements(rfp_text)
        else:
            requirements = []
        
        # Match each requirement
        matched_results = workflow_manager._match_specifications(requirements)
        
        return jsonify({
            'success': True,
            'requirements_count': len(requirements),
            'requirements': requirements,
            'matches': matched_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error matching specifications: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rfp/products', methods=['GET'])
def list_oem_products():
    """List available OEM products for matching"""
    try:
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({'error': 'Workflow manager not available'}), 500
        
        filters = {
            'conductor_size': request.args.get('size', type=float),
            'cores': request.args.get('cores', type=int),
            'oem': request.args.get('oem')
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        products = workflow_manager.list_oem_products(filters)
        
        return jsonify({
            'success': True,
            'count': len(products),
            'products': products
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rfp/calculate-pricing', methods=['POST'])
def calculate_rfp_pricing():
    """Calculate pricing for matched products"""
    try:
        data = request.json
        matched_products = data.get('matched_products', {})
        rfp_data = data.get('rfp_data', {})
        
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({'error': 'Workflow manager not available'}), 500
        
        pricing = workflow_manager._calculate_pricing(matched_products, rfp_data)
        
        return jsonify({
            'success': True,
            'pricing': pricing
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating pricing: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rfp/generate-bid', methods=['POST'])
def generate_rfp_bid():
    """Generate bid document from RFP processing result"""
    try:
        data = request.json
        workflow_id = data.get('workflow_id')
        
        if not workflow_id:
            return jsonify({'error': 'Workflow ID required'}), 400
        
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({'error': 'Workflow manager not available'}), 500
        
        # Get workflow data
        workflow = workflow_manager.get_workflow_status(workflow_id)
        
        if workflow.get('error'):
            return jsonify({'error': 'Workflow not found'}), 404
        
        bid_result = workflow.get('stages', {}).get('bid_generation', {})
        
        return jsonify({
            'success': True,
            'bid_id': bid_result.get('bid_id'),
            'documents': bid_result.get('documents', {})
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating bid: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== BID ENDPOINTS ====================

@app.route('/api/bids', methods=['POST'])
def create_bid():
    """Create a new bid"""
    try:
        data = request.json
        bid_id = data.get('bid_id', f"BID_{datetime.now().timestamp()}")
        
        # Create bid from template
        builder = BidBuilder(bid_template_manager)
        bid = (builder
            .create_bid(
                bid_id=bid_id,
                rfp_id=data.get('rfp_id'),
                vendor_id=data.get('vendor_id'),
                vendor_name=data.get('vendor_name'),
                template_id=data.get('template_id', 'BID_STANDARD_001')
            )
            .set_valid_until(data.get('valid_days', 30))
        )
        
        # Add items
        for item in data.get('items', []):
            bid.add_item(
                item_id=item.get('item_id'),
                description=item.get('description'),
                product_id=item.get('product_id'),
                quantity=item.get('quantity'),
                unit=item.get('unit', 'Unit'),
                unit_price=item.get('unit_price'),
                discount_percent=item.get('discount_percent', 0)
            )
        
        bid_obj = bid.build()
        
        # Calculate pricing
        items_list = []
        for item in bid_obj.items:
            pricing = price_calculator.calculate_item_price(
                unit_price=item.unit_price,
                quantity=item.quantity,
                discount_percent=item.discount_percent,
                tax_percent=18.0
            )
            items_list.append({
                'item_id': item.item_id,
                'description': item.description,
                'quantity': item.quantity,
                'unit': item.unit,
                'unit_price': item.unit_price,
                'discount_percent': item.discount_percent,
                'total': pricing['final_total']
            })
        
        # Save to database
        conn = get_bid_database()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bids 
            (bid_id, rfp_id, vendor_id, vendor_name, template_id, status, 
             issued_date, valid_until_date, version, created_by, created_date, 
             items_json, delivery_timeline, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (bid_id, data.get('rfp_id'), data.get('vendor_id'), 
              data.get('vendor_name'), data.get('template_id', 'BID_STANDARD_001'),
              'DRAFT', datetime.now(), bid_obj.valid_until_date, 1, 
              data.get('created_by', 'SYSTEM'), datetime.now(),
              json.dumps(items_list),
              data.get('delivery_timeline', '15 days'),
              data.get('payment_terms', 'Net 30 days')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'bid_id': bid_id,
            'status': 'DRAFT',
            'message': 'Bid created successfully'
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating bid: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/bids/<bid_id>', methods=['GET'])
def get_bid(bid_id):
    """Get bid details"""
    try:
        conn = get_bid_database()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bids WHERE bid_id = ?', (bid_id,))
        bid = cursor.fetchone()
        conn.close()
        
        if not bid:
            return jsonify({'error': 'Bid not found'}), 404
        
        # Get approval status
        approval_status = approval_workflow.get_approval_status(bid_id)
        
        return jsonify({
            'bid_id': bid['bid_id'],
            'rfp_id': bid['rfp_id'],
            'vendor_id': bid['vendor_id'],
            'vendor_name': bid['vendor_name'],
            'status': bid['status'],
            'total_cost': bid['total_cost'],
            'items': json.loads(bid['items_json']) if bid['items_json'] else [],
            'delivery_timeline': bid['delivery_timeline'],
            'payment_terms': bid['payment_terms'],
            'approval_status': approval_status,
            'created_date': bid['created_date']
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving bid: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/bids/<bid_id>', methods=['PUT'])
def update_bid(bid_id):
    """Update bid details"""
    try:
        data = request.json
        conn = get_bid_database()
        cursor = conn.cursor()
        
        # Update bid
        cursor.execute('''
            UPDATE bids 
            SET delivery_timeline = ?, payment_terms = ?, notes = ?, last_modified = ?
            WHERE bid_id = ?
        ''', (data.get('delivery_timeline'),
              data.get('payment_terms'),
              data.get('notes'),
              datetime.now(),
              bid_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Bid updated successfully'}), 200
    
    except Exception as e:
        logger.error(f"Error updating bid: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/bids', methods=['GET'])
def list_bids():
    """List all bids"""
    try:
        vendor_id = request.args.get('vendor_id')
        rfp_id = request.args.get('rfp_id')
        status = request.args.get('status')
        
        conn = get_bid_database()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM bids WHERE 1=1'
        params = []
        
        if vendor_id:
            query += ' AND vendor_id = ?'
            params.append(vendor_id)
        if rfp_id:
            query += ' AND rfp_id = ?'
            params.append(rfp_id)
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY created_date DESC'
        cursor.execute(query, params)
        bids = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(bids),
            'bids': [dict(bid) for bid in bids]
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing bids: {e}")
        return jsonify({'error': str(e)}), 400


# ==================== DOCUMENT GENERATION ====================

@app.route('/api/bids/<bid_id>/pdf', methods=['GET'])
def export_bid_pdf(bid_id):
    """Export bid as PDF"""
    try:
        # Get bid data
        conn = get_bid_database()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bids WHERE bid_id = ?', (bid_id,))
        bid_row = cursor.fetchone()
        conn.close()
        
        if not bid_row:
            return jsonify({'error': 'Bid not found'}), 404
        
        # Prepare bid data
        bid_data = {
            'bid_id': bid_row['bid_id'],
            'rfp_id': bid_row['rfp_id'],
            'vendor_name': bid_row['vendor_name'],
            'issued_date': bid_row['issued_date'],
            'valid_until_date': bid_row['valid_until_date'],
            'version': bid_row['version'],
            'items': json.loads(bid_row['items_json']) if bid_row['items_json'] else [],
            'status': bid_row['status'],
            'delivery_timeline': bid_row['delivery_timeline'],
            'payment_terms': bid_row['payment_terms'],
            'total_cost': bid_row['total_cost'] or 0
        }
        
        # Generate PDF
        pdf_bytes = pdf_generator.generate(bid_data)
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{bid_id}.pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/bids/<bid_id>/excel', methods=['GET'])
def export_bid_excel(bid_id):
    """Export bid as Excel"""
    try:
        # Get bid data
        conn = get_bid_database()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bids WHERE bid_id = ?', (bid_id,))
        bid_row = cursor.fetchone()
        conn.close()
        
        if not bid_row:
            return jsonify({'error': 'Bid not found'}), 404
        
        # Prepare bid data
        bid_data = {
            'bid_id': bid_row['bid_id'],
            'rfp_id': bid_row['rfp_id'],
            'vendor_name': bid_row['vendor_name'],
            'issued_date': bid_row['issued_date'],
            'valid_until_date': bid_row['valid_until_date'],
            'version': bid_row['version'],
            'items': json.loads(bid_row['items_json']) if bid_row['items_json'] else [],
            'status': bid_row['status'],
            'total_cost': bid_row['total_cost'] or 0
        }
        
        # Generate Excel
        excel_bytes = excel_generator.generate(bid_data)
        
        return send_file(
            io.BytesIO(excel_bytes),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{bid_id}.xlsx'
        )
    
    except Exception as e:
        logger.error(f"Error generating Excel: {e}")
        return jsonify({'error': str(e)}), 400


# ==================== APPROVAL ENDPOINTS ====================

@app.route('/api/bids/<bid_id>/submit', methods=['POST'])
def submit_for_approval(bid_id):
    """Submit bid for approval"""
    try:
        data = request.json
        success, msg = approval_workflow.submit_for_review(
            bid_id, 
            data.get('submitter_id', 'SYSTEM'),
            data.get('submitter_name', 'System')
        )
        
        if success:
            # Update bid status
            conn = get_bid_database()
            cursor = conn.cursor()
            cursor.execute('UPDATE bids SET status = ?, last_modified = ? WHERE bid_id = ?',
                         ('SUBMITTED_FOR_REVIEW', datetime.now(), bid_id))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': msg}), 200
        else:
            return jsonify({'success': False, 'error': msg}), 400
    
    except Exception as e:
        logger.error(f"Error submitting bid: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/bids/<bid_id>/approve', methods=['POST'])
def approve_bid(bid_id):
    """Approve bid"""
    try:
        data = request.json
        step_id = data.get('step_id')
        reviewer_id = data.get('reviewer_id')
        comment = data.get('comment')
        
        success, msg = approval_workflow.approve_bid(bid_id, step_id, reviewer_id, comment)
        
        if success:
            return jsonify({'success': True, 'message': msg}), 200
        else:
            return jsonify({'success': False, 'error': msg}), 400
    
    except Exception as e:
        logger.error(f"Error approving bid: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/bids/<bid_id>/reject', methods=['POST'])
def reject_bid(bid_id):
    """Reject bid"""
    try:
        data = request.json
        step_id = data.get('step_id')
        reviewer_id = data.get('reviewer_id')
        reason = data.get('reason')
        
        success, msg = approval_workflow.reject_bid(bid_id, step_id, reviewer_id, reason)
        
        if success:
            # Update bid status
            conn = get_bid_database()
            cursor = conn.cursor()
            cursor.execute('UPDATE bids SET status = ?, last_modified = ? WHERE bid_id = ?',
                         ('REJECTED', datetime.now(), bid_id))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': msg}), 200
        else:
            return jsonify({'success': False, 'error': msg}), 400
    
    except Exception as e:
        logger.error(f"Error rejecting bid: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/bids/<bid_id>/request-revision', methods=['POST'])
def request_revision(bid_id):
    """Request revision on bid"""
    try:
        data = request.json
        step_id = data.get('step_id')
        reviewer_id = data.get('reviewer_id')
        revision_details = data.get('revision_details')
        
        success, msg = approval_workflow.request_revision(bid_id, step_id, reviewer_id, revision_details)
        
        if success:
            return jsonify({'success': True, 'message': msg}), 200
        else:
            return jsonify({'success': False, 'error': msg}), 400
    
    except Exception as e:
        logger.error(f"Error requesting revision: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/api/bids/<bid_id>/approval-status', methods=['GET'])
def get_approval_status(bid_id):
    """Get approval status of bid"""
    try:
        status = approval_workflow.get_approval_status(bid_id)
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting approval status: {e}")
        return jsonify({'error': str(e)}), 400


# ==================== DASHBOARD ENDPOINTS ====================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_bid_database()
        cursor = conn.cursor()
        
        # Total bids
        cursor.execute('SELECT COUNT(*) as count FROM bids')
        total_bids = cursor.fetchone()['count']
        
        # By status
        cursor.execute('SELECT status, COUNT(*) as count FROM bids GROUP BY status')
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total value
        cursor.execute('SELECT SUM(total_cost) as total FROM bids WHERE status = "APPROVED"')
        total_value = cursor.fetchone()['total'] or 0
        
        conn.close()
        
        return jsonify({
            'total_bids': total_bids,
            'by_status': by_status,
            'total_approved_value': total_value
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 400


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'RFP Responser'}), 200


# ==================== UTILITIES ====================

@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List available bid templates"""
    templates = []
    for template_id, template in bid_template_manager.templates.items():
        templates.append({
            'template_id': template_id,
            'name': template.name,
            'format': template.bid_format.name,
            'sections': len(template.sections)
        })
    return jsonify({'templates': templates}), 200


# ==================== PDF EXTRACTION API ====================

@app.route('/api/extract/pdf', methods=['POST'])
def extract_pdf_content():
    """
    Extract text and data from uploaded PDF
    Connects to pdf_extraction module
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files supported'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({'error': 'PDF extraction not available'}), 500
        
        # Extract PDF content
        extraction_result = workflow_manager._extract_pdf_content(upload_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'extraction': extraction_result
        }), 200
        
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract/parse-terms', methods=['POST'])
def parse_rfp_terms():
    """
    Parse RFP text to extract recognized terms and fields
    Connects to RFPTermsMatcher
    """
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.terms_matcher:
            return jsonify({'error': 'Terms matcher not available'}), 500
        
        # Parse the text
        result = workflow_manager.terms_matcher.parse_rfp_text(text)
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Terms parsing error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract/database-info', methods=['GET'])
def get_terms_database_info():
    """Get information about the RFP terms database"""
    try:
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.terms_matcher:
            return jsonify({'error': 'Terms matcher not available'}), 500
        
        info = workflow_manager.terms_matcher.get_database_info()
        return jsonify({
            'success': True,
            'database_info': info
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SPEC COMPARER API ====================

@app.route('/api/specs/match', methods=['POST'])
def match_product_specs():
    """
    Match product specifications against OEM database
    Connects to spec_comparer module
    """
    try:
        data = request.json
        requirement = data.get('requirement', {})
        top_n = data.get('top_n', 3)
        
        if not requirement:
            return jsonify({'error': 'No requirement provided'}), 400
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.spec_matcher:
            return jsonify({'error': 'Spec matcher not available'}), 500
        
        # Find matching products
        matches = workflow_manager.spec_matcher.find_matching_products(requirement, top_n=top_n)
        
        return jsonify({
            'success': True,
            'requirement': requirement,
            'top_n': top_n,
            'matches': matches
        }), 200
        
    except Exception as e:
        logger.error(f"Spec matching error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/specs/parse-requirements', methods=['POST'])
def parse_product_requirements():
    """
    Parse RFP text to extract product requirements
    """
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.spec_matcher:
            return jsonify({'error': 'Spec matcher not available'}), 500
        
        requirements = workflow_manager.spec_matcher.parse_rfp_requirements(text)
        
        return jsonify({
            'success': True,
            'requirements': requirements,
            'count': len(requirements)
        }), 200
        
    except Exception as e:
        logger.error(f"Requirements parsing error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/specs/oems', methods=['GET'])
def list_available_oems():
    """List all available OEMs in the product database"""
    try:
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.product_db:
            return jsonify({'error': 'Product database not available'}), 500
        
        oems = workflow_manager.product_db.get_oem_list()
        
        return jsonify({
            'success': True,
            'oems': oems,
            'count': len(oems)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/specs/products/search', methods=['GET'])
def search_products():
    """
    Search products in the OEM database
    Query params: q (search term), oem (filter by OEM), size (conductor size), cores (number of cores)
    """
    try:
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.product_db:
            return jsonify({'error': 'Product database not available'}), 500
        
        search_term = request.args.get('q', '')
        oem_filter = request.args.get('oem')
        size_filter = request.args.get('size', type=float)
        cores_filter = request.args.get('cores', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Get all products
        products = workflow_manager.product_db.get_all_products()
        
        # Apply filters
        results = []
        for product in products:
            # Search term filter
            if search_term:
                searchable = f"{product.get('product_name', '')} {product.get('description', '')}".lower()
                if search_term.lower() not in searchable:
                    continue
            
            # OEM filter
            if oem_filter and product.get('oem', '').lower() != oem_filter.lower():
                continue
            
            # Size filter
            if size_filter and product.get('conductor_size') != size_filter:
                continue
            
            # Cores filter
            if cores_filter and product.get('cores') != cores_filter:
                continue
            
            results.append(product)
            
            if len(results) >= limit:
                break
        
        return jsonify({
            'success': True,
            'products': results,
            'count': len(results),
            'total_in_db': len(products)
        }), 200
        
    except Exception as e:
        logger.error(f"Product search error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== AGENT WORKFLOW API ====================

@app.route('/api/agents/status', methods=['GET'])
def get_agents_status():
    """Get status of all agents in the system"""
    try:
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({
                'success': False,
                'error': 'Workflow manager not available'
            }), 500
        
        agent_status = {
            'master_agent': {
                'available': workflow_manager.master_agent is not None,
                'type': 'Orchestrator',
                'role': 'Coordinates Technical and Pricing agents, prepares contextual summaries, consolidates responses'
            },
            'technical_agent': {
                'available': workflow_manager.master_agent.technical_agent is not None if workflow_manager.master_agent else False,
                'type': 'Worker',
                'role': 'Analyzes products, recommends top 3 OEM products with spec match %, creates comparison tables'
            },
            'pricing_agent': {
                'available': workflow_manager.master_agent.pricing_agent is not None if workflow_manager.master_agent else False,
                'type': 'Worker', 
                'role': 'Calculates product prices from pricing table, test costs from services table'
            },
            'sales_agent': {
                'available': workflow_manager.master_agent.sales_agent is not None if workflow_manager.master_agent else False,
                'type': 'Worker',
                'role': 'Scans URLs for RFPs, identifies RFPs due in 3 months, selects RFP for response'
            }
        }
        
        # Get conversation status if available
        if workflow_manager.master_agent:
            conversation_status = workflow_manager.master_agent.get_conversation_status()
            agent_status['conversation'] = conversation_status
        
        return jsonify({
            'success': True,
            'agents': agent_status
        }), 200
        
    except Exception as e:
        logger.error(f"Agent status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/run-workflow', methods=['POST'])
def run_agent_workflow():
    """
    Run the full multi-agent workflow
    
    Agent Communication Flow:
    1. Sales Agent scans URLs → selects RFP → sends to Master
    2. Master prepares contextual summaries (Technical: products/specs, Pricing: tests/criteria)
    3. Technical Agent analyzes → top 3 OEM recommendations with spec match % → Master AND Pricing
    4. Pricing Agent calculates → product prices + test costs → Master
    5. Master consolidates final response
    """
    try:
        data = request.json or {}
        rfp_urls = data.get('rfp_urls', [])
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.master_agent:
            return jsonify({
                'success': False,
                'error': 'Agent system not available'
            }), 500
        
        # Run the full workflow
        response = workflow_manager.master_agent.run_full_workflow(rfp_urls)
        
        # Export to JSON format
        result = workflow_manager.master_agent.export_response_to_json(response)
        
        return jsonify({
            'success': True,
            'response': json.loads(result),
            'scope_of_supply_table': workflow_manager.master_agent.print_scope_of_supply_table(response)
        }), 200
        
    except Exception as e:
        logger.error(f"Agent workflow error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/technical/analyze', methods=['POST'])
def run_technical_analysis():
    """
    Run Technical Agent analysis on RFP products
    
    Technical Agent responsibilities:
    - Summarize products in scope of supply
    - Recommend top 3 OEM products with "Spec Match" metric (%)
    - Prepare comparison table (RFP spec vs OEM 1, OEM 2, OEM 3)
    - Select top OEM product for each RFP item
    """
    try:
        data = request.json
        products_in_scope = data.get('products', [])
        rfp_id = data.get('rfp_id', 'RFP_ANALYSIS')
        
        if not products_in_scope:
            return jsonify({'error': 'No products provided'}), 400
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.master_agent:
            return jsonify({'error': 'Agent system not available'}), 500
        
        # Create technical context
        tech_context = {
            'rfp_id': rfp_id,
            'products_in_scope': products_in_scope
        }
        
        # Run technical agent
        technical_agent = workflow_manager.master_agent.technical_agent
        result = technical_agent.process_rfp(tech_context)
        
        return jsonify({
            'success': True,
            'rfp_id': rfp_id,
            'analysis': result
        }), 200
        
    except Exception as e:
        logger.error(f"Technical analysis error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/pricing/calculate', methods=['POST'])
def run_pricing_calculation():
    """
    Run Pricing Agent calculations
    
    Pricing Agent responsibilities:
    - Receive product recommendations from Technical Agent
    - Assign unit prices from pricing table
    - Assign test costs from services price table
    - Consolidate total material and services costs
    """
    try:
        data = request.json
        product_recommendations = data.get('product_recommendations', [])
        tests_required = data.get('tests_required', [])
        rfp_id = data.get('rfp_id', 'RFP_PRICING')
        
        if not product_recommendations and not tests_required:
            return jsonify({'error': 'No products or tests provided'}), 400
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.master_agent:
            return jsonify({'error': 'Agent system not available'}), 500
        
        # Create pricing input
        pricing_input = {
            'rfp_id': rfp_id,
            'product_recommendations': product_recommendations,
            'tests_required': tests_required
        }
        
        # Run pricing agent
        pricing_agent = workflow_manager.master_agent.pricing_agent
        result = pricing_agent.calculate_pricing(pricing_input)
        
        return jsonify({
            'success': True,
            'rfp_id': rfp_id,
            'pricing': result
        }), 200
        
    except Exception as e:
        logger.error(f"Pricing calculation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/sales/scan', methods=['POST'])
def run_sales_scan():
    """
    Run Sales Agent to scan for RFPs
    
    Sales Agent responsibilities:
    - Scan provided URLs for RFP information
    - Identify RFPs with due dates within 3 months
    - Select one RFP for response preparation
    """
    try:
        data = request.json
        urls = data.get('urls', [])
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.master_agent:
            return jsonify({'error': 'Agent system not available'}), 500
        
        # Run sales agent
        sales_agent = workflow_manager.master_agent.sales_agent
        selected_rfp = sales_agent.select_rfp_for_response(urls)
        
        return jsonify({
            'success': True,
            'selected_rfp': selected_rfp
        }), 200
        
    except Exception as e:
        logger.error(f"Sales scan error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/process-rfp', methods=['POST'])
def process_rfp_with_agents():
    """
    Process an uploaded RFP through the full agent pipeline
    
    Complete Flow:
    1. Upload PDF → extract text → parse requirements
    2. Sales Agent selects RFP (if URLs provided) or uses uploaded RFP
    3. Master Agent prepares contextual summaries
    4. Technical Agent analyzes products → top 3 OEM recommendations
    5. Pricing Agent calculates costs
    6. Master Agent consolidates final response
    7. Generate bid document
    """
    try:
        # Handle file upload
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files supported'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Get vendor info
        vendor_info = {
            'vendor_id': request.form.get('vendor_id', 'VENDOR_001'),
            'vendor_name': request.form.get('vendor_name', 'Default Vendor'),
            'address': request.form.get('address', ''),
            'contact': request.form.get('contact', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', ''),
            'gstin': request.form.get('gstin', ''),
        }
        
        if not WORKFLOW_AVAILABLE or not workflow_manager:
            return jsonify({'error': 'Workflow manager not available'}), 500
        
        # Process through workflow with agents enabled
        result = workflow_manager.process_rfp(
            pdf_path=upload_path,
            vendor_info=vendor_info,
            use_agents=True  # Force agent processing
        )
        
        # Add agent-specific response formatting
        agent_response = {
            'workflow_id': result.get('workflow_id'),
            'status': result.get('status'),
            'stages': {}
        }
        
        if result.get('stages'):
            stages = result.get('stages', {})
            
            # Format agent processing results
            if stages.get('agents'):
                agent_data = stages['agents']
                agent_response['agent_processing'] = {
                    'available': agent_data.get('available', False),
                    'conversation_id': agent_data.get('conversation_id'),
                    'scope_of_supply': agent_data.get('scope_of_supply', []),
                    'oem_recommendations': agent_data.get('oem_recommendations', []),
                    'test_costs': agent_data.get('test_costs', []),
                    'pricing': {
                        'total_material_cost': agent_data.get('total_material_cost', 0),
                        'total_services_cost': agent_data.get('total_services_cost', 0),
                        'grand_total': agent_data.get('grand_total', 0)
                    },
                    'overall_spec_match': agent_data.get('overall_spec_match', 0),
                    'recommendation': agent_data.get('recommendation', ''),
                    'compliance_checklist': agent_data.get('compliance_checklist', [])
                }
            
            # Include other stage results
            if stages.get('matching'):
                agent_response['stages']['matching'] = {
                    'requirements_count': len(stages['matching'].get('matched_requirements', [])),
                    'avg_match_score': stages['matching'].get('avg_match_score', 0)
                }
            
            if stages.get('pricing'):
                agent_response['stages']['pricing'] = stages['pricing']
            
            if stages.get('bid_generation'):
                agent_response['stages']['bid_generation'] = stages['bid_generation']
        
        return jsonify({
            'success': result.get('status') == 'completed',
            'result': agent_response,
            'full_workflow': result
        }), 200 if result.get('status') == 'completed' else 400
        
    except Exception as e:
        logger.error(f"Agent RFP processing error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/pipeline/full', methods=['POST'])
def pipeline_full_process():
    """
    Process RFP through the central pipeline connector.
    Full end-to-end: Extract → Match → Price → Comply → Audit → Analytics → Bid
    """
    if not PIPELINE_AVAILABLE:
        return jsonify({'error': 'Pipeline connector not available'}), 500

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400

        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        vendor_info = {
            'vendor_id': request.form.get('vendor_id', 'VENDOR_001'),
            'vendor_name': request.form.get('vendor_name', 'Default Vendor'),
            'address': request.form.get('address', ''),
            'email': request.form.get('email', ''),
            'gstin': request.form.get('gstin', ''),
        }
        use_agents = request.form.get('use_agents', 'false').lower() == 'true'

        executor = create_pipeline()
        ctx = executor.run(
            pdf_path=upload_path,
            vendor_info=vendor_info,
            use_agents=use_agents,
        )

        return jsonify({
            'success': ctx.status in ('completed', 'partial'),
            'pipeline': ctx.to_dict(),
        })

    except Exception as e:
        logger.error(f"Pipeline processing error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/pipeline/from-text', methods=['POST'])
def pipeline_from_text():
    """Process RFP from pre-extracted text through the pipeline"""
    if not PIPELINE_AVAILABLE:
        return jsonify({'error': 'Pipeline connector not available'}), 500

    try:
        data = request.json or {}
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        vendor_info = data.get('vendor_info', {})
        result = run_full_pipeline(text=text, vendor_info=vendor_info)
        return jsonify({'success': True, 'pipeline': result})

    except Exception as e:
        logger.error(f"Pipeline from-text error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/specs/calculate-testing', methods=['POST'])
def calculate_testing_costs():
    """Calculate testing costs for a product specification"""
    try:
        data = request.json
        cable_size = data.get('cable_size', 4)
        voltage_class = data.get('voltage_class', 'LT')
        quantity = data.get('quantity', 1000)
        
        if not WORKFLOW_AVAILABLE or not workflow_manager or not workflow_manager.spec_calculator:
            return jsonify({'error': 'Spec calculator not available'}), 500
        
        costs = workflow_manager.spec_calculator.calculate_testing_costs(
            cable_size=cable_size,
            voltage_class=voltage_class,
            quantity_meters=quantity
        )
        
        return jsonify({
            'success': True,
            'costs': costs
        }), 200
        
    except Exception as e:
        logger.error(f"Testing cost calculation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/integration/status', methods=['GET'])
def get_integration_status():
    """Get status of all integrated modules"""
    status = {
        'pdf_extraction': {
            'available': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.pdf_manager is not None,
            'terms_matcher': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.terms_matcher is not None,
        },
        'spec_comparer': {
            'available': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.spec_matcher is not None,
            'product_db': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.product_db is not None,
            'calculator': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.spec_calculator is not None,
        },
        'agents': {
            'available': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.master_agent is not None,
        },
        'bid_generation': {
            'templates': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.bid_template_manager is not None,
            'pdf_generator': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.pdf_generator is not None,
            'excel_generator': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.excel_generator is not None,
            'price_calculator': WORKFLOW_AVAILABLE and workflow_manager and workflow_manager.price_calculator is not None,
        }
    }
    
    # Add database stats if available
    if WORKFLOW_AVAILABLE and workflow_manager:
        if workflow_manager.product_db:
            try:
                products = workflow_manager.product_db.get_all_products()
                oems = workflow_manager.product_db.get_oem_list()
                status['spec_comparer']['products_count'] = len(products)
                status['spec_comparer']['oems_count'] = len(oems)
                status['spec_comparer']['oems'] = oems
            except:
                pass
        
        if workflow_manager.terms_matcher:
            try:
                info = workflow_manager.terms_matcher.get_database_info()
                status['pdf_extraction']['terms_count'] = info.get('total_terms', 0)
            except:
                pass
    
    return jsonify({
        'success': True,
        'status': status
    }), 200


# ==================== FRONTEND ROUTES ====================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/upload-rfp')
def upload_rfp_page():
    """RFP upload page"""
    return render_template('upload_rfp.html')


@app.route('/bids')
def bids_page():
    """Bids list page"""
    return render_template('bids.html')


@app.route('/bids/<bid_id>')
def bid_detail_page(bid_id):
    """Bid detail page"""
    return render_template('bid_detail.html', bid_id=bid_id)


@app.route('/create-bid')
def create_bid_page():
    """Create bid page"""
    return render_template('create_bid.html')


@app.route('/approvals')
def approvals_page():
    """Approvals page"""
    return render_template('approvals.html')


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5006)
