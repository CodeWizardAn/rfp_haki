"""
Inter-Agent Communication System
================================
Comprehensive message passing, state management, error handling, and retry logic.
Supports Redis or in-memory queues with full observability.

Features:
1. Message Protocol Design
2. Message Queue Implementation (Redis/In-Memory)
3. Message Serializer/Deserializer
4. Message Routing Logic
5. Agent State Manager
6. State Persistence
7. State Recovery Mechanism
8. Message Acknowledgment System
9. Retry Logic with Exponential Backoff
10. Dead Letter Queue
11. Circuit Breaker Pattern
12. Timeout Handling
13. Message Priority Queuing
14. Broadcast Messaging
15. Point-to-Point Messaging
16. Pub-Sub Pattern Support
17. Message Tracing
18. Message Analytics
19. Queue Monitoring
20. Performance Metrics
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set, Tuple, Union
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict
from threading import Lock, RLock
from pathlib import Path
import json
import uuid
import time
import hashlib
import heapq
import pickle
import logging
import traceback
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Performance Integration
try:
    perf_path = str(Path(__file__).parent.parent.parent)
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from performance.integration import cached, profiled, with_timeout
    from agents.shared.agent_performance import (
        track_agent_operation, cache_agent_result, 
        rate_limit_agent, AgentPerformanceManager
    )
    PERFORMANCE_AVAILABLE = True
    logger.info("✅ Performance integration available for inter-agent communication")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Performance integration not available: {e}")
    # Define no-op decorators for graceful fallback
    def cached(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    def profiled(func):
        return func
    def with_timeout(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    def track_agent_operation(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def cache_agent_result(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def rate_limit_agent(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# ============================================================================
# Feature 1: Message Protocol Design
# ============================================================================

class MessageStatus(Enum):
    """Message lifecycle status"""
    CREATED = "created"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    PROCESSING = "processing"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"
    EXPIRED = "expired"


class MessagePriority(Enum):
    """Message priority levels (1 = highest)"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    STANDARD = 4
    LOW = 5


class MessageType(Enum):
    """Types of inter-agent messages"""
    # RFP Workflow
    RFP_SCAN_REQUEST = "rfp_scan_request"
    RFP_SCAN_RESPONSE = "rfp_scan_response"
    RFP_SELECTED = "rfp_selected"
    
    # Technical Analysis
    TECHNICAL_ANALYSIS_REQUEST = "technical_analysis_request"
    TECHNICAL_ANALYSIS_RESPONSE = "technical_analysis_response"
    SPEC_COMPARISON = "spec_comparison"
    
    # Pricing
    PRICING_REQUEST = "pricing_request"
    PRICING_RESPONSE = "pricing_response"
    QUOTE_GENERATED = "quote_generated"
    
    # Consolidation
    CONSOLIDATION_REQUEST = "consolidation_request"
    CONSOLIDATION_RESPONSE = "consolidation_response"
    
    # System
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    ACKNOWLEDGMENT = "acknowledgment"
    
    # Control
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"
    CANCEL = "cancel"
    PAUSE = "pause"
    RESUME = "resume"


class DeliveryMode(Enum):
    """Message delivery modes"""
    POINT_TO_POINT = "point_to_point"
    BROADCAST = "broadcast"
    PUBSUB = "pubsub"
    MULTICAST = "multicast"


class AgentType(Enum):
    """Agent types in the system"""
    MASTER = "MASTER_ORCHESTRATOR"
    SALES = "SALES_AGENT"
    TECHNICAL = "TECHNICAL_AGENT"
    PRICING = "PRICING_AGENT"
    ALL = "ALL_AGENTS"


@dataclass
class MessageHeader:
    """Message header with metadata"""
    message_id: str = field(default_factory=lambda: f"MSG_{uuid.uuid4().hex[:16].upper()}")
    correlation_id: str = ""
    conversation_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    expiry: Optional[datetime] = None
    priority: MessagePriority = MessagePriority.STANDARD
    message_type: MessageType = MessageType.STATUS_UPDATE
    delivery_mode: DeliveryMode = DeliveryMode.POINT_TO_POINT
    reply_to: str = ""
    trace_id: str = field(default_factory=lambda: f"TRACE_{uuid.uuid4().hex[:12].upper()}")
    span_id: str = field(default_factory=lambda: f"SPAN_{uuid.uuid4().hex[:8].upper()}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'correlation_id': self.correlation_id,
            'conversation_id': self.conversation_id,
            'timestamp': self.timestamp.isoformat(),
            'expiry': self.expiry.isoformat() if self.expiry else None,
            'priority': self.priority.value,
            'message_type': self.message_type.value,
            'delivery_mode': self.delivery_mode.value,
            'reply_to': self.reply_to,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
        }


