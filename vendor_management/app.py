"""
Vendor Management Flask App
Web interface for vendor management, performance tracking, and communication
"""

from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import sys

# Performance Integration
try:
    perf_path = str(Path(__file__).parent.parent)
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from performance.integration import integrate_flask_app, init_performance
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    print(f"Performance integration not available: {e}")

# Import vendor modules (absolute imports from vendor_management)
from pathlib import Path

# Add vendor_management to path
sys.path.insert(0, str(Path(__file__).parent))
# Add parent directory to path for audit_trail, etc
sys.path.insert(0, str(Path(__file__).parent.parent))

from vendor_database import get_vendor_database, VendorProfile
from vendor_performance import get_performance_tracker, DeliveryMetric, QualityMetric
from vendor_rating import get_rating_engine, VendorRating
from vendor_communication import get_communication_manager, Message, MessageType
from oem_api_routes import oem_bp, create_oem_database

# Import integration modules
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'audit_and_trailing'))
    from audit_trail import get_audit_logger, AuditEntityType, AuditAction
except ImportError:
    pass

try:
    from compliance_checker import get_compliance_scorer
except ImportError:
    pass

try:
    from price_optimization import get_price_analytics
except ImportError:
    pass


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize Performance System
if PERFORMANCE_AVAILABLE:
    try:
        integrate_flask_app(app)
        logging.info("✅ Performance system integrated")
    except Exception as e:
        logging.warning(f"Performance integration failed: {e}")

# Register OEM blueprint
app.register_blueprint(oem_bp)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize managers
vendor_db = get_vendor_database()
performance_tracker = get_performance_tracker()
rating_engine = get_rating_engine()
communication_manager = get_communication_manager()

# Initialize OEM database
try:
    create_oem_database()
except Exception as e:
    logger.warning(f"OEM database initialization: {e}")

try:
    audit_logger = get_audit_logger()
except:
    audit_logger = None


