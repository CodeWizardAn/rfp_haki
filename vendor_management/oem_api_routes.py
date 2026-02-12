"""
OEM Vendor Management API Routes
Extended Flask routes for OEM vendor management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import json

# Import OEM modules
from oem_vendor_profile import (
    OEMVendorProfile, VendorType, ManufacturingCapability, 
    CertificationType, OEMCapacity, create_sample_oem_vendor
)
from oem_performance_metrics import (
    OEMVendorPerformanceReport, QualityMetric, CapacityMetric,
    DeliveryMetric, ResponsivenessMetric, TechnicalMetric, ComplianceMetric
)

# Create Blueprint
oem_bp = Blueprint('oem_vendors', __name__, url_prefix='/api/oem')


# ==================== OEM VENDOR PROFILE ENDPOINTS ====================

@oem_bp.route('/vendors', methods=['POST'])
def register_oem_vendor():
    """Register new OEM vendor with comprehensive profile"""
    try:
        data = request.json
        
        vendor = OEMVendorProfile(
            vendor_id=data.get('vendor_id', f"OEM_{datetime.now().timestamp()}"),
            name=data.get('name'),
            vendor_type=VendorType[data.get('vendor_type', 'OEM')],
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            gst_number=data.get('gst_number'),
            pan_number=data.get('pan_number'),
            cin_number=data.get('cin_number', ''),
            years_in_business=data.get('years_in_business', 0),
            product_categories=data.get('product_categories', []),
            specialization=data.get('specialization', ''),
            min_order_value=data.get('min_order_value', 0),
            payment_terms=data.get('payment_terms', 'Net 30')
        )
        
        # Store in database
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        vendor_json = json.dumps(vendor.__dict__, default=str)
        cursor.execute('''
            INSERT OR REPLACE INTO oem_vendors (vendor_id, vendor_name, vendor_data, created_date)
            VALUES (?, ?, ?, ?)
        ''', (vendor.vendor_id, vendor.name, vendor_json, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'vendor_id': vendor.vendor_id,
            'message': 'OEM vendor registered successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@oem_bp.route('/vendors/<vendor_id>', methods=['GET'])
def get_oem_vendor(vendor_id):
    """Get complete OEM vendor profile"""
    try:
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT vendor_data FROM oem_vendors WHERE vendor_id = ?', (vendor_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Vendor not found'}), 404
        
        vendor_data = json.loads(result[0])
        return jsonify(vendor_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@oem_bp.route('/vendors/<vendor_id>/capacity', methods=['POST'])
def add_oem_capacity(vendor_id):
    """Add manufacturing capacity for OEM vendor"""
    try:
        data = request.json
        
        capacity = OEMCapacity(
            capacity_id=data.get('capacity_id', f"CAP_{datetime.now().timestamp()}"),
            product_category=data.get('product_category'),
            monthly_capacity_units=data.get('monthly_capacity_units'),
            annual_capacity_units=data.get('annual_capacity_units'),
            shift_count=data.get('shift_count', 1),
            machines_available=data.get('machines_available', 0),
            skilled_workers=data.get('skilled_workers', 0),
            facility_sq_ft=data.get('facility_sq_ft', 0),
            current_utilization_percent=data.get('current_utilization_percent', 0.0),
            min_batch_size=data.get('min_batch_size', 0),
            max_batch_size=data.get('max_batch_size', 0)
        )
        
        # Store capacity
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        capacity_json = json.dumps(capacity.__dict__, default=str)
        cursor.execute('''
            INSERT INTO oem_capacities (capacity_id, vendor_id, capacity_data)
            VALUES (?, ?, ?)
        ''', (capacity.capacity_id, vendor_id, capacity_json))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'capacity_id': capacity.capacity_id,
            'message': 'Capacity added successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@oem_bp.route('/vendors/<vendor_id>/certifications', methods=['POST'])
def add_oem_certification(vendor_id):
    """Add certification for OEM vendor"""
    try:
        data = request.json
        
        # Store certification
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cert_json = json.dumps({
            'cert_id': data.get('cert_id', f"CERT_{datetime.now().timestamp()}"),
            'cert_type': data.get('cert_type'),
            'cert_body': data.get('cert_body'),
            'issue_date': data.get('issue_date'),
            'expiry_date': data.get('expiry_date'),
            'certificate_number': data.get('certificate_number'),
            'compliance_level': data.get('compliance_level', 'COMPLIANT')
        })
        
        cursor.execute('''
            INSERT INTO oem_certifications (vendor_id, cert_data)
            VALUES (?, ?)
        ''', (vendor_id, cert_json))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Certification added successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== OEM PERFORMANCE TRACKING ====================

@oem_bp.route('/vendors/<vendor_id>/performance', methods=['POST'])
def record_oem_performance(vendor_id):
    """Record OEM vendor performance metrics"""
    try:
        data = request.json
        
        report = OEMVendorPerformanceReport(
            report_id=data.get('report_id', f"PERF_{datetime.now().timestamp()}"),
            vendor_id=vendor_id,
            vendor_name=data.get('vendor_name', ''),
            report_period=data.get('report_period', 'MONTHLY'),
            report_date=datetime.now()
        )
        
        # Add quality metrics if provided
        if 'quality_metric' in data:
            qm = data['quality_metric']
            report.quality_metric = QualityMetric(
                metric_id=qm.get('metric_id', f"QM_{datetime.now().timestamp()}"),
                measurement_date=datetime.now(),
                product_category=qm.get('product_category'),
                defect_rate_ppm=qm.get('defect_rate_ppm', 0),
                first_pass_yield_percent=qm.get('first_pass_yield_percent', 100),
                rework_rate_percent=qm.get('rework_rate_percent', 0),
                scrap_rate_percent=qm.get('scrap_rate_percent', 0),
                open_capa_count=qm.get('open_capa_count', 0),
                closed_capa_count=qm.get('closed_capa_count', 0),
                capa_resolution_days=qm.get('capa_resolution_days', 0),
                internal_audit_score=qm.get('internal_audit_score', 0),
                external_audit_score=qm.get('external_audit_score', 0),
                compliance_issues=qm.get('compliance_issues', 0)
            )
        
        # Add capacity metrics if provided
        if 'capacity_metric' in data:
            cm = data['capacity_metric']
            report.capacity_metric = CapacityMetric(
                metric_id=cm.get('metric_id', f"CAP_{datetime.now().timestamp()}"),
                measurement_date=datetime.now(),
                product_category=cm.get('product_category'),
                total_capacity_monthly_units=cm.get('total_capacity_monthly_units', 0),
                current_utilization_units=cm.get('current_utilization_units', 0),
                utilization_percent=cm.get('utilization_percent', 0),
                machines_operational=cm.get('machines_operational', 0),
                machines_total=cm.get('machines_total', 0),
                equipment_downtime_percent=cm.get('equipment_downtime_percent', 0),
                skilled_workers_available=cm.get('skilled_workers_available', 0),
                skilled_workers_total=cm.get('skilled_workers_total', 0),
                worker_efficiency_percent=cm.get('worker_efficiency_percent', 0),
                average_daily_production=cm.get('average_daily_production', 0),
                peak_capacity_achieved_percent=cm.get('peak_capacity_achieved_percent', 0),
                scalability_rating=cm.get('scalability_rating', 'MEDIUM')
            )
        
        # Add delivery metrics if provided
        if 'delivery_metric' in data:
            dm = data['delivery_metric']
            report.delivery_metric = DeliveryMetric(
                metric_id=dm.get('metric_id', f"DM_{datetime.now().timestamp()}"),
                measurement_date=datetime.now(),
                product_category=dm.get('product_category'),
                total_orders=dm.get('total_orders', 0),
                on_time_orders=dm.get('on_time_orders', 0),
                early_orders=dm.get('early_orders', 0),
                late_orders=dm.get('late_orders', 0),
                average_lead_time_days=dm.get('average_lead_time_days', 0),
                promised_vs_actual_variance_days=dm.get('promised_vs_actual_variance_days', 0),
                total_shipments=dm.get('total_shipments', 0),
                damaged_shipments=dm.get('damaged_shipments', 0),
                incomplete_shipments=dm.get('incomplete_shipments', 0),
                complete_documentation_percent=dm.get('complete_documentation_percent', 100),
                invoice_accuracy_percent=dm.get('invoice_accuracy_percent', 100)
            )
        
        # Calculate overall score
        report.calculate_overall_score()
        
        # Store report
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        report_json = json.dumps(report.__dict__, default=str)
        cursor.execute('''
            INSERT INTO oem_performance_reports (report_id, vendor_id, report_data)
            VALUES (?, ?, ?)
        ''', (report.report_id, vendor_id, report_json))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'report_id': report.report_id,
            'overall_score': report.overall_score,
            'performance_rating': report.performance_rating,
            'risk_level': report.risk_level,
            'scores': report.get_scores_by_category()
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@oem_bp.route('/vendors/<vendor_id>/performance', methods=['GET'])
def get_oem_performance(vendor_id):
    """Get OEM vendor performance history"""
    try:
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT report_data FROM oem_performance_reports 
            WHERE vendor_id = ? 
            ORDER BY report_id DESC 
            LIMIT 12
        ''', (vendor_id,))
        
        reports = [json.loads(row[0]) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'vendor_id': vendor_id,
            'report_count': len(reports),
            'reports': reports
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== OEM READINESS & SCORING ====================

@oem_bp.route('/vendors/<vendor_id>/readiness', methods=['GET'])
def get_oem_readiness(vendor_id):
    """Get OEM vendor readiness score and assessment"""
    try:
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('SELECT vendor_data FROM oem_vendors WHERE vendor_id = ?', (vendor_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Vendor not found'}), 404
        
        vendor_data = json.loads(result[0])
        
        # Calculate readiness components
        readiness = {
            'vendor_id': vendor_id,
            'vendor_name': vendor_data.get('name'),
            'assessment_date': datetime.now().isoformat(),
            'components': {
                'Manufacturing Capacity': 'score_placeholder',
                'Certifications': 'score_placeholder',
                'Quality Metrics': 'score_placeholder',
                'Technical Capability': 'score_placeholder',
                'NRE Capability': 'score_placeholder'
            },
            'overall_readiness_score': 0,
            'readiness_level': 'READY',
            'key_strengths': [],
            'areas_for_improvement': []
        }
        
        return jsonify(readiness), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@oem_bp.route('/vendors/<vendor_id>/comparison', methods=['GET'])
def compare_oem_vendors(vendor_id):
    """Compare OEM vendor against industry benchmarks"""
    try:
        # Get vendor performance
        conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT report_data FROM oem_performance_reports 
            WHERE vendor_id = ? 
            ORDER BY report_id DESC 
            LIMIT 1
        ''', (vendor_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'No performance data found'}), 404
        
        vendor_report = json.loads(result[0])
        
        # Industry benchmarks
        benchmarks = {
            'Quality': {
                'industry_average': 82.0,
                'top_quartile': 92.0,
                'vendor_score': vendor_report.get('overall_score', 0)
            },
            'Delivery': {
                'industry_average': 85.0,
                'top_quartile': 95.0,
                'vendor_score': vendor_report.get('overall_score', 0)
            },
            'Capacity': {
                'industry_average': 75.0,
                'top_quartile': 88.0,
                'vendor_score': vendor_report.get('overall_score', 0)
            }
        }
        
        return jsonify({
            'vendor_id': vendor_id,
            'comparison_date': datetime.now().isoformat(),
            'benchmarks': benchmarks
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@oem_bp.route('/health', methods=['GET'])
def oem_api_health():
    """Health check for OEM API"""
    return jsonify({
        'status': 'healthy',
        'service': 'OEM Vendor Management API',
        'endpoints': ['vendors', 'capacity', 'certifications', 'performance', 'readiness']
    }), 200


def create_oem_database():
    """Initialize OEM vendor database"""
    conn = sqlite3.connect('oem_vendors.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oem_vendors (
            vendor_id TEXT PRIMARY KEY,
            vendor_name TEXT NOT NULL,
            vendor_data TEXT,
            created_date DATETIME,
            updated_date DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oem_capacities (
            capacity_id TEXT PRIMARY KEY,
            vendor_id TEXT,
            capacity_data TEXT,
            FOREIGN KEY (vendor_id) REFERENCES oem_vendors(vendor_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oem_certifications (
            cert_id TEXT PRIMARY KEY,
            vendor_id TEXT,
            cert_data TEXT,
            FOREIGN KEY (vendor_id) REFERENCES oem_vendors(vendor_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS oem_performance_reports (
            report_id TEXT PRIMARY KEY,
            vendor_id TEXT,
            report_data TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES oem_vendors(vendor_id)
        )
    ''')
    
    conn.commit()
    conn.close()
