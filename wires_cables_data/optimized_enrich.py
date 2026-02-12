#!/usr/bin/env python3
"""
Optimized enhanced data enrichment with intelligent flexible detection.
Uses product name analysis + OEM product portfolio knowledge (no online search).
"""

import os
import pandas as pd
from pathlib import Path

OEM_PATHS = {
    'POLYCAB': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/polycab',
    'HAVELLS': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/havells',
    'RR_KABEL': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/rr_kabel',
    'KEI': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/kei',
    'FINOLEX': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/finolex'
}

# Flexible cable indicators (from manufacturer datasheets)
FLEXIBLE_INDICATORS = [
    'house wire', 'pvc wire', 'stranded', 'flexible', 'twin', 'three core wire',
    'submersible wire', 'pvc sheathed', 'copper core wire', 'residential wire',
    'fr-lsh', 'lsh', 'single core pvc', 'multi-core wire', 'flex', 'twin wire',
    'pvc single core', 'copper stranded', 'pvc multi', 'residential cable'
]

# Non-flexible indicators (control/power cables)
NON_FLEXIBLE_INDICATORS = [
    'armoured cable', 'control cable', 'power cable-ht', 'power cable-lt',
    'instrumentation', 'submersible cable power', 'xlpe cable', 'epr cable',
    'swa cable', 'armour', 'underground', 'lv power', 'hv cable',
    'multi-strand armoured', 'industrial cable', 'signal cable'
]

class OptimizedFlexibleDetector:
    """Smart flexible detection using name analysis + product portfolio knowledge"""
    
    @staticmethod
    def check_name_and_specs(product_name, category, insulation_type, no_of_cores, conductor_class):
        """Comprehensive flexible detection from available columns"""
        
        text = f"{product_name} {category}".lower()
        insulation = str(insulation_type).lower() if insulation_type else ''
        cores = int(no_of_cores) if no_of_cores else 0
        cond_class = str(conductor_class).lower() if conductor_class else ''
        
        # Rule 1: Check non-flexible indicators first
        for indicator in NON_FLEXIBLE_INDICATORS:
            if indicator in text:
                return 0  # Definitely not flexible
        
        # Rule 2: Check flexible indicators
        for indicator in FLEXIBLE_INDICATORS:
            if indicator in text:
                return 1  # Definitely flexible
        
        # Rule 3: Product type heuristics
        if 'wire' in category.lower():
            # Single/twin core wires are typically flexible
            if cores in [1, 2, 3]:
                # Check if it has flexible insulation
                if 'pvc' in insulation or 'lsh' in insulation or 'frls' in insulation:
                    if 'single' in text or 'twin' in text or 'multi' in text or 'core' in text:
                        return 1
        
        # Rule 4: Conductor class indicates flexibility
        # Class 1 = solid conductor (not flexible), Class 5-6 = stranded (flexible)
        if cond_class:
            if 'class 5' in cond_class or 'class 6' in cond_class:
                return 1
            elif 'class 1' in cond_class:
                return 0
        
        # Rule 5: Single core, low voltage wires are flexible
        if cores == 1 and 'voltage' in category.lower():
            voltage = extract_voltage(product_name + ' ' + category)
            if voltage and voltage < 1000:  # < 1000V = low voltage = flexible
                if insulation and insulation != 'unknown':
                    return 1
        
        # Rule 6: If it's twin or three core, it's flexible (unless armoured)
        if 'twin' in text or 'three core' in text:
            if 'armour' not in text:
                return 1
        
        # Rule 7: Submersible wires are flexible unless marked otherwise
        if 'submersible wire' in text:
            return 1
        
        # Default: If unsure, check if it has flexible characteristics
        if cores and cores <= 3 and 'cable' not in category.lower():
            # Small core count + not a cable = flexible wire
            return 1
        
        return 0
    
    @staticmethod
    def determine_armoured(row):
        """Determine armoured status"""
        armour = str(row.get('Armour_Type', '')).lower()
        if 'armour' in armour or 'swa' in armour:
            return 1
        return 0
    
    @staticmethod
    def determine_industrial(row):
        """Determine industrial status"""
        category = str(row.get('Category', '')).lower()
        product_name = str(row.get('Product_Name', '')).lower()
        
        industrial_keywords = [
            'control cable', 'industrial cable', 'armoured', 'submersible',
            'power cable-ht', 'flexible industrial', 'instrumentation'
        ]
        
        for keyword in industrial_keywords:
            if keyword in category or keyword in product_name:
                return 1
        
        return 0
    
    @staticmethod
    def calculate_real_price(row):
        """Calculate realistic price based on specs"""
        try:
            copper_rate = 650
            conductor_material = str(row.get('Conductor_Material', '')).lower()
            
            material_mult = 1.0
            if 'aluminium' in conductor_material:
                material_mult = 0.4
            elif 'copper' in conductor_material:
                material_mult = 1.0
            
            size = float(row.get('Conductor_Size_sqmm', 1))
            cores = int(row.get('No_of_Cores', 1))
            weight = float(row.get('Approx_Weight_kg_per_km', 10))
            
            insulation = str(row.get('Insulation_Type', '')).lower()
            insulation_mult = 1.0
            if 'frls' in insulation or 'fr-lsh' in insulation:
                insulation_mult = 1.5
            elif 'pvc' in insulation:
                insulation_mult = 1.0
            elif 'xlpe' in insulation or 'epr' in insulation:
                insulation_mult = 1.3
            
            armour = str(row.get('Armour_Type', '')).lower()
            armour_mult = 1.0
            if 'armoured' in armour or 'swa' in armour:
                armour_mult = 1.6
            
            weight_per_meter = weight / 1000
            conductor_cost = (weight_per_meter * material_mult * copper_rate) / cores if cores > 0 else 0
            total_price = conductor_cost * insulation_mult * armour_mult
            total_price = total_price * 1.25
            
            return round(max(total_price, 2.0), 2)
        
        except Exception as e:
            try:
                return float(row.get('Price_Per_Meter_INR', 10.0))
            except:
                return 10.0
    
    def enrich_csv_file(self, file_path):
        """Read CSV and fill columns with enhanced data"""
        try:
            df = pd.read_csv(file_path)
            
            # Fill Is_Armoured
            df['Is_Armoured'] = df.apply(self.determine_armoured, axis=1)
            
            # Fill Is_Industrial
            df['Is_Industrial'] = df.apply(self.determine_industrial, axis=1)
            
            # Fill Is_Flexible with enhanced detection
            df['Is_Flexible'] = df.apply(
                lambda row: self.check_name_and_specs(
                    row.get('Product_Name', ''),
                    row.get('Category', ''),
                    row.get('Insulation_Type', ''),
                    row.get('No_of_Cores', 0),
                    row.get('Conductor_Class', '')
                ),
                axis=1
            )
            
            # Calculate realistic pricing
            df['Calculated_Price_Per_Meter'] = df.apply(self.calculate_real_price, axis=1)
            
            # Save
            df.to_csv(file_path, index=False)
            
            return {
                'success': True,
                'file': Path(file_path).name,
                'products': len(df),
                'armoured': (df['Is_Armoured'] == 1).sum(),
                'industrial': (df['Is_Industrial'] == 1).sum(),
                'flexible': (df['Is_Flexible'] == 1).sum(),
                'price_range': (df['Calculated_Price_Per_Meter'].min(), df['Calculated_Price_Per_Meter'].max()),
                'avg_price': df['Calculated_Price_Per_Meter'].mean()
            }
        except Exception as e:
            return {
                'success': False,
                'file': Path(file_path).name,
                'error': str(e)
            }
    
    def enrich_all(self):
        """Process all 15 CSV files"""
        results = []
        
        for oem, path in OEM_PATHS.items():
            if not os.path.exists(path):
                continue
            
            csv_files = sorted(Path(path).glob('*.csv'))
            
            for csv_file in csv_files:
                result = self.enrich_csv_file(str(csv_file))
                result['oem'] = oem
                results.append(result)
        
        return results

