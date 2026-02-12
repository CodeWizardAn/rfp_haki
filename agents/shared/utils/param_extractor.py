"""
Parameter Extraction Functions
Extract structured parameters from unstructured text

Features:
- Conductor specification extraction
- Voltage rating extraction
- Dimension extraction
- Quantity extraction
- Standards extraction
"""

import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field


@dataclass
class ExtractedParameter:
    """Extracted parameter with metadata"""
    name: str
    value: Any
    unit: Optional[str]
    confidence: float
    source_text: str
    position: Tuple[int, int]  # Start and end position in source


@dataclass
class ConductorSpec:
    """Extracted conductor specifications"""
    material: Optional[str] = None
    size_sqmm: Optional[float] = None
    number_of_cores: Optional[int] = None
    stranding: Optional[str] = None  # e.g., "7/0.67"
    class_type: Optional[str] = None  # Class 1, Class 2, Class 5, etc.
    confidence: float = 0.0
    raw_text: str = ""


@dataclass
class VoltageSpec:
    """Extracted voltage specifications"""
    rated_voltage: Optional[float] = None
    system_voltage: Optional[float] = None
    impulse_voltage: Optional[float] = None
    unit: str = "V"
    is_range: bool = False
    low_voltage: Optional[float] = None
    high_voltage: Optional[float] = None
    confidence: float = 0.0


@dataclass
class DimensionSpec:
    """Extracted dimension specifications"""
    length: Optional[float] = None
    length_unit: Optional[str] = None
    width: Optional[float] = None
    width_unit: Optional[str] = None
    height: Optional[float] = None
    height_unit: Optional[str] = None
    diameter: Optional[float] = None
    diameter_unit: Optional[str] = None
    thickness: Optional[float] = None
    thickness_unit: Optional[str] = None
    confidence: float = 0.0


@dataclass
class QuantitySpec:
    """Extracted quantity specifications"""
    value: float
    unit: str
    is_approximate: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    confidence: float = 0.0