@dataclass
class MessageEnvelope:
    """Complete message envelope with routing info"""
    header: MessageHeader
    from_agent: str
    to_agent: Union[str, List[str]]
    payload: Dict[str, Any]
    status: MessageStatus = MessageStatus.CREATED
    retry_count: int = 0
    max_retries: int = 3
    acknowledgment_required: bool = True
    timeout_seconds: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'header': self.header.to_dict(),
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
            'payload': self.payload,
            'status': self.status.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'acknowledgment_required': self.acknowledgment_required,
            'timeout_seconds': self.timeout_seconds,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'error_message': self.error_message,
        }
    
    def compute_hash(self) -> str:
        """Compute hash of message for integrity verification"""
        content = json.dumps({
            'message_id': self.header.message_id,
            'payload': self.payload,
            'from_agent': self.from_agent,
            'to_agent': self.to_agent,
        }, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# Feature 3: Message Serializer/Deserializer
# ============================================================================

class MessageSerializer:
    """Serialize and deserialize messages for transport"""
    
    @staticmethod
    def serialize(envelope: MessageEnvelope, format: str = 'json') -> bytes:
        """Serialize message envelope to bytes"""
        if format == 'json':
            return json.dumps(envelope.to_dict(), default=str).encode('utf-8')
        elif format == 'pickle':
            return pickle.dumps(envelope)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def deserialize(data: bytes, format: str = 'json') -> MessageEnvelope:
        """Deserialize bytes to message envelope"""
        if format == 'json':
            d = json.loads(data.decode('utf-8'))
            return MessageSerializer._from_dict(d)
        elif format == 'pickle':
            return pickle.loads(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def _from_dict(d: Dict[str, Any]) -> MessageEnvelope:
        """Create MessageEnvelope from dictionary"""
        header_data = d.get('header', {})
        header = MessageHeader(
            message_id=header_data.get('message_id', ''),
            correlation_id=header_data.get('correlation_id', ''),
            conversation_id=header_data.get('conversation_id', ''),
            timestamp=datetime.fromisoformat(header_data['timestamp']) if header_data.get('timestamp') else datetime.now(),
            expiry=datetime.fromisoformat(header_data['expiry']) if header_data.get('expiry') else None,
            priority=MessagePriority(header_data.get('priority', 4)),
            message_type=MessageType(header_data.get('message_type', 'status_update')),
            delivery_mode=DeliveryMode(header_data.get('delivery_mode', 'point_to_point')),
            reply_to=header_data.get('reply_to', ''),
            trace_id=header_data.get('trace_id', ''),
            span_id=header_data.get('span_id', ''),
        )
        
        return MessageEnvelope(
            header=header,
            from_agent=d.get('from_agent', ''),
            to_agent=d.get('to_agent', ''),
            payload=d.get('payload', {}),
            status=MessageStatus(d.get('status', 'created')),
            retry_count=d.get('retry_count', 0),
            max_retries=d.get('max_retries', 3),
            acknowledgment_required=d.get('acknowledgment_required', True),
            timeout_seconds=d.get('timeout_seconds', 30.0),
            metadata=d.get('metadata', {}),
            created_at=datetime.fromisoformat(d['created_at']) if d.get('created_at') else datetime.now(),
            sent_at=datetime.fromisoformat(d['sent_at']) if d.get('sent_at') else None,
            delivered_at=datetime.fromisoformat(d['delivered_at']) if d.get('delivered_at') else None,
            acknowledged_at=datetime.fromisoformat(d['acknowledged_at']) if d.get('acknowledged_at') else None,
            error_message=d.get('error_message', ''),
        )


# ============================================================================
# Feature 2: Message Queue Implementation (Redis/In-Memory)
# ============================================================================

class QueueBackend(ABC):
    """Abstract base for queue backends"""
    
    @abstractmethod
    def push(self, queue_name: str, message: bytes, priority: int = 4) -> bool:
        """Push message to queue"""
        pass
    
    @abstractmethod
    def pop(self, queue_name: str, timeout: float = 0) -> Optional[bytes]:
        """Pop message from queue"""
        pass
    
    @abstractmethod
    def peek(self, queue_name: str) -> Optional[bytes]:
        """Peek at next message without removing"""
        pass
    
    @abstractmethod
    def size(self, queue_name: str) -> int:
        """Get queue size"""
        pass
    
    @abstractmethod
    def clear(self, queue_name: str) -> int:
        """Clear queue and return count of removed items"""
        pass


class InMemoryQueueBackend(QueueBackend):
    """In-memory priority queue backend"""
    
    def __init__(self):
        self.queues: Dict[str, List[Tuple[int, float, bytes]]] = defaultdict(list)
        self.lock = RLock()
        self._counter = 0
    
    def push(self, queue_name: str, message: bytes, priority: int = 4) -> bool:
        """Push with priority (lower number = higher priority)"""
        with self.lock:
            self._counter += 1
            heapq.heappush(
                self.queues[queue_name],
                (priority, self._counter, message)
            )
            logger.debug(f"Message pushed to queue {queue_name}, priority {priority}")
            return True
    
    def pop(self, queue_name: str, timeout: float = 0) -> Optional[bytes]:
        """Pop highest priority message"""
        with self.lock:
            if self.queues[queue_name]:
                _, _, message = heapq.heappop(self.queues[queue_name])
                return message
            return None
    
    def peek(self, queue_name: str) -> Optional[bytes]:
        """Peek without removing"""
        with self.lock:
            if self.queues[queue_name]:
                return self.queues[queue_name][0][2]
            return None
    
    def size(self, queue_name: str) -> int:
        """Get queue size"""
        with self.lock:
            return len(self.queues[queue_name])
    
    def clear(self, queue_name: str) -> int:
        """Clear queue"""
        with self.lock:
            count = len(self.queues[queue_name])
            self.queues[queue_name] = []
            return count
    
    def get_all_queues(self) -> List[str]:
        """Get all queue names"""
        with self.lock:
            return list(self.queues.keys())


class RedisQueueBackend(QueueBackend):
    """Redis-based queue backend (falls back to in-memory if Redis unavailable)"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None
        self.fallback = InMemoryQueueBackend()
        self._use_fallback = False
        self._connect()
    
    def _connect(self):
        """Try to connect to Redis"""
        try:
            import redis
            self.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db)
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            self._use_fallback = False
        except Exception as e:
            logger.warning(f"Redis not available ({e}), using in-memory fallback")
            self._use_fallback = True
    
    def push(self, queue_name: str, message: bytes, priority: int = 4) -> bool:
        """Push to Redis sorted set with priority as score"""
        if self._use_fallback:
            return self.fallback.push(queue_name, message, priority)
        
        try:
            score = priority + (time.time() / 1e10)  # Priority + timestamp for FIFO within priority
            self.redis_client.zadd(queue_name, {message: score})
            return True
        except Exception as e:
            logger.error(f"Redis push error: {e}")
            return self.fallback.push(queue_name, message, priority)
    
    def pop(self, queue_name: str, timeout: float = 0) -> Optional[bytes]:
        """Pop from Redis sorted set (lowest score = highest priority)"""
        if self._use_fallback:
            return self.fallback.pop(queue_name, timeout)
        
        try:
            result = self.redis_client.zpopmin(queue_name, count=1)
            if result:
                return result[0][0]
            return None
        except Exception as e:
            logger.error(f"Redis pop error: {e}")
            return self.fallback.pop(queue_name, timeout)
    
    def peek(self, queue_name: str) -> Optional[bytes]:
        """Peek at lowest score item"""
        if self._use_fallback:
            return self.fallback.peek(queue_name)
        
        try:
            result = self.redis_client.zrange(queue_name, 0, 0)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Redis peek error: {e}")
            return self.fallback.peek(queue_name)
    
    def size(self, queue_name: str) -> int:
        """Get sorted set size"""
        if self._use_fallback:
            return self.fallback.size(queue_name)
        
        try:
            return self.redis_client.zcard(queue_name)
        except Exception as e:
            logger.error(f"Redis size error: {e}")
            return self.fallback.size(queue_name)
    
    def clear(self, queue_name: str) -> int:
        """Clear sorted set"""
        if self._use_fallback:
            return self.fallback.clear(queue_name)
        
        try:
            count = self.redis_client.zcard(queue_name)
            self.redis_client.delete(queue_name)
            return count
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return self.fallback.clear(queue_name)


# ============================================================================
# Feature 4: Message Routing Logic
# ============================================================================

@dataclass
class RoutingRule:
    """Rule for message routing"""
    name: str
    condition: Callable[[MessageEnvelope], bool]
    target_queue: str
    priority_override: Optional[int] = None
    transform: Optional[Callable[[MessageEnvelope], MessageEnvelope]] = None


class MessageRouter:
    """Routes messages based on rules and conditions"""
    
    def __init__(self):
        self.rules: List[RoutingRule] = []
        self.default_routes: Dict[str, str] = {}  # agent -> queue mapping
        self.topic_subscribers: Dict[str, Set[str]] = defaultdict(set)  # topic -> subscribers
        self.lock = Lock()
    
    def add_rule(self, rule: RoutingRule):
        """Add routing rule"""
        with self.lock:
            self.rules.append(rule)
            logger.info(f"Added routing rule: {rule.name}")
    
    def remove_rule(self, name: str) -> bool:
        """Remove routing rule by name"""
        with self.lock:
            for rule in self.rules:
                if rule.name == name:
                    self.rules.remove(rule)
                    return True
            return False
    
    def set_default_route(self, agent_id: str, queue_name: str):
        """Set default queue for an agent"""
        with self.lock:
            self.default_routes[agent_id] = queue_name
    
    def subscribe_to_topic(self, topic: str, subscriber_id: str):
        """Subscribe to a topic for pub-sub"""
        with self.lock:
            self.topic_subscribers[topic].add(subscriber_id)
            logger.info(f"Subscriber {subscriber_id} subscribed to topic {topic}")
    
    def unsubscribe_from_topic(self, topic: str, subscriber_id: str):
        """Unsubscribe from a topic"""
        with self.lock:
            self.topic_subscribers[topic].discard(subscriber_id)
    
    def get_topic_subscribers(self, topic: str) -> Set[str]:
        """Get all subscribers for a topic"""
        with self.lock:
            return self.topic_subscribers.get(topic, set()).copy()
    
    def route(self, envelope: MessageEnvelope) -> List[Tuple[str, MessageEnvelope]]:
        """
        Route message and return list of (queue_name, envelope) tuples
        Supports point-to-point, broadcast, and pub-sub
        """
        results = []
        
        with self.lock:
            # Apply routing rules first
            for rule in self.rules:
                if rule.condition(envelope):
                    transformed = rule.transform(envelope) if rule.transform else envelope
                    if rule.priority_override:
                        transformed.header.priority = MessagePriority(rule.priority_override)
                    results.append((rule.target_queue, transformed))
                    logger.debug(f"Rule {rule.name} matched, routing to {rule.target_queue}")
            
            # If no rules matched, use default routing based on delivery mode
            if not results:
                if envelope.header.delivery_mode == DeliveryMode.BROADCAST:
                    # Send to all agent queues except sender
                    for agent_id, queue in self.default_routes.items():
                        if agent_id != envelope.from_agent:
                            results.append((queue, envelope))
                
                elif envelope.header.delivery_mode == DeliveryMode.PUBSUB:
                    # Get topic from metadata
                    topic = envelope.metadata.get('topic', '')
                    subscribers = self.topic_subscribers.get(topic, set())
                    for subscriber in subscribers:
                        if subscriber in self.default_routes:
                            results.append((self.default_routes[subscriber], envelope))
                
                elif envelope.header.delivery_mode == DeliveryMode.MULTICAST:
                    # Send to multiple specified targets
                    targets = envelope.to_agent if isinstance(envelope.to_agent, list) else [envelope.to_agent]
                    for target in targets:
                        if target in self.default_routes:
                            results.append((self.default_routes[target], envelope))
                
                else:  # POINT_TO_POINT
                    target = envelope.to_agent
                    if isinstance(target, list):
                        target = target[0]
                    if target in self.default_routes:
                        results.append((self.default_routes[target], envelope))
                    else:
                        # Default queue name based on target
                        results.append((f"queue_{target}", envelope))
        
        return results


# ============================================================================
# Feature 5 & 6: Agent State Manager with Persistence
# ============================================================================

class AgentState(Enum):
    """Agent operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentStateInfo:
    """Complete state information for an agent"""
    agent_id: str
    agent_type: str
    state: AgentState = AgentState.INITIALIZING
    last_heartbeat: datetime = field(default_factory=datetime.now)
    current_task: Optional[str] = None
    pending_messages: int = 0
    processed_count: int = 0
    error_count: int = 0
    last_error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 0  # For optimistic locking
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'state': self.state.value,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'current_task': self.current_task,
            'pending_messages': self.pending_messages,
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'metadata': self.metadata,
            'version': self.version,
        }


class StatePersistence(ABC):
    """Abstract base for state persistence"""
    
    @abstractmethod
    def save(self, agent_id: str, state: AgentStateInfo) -> bool:
        pass
    
    @abstractmethod
    def load(self, agent_id: str) -> Optional[AgentStateInfo]:
        pass
    
    @abstractmethod
    def delete(self, agent_id: str) -> bool:
        pass
    
    @abstractmethod
    def list_all(self) -> List[str]:
        pass


class InMemoryStatePersistence(StatePersistence):
    """In-memory state persistence"""
    
    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
    
    def save(self, agent_id: str, state: AgentStateInfo) -> bool:
        with self.lock:
            self.states[agent_id] = state.to_dict()
            return True
    
    def load(self, agent_id: str) -> Optional[AgentStateInfo]:
        with self.lock:
            if agent_id not in self.states:
                return None
            d = self.states[agent_id]
            return AgentStateInfo(
                agent_id=d['agent_id'],
                agent_type=d['agent_type'],
                state=AgentState(d['state']),
                last_heartbeat=datetime.fromisoformat(d['last_heartbeat']),
                current_task=d.get('current_task'),
                pending_messages=d.get('pending_messages', 0),
                processed_count=d.get('processed_count', 0),
                error_count=d.get('error_count', 0),
                last_error=d.get('last_error', ''),
                metadata=d.get('metadata', {}),
                version=d.get('version', 0),
            )
    
    def delete(self, agent_id: str) -> bool:
        with self.lock:
            if agent_id in self.states:
                del self.states[agent_id]
                return True
            return False
    
    def list_all(self) -> List[str]:
        with self.lock:
            return list(self.states.keys())


class FileStatePersistence(StatePersistence):
    """File-based state persistence"""
    
    def __init__(self, directory: str = "./agent_states"):
        import os
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    def _get_path(self, agent_id: str) -> str:
        import os
        return os.path.join(self.directory, f"{agent_id}.json")
    
    def save(self, agent_id: str, state: AgentStateInfo) -> bool:
        try:
            with open(self._get_path(agent_id), 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save state for {agent_id}: {e}")
            return False
    
    def load(self, agent_id: str) -> Optional[AgentStateInfo]:
        import os
        try:
            path = self._get_path(agent_id)
            if not os.path.exists(path):
                return None
            with open(path, 'r') as f:
                d = json.load(f)
            return AgentStateInfo(
                agent_id=d['agent_id'],
                agent_type=d['agent_type'],
                state=AgentState(d['state']),
                last_heartbeat=datetime.fromisoformat(d['last_heartbeat']),
                current_task=d.get('current_task'),
                pending_messages=d.get('pending_messages', 0),
                processed_count=d.get('processed_count', 0),
                error_count=d.get('error_count', 0),
                last_error=d.get('last_error', ''),
                metadata=d.get('metadata', {}),
                version=d.get('version', 0),
            )
        except Exception as e:
            logger.error(f"Failed to load state for {agent_id}: {e}")
            return None
    
    def delete(self, agent_id: str) -> bool:
        import os
        try:
            path = self._get_path(agent_id)
            if os.path.exists(path):
                os.remove(path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete state for {agent_id}: {e}")
            return False
    
    def list_all(self) -> List[str]:
        import os
        try:
            return [f.replace('.json', '') for f in os.listdir(self.directory) if f.endswith('.json')]
        except:
            return []


class AgentStateManager:
    """
    Manages agent states with persistence and recovery
    Features: State transitions, heartbeats, recovery
    """
    
    VALID_TRANSITIONS = {
        AgentState.INITIALIZING: {AgentState.READY, AgentState.ERROR},
        AgentState.READY: {AgentState.BUSY, AgentState.PAUSED, AgentState.ERROR, AgentState.SHUTDOWN},
        AgentState.BUSY: {AgentState.READY, AgentState.PAUSED, AgentState.ERROR},
        AgentState.PAUSED: {AgentState.READY, AgentState.SHUTDOWN, AgentState.ERROR},
        AgentState.ERROR: {AgentState.READY, AgentState.SHUTDOWN},
        AgentState.SHUTDOWN: set(),
    }
    
    def __init__(self, persistence: Optional[StatePersistence] = None, 
                 heartbeat_timeout: float = 60.0):
        self.persistence = persistence or InMemoryStatePersistence()
        self.heartbeat_timeout = heartbeat_timeout
        self.states: Dict[str, AgentStateInfo] = {}
        self.listeners: List[Callable[[str, AgentState, AgentState], None]] = []
        self.lock = Lock()
        self._recover_states()
    
    def _recover_states(self):
        """Feature 7: State Recovery Mechanism"""
        agent_ids = self.persistence.list_all()
        for agent_id in agent_ids:
            state = self.persistence.load(agent_id)
            if state:
                self.states[agent_id] = state
                logger.info(f"Recovered state for agent {agent_id}: {state.state.value}")
    
    def register_agent(self, agent_id: str, agent_type: str, 
                       metadata: Dict[str, Any] = None) -> AgentStateInfo:
        """Register a new agent"""
        with self.lock:
            state = AgentStateInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                metadata=metadata or {}
            )
            self.states[agent_id] = state
            self.persistence.save(agent_id, state)
            logger.info(f"Agent registered: {agent_id} ({agent_type})")
            return state
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        with self.lock:
            if agent_id in self.states:
                del self.states[agent_id]
                self.persistence.delete(agent_id)
                logger.info(f"Agent unregistered: {agent_id}")
                return True
            return False
    
    def transition_state(self, agent_id: str, new_state: AgentState, 
                         reason: str = "") -> bool:
        """Transition agent to new state with validation"""
        with self.lock:
            if agent_id not in self.states:
                logger.warning(f"Unknown agent: {agent_id}")
                return False
            
            current = self.states[agent_id].state
            valid_next = self.VALID_TRANSITIONS.get(current, set())
            
            if new_state not in valid_next:
                logger.warning(f"Invalid transition for {agent_id}: {current.value} -> {new_state.value}")
                return False
            
            old_state = current
            self.states[agent_id].state = new_state
            self.states[agent_id].version += 1
            
            if new_state == AgentState.ERROR:
                self.states[agent_id].last_error = reason
                self.states[agent_id].error_count += 1
            
            self.persistence.save(agent_id, self.states[agent_id])
            logger.info(f"State transition for {agent_id}: {old_state.value} -> {new_state.value}")
            
            # Notify listeners
            for listener in self.listeners:
                try:
                    listener(agent_id, old_state, new_state)
                except Exception as e:
                    logger.error(f"Listener error: {e}")
            
            return True
    
    def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat"""
        with self.lock:
            if agent_id in self.states:
                self.states[agent_id].last_heartbeat = datetime.now()
                return True
            return False
    
    def get_state(self, agent_id: str) -> Optional[AgentStateInfo]:
        """Get agent state"""
        with self.lock:
            return self.states.get(agent_id)
    
    def get_all_states(self) -> Dict[str, AgentStateInfo]:
        """Get all agent states"""
        with self.lock:
            return self.states.copy()
    
    def get_stale_agents(self) -> List[str]:
        """Get agents that haven't sent heartbeat within timeout"""
        with self.lock:
            stale = []
            now = datetime.now()
            for agent_id, state in self.states.items():
                if (now - state.last_heartbeat).total_seconds() > self.heartbeat_timeout:
                    stale.append(agent_id)
            return stale
    
    def add_listener(self, listener: Callable[[str, AgentState, AgentState], None]):
        """Add state change listener"""
        self.listeners.append(listener)
    
    def update_task(self, agent_id: str, task_id: Optional[str]):
        """Update current task for agent"""
        with self.lock:
            if agent_id in self.states:
                self.states[agent_id].current_task = task_id
    
    def increment_processed(self, agent_id: str):
        """Increment processed message count"""
        with self.lock:
            if agent_id in self.states:
                self.states[agent_id].processed_count += 1


# ============================================================================
# Feature 8: Message Acknowledgment System
# ============================================================================

@dataclass
class Acknowledgment:
    """Message acknowledgment"""
    ack_id: str = field(default_factory=lambda: f"ACK_{uuid.uuid4().hex[:12].upper()}")
    message_id: str = ""
    from_agent: str = ""
    status: str = "received"  # received, processed, failed
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ack_id': self.ack_id,
            'message_id': self.message_id,
            'from_agent': self.from_agent,
            'status': self.status,
            'timestamp': self.timestamp.isoformat(),
            'processing_time_ms': self.processing_time_ms,
            'error_message': self.error_message,
        }


class AcknowledgmentManager:
    """Manages message acknowledgments"""
    
    def __init__(self, ack_timeout: float = 30.0):
        self.ack_timeout = ack_timeout
        self.pending_acks: Dict[str, MessageEnvelope] = {}  # message_id -> envelope
        self.ack_times: Dict[str, datetime] = {}  # message_id -> sent_at
        self.received_acks: Dict[str, Acknowledgment] = {}
        self.lock = Lock()
    
    def register_pending(self, envelope: MessageEnvelope):
        """Register message awaiting acknowledgment"""
        with self.lock:
            self.pending_acks[envelope.header.message_id] = envelope
            self.ack_times[envelope.header.message_id] = datetime.now()
    
    def acknowledge(self, message_id: str, from_agent: str, 
                    status: str = "processed", 
                    processing_time_ms: float = 0.0,
                    error_message: str = "") -> Acknowledgment:
        """Record acknowledgment for a message"""
        with self.lock:
            ack = Acknowledgment(
                message_id=message_id,
                from_agent=from_agent,
                status=status,
                processing_time_ms=processing_time_ms,
                error_message=error_message,
            )
            self.received_acks[message_id] = ack
            
            if message_id in self.pending_acks:
                envelope = self.pending_acks[message_id]
                envelope.status = MessageStatus.ACKNOWLEDGED
                envelope.acknowledged_at = datetime.now()
                del self.pending_acks[message_id]
                del self.ack_times[message_id]
            
            logger.debug(f"Acknowledged message {message_id} from {from_agent}: {status}")
            return ack
    
    def get_timed_out(self) -> List[MessageEnvelope]:
        """Get messages that have timed out waiting for ack"""
        with self.lock:
            timed_out = []
            now = datetime.now()
            for message_id, sent_at in list(self.ack_times.items()):
                if (now - sent_at).total_seconds() > self.ack_timeout:
                    if message_id in self.pending_acks:
                        timed_out.append(self.pending_acks[message_id])
            return timed_out
    
    def is_acknowledged(self, message_id: str) -> bool:
        """Check if message was acknowledged"""
        with self.lock:
            return message_id in self.received_acks
    
    def get_acknowledgment(self, message_id: str) -> Optional[Acknowledgment]:
        """Get acknowledgment for message"""
        with self.lock:
            return self.received_acks.get(message_id)
    
    def pending_count(self) -> int:
        """Get count of pending acknowledgments"""
        with self.lock:
            return len(self.pending_acks)


# ============================================================================
# Feature 9: Retry Logic with Exponential Backoff
# ============================================================================

@dataclass
class RetryPolicy:
    """Retry policy configuration"""
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: float = 0.1  # random jitter factor
    retryable_errors: Set[str] = field(default_factory=lambda: {'timeout', 'connection_error', 'rate_limited'})


class RetryManager:
    """Manages retry logic with exponential backoff"""
    
    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self.retry_queue: List[Tuple[float, MessageEnvelope]] = []  # (next_retry_time, envelope)
        self.lock = Lock()
    
    def calculate_delay(self, retry_count: int) -> float:
        """Calculate delay for next retry with exponential backoff"""
        import random
        delay = min(
            self.policy.initial_delay * (self.policy.exponential_base ** retry_count),
            self.policy.max_delay
        )
        # Add jitter
        jitter = delay * self.policy.jitter * random.random()
        return delay + jitter
    
    def should_retry(self, envelope: MessageEnvelope, error_type: str = "") -> bool:
        """Determine if message should be retried"""
        if envelope.retry_count >= self.policy.max_retries:
            return False
        if error_type and error_type not in self.policy.retryable_errors:
            return False
        return True
    
    def schedule_retry(self, envelope: MessageEnvelope) -> float:
        """Schedule message for retry, returns delay in seconds"""
        with self.lock:
            envelope.retry_count += 1
            envelope.status = MessageStatus.RETRYING
            delay = self.calculate_delay(envelope.retry_count)
            next_retry = time.time() + delay
            heapq.heappush(self.retry_queue, (next_retry, envelope))
            logger.info(f"Scheduled retry {envelope.retry_count}/{self.policy.max_retries} "
                       f"for {envelope.header.message_id} in {delay:.2f}s")
            return delay
    
    def get_due_retries(self) -> List[MessageEnvelope]:
        """Get messages due for retry"""
        with self.lock:
            due = []
            now = time.time()
            while self.retry_queue and self.retry_queue[0][0] <= now:
                _, envelope = heapq.heappop(self.retry_queue)
                due.append(envelope)
            return due
    
    def pending_retry_count(self) -> int:
        """Get count of messages pending retry"""
        with self.lock:
            return len(self.retry_queue)


# ============================================================================
# Feature 10: Dead Letter Queue
# ============================================================================

@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue"""
    entry_id: str = field(default_factory=lambda: f"DLQ_{uuid.uuid4().hex[:12].upper()}")
    envelope: MessageEnvelope = field(default_factory=lambda: MessageEnvelope(
        header=MessageHeader(), from_agent="", to_agent="", payload={}
    ))
    reason: str = ""
    error_details: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    original_queue: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entry_id': self.entry_id,
            'envelope': self.envelope.to_dict(),
            'reason': self.reason,
            'error_details': self.error_details,
            'created_at': self.created_at.isoformat(),
            'original_queue': self.original_queue,
        }


class DeadLetterQueue:
    """Dead letter queue for failed messages"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.entries: List[DeadLetterEntry] = []
        self.lock = Lock()
    
    def add(self, envelope: MessageEnvelope, reason: str, 
            error_details: str = "", original_queue: str = "") -> DeadLetterEntry:
        """Add message to dead letter queue"""
        with self.lock:
            envelope.status = MessageStatus.DEAD_LETTERED
            entry = DeadLetterEntry(
                envelope=envelope,
                reason=reason,
                error_details=error_details,
                original_queue=original_queue,
            )
            self.entries.append(entry)
            
            # Trim if exceeds max size
            if len(self.entries) > self.max_size:
                self.entries = self.entries[-self.max_size:]
            
            logger.warning(f"Message {envelope.header.message_id} added to DLQ: {reason}")
            return entry
    
    def get_all(self) -> List[DeadLetterEntry]:
        """Get all dead letter entries"""
        with self.lock:
            return self.entries.copy()
    
    def get_by_reason(self, reason: str) -> List[DeadLetterEntry]:
        """Get entries by reason"""
        with self.lock:
            return [e for e in self.entries if e.reason == reason]
    
    def retry(self, entry_id: str) -> Optional[MessageEnvelope]:
        """Remove entry from DLQ for retry"""
        with self.lock:
            for i, entry in enumerate(self.entries):
                if entry.entry_id == entry_id:
                    entry = self.entries.pop(i)
                    entry.envelope.status = MessageStatus.QUEUED
                    entry.envelope.retry_count = 0
                    logger.info(f"Retrying DLQ entry {entry_id}")
                    return entry.envelope
            return None
    
    def purge(self, older_than: Optional[datetime] = None) -> int:
        """Purge entries, optionally older than specified datetime"""
        with self.lock:
            if older_than:
                original_count = len(self.entries)
                self.entries = [e for e in self.entries if e.created_at >= older_than]
                return original_count - len(self.entries)
            else:
                count = len(self.entries)
                self.entries = []
                return count
    
    def size(self) -> int:
        """Get DLQ size"""
        with self.lock:
            return len(self.entries)


# ============================================================================
# Feature 11: Circuit Breaker Pattern
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5       # Failures to open circuit
    success_threshold: int = 3       # Successes to close from half-open
    timeout: float = 30.0            # Seconds before transitioning from open to half-open
    half_open_max_calls: int = 3     # Max calls in half-open state


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance
    Prevents cascading failures by stopping calls to failing services
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self.lock = Lock()
        self.listeners: List[Callable[[CircuitState, CircuitState], None]] = []
    
    def _transition(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        logger.info(f"Circuit {self.name}: {old_state.value} -> {new_state.value}")
        for listener in self.listeners:
            try:
                listener(old_state, new_state)
            except:
                pass
    
    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                # Check if timeout has passed
                if self.last_failure_time:
                    elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                    if elapsed >= self.config.timeout:
                        self._transition(CircuitState.HALF_OPEN)
                        self.half_open_calls = 0
                        return True
                return False
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.config.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False
            
            return False
    
    def record_success(self):
        """Record successful execution"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition(CircuitState.CLOSED)
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    def record_failure(self):
        """Record failed execution"""
        with self.lock:
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self._transition(CircuitState.OPEN)
                self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count += 1
                if self.failure_count >= self.config.failure_threshold:
                    self._transition(CircuitState.OPEN)
    
    def get_state(self) -> CircuitState:
        """Get current state"""
        with self.lock:
            return self.state
    
    def reset(self):
        """Force reset to closed state"""
        with self.lock:
            self._transition(CircuitState.CLOSED)
            self.failure_count = 0
            self.success_count = 0
    
    def add_listener(self, listener: Callable[[CircuitState, CircuitState], None]):
        """Add state change listener"""
        self.listeners.append(listener)


class CircuitBreakerRegistry:
    """Registry of circuit breakers for different services"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = Lock()
    
    def get_or_create(self, name: str, 
                      config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]
    
    def get_all_states(self) -> Dict[str, CircuitState]:
        """Get states of all circuit breakers"""
        with self.lock:
            return {name: cb.get_state() for name, cb in self.breakers.items()}


# ============================================================================
# Feature 12: Timeout Handling
# ============================================================================

class TimeoutError(Exception):
    """Raised when operation times out"""
    pass


class TimeoutManager:
    """Manages operation timeouts"""
    
    def __init__(self):
        self.active_timeouts: Dict[str, Tuple[datetime, float]] = {}  # id -> (start, timeout)
        self.lock = Lock()
    
    def start_timeout(self, operation_id: str, timeout_seconds: float):
        """Start tracking timeout for operation"""
        with self.lock:
            self.active_timeouts[operation_id] = (datetime.now(), timeout_seconds)
    
    def check_timeout(self, operation_id: str) -> bool:
        """Check if operation has timed out"""
        with self.lock:
            if operation_id not in self.active_timeouts:
                return False
            start, timeout = self.active_timeouts[operation_id]
            return (datetime.now() - start).total_seconds() > timeout
    
    def complete(self, operation_id: str):
        """Mark operation as complete"""
        with self.lock:
            self.active_timeouts.pop(operation_id, None)
    
    def get_timed_out_operations(self) -> List[str]:
        """Get all timed out operation IDs"""
        with self.lock:
            timed_out = []
            now = datetime.now()
            for op_id, (start, timeout) in self.active_timeouts.items():
                if (now - start).total_seconds() > timeout:
                    timed_out.append(op_id)
            return timed_out
    
    def get_remaining_time(self, operation_id: str) -> Optional[float]:
        """Get remaining time for operation"""
        with self.lock:
            if operation_id not in self.active_timeouts:
                return None
            start, timeout = self.active_timeouts[operation_id]
            elapsed = (datetime.now() - start).total_seconds()
            return max(0, timeout - elapsed)


# ============================================================================
# Feature 17: Message Tracing
# ============================================================================

@dataclass
class TraceSpan:
    """A span in the message trace"""
    span_id: str = field(default_factory=lambda: f"SPAN_{uuid.uuid4().hex[:8].upper()}")
    trace_id: str = ""
    parent_span_id: str = ""
    operation_name: str = ""
    agent_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "in_progress"
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'span_id': self.span_id,
            'trace_id': self.trace_id,
            'parent_span_id': self.parent_span_id,
            'operation_name': self.operation_name,
            'agent_id': self.agent_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': (self.end_time - self.start_time).total_seconds() * 1000 if self.end_time else None,
            'status': self.status,
            'tags': self.tags,
            'logs': self.logs,
        }


class MessageTracer:
    """Distributed tracing for messages across agents"""
    
    def __init__(self, max_traces: int = 10000):
        self.max_traces = max_traces
        self.traces: Dict[str, List[TraceSpan]] = {}  # trace_id -> spans
        self.active_spans: Dict[str, TraceSpan] = {}  # span_id -> span
        self.lock = Lock()
    
    def start_trace(self, trace_id: str = "") -> str:
        """Start a new trace"""
        with self.lock:
            if not trace_id:
                trace_id = f"TRACE_{uuid.uuid4().hex[:12].upper()}"
            self.traces[trace_id] = []
            logger.debug(f"Started trace: {trace_id}")
            return trace_id
    
    def start_span(self, trace_id: str, operation_name: str, 
                   agent_id: str, parent_span_id: str = "",
                   tags: Dict[str, str] = None) -> TraceSpan:
        """Start a new span within a trace"""
        with self.lock:
            span = TraceSpan(
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                operation_name=operation_name,
                agent_id=agent_id,
                tags=tags or {},
            )
            self.active_spans[span.span_id] = span
            if trace_id in self.traces:
                self.traces[trace_id].append(span)
            else:
                self.traces[trace_id] = [span]
            return span
    
    def add_log(self, span_id: str, message: str, level: str = "info"):
        """Add log entry to span"""
        with self.lock:
            if span_id in self.active_spans:
                self.active_spans[span_id].logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'level': level,
                    'message': message,
                })
    
    def set_tag(self, span_id: str, key: str, value: str):
        """Set tag on span"""
        with self.lock:
            if span_id in self.active_spans:
                self.active_spans[span_id].tags[key] = value
    
    def end_span(self, span_id: str, status: str = "ok"):
        """End a span"""
        with self.lock:
            if span_id in self.active_spans:
                span = self.active_spans[span_id]
                span.end_time = datetime.now()
                span.status = status
                del self.active_spans[span_id]
                logger.debug(f"Ended span {span_id}: {status}")
    
    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace"""
        with self.lock:
            return self.traces.get(trace_id, [])
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of a trace"""
        with self.lock:
            spans = self.traces.get(trace_id, [])
            if not spans:
                return {}
            
            start_time = min(s.start_time for s in spans)
            end_times = [s.end_time for s in spans if s.end_time]
            end_time = max(end_times) if end_times else None
            
            return {
                'trace_id': trace_id,
                'span_count': len(spans),
                'agents_involved': list(set(s.agent_id for s in spans)),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat() if end_time else None,
                'duration_ms': (end_time - start_time).total_seconds() * 1000 if end_time else None,
                'status': 'completed' if not self.active_spans else 'in_progress',
            }
    
    def cleanup_old_traces(self, older_than: datetime):
        """Remove traces older than specified datetime"""
        with self.lock:
            to_remove = []
            for trace_id, spans in self.traces.items():
                if spans and all(s.end_time and s.end_time < older_than for s in spans):
                    to_remove.append(trace_id)
            for trace_id in to_remove:
                del self.traces[trace_id]
            return len(to_remove)


