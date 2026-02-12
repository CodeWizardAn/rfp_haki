"""Technical Agent - Specification Matcher and OEM Recommender"""

# Original spec matcher (legacy)
from .spec_matcher import TechnicalAgent as LegacyTechnicalAgent

# Comprehensive Technical Agent with all 51 features
from .technical_agent import (
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
    VectorSearchIntegration,
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

__all__ = [
    # Enums
    'MatchConfidence',
    'RiskLevel',
    'ComplianceStatus',
    'ProcessingMode',
    
    # Data Classes
    'RFPRequirement',
    'ProductMatch',
    'ComparisonRow',
    'TechnicalReport',
    'AgentMessage',
    'WebhookConfig',
    
    # Core Classes
    'TechnicalAgent',
    'LegacyTechnicalAgent',
    'TechnicalAgentLogger',
    'RFPRequirementParser',
    'ProductRequirementExtractor',
    'ScopeOfSupplyAnalyzer',
    'MultiItemRFPHandler',
    'ProductCatalogQuerier',
    'VectorSearchIntegration',
    'SpecificationMatchingOrchestrator',
    'TopKSelector',
    'MatchScoreCalculator',
    'ComparisonTableGenerator',
    'GapAnalysisGenerator',
    'SpecificationExplanationGenerator',
    'TechnicalRiskAssessor',
    'ComplianceChecker',
    'TechnicalSummaryGenerator',
    'ProductRecommendationRanker',
    'CustomProductFlagger',
    'TechnicalReportFormatter',
    'DetailedSpecComparison',
    'EdgeCaseHandler',
    'TechnicalValidator',
    'AgentOutputHandler',
    'TechnicalAgentMemory',
    'PerformanceTracker',
    'ErrorRecoveryHandler',
    'BatchProcessor',
    'AsyncOperationSupport',
    'TechnicalAgentAPI',
    'WebhookManager',
]
