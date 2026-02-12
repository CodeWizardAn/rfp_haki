#!/usr/bin/env python3
"""
Add 7 more columns with intelligent extracted data from product specifications.
"""

import os
import pandas as pd
from pathlib import Path
import re

OEM_PATHS = {
    'POLYCAB': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/polycab',
    'HAVELLS': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/havells',
    'RR_KABEL': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/rr_kabel',
    'KEI': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/kei',
    'FINOLEX': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/finolex'
}

# Current carrying capacity formula: I = A * D * Delta_T
# Where A = current density (5-8 A/mm² for copper), D = conductor area, Delta_T = temperature rise
COPPER_CURRENT_DENSITY = 6  # A/mm² for general purpose
ALUMINIUM_CURRENT_DENSITY = 4  # A/mm² for aluminium

class AdditionalEnricher:
    """Add 7 more columns with extracted data"""
    
    @staticmethod
    def extract_voltage_level(voltage_rating):
        """Classify voltage level"""
        try:
            text = str(voltage_rating).lower()
            
            # Extract numeric voltage
            match = re.search(r'(\d+)', text)
            if match:
                voltage = int(match.group(1))
                
                if voltage <= 50:
                    return 'ELV'  # Extra Low Voltage
                elif voltage <= 1000:
                    return 'LV'  # Low Voltage
                elif voltage <= 35000:
                    return 'MV'  # Medium Voltage
                else:
                    return 'HV'  # High Voltage
        except:
            pass
        
        # Text-based classification
        if 'low' in text:
            return 'LV'
        elif 'medium' in text:
            return 'MV'
        elif 'high' in text:
            return 'HV'
        
        return 'Unknown'
    
    @staticmethod
    def extract_fire_rating(insulation_type, product_name):
        """Extract fire rating from insulation type and product name"""
        text = f"{insulation_type} {product_name}".lower()
        
        if 'frls' in text:
            return 'FRLS'  # Fire Resistant Low Smoke
        elif 'fr-' in text or 'fr ' in text:
            return 'FR'  # Fire Resistant
        elif 'pvc' in text:
            return 'PVC'
        elif 'xlpe' in text:
            return 'XLPE'
        elif 'epr' in text:
            return 'EPR'
        
        return 'Standard'
    
    @staticmethod
    def extract_cable_construction(no_of_cores, product_name):
        """Determine cable construction type"""
        text = product_name.lower()
        cores = int(no_of_cores) if no_of_cores else 0
        
        if 'twin' in text or cores == 2:
            return 'Twin Core'
        elif 'three core' in text or cores == 3:
            return 'Three Core'
        elif cores > 3:
            return f'{cores}-Core'
        elif 'single' in text or cores == 1:
            return 'Single Core'
        elif 'multi' in text:
            return 'Multi-Core'
        
        return f'{cores}-Core' if cores > 0 else 'Unknown'
    
    @staticmethod
    def extract_operating_temperature(insulation_type, max_conductor_temp):
        """Extract operating temperature class"""
        text = str(insulation_type).lower()
        
        try:
            temp = int(max_conductor_temp) if max_conductor_temp else 70
            
            if temp >= 120:
                return '120°C'
            elif temp >= 90:
                return '90°C'
            elif temp >= 70:
                return '70°C'
            else:
                return '60°C'
        except:
            pass
        
        # Text-based classification
        if '70' in text:
            return '70°C'
        elif '90' in text:
            return '90°C'
        elif '120' in text:
            return '120°C'
        
        return '70°C'  # Default
    
    @staticmethod
    def calculate_current_capacity(conductor_size, conductor_material, insulation_type):
        """Calculate estimated current carrying capacity"""
        try:
            size = float(conductor_size) if conductor_size else 1
            material = str(conductor_material).lower()
            insulation = str(insulation_type).lower()
            
            # Determine current density based on insulation (higher temp = higher capacity)
            if '120' in insulation or '120' in str(conductor_size):
                density_mult = 1.3
            elif '90' in insulation:
                density_mult = 1.1
            else:
                density_mult = 1.0
            
            # Base density
            if 'copper' in material:
                base_density = COPPER_CURRENT_DENSITY
            elif 'aluminium' in material:
                base_density = ALUMINIUM_CURRENT_DENSITY
            else:
                base_density = COPPER_CURRENT_DENSITY
            
            # Calculate capacity
            capacity = size * base_density * density_mult
            
            return round(capacity, 1)
        except:
            return 0.0
    
    @staticmethod
    def extract_protection_level(armour_type, insulation_type, conductor_material):
        """Determine protection level"""
        armour = str(armour_type).lower()
        insulation = str(insulation_type).lower()
        
        protection_factors = []
        
        # Armour protection
        if 'swa' in armour or 'steel wire' in armour:
            protection_factors.append('Mechanical')
            protection_factors.append('Armoured')
        
        # Environmental protection
        if 'frls' in insulation or 'fr-' in insulation:
            protection_factors.append('Fire-Resistant')
        
        if 'lsh' in insulation or 'low smoke' in insulation:
            protection_factors.append('Low-Smoke')
        
        if 'xlpe' in insulation or 'epr' in insulation:
            protection_factors.append('Weather-Resistant')
        
        if not protection_factors:
            protection_factors.append('Standard')
        
        return ' + '.join(protection_factors[:2])  # Top 2 protections
    
    @staticmethod
    def extract_primary_application(category, product_name, conductor_size, armour_type):
        """Determine primary application"""
        text = f"{category} {product_name}".lower()
        
        if 'house' in text or 'residential' in text:
            return 'Residential'
        elif 'control' in text:
            return 'Control'
        elif 'submersible' in text:
            return 'Submersible'
        elif 'power cable-ht' in text:
            return 'High Tension'
        elif 'power cable-lt' in text:
            return 'Low Tension'
        elif 'solar' in text:
            return 'Solar'
        elif 'flexible' in text or 'pvc wire' in text:
            return 'General Wiring'
        elif 'instrumentation' in text:
            return 'Instrumentation'
        elif 'underground' in text:
            return 'Underground'
        elif 'outdoor' in text or 'external' in text:
            return 'Outdoor'
        else:
            # Default based on size and specs
            try:
                size = float(conductor_size) if conductor_size else 0
                if size > 50:
                    return 'Power Distribution'
                elif size > 4:
                    return 'Industrial'
            except:
                pass
            
            return 'General Purpose'
    
    def add_columns_to_csv(self, file_path):
        """Add 7 new columns to CSV"""
        try:
            df = pd.read_csv(file_path)
            
            # 1. Voltage_Classification
            df['Voltage_Classification'] = df['Voltage_Rating'].apply(self.extract_voltage_level)
            
            # 2. Fire_Rating
            df['Fire_Rating'] = df.apply(
                lambda row: self.extract_fire_rating(
                    row.get('Insulation_Type', ''),
                    row.get('Product_Name', '')
                ),
                axis=1
            )
            
            # 3. Cable_Construction
            df['Cable_Construction'] = df.apply(
                lambda row: self.extract_cable_construction(
                    row.get('No_of_Cores', 0),
                    row.get('Product_Name', '')
                ),
                axis=1
            )
            
            # 4. Operating_Temperature_Class
            df['Operating_Temperature_Class'] = df.apply(
                lambda row: self.extract_operating_temperature(
                    row.get('Insulation_Type', ''),
                    row.get('Max_Conductor_Temp_C', 70)
                ),
                axis=1
            )
            
            # 5. Estimated_Current_Capacity_Amps
            df['Estimated_Current_Capacity_Amps'] = df.apply(
                lambda row: self.calculate_current_capacity(
                    row.get('Conductor_Size_sqmm', 1),
                    row.get('Conductor_Material', ''),
                    row.get('Insulation_Type', '')
                ),
                axis=1
            )
            
            # 6. Protection_Features
            df['Protection_Features'] = df.apply(
                lambda row: self.extract_protection_level(
                    row.get('Armour_Type', ''),
                    row.get('Insulation_Type', ''),
                    row.get('Conductor_Material', '')
                ),
                axis=1
            )
            
            # 7. Primary_Application
            df['Primary_Application'] = df.apply(
                lambda row: self.extract_primary_application(
                    row.get('Category', ''),
                    row.get('Product_Name', ''),
                    row.get('Conductor_Size_sqmm', 1),
                    row.get('Armour_Type', '')
                ),
                axis=1
            )
            
            # Save
            df.to_csv(file_path, index=False)
            
            return {
                'success': True,
                'file': Path(file_path).name,
                'products': len(df),
                'columns_added': 7,
                'sample': {
                    'voltage_classes': df['Voltage_Classification'].value_counts().to_dict(),
                    'fire_ratings': df['Fire_Rating'].value_counts().to_dict(),
                    'constructions': df['Cable_Construction'].value_counts().to_dict(),
                    'applications': df['Primary_Application'].value_counts().head(3).to_dict(),
                    'avg_current': df['Estimated_Current_Capacity_Amps'].mean()
                }
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
                result = self.add_columns_to_csv(str(csv_file))
                result['oem'] = oem
                results.append(result)
        
        return results

if __name__ == '__main__':
    print("=" * 80)
    print("ADDING 7 MORE COLUMNS WITH EXTRACTED DATA")
    print("=" * 80)
    
    enricher = AdditionalEnricher()
    results = enricher.enrich_all()
    
    total_files = 0
    total_products = 0
    
    for result in results:
        if result['success']:
            total_files += 1
            total_products += result['products']
            
            print(f"\n✓ {result['oem']} - {result['file']}")
            print(f"    Products: {result['products']}")
            print(f"    Columns added: {result['columns_added']}")
            
            if 'sample' in result:
                sample = result['sample']
                print(f"\n    Data Summary:")
                print(f"      Voltage Classes: {sample['voltage_classes']}")
                print(f"      Fire Ratings: {sample['fire_ratings']}")
                print(f"      Constructions: {sample['constructions']}")
                print(f"      Top Applications: {sample['applications']}")
                print(f"      Avg Current Capacity: {sample['avg_current']:.2f} A")
        else:
            print(f"\n✗ {result['oem']} - {result['file']}")
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 80)
    print("SUMMARY - 7 NEW COLUMNS ADDED")
    print("=" * 80)
    print(f"\nFiles processed: {total_files}")
    print(f"Total products enriched: {total_products}")
    print(f"\n7 New Columns Added:")
    print(f"  1. Voltage_Classification - ELV/LV/MV/HV based on voltage rating")
    print(f"  2. Fire_Rating - FRLS/FR/PVC/XLPE/EPR/Standard")
    print(f"  3. Cable_Construction - Single/Twin/Three/Multi-Core classification")
    print(f"  4. Operating_Temperature_Class - 60°C/70°C/90°C/120°C")
    print(f"  5. Estimated_Current_Capacity_Amps - Calculated from conductor size & material")
    print(f"  6. Protection_Features - Mechanical/Fire-Resistant/Low-Smoke/Weather-Resistant")
    print(f"  7. Primary_Application - Residential/Industrial/Submersible/Power/Control/etc.")
    print(f"\nTotal columns per file: 43 (29 original + 7 from Phase 1 + 7 new)")
