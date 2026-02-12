"""Shared utilities for agents"""
from .matching_engine import (
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

__all__ = [
    # Matching Engine
    'MatchingEngine',
    'MatchQuality',
    'RecommendationLevel',
    'FailureType',
    'SpecCategory',
    'StandardEquivalenceResult',
    'SpecScore',
    'CriticalFailure',
    'GapAnalysis',
    'MatchExplanation',
    'MatchResult',
    'BatchMatchResult',
    'get_matching_engine',
    'match_product',
    'batch_match',
]