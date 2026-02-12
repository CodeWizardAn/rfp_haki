#!/usr/bin/env python3
"""
Optimize wires and cables datasets for accurate RFP matching
Adds columns for better matching even when different terms are used for the same product
"""

import os
import pandas as pd
from pathlib import Path
import re
import sys
from datetime import datetime

OEM_PATHS = {
    'POLYCAB': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/polycab',
    'HAVELLS': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/havells',
    'RR_KABEL': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/rr_kabel',
    'KEI': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/kei',
    'FINOLEX': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/finolex'
}

MARKETPLACE_PATHS = {
    'moglix_1': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/moglix_1.csv',
    'moglix_2': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/moglix_2.csv'
}

# Synonyms and alternative terminology for better matching
PRODUCT_SYNONYMS = {
    'house wire': ['house wire', 'domestic wire', 'pvc wire', 'pvc sheathed wire', 'single phase wire', 'home wire', 'building wire'],
    'flexible cable': ['flexible', 'stranded', 'flexible cable', 'stranded conductor', 'multi-strand', 'soft cable', 'house cable'],
    'armoured cable': ['armoured', 'swa', 'steel wire armoured', 'armored cable', 'industrial cable', 'armour cable'],
    'control cable': ['control cable', 'instrumentation cable', 'signal cable', 'low tension cable', 'pilot cable', 'control instrumentation'],
    'power cable': ['power cable', 'distribution cable', 'feeder cable', 'main cable', 'supply cable', 'transmission cable'],
    'submersible cable': ['submersible', 'submersible wire', 'pump cable', 'submerged cable', 'underwater cable'],
    'solar cable': ['solar', 'pv cable', 'photovoltaic cable', 'dc cable', 'low voltage cable'],
    'fire resistant': ['fire resistant', 'frls', 'flame retardant', 'fr cable', 'low smoke', 'lsh', 'non-halogen', 'halogen free'],
    'low voltage': ['low voltage', 'lv cable', 'below 1000v', 'below 1kv', 'domestic voltage'],
    'high voltage': ['high voltage', 'hv cable', 'above 1000v', 'above 1kv', 'industrial voltage', 'extra high voltage', 'ehv'],
}

INSULATION_SYNONYMS = {
    'pvc': ['pvc', 'polyvinyl chloride', 'pvc insulation', 'pvc sheath'],
    'xlpe': ['xlpe', 'cross linked polyethylene', 'cross-linked pe', 'xlpe insulation'],
    'epr': ['epr', 'ethylene propylene rubber', 'rubber insulation', 'epr insulation'],
    'rubber': ['rubber', 'natural rubber', 'synthetic rubber', 'elastomer'],
}

CONDUCTOR_SYNONYMS = {
    'copper': ['copper', 'cu', 'cu conductor', 'electrolytic copper'],
    'aluminium': ['aluminium', 'aluminum', 'al', 'al conductor'],
}

ARMOUR_SYNONYMS = {
    'swa': ['swa', 'steel wire armour', 'steel wire armored', 'steel armour', 'armoured steel'],
    'gaa': ['gaa', 'galvanised', 'galvanized', 'galv armour'],
    'none': ['none', 'unarmoured', 'unarmored', 'bare', 'no armour', 'without armour'],
}

# Standard voltages and their variations
VOLTAGE_MAPPING = {
    '230V': ['230v', '230V', '220-240v', '220-240V', 'single phase'],
    '400V': ['400v', '400V', '415v', '415V', '380-415v', 'three phase', '3 phase'],
    '660V': ['660v', '660V', 'high voltage', 'industrial'],
    '1000V': ['1000v', '1kv', 'lv', 'low voltage'],
    '1100V+': ['1100v', '3.3kv', '6.6kv', '11kv', '33kv', 'mv', 'hv', 'high voltage'],
}

