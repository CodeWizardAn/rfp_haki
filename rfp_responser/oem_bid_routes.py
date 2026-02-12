"""
OEM Bid Management API Routes
Extended Flask routes for OEM-specific bid pricing and management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import json

# Import OEM pricing modules
from bid_oem_pricing import (
    OEMPriceCalculator, OEMPricingModel, VolumeTier, NRECost,
    setup_default_oem_pricing
)
from bid_templates import (
    BidTemplate, BidItem, BidDocument, BidFormat, 
    OEMCapacity, OEMCertification, OEMLeadTime, NREBreakdown
)

# Create Blueprint
oem_bid_bp = Blueprint('oem_bids', __name__, url_prefix='/api/oem-bids')


# ==================== OEM BID CREATION ENDPOINTS ====================

@oem_bid_bp.route('/create', methods=['POST'])
def create_oem_bid():
    """Create new OEM bid with pricing"""
    try:
        data = request.json
        
        bid = BidDocument(
            bid_id=data.get('bid_id', f"OEM_BID_{datetime.now().timestamp()}"),
            rfp_id=data.get('rfp_id'),
            vendor_id=data.get('vendor_id'),
            created_date=datetime.now(),
            bidder_company=data.get('bidder_company'),
            bid_amount=0,  # Will be calculated
            status='DRAFT'
        )
        
        # Store bid
        conn = sqlite3.connect('oem_bids.db', check_same_thread=False)
        cursor = conn.cursor()
        
        bid_json = json.dumps(bid.__dict__, default=str)
        cursor.execute('''
            INSERT INTO oem_bids (bid_id, rfp_id, vendor_id, bid_data, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (bid.bid_id, bid.rfp_id, data.get('vendor_id'), bid_json, 'DRAFT'))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'bid_id': bid.bid_id,
            'message': 'OEM bid created successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@oem_bid_bp.route('/<bid_id>/items', methods=['POST'])
def add_bid_item(bid_id):
    """Add item to OEM bid"""
    try:
        data = request.json
        
        item = BidItem(
            item_id=data.get('item_id', f"ITEM_{datetime.now().timestamp()}"),
            product_code=data.get('product_code'),
            product_name=data.get('product_name'),
            description=data.get('description'),
            quantity=data.get('quantity'),
            unit_price=data.get('unit_price'),
            unit=data.get('unit', 'pieces'),
            moq=data.get('moq', 1),  # OEM-specific
            lead_time_days=data.get('lead_time_days', 0),  # OEM-specific
            nre_cost=data.get('nre_cost', 0),  # OEM-specific
            technical_spec_id=data.get('technical_spec_id', '')  # OEM-specific
        )
        
        # Store item
        conn = sqlite3.connect('oem_bids.db', check_same_thread=False)
        cursor = conn.cursor()
        
        item_json = json.dumps(item.__dict__, default=str)
        cursor.execute('''
            INSERT INTO oem_bid_items (item_id, bid_id, item_data)
            VALUES (?, ?, ?)
        ''', (item.item_id, bid_id, item_json))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'item_id': item.item_id,
            'message': 'Item added successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== OEM PRICING CALCULATION ====================

@oem_bid_bp.route('/<bid_id>/calculate-nre', methods=['POST'])
def calculate_nre_pricing(bid_id):
    """Calculate NRE plus unit pricing for OEM bid"""
    try:
        data = request.json
        
        # Create calculator
        calculator = OEMPriceCalculator()
        
        # Setup default pricing or use provided tiers
        if data.get('use_default_pricing'):
            setup_default_oem_pricing(calculator)
        else:
            # Add custom volume tiers
            for tier_data in data.get('volume_tiers', []):
                tier = VolumeTier(
                    qty_from=tier_data.get('qty_from'),
                    qty_to=tier_data.get('qty_to'),
                    unit_price=tier_data.get('unit_price'),
                    moq=tier_data.get('moq', 1),
                    lead_time_days=tier_data.get('lead_time_days', 0),
                    expedited_lead_time_days=tier_data.get('expedited_lead_time_days', 0),
                    express_lead_time_days=tier_data.get('express_lead_time_days', 0)
                )
                calculator.add_volume_tier(data.get('product_id'), tier)
        
        # Create NRE cost breakdown
        nre_data = data.get('nre_cost', {})
        nre = NRECost(
            engineering_hours=nre_data.get('engineering_hours', 0),
            hourly_rate=nre_data.get('hourly_rate', 1500),
            tooling_cost=nre_data.get('tooling_cost', 0),
            setup_cost=nre_data.get('setup_cost', 0),
            testing_cost=nre_data.get('testing_cost', 0),
            documentation_cost=nre_data.get('documentation_cost', 0),
            design_cost=nre_data.get('design_cost', 0),
            certification_cost=nre_data.get('certification_cost', 0)
        )
        
        # Calculate pricing
        result = calculator.calculate_nre_plus_unit(
            product_id=data.get('product_id'),
            quantity=data.get('quantity'),
            base_unit_price=data.get('base_unit_price'),
            nre_cost=nre,
            discount_percent=data.get('discount_percent', 0)
        )
        
        return jsonify({
            'success': True,
            'bid_id': bid_id,
            'pricing': {
                'unit_subtotal': result['unit_subtotal'],
                'nre_cost': result['nre_cost'],
                'tax_amount': result['tax_amount'],
                'grand_total': result['grand_total'],
                'cost_per_unit_with_nre': result['cost_per_unit_with_nre'],
                'lead_time_days': result['lead_time_days']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@oem_bid_bp.route('/<bid_id>/apply-volume-tier', methods=['POST'])
def apply_volume_tier(bid_id):
    """Apply volume-based tiered pricing to OEM bid"""
    try:
        data = request.json
        
        calculator = OEMPriceCalculator()
        
        # Add volume tiers
        for tier_data in data.get('volume_tiers', []):
            tier = VolumeTier(
                qty_from=tier_data.get('qty_from'),
                qty_to=tier_data.get('qty_to'),
                unit_price=tier_data.get('unit_price'),
                moq=tier_data.get('moq', 1),
                lead_time_days=tier_data.get('lead_time_days', 0)
            )
            calculator.add_volume_tier(data.get('product_id'), tier)
        
        # Calculate tiered pricing
        result = calculator.calculate_volume_tiered(
            product_id=data.get('product_id'),
            quantity=data.get('quantity')
        )
        
        return jsonify({
            'success': True,
            'bid_id': bid_id,
            'pricing': {
                'applicable_tier': {
                    'qty_range': f"{result['tier'].qty_from}-{result['tier'].qty_to}",
                    'unit_price': result['tier'].unit_price
                },
                'unit_subtotal': result['unit_subtotal'],
                'tax_amount': result['tax_amount'],
                'grand_total': result['grand_total'],
                'cost_per_unit': result['cost_per_unit'],
                'lead_time_days': result['lead_time_days']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@oem_bid_bp.route('/<bid_id>/calculate-hybrid', methods=['POST'])
def calculate_hybrid_pricing(bid_id):
    """Calculate hybrid (NRE + volume tiered) pricing for OEM bid"""
    try:
        data = request.json
        
        calculator = OEMPriceCalculator()
        
        # Setup volume tiers
        for tier_data in data.get('volume_tiers', []):
            tier = VolumeTier(
                qty_from=tier_data.get('qty_from'),
                qty_to=tier_data.get('qty_to'),
                unit_price=tier_data.get('unit_price'),
                moq=tier_data.get('moq', 1),
                lead_time_days=tier_data.get('lead_time_days', 0)
            )
            calculator.add_volume_tier(data.get('product_id'), tier)
        
        # Create NRE cost
        nre_data = data.get('nre_cost', {})
        nre = NRECost(
            engineering_hours=nre_data.get('engineering_hours', 0),
            hourly_rate=nre_data.get('hourly_rate', 1500),
            tooling_cost=nre_data.get('tooling_cost', 0),
            setup_cost=nre_data.get('setup_cost', 0),
            testing_cost=nre_data.get('testing_cost', 0),
            documentation_cost=nre_data.get('documentation_cost', 0),
            design_cost=nre_data.get('design_cost', 0),
            certification_cost=nre_data.get('certification_cost', 0)
        )
        
        # Calculate hybrid
        result = calculator.calculate_hybrid(
            product_id=data.get('product_id'),
            quantity=data.get('quantity'),
            nre_cost=nre,
            nre_amortization_percent=data.get('nre_amortization_percent', 50)
        )
        
        return jsonify({
            'success': True,
            'bid_id': bid_id,
            'pricing': result
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== OEM BID RETRIEVAL & MANAGEMENT ====================

@oem_bid_bp.route('/<bid_id>', methods=['GET'])
def get_oem_bid(bid_id):
    """Get OEM bid details"""
    try:
        conn = sqlite3.connect('oem_bids.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT bid_data FROM oem_bids WHERE bid_id = ?', (bid_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'error': 'Bid not found'}), 404
        
        bid_data = json.loads(result[0])
        
        # Get bid items
        cursor.execute('SELECT item_data FROM oem_bid_items WHERE bid_id = ?', (bid_id,))
        bid_data['items'] = [json.loads(row[0]) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'bid': bid_data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@oem_bid_bp.route('/<bid_id>/pricing-breakdown', methods=['GET'])
def get_pricing_breakdown(bid_id):
    """Get detailed pricing breakdown for OEM bid"""
    try:
        conn = sqlite3.connect('oem_bids.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Get bid
        cursor.execute('SELECT bid_data FROM oem_bids WHERE bid_id = ?', (bid_id,))
        bid_result = cursor.fetchone()
        
        if not bid_result:
            conn.close()
            return jsonify({'error': 'Bid not found'}), 404
        
        bid_data = json.loads(bid_result[0])
        
        # Get items
        cursor.execute('SELECT item_data FROM oem_bid_items WHERE bid_id = ?', (bid_id,))
        items = [json.loads(row[0]) for row in cursor.fetchall()]
        
        conn.close()
        
        # Calculate breakdown
        breakdown = {
            'bid_id': bid_id,
            'items': items,
            'item_count': len(items),
            'summary': {
                'total_quantity': sum(item.get('quantity', 0) for item in items),
                'total_nre_cost': sum(item.get('nre_cost', 0) for item in items),
                'subtotal': sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items),
                'tax_percent': 18,
                'shipping_cost': 5000,
                'insurance_percent': 2
            }
        }
        
        # Calculate totals
        subtotal = breakdown['summary']['subtotal']
        nre_total = breakdown['summary']['total_nre_cost']
        tax = (subtotal + nre_total) * (breakdown['summary']['tax_percent'] / 100)
        shipping = breakdown['summary']['shipping_cost']
        insurance = (subtotal + nre_total + tax + shipping) * (breakdown['summary']['insurance_percent'] / 100)
        
        breakdown['summary']['tax_amount'] = tax
        breakdown['summary']['insurance_amount'] = insurance
        breakdown['summary']['grand_total'] = subtotal + nre_total + tax + shipping + insurance
        
        return jsonify(breakdown), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@oem_bid_bp.route('/<bid_id>/submit', methods=['POST'])
def submit_oem_bid(bid_id):
    """Submit OEM bid for approval"""
    try:
        conn = sqlite3.connect('oem_bids.db', check_same_thread=False)
        cursor = conn.cursor()
        
        # Update bid status
        cursor.execute('''
            UPDATE oem_bids 
            SET status = 'SUBMITTED', updated_date = ?
            WHERE bid_id = ?
        ''', (datetime.now(), bid_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'bid_id': bid_id,
            'status': 'SUBMITTED',
            'message': 'OEM bid submitted successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@oem_bid_bp.route('/list', methods=['GET'])
def list_oem_bids():
    """List all OEM bids"""
    try:
        vendor_id = request.args.get('vendor_id')
        status = request.args.get('status')
        
        conn = sqlite3.connect('oem_bids.db', check_same_thread=False)
        cursor = conn.cursor()
        
        query = 'SELECT bid_id, bid_data, status FROM oem_bids WHERE 1=1'
        params = []
        
        if vendor_id:
            query += ' AND vendor_id = ?'
            params.append(vendor_id)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY created_date DESC LIMIT 50'
        
        cursor.execute(query, params)
        bids = []
        for row in cursor.fetchall():
            bid_data = json.loads(row[1])
            bid_data['bid_id'] = row[0]
            bid_data['status'] = row[2]
            bids.append(bid_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(bids),
            'bids': bids
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@oem_bid_bp.route('/health', methods=['GET'])
def oem_bid_health():
    """Health check for OEM Bid API"""
    return jsonify({
        'status': 'healthy',
        'service': 'OEM Bid Management API',
        'endpoints': ['create', 'items', 'calculate-nre', 'pricing-breakdown', 'submit']
    }), 200


def create_oem_bid_database():
    """Initialize OEM bid database"""
    conn = sqlite3.connect('oem_bids.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oem_bids (
            bid_id TEXT PRIMARY KEY,
            rfp_id TEXT,
            vendor_id TEXT,
            bid_data TEXT,
            status TEXT DEFAULT 'DRAFT',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_date DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oem_bid_items (
            item_id TEXT PRIMARY KEY,
            bid_id TEXT,
            item_data TEXT,
            FOREIGN KEY (bid_id) REFERENCES oem_bids(bid_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oem_pricing_configs (
            config_id TEXT PRIMARY KEY,
            product_id TEXT,
            pricing_model TEXT,
            pricing_data TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