def extract_voltage(text):
    """Extract voltage value from text"""
    import re
    match = re.search(r'(\d+)\s*[vV]', text)
    if match:
        return int(match.group(1))
    return None

if __name__ == '__main__':
    print("=" * 80)
    print("OPTIMIZED DATA ENRICHMENT - Enhanced Flexible Detection")
    print("=" * 80)
    
    detector = OptimizedFlexibleDetector()
    results = detector.enrich_all()
    
    total_files = 0
    total_products = 0
    total_flexible = 0
    total_armoured = 0
    total_industrial = 0
    
    for result in results:
        if result['success']:
            total_files += 1
            total_products += result['products']
            total_flexible += result['flexible']
            total_armoured += result['armoured']
            total_industrial += result['industrial']
            
            print(f"\n✓ {result['oem']} - {result['file']}")
            print(f"    Products: {result['products']}")
            print(f"    Armoured: {result['armoured']} ({result['armoured']/result['products']*100:.1f}%)")
            print(f"    Industrial: {result['industrial']} ({result['industrial']/result['products']*100:.1f}%)")
            print(f"    Flexible: {result['flexible']} ({result['flexible']/result['products']*100:.1f}%)")
            print(f"    Price: Rs {result['price_range'][0]:.2f} - Rs {result['price_range'][1]:.2f}/meter")
            print(f"    Avg Price: Rs {result['avg_price']:.2f}/meter")
        else:
            print(f"\n✗ {result['oem']} - {result['file']}")
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nFiles processed: {total_files}")
    print(f"Total products: {total_products}")
    print(f"Total armoured: {total_armoured} ({total_armoured/total_products*100:.1f}%)")
    print(f"Total industrial: {total_industrial} ({total_industrial/total_products*100:.1f}%)")
    print(f"Total flexible: {total_flexible} ({total_flexible/total_products*100:.1f}%)")
    print(f"\n✓ Detection logic used:")
    print(f"  1. Product name & category analysis")
    print(f"  2. Non-flexible indicator filtering (armoured, control, power cables)")
    print(f"  3. Flexible indicator matching (house wire, twin, stranded, etc.)")
    print(f"  4. Core count heuristics (1-3 cores = typically flexible)")
    print(f"  5. Conductor class analysis (Class 5-6 = stranded = flexible)")
    print(f"  6. Voltage-based detection (low voltage wires = flexible)")
    print(f"  7. Product type classification (wires vs cables)")
