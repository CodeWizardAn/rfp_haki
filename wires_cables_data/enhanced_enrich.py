#!/usr/bin/env python3
"""
Enhanced data enrichment with online source lookup for Is_Flexible
"""

import os
import pandas as pd
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
import re

OEM_PATHS = {
    'POLYCAB': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/polycab',
    'HAVELLS': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/havells',
    'RR_KABEL': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/rr_kabel',
    'KEI': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/kei',
    'FINOLEX': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/finolex'
}

# OEM-specific flexible indicators from their product portfolios
OEM_FLEXIBLE_PRODUCTS = {
    'POLYCAB': [
        'house wire', 'pvc wire', 'stranded', 'flexible', 'twin', 'three core',
        'submersible wire', 'pvc sheathed', 'copper core', 'residential wire'
    ],
    'HAVELLS': [
        'house wire', 'flexible wire', 'stranded', 'pvc', 'twin', 'three core',
        'residential cable', 'copper wire', 'submersible'
    ],
    'RR_KABEL': [
        'house wire', 'pvc wire', 'flexible cable', 'stranded', 'residential',
        'copper core', 'submersible wire', 'twin', 'single core pvc'
    ],
    'KEI': [
        'house wire', 'flexible', 'pvc sheathed', 'stranded conductor',
        'residential wire', 'copper core', 'twin cable', 'single core'
    ],
    'FINOLEX': [
        'house wire', 'pvc wire', 'flexible cable', 'stranded', 'submersible',
        'copper core', 'residential', 'twin', 'three core', 'fr house wire'
    ]
}

class EnhancedFlexibleDetector:
    """Detect flexible cables using name analysis + online search"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_name_for_flexible(self, product_name, category, oem):
        """First check product name and category"""
        text = f"{product_name} {category}".lower()
        
        # Basic flexible indicators
        basic_flexible = [
            'flexible', 'house wire', 'pvc wire', 'stranded',
            'submersible wire', 'pvc sheathed', 'copper core single',
            'residential wire', 'twin', 'three core', 'multi-core wire'
        ]
        
        for indicator in basic_flexible:
            if indicator in text:
                return 1, 'name_match'
        
        # OEM-specific indicators
        if oem in OEM_FLEXIBLE_PRODUCTS:
            for indicator in OEM_FLEXIBLE_PRODUCTS[oem]:
                if indicator in text:
                    return 1, f'oem_{oem}_match'
        
        return 0, 'not_found_in_name'
    
    def search_online(self, product_name, product_code, oem):
        """Search online for product specifications"""
        try:
            # Try multiple search strategies
            queries = [
                f"{oem} {product_code} flexible specifications",
                f"{product_name} flexible cable",
                f"{product_code} wire specifications"
            ]
            
            for query in queries:
                try:
                    # Search using DuckDuckGo-like query (works without API key)
                    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    
                    response = self.session.get(search_url, timeout=3)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        text = soup.get_text().lower()
                        
                        # Check for flexible indicators in search results
                        flexible_indicators = [
                            'flexible', 'stranded', 'house wire', 'residential',
                            'copper core single', 'submersible', 'pvc sheathed'
                        ]
                        
                        for indicator in flexible_indicators:
                            if indicator in text:
                                return 1, f'online_search_{indicator}'
                    
                    time.sleep(0.5)  # Rate limiting
                except:
                    pass
            
            return 0, 'not_found_online'
        
        except Exception as e:
            return 0, f'error_online_search'
    
    def determine_flexible(self, row, oem):
        """Comprehensive flexible detection"""
        product_name = str(row.get('Product_Name', '')).lower()
        category = str(row.get('Category', '')).lower()
        product_code = str(row.get('Product_Code', ''))
        
        # Step 1: Check name first (fast)
        is_flexible, source = self.check_name_for_flexible(product_name, category, oem)
        
        if is_flexible == 1:
            return 1, source
        
        # Step 2: Check if it's likely NOT flexible (armoured, control, power cables)
        non_flexible_indicators = [
            'armoured', 'control cable', 'power cable-ht', 'power cable-lt',
            'instrumentation', 'submersible cable power', 'xlpe', 'epr'
        ]
        
        combined_text = f"{product_name} {category}"
        for indicator in non_flexible_indicators:
            if indicator in combined_text.lower():
                return 0, f'identified_as_{indicator}'
        
        # Step 3: Online search for uncertain cases
        # (Only search if we have connectivity, skip if it fails silently)
        try:
            is_flexible, source = self.search_online(product_name, product_code, oem)
            if is_flexible == 1:
                return 1, source
        except:
            pass
        
        # Step 4: Smart fallback heuristic
        # If it's a single/twin core wire product, likely flexible
        if 'wire' in category.lower() and 'multi' not in category.lower():
            if 'core' in combined_text:
                return 1, 'heuristic_single_core'
        
        return 0, 'defaulted_to_0'
    
    def determine_armoured(self, row):
        """Determine armoured status"""
        armour = str(row.get('Armour_Type', '')).lower()
        if 'armour' in armour or 'swa' in armour:
            return 1
        return 0
    
    def determine_industrial(self, row):
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
    
    def calculate_real_price(self, row):
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
    
    def enrich_csv_file(self, file_path, oem):
        """Read CSV and fill columns with enhanced data"""
        try:
            df = pd.read_csv(file_path)
            
            # Fill Is_Armoured
            df['Is_Armoured'] = df.apply(self.determine_armoured, axis=1)
            
            # Fill Is_Industrial
            df['Is_Industrial'] = df.apply(self.determine_industrial, axis=1)
            
            # Fill Is_Flexible with enhanced detection
            flexible_results = []
            for idx, row in df.iterrows():
                is_flex, source = self.determine_flexible(row, oem)
                flexible_results.append(is_flex)
            
            df['Is_Flexible'] = flexible_results
            
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
                result = self.enrich_csv_file(str(csv_file), oem)
                result['oem'] = oem
                results.append(result)
        
        return results

if __name__ == '__main__':
    print("=" * 80)
    print("ENHANCED DATA ENRICHMENT - Name + Online Search for Flexible Detection")
    print("=" * 80)
    
    detector = EnhancedFlexibleDetector()
    results = detector.enrich_all()
    
    total_files = 0
    total_products = 0
    total_flexible = 0
    
    for result in results:
        if result['success']:
            total_files += 1
            total_products += result['products']
            total_flexible += result['flexible']
            
            print(f"\n✓ {result['oem']} - {result['file']}")
            print(f"    Products: {result['products']}")
            print(f"    Armoured: {result['armoured']}")
            print(f"    Industrial: {result['industrial']}")
            print(f"    Flexible: {result['flexible']} ({result['flexible']/result['products']*100:.1f}%)")
            print(f"    Price: Rs {result['price_range'][0]:.2f} - Rs {result['price_range'][1]:.2f}/meter")
            print(f"    Avg: Rs {result['avg_price']:.2f}/meter")
        else:
            print(f"\n✗ {result['oem']} - {result['file']}")
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nFiles processed: {total_files}")
    print(f"Total products: {total_products}")
    print(f"Total flexible: {total_flexible} ({total_flexible/total_products*100:.1f}%)")
    print(f"\n✓ Enhanced detection methods used:")
    print(f"  1. Product name & category analysis")
    print(f"  2. OEM-specific flexible indicators")
    print(f"  3. Online search for specifications (when offline detection inconclusive)")
    print(f"  4. Smart heuristics for edge cases")
