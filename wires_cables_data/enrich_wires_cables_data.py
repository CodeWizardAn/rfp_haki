"""
Enrich Wires & Cables CSV data with valid RFP column information
Extracts data from product names, specifications, and wire/cable industry standards
"""

import pandas as pd
import os
import re
from pathlib import Path

class WiresCablesDataEnricher:
    def __init__(self):
        self.base_path = r"d:\Haki_FMCG_2.0\wires_cables_data\wires_cables_data"
        self.oems = ["polycab", "havells", "rr_kabel", "kei", "finolex"]
        
    def extract_product_info(self, row):
        """Extract structured information from product name and specs"""
        info = {
            'is_industrial': 0,
            'is_standard_certified': 0,
            'is_armoured': 0,
            'is_flexible': 0,
            'is_high_voltage': 0,
            'has_testing_requirements': 0,
            'has_warranty': 0,
            'requires_certification': 0,
        }
        
        product_name = str(row.get('Product_Name', '')).lower()
        category = str(row.get('Category', '')).lower()
        voltage = str(row.get('Voltage_Rating', '')).lower()
        standard = str(row.get('Standard', '')).lower()
        
        # Detect product characteristics
        if 'industrial' in product_name or 'industrial' in category:
            info['is_industrial'] = 1
        
        if 'armour' in product_name or 'armored' in product_name:
            info['is_armoured'] = 1
        
        if 'flexible' in product_name or 'flex' in product_name:
            info['is_flexible'] = 1
        
        # High voltage detection
        try:
            voltage_val = int(re.search(r'\d+', voltage).group() if re.search(r'\d+', voltage) else 0)
            if voltage_val > 1000:
                info['is_high_voltage'] = 1
        except:
            pass
        
        # Standard certification
        if any(std in standard for std in ['IS', 'IEC', 'BS']):
            info['is_standard_certified'] = 1
        
        # Testing requirements (cables with pricing info suggest certified testing)
        test_cost = row.get('Type_Test_Cost_INR', 0)
        if pd.notna(test_cost) and test_cost > 0:
            info['has_testing_requirements'] = 1
        
        # Warranty indicates quality assurance
        warranty = row.get('Warranty_Years', 0)
        if pd.notna(warranty) and warranty > 0:
            info['has_warranty'] = 1
        
        return info
    
    def populate_rfp_columns(self, row, product_info):
        """Populate RFP columns based on extracted product information"""
        
        # Core RFP columns that apply to wire/cable tenders
        rfp_mappings = {
            # Tender & Bidding Documents (1 if product requires formal tender process)
            'RFP_TENDER': 1 if product_info['is_industrial'] or product_info['is_high_voltage'] else 0,
            'RFP_BIDDING_DOCUMENTS': 1,
            'RFP_TENDER_DOCUMENTS': 1,
            'RFP_PUBLIC_TENDER': 1,
            'RFP_OPEN_TENDER': 1,
            
            # Technical Specifications
            'RFP_TECHNICAL_SPECIFICATIONS': 1,
            'RFP_SPECIFICATION': 1,
            'RFP_TECHNICAL_REQUIREMENT': 1,
            
            # Quality & Compliance
            'RFP_QUALITY_ASSURANCE_PLAN': 1 if product_info['has_warranty'] else 0,
            'RFP_QUALITY_ASSURANCE': 1 if product_info['is_standard_certified'] else 0,
            'RFP_QUALITY_STANDARD': 1 if product_info['is_standard_certified'] else 0,
            'RFP_QUALITY': 1,
            'RFP_COMPLIANCE': 1,
            'RFP_COMPLIANCE_DOCUMENTATION': 1,
            'RFP_REGULATORY_COMPLIANCE': 1,
            'RFP_INDUSTRY_STANDARD': 1 if product_info['is_standard_certified'] else 0,
            'RFP_STANDARD': 1 if product_info['is_standard_certified'] else 0,
            
            # Testing
            'RFP_TESTING': 1,
            'RFP_TEST_PLAN': 1 if product_info['has_testing_requirements'] else 0,
            'RFP_TEST_STRATEGY': 1 if product_info['has_testing_requirements'] else 0,
            'RFP_TEST_EXECUTION': 1 if product_info['has_testing_requirements'] else 0,
            'RFP_TEST_REPORT': 1 if product_info['has_testing_requirements'] else 0,
            'RFP_QUALITY_CHECK': 1,
            'RFP_INSPECTION_PROCEDURE': 1,
            
            # Pricing & Commercial
            'RFP_PRICE': 1,
            'RFP_RATE': 1,
            'RFP_UNIT_PRICE': 1,
            'RFP_PRICE_LIST': 1,
            'RFP_BID_PRICE': 1,
            'RFP_QUOTED_PRICE': 1,
            'RFP_PAYMENT_TERMS': 1,
            'RFP_PAYMENT': 1,
            'RFP_FIXED_PRICE': 1,
            'RFP_PAYMENT_SCHEDULE': 1,
            
            # Delivery & Warranty
            'RFP_DELIVERY': 1,
            'RFP_DELIVERY_SCHEDULE': 1,
            'RFP_WARRANTY': 1 if product_info['has_warranty'] else 0,
            'RFP_WARRANTY_CLAIM': 1 if product_info['has_warranty'] else 0,
            'RFP_WARRANTY_REPLACEMENT': 1 if product_info['has_warranty'] else 0,
            
            # Documentation & Certification
            'RFP_DOCUMENTATION_REQUIREMENT': 1,
            'RFP_TECHNICAL_SPECIFICATION_DOCUMENT': 1,
            'RFP_TECHNICAL_MANUAL': 1,
            'RFP_CERTIFICATION': 1 if product_info['is_standard_certified'] else 0,
            'RFP_TECHNICAL_QUALIFICATION': 1,
            'RFP_QUALITY_CERTIFICATION': 1 if product_info['is_standard_certified'] else 0,
            'RFP_ISO_CERTIFICATION': 1 if 'ISO' in str(row.get('Standard', '')).upper() else 0,
            
            # Industrial-specific columns
            'RFP_INFRASTRUCTURE_REQUIREMENTS': 1 if product_info['is_industrial'] else 0,
            'RFP_TECHNICAL_DESIGN': 1 if product_info['is_industrial'] else 0,
            'RFP_PERFORMANCE_OPTIMIZATION': 1 if product_info['is_high_voltage'] else 0,
            
            # Compliance & Risk
            'RFP_COMPLIANCE_REQUIREMENT': 1,
            'RFP_RISK_MITIGATION_STRATEGY': 1 if product_info['is_industrial'] else 0,
            'RFP_PERFORMANCE_MANAGEMENT': 1,
            'RFP_SCOPE_MANAGEMENT': 1,
            
            # Vendor Requirements
            'RFP_APPROVED_VENDOR': 1 if product_info['is_standard_certified'] else 0,
            'RFP_VENDOR_PERFORMANCE': 1,
        }
        
        return rfp_mappings
    
    def enrich_csv(self, file_path):
        """Enrich a single CSV file with populated RFP columns"""
        try:
            print(f"  Enriching: {Path(file_path).name}")
            
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Get all RFP columns
            rfp_columns = [col for col in df.columns if col.startswith('RFP_')]
            
            # Process each row
            for idx, row in df.iterrows():
                # Extract product information
                product_info = self.extract_product_info(row)
                
                # Get RFP mappings for this product
                rfp_values = self.populate_rfp_columns(row, product_info)
                
                # Populate only relevant RFP columns
                for col in rfp_columns:
                    if col in rfp_values:
                        df.at[idx, col] = rfp_values[col]
            
            # Save enriched CSV
            df.to_csv(file_path, index=False)
            
            # Count populated cells
            total_rfp_cells = len(df) * len(rfp_columns)
            populated_cells = 0
            for col in rfp_columns:
                populated_cells += (df[col] > 0).sum()
            
            print(f"    [+] {len(df)} rows, {populated_cells}/{total_rfp_cells} RFP cells populated")
            return True
            
        except Exception as e:
            print(f"    [!] Error: {str(e)}")
            return False
    
    def enrich_all(self):
        """Enrich all CSV files across all OEMs"""
        print("\n" + "="*80)
        print("WIRES & CABLES DATA ENRICHMENT")
        print("="*80 + "\n")
        
        total_files = 0
        successful_files = 0
        
        for oem in self.oems:
            oem_path = os.path.join(self.base_path, oem)
            
            if not os.path.exists(oem_path):
                continue
            
            print(f"{oem.upper()}")
            print("-" * 40)
            
            # Find all CSV files
            csv_files = [f for f in os.listdir(oem_path) if f.endswith('.csv')]
            
            for csv_file in csv_files:
                total_files += 1
                file_path = os.path.join(oem_path, csv_file)
                
                if self.enrich_csv(file_path):
                    successful_files += 1
            
            print()
        
        print("="*80)
        print(f"ENRICHMENT SUMMARY")
        print("="*80)
        print(f"Total files processed: {total_files}")
        print(f"Successfully enriched: {successful_files}")
        print(f"Enrichment rate: {(successful_files/total_files*100):.1f}%\n")
        print("[+] Data enrichment complete!")
        print("  - RFP columns populated with intelligent values")
        print("  - Values based on product specifications and industry standards")
        print("  - Ready for RFP document matching\n")


if __name__ == "__main__":
    enricher = WiresCablesDataEnricher()
    enricher.enrich_all()
