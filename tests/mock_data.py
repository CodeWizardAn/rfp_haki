"""
Mock Data Generators
Generate realistic test data for agents testing
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class MockDataConfig:
    """Configuration for mock data generation"""
    seed: Optional[int] = None
    locale: str = "en_IN"


class MockDataGenerator:
    """
    Generate realistic mock data for testing
    """
    
    # Conductor materials
    MATERIALS = ["copper", "aluminium", "tinned_copper"]
    
    # Standard conductor sizes (sq mm)
    CONDUCTOR_SIZES = [
        0.5, 0.75, 1.0, 1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0,
        35.0, 50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0, 300.0, 400.0
    ]
    
    # Insulation types
    INSULATION_TYPES = ["PVC", "XLPE", "Rubber", "EPR", "Silicon"]
    
    # Voltage grades
    VOLTAGE_GRADES = [250, 450, 650, 1100, 3300, 6600, 11000, 22000, 33000]
    
    # Core counts
    CORE_COUNTS = [1, 2, 3, 3.5, 4, 5, 6, 7, 8, 10, 12, 16, 19, 24, 27, 30, 37]
    
    # Standards
    STANDARDS = [
        "IS 7098", "IS 1554", "IS 694", "IS 14255",
        "IEC 60502", "IEC 60227", "BS 5467", "BS 6346"
    ]
    
    # Company name components
    COMPANY_PREFIXES = ["ABC", "National", "United", "Premier", "Excel", "Metro", "Star", "Global"]
    COMPANY_SUFFIXES = ["Cables", "Wires", "Conductors", "Electricals", "Industries"]
    COMPANY_TYPES = ["Pvt Ltd", "Ltd", "LLP", "Industries"]
    
    # Indian cities
    CITIES = ["Mumbai", "Delhi", "Chennai", "Kolkata", "Bangalore", "Hyderabad", "Pune", "Ahmedabad"]
    
    # State codes for GSTIN
    STATE_CODES = ["27", "07", "33", "19", "29", "36", "21", "24"]
    
    def __init__(self, config: Optional[MockDataConfig] = None):
        """Initialize with optional configuration"""
        self.config = config or MockDataConfig()
        if self.config.seed:
            random.seed(self.config.seed)
    
    def generate_sku(self) -> str:
        """Generate a realistic SKU"""
        material = random.choice(["CU", "AL", "TC"])
        insulation = random.choice(["PVC", "XLPE", "RUB"])
        cores = random.choice([1, 2, 3, 4])
        size = random.choice([1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95])
        
        return f"{material}-{insulation}-{cores}C-{int(size)}"
    
    def generate_product(self) -> Dict[str, Any]:
        """Generate a realistic product"""
        material = random.choice(self.MATERIALS)
        size = random.choice(self.CONDUCTOR_SIZES)
        cores = random.choice(self.CORE_COUNTS[:10])
        insulation = random.choice(self.INSULATION_TYPES[:3])
        voltage = random.choice(self.VOLTAGE_GRADES[:4])
        standard = random.choice(self.STANDARDS[:4])
        
        sku = self.generate_sku()
        
        # Calculate realistic price based on material and size
        base_price = 10 if material == "aluminium" else 25
        price = base_price * size * (cores if cores < 5 else cores * 0.9)
        
        return {
            "sku": sku,
            "name": f"{int(cores)}C x {size} sqmm {material.title()} {insulation} Cable",
            "description": f"{insulation} Insulated Cable as per {standard}",
            "category": "Power Cables" if voltage >= 1100 else "Control Cables",
            "specifications": {
                "conductor_material": material,
                "conductor_size_sqmm": size,
                "number_of_cores": cores,
                "insulation": insulation,
                "voltage_grade": f"{voltage}V",
                "standard": standard
            },
            "unit_price": round(price, 2),
            "currency": "INR",
            "unit_of_measure": "meter",
            "min_order_quantity": random.choice([100, 250, 500, 1000]),
            "lead_time_days": random.randint(3, 21),
            "is_active": True
        }
    
    def generate_vendor(self) -> Dict[str, Any]:
        """Generate a realistic vendor"""
        prefix = random.choice(self.COMPANY_PREFIXES)
        suffix = random.choice(self.COMPANY_SUFFIXES)
        company_type = random.choice(self.COMPANY_TYPES)
        city = random.choice(self.CITIES)
        state_code = random.choice(self.STATE_CODES)
        
        name = f"{prefix} {suffix} {company_type}"
        
        # Generate GSTIN
        pan_chars = ''.join(random.choices(string.ascii_uppercase, k=5))
        pan_nums = ''.join(random.choices(string.digits, k=4))
        pan_last = random.choice(string.ascii_uppercase)
        gstin = f"{state_code}{pan_chars}{pan_nums}{pan_last}1Z{random.choice(string.ascii_uppercase + string.digits)}"
        
        # Generate phone
        phone = f"+91{random.randint(6, 9)}{random.randint(100000000, 999999999)}"
        
        return {
            "vendor_id": f"VND{random.randint(100, 999)}",
            "name": name,
            "email": f"sales@{prefix.lower()}{suffix.lower()}.com",
            "phone": phone,
            "gstin": gstin,
            "address": f"{random.randint(1, 500)} Industrial Area, {city}",
            "city": city,
            "is_oem": random.choice([True, False]),
            "categories": random.sample(["Power Cables", "Control Cables", "Instrumentation", "Flexible Cables"], k=random.randint(1, 3)),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "is_active": True
        }
    
    def generate_rfp(self, num_items: int = 3) -> Dict[str, Any]:
        """Generate a realistic RFP"""
        orgs = [
            "State Electricity Board",
            "Municipal Corporation",
            "Power Grid Corporation",
            "Railway Electrification",
            "Industrial Development Corporation"
        ]
        
        rfp_id = f"RFP-{datetime.now().year}-{random.randint(100, 999)}"
        
        line_items = []
        for i in range(num_items):
            product = self.generate_product()
            line_items.append({
                "item_no": i + 1,
                "description": product["name"],
                "quantity": random.choice([1000, 2000, 3000, 5000, 10000]),
                "unit": "meters",
                "specifications": product["specifications"],
                "estimated_price": product["unit_price"]
            })
        
        return {
            "rfp_id": rfp_id,
            "title": f"Supply of {random.choice(['LT', 'HT'])} Power Cables",
            "organization": random.choice(orgs),
            "submission_deadline": datetime.now() + timedelta(days=random.randint(7, 30)),
            "line_items": line_items,
            "terms": {
                "payment_terms": random.choice(["30 days", "45 days", "60 days"]),
                "delivery_location": f"{random.choice(self.CITIES)} Warehouse",
                "warranty": random.choice(["12 months", "18 months", "24 months"]),
                "delivery_period": f"{random.randint(30, 90)} days"
            },
            "contact_email": f"procurement@{random.choice(['utility', 'power', 'corp'])}.gov.in",
            "contact_phone": f"+91{random.randint(6, 9)}{random.randint(100000000, 999999999)}"
        }
    
    def generate_rfp_text(self) -> str:
        """Generate realistic RFP text for extraction testing"""
        rfp = self.generate_rfp(num_items=random.randint(2, 5))
        
        items_text = ""
        for item in rfp["line_items"]:
            specs = item["specifications"]
            items_text += f"""
    Item {item['item_no']}: {item['description']}
            Quantity: {item['quantity']:,} {item['unit']}
            Conductor: {specs['conductor_material'].title()}
            Size: {specs['conductor_size_sqmm']} sq.mm
            Cores: {specs['number_of_cores']}
            Insulation: {specs['insulation']}
            Voltage: {specs['voltage_grade']}
            Standard: {specs['standard']}
