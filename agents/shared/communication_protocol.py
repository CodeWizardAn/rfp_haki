"""
Agent Communication Protocol
Defines message formats and communication between agents

Message Structure (per specification):
- Sender ID: Agent sending the message
- Receiver ID: Target agent(s)
- Message Type: Type of communication
- Timestamp: When message was created
- Payload: Content/data of the message
- Priority: Urgency level (1-5, 1=Critical)
- Context: Additional context for processing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json
import uuid


class MessagePriority(Enum):
    """Message priority levels (per specification)"""
    CRITICAL = 1      # Immediate processing required
    HIGH = 2          # Process before standard queue
    MEDIUM = 3        # Standard processing
    STANDARD = 4      # Normal queue priority
    LOW = 5           # Process when capacity available


class MessageType(Enum):
    """Types of messages between agents"""
    # Communication Flow 1: RFP Identification to Analysis
    RFP_IDENTIFIED = "rfp_identified"
    RFP_SELECTED = "rfp_selected"
    RFP_LIST = "rfp_list"
    
    # Communication Flow 2: Technical Analysis
    RFP_TECHNICAL_SUMMARY = "rfp_technical_summary"     # Master -> Technical
    PRODUCT_RECOMMENDATIONS = "product_recommendations"  # Technical -> Master & Pricing
    SPEC_COMPARISON = "spec_comparison"
    COMPLIANCE_REPORT = "compliance_report"
    
    # Communication Flow 3: Pricing Estimation
    RFP_PRICING_SUMMARY = "rfp_pricing_summary"   # Master -> Pricing
    PRICING_CALCULATION = "pricing_calculation"    # Pricing -> Master
    QUOTE_GENERATED = "quote_generated"
    
    # Communication Flow 4: Final Consolidation
    CONSOLIDATION_REQUEST = "consolidation_request"
    CONSOLIDATED_RESPONSE = "consolidated_response"
    
    # Workflow Control
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    
    # System Messages
    ERROR = "error"
    ACKNOWLEDGMENT = "acknowledgment"
    STATUS_UPDATE = "status_update"
    HANDSHAKE = "handshake"


class AgentType(Enum):
    """Types of agents in the system (per specification tier)"""
    # Tier 1: Orchestrator
    MASTER = "MASTER_ORCHESTRATOR"
    
    # Tier 2: Worker Agents
    SALES = "SALES_AGENT"
    TECHNICAL = "TECHNICAL_AGENT"
    PRICING = "PRICING_AGENT"
    
    # Broadcast target
    ALL = "ALL_AGENTS"


@dataclass
class MessageContext:
    """Context information for message processing (per specification)"""
    source_document: str = ""           # Source RFP document path/URL
    workflow_stage: str = ""            # Current stage in workflow
    dependencies: List[str] = field(default_factory=list)  # Required prior messages
    processing_hints: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_document': self.source_document,
            'workflow_stage': self.workflow_stage,
            'dependencies': self.dependencies,
            'processing_hints': self.processing_hints,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }


@dataclass
class AgentMessage:
    """
    Standard message format for inter-agent communication
    
    Structure (per specification):
    - Sender ID (from_agent): Agent sending the message
    - Receiver ID (to_agent): Target agent(s)
    - Message Type: Type of communication
    - Timestamp: When message was created
    - Payload: Content/data of the message
    - Priority: Urgency level
    - Context: Additional context for processing
    """
    # Required fields (per specification)
    message_id: str = field(default_factory=lambda: f"MSG_{uuid.uuid4().hex[:12].upper()}")
    timestamp: datetime = field(default_factory=datetime.now)
    from_agent: AgentType = AgentType.MASTER          # Sender ID
    to_agent: Union[AgentType, List[AgentType]] = AgentType.MASTER  # Receiver ID(s)
    message_type: MessageType = MessageType.STATUS_UPDATE
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.STANDARD
    context: MessageContext = field(default_factory=MessageContext)
    
    # Tracking fields
    conversation_id: str = ""
    rfp_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_response: bool = True
    response_to: str = ""  # message_id of original message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        to_agent_value = self.to_agent.value if isinstance(self.to_agent, AgentType) else [a.value for a in self.to_agent]
        return {
            'message_id': self.message_id,
            'timestamp': self.timestamp.isoformat(),
            'from_agent': self.from_agent.value,       # Sender ID
            'to_agent': to_agent_value,                # Receiver ID
            'message_type': self.message_type.value,
            'payload': self.payload,
            'priority': self.priority.value,
            'context': self.context.to_dict() if hasattr(self.context, 'to_dict') else self.context,
            'conversation_id': self.conversation_id,
            'rfp_id': self.rfp_id,
            'metadata': self.metadata,
            'requires_response': self.requires_response,
            'response_to': self.response_to
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        # Parse to_agent which can be single or list
        to_agent_data = data.get('to_agent', 'MASTER_ORCHESTRATOR')
        if isinstance(to_agent_data, list):
            to_agent = [AgentType(a) for a in to_agent_data]
        else:
            to_agent = AgentType(to_agent_data)
        
        # Parse priority
        priority_data = data.get('priority', 4)
        if isinstance(priority_data, int):
            priority = MessagePriority(priority_data)
        else:
            priority = MessagePriority[priority_data] if isinstance(priority_data, str) else MessagePriority.STANDARD
        
        # Parse context
        context_data = data.get('context', {})
        if isinstance(context_data, dict):
            context = MessageContext(**context_data)
        else:
            context = context_data
        
        return cls(
            message_id=data.get('message_id', f"MSG_{uuid.uuid4().hex[:12].upper()}"),
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else data.get('timestamp', datetime.now()),
            from_agent=AgentType(data.get('from_agent', 'MASTER_ORCHESTRATOR')),
            to_agent=to_agent,
            message_type=MessageType(data.get('message_type', 'status_update')),
            payload=data.get('payload', {}),
            priority=priority,
            context=context,
            conversation_id=data.get('conversation_id', ''),
            rfp_id=data.get('rfp_id', ''),
            metadata=data.get('metadata', {}),
            requires_response=data.get('requires_response', True),
            response_to=data.get('response_to', '')
        )


class MessageBroker:
    """
    Message broker for agent communication
    Handles routing, queuing, and delivery of messages between agents
    """
    
    def __init__(self):
        self.message_queue: Dict[AgentType, List[AgentMessage]] = {
            agent: [] for agent in AgentType if agent != AgentType.ALL
        }
        self.message_history: List[AgentMessage] = []
        self.subscribers: Dict[AgentType, List[callable]] = {
            agent: [] for agent in AgentType if agent != AgentType.ALL
        }
        self.pending_responses: Dict[str, AgentMessage] = {}  # Track messages awaiting response
    
    def send_message(self, message: AgentMessage) -> str:
        """
        Send a message to an agent
        Supports single agent or broadcast to multiple agents
        """
        # Handle multiple recipients
        recipients = message.to_agent if isinstance(message.to_agent, list) else [message.to_agent]
        
        for recipient in recipients:
            if recipient == AgentType.ALL:
                # Broadcast to all agents except sender
                for agent in AgentType:
                    if agent != AgentType.ALL and agent != message.from_agent:
                        self.message_queue[agent].append(message)
                        self._notify_subscribers(agent, message)
            else:
                self.message_queue[recipient].append(message)
                self._notify_subscribers(recipient, message)
        
        self.message_history.append(message)
        
        # Track if response is expected
        if message.requires_response:
            self.pending_responses[message.message_id] = message
        
        return message.message_id
    
    def _notify_subscribers(self, agent: AgentType, message: AgentMessage):
        """Notify subscribers of a message"""
        for callback in self.subscribers.get(agent, []):
            try:
                callback(message)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
    
    def get_messages(self, agent: AgentType, 
                     priority_filter: MessagePriority = None,
                     clear: bool = True) -> List[AgentMessage]:
        """
        Get all pending messages for an agent
        Optionally filter by priority
        """
        messages = self.message_queue.get(agent, []).copy()
        
        if priority_filter:
            messages = [m for m in messages if m.priority == priority_filter]
        
        # Sort by priority (lower number = higher priority)
        messages.sort(key=lambda x: x.priority.value)
        
        if clear:
            if priority_filter:
                # Only remove filtered messages
                self.message_queue[agent] = [
                    m for m in self.message_queue[agent] 
                    if m.priority != priority_filter
                ]
            else:
                self.message_queue[agent] = []
        
        return messages
    
    def get_high_priority_messages(self, agent: AgentType) -> List[AgentMessage]:
        """Get only critical and high priority messages"""
        return [
            m for m in self.message_queue.get(agent, [])
            if m.priority.value <= MessagePriority.HIGH.value
        ]
    
    def subscribe(self, agent: AgentType, callback: callable):
        """Subscribe to messages for an agent"""
        if agent not in self.subscribers:
            self.subscribers[agent] = []
        self.subscribers[agent].append(callback)
    
    def unsubscribe(self, agent: AgentType, callback: callable):
        """Unsubscribe from messages"""
        if agent in self.subscribers and callback in self.subscribers[agent]:
            self.subscribers[agent].remove(callback)
    
    def get_conversation_messages(self, conversation_id: str) -> List[AgentMessage]:
        """Get all messages in a conversation, sorted by timestamp"""
        messages = [m for m in self.message_history if m.conversation_id == conversation_id]
        messages.sort(key=lambda x: x.timestamp)
        return messages
    
    def create_response(self, original_message: AgentMessage, 
                        payload: Dict[str, Any],
                        message_type: MessageType = None,
                        priority: MessagePriority = None) -> AgentMessage:
        """Create a response message"""
        # Mark original message as responded
        if original_message.message_id in self.pending_responses:
            del self.pending_responses[original_message.message_id]
        
        return AgentMessage(
            from_agent=original_message.to_agent if isinstance(original_message.to_agent, AgentType) else original_message.to_agent[0],
            to_agent=original_message.from_agent,
            message_type=message_type or MessageType.ACKNOWLEDGMENT,
            conversation_id=original_message.conversation_id,
            rfp_id=original_message.rfp_id,
            payload=payload,
            priority=priority or original_message.priority,
            response_to=original_message.message_id,
            requires_response=False,
            context=original_message.context
        )
    
    def get_pending_responses(self) -> List[AgentMessage]:
        """Get messages that are still awaiting responses"""
        return list(self.pending_responses.values())
    
    def get_message_flow(self, rfp_id: str) -> List[Dict[str, Any]]:
        """Get the complete message flow for an RFP"""
        messages = [m for m in self.message_history if m.rfp_id == rfp_id]
        messages.sort(key=lambda x: x.timestamp)
        
        flow = []
        for msg in messages:
            flow.append({
                'timestamp': msg.timestamp.isoformat(),
                'from': msg.from_agent.value,
                'to': msg.to_agent.value if isinstance(msg.to_agent, AgentType) else [a.value for a in msg.to_agent],
                'type': msg.message_type.value,
                'priority': msg.priority.name
            })
        return flow


# Singleton broker instance
_broker_instance = None

def get_message_broker() -> MessageBroker:
    """Get singleton message broker"""
    global _broker_instance
    if _broker_instance is None:
        _broker_instance = MessageBroker()
    return _broker_instance


def reset_message_broker():
    """Reset the message broker (useful for testing)"""
    global _broker_instance
    _broker_instance = None


# ============================================================================
# Communication Flow 1: RFP Identification to Analysis
# Sales Agent -> Master Agent
# ============================================================================

def create_rfp_identified_message(
    conversation_id: str,
    rfp_id: str,
    rfp_summary: Dict[str, Any],
    source_url: str = ""
) -> AgentMessage:
    """Create message when Sales Agent identifies a new RFP"""
    return AgentMessage(
        from_agent=AgentType.SALES,
        to_agent=AgentType.MASTER,
        message_type=MessageType.RFP_IDENTIFIED,
        conversation_id=conversation_id,
        rfp_id=rfp_id,
        payload=rfp_summary,
        priority=MessagePriority.HIGH,
        context=MessageContext(source_document=source_url, workflow_stage="RFP_IDENTIFICATION")
    )


def create_rfp_selected_message(
    conversation_id: str,
    rfp_id: str,
    selected_rfp: Dict[str, Any],
    source_document: str = ""
) -> AgentMessage:
    """Create message when Sales Agent selects an RFP for response"""
    return AgentMessage(
        from_agent=AgentType.SALES,
        to_agent=AgentType.MASTER,
        message_type=MessageType.RFP_SELECTED,
        conversation_id=conversation_id,
        rfp_id=rfp_id,
        payload=selected_rfp,
        priority=MessagePriority.HIGH,
        context=MessageContext(source_document=source_document, workflow_stage="RFP_SELECTION")
    )


# ============================================================================
# Communication Flow 2: Technical Analysis
# Master Agent -> Technical Agent -> Master Agent & Pricing Agent
# ============================================================================

def create_rfp_technical_summary(
    conversation_id: str,
    rfp_id: str,
    products_in_scope: List[Dict],
    technical_requirements: List[str],
    acceptance_criteria: List[str],
    source_document: str = ""
) -> AgentMessage:
    """
    Create RFP technical summary message (Master -> Technical)
    
    Contains:
    - Products in scope of supply
    - Technical specifications
    - Acceptance criteria
    - Expected outputs
    """
    return AgentMessage(
        from_agent=AgentType.MASTER,
        to_agent=AgentType.TECHNICAL,
        message_type=MessageType.RFP_TECHNICAL_SUMMARY,
        conversation_id=conversation_id,
        rfp_id=rfp_id,
        payload={
            'products_in_scope': products_in_scope,
            'technical_requirements': technical_requirements,
            'acceptance_criteria': acceptance_criteria,
            'expected_output': {
                'product_recommendations': 'Top 3 OEM products per scope item',
                'spec_match_metrics': 'Percentage match for each recommendation',
                'comparison_table': 'RFP specs vs OEM specs (columns: Spec, RFP Req, OEM1, OEM2, OEM3)',
                'selected_products': 'Best matching OEM product per item'
            },
            'spec_match_formula': 'MatchScore = Σ(ParameterMatch_i × Weight_i) / Σ(Weight_i) × 100 (equal weights)'
        },
        priority=MessagePriority.MEDIUM,
        context=MessageContext(
            source_document=source_document,
            workflow_stage="TECHNICAL_ANALYSIS",
            processing_hints={'send_to_pricing': True}
        )
    )


def create_product_recommendations(
    conversation_id: str,
    rfp_id: str,
    recommendations: List[Dict],
    comparison_table: List[Dict],
    compliance_summary: Dict,
    send_to_pricing: bool = True
) -> AgentMessage:
    """
    Create product recommendations message (Technical -> Master & Pricing)
    
    Contains:
    - Top 3 OEM products per RFP product
    - Spec match percentages
    - Comparison tables
    - Selected products
    """
    # Send to both Master and Pricing if specified
    recipients = [AgentType.MASTER, AgentType.PRICING] if send_to_pricing else AgentType.MASTER
    
    return AgentMessage(
        from_agent=AgentType.TECHNICAL,
        to_agent=recipients,
        message_type=MessageType.PRODUCT_RECOMMENDATIONS,
        conversation_id=conversation_id,
        rfp_id=rfp_id,
        payload={
            'recommendations': recommendations,
            'comparison_table': comparison_table,
            'compliance_summary': compliance_summary,
            'scope_of_supply_table': _build_scope_of_supply_table(recommendations)
        },
        priority=MessagePriority.MEDIUM,
        context=MessageContext(workflow_stage="TECHNICAL_COMPLETE")
    )


def _build_scope_of_supply_table(recommendations: List[Dict]) -> List[Dict]:
    """Build scope of supply table from recommendations"""
    table = []
    for idx, rec in enumerate(recommendations):
        table.append({
            'sl_no': idx + 1,
            'rfp_product': rec.get('rfp_product', ''),
            'rfp_specifications': rec.get('rfp_specifications', {}),
            'quantity': rec.get('quantity', 1),
            'unit': rec.get('unit', 'Nos'),
            'recommended_oem_sku': rec.get('selected_sku', ''),
            'oem_product_name': rec.get('product_name', ''),
            'manufacturer': rec.get('manufacturer', ''),
            'spec_match_percent': rec.get('spec_match_percent', 0),
            'top_3_options': rec.get('top_3_options', [])
        })
    return table


# ============================================================================
# Communication Flow 3: Pricing Estimation
# Master Agent -> Pricing Agent -> Master Agent
# ============================================================================

def create_rfp_pricing_summary(
    conversation_id: str,
    rfp_id: str,
    tests_required: List[str],
    acceptance_criteria: List[str],
    estimated_value: float,
    source_document: str = ""
) -> AgentMessage:
    """
    Create RFP pricing summary message (Master -> Pricing)
    
    Contains:
    - Tests required in RFP
    - Acceptance criteria
    - Estimated contract value
    - Expected outputs
    """
    return AgentMessage(
        from_agent=AgentType.MASTER,
        to_agent=AgentType.PRICING,
        message_type=MessageType.RFP_PRICING_SUMMARY,
        conversation_id=conversation_id,
        rfp_id=rfp_id,
        payload={
            'tests_required': tests_required,
            'acceptance_criteria': acceptance_criteria,
            'estimated_value': estimated_value,
            'expected_output': {
                'unit_prices': 'Price per product SKU from pricing table',
                'test_costs': 'Cost per required test from services table',
                'material_total': 'Total material cost (Σ unit_price × quantity)',
                'services_total': 'Total services cost (Σ test costs)',
                'grand_total': 'Material + Services + Taxes'
            }
        },
        priority=MessagePriority.MEDIUM,
        context=MessageContext(
            source_document=source_document,
            workflow_stage="PRICING_ESTIMATION",
            dependencies=['PRODUCT_RECOMMENDATIONS']
        )
    )


def create_pricing_calculation(
    conversation_id: str,
    rfp_id: str,
    product_prices: List[Dict],
    test_costs: List[Dict],
    total_material_cost: float,
    total_services_cost: float,
    taxes: Dict[str, float],
    grand_total: float
) -> AgentMessage:
    """
    Create pricing calculation message (Pricing -> Master)
    
    Contains:
    - Product prices with SKUs
    - Test/service costs
    - Consolidated totals
    """
    return AgentMessage(
        from_agent=AgentType.PRICING,
        to_agent=AgentType.MASTER,
        message_type=MessageType.PRICING_CALCULATION,
        conversation_id=conversation_id,
        rfp_id=rfp_id,
        payload={
            'product_prices': product_prices,
            'test_costs': test_costs,
            'total_material_cost': total_material_cost,
            'total_services_cost': total_services_cost,
            'taxes': taxes,
            'grand_total': grand_total
        },
        priority=MessagePriority.MEDIUM,
        context=MessageContext(workflow_stage="PRICING_COMPLETE")
    )


# ============================================================================
# Communication Flow 4: Final Consolidation
# Master Agent consolidates all responses
# ============================================================================

def create_consolidated_response(
    conversation_id: str,
    rfp_id: str,
    scope_of_supply: List[Dict],
    test_requirements: List[Dict],
    totals: Dict[str, float],
    overall_spec_match: float,
    recommendation: str
) -> AgentMessage:
    """
    Create consolidated response message (Master -> Output)
    
    Final RFP response containing:
    - Scope of supply with OEM SKUs, spec match %, and prices
    - Test requirements with costs
    - Consolidated totals
    """
    return AgentMessage(
        from_agent=AgentType.MASTER,
        to_agent=AgentType.MASTER,  # Self - for logging/output
        message_type=MessageType.CONSOLIDATED_RESPONSE,
        conversation_id=conversation_id,
        rfp_id=rfp_id,
        payload={
            'scope_of_supply': scope_of_supply,
            'test_requirements': test_requirements,
            'total_material_cost': totals.get('material', 0),
            'total_services_cost': totals.get('services', 0),
            'taxes': totals.get('taxes', 0),
            'grand_total': totals.get('grand_total', 0),
            'overall_spec_match': overall_spec_match,
            'recommendation': recommendation
        },
        priority=MessagePriority.HIGH,
        context=MessageContext(workflow_stage="CONSOLIDATION_COMPLETE"),
        requires_response=False
    )


# ============================================================================
# Utility Messages
# ============================================================================

def create_error_message(
    from_agent: AgentType,
    to_agent: AgentType,
    conversation_id: str,
    error_details: Dict[str, Any]
) -> AgentMessage:
    """Create error message"""
    return AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.ERROR,
        conversation_id=conversation_id,
        payload=error_details,
        priority=MessagePriority.CRITICAL,
        requires_response=False
    )


def create_status_update(
    from_agent: AgentType,
    to_agent: AgentType,
    conversation_id: str,
    status: str,
    progress: float = 0,
    details: Dict[str, Any] = None
) -> AgentMessage:
    """Create status update message"""
    return AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.STATUS_UPDATE,
        conversation_id=conversation_id,
        payload={
            'status': status,
            'progress': progress,
            'details': details or {}
        },
        priority=MessagePriority.LOW,
        requires_response=False
    )
