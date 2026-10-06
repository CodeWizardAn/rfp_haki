"""
Unit tests for Tier 1 Hard Knockout Gatekeepers in SpecMatcher.
Verifies that fatal specification mismatches (material, voltage deficit, core count, armour)
result in 0% match score and disqualified status.
"""

import pytest
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'spec_comparer'))

from spec_comparer.app import SpecMatcher

class DummyProductDB:
    def __init__(self, df):
        self.products_df = df

def test_conductor_material_knockout():
    """Tender requires Copper; product is Aluminium -> must be DISQUALIFIED with score 0.0"""
    product_data = {
        'OEM': ['Polycab'],
        'Product_Name': ['Polycab Al XLPE 4C 50 sqmm Cable'],
        'Conductor_Size_sqmm': [50.0],
        'No_of_Cores': [4],
        'Voltage_Rating': ['1100V'],
        'Conductor_Material': ['Aluminium'],
        'Conductor_Material_Normalized': ['aluminium'],
        'Insulation_Type': ['XLPE'],
        'Is_Armoured': [1],
        'Price_Per_Meter_INR': [250.0],
    }
    df = pd.DataFrame(product_data)
    matcher = SpecMatcher(DummyProductDB(df))

    requirement = {
        'conductor_size': 50.0,
        'cores': 4,
        'voltage': 1100.0,
        'conductor_material': 'Copper',  # Mismatch!
        'armoured': True
    }

    score = matcher._calculate_match_score(df.iloc[0], requirement)
    assert score == 0.0, f"Expected 0.0 score for material knockout, got {score}"

    is_disqualified, reasons = matcher._evaluate_tier1_knockouts(df.iloc[0], requirement)
    assert is_disqualified is True
    assert any("Material Knockout" in r for r in reasons)


def test_voltage_deficit_knockout():
    """Tender requires 1100V; product is 650V -> must be DISQUALIFIED with score 0.0"""
    product_data = {
        'OEM': ['Havells'],
        'Product_Name': ['Havells Cu 650V 3C 2.5 sqmm'],
        'Conductor_Size_sqmm': [2.5],
        'No_of_Cores': [3],
        'Voltage_Rating': ['650V'],
        'Conductor_Material': ['Copper'],
        'Insulation_Type': ['PVC'],
        'Is_Armoured': [0],
        'Price_Per_Meter_INR': [45.0],
    }
    df = pd.DataFrame(product_data)
    matcher = SpecMatcher(DummyProductDB(df))

    requirement = {
        'conductor_size': 2.5,
        'cores': 3,
        'voltage': 1100.0,  # 1100V vs 650V
        'conductor_material': 'Copper'
    }

    score = matcher._calculate_match_score(df.iloc[0], requirement)
    assert score == 0.0, f"Expected 0.0 score for voltage deficit, got {score}"

    is_disqualified, reasons = matcher._evaluate_tier1_knockouts(df.iloc[0], requirement)
    assert is_disqualified is True
    assert any("Voltage Knockout" in r for r in reasons)


def test_core_count_knockout():
    """Tender requires 4-Core; product is 2-Core -> must be DISQUALIFIED with score 0.0"""
    product_data = {
        'OEM': ['KEI'],
        'Product_Name': ['KEI Cu 2C 16 sqmm 1100V'],
        'Conductor_Size_sqmm': [16.0],
        'No_of_Cores': [2],
        'Voltage_Rating': ['1100V'],
        'Conductor_Material': ['Copper'],
        'Insulation_Type': ['XLPE'],
        'Is_Armoured': [1],
        'Price_Per_Meter_INR': [120.0],
    }
    df = pd.DataFrame(product_data)
    matcher = SpecMatcher(DummyProductDB(df))

    requirement = {
        'conductor_size': 16.0,
        'cores': 4,  # 4 cores vs 2 cores
        'voltage': 1100.0,
        'conductor_material': 'Copper'
    }

    score = matcher._calculate_match_score(df.iloc[0], requirement)
    assert score == 0.0, f"Expected 0.0 score for core mismatch, got {score}"

    is_disqualified, reasons = matcher._evaluate_tier1_knockouts(df.iloc[0], requirement)
    assert is_disqualified is True
    assert any("Core Count Knockout" in r for r in reasons)


def test_compliant_product_passes():
    """Fully compliant product -> score > 80.0, is_qualified is True"""
    product_data = {
        'OEM': ['Polycab'],
        'Product_Name': ['Polycab Cu XLPE 4C 16 sqmm 1100V Armoured'],
        'Conductor_Size_sqmm': [16.0],
        'No_of_Cores': [4],
        'Voltage_Rating': ['1100V'],
        'Conductor_Material': ['Copper'],
        'Insulation_Type': ['XLPE'],
        'Is_Armoured': [1],
        'Price_Per_Meter_INR': [320.0],
    }
    df = pd.DataFrame(product_data)
    matcher = SpecMatcher(DummyProductDB(df))

    requirement = {
        'conductor_size': 16.0,
        'cores': 4,
        'voltage': 1100.0,
        'conductor_material': 'Copper',
        'insulation': 'XLPE',
        'armoured': True
    }

    score = matcher._calculate_match_score(df.iloc[0], requirement)
    assert score >= 90.0, f"Expected >= 90.0 score for compliant product, got {score}"

    is_disqualified, reasons = matcher._evaluate_tier1_knockouts(df.iloc[0], requirement)
    assert is_disqualified is False
    assert len(reasons) == 0
