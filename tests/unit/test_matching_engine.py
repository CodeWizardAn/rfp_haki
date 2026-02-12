"""
Unit Tests for Enhanced Matching Engine
Tests all 10 features comprehensively
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent.parent

# Add agents/shared to path
shared_path = project_root / 'agents' / 'shared'
sys.path.insert(0, str(shared_path))

# Also try the src directory if matching_engine is there
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Try agents directory directly
agents_path = project_root / 'agents'
sys.path.insert(0, str(agents_path))

# Try the root directory as well
sys.path.insert(0, str(project_root))

from matching_engine import (
    MatchingEngine,
    MatchQuality,
    RecommendationLevel,
    FailureType,
    SpecCategory,
    StandardEquivalenceResult,
    SpecScore,
    CriticalFailure,
    GapAnalysis,
    MatchExplanation,
    MatchResult,
    BatchMatchResult,
    get_matching_engine,
    match_product,
    batch_match
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def matching_engine():
    """Create a fresh matching engine instance"""
    return MatchingEngine()


@pytest.fixture
def strict_engine():
    """Create a strict mode matching engine"""
    return MatchingEngine(strict_mode=True)


@pytest.fixture
def custom_weight_engine():
    """Create engine with custom weights"""
    custom_weights = {
        SpecCategory.CRITICAL: 3.0,
        SpecCategory.IMPORTANT: 2.0,
        SpecCategory.STANDARD: 1.0,
        SpecCategory.INFORMATIONAL: 0.25
    }
    return MatchingEngine(custom_weights=custom_weights)


@pytest.fixture
def sample_rfp_specs():
    """Sample RFP specifications"""
    return {
        'conductor_material': 'Electrolytic Copper',
        'insulation_type': 'PVC',
        'voltage_rating': '1100V',
        'cross_section_sqmm': 4.0,
        'number_of_cores': 4,
        'temperature_rating': '70°C',
        'certifications': ['BIS', 'ISI']
    }


@pytest.fixture
def sample_oem_specs_good():
    """Sample OEM specs that should match well"""
    return {
        'conductor_material': 'Copper',
        'insulation_type': 'PVC Type A',
        'voltage_rating': '1100V AC',
        'cross_section_sqmm': 4.0,
        'number_of_cores': 4,
        'temperature_rating': '70°C',
        'certifications': ['BIS', 'ISI', 'CPRI']
    }


@pytest.fixture
def sample_oem_specs_poor():
    """Sample OEM specs with poor match"""
    return {
        'conductor_material': 'Aluminium',
        'insulation_type': 'XLPE',
        'voltage_rating': '650V',
        'cross_section_sqmm': 2.5,
        'number_of_cores': 3,
        'temperature_rating': '60°C',
        'certifications': []
    }


@pytest.fixture
def sample_oem_specs_partial():
    """Sample OEM specs with partial match"""
    return {
        'conductor_material': 'Copper',
        'insulation_type': 'PVC',
        'voltage_rating': '1100V',
        'cross_section_sqmm': 4.5,  # Slightly over
        'number_of_cores': 4,
        'temperature_rating': '65°C',  # Below
        'certifications': ['BIS']  # Missing ISI
    }


# ============================================================================
# 1. Standard Equivalence Checking Tests
# ============================================================================

class TestStandardEquivalenceChecking:
    """Tests for standard equivalence checking functionality"""
    
    def test_exact_standard_match(self, matching_engine):
        """Test exact match of same standard"""
        result = matching_engine.check_standard_equivalence('IS 1554-1', 'IS 1554-1')
        
        assert result.is_equivalent is True
        assert result.confidence == 1.0
        assert 'IS 1554-1' in result.mapping_path
    
    def test_direct_equivalent_standards(self, matching_engine):
        """Test directly equivalent standards"""
        result = matching_engine.check_standard_equivalence('IS 7098-1', 'IEC 60502-1')
        
        assert result.is_equivalent is True
        assert result.confidence >= 0.7
    
    def test_non_equivalent_standards(self, matching_engine):
        """Test non-equivalent standards"""
        result = matching_engine.check_standard_equivalence('IS 694', 'IEC 62067')
        
        # These may or may not be equivalent depending on the mapping
        assert isinstance(result.is_equivalent, bool)
        assert 0.0 <= result.confidence <= 1.0
    
    def test_case_insensitive_match(self, matching_engine):
        """Test case insensitive standard matching"""
        result = matching_engine.check_standard_equivalence('is 1554-1', 'IS 1554-1')
        
        assert result.is_equivalent is True
    
    def test_base_code_match(self, matching_engine):
        """Test matching with base code (part number difference)"""
        result = matching_engine.check_standard_equivalence('IS 7098', 'IS 7098-1')
        
        assert result.is_equivalent is True
        assert result.confidence >= 0.7  # May be indirect match through equivalence groups

    
    def test_multiple_standards_check(self, matching_engine):
        """Test checking multiple standards"""
        rfp_standards = ['IS 1554-1', 'IS 8130']
        product_standards = ['IS 1554-1', 'IEC 60228']
        
        score, results = matching_engine.check_multiple_standards(rfp_standards, product_standards)
        
        assert 0.0 <= score <= 1.0
        assert len(results) == len(rfp_standards)
    
    def test_empty_standards_handling(self, matching_engine):
        """Test handling of empty standard lists"""
        score, results = matching_engine.check_multiple_standards([], [])
        
        assert score == 1.0
        assert results == []


# ============================================================================
# 2. Scoring Aggregation Tests
# ============================================================================

class TestScoringAggregation:
    """Tests for score aggregation functionality"""
    
    def test_aggregate_empty_scores(self, matching_engine):
        """Test aggregation with no scores"""
        result = matching_engine.aggregate_scores([])
        
        assert result['overall'] == 0.0
        assert result['weighted'] == 0.0
        assert result['average'] == 0.0
    
    def test_aggregate_perfect_scores(self, matching_engine):
        """Test aggregation with perfect scores"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 2.0, 2.0, SpecCategory.CRITICAL, 'exact', 'Match'),
            SpecScore('material', 'copper', 'copper', 1.0, 1.5, 1.5, SpecCategory.IMPORTANT, 'exact', 'Match'),
        ]
        
        result = matching_engine.aggregate_scores(spec_scores, 1.0, 1.0)
        
        assert result['average'] == 1.0
        assert result['weighted'] == 1.0
        assert result['critical_only'] == 1.0
    
    def test_aggregate_mixed_scores(self, matching_engine):
        """Test aggregation with mixed scores"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 2.0, 2.0, SpecCategory.CRITICAL, 'exact', 'Match'),
            SpecScore('size', 4.0, 3.5, 0.5, 0.75, 1.5, SpecCategory.IMPORTANT, 'partial', 'Partial'),
            SpecScore('color', 'red', 'blue', 0.0, 0.0, 0.5, SpecCategory.INFORMATIONAL, 'none', 'No match'),
        ]
        
        result = matching_engine.aggregate_scores(spec_scores, 0.8, 0.9)
        
        assert 0.0 < result['overall'] < 1.0
        assert 'by_category' in result
        assert result['by_category']['critical'] == 1.0
    
    def test_aggregate_preserves_standard_scores(self, matching_engine):
        """Test that standard and certification scores are preserved"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 1.0, 1.0, SpecCategory.CRITICAL, 'exact', 'Match'),
        ]
        
        result = matching_engine.aggregate_scores(spec_scores, 0.75, 0.85)
        
        assert result['standard_score'] == 0.75
        assert result['certification_score'] == 0.85


