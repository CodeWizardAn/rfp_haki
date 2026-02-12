"""
Enhanced Matching Engine
Advanced specification matching with scoring, confidence, and explanations

Features:
1. Standard equivalence checking
2. Scoring aggregation
3. Weighted score calculation
4. Confidence score calculation
5. Match explanation generation
6. Critical failure detection
7. Gap analysis
8. Match quality classification
9. Recommendation level calculation
10. Batch matching support
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

# Import shared utilities
try:
    from .utils import (
        StandardMapper,
        SpecificationNormalizer,
        UnitConverter,
        TextCleaner,
        is_standard_equivalent,
        get_equivalent_standards
    )
except ImportError:
    # Fallback for direct execution
    from utils import (
        StandardMapper,
        SpecificationNormalizer,
        UnitConverter,
        TextCleaner,
        is_standard_equivalent,
        get_equivalent_standards
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class MatchQuality(Enum):
    """Match quality tiers"""
    EXCELLENT = "excellent"      # >= 95% match
    GOOD = "good"               # >= 85% match
    FAIR = "fair"               # >= 70% match
    POOR = "poor"               # >= 50% match
    DISQUALIFIED = "disqualified"  # Critical failure or < 50%


class RecommendationLevel(Enum):
    """Recommendation levels for products"""
    HIGHLY_RECOMMENDED = "highly_recommended"
    RECOMMENDED = "recommended"
    CONDITIONAL = "conditional"
    NOT_RECOMMENDED = "not_recommended"


class FailureType(Enum):
    """Types of critical failures"""
    VOLTAGE_MISMATCH = "voltage_mismatch"
    STANDARD_NON_COMPLIANCE = "standard_non_compliance"
    MATERIAL_INCOMPATIBLE = "material_incompatible"
    SIZE_OUT_OF_RANGE = "size_out_of_range"
    CERTIFICATION_MISSING = "certification_missing"
    SAFETY_REQUIREMENT = "safety_requirement"
    TEMPERATURE_RATING = "temperature_rating"
    CURRENT_CAPACITY = "current_capacity"


class SpecCategory(Enum):
    """Specification categories for weighting"""
    CRITICAL = "critical"       # Must match (e.g., voltage, material)
    IMPORTANT = "important"     # Should match (e.g., size, insulation)
    STANDARD = "standard"       # Nice to match (e.g., certifications)
    INFORMATIONAL = "informational"  # For reference only


@dataclass
class StandardEquivalenceResult:
    """Result of standard equivalence check"""
    standard1: str
    standard2: str
    is_equivalent: bool
    confidence: float
    mapping_path: List[str]
    notes: List[str]


@dataclass
class SpecScore:
    """Score for a single specification"""
    spec_name: str
    rfp_value: Any
    product_value: Any
    raw_score: float        # 0.0 - 1.0
    weighted_score: float   # After applying weight
    weight: float
    category: SpecCategory
    match_type: str         # exact, partial, semantic, range, none
    explanation: str


@dataclass
class CriticalFailure:
    """Details of a critical failure"""
    failure_type: FailureType
    spec_name: str
    rfp_value: Any
    product_value: Any
    severity: str           # critical, severe, moderate
    explanation: str
    remediation: Optional[str] = None


@dataclass
class GapAnalysis:
    """Analysis of gaps between requirement and product"""
    spec_name: str
    requirement: Any
    actual: Any
    gap_type: str           # missing, insufficient, over_specified
    gap_magnitude: Optional[float]
    impact: str             # high, medium, low
    remediation_options: List[str]


@dataclass
class MatchExplanation:
    """Human-readable explanation of a match"""
    summary: str
    quality_tier: MatchQuality
    recommendation: RecommendationLevel
    strengths: List[str]
    weaknesses: List[str]
    critical_issues: List[str]
    spec_details: List[Dict[str, Any]]
    overall_assessment: str


@dataclass
class MatchResult:
    """Complete match result"""
    rfp_product: str
    oem_product: str
    oem_sku: str
    
    # Scores
    overall_score: float
    confidence: float
    weighted_score: float
    
    # Quality and recommendation
    quality: MatchQuality
    recommendation: RecommendationLevel
    
    # Detailed results
    spec_scores: List[SpecScore]
    critical_failures: List[CriticalFailure]
    gaps: List[GapAnalysis]
    standard_equivalences: List[StandardEquivalenceResult]
    
    # Explanation
    explanation: MatchExplanation
    
    # Metadata
    matched_at: str
    processing_time_ms: float


@dataclass
class BatchMatchResult:
    """Results from batch matching"""
    total_requirements: int
    total_products: int
    total_matches: int
    processing_time_ms: float
    matches: List[MatchResult]
    summary: Dict[str, Any]


# ============================================================================
# Enhanced Matching Engine
# ============================================================================

class MatchingEngine:
    """
    Enhanced specification matching engine with comprehensive scoring,
    confidence calculation, and explanation generation.
    """
    
    # Default weights for specification categories
    DEFAULT_WEIGHTS = {
        SpecCategory.CRITICAL: 2.0,
        SpecCategory.IMPORTANT: 1.5,
        SpecCategory.STANDARD: 1.0,
        SpecCategory.INFORMATIONAL: 0.5
    }
    
    # Spec categorization rules
    SPEC_CATEGORIES = {
        # Critical specs - must match
        'voltage_rating': SpecCategory.CRITICAL,
        'rated_voltage': SpecCategory.CRITICAL,
        'voltage_grade': SpecCategory.CRITICAL,
        'conductor_material': SpecCategory.CRITICAL,
        'insulation_type': SpecCategory.CRITICAL,
        'temperature_rating': SpecCategory.CRITICAL,
        'current_rating': SpecCategory.CRITICAL,
        'fire_rating': SpecCategory.CRITICAL,
        
        # Important specs - should match
        'conductor_size': SpecCategory.IMPORTANT,
        'cross_section_sqmm': SpecCategory.IMPORTANT,
        'number_of_cores': SpecCategory.IMPORTANT,
        'armour_type': SpecCategory.IMPORTANT,
        'outer_sheath': SpecCategory.IMPORTANT,
        'standard': SpecCategory.IMPORTANT,
        
        # Standard specs - nice to match
        'conductor_type': SpecCategory.STANDARD,
        'conductor_class': SpecCategory.STANDARD,
        'color': SpecCategory.STANDARD,
        'certifications': SpecCategory.STANDARD,
        
        # Informational
        'manufacturer': SpecCategory.INFORMATIONAL,
        'brand': SpecCategory.INFORMATIONAL,
        'moq': SpecCategory.INFORMATIONAL,
        'lead_time': SpecCategory.INFORMATIONAL,
    }
    
    # Critical failure thresholds
    CRITICAL_THRESHOLDS = {
        'voltage_mismatch_percent': 10,     # >10% voltage difference
        'size_mismatch_percent': 20,        # >20% size difference
        'temp_rating_min_margin': 10,       # Must have 10°C margin
        'current_capacity_margin': 0.1,     # 10% margin required
    }
    
    def __init__(
        self,
        custom_weights: Optional[Dict[str, float]] = None,
        strict_mode: bool = False
    ):
        """
        Initialize the matching engine.
        
        Args:
            custom_weights: Custom weights for spec categories
            strict_mode: If True, any critical failure disqualifies the product
        """
        self.standard_mapper = StandardMapper()
        self.spec_normalizer = SpecificationNormalizer()
        self.weights = custom_weights or self.DEFAULT_WEIGHTS
        self.strict_mode = strict_mode
        
        logger.info("✅ MatchingEngine initialized")
    
    # ========================================================================
    # 1. Standard Equivalence Checking
    # ========================================================================
    
    def check_standard_equivalence(
        self,
        rfp_standard: str,
        product_standard: str
    ) -> StandardEquivalenceResult:
        """
        Check if two standards are equivalent.
        
        Extends StandardMapper with additional path finding and confidence.
        
        Args:
            rfp_standard: Standard required by RFP
            product_standard: Standard of the product
            
        Returns:
            StandardEquivalenceResult with detailed information
        """
        notes = []
        mapping_path = []
        
        # Normalize standards
        rfp_std = rfp_standard.upper().strip()
        prod_std = product_standard.upper().strip()
        
        # Check direct equivalence
        is_equiv, confidence = is_standard_equivalent(rfp_std, prod_std)
        
        if is_equiv:
            mapping_path = [rfp_std, prod_std]
            notes.append(f"Direct equivalence found with {confidence*100:.0f}% confidence")
        else:
            # Try to find path through equivalence groups
            rfp_equivs = get_equivalent_standards(rfp_std)
            prod_equivs = get_equivalent_standards(prod_std)
            
            # Check for common equivalents
            common = set(rfp_equivs) & set(prod_equivs)
            if common:
                bridge_std = list(common)[0]
                is_equiv = True
                confidence = 0.75
                mapping_path = [rfp_std, bridge_std, prod_std]
                notes.append(f"Indirect equivalence through {bridge_std}")
            else:
                # Check base codes (e.g., IS 7098 vs IS 7098-1)
                rfp_base = re.sub(r'-\d+$', '', rfp_std)
                prod_base = re.sub(r'-\d+$', '', prod_std)
                
                if rfp_base == prod_base:
                    is_equiv = True
                    confidence = 0.85
                    mapping_path = [rfp_std, prod_std]
                    notes.append("Same standard family (part number difference)")
        
        # Check if standards are from same domain
        if not is_equiv:
            rfp_info = self.standard_mapper.get_standard_info(rfp_std)
            prod_info = self.standard_mapper.get_standard_info(prod_std)
            
            if rfp_info and prod_info:
                if rfp_info.category == prod_info.category:
                    notes.append(f"Both standards cover {rfp_info.category}")
        
        return StandardEquivalenceResult(
            standard1=rfp_standard,
            standard2=product_standard,
            is_equivalent=is_equiv,
            confidence=confidence,
            mapping_path=mapping_path,
            notes=notes
        )
    
    def check_multiple_standards(
        self,
        rfp_standards: List[str],
        product_standards: List[str]
    ) -> Tuple[float, List[StandardEquivalenceResult]]:
        """
        Check equivalence for multiple standards.
        
        Args:
            rfp_standards: Standards required by RFP
            product_standards: Standards of the product
            
        Returns:
            Tuple of (overall compliance score, list of results)
        """
        results = []
        matched_count = 0
        
        for rfp_std in rfp_standards:
            best_match = None
            best_confidence = 0.0
            
            for prod_std in product_standards:
                result = self.check_standard_equivalence(rfp_std, prod_std)
                if result.is_equivalent and result.confidence > best_confidence:
                    best_match = result
                    best_confidence = result.confidence
            
            if best_match:
                results.append(best_match)
                matched_count += 1
            else:
                results.append(StandardEquivalenceResult(
                    standard1=rfp_std,
                    standard2="NOT_FOUND",
                    is_equivalent=False,
                    confidence=0.0,
                    mapping_path=[],
                    notes=["No equivalent standard found in product"]
                ))
        
        score = matched_count / len(rfp_standards) if rfp_standards else 1.0
        return score, results
    
    # ========================================================================
    # 2. Scoring Aggregation
    # ========================================================================
    
    def aggregate_scores(
        self,
        spec_scores: List[SpecScore],
        standard_score: float = 1.0,
        certification_score: float = 1.0
    ) -> Dict[str, float]:
        """
        Aggregate multiple dimension scores into unified metrics.
        
        Args:
            spec_scores: Individual specification scores
            standard_score: Score from standard equivalence check
            certification_score: Score from certification check
            
        Returns:
            Dictionary with aggregated scores
        """
        if not spec_scores:
            return {
                'overall': 0.0,
                'weighted': 0.0,
                'average': 0.0,
                'critical_only': 0.0,
                'by_category': {}
            }
        
        # Simple average
        raw_scores = [s.raw_score for s in spec_scores]
        average = sum(raw_scores) / len(raw_scores) if raw_scores else 0.0
        
        # Weighted average
        total_weight = sum(s.weight for s in spec_scores)
        weighted = sum(s.weighted_score for s in spec_scores) / total_weight if total_weight > 0 else 0.0
        
        # Category breakdown
        by_category = {}
        for category in SpecCategory:
            cat_scores = [s for s in spec_scores if s.category == category]
            if cat_scores:
                cat_avg = sum(s.raw_score for s in cat_scores) / len(cat_scores)
                by_category[category.value] = round(cat_avg, 4)
        
        # Critical-only score
        critical_scores = [s for s in spec_scores if s.category == SpecCategory.CRITICAL]
        critical_only = sum(s.raw_score for s in critical_scores) / len(critical_scores) if critical_scores else 1.0
        
        # Overall score (combines all dimensions)
        overall = (
            weighted * 0.5 +
            standard_score * 0.25 +
            certification_score * 0.15 +
            critical_only * 0.1
        )
        
        return {
            'overall': round(overall, 4),
            'weighted': round(weighted, 4),
            'average': round(average, 4),
            'critical_only': round(critical_only, 4),
            'standard_score': round(standard_score, 4),
            'certification_score': round(certification_score, 4),
            'by_category': by_category
        }
    
    # ========================================================================
    # 3. Weighted Score Calculation
    # ========================================================================
    
    def calculate_weighted_score(
        self,
        spec_name: str,
        raw_score: float,
        custom_weight: Optional[float] = None
    ) -> Tuple[float, float, SpecCategory]:
        """
        Calculate weighted score for a specification.
        
        Args:
            spec_name: Name of the specification
            raw_score: Raw match score (0.0 - 1.0)
            custom_weight: Optional custom weight override
            
        Returns:
            Tuple of (weighted_score, weight, category)
        """
        # Determine category
        spec_lower = spec_name.lower().replace(' ', '_').replace('-', '_')
        category = self.SPEC_CATEGORIES.get(spec_lower, SpecCategory.STANDARD)
        
        # Get weight
        if custom_weight is not None:
            weight = custom_weight
        else:
            weight = self.weights.get(category, 1.0)
        
        weighted_score = raw_score * weight
        
        return weighted_score, weight, category
    
    def apply_weights_to_scores(
        self,
        raw_scores: Dict[str, float],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[SpecScore]:
        """
        Apply weights to a dictionary of raw scores.
        
        Args:
            raw_scores: Dictionary of spec_name -> raw_score
            custom_weights: Optional custom weights per spec
            
        Returns:
            List of SpecScore objects with weights applied
        """
        spec_scores = []
        
        for spec_name, raw_score in raw_scores.items():
            custom_weight = custom_weights.get(spec_name) if custom_weights else None
            weighted_score, weight, category = self.calculate_weighted_score(
                spec_name, raw_score, custom_weight
            )
            
            spec_scores.append(SpecScore(
                spec_name=spec_name,
                rfp_value=None,  # To be filled by caller
                product_value=None,
                raw_score=raw_score,
                weighted_score=weighted_score,
                weight=weight,
                category=category,
                match_type='calculated',
                explanation=f"Score: {raw_score:.2%} × Weight: {weight:.1f} = {weighted_score:.2f}"
            ))
        
        return spec_scores
    
    # ========================================================================
    # 4. Confidence Score Calculation
    # ========================================================================
    
    def calculate_confidence(
        self,
        spec_scores: List[SpecScore],
        data_completeness: float,
        verification_status: str = 'unverified',
        standard_confidence: float = 1.0
    ) -> float:
        """
        Calculate overall confidence score.
        
        Confidence is based on:
        - Data completeness (how many specs are available)
        - Match quality consistency
        - Verification status
        - Standard mapping confidence
        
        Args:
            spec_scores: List of specification scores
            data_completeness: Ratio of available specs (0.0 - 1.0)
            verification_status: 'verified', 'partially_verified', 'unverified'
            standard_confidence: Confidence from standard equivalence
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        if not spec_scores:
            return 0.0
        
        # 1. Data completeness factor (30%)
        completeness_factor = data_completeness
        
        # 2. Match consistency factor (25%)
        raw_scores = [s.raw_score for s in spec_scores]
        mean_score = sum(raw_scores) / len(raw_scores)
        variance = sum((s - mean_score) ** 2 for s in raw_scores) / len(raw_scores)
        std_dev = math.sqrt(variance) if variance > 0 else 0
        consistency_factor = 1.0 - min(std_dev, 0.5)  # Lower std = higher consistency
        
        # 3. Verification factor (20%)
        verification_factors = {
            'verified': 1.0,
            'partially_verified': 0.7,
            'unverified': 0.5
        }
        verification_factor = verification_factors.get(verification_status, 0.5)
        
        # 4. Critical specs factor (15%)
        critical_scores = [s for s in spec_scores if s.category == SpecCategory.CRITICAL]
        if critical_scores:
            critical_avg = sum(s.raw_score for s in critical_scores) / len(critical_scores)
            critical_factor = critical_avg
        else:
            critical_factor = 1.0
        
        # 5. Standard confidence factor (10%)
        standard_factor = standard_confidence
        
        # Calculate weighted confidence
        confidence = (
            completeness_factor * 0.30 +
            consistency_factor * 0.25 +
            verification_factor * 0.20 +
            critical_factor * 0.15 +
            standard_factor * 0.10
        )
        
        return round(min(confidence, 1.0), 4)
    
    # ========================================================================
    # 5. Match Explanation Generator
    # ========================================================================
    
    def generate_explanation(
        self,
        spec_scores: List[SpecScore],
        critical_failures: List[CriticalFailure],
        gaps: List[GapAnalysis],
        overall_score: float,
        quality: MatchQuality,
        recommendation: RecommendationLevel
    ) -> MatchExplanation:
        """
        Generate human-readable explanation for a match.
        
        Args:
            spec_scores: Individual specification scores
            critical_failures: List of critical failures
            gaps: List of identified gaps
            overall_score: Overall match score
            quality: Match quality tier
            recommendation: Recommendation level
            
        Returns:
            MatchExplanation with detailed information
        """
        strengths = []
        weaknesses = []
        critical_issues = []
        spec_details = []
        
        # Analyze spec scores
        for score in spec_scores:
            detail = {
                'spec': score.spec_name,
                'rfp': str(score.rfp_value),
                'product': str(score.product_value),
                'match': f"{score.raw_score:.0%}",
                'type': score.match_type
            }
            spec_details.append(detail)
            
            if score.raw_score >= 0.95:
                strengths.append(f"✓ {score.spec_name}: Excellent match ({score.match_type})")
            elif score.raw_score >= 0.8:
                strengths.append(f"✓ {score.spec_name}: Good match ({score.raw_score:.0%})")
            elif score.raw_score >= 0.5:
                weaknesses.append(f"△ {score.spec_name}: Partial match ({score.raw_score:.0%})")
            else:
                weaknesses.append(f"✗ {score.spec_name}: Poor match ({score.raw_score:.0%})")
        
        # Add critical failures
        for failure in critical_failures:
            critical_issues.append(
                f"⚠ {failure.failure_type.value}: {failure.explanation}"
            )
        
        # Generate summary
        if critical_failures:
            summary = f"Product has {len(critical_failures)} critical issue(s) that may disqualify it."
        elif quality == MatchQuality.EXCELLENT:
            summary = f"Excellent match with {overall_score:.0%} overall compatibility."
        elif quality == MatchQuality.GOOD:
            summary = f"Good match with {overall_score:.0%} overall compatibility. Minor gaps identified."
        elif quality == MatchQuality.FAIR:
            summary = f"Fair match with {overall_score:.0%} compatibility. Review gaps before selection."
        else:
            summary = f"Poor match with only {overall_score:.0%} compatibility. Not recommended."
        
        # Generate assessment
        if recommendation == RecommendationLevel.HIGHLY_RECOMMENDED:
            assessment = "This product meets or exceeds all requirements and is highly recommended for selection."
        elif recommendation == RecommendationLevel.RECOMMENDED:
            assessment = "This product meets most requirements and is suitable for selection with minor considerations."
        elif recommendation == RecommendationLevel.CONDITIONAL:
            assessment = "This product can be considered if gaps can be addressed or requirements relaxed."
        else:
            assessment = "This product does not meet requirements and should not be selected."
        
        return MatchExplanation(
            summary=summary,
            quality_tier=quality,
            recommendation=recommendation,
            strengths=strengths,
            weaknesses=weaknesses,
            critical_issues=critical_issues,
            spec_details=spec_details,
            overall_assessment=assessment
        )
    
    # ========================================================================
    # 6. Critical Failure Detection
    # ========================================================================
    
    def detect_critical_failures(
        self,
        rfp_specs: Dict[str, Any],
        product_specs: Dict[str, Any]
    ) -> List[CriticalFailure]:
        """
        Detect critical failures that should disqualify a product.
        
        Args:
            rfp_specs: RFP specifications
            product_specs: Product specifications
            
        Returns:
            List of critical failures
        """
        failures = []
        
        # 1. Voltage mismatch check
        rfp_voltage = self._extract_numeric(rfp_specs.get('voltage_rating') or rfp_specs.get('rated_voltage'))
        prod_voltage = self._extract_numeric(product_specs.get('voltage_rating') or product_specs.get('rated_voltage'))
        
        if rfp_voltage and prod_voltage:
            diff_percent = abs(rfp_voltage - prod_voltage) / rfp_voltage * 100
            if diff_percent > self.CRITICAL_THRESHOLDS['voltage_mismatch_percent']:
                if prod_voltage < rfp_voltage:
                    failures.append(CriticalFailure(
                        failure_type=FailureType.VOLTAGE_MISMATCH,
                        spec_name='voltage_rating',
                        rfp_value=rfp_voltage,
                        product_value=prod_voltage,
                        severity='critical',
                        explanation=f"Product voltage ({prod_voltage}V) is {diff_percent:.0f}% below requirement ({rfp_voltage}V)",
                        remediation="Select a product with higher voltage rating"
                    ))
        
        # 2. Temperature rating check
        rfp_temp = self._extract_numeric(rfp_specs.get('temperature_rating'))
        prod_temp = self._extract_numeric(product_specs.get('temperature_rating'))
        
        if rfp_temp and prod_temp:
            margin = prod_temp - rfp_temp
            if margin < self.CRITICAL_THRESHOLDS['temp_rating_min_margin']:
                failures.append(CriticalFailure(
                    failure_type=FailureType.TEMPERATURE_RATING,
                    spec_name='temperature_rating',
                    rfp_value=rfp_temp,
                    product_value=prod_temp,
                    severity='severe' if margin < 0 else 'moderate',
                    explanation=f"Product temp rating ({prod_temp}°C) has insufficient margin over requirement ({rfp_temp}°C)",
                    remediation="Select product with higher temperature rating"
                ))
        
        # 3. Conductor size check
        rfp_size = self._extract_numeric(rfp_specs.get('cross_section_sqmm') or rfp_specs.get('conductor_size'))
        prod_size = self._extract_numeric(product_specs.get('cross_section_sqmm') or product_specs.get('conductor_size'))
        
        if rfp_size and prod_size:
            diff_percent = abs(rfp_size - prod_size) / rfp_size * 100
            if diff_percent > self.CRITICAL_THRESHOLDS['size_mismatch_percent']:
                failures.append(CriticalFailure(
                    failure_type=FailureType.SIZE_OUT_OF_RANGE,
                    spec_name='cross_section_sqmm',
                    rfp_value=rfp_size,
                    product_value=prod_size,
                    severity='severe' if prod_size < rfp_size else 'moderate',
                    explanation=f"Conductor size ({prod_size} sq mm) differs by {diff_percent:.0f}% from requirement ({rfp_size} sq mm)",
                    remediation="Select correct conductor size"
                ))
        
        # 4. Material compatibility check
        rfp_material = str(rfp_specs.get('conductor_material', '')).lower()
        prod_material = str(product_specs.get('conductor_material', '')).lower()
        
        if rfp_material and prod_material:
            # Check for incompatible materials
            incompatible_pairs = [
                ('copper', 'aluminium'),
                ('aluminium', 'copper'),
            ]
            for mat1, mat2 in incompatible_pairs:
                if mat1 in rfp_material and mat2 in prod_material:
                    failures.append(CriticalFailure(
                        failure_type=FailureType.MATERIAL_INCOMPATIBLE,
                        spec_name='conductor_material',
                        rfp_value=rfp_material,
                        product_value=prod_material,
                        severity='critical',
                        explanation=f"Material mismatch: RFP requires {rfp_material}, product offers {prod_material}",
                        remediation=f"Select product with {rfp_material} conductor"
                    ))
        
        # 5. Required certifications check
        rfp_certs = set(str(c).upper() for c in (rfp_specs.get('certifications') or []))
        prod_certs = set(str(c).upper() for c in (product_specs.get('certifications') or []))
        
        # Critical certifications that must be present
        critical_certs = {'BIS', 'ISI', 'CPRI'}
        required_critical = rfp_certs & critical_certs
        
        for cert in required_critical:
            if cert not in prod_certs:
                failures.append(CriticalFailure(
                    failure_type=FailureType.CERTIFICATION_MISSING,
                    spec_name='certifications',
                    rfp_value=cert,
                    product_value=list(prod_certs),
                    severity='critical',
                    explanation=f"Required certification '{cert}' is missing",
                    remediation=f"Select product with {cert} certification"
                ))
        
        return failures
    
    # ========================================================================
    # 7. Gap Analysis
    # ========================================================================
    
    def analyze_gaps(
        self,
        rfp_specs: Dict[str, Any],
        product_specs: Dict[str, Any]
    ) -> List[GapAnalysis]:
        """
        Analyze gaps between RFP requirements and product specifications.
        
        Args:
            rfp_specs: RFP specifications
            product_specs: Product specifications
            
        Returns:
            List of gap analyses
        """
        gaps = []
        
        for spec_name, rfp_value in rfp_specs.items():
            prod_value = product_specs.get(spec_name)
            
            # Check for missing specs
            if prod_value is None:
                gaps.append(GapAnalysis(
                    spec_name=spec_name,
                    requirement=rfp_value,
                    actual=None,
                    gap_type='missing',
                    gap_magnitude=None,
                    impact=self._get_gap_impact(spec_name),
                    remediation_options=[
                        f"Request {spec_name} data from manufacturer",
                        "Check product datasheet for specification",
                        "Consider alternative product with complete specs"
                    ]
                ))
                continue
            
            # Check numeric gaps
            rfp_num = self._extract_numeric(rfp_value)
            prod_num = self._extract_numeric(prod_value)
            
            if rfp_num is not None and prod_num is not None:
                if prod_num < rfp_num:
                    gap_pct = (rfp_num - prod_num) / rfp_num * 100
                    gaps.append(GapAnalysis(
                        spec_name=spec_name,
                        requirement=rfp_value,
                        actual=prod_value,
                        gap_type='insufficient',
                        gap_magnitude=gap_pct,
                        impact=self._get_gap_impact(spec_name),
                        remediation_options=[
                            f"Select product with {spec_name} >= {rfp_value}",
                            "Request deviation approval if gap is acceptable",
                            "Check if requirement can be relaxed"
                        ]
                    ))
                elif prod_num > rfp_num * 1.5:  # Over 50% more than required
                    gaps.append(GapAnalysis(
                        spec_name=spec_name,
                        requirement=rfp_value,
                        actual=prod_value,
                        gap_type='over_specified',
                        gap_magnitude=(prod_num - rfp_num) / rfp_num * 100,
                        impact='low',
                        remediation_options=[
                            "Consider if over-specification adds value",
                            "Check for cost-optimized alternatives",
                            "Verify no compatibility issues from over-specification"
                        ]
                    ))
        
        return gaps
    
    def _get_gap_impact(self, spec_name: str) -> str:
        """Determine impact level of a gap based on spec category"""
        spec_lower = spec_name.lower().replace(' ', '_').replace('-', '_')
        category = self.SPEC_CATEGORIES.get(spec_lower, SpecCategory.STANDARD)
        
        impact_map = {
            SpecCategory.CRITICAL: 'high',
            SpecCategory.IMPORTANT: 'medium',
            SpecCategory.STANDARD: 'low',
            SpecCategory.INFORMATIONAL: 'low'
        }
        return impact_map.get(category, 'medium')
    
    # ========================================================================
    # 8. Match Quality Classifier
    # ========================================================================
    
    def classify_match_quality(
        self,
        overall_score: float,
        critical_failures: List[CriticalFailure],
        confidence: float
    ) -> MatchQuality:
        """
        Classify match into quality tiers.
        
        Args:
            overall_score: Overall match score (0.0 - 1.0)
            critical_failures: List of critical failures
            confidence: Confidence score
            
        Returns:
            MatchQuality enum
        """
        # Disqualified if critical failures in strict mode
        if self.strict_mode and critical_failures:
            return MatchQuality.DISQUALIFIED
        
        # Disqualified if any severe/critical failures
        severe_failures = [f for f in critical_failures if f.severity in ('critical', 'severe')]
        if severe_failures:
            return MatchQuality.DISQUALIFIED
        
        # Adjust score by confidence
        adjusted_score = overall_score * (0.7 + 0.3 * confidence)
        
        # Apply moderate failure penalty
        moderate_failures = [f for f in critical_failures if f.severity == 'moderate']
        penalty = len(moderate_failures) * 0.05
        adjusted_score = max(0, adjusted_score - penalty)
        
        # Classify
        if adjusted_score >= 0.95:
            return MatchQuality.EXCELLENT
        elif adjusted_score >= 0.85:
            return MatchQuality.GOOD
        elif adjusted_score >= 0.70:
            return MatchQuality.FAIR
        elif adjusted_score >= 0.50:
            return MatchQuality.POOR
        else:
            return MatchQuality.DISQUALIFIED
    
    # ========================================================================
    # 9. Recommendation Level Calculator
    # ========================================================================
    
    def calculate_recommendation(
        self,
        quality: MatchQuality,
        gaps: List[GapAnalysis],
        critical_failures: List[CriticalFailure]
    ) -> RecommendationLevel:
        """
        Calculate recommendation level based on match quality and issues.
        
        Args:
            quality: Match quality tier
            gaps: List of gaps
            critical_failures: List of critical failures
            
        Returns:
            RecommendationLevel enum
        """
        if quality == MatchQuality.DISQUALIFIED:
            return RecommendationLevel.NOT_RECOMMENDED
        
        # Count high-impact gaps
        high_impact_gaps = [g for g in gaps if g.impact == 'high']
        medium_impact_gaps = [g for g in gaps if g.impact == 'medium']
        
        if quality == MatchQuality.EXCELLENT and not high_impact_gaps:
            return RecommendationLevel.HIGHLY_RECOMMENDED
        
        if quality == MatchQuality.GOOD:
            if not high_impact_gaps and len(medium_impact_gaps) <= 2:
                return RecommendationLevel.RECOMMENDED
            else:
                return RecommendationLevel.CONDITIONAL
        
        if quality == MatchQuality.FAIR:
            return RecommendationLevel.CONDITIONAL
        
        return RecommendationLevel.NOT_RECOMMENDED
    
    # ========================================================================
    # 10. Batch Matching Support
    # ========================================================================
    
    def batch_match(
        self,
        requirements: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        top_n: int = 3
    ) -> BatchMatchResult:
        """
        Efficiently match multiple requirements against multiple products.
        
        Args:
            requirements: List of RFP requirements with specs
            products: List of products with specs
            top_n: Number of top matches to return per requirement
            
        Returns:
            BatchMatchResult with all matches
        """
        start_time = datetime.now()
        all_matches = []
        
        for req in requirements:
            req_name = req.get('name', 'Unknown')
            req_specs = req.get('specifications', {})
            
            matches_for_req = []
            
            for prod in products:
                prod_name = prod.get('name', 'Unknown')
                prod_sku = prod.get('sku', 'N/A')
                prod_specs = prod.get('specifications', {})
                
                # Full match analysis
                match = self.match_product(
                    rfp_product=req_name,
                    rfp_specs=req_specs,
                    oem_product=prod_name,
                    oem_sku=prod_sku,
                    oem_specs=prod_specs
                )
                matches_for_req.append(match)
            
            # Sort and keep top N
            matches_for_req.sort(key=lambda m: m.overall_score, reverse=True)
            all_matches.extend(matches_for_req[:top_n])
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Build summary
        excellent = sum(1 for m in all_matches if m.quality == MatchQuality.EXCELLENT)
        good = sum(1 for m in all_matches if m.quality == MatchQuality.GOOD)
        fair = sum(1 for m in all_matches if m.quality == MatchQuality.FAIR)
        poor = sum(1 for m in all_matches if m.quality == MatchQuality.POOR)
        disqualified = sum(1 for m in all_matches if m.quality == MatchQuality.DISQUALIFIED)
        
        summary = {
            'quality_distribution': {
                'excellent': excellent,
                'good': good,
                'fair': fair,
                'poor': poor,
                'disqualified': disqualified
            },
            'average_score': sum(m.overall_score for m in all_matches) / len(all_matches) if all_matches else 0,
            'highly_recommended_count': sum(1 for m in all_matches if m.recommendation == RecommendationLevel.HIGHLY_RECOMMENDED),
            'recommended_count': sum(1 for m in all_matches if m.recommendation == RecommendationLevel.RECOMMENDED),
        }
        
        return BatchMatchResult(
            total_requirements=len(requirements),
            total_products=len(products),
            total_matches=len(all_matches),
            processing_time_ms=processing_time,
            matches=all_matches,
            summary=summary
        )
    
    # ========================================================================
    # Main Matching Method
    # ========================================================================
    
    def match_product(
        self,
        rfp_product: str,
        rfp_specs: Dict[str, Any],
        oem_product: str,
        oem_sku: str,
        oem_specs: Dict[str, Any],
        rfp_standards: Optional[List[str]] = None,
        oem_standards: Optional[List[str]] = None
    ) -> MatchResult:
        """
        Perform complete match analysis between RFP requirement and product.
        
        Args:
            rfp_product: RFP product name
            rfp_specs: RFP specifications
            oem_product: OEM product name
            oem_sku: OEM product SKU
            oem_specs: OEM product specifications
            rfp_standards: Standards required by RFP
            oem_standards: Standards of the OEM product
            
        Returns:
            Complete MatchResult
        """
        start_time = datetime.now()
        
        # 1. Calculate spec scores
        spec_scores = self._calculate_spec_scores(rfp_specs, oem_specs)
        
        # 2. Check standards
        standard_equivalences = []
        standard_score = 1.0
        if rfp_standards and oem_standards:
            standard_score, standard_equivalences = self.check_multiple_standards(
                rfp_standards, oem_standards
            )
        
        # 3. Detect critical failures
        critical_failures = self.detect_critical_failures(rfp_specs, oem_specs)
        
        # 4. Analyze gaps
        gaps = self.analyze_gaps(rfp_specs, oem_specs)
        
        # 5. Calculate data completeness
        total_specs = len(rfp_specs)
        available_specs = sum(1 for k in rfp_specs if k in oem_specs)
        data_completeness = available_specs / total_specs if total_specs > 0 else 0
        
        # 6. Aggregate scores
        cert_score = self._calculate_certification_score(rfp_specs, oem_specs)
        aggregated = self.aggregate_scores(spec_scores, standard_score, cert_score)
        
        # 7. Calculate confidence
        standard_conf = sum(e.confidence for e in standard_equivalences) / len(standard_equivalences) if standard_equivalences else 1.0
        confidence = self.calculate_confidence(
            spec_scores,
            data_completeness,
            'unverified',
            standard_conf
        )
        
        # 8. Classify quality
        quality = self.classify_match_quality(
            aggregated['overall'],
            critical_failures,
            confidence
        )
        
        # 9. Calculate recommendation
        recommendation = self.calculate_recommendation(quality, gaps, critical_failures)
        
        # 10. Generate explanation
        explanation = self.generate_explanation(
            spec_scores,
            critical_failures,
            gaps,
            aggregated['overall'],
            quality,
            recommendation
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchResult(
            rfp_product=rfp_product,
            oem_product=oem_product,
            oem_sku=oem_sku,
            overall_score=aggregated['overall'],
            confidence=confidence,
            weighted_score=aggregated['weighted'],
            quality=quality,
            recommendation=recommendation,
            spec_scores=spec_scores,
            critical_failures=critical_failures,
            gaps=gaps,
            standard_equivalences=standard_equivalences,
            explanation=explanation,
            matched_at=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
    
    def _calculate_spec_scores(
        self,
        rfp_specs: Dict[str, Any],
        oem_specs: Dict[str, Any]
    ) -> List[SpecScore]:
        """Calculate individual specification scores"""
        spec_scores = []
        
        for spec_name, rfp_value in rfp_specs.items():
            oem_value = oem_specs.get(spec_name)
            
            if oem_value is None:
                raw_score = 0.0
                match_type = 'none'
                explanation = f"Specification not found in product"
            else:
                raw_score, match_type, explanation = self._compare_values(
                    spec_name, rfp_value, oem_value
                )
            
            weighted_score, weight, category = self.calculate_weighted_score(
                spec_name, raw_score
            )
            
            spec_scores.append(SpecScore(
                spec_name=spec_name,
                rfp_value=rfp_value,
                product_value=oem_value,
                raw_score=raw_score,
                weighted_score=weighted_score,
                weight=weight,
                category=category,
                match_type=match_type,
                explanation=explanation
            ))
        
        return spec_scores
    
    def _compare_values(
        self,
        spec_name: str,
        rfp_value: Any,
        oem_value: Any
    ) -> Tuple[float, str, str]:
        """Compare RFP and OEM values, returning (score, match_type, explanation)"""
        # Handle None values
        if rfp_value is None or oem_value is None:
            return 0.0, 'none', 'Value missing'
        
        # Normalize values
        rfp_str = str(rfp_value).lower().strip()
        oem_str = str(oem_value).lower().strip()
        
        # Exact match
        if rfp_str == oem_str:
            return 1.0, 'exact', f"Exact match: {rfp_value}"
        
        # Numeric comparison
        rfp_num = self._extract_numeric(rfp_value)
        oem_num = self._extract_numeric(oem_value)
        
        if rfp_num is not None and oem_num is not None:
            if rfp_num == oem_num:
                return 1.0, 'exact', f"Numeric match: {rfp_num}"
            
            if rfp_num != 0:
                diff_pct = abs(rfp_num - oem_num) / rfp_num
                if diff_pct <= 0.05:
                    return 0.95, 'range', f"Within 5% tolerance"
                elif diff_pct <= 0.10:
                    return 0.85, 'range', f"Within 10% tolerance"
                elif diff_pct <= 0.20:
                    return 0.70, 'partial', f"Within 20% - {diff_pct*100:.0f}% difference"
                else:
                    return max(0, 1 - diff_pct), 'partial', f"{diff_pct*100:.0f}% difference"
        
        # String partial match
        if rfp_str in oem_str or oem_str in rfp_str:
            return 0.9, 'partial', f"Partial string match"
        
        # Word overlap
        rfp_words = set(rfp_str.split())
        oem_words = set(oem_str.split())
        if rfp_words and oem_words:
            overlap = len(rfp_words & oem_words) / max(len(rfp_words), len(oem_words))
            if overlap > 0:
                return overlap, 'semantic', f"{overlap*100:.0f}% word overlap"
        
        return 0.0, 'none', f"No match: {rfp_value} vs {oem_value}"
    
    def _extract_numeric(self, value: Any) -> Optional[float]:
        """Extract numeric value from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            match = re.search(r'([\d.]+)', value)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _calculate_certification_score(
        self,
        rfp_specs: Dict[str, Any],
        oem_specs: Dict[str, Any]
    ) -> float:
        """Calculate certification compliance score"""
        rfp_certs = set(str(c).upper() for c in (rfp_specs.get('certifications') or []))
        oem_certs = set(str(c).upper() for c in (oem_specs.get('certifications') or []))
        
        if not rfp_certs:
            return 1.0
        
        matched = len(rfp_certs & oem_certs)
        return matched / len(rfp_certs)


# ============================================================================
# Module-level convenience functions
# ============================================================================

_engine = None


def get_matching_engine(
    custom_weights: Optional[Dict[str, float]] = None,
    strict_mode: bool = False
) -> MatchingEngine:
    """Get or create the matching engine singleton"""
    global _engine
    if _engine is None or custom_weights or strict_mode:
        _engine = MatchingEngine(custom_weights, strict_mode)
    return _engine


def match_product(
    rfp_product: str,
    rfp_specs: Dict[str, Any],
    oem_product: str,
    oem_sku: str,
    oem_specs: Dict[str, Any],
    **kwargs
) -> MatchResult:
    """Convenience function to match a single product"""
    engine = get_matching_engine()
    return engine.match_product(
        rfp_product, rfp_specs, oem_product, oem_sku, oem_specs, **kwargs
    )


def batch_match(
    requirements: List[Dict[str, Any]],
    products: List[Dict[str, Any]],
    top_n: int = 3
) -> BatchMatchResult:
    """Convenience function for batch matching"""
    engine = get_matching_engine()
    return engine.batch_match(requirements, products, top_n)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize engine
    engine = MatchingEngine()
    
    # Sample RFP requirement
    rfp_specs = {
        'conductor_material': 'Electrolytic Copper',
        'insulation_type': 'PVC',
        'voltage_rating': '1100V',
        'cross_section_sqmm': 4.0,
        'number_of_cores': 4,
        'temperature_rating': '70°C',
        'standard': 'IS 1554-1'
    }
    
    # Sample OEM product
    oem_specs = {
        'conductor_material': 'Copper',
        'insulation_type': 'PVC Type A',
        'voltage_rating': '1100V AC',
        'cross_section_sqmm': 4.0,
        'number_of_cores': 4,
        'temperature_rating': '70°C',
        'standard': 'IS 1554-1',
        'certifications': ['BIS', 'ISI']
    }
    
    # Perform match
    result = engine.match_product(
        rfp_product="PVC Insulated Power Cable 4C x 4 sq mm",
        rfp_specs=rfp_specs,
        oem_product="ACME Power Cable PVC 4C4",
        oem_sku="ACME-PVC-4C4-001",
        oem_specs=oem_specs,
        rfp_standards=['IS 1554-1'],
        oem_standards=['IS 1554-1', 'IEC 60502-1']
    )
    
    # Print results
    print(f"\n{'='*60}")
    print("MATCHING ENGINE DEMO")
    print('='*60)
    print(f"\nRFP Product: {result.rfp_product}")
    print(f"OEM Product: {result.oem_product} ({result.oem_sku})")
    print(f"\nOverall Score: {result.overall_score:.1%}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Quality: {result.quality.value}")
    print(f"Recommendation: {result.recommendation.value}")
    
    print(f"\n--- Explanation ---")
    print(f"Summary: {result.explanation.summary}")
    print(f"\nStrengths:")
    for s in result.explanation.strengths:
        print(f"  {s}")
    
    if result.explanation.weaknesses:
        print(f"\nWeaknesses:")
        for w in result.explanation.weaknesses:
            print(f"  {w}")
    
    if result.explanation.critical_issues:
        print(f"\nCritical Issues:")
        for c in result.explanation.critical_issues:
            print(f"  {c}")
    
    print(f"\n{result.explanation.overall_assessment}")
    print(f"\nProcessing time: {result.processing_time_ms:.2f}ms")
