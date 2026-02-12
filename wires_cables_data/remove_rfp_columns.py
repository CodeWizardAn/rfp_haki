#!/usr/bin/env python3
"""
Remove 239 RFP indicator columns from all enriched CSV files.
Keep only original product columns + 7 new enriched data columns.
"""

import os
import pandas as pd
from pathlib import Path

# Columns to keep (original 29 + 7 enriched)
COLUMNS_TO_KEEP = [
    'Company', 'Product_Code', 'Product_Name', 'Category', 'Type',
    'Voltage_Rating', 'Conductor_Material', 'Conductor_Size_sqmm', 'No_of_Cores',
    'Conductor_Class', 'Insulation_Type', 'Insulation_Thickness_mm', 'Armour_Type',
    'Outer_Diameter_mm', 'Approx_Weight_kg_per_km', 'Standard', 'Max_Conductor_Temp_C',
    'Current_Rating_Amps', 'Price_Per_Meter_INR', 'Price_Per_90m_INR', 'Price_Per_100m_INR',
    'Price_Per_180m_INR', 'Test_Certificate_Cost_INR', 'Routine_Test_Cost_INR',
    'Type_Test_Cost_INR', 'HSN_Code', 'Warranty_Years', 'Product_URL', 'Extracted_Date',
    # 7 Enriched columns
    'Testing_Requirements', 'Compliance_Standards', 'Product_Category',
    'Is_Armoured', 'Is_Industrial', 'Is_Flexible', 'Calculated_Price_Per_Meter'
]

OEM_PATHS = {
    'POLYCAB': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/polycab',
    'HAVELLS': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/havells',
    'RR_KABEL': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/rr_kabel',
    'KEI': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/kei',
    'FINOLEX': 'd:/Haki_FMCG_2.0/wires_cables_data/wires_cables_data/finolex'
}

print("=" * 80)
print("REMOVING RFP INDICATOR COLUMNS FROM ALL CSV FILES")
print("=" * 80)

total_files = 0
total_removed = 0

for oem, path in OEM_PATHS.items():
    print(f"\n{oem}")
    print("-" * 40)
    
    if not os.path.exists(path):
        print(f"  [!] Path not found: {path}")
        continue
    
    csv_files = list(Path(path).glob('*.csv'))
    if not csv_files:
        print(f"  [!] No CSV files found")
        continue
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(str(csv_file))
            original_cols = len(df.columns)
            
            # Keep only specified columns (if they exist in file)
            cols_to_keep = [col for col in COLUMNS_TO_KEEP if col in df.columns]
            df = df[cols_to_keep]
            
            removed_cols = original_cols - len(df.columns)
            
            # Save the file
            df.to_csv(str(csv_file), index=False)
            
            print(f"  ✓ {csv_file.name}")
            print(f"      Columns: {original_cols} → {len(df.columns)} (removed {removed_cols})")
            print(f"      Products: {len(df)}")
            
            total_files += 1
            total_removed += removed_cols
            
        except Exception as e:
            print(f"  [!] Error processing {csv_file.name}: {str(e)}")

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)
print(f"\nFiles processed: {total_files}")
print(f"Total RFP columns removed: {total_removed}")
print(f"Columns remaining per file: {len(COLUMNS_TO_KEEP)}")
print(f"\nRetained columns:")
for col in COLUMNS_TO_KEEP:
    print(f"  - {col}")