# ============================================================================
# Feature 18: Message Analytics
# ============================================================================

@dataclass
class MessageMetrics:
    """Metrics for message analytics"""
    total_sent: int = 0
    total_received: int = 0
    total_processed: int = 0
    total_failed: int = 0
    total_retried: int = 0
    total_dead_lettered: int = 0
    avg_processing_time_ms: float = 0.0
    processing_times: List[float] = field(default_factory=list)
    messages_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    messages_by_priority: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class MessageAnalytics:
    """Analytics for message processing"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics_by_agent: Dict[str, MessageMetrics] = defaultdict(MessageMetrics)
        self.global_metrics = MessageMetrics()
        self.lock = Lock()
    
    def record_sent(self, from_agent: str, message_type: str, priority: int):
        """Record message sent"""
        with self.lock:
            self.global_metrics.total_sent += 1
            self.global_metrics.messages_by_type[message_type] += 1
            self.global_metrics.messages_by_priority[priority] += 1
            self.metrics_by_agent[from_agent].total_sent += 1
    
    def record_received(self, to_agent: str):
        """Record message received"""
        with self.lock:
            self.global_metrics.total_received += 1
            self.metrics_by_agent[to_agent].total_received += 1
    
    def record_processed(self, agent_id: str, processing_time_ms: float):
        """Record message processed"""
        with self.lock:
            self.global_metrics.total_processed += 1
            self.global_metrics.processing_times.append(processing_time_ms)
            
            # Keep window size
            if len(self.global_metrics.processing_times) > self.window_size:
                self.global_metrics.processing_times = self.global_metrics.processing_times[-self.window_size:]
            
            # Update average
            self.global_metrics.avg_processing_time_ms = sum(self.global_metrics.processing_times) / len(self.global_metrics.processing_times)
            
            self.metrics_by_agent[agent_id].total_processed += 1
    
    def record_failed(self, agent_id: str, error_type: str):
        """Record message failure"""
        with self.lock:
            self.global_metrics.total_failed += 1
            self.global_metrics.errors_by_type[error_type] += 1
            self.metrics_by_agent[agent_id].total_failed += 1
    
    def record_retry(self, agent_id: str):
        """Record message retry"""
        with self.lock:
            self.global_metrics.total_retried += 1
            self.metrics_by_agent[agent_id].total_retried += 1
    
    def record_dead_letter(self, agent_id: str):
        """Record message dead-lettered"""
        with self.lock:
            self.global_metrics.total_dead_lettered += 1
            self.metrics_by_agent[agent_id].total_dead_lettered += 1
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global metrics"""
        with self.lock:
            return {
                'total_sent': self.global_metrics.total_sent,
                'total_received': self.global_metrics.total_received,
                'total_processed': self.global_metrics.total_processed,
                'total_failed': self.global_metrics.total_failed,
                'total_retried': self.global_metrics.total_retried,
                'total_dead_lettered': self.global_metrics.total_dead_lettered,
                'avg_processing_time_ms': round(self.global_metrics.avg_processing_time_ms, 2),
                'messages_by_type': dict(self.global_metrics.messages_by_type),
                'messages_by_priority': dict(self.global_metrics.messages_by_priority),
                'errors_by_type': dict(self.global_metrics.errors_by_type),
                'success_rate': round(
                    self.global_metrics.total_processed / max(1, self.global_metrics.total_sent) * 100, 2
                ),
            }
    
    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for specific agent"""
        with self.lock:
            m = self.metrics_by_agent.get(agent_id, MessageMetrics())
            return {
                'agent_id': agent_id,
                'total_sent': m.total_sent,
                'total_received': m.total_received,
                'total_processed': m.total_processed,
                'total_failed': m.total_failed,
                'total_retried': m.total_retried,
            }


# ============================================================================
# Feature 19: Queue Monitoring
# ============================================================================

@dataclass
class QueueStats:
    """Statistics for a queue"""
    queue_name: str
    size: int
    enqueue_rate: float  # messages per second
    dequeue_rate: float
    oldest_message_age_seconds: float
    avg_wait_time_seconds: float


class QueueMonitor:
    """Monitors queue health and performance"""
    
    def __init__(self, backend: QueueBackend):
        self.backend = backend
        self.enqueue_counts: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        self.dequeue_counts: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        self.lock = Lock()
    
    def record_enqueue(self, queue_name: str):
        """Record enqueue event"""
        with self.lock:
            now = time.time()
            self.enqueue_counts[queue_name].append((now, 1))
            # Keep last 60 seconds
            self.enqueue_counts[queue_name] = [
                (t, c) for t, c in self.enqueue_counts[queue_name]
                if now - t < 60
            ]
    
    def record_dequeue(self, queue_name: str):
        """Record dequeue event"""
        with self.lock:
            now = time.time()
            self.dequeue_counts[queue_name].append((now, 1))
            self.dequeue_counts[queue_name] = [
                (t, c) for t, c in self.dequeue_counts[queue_name]
                if now - t < 60
            ]
    
    def get_queue_stats(self, queue_name: str) -> QueueStats:
        """Get statistics for a queue"""
        with self.lock:
            now = time.time()
            
            # Calculate rates (messages per second over last 60 seconds)
            enqueue_count = sum(c for t, c in self.enqueue_counts.get(queue_name, []))
            dequeue_count = sum(c for t, c in self.dequeue_counts.get(queue_name, []))
            
            return QueueStats(
                queue_name=queue_name,
                size=self.backend.size(queue_name),
                enqueue_rate=enqueue_count / 60.0,
                dequeue_rate=dequeue_count / 60.0,
                oldest_message_age_seconds=0.0,  # Would need message timestamps
                avg_wait_time_seconds=0.0,
            )
    
    def get_all_queue_stats(self) -> List[QueueStats]:
        """Get stats for all queues"""
        if isinstance(self.backend, InMemoryQueueBackend):
            queues = self.backend.get_all_queues()
            return [self.get_queue_stats(q) for q in queues]
        return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        stats = self.get_all_queue_stats()
        total_size = sum(s.size for s in stats)
        
        return {
            'healthy': True,
            'queue_count': len(stats),
            'total_messages': total_size,
            'queues': [
                {
                    'name': s.queue_name,
                    'size': s.size,
                    'enqueue_rate': round(s.enqueue_rate, 2),
                    'dequeue_rate': round(s.dequeue_rate, 2),
                }
                for s in stats
            ]
        }


# ============================================================================
# Feature 20: Performance Metrics
# ============================================================================

@dataclass
class PerformanceSnapshot:
    """Point-in-time performance snapshot"""
    timestamp: datetime = field(default_factory=datetime.now)
    messages_in_flight: int = 0
    queue_depth: int = 0
    avg_latency_ms: float = 0.0
    throughput_per_second: float = 0.0
    error_rate: float = 0.0
    active_agents: int = 0
    circuit_breakers_open: int = 0


class PerformanceMetrics:
    """Comprehensive performance metrics collection"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.snapshots: List[PerformanceSnapshot] = []
        self.latencies: List[float] = []
        self.throughput_window: List[Tuple[float, int]] = []  # (timestamp, count)
        self.lock = RLock()  # Use RLock for reentrant locking
    
    def record_latency(self, latency_ms: float):
        """Record message latency"""
        with self.lock:
            self.latencies.append(latency_ms)
            if len(self.latencies) > self.history_size:
                self.latencies = self.latencies[-self.history_size:]
    
    def record_throughput(self, count: int = 1):
        """Record message throughput"""
        with self.lock:
            now = time.time()
            self.throughput_window.append((now, count))
            # Keep last 60 seconds
            self.throughput_window = [
                (t, c) for t, c in self.throughput_window
                if now - t < 60
            ]
    
    def get_avg_latency(self) -> float:
        """Get average latency"""
        with self.lock:
            if not self.latencies:
                return 0.0
            return sum(self.latencies) / len(self.latencies)
    
    def get_p99_latency(self) -> float:
        """Get 99th percentile latency"""
        with self.lock:
            if not self.latencies:
                return 0.0
            sorted_latencies = sorted(self.latencies)
            idx = int(len(sorted_latencies) * 0.99)
            return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def get_throughput(self) -> float:
        """Get messages per second (last 60 seconds)"""
        with self.lock:
            if not self.throughput_window:
                return 0.0
            total = sum(c for _, c in self.throughput_window)
            return total / 60.0
    
    def take_snapshot(self, messages_in_flight: int = 0, 
                      queue_depth: int = 0,
                      active_agents: int = 0,
                      error_rate: float = 0.0,
                      circuit_breakers_open: int = 0) -> PerformanceSnapshot:
        """Take performance snapshot"""
        with self.lock:
            snapshot = PerformanceSnapshot(
                messages_in_flight=messages_in_flight,
                queue_depth=queue_depth,
                avg_latency_ms=self.get_avg_latency(),
                throughput_per_second=self.get_throughput(),
                error_rate=error_rate,
                active_agents=active_agents,
                circuit_breakers_open=circuit_breakers_open,
            )
            self.snapshots.append(snapshot)
            if len(self.snapshots) > self.history_size:
                self.snapshots = self.snapshots[-self.history_size:]
            return snapshot
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        with self.lock:
            return {
                'avg_latency_ms': round(self.get_avg_latency(), 2),
                'p99_latency_ms': round(self.get_p99_latency(), 2),
                'throughput_per_second': round(self.get_throughput(), 2),
                'latency_samples': len(self.latencies),
                'snapshot_count': len(self.snapshots),
            }


