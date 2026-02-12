"""
Data Loader Classes for Synthetic Data Files
Supports CSV and JSON formats for:
- Products (OEM product catalog)
- Pricing (product prices and service prices)
- Tests (testing services)
- Historical RFPs

Includes comprehensive validation for missing fields
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"      # Critical - data cannot be used
    WARNING = "warning"  # Important - data may have issues
    INFO = "info"        # Minor - data usable but not optimal


@dataclass
class ValidationIssue:
    """Represents a validation issue found in data"""
    field: str
    message: str
    severity: ValidationSeverity
    row_index: Optional[int] = None
    record_id: Optional[str] = None
    value: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
    
    def summary(self) -> str:
        return (f"Validation: {'PASSED' if self.is_valid else 'FAILED'} | "
                f"Records: {self.valid_records}/{self.total_records} valid | "
                f"Errors: {self.error_count} | Warnings: {self.warning_count}")


class BaseDataLoader:
    """Base class for all data loaders"""
    
    def __init__(self, base_path: str = None):
        """
        Initialize the data loader
        
        Args:
            base_path: Base path for data files. Defaults to database folder.
        """
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = Path(base_path)
        self.data: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.validation_result: Optional[ValidationResult] = None
        
    def load_json(self, file_path: str) -> Tuple[List[Dict], Dict]:
        """
        Load data from JSON file
        
        Args:
            file_path: Path to JSON file (relative or absolute)
            
        Returns:
            Tuple of (data list, metadata dict)
        """
        full_path = self._resolve_path(file_path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"JSON file not found: {full_path}")
        
        logger.info(f"Loading JSON from: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Handle different JSON structures
        if isinstance(content, dict):
            metadata = content.get('metadata', {})
            # Try common data keys
            for key in ['products', 'services', 'prices', 'rfps', 'data', 'items', 'records']:
                if key in content:
                    return content[key], metadata
            # If no known key, return all non-metadata as data
            data = {k: v for k, v in content.items() if k != 'metadata'}
            return [data] if data else [], metadata
        elif isinstance(content, list):
            return content, {}
        else:
            return [], {}
    
    def load_csv(self, file_path: str, encoding: str = 'utf-8') -> List[Dict]:
        """
        Load data from CSV file
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding (default: utf-8)
            
        Returns:
            List of dictionaries representing rows
        """
        full_path = self._resolve_path(file_path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"CSV file not found: {full_path}")
        
        logger.info(f"Loading CSV from: {full_path}")
        
        data = []
        try:
            with open(full_path, 'r', encoding=encoding, errors='replace') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean up row - remove empty string keys and strip values
                    cleaned_row = {
                        k.strip(): v.strip() if isinstance(v, str) else v 
                        for k, v in row.items() 
                        if k and k.strip()
                    }
                    data.append(cleaned_row)
        except UnicodeDecodeError:
            # Try with latin-1 encoding
            with open(full_path, 'r', encoding='latin-1') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cleaned_row = {
                        k.strip(): v.strip() if isinstance(v, str) else v 
                        for k, v in row.items() 
                        if k and k.strip()
                    }
                    data.append(cleaned_row)
        
        logger.info(f"Loaded {len(data)} records from CSV")
        return data
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path (relative or absolute)"""
        path = Path(file_path)
        if path.is_absolute():
            return path
        return self.base_path / path
    
    def _convert_type(self, value: Any, target_type: type) -> Any:
        """Convert value to target type with error handling"""
        if value is None or value == '':
            return None
        
        try:
            if target_type == float:
                # Handle currency symbols and commas
                if isinstance(value, str):
                    value = re.sub(r'[₹$€,]', '', value)
                return float(value)
            elif target_type == int:
                if isinstance(value, str):
                    value = re.sub(r'[₹$€,]', '', value)
                return int(float(value))
            elif target_type == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'y', 'active')
                return bool(value)
            elif target_type == list:
                if isinstance(value, str):
                    return [v.strip() for v in value.split(',') if v.strip()]
                return list(value) if value else []
            else:
                return target_type(value)
        except (ValueError, TypeError):
            return None
    
    def validate(self) -> ValidationResult:
        """Validate loaded data - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement validate()")
    
    def get_valid_records(self) -> List[Dict]:
        """Get only records that passed validation"""
        if not self.validation_result:
            self.validate()
        
        invalid_indices = {
            i.row_index for i in self.validation_result.issues 
            if i.severity == ValidationSeverity.ERROR and i.row_index is not None
        }
        
        return [
            record for i, record in enumerate(self.data) 
            if i not in invalid_indices
        ]


class ProductDataLoader(BaseDataLoader):
    """
    Loader for OEM product data
    Supports both JSON (oem_products.json) and CSV (polycab_*.csv etc.)
    """
    
    # Required fields for product data
    REQUIRED_FIELDS = {
        'sku': str,           # Product SKU/code
        'name': str,          # Product name
        'manufacturer': str,  # OEM/Manufacturer name
    }
    
    # Optional but important fields
    IMPORTANT_FIELDS = {
        'category': str,
        'specifications': dict,
        'certifications': list,
        'standards_compliance': list,
    }
    
    # Field mappings for CSV files (different naming conventions)
    FIELD_MAPPINGS = {
        'Product_Code': 'sku',
        'Product_Name': 'name',
        'Company': 'manufacturer',
        'Category': 'category',
        'Type': 'product_type',
        'Voltage_Rating': 'voltage_rating',
        'Conductor_Material': 'conductor_material',
        'Conductor_Size_sqmm': 'conductor_size_sqmm',
        'No_of_Cores': 'no_of_cores',
        'Insulation_Type': 'insulation_type',
        'Standard': 'standard',
        'Price_Per_Meter_INR': 'price_per_meter',
        'Current_Rating_Amps': 'current_rating_amps',
    }
    
    def __init__(self, base_path: str = None):
        super().__init__(base_path)
        self.products_by_sku: Dict[str, Dict] = {}
        self.products_by_oem: Dict[str, List[Dict]] = {}
    
    def load(self, file_path: str) -> 'ProductDataLoader':
        """
        Load product data from JSON or CSV file
        
        Args:
            file_path: Path to data file
            
        Returns:
            Self for method chaining
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.json':
            self.data, self.metadata = self.load_json(file_path)
        elif file_ext == '.csv':
            self.data = self.load_csv(file_path)
            self._normalize_csv_fields()
            self.metadata = {'source': 'csv', 'file': file_path}
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Build lookup indexes
        self._build_indexes()
        
        logger.info(f"Loaded {len(self.data)} products")
        return self
    
    def load_multiple(self, file_paths: List[str]) -> 'ProductDataLoader':
        """
        Load and merge products from multiple files
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Self for method chaining
        """
        all_products = []
        
        for file_path in file_paths:
            try:
                file_ext = Path(file_path).suffix.lower()
                if file_ext == '.json':
                    products, _ = self.load_json(file_path)
                elif file_ext == '.csv':
                    products = self.load_csv(file_path)
                    products = self._normalize_csv_data(products)
                else:
                    continue
                all_products.extend(products)
                logger.info(f"Added {len(products)} products from {file_path}")
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
        
        self.data = all_products
        self._build_indexes()
        
        logger.info(f"Total products loaded: {len(self.data)}")
        return self
    
    def _normalize_csv_fields(self):
        """Normalize CSV field names to standard format"""
        self.data = self._normalize_csv_data(self.data)
    
    def _normalize_csv_data(self, data: List[Dict]) -> List[Dict]:
        """Normalize CSV data with field mappings"""
        normalized = []
        for row in data:
            normalized_row = {}
            for csv_field, standard_field in self.FIELD_MAPPINGS.items():
                if csv_field in row:
                    normalized_row[standard_field] = row[csv_field]
            # Keep original fields too
            for key, value in row.items():
                if key not in self.FIELD_MAPPINGS:
                    normalized_row[key.lower().replace(' ', '_')] = value
            normalized.append(normalized_row)
        return normalized
    
    def _build_indexes(self):
        """Build lookup indexes for fast access"""
        self.products_by_sku = {}
        self.products_by_oem = {}
        
        for product in self.data:
            sku = product.get('sku') or product.get('Product_Code')
            if sku:
                self.products_by_sku[sku] = product
            
            oem = product.get('manufacturer') or product.get('Company')
            if oem:
                if oem not in self.products_by_oem:
                    self.products_by_oem[oem] = []
                self.products_by_oem[oem].append(product)
    
    def validate(self) -> ValidationResult:
        """Validate product data for required and important fields"""
        issues = []
        valid_count = 0
        
        for i, product in enumerate(self.data):
            record_valid = True
            sku = product.get('sku') or product.get('Product_Code', f'ROW_{i}')
            
            # Check required fields
            for field_name, field_type in self.REQUIRED_FIELDS.items():
                value = product.get(field_name)
                # Try alternate field names
                if value is None:
                    for alt_name in [field_name.upper(), field_name.title(), 
                                    field_name.replace('_', ' ').title()]:
                        if alt_name in product:
                            value = product[alt_name]
                            break
                
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing required field '{field_name}'",
                        severity=ValidationSeverity.ERROR,
                        row_index=i,
                        record_id=sku
                    ))
                    record_valid = False
            
            # Check important fields (warnings only)
            for field_name, field_type in self.IMPORTANT_FIELDS.items():
                value = product.get(field_name)
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing important field '{field_name}'",
                        severity=ValidationSeverity.WARNING,
                        row_index=i,
                        record_id=sku
                    ))
            
            # Validate specifications if present
            specs = product.get('specifications', {})
            if isinstance(specs, dict) and not specs:
                issues.append(ValidationIssue(
                    field='specifications',
                    message="Empty specifications object",
                    severity=ValidationSeverity.WARNING,
                    row_index=i,
                    record_id=sku
                ))
            
            if record_valid:
                valid_count += 1
        
        self.validation_result = ValidationResult(
            is_valid=valid_count == len(self.data),
            total_records=len(self.data),
            valid_records=valid_count,
            invalid_records=len(self.data) - valid_count,
            issues=issues
        )
        
        logger.info(self.validation_result.summary())
        return self.validation_result
    
    def get_by_sku(self, sku: str) -> Optional[Dict]:
        """Get product by SKU"""
        return self.products_by_sku.get(sku)
    
    def get_by_oem(self, oem: str) -> List[Dict]:
        """Get all products for an OEM"""
        return self.products_by_oem.get(oem, [])
    
    def get_oem_list(self) -> List[str]:
        """Get list of all OEMs"""
        return list(self.products_by_oem.keys())
    
    def search(self, **criteria) -> List[Dict]:
        """
        Search products by criteria
        
        Args:
            **criteria: Field-value pairs to match
            
        Returns:
            List of matching products
        """
        results = []
        for product in self.data:
            match = True
            for field, value in criteria.items():
                product_value = product.get(field)
                if product_value is None:
                    match = False
                    break
                if isinstance(value, str) and isinstance(product_value, str):
                    if value.lower() not in product_value.lower():
                        match = False
                        break
                elif product_value != value:
                    match = False
                    break
            if match:
                results.append(product)
        return results


