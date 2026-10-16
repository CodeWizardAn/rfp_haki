"""
Spec Comparer Pro - RFP Product Specification Matching System
Compares RFP requirements against OEM wire/cable products
Returns Top 3 matching products with scoring, calculations, and recommendations
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import re
import json
import math
import glob
import sys
from typing import Dict, List, Any, Tuple, Optional
from difflib import SequenceMatcher
import logging

# Performance Integration
try:
    perf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from performance.integration import integrate_flask_app, init_performance
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    print(f"Performance integration not available: {e}")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Performance System
if PERFORMANCE_AVAILABLE:
    try:
        integrate_flask_app(app)
        logger.info("✅ Performance system integrated")
    except Exception as e:
        logger.warning(f"Performance integration failed: {e}")

# Create uploads folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# OEM Data paths
OEM_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             'wires_cables_data', 'wires_cables_data')

# Key specification columns for matching
SPEC_COLUMNS = [
    'Conductor_Size_sqmm', 'No_of_Cores', 'Voltage_Rating', 'Conductor_Material',
    'Insulation_Type', 'Armour_Type', 'Standard', 'Current_Rating_Amps',
    'Max_Conductor_Temp_C', 'Fire_Rating', 'Is_Armoured', 'Is_Flexible'
]

# Scoring weights for different specs
SCORING_WEIGHTS = {
    'Conductor_Size_sqmm': 25,      # Most critical
    'No_of_Cores': 20,              # Very important
    'Voltage_Rating': 15,           # Important
    'Conductor_Material': 10,       # Material match
    'Insulation_Type': 10,          # Insulation type
    'Current_Rating_Amps': 8,       # Current capacity
    'Standard': 5,                  # Standard compliance
    'Fire_Rating': 4,               # Fire safety
    'Is_Armoured': 3,               # Armour requirement
}


class SpecCalculator:
    """
    Electrical Cable Specification Calculator
    Based on IS 3961 / IEC 60364-5-52 standards
    """
    
    # Current carrying capacity tables (IS 3961 / IEC 60364-5-52)
    CURRENT_CAPACITY = {
        'copper': {
            1.0: {'single': 15, 'multi': 11},
            1.5: {'single': 19, 'multi': 14},
            2.5: {'single': 27, 'multi': 19},
            4.0: {'single': 36, 'multi': 26},
            6.0: {'single': 46, 'multi': 34},
            10.0: {'single': 63, 'multi': 46},
            16.0: {'single': 85, 'multi': 62},
            25.0: {'single': 112, 'multi': 80},
            35.0: {'single': 138, 'multi': 99},
            50.0: {'single': 168, 'multi': 119},
            70.0: {'single': 213, 'multi': 151},
            95.0: {'single': 258, 'multi': 182},
            120.0: {'single': 299, 'multi': 210},
            150.0: {'single': 344, 'multi': 240},
            185.0: {'single': 392, 'multi': 273},
            240.0: {'single': 461, 'multi': 321},
            300.0: {'single': 530, 'multi': 367},
            400.0: {'single': 634, 'multi': 438},
            500.0: {'single': 745, 'multi': 514},
            630.0: {'single': 873, 'multi': 599},
        },
        'aluminum': {
            2.5: {'single': 21, 'multi': 15},
            4.0: {'single': 28, 'multi': 20},
            6.0: {'single': 36, 'multi': 26},
            10.0: {'single': 49, 'multi': 36},
            16.0: {'single': 66, 'multi': 48},
            25.0: {'single': 83, 'multi': 62},
            35.0: {'single': 103, 'multi': 77},
            50.0: {'single': 125, 'multi': 92},
            70.0: {'single': 160, 'multi': 117},
            95.0: {'single': 195, 'multi': 141},
            120.0: {'single': 226, 'multi': 163},
            150.0: {'single': 261, 'multi': 186},
            185.0: {'single': 298, 'multi': 212},
            240.0: {'single': 352, 'multi': 250},
            300.0: {'single': 406, 'multi': 287},
            400.0: {'single': 486, 'multi': 342},
            500.0: {'single': 571, 'multi': 400},
            630.0: {'single': 671, 'multi': 469},
        }
    }
    
    # Derating factors for ambient temperature (base 30°C for PVC, 40°C for XLPE)
    TEMP_DERATING = {
        'PVC': {25: 1.06, 30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61},
        'XLPE': {25: 1.07, 30: 1.04, 35: 1.00, 40: 0.96, 45: 0.91, 50: 0.87, 55: 0.82}
    }
    
    # Grouping derating factors
    GROUPING_DERATING = {
        1: 1.00, 2: 0.88, 3: 0.82, 4: 0.77, 5: 0.75,
        6: 0.72, 7: 0.70, 8: 0.68, 9: 0.66, 10: 0.64,
        12: 0.61, 14: 0.59, 16: 0.57, 18: 0.55, 20: 0.53
    }
    
    # Installation method factors
    INSTALLATION_FACTORS = {
        'conduit_wall': 0.87,
        'conduit_air': 0.95,
        'tray_touching': 0.85,
        'tray_spaced': 1.00,
        'ladder': 1.00,
        'direct_buried': 0.80,
        'duct': 0.85,
        'free_air': 1.00
    }
    
    # Resistivity values (Ω·mm²/m at 20°C)
    RESISTIVITY = {
        'copper': 0.0178,
        'aluminum': 0.0283
    }
    
    # Temperature coefficient
    TEMP_COEFFICIENT = {
        'copper': 0.00393,
        'aluminum': 0.00403
    }
    
    def calculate_cable_sizing(self, load_current: float, voltage: float,
                              material: str = 'copper',
                              installation: str = 'tray_spaced',
                              ambient_temp: int = 40,
                              cable_grouping: int = 1,
                              safety_factor: float = 1.25) -> Dict:
        """Calculate recommended cable size for given load"""
        material = material.lower()
        required_capacity = load_current * safety_factor
        
        # Get derating factors
        insulation = 'XLPE' if ambient_temp > 45 else 'PVC'
        temp_factor = self._get_temp_derating(ambient_temp, insulation)
        group_factor = self._get_grouping_derating(cable_grouping)
        install_factor = self.INSTALLATION_FACTORS.get(installation, 1.0)
        
        total_derating = temp_factor * group_factor * install_factor
        
        # Find suitable cable size
        cable_type = 'multi' if cable_grouping > 1 else 'single'
        capacity_table = self.CURRENT_CAPACITY.get(material, self.CURRENT_CAPACITY['copper'])
        
        recommended_size = None
        for size, capacities in sorted(capacity_table.items()):
            derated_capacity = capacities[cable_type] * total_derating
            if derated_capacity >= required_capacity:
                recommended_size = size
                break
        
        if recommended_size is None:
            recommended_size = max(capacity_table.keys())
        
        return {
            'calculation_type': 'cable_sizing',
            'input': {
                'load_current': load_current,
                'voltage': voltage,
                'material': material,
                'installation': installation,
                'ambient_temp': ambient_temp,
                'cable_grouping': cable_grouping,
                'safety_factor': safety_factor
            },
            'derating_factors': {
                'temperature': round(temp_factor, 3),
                'grouping': round(group_factor, 3),
                'installation': round(install_factor, 3),
                'total': round(total_derating, 3)
            },
            'calculation': {
                'required_capacity': round(required_capacity, 2),
                'recommended_size_sqmm': recommended_size,
                'base_capacity': capacity_table[recommended_size][cable_type],
                'derated_capacity': round(capacity_table[recommended_size][cable_type] * total_derating, 2)
            }
        }
    
    def calculate_voltage_drop(self, cable_size: float, length: float,
                              current: float, material: str = 'copper',
                              voltage: float = 415, power_factor: float = 0.85,
                              cores: int = 3) -> Dict:
        """Calculate voltage drop for given cable run"""
        material = material.lower()
        
        # Get resistivity and calculate resistance
        resistivity = self.RESISTIVITY.get(material, 0.0178)
        operating_temp = 70  # Typical operating temp
        temp_factor = 1 + self.TEMP_COEFFICIENT.get(material, 0.00393) * (operating_temp - 20)
        resistance = (resistivity * temp_factor * length) / cable_size
        
        # Approximate reactance (mΩ/m) - simplified
        reactance = 0.08 * length / 1000  # Approximate for most cables
        
        # Calculate voltage drop (single phase vs three phase)
        if cores == 1 or cores == 2:
            # Single phase: Vd = 2 * I * (R*cosφ + X*sinφ)
            sin_phi = math.sqrt(1 - power_factor**2)
            vd = 2 * current * (resistance * power_factor + reactance * sin_phi)
        else:
            # Three phase: Vd = √3 * I * (R*cosφ + X*sinφ)
            sin_phi = math.sqrt(1 - power_factor**2)
            vd = math.sqrt(3) * current * (resistance * power_factor + reactance * sin_phi)
        
        vd_percent = (vd / voltage) * 100
        
        # Assessment
        if vd_percent <= 2:
            assessment = "Excellent"
        elif vd_percent <= 3:
            assessment = "Good"
        elif vd_percent <= 5:
            assessment = "Acceptable"
        else:
            assessment = "Exceeds Limit"
        
        return {
            'calculation_type': 'voltage_drop',
            'input': {
                'cable_size': cable_size,
                'length': length,
                'current': current,
                'material': material,
                'voltage': voltage,
                'power_factor': power_factor,
                'cores': cores
            },
            'calculation': {
                'resistance_per_km': round(resistivity * temp_factor * 1000 / cable_size, 4),
                'total_resistance': round(resistance, 4),
                'voltage_drop_volts': round(vd, 2),
                'voltage_drop_percent': round(vd_percent, 2),
                'assessment': assessment
            },
            'standards': {
                'max_allowed_feeder': 3.0,
                'max_allowed_branch': 5.0,
                'compliant_feeder': vd_percent <= 3.0,
                'compliant_branch': vd_percent <= 5.0
            }
        }
    
    def calculate_short_circuit_capacity(self, cable_size: float,
                                        material: str = 'copper',
                                        fault_duration: float = 1.0) -> Dict:
        """Calculate short circuit withstand capacity"""
        material = material.lower()
        
        # K factor (thermal constant) - A²s/mm⁴
        k_factors = {
            'copper': {'PVC': 115, 'XLPE': 143},
            'aluminum': {'PVC': 76, 'XLPE': 94}
        }
        
        k = k_factors.get(material, k_factors['copper'])['XLPE']
        
        # Short circuit capacity: I = K * A / √t
        i_sc = (k * cable_size) / math.sqrt(fault_duration)
        i_sc_ka = i_sc / 1000
        
        # I²t rating
        i2t = (i_sc ** 2) * fault_duration
        
        return {
            'calculation_type': 'short_circuit',
            'input': {
                'cable_size': cable_size,
                'material': material,
                'fault_duration': fault_duration
            },
            'calculation': {
                'k_factor': k,
                'withstand_current_1s_kA': round(i_sc_ka, 2),
                'withstand_current_actual_kA': round(i_sc_ka * math.sqrt(1/fault_duration), 2) if fault_duration != 1 else round(i_sc_ka, 2),
                'i2t_rating': round(i2t, 0)
            }
        }
    
    def calculate_power_capacity(self, cable_size: float, voltage: float = 415,
                                material: str = 'copper', cores: int = 3,
                                power_factor: float = 0.85,
                                installation: str = 'tray_spaced') -> Dict:
        """Calculate power capacity of a cable"""
        material = material.lower()
        
        capacity_table = self.CURRENT_CAPACITY.get(material, self.CURRENT_CAPACITY['copper'])
        base_current = capacity_table.get(cable_size, {}).get('multi', 0)
        
        install_factor = self.INSTALLATION_FACTORS.get(installation, 1.0)
        derated_current = base_current * install_factor
        
        if cores == 1 or cores == 2:
            power_kw = (voltage * derated_current * power_factor) / 1000
            power_kva = (voltage * derated_current) / 1000
        else:
            power_kw = (math.sqrt(3) * voltage * derated_current * power_factor) / 1000
            power_kva = (math.sqrt(3) * voltage * derated_current) / 1000
        
        return {
            'calculation_type': 'power_capacity',
            'input': {
                'cable_size': cable_size,
                'voltage': voltage,
                'material': material,
                'cores': cores,
                'power_factor': power_factor,
                'installation': installation
            },
            'calculation': {
                'base_current_capacity': base_current,
                'installation_factor': install_factor,
                'derated_current_capacity': round(derated_current, 2),
                'power_capacity_kW': round(power_kw, 2),
                'power_capacity_kVA': round(power_kva, 2)
            }
        }
    
    def _get_temp_derating(self, temp: int, insulation: str) -> float:
        factors = self.TEMP_DERATING.get(insulation, self.TEMP_DERATING['PVC'])
        if temp in factors:
            return factors[temp]
        temps = sorted(factors.keys())
        for i, t in enumerate(temps):
            if t > temp:
                if i == 0:
                    return factors[temps[0]]
                t1, t2 = temps[i-1], t
                return factors[t1] + (factors[t2] - factors[t1]) * (temp - t1) / (t2 - t1)
        return factors[temps[-1]]
    
    def _get_grouping_derating(self, num_cables: int) -> float:
        if num_cables in self.GROUPING_DERATING:
            return self.GROUPING_DERATING[num_cables]
        cables = sorted(self.GROUPING_DERATING.keys())
        for i, n in enumerate(cables):
            if n > num_cables:
                if i == 0:
                    return 1.0
                return self.GROUPING_DERATING[cables[i-1]]
        return self.GROUPING_DERATING[cables[-1]]
    
    def calculate_testing_costs(self, cable_size: float, voltage_class: str = 'LT',
                               cable_type: str = 'power', is_armoured: bool = False,
                               quantity_meters: float = 1000, num_samples: int = 3) -> Dict:
        """
        Calculate comprehensive testing costs for cable procurement
        Based on IS/IEC testing standards
        """
        # Base costs for different test types (INR)
        base_costs = {
            'routine_tests': {
                'LT': {'base': 2500, 'per_sample': 500},
                'HT': {'base': 8000, 'per_sample': 1500},
                'EHV': {'base': 25000, 'per_sample': 5000}
            },
            'type_tests': {
                'LT': {'base': 15000, 'per_sqmm': 200},
                'HT': {'base': 75000, 'per_sqmm': 500},
                'EHV': {'base': 250000, 'per_sqmm': 1500}
            },
            'acceptance_tests': {
                'LT': {'base': 5000, 'per_km': 500},
                'HT': {'base': 15000, 'per_km': 1500},
                'EHV': {'base': 50000, 'per_km': 5000}
            }
        }
        
        # Get costs for voltage class
        routine = base_costs['routine_tests'].get(voltage_class, base_costs['routine_tests']['LT'])
        type_test = base_costs['type_tests'].get(voltage_class, base_costs['type_tests']['LT'])
        acceptance = base_costs['acceptance_tests'].get(voltage_class, base_costs['acceptance_tests']['LT'])
        
        # Calculate routine test cost
        routine_cost = routine['base'] + (routine['per_sample'] * num_samples)
        if is_armoured:
            routine_cost *= 1.3  # 30% extra for armoured cables
        
        # Calculate type test cost
        type_test_cost = type_test['base'] + (type_test['per_sqmm'] * cable_size)
        if is_armoured:
            type_test_cost *= 1.4  # 40% extra for armoured cables
        
        # Calculate acceptance test cost
        length_km = quantity_meters / 1000
        acceptance_cost = acceptance['base'] + (acceptance['per_km'] * length_km)
        
        # Test certificate cost
        certificate_cost = 500 if voltage_class == 'LT' else (1500 if voltage_class == 'HT' else 3000)
        
        # Total cost
        total_cost = routine_cost + type_test_cost + acceptance_cost + certificate_cost
        
        # Cost per meter
        cost_per_meter = total_cost / quantity_meters if quantity_meters > 0 else 0
        
        return {
            'calculation_type': 'testing_costs',
            'input': {
                'cable_size': cable_size,
                'voltage_class': voltage_class,
                'cable_type': cable_type,
                'is_armoured': is_armoured,
                'quantity_meters': quantity_meters,
                'num_samples': num_samples
            },
            'costs': {
                'routine_tests_INR': round(routine_cost, 2),
                'type_tests_INR': round(type_test_cost, 2),
                'acceptance_tests_INR': round(acceptance_cost, 2),
                'certificate_cost_INR': certificate_cost,
                'total_testing_cost_INR': round(total_cost, 2),
                'testing_cost_per_meter_INR': round(cost_per_meter, 4)
            },
            'tests_included': self._get_required_tests(voltage_class, cable_type, is_armoured)
        }
    
    def _get_required_tests(self, voltage_class: str, cable_type: str, is_armoured: bool) -> Dict:
        """Get list of required tests based on cable specifications"""
        routine_tests = [
            'Conductor Resistance Test',
            'Insulation Resistance Test (IR)',
            'High Voltage Test (HV)',
            'Spark Test (for insulation)'
        ]
        
        type_tests = [
            'Tensile Strength & Elongation',
            'Hot Set Test',
            'Thermal Stability Test',
            'Oxygen Index Test',
            'Heat Shock Test',
            'Cold Bend Test'
        ]
        
        acceptance_tests = [
            'Visual Inspection',
            'Dimensional Check',
            'Conductor Resistance Verification',
            'Insulation Resistance Verification'
        ]
        
        # Add voltage-class specific tests
        if voltage_class in ['HT', 'EHV']:
            routine_tests.extend([
                'Partial Discharge Test',
                'Capacitance Test'
            ])
            type_tests.extend([
                'Impulse Withstand Test',
                'Bending Test',
                'Tan Delta Test',
                'Water Penetration Test'
            ])
        
        if voltage_class == 'EHV':
            type_tests.extend([
                'Long Duration Voltage Test',
                'Heating Cycle Test',
                'External Damage Test'
            ])
        
        # Add armour-specific tests
        if is_armoured:
            routine_tests.append('Armour Continuity Test')
            type_tests.extend([
                'Armour Corrosion Resistance Test',
                'Armour Tensile Test'
            ])
        
        return {
            'routine_tests': routine_tests,
            'type_tests': type_tests,
            'acceptance_tests': acceptance_tests,
            'total_test_count': len(routine_tests) + len(type_tests) + len(acceptance_tests)
        }
    
    def calculate_insulation_resistance(self, cable_size: float, length: float,
                                        insulation_type: str = 'PVC',
                                        voltage_rating: float = 1100,
                                        temperature: int = 20) -> Dict:
        """
        Calculate expected insulation resistance values
        Based on IS 694 / IS 1554 standards
        """
        # Minimum IR values (MΩ·km) at 20°C
        min_ir_values = {
            'PVC': {'LT': 50, 'HT': 100},
            'XLPE': {'LT': 100, 'HT': 500},
            'FRLS': {'LT': 50, 'HT': 100},
            'Rubber': {'LT': 20, 'HT': 50}
        }
        
        voltage_class = 'HT' if voltage_rating > 1100 else 'LT'
        base_ir = min_ir_values.get(insulation_type, min_ir_values['PVC']).get(voltage_class, 50)
        
        # Temperature correction (IR halves for every 10°C rise)
        temp_factor = 2 ** ((20 - temperature) / 10)
        
        # Length correction (IR is inversely proportional to length)
        length_km = length / 1000
        ir_for_length = (base_ir / length_km) if length_km > 0 else base_ir
        
        # Apply temperature correction
        expected_ir = ir_for_length * temp_factor
        
        # Minimum acceptable value
        min_acceptable = (base_ir / length_km) if length_km > 0 else base_ir
        
        # Calculate test voltage
        test_voltage = 500 if voltage_rating <= 650 else (1000 if voltage_rating <= 1100 else 2500)
        
        return {
            'calculation_type': 'insulation_resistance',
            'input': {
                'cable_size': cable_size,
                'length': length,
                'insulation_type': insulation_type,
                'voltage_rating': voltage_rating,
                'temperature': temperature
            },
            'calculation': {
                'base_ir_mohm_km': base_ir,
                'temperature_correction_factor': round(temp_factor, 3),
                'expected_ir_mohm': round(expected_ir, 2),
                'minimum_acceptable_ir_mohm': round(min_acceptable, 2),
                'test_voltage_dc': test_voltage
            },
            'test_procedure': {
                'duration_minutes': 1,
                'stabilization_time_seconds': 60,
                'reading_interval': 'After 1 minute of voltage application'
            }
        }
    
    def calculate_hi_pot_test(self, voltage_rating: float, cable_type: str = 'power',
                             test_type: str = 'routine', duration_minutes: int = 5) -> Dict:
        """
        Calculate High Potential (Hi-Pot) test parameters
        Based on IS/IEC standards
        """
        # Test voltage multipliers
        multipliers = {
            'routine': {'AC': 2.5, 'DC': 4.0},
            'type': {'AC': 3.5, 'DC': 5.6},
            'acceptance': {'AC': 2.0, 'DC': 3.2}
        }
        
        mult = multipliers.get(test_type, multipliers['routine'])
        
        # Calculate test voltages
        ac_test_voltage = voltage_rating * mult['AC']
        dc_test_voltage = voltage_rating * mult['DC']
        
        # Duration based on test type
        durations = {
            'routine': 5,
            'type': 15,
            'acceptance': 5
        }
        test_duration = durations.get(test_type, 5)
        
        # Leakage current limits (μA/km)
        max_leakage = {
            'LT': 1.0,
            'HT': 0.5,
            'EHV': 0.3
        }
        voltage_class = 'EHV' if voltage_rating > 33000 else ('HT' if voltage_rating > 1100 else 'LT')
        
        return {
            'calculation_type': 'hi_pot_test',
            'input': {
                'voltage_rating': voltage_rating,
                'cable_type': cable_type,
                'test_type': test_type,
                'duration_minutes': duration_minutes
            },
            'test_parameters': {
                'ac_test_voltage_kV': round(ac_test_voltage / 1000, 2),
                'dc_test_voltage_kV': round(dc_test_voltage / 1000, 2),
                'test_duration_minutes': test_duration,
                'max_leakage_current_uA_km': max_leakage[voltage_class],
                'voltage_class': voltage_class
            },
            'pass_criteria': {
                'no_breakdown': True,
                'no_flashover': True,
                'leakage_within_limits': True,
                'no_visible_damage': True
            },
            'safety_requirements': [
                'Ensure proper grounding',
                'Use appropriate PPE',
                'Maintain safe clearance distance',
                'Discharge cable after test',
                'Use calibrated equipment'
            ]
        }
    
    def calculate_conductor_resistance(self, cable_size: float, length: float,
                                       material: str = 'copper',
                                       temperature: int = 20,
                                       stranding: str = 'Class 2') -> Dict:
        """
        Calculate conductor resistance and verify against standards
        Based on IS 8130 / IEC 60228
        """
        # Maximum resistance at 20°C (Ω/km) - IS 8130 / IEC 60228
        max_resistance_20c = {
            'copper': {
                'Class 1': {1.0: 18.1, 1.5: 12.1, 2.5: 7.41, 4.0: 4.61, 6.0: 3.08, 
                           10.0: 1.83, 16.0: 1.15, 25.0: 0.727, 35.0: 0.524, 
                           50.0: 0.387, 70.0: 0.268, 95.0: 0.193, 120.0: 0.153,
                           150.0: 0.124, 185.0: 0.0991, 240.0: 0.0754, 300.0: 0.0601},
                'Class 2': {1.0: 18.1, 1.5: 12.1, 2.5: 7.41, 4.0: 4.61, 6.0: 3.08, 
                           10.0: 1.83, 16.0: 1.15, 25.0: 0.727, 35.0: 0.524, 
                           50.0: 0.387, 70.0: 0.268, 95.0: 0.193, 120.0: 0.153,
                           150.0: 0.124, 185.0: 0.0991, 240.0: 0.0754, 300.0: 0.0601},
                'Class 5': {0.5: 39.0, 0.75: 26.0, 1.0: 19.5, 1.5: 13.3, 2.5: 7.98, 
                           4.0: 4.95, 6.0: 3.30, 10.0: 1.91, 16.0: 1.21, 25.0: 0.780}
            },
            'aluminum': {
                'Class 1': {2.5: 12.1, 4.0: 7.41, 6.0: 4.61, 10.0: 3.08, 16.0: 1.91,
                           25.0: 1.20, 35.0: 0.868, 50.0: 0.641, 70.0: 0.443, 
                           95.0: 0.320, 120.0: 0.253, 150.0: 0.206, 185.0: 0.164,
                           240.0: 0.125, 300.0: 0.100},
                'Class 2': {2.5: 12.1, 4.0: 7.41, 6.0: 4.61, 10.0: 3.08, 16.0: 1.91,
                           25.0: 1.20, 35.0: 0.868, 50.0: 0.641, 70.0: 0.443, 
                           95.0: 0.320, 120.0: 0.253, 150.0: 0.206, 185.0: 0.164,
                           240.0: 0.125, 300.0: 0.100}
            }
        }
        
        material = material.lower()
        mat_key = 'copper' if 'copper' in material or 'cu' in material else 'aluminum'
        
        # Get max resistance at 20°C
        resistance_table = max_resistance_20c.get(mat_key, {}).get(stranding, {})
        
        # Find closest cable size
        sizes = sorted(resistance_table.keys())
        closest_size = min(sizes, key=lambda x: abs(x - cable_size)) if sizes else cable_size
        max_r_20c = resistance_table.get(closest_size, self.RESISTIVITY[mat_key] * 1000 / cable_size)
        
        # Temperature correction
        temp_coeff = self.TEMP_COEFFICIENT.get(mat_key, 0.00393)
        correction_factor = 1 + temp_coeff * (temperature - 20)
        max_r_at_temp = max_r_20c * correction_factor
        
        # Calculate for given length
        length_km = length / 1000
        max_resistance = max_r_at_temp * length_km
        
        return {
            'calculation_type': 'conductor_resistance',
            'input': {
                'cable_size': cable_size,
                'length': length,
                'material': mat_key,
                'temperature': temperature,
                'stranding': stranding
            },
            'calculation': {
                'max_resistance_20c_ohm_km': max_r_20c,
                'temperature_correction_factor': round(correction_factor, 4),
                'max_resistance_at_temp_ohm_km': round(max_r_at_temp, 4),
                'max_resistance_for_length_ohm': round(max_resistance, 4)
            },
            'test_parameters': {
                'test_current_amps': min(10, cable_size),  # Use lower of 10A or cable size
                'measurement_accuracy': '±0.5%',
                'temperature_measurement': 'Required for correction'
            },
            'pass_criteria': {
                'measured_less_than_max': f'R < {round(max_resistance, 4)} Ω',
                'standard_reference': 'IS 8130 / IEC 60228'
            }
        }


class ProductRecommender:
    """Smart product recommendation engine"""
    
    APPLICATION_PROFILES = {
        'residential': {
            'preferred_insulation': ['PVC', 'FRLS'],
            'voltage_range': (650, 1100),
            'armoured': False,
            'fire_rating_required': False,
            'description': 'Standard residential wiring - focus on safety and cost-effectiveness'
        },
        'commercial': {
            'preferred_insulation': ['FRLS', 'ZHFR', 'LSHF'],
            'voltage_range': (650, 1100),
            'armoured': False,
            'fire_rating_required': True,
            'description': 'Commercial buildings - fire safety and compliance focused'
        },
        'industrial': {
            'preferred_insulation': ['XLPE', 'FRLS'],
            'voltage_range': (1100, 3300),
            'armoured': True,
            'fire_rating_required': True,
            'description': 'Industrial applications - durability and high capacity'
        },
        'underground': {
            'preferred_insulation': ['XLPE'],
            'voltage_range': (1100, 11000),
            'armoured': True,
            'fire_rating_required': False,
            'description': 'Underground installations - moisture and mechanical protection'
        },
        'outdoor': {
            'preferred_insulation': ['XLPE', 'PVC'],
            'voltage_range': (1100, 3300),
            'armoured': True,
            'fire_rating_required': False,
            'description': 'Outdoor installations - weather and UV resistance'
        },
        'high_rise': {
            'preferred_insulation': ['FRLS', 'ZHFR', 'LSHF'],
            'voltage_range': (650, 1100),
            'armoured': False,
            'fire_rating_required': True,
            'description': 'High-rise buildings - fire safety critical'
        },
        'hospital': {
            'preferred_insulation': ['LSHF', 'ZHFR', 'FRLS'],
            'voltage_range': (650, 1100),
            'armoured': False,
            'fire_rating_required': True,
            'description': 'Healthcare facilities - low smoke, zero halogen required'
        },
        'data_center': {
            'preferred_insulation': ['LSHF', 'ZHFR'],
            'voltage_range': (650, 1100),
            'armoured': False,
            'fire_rating_required': True,
            'description': 'Data centers - low smoke, equipment protection'
        }
    }
    
    def __init__(self, product_db):
        self.product_db = product_db
    
    def get_application_profile(self, application: str) -> Dict:
        return self.APPLICATION_PROFILES.get(application, self.APPLICATION_PROFILES['commercial'])


class OEMProductDatabase:
    """Loads and manages all OEM product data including Moglix marketplace"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.products_df = None
        self.oem_list = []
        self.source_stats = {}  # Track products by source
        self._load_all_oem_data()
    
    def _load_all_oem_data(self):
        """Load product data from all OEMs and Moglix marketplace"""
        import glob
        all_products = []
        
        # Load OEM data from subfolders (Polycab, Havells, KEI, Finolex, RR_KABEL)
        for oem_folder in os.listdir(self.data_path):
            oem_path = os.path.join(self.data_path, oem_folder)
            if os.path.isdir(oem_path):
                # Find complete products CSV - prefer optimized versions
                all_csv_files = glob.glob(os.path.join(oem_path, '*complete_products*.csv'))
                # Separate optimized and regular files
                optimized_files = [f for f in all_csv_files if '_optimized_' in f]
                regular_files = [f for f in all_csv_files if '_optimized_' not in f]
                # Use optimized if available, otherwise use regular
                files_to_load = optimized_files if optimized_files else regular_files
                
                for csv_path in files_to_load:
                    try:
                        df = pd.read_csv(csv_path, low_memory=False)
                        oem_name = oem_folder.title().replace('_', ' ')
                        df['OEM'] = oem_name
                        df['Source'] = 'OEM Direct'
                        all_products.append(df)
                        self.oem_list.append(oem_name)
                        self.source_stats[oem_name] = len(df)
                        logger.info(f"Loaded {len(df)} products from {oem_folder} (optimized: {'_optimized_' in csv_path})")
                    except Exception as e:
                        logger.error(f"Error loading {csv_path}: {e}")
        
        # Load Moglix marketplace data (OPTIMIZED: moglix_*_optimized_*.csv, fallback to regular)
        moglix_pattern_optimized = os.path.join(self.data_path, 'moglix_*_optimized_*.csv')
        moglix_optimized = glob.glob(moglix_pattern_optimized)
        moglix_files = moglix_optimized if moglix_optimized else ['moglix_1.csv', 'moglix_2.csv']
        moglix_total = 0
        for moglix_file in moglix_files:
            # Handle both full paths (from glob) and filenames
            if os.path.isabs(moglix_file):
                moglix_path = moglix_file
            else:
                moglix_path = os.path.join(self.data_path, moglix_file)
            if os.path.exists(moglix_path):
                try:
                    df = pd.read_csv(moglix_path, low_memory=False)
                    # Use Company column if exists, otherwise set to Moglix
                    if 'Company' in df.columns:
                        df['OEM'] = df['Company'].fillna('Moglix Marketplace')
                    else:
                        df['OEM'] = 'Moglix Marketplace'
                    df['Source'] = 'Moglix Marketplace'
                    all_products.append(df)
                    moglix_total += len(df)
                    logger.info(f"Loaded {len(df)} products from {moglix_file}")
                except Exception as e:
                    logger.error(f"Error loading {moglix_path}: {e}")
        
        if moglix_total > 0:
            self.oem_list.append('Moglix Marketplace')
            self.source_stats['Moglix Marketplace'] = moglix_total
        
        if all_products:
            self.products_df = pd.concat(all_products, ignore_index=True)
            logger.info(f"Total products loaded: {len(self.products_df)} from {len(self.oem_list)} sources")
            logger.info(f"Sources: {', '.join(self.oem_list)}")
        else:
            self.products_df = pd.DataFrame()
            logger.warning("No product data loaded!")
    
    def get_total_products(self) -> int:
        return len(self.products_df) if self.products_df is not None else 0
    
    def get_oem_list(self) -> List[str]:
        return self.oem_list
    
    def get_source_stats(self) -> Dict[str, int]:
        """Get product count by source"""
        return self.source_stats
    
    def get_products_by_source(self, source: str) -> pd.DataFrame:
        """Get products filtered by source"""
        if self.products_df is None:
            return pd.DataFrame()
        return self.products_df[self.products_df['Source'] == source]
    
    def get_all_products(self, limit: int = None) -> List[Dict]:
        """Get all products as list of dicts"""
        if self.products_df is None or len(self.products_df) == 0:
            return []
        
        df = self.products_df
        if limit:
            df = df.head(limit)
        
        # Convert to list of dicts with cleaned values
        products = df.to_dict('records')
        return [clean_nan_values(p) for p in products]
    
    def search_products(self, query: str = None, oem: str = None, 
                       size: float = None, cores: int = None, 
                       limit: int = 50) -> List[Dict]:
        """Search products with filters"""
        if self.products_df is None or len(self.products_df) == 0:
            return []
        
        df = self.products_df.copy()
        
        # Apply filters
        if oem:
            df = df[df['OEM'].str.lower() == oem.lower()]
        
        if size:
            # Try different column names for conductor size
            size_cols = ['conductor_size', 'Conductor Size', 'size', 'Size', 'nominal_area']
            for col in size_cols:
                if col in df.columns:
                    df = df[df[col] == size]
                    break
        
        if cores:
            cores_cols = ['cores', 'Cores', 'no_of_cores', 'No of Cores']
            for col in cores_cols:
                if col in df.columns:
                    df = df[df[col] == cores]
                    break
        
        if query:
            # Search in product name and description
            query_lower = query.lower()
            name_cols = ['product_name', 'Product Name', 'name', 'Name', 'description', 'Description']
            mask = pd.Series([False] * len(df))
            for col in name_cols:
                if col in df.columns:
                    mask = mask | df[col].astype(str).str.lower().str.contains(query_lower, na=False)
            df = df[mask]
        
        # Limit results
        if limit:
            df = df.head(limit)
        
        # Convert to list of dicts
        products = df.to_dict('records')
        return [clean_nan_values(p) for p in products]