class ParameterExtractor:
    """
    Extract structured parameters from unstructured RFP text
    """
    
    # Conductor material patterns
    MATERIAL_PATTERNS = {
        'copper': [
            r'\bcopper\b', r'\bcu\b', r'\betp\s*copper\b',
            r'\belectrolytic\s*copper\b', r'\bannealed\s*copper\b',
        ],
        'aluminium': [
            r'\balumini?um\b', r'\bal\b', r'\baaac\b', r'\baac\b',
        ],
        'tinned_copper': [
            r'\btinned\s*copper\b', r'\btin\s*plated\b', r'\btc\b',
        ],
    }
    
    # Conductor size patterns (sq mm)
    SIZE_PATTERNS = [
        r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*mm|sqmm|mm²|mm2)',
        r'(\d+(?:\.\d+)?)\s*(?:square\s*mm|square\s*millimeter)',
        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*mm|sqmm)',  # Multi-core
        r'(\d+)\s*[cC]\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(?:sq\.?\s*mm|sqmm)?',  # 4C x 25 sqmm
    ]
    
    # Voltage patterns
    VOLTAGE_PATTERNS = [
        r'(\d+)\s*/\s*(\d+)\s*[vV]',  # 600/1000V format
        r'(\d+(?:\.\d+)?)\s*[kK][vV]',  # kV format
        r'(\d+)\s*[vV](?:olt)?(?:s)?',  # V format
        r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*[vV]',  # Range
        r'rated\s*(?:voltage|volt)\s*[:\s]*(\d+)',
        r'system\s*voltage\s*[:\s]*(\d+(?:\.\d+)?)\s*[kK][vV]',
    ]
    
    # Core count patterns
    CORE_PATTERNS = [
        r'(\d+)\s*[cC]ore',
        r'(\d+)\s*[cC]\s*[xX×]',
        r'(\d+)\s*conductor',
        r'single\s*core',  # 1 core
        r'two\s*core',     # 2 core
        r'three\s*core',   # 3 core
        r'four\s*core',    # 4 core
        r'multi\s*core',   # Multiple cores
    ]
    
    # Dimension patterns
    DIMENSION_PATTERNS = {
        'length': [
            r'length\s*[:\s]*(\d+(?:\.\d+)?)\s*(m|meter|metre|km|ft|feet)',
            r'(\d+(?:\.\d+)?)\s*(m|meter|metre|km)\s*(?:length|long)',
        ],
        'diameter': [
            r'(?:outer\s*)?diameter\s*[:\s]*(\d+(?:\.\d+)?)\s*(mm|cm|inch)',
            r'(?:o\.?d\.?|od)\s*[:\s]*(\d+(?:\.\d+)?)\s*(mm)?',
        ],
        'thickness': [
            r'thickness\s*[:\s]*(\d+(?:\.\d+)?)\s*(mm|cm|inch)',
            r'(\d+(?:\.\d+)?)\s*(mm)\s*(?:thick|thickness)',
        ],
    }
    
    # Quantity patterns
    QUANTITY_PATTERNS = [
        r'(?:qty|quantity)\s*[:\s]*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(nos?|pcs?|units?|sets?|rolls?|coils?|meters?|m|km)?',
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(nos?|pcs?|units?|sets?|rolls?|coils?|meters?|m|km)',
        r'(?:approx\.?|approximately)\s*(\d+(?:,\d{3})*(?:\.\d+)?)',
        r'(\d+(?:,\d{3})*)\s*(?:to|-)\s*(\d+(?:,\d{3})*)\s*(meters?|m|km|nos?)',  # Range
    ]
    
    # Standard patterns
    STANDARD_PATTERNS = [
        r'IS[\s-]?\d{3,5}(?:-\d)?(?:\s*(?:Part|Pt\.?)\s*\d)?',
        r'IEC[\s-]?\d{4,5}(?:-\d)?',
        r'BS[\s-]?\d{4,5}',
        r'ASTM[\s-]?[A-Z]?\d{1,4}',
        r'IEEE[\s-]?\d{2,4}',
    ]
    
    def __init__(self):
        """Initialize parameter extractor"""
        pass
    
    def extract_conductor_specs(self, text: str) -> ConductorSpec:
        """
        Extract conductor specifications from text
        
        Args:
            text: Input text
            
        Returns:
            ConductorSpec with extracted values
        """
        spec = ConductorSpec(raw_text=text)
        confidence_scores = []
        
        text_lower = text.lower()
        
        # Extract material
        for material, patterns in self.MATERIAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    spec.material = material
                    confidence_scores.append(0.9)
                    break
            if spec.material:
                break
        
        # Extract size
        for pattern in self.SIZE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:
                    # Multi-core format: 4C x 25 sqmm
                    try:
                        spec.number_of_cores = int(float(groups[0]))
                        spec.size_sqmm = float(groups[1])
                    except ValueError:
                        spec.size_sqmm = float(groups[0])
                else:
                    try:
                        spec.size_sqmm = float(groups[0])
                    except ValueError:
                        pass
                
                if spec.size_sqmm:
                    confidence_scores.append(0.95)
                break
        
        # Extract number of cores
        if not spec.number_of_cores:
            for pattern in self.CORE_PATTERNS:
                match = re.search(pattern, text_lower)
                if match:
                    if 'single' in pattern:
                        spec.number_of_cores = 1
                    elif 'two' in pattern:
                        spec.number_of_cores = 2
                    elif 'three' in pattern:
                        spec.number_of_cores = 3
                    elif 'four' in pattern:
                        spec.number_of_cores = 4
                    elif 'multi' in pattern:
                        spec.number_of_cores = -1  # Indicates multi-core, exact count unknown
                    else:
                        try:
                            spec.number_of_cores = int(match.group(1))
                        except (ValueError, IndexError):
                            pass
                    
                    if spec.number_of_cores:
                        confidence_scores.append(0.9)
                    break
        
        # Extract stranding (e.g., "7/0.67")
        stranding_match = re.search(r'(\d+)/(\d+(?:\.\d+)?)', text)
        if stranding_match:
            spec.stranding = stranding_match.group(0)
            confidence_scores.append(0.85)
        
        # Extract class
        class_match = re.search(r'class\s*(\d|[1-6])', text_lower)
        if class_match:
            spec.class_type = f"Class {class_match.group(1)}"
            confidence_scores.append(0.9)
        
        # Calculate overall confidence
        spec.confidence = sum(confidence_scores) / max(len(confidence_scores), 1) if confidence_scores else 0.0
        
        return spec
    
    def extract_voltage_rating(self, text: str) -> VoltageSpec:
        """
        Extract voltage rating from text
        
        Args:
            text: Input text
            
        Returns:
            VoltageSpec with extracted values
        """
        spec = VoltageSpec()
        confidence_scores = []
        
        # Check for voltage range format (600/1000V)
        range_match = re.search(r'(\d+)\s*/\s*(\d+)\s*[vV]', text)
        if range_match:
            spec.is_range = True
            spec.low_voltage = float(range_match.group(1))
            spec.high_voltage = float(range_match.group(2))
            spec.rated_voltage = spec.high_voltage
            spec.unit = 'V'
            confidence_scores.append(0.95)
        
        # Check for kV format
        if not spec.rated_voltage:
            kv_match = re.search(r'(\d+(?:\.\d+)?)\s*[kK][vV]', text)
            if kv_match:
                spec.rated_voltage = float(kv_match.group(1)) * 1000
                spec.unit = 'V'
                confidence_scores.append(0.9)
        
        # Check for plain V format
        if not spec.rated_voltage:
            v_match = re.search(r'(\d+)\s*[vV](?:olt)?(?:s)?', text)
            if v_match:
                spec.rated_voltage = float(v_match.group(1))
                spec.unit = 'V'
                confidence_scores.append(0.85)
        
        # Check for system voltage
        sys_match = re.search(r'system\s*voltage\s*[:\s]*(\d+(?:\.\d+)?)\s*([kK]?[vV])', text, re.IGNORECASE)
        if sys_match:
            value = float(sys_match.group(1))
            unit = sys_match.group(2).lower()
            if 'k' in unit:
                value *= 1000
            spec.system_voltage = value
            confidence_scores.append(0.9)
        
        spec.confidence = sum(confidence_scores) / max(len(confidence_scores), 1) if confidence_scores else 0.0
        
        return spec
    
    def extract_dimensions(self, text: str) -> DimensionSpec:
        """
        Extract dimensions from text
        
        Args:
            text: Input text
            
        Returns:
            DimensionSpec with extracted values
        """
        spec = DimensionSpec()
        confidence_scores = []
        
        text_lower = text.lower()
        
        for dim_type, patterns in self.DIMENSION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2) if len(match.groups()) > 1 else 'mm'
                    
                    if dim_type == 'length':
                        spec.length = value
                        spec.length_unit = unit
                    elif dim_type == 'diameter':
                        spec.diameter = value
                        spec.diameter_unit = unit
                    elif dim_type == 'thickness':
                        spec.thickness = value
                        spec.thickness_unit = unit
                    
                    confidence_scores.append(0.9)
                    break
        
        spec.confidence = sum(confidence_scores) / max(len(confidence_scores), 1) if confidence_scores else 0.0
        
        return spec
    
    def extract_quantity(self, text: str) -> Optional[QuantitySpec]:
        """
        Extract quantity from text
        
        Args:
            text: Input text
            
        Returns:
            QuantitySpec or None
        """
        text_lower = text.lower()
        
        # Check for range
        range_match = re.search(
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(meters?|m|km|nos?|pcs?)?',
            text_lower
        )
        if range_match:
            min_val = float(range_match.group(1).replace(',', ''))
            max_val = float(range_match.group(2).replace(',', ''))
            unit = range_match.group(3) or 'nos'
            
            return QuantitySpec(
                value=(min_val + max_val) / 2,
                unit=unit,
                is_approximate=True,
                min_value=min_val,
                max_value=max_val,
                confidence=0.85
            )
        
        # Check for approximate
        approx_match = re.search(
            r'(?:approx\.?|approximately|about|around)\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(meters?|m|km|nos?|pcs?)?',
            text_lower
        )
        if approx_match:
            value = float(approx_match.group(1).replace(',', ''))
            unit = approx_match.group(2) or 'nos'
            
            return QuantitySpec(
                value=value,
                unit=unit,
                is_approximate=True,
                confidence=0.8
            )
        
        # Check for exact quantity
        for pattern in self.QUANTITY_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else 'nos'
                    
                    return QuantitySpec(
                        value=value,
                        unit=unit,
                        is_approximate=False,
                        confidence=0.9
                    )
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_standards_from_text(self, text: str) -> List[str]:
        """
        Extract standard codes from text
        
        Args:
            text: Input text
            
        Returns:
            List of found standard codes
        """
        found = []
        
        for pattern in self.STANDARD_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)
        
        # Normalize and deduplicate
        normalized = []
        seen = set()
        
        for std in found:
            norm = std.upper().replace('-', ' ').strip()
            if norm not in seen:
                seen.add(norm)
                normalized.append(norm)
        
        return normalized
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all parameters from text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with all extracted parameters
        """
        return {
            'conductor': self.extract_conductor_specs(text),
            'voltage': self.extract_voltage_rating(text),
            'dimensions': self.extract_dimensions(text),
            'quantity': self.extract_quantity(text),
            'standards': self.extract_standards_from_text(text),
        }


# Module-level extractor instance
_extractor = ParameterExtractor()


def extract_conductor_specs(text: str) -> ConductorSpec:
    """Extract conductor specifications from text"""
    return _extractor.extract_conductor_specs(text)


def extract_voltage_rating(text: str) -> VoltageSpec:
    """Extract voltage rating from text"""
    return _extractor.extract_voltage_rating(text)


def extract_dimensions(text: str) -> DimensionSpec:
    """Extract dimensions from text"""
    return _extractor.extract_dimensions(text)


def extract_quantity(text: str) -> Optional[QuantitySpec]:
    """Extract quantity from text"""
    return _extractor.extract_quantity(text)


def extract_standards_from_text(text: str) -> List[str]:
    """Extract standard codes from text"""
    return _extractor.extract_standards_from_text(text)