class PricingDataLoader(BaseDataLoader):
    """
    Loader for pricing data
    Supports product prices and service/test prices
    """
    
    REQUIRED_PRODUCT_PRICE_FIELDS = {
        'sku': str,
        'product_name': str,
        'unit_price': float,
    }
    
    REQUIRED_SERVICE_PRICE_FIELDS = {
        'service_id': str,
        'service_name': str,
        'price': float,
    }
    
    IMPORTANT_PRICE_FIELDS = {
        'manufacturer': str,
        'unit': str,
        'moq': int,
        'bulk_discount_percent': float,
        'category': str,
    }
    
    def __init__(self, base_path: str = None):
        super().__init__(base_path)
        self.product_prices: Dict[str, Dict] = {}
        self.service_prices: Dict[str, Dict] = {}
        self.price_type: str = 'unknown'  # 'product' or 'service'
    
    def load_product_prices(self, file_path: str) -> 'PricingDataLoader':
        """Load product pricing data"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.json':
            self.data, self.metadata = self.load_json(file_path)
        elif file_ext == '.csv':
            self.data = self.load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        self.price_type = 'product'
        self._build_product_price_index()
        
        logger.info(f"Loaded {len(self.product_prices)} product prices")
        return self
    
    def load_service_prices(self, file_path: str) -> 'PricingDataLoader':
        """Load service/test pricing data"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.json':
            self.data, self.metadata = self.load_json(file_path)
        elif file_ext == '.csv':
            self.data = self.load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        self.price_type = 'service'
        self._build_service_price_index()
        
        logger.info(f"Loaded {len(self.service_prices)} service prices")
        return self
    
    def _build_product_price_index(self):
        """Build product price lookup index"""
        self.product_prices = {}
        for item in self.data:
            sku = item.get('sku')
            if sku:
                # Convert price to float
                unit_price = self._convert_type(item.get('unit_price'), float)
                item['unit_price'] = unit_price
                self.product_prices[sku] = item
    
    def _build_service_price_index(self):
        """Build service price lookup index"""
        self.service_prices = {}
        for item in self.data:
            service_id = item.get('service_id')
            if service_id:
                # Convert price to float
                price = self._convert_type(item.get('price'), float)
                item['price'] = price
                self.service_prices[service_id] = item
    
    def validate(self) -> ValidationResult:
        """Validate pricing data"""
        issues = []
        valid_count = 0
        
        required_fields = (self.REQUIRED_PRODUCT_PRICE_FIELDS 
                          if self.price_type == 'product' 
                          else self.REQUIRED_SERVICE_PRICE_FIELDS)
        
        id_field = 'sku' if self.price_type == 'product' else 'service_id'
        
        for i, item in enumerate(self.data):
            record_valid = True
            record_id = item.get(id_field, f'ROW_{i}')
            
            # Check required fields
            for field_name, field_type in required_fields.items():
                value = item.get(field_name)
                
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing required field '{field_name}'",
                        severity=ValidationSeverity.ERROR,
                        row_index=i,
                        record_id=record_id
                    ))
                    record_valid = False
                elif field_type == float:
                    converted = self._convert_type(value, float)
                    if converted is None:
                        issues.append(ValidationIssue(
                            field=field_name,
                            message=f"Invalid numeric value for '{field_name}': {value}",
                            severity=ValidationSeverity.ERROR,
                            row_index=i,
                            record_id=record_id,
                            value=value
                        ))
                        record_valid = False
                    elif converted <= 0:
                        issues.append(ValidationIssue(
                            field=field_name,
                            message=f"Price must be positive for '{field_name}': {converted}",
                            severity=ValidationSeverity.WARNING,
                            row_index=i,
                            record_id=record_id,
                            value=converted
                        ))
            
            # Check important fields
            for field_name, field_type in self.IMPORTANT_PRICE_FIELDS.items():
                value = item.get(field_name)
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing important field '{field_name}'",
                        severity=ValidationSeverity.INFO,
                        row_index=i,
                        record_id=record_id
                    ))
            
            if record_valid:
                valid_count += 1
        
        self.validation_result = ValidationResult(
            is_valid=valid_count == len(self.data),
            total_records=len(self.data),
            valid_records=valid_count,
            invalid_records=len(self.data) - valid_count,
            issues=issues
        )
        
        logger.info(self.validation_result.summary())
        return self.validation_result
    
    def get_product_price(self, sku: str) -> Optional[float]:
        """Get price for a product SKU"""
        item = self.product_prices.get(sku)
        return item.get('unit_price') if item else None
    
    def get_service_price(self, service_id: str) -> Optional[float]:
        """Get price for a service"""
        item = self.service_prices.get(service_id)
        return item.get('price') if item else None
    
    def calculate_bulk_price(self, sku: str, quantity: int) -> Optional[Dict]:
        """Calculate price with bulk discount"""
        item = self.product_prices.get(sku)
        if not item:
            return None
        
        unit_price = item.get('unit_price', 0)
        bulk_discount = item.get('bulk_discount_percent', 0)
        bulk_threshold = item.get('bulk_threshold', 0)
        
        if quantity >= bulk_threshold and bulk_discount > 0:
            discounted_price = unit_price * (1 - bulk_discount / 100)
            total = discounted_price * quantity
            return {
                'sku': sku,
                'quantity': quantity,
                'unit_price': unit_price,
                'discount_percent': bulk_discount,
                'discounted_unit_price': discounted_price,
                'total_price': total
            }
        else:
            return {
                'sku': sku,
                'quantity': quantity,
                'unit_price': unit_price,
                'discount_percent': 0,
                'discounted_unit_price': unit_price,
                'total_price': unit_price * quantity
            }