def clean_nan_values(obj):
    """Convert NaN/None values to JSON-safe values"""
    import math
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj):
            return None
        return obj
    elif pd.isna(obj):
        return None
    return obj


class SpecMatcher:
    """Matches RFP specifications against OEM products"""
    
    def __init__(self, product_db: OEMProductDatabase):
        self.product_db = product_db
    
    def parse_rfp_requirements(self, rfp_text: str) -> List[Dict]:
        """
        Extract product requirements from RFP text
        Returns list of required products with specifications
        """
        requirements = []
        
        # Common wire/cable specification patterns
        patterns = {
            # Pattern: "2.5 sq mm 3 core" or "2.5 sqmm 3C"
            'size_core': r'(\d+\.?\d*)\s*(?:sq\.?\s*mm|sqmm|mm2|mm²)\s*(?:x\s*)?(\d+)\s*(?:core|c\b)',
            # Pattern: "3 core 2.5 sq mm"
            'core_size': r'(\d+)\s*(?:core|c)\s*(?:x\s*)?(\d+\.?\d*)\s*(?:sq\.?\s*mm|sqmm|mm2|mm²)',
            # Voltage pattern: "1100V" or "1.1kV"
            'voltage': r'(\d+\.?\d*)\s*(?:kv|v)\b',
            # Armoured pattern
            'armoured': r'\b(armour(?:ed)?|unarmour(?:ed)?|arm|una)\b',
            # Insulation type
            'insulation': r'\b(pvc|xlpe|frls|fr-lsh|rubber|lshf)\b',
            # Copper/Aluminum
            'conductor': r'\b(copper|aluminium|aluminum|cu|al)\b',
            # Current rating
            'current': r'(\d+)\s*(?:amp|a)\b',
            # Standard
            'standard': r'\b(is\s*\d+|iec\s*\d+|bs\s*\d+)\b',
        }
        
        # Split text into lines and analyze
        lines = rfp_text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if line contains wire/cable specification
            if any(kw in line_lower for kw in ['wire', 'cable', 'sq mm', 'sqmm', 'core', 'conductor']):
                req = self._extract_specs_from_line(line, patterns)
                if req.get('conductor_size') or req.get('cores'):
                    req['original_text'] = line.strip()
                    requirements.append(req)
        
        # Deduplicate and clean requirements
        unique_reqs = self._deduplicate_requirements(requirements)
        
        return unique_reqs
    
    def _extract_specs_from_line(self, line: str, patterns: Dict) -> Dict:
        """Extract specifications from a single line"""
        line_lower = line.lower()
        req = {}
        
        # Extract size and cores
        match = re.search(patterns['size_core'], line_lower, re.IGNORECASE)
        if match:
            req['conductor_size'] = float(match.group(1))
            req['cores'] = int(match.group(2))
        else:
            match = re.search(patterns['core_size'], line_lower, re.IGNORECASE)
            if match:
                req['cores'] = int(match.group(1))
                req['conductor_size'] = float(match.group(2))
        
        # Extract voltage
        match = re.search(patterns['voltage'], line_lower, re.IGNORECASE)
        if match:
            voltage = float(match.group(1))
            if 'kv' in line_lower[match.start():match.end()+2].lower():
                voltage *= 1000
            req['voltage'] = voltage
        
        # Extract armoured status
        match = re.search(patterns['armoured'], line_lower, re.IGNORECASE)
        if match:
            req['armoured'] = 'unarm' not in match.group(1).lower()
        
        # Extract insulation type
        match = re.search(patterns['insulation'], line_lower, re.IGNORECASE)
        if match:
            req['insulation'] = match.group(1).upper()
        
        # Extract conductor material
        match = re.search(patterns['conductor'], line_lower, re.IGNORECASE)
        if match:
            material = match.group(1).lower()
            req['conductor_material'] = 'Copper' if material in ['copper', 'cu'] else 'Aluminium'
        
        # Extract current rating
        match = re.search(patterns['current'], line_lower, re.IGNORECASE)
        if match:
            req['current_rating'] = int(match.group(1))
        
        # Extract standard
        match = re.search(patterns['standard'], line_lower, re.IGNORECASE)
        if match:
            req['standard'] = match.group(1).upper().replace(' ', '')
        
        return req
    
    def _deduplicate_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """Remove duplicate requirements"""
        seen = set()
        unique = []
        
        for req in requirements:
            # Create a key from main specs
            key = (req.get('conductor_size'), req.get('cores'), 
                   req.get('voltage'), req.get('insulation'))
            if key not in seen and (req.get('conductor_size') or req.get('cores')):
                seen.add(key)
                unique.append(req)
        
        return unique
    
    def find_matching_products(self, requirement: Dict, top_n: int = 3) -> List[Dict]:
        """
        Find top N matching products for a requirement.
        Ensures OEM diversity — picks the best product from each OEM first,
        then fills remaining slots with next-best from any OEM.
        """
        if self.product_db.products_df is None or len(self.product_db.products_df) == 0:
            return []
        
        df = self.product_db.products_df.copy()
        
        # Calculate match scores
        df['match_score'] = df.apply(
            lambda row: self._calculate_match_score(row, requirement), axis=1
        )
        
        # Filter out zero-score products (no spec matched at all)
        df = df[df['match_score'] > 0]
        
        # Sort by score descending
        df = df.sort_values('match_score', ascending=False)
        
        # OEM-diverse selection: pick best from each unique OEM first
        selected_indices = []
        seen_oems = set()
        
        # First pass: best product per OEM
        for idx, row in df.iterrows():
            oem = row.get('OEM', row.get('Company', 'Unknown'))
            if oem not in seen_oems:
                selected_indices.append(idx)
                seen_oems.add(oem)
                if len(selected_indices) >= top_n:
                    break
        
        # If we still need more (fewer OEMs than top_n), fill from remaining
        if len(selected_indices) < top_n:
            for idx, row in df.iterrows():
                if idx not in selected_indices:
                    selected_indices.append(idx)
                    if len(selected_indices) >= top_n:
                        break
        
        top_products = df.loc[selected_indices]
        
        def _first_valid(*vals):
            for v in vals:
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    sv = str(v).strip()
                    if sv and sv.lower() not in ['nan', 'none']:
                        return v
            return None

        results = []
        for _, row in top_products.iterrows():
            product = {
                'oem': row.get('OEM', row.get('Company', 'Unknown')),
                'source': row.get('Source', 'Unknown'),
                'product_code': row.get('Product_Code', ''),
                'product_name': row.get('Product_Name', ''),
                'match_score': round(row['match_score'], 1),
                'conductor_size': _first_valid(row.get('Conductor_Size_sqmm'), row.get('Conductor_Size_Range')),
                'cores': _first_valid(row.get('No_of_Cores'), row.get('Cores_Category')),
                'voltage_rating': _first_valid(row.get('Voltage_Rating'), row.get('Voltage_Normalized')),
                'insulation_type': _first_valid(row.get('Insulation_Type'), row.get('Insulation_Type_Normalized')),
                'conductor_material': _first_valid(row.get('Conductor_Material'), row.get('Conductor_Material_Normalized')),
                'current_rating': row.get('Current_Rating_Amps'),
                'standard': _first_valid(row.get('Standard'), row.get('Compliance_Level')),
                'price_per_meter': row.get('Price_Per_Meter_INR'),
                'price_per_100m': row.get('Price_Per_100m_INR'),
                'fire_rating': _first_valid(row.get('Fire_Rating'), row.get('Fire_Rating_Extracted')),
                'is_armoured': row.get('Is_Armoured'),
                'warranty_years': row.get('Warranty_Years'),
                'overall_quality_score': row.get('Overall_Quality_Score'),
                # NEW OPTIMIZED COLUMNS (if available)
                'voltage_normalized': row.get('Voltage_Normalized'),
                'conductor_material_normalized': row.get('Conductor_Material_Normalized'),
                'insulation_type_normalized': row.get('Insulation_Type_Normalized'),
                'size_range': row.get('Conductor_Size_Range'),
                'cores_category': row.get('Cores_Category'),
                'application_domain': row.get('Application_Domain'),
                'cable_type_simplified': row.get('Cable_Type_Simplified'),
                'fire_rating_extracted': row.get('Fire_Rating_Extracted'),
                'compliance_level': row.get('Compliance_Level'),
                'cost_efficiency': row.get('Cost_Efficiency_Category'),
                'matching_confidence': row.get('Matching_Confidence'),
                'rfp_fit_score': row.get('RFP_Fit_Score'),
                'product_signature': row.get('Product_Signature'),
                'product_category_synonyms': row.get('Product_Category_Synonyms'),
                'rfp_matching_tags': row.get('RFP_Matching_Tags'),
                # Enriched data columns (original)
                'cable_construction': row.get('Cable_Construction'),
                'primary_application': row.get('Primary_Application'),
                'installation_difficulty': row.get('Installation_Difficulty'),
                'safety_rating': row.get('Safety_Rating'),
                'durability_rating': row.get('Durability_Rating'),
                'thermal_resistance': row.get('Thermal_Resistance_Level'),
                'flame_retardant_rating': row.get('Flame_Retardant_Rating'),
                'hsn_code': row.get('HSN_Code'),
                'compliance_standards': row.get('Compliance_Standards'),
            }
            # Detect price unit from product name (coil length) or price ratio
            _pname = str(row.get('Product_Name', ''))
            _coil_m = __import__('re').search(r'Length:\s*(\d+)\s*m', _pname, __import__('re').IGNORECASE)
            if _coil_m:
                product['price_unit'] = f"{_coil_m.group(1)}m"
            else:
                _ppm = row.get('Price_Per_Meter_INR') or 0
                _calc = row.get('Calculated_Price_Per_Meter') or 0
                try:
                    _ratio = float(_ppm) / float(_calc) if float(_calc) > 0 else 1
                    if 85 <= _ratio <= 115:
                        product['price_unit'] = '100m'
                    elif 170 <= _ratio <= 195:
                        product['price_unit'] = '180m'
                    elif 80 <= _ratio <= 95:
                        product['price_unit'] = '90m'
                    else:
                        product['price_unit'] = 'm'
                except (TypeError, ValueError, ZeroDivisionError):
                    product['price_unit'] = 'm'
            # Evaluate Tier 1 Knockout Status & Compliance Classification
            is_disqualified, knockout_reasons = self._evaluate_tier1_knockouts(row, requirement)
            m_score = float(product.get('match_score', 0.0))
            if is_disqualified or m_score == 0:
                compliance_status = "DISQUALIFIED"
            elif m_score >= 90:
                compliance_status = "FULLY_COMPLIANT"
            elif m_score >= 75:
                compliance_status = "ACCEPTABLE_EQUIVALENT"
            elif m_score >= 50:
                compliance_status = "PARTIALLY_COMPLIANT"
            else:
                compliance_status = "NON_COMPLIANT"

            product['is_qualified'] = not is_disqualified
            product['knockout_reasons'] = knockout_reasons
            product['compliance_status'] = compliance_status

            # Clean NaN values for JSON serialization
            results.append(clean_nan_values(product))
        
        return results
    
    def _evaluate_tier1_knockouts(self, product_row: pd.Series, requirement: Dict) -> Tuple[bool, List[str]]:
        """
        Evaluate Tier 1 Hard Knockout Gatekeeper Rules.
        Returns: (is_disqualified, list_of_fatal_reasons)
        """
        reasons = []

        # 1. Conductor Material Knockout
        req_mat = requirement.get('conductor_material')
        if req_mat:
            req_mat_clean = 'copper' if any(x in str(req_mat).lower() for x in ['cu', 'copper']) else (
                'aluminium' if any(x in str(req_mat).lower() for x in ['al', 'aluminium', 'aluminum']) else str(req_mat).lower()
            )
            prod_mat = str(product_row.get('Conductor_Material_Normalized') or product_row.get('Conductor_Material') or '').lower()
            prod_mat_clean = 'copper' if any(x in prod_mat for x in ['cu', 'copper']) else (
                'aluminium' if any(x in prod_mat for x in ['al', 'aluminium', 'aluminum']) else prod_mat
            )
            if req_mat_clean in ['copper', 'aluminium'] and prod_mat_clean in ['copper', 'aluminium']:
                if req_mat_clean != prod_mat_clean:
                    reasons.append(f"Material Knockout: RFP requires {req_mat_clean.capitalize()} conductor, but offered product is {prod_mat_clean.capitalize()}")

        # 2. Voltage Deficit Knockout
        req_volt = requirement.get('voltage')
        if req_volt:
            try:
                req_v = float(req_volt)
                prod_v_str = str(product_row.get('Voltage_Rating') or product_row.get('Voltage_Normalized') or '')
                vm = re.search(r'(\d+\.?\d*)', prod_v_str)
                if vm:
                    pv = float(vm.group(1))
                    if 'kv' in prod_v_str.lower() and pv < 100:
                        pv *= 1000
                    if pv < req_v * 0.95:
                        reasons.append(f"Voltage Knockout: RFP requires {req_v}V rating, but offered product is rated only {pv}V (insufficient dielectric withstand)")
            except (ValueError, TypeError):
                pass

        # 3. Core Count Knockout
        req_cores = requirement.get('cores')
        if req_cores:
            try:
                rc = int(req_cores)
                pc = int(product_row.get('No_of_Cores', 0))
                is_3_5c_exception = (rc == 4 and pc == 3.5)
                if pc > 0 and rc != pc and not is_3_5c_exception:
                    reasons.append(f"Core Count Knockout: RFP requires {rc}-Core cable, but offered product has {pc} cores")
            except (ValueError, TypeError):
                pass

        # 4. Armour Mandatory Requirement Knockout
        req_armoured = requirement.get('armoured')
        if req_armoured is True:
            prod_armoured = product_row.get('Is_Armoured')
            if prod_armoured is not None:
                try:
                    if int(prod_armoured) == 0:
                        reasons.append("Armour Knockout: RFP mandates Armoured mechanical protection, but product is Unarmoured")
                except (ValueError, TypeError):
                    pass

        is_disqualified = len(reasons) > 0
        return is_disqualified, reasons

    def _calculate_match_score(self, product_row: pd.Series, requirement: Dict) -> float:
        """Calculate match score between product and requirement.
        
        Score is purely based on how well the product's specs match the RFP requirement.
        Pre-calculated data-quality columns (Matching_Confidence, RFP_Fit_Score) are used
        only as minor tiebreakers, NOT as primary score contributors.
        """
        # Tier 1 Knockout Gatekeeper check - fatal non-compliance yields 0% immediately
        is_disqualified, _ = self._evaluate_tier1_knockouts(product_row, requirement)
        if is_disqualified:
            return 0.0

        score = 0
        max_score = sum(SCORING_WEIGHTS.values())  # 100
        matched_fields = 0
        total_fields = 0
        
        # USE NEW OPTIMIZED COLUMNS if available for normalized matching
        # but do NOT add free bonus points  — Matching_Confidence and RFP_Fit_Score
        # measure data completeness, not requirement fit
        has_optimized_cols = 'Matching_Confidence' in product_row and 'RFP_Fit_Score' in product_row
        
        # Conductor size match (most important)
        if requirement.get('conductor_size'):
            total_fields += 1
            product_size = product_row.get('Conductor_Size_sqmm')
            # NEW: Try using Conductor_Size_Range if available
            if 'Conductor_Size_Range' in product_row and pd.notna(product_row['Conductor_Size_Range']):
                req_size_range = self._get_size_range(float(requirement['conductor_size']))
                if product_row['Conductor_Size_Range'] == req_size_range:
                    score += SCORING_WEIGHTS['Conductor_Size_sqmm']
                    matched_fields += 1
                elif product_size:
                    try:
                        product_size = float(product_size)
                        req_size = float(requirement['conductor_size'])
                        if product_size == req_size:
                            score += SCORING_WEIGHTS['Conductor_Size_sqmm']
                            matched_fields += 1
                        elif abs(product_size - req_size) / req_size < 0.1:
                            score += SCORING_WEIGHTS['Conductor_Size_sqmm'] * 0.8
                        elif abs(product_size - req_size) / req_size < 0.25:
                            score += SCORING_WEIGHTS['Conductor_Size_sqmm'] * 0.5
                    except:
                        pass
            else:
                if product_size:
                    try:
                        product_size = float(product_size)
                        req_size = float(requirement['conductor_size'])
                        if product_size == req_size:
                            score += SCORING_WEIGHTS['Conductor_Size_sqmm']
                            matched_fields += 1
                        elif abs(product_size - req_size) / req_size < 0.1:
                            score += SCORING_WEIGHTS['Conductor_Size_sqmm'] * 0.8
                        elif abs(product_size - req_size) / req_size < 0.25:
                            score += SCORING_WEIGHTS['Conductor_Size_sqmm'] * 0.5
                    except:
                        pass
        
        # Number of cores match
        if requirement.get('cores'):
            total_fields += 1
            product_cores = product_row.get('No_of_Cores')
            if 'Cores_Category' in product_row and pd.notna(product_row['Cores_Category']):
                req_cores_cat = self._get_cores_category(int(requirement['cores']))
                if product_row['Cores_Category'] == req_cores_cat:
                    score += SCORING_WEIGHTS['No_of_Cores']
                    matched_fields += 1
            elif product_cores:
                try:
                    if int(product_cores) == int(requirement['cores']):
                        score += SCORING_WEIGHTS['No_of_Cores']
                        matched_fields += 1
                    elif abs(int(product_cores) - int(requirement['cores'])) == 1:
                        score += SCORING_WEIGHTS['No_of_Cores'] * 0.5
                except:
                    pass
        
        # Voltage rating match
        if requirement.get('voltage'):
            total_fields += 1
            product_voltage = str(product_row.get('Voltage_Rating', ''))
            
            def _extract_numeric_volts(v):
                if v is None or pd.isna(v):
                    return None
                s = str(v).lower().replace(' ', '')
                m = re.search(r'(\d+\.?\d*)', s)
                if not m:
                    return None
                val = float(m.group(1))
                if 'kv' in s and val < 100:
                    val *= 1000
                return val

            req_v = _extract_numeric_volts(requirement['voltage'])
            prod_v = _extract_numeric_volts(product_row.get('Voltage_Rating')) or _extract_numeric_volts(product_row.get('Voltage_Normalized'))

            if req_v is not None and prod_v is not None:
                if prod_v >= req_v or abs(prod_v - req_v) / req_v < 0.05:
                    score += SCORING_WEIGHTS['Voltage_Rating']
                    matched_fields += 1
                elif prod_v >= req_v * 0.9:
                    score += SCORING_WEIGHTS['Voltage_Rating'] * 0.7
            elif 'Voltage_Normalized' in product_row and pd.notna(product_row['Voltage_Normalized']):
                req_voltage_norm = self._normalize_voltage(requirement['voltage'])
                if product_row['Voltage_Normalized'] == req_voltage_norm:
                    score += SCORING_WEIGHTS['Voltage_Rating']
                    matched_fields += 1
        
        # Conductor material match
        if requirement.get('conductor_material'):
            total_fields += 1
            if 'Conductor_Material_Normalized' in product_row and pd.notna(product_row['Conductor_Material_Normalized']):
                req_material_norm = self._normalize_material(requirement['conductor_material'])
                if product_row['Conductor_Material_Normalized'] == req_material_norm:
                    score += SCORING_WEIGHTS['Conductor_Material']
                    matched_fields += 1
            else:
                product_material = str(product_row.get('Conductor_Material', '')).lower()
                req_material = requirement['conductor_material'].lower()
                if req_material in product_material or product_material in req_material:
                    score += SCORING_WEIGHTS['Conductor_Material']
                    matched_fields += 1
        
        # Insulation type match
        if requirement.get('insulation'):
            total_fields += 1
            if 'Insulation_Type_Normalized' in product_row and pd.notna(product_row['Insulation_Type_Normalized']):
                req_insulation_norm = self._normalize_insulation(requirement['insulation'])
                if product_row['Insulation_Type_Normalized'] == req_insulation_norm:
                    score += SCORING_WEIGHTS['Insulation_Type']
                    matched_fields += 1
            else:
                product_insulation = str(product_row.get('Insulation_Type', '')).upper()
                req_insulation = requirement['insulation'].upper()
                if req_insulation in product_insulation:
                    score += SCORING_WEIGHTS['Insulation_Type']
                    matched_fields += 1
                elif ('FRLS' in req_insulation and 'FRLS' in product_insulation) or \
                     ('PVC' in req_insulation and 'PVC' in product_insulation) or \
                     ('XLPE' in req_insulation and 'XLPE' in product_insulation):
                    score += SCORING_WEIGHTS['Insulation_Type']
                    matched_fields += 1
        
        # Current rating match
        if requirement.get('current_rating'):
            total_fields += 1
            product_current = product_row.get('Current_Rating_Amps')
            if product_current:
                try:
                    if float(product_current) >= float(requirement['current_rating']):
                        score += SCORING_WEIGHTS['Current_Rating_Amps']
                        matched_fields += 1
                    elif float(product_current) >= float(requirement['current_rating']) * 0.9:
                        score += SCORING_WEIGHTS['Current_Rating_Amps'] * 0.7
                except:
                    pass
        
        # Standard match
        if requirement.get('standard'):
            total_fields += 1
            product_standard = str(product_row.get('Standard', '')).upper()
            req_standard = str(requirement['standard']).upper()
            if req_standard in product_standard or product_standard in req_standard:
                score += SCORING_WEIGHTS['Standard']
                matched_fields += 1
        
        # Armoured status match
        if requirement.get('armoured') is not None:
            total_fields += 1
            product_armoured = product_row.get('Is_Armoured')
            if product_armoured is not None:
                try:
                    if bool(int(product_armoured)) == requirement['armoured']:
                        score += SCORING_WEIGHTS['Is_Armoured']
                        matched_fields += 1
                except:
                    pass
        
        # Fire rating match — only if not already scored via Insulation_Type
        if requirement.get('fire_resistant') and not requirement.get('insulation'):
            total_fields += 1
            if 'Fire_Rating_Extracted' in product_row:
                fire_rating = str(product_row.get('Fire_Rating_Extracted', '')).upper()
                if 'FRLS' in fire_rating or 'FR' in fire_rating:
                    score += SCORING_WEIGHTS.get('Fire_Rating', 4)
                    matched_fields += 1
        
        # ── Normalize by ACHIEVABLE score, not total max ──
        # If the RFP only mentions 3 of 9 fields, a perfect match on those 3
        # should be ~100%, not capped at 60%.
        # Compute achievable_score = sum of weights for fields the RFP specified.
        field_weight_map = {
            'conductor_size': 'Conductor_Size_sqmm',
            'cores': 'No_of_Cores',
            'voltage': 'Voltage_Rating',
            'conductor_material': 'Conductor_Material',
            'insulation': 'Insulation_Type',
            'current_rating': 'Current_Rating_Amps',
            'standard': 'Standard',
            'armoured': 'Is_Armoured',
        }
        achievable_score = 0
        for req_key, weight_key in field_weight_map.items():
            if req_key == 'armoured':
                if requirement.get(req_key) is not None:
                    achievable_score += SCORING_WEIGHTS.get(weight_key, 0)
            elif requirement.get(req_key):
                achievable_score += SCORING_WEIGHTS.get(weight_key, 0)
        # Fire rating (only counted when insulation absent)
        if requirement.get('fire_resistant') and not requirement.get('insulation'):
            achievable_score += SCORING_WEIGHTS.get('Fire_Rating', 4)

        # Use achievable_score if we have any fields, else fall back to max_score
        denominator = achievable_score if achievable_score > 0 else max_score
        raw_pct = (score / denominator) * 100 if denominator > 0 else 0
        
        # Add minor tiebreaker from data quality (max +2 points)
        # This differentiates products with identical spec matches
        if has_optimized_cols:
            confidence = product_row.get('Matching_Confidence', 0) or 0
            fit = product_row.get('RFP_Fit_Score', 0) or 0
            tiebreak = ((confidence / 100) * 1.0) + ((fit / 100) * 1.0)  # max +2
            raw_pct += tiebreak
        
        return min(100.0, max(0.0, raw_pct))
    
    def _normalize_voltage(self, voltage) -> str:
        """Normalize voltage to standard format"""
        try:
            if not voltage or pd.isna(voltage):
                return 'Unknown'
            s = str(voltage).lower().replace(' ', '')
            m = re.search(r'(\d+\.?\d*)', s)
            if not m:
                return 'Unknown'
            val = float(m.group(1))
            if 'kv' in s and val < 100:
                val *= 1000
            
            if val <= 250:
                return '230V'
            elif val <= 440:
                return '415V'
            elif val <= 660:
                return '660V'
            elif val <= 1100:
                return '1100V'
            elif val <= 3300:
                return '3.3kV'
            elif val <= 6600:
                return '6.6kV'
            elif val <= 11000:
                return '11kV'
            elif val <= 33000:
                return '33kV'
            else:
                return '>33kV'
        except:
            return 'Unknown'
    
    def _normalize_material(self, material: str) -> str:
        """Normalize conductor material"""
        material_lower = str(material).lower()
        if 'copper' in material_lower or 'cu' in material_lower:
            return 'Copper'
        elif 'aluminium' in material_lower or 'aluminum' in material_lower:
            return 'Aluminium'
        return 'Other'
    
    def _normalize_insulation(self, insulation: str) -> str:
        """Normalize insulation type"""
        insul_lower = str(insulation).lower()
        if 'pvc' in insul_lower:
            return 'PVC'
        elif 'xlpe' in insul_lower:
            return 'XLPE'
        elif 'epr' in insul_lower:
            return 'EPR'
        elif 'rubber' in insul_lower:
            return 'RUBBER'
        return 'Other'
    
    def _get_size_range(self, size: float) -> str:
        """Get size range for conductor"""
        try:
            s = float(size)
            ranges = [
                (1.5, '<=1.5 sqmm'), (2.5, '2.5 sqmm'), (4.0, '4.0 sqmm'),
                (6.0, '6.0 sqmm'), (10.0, '10.0 sqmm'), (16.0, '16.0 sqmm'),
                (25.0, '25.0 sqmm'), (35.0, '35.0 sqmm'), (50.0, '50.0 sqmm'),
                (70.0, '70.0 sqmm'), (95.0, '95.0 sqmm'), (120.0, '120.0 sqmm'),
                (150.0, '150.0 sqmm'), (float('inf'), '>150 sqmm')
            ]
            for threshold, label in ranges:
                if s <= threshold:
                    return label
        except:
            pass
        return 'Unknown'
    
    def _get_cores_category(self, cores: int) -> str:
        """Get cores category"""
        try:
            c = int(cores)
            if c == 1: return 'Single Core'
            elif c == 2: return 'Twin'
            elif c == 3: return 'Three Core'
            elif c == 4: return 'Four Core'
            else: return f'{c} Cores'
        except:
            return 'Unknown'


