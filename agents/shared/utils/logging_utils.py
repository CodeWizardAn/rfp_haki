"""
Logging Utilities
Centralized logging configuration for agents

Features:
- Agent-specific loggers
- Structured logging
- Performance logging
- Error tracking
- Log rotation
"""

import logging
import logging.handlers
import json
import time
import traceback
from typing import Any, Dict, Optional, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    agent: str
    action: str
    message: str
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        for key in ['agent', 'action', 'duration_ms', 'metadata', 'rfp_id', 'product_id']:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)
        
        # Add exception info if present
        if record.exc_info:
            log_data['error'] = str(record.exc_info[1])
            log_data['traceback'] = ''.join(traceback.format_exception(*record.exc_info))
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Formatter with color support for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class AgentLogger:
    """
    Centralized logger for agents with structured logging support
    """
    
    _loggers: Dict[str, 'AgentLogger'] = {}
    _lock = threading.Lock()
    _initialized = False
    _log_dir: Optional[Path] = None
    
    def __init__(
        self,
        agent_name: str,
        level: Union[int, LogLevel] = LogLevel.INFO
    ):
        """
        Initialize agent logger
        
        Args:
            agent_name: Name of the agent
            level: Logging level
        """
        self.agent_name = agent_name
        self._level = level.value if isinstance(level, LogLevel) else level
        
        # Create logger
        self.logger = logging.getLogger(f"agent.{agent_name}")
        self.logger.setLevel(self._level)
        
        # Track performance metrics
        self._metrics: Dict[str, list] = {}
        self._metrics_lock = threading.Lock()
    
    @classmethod
    def setup_logging(
        cls,
        log_dir: Optional[str] = None,
        log_level: Union[int, LogLevel] = LogLevel.INFO,
        console_output: bool = True,
        file_output: bool = True,
        json_format: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Set up global logging configuration
        
        Args:
            log_dir: Directory for log files
            log_level: Default logging level
            console_output: Enable console logging
            file_output: Enable file logging
            json_format: Use JSON format for logs
            max_file_size: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        with cls._lock:
            if cls._initialized:
                return
            
            level = log_level.value if isinstance(log_level, LogLevel) else log_level
            
            # Set root logger level
            root_logger = logging.getLogger()
            root_logger.setLevel(level)
            
            # Create log directory
            if log_dir:
                cls._log_dir = Path(log_dir)
                cls._log_dir.mkdir(parents=True, exist_ok=True)
            
            # Console handler
            if console_output:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(level)
                
                if json_format:
                    console_handler.setFormatter(StructuredFormatter())
                else:
                    console_handler.setFormatter(ColoredFormatter(
                        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    ))
                
                root_logger.addHandler(console_handler)
            
            # File handler with rotation
            if file_output and cls._log_dir:
                file_handler = logging.handlers.RotatingFileHandler(
                    cls._log_dir / 'agents.log',
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(level)
                
                if json_format:
                    file_handler.setFormatter(StructuredFormatter())
                else:
                    file_handler.setFormatter(logging.Formatter(
                        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    ))
                
                root_logger.addHandler(file_handler)
                
                # Separate error log
                error_handler = logging.handlers.RotatingFileHandler(
                    cls._log_dir / 'agents_error.log',
                    maxBytes=max_file_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(StructuredFormatter())
                root_logger.addHandler(error_handler)
            
            cls._initialized = True
    
    @classmethod
    def get_logger(cls, agent_name: str, level: Union[int, LogLevel] = LogLevel.INFO) -> 'AgentLogger':
        """
        Get or create a logger for an agent
        
        Args:
            agent_name: Name of the agent
            level: Logging level
            
        Returns:
            AgentLogger instance
        """
        with cls._lock:
            if agent_name not in cls._loggers:
                cls._loggers[agent_name] = cls(agent_name, level)
            return cls._loggers[agent_name]
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs):
        """Internal logging method"""
        extra = {'agent': self.agent_name}
        extra.update(kwargs)
        self.logger.log(level, message, exc_info=exc_info, extra=extra)
    
    def log_agent_action(
        self,
        action: str,
        message: str,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict] = None,
        level: Union[int, LogLevel] = LogLevel.INFO
    ):
        """
        Log an agent action with structured data
        
        Args:
            action: Action being performed
            message: Log message
            duration_ms: Optional duration in milliseconds
            metadata: Optional additional metadata
            level: Logging level
        """
        log_level = level.value if isinstance(level, LogLevel) else level
        
        extra = {
            'agent': self.agent_name,
            'action': action,
            'duration_ms': duration_ms,
            'metadata': metadata,
        }
        
        self.logger.log(log_level, f"[{action}] {message}", extra=extra)
        
        # Track performance
        if duration_ms is not None:
            self._track_metric(action, duration_ms)
    
    def log_error(
        self,
        action: str,
        error: Exception,
        message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log an error with full context
        
        Args:
            action: Action that caused the error
            error: The exception
            message: Optional additional message
            metadata: Optional additional metadata
        """
        error_msg = message or str(error)
        tb = traceback.format_exc()
        
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            level='ERROR',
            agent=self.agent_name,
            action=action,
            message=error_msg,
            error=str(error),
            traceback=tb,
            metadata=metadata
        )
        
        self.logger.error(
            f"[{action}] {error_msg}",
            extra={
                'agent': self.agent_name,
                'action': action,
                'metadata': metadata,
            },
            exc_info=True
        )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict] = None
    ):
        """
        Log performance metrics
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        status = "completed" if success else "failed"
        
        self.logger.info(
            f"[PERF] {operation} {status} in {duration_ms:.2f}ms",
            extra={
                'agent': self.agent_name,
                'action': 'performance',
                'duration_ms': duration_ms,
                'metadata': {
                    'operation': operation,
                    'success': success,
                    **(metadata or {})
                }
            }
        )
        
        self._track_metric(operation, duration_ms)
    
    def _track_metric(self, name: str, value: float):
        """Track a metric for performance analysis"""
        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(value)
            # Keep only last 1000 values
            if len(self._metrics[name]) > 1000:
                self._metrics[name] = self._metrics[name][-1000:]
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get aggregated metrics
        
        Returns:
            Dictionary with metric statistics
        """
        with self._metrics_lock:
            result = {}
            for name, values in self._metrics.items():
                if values:
                    result[name] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'total': sum(values),
                    }
            return result
    
    def context(self, action: str, **metadata):
        """
        Create a logging context manager for timing operations
        
        Args:
            action: Action being performed
            **metadata: Additional metadata
            
        Example:
            with logger.context('process_rfp', rfp_id='123'):
                # Do work
        """
        return LogContext(self, action, metadata)


class LogContext:
    """Context manager for timing and logging operations"""
    
    def __init__(self, logger: AgentLogger, action: str, metadata: Dict):
        self.logger = logger
        self.action = action
        self.metadata = metadata
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger.debug(f"Starting {self.action}", **self.metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        if exc_type is None:
            self.logger.log_performance(
                self.action,
                duration_ms,
                success=True,
                metadata=self.metadata
            )
        else:
            self.logger.log_error(
                self.action,
                exc_val,
                metadata={'duration_ms': duration_ms, **self.metadata}
            )
        
        return False  # Don't suppress exceptions


# Module-level convenience functions
def setup_logging(**kwargs):
    """Set up global logging configuration"""
    AgentLogger.setup_logging(**kwargs)


def get_logger(agent_name: str, level: Union[int, LogLevel] = LogLevel.INFO) -> AgentLogger:
    """Get or create a logger for an agent"""
    return AgentLogger.get_logger(agent_name, level)


def log_agent_action(
    agent_name: str,
    action: str,
    message: str,
    **kwargs
):
    """Log an agent action"""
    logger = get_logger(agent_name)
    logger.log_agent_action(action, message, **kwargs)


def log_error(
    agent_name: str,
    action: str,
    error: Exception,
    **kwargs
):
    """Log an error"""
    logger = get_logger(agent_name)
    logger.log_error(action, error, **kwargs)


def log_performance(
    agent_name: str,
    operation: str,
    duration_ms: float,
    **kwargs
):
    """Log performance metrics"""
    logger = get_logger(agent_name)
    logger.log_performance(operation, duration_ms, **kwargs)