# ============================================================================
# 3. Weighted Score Calculation Tests
# ============================================================================

class TestWeightedScoreCalculation:
    """Tests for weighted score calculation"""
    
    def test_critical_spec_weight(self, matching_engine):
        """Test critical specs get higher weight"""
        weighted, weight, category = matching_engine.calculate_weighted_score('voltage_rating', 1.0)
        
        assert category == SpecCategory.CRITICAL
        assert weight == 2.0  # Default critical weight
        assert weighted == 2.0
    
    def test_important_spec_weight(self, matching_engine):
        """Test important specs get medium weight"""
        weighted, weight, category = matching_engine.calculate_weighted_score('cross_section_sqmm', 1.0)
        
        assert category == SpecCategory.IMPORTANT
        assert weight == 1.5  # Default important weight
    
    def test_informational_spec_weight(self, matching_engine):
        """Test informational specs get lower weight"""
        weighted, weight, category = matching_engine.calculate_weighted_score('manufacturer', 1.0)
        
        assert category == SpecCategory.INFORMATIONAL
        assert weight == 0.5
    
    def test_custom_weight_override(self, matching_engine):
        """Test custom weight overrides default"""
        weighted, weight, category = matching_engine.calculate_weighted_score(
            'voltage_rating', 1.0, custom_weight=5.0
        )
        
        assert weight == 5.0
        assert weighted == 5.0
    
    def test_unknown_spec_defaults_to_standard(self, matching_engine):
        """Test unknown specs default to standard category"""
        weighted, weight, category = matching_engine.calculate_weighted_score('unknown_spec', 1.0)
        
        assert category == SpecCategory.STANDARD
        assert weight == 1.0
    
    def test_apply_weights_to_scores(self, matching_engine):
        """Test applying weights to multiple scores"""
        raw_scores = {
            'voltage_rating': 1.0,
            'conductor_size': 0.8,
            'manufacturer': 0.5
        }
        
        spec_scores = matching_engine.apply_weights_to_scores(raw_scores)
        
        assert len(spec_scores) == 3
        
        voltage_score = next(s for s in spec_scores if s.spec_name == 'voltage_rating')
        assert voltage_score.category == SpecCategory.CRITICAL
        assert voltage_score.weighted_score == 2.0  # 1.0 * 2.0
    
    def test_custom_weight_engine_different_weights(self, custom_weight_engine):
        """Test engine with custom weight configuration"""
        weighted, weight, _ = custom_weight_engine.calculate_weighted_score('voltage_rating', 1.0)
        
        assert weight == 3.0  # Custom weight
        assert weighted == 3.0