# Initialize database and calculators
logger.info("Loading OEM product database...")
product_db = OEMProductDatabase(OEM_DATA_PATH)
spec_matcher = SpecMatcher(product_db)
spec_calculator = SpecCalculator()
product_recommender = ProductRecommender(product_db)
logger.info(f"Database ready: {product_db.get_total_products()} products from {len(product_db.get_oem_list())} OEMs")


def _detect_application_type(rfp_text: str) -> str:
    """Auto-detect application type from RFP text"""
    text_lower = rfp_text.lower()
    
    application_keywords = {
        'hospital': ['hospital', 'medical', 'healthcare', 'clinic', 'icu', 'operation theatre'],
        'data_center': ['data center', 'data centre', 'server room', 'it infrastructure', 'ups room'],
        'high_rise': ['high rise', 'high-rise', 'multistorey', 'multi-storey', 'tower', 'apartment'],
        'industrial': ['factory', 'plant', 'manufacturing', 'industry', 'industrial', 'motor', 'machinery'],
        'underground': ['underground', 'buried', 'below ground', 'trench', 'duct bank'],
        'outdoor': ['outdoor', 'external', 'weather', 'exposed', 'street light'],
        'commercial': ['office', 'mall', 'shopping', 'commercial', 'retail', 'bank'],
        'residential': ['residential', 'housing', 'home', 'domestic', 'apartment']
    }
    
    scores = {}
    for app_type, keywords in application_keywords.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[app_type] = score
    
    if scores:
        return max(scores, key=scores.get)
    return 'commercial'


