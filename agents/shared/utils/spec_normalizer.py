"""
Specification Normalizer
Normalizes product specifications to standard formats

Features:
- Conductor size normalization
- Voltage rating normalization
- Temperature rating normalization
- Material name normalization
- Unit standardization
"""

import re
from typing import Dict, Any, Optional, Union, List, Tuple
from dataclasses import dataclass
from enum import Enum


class MaterialType(Enum):
    """Standard material types"""
    COPPER = "copper"
    ALUMINIUM = "aluminium"
    TINNED_COPPER = "tinned_copper"
    SILVER_PLATED = "silver_plated"
    GALVANIZED_STEEL = "galvanized_steel"
    UNKNOWN = "unknown"


class InsulationType(Enum):
    """Standard insulation types"""
    PVC = "pvc"
    XLPE = "xlpe"
    RUBBER = "rubber"
    SILICON = "silicon"
    TEFLON = "teflon"
    PE = "pe"
    EPR = "epr"
    FRLS = "frls"
    LSZH = "lszh"
    UNKNOWN = "unknown"


@dataclass
class NormalizedSpec:
    """Normalized specification result"""
    original: str
    normalized: Any
    unit: Optional[str]
    confidence: float
    warnings: List[str]


class SpecificationNormalizer:
    """
    Normalizes product specifications to standard formats
    """
    
    # Material aliases mapping
    MATERIAL_ALIASES = {
        # Copper variants
        'copper': MaterialType.COPPER,
        'cu': MaterialType.COPPER,
        'electrolytic copper': MaterialType.COPPER,
        'etp copper': MaterialType.COPPER,
        'bare copper': MaterialType.COPPER,
        'annealed copper': MaterialType.COPPER,
        
        # Aluminium variants
        'aluminium': MaterialType.ALUMINIUM,
        'aluminum': MaterialType.ALUMINIUM,
        'al': MaterialType.ALUMINIUM,
        'aaac': MaterialType.ALUMINIUM,
        'aac': MaterialType.ALUMINIUM,
        
        # Tinned copper
        'tinned copper': MaterialType.TINNED_COPPER,
        'tin plated copper': MaterialType.TINNED_COPPER,
        'tc': MaterialType.TINNED_COPPER,
        
        # Silver plated
        'silver plated': MaterialType.SILVER_PLATED,
        'silver plated copper': MaterialType.SILVER_PLATED,
        'spc': MaterialType.SILVER_PLATED,
        
        # Steel
        'galvanized steel': MaterialType.GALVANIZED_STEEL,
        'gi': MaterialType.GALVANIZED_STEEL,
        'gs': MaterialType.GALVANIZED_STEEL,
        'steel': MaterialType.GALVANIZED_STEEL,
    }
    
    # Insulation aliases mapping
    INSULATION_ALIASES = {
        # PVC
        'pvc': InsulationType.PVC,
        'polyvinyl chloride': InsulationType.PVC,
        'poly vinyl chloride': InsulationType.PVC,
        
        # XLPE
        'xlpe': InsulationType.XLPE,
        'cross linked polyethylene': InsulationType.XLPE,
        'cross-linked polyethylene': InsulationType.XLPE,
        'crosslinked pe': InsulationType.XLPE,
        
        # Rubber
        'rubber': InsulationType.RUBBER,
        'natural rubber': InsulationType.RUBBER,
        'nr': InsulationType.RUBBER,
        
        # Silicon
        'silicon': InsulationType.SILICON,
        'silicone': InsulationType.SILICON,
        'si': InsulationType.SILICON,
        
        # Teflon/PTFE
        'teflon': InsulationType.TEFLON,
        'ptfe': InsulationType.TEFLON,
        'polytetrafluoroethylene': InsulationType.TEFLON,
        
        # PE
        'pe': InsulationType.PE,
        'polyethylene': InsulationType.PE,
        'hdpe': InsulationType.PE,
        'ldpe': InsulationType.PE,
        
        # EPR
        'epr': InsulationType.EPR,
        'ethylene propylene rubber': InsulationType.EPR,
        'epdm': InsulationType.EPR,
        
        # FRLS
        'frls': InsulationType.FRLS,
        'flame retardant low smoke': InsulationType.FRLS,
        'fr': InsulationType.FRLS,
        
        # LSZH
        'lszh': InsulationType.LSZH,
        'lsoh': InsulationType.LSZH,
        'ls0h': InsulationType.LSZH,
        'low smoke zero halogen': InsulationType.LSZH,
        'halogen free': InsulationType.LSZH,
    }
    
    # Standard conductor sizes (sq mm)
    STANDARD_SIZES = [
        0.5, 0.75, 1.0, 1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0,
        35.0, 50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0,
        300.0, 400.0, 500.0, 630.0, 800.0, 1000.0
    ]
    
    # AWG to sq mm conversion
    AWG_TO_SQMM = {
        '0000': 107.2, '000': 85.0, '00': 67.4, '0': 53.5,
        '1': 42.4, '2': 33.6, '3': 26.7, '4': 21.2,
        '5': 16.8, '6': 13.3, '7': 10.5, '8': 8.37,
        '9': 6.63, '10': 5.26, '11': 4.17, '12': 3.31,
        '13': 2.62, '14': 2.08, '15': 1.65, '16': 1.31,
        '17': 1.04, '18': 0.823, '19': 0.653, '20': 0.518,
        '21': 0.410, '22': 0.326, '23': 0.258, '24': 0.205,
        '25': 0.162, '26': 0.129, '27': 0.102, '28': 0.0810,
        '29': 0.0642, '30': 0.0509
    }
    
    def __init__(self):
        """Initialize normalizer"""
        self._cache = {}
    
    def normalize_conductor_size(
        self,
        value: Union[str, float, int],
        input_unit: str = 'sqmm'
    ) -> NormalizedSpec:
        """
        Normalize conductor size to sq mm
        
        Args:
            value: Input conductor size
            input_unit: Input unit (sqmm, awg, kcmil, mm)
            
        Returns:
            NormalizedSpec with normalized value
        """
        warnings = []
        original = str(value)
        
        try:
            # Handle string input
            if isinstance(value, str):
                value = value.strip().lower()
                
                # Extract numeric part and unit
                match = re.match(r'([\d.]+)\s*(sqmm|sq\.?mm|mm2|mm²|awg|kcmil|mcm)?', value)
                if match:
                    num_str = match.group(1)
                    unit = match.group(2) or input_unit
                    value = float(num_str)
                    input_unit = unit.lower() if unit else 'sqmm'
                
                # Check for AWG notation like "12 AWG"
                awg_match = re.match(r'(\d{1,4}|0{1,4})\s*awg', value)
                if awg_match:
                    awg_value = awg_match.group(1)
                    if awg_value in self.AWG_TO_SQMM:
                        value = self.AWG_TO_SQMM[awg_value]
                        input_unit = 'sqmm'
            
            # Convert to sq mm
            if isinstance(value, (int, float)):
                if input_unit in ['awg']:
                    awg_key = str(int(value))
                    if awg_key in self.AWG_TO_SQMM:
                        value = self.AWG_TO_SQMM[awg_key]
                    else:
                        warnings.append(f"Unknown AWG value: {awg_key}")
                        return NormalizedSpec(original, None, None, 0.0, warnings)
                
                elif input_unit in ['kcmil', 'mcm']:
                    value = value * 0.5067  # kcmil to sq mm
                
                elif input_unit in ['mm', 'diameter']:
                    # Assume diameter, convert to area
                    import math
                    value = math.pi * (value / 2) ** 2
                
                # Round to nearest standard size if close
                normalized = self._find_nearest_standard_size(value)
                if abs(normalized - value) / value > 0.1:
                    warnings.append(f"Non-standard size: {value} sq mm")
                    normalized = round(value, 2)
                
                return NormalizedSpec(
                    original=original,
                    normalized=normalized,
                    unit='sqmm',
                    confidence=1.0 if not warnings else 0.8,
                    warnings=warnings
                )
        
        except Exception as e:
            warnings.append(f"Error normalizing: {str(e)}")
        
        return NormalizedSpec(original, None, None, 0.0, warnings)
    
    def _find_nearest_standard_size(self, value: float) -> float:
        """Find nearest standard conductor size"""
        if value <= 0:
            return 0.0
        
        closest = min(self.STANDARD_SIZES, key=lambda x: abs(x - value))
        
        # Only use standard if within 10%
        if abs(closest - value) / value <= 0.1:
            return closest
        return value
    
    def normalize_voltage(
        self,
        value: Union[str, float, int],
        input_unit: str = 'v'
    ) -> NormalizedSpec:
        """
        Normalize voltage rating
        
        Args:
            value: Input voltage
            input_unit: Input unit (v, kv, mv)
            
        Returns:
            NormalizedSpec with normalized value in volts
        """
        warnings = []
        original = str(value)
        
        try:
            if isinstance(value, str):
                value = value.strip().lower()
                
                # Handle voltage ranges like "600/1000V"
                range_match = re.match(r'(\d+)\s*/\s*(\d+)\s*(v|kv)?', value)
                if range_match:
                    v1 = float(range_match.group(1))
                    v2 = float(range_match.group(2))
                    unit = range_match.group(3) or 'v'
                    
                    if unit == 'kv':
                        v1 *= 1000
                        v2 *= 1000
                    
                    return NormalizedSpec(
                        original=original,
                        normalized={'low': v1, 'high': v2},
                        unit='V',
                        confidence=1.0,
                        warnings=warnings
                    )
                
                # Handle single voltage
                match = re.match(r'([\d.]+)\s*(v|kv|mv)?', value)
                if match:
                    value = float(match.group(1))
                    input_unit = match.group(2) or input_unit
            
            if isinstance(value, (int, float)):
                # Convert to volts
                if input_unit.lower() == 'kv':
                    value *= 1000
                elif input_unit.lower() == 'mv':
                    value /= 1000
                
                return NormalizedSpec(
                    original=original,
                    normalized=value,
                    unit='V',
                    confidence=1.0,
                    warnings=warnings
                )
        
        except Exception as e:
            warnings.append(f"Error normalizing voltage: {str(e)}")
        
        return NormalizedSpec(original, None, None, 0.0, warnings)
    
    def normalize_temperature(
        self,
        value: Union[str, float, int],
        input_unit: str = 'c'
    ) -> NormalizedSpec:
        """
        Normalize temperature rating to Celsius
        
        Args:
            value: Input temperature
            input_unit: Input unit (c, f, k)
            
        Returns:
            NormalizedSpec with normalized value in Celsius
        """
        warnings = []
        original = str(value)
        
        try:
            if isinstance(value, str):
                value = value.strip().lower()
                
                # Handle range like "-40 to +90°C"
                range_match = re.match(r'([+-]?\d+)\s*(?:to|~|-)\s*([+-]?\d+)\s*[°]?([cfk])?', value)
                if range_match:
                    t1 = float(range_match.group(1))
                    t2 = float(range_match.group(2))
                    unit = range_match.group(3) or input_unit
                    
                    if unit == 'f':
                        t1 = (t1 - 32) * 5/9
                        t2 = (t2 - 32) * 5/9
                    elif unit == 'k':
                        t1 -= 273.15
                        t2 -= 273.15
                    
                    return NormalizedSpec(
                        original=original,
                        normalized={'min': t1, 'max': t2},
                        unit='°C',
                        confidence=1.0,
                        warnings=warnings
                    )
                
                # Handle single temperature
                match = re.match(r'([+-]?\d+)\s*[°]?([cfk])?', value)
                if match:
                    value = float(match.group(1))
                    input_unit = match.group(2) or input_unit
            
            if isinstance(value, (int, float)):
                # Convert to Celsius
                if input_unit.lower() == 'f':
                    value = (value - 32) * 5/9
                elif input_unit.lower() == 'k':
                    value -= 273.15
                
                return NormalizedSpec(
                    original=original,
                    normalized=round(value, 1),
                    unit='°C',
                    confidence=1.0,
                    warnings=warnings
                )
        
        except Exception as e:
            warnings.append(f"Error normalizing temperature: {str(e)}")
        
        return NormalizedSpec(original, None, None, 0.0, warnings)
    
    def normalize_material(
        self,
        value: str,
        material_type: str = 'conductor'
    ) -> NormalizedSpec:
        """
        Normalize material name
        
        Args:
            value: Input material name
            material_type: Type of material (conductor, insulation)
            
        Returns:
            NormalizedSpec with normalized material enum
        """
        warnings = []
        original = value
        
        try:
            value_lower = value.strip().lower()
            
            if material_type == 'conductor':
                aliases = self.MATERIAL_ALIASES
                default = MaterialType.UNKNOWN
            else:
                aliases = self.INSULATION_ALIASES
                default = InsulationType.UNKNOWN
            
            # Direct match
            if value_lower in aliases:
                return NormalizedSpec(
                    original=original,
                    normalized=aliases[value_lower],
                    unit=None,
                    confidence=1.0,
                    warnings=warnings
                )
            
            # Partial match
            for alias, material in aliases.items():
                if alias in value_lower or value_lower in alias:
                    warnings.append(f"Partial match: '{value}' -> '{alias}'")
                    return NormalizedSpec(
                        original=original,
                        normalized=material,
                        unit=None,
                        confidence=0.8,
                        warnings=warnings
                    )
            
            warnings.append(f"Unknown material: {value}")
            return NormalizedSpec(original, default, None, 0.5, warnings)
        
        except Exception as e:
            warnings.append(f"Error normalizing material: {str(e)}")
        
        return NormalizedSpec(original, None, None, 0.0, warnings)
    
    def normalize_all(self, specs: Dict[str, Any]) -> Dict[str, NormalizedSpec]:
        """
        Normalize all specifications in a dictionary
        
        Args:
            specs: Dictionary of specifications
            
        Returns:
            Dictionary of normalized specifications
        """
        result = {}
        
        # Map field names to normalization methods
        normalizers = {
            'conductor_size': self.normalize_conductor_size,
            'conductor_size_sqmm': self.normalize_conductor_size,
            'cross_section': self.normalize_conductor_size,
            'voltage': self.normalize_voltage,
            'voltage_rating': self.normalize_voltage,
            'rated_voltage': self.normalize_voltage,
            'temperature': self.normalize_temperature,
            'temperature_rating': self.normalize_temperature,
            'operating_temp': self.normalize_temperature,
            'conductor_material': lambda v: self.normalize_material(v, 'conductor'),
            'material': lambda v: self.normalize_material(v, 'conductor'),
            'insulation': lambda v: self.normalize_material(v, 'insulation'),
            'insulation_type': lambda v: self.normalize_material(v, 'insulation'),
        }
        
        for key, value in specs.items():
            key_lower = key.lower().replace(' ', '_')
            
            if key_lower in normalizers:
                result[key] = normalizers[key_lower](value)
            else:
                # Pass through unchanged
                result[key] = NormalizedSpec(
                    original=str(value),
                    normalized=value,
                    unit=None,
                    confidence=1.0,
                    warnings=[]
                )
        
        return result


# Module-level functions for convenience
_normalizer = SpecificationNormalizer()


def normalize_specification(specs: Dict[str, Any]) -> Dict[str, NormalizedSpec]:
    """Normalize all specifications"""
    return _normalizer.normalize_all(specs)


def normalize_conductor_size(value: Union[str, float], unit: str = 'sqmm') -> NormalizedSpec:
    """Normalize conductor size"""
    return _normalizer.normalize_conductor_size(value, unit)


def normalize_voltage(value: Union[str, float], unit: str = 'v') -> NormalizedSpec:
    """Normalize voltage"""
    return _normalizer.normalize_voltage(value, unit)


def normalize_temperature(value: Union[str, float], unit: str = 'c') -> NormalizedSpec:
    """Normalize temperature"""
    return _normalizer.normalize_temperature(value, unit)


def normalize_material(value: str, material_type: str = 'conductor') -> NormalizedSpec:
    """Normalize material name"""
    return _normalizer.normalize_material(value, material_type)
