"""
Sales Agent - Comprehensive RFP Monitoring and Selection System

This module provides a full-featured Sales Agent for:
- URL monitoring and web scraping
- RFP detection and relevance filtering
- Priority scoring and selection
- Orchestrator handoff
- Dashboard and analytics
"""

# Import from the new comprehensive sales_agent module
from .sales_agent import (
    # Enums
    AgentState,
    RFPPriority,
    RFPSource,
    AlertLevel,
    
    # Data Classes
    URLMonitorConfig,
    ScrapedRFP,
    Alert,
    ScrapeResult,
    ScrapingStats,
    
    # Core Classes
    SalesAgent,
    SalesAgentLogger,
    URLMonitorManager,
    RateLimiter,
    ProxyRotator,
    WebScraper,
    RFPDetector,
    KeywordFilter,
    PriorityScorer,
    AlertManager,
    RFPMetadataExtractor,
    DuplicateDetector,
    StatisticsTracker,
    RFPSummaryGenerator,
    RFPSelector,
    OrchestratorHandoff,
    Scheduler,
    AgentStateManager,
    HealthChecker,
    StatusReporter,
    ConfigManager,
)

# Legacy import for backward compatibility
from .rfp_scanner import SalesAgent as LegacySalesAgent

__all__ = [
    # Enums
    'AgentState',
    'RFPPriority',
    'RFPSource',
    'AlertLevel',
    
    # Data Classes
    'URLMonitorConfig',
    'ScrapedRFP',
    'Alert',
    'ScrapeResult',
    'ScrapingStats',
    
    # Core Classes
    'SalesAgent',
    'SalesAgentLogger',
    'URLMonitorManager',
    'RateLimiter',
    'ProxyRotator',
    'WebScraper',
    'RFPDetector',
    'KeywordFilter',
    'PriorityScorer',
    'AlertManager',
    'RFPMetadataExtractor',
    'DuplicateDetector',
    'StatisticsTracker',
    'RFPSummaryGenerator',
    'RFPSelector',
    'OrchestratorHandoff',
    'Scheduler',
    'AgentStateManager',
    'HealthChecker',
    'StatusReporter',
    'ConfigManager',
    
    # Legacy
    'LegacySalesAgent',
]
