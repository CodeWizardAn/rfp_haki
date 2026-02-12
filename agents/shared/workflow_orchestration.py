"""
Workflow Orchestration Engine
=============================
Complete end-to-end workflow from RFP identification to final response generation.
Includes all agent interactions, data flows, and error handling.

Features:
1. Workflow Orchestration Engine
2. Workflow State Tracker
3. Step-by-Step Execution
4. Checkpoint System
5. Rollback Mechanism
6. Parallel Processing Support
7. Workflow Visualization
8. Progress Tracking
9. Time Estimation
10. Workflow Templates
11. Conditional Branching
12. Human-in-the-Loop Points
13. Approval Workflows
14. Notification Triggers
15. Workflow Logging
16. Workflow Metrics
17. Success/Failure Handlers
18. Workflow Retry Logic
19. Workflow Testing Framework
20. End-to-End Test Scenarios
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set, Tuple, Union, Type
from enum import Enum, auto
from abc import ABC, abstractmethod
from collections import defaultdict
from threading import Lock, RLock, Event, Thread
from concurrent.futures import ThreadPoolExecutor, Future, as_completed, TimeoutError as FutureTimeoutError
from queue import Queue, PriorityQueue, Empty
import json
import uuid
import time
import hashlib
import copy
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class WorkflowStatus(Enum):
    """Overall workflow status"""
    DRAFT = "draft"
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class StepStatus(Enum):
    """Status of individual workflow step"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"
    ROLLED_BACK = "rolled_back"


class StepType(Enum):
    """Type of workflow step"""
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    APPROVAL = "approval"
    HUMAN_INPUT = "human_input"
    NOTIFICATION = "notification"
    CHECKPOINT = "checkpoint"
    SUBWORKFLOW = "subworkflow"


class ApprovalStatus(Enum):
    """Status of approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    APPROVAL_REQUIRED = "approval_required"
    ACTION_REQUIRED = "action_required"


class BranchCondition(Enum):
    """Conditional branching types"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX_MATCH = "regex_match"
    CUSTOM = "custom"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class StepDefinition:
    """Definition of a workflow step"""
    step_id: str
    name: str
    step_type: StepType = StepType.TASK
    handler: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 3
    retry_delay_seconds: int = 5
    is_checkpoint: bool = False
    is_human_task: bool = False
    approval_required: bool = False
    approvers: List[str] = field(default_factory=list)
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of executing a workflow step"""
    step_id: str
    status: StepStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    execution_time_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Checkpoint:
    """Checkpoint for workflow state"""
    checkpoint_id: str
    workflow_id: str
    step_id: str
    created_at: datetime
    state_snapshot: Dict[str, Any]
    context_snapshot: Dict[str, Any]
    step_results: Dict[str, StepResult]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    workflow_id: str
    step_id: str
    requested_at: datetime
    requester: str
    approvers: List[str]
    title: str
    description: str
    data: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    comments: str = ""
    expires_at: Optional[datetime] = None


@dataclass
class Notification:
    """Workflow notification"""
    notification_id: str
    workflow_id: str
    step_id: str
    notification_type: NotificationType
    title: str
    message: str
    recipients: List[str]
    sent_at: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution"""
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    total_execution_time_ms: float = 0
    avg_step_time_ms: float = 0
    retry_count: int = 0
    checkpoint_count: int = 0
    rollback_count: int = 0


@dataclass
class TimeEstimate:
    """Time estimation for workflow completion"""
    estimated_total_seconds: float
    estimated_remaining_seconds: float
    estimated_completion_time: datetime
    confidence: float  # 0-1
    based_on_steps: int


@dataclass
class ProgressInfo:
    """Progress information for workflow"""
    workflow_id: str
    current_step: str
    current_step_name: str
    total_steps: int
    completed_steps: int
    progress_percent: float
    status: WorkflowStatus
    estimated_time_remaining: Optional[float] = None
    current_step_progress: float = 0


@dataclass
class BranchRule:
    """Rule for conditional branching"""
    rule_id: str
    condition: BranchCondition
    field: str
    value: Any
    target_step: str
    priority: int = 0
    custom_evaluator: Optional[Callable[[Dict[str, Any]], bool]] = None


@dataclass
class WorkflowTemplate:
    """Template for creating workflows"""
    template_id: str
    name: str
    description: str
    version: str
    steps: List[StepDefinition]
    created_at: datetime
    created_by: str
    tags: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowInstance:
    """Instance of a running workflow"""
    workflow_id: str
    template_id: Optional[str]
    name: str
    status: WorkflowStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    checkpoints: List[str] = field(default_factory=list)
    metrics: WorkflowMetrics = field(default_factory=WorkflowMetrics)
    error: Optional[str] = None


@dataclass
class WorkflowLog:
    """Log entry for workflow"""
    log_id: str
    workflow_id: str
    step_id: Optional[str]
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR, DEBUG
    message: str
    data: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Feature 15: Workflow Logging
# ============================================================================

class WorkflowLogger:
    """Centralized logging for workflows"""
    
    def __init__(self, max_logs: int = 10000):
        self.max_logs = max_logs
        self.logs: List[WorkflowLog] = []
        self._lock = RLock()
        self._log_handlers: List[Callable[[WorkflowLog], None]] = []
    
    def log(self, workflow_id: str, level: str, message: str,
            step_id: str = None, data: Dict[str, Any] = None):
        """Add a log entry"""
        log_entry = WorkflowLog(
            log_id=f"LOG_{uuid.uuid4().hex[:12].upper()}",
            workflow_id=workflow_id,
            step_id=step_id,
            timestamp=datetime.now(),
            level=level,
            message=message,
            data=data or {}
        )
        
        with self._lock:
            self.logs.append(log_entry)
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
        
        # Notify handlers
        for handler in self._log_handlers:
            try:
                handler(log_entry)
            except Exception:
                pass
        
        # Also log to standard logger
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{workflow_id}] {message}")
    
    def info(self, workflow_id: str, message: str, step_id: str = None, data: Dict = None):
        self.log(workflow_id, "INFO", message, step_id, data)
    
    def warning(self, workflow_id: str, message: str, step_id: str = None, data: Dict = None):
        self.log(workflow_id, "WARNING", message, step_id, data)
    
    def error(self, workflow_id: str, message: str, step_id: str = None, data: Dict = None):
        self.log(workflow_id, "ERROR", message, step_id, data)
    
    def debug(self, workflow_id: str, message: str, step_id: str = None, data: Dict = None):
        self.log(workflow_id, "DEBUG", message, step_id, data)
    
    def get_logs(self, workflow_id: str = None, step_id: str = None,
                 level: str = None, limit: int = 100) -> List[WorkflowLog]:
        """Get filtered logs"""
        with self._lock:
            filtered = self.logs.copy()
        
        if workflow_id:
            filtered = [l for l in filtered if l.workflow_id == workflow_id]
        if step_id:
            filtered = [l for l in filtered if l.step_id == step_id]
        if level:
            filtered = [l for l in filtered if l.level == level]
        
        return filtered[-limit:]
    
    def add_handler(self, handler: Callable[[WorkflowLog], None]):
        """Add log handler"""
        self._log_handlers.append(handler)
    
    def clear(self, workflow_id: str = None):
        """Clear logs"""
        with self._lock:
            if workflow_id:
                self.logs = [l for l in self.logs if l.workflow_id != workflow_id]
            else:
                self.logs.clear()


# ============================================================================
# Feature 16: Workflow Metrics
# ============================================================================

