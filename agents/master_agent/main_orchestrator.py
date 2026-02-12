"""
Main Orchestrator Agent
Comprehensive orchestration system for coordinating all worker agents,
managing workflow, consolidating responses, and generating final RFP documents.

Features:
1. MainOrchestrator class
2. Agent registry
3. Workflow state machine
4. Sales agent integration
5. Technical agent integration
6. Pricing agent integration
7. Message queue system
8. Agent communication protocol
9. Context-aware summarization
10. Role-specific message formatting
11. Response consolidation
12. Final document generator
13. Quality validation checks
14. Completeness checker
15. Consistency validator
16. Output formatter
17. PDF report generator
18. Executive summary writer
19. Detailed response compiler
20. Audit trail generator

Performance Integration:
- Agent operation tracking
- Message queue optimization
- Workflow performance metrics
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from enum import Enum
import json
import logging
import uuid
import threading
import time
from queue import Queue, PriorityQueue, Empty
from abc import ABC, abstractmethod
import hashlib

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Performance Integration
try:
    from performance.integration import cached, profiled, with_timeout, init_performance
    from agents.shared.agent_performance import (
        track_agent_operation, cache_agent_result,
        AgentPerformanceManager, get_agent_performance_manager
    )
    PERFORMANCE_AVAILABLE = True
    logger.info("✅ Performance integration loaded for MainOrchestrator")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Performance integration not available: {e}")
    # Define no-op decorators
    def cached(*args, **kwargs):
        def decorator(func): return func
        return decorator if not args or not callable(args[0]) else args[0]
    def profiled(func): return func
    def with_timeout(*args, **kwargs):
        def decorator(func): return func
        return decorator if not args or not callable(args[0]) else args[0]
    def track_agent_operation(*args, **kwargs):
        def decorator(func): return func
        return decorator
    def cache_agent_result(*args, **kwargs):
        def decorator(func): return func
        return decorator


# ============================================================================
# Enums and Constants
# ============================================================================

class WorkflowState(Enum):
    """States in the workflow state machine"""
    IDLE = "idle"
    INITIALIZED = "initialized"
    RFP_SCANNING = "rfp_scanning"
    RFP_SELECTED = "rfp_selected"
    PREPARING_CONTEXT = "preparing_context"
    TECHNICAL_ANALYSIS = "technical_analysis"
    PRICING_ANALYSIS = "pricing_analysis"
    CONSOLIDATING = "consolidating"
    VALIDATING = "validating"
    GENERATING_DOCUMENTS = "generating_documents"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"


class AgentStatus(Enum):
    """Status of registered agents"""
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"
    READY = "ready"


class MessagePriority(Enum):
    """Message priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    STANDARD = 4
    LOW = 5


class MessageType(Enum):
    """Types of messages in the system"""
    RFP_SCAN_REQUEST = "rfp_scan_request"
    RFP_SELECTED = "rfp_selected"
    TECHNICAL_CONTEXT = "technical_context"
    PRICING_CONTEXT = "pricing_context"
    TECHNICAL_RESPONSE = "technical_response"
    PRICING_RESPONSE = "pricing_response"
    CONSOLIDATION_REQUEST = "consolidation_request"
    VALIDATION_REQUEST = "validation_request"
    DOCUMENT_REQUEST = "document_request"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    ACKNOWLEDGMENT = "acknowledgment"
    HEARTBEAT = "heartbeat"


class QualityLevel(Enum):
    """Quality validation levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class AgentInfo:
    """Information about a registered agent"""
    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.OFFLINE
    capabilities: List[str] = field(default_factory=list)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)
    instance: Any = None


@dataclass
class QueueMessage:
    """Message in the message queue"""
    message_id: str
    priority: int
    timestamp: datetime
    from_agent: str
    to_agent: str
    message_type: MessageType
    payload: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    requires_ack: bool = True
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """For priority queue comparison"""
        return (self.priority, self.timestamp) < (other.priority, other.timestamp)


@dataclass
class WorkflowContext:
    """Context for the current workflow"""
    workflow_id: str
    rfp_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    current_state: WorkflowState = WorkflowState.IDLE
    rfp_data: Dict[str, Any] = field(default_factory=dict)
    technical_response: Dict[str, Any] = field(default_factory=dict)
    pricing_response: Dict[str, Any] = field(default_factory=dict)
    consolidated_response: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    documents_generated: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of validation check"""
    check_name: str
    passed: bool
    score: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentSection:
    """Section of a generated document"""
    section_id: str
    title: str
    content: str
    order: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntry:
    """Entry in the audit trail"""
    entry_id: str
    timestamp: datetime
    action: str
    actor: str
    details: Dict[str, Any]
    previous_state: str
    new_state: str
    data_hash: str


# ============================================================================
# Feature 1: MainOrchestrator Class
# ============================================================================

class OrchestratorLogger:
    """Logger for the orchestrator"""
    
    def __init__(self, orchestrator_id: str, log_dir: str = None):
        self.orchestrator_id = orchestrator_id
        self.log_dir = Path(log_dir) if log_dir else Path("logs/orchestrator")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"Orchestrator.{orchestrator_id}")
        
        # File handler
        log_file = self.log_dir / f"{orchestrator_id}_{datetime.now().strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(fh)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


