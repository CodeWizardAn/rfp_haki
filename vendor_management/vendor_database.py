"""
Vendor Database Module
CRUD operations and vendor data management
"""

import json
import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging


@dataclass
class VendorProfile:
    """Complete vendor profile"""
    vendor_id: str
    name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    pincode: str
    gst_number: str
    pan_number: str
    website: str = None
    registration_date: datetime = None
    status: str = "ACTIVE"  # ACTIVE, INACTIVE, SUSPENDED
    product_categories: List[str] = None
    min_order_value: float = 0
    payment_terms: str = "Net 30"
    delivery_locations: List[str] = None
    notes: str = ""

    def __post_init__(self):
        if self.registration_date is None:
            self.registration_date = datetime.now()
        if self.product_categories is None:
            self.product_categories = []
        if self.delivery_locations is None:
            self.delivery_locations = []


class VendorDatabase:
    """SQLite database for vendor management"""

    def __init__(self, db_path: str = None):
        """Initialize vendor database"""
        if db_path is None:
            # Use centralized database path
            from db_paths import get_vendors_db_path
            db_path = get_vendors_db_path()
        
        self.db_path = db_path
        self.connection = None
        self.logger = logging.getLogger('vendor_db')
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = self.connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                pincode TEXT,
                gst_number TEXT UNIQUE,
                pan_number TEXT UNIQUE,
                website TEXT,
                registration_date DATETIME,
                status TEXT DEFAULT 'ACTIVE',
                product_categories TEXT,
                min_order_value REAL,
                payment_terms TEXT,
                delivery_locations TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_vendor_name 
            ON vendors(name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_vendor_status 
            ON vendors(status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_vendor_email 
            ON vendors(email)
        ''')

        self.connection.commit()
        self.logger.info(f"✅ Vendor database initialized at {self.db_path}")

    def create_vendor(self, vendor: VendorProfile) -> bool:
        """Create new vendor"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO vendors (
                    vendor_id, name, email, phone, address, city, state,
                    pincode, gst_number, pan_number, website, registration_date,
                    status, product_categories, min_order_value, payment_terms,
                    delivery_locations, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vendor.vendor_id, vendor.name, vendor.email, vendor.phone,
                vendor.address, vendor.city, vendor.state, vendor.pincode,
                vendor.gst_number, vendor.pan_number, vendor.website,
                vendor.registration_date.isoformat(), vendor.status,
                json.dumps(vendor.product_categories), vendor.min_order_value,
                vendor.payment_terms, json.dumps(vendor.delivery_locations),
                vendor.notes
            ))
            self.connection.commit()
            self.logger.info(f"Created vendor: {vendor.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create vendor: {e}")
            return False

    def get_vendor(self, vendor_id: str) -> Optional[Dict]:
        """Get vendor by ID"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM vendors WHERE vendor_id = ?', (vendor_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        vendor_dict = dict(zip(columns, row))
        vendor_dict['product_categories'] = json.loads(vendor_dict['product_categories'] or '[]')
        vendor_dict['delivery_locations'] = json.loads(vendor_dict['delivery_locations'] or '[]')
        return vendor_dict

    def get_vendor_by_name(self, name: str) -> Optional[Dict]:
        """Get vendor by name"""
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM vendors WHERE name = ?', (name,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        vendor_dict = dict(zip(columns, row))
        vendor_dict['product_categories'] = json.loads(vendor_dict['product_categories'] or '[]')
        vendor_dict['delivery_locations'] = json.loads(vendor_dict['delivery_locations'] or '[]')
        return vendor_dict

    def list_vendors(self, status: str = None, limit: int = 100) -> List[Dict]:
        """List all vendors"""
        cursor = self.connection.cursor()
        
        if status:
            cursor.execute(
                'SELECT * FROM vendors WHERE status = ? LIMIT ?',
                (status, limit)
            )
        else:
            cursor.execute('SELECT * FROM vendors LIMIT ?', (limit,))
        
        columns = [description[0] for description in cursor.description]
        vendors = []
        for row in cursor.fetchall():
            vendor_dict = dict(zip(columns, row))
            vendor_dict['product_categories'] = json.loads(vendor_dict['product_categories'] or '[]')
            vendor_dict['delivery_locations'] = json.loads(vendor_dict['delivery_locations'] or '[]')
            vendors.append(vendor_dict)
        
        return vendors

    def update_vendor(self, vendor_id: str, updates: Dict) -> bool:
        """Update vendor"""
        try:
            cursor = self.connection.cursor()
            
            # Build update query
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            set_clause += ', updated_at = CURRENT_TIMESTAMP'
            
            values = list(updates.values())
            values.append(vendor_id)
            
            cursor.execute(
                f'UPDATE vendors SET {set_clause} WHERE vendor_id = ?',
                values
            )
            self.connection.commit()
            self.logger.info(f"Updated vendor: {vendor_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update vendor: {e}")
            return False

    def delete_vendor(self, vendor_id: str) -> bool:
        """Soft delete vendor (set status to INACTIVE)"""
        try:
            return self.update_vendor(vendor_id, {'status': 'INACTIVE'})
        except Exception as e:
            self.logger.error(f"Failed to delete vendor: {e}")
            return False

    def search_vendors(self, keyword: str) -> List[Dict]:
        """Search vendors by name, email, or GST"""
        cursor = self.connection.cursor()
        search_term = f"%{keyword}%"
        
        cursor.execute('''
            SELECT * FROM vendors 
            WHERE name LIKE ? OR email LIKE ? OR gst_number LIKE ?
        ''', (search_term, search_term, search_term))
        
        columns = [description[0] for description in cursor.description]
        vendors = []
        for row in cursor.fetchall():
            vendor_dict = dict(zip(columns, row))
            vendor_dict['product_categories'] = json.loads(vendor_dict['product_categories'] or '[]')
            vendor_dict['delivery_locations'] = json.loads(vendor_dict['delivery_locations'] or '[]')
            vendors.append(vendor_dict)
        
        return vendors

    def get_vendor_count(self, status: str = None) -> int:
        """Get total vendor count"""
        cursor = self.connection.cursor()
        
        if status:
            cursor.execute('SELECT COUNT(*) FROM vendors WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT COUNT(*) FROM vendors')
        
        return cursor.fetchone()[0]

    def bulk_import_vendors(self, vendors_data: List[Dict]) -> int:
        """Bulk import vendors from JSON/CSV"""
        imported = 0
        for vendor_data in vendors_data:
            vendor = VendorProfile(**vendor_data)
            if self.create_vendor(vendor):
                imported += 1
        
        self.logger.info(f"Imported {imported}/{len(vendors_data)} vendors")
        return imported

    def export_vendors(self, output_path: str, status: str = None):
        """Export vendors to JSON"""
        vendors = self.list_vendors(status=status, limit=10000)
        
        with open(output_path, 'w') as f:
            json.dump(vendors, f, indent=2, default=str)
        
        self.logger.info(f"Exported {len(vendors)} vendors to {output_path}")

    def close(self):
        """Close database"""
        if self.connection:
            self.connection.close()


# Singleton instance
_vendor_db = None

def get_vendor_database() -> VendorDatabase:
    """Get or create vendor database"""
    global _vendor_db
    if _vendor_db is None:
        _vendor_db = VendorDatabase()
    return _vendor_db


if __name__ == '__main__':
    db = VendorDatabase()

    # Create sample vendors
    vendor1 = VendorProfile(
        vendor_id='V001',
        name='Polycab Industries',
        email='sales@polycab.com',
        phone='022-1234567',
        address='123 Industrial Road',
        city='Mumbai',
        state='Maharashtra',
        pincode='400001',
        gst_number='27AAFCT1234H1Z0',
        pan_number='AAACT1234H',
        website='www.polycab.com',
        product_categories=['Wires', 'Cables', 'Switches'],
        min_order_value=5000,
        delivery_locations=['Mumbai', 'Pune', 'Bangalore']
    )

    if db.create_vendor(vendor1):
        print("✅ Vendor created")
        
        # Get vendor
        vendor = db.get_vendor('V001')
        print(f"Vendor: {vendor['name']}")
        
        # List vendors
        vendors = db.list_vendors()
        print(f"Total vendors: {len(vendors)}")

    db.close()