class WorkflowMetricsCollector:
    """Collects and aggregates workflow metrics"""
    
    def __init__(self):
        self._lock = RLock()
        self._workflow_metrics: Dict[str, WorkflowMetrics] = {}
        self._step_times: Dict[str, List[float]] = defaultdict(list)
        self._global_metrics = {
            'total_workflows': 0,
            'completed_workflows': 0,
            'failed_workflows': 0,
            'total_steps_executed': 0,
            'total_execution_time': 0,
            'avg_workflow_time': 0,
            'success_rate': 0
        }
    
    def start_workflow(self, workflow_id: str, total_steps: int):
        """Record workflow start"""
        with self._lock:
            self._workflow_metrics[workflow_id] = WorkflowMetrics(total_steps=total_steps)
            self._global_metrics['total_workflows'] += 1
    
    def record_step_completion(self, workflow_id: str, step_id: str,
                               execution_time_ms: float, success: bool):
        """Record step completion"""
        with self._lock:
            if workflow_id in self._workflow_metrics:
                metrics = self._workflow_metrics[workflow_id]
                if success:
                    metrics.completed_steps += 1
                else:
                    metrics.failed_steps += 1
                metrics.total_execution_time_ms += execution_time_ms
                
                # Update average
                total = metrics.completed_steps + metrics.failed_steps
                if total > 0:
                    metrics.avg_step_time_ms = metrics.total_execution_time_ms / total
            
            # Track step times for estimation
            self._step_times[step_id].append(execution_time_ms)
            self._global_metrics['total_steps_executed'] += 1
            self._global_metrics['total_execution_time'] += execution_time_ms
    
    def record_step_skip(self, workflow_id: str):
        """Record skipped step"""
        with self._lock:
            if workflow_id in self._workflow_metrics:
                self._workflow_metrics[workflow_id].skipped_steps += 1
    
    def record_retry(self, workflow_id: str):
        """Record retry attempt"""
        with self._lock:
            if workflow_id in self._workflow_metrics:
                self._workflow_metrics[workflow_id].retry_count += 1
    
    def record_checkpoint(self, workflow_id: str):
        """Record checkpoint creation"""
        with self._lock:
            if workflow_id in self._workflow_metrics:
                self._workflow_metrics[workflow_id].checkpoint_count += 1
    
    def record_rollback(self, workflow_id: str):
        """Record rollback"""
        with self._lock:
            if workflow_id in self._workflow_metrics:
                self._workflow_metrics[workflow_id].rollback_count += 1
    
    def complete_workflow(self, workflow_id: str, success: bool):
        """Record workflow completion"""
        with self._lock:
            if success:
                self._global_metrics['completed_workflows'] += 1
            else:
                self._global_metrics['failed_workflows'] += 1
            
            # Update success rate
            total = self._global_metrics['completed_workflows'] + self._global_metrics['failed_workflows']
            if total > 0:
                self._global_metrics['success_rate'] = self._global_metrics['completed_workflows'] / total
            
            # Update average workflow time
            if workflow_id in self._workflow_metrics:
                self._global_metrics['avg_workflow_time'] = (
                    self._global_metrics['total_execution_time'] / total
                ) if total > 0 else 0
    
    def get_workflow_metrics(self, workflow_id: str) -> Optional[WorkflowMetrics]:
        """Get metrics for specific workflow"""
        with self._lock:
            return self._workflow_metrics.get(workflow_id)
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global metrics"""
        with self._lock:
            return self._global_metrics.copy()
    
    def get_step_avg_time(self, step_id: str) -> float:
        """Get average execution time for a step"""
        with self._lock:
            times = self._step_times.get(step_id, [])
            return sum(times) / len(times) if times else 0


# ============================================================================
# Feature 9: Time Estimation
# ============================================================================

class TimeEstimator:
    """Estimates time for workflow completion"""
    
    def __init__(self, metrics_collector: WorkflowMetricsCollector):
        self.metrics = metrics_collector
        self._default_step_time_ms = 5000  # 5 seconds default
    
    def estimate_step_time(self, step_id: str, step_def: StepDefinition) -> float:
        """Estimate time for a single step in milliseconds"""
        # Check historical data
        avg_time = self.metrics.get_step_avg_time(step_id)
        if avg_time > 0:
            return avg_time
        
        # Use step timeout as upper bound estimate
        if step_def.timeout_seconds > 0:
            return step_def.timeout_seconds * 1000 * 0.2  # Assume 20% of timeout
        
        return self._default_step_time_ms
    
    def estimate_workflow(self, workflow: WorkflowInstance,
                          steps: List[StepDefinition]) -> TimeEstimate:
        """Estimate remaining time for workflow"""
        completed_step_ids = set(workflow.step_results.keys())
        remaining_steps = [s for s in steps if s.step_id not in completed_step_ids]
        
        # Calculate estimated remaining time
        estimated_remaining_ms = sum(
            self.estimate_step_time(s.step_id, s) for s in remaining_steps
        )
        
        # Calculate total estimated time
        actual_time = workflow.metrics.total_execution_time_ms
        total_estimated = actual_time + estimated_remaining_ms
        
        # Calculate confidence based on historical data availability
        steps_with_history = sum(
            1 for s in remaining_steps
            if self.metrics.get_step_avg_time(s.step_id) > 0
        )
        confidence = steps_with_history / len(remaining_steps) if remaining_steps else 1.0
        
        return TimeEstimate(
            estimated_total_seconds=total_estimated / 1000,
            estimated_remaining_seconds=estimated_remaining_ms / 1000,
            estimated_completion_time=datetime.now() + timedelta(milliseconds=estimated_remaining_ms),
            confidence=confidence,
            based_on_steps=len(remaining_steps)
        )


# ============================================================================
# Feature 8: Progress Tracking
# ============================================================================

class ProgressTracker:
    """Tracks progress of workflow execution"""
    
    def __init__(self):
        self._lock = RLock()
        self._progress: Dict[str, ProgressInfo] = {}
        self._callbacks: Dict[str, List[Callable[[ProgressInfo], None]]] = defaultdict(list)
    
    def init_workflow(self, workflow: WorkflowInstance, total_steps: int):
        """Initialize progress tracking for workflow"""
        with self._lock:
            self._progress[workflow.workflow_id] = ProgressInfo(
                workflow_id=workflow.workflow_id,
                current_step="",
                current_step_name="Initializing",
                total_steps=total_steps,
                completed_steps=0,
                progress_percent=0,
                status=workflow.status
            )
    
    def update_progress(self, workflow_id: str, step_id: str, step_name: str,
                        completed_steps: int, status: WorkflowStatus,
                        step_progress: float = 0, time_remaining: float = None):
        """Update workflow progress"""
        with self._lock:
            if workflow_id in self._progress:
                info = self._progress[workflow_id]
                info.current_step = step_id
                info.current_step_name = step_name
                info.completed_steps = completed_steps
                info.progress_percent = (completed_steps / info.total_steps * 100) if info.total_steps > 0 else 0
                info.status = status
                info.current_step_progress = step_progress
                info.estimated_time_remaining = time_remaining
                
                # Notify callbacks
                callbacks = self._callbacks.get(workflow_id, [])
        
        for callback in callbacks:
            try:
                callback(info)
            except Exception:
                pass
    
    def get_progress(self, workflow_id: str) -> Optional[ProgressInfo]:
        """Get current progress"""
        with self._lock:
            return self._progress.get(workflow_id)
    
    def subscribe(self, workflow_id: str, callback: Callable[[ProgressInfo], None]):
        """Subscribe to progress updates"""
        with self._lock:
            self._callbacks[workflow_id].append(callback)
    
    def unsubscribe(self, workflow_id: str, callback: Callable[[ProgressInfo], None]):
        """Unsubscribe from progress updates"""
        with self._lock:
            if workflow_id in self._callbacks:
                if callback in self._callbacks[workflow_id]:
                    self._callbacks[workflow_id].remove(callback)
    
    def complete_workflow(self, workflow_id: str, status: WorkflowStatus):
        """Mark workflow as complete"""
        with self._lock:
            if workflow_id in self._progress:
                info = self._progress[workflow_id]
                info.status = status
                info.progress_percent = 100 if status == WorkflowStatus.COMPLETED else info.progress_percent
                info.estimated_time_remaining = 0


# ============================================================================
# Feature 4: Checkpoint System
# ============================================================================

class CheckpointManager:
    """Manages workflow checkpoints for recovery"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path
        self._lock = RLock()
        self._checkpoints: Dict[str, List[Checkpoint]] = defaultdict(list)
    
    def create_checkpoint(self, workflow: WorkflowInstance, step_id: str,
                          context: Dict[str, Any]) -> Checkpoint:
        """Create a checkpoint"""
        checkpoint = Checkpoint(
            checkpoint_id=f"CP_{uuid.uuid4().hex[:12].upper()}",
            workflow_id=workflow.workflow_id,
            step_id=step_id,
            created_at=datetime.now(),
            state_snapshot={
                'status': workflow.status.value,
                'current_step': workflow.current_step,
                'started_at': workflow.started_at.isoformat() if workflow.started_at else None
            },
            context_snapshot=copy.deepcopy(context),
            step_results={k: self._serialize_result(v) for k, v in workflow.step_results.items()}
        )
        
        with self._lock:
            self._checkpoints[workflow.workflow_id].append(checkpoint)
            workflow.checkpoints.append(checkpoint.checkpoint_id)
        
        logger.info(f"Checkpoint created: {checkpoint.checkpoint_id} for workflow {workflow.workflow_id}")
        return checkpoint
    
    def _serialize_result(self, result: StepResult) -> StepResult:
        """Create a serializable copy of step result"""
        return StepResult(
            step_id=result.step_id,
            status=result.status,
            started_at=result.started_at,
            completed_at=result.completed_at,
            output=result.output if isinstance(result.output, (dict, list, str, int, float, bool, type(None))) else str(result.output),
            error=result.error,
            retry_count=result.retry_count,
            execution_time_ms=result.execution_time_ms,
            metadata=result.metadata
        )
    
    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        """Get the latest checkpoint for a workflow"""
        with self._lock:
            checkpoints = self._checkpoints.get(workflow_id, [])
            return checkpoints[-1] if checkpoints else None
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a specific checkpoint by ID"""
        with self._lock:
            for checkpoints in self._checkpoints.values():
                for cp in checkpoints:
                    if cp.checkpoint_id == checkpoint_id:
                        return cp
        return None
    
    def get_checkpoints(self, workflow_id: str) -> List[Checkpoint]:
        """Get all checkpoints for a workflow"""
        with self._lock:
            return self._checkpoints.get(workflow_id, []).copy()
    
    def delete_checkpoints(self, workflow_id: str):
        """Delete all checkpoints for a workflow"""
        with self._lock:
            if workflow_id in self._checkpoints:
                del self._checkpoints[workflow_id]


# ============================================================================
# Feature 5: Rollback Mechanism
# ============================================================================

class RollbackManager:
    """Manages rollback operations for workflows"""
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        self.checkpoint_manager = checkpoint_manager
        self._rollback_handlers: Dict[str, Callable[[str, Dict[str, Any]], None]] = {}
    
    def register_rollback_handler(self, step_id: str,
                                   handler: Callable[[str, Dict[str, Any]], None]):
        """Register a rollback handler for a step"""
        self._rollback_handlers[step_id] = handler
    
    def rollback_to_checkpoint(self, workflow: WorkflowInstance,
                                checkpoint_id: str = None) -> bool:
        """Rollback workflow to a checkpoint"""
        # Get checkpoint
        if checkpoint_id:
            checkpoint = self.checkpoint_manager.get_checkpoint(checkpoint_id)
        else:
            checkpoint = self.checkpoint_manager.get_latest_checkpoint(workflow.workflow_id)
        
        if not checkpoint:
            logger.error(f"No checkpoint found for rollback")
            return False
        
        # Execute rollback handlers for steps after checkpoint
        steps_to_rollback = [
            step_id for step_id in workflow.step_results.keys()
            if step_id not in checkpoint.step_results
        ]
        
        for step_id in reversed(steps_to_rollback):
            if step_id in self._rollback_handlers:
                try:
                    result = workflow.step_results.get(step_id)
                    self._rollback_handlers[step_id](step_id, result.output if result else {})
                    logger.info(f"Rolled back step: {step_id}")
                except Exception as e:
                    logger.error(f"Rollback handler failed for {step_id}: {e}")
        
        # Restore state
        workflow.status = WorkflowStatus(checkpoint.state_snapshot['status'])
        workflow.current_step = checkpoint.state_snapshot['current_step']
        workflow.context = copy.deepcopy(checkpoint.context_snapshot)
        workflow.step_results = {k: v for k, v in checkpoint.step_results.items()}
        
        logger.info(f"Rolled back workflow {workflow.workflow_id} to checkpoint {checkpoint.checkpoint_id}")
        return True
    
    def can_rollback(self, workflow: WorkflowInstance) -> bool:
        """Check if workflow can be rolled back"""
        checkpoints = self.checkpoint_manager.get_checkpoints(workflow.workflow_id)
        return len(checkpoints) > 0


# ============================================================================
# Feature 11: Conditional Branching
# ============================================================================

class ConditionalBrancher:
    """Handles conditional branching in workflows"""
    
    def __init__(self):
        self._rules: Dict[str, List[BranchRule]] = defaultdict(list)
    
    def add_rule(self, step_id: str, rule: BranchRule):
        """Add a branching rule for a step"""
        self._rules[step_id].append(rule)
        # Sort by priority
        self._rules[step_id].sort(key=lambda r: r.priority)
    
    def evaluate(self, step_id: str, context: Dict[str, Any]) -> Optional[str]:
        """Evaluate branching rules and return target step"""
        rules = self._rules.get(step_id, [])
        
        for rule in rules:
            if self._evaluate_rule(rule, context):
                return rule.target_step
        
        return None
    
    def _evaluate_rule(self, rule: BranchRule, context: Dict[str, Any]) -> bool:
        """Evaluate a single branching rule"""
        if rule.condition == BranchCondition.CUSTOM:
            if rule.custom_evaluator:
                return rule.custom_evaluator(context)
            return False
        
        # Get field value from context
        value = self._get_nested_value(context, rule.field)
        
        if rule.condition == BranchCondition.EQUALS:
            return value == rule.value
        elif rule.condition == BranchCondition.NOT_EQUALS:
            return value != rule.value
        elif rule.condition == BranchCondition.GREATER_THAN:
            return value is not None and value > rule.value
        elif rule.condition == BranchCondition.LESS_THAN:
            return value is not None and value < rule.value
        elif rule.condition == BranchCondition.CONTAINS:
            return rule.value in value if value else False
        elif rule.condition == BranchCondition.NOT_CONTAINS:
            return rule.value not in value if value else True
        elif rule.condition == BranchCondition.REGEX_MATCH:
            import re
            return bool(re.match(rule.value, str(value))) if value else False
        
        return False
    
    def _get_nested_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = field.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def get_rules(self, step_id: str) -> List[BranchRule]:
        """Get all rules for a step"""
        return self._rules.get(step_id, [])


# ============================================================================
# Feature 12: Human-in-the-Loop Points
# ============================================================================

class HumanTaskManager:
    """Manages human-in-the-loop tasks"""
    
    def __init__(self):
        self._lock = RLock()
        self._pending_tasks: Dict[str, Dict[str, Any]] = {}
        self._task_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self._task_events: Dict[str, Event] = {}
    
    def create_human_task(self, workflow_id: str, step_id: str,
                          task_type: str, data: Dict[str, Any],
                          timeout_seconds: int = None) -> str:
        """Create a human task and wait for completion"""
        task_id = f"HTASK_{uuid.uuid4().hex[:12].upper()}"
        event = Event()
        
        with self._lock:
            self._pending_tasks[task_id] = {
                'task_id': task_id,
                'workflow_id': workflow_id,
                'step_id': step_id,
                'task_type': task_type,
                'data': data,
                'created_at': datetime.now(),
                'status': 'pending',
                'result': None
            }
            self._task_events[task_id] = event
        
        logger.info(f"Human task created: {task_id} for workflow {workflow_id}")
        return task_id
    
    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Complete a human task with result"""
        with self._lock:
            if task_id not in self._pending_tasks:
                return False
            
            self._pending_tasks[task_id]['status'] = 'completed'
            self._pending_tasks[task_id]['result'] = result
            self._pending_tasks[task_id]['completed_at'] = datetime.now()
            
            # Signal waiting thread
            if task_id in self._task_events:
                self._task_events[task_id].set()
        
        logger.info(f"Human task completed: {task_id}")
        return True
    
    def wait_for_task(self, task_id: str, timeout: float = None) -> Optional[Dict[str, Any]]:
        """Wait for a human task to complete"""
        event = self._task_events.get(task_id)
        if not event:
            return None
        
        completed = event.wait(timeout=timeout)
        if not completed:
            return None
        
        with self._lock:
            task = self._pending_tasks.get(task_id, {})
            return task.get('result')
    
    def get_pending_tasks(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get pending human tasks"""
        with self._lock:
            tasks = list(self._pending_tasks.values())
        
        if workflow_id:
            tasks = [t for t in tasks if t['workflow_id'] == workflow_id and t['status'] == 'pending']
        else:
            tasks = [t for t in tasks if t['status'] == 'pending']
        
        return tasks
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending human task"""
        with self._lock:
            if task_id in self._pending_tasks:
                self._pending_tasks[task_id]['status'] = 'cancelled'
                if task_id in self._task_events:
                    self._task_events[task_id].set()
                return True
        return False


# ============================================================================
# Feature 13: Approval Workflows
# ============================================================================

class ApprovalManager:
    """Manages approval workflows"""
    
    def __init__(self):
        self._lock = RLock()
        self._requests: Dict[str, ApprovalRequest] = {}
        self._approval_events: Dict[str, Event] = {}
        self._approval_callbacks: List[Callable[[ApprovalRequest], None]] = []
    
    def request_approval(self, workflow_id: str, step_id: str,
                         requester: str, approvers: List[str],
                         title: str, description: str,
                         data: Dict[str, Any],
                         expires_in_hours: int = 24) -> ApprovalRequest:
        """Create an approval request"""
        request = ApprovalRequest(
            request_id=f"APR_{uuid.uuid4().hex[:12].upper()}",
            workflow_id=workflow_id,
            step_id=step_id,
            requested_at=datetime.now(),
            requester=requester,
            approvers=approvers,
            title=title,
            description=description,
            data=data,
            expires_at=datetime.now() + timedelta(hours=expires_in_hours) if expires_in_hours else None
        )
        
        event = Event()
        
        with self._lock:
            self._requests[request.request_id] = request
            self._approval_events[request.request_id] = event
        
        # Notify callbacks
        for callback in self._approval_callbacks:
            try:
                callback(request)
            except Exception:
                pass
        
        logger.info(f"Approval requested: {request.request_id} for workflow {workflow_id}")
        return request
    
    def approve(self, request_id: str, approver: str, comments: str = "") -> bool:
        """Approve a request"""
        with self._lock:
            request = self._requests.get(request_id)
            if not request:
                return False
            
            if request.status != ApprovalStatus.PENDING:
                return False
            
            if approver not in request.approvers:
                return False
            
            request.status = ApprovalStatus.APPROVED
            request.approved_by = approver
            request.approved_at = datetime.now()
            request.comments = comments
            
            if request_id in self._approval_events:
                self._approval_events[request_id].set()
        
        logger.info(f"Approval granted: {request_id} by {approver}")
        return True
    
    def reject(self, request_id: str, approver: str, comments: str = "") -> bool:
        """Reject a request"""
        with self._lock:
            request = self._requests.get(request_id)
            if not request:
                return False
            
            if request.status != ApprovalStatus.PENDING:
                return False
            
            if approver not in request.approvers:
                return False
            
            request.status = ApprovalStatus.REJECTED
            request.approved_by = approver
            request.approved_at = datetime.now()
            request.comments = comments
            
            if request_id in self._approval_events:
                self._approval_events[request_id].set()
        
        logger.info(f"Approval rejected: {request_id} by {approver}")
        return True
    
    def wait_for_approval(self, request_id: str, timeout: float = None) -> Optional[ApprovalStatus]:
        """Wait for approval decision"""
        event = self._approval_events.get(request_id)
        if not event:
            return None
        
        completed = event.wait(timeout=timeout)
        if not completed:
            # Check for expiry
            with self._lock:
                request = self._requests.get(request_id)
                if request and request.expires_at and datetime.now() > request.expires_at:
                    request.status = ApprovalStatus.EXPIRED
            return ApprovalStatus.EXPIRED
        
        with self._lock:
            request = self._requests.get(request_id)
            return request.status if request else None
    
    def get_pending_requests(self, approver: str = None) -> List[ApprovalRequest]:
        """Get pending approval requests"""
        with self._lock:
            requests = [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]
        
        if approver:
            requests = [r for r in requests if approver in r.approvers]
        
        return requests
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID"""
        with self._lock:
            return self._requests.get(request_id)
    
    def add_callback(self, callback: Callable[[ApprovalRequest], None]):
        """Add callback for new approval requests"""
        self._approval_callbacks.append(callback)


# ============================================================================
# Feature 14: Notification Triggers
# ============================================================================

class NotificationManager:
    """Manages workflow notifications"""
    
    def __init__(self):
        self._lock = RLock()
        self._notifications: List[Notification] = []
        self._handlers: Dict[NotificationType, List[Callable[[Notification], None]]] = defaultdict(list)
        self._triggers: List[Dict[str, Any]] = []
    
    def send(self, workflow_id: str, step_id: str,
             notification_type: NotificationType,
             title: str, message: str,
             recipients: List[str],
             data: Dict[str, Any] = None) -> Notification:
        """Send a notification"""
        notification = Notification(
            notification_id=f"NOTIF_{uuid.uuid4().hex[:12].upper()}",
            workflow_id=workflow_id,
            step_id=step_id,
            notification_type=notification_type,
            title=title,
            message=message,
            recipients=recipients,
            sent_at=datetime.now(),
            data=data or {}
        )
        
        with self._lock:
            self._notifications.append(notification)
        
        # Execute handlers
        handlers = self._handlers.get(notification_type, []) + self._handlers.get(None, [])
        for handler in handlers:
            try:
                handler(notification)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
        
        logger.info(f"Notification sent: {notification.notification_id} to {recipients}")
        return notification
    
    def add_handler(self, handler: Callable[[Notification], None],
                    notification_type: NotificationType = None):
        """Add notification handler"""
        self._handlers[notification_type].append(handler)
    
    def add_trigger(self, event: str, notification_type: NotificationType,
                    title_template: str, message_template: str,
                    recipients: List[str], condition: Callable[[Dict], bool] = None):
        """Add automatic notification trigger"""
        self._triggers.append({
            'event': event,
            'notification_type': notification_type,
            'title_template': title_template,
            'message_template': message_template,
            'recipients': recipients,
            'condition': condition
        })
    
    def trigger_event(self, event: str, workflow_id: str, step_id: str,
                      context: Dict[str, Any]):
        """Trigger notifications based on event"""
        for trigger in self._triggers:
            if trigger['event'] != event:
                continue
            
            # Check condition
            if trigger['condition'] and not trigger['condition'](context):
                continue
            
            # Format message
            title = trigger['title_template'].format(**context)
            message = trigger['message_template'].format(**context)
            
            self.send(
                workflow_id, step_id,
                trigger['notification_type'],
                title, message,
                trigger['recipients'],
                context
            )
    
    def acknowledge(self, notification_id: str) -> bool:
        """Acknowledge a notification"""
        with self._lock:
            for notification in self._notifications:
                if notification.notification_id == notification_id:
                    notification.acknowledged = True
                    return True
        return False
    
    def get_notifications(self, workflow_id: str = None,
                          acknowledged: bool = None) -> List[Notification]:
        """Get notifications"""
        with self._lock:
            notifications = self._notifications.copy()
        
        if workflow_id:
            notifications = [n for n in notifications if n.workflow_id == workflow_id]
        if acknowledged is not None:
            notifications = [n for n in notifications if n.acknowledged == acknowledged]
        
        return notifications


# ============================================================================
# Feature 17: Success/Failure Handlers
# ============================================================================

class ResultHandler:
    """Handles workflow success and failure outcomes"""
    
    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager
        self._success_handlers: List[Callable[[WorkflowInstance], None]] = []
        self._failure_handlers: List[Callable[[WorkflowInstance, str], None]] = []
        self._step_success_handlers: Dict[str, List[Callable[[StepResult], None]]] = defaultdict(list)
        self._step_failure_handlers: Dict[str, List[Callable[[StepResult, str], None]]] = defaultdict(list)
    
    def on_workflow_success(self, handler: Callable[[WorkflowInstance], None]):
        """Register workflow success handler"""
        self._success_handlers.append(handler)
    
    def on_workflow_failure(self, handler: Callable[[WorkflowInstance, str], None]):
        """Register workflow failure handler"""
        self._failure_handlers.append(handler)
    
    def on_step_success(self, step_id: str, handler: Callable[[StepResult], None]):
        """Register step success handler"""
        self._step_success_handlers[step_id].append(handler)
    
    def on_step_failure(self, step_id: str, handler: Callable[[StepResult, str], None]):
        """Register step failure handler"""
        self._step_failure_handlers[step_id].append(handler)
    
    def handle_workflow_success(self, workflow: WorkflowInstance):
        """Handle successful workflow completion"""
        logger.info(f"Workflow completed successfully: {workflow.workflow_id}")
        
        # Send success notification
        self.notification_manager.send(
            workflow.workflow_id, "",
            NotificationType.SUCCESS,
            "Workflow Completed",
            f"Workflow {workflow.name} completed successfully",
            [],  # Recipients would be set by configuration
            {'workflow_id': workflow.workflow_id}
        )
        
        # Execute handlers
        for handler in self._success_handlers:
            try:
                handler(workflow)
            except Exception as e:
                logger.error(f"Success handler error: {e}")
    
    def handle_workflow_failure(self, workflow: WorkflowInstance, error: str):
        """Handle workflow failure"""
        logger.error(f"Workflow failed: {workflow.workflow_id} - {error}")
        
        # Send failure notification
        self.notification_manager.send(
            workflow.workflow_id, workflow.current_step or "",
            NotificationType.ERROR,
            "Workflow Failed",
            f"Workflow {workflow.name} failed: {error}",
            [],
            {'workflow_id': workflow.workflow_id, 'error': error}
        )
        
        # Execute handlers
        for handler in self._failure_handlers:
            try:
                handler(workflow, error)
            except Exception as e:
                logger.error(f"Failure handler error: {e}")
    
    def handle_step_success(self, step_id: str, result: StepResult):
        """Handle successful step completion"""
        handlers = self._step_success_handlers.get(step_id, [])
        for handler in handlers:
            try:
                handler(result)
            except Exception as e:
                logger.error(f"Step success handler error: {e}")
    
    def handle_step_failure(self, step_id: str, result: StepResult, error: str):
        """Handle step failure"""
        handlers = self._step_failure_handlers.get(step_id, [])
        for handler in handlers:
            try:
                handler(result, error)
            except Exception as e:
                logger.error(f"Step failure handler error: {e}")


# ============================================================================
# Feature 18: Workflow Retry Logic
# ============================================================================

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_backoff: bool = True
    backoff_multiplier: float = 2.0
    retryable_errors: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    jitter: bool = True


class WorkflowRetryManager:
    """Manages retry logic for workflows"""
    
    def __init__(self, default_config: RetryConfig = None):
        self.default_config = default_config or RetryConfig()
        self._step_configs: Dict[str, RetryConfig] = {}
        self._retry_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def set_step_config(self, step_id: str, config: RetryConfig):
        """Set retry configuration for specific step"""
        self._step_configs[step_id] = config
    
    def get_config(self, step_id: str) -> RetryConfig:
        """Get retry configuration for step"""
        return self._step_configs.get(step_id, self.default_config)
    
    def should_retry(self, step_id: str, attempt: int, error: Exception) -> bool:
        """Determine if step should be retried"""
        config = self.get_config(step_id)
        
        if attempt >= config.max_retries:
            return False
        
        # Check if error is retryable
        for error_type in config.retryable_errors:
            if isinstance(error, error_type):
                return True
        
        return False
    
    def get_delay(self, step_id: str, attempt: int) -> float:
        """Calculate delay before next retry"""
        config = self.get_config(step_id)
        
        if config.exponential_backoff:
            delay = config.base_delay_seconds * (config.backoff_multiplier ** attempt)
        else:
            delay = config.base_delay_seconds
        
        delay = min(delay, config.max_delay_seconds)
        
        # Add jitter
        if config.jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay
    
    def record_retry(self, workflow_id: str, step_id: str, attempt: int,
                     error: str, delay: float):
        """Record retry attempt"""
        self._retry_history[workflow_id].append({
            'step_id': step_id,
            'attempt': attempt,
            'error': error,
            'delay': delay,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_retry_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get retry history for workflow"""
        return self._retry_history.get(workflow_id, [])
    
    def execute_with_retry(self, step_id: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        config = self.get_config(step_id)
        last_error = None
        
        for attempt in range(config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if not self.should_retry(step_id, attempt, e):
                    raise
                
                delay = self.get_delay(step_id, attempt)
                logger.warning(f"Step {step_id} attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                time.sleep(delay)
        
        raise last_error


# ============================================================================
# Feature 6: Parallel Processing Support
# ============================================================================

class ParallelExecutor:
    """Executes steps in parallel when dependencies allow"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
    
    def start(self):
        """Start the executor"""
        if not self._executor:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
    
    def stop(self):
        """Stop the executor"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
    
    def execute_parallel(self, tasks: List[Tuple[str, Callable, tuple, dict]],
                         timeout: float = None) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel
        
        Args:
            tasks: List of (task_id, callable, args, kwargs)
            timeout: Overall timeout in seconds
        
        Returns:
            Dict mapping task_id to result or error
        """
        if not self._executor:
            self.start()
        
        futures: Dict[Future, str] = {}
        results: Dict[str, Any] = {}
        
        # Submit all tasks
        for task_id, func, args, kwargs in tasks:
            future = self._executor.submit(func, *args, **kwargs)
            futures[future] = task_id
        
        # Collect results
        try:
            for future in as_completed(futures.keys(), timeout=timeout):
                task_id = futures[future]
                try:
                    results[task_id] = {'success': True, 'result': future.result()}
                except Exception as e:
                    results[task_id] = {'success': False, 'error': str(e)}
        except FutureTimeoutError:
            # Cancel remaining futures
            for future, task_id in futures.items():
                if task_id not in results:
                    future.cancel()
                    results[task_id] = {'success': False, 'error': 'Timeout'}
        
        return results
    
    def find_parallel_groups(self, steps: List[StepDefinition],
                              completed: Set[str]) -> List[List[StepDefinition]]:
        """Find groups of steps that can be executed in parallel"""
        groups = []
        remaining = [s for s in steps if s.step_id not in completed]
        
        while remaining:
            # Find steps with all dependencies satisfied
            ready = []
            for step in remaining:
                deps_satisfied = all(d in completed for d in step.dependencies)
                if deps_satisfied:
                    ready.append(step)
            
            if not ready:
                break
            
            groups.append(ready)
            completed = completed | {s.step_id for s in ready}
            remaining = [s for s in remaining if s.step_id not in completed]
        
        return groups


# ============================================================================
# Feature 7: Workflow Visualization
# ============================================================================

class WorkflowVisualizer:
    """Generates visual representations of workflows"""
    
    def __init__(self):
        self._status_colors = {
            StepStatus.PENDING: "#gray",
            StepStatus.READY: "#blue",
            StepStatus.RUNNING: "#yellow",
            StepStatus.COMPLETED: "#green",
            StepStatus.FAILED: "#red",
            StepStatus.SKIPPED: "#lightgray",
            StepStatus.WAITING: "#orange",
            StepStatus.ROLLED_BACK: "#purple"
        }
    
    def generate_mermaid(self, steps: List[StepDefinition],
                          results: Dict[str, StepResult] = None) -> str:
        """Generate Mermaid flowchart diagram"""
        lines = ["graph TD"]
        
        for step in steps:
            # Determine node shape based on type
            if step.step_type == StepType.DECISION:
                shape = f"{{{step.name}}}"
            elif step.step_type == StepType.APPROVAL:
                shape = f"[/{step.name}/]"
            elif step.step_type == StepType.PARALLEL:
                shape = f"[[{step.name}]]"
            else:
                shape = f"[{step.name}]"
            
            # Add status styling
            status = StepStatus.PENDING
            if results and step.step_id in results:
                status = results[step.step_id].status
            
            color = self._status_colors.get(status, "#gray")
            lines.append(f"    {step.step_id}{shape}")
            lines.append(f"    style {step.step_id} fill:{color}")
            
            # Add edges for dependencies
            for dep in step.dependencies:
                lines.append(f"    {dep} --> {step.step_id}")
        
        return "\n".join(lines)
    
    def generate_text_tree(self, steps: List[StepDefinition],
                            results: Dict[str, StepResult] = None,
                            current_step: str = None) -> str:
        """Generate text-based tree visualization"""
        lines = ["Workflow Steps:"]
        lines.append("=" * 50)
        
        for i, step in enumerate(steps):
            # Status indicator
            if results and step.step_id in results:
                status = results[step.step_id].status
                if status == StepStatus.COMPLETED:
                    indicator = "✓"
                elif status == StepStatus.FAILED:
                    indicator = "✗"
                elif status == StepStatus.RUNNING:
                    indicator = "▶"
                elif status == StepStatus.SKIPPED:
                    indicator = "⊘"
                else:
                    indicator = "○"
            else:
                indicator = "○"
            
            # Current step marker
            current = " ←" if step.step_id == current_step else ""
            
            # Type indicator
            type_mark = ""
            if step.step_type == StepType.DECISION:
                type_mark = " [?]"
            elif step.step_type == StepType.APPROVAL:
                type_mark = " [✋]"
            elif step.step_type == StepType.PARALLEL:
                type_mark = " [∥]"
            elif step.step_type == StepType.HUMAN_INPUT:
                type_mark = " [👤]"
            
            lines.append(f"  {indicator} {i+1}. {step.name}{type_mark}{current}")
            
            # Show dependencies
            if step.dependencies:
                deps = ", ".join(step.dependencies)
                lines.append(f"      └─ depends on: {deps}")
        
        lines.append("=" * 50)
        return "\n".join(lines)
    
    def generate_json_graph(self, steps: List[StepDefinition],
                             results: Dict[str, StepResult] = None) -> Dict[str, Any]:
        """Generate JSON representation for UI rendering"""
        nodes = []
        edges = []
        
        for step in steps:
            status = "pending"
            if results and step.step_id in results:
                status = results[step.step_id].status.value
            
            nodes.append({
                'id': step.step_id,
                'name': step.name,
                'type': step.step_type.value,
                'status': status,
                'metadata': step.metadata
            })
            
            for dep in step.dependencies:
                edges.append({
                    'from': dep,
                    'to': step.step_id
                })
        
        return {'nodes': nodes, 'edges': edges}


# ============================================================================
# Feature 10: Workflow Templates
# ============================================================================

class WorkflowTemplateManager:
    """Manages workflow templates"""
    
    def __init__(self):
        self._lock = RLock()
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._builtin_templates = self._create_builtin_templates()
    
    def _create_builtin_templates(self) -> Dict[str, WorkflowTemplate]:
        """Create built-in RFP workflow templates"""
        templates = {}
        
        # Standard RFP Response Template
        templates['rfp_standard'] = WorkflowTemplate(
            template_id='rfp_standard',
            name='Standard RFP Response',
            description='Complete end-to-end RFP response workflow',
            version='1.0.0',
            created_at=datetime.now(),
            created_by='system',
            tags=['rfp', 'standard'],
            steps=[
                StepDefinition(
                    step_id='scan_rfp',
                    name='Scan RFP Sources',
                    step_type=StepType.TASK,
                    is_checkpoint=True
                ),
                StepDefinition(
                    step_id='select_rfp',
                    name='Select Target RFP',
                    step_type=StepType.DECISION,
                    dependencies=['scan_rfp']
                ),
                StepDefinition(
                    step_id='extract_requirements',
                    name='Extract Requirements',
                    step_type=StepType.TASK,
                    dependencies=['select_rfp'],
                    is_checkpoint=True
                ),
                StepDefinition(
                    step_id='technical_analysis',
                    name='Technical Analysis',
                    step_type=StepType.TASK,
                    dependencies=['extract_requirements']
                ),
                StepDefinition(
                    step_id='pricing_calculation',
                    name='Pricing Calculation',
                    step_type=StepType.TASK,
                    dependencies=['technical_analysis']
                ),
                StepDefinition(
                    step_id='review_approval',
                    name='Manager Approval',
                    step_type=StepType.APPROVAL,
                    dependencies=['pricing_calculation'],
                    approval_required=True,
                    approvers=['manager']
                ),
                StepDefinition(
                    step_id='generate_response',
                    name='Generate Response Document',
                    step_type=StepType.TASK,
                    dependencies=['review_approval'],
                    is_checkpoint=True
                ),
                StepDefinition(
                    step_id='final_review',
                    name='Final Review',
                    step_type=StepType.HUMAN_INPUT,
                    dependencies=['generate_response'],
                    is_human_task=True
                ),
                StepDefinition(
                    step_id='submit',
                    name='Submit Response',
                    step_type=StepType.TASK,
                    dependencies=['final_review']
                )
            ]
        )
        
        # Quick RFP Template
        templates['rfp_quick'] = WorkflowTemplate(
            template_id='rfp_quick',
            name='Quick RFP Response',
            description='Streamlined RFP response for simple requirements',
            version='1.0.0',
            created_at=datetime.now(),
            created_by='system',
            tags=['rfp', 'quick'],
            steps=[
                StepDefinition(step_id='analyze', name='Analyze RFP', step_type=StepType.TASK),
                StepDefinition(step_id='match', name='Match Products', step_type=StepType.TASK, dependencies=['analyze']),
                StepDefinition(step_id='price', name='Calculate Price', step_type=StepType.TASK, dependencies=['match']),
                StepDefinition(step_id='generate', name='Generate Response', step_type=StepType.TASK, dependencies=['price'])
            ]
        )
        
        # Parallel RFP Template
        templates['rfp_parallel'] = WorkflowTemplate(
            template_id='rfp_parallel',
            name='Parallel RFP Response',
            description='RFP response with parallel technical and pricing analysis',
            version='1.0.0',
            created_at=datetime.now(),
            created_by='system',
            tags=['rfp', 'parallel'],
            steps=[
                StepDefinition(step_id='init', name='Initialize', step_type=StepType.TASK, is_checkpoint=True),
                StepDefinition(step_id='extract', name='Extract Requirements', step_type=StepType.TASK, dependencies=['init']),
                StepDefinition(step_id='tech', name='Technical Analysis', step_type=StepType.TASK, dependencies=['extract']),
                StepDefinition(step_id='price', name='Pricing Analysis', step_type=StepType.TASK, dependencies=['extract']),
                StepDefinition(step_id='merge', name='Consolidate Results', step_type=StepType.TASK, dependencies=['tech', 'price']),
                StepDefinition(step_id='generate', name='Generate Response', step_type=StepType.TASK, dependencies=['merge'])
            ]
        )
        
        return templates
    
    def register(self, template: WorkflowTemplate):
        """Register a workflow template"""
        with self._lock:
            self._templates[template.template_id] = template
        logger.info(f"Registered workflow template: {template.template_id}")
    
    def get(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a template by ID"""
        with self._lock:
            return self._templates.get(template_id) or self._builtin_templates.get(template_id)
    
    def list_templates(self, tags: List[str] = None) -> List[WorkflowTemplate]:
        """List all templates, optionally filtered by tags"""
        with self._lock:
            all_templates = list(self._builtin_templates.values()) + list(self._templates.values())
        
        if tags:
            all_templates = [t for t in all_templates if any(tag in t.tags for tag in tags)]
        
        return all_templates
    
    def create_instance(self, template_id: str, name: str = None,
                        variables: Dict[str, Any] = None) -> Optional[WorkflowInstance]:
        """Create a workflow instance from template"""
        template = self.get(template_id)
        if not template:
            return None
        
        workflow = WorkflowInstance(
            workflow_id=f"WF_{uuid.uuid4().hex[:12].upper()}",
            template_id=template_id,
            name=name or template.name,
            status=WorkflowStatus.DRAFT,
            created_at=datetime.now(),
            context=variables or {}
        )
        workflow.metrics.total_steps = len(template.steps)
        
        return workflow
    
    def delete(self, template_id: str) -> bool:
        """Delete a template"""
        with self._lock:
            if template_id in self._templates:
                del self._templates[template_id]
                return True
        return False


# ============================================================================
# Feature 2: Workflow State Tracker
# ============================================================================

class WorkflowStateTracker:
    """Tracks the state of workflow execution"""
    
    def __init__(self):
        self._lock = RLock()
        self._workflows: Dict[str, WorkflowInstance] = {}
        self._state_history: Dict[str, List[Tuple[datetime, WorkflowStatus]]] = defaultdict(list)
    
    def register(self, workflow: WorkflowInstance):
        """Register a workflow for tracking"""
        with self._lock:
            self._workflows[workflow.workflow_id] = workflow
            self._state_history[workflow.workflow_id].append((datetime.now(), workflow.status))
    
    def update_status(self, workflow_id: str, status: WorkflowStatus):
        """Update workflow status"""
        with self._lock:
            if workflow_id in self._workflows:
                self._workflows[workflow_id].status = status
                self._state_history[workflow_id].append((datetime.now(), status))
    
    def update_current_step(self, workflow_id: str, step_id: str):
        """Update current step"""
        with self._lock:
            if workflow_id in self._workflows:
                self._workflows[workflow_id].current_step = step_id
    
    def record_step_result(self, workflow_id: str, result: StepResult):
        """Record step execution result"""
        with self._lock:
            if workflow_id in self._workflows:
                self._workflows[workflow_id].step_results[result.step_id] = result
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """Get workflow by ID"""
        with self._lock:
            return self._workflows.get(workflow_id)
    
    def get_all_workflows(self, status: WorkflowStatus = None) -> List[WorkflowInstance]:
        """Get all workflows, optionally filtered by status"""
        with self._lock:
            workflows = list(self._workflows.values())
        
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        return workflows
    
    def get_state_history(self, workflow_id: str) -> List[Tuple[datetime, WorkflowStatus]]:
        """Get state transition history"""
        with self._lock:
            return self._state_history.get(workflow_id, []).copy()
    
    def complete_workflow(self, workflow_id: str, success: bool, error: str = None):
        """Mark workflow as complete"""
        with self._lock:
            if workflow_id in self._workflows:
                workflow = self._workflows[workflow_id]
                workflow.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
                workflow.completed_at = datetime.now()
                if error:
                    workflow.error = error
                self._state_history[workflow_id].append((datetime.now(), workflow.status))


# ============================================================================
# Feature 3: Step-by-Step Execution (Step Executor)
# ============================================================================

class StepExecutor:
    """Executes individual workflow steps"""
    
    def __init__(self, retry_manager: WorkflowRetryManager,
                 metrics_collector: WorkflowMetricsCollector,
                 logger: WorkflowLogger):
        self.retry_manager = retry_manager
        self.metrics = metrics_collector
        self.logger = logger
        self._step_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
    
    def register_handler(self, step_id: str,
                         handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """Register a handler for a step"""
        self._step_handlers[step_id] = handler
    
    def execute(self, step: StepDefinition, context: Dict[str, Any],
                workflow_id: str) -> StepResult:
        """Execute a single step"""
        started_at = datetime.now()
        result = StepResult(
            step_id=step.step_id,
            status=StepStatus.RUNNING,
            started_at=started_at
        )
        
        self.logger.info(workflow_id, f"Executing step: {step.name}", step.step_id)
        
        try:
            # Get handler
            handler = step.handler or self._step_handlers.get(step.step_id)
            if not handler:
                raise ValueError(f"No handler registered for step: {step.step_id}")
            
            # Execute with retry logic
            output = self.retry_manager.execute_with_retry(
                step.step_id,
                handler,
                context
            )
            
            result.status = StepStatus.COMPLETED
            result.output = output
            result.completed_at = datetime.now()
            result.execution_time_ms = (result.completed_at - started_at).total_seconds() * 1000
            
            # Record metrics
            self.metrics.record_step_completion(
                workflow_id, step.step_id,
                result.execution_time_ms, True
            )
            
            self.logger.info(
                workflow_id,
                f"Step completed: {step.name} in {result.execution_time_ms:.2f}ms",
                step.step_id
            )
            
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now()
            result.execution_time_ms = (result.completed_at - started_at).total_seconds() * 1000
            
            self.metrics.record_step_completion(
                workflow_id, step.step_id,
                result.execution_time_ms, False
            )
            
            self.logger.error(
                workflow_id,
                f"Step failed: {step.name} - {e}",
                step.step_id
            )
        
        return result


# ============================================================================
# Feature 19: Workflow Testing Framework
# ============================================================================

class WorkflowTestCase:
    """Base class for workflow test cases"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.setup_handlers: List[Callable] = []
        self.teardown_handlers: List[Callable] = []
    
    def setup(self):
        """Setup test environment"""
        for handler in self.setup_handlers:
            handler()
    
    def teardown(self):
        """Teardown test environment"""
        for handler in self.teardown_handlers:
            handler()
    
    def run(self, engine: 'WorkflowOrchestrationEngine') -> Dict[str, Any]:
        """Run the test case - override in subclasses"""
        raise NotImplementedError


class WorkflowTestResult:
    """Result of a workflow test"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.duration_ms = 0
        self.error: Optional[str] = None
        self.assertions: List[Dict[str, Any]] = []
        self.workflow_id: Optional[str] = None
    
    def add_assertion(self, name: str, passed: bool, message: str = ""):
        """Add an assertion result"""
        self.assertions.append({
            'name': name,
            'passed': passed,
            'message': message
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'passed': self.passed,
            'duration_ms': self.duration_ms,
            'error': self.error,
            'assertions': self.assertions,
            'workflow_id': self.workflow_id
        }


class WorkflowTestRunner:
    """Runs workflow tests"""
    
    def __init__(self, engine: 'WorkflowOrchestrationEngine'):
        self.engine = engine
        self._test_cases: List[WorkflowTestCase] = []
    
    def add_test(self, test_case: WorkflowTestCase):
        """Add a test case"""
        self._test_cases.append(test_case)
    
    def run_all(self) -> List[WorkflowTestResult]:
        """Run all test cases"""
        results = []
        for test_case in self._test_cases:
            result = self.run_test(test_case)
            results.append(result)
        return results
    
    def run_test(self, test_case: WorkflowTestCase) -> WorkflowTestResult:
        """Run a single test case"""
        result = WorkflowTestResult(test_case.name)
        started_at = datetime.now()
        
        try:
            test_case.setup()
            
            test_output = test_case.run(self.engine)
            result.workflow_id = test_output.get('workflow_id')
            
            # Check assertions
            if 'assertions' in test_output:
                for assertion in test_output['assertions']:
                    result.add_assertion(
                        assertion.get('name', 'unknown'),
                        assertion.get('passed', False),
                        assertion.get('message', '')
                    )
            
            result.passed = all(a['passed'] for a in result.assertions) if result.assertions else test_output.get('success', False)
            
        except Exception as e:
            result.passed = False
            result.error = str(e)
            logger.error(f"Test failed: {test_case.name} - {e}")
        
        finally:
            try:
                test_case.teardown()
            except Exception:
                pass
            
            result.duration_ms = (datetime.now() - started_at).total_seconds() * 1000
        
        return result
    
    def generate_report(self, results: List[WorkflowTestResult]) -> str:
        """Generate test report"""
        lines = ["Workflow Test Report", "=" * 50]
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        lines.append(f"Total Tests: {len(results)}")
        lines.append(f"Passed: {passed}")
        lines.append(f"Failed: {failed}")
        lines.append("-" * 50)
        
        for result in results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            lines.append(f"{status} {result.test_name} ({result.duration_ms:.2f}ms)")
            if result.error:
                lines.append(f"    Error: {result.error}")
            for assertion in result.assertions:
                a_status = "✓" if assertion['passed'] else "✗"
                lines.append(f"    {a_status} {assertion['name']}: {assertion['message']}")
        
        lines.append("=" * 50)
        return "\n".join(lines)


# ============================================================================
# Feature 20: End-to-End Test Scenarios
# ============================================================================

class RFPWorkflowTestScenario(WorkflowTestCase):
    """End-to-end test scenario for RFP workflow"""
    
    def __init__(self):
        super().__init__(
            name="RFP End-to-End Workflow",
            description="Tests complete RFP response workflow from scan to submission"
        )
        self.mock_data = {}
    
    def setup(self):
        """Setup mock data"""
        self.mock_data = {
            'rfp': {
                'id': 'RFP_TEST_001',
                'title': 'Test RFP for Power Cables',
                'requirements': [
                    {'type': 'cable', 'spec': '4x16 sq.mm', 'quantity': 1000}
                ]
            },
            'products': [
                {'sku': 'CABLE-001', 'name': 'Power Cable 4x16mm', 'price': 150}
            ]
        }
    
    def run(self, engine: 'WorkflowOrchestrationEngine') -> Dict[str, Any]:
        """Run the test scenario"""
        assertions = []
        
        # Create workflow from template
        workflow = engine.template_manager.create_instance(
            'rfp_quick',
            'Test RFP Workflow',
            {'rfp_data': self.mock_data['rfp']}
        )
        
        assertions.append({
            'name': 'workflow_created',
            'passed': workflow is not None,
            'message': 'Workflow instance created from template'
        })
        
        if not workflow:
            return {'success': False, 'assertions': assertions}
        
        # Register mock handlers
        def mock_analyze(ctx):
            return {'analyzed': True, 'rfp_id': ctx.get('rfp_data', {}).get('id')}
        
        def mock_match(ctx):
            return {'matched': True, 'products': [{'sku': 'CABLE-001'}]}
        
        def mock_price(ctx):
            return {'priced': True, 'total': 150000}
        
        def mock_generate(ctx):
            return {'generated': True, 'document': 'response.pdf'}
        
        engine.step_executor.register_handler('analyze', mock_analyze)
        engine.step_executor.register_handler('match', mock_match)
        engine.step_executor.register_handler('price', mock_price)
        engine.step_executor.register_handler('generate', mock_generate)
        
        # Start workflow
        engine.start_workflow(workflow.workflow_id)
        
        assertions.append({
            'name': 'workflow_started',
            'passed': workflow.status == WorkflowStatus.RUNNING,
            'message': 'Workflow started successfully'
        })
        
        # Execute all steps
        template = engine.template_manager.get('rfp_quick')
        for step in template.steps:
            result = engine.execute_step(workflow.workflow_id, step.step_id)
            assertions.append({
                'name': f'step_{step.step_id}_executed',
                'passed': result.status == StepStatus.COMPLETED,
                'message': f'Step {step.name} completed'
            })
        
        # Check final state
        final_workflow = engine.state_tracker.get_workflow(workflow.workflow_id)
        
        assertions.append({
            'name': 'all_steps_completed',
            'passed': len(final_workflow.step_results) == len(template.steps),
            'message': f'All {len(template.steps)} steps completed'
        })
        
        return {
            'success': all(a['passed'] for a in assertions),
            'assertions': assertions,
            'workflow_id': workflow.workflow_id
        }


class ParallelExecutionTestScenario(WorkflowTestCase):
    """Test scenario for parallel step execution"""
    
    def __init__(self):
        super().__init__(
            name="Parallel Execution Test",
            description="Tests parallel step execution capability"
        )
    
    def run(self, engine: 'WorkflowOrchestrationEngine') -> Dict[str, Any]:
        assertions = []
        
        # Register parallel handlers with delays
        execution_times = {}
        
        def create_handler(step_id, delay):
            def handler(ctx):
                start = time.time()
                time.sleep(delay)
                execution_times[step_id] = time.time() - start
                return {'completed': step_id}
            return handler
        
        # Create workflow
        workflow = engine.template_manager.create_instance('rfp_parallel', 'Parallel Test')
        if not workflow:
            return {'success': False, 'assertions': [{'name': 'create_workflow', 'passed': False, 'message': 'Failed to create workflow'}]}
        
        # Register handlers
        engine.step_executor.register_handler('init', create_handler('init', 0.1))
        engine.step_executor.register_handler('extract', create_handler('extract', 0.1))
        engine.step_executor.register_handler('tech', create_handler('tech', 0.2))
        engine.step_executor.register_handler('price', create_handler('price', 0.2))
        engine.step_executor.register_handler('merge', create_handler('merge', 0.1))
        engine.step_executor.register_handler('generate', create_handler('generate', 0.1))
        
        assertions.append({
            'name': 'workflow_created',
            'passed': workflow is not None,
            'message': 'Parallel workflow created'
        })
        
        return {
            'success': all(a['passed'] for a in assertions),
            'assertions': assertions,
            'workflow_id': workflow.workflow_id if workflow else None
        }


class CheckpointRollbackTestScenario(WorkflowTestCase):
    """Test scenario for checkpoint and rollback functionality"""
    
    def __init__(self):
        super().__init__(
            name="Checkpoint Rollback Test",
            description="Tests checkpoint creation and rollback mechanism"
        )
    
    def run(self, engine: 'WorkflowOrchestrationEngine') -> Dict[str, Any]:
        assertions = []
        
        # Create workflow
        workflow = engine.template_manager.create_instance('rfp_quick', 'Rollback Test')
        if not workflow:
            return {'success': False, 'assertions': [{'name': 'create_workflow', 'passed': False, 'message': 'Failed'}]}
        
        # Register handlers
        engine.step_executor.register_handler('analyze', lambda ctx: {'step': 'analyze'})
        engine.step_executor.register_handler('match', lambda ctx: {'step': 'match'})
        engine.step_executor.register_handler('price', lambda ctx: {'step': 'price'})
        engine.step_executor.register_handler('generate', lambda ctx: {'step': 'generate'})
        
        engine.start_workflow(workflow.workflow_id)
        
        # Execute first two steps
        engine.execute_step(workflow.workflow_id, 'analyze')
        engine.execute_step(workflow.workflow_id, 'match')
        
        # Create checkpoint
        checkpoint = engine.create_checkpoint(workflow.workflow_id)
        assertions.append({
            'name': 'checkpoint_created',
            'passed': checkpoint is not None,
            'message': 'Checkpoint created after step 2'
        })
        
        # Execute more steps
        engine.execute_step(workflow.workflow_id, 'price')
        
        current_workflow = engine.state_tracker.get_workflow(workflow.workflow_id)
        steps_before_rollback = len(current_workflow.step_results)
        
        # Rollback
        success = engine.rollback(workflow.workflow_id)
        assertions.append({
            'name': 'rollback_executed',
            'passed': success,
            'message': 'Rollback executed successfully'
        })
        
        # Check state after rollback
        rolled_back_workflow = engine.state_tracker.get_workflow(workflow.workflow_id)
        steps_after_rollback = len(rolled_back_workflow.step_results)
        
        assertions.append({
            'name': 'state_restored',
            'passed': steps_after_rollback < steps_before_rollback,
            'message': f'Steps reduced from {steps_before_rollback} to {steps_after_rollback}'
        })
        
        return {
            'success': all(a['passed'] for a in assertions),
            'assertions': assertions,
            'workflow_id': workflow.workflow_id
        }


# ============================================================================
# Feature 1: Workflow Orchestration Engine (Main Class)
# ============================================================================

class WorkflowOrchestrationEngine:
    """
    Main workflow orchestration engine
    
    Coordinates complete end-to-end workflow from RFP identification
    to final response generation with full agent interactions,
    data flows, and error handling.
    """
    
    def __init__(self, engine_id: str = None, max_parallel_workers: int = 4):
        self.engine_id = engine_id or f"ENGINE_{uuid.uuid4().hex[:8].upper()}"
        
        # Feature 15: Logging
        self.logger = WorkflowLogger()
        
        # Feature 16: Metrics
        self.metrics_collector = WorkflowMetricsCollector()
        
        # Feature 18: Retry Logic
        self.retry_manager = WorkflowRetryManager()
        
        # Feature 3: Step Executor
        self.step_executor = StepExecutor(
            self.retry_manager,
            self.metrics_collector,
            self.logger
        )
        
        # Feature 2: State Tracker
        self.state_tracker = WorkflowStateTracker()
        
        # Feature 4: Checkpoint System
        self.checkpoint_manager = CheckpointManager()
        
        # Feature 5: Rollback Mechanism
        self.rollback_manager = RollbackManager(self.checkpoint_manager)
        
        # Feature 6: Parallel Processing
        self.parallel_executor = ParallelExecutor(max_workers=max_parallel_workers)
        
        # Feature 7: Visualization
        self.visualizer = WorkflowVisualizer()
        
        # Feature 8: Progress Tracking
        self.progress_tracker = ProgressTracker()
        
        # Feature 9: Time Estimation
        self.time_estimator = TimeEstimator(self.metrics_collector)
        
        # Feature 10: Templates
        self.template_manager = WorkflowTemplateManager()
        
        # Feature 11: Conditional Branching
        self.brancher = ConditionalBrancher()
        
        # Feature 12: Human Tasks
        self.human_task_manager = HumanTaskManager()
        
        # Feature 13: Approvals
        self.approval_manager = ApprovalManager()
        
        # Feature 14: Notifications
        self.notification_manager = NotificationManager()
        
        # Feature 17: Result Handlers
        self.result_handler = ResultHandler(self.notification_manager)
        
        # Feature 19 & 20: Testing Framework
        self.test_runner = WorkflowTestRunner(self)
        
        # Internal state
        self._lock = RLock()
        self._running = False
        
        logger.info(f"Workflow Orchestration Engine initialized: {self.engine_id}")
    
    def start(self):
        """Start the engine"""
        self._running = True
        self.parallel_executor.start()
        logger.info(f"Engine started: {self.engine_id}")
    
    def stop(self):
        """Stop the engine"""
        self._running = False
        self.parallel_executor.stop()
        logger.info(f"Engine stopped: {self.engine_id}")
    
    def create_workflow(self, template_id: str = None, name: str = None,
                        steps: List[StepDefinition] = None,
                        context: Dict[str, Any] = None) -> WorkflowInstance:
        """Create a new workflow instance"""
        if template_id:
            workflow = self.template_manager.create_instance(template_id, name, context)
            if not workflow:
                raise ValueError(f"Template not found: {template_id}")
        else:
            workflow = WorkflowInstance(
                workflow_id=f"WF_{uuid.uuid4().hex[:12].upper()}",
                template_id=None,
                name=name or "Custom Workflow",
                status=WorkflowStatus.DRAFT,
                created_at=datetime.now(),
                context=context or {}
            )
            if steps:
                workflow.metrics.total_steps = len(steps)
        
        # Register with state tracker
        self.state_tracker.register(workflow)
        self.progress_tracker.init_workflow(workflow, workflow.metrics.total_steps)
        self.metrics_collector.start_workflow(workflow.workflow_id, workflow.metrics.total_steps)
        
        self.logger.info(workflow.workflow_id, f"Workflow created: {workflow.name}")
        
        return workflow
    
    def start_workflow(self, workflow_id: str) -> bool:
        """Start executing a workflow"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow:
            return False
        
        if workflow.status not in [WorkflowStatus.DRAFT, WorkflowStatus.PAUSED]:
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        self.state_tracker.update_status(workflow_id, WorkflowStatus.RUNNING)
        
        self.logger.info(workflow_id, "Workflow started")
        self.notification_manager.trigger_event(
            'workflow_started', workflow_id, '',
            {'workflow_name': workflow.name}
        )
        
        return True
    
    def execute_step(self, workflow_id: str, step_id: str) -> StepResult:
        """Execute a specific step"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Get step definition
        template = self.template_manager.get(workflow.template_id) if workflow.template_id else None
        step = None
        if template:
            step = next((s for s in template.steps if s.step_id == step_id), None)
        
        if not step:
            # Create minimal step definition
            step = StepDefinition(step_id=step_id, name=step_id)
        
        # Update current step
        workflow.current_step = step_id
        self.state_tracker.update_current_step(workflow_id, step_id)
        
        # Check if checkpoint is needed
        if step.is_checkpoint:
            self.create_checkpoint(workflow_id)
        
        # Handle special step types
        if step.step_type == StepType.APPROVAL:
            return self._handle_approval_step(workflow, step)
        elif step.step_type == StepType.HUMAN_INPUT:
            return self._handle_human_input_step(workflow, step)
        elif step.step_type == StepType.DECISION:
            return self._handle_decision_step(workflow, step)
        
        # Execute normal step
        result = self.step_executor.execute(step, workflow.context, workflow_id)
        
        # Record result
        self.state_tracker.record_step_result(workflow_id, result)
        
        # Update context with output
        if result.status == StepStatus.COMPLETED and result.output:
            workflow.context[step_id] = result.output
        
        # Update progress
        completed_count = len([r for r in workflow.step_results.values() 
                              if r.status == StepStatus.COMPLETED])
        self.progress_tracker.update_progress(
            workflow_id, step_id, step.name,
            completed_count, workflow.status
        )
        
        # Handle success/failure
        if result.status == StepStatus.COMPLETED:
            self.result_handler.handle_step_success(step_id, result)
        else:
            self.result_handler.handle_step_failure(step_id, result, result.error or "Unknown error")
        
        return result
    
    def _handle_approval_step(self, workflow: WorkflowInstance,
                               step: StepDefinition) -> StepResult:
        """Handle approval step"""
        started_at = datetime.now()
        
        # Create approval request
        request = self.approval_manager.request_approval(
            workflow.workflow_id,
            step.step_id,
            "system",
            step.approvers or ['default_approver'],
            f"Approval Required: {step.name}",
            f"Please review and approve step: {step.name}",
            workflow.context
        )
        
        # Update workflow status
        workflow.status = WorkflowStatus.WAITING_APPROVAL
        self.state_tracker.update_status(workflow.workflow_id, WorkflowStatus.WAITING_APPROVAL)
        
        # Wait for approval (with timeout from step config)
        status = self.approval_manager.wait_for_approval(
            request.request_id,
            timeout=step.timeout_seconds
        )
        
        completed_at = datetime.now()
        
        if status == ApprovalStatus.APPROVED:
            workflow.status = WorkflowStatus.RUNNING
            self.state_tracker.update_status(workflow.workflow_id, WorkflowStatus.RUNNING)
            
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.COMPLETED,
                started_at=started_at,
                completed_at=completed_at,
                output={'approved': True, 'approved_by': request.approved_by},
                execution_time_ms=(completed_at - started_at).total_seconds() * 1000
            )
        else:
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                error=f"Approval {status.value}: {request.comments}",
                execution_time_ms=(completed_at - started_at).total_seconds() * 1000
            )
    
    def _handle_human_input_step(self, workflow: WorkflowInstance,
                                  step: StepDefinition) -> StepResult:
        """Handle human input step"""
        started_at = datetime.now()
        
        # Create human task
        task_id = self.human_task_manager.create_human_task(
            workflow.workflow_id,
            step.step_id,
            step.name,
            workflow.context
        )
        
        # Update workflow status
        workflow.status = WorkflowStatus.WAITING_INPUT
        self.state_tracker.update_status(workflow.workflow_id, WorkflowStatus.WAITING_INPUT)
        
        # Wait for input
        result_data = self.human_task_manager.wait_for_task(
            task_id,
            timeout=step.timeout_seconds
        )
        
        completed_at = datetime.now()
        
        if result_data is not None:
            workflow.status = WorkflowStatus.RUNNING
            self.state_tracker.update_status(workflow.workflow_id, WorkflowStatus.RUNNING)
            
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.COMPLETED,
                started_at=started_at,
                completed_at=completed_at,
                output=result_data,
                execution_time_ms=(completed_at - started_at).total_seconds() * 1000
            )
        else:
            return StepResult(
                step_id=step.step_id,
                status=StepStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                error="Human input timeout or cancelled",
                execution_time_ms=(completed_at - started_at).total_seconds() * 1000
            )
    
    def _handle_decision_step(self, workflow: WorkflowInstance,
                               step: StepDefinition) -> StepResult:
        """Handle decision/branching step"""
        started_at = datetime.now()
        
        # Evaluate branching rules
        next_step = self.brancher.evaluate(step.step_id, workflow.context)
        
        completed_at = datetime.now()
        
        return StepResult(
            step_id=step.step_id,
            status=StepStatus.COMPLETED,
            started_at=started_at,
            completed_at=completed_at,
            output={'next_step': next_step or step.on_success},
            execution_time_ms=(completed_at - started_at).total_seconds() * 1000
        )
    
    def execute_parallel_steps(self, workflow_id: str,
                                step_ids: List[str]) -> Dict[str, StepResult]:
        """Execute multiple steps in parallel"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        template = self.template_manager.get(workflow.template_id)
        if not template:
            raise ValueError(f"Template not found: {workflow.template_id}")
        
        # Prepare tasks
        tasks = []
        for step_id in step_ids:
            step = next((s for s in template.steps if s.step_id == step_id), None)
            if step and step.handler:
                tasks.append((step_id, step.handler, (workflow.context,), {}))
        
        # Execute in parallel
        parallel_results = self.parallel_executor.execute_parallel(tasks)
        
        # Convert to StepResults
        results = {}
        for step_id, task_result in parallel_results.items():
            if task_result['success']:
                results[step_id] = StepResult(
                    step_id=step_id,
                    status=StepStatus.COMPLETED,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    output=task_result['result']
                )
            else:
                results[step_id] = StepResult(
                    step_id=step_id,
                    status=StepStatus.FAILED,
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    error=task_result['error']
                )
            
            self.state_tracker.record_step_result(workflow_id, results[step_id])
        
        return results
    
    def create_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        """Create a checkpoint for the workflow"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow:
            return None
        
        checkpoint = self.checkpoint_manager.create_checkpoint(
            workflow,
            workflow.current_step or "",
            workflow.context
        )
        
        self.metrics_collector.record_checkpoint(workflow_id)
        self.logger.info(workflow_id, f"Checkpoint created: {checkpoint.checkpoint_id}")
        
        return checkpoint
    
    def rollback(self, workflow_id: str, checkpoint_id: str = None) -> bool:
        """Rollback workflow to a checkpoint"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow:
            return False
        
        success = self.rollback_manager.rollback_to_checkpoint(workflow, checkpoint_id)
        
        if success:
            self.metrics_collector.record_rollback(workflow_id)
            self.state_tracker.update_status(workflow_id, WorkflowStatus.ROLLED_BACK)
            self.logger.info(workflow_id, "Workflow rolled back")
        
        return success
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause workflow execution"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return False
        
        workflow.status = WorkflowStatus.PAUSED
        self.state_tracker.update_status(workflow_id, WorkflowStatus.PAUSED)
        self.logger.info(workflow_id, "Workflow paused")
        
        return True
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume paused workflow"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.PAUSED:
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        self.state_tracker.update_status(workflow_id, WorkflowStatus.RUNNING)
        self.logger.info(workflow_id, "Workflow resumed")
        
        return True
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel workflow execution"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow:
            return False
        
        workflow.status = WorkflowStatus.CANCELLED
        self.state_tracker.update_status(workflow_id, WorkflowStatus.CANCELLED)
        self.logger.info(workflow_id, "Workflow cancelled")
        
        return True
    
    def complete_workflow(self, workflow_id: str, success: bool = True,
                          error: str = None):
        """Mark workflow as complete"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow:
            return
        
        self.state_tracker.complete_workflow(workflow_id, success, error)
        self.metrics_collector.complete_workflow(workflow_id, success)
        self.progress_tracker.complete_workflow(
            workflow_id,
            WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
        )
        
        if success:
            self.result_handler.handle_workflow_success(workflow)
        else:
            self.result_handler.handle_workflow_failure(workflow, error or "Unknown error")
    
    def get_progress(self, workflow_id: str) -> Optional[ProgressInfo]:
        """Get workflow progress"""
        return self.progress_tracker.get_progress(workflow_id)
    
    def get_time_estimate(self, workflow_id: str) -> Optional[TimeEstimate]:
        """Get time estimate for workflow completion"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow or not workflow.template_id:
            return None
        
        template = self.template_manager.get(workflow.template_id)
        if not template:
            return None
        
        return self.time_estimator.estimate_workflow(workflow, template.steps)
    
    def visualize(self, workflow_id: str, format: str = "text") -> str:
        """Generate workflow visualization"""
        workflow = self.state_tracker.get_workflow(workflow_id)
        if not workflow or not workflow.template_id:
            return ""
        
        template = self.template_manager.get(workflow.template_id)
        if not template:
            return ""
        
        if format == "mermaid":
            return self.visualizer.generate_mermaid(template.steps, workflow.step_results)
        elif format == "json":
            return json.dumps(
                self.visualizer.generate_json_graph(template.steps, workflow.step_results),
                indent=2
            )
        else:
            return self.visualizer.generate_text_tree(
                template.steps,
                workflow.step_results,
                workflow.current_step
            )
    
    def get_workflow_metrics(self, workflow_id: str) -> Optional[WorkflowMetrics]:
        """Get metrics for a workflow"""
        return self.metrics_collector.get_workflow_metrics(workflow_id)
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global engine metrics"""
        return self.metrics_collector.get_global_metrics()
    
    def get_logs(self, workflow_id: str = None, limit: int = 100) -> List[WorkflowLog]:
        """Get workflow logs"""
        return self.logger.get_logs(workflow_id=workflow_id, limit=limit)
    
    def run_tests(self) -> List[WorkflowTestResult]:
        """Run workflow tests"""
        # Add built-in test scenarios
        self.test_runner.add_test(RFPWorkflowTestScenario())
        self.test_runner.add_test(ParallelExecutionTestScenario())
        self.test_runner.add_test(CheckpointRollbackTestScenario())
        
        return self.test_runner.run_all()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            'engine_id': self.engine_id,
            'status': 'healthy' if self._running else 'stopped',
            'running_workflows': len([
                w for w in self.state_tracker.get_all_workflows()
                if w.status == WorkflowStatus.RUNNING
            ]),
            'global_metrics': self.get_global_metrics(),
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# Convenience Functions
# ============================================================================

_default_engine: Optional[WorkflowOrchestrationEngine] = None

def get_engine() -> WorkflowOrchestrationEngine:
    """Get or create the default engine instance"""
    global _default_engine
    if _default_engine is None:
        _default_engine = WorkflowOrchestrationEngine()
    return _default_engine

def create_workflow(template_id: str, name: str = None,
                    context: Dict[str, Any] = None) -> WorkflowInstance:
    """Create a workflow using the default engine"""
    return get_engine().create_workflow(template_id, name, context=context)

def run_workflow(workflow_id: str):
    """Run a workflow using the default engine"""
    return get_engine().start_workflow(workflow_id)