# ============= VENDOR MANAGEMENT ROUTES =============

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Get all vendors"""
    try:
        status = request.args.get('status')
        vendors = vendor_db.list_vendors(status=status, limit=100)
        return jsonify({
            'success': True,
            'count': len(vendors),
            'vendors': vendors
        })
    except Exception as e:
        logger.error(f"Error fetching vendors: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vendors/<vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    """Get vendor details"""
    try:
        vendor = vendor_db.get_vendor(vendor_id)
        if not vendor:
            return jsonify({'success': False, 'error': 'Vendor not found'}), 404
        
        # Get performance metrics
        performance = performance_tracker.get_overall_performance(vendor_id)
        
        # Get rating
        rating = rating_engine.get_vendor_rating(vendor_id)
        badges = rating_engine.get_vendor_badges(vendor_id)
        
        vendor['performance'] = performance
        vendor['rating'] = rating
        vendor['badges'] = badges
        
        return jsonify({'success': True, 'vendor': vendor})
    except Exception as e:
        logger.error(f"Error fetching vendor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vendors', methods=['POST'])
def create_vendor():
    """Create new vendor"""
    try:
        data = request.json
        
        vendor = VendorProfile(
            vendor_id=data.get('vendor_id'),
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            gst_number=data.get('gst_number'),
            pan_number=data.get('pan_number'),
            website=data.get('website'),
            product_categories=data.get('product_categories', []),
            min_order_value=float(data.get('min_order_value', 0)),
            delivery_locations=data.get('delivery_locations', [])
        )
        
        if vendor_db.create_vendor(vendor):
            # Log to audit trail
            if audit_logger:
                audit_logger.log_create(
                    user_id=request.remote_addr,
                    entity_type=AuditEntityType.VENDOR,
                    entity_id=vendor.vendor_id,
                    new_value={'name': vendor.name, 'email': vendor.email}
                )
            
            return jsonify({'success': True, 'vendor_id': vendor.vendor_id}), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create vendor'}), 400
    except Exception as e:
        logger.error(f"Error creating vendor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vendors/<vendor_id>', methods=['PUT'])
def update_vendor(vendor_id):
    """Update vendor"""
    try:
        data = request.json
        updates = {}
        
        for key in ['name', 'email', 'phone', 'address', 'city', 'state', 'pincode', 'status']:
            if key in data:
                updates[key] = data[key]
        
        if vendor_db.update_vendor(vendor_id, updates):
            # Log to audit trail
            if audit_logger:
                audit_logger.log_update(
                    user_id=request.remote_addr,
                    entity_type=AuditEntityType.VENDOR,
                    entity_id=vendor_id,
                    old_value=vendor_db.get_vendor(vendor_id),
                    new_value=updates
                )
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Update failed'}), 400
    except Exception as e:
        logger.error(f"Error updating vendor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vendors/<vendor_id>', methods=['DELETE'])
def delete_vendor(vendor_id):
    """Delete vendor (soft delete)"""
    try:
        if vendor_db.delete_vendor(vendor_id):
            if audit_logger:
                audit_logger.log_delete(
                    user_id=request.remote_addr,
                    entity_type=AuditEntityType.VENDOR,
                    entity_id=vendor_id
                )
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Delete failed'}), 400
    except Exception as e:
        logger.error(f"Error deleting vendor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vendors/search', methods=['GET'])
def search_vendors():
    """Search vendors"""
    try:
        keyword = request.args.get('q', '')
        if not keyword:
            return jsonify({'success': False, 'error': 'No search term'}), 400
        
        vendors = vendor_db.search_vendors(keyword)
        return jsonify({'success': True, 'count': len(vendors), 'vendors': vendors})
    except Exception as e:
        logger.error(f"Error searching vendors: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= PERFORMANCE ROUTES =============

@app.route('/api/performance/<vendor_id>', methods=['GET'])
def get_performance(vendor_id):
    """Get vendor performance metrics"""
    try:
        days = request.args.get('days', 90, type=int)
        performance = performance_tracker.get_overall_performance(vendor_id, days)
        return jsonify({'success': True, 'performance': performance})
    except Exception as e:
        logger.error(f"Error fetching performance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/performance/<vendor_id>/delivery', methods=['POST'])
def log_delivery(vendor_id):
    """Log delivery metric"""
    try:
        data = request.json
        
        metric = DeliveryMetric(
            vendor_id=vendor_id,
            order_id=data.get('order_id'),
            promised_date=datetime.fromisoformat(data.get('promised_date')),
            actual_date=datetime.fromisoformat(data.get('actual_date')),
            days_early_late=int(data.get('days_early_late', 0)),
            status=data.get('status', 'ON_TIME')
        )
        
        if performance_tracker.log_delivery(metric):
            if audit_logger:
                audit_logger.log_create(
                    user_id=request.remote_addr,
                    entity_type=AuditEntityType.VENDOR,
                    entity_id=vendor_id,
                    new_value={'delivery_order': data.get('order_id')}
                )
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to log delivery'}), 400
    except Exception as e:
        logger.error(f"Error logging delivery: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/performance/<vendor_id>/quality', methods=['POST'])
def log_quality(vendor_id):
    """Log quality metric"""
    try:
        data = request.json
        
        metric = QualityMetric(
            vendor_id=vendor_id,
            product_id=data.get('product_id'),
            order_id=data.get('order_id'),
            defect_count=int(data.get('defect_count', 0)),
            total_units=int(data.get('total_units', 0)),
            defect_rate=float(data.get('defect_rate', 0)),
            severity=data.get('severity', 'LOW')
        )
        
        if performance_tracker.log_quality(metric):
            if audit_logger:
                audit_logger.log_create(
                    user_id=request.remote_addr,
                    entity_type=AuditEntityType.VENDOR,
                    entity_id=vendor_id,
                    new_value={'quality_check': data.get('order_id')}
                )
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to log quality'}), 400
    except Exception as e:
        logger.error(f"Error logging quality: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= RATING ROUTES =============

@app.route('/api/ratings/<vendor_id>', methods=['GET'])
def get_rating(vendor_id):
    """Get vendor rating"""
    try:
        rating = rating_engine.get_vendor_rating(vendor_id)
        history = rating_engine.get_rating_history(vendor_id, limit=12)
        badges = rating_engine.get_vendor_badges(vendor_id)
        
        return jsonify({
            'success': True,
            'rating': rating,
            'history': history,
            'badges': badges
        })
    except Exception as e:
        logger.error(f"Error fetching rating: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ratings', methods=['GET'])
def get_vendor_rankings():
    """Get vendor rankings"""
    try:
        top_n = request.args.get('top_n', 10, type=int)
        rankings = rating_engine.rank_vendors(top_n=top_n)
        return jsonify({'success': True, 'rankings': rankings})
    except Exception as e:
        logger.error(f"Error fetching rankings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ratings/<vendor_id>', methods=['POST'])
def record_rating(vendor_id):
    """Record vendor rating"""
    try:
        data = request.json
        
        rating = VendorRating(
            vendor_id=vendor_id,
            rating_date=datetime.now(),
            delivery_score=float(data.get('delivery_score', 0)),
            quality_score=float(data.get('quality_score', 0)),
            response_score=float(data.get('response_score', 0)),
            compliance_score=float(data.get('compliance_score', 0)),
            price_score=float(data.get('price_score', 0)),
            overall_rating=0  # Will be calculated
        )
        
        # Calculate overall rating
        rating.overall_rating = rating_engine.calculate_rating(
            rating.delivery_score,
            rating.quality_score,
            rating.response_score,
            rating.compliance_score,
            rating.price_score
        )
        
        # Assign badge
        badge = rating_engine.assign_badge(vendor_id, rating.overall_rating)
        rating.badge = badge
        
        if rating_engine.record_rating(rating):
            if audit_logger:
                audit_logger.log_update(
                    user_id=request.remote_addr,
                    entity_type=AuditEntityType.VENDOR,
                    entity_id=vendor_id,
                    new_value={'rating': rating.overall_rating}
                )
            return jsonify({'success': True, 'overall_rating': rating.overall_rating, 'badge': badge.value if badge else None})
        else:
            return jsonify({'success': False, 'error': 'Failed to record rating'}), 400
    except Exception as e:
        logger.error(f"Error recording rating: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= COMMUNICATION ROUTES =============

@app.route('/api/communications/<vendor_id>', methods=['GET'])
def get_vendor_communications(vendor_id):
    """Get vendor communications"""
    try:
        messages = communication_manager.get_vendor_messages(vendor_id, limit=50)
        return jsonify({'success': True, 'count': len(messages), 'messages': messages})
    except Exception as e:
        logger.error(f"Error fetching communications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/communications/<vendor_id>', methods=['POST'])
def send_communication(vendor_id):
    """Send message to vendor"""
    try:
        data = request.json
        
        message = Message(
            message_id=f"MSG_{int(datetime.now().timestamp())}",
            vendor_id=vendor_id,
            message_type=MessageType[data.get('message_type', 'INQUIRY').upper()],
            sender=data.get('sender', 'system@company.com'),
            recipient=data.get('recipient'),
            subject=data.get('subject'),
            body=data.get('body'),
            sent_date=datetime.now()
        )
        
        if communication_manager.send_message(message):
            if audit_logger:
                audit_logger.log_create(
                    user_id=request.remote_addr,
                    entity_type=AuditEntityType.VENDOR,
                    entity_id=vendor_id,
                    new_value={'message': message.message_id}
                )
            return jsonify({'success': True, 'message_id': message.message_id})
        else:
            return jsonify({'success': False, 'error': 'Failed to send message'}), 400
    except Exception as e:
        logger.error(f"Error sending communication: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= FRONTEND ROUTES =============

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/vendors')
def vendors_page():
    """Vendors list page"""
    return render_template('vendors.html')


@app.route('/vendors/<vendor_id>')
def vendor_detail(vendor_id):
    """Vendor detail page"""
    return render_template('vendor_detail.html', vendor_id=vendor_id)


@app.route('/performance')
def performance_page():
    """Performance dashboard"""
    return render_template('performance.html')


@app.route('/ratings')
def ratings_page():
    """Ratings and rankings page"""
    return render_template('ratings.html')


@app.route('/communications')
def communications_page():
    """Communications page"""
    return render_template('communications.html')


# ============= HEALTH CHECK =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'vendor-management'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5005)