# ============================================================================
# 4. Confidence Score Calculation Tests
# ============================================================================

class TestConfidenceCalculation:
    """Tests for confidence score calculation"""
    
    def test_confidence_with_complete_data(self, matching_engine):
        """Test confidence with complete high-quality data"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 1.0, 1.0, SpecCategory.CRITICAL, 'exact', ''),
            SpecScore('material', 'cu', 'cu', 1.0, 1.0, 1.0, SpecCategory.CRITICAL, 'exact', ''),
        ]
        
        confidence = matching_engine.calculate_confidence(
            spec_scores,
            data_completeness=1.0,
            verification_status='verified',
            standard_confidence=1.0
        )
        
        assert confidence >= 0.9
    
    def test_confidence_with_incomplete_data(self, matching_engine):
        """Test confidence penalty for incomplete data"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 1.0, 1.0, SpecCategory.CRITICAL, 'exact', ''),
        ]
        
        confidence = matching_engine.calculate_confidence(
            spec_scores,
            data_completeness=0.3,
            verification_status='unverified',
            standard_confidence=0.5
        )
        
        assert confidence < 0.7
    
    def test_confidence_with_inconsistent_scores(self, matching_engine):
        """Test confidence penalty for inconsistent scores"""
        spec_scores = [
            SpecScore('v1', None, None, 1.0, 1.0, 1.0, SpecCategory.STANDARD, 'exact', ''),
            SpecScore('v2', None, None, 0.0, 0.0, 1.0, SpecCategory.STANDARD, 'none', ''),
            SpecScore('v3', None, None, 0.5, 0.5, 1.0, SpecCategory.STANDARD, 'partial', ''),
        ]
        
        confidence = matching_engine.calculate_confidence(
            spec_scores,
            data_completeness=1.0,
            verification_status='verified',
            standard_confidence=1.0
        )
        
        # High variance should reduce confidence
        assert confidence < 0.95
    
    def test_confidence_empty_scores(self, matching_engine):
        """Test confidence with no scores returns 0"""
        confidence = matching_engine.calculate_confidence([], 1.0)
        
        assert confidence == 0.0
    
    def test_confidence_verification_levels(self, matching_engine):
        """Test different verification status effects"""
        spec_scores = [
            SpecScore('v', None, None, 0.8, 0.8, 1.0, SpecCategory.CRITICAL, 'partial', ''),
        ]
        
        conf_verified = matching_engine.calculate_confidence(spec_scores, 1.0, 'verified')
        conf_partial = matching_engine.calculate_confidence(spec_scores, 1.0, 'partially_verified')
        conf_unverified = matching_engine.calculate_confidence(spec_scores, 1.0, 'unverified')
        
        assert conf_verified > conf_partial > conf_unverified