class RFPMatchingOptimizer:
    """Optimize datasets for RFP matching with enhanced columns"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def extract_product_synonyms(self, product_name, category, insulation_type):
        """Extract matching synonyms from product information"""
        if not product_name:
            return []
        
        text = f"{product_name} {category} {insulation_type}".lower()
        synonyms = []
        
        for synonym_group, variations in PRODUCT_SYNONYMS.items():
            for var in variations:
                if var.lower() in text:
                    synonyms.append(synonym_group)
                    break
        
        return list(set(synonyms))
    
    def normalize_voltage(self, voltage_rating):
        """Normalize voltage to standard categories"""
        if not voltage_rating:
            return 'Unknown'
        
        voltage_str = str(voltage_rating).lower().replace('v', '').replace(' ', '')
        
        for std_voltage, variations in VOLTAGE_MAPPING.items():
            for var in variations:
                if var.lower() in str(voltage_rating).lower():
                    return std_voltage
        
        try:
            val = float(voltage_str.split('-')[0]) if '-' in voltage_str else float(voltage_str)
            if val <= 250:
                return '230V'
            elif val <= 500:
                return '400V'
            elif val <= 1000:
                return '1000V'
            else:
                return '1100V+'
        except:
            return 'Unknown'
    
    def normalize_conductor_material(self, material):
        """Normalize conductor material"""
        if not material:
            return 'Unknown'
        
        text = str(material).lower()
        
        for std_material, variations in CONDUCTOR_SYNONYMS.items():
            for var in variations:
                if var.lower() in text:
                    return std_material.capitalize()
        
        return 'Other'
    
    def normalize_insulation(self, insulation_type):
        """Normalize insulation type"""
        if not insulation_type:
            return 'Unknown'
        
        text = str(insulation_type).lower()
        
        for std_insulation, variations in INSULATION_SYNONYMS.items():
            for var in variations:
                if var.lower() in text:
                    return std_insulation.upper()
        
        return 'Other'
    
    def normalize_armour(self, armour_type):
        """Normalize armour type"""
        if not armour_type:
            return 'None'
        
        text = str(armour_type).lower()
        
        for std_armour, variations in ARMOUR_SYNONYMS.items():
            for var in variations:
                if var.lower() in text:
                    return std_armour.upper()
        
        return 'Other'
    
    def extract_size_range(self, conductor_size):
        """Extract size range for grouping"""
        try:
            size = float(conductor_size)
            if size <= 1.5:
                return '≤1.5 sqmm'
            elif size <= 2.5:
                return '2.5 sqmm'
            elif size <= 4.0:
                return '4.0 sqmm'
            elif size <= 6.0:
                return '6.0 sqmm'
            elif size <= 10.0:
                return '10.0 sqmm'
            elif size <= 16.0:
                return '16.0 sqmm'
            elif size <= 25.0:
                return '25.0 sqmm'
            elif size <= 35.0:
                return '35.0 sqmm'
            elif size <= 50.0:
                return '50.0 sqmm'
            elif size <= 70.0:
                return '70.0 sqmm'
            elif size <= 95.0:
                return '95.0 sqmm'
            elif size <= 120.0:
                return '120.0 sqmm'
            elif size <= 150.0:
                return '150.0 sqmm'
            else:
                return '>150 sqmm'
        except:
            return 'Unknown'
    
    def extract_cores_category(self, no_of_cores):
        """Categorize by number of cores"""
        try:
            cores = int(no_of_cores) if no_of_cores else 0
            if cores == 1:
                return 'Single Core'
            elif cores == 2:
                return 'Twin'
            elif cores == 3:
                return 'Three Core'
            elif cores == 4:
                return 'Four Core'
            else:
                return f'{cores} Cores'
        except:
            return 'Unknown'
    
    def extract_fire_rating(self, insulation_type, product_name, category):
        """Extract fire rating information"""
        text = f"{insulation_type} {product_name} {category}".lower()
        
        if 'frls' in text or 'fr-ls' in text:
            return 'FRLS'
        elif 'fr' in text and 'flame' in text:
            return 'FR'
        elif 'lsh' in text or 'low smoke' in text or 'halogen free' in text:
            return 'LSH'
        elif 'pvc' in text:
            return 'Standard'
        else:
            return 'Not Specified'
    
    def extract_application_domain(self, product_name, category, is_armoured, is_industrial):
        """Extract application domain/sector"""
        text = f"{product_name} {category}".lower()
        
        if 'submersible' in text or 'pump' in text:
            return 'Submersible/Agricultural'
        elif 'solar' in text or 'pv' in text or 'dc' in text:
            return 'Solar/Renewable'
        elif 'industrial' in text or is_industrial == 1:
            return 'Industrial'
        elif 'underground' in text or 'buried' in text:
            return 'Underground'
        elif 'control' in text or 'instrument' in text or 'signal' in text:
            return 'Control/Instrumentation'
        elif 'power' in text or 'distribution' in text:
            return 'Power Distribution'
        elif 'house' in text or 'domestic' in text or 'residential' in text:
            return 'Residential'
        else:
            return 'General Purpose'
    
    def extract_matching_tags(self, row):
        """Extract multiple matching tags for RFP comparison"""
        tags = []
        
        # Voltage-based tags
        voltage_norm = self.normalize_voltage(row.get('Voltage_Rating', ''))
        if voltage_norm != 'Unknown':
            tags.append(f"volt_{voltage_norm.replace('V', '').replace('+', 'plus')}")
        
        # Conductor material tags
        conductor = self.normalize_conductor_material(row.get('Conductor_Material', ''))
        if conductor != 'Unknown':
            tags.append(f"conductor_{conductor.lower()}")
        
        # Insulation tags
        insulation = self.normalize_insulation(row.get('Insulation_Type', ''))
        if insulation != 'Unknown':
            tags.append(f"insulation_{insulation.lower()}")
        
        # Size tags
        size_range = self.extract_size_range(row.get('Conductor_Size_sqmm', ''))
        if size_range != 'Unknown':
            tags.append(f"size_{size_range.replace(' ', '').lower()}")
        
        # Cores tags
        cores_cat = self.extract_cores_category(row.get('No_of_Cores', ''))
        if cores_cat != 'Unknown':
            tags.append(f"cores_{cores_cat.replace(' ', '_').lower()}")
        
        # Armour tags
        armour = self.normalize_armour(row.get('Armour_Type', ''))
        tags.append(f"armour_{armour.lower()}")
        
        # Application tags
        app_domain = self.extract_application_domain(
            row.get('Product_Name', ''),
            row.get('Category', ''),
            row.get('Is_Armoured', 0),
            row.get('Is_Industrial', 0)
        )
        if app_domain:
            tags.append(f"app_{app_domain.replace('/', '_').replace(' ', '_').lower()}")
        
        return '|'.join(tags) if tags else 'general'
    
    def add_optimization_columns(self, df, oem_name='Unknown'):
        """Add optimization columns to dataframe"""
        
        # 1. Normalized Voltage Classification
        df['Voltage_Normalized'] = df['Voltage_Rating'].apply(self.normalize_voltage)
        
        # 2. Normalized Conductor Material
        df['Conductor_Material_Normalized'] = df['Conductor_Material'].apply(
            self.normalize_conductor_material
        )
        
        # 3. Normalized Insulation Type
        df['Insulation_Type_Normalized'] = df['Insulation_Type'].apply(
            self.normalize_insulation
        )
        
        # 4. Normalized Armour Type
        df['Armour_Type_Normalized'] = df['Armour_Type'].apply(
            self.normalize_armour
        )
        
        # 5. Size Range Category
        df['Conductor_Size_Range'] = df['Conductor_Size_sqmm'].apply(
            self.extract_size_range
        )
        
        # 6. Cores Category
        df['Cores_Category'] = df['No_of_Cores'].apply(
            self.extract_cores_category
        )
        
        # 7. Fire Rating
        df['Fire_Rating_Extracted'] = df.apply(
            lambda row: self.extract_fire_rating(
                row.get('Insulation_Type', ''),
                row.get('Product_Name', ''),
                row.get('Category', '')
            ),
            axis=1
        )
        
        # 8. Application Domain
        df['Application_Domain'] = df.apply(
            lambda row: self.extract_application_domain(
                row.get('Product_Name', ''),
                row.get('Category', ''),
                row.get('Is_Armoured', 0),
                row.get('Is_Industrial', 0)
            ),
            axis=1
        )
        
        # 9. Product Synonyms (all matching categories)
        df['Product_Category_Synonyms'] = df.apply(
            lambda row: '|'.join(self.extract_product_synonyms(
                row.get('Product_Name', ''),
                row.get('Category', ''),
                row.get('Insulation_Type', '')
            )) if len(self.extract_product_synonyms(
                row.get('Product_Name', ''),
                row.get('Category', ''),
                row.get('Insulation_Type', '')
            )) > 0 else 'general_purpose',
            axis=1
        )
        
        # 10. Matching Tags (searchable tags for RFP)
        df['RFP_Matching_Tags'] = df.apply(
            self.extract_matching_tags,
            axis=1
        )
        
        # 11. Combined Standard Specification
        df['Standard_Spec_String'] = df.apply(
            lambda row: f"{row.get('Voltage_Normalized', '')}_{row.get('Conductor_Material_Normalized', '')}_" +
                       f"{row.get('Insulation_Type_Normalized', '')}_" +
                       f"{row.get('Conductor_Size_Range', '')}_" +
                       f"{row.get('Cores_Category', '')}_" +
                       f"{row.get('Armour_Type_Normalized', '')}",
            axis=1
        )
        
        # 12. Current Capacity Range (for matching with RFP current requirements)
        df['Current_Capacity_Range'] = df.apply(
            lambda row: self._get_current_range(
                row.get('Current_Rating_Amps', 0),
                row.get('Conductor_Material_Normalized', '')
            ),
            axis=1
        )
        
        # 13. Temperature Class
        df['Temperature_Class'] = df['Max_Conductor_Temp_C'].apply(
            lambda x: self._get_temperature_class(x)
        )
        
        # 14. Cable Type Simplified
        df['Cable_Type_Simplified'] = df.apply(
            lambda row: self._simplify_cable_type(
                row.get('Product_Name', ''),
                row.get('Is_Armoured', 0),
                row.get('Is_Industrial', 0)
            ),
            axis=1
        )
        
        # 15. Cost Efficiency Rating
        df['Cost_Efficiency_Category'] = df.apply(
            lambda row: self._rate_cost_efficiency(
                row.get('Price_Per_Meter_INR', 0),
                row.get('Current_Rating_Amps', 0),
                row.get('Conductor_Size_sqmm', 0)
            ),
            axis=1
        )
        
        # 16. Compliance Level
        df['Compliance_Level'] = df.apply(
            lambda row: self._extract_compliance_level(
                row.get('Compliance_Standards', ''),
                row.get('Testing_Requirements', '')
            ),
            axis=1
        )
        
        # 17. OEM Name (for cross-OEM matching)
        df['OEM_Source'] = oem_name
        
        # 18. Product Uniqueness Signature (for deduplication)
        df['Product_Signature'] = df.apply(
            lambda row: self._generate_product_signature(row),
            axis=1
        )
        
        # 19. Matching Confidence Score
        df['Matching_Confidence'] = df.apply(
            lambda row: self._calculate_matching_confidence(row),
            axis=1
        )
        
        # 20. RFP Requirement Fit Score
        df['RFP_Fit_Score'] = df.apply(
            lambda row: self._calculate_rfp_fit(row),
            axis=1
        )
        
        return df
    
    def _get_current_range(self, current_rating, conductor_material):
        """Get current capacity range for matching"""
        try:
            current = float(current_rating) if current_rating else 0
            if current <= 0:
                return 'Unknown'
            elif current <= 20:
                return '≤20A'
            elif current <= 32:
                return '20-32A'
            elif current <= 63:
                return '32-63A'
            elif current <= 100:
                return '63-100A'
            elif current <= 160:
                return '100-160A'
            elif current <= 250:
                return '160-250A'
            else:
                return '>250A'
        except:
            return 'Unknown'
    
    def _get_temperature_class(self, max_temp):
        """Get temperature class from max temperature"""
        try:
            temp = float(max_temp) if max_temp else 0
            if temp <= 70:
                return 'Standard (70°C)'
            elif temp <= 90:
                return 'Enhanced (90°C)'
            elif temp <= 120:
                return 'High (120°C)'
            else:
                return 'Very High (>120°C)'
        except:
            return 'Unknown'
    
    def _simplify_cable_type(self, product_name, is_armoured, is_industrial):
        """Simplify cable type for easier matching"""
        text = str(product_name).lower()
        
        if is_armoured == 1 or 'armour' in text or 'swa' in text:
            return 'Armoured'
        elif 'submersible' in text or 'pump' in text:
            return 'Submersible'
        elif 'solar' in text or 'pv' in text:
            return 'Solar'
        elif 'underground' in text or 'buried' in text:
            return 'Underground'
        elif 'house' in text or 'domestic' in text:
            return 'House Wire'
        elif 'flexible' in text or 'stranded' in text:
            return 'Flexible'
        elif is_industrial == 1 or 'industrial' in text:
            return 'Industrial'
        elif 'control' in text or 'instrument' in text:
            return 'Control/Instrumentation'
        else:
            return 'Standard/General'
    
    def _rate_cost_efficiency(self, price_per_meter, current_rating, conductor_size):
        """Rate cost efficiency for matching budget-conscious RFPs"""
        try:
            price = float(price_per_meter) if price_per_meter else 0
            current = float(current_rating) if current_rating else 1
            size = float(conductor_size) if conductor_size else 1
            
            if price <= 0 or current <= 0:
                return 'Unknown'
            
            cost_per_ampere = price / current
            
            if cost_per_ampere < 2:
                return 'Very High Efficiency'
            elif cost_per_ampere < 5:
                return 'High Efficiency'
            elif cost_per_ampere < 10:
                return 'Moderate Efficiency'
            else:
                return 'Standard Efficiency'
        except:
            return 'Unknown'
    
    def _extract_compliance_level(self, compliance_standards, testing_requirements):
        """Extract compliance level from standards and testing"""
        text = f"{compliance_standards} {testing_requirements}".lower()
        
        if 'iso' in text and 'iec' in text:
            return 'International Grade'
        elif 'iec' in text or 'international' in text:
            return 'International'
        elif 'is' in text and 'indian' in text:
            return 'Indian Standard Grade'
        elif 'is' in text:
            return 'Indian Standard'
        elif 'type test' in text and 'routine test' in text:
            return 'Full Testing'
        elif 'type test' in text or 'routine test' in text:
            return 'Partial Testing'
        else:
            return 'Basic'
    
    def _generate_product_signature(self, row):
        """Generate unique product signature for matching/deduplication"""
        components = [
            str(row.get('Voltage_Normalized', 'UNK')),
            str(row.get('Conductor_Material_Normalized', 'UNK')),
            str(row.get('Insulation_Type_Normalized', 'UNK')),
            str(row.get('Conductor_Size_Range', 'UNK')),
            str(row.get('Cores_Category', 'UNK')),
            str(row.get('Armour_Type_Normalized', 'UNK')),
            str(row.get('Max_Conductor_Temp_C', '0'))
        ]
        return '|'.join(components)
    
    def _calculate_matching_confidence(self, row):
        """Calculate matching confidence score (0-100)"""
        score = 0
        checks = 0
        
        # Voltage normalized
        if row.get('Voltage_Normalized') != 'Unknown':
            score += 10
        checks += 10
        
        # Conductor material specified
        if row.get('Conductor_Material_Normalized') != 'Unknown':
            score += 10
        checks += 10
        
        # Insulation type specified
        if row.get('Insulation_Type_Normalized') != 'Unknown':
            score += 10
        checks += 10
        
        # Conductor size specified
        if row.get('Conductor_Size_Range') != 'Unknown':
            score += 10
        checks += 10
        
        # Cores specified
        if row.get('Cores_Category') != 'Unknown':
            score += 10
        checks += 10
        
        # Current rating specified
        if row.get('Current_Rating_Amps') and float(row.get('Current_Rating_Amps', 0)) > 0:
            score += 10
        checks += 10
        
        # Testing requirements specified
        if row.get('Testing_Requirements') and str(row.get('Testing_Requirements')).strip():
            score += 10
        checks += 10
        
        # Compliance standards specified
        if row.get('Compliance_Standards') and str(row.get('Compliance_Standards')).strip():
            score += 10
        checks += 10
        
        # Application domain identified
        if row.get('Application_Domain') != 'General Purpose':
            score += 5
        checks += 5
        
        # Fire rating specified
        if row.get('Fire_Rating_Extracted') != 'Not Specified':
            score += 5
        checks += 5
        
        return round((score / checks) * 100) if checks > 0 else 0
    
    def _calculate_rfp_fit(self, row):
        """Calculate RFP fit score (0-100)"""
        score = 0
        
        # Has testing requirements
        if row.get('Testing_Requirements') and str(row.get('Testing_Requirements')).strip():
            score += 15
        
        # Has compliance standards
        if row.get('Compliance_Standards') and str(row.get('Compliance_Standards')).strip():
            score += 15
        
        # Has complete specifications
        spec_fields = ['Voltage_Rating', 'Conductor_Material', 'Insulation_Type', 
                      'Conductor_Size_sqmm', 'No_of_Cores', 'Current_Rating_Amps']
        spec_count = sum(1 for field in spec_fields if row.get(field))
        score += (spec_count / len(spec_fields)) * 30
        
        # Has fire rating
        if row.get('Fire_Rating_Extracted') != 'Not Specified':
            score += 10
        
        # Has armour/protection
        if row.get('Is_Armoured') == 1:
            score += 10
        
        # Has product URL/documentation
        if row.get('Product_URL') and str(row.get('Product_URL')).strip():
            score += 5
        
        # Has warranty info
        if row.get('Warranty_Years') and float(row.get('Warranty_Years', 0)) > 0:
            score += 5
        
        return round(score)
    
    def process_csv_file(self, file_path, oem_name='Unknown'):
        """Process a single CSV file and add optimization columns"""
        try:
            print(f"Processing: {file_path}")
            df = pd.read_csv(file_path)
            
            print(f"  Initial rows: {len(df)}")
            print(f"  Initial columns: {len(df.columns)}")
            
            # Add optimization columns
            df = self.add_optimization_columns(df, oem_name)
            
            print(f"  Final columns: {len(df.columns)}")
            
            # Save optimized file
            base_path = Path(file_path).parent / Path(file_path).stem
            optimized_path = f"{base_path}_optimized_{self.timestamp}.csv"
            
            df.to_csv(optimized_path, index=False)
            print(f"  ✓ Saved: {optimized_path}")
            print(f"  ✓ New columns added: {len(df.columns) - 80} (est 20 columns)")
            
            return df, optimized_path
            
        except Exception as e:
            print(f"  ✗ Error processing {file_path}: {str(e)}")
            return None, None
    
    def process_all_files(self):
        """Process all CSV files in the dataset"""
        print("\n" + "="*80)
        print("RFP MATCHING OPTIMIZATION STARTED")
        print("="*80 + "\n")
        
        results = {}
        
        # Process marketplace files
        print("PROCESSING MARKETPLACE DATA:")
        print("-" * 80)
        for name, path in MARKETPLACE_PATHS.items():
            if os.path.exists(path):
                df, opt_path = self.process_csv_file(path, f'Moglix-{name}')
                if df is not None:
                    results[name] = (df, opt_path)
            else:
                print(f"  ✗ File not found: {path}")
        
        # Process OEM files
        print("\nPROCESSING OEM DATA:")
        print("-" * 80)
        for oem_name, oem_path in OEM_PATHS.items():
            print(f"\n{oem_name} ({oem_path}):")
            if os.path.exists(oem_path):
                csv_files = list(Path(oem_path).glob('*.csv'))
                for csv_file in csv_files:
                    df, opt_path = self.process_csv_file(str(csv_file), oem_name)
                    if df is not None:
                        results[f"{oem_name}_{csv_file.stem}"] = (df, opt_path)
            else:
                print(f"  ✗ Path not found: {oem_path}")
        
        print("\n" + "="*80)
        print(f"OPTIMIZATION COMPLETE - {len(results)} files processed")
        print("="*80 + "\n")
        
        # Print summary statistics
        print("SUMMARY STATISTICS:")
        print("-" * 80)
        for name, (df, path) in results.items():
            print(f"\n{name}:")
            print(f"  Total rows: {len(df)}")
            print(f"  Total columns: {len(df.columns)}")
            
            # Sample matching tags
            if 'RFP_Matching_Tags' in df.columns:
                sample_tags = df['RFP_Matching_Tags'].head(3).values
                print(f"  Sample matching tags: {sample_tags[0] if len(sample_tags) > 0 else 'N/A'}")
            
            # Matching confidence stats
            if 'Matching_Confidence' in df.columns:
                avg_confidence = df['Matching_Confidence'].mean()
                print(f"  Avg matching confidence: {avg_confidence:.1f}%")
            
            # RFP fit stats
            if 'RFP_Fit_Score' in df.columns:
                avg_fit = df['RFP_Fit_Score'].mean()
                print(f"  Avg RFP fit score: {avg_fit:.1f}/100")
        
        return results


def main():
    """Main entry point"""
    optimizer = RFPMatchingOptimizer()
    results = optimizer.process_all_files()
    
    print("\n✓ All files optimized successfully!")
    print(f"✓ Total files processed: {len(results)}")


if __name__ == '__main__':
    main()
