"""
OEM Product Datasheet Repository
Contains product specifications for OEM vendor products
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProductDatasheet:
    """Complete product datasheet for OEM products"""
    sku: str
    product_name: str
    manufacturer: str
    brand: str
    category: str
    sub_category: str
    
    # Technical Specifications
    specifications: Dict[str, Any] = field(default_factory=dict)
    
    # Compliance & Certifications
    standards_compliance: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    bis_license_number: str = ""
    
    # Physical Properties
    physical_properties: Dict[str, Any] = field(default_factory=dict)
    
    # Electrical Properties
    electrical_properties: Dict[str, Any] = field(default_factory=dict)
    
    # Test Data
    type_test_report: Dict[str, Any] = field(default_factory=dict)
    
    # Packaging & Delivery
    packaging_info: Dict[str, Any] = field(default_factory=dict)
    
    # Pricing Info
    price_per_unit: float = 0.0
    currency: str = "INR"
    moq: int = 1
    lead_time_days: int = 7
    
    # Metadata
    datasheet_url: str = ""
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class OEMProductRepository:
    """Repository for OEM product datasheets"""
    
    def __init__(self):
        self.products: Dict[str, ProductDatasheet] = {}
        self._load_default_products()
        logger.info(f"✅ OEM Repository loaded with {len(self.products)} products")
    
    def _load_default_products(self):
        """Load default OEM product datasheets"""
        
        # ================== POLYCAB PRODUCTS ==================
        self.add_product(ProductDatasheet(
            sku="POL-PVC-1.5-R",
            product_name="Polycab Optima Plus FR PVC Insulated Industrial Cable",
            manufacturer="Polycab India Limited",
            brand="Polycab Optima Plus",
            category="Wires & Cables",
            sub_category="PVC Insulated Wire",
            specifications={
                'conductor_material': 'Electrolytic Grade Copper',
                'conductor_type': 'Solid/Stranded',
                'insulation_material': 'FR PVC Type A',
                'cross_section_sqmm': 1.5,
                'number_of_strands': 7,
                'strand_diameter_mm': 0.52,
                'overall_diameter_mm': 2.9,
                'voltage_grade': '1100V',
                'current_rating_amp': 15,
                'standard': 'IS 694:2010',
                'temperature_rating_celsius': 70,
                'min_bending_radius_mm': 30,
                'color_options': ['Red', 'Yellow', 'Blue', 'Black', 'Green']
            },
            standards_compliance=['IS 694:2010', 'IEC 60227'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015', 'ISO 14001:2015'],
            bis_license_number='CM/L-1234567',
            electrical_properties={
                'conductor_resistance_ohm_per_km': 12.1,
                'insulation_resistance_mohm_km': 100,
                'voltage_test_kv': 3.5,
                'spark_test_voltage_kv': 6
            },
            physical_properties={
                'weight_kg_per_km': 25,
                'insulation_thickness_mm': 0.7,
                'tensile_strength_mpa': 12.5,
                'elongation_percent': 150
            },
            packaging_info={
                'coil_length_m': 90,
                'drum_length_m': [200, 500, 1000],
                'packaging_type': 'Shrink wrapped coil / Wooden drum'
            },
            price_per_unit=17.50,
            moq=100,
            lead_time_days=7
        ))
        
        self.add_product(ProductDatasheet(
            sku="POL-PVC-2.5-R",
            product_name="Polycab Optima Plus FR PVC Insulated Industrial Cable 2.5 sq mm",
            manufacturer="Polycab India Limited",
            brand="Polycab Optima Plus",
            category="Wires & Cables",
            sub_category="PVC Insulated Wire",
            specifications={
                'conductor_material': 'Electrolytic Grade Copper',
                'conductor_type': 'Stranded',
                'insulation_material': 'FR PVC Type A',
                'cross_section_sqmm': 2.5,
                'number_of_strands': 7,
                'strand_diameter_mm': 0.67,
                'overall_diameter_mm': 3.4,
                'voltage_grade': '1100V',
                'current_rating_amp': 21,
                'standard': 'IS 694:2010',
                'temperature_rating_celsius': 70,
                'color_options': ['Red', 'Yellow', 'Blue', 'Black']
            },
            standards_compliance=['IS 694:2010', 'IEC 60227'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015', 'ISO 14001:2015'],
            electrical_properties={
                'conductor_resistance_ohm_per_km': 7.41,
                'insulation_resistance_mohm_km': 100,
                'voltage_test_kv': 3.5
            },
            physical_properties={
                'weight_kg_per_km': 38,
                'insulation_thickness_mm': 0.8
            },
            price_per_unit=28.50,
            moq=100,
            lead_time_days=7
        ))
        
        self.add_product(ProductDatasheet(
            sku="POL-XLPE-4C16",
            product_name="Polycab XLPE Insulated Armoured Power Cable 4Cx16 sq mm",
            manufacturer="Polycab India Limited",
            brand="Polycab",
            category="Wires & Cables",
            sub_category="XLPE Power Cable",
            specifications={
                'conductor_material': 'Stranded Annealed Copper',
                'conductor_type': 'Class 2 Stranded',
                'insulation_material': 'XLPE (Cross-linked Polyethylene)',
                'number_of_cores': 4,
                'cross_section_sqmm': 16,
                'voltage_grade': '1.1 kV',
                'armour_type': 'Galvanized Steel Wire Armour (SWA)',
                'outer_sheath': 'PVC ST2 Type',
                'standard': 'IS 7098 Part 1',
                'temperature_rating_celsius': 90,
                'short_circuit_temp_celsius': 250,
                'current_rating_amp': 85
            },
            standards_compliance=['IS 7098 Part 1', 'IEC 60502-1'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015'],
            electrical_properties={
                'conductor_resistance_ohm_per_km': 1.15,
                'insulation_resistance_mohm_km': 200,
                'voltage_test_kv': 4,
                'impulse_withstand_kv': 20
            },
            physical_properties={
                'overall_diameter_mm': 32,
                'weight_kg_per_km': 1250,
                'min_bending_radius_mm': 384
            },
            packaging_info={
                'drum_length_m': [100, 250, 500],
                'packaging_type': 'Wooden/Steel drum'
            },
            price_per_unit=485.00,
            moq=100,
            lead_time_days=14
        ))
        
        # ================== HAVELLS PRODUCTS ==================
        self.add_product(ProductDatasheet(
            sku="HAV-LIFELINE-1.5",
            product_name="Havells Lifeline Plus S3 HRFR Cable 1.5 sq mm",
            manufacturer="Havells India Limited",
            brand="Havells Lifeline Plus",
            category="Wires & Cables",
            sub_category="PVC Insulated Wire",
            specifications={
                'conductor_material': 'Electrolytic Grade Copper',
                'conductor_type': 'Solid/Stranded',
                'insulation_material': 'HRFR (Heat Resistant Flame Retardant) PVC',
                'cross_section_sqmm': 1.5,
                'number_of_strands': 7,
                'overall_diameter_mm': 2.9,
                'voltage_grade': '1100V',
                'current_rating_amp': 16,
                'standard': 'IS 694:2010',
                'temperature_rating_celsius': 85,
                'flame_retardant': True,
                'halogen_free': False,
                'color_options': ['Red', 'Yellow', 'Blue', 'Black', 'Green', 'White']
            },
            standards_compliance=['IS 694:2010', 'IEC 60227', 'IEC 60332-1'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015', 'ISO 14001:2015', 'RoHS Compliant'],
            electrical_properties={
                'conductor_resistance_ohm_per_km': 12.1,
                'insulation_resistance_mohm_km': 100,
                'voltage_test_kv': 3.5
            },
            physical_properties={
                'weight_kg_per_km': 26,
                'insulation_thickness_mm': 0.7,
                'oxygen_index_percent': 29
            },
            price_per_unit=21.00,
            moq=100,
            lead_time_days=10
        ))
        
        self.add_product(ProductDatasheet(
            sku="HAV-LIFELINE-2.5",
            product_name="Havells Lifeline Plus S3 HRFR Cable 2.5 sq mm",
            manufacturer="Havells India Limited",
            brand="Havells Lifeline Plus",
            category="Wires & Cables",
            sub_category="PVC Insulated Wire",
            specifications={
                'conductor_material': 'Electrolytic Grade Copper',
                'conductor_type': 'Stranded',
                'insulation_material': 'HRFR PVC',
                'cross_section_sqmm': 2.5,
                'number_of_strands': 7,
                'overall_diameter_mm': 3.5,
                'voltage_grade': '1100V',
                'current_rating_amp': 22,
                'standard': 'IS 694:2010',
                'temperature_rating_celsius': 85,
                'flame_retardant': True
            },
            standards_compliance=['IS 694:2010', 'IEC 60332-1'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015', 'RoHS Compliant'],
            electrical_properties={
                'conductor_resistance_ohm_per_km': 7.41,
                'insulation_resistance_mohm_km': 100
            },
            price_per_unit=32.00,
            moq=100,
            lead_time_days=10
        ))
        
        # ================== KEI PRODUCTS ==================
        self.add_product(ProductDatasheet(
            sku="KEI-HOMECAB-1.5",
            product_name="KEI Homecab FR-LSH PVC Insulated Wire 1.5 sq mm",
            manufacturer="KEI Industries Limited",
            brand="KEI Homecab",
            category="Wires & Cables",
            sub_category="PVC Insulated Wire",
            specifications={
                'conductor_material': 'Electrolytic Grade Copper',
                'conductor_type': 'Solid/Stranded',
                'insulation_material': 'FR-LSH PVC',
                'cross_section_sqmm': 1.5,
                'number_of_strands': 7,
                'voltage_grade': '1100V',
                'current_rating_amp': 15,
                'standard': 'IS 694:2010',
                'temperature_rating_celsius': 70,
                'low_smoke': True,
                'halogen_free': True
            },
            standards_compliance=['IS 694:2010'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015'],
            electrical_properties={
                'conductor_resistance_ohm_per_km': 12.1,
                'insulation_resistance_mohm_km': 100
            },
            price_per_unit=16.00,
            moq=100,
            lead_time_days=7
        ))
        
        # ================== FINOLEX PRODUCTS ==================
        self.add_product(ProductDatasheet(
            sku="FIN-FR-1.5",
            product_name="Finolex FR PVC Insulated Industrial Cable 1.5 sq mm",
            manufacturer="Finolex Cables Limited",
            brand="Finolex",
            category="Wires & Cables",
            sub_category="PVC Insulated Wire",
            specifications={
                'conductor_material': 'Electrolytic Grade Copper',
                'conductor_type': 'Solid',
                'insulation_material': 'FR PVC',
                'cross_section_sqmm': 1.5,
                'voltage_grade': '1100V',
                'current_rating_amp': 15,
                'standard': 'IS 694:2010',
                'temperature_rating_celsius': 70,
                'flame_retardant': True
            },
            standards_compliance=['IS 694:2010', 'IEC 60332-1'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015', 'ISO 14001:2015'],
            electrical_properties={
                'conductor_resistance_ohm_per_km': 12.1,
                'insulation_resistance_mohm_km': 100
            },
            price_per_unit=18.50,
            moq=100,
            lead_time_days=7
        ))
        
        # ================== FLEXIBLE CABLES ==================
        self.add_product(ProductDatasheet(
            sku="POL-FLEX-3C2.5",
            product_name="Polycab Flexible Cable 3 Core x 2.5 sq mm",
            manufacturer="Polycab India Limited",
            brand="Polycab",
            category="Wires & Cables",
            sub_category="Flexible Cable",
            specifications={
                'conductor_material': 'Tinned Annealed Copper',
                'conductor_type': 'Class 5 Flexible',
                'insulation_material': 'PVC',
                'number_of_cores': 3,
                'cross_section_sqmm': 2.5,
                'voltage_grade': '1100V',
                'current_rating_amp': 18,
                'standard': 'IS 694',
                'temperature_rating_celsius': 70,
                'flexibility_class': 'Class 5'
            },
            standards_compliance=['IS 694'],
            certifications=['BIS (ISI Mark)', 'ISO 9001:2015'],
            electrical_properties={
                'conductor_resistance_ohm_per_km': 7.98
            },
            price_per_unit=95.00,
            moq=50,
            lead_time_days=7
        ))
    
    def add_product(self, product: ProductDatasheet):
        """Add a product to the repository"""
        self.products[product.sku] = product
    
    def get_product(self, sku: str) -> Optional[ProductDatasheet]:
        """Get product by SKU"""
        return self.products.get(sku)
    
    def search_products(self, query: str) -> List[ProductDatasheet]:
        """Search products by name or specifications"""
        query_lower = query.lower()
        results = []
        
        for product in self.products.values():
            if (query_lower in product.product_name.lower() or
                query_lower in product.category.lower() or
                query_lower in product.sub_category.lower() or
                query_lower in product.manufacturer.lower()):
                results.append(product)
        
        return results
    
    def get_products_by_category(self, category: str) -> List[ProductDatasheet]:
        """Get all products in a category"""
        return [p for p in self.products.values() if p.category.lower() == category.lower()]
    
    def get_products_by_manufacturer(self, manufacturer: str) -> List[ProductDatasheet]:
        """Get all products from a manufacturer"""
        return [p for p in self.products.values() if manufacturer.lower() in p.manufacturer.lower()]
    
    def export_to_json(self, filepath: str = None) -> str:
        """Export repository to JSON"""
        data = {sku: asdict(product) for sku, product in self.products.items()}
        json_str = json.dumps(data, indent=2, default=str)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def load_from_json(self, filepath: str):
        """Load products from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for sku, product_data in data.items():
            self.products[sku] = ProductDatasheet(**product_data)


# Singleton instance
_repository_instance = None

def get_oem_repository() -> OEMProductRepository:
    """Get singleton instance of OEM repository"""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = OEMProductRepository()
    return _repository_instance


# Example usage
if __name__ == "__main__":
    repo = get_oem_repository()
    
    print(f"Total products: {len(repo.products)}")
    print("\nProducts by category:")
    for product in repo.get_products_by_category("Wires & Cables"):
        print(f"  - {product.sku}: {product.product_name}")