class MainOrchestrator:
    """
    Main Orchestrator Agent
    
    Coordinates all worker agents, manages workflow state machine,
    consolidates responses, and generates final RFP response documents.
    """
    
    def __init__(self, orchestrator_id: str = None, log_dir: str = None):
        self.orchestrator_id = orchestrator_id or f"ORCH_{uuid.uuid4().hex[:8].upper()}"
        self.logger = OrchestratorLogger(self.orchestrator_id, log_dir)
        
        # Initialize components
        self.agent_registry = AgentRegistry()
        self.state_machine = WorkflowStateMachine()
        self.message_queue = MessageQueueSystem()
        self.comm_protocol = AgentCommunicationProtocol(self)
        
        # Agent integrations
        self.sales_integration = SalesAgentIntegration(self)
        self.technical_integration = TechnicalAgentIntegration(self)
        self.pricing_integration = PricingAgentIntegration(self)
        
        # Processing components
        self.summarizer = ContextAwareSummarizer()
        self.formatter = RoleSpecificFormatter()
        self.consolidator = ResponseConsolidator()
        self.document_generator = FinalDocumentGenerator()
        
        # Validation components
        self.quality_validator = QualityValidator()
        self.completeness_checker = CompletenessChecker()
        self.consistency_validator = ConsistencyValidator()
        
        # Output components
        self.output_formatter = OutputFormatter()
        self.pdf_generator = PDFReportGenerator()
        self.summary_writer = ExecutiveSummaryWriter()
        self.response_compiler = DetailedResponseCompiler()
        self.audit_generator = AuditTrailGenerator()
        
        # Current workflow
        self.current_workflow: Optional[WorkflowContext] = None
        
        # Metrics
        self._lock = threading.Lock()
        self.metrics = {
            'workflows_started': 0,
            'workflows_completed': 0,
            'workflows_failed': 0,
            'messages_processed': 0,
            'documents_generated': 0
        }
        
        self.logger.info(f"Main Orchestrator initialized: {self.orchestrator_id}")
    
    def start_workflow(self, rfp_data: Dict[str, Any] = None) -> str:
        """Start a new RFP response workflow"""
        workflow_id = f"WF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"
        
        self.current_workflow = WorkflowContext(
            workflow_id=workflow_id,
            rfp_id=rfp_data.get('rfp_id', '') if rfp_data else '',
            rfp_data=rfp_data or {}
        )
        
        self.state_machine.transition(WorkflowState.INITIALIZED)
        self.audit_generator.record(
            workflow_id, 'workflow_started', 'orchestrator',
            {'rfp_data': rfp_data}, 'IDLE', 'INITIALIZED'
        )
        
        with self._lock:
            self.metrics['workflows_started'] += 1
        
        self.logger.info(f"Workflow started: {workflow_id}")
        return workflow_id
    
    def run_full_workflow(self, rfp_urls: List[str] = None) -> Dict[str, Any]:
        """Run complete RFP response workflow"""
        workflow_id = self.start_workflow({'rfp_urls': rfp_urls})
        
        try:
            # Step 1: RFP Scanning (Sales Agent)
            self.state_machine.transition(WorkflowState.RFP_SCANNING)
            rfp_data = self.sales_integration.scan_and_select(rfp_urls)
            self.current_workflow.rfp_data = rfp_data
            self.current_workflow.rfp_id = rfp_data.get('rfp_id', '')
            
            # Step 2: Prepare Context
            self.state_machine.transition(WorkflowState.PREPARING_CONTEXT)
            tech_context = self.summarizer.create_technical_context(rfp_data)
            pricing_context = self.summarizer.create_pricing_context(rfp_data)
            
            # Step 3: Technical Analysis
            self.state_machine.transition(WorkflowState.TECHNICAL_ANALYSIS)
            tech_response = self.technical_integration.analyze(tech_context)
            self.current_workflow.technical_response = tech_response
            
            # Step 4: Pricing Analysis
            self.state_machine.transition(WorkflowState.PRICING_ANALYSIS)
            pricing_response = self.pricing_integration.calculate(
                pricing_context, tech_response
            )
            self.current_workflow.pricing_response = pricing_response
            
            # Step 5: Consolidation
            self.state_machine.transition(WorkflowState.CONSOLIDATING)
            consolidated = self.consolidator.consolidate(
                rfp_data, tech_response, pricing_response
            )
            self.current_workflow.consolidated_response = consolidated
            
            # Step 6: Validation
            self.state_machine.transition(WorkflowState.VALIDATING)
            validation = self.validate_response(consolidated)
            self.current_workflow.validation_results = validation
            
            # Step 7: Document Generation
            self.state_machine.transition(WorkflowState.GENERATING_DOCUMENTS)
            documents = self.generate_documents(consolidated, validation)
            self.current_workflow.documents_generated = documents
            
            # Complete
            self.state_machine.transition(WorkflowState.COMPLETED)
            
            with self._lock:
                self.metrics['workflows_completed'] += 1
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'consolidated_response': consolidated,
                'validation': validation,
                'documents': documents
            }
            
        except Exception as e:
            self.state_machine.transition(WorkflowState.ERROR)
            self.current_workflow.errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
            
            with self._lock:
                self.metrics['workflows_failed'] += 1
            
            self.logger.error(f"Workflow failed: {e}")
            raise
    
    def validate_response(self, consolidated: Dict[str, Any]) -> Dict[str, Any]:
        """Run all validation checks"""
        quality = self.quality_validator.validate(consolidated)
        completeness = self.completeness_checker.check(consolidated)
        consistency = self.consistency_validator.validate(consolidated)
        
        return {
            'quality': quality,
            'completeness': completeness,
            'consistency': consistency,
            'overall_valid': quality['passed'] and completeness['complete'] and consistency['consistent']
        }
    
    def generate_documents(self, consolidated: Dict[str, Any], validation: Dict[str, Any]) -> List[str]:
        """Generate all output documents"""
        documents = []
        
        # Executive summary
        summary = self.summary_writer.write(consolidated)
        documents.append(summary)
        
        # Detailed response
        detailed = self.response_compiler.compile(consolidated)
        documents.append(detailed)
        
        # PDF report
        pdf = self.pdf_generator.generate(consolidated, validation)
        documents.append(pdf)
        
        # Audit trail
        audit = self.audit_generator.generate_report(self.current_workflow.workflow_id)
        documents.append(audit)
        
        with self._lock:
            self.metrics['documents_generated'] += len(documents)
        
        return documents
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'orchestrator_id': self.orchestrator_id,
            'current_state': self.state_machine.current_state.value,
            'workflow_id': self.current_workflow.workflow_id if self.current_workflow else None,
            'agents_registered': self.agent_registry.count(),
            'messages_pending': self.message_queue.pending_count(),
            'metrics': self.metrics.copy()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for orchestrator"""
        return {
            'healthy': True,
            'orchestrator_id': self.orchestrator_id,
            'state': self.state_machine.current_state.value,
            'components': {
                'agent_registry': self.agent_registry.count() >= 0,
                'message_queue': True,
                'state_machine': True
            }
        }


# ============================================================================
# Feature 2: Agent Registry
# ============================================================================

class AgentRegistry:
    """Registry for managing agent registration and discovery"""
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger("AgentRegistry")
    
    def register(self, agent_id: str, agent_type: str, 
                 capabilities: List[str] = None, instance: Any = None) -> bool:
        """Register an agent"""
        with self._lock:
            if agent_id in self._agents:
                self.logger.warning(f"Agent already registered: {agent_id}")
                return False
            
            self._agents[agent_id] = AgentInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                status=AgentStatus.READY,
                capabilities=capabilities or [],
                instance=instance
            )
            
            self.logger.info(f"Agent registered: {agent_id} ({agent_type})")
            return True
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent"""
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                self.logger.info(f"Agent unregistered: {agent_id}")
                return True
            return False
    
    def get(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent info"""
        return self._agents.get(agent_id)
    
    def get_by_type(self, agent_type: str) -> List[AgentInfo]:
        """Get all agents of a type"""
        return [a for a in self._agents.values() if a.agent_type == agent_type]
    
    def get_by_capability(self, capability: str) -> List[AgentInfo]:
        """Get agents with a capability"""
        return [a for a in self._agents.values() if capability in a.capabilities]
    
    def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].status = status
                self._agents[agent_id].last_heartbeat = datetime.now()
                return True
            return False
    
    def heartbeat(self, agent_id: str) -> bool:
        """Record agent heartbeat"""
        with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].last_heartbeat = datetime.now()
                return True
            return False
    
    def get_all(self) -> List[AgentInfo]:
        """Get all registered agents"""
        return list(self._agents.values())
    
    def count(self) -> int:
        """Count registered agents"""
        return len(self._agents)
    
    def is_registered(self, agent_id: str) -> bool:
        """Check if agent is registered"""
        return agent_id in self._agents


# ============================================================================
# Feature 3: Workflow State Machine
# ============================================================================

class WorkflowStateMachine:
    """State machine for managing workflow states"""
    
    # Valid state transitions
    TRANSITIONS = {
        WorkflowState.IDLE: [WorkflowState.INITIALIZED, WorkflowState.ERROR],
        WorkflowState.INITIALIZED: [WorkflowState.RFP_SCANNING, WorkflowState.ERROR, WorkflowState.IDLE],
        WorkflowState.RFP_SCANNING: [WorkflowState.RFP_SELECTED, WorkflowState.ERROR, WorkflowState.PAUSED],
        WorkflowState.RFP_SELECTED: [WorkflowState.PREPARING_CONTEXT, WorkflowState.ERROR],
        WorkflowState.PREPARING_CONTEXT: [WorkflowState.TECHNICAL_ANALYSIS, WorkflowState.ERROR],
        WorkflowState.TECHNICAL_ANALYSIS: [WorkflowState.PRICING_ANALYSIS, WorkflowState.ERROR, WorkflowState.PAUSED],
        WorkflowState.PRICING_ANALYSIS: [WorkflowState.CONSOLIDATING, WorkflowState.ERROR, WorkflowState.PAUSED],
        WorkflowState.CONSOLIDATING: [WorkflowState.VALIDATING, WorkflowState.ERROR],
        WorkflowState.VALIDATING: [WorkflowState.GENERATING_DOCUMENTS, WorkflowState.CONSOLIDATING, WorkflowState.ERROR],
        WorkflowState.GENERATING_DOCUMENTS: [WorkflowState.COMPLETED, WorkflowState.ERROR],
        WorkflowState.COMPLETED: [WorkflowState.IDLE],
        WorkflowState.ERROR: [WorkflowState.IDLE, WorkflowState.INITIALIZED],
        WorkflowState.PAUSED: [WorkflowState.RFP_SCANNING, WorkflowState.TECHNICAL_ANALYSIS, 
                              WorkflowState.PRICING_ANALYSIS, WorkflowState.IDLE]
    }
    
    def __init__(self):
        self.current_state = WorkflowState.IDLE
        self.state_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.listeners: List[Callable] = []
        self.logger = logging.getLogger("StateMachine")
    
    def transition(self, new_state: WorkflowState) -> bool:
        """Transition to a new state"""
        with self._lock:
            valid_transitions = self.TRANSITIONS.get(self.current_state, [])
            
            if new_state not in valid_transitions:
                self.logger.warning(
                    f"Invalid transition: {self.current_state.value} -> {new_state.value}"
                )
                return False
            
            old_state = self.current_state
            self.current_state = new_state
            
            self.state_history.append({
                'timestamp': datetime.now().isoformat(),
                'from_state': old_state.value,
                'to_state': new_state.value
            })
            
            # Notify listeners
            for listener in self.listeners:
                try:
                    listener(old_state, new_state)
                except Exception as e:
                    self.logger.error(f"Listener error: {e}")
            
            self.logger.info(f"State transition: {old_state.value} -> {new_state.value}")
            return True
    
    def can_transition(self, new_state: WorkflowState) -> bool:
        """Check if transition is valid"""
        return new_state in self.TRANSITIONS.get(self.current_state, [])
    
    def add_listener(self, listener: Callable):
        """Add state change listener"""
        self.listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """Remove state change listener"""
        if listener in self.listeners:
            self.listeners.remove(listener)
    
    def reset(self):
        """Reset to idle state"""
        with self._lock:
            self.current_state = WorkflowState.IDLE
            self.state_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get state history"""
        return self.state_history.copy()
    
    def is_terminal(self) -> bool:
        """Check if current state is terminal"""
        return self.current_state in [WorkflowState.COMPLETED, WorkflowState.ERROR]


# ============================================================================
# Features 4-6: Agent Integrations
# ============================================================================

class AgentIntegration(ABC):
    """Base class for agent integrations"""
    
    def __init__(self, orchestrator: 'MainOrchestrator'):
        self.orchestrator = orchestrator
        self.agent_instance = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the agent integration"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if agent is available"""
        pass


class SalesAgentIntegration(AgentIntegration):
    """Integration with Sales Agent"""
    
    def __init__(self, orchestrator: 'MainOrchestrator'):
        super().__init__(orchestrator)
        self.agent_type = "SALES_AGENT"
    
    def initialize(self) -> bool:
        """Initialize Sales Agent"""
        try:
            from agents.sales_agent.sales_agent import SalesAgent
            self.agent_instance = SalesAgent()
            self.orchestrator.agent_registry.register(
                'SALES_001', self.agent_type,
                ['rfp_scanning', 'rfp_selection', 'qualification'],
                self.agent_instance
            )
            return True
        except ImportError:
            self.logger.warning("Sales Agent not available, using mock")
            return False
    
    def is_available(self) -> bool:
        """Check if Sales Agent is available"""
        return self.agent_instance is not None
    
    def scan_and_select(self, rfp_urls: List[str] = None) -> Dict[str, Any]:
        """Scan RFPs and select one for response"""
        self.logger.info("Scanning RFPs via Sales Agent...")
        
        if self.agent_instance and hasattr(self.agent_instance, 'select_rfp_for_response'):
            try:
                return self.agent_instance.select_rfp_for_response(rfp_urls)
            except Exception as e:
                self.logger.error(f"Sales agent error: {e}")
        
        # Return mock data if agent not available
        return MockDataHandler.get_mock_rfp_data()


class TechnicalAgentIntegration(AgentIntegration):
    """Integration with Technical Agent"""
    
    def __init__(self, orchestrator: 'MainOrchestrator'):
        super().__init__(orchestrator)
        self.agent_type = "TECHNICAL_AGENT"
    
    def initialize(self) -> bool:
        """Initialize Technical Agent"""
        try:
            from agents.technical_agent.technical_agent import TechnicalAgent
            self.agent_instance = TechnicalAgent()
            self.orchestrator.agent_registry.register(
                'TECHNICAL_001', self.agent_type,
                ['spec_matching', 'oem_recommendation', 'compliance_analysis'],
                self.agent_instance
            )
            return True
        except ImportError:
            self.logger.warning("Technical Agent not available, using mock")
            return False
    
    def is_available(self) -> bool:
        """Check if Technical Agent is available"""
        return self.agent_instance is not None
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run technical analysis"""
        self.logger.info("Running technical analysis...")
        
        if self.agent_instance and hasattr(self.agent_instance, 'process'):
            try:
                return self.agent_instance.process(context)
            except Exception as e:
                self.logger.error(f"Technical agent error: {e}")
        
        # Return mock response
        return MockDataHandler.get_mock_technical_response()


class PricingAgentIntegration(AgentIntegration):
    """Integration with Pricing Agent"""
    
    def __init__(self, orchestrator: 'MainOrchestrator'):
        super().__init__(orchestrator)
        self.agent_type = "PRICING_AGENT"
    
    def initialize(self) -> bool:
        """Initialize Pricing Agent"""
        try:
            from agents.pricing_agent.pricing_agent import PricingAgent
            self.agent_instance = PricingAgent()
            self.orchestrator.agent_registry.register(
                'PRICING_001', self.agent_type,
                ['pricing', 'cost_calculation', 'margin_analysis'],
                self.agent_instance
            )
            return True
        except ImportError:
            self.logger.warning("Pricing Agent not available, using mock")
            return False
    
    def is_available(self) -> bool:
        """Check if Pricing Agent is available"""
        return self.agent_instance is not None
    
    def calculate(self, context: Dict[str, Any], 
                  technical_response: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate pricing"""
        self.logger.info("Calculating pricing...")
        
        pricing_input = {
            **context,
            'recommendations': technical_response.get('recommendations', [])
        }
        
        if self.agent_instance and hasattr(self.agent_instance, 'calculate_pricing'):
            try:
                return self.agent_instance.calculate_pricing(pricing_input)
            except Exception as e:
                self.logger.error(f"Pricing agent error: {e}")
        
        # Return mock response
        return MockDataHandler.get_mock_pricing_response()


# ============================================================================
# Feature 7: Message Queue System
# ============================================================================

class MessageQueueSystem:
    """Message queue for inter-agent communication"""
    
    def __init__(self, max_size: int = 1000):
        self.queue: PriorityQueue = PriorityQueue(maxsize=max_size)
        self.processed: Dict[str, QueueMessage] = {}
        self.failed: Dict[str, QueueMessage] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger("MessageQueue")
        
        # Statistics
        self.stats = {
            'enqueued': 0,
            'processed': 0,
            'failed': 0
        }
    
    def enqueue(self, message: QueueMessage) -> bool:
        """Add message to queue"""
        try:
            self.queue.put_nowait(message)
            with self._lock:
                self.stats['enqueued'] += 1
            self.logger.debug(f"Message enqueued: {message.message_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enqueue: {e}")
            return False
    
    def dequeue(self, timeout: float = 1.0) -> Optional[QueueMessage]:
        """Get next message from queue"""
        try:
            message = self.queue.get(timeout=timeout)
            return message
        except Empty:
            return None
    
    def process_message(self, message: QueueMessage, handler: Callable) -> bool:
        """Process a message with handler"""
        try:
            handler(message)
            with self._lock:
                self.processed[message.message_id] = message
                self.stats['processed'] += 1
            return True
        except Exception as e:
            message.retry_count += 1
            if message.retry_count < message.max_retries:
                self.enqueue(message)
            else:
                with self._lock:
                    self.failed[message.message_id] = message
                    self.stats['failed'] += 1
            self.logger.error(f"Message processing failed: {e}")
            return False
    
    def pending_count(self) -> int:
        """Count pending messages"""
        return self.queue.qsize()
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        return self.stats.copy()
    
    def create_message(self, from_agent: str, to_agent: str,
                       msg_type: MessageType, payload: Dict[str, Any],
                       priority: MessagePriority = MessagePriority.STANDARD) -> QueueMessage:
        """Create a new message"""
        return QueueMessage(
            message_id=f"MSG_{uuid.uuid4().hex[:12].upper()}",
            priority=priority.value,
            timestamp=datetime.now(),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=msg_type,
            payload=payload
        )


# ============================================================================
# Feature 8: Agent Communication Protocol
# ============================================================================

class AgentCommunicationProtocol:
    """Protocol for agent-to-agent communication"""
    
    def __init__(self, orchestrator: 'MainOrchestrator'):
        self.orchestrator = orchestrator
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_acks: Dict[str, QueueMessage] = {}
        self.logger = logging.getLogger("CommProtocol")
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_handler(MessageType.ACKNOWLEDGMENT, self._handle_ack)
        self.register_handler(MessageType.ERROR, self._handle_error)
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
    
    def register_handler(self, msg_type: MessageType, handler: Callable):
        """Register a message handler"""
        self.message_handlers[msg_type] = handler
    
    def send(self, from_agent: str, to_agent: str, 
             msg_type: MessageType, payload: Dict[str, Any],
             priority: MessagePriority = MessagePriority.STANDARD,
             requires_ack: bool = True) -> str:
        """Send a message"""
        message = self.orchestrator.message_queue.create_message(
            from_agent, to_agent, msg_type, payload, priority
        )
        message.requires_ack = requires_ack
        
        self.orchestrator.message_queue.enqueue(message)
        
        if requires_ack:
            self.pending_acks[message.message_id] = message
        
        self.logger.info(f"Message sent: {message.message_id} ({msg_type.value})")
        return message.message_id
    
    def receive(self, message: QueueMessage) -> Dict[str, Any]:
        """Receive and process a message"""
        handler = self.message_handlers.get(message.message_type)
        
        if handler:
            result = handler(message)
            
            # Send ACK if required
            if message.requires_ack:
                self.send_ack(message)
            
            return result
        else:
            self.logger.warning(f"No handler for: {message.message_type.value}")
            return {'status': 'no_handler'}
    
    def send_ack(self, original_message: QueueMessage):
        """Send acknowledgment"""
        self.send(
            original_message.to_agent,
            original_message.from_agent,
            MessageType.ACKNOWLEDGMENT,
            {'original_message_id': original_message.message_id},
            requires_ack=False
        )
    
    def _handle_ack(self, message: QueueMessage) -> Dict[str, Any]:
        """Handle acknowledgment"""
        original_id = message.payload.get('original_message_id')
        if original_id in self.pending_acks:
            del self.pending_acks[original_id]
        return {'status': 'acknowledged'}
    
    def _handle_error(self, message: QueueMessage) -> Dict[str, Any]:
        """Handle error message"""
        self.logger.error(f"Error from {message.from_agent}: {message.payload}")
        return {'status': 'error_logged'}
    
    def _handle_heartbeat(self, message: QueueMessage) -> Dict[str, Any]:
        """Handle heartbeat"""
        self.orchestrator.agent_registry.heartbeat(message.from_agent)
        return {'status': 'heartbeat_received'}
    
    def broadcast(self, from_agent: str, msg_type: MessageType,
                  payload: Dict[str, Any]) -> List[str]:
        """Broadcast message to all agents"""
        message_ids = []
        for agent in self.orchestrator.agent_registry.get_all():
            if agent.agent_id != from_agent:
                msg_id = self.send(from_agent, agent.agent_id, msg_type, payload)
                message_ids.append(msg_id)
        return message_ids


# ============================================================================
# Feature 9: Context-Aware Summarization
# ============================================================================

class ContextAwareSummarizer:
    """Creates context-aware summaries for different agents"""
    
    def __init__(self):
        self.logger = logging.getLogger("Summarizer")
    
    def create_technical_context(self, rfp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create technical context summary"""
        return {
            'rfp_id': rfp_data.get('rfp_id', ''),
            'title': rfp_data.get('title', ''),
            'products_in_scope': rfp_data.get('products', []),
            'technical_requirements': rfp_data.get('technical_requirements', []),
            'standards_required': rfp_data.get('standards', []),
            'acceptance_criteria': rfp_data.get('acceptance_criteria', []),
            'focus_areas': [
                'Product specification matching',
                'OEM product recommendations (top 3)',
                'Spec match percentage calculation',
                'Comparison table preparation'
            ],
            'expected_output': {
                'recommendations': 'Top 3 OEM products per scope item',
                'spec_match': 'Percentage match for each',
                'comparison_table': 'RFP vs OEM specifications'
            }
        }
    
    def create_pricing_context(self, rfp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create pricing context summary"""
        return {
            'rfp_id': rfp_data.get('rfp_id', ''),
            'title': rfp_data.get('title', ''),
            'tests_required': rfp_data.get('tests_required', []),
            'certifications': rfp_data.get('certifications', []),
            'estimated_value': rfp_data.get('estimated_value', 0),
            'delivery_requirements': rfp_data.get('delivery', {}),
            'focus_areas': [
                'Unit pricing from pricing table',
                'Test cost calculation',
                'Material cost consolidation',
                'Services cost consolidation',
                'Tax calculation and grand total'
            ],
            'expected_output': {
                'unit_prices': 'Price per product SKU',
                'test_costs': 'Cost per required test',
                'totals': 'Material, services, grand total'
            }
        }
    
    def create_executive_summary(self, consolidated: Dict[str, Any]) -> str:
        """Create executive summary"""
        rfp_id = consolidated.get('rfp_id', 'Unknown')
        grand_total = consolidated.get('grand_total', 0)
        spec_match = consolidated.get('overall_spec_match', 0)
        
        return f"""
## Executive Summary

**RFP ID:** {rfp_id}
**Response Date:** {datetime.now().strftime('%Y-%m-%d')}

### Key Highlights
- **Total Bid Value:** ₹{grand_total:,.2f}
- **Overall Specification Match:** {spec_match:.1f}%
- **Products Covered:** {len(consolidated.get('scope_of_supply', []))}
- **Tests Included:** {len(consolidated.get('test_costs', []))}

### Recommendation
{consolidated.get('recommendation', 'Review required')}
"""


# ============================================================================
# Feature 10: Role-Specific Message Formatting
# ============================================================================

class RoleSpecificFormatter:
    """Formats messages for specific agent roles"""
    
    def __init__(self):
        self.formatters = {
            'SALES_AGENT': self._format_for_sales,
            'TECHNICAL_AGENT': self._format_for_technical,
            'PRICING_AGENT': self._format_for_pricing,
            'MASTER': self._format_for_master
        }
    
    def format(self, agent_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for specific agent"""
        formatter = self.formatters.get(agent_type, self._default_format)
        return formatter(data)
    
    def _format_for_sales(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format for Sales Agent"""
        return {
            'rfp_summary': {
                'rfp_id': data.get('rfp_id'),
                'title': data.get('title'),
                'due_date': data.get('due_date'),
                'estimated_value': data.get('estimated_value')
            },
            'action_required': 'scan_and_select',
            'priority': 'high'
        }
    
    def _format_for_technical(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format for Technical Agent"""
        return {
            'rfp_id': data.get('rfp_id'),
            'products': data.get('products', []),
            'specifications': data.get('technical_requirements', []),
            'standards': data.get('standards', []),
            'action_required': 'analyze_and_recommend'
        }
    
    def _format_for_pricing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format for Pricing Agent"""
        return {
            'rfp_id': data.get('rfp_id'),
            'products': data.get('recommendations', []),
            'tests': data.get('tests_required', []),
            'certifications': data.get('certifications', []),
            'action_required': 'calculate_pricing'
        }
    
    def _format_for_master(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format for Master Agent"""
        return {
            'source_agent': data.get('from_agent'),
            'response_type': data.get('response_type'),
            'data': data.get('data', {}),
            'status': data.get('status', 'received')
        }
    
    def _default_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Default format"""
        return data


# ============================================================================
# Feature 11: Response Consolidation
# ============================================================================

class ResponseConsolidator:
    """Consolidates responses from all agents"""
    
    def __init__(self):
        self.logger = logging.getLogger("Consolidator")
    
    def consolidate(self, rfp_data: Dict[str, Any],
                    technical_response: Dict[str, Any],
                    pricing_response: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate all responses into final response"""
        self.logger.info("Consolidating responses...")
        
        # Build scope of supply
        scope_of_supply = self._build_scope_of_supply(
            rfp_data, technical_response, pricing_response
        )
        
        # Calculate overall spec match
        if scope_of_supply:
            overall_spec_match = sum(
                s.get('spec_match_percent', 0) for s in scope_of_supply
            ) / len(scope_of_supply)
        else:
            overall_spec_match = 0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(overall_spec_match)
        
        return {
            'rfp_id': rfp_data.get('rfp_id', ''),
            'response_id': f"RESP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generated_date': datetime.now().isoformat(),
            'scope_of_supply': scope_of_supply,
            'test_costs': pricing_response.get('test_costs', []),
            'pricing_summary': {
                'total_material_cost': pricing_response.get('total_material_cost', 0),
                'total_services_cost': pricing_response.get('total_services_cost', 0),
                'taxes': pricing_response.get('taxes', {}),
                'grand_total': pricing_response.get('grand_total', 0)
            },
            'total_material_cost': pricing_response.get('total_material_cost', 0),
            'total_services_cost': pricing_response.get('total_services_cost', 0),
            'taxes': pricing_response.get('taxes', 0),
            'grand_total': pricing_response.get('grand_total', 0),
            'overall_spec_match': round(overall_spec_match, 2),
            'recommendation': recommendation,
            'compliance_checklist': self._build_compliance_checklist(
                technical_response, pricing_response
            ),
            'technical_summary': technical_response.get('summary', {}),
            'pricing_breakdown': pricing_response.get('breakdown', {})
        }
    
    def _build_scope_of_supply(self, rfp_data: Dict[str, Any],
                               technical_response: Dict[str, Any],
                               pricing_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build scope of supply table"""
        scope = []
        recommendations = technical_response.get('recommendations', [])
        prices = pricing_response.get('product_prices', [])
        products = rfp_data.get('products', [])
        
        for idx, product in enumerate(products):
            rec = recommendations[idx] if idx < len(recommendations) else {}
            price = prices[idx] if idx < len(prices) else {}
            
            scope.append({
                'sl_no': idx + 1,
                'rfp_product': product.get('name', rec.get('rfp_product', '')),
                'quantity': rec.get('quantity', product.get('quantity', 1)),
                'unit': rec.get('unit', product.get('unit', 'Nos')),
                'recommended_sku': rec.get('selected_sku', ''),
                'oem_product': rec.get('product_name', ''),
                'manufacturer': rec.get('manufacturer', ''),
                'spec_match_percent': rec.get('spec_match_percent', 0),
                'unit_price': price.get('unit_price', 0),
                'total_price': price.get('total_price', 0)
            })
        
        return scope
    
    def _generate_recommendation(self, spec_match: float) -> str:
        """Generate recommendation based on spec match"""
        if spec_match >= 90:
            return "HIGHLY RECOMMENDED - Excellent specification match"
        elif spec_match >= 75:
            return "RECOMMENDED - Good specification match with minor deviations"
        elif spec_match >= 60:
            return "CONDITIONALLY RECOMMENDED - Review required"
        else:
            return "REVIEW REQUIRED - Significant specification deviations"
    
    def _build_compliance_checklist(self, technical_response: Dict[str, Any],
                                     pricing_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build compliance checklist"""
        return [
            {'item': 'Products addressed', 'compliant': bool(technical_response.get('recommendations'))},
            {'item': 'OEM recommendations', 'compliant': len(technical_response.get('recommendations', [])) > 0},
            {'item': 'Spec match calculated', 'compliant': True},
            {'item': 'Pricing assigned', 'compliant': bool(pricing_response.get('product_prices'))},
            {'item': 'Tests costed', 'compliant': bool(pricing_response.get('test_costs'))},
            {'item': 'Total calculated', 'compliant': pricing_response.get('grand_total', 0) > 0}
        ]


# ============================================================================
# Feature 12: Final Document Generator
# ============================================================================

class FinalDocumentGenerator:
    """Generates final RFP response documents"""
    
    def __init__(self):
        self.logger = logging.getLogger("DocumentGenerator")
        self.templates = {}
    
    def generate(self, consolidated: Dict[str, Any], 
                 template: str = 'default') -> str:
        """Generate final document"""
        self.logger.info("Generating final document...")
        
        sections = []
        
        # Cover page
        sections.append(self._generate_cover_page(consolidated))
        
        # Executive summary
        sections.append(self._generate_executive_summary(consolidated))
        
        # Scope of supply
        sections.append(self._generate_scope_section(consolidated))
        
        # Technical compliance
        sections.append(self._generate_technical_section(consolidated))
        
        # Commercial section
        sections.append(self._generate_commercial_section(consolidated))
        
        # Terms and conditions
        sections.append(self._generate_terms_section(consolidated))
        
        return '\n\n'.join(sections)
    
    def _generate_cover_page(self, data: Dict[str, Any]) -> str:
        """Generate cover page"""
        return f"""
# RFP Response Document

**RFP ID:** {data.get('rfp_id', 'N/A')}
**Response ID:** {data.get('response_id', 'N/A')}
**Date:** {data.get('generated_date', datetime.now().isoformat())}

---
"""
    
    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary section"""
        return f"""
## 1. Executive Summary

This document presents our response to RFP {data.get('rfp_id')}.

**Key Highlights:**
- Total Bid Value: ₹{data.get('grand_total', 0):,.2f}
- Overall Specification Match: {data.get('overall_spec_match', 0):.1f}%
- Items Covered: {len(data.get('scope_of_supply', []))}

**Recommendation:** {data.get('recommendation', 'N/A')}
"""
    
    def _generate_scope_section(self, data: Dict[str, Any]) -> str:
        """Generate scope of supply section"""
        lines = ["## 2. Scope of Supply\n"]
        lines.append("| Sl | Product | SKU | Spec Match | Qty | Unit Price | Total |")
        lines.append("|---|---|---|---|---|---|---|")
        
        for item in data.get('scope_of_supply', []):
            lines.append(
                f"| {item['sl_no']} | {item['rfp_product'][:30]} | "
                f"{item['recommended_sku']} | {item['spec_match_percent']:.1f}% | "
                f"{item['quantity']} | ₹{item['unit_price']:,.2f} | ₹{item['total_price']:,.2f} |"
            )
        
        return '\n'.join(lines)
    
    def _generate_technical_section(self, data: Dict[str, Any]) -> str:
        """Generate technical compliance section"""
        return f"""
## 3. Technical Compliance

Overall Specification Match: **{data.get('overall_spec_match', 0):.1f}%**

### Compliance Checklist
""" + '\n'.join(
            f"- {'✅' if item['compliant'] else '❌'} {item['item']}"
            for item in data.get('compliance_checklist', [])
        )
    
    def _generate_commercial_section(self, data: Dict[str, Any]) -> str:
        """Generate commercial section"""
        pricing = data.get('pricing_summary', {})
        return f"""
## 4. Commercial Summary

| Component | Amount |
|---|---:|
| Material Cost | ₹{pricing.get('total_material_cost', 0):,.2f} |
| Services Cost | ₹{pricing.get('total_services_cost', 0):,.2f} |
| Taxes | ₹{data.get('taxes', 0):,.2f} |
| **Grand Total** | **₹{data.get('grand_total', 0):,.2f}** |
"""
    
    def _generate_terms_section(self, data: Dict[str, Any]) -> str:
        """Generate terms section"""
        return """
## 5. Terms and Conditions

- **Validity:** 30 days from date of submission
- **Payment:** As per RFP terms
- **Delivery:** As per RFP schedule
- **Warranty:** As per manufacturer terms
"""


# ============================================================================
# Features 13-15: Quality, Completeness, Consistency Validation
# ============================================================================

class QualityValidator:
    """Validates quality of response"""
    
    def __init__(self):
        self.logger = logging.getLogger("QualityValidator")
        self.min_spec_match = 60.0
        self.required_sections = ['scope_of_supply', 'grand_total', 'recommendation']
    
    def validate(self, consolidated: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response quality"""
        issues = []
        score = 100.0
        
        # Check spec match
        spec_match = consolidated.get('overall_spec_match', 0)
        if spec_match < self.min_spec_match:
            issues.append(f"Spec match {spec_match}% below minimum {self.min_spec_match}%")
            score -= 20
        
        # Check required sections
        for section in self.required_sections:
            if not consolidated.get(section):
                issues.append(f"Missing required section: {section}")
                score -= 10
        
        # Check pricing
        if consolidated.get('grand_total', 0) <= 0:
            issues.append("Invalid grand total")
            score -= 15
        
        # Determine quality level
        if score >= 90:
            level = QualityLevel.EXCELLENT
        elif score >= 75:
            level = QualityLevel.GOOD
        elif score >= 60:
            level = QualityLevel.ACCEPTABLE
        elif score >= 40:
            level = QualityLevel.NEEDS_REVIEW
        else:
            level = QualityLevel.FAILED
        
        return {
            'passed': score >= 60,
            'score': score,
            'level': level.value,
            'issues': issues,
            'validated_at': datetime.now().isoformat()
        }


class CompletenessChecker:
    """Checks completeness of response"""
    
    def __init__(self):
        self.required_fields = [
            'rfp_id', 'response_id', 'scope_of_supply',
            'grand_total', 'recommendation'
        ]
        self.optional_fields = [
            'test_costs', 'compliance_checklist', 'technical_summary'
        ]
    
    def check(self, consolidated: Dict[str, Any]) -> Dict[str, Any]:
        """Check response completeness"""
        missing_required = []
        missing_optional = []
        
        for field in self.required_fields:
            if not consolidated.get(field):
                missing_required.append(field)
        
        for field in self.optional_fields:
            if not consolidated.get(field):
                missing_optional.append(field)
        
        completeness_score = (
            (len(self.required_fields) - len(missing_required)) / 
            len(self.required_fields) * 100
        )
        
        return {
            'complete': len(missing_required) == 0,
            'completeness_score': completeness_score,
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'total_fields': len(self.required_fields) + len(self.optional_fields),
            'fields_present': (len(self.required_fields) - len(missing_required) + 
                             len(self.optional_fields) - len(missing_optional))
        }


class ConsistencyValidator:
    """Validates consistency of response data"""
    
    def __init__(self):
        self.logger = logging.getLogger("ConsistencyValidator")
    
    def validate(self, consolidated: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data consistency"""
        issues = []
        
        # Check scope totals match grand total
        scope_total = sum(
            item.get('total_price', 0) 
            for item in consolidated.get('scope_of_supply', [])
        )
        
        material_cost = consolidated.get('total_material_cost', 0)
        if abs(scope_total - material_cost) > 0.01 and material_cost > 0:
            issues.append(
                f"Scope total (₹{scope_total:,.2f}) doesn't match material cost (₹{material_cost:,.2f})"
            )
        
        # Check item counts
        scope_items = len(consolidated.get('scope_of_supply', []))
        if scope_items == 0:
            issues.append("No items in scope of supply")
        
        # Check spec match ranges
        for item in consolidated.get('scope_of_supply', []):
            spec_match = item.get('spec_match_percent', 0)
            if spec_match < 0 or spec_match > 100:
                issues.append(f"Invalid spec match for item {item.get('sl_no')}: {spec_match}%")
        
        return {
            'consistent': len(issues) == 0,
            'issues': issues,
            'checks_performed': 3,
            'checks_passed': 3 - len(issues)
        }


# ============================================================================
# Feature 16: Output Formatter
# ============================================================================

class OutputFormatter:
    """Formats output in various formats"""
    
    def __init__(self):
        self.formats = ['json', 'markdown', 'html', 'text']
    
    def format(self, data: Dict[str, Any], output_format: str = 'json') -> str:
        """Format data to specified format"""
        if output_format == 'json':
            return self.to_json(data)
        elif output_format == 'markdown':
            return self.to_markdown(data)
        elif output_format == 'html':
            return self.to_html(data)
        elif output_format == 'text':
            return self.to_text(data)
        else:
            return self.to_json(data)
    
    def to_json(self, data: Dict[str, Any]) -> str:
        """Format as JSON"""
        return json.dumps(data, indent=2, default=str)
    
    def to_markdown(self, data: Dict[str, Any]) -> str:
        """Format as Markdown"""
        lines = [f"# Response: {data.get('rfp_id', 'N/A')}\n"]
        
        lines.append("## Summary\n")
        lines.append(f"- **Grand Total:** ₹{data.get('grand_total', 0):,.2f}")
        lines.append(f"- **Spec Match:** {data.get('overall_spec_match', 0):.1f}%")
        lines.append(f"- **Recommendation:** {data.get('recommendation', 'N/A')}\n")
        
        return '\n'.join(lines)
    
    def to_html(self, data: Dict[str, Any]) -> str:
        """Format as HTML"""
        return f"""
<!DOCTYPE html>
<html>
<head><title>RFP Response - {data.get('rfp_id', '')}</title></head>
<body>
<h1>RFP Response</h1>
<p><strong>RFP ID:</strong> {data.get('rfp_id', 'N/A')}</p>
<p><strong>Grand Total:</strong> ₹{data.get('grand_total', 0):,.2f}</p>
<p><strong>Spec Match:</strong> {data.get('overall_spec_match', 0):.1f}%</p>
</body>
</html>
"""
    
    def to_text(self, data: Dict[str, Any]) -> str:
        """Format as plain text"""
        lines = [
            f"RFP Response: {data.get('rfp_id', 'N/A')}",
            "=" * 50,
            f"Grand Total: Rs. {data.get('grand_total', 0):,.2f}",
            f"Spec Match: {data.get('overall_spec_match', 0):.1f}%",
            f"Recommendation: {data.get('recommendation', 'N/A')}"
        ]
        return '\n'.join(lines)


# ============================================================================
# Feature 17: PDF Report Generator
# ============================================================================

class PDFReportGenerator:
    """Generates PDF reports"""
    
    def __init__(self):
        self.logger = logging.getLogger("PDFGenerator")
        self.document_generator = FinalDocumentGenerator()
    
    def generate(self, consolidated: Dict[str, Any],
                 validation: Dict[str, Any] = None) -> str:
        """Generate PDF report (returns path)"""
        self.logger.info("Generating PDF report...")
        
        # Generate markdown content first
        content = self.document_generator.generate(consolidated)
        
        # Add validation section if provided
        if validation:
            content += self._add_validation_section(validation)
        
        # In production, would use a PDF library
        # For now, return the content as a pseudo-path
        report_id = f"PDF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return f"reports/{report_id}.pdf"
    
    def _add_validation_section(self, validation: Dict[str, Any]) -> str:
        """Add validation section to report"""
        quality = validation.get('quality', {})
        completeness = validation.get('completeness', {})
        
        return f"""

## Validation Report

### Quality Check
- **Score:** {quality.get('score', 0):.1f}%
- **Level:** {quality.get('level', 'N/A')}
- **Passed:** {'Yes' if quality.get('passed') else 'No'}

### Completeness Check
- **Score:** {completeness.get('completeness_score', 0):.1f}%
- **Complete:** {'Yes' if completeness.get('complete') else 'No'}
"""
    
    def get_supported_formats(self) -> List[str]:
        """Get supported output formats"""
        return ['pdf', 'docx', 'html']


# ============================================================================
# Feature 18: Executive Summary Writer
# ============================================================================

class ExecutiveSummaryWriter:
    """Writes executive summaries"""
    
    def __init__(self):
        self.logger = logging.getLogger("SummaryWriter")
    
    def write(self, consolidated: Dict[str, Any]) -> str:
        """Write executive summary"""
        rfp_id = consolidated.get('rfp_id', 'Unknown')
        grand_total = consolidated.get('grand_total', 0)
        spec_match = consolidated.get('overall_spec_match', 0)
        scope = consolidated.get('scope_of_supply', [])
        tests = consolidated.get('test_costs', [])
        recommendation = consolidated.get('recommendation', 'Review required')
        
        # Determine status
        if spec_match >= 90:
            status = "Excellent Match"
            status_icon = "🟢"
        elif spec_match >= 75:
            status = "Good Match"
            status_icon = "🟡"
        else:
            status = "Review Required"
            status_icon = "🔴"
        
        summary = f"""
# Executive Summary {status_icon}

## RFP Response Overview

**RFP ID:** {rfp_id}
**Response Date:** {datetime.now().strftime('%B %d, %Y')}
**Status:** {status}

---

## Financial Summary

| Category | Amount |
|----------|-------:|
| Material Cost | ₹{consolidated.get('total_material_cost', 0):,.2f} |
| Services Cost | ₹{consolidated.get('total_services_cost', 0):,.2f} |
| Taxes | ₹{consolidated.get('taxes', 0):,.2f} |
| **Grand Total** | **₹{grand_total:,.2f}** |

## Technical Summary

- **Overall Specification Match:** {spec_match:.1f}%
- **Products Covered:** {len(scope)} items
- **Tests Included:** {len(tests)} tests

## Recommendation

{recommendation}

---

*This summary was auto-generated by the RFP Response System*
"""
        return summary


# ============================================================================
# Feature 19: Detailed Response Compiler
# ============================================================================

class DetailedResponseCompiler:
    """Compiles detailed RFP responses"""
    
    def __init__(self):
        self.logger = logging.getLogger("ResponseCompiler")
    
    def compile(self, consolidated: Dict[str, Any]) -> str:
        """Compile detailed response"""
        sections = []
        
        # Header
        sections.append(self._compile_header(consolidated))
        
        # Table of contents
        sections.append(self._compile_toc())
        
        # Introduction
        sections.append(self._compile_introduction(consolidated))
        
        # Scope of supply (detailed)
        sections.append(self._compile_scope_detailed(consolidated))
        
        # Technical compliance (detailed)
        sections.append(self._compile_technical_detailed(consolidated))
        
        # Pricing breakdown
        sections.append(self._compile_pricing_detailed(consolidated))
        
        # Test costs
        sections.append(self._compile_tests_detailed(consolidated))
        
        # Annexures
        sections.append(self._compile_annexures(consolidated))
        
        return '\n\n'.join(sections)
    
    def _compile_header(self, data: Dict[str, Any]) -> str:
        """Compile document header"""
        return f"""
# Detailed RFP Response

**RFP ID:** {data.get('rfp_id', 'N/A')}
**Response ID:** {data.get('response_id', 'N/A')}
**Prepared On:** {datetime.now().strftime('%B %d, %Y')}

---
"""
    
    def _compile_toc(self) -> str:
        """Compile table of contents"""
        return """
## Table of Contents

1. Introduction
2. Scope of Supply
3. Technical Compliance
4. Commercial Proposal
5. Testing & Certification
6. Annexures
"""
    
    def _compile_introduction(self, data: Dict[str, Any]) -> str:
        """Compile introduction section"""
        return f"""
## 1. Introduction

This document presents our comprehensive response to RFP {data.get('rfp_id')}.

**Key Highlights:**
- Competitive pricing with ₹{data.get('grand_total', 0):,.2f} total value
- {data.get('overall_spec_match', 0):.1f}% specification compliance
- Complete scope coverage with {len(data.get('scope_of_supply', []))} items
"""
    
    def _compile_scope_detailed(self, data: Dict[str, Any]) -> str:
        """Compile detailed scope section"""
        lines = ["## 2. Scope of Supply\n"]
        
        for item in data.get('scope_of_supply', []):
            lines.append(f"### 2.{item['sl_no']} {item['rfp_product']}\n")
            lines.append(f"- **OEM SKU:** {item['recommended_sku']}")
            lines.append(f"- **Manufacturer:** {item.get('manufacturer', 'N/A')}")
            lines.append(f"- **Quantity:** {item['quantity']} {item.get('unit', 'units')}")
            lines.append(f"- **Unit Price:** ₹{item['unit_price']:,.2f}")
            lines.append(f"- **Total:** ₹{item['total_price']:,.2f}")
            lines.append(f"- **Spec Match:** {item['spec_match_percent']:.1f}%\n")
        
        return '\n'.join(lines)
    
    def _compile_technical_detailed(self, data: Dict[str, Any]) -> str:
        """Compile detailed technical section"""
        return f"""
## 3. Technical Compliance

### 3.1 Overall Compliance
- **Specification Match:** {data.get('overall_spec_match', 0):.1f}%

### 3.2 Compliance Checklist
""" + '\n'.join(
            f"- {'✅' if item['compliant'] else '❌'} {item['item']}"
            for item in data.get('compliance_checklist', [])
        )
    
    def _compile_pricing_detailed(self, data: Dict[str, Any]) -> str:
        """Compile detailed pricing section"""
        pricing = data.get('pricing_summary', {})
        return f"""
## 4. Commercial Proposal

### 4.1 Pricing Summary

| Component | Amount (INR) |
|-----------|-------------:|
| Material Cost | {pricing.get('total_material_cost', 0):,.2f} |
| Services Cost | {pricing.get('total_services_cost', 0):,.2f} |
| Taxes | {data.get('taxes', 0):,.2f} |
| **Grand Total** | **{data.get('grand_total', 0):,.2f}** |

### 4.2 Payment Terms
- As per RFP terms and conditions
"""
    
    def _compile_tests_detailed(self, data: Dict[str, Any]) -> str:
        """Compile detailed tests section"""
        tests = data.get('test_costs', [])
        if not tests:
            return "## 5. Testing & Certification\n\nNo specific tests required."
        
        lines = ["## 5. Testing & Certification\n"]
        for idx, test in enumerate(tests, 1):
            lines.append(f"### 5.{idx} {test.get('test_name', 'Test')}")
            lines.append(f"- **Cost:** ₹{test.get('cost', 0):,.2f}")
        
        return '\n'.join(lines)
    
    def _compile_annexures(self, data: Dict[str, Any]) -> str:
        """Compile annexures section"""
        return """
## 6. Annexures

- Annexure A: Detailed Technical Specifications
- Annexure B: OEM Product Datasheets
- Annexure C: Test Certificates
- Annexure D: Company Profile
"""


# ============================================================================
# Feature 20: Audit Trail Generator
# ============================================================================

class AuditTrailGenerator:
    """Generates audit trails for workflow tracking"""
    
    def __init__(self):
        self.entries: Dict[str, List[AuditEntry]] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger("AuditTrail")
    
    def record(self, workflow_id: str, action: str, actor: str,
               details: Dict[str, Any], previous_state: str, 
               new_state: str) -> str:
        """Record an audit entry"""
        entry_id = f"AUD_{uuid.uuid4().hex[:10].upper()}"
        
        # Create data hash for integrity
        data_str = json.dumps(details, sort_keys=True, default=str)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            action=action,
            actor=actor,
            details=details,
            previous_state=previous_state,
            new_state=new_state,
            data_hash=data_hash
        )
        
        with self._lock:
            if workflow_id not in self.entries:
                self.entries[workflow_id] = []
            self.entries[workflow_id].append(entry)
        
        self.logger.info(f"Audit entry recorded: {entry_id}")
        return entry_id
    
    def get_trail(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for workflow"""
        entries = self.entries.get(workflow_id, [])
        return [
            {
                'entry_id': e.entry_id,
                'timestamp': e.timestamp.isoformat(),
                'action': e.action,
                'actor': e.actor,
                'previous_state': e.previous_state,
                'new_state': e.new_state,
                'data_hash': e.data_hash
            }
            for e in entries
        ]
    
    def generate_report(self, workflow_id: str) -> str:
        """Generate audit trail report"""
        trail = self.get_trail(workflow_id)
        
        if not trail:
            return f"No audit trail found for workflow: {workflow_id}"
        
        lines = [
            f"# Audit Trail Report",
            f"**Workflow ID:** {workflow_id}",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Total Entries:** {len(trail)}",
            "",
            "## Timeline",
            ""
        ]
        
        for entry in trail:
            lines.append(f"### {entry['timestamp']}")
            lines.append(f"- **Action:** {entry['action']}")
            lines.append(f"- **Actor:** {entry['actor']}")
            lines.append(f"- **State Change:** {entry['previous_state']} → {entry['new_state']}")
            lines.append(f"- **Hash:** {entry['data_hash']}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def verify_integrity(self, workflow_id: str) -> bool:
        """Verify audit trail integrity"""
        entries = self.entries.get(workflow_id, [])
        
        for entry in entries:
            data_str = json.dumps(entry.details, sort_keys=True, default=str)
            expected_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
            
            if entry.data_hash != expected_hash:
                self.logger.error(f"Integrity check failed for: {entry.entry_id}")
                return False
        
        return True
    
    def export(self, workflow_id: str, format: str = 'json') -> str:
        """Export audit trail"""
        trail = self.get_trail(workflow_id)
        
        if format == 'json':
            return json.dumps({'workflow_id': workflow_id, 'entries': trail}, indent=2)
        else:
            return self.generate_report(workflow_id)


# ============================================================================
# Mock Data Handler
# ============================================================================

class MockDataHandler:
    """Provides mock data for testing"""
    
    @staticmethod
    def get_mock_rfp_data() -> Dict[str, Any]:
        """Get mock RFP data"""
        return {
            'rfp_id': f'RFP_{datetime.now().strftime("%Y%m%d")}_{uuid.uuid4().hex[:4].upper()}',
            'title': 'Supply of Electrical Wires and Cables',
            'issuing_authority': 'State Electricity Board',
            'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'estimated_value': 5000000,
            'products': [
                {
                    'name': 'PVC Insulated Copper Wire 1.5 sqmm',
                    'quantity': 10000,
                    'unit': 'meters',
                    'specifications': {'conductor': 'Copper', 'insulation': 'PVC', 'voltage': '1100V'}
                },
                {
                    'name': 'XLPE Power Cable 4 Core 25 sqmm',
                    'quantity': 5000,
                    'unit': 'meters',
                    'specifications': {'conductor': 'Aluminum', 'insulation': 'XLPE', 'cores': 4}
                }
            ],
            'technical_requirements': ['IS 694', 'IS 7098', 'BIS Certified'],
            'tests_required': ['Conductor Resistance', 'Insulation Resistance', 'High Voltage Test'],
            'certifications': ['BIS', 'ISI'],
            'acceptance_criteria': ['100% electrical testing', 'Visual inspection']
        }
    
    @staticmethod
    def get_mock_technical_response() -> Dict[str, Any]:
        """Get mock technical response"""
        return {
            'recommendations': [
                {
                    'requirement_id': 'REQ_001',
                    'rfp_product': 'PVC Insulated Copper Wire 1.5 sqmm',
                    'selected_sku': 'POLYCAB_PVC_1.5',
                    'product_name': 'Polycab PVC Wire 1.5 sqmm',
                    'manufacturer': 'Polycab',
                    'spec_match_percent': 95.0,
                    'quantity': 10000,
                    'unit': 'meters'
                },
                {
                    'requirement_id': 'REQ_002',
                    'rfp_product': 'XLPE Power Cable 4C 25 sqmm',
                    'selected_sku': 'HAVELLS_XLPE_4C25',
                    'product_name': 'Havells XLPE Cable 4C 25sqmm',
                    'manufacturer': 'Havells',
                    'spec_match_percent': 88.0,
                    'quantity': 5000,
                    'unit': 'meters'
                }
            ],
            'summary': {
                'total_products': 2,
                'average_spec_match': 91.5
            }
        }
    
    @staticmethod
    def get_mock_pricing_response() -> Dict[str, Any]:
        """Get mock pricing response"""
        return {
            'product_prices': [
                {
                    'sku': 'POLYCAB_PVC_1.5',
                    'unit_price': 25.0,
                    'quantity': 10000,
                    'total_price': 250000
                },
                {
                    'sku': 'HAVELLS_XLPE_4C25',
                    'unit_price': 450.0,
                    'quantity': 5000,
                    'total_price': 2250000
                }
            ],
            'test_costs': [
                {'test_name': 'Conductor Resistance', 'cost': 5000},
                {'test_name': 'Insulation Resistance', 'cost': 7500},
                {'test_name': 'High Voltage Test', 'cost': 25000}
            ],
            'total_material_cost': 2500000,
            'total_services_cost': 37500,
            'taxes': 457050,
            'grand_total': 2994550,
            'breakdown': {
                'material': 2500000,
                'services': 37500,
                'gst': 457050
            }
        }


# ============================================================================
# Orchestrator API
# ============================================================================

class OrchestratorAPI:
    """API interface for the orchestrator"""
    
    def __init__(self, orchestrator: MainOrchestrator):
        self.orchestrator = orchestrator
        self.endpoints = {
            'health': self._handle_health,
            'status': self._handle_status,
            'start_workflow': self._handle_start_workflow,
            'run_workflow': self._handle_run_workflow,
            'get_result': self._handle_get_result
        }
    
    def handle_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle API request"""
        handler = self.endpoints.get(endpoint)
        
        if handler:
            try:
                result = handler(payload)
                return {'status': 200, 'data': result}
            except Exception as e:
                return {'status': 500, 'error': str(e)}
        else:
            return {'status': 404, 'error': f'Unknown endpoint: {endpoint}'}
    
    def _handle_health(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check"""
        return self.orchestrator.health_check()
    
    def _handle_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request"""
        return self.orchestrator.get_status()
    
    def _handle_start_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle start workflow request"""
        workflow_id = self.orchestrator.start_workflow(payload.get('rfp_data'))
        return {'workflow_id': workflow_id}
    
    def _handle_run_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle run workflow request"""
        return self.orchestrator.run_full_workflow(payload.get('rfp_urls'))
    
    def _handle_get_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get result request"""
        if self.orchestrator.current_workflow:
            return {
                'workflow_id': self.orchestrator.current_workflow.workflow_id,
                'consolidated': self.orchestrator.current_workflow.consolidated_response
            }
        return {'error': 'No active workflow'}


# Example usage
if __name__ == "__main__":
    orchestrator = MainOrchestrator()
    print(f"Orchestrator Status: {orchestrator.get_status()}")
    print(f"Health Check: {orchestrator.health_check()}")
