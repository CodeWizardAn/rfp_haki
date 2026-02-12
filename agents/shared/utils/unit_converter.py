"""
Unit Conversion Utilities
Comprehensive unit conversion for electrical and physical measurements

Features:
- Length conversions (m, cm, mm, ft, inch, km)
- Area conversions (sqmm, sqm, sqft, sqinch)
- Temperature conversions (C, F, K)
- Voltage conversions (V, kV, mV)
- Current conversions (A, mA, kA)
- Weight conversions (kg, g, lb, oz)
- Power conversions (W, kW, MW, HP)
"""

from typing import Union, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class UnitCategory(Enum):
    """Categories of units"""
    LENGTH = "length"
    AREA = "area"
    TEMPERATURE = "temperature"
    VOLTAGE = "voltage"
    CURRENT = "current"
    WEIGHT = "weight"
    POWER = "power"
    FREQUENCY = "frequency"
    RESISTANCE = "resistance"


@dataclass
class ConversionResult:
    """Result of a unit conversion"""
    value: float
    from_unit: str
    to_unit: str
    original_value: float
    success: bool
    error: Optional[str] = None


class UnitConverter:
    """
    Comprehensive unit converter for electrical and physical measurements
    """
    
    # Length conversion factors (to meters)
    LENGTH_TO_METER = {
        'm': 1.0,
        'meter': 1.0,
        'meters': 1.0,
        'cm': 0.01,
        'centimeter': 0.01,
        'mm': 0.001,
        'millimeter': 0.001,
        'km': 1000.0,
        'kilometer': 1000.0,
        'ft': 0.3048,
        'foot': 0.3048,
        'feet': 0.3048,
        'in': 0.0254,
        'inch': 0.0254,
        'inches': 0.0254,
        'yd': 0.9144,
        'yard': 0.9144,
        'mi': 1609.344,
        'mile': 1609.344,
    }
    
    # Area conversion factors (to sq meters)
    AREA_TO_SQM = {
        'sqm': 1.0,
        'sq m': 1.0,
        'm2': 1.0,
        'm²': 1.0,
        'sqmm': 1e-6,
        'sq mm': 1e-6,
        'mm2': 1e-6,
        'mm²': 1e-6,
        'sqcm': 1e-4,
        'sq cm': 1e-4,
        'cm2': 1e-4,
        'sqft': 0.092903,
        'sq ft': 0.092903,
        'ft2': 0.092903,
        'sqin': 0.00064516,
        'sq in': 0.00064516,
        'in2': 0.00064516,
        'acre': 4046.86,
        'hectare': 10000.0,
        'ha': 10000.0,
    }
    
    # Weight conversion factors (to kg)
    WEIGHT_TO_KG = {
        'kg': 1.0,
        'kilogram': 1.0,
        'g': 0.001,
        'gram': 0.001,
        'mg': 1e-6,
        'milligram': 1e-6,
        'lb': 0.453592,
        'pound': 0.453592,
        'oz': 0.0283495,
        'ounce': 0.0283495,
        'ton': 1000.0,
        'tonne': 1000.0,
        'mt': 1000.0,
    }
    
    # Voltage conversion factors (to volts)
    VOLTAGE_TO_V = {
        'v': 1.0,
        'volt': 1.0,
        'volts': 1.0,
        'mv': 0.001,
        'millivolt': 0.001,
        'kv': 1000.0,
        'kilovolt': 1000.0,
    }
    
    # Current conversion factors (to amperes)
    CURRENT_TO_A = {
        'a': 1.0,
        'amp': 1.0,
        'ampere': 1.0,
        'amps': 1.0,
        'ma': 0.001,
        'milliamp': 0.001,
        'milliampere': 0.001,
        'ka': 1000.0,
        'kiloamp': 1000.0,
        'ua': 1e-6,
        'microamp': 1e-6,
    }
    
    # Power conversion factors (to watts)
    POWER_TO_W = {
        'w': 1.0,
        'watt': 1.0,
        'watts': 1.0,
        'mw': 0.001,
        'milliwatt': 0.001,
        'kw': 1000.0,
        'kilowatt': 1000.0,
        'mw_mega': 1e6,  # Use mw_mega for megawatt
        'megawatt': 1e6,
        'hp': 745.7,
        'horsepower': 745.7,
        'bhp': 745.7,
        'va': 1.0,
        'kva': 1000.0,
    }
    
    # Resistance conversion factors (to ohms)
    RESISTANCE_TO_OHM = {
        'ohm': 1.0,
        'Ω': 1.0,
        'mohm': 0.001,
        'milliohm': 0.001,
        'kohm': 1000.0,
        'kilohm': 1000.0,
        'megohm': 1e6,
    }
    
    # Frequency conversion factors (to Hz)
    FREQUENCY_TO_HZ = {
        'hz': 1.0,
        'hertz': 1.0,
        'khz': 1000.0,
        'kilohertz': 1000.0,
        'mhz': 1e6,
        'megahertz': 1e6,
        'ghz': 1e9,
        'gigahertz': 1e9,
    }
    
    def __init__(self):
        """Initialize unit converter"""
        self._category_maps = {
            UnitCategory.LENGTH: self.LENGTH_TO_METER,
            UnitCategory.AREA: self.AREA_TO_SQM,
            UnitCategory.WEIGHT: self.WEIGHT_TO_KG,
            UnitCategory.VOLTAGE: self.VOLTAGE_TO_V,
            UnitCategory.CURRENT: self.CURRENT_TO_A,
            UnitCategory.POWER: self.POWER_TO_W,
            UnitCategory.RESISTANCE: self.RESISTANCE_TO_OHM,
            UnitCategory.FREQUENCY: self.FREQUENCY_TO_HZ,
        }
    
    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit string"""
        return unit.lower().strip().replace('-', '').replace('_', ' ')
    
    def _get_category(self, unit: str) -> Optional[Tuple[UnitCategory, Dict]]:
        """Determine the category of a unit"""
        unit = self._normalize_unit(unit)
        
        for category, conversion_map in self._category_maps.items():
            if unit in conversion_map:
                return category, conversion_map
        
        return None
    
    def convert(
        self,
        value: Union[float, int, str],
        from_unit: str,
        to_unit: str
    ) -> ConversionResult:
        """
        Convert a value between units
        
        Args:
            value: The value to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            ConversionResult with converted value
        """
        try:
            # Parse value if string
            if isinstance(value, str):
                value = float(value.replace(',', ''))
            
            original_value = value
            from_unit_norm = self._normalize_unit(from_unit)
            to_unit_norm = self._normalize_unit(to_unit)
            
            # Handle temperature separately (non-linear conversion)
            if from_unit_norm in ['c', 'celsius', 'f', 'fahrenheit', 'k', 'kelvin']:
                return self._convert_temperature(value, from_unit_norm, to_unit_norm)
            
            # Find category
            from_cat = self._get_category(from_unit_norm)
            to_cat = self._get_category(to_unit_norm)
            
            if from_cat is None:
                return ConversionResult(
                    value=0.0, from_unit=from_unit, to_unit=to_unit,
                    original_value=original_value, success=False,
                    error=f"Unknown source unit: {from_unit}"
                )
            
            if to_cat is None:
                return ConversionResult(
                    value=0.0, from_unit=from_unit, to_unit=to_unit,
                    original_value=original_value, success=False,
                    error=f"Unknown target unit: {to_unit}"
                )
            
            if from_cat[0] != to_cat[0]:
                return ConversionResult(
                    value=0.0, from_unit=from_unit, to_unit=to_unit,
                    original_value=original_value, success=False,
                    error=f"Cannot convert between {from_cat[0].value} and {to_cat[0].value}"
                )
            
            # Convert via base unit
            conversion_map = from_cat[1]
            base_value = value * conversion_map[from_unit_norm]
            result_value = base_value / conversion_map[to_unit_norm]
            
            return ConversionResult(
                value=result_value,
                from_unit=from_unit,
                to_unit=to_unit,
                original_value=original_value,
                success=True
            )
            
        except Exception as e:
            return ConversionResult(
                value=0.0, from_unit=from_unit, to_unit=to_unit,
                original_value=float(value) if isinstance(value, (int, float)) else 0.0,
                success=False, error=str(e)
            )
    
    def _convert_temperature(
        self,
        value: float,
        from_unit: str,
        to_unit: str
    ) -> ConversionResult:
        """Convert temperature (non-linear conversion)"""
        original_value = value
        
        # Normalize unit names
        unit_map = {
            'c': 'c', 'celsius': 'c',
            'f': 'f', 'fahrenheit': 'f',
            'k': 'k', 'kelvin': 'k'
        }
        
        from_u = unit_map.get(from_unit, from_unit)
        to_u = unit_map.get(to_unit, to_unit)
        
        if from_u not in ['c', 'f', 'k'] or to_u not in ['c', 'f', 'k']:
            return ConversionResult(
                value=0.0, from_unit=from_unit, to_unit=to_unit,
                original_value=original_value, success=False,
                error="Invalid temperature unit"
            )
        
        # Convert to Celsius first
        if from_u == 'c':
            celsius = value
        elif from_u == 'f':
            celsius = (value - 32) * 5 / 9
        else:  # kelvin
            celsius = value - 273.15
        
        # Convert from Celsius to target
        if to_u == 'c':
            result = celsius
        elif to_u == 'f':
            result = celsius * 9 / 5 + 32
        else:  # kelvin
            result = celsius + 273.15
        
        return ConversionResult(
            value=result,
            from_unit=from_unit,
            to_unit=to_unit,
            original_value=original_value,
            success=True
        )
    
    def convert_length(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert length units"""
        result = self.convert(value, from_unit, to_unit)
        if result.success:
            return result.value
        raise ValueError(result.error)
    
    def convert_area(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert area units"""
        result = self.convert(value, from_unit, to_unit)
        if result.success:
            return result.value
        raise ValueError(result.error)
    
    def convert_weight(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert weight units"""
        result = self.convert(value, from_unit, to_unit)
        if result.success:
            return result.value
        raise ValueError(result.error)
    
    def convert_voltage(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert voltage units"""
        result = self.convert(value, from_unit, to_unit)
        if result.success:
            return result.value
        raise ValueError(result.error)
    
    def convert_current(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert current units"""
        result = self.convert(value, from_unit, to_unit)
        if result.success:
            return result.value
        raise ValueError(result.error)
    
    def get_supported_units(self, category: UnitCategory) -> list:
        """Get list of supported units for a category"""
        if category in self._category_maps:
            return list(self._category_maps[category].keys())
        elif category == UnitCategory.TEMPERATURE:
            return ['c', 'celsius', 'f', 'fahrenheit', 'k', 'kelvin']
        return []


# Module-level converter instance
_converter = UnitConverter()


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """Convert length between units"""
    return _converter.convert_length(value, from_unit, to_unit)


def convert_area(value: float, from_unit: str, to_unit: str) -> float:
    """Convert area between units"""
    return _converter.convert_area(value, from_unit, to_unit)


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between units"""
    result = _converter.convert(value, from_unit, to_unit)
    if result.success:
        return result.value
    raise ValueError(result.error)


def convert_voltage(value: float, from_unit: str, to_unit: str) -> float:
    """Convert voltage between units"""
    return _converter.convert_voltage(value, from_unit, to_unit)


def convert_current(value: float, from_unit: str, to_unit: str) -> float:
    """Convert current between units"""
    return _converter.convert_current(value, from_unit, to_unit)


def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    """Convert weight between units"""
    return _converter.convert_weight(value, from_unit, to_unit)
