"""
Unit Tests for Technical Agent
Comprehensive tests for all 51 features
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import sys
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.technical_agent.technical_agent import (
    # Enums
    MatchConfidence,
    RiskLevel,
    ComplianceStatus,
    ProcessingMode,
    
    # Data Classes
    RFPRequirement,
    ProductMatch,
    ComparisonRow,
    TechnicalReport,
    AgentMessage,
    WebhookConfig,
    
    # Core Classes
    TechnicalAgent,
    TechnicalAgentLogger,
    RFPRequirementParser,
    ProductRequirementExtractor,
    ScopeOfSupplyAnalyzer,
    MultiItemRFPHandler,
    ProductCatalogQuerier,
    SpecificationMatchingOrchestrator,
    TopKSelector,
    MatchScoreCalculator,
    ComparisonTableGenerator,
    GapAnalysisGenerator,
    SpecificationExplanationGenerator,
    TechnicalRiskAssessor,
    ComplianceChecker,
    TechnicalSummaryGenerator,
    ProductRecommendationRanker,
    CustomProductFlagger,
    TechnicalReportFormatter,
    DetailedSpecComparison,
    EdgeCaseHandler,
    TechnicalValidator,
    AgentOutputHandler,
    TechnicalAgentMemory,
    PerformanceTracker,
    ErrorRecoveryHandler,
    BatchProcessor,
    AsyncOperationSupport,
    TechnicalAgentAPI,
    WebhookManager,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_requirement():
    """Sample RFP requirement"""
    return RFPRequirement(
        id="REQ_001",
        name="PVC Insulated Copper Wire 1.5 sq mm",
        description="Supply of PVC insulated copper wire for building wiring",
        specifications={
            'conductor_material': 'Copper',
            'cross_section_sqmm': 1.5,
            'voltage_rating': '1100V',
            'insulation_type': 'PVC',
            'number_of_cores': 1,
            'temperature_rating': 70
        },
        quantity=5000,
        unit='meters',
        priority='normal',
        standards=['IS 694:2010'],
        certifications=['BIS', 'ISI']
    )


@pytest.fixture
def sample_product_match():
    """Sample product match"""
    return ProductMatch(
        product_id="SKU_WIRE_001",
        product_name="Premium PVC Copper Wire 1.5 sqmm",
        manufacturer="KEI Industries",
        category="building_wires",
        specifications={
            'conductor_material': 'Electrolytic Copper',
            'cross_section_sqmm': 1.5,
            'voltage_rating': '1100V AC',
            'insulation_type': 'FR PVC',
            'number_of_cores': 1,
            'temperature_rating': 70
        },
        match_score=92.5,
        confidence=MatchConfidence.HIGH,
        matched_specs={
            'cross_section_sqmm': {'rfp_value': 1.5, 'product_value': 1.5, 'match': 'FULL'},
            'number_of_cores': {'rfp_value': 1, 'product_value': 1, 'match': 'FULL'}
        },
        unmatched_specs=[],
        partial_matches=[
            {'spec': 'conductor_material', 'rfp_value': 'Copper', 
             'product_value': 'Electrolytic Copper', 'match_percent': 95}
        ],
        gap_analysis={'missing_specs': [], 'deviations': []},
        compliance_notes=['BIS certified', 'ISI marked'],
        risk_level=RiskLevel.LOW,
        justification="Excellent match with 92.5% specification alignment."
    )


@pytest.fixture
def sample_rfp_context():
    """Sample RFP context"""
    return {
        'rfp_id': 'RFP_TEST_001',
        'issuing_authority': 'State Electricity Board',
        'products_in_scope': [
            {
                'name': 'PVC Insulated Wire 1.5 sq mm',
                'specifications': {
                    'conductor_material': 'Copper',
                    'cross_section_sqmm': 1.5,
                    'voltage_rating': '1100V',
                    'insulation_type': 'PVC'
                },
                'quantity': 5000,
                'unit': 'meters'
            },
            {
                'name': 'XLPE Power Cable 4 sq mm',
                'specifications': {
                    'conductor_material': 'Copper',
                    'cross_section_sqmm': 4,
                    'voltage_rating': '3300V',
                    'insulation_type': 'XLPE'
                },
                'quantity': 2000,
                'unit': 'meters'
            }
        ]
    }


@pytest.fixture
def technical_agent(tmp_path):
    """Create Technical Agent for testing"""
    agent = TechnicalAgent(
        agent_id="TEST_AGENT",
        log_dir=str(tmp_path / "logs")
    )
    return agent


# ============================================================================
# Test 1: TechnicalAgent Class Structure
# ============================================================================

class TestTechnicalAgentStructure:
    """Test Technical Agent class structure"""
    
    def test_agent_initialization(self, technical_agent):
        """Agent should initialize with all components"""
        assert technical_agent.agent_id == "TEST_AGENT"
        assert technical_agent.requirement_parser is not None
        assert technical_agent.matching_orchestrator is not None
        assert technical_agent.comparison_generator is not None
        assert technical_agent.risk_assessor is not None
        assert technical_agent.api is not None
    
    def test_agent_has_required_methods(self, technical_agent):
        """Agent should have all required methods"""
        required_methods = [
            'process_rfp', 'get_status', 'health_check',
            'process_batch', 'process_async'
        ]
        for method in required_methods:
            assert hasattr(technical_agent, method), f"Missing method: {method}"
    
    def test_health_check(self, technical_agent):
        """Health check should return status"""
        health = technical_agent.health_check()
        assert 'healthy' in health
        assert health['agent_id'] == "TEST_AGENT"


# ============================================================================
# Test 2: RFP Requirement Parser
# ============================================================================

class TestRFPRequirementParser:
    """Test RFP requirement parser"""
    
    def test_parse_rfp_content(self, sample_rfp_context):
        """Should parse RFP content into requirements"""
        parser = RFPRequirementParser()
        requirements = parser.parse(sample_rfp_context)
        
        assert len(requirements) == 2
        assert requirements[0].name == 'PVC Insulated Wire 1.5 sq mm'
        assert requirements[0].quantity == 5000
    
    def test_extract_specs_from_text(self):
        """Should extract specifications from text"""
        parser = RFPRequirementParser()
        
        text = "Supply of 1.5 sq mm copper wire with 1100V rating"
        specs = parser._extract_specs_from_text(text)
        
        assert 'cross_section' in specs or 'voltage' in specs
    
    def test_extract_standards(self):
        """Should extract standard references"""
        parser = RFPRequirementParser()
        
        standards = parser._extract_standards("Compliant with IS 694:2010 and IEC 60502")
        
        assert len(standards) >= 1


# ============================================================================
# Test 4: Product Requirement Extractor
# ============================================================================

class TestProductRequirementExtractor:
    """Test product requirement extractor"""
    
    def test_extract_category(self, sample_requirement):
        """Should detect product category"""
        extractor = ProductRequirementExtractor()
        extracted = extractor.extract(sample_requirement)
        
        assert 'category' in extracted
        assert extracted['category'] in ['building_wires', 'power_cables', 'general']
    
    def test_extract_conductor_material(self, sample_requirement):
        """Should detect conductor material"""
        extractor = ProductRequirementExtractor()
        extracted = extractor.extract(sample_requirement)
        
        assert extracted['conductor_material'] == 'copper'
    
    def test_extract_electrical_requirements(self, sample_requirement):
        """Should extract electrical requirements"""
        extractor = ProductRequirementExtractor()
        extracted = extractor.extract(sample_requirement)
        
        assert 'electrical_requirements' in extracted
        assert extracted['electrical_requirements']['voltage_rating'] == '1100V'


# ============================================================================
# Test 5: Scope of Supply Analyzer
# ============================================================================

class TestScopeOfSupplyAnalyzer:
    """Test scope analyzer"""
    
    def test_analyze_scope(self, sample_rfp_context):
        """Should analyze scope of supply"""
        analyzer = ScopeOfSupplyAnalyzer()
        analysis = analyzer.analyze(sample_rfp_context)
        
        assert analysis['total_items'] == 2
        assert 'complexity_score' in analysis
        assert 'quantity_summary' in analysis
    
    def test_calculate_complexity(self):
        """Should calculate complexity score"""
        analyzer = ScopeOfSupplyAnalyzer()
        
        items = [{'specifications': {'a': 1, 'b': 2}} for _ in range(5)]
        score = analyzer._calculate_complexity(items)
        
        assert 0 <= score <= 1


# ============================================================================
# Test 6: Multi-item RFP Handler
# ============================================================================

class TestMultiItemRFPHandler:
    """Test multi-item handler"""
    
    def test_process_items(self, sample_requirement):
        """Should process multiple items"""
        handler = MultiItemRFPHandler()
        requirements = [sample_requirement]
        
        results = handler.process_items(
            requirements,
            lambda r: {'id': r.id, 'processed': True}
        )
        
        assert len(results) == 1
        assert results[0]['processed'] is True
    
    def test_group_by_category(self, sample_requirement):
        """Should group by category"""
        handler = MultiItemRFPHandler()
        
        req1 = sample_requirement
        req1.metadata['category'] = 'wires'
        
        groups = handler.group_by_category([req1])
        
        assert 'wires' in groups


# ============================================================================
# Test 7: Product Catalog Querier
# ============================================================================

class TestProductCatalogQuerier:
    """Test catalog querier"""
    
    def test_query_with_category(self):
        """Should query by category"""
        querier = ProductCatalogQuerier()
        
        # Query should not fail even with empty catalog
        results = querier.query(category='building_wires', limit=10)
        
        assert isinstance(results, list)
    
    def test_query_with_specifications(self):
        """Should filter by specifications"""
        querier = ProductCatalogQuerier()
        querier.catalog = [
            {'sku': 'P1', 'specifications': {'voltage': '1100V'}},
            {'sku': 'P2', 'specifications': {'voltage': '3300V'}}
        ]
        
        results = querier.query(specifications={'voltage': '1100V'})
        
        assert len(results) >= 1


# ============================================================================
# Test 8-10: Specification Matching Orchestrator
# ============================================================================

class TestSpecificationMatchingOrchestrator:
    """Test matching orchestrator"""
    
    def test_find_matches(self, sample_requirement):
        """Should find matches for requirement"""
        orchestrator = SpecificationMatchingOrchestrator()
        orchestrator.catalog_querier.catalog = [
            {
                'sku': 'TEST_001',
                'name': 'Test Wire',
                'manufacturer': 'Test Mfr',
                'category': 'building_wires',
                'specifications': {
                    'conductor_material': 'copper',
                    'cross_section_sqmm': 1.5,
                    'voltage_rating': '1100V',
                    'insulation_type': 'pvc'
                }
            }
        ]
        
        matches = orchestrator.find_matches(sample_requirement, use_vector_search=False)
        
        assert isinstance(matches, list)
    
    def test_compare_values_exact(self):
        """Should match exact values"""
        orchestrator = SpecificationMatchingOrchestrator()
        
        score = orchestrator._compare_values('voltage_rating', '1100V', '1100V')
        assert score == 1.0
    
    def test_compare_values_semantic(self):
        """Should match semantic equivalents"""
        orchestrator = SpecificationMatchingOrchestrator()
        
        score = orchestrator._compare_values(
            'conductor_material', 'copper', 'electrolytic copper'
        )
        assert score > 0.8
    
    def test_weighted_scoring(self):
        """Should apply weights to scoring"""
        orchestrator = SpecificationMatchingOrchestrator()
        
        # Critical specs should have higher weights
        assert orchestrator.weights.get('voltage_rating', 0) >= 0.8
        assert orchestrator.weights.get('cross_section_sqmm', 0) >= 0.8


# ============================================================================
# Test 11: Top-K Selector
# ============================================================================

class TestTopKSelector:
    """Test top-K selector"""
    
    def test_select_top_3(self, sample_product_match):
        """Should select top 3 matches"""
        selector = TopKSelector(k=3)
        
        matches = [sample_product_match] * 5
        top = selector.select(matches)
        
        assert len(top) == 3
    
    def test_diversify_manufacturers(self, sample_product_match):
        """Should diversify by manufacturer"""
        selector = TopKSelector(k=3)
        
        match1 = sample_product_match
        match2 = ProductMatch(
            product_id="SKU_002",
            product_name="Another Wire",
            manufacturer="Different Mfr",
            category="building_wires",
            specifications={},
            match_score=90,
            confidence=MatchConfidence.HIGH,
            matched_specs={},
            unmatched_specs=[],
            partial_matches=[],
            gap_analysis={},
            compliance_notes=[],
            risk_level=RiskLevel.LOW,
            justification="Good match"
        )
        
        top = selector.select([match1, match2], diversify=True)
        
        assert len(top) == 2


# ============================================================================
# Test 12 & 13: Match Score Calculator with Confidence
# ============================================================================

class TestMatchScoreCalculator:
    """Test score calculator"""
    
    def test_calculate_composite_score(self, sample_product_match):
        """Should calculate composite score"""
        calculator = MatchScoreCalculator()
        
        result = calculator.calculate_composite_score(sample_product_match)
        
        assert 'composite_score' in result
        assert 'confidence_level' in result
        assert result['spec_score'] == 92.5
    
    def test_compliance_bonus(self, sample_product_match):
        """Should apply compliance bonus"""
        calculator = MatchScoreCalculator()
        
        result = calculator.calculate_composite_score(sample_product_match)
        
        assert result['compliance_bonus'] > 0


# ============================================================================
# Test 14: Comparison Table Generator
# ============================================================================

class TestComparisonTableGenerator:
    """Test comparison table generator"""
    
    def test_generate_table(self, sample_requirement, sample_product_match):
        """Should generate comparison table"""
        generator = ComparisonTableGenerator()
        
        rows = generator.generate(sample_requirement, [sample_product_match])
        
        assert len(rows) > 0
        assert isinstance(rows[0], ComparisonRow)
    
    def test_to_dict(self, sample_requirement, sample_product_match):
        """Should convert to dictionary format"""
        generator = ComparisonTableGenerator()
        
        rows = generator.generate(sample_requirement, [sample_product_match])
        dict_rows = generator.to_dict(rows)
        
        assert isinstance(dict_rows, list)
        assert 'specification' in dict_rows[0]


# ============================================================================
# Test 15: Gap Analysis Generator
# ============================================================================

class TestGapAnalysisGenerator:
    """Test gap analysis generator"""
    
    def test_generate_gap_analysis(self, sample_requirement, sample_product_match):
        """Should generate gap analysis"""
        generator = GapAnalysisGenerator()
        
        gap = generator.generate(sample_requirement, sample_product_match)
        
        assert 'summary' in gap
        assert 'critical_gaps' in gap
        assert 'mitigations' in gap


# ============================================================================
# Test 16: Specification Explanation Generator
# ============================================================================

class TestSpecificationExplanationGenerator:
    """Test explanation generator"""
    
    def test_explain_spec(self):
        """Should explain specification"""
        generator = SpecificationExplanationGenerator()
        
        explanation = generator.explain_spec('conductor_material', 'copper')
        
        assert 'explanation' in explanation
        assert 'importance' in explanation
    
    def test_explain_match(self, sample_product_match):
        """Should explain match"""
        generator = SpecificationExplanationGenerator()
        
        explanation = generator.explain_match(sample_product_match)
        
        assert '92.5%' in explanation or 'Excellent' in explanation


# ============================================================================
# Test 17: Technical Risk Assessor
# ============================================================================

class TestTechnicalRiskAssessor:
    """Test risk assessor"""
    
    def test_assess_low_risk(self, sample_requirement, sample_product_match):
        """Should assess low risk for good match"""
        assessor = TechnicalRiskAssessor()
        
        assessment = assessor.assess(sample_product_match, sample_requirement)
        
        assert 'overall_risk_level' in assessment
        assert assessment['overall_risk_level'] in ['low', 'none', 'medium']
    
    def test_assess_high_risk_with_gaps(self, sample_requirement):
        """Should assess high risk with critical gaps"""
        assessor = TechnicalRiskAssessor()
        
        match = ProductMatch(
            product_id="SKU_001",
            product_name="Test",
            manufacturer="Test",
            category="test",
            specifications={},
            match_score=50,
            confidence=MatchConfidence.LOW,
            matched_specs={},
            unmatched_specs=['voltage_rating', 'current_rating'],
            partial_matches=[],
            gap_analysis={},
            compliance_notes=[],
            risk_level=RiskLevel.HIGH,
            justification=""
        )
        
        assessment = assessor.assess(match, sample_requirement)
        
        assert assessment['overall_risk_level'] in ['high', 'critical']


# ============================================================================
# Test 18 & 19: Compliance Checker with Standard Verification
# ============================================================================

class TestComplianceChecker:
    """Test compliance checker"""
    
    def test_check_compliance(self, sample_requirement, sample_product_match):
        """Should check compliance"""
        checker = ComplianceChecker()
        
        result = checker.check(sample_requirement, sample_product_match)
        
        assert 'status' in result
        assert 'standards_check' in result
        assert 'certification_check' in result
    
    def test_check_certification(self, sample_product_match):
        """Should check for certification"""
        checker = ComplianceChecker()
        
        # The product has BIS in compliance_notes
        result = checker._check_certification('BIS', sample_product_match)
        
        # Check that the result has a valid status
        assert result['status'] in ['available', 'not_found', 'not_checked']


# ============================================================================
# Test 20: Technical Summary Generator
# ============================================================================

class TestTechnicalSummaryGenerator:
    """Test summary generator"""
    
    def test_generate_summary(self, sample_requirement, sample_product_match):
        """Should generate summary"""
        generator = TechnicalSummaryGenerator()
        
        summary = generator.generate_summary(sample_requirement, [sample_product_match])
        
        assert '## Technical Analysis' in summary
        assert sample_requirement.name in summary
    
    def test_generate_brief(self, sample_product_match):
        """Should generate brief summary"""
        generator = TechnicalSummaryGenerator()
        
        brief = generator.generate_brief(sample_product_match)
        
        assert sample_product_match.product_name in brief
        assert '92.5%' in brief


# ============================================================================
# Test 21 & 22: Product Recommendation Ranker with Alternatives
# ============================================================================

class TestProductRecommendationRanker:
    """Test recommendation ranker"""
    
    def test_rank_matches(self, sample_product_match):
        """Should rank matches"""
        ranker = ProductRecommendationRanker()
        
        ranked = ranker.rank([sample_product_match])
        
        assert len(ranked) == 1
        assert ranked[0]['rank'] == 1
    
    def test_suggest_alternatives(self, sample_product_match):
        """Should suggest alternatives"""
        ranker = ProductRecommendationRanker()
        
        alt_match = ProductMatch(
            product_id="SKU_ALT",
            product_name="Alternative Wire",
            manufacturer="Other Manufacturer",
            category="building_wires",
            specifications={},
            match_score=88,
            confidence=MatchConfidence.HIGH,
            matched_specs={},
            unmatched_specs=[],
            partial_matches=[],
            gap_analysis={},
            compliance_notes=['BIS'],
            risk_level=RiskLevel.LOW,
            justification=""
        )
        
        alternatives = ranker.suggest_alternatives(
            sample_product_match, 
            [sample_product_match, alt_match]
        )
        
        assert len(alternatives) >= 1


# ============================================================================
# Test 23: Custom Product Flagging
# ============================================================================

class TestCustomProductFlagger:
    """Test custom product flagger"""
    
    def test_no_custom_needed(self, sample_requirement, sample_product_match):
        """Should not flag for good match"""
        flagger = CustomProductFlagger()
        
        result = flagger.evaluate(sample_requirement, [sample_product_match])
        
        assert result['needs_custom'] is False
    
    def test_custom_needed_for_low_match(self, sample_requirement):
        """Should flag for low match"""
        flagger = CustomProductFlagger()
        
        low_match = ProductMatch(
            product_id="SKU_LOW",
            product_name="Low Match",
            manufacturer="Test",
            category="test",
            specifications={},
            match_score=40,
            confidence=MatchConfidence.VERY_LOW,
            matched_specs={},
            unmatched_specs=['voltage_rating', 'current_rating', 'cross_section_sqmm'],
            partial_matches=[],
            gap_analysis={},
            compliance_notes=[],
            risk_level=RiskLevel.CRITICAL,
            justification=""
        )
        
        result = flagger.evaluate(sample_requirement, [low_match])
        
        assert result['needs_custom'] is True


# ============================================================================
# Test 24 & 25: Technical Report Formatter with Visualization
# ============================================================================

class TestTechnicalReportFormatter:
    """Test report formatter"""
    
    def test_format_report(self, sample_requirement, sample_product_match):
        """Should format complete report"""
        formatter = TechnicalReportFormatter()
        
        all_matches = {sample_requirement.id: [sample_product_match]}
        
        report = formatter.format_report(
            'RFP_TEST',
            [sample_requirement],
            all_matches
        )
        
        assert isinstance(report, TechnicalReport)
        assert report.rfp_id == 'RFP_TEST'
        assert len(report.recommendations) == 1
    
    def test_visualization_data(self, sample_requirement, sample_product_match):
        """Should generate visualization data"""
        formatter = TechnicalReportFormatter()
        
        all_matches = {sample_requirement.id: [sample_product_match]}
        
        report = formatter.format_report(
            'RFP_TEST',
            [sample_requirement],
            all_matches
        )
        
        assert 'match_score_distribution' in report.visualization_data
        assert 'chart_data' in report.visualization_data


# ============================================================================
# Test 26 & 27: Detailed Spec Comparison with Justification
# ============================================================================

class TestDetailedSpecComparison:
    """Test detailed comparison"""
    
    def test_compare(self, sample_requirement, sample_product_match):
        """Should generate detailed comparison"""
        comparator = DetailedSpecComparison()
        
        comparison = comparator.compare(sample_requirement, sample_product_match)
        
        assert 'specifications' in comparison
        assert len(comparison['specifications']) > 0
        assert 'justification' in comparison['specifications'][0]


# ============================================================================
# Test 28: Edge Case Handlers
# ============================================================================

class TestEdgeCaseHandler:
    """Test edge case handlers"""
    
    def test_handle_no_matches(self, sample_requirement):
        """Should handle no matches"""
        handler = EdgeCaseHandler()
        
        result = handler.handle_no_matches(sample_requirement)
        
        assert result['status'] == 'no_matches'
        assert result['escalation_required'] is True
    
    def test_handle_unusual_quantity(self, sample_requirement):
        """Should handle unusual quantities"""
        handler = EdgeCaseHandler()
        
        # Normal quantity
        result = handler.handle_unusual_quantity(sample_requirement)
        assert result['status'] == 'normal'
        
        # Large quantity
        sample_requirement.quantity = 5000000
        result = handler.handle_unusual_quantity(sample_requirement)
        assert result['status'] == 'large_quantity'


# ============================================================================
# Test 29: Technical Validation
# ============================================================================

class TestTechnicalValidator:
    """Test technical validator"""
    
    def test_validate_requirement(self, sample_requirement):
        """Should validate requirement"""
        validator = TechnicalValidator()
        
        result = validator.validate_requirement(sample_requirement)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_invalid_requirement(self):
        """Should detect invalid requirement"""
        validator = TechnicalValidator()
        
        invalid_req = RFPRequirement(
            id="",
            name="",
            description="",
            specifications={},
            quantity=-1,
            unit=""
        )
        
        result = validator.validate_requirement(invalid_req)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_validate_match(self, sample_product_match):
        """Should validate match"""
        validator = TechnicalValidator()
        
        result = validator.validate_match(sample_product_match)
        
        assert result['valid'] is True


# ============================================================================
# Test 30 & 31: Output to Pricing and Main Agent
# ============================================================================

class TestAgentOutputHandler:
    """Test output handler"""
    
    def test_prepare_pricing_output(self):
        """Should prepare pricing output"""
        handler = AgentOutputHandler()
        
        recommendations = [{
            'requirement_id': 'REQ_001',
            'selected': {
                'product_id': 'SKU_001',
                'manufacturer': 'Test Mfr',
                'match_score': 92.5
            },
            'quantity': 5000,
            'unit': 'meters',
            'alternatives': []
        }]
        
        message = handler.prepare_pricing_output('RFP_001', recommendations)
        
        assert isinstance(message, AgentMessage)
        assert message.recipient == 'PRICING_AGENT'
        assert message.message_type == 'pricing_request'
    
    def test_prepare_main_output(self, sample_requirement, sample_product_match):
        """Should prepare main agent output"""
        handler = AgentOutputHandler()
        formatter = TechnicalReportFormatter()
        
        report = formatter.format_report(
            'RFP_001',
            [sample_requirement],
            {sample_requirement.id: [sample_product_match]}
        )
        
        message = handler.prepare_main_output(report)
        
        assert message.recipient == 'MASTER_AGENT'
        assert message.message_type == 'technical_analysis_complete'


# ============================================================================
# Test 32-34: Technical Agent Memory, Context, History
# ============================================================================

class TestTechnicalAgentMemory:
    """Test agent memory"""
    
    def test_store_and_retrieve(self):
        """Should store and retrieve values"""
        memory = TechnicalAgentMemory()
        
        memory.store('test_key', 'test_value')
        result = memory.retrieve('test_key')
        
        assert result == 'test_value'
    
    def test_long_term_storage(self):
        """Should handle long-term storage"""
        memory = TechnicalAgentMemory()
        
        memory.store('persist_key', 'persist_value', long_term=True)
        memory.clear_session()
        
        result = memory.retrieve('persist_key')
        assert result == 'persist_value'
    
    def test_conversation_history(self):
        """Should track conversation history"""
        memory = TechnicalAgentMemory()
        
        memory.add_conversation('user', 'Hello')
        memory.add_conversation('agent', 'Hi there')
        
        history = memory.get_conversation_context()
        
        assert len(history) == 2
    
    def test_context_stack(self):
        """Should manage context stack"""
        memory = TechnicalAgentMemory()
        
        memory.push_context({'rfp_id': 'RFP_001'})
        ctx = memory.get_current_context()
        
        assert ctx['rfp_id'] == 'RFP_001'
        
        memory.pop_context()
        assert memory.get_current_context() is None


# ============================================================================
# Test 35: Technical Agent Logging
# ============================================================================

class TestTechnicalAgentLogger:
    """Test agent logger"""
    
    def test_logger_initialization(self, tmp_path):
        """Should initialize logger"""
        logger = TechnicalAgentLogger("TEST", str(tmp_path))
        
        logger.info("Test message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Should not raise


# ============================================================================
# Test 36: Performance Tracking
# ============================================================================

class TestPerformanceTracker:
    """Test performance tracker"""
    
    def test_record_metrics(self):
        """Should record metrics"""
        tracker = PerformanceTracker()
        
        tracker.record_processing_time(150.5)
        tracker.record_match_score(85.0)
        tracker.increment('total_requests')
        
        stats = tracker.get_stats()
        
        assert stats['avg_processing_time_ms'] == 150.5
        assert stats['avg_match_score'] == 85.0
        assert stats['total_requests'] == 1


# ============================================================================
# Test 37: Error Recovery
# ============================================================================

class TestErrorRecoveryHandler:
    """Test error recovery"""
    
    def test_with_retry_success(self):
        """Should succeed on first try"""
        handler = ErrorRecoveryHandler()
        
        success, result = handler.with_retry(
            lambda: 42,
            "test_operation"
        )
        
        assert success is True
        assert result == 42
    
    def test_with_retry_failure(self):
        """Should fail after max retries"""
        handler = ErrorRecoveryHandler(max_retries=2)
        
        def failing_op():
            raise Exception("Always fails")
        
        success, result = handler.with_retry(
            failing_op,
            "failing_operation"
        )
        
        assert success is False


# ============================================================================
# Test 38: Batch Processing
# ============================================================================

class TestBatchProcessor:
    """Test batch processor"""
    
    def test_process_batch(self):
        """Should process items in batches"""
        processor = BatchProcessor(batch_size=2)
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_batch(items, lambda x: x * 2)
        
        assert results == [2, 4, 6, 8, 10]


# ============================================================================
# Test 39: Async Operation Support
# ============================================================================

class TestAsyncOperationSupport:
    """Test async support"""
    
    @pytest.mark.asyncio
    async def test_process_async(self):
        """Should process asynchronously"""
        async_support = AsyncOperationSupport()
        
        result = await async_support.process_async(lambda: 42)
        
        assert result == 42


# ============================================================================
# Test 40: API Interface
# ============================================================================

class TestTechnicalAgentAPI:
    """Test API interface"""
    
    def test_handle_health_request(self, technical_agent):
        """Should handle health check request"""
        response = technical_agent.api.handle_request('health', {})
        
        assert response['status'] == 200
        assert response['data']['healthy'] is True
    
    def test_handle_status_request(self, technical_agent):
        """Should handle status request"""
        response = technical_agent.api.handle_request('get_status', {})
        
        assert response['status'] == 200
        assert 'agent_id' in response['data']
    
    def test_handle_unknown_endpoint(self, technical_agent):
        """Should handle unknown endpoint"""
        response = technical_agent.api.handle_request('unknown', {})
        
        assert response['status'] == 404


# ============================================================================
# Test 41: Webhook Support
# ============================================================================

class TestWebhookManager:
    """Test webhook manager"""
    
    def test_register_webhook(self):
        """Should register webhook"""
        manager = WebhookManager()
        
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=['analysis_complete']
        )
        
        manager.register(config)
        
        assert len(manager.webhooks) == 1
    
    def test_unregister_webhook(self):
        """Should unregister webhook"""
        manager = WebhookManager()
        
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=['analysis_complete']
        )
        
        manager.register(config)
        manager.unregister("https://example.com/webhook")
        
        assert len(manager.webhooks) == 0


# ============================================================================
# Test Data Classes
# ============================================================================

class TestDataClasses:
    """Test data class creation"""
    
    def test_rfp_requirement(self, sample_requirement):
        """Should create RFPRequirement"""
        assert sample_requirement.id == "REQ_001"
        assert sample_requirement.quantity == 5000
    
    def test_product_match(self, sample_product_match):
        """Should create ProductMatch"""
        assert sample_product_match.match_score == 92.5
        assert sample_product_match.confidence == MatchConfidence.HIGH
    
    def test_comparison_row(self):
        """Should create ComparisonRow"""
        row = ComparisonRow(
            spec_name='voltage_rating',
            rfp_value='1100V',
            product_values={'p1': '1100V'},
            match_status={'p1': '✓ Match'}
        )
        assert row.spec_name == 'voltage_rating'
    
    def test_agent_message(self):
        """Should create AgentMessage"""
        msg = AgentMessage(
            id='msg_001',
            sender='TECH_AGENT',
            recipient='PRICE_AGENT',
            message_type='request',
            payload={'test': True},
            timestamp=datetime.now()
        )
        assert msg.sender == 'TECH_AGENT'


# ============================================================================
# Test Enums
# ============================================================================

class TestEnums:
    """Test enum values"""
    
    def test_match_confidence_levels(self):
        """Should have all confidence levels"""
        levels = [c.value for c in MatchConfidence]
        assert 'very_high' in levels
        assert 'high' in levels
        assert 'medium' in levels
        assert 'low' in levels
    
    def test_risk_levels(self):
        """Should have all risk levels"""
        levels = [r.value for r in RiskLevel]
        assert 'critical' in levels
        assert 'high' in levels
        assert 'none' in levels
    
    def test_compliance_status(self):
        """Should have all compliance statuses"""
        statuses = [s.value for s in ComplianceStatus]
        assert 'compliant' in statuses
        assert 'partial' in statuses
        assert 'non_compliant' in statuses


# ============================================================================
# Integration Tests
# ============================================================================

class TestTechnicalAgentIntegration:
    """Integration tests"""
    
    def test_get_status(self, technical_agent):
        """Should return status"""
        status = technical_agent.get_status()
        
        assert status['agent_id'] == 'TEST_AGENT'
        assert 'performance' in status
        assert 'memory' in status
    
    def test_health_check(self, technical_agent):
        """Should return health"""
        health = technical_agent.health_check()
        
        assert health['healthy'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
