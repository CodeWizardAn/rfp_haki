"""
Unit tests for MetalCommodityPricingModel and LandedCostCalculator
Verifies conductor weight physics, commodity index conversion, and itemized landed BOQ costing.
"""

import pytest
from price_optimization import CommodityRates, MetalCommodityPricingModel, LandedCostCalculator

def test_conductor_weight_physics():
    """Verify Copper and Aluminium physical weight calculations per km"""
    engine = MetalCommodityPricingModel()

    # 4C x 50 sq.mm Copper
    # Weight = 4 * 50 * 0.00889 * 1.02 * 1000 = ~1813.56 kg/km
    weight_cu_km = engine.calculate_conductor_weight_per_km(50.0, 4, 'copper')
    assert 1800.0 <= weight_cu_km <= 1830.0

    # 4C x 50 sq.mm Aluminium
    # Weight = 4 * 50 * 0.00270 * 1.02 * 1000 = ~550.8 kg/km
    weight_al_km = engine.calculate_conductor_weight_per_km(50.0, 4, 'aluminium')
    assert 540.0 <= weight_al_km <= 560.0

    # Aluminium should be ~3.3x lighter than Copper
    ratio = weight_cu_km / weight_al_km
    assert 3.2 <= ratio <= 3.4


def test_metal_cost_per_meter():
    """Verify metal cost per meter calculation reflects commodity spot price"""
    rates = CommodityRates(copper_inr_per_kg=800.0, aluminium_inr_per_kg=250.0)
    engine = MetalCommodityPricingModel(rates=rates)

    res = engine.calculate_metal_cost_per_meter(25.0, 3, 'copper')
    assert res['material'] == 'Copper'
    assert res['rate_inr_per_kg'] == 800.0
    # Weight per m = 3 * 25 * 0.00889 * 1.02 = 0.680085 kg/m
    # Cost per m = 0.680085 * 800 = ~544.07 INR
    assert 540.0 <= res['conductor_cost_per_meter'] <= 550.0


def test_landed_cost_calculator():
    """Verify full BOQ line cost breakdown includes ex-factory, freight, insurance, and GST"""
    calculator = LandedCostCalculator()
    boq = calculator.calculate_boq_line_cost(
        conductor_size_sqmm=16.0,
        no_of_cores=4,
        material='copper',
        insulation='xlpe',
        is_armoured=True,
        quantity_meters=1000.0,
        fabrication_base_cost_per_m=20.0,
        margin_percent=15.0,
        freight_distance_km=300.0,
        gst_percent=18.0
    )

    assert boq['quantity_meters'] == 1000.0
    totals = boq['totals']
    assert totals['ex_factory_total'] > 0
    assert totals['drum_packaging'] > 0
    assert totals['freight'] > 0
    assert totals['margin_amount'] > 0
    assert totals['gst_amount'] > 0
    assert totals['final_landed_total'] > totals['ex_factory_total']
    assert boq['unit_costs']['landed_unit_price_inclusive_gst'] > 0