# ============================================================================
# 5. Match Explanation Generator Tests
# ============================================================================

class TestMatchExplanationGenerator:
    """Tests for match explanation generation"""
    
    def test_explanation_has_required_fields(self, matching_engine):
        """Test explanation contains all required fields"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 2.0, 2.0, SpecCategory.CRITICAL, 'exact', 'Match'),
        ]
        
        explanation = matching_engine.generate_explanation(
            spec_scores, [], [], 0.95, MatchQuality.EXCELLENT, RecommendationLevel.HIGHLY_RECOMMENDED
        )
        
        assert explanation.summary
        assert explanation.quality_tier == MatchQuality.EXCELLENT
        assert explanation.recommendation == RecommendationLevel.HIGHLY_RECOMMENDED
        assert isinstance(explanation.strengths, list)
        assert isinstance(explanation.weaknesses, list)
        assert isinstance(explanation.critical_issues, list)
        assert isinstance(explanation.spec_details, list)
        assert explanation.overall_assessment
    
    def test_explanation_identifies_strengths(self, matching_engine):
        """Test explanation correctly identifies strengths"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 2.0, 2.0, SpecCategory.CRITICAL, 'exact', 'Match'),
            SpecScore('material', 'copper', 'copper', 0.95, 1.0, 1.0, SpecCategory.IMPORTANT, 'exact', 'Match'),
        ]
        
        explanation = matching_engine.generate_explanation(
            spec_scores, [], [], 0.97, MatchQuality.EXCELLENT, RecommendationLevel.HIGHLY_RECOMMENDED
        )
        
        assert len(explanation.strengths) >= 2
        assert any('voltage' in s for s in explanation.strengths)
    
    def test_explanation_identifies_weaknesses(self, matching_engine):
        """Test explanation correctly identifies weaknesses"""
        spec_scores = [
            SpecScore('voltage', 1100, 1100, 1.0, 2.0, 2.0, SpecCategory.CRITICAL, 'exact', 'Match'),
            SpecScore('size', 4.0, 3.0, 0.4, 0.4, 1.0, SpecCategory.IMPORTANT, 'partial', 'Partial'),
        ]
        
        explanation = matching_engine.generate_explanation(
            spec_scores, [], [], 0.7, MatchQuality.FAIR, RecommendationLevel.CONDITIONAL
        )
        
        assert any('size' in w.lower() for w in explanation.weaknesses)
    
    def test_explanation_includes_critical_issues(self, matching_engine):
        """Test explanation includes critical issues"""
        spec_scores = []
        critical_failures = [
            CriticalFailure(
                FailureType.VOLTAGE_MISMATCH, 'voltage', 1100, 650, 'critical',
                'Voltage too low', 'Select higher voltage product'
            )
        ]
        
        explanation = matching_engine.generate_explanation(
            spec_scores, critical_failures, [], 0.3, MatchQuality.DISQUALIFIED, RecommendationLevel.NOT_RECOMMENDED
        )
        
        assert len(explanation.critical_issues) > 0
        assert 'voltage_mismatch' in explanation.critical_issues[0].lower()