def _generate_product_recommendations(product: dict, requirement: dict, application: str, rank: int) -> list:
    """Generate smart recommendations for a product"""
    recommendations = []
    
    if rank == 1:
        recommendations.append("🥇 Best match for this requirement - highest compatibility score")
    elif rank == 2:
        recommendations.append("🥈 Strong alternative - good balance of specs and value")
    elif rank == 3:
        recommendations.append("🥉 Budget-friendly option - meets basic requirements")
    
    app_recommendations = {
        'hospital': {'check': ['FRLS', 'ZHFR', 'LSHF'], 'message': '✅ Suitable for hospital - low smoke emission'},
        'data_center': {'check': ['FRLS', 'ZHFR'], 'message': '✅ Good for data center - fire retardant'},
        'high_rise': {'check': ['FRLS', 'FR'], 'message': '✅ Recommended for high-rise - fire safety compliant'},
        'underground': {'check': ['armoured', 'XLPE'], 'message': '✅ Suitable for underground - moisture resistant'},
        'industrial': {'check': ['armoured', 'XLPE'], 'message': '✅ Good for industrial - mechanical protection'}
    }
    
    if application in app_recommendations:
        app_rec = app_recommendations[application]
        insulation = str(product.get('insulation_type', '')).upper()
        is_armoured = product.get('is_armoured')
        
        for check in app_rec['check']:
            if check.upper() in insulation or (check == 'armoured' and is_armoured):
                recommendations.append(app_rec['message'])
                break
    
    quality = product.get('overall_quality_score')
    if quality:
        if quality >= 85:
            recommendations.append("⭐ Premium quality product - excellent reliability")
        elif quality >= 70:
            recommendations.append("✓ Good quality - reliable performance")
    
    warranty = product.get('warranty_years')
    if warranty and warranty >= 5:
        recommendations.append(f"🛡️ {warranty}-year warranty - long-term coverage")
    
    price = product.get('price_per_meter')
    if price:
        if price < 50:
            recommendations.append("💰 Budget-friendly pricing")
        elif price > 150:
            recommendations.append("💎 Premium segment - best-in-class specs")
    
    return recommendations[:4]