class TestDataLoader(BaseDataLoader):
    """
    Loader for test/service data
    Loads testing requirements and costs
    """
    
    REQUIRED_FIELDS = {
        'service_id': str,
        'service_name': str,
        'price': float,
    }
    
    IMPORTANT_FIELDS = {
        'description': str,
        'unit': str,
        'turnaround_days': int,
        'category': str,
        'standard': str,
    }
    
    def __init__(self, base_path: str = None):
        super().__init__(base_path)
        self.tests_by_id: Dict[str, Dict] = {}
        self.tests_by_category: Dict[str, List[Dict]] = {}
        self.tests_by_standard: Dict[str, List[Dict]] = {}
    
    def load(self, file_path: str) -> 'TestDataLoader':
        """Load test/service data"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.json':
            self.data, self.metadata = self.load_json(file_path)
        elif file_ext == '.csv':
            self.data = self.load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        self._build_indexes()
        
        logger.info(f"Loaded {len(self.data)} tests/services")
        return self
    
    def _build_indexes(self):
        """Build lookup indexes"""
        self.tests_by_id = {}
        self.tests_by_category = {}
        self.tests_by_standard = {}
        
        for test in self.data:
            # By ID
            test_id = test.get('service_id')
            if test_id:
                self.tests_by_id[test_id] = test
            
            # By category
            category = test.get('category')
            if category:
                if category not in self.tests_by_category:
                    self.tests_by_category[category] = []
                self.tests_by_category[category].append(test)
            
            # By standard
            standard = test.get('standard')
            if standard:
                if standard not in self.tests_by_standard:
                    self.tests_by_standard[standard] = []
                self.tests_by_standard[standard].append(test)
    
    def validate(self) -> ValidationResult:
        """Validate test data"""
        issues = []
        valid_count = 0
        
        for i, test in enumerate(self.data):
            record_valid = True
            test_id = test.get('service_id', f'ROW_{i}')
            
            # Check required fields
            for field_name, field_type in self.REQUIRED_FIELDS.items():
                value = test.get(field_name)
                
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing required field '{field_name}'",
                        severity=ValidationSeverity.ERROR,
                        row_index=i,
                        record_id=test_id
                    ))
                    record_valid = False
                elif field_type == float:
                    converted = self._convert_type(value, float)
                    if converted is None:
                        issues.append(ValidationIssue(
                            field=field_name,
                            message=f"Invalid numeric value for '{field_name}'",
                            severity=ValidationSeverity.ERROR,
                            row_index=i,
                            record_id=test_id,
                            value=value
                        ))
                        record_valid = False
            
            # Check important fields
            for field_name, field_type in self.IMPORTANT_FIELDS.items():
                value = test.get(field_name)
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing important field '{field_name}'",
                        severity=ValidationSeverity.WARNING,
                        row_index=i,
                        record_id=test_id
                    ))
            
            if record_valid:
                valid_count += 1
        
        self.validation_result = ValidationResult(
            is_valid=valid_count == len(self.data),
            total_records=len(self.data),
            valid_records=valid_count,
            invalid_records=len(self.data) - valid_count,
            issues=issues
        )
        
        logger.info(self.validation_result.summary())
        return self.validation_result
    
    def get_test(self, test_id: str) -> Optional[Dict]:
        """Get test by ID"""
        return self.tests_by_id.get(test_id)
    
    def get_tests_by_category(self, category: str) -> List[Dict]:
        """Get all tests in a category"""
        return self.tests_by_category.get(category, [])
    
    def get_tests_by_standard(self, standard: str) -> List[Dict]:
        """Get all tests for a standard"""
        return self.tests_by_standard.get(standard, [])
    
    def get_categories(self) -> List[str]:
        """Get all test categories"""
        return list(self.tests_by_category.keys())
    
    def calculate_total_test_cost(self, test_ids: List[str]) -> Dict:
        """Calculate total cost for multiple tests"""
        total = 0
        tests_included = []
        tests_not_found = []
        
        for test_id in test_ids:
            test = self.tests_by_id.get(test_id)
            if test:
                price = self._convert_type(test.get('price'), float) or 0
                total += price
                tests_included.append({
                    'test_id': test_id,
                    'name': test.get('service_name'),
                    'price': price
                })
            else:
                tests_not_found.append(test_id)
        
        return {
            'total_cost': total,
            'tests_included': tests_included,
            'tests_not_found': tests_not_found,
            'count': len(tests_included)
        }


class RFPDataLoader(BaseDataLoader):
    """
    Loader for historical RFP data
    Supports RFP documents, bid history, and approval records
    """
    
    REQUIRED_FIELDS = {
        'rfp_id': str,
        'title': str,
    }
    
    IMPORTANT_FIELDS = {
        'issuing_authority': str,
        'due_date': str,
        'estimated_value': float,
        'status': str,
        'requirements': list,
        'products': list,
    }
    
    def __init__(self, base_path: str = None):
        super().__init__(base_path)
        self.rfps_by_id: Dict[str, Dict] = {}
        self.rfps_by_status: Dict[str, List[Dict]] = {}
    
    def load(self, file_path: str) -> 'RFPDataLoader':
        """Load RFP data"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.json':
            self.data, self.metadata = self.load_json(file_path)
        elif file_ext == '.csv':
            self.data = self.load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        self._build_indexes()
        
        logger.info(f"Loaded {len(self.data)} RFPs")
        return self
    
    def _build_indexes(self):
        """Build lookup indexes"""
        self.rfps_by_id = {}
        self.rfps_by_status = {}
        
        for rfp in self.data:
            rfp_id = rfp.get('rfp_id')
            if rfp_id:
                self.rfps_by_id[rfp_id] = rfp
            
            status = rfp.get('status', 'unknown')
            if status not in self.rfps_by_status:
                self.rfps_by_status[status] = []
            self.rfps_by_status[status].append(rfp)
    
    def validate(self) -> ValidationResult:
        """Validate RFP data"""
        issues = []
        valid_count = 0
        
        for i, rfp in enumerate(self.data):
            record_valid = True
            rfp_id = rfp.get('rfp_id', f'ROW_{i}')
            
            # Check required fields
            for field_name, field_type in self.REQUIRED_FIELDS.items():
                value = rfp.get(field_name)
                
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing required field '{field_name}'",
                        severity=ValidationSeverity.ERROR,
                        row_index=i,
                        record_id=rfp_id
                    ))
                    record_valid = False
            
            # Check important fields
            for field_name, field_type in self.IMPORTANT_FIELDS.items():
                value = rfp.get(field_name)
                if value is None or value == '':
                    issues.append(ValidationIssue(
                        field=field_name,
                        message=f"Missing important field '{field_name}'",
                        severity=ValidationSeverity.WARNING,
                        row_index=i,
                        record_id=rfp_id
                    ))
            
            # Validate date format if present
            due_date = rfp.get('due_date')
            if due_date:
                try:
                    if isinstance(due_date, str):
                        datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    issues.append(ValidationIssue(
                        field='due_date',
                        message=f"Invalid date format: {due_date}",
                        severity=ValidationSeverity.WARNING,
                        row_index=i,
                        record_id=rfp_id,
                        value=due_date
                    ))
            
            # Validate products/requirements are lists
            for list_field in ['products', 'requirements']:
                value = rfp.get(list_field)
                if value is not None and not isinstance(value, list):
                    issues.append(ValidationIssue(
                        field=list_field,
                        message=f"Field '{list_field}' should be a list",
                        severity=ValidationSeverity.WARNING,
                        row_index=i,
                        record_id=rfp_id
                    ))
            
            if record_valid:
                valid_count += 1
        
        self.validation_result = ValidationResult(
            is_valid=valid_count == len(self.data),
            total_records=len(self.data),
            valid_records=valid_count,
            invalid_records=len(self.data) - valid_count,
            issues=issues
        )
        
        logger.info(self.validation_result.summary())
        return self.validation_result
    
    def get_rfp(self, rfp_id: str) -> Optional[Dict]:
        """Get RFP by ID"""
        return self.rfps_by_id.get(rfp_id)
    
    def get_rfps_by_status(self, status: str) -> List[Dict]:
        """Get all RFPs with a specific status"""
        return self.rfps_by_status.get(status, [])
    
    def get_active_rfps(self) -> List[Dict]:
        """Get all active/open RFPs"""
        active_statuses = ['open', 'active', 'pending', 'in_progress']
        results = []
        for status in active_statuses:
            results.extend(self.rfps_by_status.get(status, []))
        return results
    
    def get_rfps_due_within(self, days: int) -> List[Dict]:
        """Get RFPs due within specified days"""
        cutoff = datetime.now() + timedelta(days=days)
        results = []
        
        for rfp in self.data:
            due_date_str = rfp.get('due_date')
            if due_date_str:
                try:
                    if isinstance(due_date_str, str):
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                        if due_date.replace(tzinfo=None) <= cutoff:
                            results.append(rfp)
                except ValueError:
                    pass
        
        return results