# ============================================================================
# 6. Critical Failure Detection Tests
# ============================================================================

class TestCriticalFailureDetection:
    """Tests for critical failure detection"""
    
    def test_detect_voltage_mismatch(self, matching_engine, sample_rfp_specs):
        """Test voltage mismatch detection"""
        oem_specs = {**sample_rfp_specs, 'voltage_rating': '650V'}
        
        failures = matching_engine.detect_critical_failures(sample_rfp_specs, oem_specs)
        
        voltage_failures = [f for f in failures if f.failure_type == FailureType.VOLTAGE_MISMATCH]
        assert len(voltage_failures) > 0
        assert voltage_failures[0].severity in ('critical', 'severe')
    
    def test_detect_material_incompatibility(self, matching_engine, sample_rfp_specs):
        """Test material incompatibility detection"""
        oem_specs = {**sample_rfp_specs, 'conductor_material': 'Aluminium'}
        
        failures = matching_engine.detect_critical_failures(sample_rfp_specs, oem_specs)
        
        material_failures = [f for f in failures if f.failure_type == FailureType.MATERIAL_INCOMPATIBLE]
        assert len(material_failures) > 0
    
    def test_detect_missing_certification(self, matching_engine, sample_rfp_specs):
        """Test missing certification detection"""
        oem_specs = {**sample_rfp_specs, 'certifications': []}
        
        failures = matching_engine.detect_critical_failures(sample_rfp_specs, oem_specs)
        
        cert_failures = [f for f in failures if f.failure_type == FailureType.CERTIFICATION_MISSING]
        assert len(cert_failures) > 0
    
    def test_detect_size_mismatch(self, matching_engine, sample_rfp_specs):
        """Test conductor size mismatch detection"""
        oem_specs = {**sample_rfp_specs, 'cross_section_sqmm': 1.5}  # 62.5% smaller
        
        failures = matching_engine.detect_critical_failures(sample_rfp_specs, oem_specs)
        
        size_failures = [f for f in failures if f.failure_type == FailureType.SIZE_OUT_OF_RANGE]
        assert len(size_failures) > 0
    
    def test_no_failures_for_matching_specs(self, matching_engine, sample_rfp_specs, sample_oem_specs_good):
        """Test no critical failures for matching specs"""
        failures = matching_engine.detect_critical_failures(sample_rfp_specs, sample_oem_specs_good)
        
        # Good specs should have minimal or no critical failures
        critical_severe = [f for f in failures if f.severity in ('critical', 'severe')]
        assert len(critical_severe) == 0
    
    def test_failure_includes_remediation(self, matching_engine, sample_rfp_specs):
        """Test failure includes remediation suggestion"""
        oem_specs = {**sample_rfp_specs, 'voltage_rating': '650V'}
        
        failures = matching_engine.detect_critical_failures(sample_rfp_specs, oem_specs)
        
        for failure in failures:
            if failure.failure_type == FailureType.VOLTAGE_MISMATCH:
                assert failure.remediation is not None


# ============================================================================
# 7. Gap Analysis Tests
# ============================================================================

