"""Master Agent - Main Orchestrator for RFP Response System"""

# Legacy orchestrator
from .orchestrator import MasterAgent, ConversationState, RFPSummary, ConsolidatedResponse

# New comprehensive orchestrator
from .main_orchestrator import (
    # Enums
    WorkflowState,
    AgentStatus,
    MessagePriority,
    MessageType,
    QualityLevel,
    
    # Data Classes
    AgentInfo,
    QueueMessage,
    WorkflowContext,
    ValidationResult,
    DocumentSection,
    AuditEntry,
    
    # Core Classes
    MainOrchestrator,
    OrchestratorLogger,
    AgentRegistry,
    WorkflowStateMachine,
    
    # Agent Integrations
    AgentIntegration,
    SalesAgentIntegration,
    TechnicalAgentIntegration,
    PricingAgentIntegration,
    
    # Communication
    MessageQueueSystem,
    AgentCommunicationProtocol,
    
    # Processing
    ContextAwareSummarizer,
    RoleSpecificFormatter,
    ResponseConsolidator,
    FinalDocumentGenerator,
    
    # Validation
    QualityValidator,
    CompletenessChecker,
    ConsistencyValidator,
    
    # Output
    OutputFormatter,
    PDFReportGenerator,
    ExecutiveSummaryWriter,
    DetailedResponseCompiler,
    AuditTrailGenerator,
    
    # Utilities
    MockDataHandler,
    OrchestratorAPI,
)

__all__ = [
    # Legacy
    'MasterAgent',
    'ConversationState',
    'RFPSummary',
    'ConsolidatedResponse',
    
    # Enums
    'WorkflowState',
    'AgentStatus',
    'MessagePriority',
    'MessageType',
    'QualityLevel',
    
    # Data Classes
    'AgentInfo',
    'QueueMessage',
    'WorkflowContext',
    'ValidationResult',
    'DocumentSection',
    'AuditEntry',
    
    # Core
    'MainOrchestrator',
    'OrchestratorLogger',
    'AgentRegistry',
    'WorkflowStateMachine',
    
    # Integrations
    'AgentIntegration',
    'SalesAgentIntegration',
    'TechnicalAgentIntegration',
    'PricingAgentIntegration',
    
    # Communication
    'MessageQueueSystem',
    'AgentCommunicationProtocol',
    
    # Processing
    'ContextAwareSummarizer',
    'RoleSpecificFormatter',
    'ResponseConsolidator',
    'FinalDocumentGenerator',
    
    # Validation
    'QualityValidator',
    'CompletenessChecker',
    'ConsistencyValidator',
    
    # Output
    'OutputFormatter',
    'PDFReportGenerator',
    'ExecutiveSummaryWriter',
    'DetailedResponseCompiler',
    'AuditTrailGenerator',
    
    # Utilities
    'MockDataHandler',
    'OrchestratorAPI',
]
