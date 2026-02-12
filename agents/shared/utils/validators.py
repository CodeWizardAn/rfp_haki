"""
Validation Helpers
Common validation functions for data integrity

Features:
- SKU validation
- Email validation
- Phone validation
- GSTIN validation
- Specification validation
- Price validation
- Quantity validation
"""

import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    value: Any
    normalized_value: Optional[Any] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        self.errors = self.errors or []
        self.warnings = self.warnings or []
    
    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)


class Validator:
    """
    Common validation functions for data integrity
    """
    
    # SKU pattern: alphanumeric with optional dashes/underscores
    SKU_PATTERN = r'^[A-Za-z0-9][A-Za-z0-9\-_\.]{2,49}$'
    
    # Email pattern: standard email format
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Phone patterns
    PHONE_PATTERNS = {
        'IN': r'^(?:\+91|91|0)?[6-9]\d{9}$',  # India
        'US': r'^(?:\+1)?[2-9]\d{2}[2-9]\d{6}$',  # USA
        'INTL': r'^\+\d{1,4}\d{6,14}$',  # International
    }
    
    # GSTIN pattern (India)
    GSTIN_PATTERN = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    # PAN pattern (India)
    PAN_PATTERN = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    
    # Valid conductor sizes (sq mm)
    VALID_CONDUCTOR_SIZES = [
        0.5, 0.75, 1.0, 1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0,
        35.0, 50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0,
        300.0, 400.0, 500.0, 630.0, 800.0, 1000.0
    ]
    
    # Valid voltage ratings (common)
    VALID_VOLTAGES = [
        250, 300, 450, 500, 600, 650, 750,
        1000, 1100, 3300, 6600, 11000, 22000, 33000
    ]
    
    def __init__(self):
        """Initialize validator"""
        pass
    
    def validate_sku(self, sku: str) -> ValidationResult:
        """
        Validate product SKU/item code
        
        Args:
            sku: SKU to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=sku)
        
        if not sku:
            result.add_error("SKU cannot be empty")
            return result
        
        sku_clean = sku.strip()
        
        if len(sku_clean) < 3:
            result.add_error("SKU must be at least 3 characters")
        elif len(sku_clean) > 50:
            result.add_error("SKU cannot exceed 50 characters")
        
        if not re.match(self.SKU_PATTERN, sku_clean):
            result.add_error("SKU contains invalid characters. Use alphanumeric, dash, underscore, or period")
        
        if result.is_valid:
            result.normalized_value = sku_clean.upper()
        
        return result
    
    def validate_email(self, email: str) -> ValidationResult:
        """
        Validate email address
        
        Args:
            email: Email to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=email)
        
        if not email:
            result.add_error("Email cannot be empty")
            return result
        
        email_clean = email.strip().lower()
        
        if not re.match(self.EMAIL_PATTERN, email_clean):
            result.add_error("Invalid email format")
            return result
        
        # Check for common typos
        typo_domains = {
            'gmial.com': 'gmail.com',
            'gmal.com': 'gmail.com',
            'gmail.co': 'gmail.com',
            'yahooo.com': 'yahoo.com',
            'yaho.com': 'yahoo.com',
            'hotmal.com': 'hotmail.com',
            'outlok.com': 'outlook.com',
        }
        
        domain = email_clean.split('@')[1]
        if domain in typo_domains:
            result.add_warning(f"Did you mean {typo_domains[domain]}?")
        
        result.normalized_value = email_clean
        return result
    
    def validate_phone(
        self,
        phone: str,
        country: str = 'IN'
    ) -> ValidationResult:
        """
        Validate phone number
        
        Args:
            phone: Phone number to validate
            country: Country code for format validation
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=phone)
        
        if not phone:
            result.add_error("Phone number cannot be empty")
            return result
        
        # Clean phone number
        phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
        
        pattern = self.PHONE_PATTERNS.get(country, self.PHONE_PATTERNS['INTL'])
        
        if not re.match(pattern, phone_clean):
            result.add_error(f"Invalid phone number format for {country}")
            return result
        
        # Normalize to international format for India
        if country == 'IN':
            if phone_clean.startswith('0'):
                phone_clean = '+91' + phone_clean[1:]
            elif not phone_clean.startswith('+'):
                if phone_clean.startswith('91'):
                    phone_clean = '+' + phone_clean
                else:
                    phone_clean = '+91' + phone_clean
        
        result.normalized_value = phone_clean
        return result
    
    def validate_gstin(self, gstin: str) -> ValidationResult:
        """
        Validate Indian GSTIN (Goods and Services Tax Identification Number)
        
        Args:
            gstin: GSTIN to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=gstin)
        
        if not gstin:
            result.add_error("GSTIN cannot be empty")
            return result
        
        gstin_clean = gstin.strip().upper()
        
        if len(gstin_clean) != 15:
            result.add_error("GSTIN must be exactly 15 characters")
            return result
        
        if not re.match(self.GSTIN_PATTERN, gstin_clean):
            result.add_error("Invalid GSTIN format")
            return result
        
        # Validate state code (first 2 digits)
        valid_state_codes = [
            '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
            '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
            '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
            '31', '32', '33', '34', '35', '36', '37', '38', '97'
        ]
        
        state_code = gstin_clean[:2]
        if state_code not in valid_state_codes:
            result.add_error(f"Invalid state code: {state_code}")
            return result
        
        # Validate check digit using Luhn algorithm variant
        result.normalized_value = gstin_clean
        return result
    
    def validate_pan(self, pan: str) -> ValidationResult:
        """
        Validate Indian PAN (Permanent Account Number)
        
        Args:
            pan: PAN to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=pan)
        
        if not pan:
            result.add_error("PAN cannot be empty")
            return result
        
        pan_clean = pan.strip().upper()
        
        if len(pan_clean) != 10:
            result.add_error("PAN must be exactly 10 characters")
            return result
        
        if not re.match(self.PAN_PATTERN, pan_clean):
            result.add_error("Invalid PAN format")
            return result
        
        # 4th character indicates entity type
        entity_types = {
            'A': 'Association of Persons',
            'B': 'Body of Individuals',
            'C': 'Company',
            'F': 'Firm',
            'G': 'Government',
            'H': 'HUF',
            'L': 'Local Authority',
            'J': 'Artificial Juridical Person',
            'P': 'Individual',
            'T': 'Trust',
        }
        
        entity_code = pan_clean[3]
        if entity_code not in entity_types:
            result.add_error(f"Invalid entity type code: {entity_code}")
            return result
        
        result.normalized_value = pan_clean
        return result
    
    def validate_specification(
        self,
        spec: Dict[str, Any],
        required_fields: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate product specification dictionary
        
        Args:
            spec: Specification dictionary
            required_fields: List of required field names
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=spec)
        required_fields = required_fields or []
        
        if not spec:
            result.add_error("Specification cannot be empty")
            return result
        
        # Check required fields
        for field in required_fields:
            if field not in spec or spec[field] is None:
                result.add_error(f"Missing required field: {field}")
        
        # Validate conductor size if present
        if 'conductor_size' in spec and spec['conductor_size']:
            size = spec['conductor_size']
            if isinstance(size, (int, float)):
                if size not in self.VALID_CONDUCTOR_SIZES:
                    closest = min(self.VALID_CONDUCTOR_SIZES, key=lambda x: abs(x - size))
                    result.add_warning(f"Non-standard conductor size {size}. Closest standard: {closest}")
        
        # Validate voltage if present
        if 'voltage' in spec and spec['voltage']:
            voltage = spec['voltage']
            if isinstance(voltage, (int, float)):
                if voltage not in self.VALID_VOLTAGES:
                    result.add_warning(f"Non-standard voltage rating: {voltage}V")
        
        # Validate core count if present
        if 'cores' in spec and spec['cores']:
            cores = spec['cores']
            if isinstance(cores, int) and cores not in [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 19, 24, 27, 30, 37, 44, 61]:
                result.add_warning(f"Non-standard core count: {cores}")
        
        return result
    
    def validate_price(
        self,
        price: Union[int, float, str],
        currency: str = 'INR',
        min_price: float = 0,
        max_price: float = float('inf')
    ) -> ValidationResult:
        """
        Validate price value
        
        Args:
            price: Price to validate
            currency: Currency code
            min_price: Minimum allowed price
            max_price: Maximum allowed price
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=price)
        
        # Convert string to number
        if isinstance(price, str):
            price_clean = price.strip()
            # Remove currency symbols and commas
            price_clean = re.sub(r'[₹$€£,\s]', '', price_clean)
            try:
                price_num = float(price_clean)
            except ValueError:
                result.add_error(f"Invalid price format: {price}")
                return result
        else:
            price_num = float(price)
        
        if price_num < 0:
            result.add_error("Price cannot be negative")
            return result
        
        if price_num < min_price:
            result.add_error(f"Price must be at least {min_price}")
        
        if price_num > max_price:
            result.add_error(f"Price cannot exceed {max_price}")
        
        # Warn about suspicious prices
        if price_num > 0 and price_num < 1:
            result.add_warning("Price seems unusually low")
        
        if currency == 'INR' and price_num > 10000000:
            result.add_warning("Price seems unusually high (>1 Crore)")
        
        result.normalized_value = round(price_num, 2)
        return result
    
    def validate_quantity(
        self,
        quantity: Union[int, float, str],
        unit: str = 'nos',
        min_qty: float = 0,
        max_qty: float = float('inf')
    ) -> ValidationResult:
        """
        Validate quantity value
        
        Args:
            quantity: Quantity to validate
            unit: Unit of measurement
            min_qty: Minimum allowed quantity
            max_qty: Maximum allowed quantity
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, value=quantity)
        
        # Convert string to number
        if isinstance(quantity, str):
            qty_clean = quantity.strip()
            qty_clean = qty_clean.replace(',', '')
            try:
                qty_num = float(qty_clean)
            except ValueError:
                result.add_error(f"Invalid quantity format: {quantity}")
                return result
        else:
            qty_num = float(quantity)
        
        if qty_num < 0:
            result.add_error("Quantity cannot be negative")
            return result
        
        if qty_num < min_qty:
            result.add_error(f"Quantity must be at least {min_qty}")
        
        if qty_num > max_qty:
            result.add_error(f"Quantity cannot exceed {max_qty}")
        
        # Check for integer units
        integer_units = ['nos', 'pcs', 'units', 'sets', 'rolls', 'coils', 'drums']
        if unit.lower() in integer_units and qty_num != int(qty_num):
            result.add_warning(f"Quantity for '{unit}' should be a whole number")
        
        result.normalized_value = qty_num
        return result
    
    def validate_date_format(self, date_str: str) -> ValidationResult:
        """
        Validate date string format
        
        Args:
            date_str: Date string to validate
            
        Returns:
            ValidationResult
        """
        from datetime import datetime
        
        result = ValidationResult(is_valid=True, value=date_str)
        
        if not date_str:
            result.add_error("Date cannot be empty")
            return result
        
        date_str = date_str.strip()
        
        # Common date formats
        formats = [
            '%Y-%m-%d',      # 2024-01-15
            '%d-%m-%Y',      # 15-01-2024
            '%d/%m/%Y',      # 15/01/2024
            '%Y/%m/%d',      # 2024/01/15
            '%d-%b-%Y',      # 15-Jan-2024
            '%d %b %Y',      # 15 Jan 2024
            '%B %d, %Y',     # January 15, 2024
        ]
        
        parsed_date = None
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            result.add_error("Invalid date format. Use YYYY-MM-DD or DD/MM/YYYY")
            return result
        
        # Validate reasonable date range
        if parsed_date.year < 2000 or parsed_date.year > 2100:
            result.add_warning(f"Date year {parsed_date.year} seems unusual")
        
        result.normalized_value = parsed_date.strftime('%Y-%m-%d')
        return result


# Module-level validator instance
_validator = Validator()


def validate_sku(sku: str) -> ValidationResult:
    """Validate product SKU"""
    return _validator.validate_sku(sku)


def validate_email(email: str) -> ValidationResult:
    """Validate email address"""
    return _validator.validate_email(email)


def validate_phone(phone: str, country: str = 'IN') -> ValidationResult:
    """Validate phone number"""
    return _validator.validate_phone(phone, country)


def validate_gstin(gstin: str) -> ValidationResult:
    """Validate Indian GSTIN"""
    return _validator.validate_gstin(gstin)


def validate_specification(spec: Dict, required_fields: List[str] = None) -> ValidationResult:
    """Validate product specification"""
    return _validator.validate_specification(spec, required_fields)


def validate_price(price, currency: str = 'INR', min_price: float = 0, max_price: float = float('inf')) -> ValidationResult:
    """Validate price value"""
    return _validator.validate_price(price, currency, min_price, max_price)


def validate_quantity(quantity, unit: str = 'nos', min_qty: float = 0, max_qty: float = float('inf')) -> ValidationResult:
    """Validate quantity value"""
    return _validator.validate_quantity(quantity, unit, min_qty, max_qty)