# ============================================================================
# Main Communication System (Integrates All Features)
# ============================================================================

class InterAgentCommunicationSystem:
    """
    Complete inter-agent communication system
    Integrates all 20 features for robust message passing
    """
    
    def __init__(self, 
                 use_redis: bool = False,
                 redis_host: str = 'localhost',
                 redis_port: int = 6379,
                 state_persistence_dir: Optional[str] = None):
        """
        Initialize the communication system
        
        Args:
            use_redis: Whether to use Redis (falls back to in-memory if unavailable)
            redis_host: Redis host
            redis_port: Redis port
            state_persistence_dir: Directory for state persistence (None for in-memory)
        """
        # Feature 2: Queue Backend
        if use_redis:
            self.queue_backend = RedisQueueBackend(redis_host, redis_port)
        else:
            self.queue_backend = InMemoryQueueBackend()
        
        # Feature 3: Serializer
        self.serializer = MessageSerializer()
        
        # Feature 4: Router
        self.router = MessageRouter()
        
        # Feature 5 & 6: State Manager with Persistence
        if state_persistence_dir:
            persistence = FileStatePersistence(state_persistence_dir)
        else:
            persistence = InMemoryStatePersistence()
        self.state_manager = AgentStateManager(persistence)
        
        # Feature 8: Acknowledgment Manager
        self.ack_manager = AcknowledgmentManager()
        
        # Feature 9: Retry Manager
        self.retry_manager = RetryManager()
        
        # Feature 10: Dead Letter Queue
        self.dlq = DeadLetterQueue()
        
        # Feature 11: Circuit Breakers
        self.circuit_registry = CircuitBreakerRegistry()
        
        # Feature 12: Timeout Manager
        self.timeout_manager = TimeoutManager()
        
        # Feature 17: Message Tracer
        self.tracer = MessageTracer()
        
        # Feature 18: Analytics
        self.analytics = MessageAnalytics()
        
        # Feature 19: Queue Monitor
        self.queue_monitor = QueueMonitor(self.queue_backend)
        
        # Feature 20: Performance Metrics
        self.performance = PerformanceMetrics()
        
        # Message handlers
        self.handlers: Dict[str, List[Callable[[MessageEnvelope], None]]] = defaultdict(list)
        
        logger.info("InterAgentCommunicationSystem initialized")
    
    def register_agent(self, agent_id: str, agent_type: str, 
                       metadata: Dict[str, Any] = None) -> AgentStateInfo:
        """Register an agent with the system"""
        state = self.state_manager.register_agent(agent_id, agent_type, metadata)
        self.router.set_default_route(agent_id, f"queue_{agent_id}")
        return state
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        return self.state_manager.unregister_agent(agent_id)
    
    def create_message(self, 
                       from_agent: str,
                       to_agent: Union[str, List[str]],
                       message_type: MessageType,
                       payload: Dict[str, Any],
                       priority: MessagePriority = MessagePriority.STANDARD,
                       delivery_mode: DeliveryMode = DeliveryMode.POINT_TO_POINT,
                       timeout_seconds: float = 30.0,
                       correlation_id: str = "",
                       conversation_id: str = "",
                       metadata: Dict[str, Any] = None) -> MessageEnvelope:
        """Create a new message envelope"""
        header = MessageHeader(
            priority=priority,
            message_type=message_type,
            delivery_mode=delivery_mode,
            correlation_id=correlation_id,
            conversation_id=conversation_id,
        )
        
        return MessageEnvelope(
            header=header,
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {},
        )
    
    def send(self, envelope: MessageEnvelope) -> str:
        """
        Send a message through the system
        Features: Routing, Priority Queuing, Tracing, Analytics
        """
        # Check circuit breaker for target
        target = envelope.to_agent if isinstance(envelope.to_agent, str) else envelope.to_agent[0]
        circuit = self.circuit_registry.get_or_create(target)
        
        if not circuit.can_execute():
            logger.warning(f"Circuit breaker open for {target}, message not sent")
            self.dlq.add(envelope, "circuit_breaker_open")
            return ""
        
        # Start trace
        trace_id = envelope.header.trace_id
        if trace_id not in self.tracer.traces:
            self.tracer.start_trace(trace_id)
        
        span = self.tracer.start_span(
            trace_id, 
            f"send_{envelope.header.message_type.value}",
            envelope.from_agent
        )
        
        try:
            # Route message
            routes = self.router.route(envelope)
            
            for queue_name, routed_envelope in routes:
                # Serialize
                data = self.serializer.serialize(routed_envelope)
                
                # Push to queue with priority
                self.queue_backend.push(
                    queue_name, 
                    data, 
                    routed_envelope.header.priority.value
                )
                
                # Update status
                routed_envelope.status = MessageStatus.QUEUED
                routed_envelope.sent_at = datetime.now()
                
                # Track for acknowledgment if required
                if routed_envelope.acknowledgment_required:
                    self.ack_manager.register_pending(routed_envelope)
                
                # Start timeout tracking
                self.timeout_manager.start_timeout(
                    routed_envelope.header.message_id,
                    routed_envelope.timeout_seconds
                )
                
                # Record analytics
                self.analytics.record_sent(
                    envelope.from_agent,
                    envelope.header.message_type.value,
                    envelope.header.priority.value
                )
                
                # Monitor queue
                self.queue_monitor.record_enqueue(queue_name)
                
                logger.info(f"Message {envelope.header.message_id} queued to {queue_name}")
            
            circuit.record_success()
            self.tracer.end_span(span.span_id, "ok")
            return envelope.header.message_id
            
        except Exception as e:
            circuit.record_failure()
            self.tracer.end_span(span.span_id, "error")
            logger.error(f"Failed to send message: {e}")
            raise
    
    def receive(self, agent_id: str, timeout: float = 0) -> Optional[MessageEnvelope]:
        """
        Receive next message for an agent
        Features: Priority Queue, Timeout, Tracing
        """
        queue_name = f"queue_{agent_id}"
        
        data = self.queue_backend.pop(queue_name, timeout)
        if not data:
            return None
        
        envelope = self.serializer.deserialize(data)
        envelope.status = MessageStatus.DELIVERED
        envelope.delivered_at = datetime.now()
        
        # Record analytics
        self.analytics.record_received(agent_id)
        self.queue_monitor.record_dequeue(queue_name)
        
        # Add trace span
        span = self.tracer.start_span(
            envelope.header.trace_id,
            f"receive_{envelope.header.message_type.value}",
            agent_id,
            envelope.header.span_id
        )
        envelope.metadata['receive_span_id'] = span.span_id
        
        logger.debug(f"Agent {agent_id} received message {envelope.header.message_id}")
        return envelope
    
    def acknowledge(self, envelope: MessageEnvelope, 
                    status: str = "processed",
                    processing_time_ms: float = 0.0,
                    error_message: str = "") -> Acknowledgment:
        """
        Acknowledge message processing
        Features: Acknowledgment, Analytics, Tracing
        """
        ack = self.ack_manager.acknowledge(
            envelope.header.message_id,
            envelope.to_agent if isinstance(envelope.to_agent, str) else envelope.to_agent[0],
            status,
            processing_time_ms,
            error_message
        )
        
        # Complete timeout tracking
        self.timeout_manager.complete(envelope.header.message_id)
        
        # Record analytics
        if status == "processed":
            self.analytics.record_processed(
                envelope.to_agent if isinstance(envelope.to_agent, str) else envelope.to_agent[0],
                processing_time_ms
            )
            self.performance.record_latency(processing_time_ms)
            self.performance.record_throughput()
        elif status == "failed":
            self.analytics.record_failed(
                envelope.to_agent if isinstance(envelope.to_agent, str) else envelope.to_agent[0],
                error_message
            )
        
        # End trace span
        if 'receive_span_id' in envelope.metadata:
            self.tracer.end_span(envelope.metadata['receive_span_id'], status)
        
        return ack
    
    def handle_failure(self, envelope: MessageEnvelope, 
                       error_type: str = "unknown",
                       error_details: str = "") -> bool:
        """
        Handle message processing failure
        Features: Retry Logic, Dead Letter Queue, Analytics
        """
        if self.retry_manager.should_retry(envelope, error_type):
            delay = self.retry_manager.schedule_retry(envelope)
            self.analytics.record_retry(
                envelope.to_agent if isinstance(envelope.to_agent, str) else envelope.to_agent[0]
            )
            logger.info(f"Message {envelope.header.message_id} scheduled for retry in {delay:.2f}s")
            return True
        else:
            # Move to dead letter queue
            self.dlq.add(
                envelope, 
                reason=error_type, 
                error_details=error_details,
                original_queue=f"queue_{envelope.to_agent}"
            )
            self.analytics.record_dead_letter(
                envelope.to_agent if isinstance(envelope.to_agent, str) else envelope.to_agent[0]
            )
            return False
    
    def process_retries(self) -> List[MessageEnvelope]:
        """Process messages due for retry"""
        due = self.retry_manager.get_due_retries()
        for envelope in due:
            try:
                self.send(envelope)
            except Exception as e:
                logger.error(f"Retry failed for {envelope.header.message_id}: {e}")
        return due
    
    def broadcast(self, from_agent: str, 
                  message_type: MessageType,
                  payload: Dict[str, Any],
                  priority: MessagePriority = MessagePriority.STANDARD) -> str:
        """Feature 14: Broadcast Messaging"""
        envelope = self.create_message(
            from_agent=from_agent,
            to_agent="ALL",
            message_type=message_type,
            payload=payload,
            priority=priority,
            delivery_mode=DeliveryMode.BROADCAST
        )
        return self.send(envelope)
    
    def point_to_point(self, from_agent: str,
                       to_agent: str,
                       message_type: MessageType,
                       payload: Dict[str, Any],
                       priority: MessagePriority = MessagePriority.STANDARD) -> str:
        """Feature 15: Point-to-Point Messaging"""
        envelope = self.create_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            priority=priority,
            delivery_mode=DeliveryMode.POINT_TO_POINT
        )
        return self.send(envelope)
    
    def publish(self, from_agent: str,
                topic: str,
                message_type: MessageType,
                payload: Dict[str, Any],
                priority: MessagePriority = MessagePriority.STANDARD) -> str:
        """Feature 16: Pub-Sub Pattern - Publish"""
        envelope = self.create_message(
            from_agent=from_agent,
            to_agent="TOPIC",
            message_type=message_type,
            payload=payload,
            priority=priority,
            delivery_mode=DeliveryMode.PUBSUB,
            metadata={'topic': topic}
        )
        return self.send(envelope)
    
    def subscribe(self, agent_id: str, topic: str):
        """Feature 16: Pub-Sub Pattern - Subscribe"""
        self.router.subscribe_to_topic(topic, agent_id)
        logger.info(f"Agent {agent_id} subscribed to topic {topic}")
    
    def unsubscribe(self, agent_id: str, topic: str):
        """Feature 16: Pub-Sub Pattern - Unsubscribe"""
        self.router.unsubscribe_from_topic(topic, agent_id)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        return {
            'healthy': True,
            'queue_health': self.queue_monitor.get_health_status(),
            'agent_states': {
                agent_id: state.to_dict() 
                for agent_id, state in self.state_manager.get_all_states().items()
            },
            'circuit_breakers': {
                name: state.value 
                for name, state in self.circuit_registry.get_all_states().items()
            },
            'pending_acks': self.ack_manager.pending_count(),
            'pending_retries': self.retry_manager.pending_retry_count(),
            'dlq_size': self.dlq.size(),
            'analytics': self.analytics.get_global_metrics(),
            'performance': self.performance.get_metrics_summary(),
        }
    
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """Get message trace"""
        return self.tracer.get_trace_summary(trace_id)