def _calculate_value_rating(product: dict) -> str:
    """Calculate value rating for a product"""
    quality = product.get('overall_quality_score', 50)
    price = product.get('price_per_meter', 100)
    warranty = product.get('warranty_years', 1)
    
    if price and price > 0:
        value_score = (quality * (1 + warranty * 0.1)) / (price / 50)
        if value_score >= 80:
            return "Excellent Value"
        elif value_score >= 60:
            return "Good Value"
        elif value_score >= 40:
            return "Fair Value"
        else:
            return "Premium"
    return "N/A"


def _generate_oem_comparison_summary(products: list, product_db) -> dict:
    """Generate OEM comparison summary for ALL OEMs based on best matches"""
    # Get all OEMs from database
    all_oems = product_db.get_oem_list()
    oem_stats = {}
    
    # Initialize stats for all OEMs
    for oem in all_oems:
        oem_stats[oem] = {
            'count': 0, 'total_score': 0, 'prices': [],
            'max_quality': 0, 'warranty_max': 0, 'best_match': 0
        }
    
    # Collect stats from matched products
    for product in products:
        oem = product.get('oem', 'Unknown')
        if oem in oem_stats:
            oem_stats[oem]['count'] += 1
            score = product.get('match_score', 0)
            oem_stats[oem]['total_score'] += score
            # Track best match score for each OEM
            if score > oem_stats[oem]['best_match']:
                oem_stats[oem]['best_match'] = score
            
            if product.get('price_per_meter'):
                oem_stats[oem]['prices'].append(product['price_per_meter'])
            
            quality = product.get('overall_quality_score', 0)
            if quality and quality > oem_stats[oem]['max_quality']:
                oem_stats[oem]['max_quality'] = quality
            
            warranty = product.get('warranty_years', 0)
            if warranty and warranty > oem_stats[oem]['warranty_max']:
                oem_stats[oem]['warranty_max'] = warranty
    
    # Generate rankings for ALL OEMs
    oem_rankings = []
    for oem, stats in oem_stats.items():
        # Use best_match score if available, otherwise 0 (no matches found)
        best_score = stats['best_match'] if stats['count'] > 0 else 0
        avg_score = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0
        avg_price = sum(stats['prices']) / len(stats['prices']) if stats['prices'] else 0
        
        oem_rankings.append({
            'oem': oem,
            'appearances': stats['count'],
            'best_match_score': round(best_score, 1),
            'avg_match_score': round(avg_score, 1),
            'avg_price': round(avg_price, 2),
            'max_quality_score': stats['max_quality'],
            'max_warranty': stats['warranty_max']
        })
    
    # Sort by appearances (descending), then by best match score (descending)
    oem_rankings.sort(key=lambda x: (x['appearances'], x['best_match_score']), reverse=True)
    
    return {
        'oem_rankings': oem_rankings,
        'total_oems': len(oem_rankings),
        'best_oem': oem_rankings[0]['oem'] if oem_rankings else None
    }


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         total_products=product_db.get_total_products(),
                         oem_list=product_db.get_oem_list())


