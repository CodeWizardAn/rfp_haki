#!/usr/bin/env python3
"""
Add 10 more columns with extracted data from product specifications.
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

class AdditionalEnricher10:
    """Add 10 more columns with extracted intelligent data"""
    
    @staticmethod
    def classify_weight(weight_kg_per_km):
        """Classify cable weight category"""
        try:
            weight = float(weight_kg_per_km) if weight_kg_per_km else 0
            
            if weight < 10:
                return 'Light'
            elif weight < 50:
                return 'Medium'
            elif weight < 200:
                return 'Heavy'
            else:
                return 'Very Heavy'
        except:
            return 'Unknown'
    
    @staticmethod
    def determine_conductor_type(conductor_class):
        """Determine if conductor is solid or stranded"""
        text = str(conductor_class).lower()
        
        if 'class 1' in text or 'class 2' in text:
            return 'Solid'
        elif 'class 5' in text or 'class 6' in text:
            return 'Stranded'
        elif 'solid' in text:
            return 'Solid'
        elif 'stranded' in text:
            return 'Stranded'
        
        # Default based on presence
        if text and text != 'unknown' and text != 'nan':
            return 'Stranded'  # Most modern cables use stranded
        
        return 'Unknown'
    
    @staticmethod
    def classify_insulation_thickness(insulation_thickness_mm, conductor_size):
        """Classify insulation thickness"""
        try:
            thickness = float(insulation_thickness_mm) if insulation_thickness_mm else 1.0
            size = float(conductor_size) if conductor_size else 1.0
            
            # Ratio of insulation to conductor
            ratio = thickness / (size ** 0.5)
            
            if ratio < 0.5:
                return 'Thin'
            elif ratio < 1.5:
                return 'Standard'
            else:
                return 'Thick'
        except:
            return 'Standard'
    
    @staticmethod
    def classify_diameter(outer_diameter_mm):
        """Classify cable by outer diameter"""
        try:
            diameter = float(outer_diameter_mm) if outer_diameter_mm else 0
            
            if diameter < 5:
                return 'Compact'
            elif diameter < 15:
                return 'Small'
            elif diameter < 30:
                return 'Medium'
            elif diameter < 60:
                return 'Large'
            else:
                return 'Very Large'
        except:
            return 'Unknown'
    
    @staticmethod
    def is_suitable_for_underground(armour_type, insulation_type, standard):
        """Determine if suitable for underground use"""
        armour = str(armour_type).lower()
        insulation = str(insulation_type).lower()
        standard_text = str(standard).lower()
        
        # Underground requires armour + proper insulation
        is_armoured = 'armour' in armour or 'swa' in armour
        has_good_insulation = ('xlpe' in insulation or 'epr' in insulation or 'pvc' in insulation)
        
        # Check standards
        is_underground_rated = ('is 7098' in standard_text or 'underground' in standard_text)
        
        if is_armoured and has_good_insulation:
            return 'Yes'
        elif is_underground_rated:
            return 'Yes'
        else:
            return 'No'
    
    @staticmethod
    def get_thermal_resistance(insulation_type, max_temp):
        """Estimate thermal resistance category"""
        text = str(insulation_type).lower()
        
        try:
            temp = int(max_temp) if max_temp else 70
            
            if temp >= 120:
                return 'Very High'
            elif temp >= 90:
                return 'High'
            elif temp >= 70:
                return 'Medium'
            else:
                return 'Low'
        except:
            pass
        
        if 'xlpe' in text or 'epr' in text:
            return 'High'
        elif 'frls' in text or 'pvc' in text:
            return 'Medium'
        else:
            return 'Medium'
    
    @staticmethod
    def estimate_bending_radius(conductor_size, no_of_cores, armour_type):
        """Estimate bending radius category"""
        try:
            size = float(conductor_size) if conductor_size else 1
            cores = int(no_of_cores) if no_of_cores else 1
            armour = str(armour_type).lower()
            
            is_armoured = 'armour' in armour or 'swa' in armour
            
            # Smaller, flexible cores = smaller bending radius
            if cores <= 3 and not is_armoured:
                return 'Very Flexible'
            elif size <= 4 and cores <= 3:
                return 'Flexible'
            elif size <= 16:
                return 'Semi-Flexible'
            else:
                return 'Rigid'
        except:
            return 'Standard'
    
    @staticmethod
    def environmental_suitability(category, product_name, insulation_type):
        """Determine environmental suitability"""
        text = f"{category} {product_name}".lower()
        insulation = str(insulation_type).lower()
        
        is_outdoor = ('underground' in text or 'outdoor' in text or 'external' in text)
        is_industrial = ('industrial' in text or 'control' in text)
        
        # Check insulation for outdoor use
        has_outdoor_insulation = ('xlpe' in insulation or 'epr' in insulation)
        
        if is_outdoor and has_outdoor_insulation:
            return 'Outdoor'
        elif is_industrial:
            return 'Both'
        else:
            return 'Indoor/General'
    
    @staticmethod
    def calculate_cost_per_ampere(price_per_meter, estimated_current_capacity):
        """Calculate cost per ampere (efficiency metric)"""
        try:
            price = float(price_per_meter) if price_per_meter else 0
            current = float(estimated_current_capacity) if estimated_current_capacity else 1
            
            if current > 0:
                return round(price / current, 2)
            else:
                return 0
        except:
            return 0
    
    @staticmethod
    def classify_wire_gauge(conductor_size):
        """Classify conductor wire gauge"""
        try:
            size = float(conductor_size) if conductor_size else 1
            
            if size < 0.5:
                return '> 18 AWG'
            elif size < 1:
                return '16-18 AWG'
            elif size < 2.5:
                return '14-16 AWG'
            elif size < 4:
                return '12-14 AWG'
            elif size < 6:
                return '10-12 AWG'
            elif size < 10:
                return '8-10 AWG'
            elif size < 16:
                return '6-8 AWG'
            elif size < 25:
                return '4-6 AWG'
            else:
                return '< 4 AWG'
        except:
            return 'Unknown'
    
    @staticmethod
    def estimate_installation_difficulty(no_of_cores, outer_diameter_mm, armour_type):
        """Estimate installation difficulty"""
        try:
            cores = int(no_of_cores) if no_of_cores else 1
            diameter = float(outer_diameter_mm) if outer_diameter_mm else 5
            armour = str(armour_type).lower()
            
            is_armoured = 'armour' in armour or 'swa' in armour
            
            # Simple scoring
            score = 0
            
            # Diameter impact
            if diameter > 30:
                score += 2
            elif diameter > 15:
                score += 1
            
            # Cores impact
            if cores > 4:
                score += 2
            elif cores > 2:
                score += 1
            
            # Armour impact
            if is_armoured:
                score += 1
            
            if score >= 3:
                return 'Complex'
            elif score >= 1:
                return 'Moderate'
            else:
                return 'Easy'
        except:
            return 'Standard'
    
    def add_columns_to_csv(self, file_path):
        """Add 10 new columns to CSV"""
        try:
            df = pd.read_csv(file_path)
            
            # 1. Weight_Category
            df['Weight_Category'] = df['Approx_Weight_kg_per_km'].apply(self.classify_weight)
            
            # 2. Conductor_Type
            df['Conductor_Type'] = df['Conductor_Class'].apply(self.determine_conductor_type)
            
            # 3. Insulation_Thickness_Category
            df['Insulation_Thickness_Category'] = df.apply(
                lambda row: self.classify_insulation_thickness(
                    row.get('Insulation_Thickness_mm'),
                    row.get('Conductor_Size_sqmm')
                ),
                axis=1
            )
            
            # 4. Cable_Diameter_Category
            df['Cable_Diameter_Category'] = df['Outer_Diameter_mm'].apply(self.classify_diameter)
            
            # 5. Suitable_For_Underground
            df['Suitable_For_Underground'] = df.apply(
                lambda row: self.is_suitable_for_underground(
                    row.get('Armour_Type'),
                    row.get('Insulation_Type'),
                    row.get('Standard')
                ),
                axis=1
            )
            
            # 6. Thermal_Resistance_Level
            df['Thermal_Resistance_Level'] = df.apply(
                lambda row: self.get_thermal_resistance(
                    row.get('Insulation_Type'),
                    row.get('Max_Conductor_Temp_C')
                ),
                axis=1
            )
            
            # 7. Bending_Radius_Category
            df['Bending_Radius_Category'] = df.apply(
                lambda row: self.estimate_bending_radius(
                    row.get('Conductor_Size_sqmm'),
                    row.get('No_of_Cores'),
                    row.get('Armour_Type')
                ),
                axis=1
            )
            
            # 8. Environmental_Suitability
            df['Environmental_Suitability'] = df.apply(
                lambda row: self.environmental_suitability(
                    row.get('Category'),
                    row.get('Product_Name'),
                    row.get('Insulation_Type')
                ),
                axis=1
            )
            
            # 9. Cost_Per_Ampere_INR
            df['Cost_Per_Ampere_INR'] = df.apply(
                lambda row: self.calculate_cost_per_ampere(
                    row.get('Price_Per_Meter_INR'),
                    row.get('Estimated_Current_Capacity_Amps')
                ),
                axis=1
            )
            
            # 10. Wire_Gauge_Classification
            df['Wire_Gauge_Classification'] = df['Conductor_Size_sqmm'].apply(self.classify_wire_gauge)
            
            # Bonus: Installation_Difficulty
            df['Installation_Difficulty'] = df.apply(
                lambda row: self.estimate_installation_difficulty(
                    row.get('No_of_Cores'),
                    row.get('Outer_Diameter_mm'),
                    row.get('Armour_Type')
                ),
                axis=1
            )
            
            # Save
            df.to_csv(file_path, index=False)
            
            return {
                'success': True,
                'file': Path(file_path).name,
                'products': len(df),
                'columns_added': 11,  # 10 + 1 bonus
                'total_columns': len(df.columns),
                'sample': {
                    'weight_categories': df['Weight_Category'].value_counts().head(3).to_dict(),
                    'conductor_types': df['Conductor_Type'].value_counts().to_dict(),
                    'diameter_categories': df['Cable_Diameter_Category'].value_counts().head(3).to_dict(),
                    'underground_suitable': df['Suitable_For_Underground'].value_counts().to_dict(),
                    'avg_cost_per_amp': df['Cost_Per_Ampere_INR'].mean()
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
    print("ADDING 10 MORE COLUMNS (+ 1 BONUS) WITH EXTRACTED DATA")
    print("=" * 80)
    
    enricher = AdditionalEnricher10()
    results = enricher.enrich_all()
    
    total_files = 0
    total_products = 0
    
    for result in results:
        if result['success']:
            total_files += 1
            total_products += result['products']
            
            print(f"\n✓ {result['oem']} - {result['file']}")
            print(f"    Products: {result['products']}")
            print(f"    Total columns now: {result['total_columns']}")
            
            if 'sample' in result:
                sample = result['sample']
                print(f"\n    Data Summary:")
                print(f"      Weight Categories: {sample['weight_categories']}")
                print(f"      Conductor Types: {sample['conductor_types']}")
                print(f"      Diameter Categories: {sample['diameter_categories']}")
                print(f"      Underground Suitable: {sample['underground_suitable']}")
                print(f"      Avg Cost/Ampere: Rs {sample['avg_cost_per_amp']:.2f}")
        else:
            print(f"\n✗ {result['oem']} - {result['file']}")
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 80)
    print("SUMMARY - 10 NEW COLUMNS + 1 BONUS ADDED")
    print("=" * 80)
    print(f"\nFiles processed: {total_files}")
    print(f"Total products enriched: {total_products}")
    print(f"\n10 New Columns Added:")
    print(f"  1. Weight_Category - Light/Medium/Heavy/Very Heavy")
    print(f"  2. Conductor_Type - Solid/Stranded based on conductor class")
    print(f"  3. Insulation_Thickness_Category - Thin/Standard/Thick")
    print(f"  4. Cable_Diameter_Category - Compact/Small/Medium/Large/Very Large")
    print(f"  5. Suitable_For_Underground - Yes/No based on specs")
    print(f"  6. Thermal_Resistance_Level - Low/Medium/High/Very High")
    print(f"  7. Bending_Radius_Category - Very Flexible/Flexible/Semi-Flexible/Rigid")
    print(f"  8. Environmental_Suitability - Indoor/General/Both/Outdoor")
    print(f"  9. Cost_Per_Ampere_INR - Price efficiency metric")
    print(f" 10. Wire_Gauge_Classification - AWG equivalents")
    print(f"\n+ BONUS Column:")
    print(f" 11. Installation_Difficulty - Easy/Moderate/Complex")
    print(f"\nTotal columns per file now: 54 (29 original + 7 Phase1 + 7 Phase2 + 11)")
