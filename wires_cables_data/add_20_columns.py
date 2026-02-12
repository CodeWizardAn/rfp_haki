#!/usr/bin/env python3
"""
Add 20 more columns with advanced extracted data and quality metrics.
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

class Advanced20Enricher:
    """Add 20 advanced columns with quality metrics and risk assessments"""
    
    @staticmethod
    def voltage_drop_risk(conductor_size, no_of_cores, voltage_rating):
        """Assess voltage drop risk"""
        try:
            size = float(conductor_size) if conductor_size else 1
            cores = int(no_of_cores) if no_of_cores else 1
            
            # Voltage drop is inversely proportional to conductor area
            area = size * cores
            
            if area > 50:
                return 'Very Low'
            elif area > 16:
                return 'Low'
            elif area > 4:
                return 'Moderate'
            elif area > 1:
                return 'High'
            else:
                return 'Very High'
        except:
            return 'Unknown'
    
    @staticmethod
    def mechanical_strength(armour_type, no_of_cores, conductor_size):
        """Rate mechanical strength"""
        armour = str(armour_type).lower()
        
        if 'swa' in armour or 'steel' in armour:
            return 'Very High'
        elif 'armoured' in armour:
            return 'High'
        elif int(no_of_cores) if no_of_cores else 0 <= 3:
            return 'Moderate'
        else:
            return 'Low'
    
    @staticmethod
    def chemical_resistance(insulation_type, conductor_material):
        """Determine chemical resistance"""
        insulation = str(insulation_type).lower()
        material = str(conductor_material).lower()
        
        if 'xlpe' in insulation or 'epr' in insulation:
            return 'Excellent'
        elif 'pvc' in insulation:
            return 'Good'
        else:
            return 'Fair'
    
    @staticmethod
    def moisture_resistance(insulation_type, armour_type):
        """Rate moisture resistance"""
        insulation = str(insulation_type).lower()
        armour = str(armour_type).lower()
        
        has_protection = 'armour' in armour or 'swa' in armour
        
        if 'xlpe' in insulation or 'epr' in insulation:
            return 'Excellent' if has_protection else 'Very Good'
        elif 'frls' in insulation:
            return 'Very Good'
        elif 'pvc' in insulation:
            return 'Good' if has_protection else 'Fair'
        else:
            return 'Fair'
    
    @staticmethod
    def uv_resistance(insulation_type, product_name, category):
        """Assess UV resistance"""
        text = f"{insulation_type} {product_name} {category}".lower()
        
        if 'xlpe' in text or 'epr' in text:
            return 'Excellent'
        elif 'outdoor' in text or 'underground' in text:
            return 'Very Good'
        elif 'pvc' in text:
            return 'Good'
        else:
            return 'Fair'
    
    @staticmethod
    def flame_retardant_rating(insulation_type):
        """Rate flame retardant capability"""
        text = str(insulation_type).lower()
        
        if 'frls' in text:
            return 'FRLS (Best)'
        elif 'fr-' in text or 'fr ' in text:
            return 'FR (Very Good)'
        elif 'xlpe' in text or 'epr' in text:
            return 'Self-Extinguishing (Good)'
        elif 'pvc' in text:
            return 'Limited (Fair)'
        else:
            return 'Standard'
    
    @staticmethod
    def smoke_emission(insulation_type):
        """Rate smoke emission level"""
        text = str(insulation_type).lower()
        
        if 'lsh' in text or 'low smoke' in text:
            return 'Low'
        elif 'frls' in text:
            return 'Very Low'
        elif 'xlpe' in text or 'epr' in text:
            return 'Moderate'
        else:
            return 'High'
    
    @staticmethod
    def halogen_content(insulation_type):
        """Assess halogen content"""
        text = str(insulation_type).lower()
        
        if 'lsh' in text or 'low smoke' in text or 'frls' in text:
            return 'Halogen-Free'
        elif 'pvc' in text:
            return 'Contains Halogen'
        elif 'xlpe' in text or 'epr' in text:
            return 'Halogen-Free'
        else:
            return 'Unknown'
    
    @staticmethod
    def comprehensive_safety_rating(insulation_type, armour_type, max_conductor_temp):
        """Comprehensive safety rating"""
        score = 0
        
        insulation = str(insulation_type).lower()
        armour = str(armour_type).lower()
        
        # Temperature safety
        try:
            temp = int(max_conductor_temp) if max_conductor_temp else 70
            if temp >= 120:
                score += 3
            elif temp >= 90:
                score += 2
            else:
                score += 1
        except:
            score += 1
        
        # Insulation safety
        if 'frls' in insulation:
            score += 3
        elif 'fr-' in insulation or 'xlpe' in insulation:
            score += 2
        else:
            score += 1
        
        # Mechanical safety
        if 'swa' in armour:
            score += 2
        elif 'armoured' in armour:
            score += 1
        
        if score >= 7:
            return 'Excellent'
        elif score >= 5:
            return 'Very Good'
        elif score >= 3:
            return 'Good'
        else:
            return 'Fair'
    
    @staticmethod
    def maintenance_frequency(category, insulation_type, armour_type):
        """Estimate maintenance frequency"""
        text = f"{category} {insulation_type}".lower()
        
        if 'frls' in text or 'xlpe' in text:
            return 'Low (5+ years)'
        elif 'armoured' in text:
            return 'Low (5+ years)'
        elif 'pvc' in text:
            return 'Moderate (2-3 years)'
        else:
            return 'Regular (Annual)'
    
    @staticmethod
    def estimated_lifespan(insulation_type, max_conductor_temp, armour_type):
        """Estimate product lifespan in years"""
        insulation = str(insulation_type).lower()
        
        base_years = 20
        
        # Temperature affects lifespan
        try:
            temp = int(max_conductor_temp) if max_conductor_temp else 70
            if temp <= 70:
                base_years += 10
            elif temp >= 120:
                base_years -= 5
        except:
            pass
        
        # Insulation affects lifespan
        if 'xlpe' in insulation or 'epr' in insulation:
            base_years += 10
        elif 'frls' in insulation:
            base_years += 5
        
        return f'{base_years} years'
    
    @staticmethod
    def recycling_capability(conductor_material, insulation_type, armour_type):
        """Assess recyclability"""
        material = str(conductor_material).lower()
        insulation = str(insulation_type).lower()
        
        if 'copper' in material and ('xlpe' in insulation or 'pvc' in insulation):
            return 'Highly Recyclable'
        elif 'copper' in material:
            return 'Recyclable'
        elif 'aluminium' in material:
            return 'Recyclable'
        else:
            return 'Partially Recyclable'
    
    @staticmethod
    def humidity_tolerance(insulation_type, armour_type):
        """Rate humidity tolerance"""
        insulation = str(insulation_type).lower()
        armour = str(armour_type).lower()
        
        is_protected = 'armour' in armour or 'swa' in armour
        
        if 'xlpe' in insulation or 'epr' in insulation:
            return 'Excellent'
        elif 'frls' in insulation:
            return 'Very Good'
        elif 'pvc' in insulation:
            return 'Good' if is_protected else 'Fair'
        else:
            return 'Fair'
    
    @staticmethod
    def oil_resistance(conductor_material, insulation_type):
        """Rate oil resistance"""
        insulation = str(insulation_type).lower()
        
        if 'epr' in insulation or 'xlpe' in insulation:
            return 'Excellent'
        elif 'pvc' in insulation:
            return 'Good'
        else:
            return 'Fair'
    
    @staticmethod
    def ozone_resistance(insulation_type):
        """Rate ozone resistance"""
        text = str(insulation_type).lower()
        
        if 'xlpe' in text or 'epr' in text:
            return 'Excellent'
        elif 'frls' in text:
            return 'Very Good'
        else:
            return 'Fair'
    
    @staticmethod
    def tensile_strength_category(armour_type, conductor_material, no_of_cores):
        """Classify tensile strength"""
        armour = str(armour_type).lower()
        material = str(conductor_material).lower()
        
        if 'swa' in armour or 'steel' in armour:
            return 'Very High'
        elif 'armoured' in armour:
            return 'High'
        elif 'copper' in material:
            return 'High'
        else:
            return 'Moderate'
    
    @staticmethod
    def flexibility_score(conductor_size, no_of_cores, insulation_type):
        """Calculate flexibility score (0-100)"""
        try:
            size = float(conductor_size) if conductor_size else 1
            cores = int(no_of_cores) if no_of_cores else 1
            
            score = 100
            
            # Size penalty
            score -= min(size * 5, 40)
            
            # Core count bonus
            if cores <= 3:
                score += 10
            
            return max(20, min(100, score))
        except:
            return 50
    
    @staticmethod
    def durability_rating(insulation_type, armour_type, max_conductor_temp):
        """Comprehensive durability assessment"""
        insulation = str(insulation_type).lower()
        armour = str(armour_type).lower()
        
        score = 0
        
        # Insulation durability
        if 'xlpe' in insulation or 'epr' in insulation:
            score += 3
        elif 'frls' in insulation:
            score += 2
        else:
            score += 1
        
        # Mechanical protection
        if 'swa' in armour:
            score += 3
        elif 'armoured' in armour:
            score += 2
        
        # Temperature rating
        try:
            temp = int(max_conductor_temp) if max_conductor_temp else 70
            if temp >= 120:
                score += 2
            elif temp >= 90:
                score += 1
        except:
            pass
        
        if score >= 6:
            return 'Excellent'
        elif score >= 4:
            return 'Very Good'
        elif score >= 2:
            return 'Good'
        else:
            return 'Fair'
    
    @staticmethod
    def price_category(price_per_meter):
        """Classify price tier"""
        try:
            price = float(price_per_meter) if price_per_meter else 0
            
            if price < 50:
                return 'Budget'
            elif price < 200:
                return 'Standard'
            elif price < 1000:
                return 'Premium'
            else:
                return 'Ultra-Premium'
        except:
            return 'Unknown'
    
    @staticmethod
    def overall_quality_score(insulation_type, armour_type, conductor_material, 
                            max_conductor_temp, no_of_cores, conductor_size):
        """Comprehensive quality metric (0-100)"""
        score = 50
        
        insulation = str(insulation_type).lower()
        armour = str(armour_type).lower()
        material = str(conductor_material).lower()
        
        # Material quality
        if 'copper' in material:
            score += 10
        elif 'aluminium' in material:
            score += 5
        
        # Insulation quality
        if 'xlpe' in insulation or 'epr' in insulation:
            score += 15
        elif 'frls' in insulation:
            score += 12
        elif 'pvc' in insulation:
            score += 8
        
        # Protection
        if 'swa' in armour:
            score += 12
        elif 'armoured' in armour:
            score += 8
        
        # Temperature capability
        try:
            temp = int(max_conductor_temp) if max_conductor_temp else 70
            if temp >= 120:
                score += 8
            elif temp >= 90:
                score += 5
        except:
            pass
        
        # Core configuration
        try:
            cores = int(no_of_cores) if no_of_cores else 1
            size = float(conductor_size) if conductor_size else 1
            
            if cores >= 4 and size > 4:
                score += 5
        except:
            pass
        
        return min(100, score)
    
    def add_columns_to_csv(self, file_path):
        """Add 20 new columns to CSV"""
        try:
            df = pd.read_csv(file_path)
            
            # 1. Voltage_Drop_Risk
            df['Voltage_Drop_Risk'] = df.apply(
                lambda row: self.voltage_drop_risk(
                    row.get('Conductor_Size_sqmm'),
                    row.get('No_of_Cores'),
                    row.get('Voltage_Rating')
                ),
                axis=1
            )
            
            # 2. Mechanical_Strength
            df['Mechanical_Strength'] = df.apply(
                lambda row: self.mechanical_strength(
                    row.get('Armour_Type'),
                    row.get('No_of_Cores'),
                    row.get('Conductor_Size_sqmm')
                ),
                axis=1
            )
            
            # 3. Chemical_Resistance
            df['Chemical_Resistance'] = df.apply(
                lambda row: self.chemical_resistance(
                    row.get('Insulation_Type'),
                    row.get('Conductor_Material')
                ),
                axis=1
            )
            
            # 4. Moisture_Resistance
            df['Moisture_Resistance'] = df.apply(
                lambda row: self.moisture_resistance(
                    row.get('Insulation_Type'),
                    row.get('Armour_Type')
                ),
                axis=1
            )
            
            # 5. UV_Resistance
            df['UV_Resistance'] = df.apply(
                lambda row: self.uv_resistance(
                    row.get('Insulation_Type'),
                    row.get('Product_Name'),
                    row.get('Category')
                ),
                axis=1
            )
            
            # 6. Flame_Retardant_Rating
            df['Flame_Retardant_Rating'] = df['Insulation_Type'].apply(self.flame_retardant_rating)
            
            # 7. Smoke_Emission_Level
            df['Smoke_Emission_Level'] = df['Insulation_Type'].apply(self.smoke_emission)
            
            # 8. Halogen_Content_Status
            df['Halogen_Content_Status'] = df['Insulation_Type'].apply(self.halogen_content)
            
            # 9. Safety_Rating
            df['Safety_Rating'] = df.apply(
                lambda row: self.comprehensive_safety_rating(
                    row.get('Insulation_Type'),
                    row.get('Armour_Type'),
                    row.get('Max_Conductor_Temp_C')
                ),
                axis=1
            )
            
            # 10. Maintenance_Schedule
            df['Maintenance_Schedule'] = df.apply(
                lambda row: self.maintenance_frequency(
                    row.get('Category'),
                    row.get('Insulation_Type'),
                    row.get('Armour_Type')
                ),
                axis=1
            )
            
            # 11. Estimated_Lifespan
            df['Estimated_Lifespan'] = df.apply(
                lambda row: self.estimated_lifespan(
                    row.get('Insulation_Type'),
                    row.get('Max_Conductor_Temp_C'),
                    row.get('Armour_Type')
                ),
                axis=1
            )
            
            # 12. Recycling_Capability
            df['Recycling_Capability'] = df.apply(
                lambda row: self.recycling_capability(
                    row.get('Conductor_Material'),
                    row.get('Insulation_Type'),
                    row.get('Armour_Type')
                ),
                axis=1
            )
            
            # 13. Humidity_Tolerance
            df['Humidity_Tolerance'] = df.apply(
                lambda row: self.humidity_tolerance(
                    row.get('Insulation_Type'),
                    row.get('Armour_Type')
                ),
                axis=1
            )
            
            # 14. Oil_Resistance
            df['Oil_Resistance'] = df.apply(
                lambda row: self.oil_resistance(
                    row.get('Conductor_Material'),
                    row.get('Insulation_Type')
                ),
                axis=1
            )
            
            # 15. Ozone_Resistance
            df['Ozone_Resistance'] = df['Insulation_Type'].apply(self.ozone_resistance)
            
            # 16. Tensile_Strength_Rating
            df['Tensile_Strength_Rating'] = df.apply(
                lambda row: self.tensile_strength_category(
                    row.get('Armour_Type'),
                    row.get('Conductor_Material'),
                    row.get('No_of_Cores')
                ),
                axis=1
            )
            
            # 17. Flexibility_Score
            df['Flexibility_Score'] = df.apply(
                lambda row: self.flexibility_score(
                    row.get('Conductor_Size_sqmm'),
                    row.get('No_of_Cores'),
                    row.get('Insulation_Type')
                ),
                axis=1
            )
            
            # 18. Durability_Rating
            df['Durability_Rating'] = df.apply(
                lambda row: self.durability_rating(
                    row.get('Insulation_Type'),
                    row.get('Armour_Type'),
                    row.get('Max_Conductor_Temp_C')
                ),
                axis=1
            )
            
            # 19. Price_Tier
            df['Price_Tier'] = df['Price_Per_Meter_INR'].apply(self.price_category)
            
            # 20. Overall_Quality_Score
            df['Overall_Quality_Score'] = df.apply(
                lambda row: self.overall_quality_score(
                    row.get('Insulation_Type'),
                    row.get('Armour_Type'),
                    row.get('Conductor_Material'),
                    row.get('Max_Conductor_Temp_C'),
                    row.get('No_of_Cores'),
                    row.get('Conductor_Size_sqmm')
                ),
                axis=1
            )
            
            # Save
            df.to_csv(file_path, index=False)
            
            return {
                'success': True,
                'file': Path(file_path).name,
                'products': len(df),
                'columns_added': 20,
                'total_columns': len(df.columns),
                'sample': {
                    'safety_ratings': df['Safety_Rating'].value_counts().to_dict(),
                    'durability_ratings': df['Durability_Rating'].value_counts().to_dict(),
                    'avg_quality_score': df['Overall_Quality_Score'].mean(),
                    'avg_flexibility': df['Flexibility_Score'].mean(),
                    'price_distribution': df['Price_Tier'].value_counts().to_dict()
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
    print("=" * 90)
    print("ADDING 20 MORE ADVANCED COLUMNS WITH QUALITY & RISK METRICS")
    print("=" * 90)
    
    enricher = Advanced20Enricher()
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
                print(f"      Safety Ratings: {sample['safety_ratings']}")
                print(f"      Durability Ratings: {sample['durability_ratings']}")
                print(f"      Avg Quality Score: {sample['avg_quality_score']:.1f}/100")
                print(f"      Avg Flexibility Score: {sample['avg_flexibility']:.1f}/100")
                print(f"      Price Distribution: {sample['price_distribution']}")
        else:
            print(f"\n✗ {result['oem']} - {result['file']}")
            print(f"    Error: {result['error']}")
    
    print("\n" + "=" * 90)
    print("SUMMARY - 20 NEW ADVANCED COLUMNS ADDED")
    print("=" * 90)
    print(f"\nFiles processed: {total_files}")
    print(f"Total products enriched: {total_products}")
    print(f"\n20 New Advanced Columns:")
    print(f"  1. Voltage_Drop_Risk - Very Low/Low/Moderate/High/Very High")
    print(f"  2. Mechanical_Strength - Low/Moderate/High/Very High")
    print(f"  3. Chemical_Resistance - Fair/Good/Excellent")
    print(f"  4. Moisture_Resistance - Fair/Good/Very Good/Excellent")
    print(f"  5. UV_Resistance - Fair/Good/Very Good/Excellent")
    print(f"  6. Flame_Retardant_Rating - FRLS/FR/Self-Extinguishing/Limited/Standard")
    print(f"  7. Smoke_Emission_Level - Low/Very Low/Moderate/High")
    print(f"  8. Halogen_Content_Status - Halogen-Free/Contains Halogen")
    print(f"  9. Safety_Rating - Fair/Good/Very Good/Excellent")
    print(f" 10. Maintenance_Schedule - Low/Moderate/Regular frequency")
    print(f" 11. Estimated_Lifespan - Years estimate")
    print(f" 12. Recycling_Capability - Highly Recyclable/Recyclable/Partially")
    print(f" 13. Humidity_Tolerance - Fair/Good/Very Good/Excellent")
    print(f" 14. Oil_Resistance - Fair/Good/Excellent")
    print(f" 15. Ozone_Resistance - Fair/Very Good/Excellent")
    print(f" 16. Tensile_Strength_Rating - Moderate/High/Very High")
    print(f" 17. Flexibility_Score - 0-100 numeric score")
    print(f" 18. Durability_Rating - Fair/Good/Very Good/Excellent")
    print(f" 19. Price_Tier - Budget/Standard/Premium/Ultra-Premium")
    print(f" 20. Overall_Quality_Score - 0-100 comprehensive metric")
    print(f"\nTotal columns per file now: 74 (29 original + 45 enriched)")