# ============================================================================
# Singleton and Factory Functions
# ============================================================================

_comm_system_instance: Optional[InterAgentCommunicationSystem] = None

def get_communication_system(use_redis: bool = False,
                             redis_host: str = 'localhost',
                             redis_port: int = 6379,
                             state_persistence_dir: Optional[str] = None) -> InterAgentCommunicationSystem:
    """Get or create singleton communication system"""
    global _comm_system_instance
    if _comm_system_instance is None:
        _comm_system_instance = InterAgentCommunicationSystem(
            use_redis=use_redis,
            redis_host=redis_host,
            redis_port=redis_port,
            state_persistence_dir=state_persistence_dir
        )
    return _comm_system_instance

def reset_communication_system():
    """Reset the communication system (for testing)"""
    global _comm_system_instance
    _comm_system_instance = None


# ============================================================================
# Convenience Functions
# ============================================================================

def create_rfp_workflow_message(from_agent: str, to_agent: str,
                                rfp_id: str, workflow_stage: str,
                                payload: Dict[str, Any]) -> MessageEnvelope:
    """Create an RFP workflow message"""
    header = MessageHeader(
        priority=MessagePriority.HIGH,
        message_type=MessageType.WORKFLOW_START,
        conversation_id=f"CONV_{rfp_id}",
    )
    
    return MessageEnvelope(
        header=header,
        from_agent=from_agent,
        to_agent=to_agent,
        payload=payload,
        metadata={
            'rfp_id': rfp_id,
            'workflow_stage': workflow_stage,
        }
    )
