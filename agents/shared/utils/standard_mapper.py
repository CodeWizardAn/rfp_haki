"""
Standard Equivalence Mapper
Maps between different electrical standards (IS, IEC, BS, ASTM, etc.)

Features:
- Standard code mapping
- Equivalent standard lookup
- Standard information retrieval
- Compatibility checking
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class StandardBody(Enum):
    """Standard issuing bodies"""
    BIS = "Bureau of Indian Standards"
    IEC = "International Electrotechnical Commission"
    ISO = "International Organization for Standardization"
    BS = "British Standards"
    ASTM = "American Society for Testing and Materials"
    IEEE = "Institute of Electrical and Electronics Engineers"
    NEMA = "National Electrical Manufacturers Association"
    UL = "Underwriters Laboratories"
    DIN = "Deutsches Institut für Normung"
    JIS = "Japanese Industrial Standards"
    NFC = "Norme Française"
    VDE = "Verband der Elektrotechnik"


@dataclass
class StandardInfo:
    """Information about a standard"""
    code: str
    name: str
    issuing_body: StandardBody
    description: str
    year: Optional[int] = None
    superseded_by: Optional[str] = None
    equivalents: List[str] = field(default_factory=list)
    category: str = ""
    scope: str = ""


class StandardMapper:
    """
    Maps and finds equivalences between electrical standards
    """
    
    # Standard equivalence groups for wires and cables
    EQUIVALENCE_GROUPS = {
        # LT Power Cables
        'lt_power_cables': [
            'IS 1554-1', 'IEC 60502-1', 'BS 6346', 'BS 5467',
        ],
        'lt_power_cables_xlpe': [
            'IS 7098-1', 'IEC 60502-1', 'BS 5467',
        ],
        
        # HT Power Cables
        'ht_power_cables': [
            'IS 7098-2', 'IEC 60502-2', 'BS 6622',
        ],
        
        # Control Cables
        'control_cables': [
            'IS 1554-1', 'IEC 60502-1', 'BS 6346',
        ],
        
        # Flexible Cables
        'flexible_cables': [
            'IS 694', 'IEC 60227', 'BS 6500',
        ],
        
        # Building Wires
        'building_wires': [
            'IS 694', 'IEC 60227-3', 'BS 6004',
        ],
        
        # Fire Resistant Cables
        'fire_resistant': [
            'IS 15733', 'IEC 60332-3', 'BS 6387', 'BS 8519',
        ],
        
        # Instrumentation Cables
        'instrumentation': [
            'IS 1554', 'IEC 60502', 'BS 5308',
        ],
        
        # Conductor Standards
        'conductor_copper': [
            'IS 8130', 'IEC 60228', 'BS 6360', 'ASTM B8',
        ],
        'conductor_aluminium': [
            'IS 8130', 'IEC 60228', 'BS 6360', 'ASTM B231',
        ],
        
        # Insulation Standards
        'pvc_insulation': [
            'IS 5831', 'IEC 60502', 'BS 6746',
        ],
        'xlpe_insulation': [
            'IS 7098', 'IEC 60502', 'BS 7655',
        ],
        
        # Testing Standards
        'routine_testing': [
            'IS 10810', 'IEC 60811', 'BS 6469',
        ],
        'type_testing': [
            'IS 10810', 'IEC 60811', 'IEC 62067',
        ],
    }
    
    # Detailed standard information
    STANDARDS_DB: Dict[str, StandardInfo] = {}
    
    def __init__(self):
        """Initialize the standard mapper"""
        self._build_standards_db()
        self._build_equivalence_index()
    
    def _build_standards_db(self):
        """Build the standards database"""
        standards_data = [
            # Indian Standards (IS)
            StandardInfo(
                code='IS 694',
                name='PVC Insulated Cables for Working Voltages up to 1100V',
                issuing_body=StandardBody.BIS,
                description='Specification for PVC insulated (heavy duty) electric cables',
                category='Building Wires',
                scope='Up to 1100V'
            ),
            StandardInfo(
                code='IS 1554-1',
                name='PVC Insulated Power Cables Part 1',
                issuing_body=StandardBody.BIS,
                description='PVC insulated cables for working voltages up to and including 1100V',
                category='LT Power Cables',
                scope='Up to 1100V'
            ),
            StandardInfo(
                code='IS 1554-2',
                name='PVC Insulated Power Cables Part 2',
                issuing_body=StandardBody.BIS,
                description='PVC insulated cables for working voltages from 3.3kV up to 11kV',
                category='HT Power Cables',
                scope='3.3kV to 11kV'
            ),
            StandardInfo(
                code='IS 7098-1',
                name='XLPE Insulated Power Cables Part 1',
                issuing_body=StandardBody.BIS,
                description='XLPE insulated cables for working voltages from 1.1kV up to 33kV',
                category='LT/HT Power Cables',
                scope='1.1kV to 33kV'
            ),
            StandardInfo(
                code='IS 7098-2',
                name='XLPE Insulated Power Cables Part 2',
                issuing_body=StandardBody.BIS,
                description='XLPE insulated cables for working voltages from 33kV up to 66kV',
                category='HT/EHV Power Cables',
                scope='33kV to 66kV'
            ),
            StandardInfo(
                code='IS 8130',
                name='Conductors for Insulated Electric Cables',
                issuing_body=StandardBody.BIS,
                description='Specification for conductors for insulated electric cables and flexible cords',
                category='Conductors',
                scope='All voltage grades'
            ),
            StandardInfo(
                code='IS 5831',
                name='PVC Insulation and Sheath of Electric Cables',
                issuing_body=StandardBody.BIS,
                description='Specification for PVC insulation and sheath of electric cables',
                category='Insulation',
                scope='PVC compounds'
            ),
            StandardInfo(
                code='IS 15733',
                name='Fire Survival Cables',
                issuing_body=StandardBody.BIS,
                description='Specification for fire survival cables',
                category='Fire Resistant',
                scope='Fire performance'
            ),
            
            # IEC Standards
            StandardInfo(
                code='IEC 60227',
                name='PVC Insulated Cables of Rated Voltages up to 450/750V',
                issuing_body=StandardBody.IEC,
                description='Polyvinyl chloride insulated cables',
                category='Building Wires',
                scope='Up to 450/750V'
            ),
            StandardInfo(
                code='IEC 60228',
                name='Conductors of Insulated Cables',
                issuing_body=StandardBody.IEC,
                description='Specification for conductors of insulated cables',
                category='Conductors',
                scope='All voltage grades'
            ),
            StandardInfo(
                code='IEC 60502-1',
                name='Power Cables Part 1',
                issuing_body=StandardBody.IEC,
                description='Power cables with extruded insulation for 1kV to 30kV',
                category='LT/HT Power Cables',
                scope='1kV to 30kV'
            ),
            StandardInfo(
                code='IEC 60502-2',
                name='Power Cables Part 2',
                issuing_body=StandardBody.IEC,
                description='Power cables with extruded insulation for 6kV to 30kV',
                category='HT Power Cables',
                scope='6kV to 30kV'
            ),
            StandardInfo(
                code='IEC 60332-3',
                name='Flame Propagation Test on Bunched Cables',
                issuing_body=StandardBody.IEC,
                description='Tests on cables under fire conditions',
                category='Fire Testing',
                scope='Fire performance'
            ),
            StandardInfo(
                code='IEC 60811',
                name='Cable Insulation and Sheathing Materials Testing',
                issuing_body=StandardBody.IEC,
                description='Common test methods for insulation and sheathing materials',
                category='Testing',
                scope='Material testing'
            ),
            
            # British Standards
            StandardInfo(
                code='BS 5467',
                name='Electric Cables - Thermosetting Insulated',
                issuing_body=StandardBody.BS,
                description='Armoured cables with thermosetting insulation for voltages up to 600/1000V',
                category='LT Power Cables',
                scope='Up to 600/1000V'
            ),
            StandardInfo(
                code='BS 6004',
                name='PVC Insulated Non-armoured Cables',
                issuing_body=StandardBody.BS,
                description='PVC insulated cables for voltages up to 450/750V',
                category='Building Wires',
                scope='Up to 450/750V'
            ),
            StandardInfo(
                code='BS 6346',
                name='Electric Cables - PVC Insulated Armoured',
                issuing_body=StandardBody.BS,
                description='PVC insulated armoured cables for voltages up to 600/1000V',
                category='LT Power Cables',
                scope='Up to 600/1000V'
            ),
            StandardInfo(
                code='BS 6360',
                name='Conductors in Insulated Cables',
                issuing_body=StandardBody.BS,
                description='Specification for conductors in insulated cables and cords',
                category='Conductors',
                scope='All voltage grades'
            ),
            StandardInfo(
                code='BS 6387',
                name='Fire Resistant Electric Cables',
                issuing_body=StandardBody.BS,
                description='Performance requirements for cables to maintain circuit integrity',
                category='Fire Resistant',
                scope='Fire performance'
            ),
            StandardInfo(
                code='BS 6622',
                name='High Voltage Cables up to 33kV',
                issuing_body=StandardBody.BS,
                description='Cables with extruded cross-linked polyethylene insulation',
                category='HT Power Cables',
                scope='6kV to 33kV'
            ),
            StandardInfo(
                code='BS 5308',
                name='Instrumentation Cables',
                issuing_body=StandardBody.BS,
                description='Specification for instrumentation cables',
                category='Instrumentation',
                scope='Control and signal'
            ),
        ]
        
        for std in standards_data:
            self.STANDARDS_DB[std.code.upper()] = std
            # Also index without part numbers
            base_code = re.sub(r'-\d+$', '', std.code)
            if base_code.upper() not in self.STANDARDS_DB:
                self.STANDARDS_DB[base_code.upper()] = std
    
    def _build_equivalence_index(self):
        """Build reverse index for equivalence lookup"""
        self._equivalence_index: Dict[str, Set[str]] = {}
        
        for group_name, standards in self.EQUIVALENCE_GROUPS.items():
            standards_set = set(s.upper() for s in standards)
            
            for std in standards:
                std_upper = std.upper()
                if std_upper not in self._equivalence_index:
                    self._equivalence_index[std_upper] = set()
                self._equivalence_index[std_upper].update(standards_set - {std_upper})
    
    def get_equivalent_standards(
        self,
        standard_code: str,
        include_partial: bool = True
    ) -> List[str]:
        """
        Get equivalent standards for a given standard code
        
        Args:
            standard_code: The standard code to look up
            include_partial: Include partial matches (e.g., IS 1554 matches IS 1554-1)
            
        Returns:
            List of equivalent standard codes
        """
        code_upper = standard_code.upper().strip()
        equivalents = set()
        
        # Direct lookup
        if code_upper in self._equivalence_index:
            equivalents.update(self._equivalence_index[code_upper])
        
        # Partial match (for standards with parts)
        if include_partial:
            base_code = re.sub(r'-\d+$', '', code_upper)
            
            for indexed_code, eq_set in self._equivalence_index.items():
                indexed_base = re.sub(r'-\d+$', '', indexed_code)
                if base_code == indexed_base or indexed_base == code_upper:
                    equivalents.update(eq_set)
        
        return sorted(list(equivalents))
    
    def map_standard_code(
        self,
        from_code: str,
        to_body: StandardBody
    ) -> Optional[str]:
        """
        Map a standard code to an equivalent from another standards body
        
        Args:
            from_code: Source standard code
            to_body: Target standards body
            
        Returns:
            Equivalent standard code or None
        """
        equivalents = self.get_equivalent_standards(from_code)
        
        # Get prefix for target body
        body_prefixes = {
            StandardBody.BIS: ['IS '],
            StandardBody.IEC: ['IEC '],
            StandardBody.BS: ['BS '],
            StandardBody.ASTM: ['ASTM '],
            StandardBody.IEEE: ['IEEE '],
            StandardBody.DIN: ['DIN '],
        }
        
        prefixes = body_prefixes.get(to_body, [])
        
        for eq in equivalents:
            for prefix in prefixes:
                if eq.startswith(prefix):
                    return eq
        
        return None
    
    def is_standard_equivalent(
        self,
        standard1: str,
        standard2: str
    ) -> Tuple[bool, float]:
        """
        Check if two standards are equivalent
        
        Args:
            standard1: First standard code
            standard2: Second standard code
            
        Returns:
            Tuple of (is_equivalent, confidence)
        """
        std1_upper = standard1.upper().strip()
        std2_upper = standard2.upper().strip()
        
        # Exact match
        if std1_upper == std2_upper:
            return True, 1.0
        
        # Check equivalence
        eq1 = self.get_equivalent_standards(std1_upper)
        
        if std2_upper in eq1:
            return True, 0.95
        
        # Check base codes (partial match)
        base1 = re.sub(r'-\d+$', '', std1_upper)
        base2 = re.sub(r'-\d+$', '', std2_upper)
        
        eq_base = self.get_equivalent_standards(base1)
        if base2 in [re.sub(r'-\d+$', '', e) for e in eq_base]:
            return True, 0.8
        
        return False, 0.0
    
    def get_standard_info(self, standard_code: str) -> Optional[StandardInfo]:
        """
        Get detailed information about a standard
        
        Args:
            standard_code: The standard code
            
        Returns:
            StandardInfo or None
        """
        code_upper = standard_code.upper().strip()
        
        # Direct lookup
        if code_upper in self.STANDARDS_DB:
            return self.STANDARDS_DB[code_upper]
        
        # Try without part number
        base_code = re.sub(r'-\d+$', '', code_upper)
        if base_code in self.STANDARDS_DB:
            return self.STANDARDS_DB[base_code]
        
        # Try with common prefixes normalized
        normalized = code_upper.replace('IS-', 'IS ').replace('IEC-', 'IEC ').replace('BS-', 'BS ')
        if normalized in self.STANDARDS_DB:
            return self.STANDARDS_DB[normalized]
        
        return None
    
    def find_standards_by_category(self, category: str) -> List[StandardInfo]:
        """Find all standards in a category"""
        category_lower = category.lower()
        results = []
        
        for std in self.STANDARDS_DB.values():
            if category_lower in std.category.lower():
                results.append(std)
        
        return results
    
    def parse_standard_from_text(self, text: str) -> List[str]:
        """
        Extract standard codes from text
        
        Args:
            text: Text containing standard references
            
        Returns:
            List of found standard codes
        """
        patterns = [
            r'IS[\s-]?\d{3,5}(?:-\d)?',
            r'IEC[\s-]?\d{4,5}(?:-\d)?',
            r'BS[\s-]?\d{4,5}',
            r'ASTM[\s-]?[A-Z]?\d{1,4}',
            r'IEEE[\s-]?\d{2,4}',
            r'DIN[\s-]?\d{4,5}',
        ]
        
        found = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.extend(matches)
        
        # Normalize
        return [m.upper().replace('-', ' ').strip() for m in found]


# Module-level mapper instance
_mapper = StandardMapper()


def get_equivalent_standards(standard_code: str) -> List[str]:
    """Get equivalent standards for a given code"""
    return _mapper.get_equivalent_standards(standard_code)


def map_standard_code(from_code: str, to_body: StandardBody) -> Optional[str]:
    """Map a standard to another standards body"""
    return _mapper.map_standard_code(from_code, to_body)


def is_standard_equivalent(standard1: str, standard2: str) -> Tuple[bool, float]:
    """Check if two standards are equivalent"""
    return _mapper.is_standard_equivalent(standard1, standard2)


def get_standard_info(standard_code: str) -> Optional[StandardInfo]:
    """Get information about a standard"""
    return _mapper.get_standard_info(standard_code)
