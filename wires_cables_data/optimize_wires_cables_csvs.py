"""
Optimize Wires & Cables CSVs with RFP-Relevant Columns
Adds 500+ RFP terms as columns for future matching in RFP documents
"""

import pandas as pd
import os
import glob
import sys
from datetime import datetime
import re

# Add pdf_extraction to path to access expanded terms
sys.path.insert(0, 'd:/Haki_FMCG_2.0/pdf_extraction')
from expanded_terms import ENGLISH_EXPANDED_TERMS

class WiresCablesOptimizer:
    """Optimize wires and cables CSVs with RFP-relevant columns"""
    
    def __init__(self):
        self.base_path = 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data'
        self.oems = ['polycab', 'havells', 'rr_kabel', 'kei', 'finolex']
        self.rfp_terms = self._extract_rfp_terms()
        self.processed_files = 0
        self.optimized_files = 0
        
    def _extract_rfp_terms(self):
        """Extract all relevant RFP terms for wires and cables"""
        all_terms = []
        
        for category, terms in ENGLISH_EXPANDED_TERMS.items():
            for term in terms:
                all_terms.append(term)
        
        # Filter to ~500 most relevant terms for wires/cables
        wire_cable_keywords = [
            'wire', 'cable', 'conductor', 'insulation', 'voltage', 'rating', 'ampere',
            'standard', 'test', 'certificate', 'quality', 'price', 'delivery', 'warranty',
            'specification', 'material', 'performance', 'certification', 'compliance',
            'safety', 'environmental', 'requirement', 'technical', 'commercial', 'scope',
            'bidding', 'tender', 'supply', 'quantity', 'rate', 'terms', 'condition',
            'payment', 'gst', 'tax', 'transport', 'weight', 'dimension', 'approved',
            'inspection', 'testing', 'validation', 'verification', 'approval',
            'core', 'armor', 'armour', 'sheath', 'jacket', 'duct', 'tray', 'conduit'
        ]
        
        relevant_terms = []
        for term in all_terms:
            term_lower = term.lower()
            for keyword in wire_cable_keywords:
                if keyword in term_lower:
                    relevant_terms.append(term)
                    break
        
        # Limit to top 500 and remove duplicates
        relevant_terms = list(dict.fromkeys(relevant_terms))[:500]
        return relevant_terms
    
    def _get_csv_files_for_oem(self, oem):
        """Get all relevant CSV files for an OEM"""
        oem_path = os.path.join(self.base_path, oem)
        
        csv_files = []
        
        # Get main CSV files
        if os.path.exists(oem_path):
            for csv_file in glob.glob(os.path.join(oem_path, f'{oem}_*.csv')):
                # Skip if it contains 'summary' or is in subdirectories
                if '_summary' not in csv_file:
                    csv_files.append(csv_file)
        
        return csv_files
    
    def _add_rfp_term_columns(self, df):
        """Add RFP term columns to dataframe"""
        # Combine all text columns for searching
        text_columns = df.select_dtypes(include=['object']).columns
        
        for term in self.rfp_terms:
            column_name = f'RFP_{term.upper().replace(" ", "_").replace("-", "_")}'
            
            # Create a binary indicator for each term
            df[column_name] = 0
            
            # Check if term appears in any text column
            for text_col in text_columns:
                mask = df[text_col].astype(str).str.lower().str.contains(
                    re.escape(term.lower()), 
                    case=False, 
                    regex=True, 
                    na=False
                )
                df.loc[mask, column_name] = 1
        
        return df
    
    def _optimize_csv(self, csv_file):
        """Optimize a single CSV file"""
        try:
            print(f"  Processing: {os.path.basename(csv_file)}")
            
            # Read CSV
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # Add RFP term columns
            print(f"    Adding {len(self.rfp_terms)} RFP term columns...")
            df = self._add_rfp_term_columns(df)
            
            # Save to temporary file
            temp_file = csv_file + '.temp'
            df.to_csv(temp_file, index=False, encoding='utf-8')
            
            # Remove old file and rename temp
            os.remove(csv_file)
            os.rename(temp_file, csv_file)
            
            print(f"    Optimized! New shape: {df.shape} ({len(self.rfp_terms)} new columns)")
            self.optimized_files += 1
            
            return True
            
        except Exception as e:
            print(f"    ERROR: {str(e)}")
            return False
    
    def optimize_all(self):
        """Optimize all wires and cables CSVs"""
        print("\n" + "="*80)
        print("WIRES & CABLES CSV OPTIMIZATION")
        print("="*80)
        print(f"\nRFP Terms Available: {len(self.rfp_terms)}")
        print(f"OEMs to Process: {', '.join(self.oems)}")
        
        total_start_time = datetime.now()
        
        for oem in self.oems:
            print(f"\n{oem.upper()}")
            print("-" * 40)
            
            csv_files = self._get_csv_files_for_oem(oem)
            
            if not csv_files:
                print(f"  No CSV files found for {oem}")
                continue
            
            for csv_file in csv_files:
                self.processed_files += 1
                self._optimize_csv(csv_file)
        
        # Print summary
        total_time = (datetime.now() - total_start_time).total_seconds()
        
        print("\n" + "="*80)
        print("OPTIMIZATION SUMMARY")
        print("="*80)
        print(f"Total files processed: {self.processed_files}")
        print(f"Successfully optimized: {self.optimized_files}")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"RFP terms added per file: {len(self.rfp_terms)}")
        print("\nOptimization complete! CSVs now include:")
        print(f"  - Original product columns")
        print(f"  - {len(self.rfp_terms)} RFP term indicator columns (binary)")
        print(f"  - Ready for RFP matching and analysis")
        print("="*80 + "\n")
        
        return self.optimized_files == self.processed_files

if __name__ == '__main__':
    optimizer = WiresCablesOptimizer()
    success = optimizer.optimize_all()
    sys.exit(0 if success else 1)