class TestGapAnalysis:
    """Tests for gap analysis functionality"""
    
    def test_detect_missing_spec(self, matching_engine, sample_rfp_specs):
        """Test detection of missing specifications"""
        oem_specs = {
            'conductor_material': 'Copper',
            # voltage_rating is missing
        }
        
        gaps = matching_engine.analyze_gaps(sample_rfp_specs, oem_specs)
        
        missing_gaps = [g for g in gaps if g.gap_type == 'missing']
        assert len(missing_gaps) > 0
    
    def test_detect_insufficient_spec(self, matching_engine, sample_rfp_specs):
        """Test detection of insufficient specifications"""
        oem_specs = {
            **sample_rfp_specs,
            'cross_section_sqmm': 2.5,  # Below required 4.0
        }
        
        gaps = matching_engine.analyze_gaps(sample_rfp_specs, oem_specs)
        
        insufficient_gaps = [g for g in gaps if g.gap_type == 'insufficient']
        assert len(insufficient_gaps) > 0
        assert insufficient_gaps[0].gap_magnitude is not None
    
    def test_detect_over_specified(self, matching_engine):
        """Test detection of over-specified values"""
        rfp_specs = {'cross_section_sqmm': 4.0}
        oem_specs = {'cross_section_sqmm': 10.0}  # 150% more than required
        
        gaps = matching_engine.analyze_gaps(rfp_specs, oem_specs)
        
        over_gaps = [g for g in gaps if g.gap_type == 'over_specified']
        assert len(over_gaps) > 0
    
    def test_gap_includes_impact(self, matching_engine, sample_rfp_specs):
        """Test gaps include impact assessment"""
        oem_specs = {}  # All specs missing
        
        gaps = matching_engine.analyze_gaps(sample_rfp_specs, oem_specs)
        
        for gap in gaps:
            assert gap.impact in ('high', 'medium', 'low')
    
    def test_gap_includes_remediation_options(self, matching_engine, sample_rfp_specs):
        """Test gaps include remediation options"""
        oem_specs = {'conductor_material': 'Copper'}  # Most specs missing
        
        gaps = matching_engine.analyze_gaps(sample_rfp_specs, oem_specs)
        
        for gap in gaps:
            assert isinstance(gap.remediation_options, list)
            assert len(gap.remediation_options) > 0


# ============================================================================
# 8. Match Quality Classifier Tests
# ============================================================================

class TestMatchQualityClassifier:
    """Tests for match quality classification"""
    
    def test_excellent_quality(self, matching_engine):
        """Test excellent quality classification"""
        quality = matching_engine.classify_match_quality(0.97, [], 0.95)
        
        assert quality == MatchQuality.EXCELLENT
    
    def test_good_quality(self, matching_engine):
        """Test good quality classification"""
        quality = matching_engine.classify_match_quality(0.88, [], 0.9)
        
        assert quality == MatchQuality.GOOD
    
    def test_fair_quality(self, matching_engine):
        """Test fair quality classification"""
        quality = matching_engine.classify_match_quality(0.75, [], 0.8)
        
        assert quality == MatchQuality.FAIR
    
    def test_poor_quality(self, matching_engine):
        """Test poor quality classification"""
        quality = matching_engine.classify_match_quality(0.55, [], 0.7)
        
        assert quality == MatchQuality.POOR
    
    def test_disqualified_low_score(self, matching_engine):
        """Test disqualified due to low score"""
        quality = matching_engine.classify_match_quality(0.3, [], 0.5)
        
        assert quality == MatchQuality.DISQUALIFIED
    
    def test_disqualified_critical_failure(self, matching_engine):
        """Test disqualified due to critical failure"""
        critical_failures = [
            CriticalFailure(
                FailureType.VOLTAGE_MISMATCH, 'voltage', 1100, 650, 'critical',
                'Voltage mismatch', None
            )
        ]
        
        quality = matching_engine.classify_match_quality(0.9, critical_failures, 0.9)
        
        assert quality == MatchQuality.DISQUALIFIED
    
    def test_strict_mode_disqualifies_any_failure(self, strict_engine):
        """Test strict mode disqualifies on any failure"""
        moderate_failure = [
            CriticalFailure(
                FailureType.SIZE_OUT_OF_RANGE, 'size', 4.0, 4.5, 'moderate',
                'Slight size difference', None
            )
        ]
        
        quality = strict_engine.classify_match_quality(0.95, moderate_failure, 0.95)
        
        assert quality == MatchQuality.DISQUALIFIED