@app.route('/api/compare', methods=['POST'])
def compare_specs():
    """
    Compare RFP requirements against OEM products
    Returns top 3 matches with integrated calculations and recommendations
    """
    try:
        rfp_text = ""
        
        # Get analysis options
        include_calculations = request.form.get('include_calculations', 'true') == 'true'
        include_recommendations = request.form.get('include_recommendations', 'true') == 'true'
        include_budget = request.form.get('include_budget', 'true') == 'true'
        include_oem_comparison = request.form.get('include_oem_comparison', 'true') == 'true'
        cable_length = float(request.form.get('cable_length', 100))
        application = request.form.get('application', 'auto')
        
        # Check if text was provided
        if 'rfp_text' in request.form and request.form['rfp_text'].strip():
            rfp_text = request.form['rfp_text']
        
        # Check if file was uploaded
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename:
                filename = file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                try:
                    import sys
                    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pdf_extraction'))
                    from multilingual_extractor import MultilingualExtractor
                    
                    extractor = MultilingualExtractor(file_path)
                    rfp_text = extractor.extract_all_text()
                except ImportError:
                    import fitz
                    doc = fitz.open(file_path)
                    for page in doc:
                        rfp_text += page.get_text()
                    doc.close()
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)
        
        if not rfp_text.strip():
            return jsonify({'error': 'No RFP text or file provided'}), 400
        
        # Auto-detect application type
        detected_application = _detect_application_type(rfp_text) if application == 'auto' else application
        
        # Parse requirements from RFP
        requirements = spec_matcher.parse_rfp_requirements(rfp_text)
        
        if not requirements:
            return jsonify({
                'status': 'success',
                'message': 'No wire/cable specifications found in RFP',
                'requirements': [],
                'comparisons': [],
                'detected_application': detected_application
            })
        
        # Find matching products with enhanced analysis
        comparisons = []
        all_top_products = []
        
        for req in requirements:
            top_products = spec_matcher.find_matching_products(req, top_n=3)
            
            enhanced_products = []
            for idx, product in enumerate(top_products):
                enhanced_product = product.copy()
                
                # Add calculations
                if include_calculations and product.get('conductor_size'):
                    cable_size = float(product.get('conductor_size', 4))
                    cores = int(product.get('cores', 3)) if product.get('cores') else 3
                    material = 'copper' if 'copper' in str(product.get('conductor_material', '')).lower() else 'aluminum'
                    current_rating = float(product.get('current_rating', 20)) if product.get('current_rating') else 20
                    
                    voltage_str = str(product.get('voltage_rating', '415'))
                    voltage_match = re.search(r'(\d+)', voltage_str)
                    voltage = float(voltage_match.group(1)) if voltage_match else 415
                    if 'kv' in voltage_str.lower():
                        voltage *= 1000
                    
                    vd_calc = spec_calculator.calculate_voltage_drop(
                        cable_size=cable_size, length=cable_length, current=current_rating,
                        material=material, voltage=voltage, cores=cores
                    )
                    enhanced_product['voltage_drop'] = {
                        'drop_volts': vd_calc['calculation']['voltage_drop_volts'],
                        'drop_percent': vd_calc['calculation']['voltage_drop_percent'],
                        'status': vd_calc['calculation']['assessment'],
                        'compliant_feeder': vd_calc['standards']['compliant_feeder'],
                        'compliant_branch': vd_calc['standards']['compliant_branch'],
                        'cable_length': cable_length
                    }
                    
                    pc_calc = spec_calculator.calculate_power_capacity(
                        cable_size=cable_size, voltage=voltage, material=material, cores=cores
                    )
                    enhanced_product['power_capacity'] = {
                        'power_kw': pc_calc['calculation']['power_capacity_kW'],
                        'power_kva': pc_calc['calculation']['power_capacity_kVA'],
                        'current_capacity': pc_calc['calculation']['derated_current_capacity']
                    }
                    
                    sc_calc = spec_calculator.calculate_short_circuit_capacity(
                        cable_size=cable_size, material=material
                    )
                    enhanced_product['short_circuit'] = {
                        'withstand_1s_kA': sc_calc['calculation']['withstand_current_1s_kA'],
                        'i2t_rating': sc_calc['calculation']['i2t_rating']
                    }
                
                # Add recommendations
                if include_recommendations:
                    enhanced_product['recommendations'] = _generate_product_recommendations(
                        product, req, detected_application, idx + 1
                    )
                
                # Add budget analysis
                if include_budget and product.get('price_per_meter'):
                    price = float(product.get('price_per_meter', 0))
                    enhanced_product['budget_analysis'] = {
                        'price_per_meter': price,
                        'total_cost': round(price * cable_length, 2),
                        'cable_length': cable_length,
                        'value_rating': _calculate_value_rating(product)
                    }
                
                enhanced_products.append(enhanced_product)
                all_top_products.append(product)
            
            comparisons.append({
                'requirement': {
                    'original_text': req.get('original_text', ''),
                    'conductor_size': req.get('conductor_size'),
                    'cores': req.get('cores'),
                    'voltage': req.get('voltage'),
                    'insulation': req.get('insulation'),
                    'conductor_material': req.get('conductor_material'),
                    'armoured': req.get('armoured'),
                    'current_rating': req.get('current_rating'),
                },
                'top_matches': enhanced_products,
                'match_count': len(enhanced_products)
            })
        
        # Generate OEM comparison summary
        oem_summary = None
        if include_oem_comparison and all_top_products:
            oem_summary = _generate_oem_comparison_summary(all_top_products, product_db)
        
        return jsonify({
            'status': 'success',
            'total_requirements': len(requirements),
            'comparisons': comparisons,
            'detected_application': detected_application,
            'analysis_options': {
                'calculations_included': include_calculations,
                'recommendations_included': include_recommendations,
                'budget_included': include_budget,
                'cable_length': cable_length
            },
            'oem_summary': oem_summary
        })
    
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/stats', methods=['GET'])
def get_database_stats():
    """Get OEM database statistics including Moglix marketplace"""
    try:
        if product_db.products_df is None:
            return jsonify({'error': 'Database not loaded'}), 500
        
        df = product_db.products_df
        
        # Get unique companies/brands from the data
        companies = []
        if 'Company' in df.columns:
            companies = df['Company'].dropna().unique().tolist()
        
        stats = {
            'total_products': len(df),
            'oems': product_db.get_oem_list(),
            'oem_count': len(product_db.get_oem_list()),
            'source_stats': product_db.get_source_stats(),
            'companies': companies[:50],  # Top 50 companies/brands
            'categories': df['Category'].dropna().unique().tolist() if 'Category' in df.columns else [],
            'conductor_sizes': sorted(df['Conductor_Size_sqmm'].dropna().unique().tolist()) if 'Conductor_Size_sqmm' in df.columns else [],
            'products_by_oem': df.groupby('OEM').size().to_dict() if 'OEM' in df.columns else {},
            'products_by_source': df.groupby('Source').size().to_dict() if 'Source' in df.columns else {},
            'data_quality': {
                'with_price': int(df['Price_Per_Meter_INR'].notna().sum()) if 'Price_Per_Meter_INR' in df.columns else 0,
                'with_current_rating': int(df['Current_Rating_Amps'].notna().sum()) if 'Current_Rating_Amps' in df.columns else 0,
                'with_voltage': int(df['Voltage_Rating'].notna().sum()) if 'Voltage_Rating' in df.columns else 0,
            }
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['GET'])
def search_products():
    """Search products by specifications"""
    try:
        size = request.args.get('size', type=float)
        cores = request.args.get('cores', type=int)
        oem = request.args.get('oem', '')
        
        df = product_db.products_df.copy()
        
        if size:
            df = df[df['Conductor_Size_sqmm'] == size]
        if cores:
            df = df[df['No_of_Cores'] == cores]
        if oem:
            df = df[df['OEM'].str.lower() == oem.lower()]
        
        # Return top 50 results
        results = df.head(50).to_dict('records')
        
        return jsonify({
            'total': len(df),
            'returned': len(results),
            'products': clean_nan_values(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/testing-costs', methods=['POST'])
def calculate_testing_costs():
    """Calculate comprehensive testing costs for cable procurement"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        voltage_class = data.get('voltage_class', 'LT')
        cable_type = data.get('cable_type', 'power')
        is_armoured = data.get('is_armoured', 'false').lower() == 'true' if isinstance(data.get('is_armoured'), str) else bool(data.get('is_armoured', False))
        quantity_meters = float(data.get('quantity_meters', 1000))
        num_samples = int(data.get('num_samples', 3))
        
        result = spec_calculator.calculate_testing_costs(
            cable_size=cable_size,
            voltage_class=voltage_class,
            cable_type=cable_type,
            is_armoured=is_armoured,
            quantity_meters=quantity_meters,
            num_samples=num_samples
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/insulation-resistance', methods=['POST'])
def calculate_insulation_resistance():
    """Calculate expected insulation resistance values"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        length = float(data.get('length', 100))
        insulation_type = data.get('insulation_type', 'PVC')
        voltage_rating = float(data.get('voltage_rating', 1100))
        temperature = int(data.get('temperature', 20))
        
        result = spec_calculator.calculate_insulation_resistance(
            cable_size=cable_size,
            length=length,
            insulation_type=insulation_type,
            voltage_rating=voltage_rating,
            temperature=temperature
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/hi-pot-test', methods=['POST'])
def calculate_hi_pot_test():
    """Calculate High Potential (Hi-Pot) test parameters"""
    try:
        data = request.get_json() or request.form
        
        voltage_rating = float(data.get('voltage_rating', 1100))
        cable_type = data.get('cable_type', 'power')
        test_type = data.get('test_type', 'routine')
        duration_minutes = int(data.get('duration_minutes', 5))
        
        result = spec_calculator.calculate_hi_pot_test(
            voltage_rating=voltage_rating,
            cable_type=cable_type,
            test_type=test_type,
            duration_minutes=duration_minutes
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/conductor-resistance', methods=['POST'])
def calculate_conductor_resistance():
    """Calculate conductor resistance and verify against standards"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        length = float(data.get('length', 100))
        material = data.get('material', 'copper')
        temperature = int(data.get('temperature', 20))
        stranding = data.get('stranding', 'Class 2')
        
        result = spec_calculator.calculate_conductor_resistance(
            cable_size=cable_size,
            length=length,
            material=material,
            temperature=temperature,
            stranding=stranding
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/all-tests', methods=['POST'])
def calculate_all_tests():
    """Calculate all testing parameters for a cable specification"""
    try:
        data = request.get_json() or request.form
        
        cable_size = float(data.get('cable_size', 4))
        length = float(data.get('length', 100))
        voltage_rating = float(data.get('voltage_rating', 1100))
        material = data.get('material', 'copper')
        insulation_type = data.get('insulation_type', 'PVC')
        is_armoured = data.get('is_armoured', 'false').lower() == 'true' if isinstance(data.get('is_armoured'), str) else bool(data.get('is_armoured', False))
        quantity_meters = float(data.get('quantity_meters', 1000))
        
        voltage_class = 'EHV' if voltage_rating > 33000 else ('HT' if voltage_rating > 1100 else 'LT')
        
        results = {
            'cable_specification': {
                'cable_size': cable_size,
                'length': length,
                'voltage_rating': voltage_rating,
                'voltage_class': voltage_class,
                'material': material,
                'insulation_type': insulation_type,
                'is_armoured': is_armoured,
                'quantity_meters': quantity_meters
            },
            'testing_costs': spec_calculator.calculate_testing_costs(
                cable_size=cable_size,
                voltage_class=voltage_class,
                is_armoured=is_armoured,
                quantity_meters=quantity_meters
            ),
            'conductor_resistance': spec_calculator.calculate_conductor_resistance(
                cable_size=cable_size,
                length=length,
                material=material
            ),
            'insulation_resistance': spec_calculator.calculate_insulation_resistance(
                cable_size=cable_size,
                length=length,
                insulation_type=insulation_type,
                voltage_rating=voltage_rating
            ),
            'hi_pot_test': spec_calculator.calculate_hi_pot_test(
                voltage_rating=voltage_rating,
                test_type='routine'
            )
        }
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("SPEC COMPARER PRO - RFP Product Matching System")
    print("="*70)
    print(f"📊 Loaded {product_db.get_total_products():,} products from {len(product_db.get_oem_list())} sources")
    print(f"🏭 Sources: {', '.join(product_db.get_oem_list())}")
    print(f"📦 Breakdown:")
    for source, count in product_db.get_source_stats().items():
        print(f"   - {source}: {count:,} products")
    print(f"🧮 Calculator: Cable sizing, voltage drop, short circuit, power capacity")
    print(f"🧪 Testing: Costs, IR, Hi-Pot, Conductor resistance")
    print(f"🎯 Recommender: Application-based, budget, quality analysis")
    print(f"📍 Open: http://localhost:5001")
    print("="*70 + "\n")
    
    app.run(host='localhost', port=5001, debug=True)