class DataLoaderManager:
    """
    Manager class to coordinate all data loaders
    Provides a unified interface to load and validate all data
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the data loader manager
        
        Args:
            base_path: Base path for all data files
        """
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = Path(base_path)
        
        self.product_loader = ProductDataLoader(base_path)
        self.pricing_loader = PricingDataLoader(base_path)
        self.test_loader = TestDataLoader(base_path)
        self.rfp_loader = RFPDataLoader(base_path)
        
        self._loaded = {
            'products': False,
            'pricing': False,
            'tests': False,
            'rfps': False
        }
    
    def load_all(self, config: Dict[str, str] = None) -> 'DataLoaderManager':
        """
        Load all data files
        
        Args:
            config: Dictionary mapping data type to file path
                   e.g., {'products': 'db_products/oem_products.json'}
                   
        Returns:
            Self for method chaining
        """
        if config is None:
            config = {
                'products': 'db_products/oem_products.json',
                'product_prices': 'db_pricing/product_prices.json',
                'service_prices': 'db_pricing/service_prices.json',
            }
        
        # Load products
        if 'products' in config:
            try:
                self.product_loader.load(config['products'])
                self._loaded['products'] = True
            except Exception as e:
                logger.error(f"Failed to load products: {e}")
        
        # Load product prices
        if 'product_prices' in config:
            try:
                self.pricing_loader.load_product_prices(config['product_prices'])
                self._loaded['pricing'] = True
            except Exception as e:
                logger.error(f"Failed to load product prices: {e}")
        
        # Load service prices (tests)
        if 'service_prices' in config:
            try:
                self.test_loader.load(config['service_prices'])
                self._loaded['tests'] = True
            except Exception as e:
                logger.error(f"Failed to load service prices: {e}")
        
        # Load RFPs
        if 'rfps' in config:
            try:
                self.rfp_loader.load(config['rfps'])
                self._loaded['rfps'] = True
            except Exception as e:
                logger.error(f"Failed to load RFPs: {e}")
        
        return self
    
    def validate_all(self) -> Dict[str, ValidationResult]:
        """Validate all loaded data"""
        results = {}
        
        if self._loaded['products']:
            results['products'] = self.product_loader.validate()
        
        if self._loaded['pricing']:
            results['pricing'] = self.pricing_loader.validate()
        
        if self._loaded['tests']:
            results['tests'] = self.test_loader.validate()
        
        if self._loaded['rfps']:
            results['rfps'] = self.rfp_loader.validate()
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all loaded data"""
        summary = {
            'loaded': self._loaded,
            'counts': {},
            'validation': {}
        }
        
        if self._loaded['products']:
            summary['counts']['products'] = len(self.product_loader.data)
            summary['counts']['oems'] = len(self.product_loader.get_oem_list())
            if self.product_loader.validation_result:
                summary['validation']['products'] = self.product_loader.validation_result.summary()
        
        if self._loaded['pricing']:
            summary['counts']['product_prices'] = len(self.pricing_loader.product_prices)
            if self.pricing_loader.validation_result:
                summary['validation']['pricing'] = self.pricing_loader.validation_result.summary()
        
        if self._loaded['tests']:
            summary['counts']['tests'] = len(self.test_loader.data)
            summary['counts']['test_categories'] = len(self.test_loader.get_categories())
            if self.test_loader.validation_result:
                summary['validation']['tests'] = self.test_loader.validation_result.summary()
        
        if self._loaded['rfps']:
            summary['counts']['rfps'] = len(self.rfp_loader.data)
            if self.rfp_loader.validation_result:
                summary['validation']['rfps'] = self.rfp_loader.validation_result.summary()
        
        return summary
    
    def print_validation_report(self):
        """Print detailed validation report"""
        print("\n" + "="*80)
        print("DATA VALIDATION REPORT")
        print("="*80)
        
        results = self.validate_all()
        
        for data_type, result in results.items():
            print(f"\n{data_type.upper()}")
            print("-"*40)
            print(result.summary())
            
            if result.error_count > 0:
                print(f"\n  Errors ({result.error_count}):")
                for issue in result.issues[:10]:  # Show first 10
                    if issue.severity == ValidationSeverity.ERROR:
                        print(f"    - [{issue.record_id}] {issue.field}: {issue.message}")
            
            if result.warning_count > 0:
                print(f"\n  Warnings ({result.warning_count}):")
                for issue in result.issues[:5]:  # Show first 5
                    if issue.severity == ValidationSeverity.WARNING:
                        print(f"    - [{issue.record_id}] {issue.field}: {issue.message}")
        
        print("\n" + "="*80)


# Convenience function to get a configured manager
def get_data_loader_manager(base_path: str = None) -> DataLoaderManager:
    """Get a data loader manager with default configuration"""
    if base_path is None:
        base_path = Path(__file__).parent
    return DataLoaderManager(base_path)


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Get base path
    base_path = Path(__file__).parent
    
    print("="*80)
    print("DATA LOADER TEST")
    print("="*80)
    
    # Test Product Loader
    print("\n1. Testing Product Loader...")
    try:
        product_loader = ProductDataLoader(base_path)
        product_loader.load('db_products/oem_products.json')
        validation = product_loader.validate()
        print(f"   Products loaded: {len(product_loader.data)}")
        print(f"   OEMs: {product_loader.get_oem_list()}")
        print(f"   Validation: {validation.summary()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Pricing Loader
    print("\n2. Testing Pricing Loader...")
    try:
        pricing_loader = PricingDataLoader(base_path)
        pricing_loader.load_product_prices('db_pricing/product_prices.json')
        validation = pricing_loader.validate()
        print(f"   Prices loaded: {len(pricing_loader.product_prices)}")
        print(f"   Validation: {validation.summary()}")
        
        # Test bulk pricing
        bulk = pricing_loader.calculate_bulk_price('POL-PVC-2.5-R', 15000)
        if bulk:
            print(f"   Bulk price test: {bulk}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Test/Service Loader
    print("\n3. Testing Test/Service Loader...")
    try:
        test_loader = TestDataLoader(base_path)
        test_loader.load('db_pricing/service_prices.json')
        validation = test_loader.validate()
        print(f"   Tests loaded: {len(test_loader.data)}")
        print(f"   Categories: {test_loader.get_categories()}")
        print(f"   Validation: {validation.summary()}")
        
        # Test total cost calculation
        cost = test_loader.calculate_total_test_cost(['TEST_CONDUCTOR_RES', 'TEST_HV'])
        print(f"   Test cost calculation: {cost}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test Manager
    print("\n4. Testing Data Loader Manager...")
    try:
        manager = get_data_loader_manager(base_path)
        manager.load_all()
        manager.print_validation_report()
        
        summary = manager.get_summary()
        print("\nSummary:")
        print(f"   Loaded: {summary['loaded']}")
        print(f"   Counts: {summary['counts']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