"""
        
        return f"""
    TENDER NOTICE
    Reference: {rfp['rfp_id']}
    
    {rfp['title']}
    
    Organization: {rfp['organization']}
    
    SCHEDULE OF ITEMS:
    {items_text}
    
    TERMS AND CONDITIONS:
    - Payment Terms: {rfp['terms']['payment_terms']}
    - Delivery Location: {rfp['terms']['delivery_location']}
    - Warranty Period: {rfp['terms']['warranty']}
    - Delivery Period: {rfp['terms']['delivery_period']}
    
    Submission Deadline: {rfp['submission_deadline'].strftime('%d %B %Y')}
    
    Contact:
    Email: {rfp['contact_email']}
    Phone: {rfp['contact_phone']}
    """
    
    def generate_products_batch(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate multiple products"""
        return [self.generate_product() for _ in range(count)]
    
    def generate_vendors_batch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Generate multiple vendors"""
        return [self.generate_vendor() for _ in range(count)]
    
    def generate_test_emails(self, count: int = 10) -> List[str]:
        """Generate test email addresses"""
        domains = ["gmail.com", "yahoo.com", "outlook.com", "company.com"]
        emails = []
        for _ in range(count):
            name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
            domain = random.choice(domains)
            emails.append(f"{name}@{domain}")
        return emails
    
    def generate_test_phones(self, count: int = 10) -> List[str]:
        """Generate test phone numbers"""
        phones = []
        for _ in range(count):
            prefix = random.choice(["+91", "91", "0", ""])
            number = f"{random.randint(6, 9)}{random.randint(100000000, 999999999)}"
            phones.append(f"{prefix}{number}")
        return phones
    
    def generate_conductor_text_samples(self) -> List[str]:
        """Generate text samples for conductor extraction testing"""
        return [
            "4 Core x 25 sq.mm Copper XLPE Cable",
            "4C x 25 sqmm Cu XLPE",
            "4 core 25mm² copper",
            "25 sq mm 4 core copper conductor",
            "3.5C x 95 sqmm Al XLPE Cable",
            "Single core 400 sqmm Aluminium",
            "2 Core 2.5 sq.mm tinned copper",
            "16 AWG copper wire",
            "7/0.67 stranding Class 2",
        ]
    
    def generate_voltage_text_samples(self) -> List[str]:
        """Generate text samples for voltage extraction testing"""
        return [
            "Voltage: 1100V",
            "600/1100V grade",
            "11kV rated",
            "voltage rating 650V",
            "system voltage 33kV",
            "1.1 kV",
            "0.6/1kV",
            "rated for 415V",
        ]


# Pytest fixture function
def get_mock_generator(seed: Optional[int] = None) -> MockDataGenerator:
    """Get a mock data generator instance"""
    return MockDataGenerator(MockDataConfig(seed=seed))


# Pre-generated test data for deterministic tests
DETERMINISTIC_PRODUCTS = [
    {
        "sku": "TEST-CU-4C-25",
        "name": "4C x 25 sqmm Copper XLPE Cable",
        "conductor_material": "copper",
        "conductor_size_sqmm": 25.0,
        "number_of_cores": 4,
        "insulation": "XLPE",
        "voltage_grade": 1100,
        "price": 450.00
    },
    {
        "sku": "TEST-AL-3.5C-95",
        "name": "3.5C x 95 sqmm Aluminium XLPE Cable",
        "conductor_material": "aluminium",
        "conductor_size_sqmm": 95.0,
        "number_of_cores": 3.5,
        "insulation": "XLPE",
        "voltage_grade": 1100,
        "price": 320.00
    },
    {
        "sku": "TEST-CU-2C-2.5",
        "name": "2C x 2.5 sqmm Copper PVC Cable",
        "conductor_material": "copper",
        "conductor_size_sqmm": 2.5,
        "number_of_cores": 2,
        "insulation": "PVC",
        "voltage_grade": 650,
        "price": 45.00
    }
]

DETERMINISTIC_VENDORS = [
    {
        "vendor_id": "VND001",
        "name": "Test Cables Pvt Ltd",
        "email": "sales@testcables.com",
        "phone": "+919876543210",
        "gstin": "27AABCU9603R1ZM",
        "city": "Mumbai"
    },
    {
        "vendor_id": "VND002",
        "name": "Sample Wires Ltd",
        "email": "info@samplewires.com",
        "phone": "+919123456789",
        "gstin": "07AAACP1234F1ZK",
        "city": "Delhi"
    }
]
