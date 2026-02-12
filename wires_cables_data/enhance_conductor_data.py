"""
Enhance conductor material data across CSVs and JSONs
1. Add Conductor_Material_Grade column with detailed copper/aluminium types
2. Fix Moglix company entries (extract real manufacturer from product name)
3. Update JSON files with enhanced specifications
"""

import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime

# ============================================================================
# Conductor Material Grade Mapping
# ============================================================================

CONDUCTOR_GRADE_MAP = {
    # Copper grades
    'Copper': 'Electrolytic Grade Copper (ETP)',
    'Annealed Copper': 'Electrolytic Grade Annealed Copper',
    'Pure Copper': '99.97% Pure Electrolytic Copper',
    'OFC Copper': 'Oxygen Free Copper (OFC)',
    'Tinned Copper': 'Tin Plated Electrolytic Copper',
    
    # Aluminium grades
    'Aluminium': 'EC Grade Aluminium',
    'Aluminum': 'EC Grade Aluminium',
    'EC Aluminium': 'EC Grade Aluminium (99.5% Purity)',
    
    # CCS (Copper Clad Steel)
    'CCS': 'Copper Clad Steel (CCS)',
}

# Known manufacturers to extract from product names when Company is "Moglix"
KNOWN_MANUFACTURERS = [
    'Polycab', 'Havells', 'KEI', 'Finolex', 'RR Kabel', 'TWC',
    'Kalinga Plus', 'Kalinga', 'CabONE', 'FAB', 'Damor', 'R.K', 'RK',
    'Shivpriya', 'Finoflex', 'V-Guard', 'Anchor', 'L&T', 'Bajaj',
    'Crompton', 'Syska', 'Orient', 'Plaza', 'GM', 'Legrand'
]

def extract_manufacturer(product_name: str, company: str) -> str:
    """Extract real manufacturer from product name if company is Moglix"""
    if company.lower() != 'moglix':
        return company
    
    product_name_lower = product_name.lower()
    
    for mfr in KNOWN_MANUFACTURERS:
        # Check if manufacturer name is at the start of product name
        if product_name_lower.startswith(mfr.lower()):
            return mfr
        # Check if manufacturer name is in product name with space/delimiter
        patterns = [
            rf'^{re.escape(mfr)}\s',  # At start with space
            rf'\s{re.escape(mfr)}\s',  # In middle with spaces
        ]
        for pattern in patterns:
            if re.search(pattern, product_name, re.IGNORECASE):
                return mfr
    
    # If no known manufacturer found, return "Other" instead of Moglix
    return "Other (Moglix Listed)"

def get_conductor_grade(material: str, product_name: str = "") -> str:
    """Get detailed conductor grade from material type"""
    if pd.isna(material) or not material:
        return "Unknown"
    
    material_upper = str(material).strip()
    material_lower = material_upper.lower()
    
    # Check for CCS in product name
    if 'ccs' in product_name.lower():
        return 'Copper Clad Steel (CCS)'
    
    # Direct mapping
    if material_upper in CONDUCTOR_GRADE_MAP:
        return CONDUCTOR_GRADE_MAP[material_upper]
    
    # Keyword-based mapping
    if 'annealed' in material_lower:
        return 'Electrolytic Grade Annealed Copper'
    elif 'tinned' in material_lower or 'tin plated' in material_lower:
        return 'Tin Plated Electrolytic Copper'
    elif 'ofc' in material_lower or 'oxygen free' in material_lower:
        return 'Oxygen Free Copper (OFC)'
    elif 'pure' in material_lower and 'copper' in material_lower:
        return '99.97% Pure Electrolytic Copper'
    elif 'copper' in material_lower:
        return 'Electrolytic Grade Copper (ETP)'
    elif 'aluminium' in material_lower or 'aluminum' in material_lower:
        return 'EC Grade Aluminium'
    elif 'pvc' in material_lower:
        # Some entries incorrectly have PVC as conductor material
        return 'Electrolytic Grade Copper (ETP)'  # Default assumption
    
    return material_upper

def process_csv(csv_path: Path) -> pd.DataFrame:
    """Process a single CSV file"""
    print(f"Processing: {csv_path.name}")
    df = pd.read_csv(csv_path)
    
    # Add Conductor_Material_Grade column
    df['Conductor_Material_Grade'] = df.apply(
        lambda row: get_conductor_grade(
            row.get('Conductor_Material', ''),
            row.get('Product_Name', '')
        ),
        axis=1
    )
    
    # Fix Moglix company entries
    if 'Company' in df.columns:
        original_moglix_count = (df['Company'].str.lower() == 'moglix').sum()
        df['Company'] = df.apply(
            lambda row: extract_manufacturer(
                row.get('Product_Name', ''),
                row.get('Company', '')
            ),
            axis=1
        )
        new_moglix_count = (df['Company'].str.lower() == 'moglix').sum()
        print(f"  - Fixed {original_moglix_count - new_moglix_count} Moglix entries")
    
    # Count grade distribution
    grade_counts = df['Conductor_Material_Grade'].value_counts()
    print(f"  - Conductor grades: {dict(grade_counts.head(5))}")
    
    return df

