"""
Unit Tests for Pricing Agent
Comprehensive tests for all 51 features
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.pricing_agent.pricing_agent import (
    # Enums
    ApprovalStatus,
    PriceConfidence,
    CostCategory,
    TestType,
    TransportMode,
    
    # Data Classes
    ProductPriceEntry,
    TestCostEntry,
    LineItem,
    PricingBreakdown,
    CommercialTerms,
    PricingApproval,
    AgentMessage,
    
    # Core Classes
    PricingAgent,
    PricingAgentLogger,
    ProductListReceiver,
    PriceLookupIntegration,
    QuantityAggregator,
    UnitPriceCalculator,
    VolumeDiscountApplier,
    TestRequirementParser,
    TestCostCalculator,
    TestFrequencyAnalyzer,
    SampleTestingCost,
    TypeTestCostAllocator,
    RoutineTestCostCalculator,
    AcceptanceTestCost,
    CertificationCostAdder,
    LogisticsCostCalculator,
    TransportationCostCalculator,
    InsuranceCostCalculator,
    PackagingCostAdder,
    HandlingChargesCalculator,
    CustomsDutiesCalculator,
    SubtotalAggregator,
    ContingencyBuffer,
    MarginCalculator,
    FinalPriceGenerator,
    CompetitiveAnalysis,
    PricingRecommendationEngine,
    PriceOptimization,
    WinProbabilityEstimator,
    PricingBreakdownGenerator,
    CommercialTermsFormatter,
    PaymentTermsGenerator,
    PricingTableCreator,
    CostComparisonGenerator,
    SensitivityAnalysis,
    WhatIfScenarioGenerator,
    PricingSummaryGenerator,
    DetailedLineItemBreakdown,
    PricingValidator,
    PricingApprovalWorkflow,
    PricingHistoryTracker,
    PricingAnalytics,
    PricingErrorHandler,
    MockDataHandler,
    PricingMetrics,
    PricingDashboard,
    RealTimeUpdater,
    PricingAgentAPI,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_product_price():
    """Sample product price entry"""
    return ProductPriceEntry(
        sku="SKU_WIRE_001",
        product_name="PVC Copper Wire 1.5 sqmm",
        manufacturer="Polycab",
        base_price=25.0,
        currency="INR",
        unit="meter",
        moq=100,
        lead_time_days=7,
        discount_tiers={1000: 5, 5000: 10, 10000: 15}
    )


@pytest.fixture
def sample_test_cost():
    """Sample test cost entry"""
    return TestCostEntry(
        test_id="TEST_001",
        test_name="Conductor Resistance Test",
        test_type=TestType.ROUTINE_TEST,
        base_cost=5000.0,
        samples_required=3,
        turnaround_days=5,
        lab_name="NABL Lab",
        standard_reference="IS 8130"
    )


@pytest.fixture
def sample_pricing_input():
    """Sample pricing input"""
    return {
        'rfp_id': 'RFP_TEST_001',
        'recommendations': [
            {
                'requirement_id': 'REQ_001',
                'product_id': 'SKU_WIRE_001',
                'product_name': 'PVC Copper Wire 1.5 sqmm',
                'manufacturer': 'Polycab',
                'quantity': 5000,
                'unit': 'meters'
            }
        ],
        'tests_required': [
            'Conductor Resistance Test',
            'Type Test - High Voltage',
            'Routine Insulation Test'
        ],
        'certifications': ['BIS', 'ISI'],
        'distance_km': 500,
        'destination': 'domestic'
    }


@pytest.fixture
def pricing_agent(tmp_path):
    """Create Pricing Agent for testing"""
    agent = PricingAgent(
        agent_id="TEST_AGENT",
        log_dir=str(tmp_path / "logs")
    )
    return agent


# ============================================================================
# Test 1: PricingAgent Class Structure
# ============================================================================

class TestPricingAgentStructure:
    """Test Pricing Agent class structure"""
    
    def test_agent_initialization(self, pricing_agent):
        """Agent should initialize with all components"""
        assert pricing_agent.agent_id == "TEST_AGENT"
        assert pricing_agent.product_receiver is not None
        assert pricing_agent.price_lookup is not None
        assert pricing_agent.margin_calculator is not None
        assert pricing_agent.api is not None
    
    def test_agent_has_required_methods(self, pricing_agent):
        """Agent should have all required methods"""
        required_methods = [
            'calculate_pricing', 'get_status', 'health_check',
            'generate_commercial_terms', 'perform_competitive_analysis'
        ]
        for method in required_methods:
            assert hasattr(pricing_agent, method), f"Missing method: {method}"
    
    def test_health_check(self, pricing_agent):
        """Health check should return status"""
        health = pricing_agent.health_check()
        assert health['healthy'] is True
        assert health['agent_id'] == "TEST_AGENT"


# ============================================================================
# Test 2: Product List Receiver
# ============================================================================

class TestProductListReceiver:
    """Test product list receiver"""
    
    def test_receive_products(self, sample_pricing_input):
        """Should receive product list"""
        receiver = ProductListReceiver()
        products = receiver.receive(sample_pricing_input)
        
        assert len(products) == 1
        assert products[0]['selected_sku'] == 'SKU_WIRE_001'
        assert products[0]['quantity'] == 5000
    
    def test_get_products(self, sample_pricing_input):
        """Should return received products"""
        receiver = ProductListReceiver()
        receiver.receive(sample_pricing_input)
        
        products = receiver.get_products()
        assert len(products) == 1


# ============================================================================
# Test 3: Price Lookup Integration
# ============================================================================

class TestPriceLookupIntegration:
    """Test price lookup integration"""
    
    def test_lookup_initialization(self):
        """Should initialize price lookup"""
        lookup = PriceLookupIntegration()
        # Should not fail even if database is not available
        assert isinstance(lookup.price_table, dict)
    
    def test_lookup_by_sku(self):
        """Should lookup by SKU"""
        lookup = PriceLookupIntegration()
        
        # Add test data
        lookup.price_table['TEST_SKU'] = ProductPriceEntry(
            sku='TEST_SKU',
            product_name='Test Product',
            manufacturer='Test',
            base_price=100.0
        )
        
        result = lookup.lookup('TEST_SKU')
        assert result is not None
        assert result.base_price == 100.0
    
    def test_lookup_not_found(self):
        """Should return None for unknown SKU"""
        lookup = PriceLookupIntegration()
        result = lookup.lookup('UNKNOWN_SKU')
        assert result is None


# ============================================================================
# Test 4: Quantity Aggregation
# ============================================================================

class TestQuantityAggregator:
    """Test quantity aggregation"""
    
    def test_aggregate_quantities(self):
        """Should aggregate quantities by SKU"""
        aggregator = QuantityAggregator()
        
        products = [
            {'selected_sku': 'SKU_001', 'product_name': 'Wire', 'quantity': 1000, 'requirement_id': 'R1'},
            {'selected_sku': 'SKU_001', 'product_name': 'Wire', 'quantity': 2000, 'requirement_id': 'R2'},
            {'selected_sku': 'SKU_002', 'product_name': 'Cable', 'quantity': 500, 'requirement_id': 'R3'}
        ]
        
        result = aggregator.aggregate(products)
        
        assert result['SKU_001']['total_quantity'] == 3000
        assert result['SKU_002']['total_quantity'] == 500
    
    def test_get_total_quantity(self):
        """Should return total quantity for SKU"""
        aggregator = QuantityAggregator()
        aggregator.aggregate([
            {'selected_sku': 'SKU_001', 'quantity': 1000, 'requirement_id': 'R1'}
        ])
        
        assert aggregator.get_total_quantity('SKU_001') == 1000
        assert aggregator.get_total_quantity('UNKNOWN') == 0


# ============================================================================
# Test 5: Unit Price Calculator
# ============================================================================

class TestUnitPriceCalculator:
    """Test unit price calculator"""
    
    def test_calculate_with_known_price(self):
        """Should calculate with known price"""
        lookup = PriceLookupIntegration()
        lookup.price_table['SKU_001'] = ProductPriceEntry(
            sku='SKU_001', product_name='Test', manufacturer='Test', base_price=50.0
        )
        
        calculator = UnitPriceCalculator(lookup)
        result = calculator.calculate('SKU_001', 100)
        
        assert result['unit_price'] == 50.0
        assert result['confidence'] == 'high'
        assert result['price_found'] is True
    
    def test_calculate_with_unknown_price(self):
        """Should estimate for unknown SKU"""
        lookup = PriceLookupIntegration()
        calculator = UnitPriceCalculator(lookup)
        
        result = calculator.calculate('UNKNOWN_SKU', 100)
        
        assert result['confidence'] == 'estimated'
        assert result['price_found'] is False
    
    def test_set_markup(self):
        """Should apply markup"""
        lookup = PriceLookupIntegration()
        lookup.price_table['SKU_001'] = ProductPriceEntry(
            sku='SKU_001', product_name='Test', manufacturer='Test', base_price=100.0
        )
        
        calculator = UnitPriceCalculator(lookup)
        calculator.set_markup(10)  # 10% markup
        
        result = calculator.calculate('SKU_001', 100)
        assert result['unit_price'] == 110.0


# ============================================================================
# Test 6: Volume Discount Applier
# ============================================================================

class TestVolumeDiscountApplier:
    """Test volume discount applier"""
    
    def test_no_discount_for_small_quantity(self):
        """Should not apply discount for small quantity"""
        applier = VolumeDiscountApplier()
        result = applier.apply(100.0, 50)
        
        assert result['discount_percent'] == 0
        assert result['discounted_unit_price'] == 100.0
    
    def test_discount_for_large_quantity(self):
        """Should apply discount for large quantity"""
        applier = VolumeDiscountApplier()
        result = applier.apply(100.0, 5000)
        
        assert result['discount_percent'] == 10.0
        assert result['discounted_unit_price'] == 90.0
    
    def test_custom_tiers(self):
        """Should use custom discount tiers"""
        applier = VolumeDiscountApplier()
        custom_tiers = {100: 5, 500: 15}
        
        result = applier.apply(100.0, 500, custom_tiers)
        assert result['discount_percent'] == 15.0


# ============================================================================
# Test 7: Test Requirement Parser
# ============================================================================

class TestTestRequirementParser:
    """Test requirement parser"""
    
    def test_parse_type_test(self):
        """Should detect type test"""
        parser = TestRequirementParser()
        result = parser.parse(['Type Test - High Voltage'])
        
        assert len(result) == 1
        assert result[0]['test_type'] == 'type_test'
    
    def test_parse_routine_test(self):
        """Should detect routine test"""
        parser = TestRequirementParser()
        result = parser.parse(['Routine Test - Insulation'])
        
        assert result[0]['test_type'] == 'routine_test'
    
    def test_extract_standard(self):
        """Should extract standard reference"""
        parser = TestRequirementParser()
        result = parser.parse(['Conductor Resistance Test as per IS 8130:2013'])
        
        assert 'IS' in result[0]['standard_reference']


# ============================================================================
# Test 8: Test Cost Calculator
# ============================================================================

class TestTestCostCalculator:
    """Test cost calculator"""
    
    def test_calculate_cost(self):
        """Should calculate test cost"""
        calculator = TestCostCalculator()
        result = calculator.calculate('Conductor Resistance', TestType.ROUTINE_TEST, 1)
        
        assert 'total_cost' in result
        assert result['total_cost'] > 0
    
    def test_estimate_type_test(self):
        """Should estimate type test cost"""
        calculator = TestCostCalculator()
        result = calculator.calculate('Unknown Test', TestType.TYPE_TEST, 1)
        
        assert result['confidence'] == 'estimated'
        assert result['total_cost'] >= 25000


# ============================================================================
# Test 9: Test Frequency Analyzer
# ============================================================================

class TestTestFrequencyAnalyzer:
    """Test frequency analyzer"""
    
    def test_per_lot_frequency(self):
        """Should detect per lot frequency"""
        analyzer = TestFrequencyAnalyzer()
        result = analyzer.analyze('Test per lot', 5000, lot_size=1000)
        
        assert result['frequency'] == 'per_lot'
        assert result['test_count'] == 5
    
    def test_one_time_frequency(self):
        """Should detect one-time frequency"""
        analyzer = TestFrequencyAnalyzer()
        result = analyzer.analyze('Initial type test', 5000, lot_size=1000)
        
        assert result['frequency'] == 'one_time'
        assert result['test_count'] == 1


# ============================================================================
# Tests 10-13: Sample, Type, Routine, Acceptance Test Costs
# ============================================================================

class TestSampleTestingCost:
    """Test sample testing cost"""
    
    def test_calculate_sample_costs(self):
        """Should calculate sample testing costs"""
        calculator = TestCostCalculator()
        sample_cost = SampleTestingCost(calculator)
        
        result = sample_cost.calculate(['Test 1', 'Test 2'], samples_per_test=3)
        
        assert result['test_type'] == 'sample_testing'
        assert result['total_cost'] > 0


class TestTypeTestCostAllocator:
    """Test type test cost allocator"""
    
    def test_allocate_type_test(self):
        """Should allocate type test costs"""
        calculator = TestCostCalculator()
        allocator = TypeTestCostAllocator(calculator)
        
        result = allocator.allocate(['High Voltage Test'], 10000)
        
        assert result['test_type'] == 'type_test'
        assert result['cost_per_unit'] > 0


class TestRoutineTestCostCalculator:
    """Test routine test cost calculator"""
    
    def test_calculate_routine_costs(self):
        """Should calculate routine test costs"""
        calculator = TestCostCalculator()
        routine = RoutineTestCostCalculator(calculator)
        
        result = routine.calculate(['Insulation Test'], 5000, lot_size=1000)
        
        assert result['test_type'] == 'routine_test'
        assert result['total_cost'] > 0


class TestAcceptanceTestCost:
    """Test acceptance test cost"""
    
    def test_calculate_with_witness(self):
        """Should include witness cost"""
        calculator = TestCostCalculator()
        acceptance = AcceptanceTestCost(calculator)
        
        result = acceptance.calculate(['FAT Test'], witness_required=True)
        
        assert result['witness_required'] is True
        assert result['witness_cost'] > 0


# ============================================================================
# Test 14: Certification Cost Adder
# ============================================================================

class TestCertificationCostAdder:
    """Test certification cost adder"""
    
    def test_calculate_bis_cost(self):
        """Should calculate BIS certification cost"""
        adder = CertificationCostAdder()
        result = adder.calculate(['BIS Certification'])
        
        assert len(result['certifications']) == 1
        assert result['total_cost'] > 0
    
    def test_calculate_multiple_certs(self):
        """Should calculate multiple certifications"""
        adder = CertificationCostAdder()
        result = adder.calculate(['BIS', 'ISI', 'CE'])
        
        assert len(result['certifications']) == 3


# ============================================================================
# Tests 15-20: Logistics Costs
# ============================================================================

class TestLogisticsCostCalculator:
    """Test logistics cost calculator"""
    
    def test_calculate_all_logistics(self):
        """Should calculate all logistics costs"""
        calculator = LogisticsCostCalculator()
        
        result = calculator.calculate(
            material_value=100000,
            weight_kg=500,
            distance_km=500,
            destination='domestic'
        )
        
        assert 'transportation' in result
        assert 'insurance' in result
        assert 'packaging' in result
        assert 'handling' in result
        assert result['total_logistics_cost'] > 0


class TestTransportationCostCalculator:
    """Test transportation cost calculator"""
    
    def test_road_transport(self):
        """Should calculate road transport cost"""
        calculator = TransportationCostCalculator()
        result = calculator.calculate(500, 500, TransportMode.ROAD)
        
        assert result['mode'] == 'road'
        assert result['total_cost'] > 0
    
    def test_air_transport_higher(self):
        """Air transport should be more expensive"""
        calculator = TransportationCostCalculator()
        road = calculator.calculate(500, 500, TransportMode.ROAD)
        air = calculator.calculate(500, 500, TransportMode.AIR)
        
        assert air['total_cost'] > road['total_cost']


class TestInsuranceCostCalculator:
    """Test insurance cost calculator"""
    
    def test_domestic_insurance(self):
        """Should calculate domestic insurance"""
        calculator = InsuranceCostCalculator()
        result = calculator.calculate(1000000, 'domestic')
        
        assert result['total_cost'] > 0
    
    def test_international_higher(self):
        """International insurance should be higher"""
        calculator = InsuranceCostCalculator()
        # Use larger values to ensure we exceed minimum premium
        domestic = calculator.calculate(1000000, 'domestic')
        international = calculator.calculate(1000000, 'international')
        
        assert international['total_cost'] > domestic['total_cost']


class TestPackagingCostAdder:
    """Test packaging cost adder"""
    
    def test_calculate_packaging(self):
        """Should calculate packaging cost"""
        adder = PackagingCostAdder()
        result = adder.calculate(500)
        
        assert result['total_cost'] > 0


class TestHandlingChargesCalculator:
    """Test handling charges calculator"""
    
    def test_calculate_handling(self):
        """Should calculate handling charges"""
        calculator = HandlingChargesCalculator()
        result = calculator.calculate(500)
        
        assert result['total_cost'] > 0
        assert result['base_charge'] == 500


class TestCustomsDutiesCalculator:
    """Test customs duties calculator"""
    
    def test_calculate_customs(self):
        """Should calculate customs duties"""
        calculator = CustomsDutiesCalculator()
        result = calculator.calculate(100000, 'electrical')
        
        assert result['basic_customs_duty'] > 0
        assert result['igst'] > 0
        assert result['total_cost'] > 0


# ============================================================================
# Tests 21-24: Subtotal, Contingency, Margin, Final Price
# ============================================================================

class TestSubtotalAggregator:
    """Test subtotal aggregator"""
    
    def test_aggregate_costs(self):
        """Should aggregate all costs"""
        aggregator = SubtotalAggregator()
        
        costs = {
            'material': 100000,
            'sample_testing': 5000,
            'type_testing': 25000,
            'routine_testing': 10000,
            'acceptance_testing': 15000,
            'certification': 50000,
            'logistics': 20000
        }
        
        result = aggregator.aggregate(costs)
        
        assert result['gross_total'] == 225000
        assert 'cost_breakdown' in result


class TestContingencyBuffer:
    """Test contingency buffer"""
    
    def test_default_contingency(self):
        """Should apply default contingency"""
        buffer = ContingencyBuffer()
        result = buffer.calculate(100000)
        
        assert result['contingency_percent'] == 5.0
        assert result['contingency_amount'] == 5000
    
    def test_custom_contingency(self):
        """Should apply custom contingency"""
        buffer = ContingencyBuffer()
        result = buffer.calculate(100000, percent=10)
        
        assert result['contingency_percent'] == 10.0
        assert result['contingency_amount'] == 10000


class TestMarginCalculator:
    """Test margin calculator"""
    
    def test_default_margin(self):
        """Should apply default margin"""
        calculator = MarginCalculator()
        result = calculator.calculate(100000)
        
        assert result['margin_percent'] == 15.0
        assert result['selling_price'] == 115000
    
    def test_custom_margin(self):
        """Should apply custom margin"""
        calculator = MarginCalculator()
        result = calculator.calculate(100000, target_margin=20)
        
        assert result['margin_percent'] == 20.0
        assert result['selling_price'] == 120000


class TestFinalPriceGenerator:
    """Test final price generator"""
    
    def test_with_gst(self):
        """Should add GST"""
        generator = FinalPriceGenerator()
        result = generator.generate(100000, include_gst=True)
        
        assert result['gst_amount'] == 18000
        assert result['final_price'] == 118000
    
    def test_without_gst(self):
        """Should not add GST when disabled"""
        generator = FinalPriceGenerator()
        result = generator.generate(100000, include_gst=False)
        
        assert result['gst_amount'] == 0
        assert result['final_price'] == 100000


# ============================================================================
# Tests 25-28: Competitive Analysis, Recommendations, Optimization, Win Probability
# ============================================================================

class TestCompetitiveAnalysis:
    """Test competitive analysis"""
    
    def test_analyze_competitive(self):
        """Should analyze competitive position"""
        analysis = CompetitiveAnalysis()
        result = analysis.analyze(95, 'wires', [100, 110, 90])
        
        assert result['position'] in ['lowest', 'below_average', 'above_average', 'highest']
        assert result['average_competitor_price'] == 100
    
    def test_price_index(self):
        """Should calculate price index"""
        analysis = CompetitiveAnalysis()
        result = analysis.analyze(100, 'wires', [100])
        
        assert result['price_index'] == 100.0


class TestPricingRecommendationEngine:
    """Test pricing recommendation engine"""
    
    def test_generate_recommendations(self):
        """Should generate recommendations"""
        engine = PricingRecommendationEngine()
        result = engine.recommend(100000, 15)
        
        assert len(result['recommendations']) >= 3
        assert 'aggressive' in [r['strategy'] for r in result['recommendations']]
        assert 'standard' in [r['strategy'] for r in result['recommendations']]


class TestPriceOptimization:
    """Test price optimization"""
    
    def test_optimize_for_profit(self):
        """Should optimize for profit"""
        optimizer = PriceOptimization()
        result = optimizer.optimize(100000, objective='profit')
        
        assert result['optimal_margin'] >= 15
    
    def test_optimize_for_volume(self):
        """Should optimize for volume"""
        optimizer = PriceOptimization()
        result = optimizer.optimize(100000, objective='volume')
        
        assert result['optimal_margin'] <= 10


class TestWinProbabilityEstimator:
    """Test win probability estimator"""
    
    def test_high_probability_low_price(self):
        """Low price should have high probability"""
        estimator = WinProbabilityEstimator()
        result = estimator.estimate(90, 100)
        
        assert result['win_probability'] > 0.5
    
    def test_low_probability_high_price(self):
        """High price should have lower probability"""
        estimator = WinProbabilityEstimator()
        result = estimator.estimate(120, 100)
        
        assert result['win_probability'] < 0.7


# ============================================================================
# Tests 29-33: Breakdown, Terms, Payment, Tables, Comparison
# ============================================================================

class TestPricingBreakdownGenerator:
    """Test pricing breakdown generator"""
    
    def test_generate_breakdown(self):
        """Should generate breakdown"""
        generator = PricingBreakdownGenerator()
        
        pricing_data = {
            'rfp_id': 'RFP_001',
            'products': [{'id': 'P1', 'name': 'Wire', 'quantity': 1000, 'unit_price': 25, 'total': 25000}],
            'tests': [],
            'grand_total': 30000
        }
        
        breakdown = generator.generate(pricing_data)
        
        assert breakdown.rfp_id == 'RFP_001'
        assert len(breakdown.material_costs) == 1


class TestCommercialTermsFormatter:
    """Test commercial terms formatter"""
    
    def test_format_terms(self):
        """Should format commercial terms"""
        formatter = CommercialTermsFormatter()
        terms = formatter.format()
        
        assert terms.payment_terms != ''
        assert terms.warranty_period != ''


class TestPaymentTermsGenerator:
    """Test payment terms generator"""
    
    def test_government_terms(self):
        """Should generate government terms"""
        generator = PaymentTermsGenerator()
        result = generator.generate(100000, 'government')
        
        assert result['customer_type'] == 'government'
        assert len(result['options']) >= 1
    
    def test_private_terms(self):
        """Should generate private terms"""
        generator = PaymentTermsGenerator()
        result = generator.generate(100000, 'private')
        
        assert len(result['options']) >= 2


class TestPricingTableCreator:
    """Test pricing table creator"""
    
    def test_create_table(self):
        """Should create pricing table"""
        creator = PricingTableCreator()
        
        breakdown = PricingBreakdown(
            breakdown_id='BRK_001',
            rfp_id='RFP_001',
            created_at=datetime.now(),
            material_costs=[LineItem(
                item_id='M1', description='Wire', category=CostCategory.MATERIAL,
                quantity=1000, unit='m', unit_price=25, total_price=25000
            )],
            testing_costs=[],
            certification_costs=[],
            logistics_costs=[],
            overhead_costs=[],
            subtotals={'material': 25000},
            contingency=1250,
            margin=3937.5,
            taxes={'gst': 5433.75},
            grand_total=35621.25
        )
        
        table = creator.create(breakdown)
        
        assert 'rows' in table
        assert len(table['rows']) == 1


class TestCostComparisonGenerator:
    """Test cost comparison generator"""
    
    def test_generate_comparison(self):
        """Should generate comparison"""
        generator = CostComparisonGenerator()
        
        scenarios = [
            {'name': 'Option A', 'total': 100000},
            {'name': 'Option B', 'total': 95000}
        ]
        
        result = generator.generate(scenarios)
        
        assert result['summary']['lowest_price'] == 95000
        assert result['summary']['highest_price'] == 100000


# ============================================================================
# Tests 34-37: Sensitivity, What-if, Summary, Line-item
# ============================================================================

class TestSensitivityAnalysis:
    """Test sensitivity analysis"""
    
    def test_analyze_sensitivity(self):
        """Should analyze sensitivity"""
        analysis = SensitivityAnalysis()
        result = analysis.analyze(100000, 15)
        
        assert 'sensitivity_results' in result
        assert len(result['sensitivity_results']) > 0


class TestWhatIfScenarioGenerator:
    """Test what-if scenario generator"""
    
    def test_generate_scenarios(self):
        """Should generate scenarios"""
        generator = WhatIfScenarioGenerator()
        base = {'grand_total': 100000, 'margin_percent': 15}
        
        scenarios = generator.generate(base)
        
        assert len(scenarios) >= 3
        assert 'aggressive_pricing' in [s['scenario'] for s in scenarios]


class TestPricingSummaryGenerator:
    """Test pricing summary generator"""
    
    def test_generate_summary(self):
        """Should generate markdown summary"""
        generator = PricingSummaryGenerator()
        
        breakdown = PricingBreakdown(
            breakdown_id='BRK_001',
            rfp_id='RFP_001',
            created_at=datetime.now(),
            material_costs=[],
            testing_costs=[],
            certification_costs=[],
            logistics_costs=[],
            overhead_costs=[],
            subtotals={'material': 100000},
            contingency=5000,
            margin=15000,
            taxes={'gst': 21600},
            grand_total=141600
        )
        
        summary = generator.generate(breakdown)
        
        assert '# Pricing Summary' in summary
        assert 'RFP_001' in summary


class TestDetailedLineItemBreakdown:
    """Test detailed line-item breakdown"""
    
    def test_create_breakdown(self):
        """Should create detailed breakdown"""
        creator = DetailedLineItemBreakdown()
        
        breakdown = PricingBreakdown(
            breakdown_id='BRK_001',
            rfp_id='RFP_001',
            created_at=datetime.now(),
            material_costs=[LineItem(
                item_id='M1', description='Wire', category=CostCategory.MATERIAL,
                quantity=1000, unit='m', unit_price=25, total_price=25000
            )],
            testing_costs=[],
            certification_costs=[],
            logistics_costs=[],
            overhead_costs=[],
            subtotals={'material': 25000},
            contingency=1250,
            margin=3937.5,
            taxes={'gst': 5433.75},
            grand_total=35621.25
        )
        
        result = creator.create(breakdown)
        
        assert result['item_count'] == 1
        assert len(result['summary']) > 0


# ============================================================================
# Tests 38-41: Validation, Approval, History, Analytics
# ============================================================================

class TestPricingValidator:
    """Test pricing validator"""
    
    def test_validate_valid_pricing(self):
        """Should validate valid pricing"""
        validator = PricingValidator()
        
        pricing = {
            'rfp_id': 'RFP_001',
            'grand_total': 100000,
            'margin_percent': 15
        }
        
        result = validator.validate(pricing)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_invalid_pricing(self):
        """Should detect invalid pricing"""
        validator = PricingValidator()
        
        pricing = {'grand_total': 0}  # Missing rfp_id
        
        result = validator.validate(pricing)
        
        assert result['valid'] is False


class TestPricingApprovalWorkflow:
    """Test pricing approval workflow"""
    
    def test_submit_for_approval(self):
        """Should submit for approval"""
        workflow = PricingApprovalWorkflow()
        
        approval = workflow.submit_for_approval(
            'PRC_001', 'RFP_001', 500000, 'user1'
        )
        
        assert approval.status == ApprovalStatus.PENDING
    
    def test_auto_approve_small_amount(self):
        """Should auto-approve small amounts"""
        workflow = PricingApprovalWorkflow()
        
        approval = workflow.submit_for_approval(
            'PRC_001', 'RFP_001', 50000, 'user1'
        )
        
        assert approval.status == ApprovalStatus.APPROVED
    
    def test_approve(self):
        """Should approve pricing"""
        workflow = PricingApprovalWorkflow()
        approval = workflow.submit_for_approval('PRC_001', 'RFP_001', 500000, 'user1')
        
        approved = workflow.approve(approval.approval_id, 'manager1')
        
        assert approved.status == ApprovalStatus.APPROVED


class TestPricingHistoryTracker:
    """Test pricing history tracker"""
    
    def test_record_event(self):
        """Should record event"""
        tracker = PricingHistoryTracker()
        
        event_id = tracker.record('created', 'PRC_001', {'amount': 100000})
        
        assert event_id is not None
    
    def test_get_history(self):
        """Should get history"""
        tracker = PricingHistoryTracker()
        tracker.record('created', 'PRC_001', {})
        tracker.record('updated', 'PRC_001', {})
        
        history = tracker.get_history('PRC_001')
        
        assert len(history) == 2


class TestPricingAnalytics:
    """Test pricing analytics"""
    
    def test_add_data(self):
        """Should add analytics data"""
        analytics = PricingAnalytics()
        
        analytics.add_data({'rfp_id': 'RFP_001', 'grand_total': 100000, 'margin_percent': 15})
        
        result = analytics.get_analytics()
        
        assert result['total_quotes'] == 1
    
    def test_calculate_averages(self):
        """Should calculate averages"""
        analytics = PricingAnalytics()
        
        analytics.add_data({'rfp_id': 'R1', 'grand_total': 100000, 'margin_percent': 15})
        analytics.add_data({'rfp_id': 'R2', 'grand_total': 200000, 'margin_percent': 20})
        
        result = analytics.get_analytics()
        
        assert result['average_quote_value'] == 150000


# ============================================================================
# Tests 42-43: Logging and Error Handling
# ============================================================================

class TestPricingAgentLogger:
    """Test pricing agent logger"""
    
    def test_logger_initialization(self, tmp_path):
        """Should initialize logger"""
        logger = PricingAgentLogger("TEST", str(tmp_path))
        
        logger.info("Test message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Should not raise


class TestPricingErrorHandler:
    """Test error handler"""
    
    def test_with_retry_success(self):
        """Should succeed on first try"""
        handler = PricingErrorHandler()
        
        success, result = handler.with_retry(lambda: 42, "test_op")
        
        assert success is True
        assert result == 42
    
    def test_with_retry_failure(self):
        """Should fail after max retries"""
        handler = PricingErrorHandler(max_retries=2)
        
        def failing():
            raise Exception("Fail")
        
        success, result = handler.with_retry(failing, "failing_op")
        
        assert success is False


# ============================================================================
# Tests 45-49: Mock, Metrics, Dashboard, Real-time
# ============================================================================

class TestMockDataHandler:
    """Test mock data handler"""
    
    def test_get_mock_products(self):
        """Should return mock products"""
        products = MockDataHandler.get_mock_products()
        
        assert len(products) >= 1
        assert 'selected_sku' in products[0]
    
    def test_get_mock_tests(self):
        """Should return mock tests"""
        tests = MockDataHandler.get_mock_tests()
        
        assert len(tests) >= 1
    
    def test_get_mock_pricing_input(self):
        """Should return complete mock input"""
        input_data = MockDataHandler.get_mock_pricing_input()
        
        assert 'rfp_id' in input_data
        assert 'recommendations' in input_data


class TestPricingMetrics:
    """Test pricing metrics"""
    
    def test_record_quote(self):
        """Should record quote"""
        metrics = PricingMetrics()
        metrics.record_quote(100000, 150.5)
        
        stats = metrics.get_stats()
        
        assert stats['total_quotes'] == 1
        assert stats['avg_processing_time_ms'] == 150.5
    
    def test_record_error(self):
        """Should record error"""
        metrics = PricingMetrics()
        metrics.record_error()
        
        stats = metrics.get_stats()
        
        assert stats['error_count'] == 1


class TestPricingDashboard:
    """Test pricing dashboard"""
    
    def test_get_dashboard_data(self):
        """Should return dashboard data"""
        metrics = PricingMetrics()
        analytics = PricingAnalytics()
        dashboard = PricingDashboard(metrics, analytics)
        
        data = dashboard.get_dashboard_data()
        
        assert 'metrics' in data
        assert 'analytics' in data


class TestRealTimeUpdater:
    """Test real-time updater"""
    
    def test_subscribe_and_publish(self):
        """Should notify subscribers"""
        updater = RealTimeUpdater()
        received = []
        
        updater.subscribe(lambda u: received.append(u))
        updater.publish({'event': 'test'})
        
        assert len(received) == 1
        assert received[0]['event'] == 'test'


# ============================================================================
# Test 51: API Interface
# ============================================================================

class TestPricingAgentAPI:
    """Test API interface"""
    
    def test_handle_health(self, pricing_agent):
        """Should handle health request"""
        response = pricing_agent.api.handle_request('health', {})
        
        assert response['status'] == 200
        assert response['data']['healthy'] is True
    
    def test_handle_status(self, pricing_agent):
        """Should handle status request"""
        response = pricing_agent.api.handle_request('get_status', {})
        
        assert response['status'] == 200
        assert response['data']['agent_id'] == 'TEST_AGENT'
    
    def test_handle_unknown_endpoint(self, pricing_agent):
        """Should handle unknown endpoint"""
        response = pricing_agent.api.handle_request('unknown', {})
        
        assert response['status'] == 404


# ============================================================================
# Test Data Classes
# ============================================================================

class TestDataClasses:
    """Test data class creation"""
    
    def test_product_price_entry(self, sample_product_price):
        """Should create ProductPriceEntry"""
        assert sample_product_price.sku == "SKU_WIRE_001"
        assert sample_product_price.base_price == 25.0
    
    def test_test_cost_entry(self, sample_test_cost):
        """Should create TestCostEntry"""
        assert sample_test_cost.test_type == TestType.ROUTINE_TEST
        assert sample_test_cost.base_cost == 5000.0
    
    def test_line_item(self):
        """Should create LineItem"""
        item = LineItem(
            item_id='L1',
            description='Test Item',
            category=CostCategory.MATERIAL,
            quantity=100,
            unit='pcs',
            unit_price=50,
            total_price=5000
        )
        assert item.total_price == 5000
    
    def test_commercial_terms(self):
        """Should create CommercialTerms"""
        terms = CommercialTerms(
            payment_terms='30 days',
            delivery_terms='Ex-works',
            warranty_period='12 months',
            validity_period='30 days',
            price_escalation_clause='Fixed',
            penalties=[],
            exclusions=[],
            special_conditions=[]
        )
        assert terms.payment_terms == '30 days'


# ============================================================================
# Test Enums
# ============================================================================

class TestEnums:
    """Test enum values"""
    
    def test_approval_status(self):
        """Should have all approval statuses"""
        statuses = [s.value for s in ApprovalStatus]
        assert 'pending' in statuses
        assert 'approved' in statuses
        assert 'rejected' in statuses
    
    def test_price_confidence(self):
        """Should have all confidence levels"""
        levels = [c.value for c in PriceConfidence]
        assert 'high' in levels
        assert 'estimated' in levels
    
    def test_cost_category(self):
        """Should have all cost categories"""
        categories = [c.value for c in CostCategory]
        assert 'material' in categories
        assert 'testing' in categories
        assert 'logistics' in categories
    
    def test_test_type(self):
        """Should have all test types"""
        types = [t.value for t in TestType]
        assert 'type_test' in types
        assert 'routine_test' in types


# ============================================================================
# Integration Tests
# ============================================================================

class TestPricingAgentIntegration:
    """Integration tests"""
    
    def test_get_status(self, pricing_agent):
        """Should return status"""
        status = pricing_agent.get_status()
        
        assert status['agent_id'] == 'TEST_AGENT'
        assert 'metrics' in status
    
    def test_generate_commercial_terms(self, pricing_agent):
        """Should generate commercial terms"""
        terms = pricing_agent.generate_commercial_terms(100000, 'government')
        
        assert 'terms' in terms
        assert 'payment_options' in terms
    
    def test_run_sensitivity_analysis(self, pricing_agent):
        """Should run sensitivity analysis"""
        result = pricing_agent.run_sensitivity_analysis(100000, 15)
        
        assert 'sensitivity_results' in result
    
    def test_get_recommendations(self, pricing_agent):
        """Should get recommendations"""
        result = pricing_agent.get_recommendations(100000, 15)
        
        assert 'recommendations' in result
        assert len(result['recommendations']) >= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