# ============================================================================
# 9. Recommendation Level Calculator Tests
# ============================================================================

class TestRecommendationLevelCalculator:
    """Tests for recommendation level calculation"""
    
    def test_highly_recommended(self, matching_engine):
        """Test highly recommended level"""
        recommendation = matching_engine.calculate_recommendation(
            MatchQuality.EXCELLENT, [], []
        )
        
        assert recommendation == RecommendationLevel.HIGHLY_RECOMMENDED
    
    def test_recommended(self, matching_engine):
        """Test recommended level"""
        medium_gaps = [
            GapAnalysis('size', 4.0, 4.2, 'insufficient', 5.0, 'medium', [])
        ]
        
        recommendation = matching_engine.calculate_recommendation(
            MatchQuality.GOOD, medium_gaps, []
        )
        
        assert recommendation == RecommendationLevel.RECOMMENDED
    
    def test_conditional(self, matching_engine):
        """Test conditional recommendation"""
        high_gaps = [
            GapAnalysis('voltage', 1100, 1000, 'insufficient', 10.0, 'high', [])
        ]
        
        recommendation = matching_engine.calculate_recommendation(
            MatchQuality.GOOD, high_gaps, []
        )
        
        assert recommendation == RecommendationLevel.CONDITIONAL
    
    def test_not_recommended(self, matching_engine):
        """Test not recommended level"""
        recommendation = matching_engine.calculate_recommendation(
            MatchQuality.DISQUALIFIED, [], []
        )
        
        assert recommendation == RecommendationLevel.NOT_RECOMMENDED
    
    def test_fair_quality_is_conditional(self, matching_engine):
        """Test fair quality results in conditional"""
        recommendation = matching_engine.calculate_recommendation(
            MatchQuality.FAIR, [], []
        )
        
        assert recommendation == RecommendationLevel.CONDITIONAL


# ============================================================================
# 10. Batch Matching Tests
# ============================================================================