def update_oem_products_json(json_path: Path):
    """Update OEM products JSON with enhanced conductor details"""
    print(f"\nUpdating: {json_path.name}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for product in data.get('products', []):
        specs = product.get('specifications', {})
        conductor = specs.get('conductor_material', '')
        
        # Add conductor_material_grade
        if conductor:
            specs['conductor_material_grade'] = get_conductor_grade(conductor, product.get('name', ''))
        
        # Add conductor purity percentage
        if 'copper' in conductor.lower():
            specs['conductor_purity_percent'] = 99.97
            specs['conductor_standard'] = 'IS 8130 / IEC 60228'
        elif 'aluminium' in conductor.lower():
            specs['conductor_purity_percent'] = 99.5
            specs['conductor_standard'] = 'IS 8130 / IEC 60228'
    
    # Update metadata
    data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    data['metadata']['conductor_grades_added'] = True
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"  - Updated {len(data.get('products', []))} products")

def update_oem_datasheets_json(json_path: Path):
    """Update OEM datasheets JSON with enhanced conductor details"""
    print(f"\nUpdating: {json_path.name}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for datasheet in data.get('datasheets', []):
        physical = datasheet.get('physical_properties', {})
        conductor = physical.get('conductor_material', '')
        
        if conductor:
            # Add detailed conductor info
            physical['conductor_material_grade'] = get_conductor_grade(conductor, datasheet.get('product_name', ''))
            
            if 'copper' in conductor.lower():
                physical['conductor_purity'] = '99.97% minimum'
                physical['conductor_conductivity'] = '100% IACS minimum'
                physical['conductor_resistivity'] = '17.241 nΩ·m at 20°C'
            elif 'aluminium' in conductor.lower():
                physical['conductor_purity'] = '99.5% minimum (EC Grade)'
                physical['conductor_conductivity'] = '61% IACS minimum'
                physical['conductor_resistivity'] = '28.264 nΩ·m at 20°C'
    
    # Update metadata
    data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    data['metadata']['enhanced_conductor_specs'] = True
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"  - Updated {len(data.get('datasheets', []))} datasheets")

def main():
    print("=" * 70)
    print("Enhancing Conductor Material Data")
    print("=" * 70)
    
    base_path = Path(__file__).parent
    
    # Process CSVs
    csv_dir = base_path / 'wires_cables_data'
    csv_files = list(csv_dir.glob('moglix_*.csv'))
    
    print(f"\nFound {len(csv_files)} CSV files to process")
    
    for csv_file in csv_files:
        if '_optimized_' not in csv_file.name:  # Skip already optimized files
            df = process_csv(csv_file)
            
            # Save enhanced CSV
            output_name = csv_file.stem + '_enhanced.csv'
            output_path = csv_dir / output_name
            df.to_csv(output_path, index=False)
            print(f"  - Saved: {output_name}")
    
    # Update JSON files
    db_path = base_path.parent / 'database' / 'db_products'
    
    oem_products_path = db_path / 'oem_products.json'
    if oem_products_path.exists():
        update_oem_products_json(oem_products_path)
    
    oem_datasheets_path = db_path / 'oem_datasheets.json'
    if oem_datasheets_path.exists():
        update_oem_datasheets_json(oem_datasheets_path)
    
    print("\n" + "=" * 70)
    print("Enhancement Complete!")
    print("=" * 70)
    
    # Print summary of conductor grades
    print("\nConductor Material Grade Hierarchy:")
    print("-" * 40)
    print("COPPER:")
    print("  ├─ Electrolytic Grade Copper (ETP)")
    print("  │   └─ 99.97% Pure Electrolytic Copper")
    print("  ├─ Electrolytic Grade Annealed Copper")
    print("  ├─ Oxygen Free Copper (OFC)")
    print("  ├─ Tin Plated Electrolytic Copper")
    print("  └─ Copper Clad Steel (CCS)")
    print("\nALUMINIUM:")
    print("  └─ EC Grade Aluminium (99.5% Purity)")

if __name__ == '__main__':
    main()
