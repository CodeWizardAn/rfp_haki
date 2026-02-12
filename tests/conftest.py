"""
Pytest Configuration and Fixtures
Central fixture definitions for all tests
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Generator
import tempfile
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_db_path():
    """Provide a temporary database path for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test_agents.db")


@pytest.fixture(scope="function")
def db_manager(test_db_path):
    """Create a test database manager"""
    from database.db_engine import DatabaseManager
    from database.models import Base
    
    # Reset singleton for testing
    DatabaseManager._instance = None
    DatabaseManager._engine = None
    DatabaseManager._session_factory = None
    DatabaseManager._scoped_session = None
    
    manager = DatabaseManager(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(manager.engine)
    yield manager
    
    # Cleanup - use close() not dispose()
    manager.close()
    DatabaseManager._instance = None


@pytest.fixture(scope="function")
def db_session(db_manager):
    """Provide a database session for tests"""
    session = db_manager.get_session()
    yield session
    session.rollback()
    session.close()


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_product_data() -> Dict[str, Any]:
    """Sample product data for testing"""
    return {
        "sku": "WC-CU-4C-25-XLPE-1KV",
        "name": "4 Core 25 sq.mm XLPE Copper Cable",
        "description": "LT Power Cable as per IS 7098",
        "category": "Power Cables",
        "subcategory": "LT XLPE",
        "specifications": {
            "conductor_material": "copper",
            "conductor_size_sqmm": 25.0,
            "number_of_cores": 4,
            "insulation": "XLPE",
            "voltage_grade": "1100V",
            "standard": "IS 7098 Part 1"
        },
        "unit_price": 450.00,
        "currency": "INR",
        "unit_of_measure": "meter",
        "min_order_quantity": 100,
        "lead_time_days": 7,
        "is_active": True
    }


@pytest.fixture
def sample_vendor_data() -> Dict[str, Any]:
    """Sample vendor data for testing"""
    return {
        "vendor_id": "VND001",
        "name": "ABC Cables Pvt Ltd",
        "email": "sales@abccables.com",
        "phone": "+919876543210",
        "gstin": "27AABCU9603R1ZM",
        "address": "123 Industrial Area, Mumbai",
        "is_oem": True,
        "categories": ["Power Cables", "Control Cables"],
        "rating": 4.5,
        "is_active": True
    }


@pytest.fixture
def sample_rfp_data() -> Dict[str, Any]:
    """Sample RFP data for testing"""
    return {
        "rfp_id": "RFP-2026-001",
        "title": "Supply of LT Power Cables",
        "organization": "State Electricity Board",
        "submission_deadline": datetime.now() + timedelta(days=15),
        "line_items": [
            {
                "item_no": 1,
                "description": "4C x 25 sq.mm Copper XLPE Cable",
                "quantity": 5000,
                "unit": "meters",
                "specifications": {
                    "conductor": "copper",
                    "size": "25 sqmm",
                    "cores": 4,
                    "insulation": "XLPE",
                    "voltage": "1.1kV",
                    "standard": "IS 7098"
                }
            },
            {
                "item_no": 2,
                "description": "3.5C x 95 sq.mm Aluminium XLPE Cable",
                "quantity": 3000,
                "unit": "meters",
                "specifications": {
                    "conductor": "aluminium",
                    "size": "95 sqmm",
                    "cores": 3.5,
                    "insulation": "XLPE",
                    "voltage": "1.1kV",
                    "standard": "IS 7098"
                }
            }
        ],
        "terms": {
            "payment_terms": "30 days",
            "delivery_location": "Mumbai Warehouse",
            "warranty": "12 months"
        }
    }


@pytest.fixture
def sample_conductor_specs() -> List[Dict[str, Any]]:
    """Sample conductor specifications for testing"""
    return [
        {"size_sqmm": 1.5, "awg": "16", "stranding": "7/0.52", "class": 2},
        {"size_sqmm": 2.5, "awg": "14", "stranding": "7/0.67", "class": 2},
        {"size_sqmm": 4.0, "awg": "12", "stranding": "7/0.85", "class": 2},
        {"size_sqmm": 6.0, "awg": "10", "stranding": "7/1.04", "class": 2},
        {"size_sqmm": 10.0, "awg": "8", "stranding": "7/1.35", "class": 2},
        {"size_sqmm": 16.0, "awg": "6", "stranding": "7/1.70", "class": 2},
        {"size_sqmm": 25.0, "awg": "4", "stranding": "7/2.14", "class": 2},
        {"size_sqmm": 35.0, "awg": "2", "stranding": "7/2.52", "class": 2},
        {"size_sqmm": 50.0, "awg": "1/0", "stranding": "19/1.78", "class": 2},
        {"size_sqmm": 70.0, "awg": "2/0", "stranding": "19/2.14", "class": 2},
        {"size_sqmm": 95.0, "awg": "3/0", "stranding": "19/2.52", "class": 2},
        {"size_sqmm": 120.0, "awg": "4/0", "stranding": "37/2.03", "class": 2},
    ]


@pytest.fixture
def sample_standards() -> List[Dict[str, str]]:
    """Sample electrical standards for testing"""
    return [
        {"code": "IS 7098", "body": "BIS", "title": "XLPE Insulated PVC Sheathed Cables"},
        {"code": "IS 1554", "body": "BIS", "title": "PVC Insulated Cables"},
        {"code": "IEC 60502", "body": "IEC", "title": "Power Cables"},
        {"code": "BS 5467", "body": "BSI", "title": "XLPE Armoured Cables"},
        {"code": "IS 694", "body": "BIS", "title": "PVC Insulated Cables for Working Voltages up to 1100V"},
    ]


# ============================================================================
# Normalizer Fixtures
# ============================================================================

@pytest.fixture
def spec_normalizer():
    """Provide SpecificationNormalizer instance"""
    from agents.shared.utils.spec_normalizer import SpecificationNormalizer
    return SpecificationNormalizer()


@pytest.fixture
def unit_converter():
    """Provide UnitConverter instance"""
    from agents.shared.utils.unit_converter import UnitConverter
    return UnitConverter()


@pytest.fixture
def standard_mapper():
    """Provide StandardMapper instance"""
    from agents.shared.utils.standard_mapper import StandardMapper
    return StandardMapper()


@pytest.fixture
def text_cleaner():
    """Provide TextCleaner instance"""
    from agents.shared.utils.text_utils import TextCleaner
    return TextCleaner()


@pytest.fixture
def param_extractor():
    """Provide ParameterExtractor instance"""
    from agents.shared.utils.param_extractor import ParameterExtractor
    return ParameterExtractor()


@pytest.fixture
def validator():
    """Provide Validator instance"""
    from agents.shared.utils.validators import Validator
    return Validator()


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def mock_rfp_text() -> str:
    """Sample RFP text for extraction testing"""
    return """
    TENDER NOTICE
    
    Supply of Electrical Cables for Power Distribution Network
    
    Item 1: 4 Core x 25 sq.mm Copper XLPE Insulated PVC Sheathed Armoured Cable
            Quantity: 5,000 meters
            Voltage Grade: 1100V (600/1100V)
            Standard: IS 7098 Part 1
            
    Item 2: 3.5 Core x 95 sq.mm Aluminium XLPE Cable
            Quantity: 3,000 meters  
            Voltage Grade: 1.1kV
            Standard: IS 7098 Part 1
            
    Item 3: 2 Core x 2.5 sq.mm Copper PVC Cable
            Quantity: 10,000 meters
            Voltage Grade: 650V
            Standard: IS 694
    
    Technical Specifications:
    - Conductor: Class 2 stranded as per IS 8130
    - Insulation thickness as per IS 7098
    - Armour: Galvanized Steel Wire/Strip
    - Temperature rating: 90°C
    
    Submission Deadline: 15th February 2026
    Contact: procurement@utility.gov.in
    Phone: +91 22 2345 6789
    """


@pytest.fixture
def mock_product_catalog() -> List[Dict[str, Any]]:
    """Mock product catalog for testing"""
    return [
        {
            "sku": "CU-XLPE-4C-25",
            "name": "4C x 25 sqmm Cu XLPE",
            "conductor": "copper",
            "size_sqmm": 25.0,
            "cores": 4,
            "insulation": "XLPE",
            "voltage": 1100,
            "price": 450.0
        },
        {
            "sku": "AL-XLPE-3.5C-95",
            "name": "3.5C x 95 sqmm Al XLPE",
            "conductor": "aluminium",
            "size_sqmm": 95.0,
            "cores": 3.5,
            "insulation": "XLPE",
            "voltage": 1100,
            "price": 380.0
        },
        {
            "sku": "CU-PVC-2C-2.5",
            "name": "2C x 2.5 sqmm Cu PVC",
            "conductor": "copper",
            "size_sqmm": 2.5,
            "cores": 2,
            "insulation": "PVC",
            "voltage": 650,
            "price": 45.0
        },
    ]


# ============================================================================
# Temporary File Fixtures
# ============================================================================

@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file"""
    def _create_json(data: Dict, filename: str = "test_data.json"):
        filepath = tmp_path / filename
        with open(filepath, 'w') as f:
            json.dump(data, f)
        return filepath
    return _create_json


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file"""
    config = {
        "database": {
            "url": "sqlite:///test.db",
            "echo": False
        },
        "agents": {
            "timeout": 30,
            "max_retries": 3
        }
    }
    filepath = tmp_path / "config.json"
    with open(filepath, 'w') as f:
        json.dump(config, f)
    return filepath


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup code runs after each test
    import gc
    gc.collect()