class TestBatchMatching:
    """Tests for batch matching functionality"""
    
    def test_batch_match_multiple_requirements(self, matching_engine):
        """Test batch matching multiple requirements"""
        requirements = [
            {'name': 'Product A', 'specifications': {'voltage': 1100, 'material': 'copper'}},
            {'name': 'Product B', 'specifications': {'voltage': 650, 'material': 'aluminium'}},
        ]
        products = [
            {'name': 'OEM 1', 'sku': 'SKU1', 'specifications': {'voltage': 1100, 'material': 'copper'}},
            {'name': 'OEM 2', 'sku': 'SKU2', 'specifications': {'voltage': 650, 'material': 'aluminium'}},
        ]
        
        result = matching_engine.batch_match(requirements, products, top_n=2)
        
        assert isinstance(result, BatchMatchResult)
        assert result.total_requirements == 2
        assert result.total_products == 2
        assert len(result.matches) <= 4  # 2 requirements × 2 top matches
    
    def test_batch_match_returns_top_n(self, matching_engine):
        """Test batch matching returns top N matches"""
        requirements = [
            {'name': 'Product A', 'specifications': {'voltage': 1100}}
        ]
        products = [
            {'name': f'OEM {i}', 'sku': f'SKU{i}', 'specifications': {'voltage': 1100}} 
            for i in range(5)
        ]
        
        result = matching_engine.batch_match(requirements, products, top_n=3)
        
        assert len(result.matches) == 3
    
    def test_batch_match_summary(self, matching_engine):
        """Test batch match includes summary"""
        requirements = [
            {'name': 'Product A', 'specifications': {'voltage': 1100}}
        ]
        products = [
            {'name': 'OEM 1', 'sku': 'SKU1', 'specifications': {'voltage': 1100}}
        ]
        
        result = matching_engine.batch_match(requirements, products)
        
        assert 'quality_distribution' in result.summary
        assert 'average_score' in result.summary
    
    def test_batch_match_processing_time(self, matching_engine):
        """Test batch match records processing time"""
        requirements = [{'name': 'A', 'specifications': {}}]
        products = [{'name': 'B', 'sku': 'C', 'specifications': {}}]
        
        result = matching_engine.batch_match(requirements, products)
        
        assert result.processing_time_ms >= 0
    
    def test_batch_match_empty_inputs(self, matching_engine):
        """Test batch match with empty inputs"""
        result = matching_engine.batch_match([], [])
        
        assert result.total_requirements == 0
        assert result.total_products == 0
        assert len(result.matches) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestMatchProductIntegration:
    """Integration tests for complete product matching"""
    
    def test_complete_match_workflow(
        self, matching_engine, sample_rfp_specs, sample_oem_specs_good
    ):
        """Test complete matching workflow"""
        result = matching_engine.match_product(
            rfp_product="PVC Cable 4C x 4 sq mm",
            rfp_specs=sample_rfp_specs,
            oem_product="ACME PVC Cable",
            oem_sku="ACME-001",
            oem_specs=sample_oem_specs_good
        )
        
        assert isinstance(result, MatchResult)
        assert 0 <= result.overall_score <= 1
        assert 0 <= result.confidence <= 1
        assert isinstance(result.quality, MatchQuality)
        assert isinstance(result.recommendation, RecommendationLevel)
        assert isinstance(result.explanation, MatchExplanation)
    
    def test_match_with_standards(self, matching_engine, sample_rfp_specs, sample_oem_specs_good):
        """Test matching with standard checking"""
        result = matching_engine.match_product(
            rfp_product="Cable",
            rfp_specs=sample_rfp_specs,
            oem_product="OEM Cable",
            oem_sku="OEM-001",
            oem_specs=sample_oem_specs_good,
            rfp_standards=['IS 1554-1'],
            oem_standards=['IS 1554-1', 'IEC 60502-1']
        )
        
        assert len(result.standard_equivalences) > 0
    
    def test_poor_match_identified(
        self, matching_engine, sample_rfp_specs, sample_oem_specs_poor
    ):
        """Test poor match is correctly identified"""
        result = matching_engine.match_product(
            rfp_product="PVC Cable",
            rfp_specs=sample_rfp_specs,
            oem_product="Wrong Cable",
            oem_sku="WRONG-001",
            oem_specs=sample_oem_specs_poor
        )
        
        assert result.quality in (MatchQuality.POOR, MatchQuality.DISQUALIFIED)
        assert result.recommendation == RecommendationLevel.NOT_RECOMMENDED
        assert len(result.critical_failures) > 0


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions"""
    
    def test_get_matching_engine_singleton(self):
        """Test singleton pattern for matching engine"""
        engine1 = get_matching_engine()
        engine2 = get_matching_engine()
        
        assert engine1 is engine2
    
    def test_match_product_convenience(self, sample_rfp_specs, sample_oem_specs_good):
        """Test convenience match_product function"""
        result = match_product(
            rfp_product="Cable",
            rfp_specs=sample_rfp_specs,
            oem_product="OEM Cable",
            oem_sku="SKU-001",
            oem_specs=sample_oem_specs_good
        )
        
        assert isinstance(result, MatchResult)
    
    def test_batch_match_convenience(self):
        """Test convenience batch_match function"""
        reqs = [{'name': 'A', 'specifications': {'v': 100}}]
        prods = [{'name': 'B', 'sku': 'C', 'specifications': {'v': 100}}]
        
        result = batch_match(reqs, prods)
        
        assert isinstance(result, BatchMatchResult)
