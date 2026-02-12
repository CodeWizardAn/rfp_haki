"""
Batch Processing

Efficient batch operations with:
- Chunked processing
- Pipeline execution
- Progress tracking
- Error handling and retries
"""

import time
import logging
import threading
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class BatchStatus(Enum):
    """Batch processing status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some items failed


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    batch_size: int = 100
    max_workers: int = 4
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout_per_item: float = 30.0
    continue_on_error: bool = True
    progress_callback: Optional[Callable[[int, int], None]] = None


@dataclass
class BatchResult(Generic[R]):
    """Result of batch processing"""
    status: BatchStatus = BatchStatus.PENDING
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    results: List[R] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def items_per_second(self) -> float:
        if self.duration_seconds > 0:
            return self.processed_items / self.duration_seconds
        return 0.0
    
    @property
    def success_rate(self) -> float:
        if self.processed_items > 0:
            return self.successful_items / self.processed_items
        return 0.0


class BatchProcessor(Generic[T, R]):
    """
    Generic batch processor for efficient bulk operations
    """
    
    def __init__(self, config: BatchConfig = None):
        """
        Initialize batch processor
        
        Args:
            config: Batch processing configuration
        """
        self.config = config or BatchConfig()
        self._lock = threading.Lock()
        
        logger.info(f"BatchProcessor initialized: batch_size={self.config.batch_size}, workers={self.config.max_workers}")
    
    def process(self, items: List[T], 
                processor: Callable[[T], R]) -> BatchResult[R]:
        """
        Process items in batches
        
        Args:
            items: Items to process
            processor: Function to process each item
            
        Returns:
            BatchResult with results and statistics
        """
        result = BatchResult[R](
            total_items=len(items),
            start_time=datetime.now()
        )
        result.status = BatchStatus.RUNNING
        
        try:
            # Process in batches
            for batch_start in range(0, len(items), self.config.batch_size):
                batch_end = min(batch_start + self.config.batch_size, len(items))
                batch = items[batch_start:batch_end]
                
                batch_results = self._process_batch(batch, processor)
                
                for item_result in batch_results:
                    result.processed_items += 1
                    
                    if item_result['success']:
                        result.successful_items += 1
                        result.results.append(item_result['result'])
                    else:
                        result.failed_items += 1
                        result.errors.append(item_result['error'])
                        
                        if not self.config.continue_on_error:
                            result.status = BatchStatus.FAILED
                            result.end_time = datetime.now()
                            return result
                
                # Progress callback
                if self.config.progress_callback:
                    self.config.progress_callback(result.processed_items, result.total_items)
            
            # Determine final status
            if result.failed_items == 0:
                result.status = BatchStatus.COMPLETED
            elif result.successful_items > 0:
                result.status = BatchStatus.PARTIAL
            else:
                result.status = BatchStatus.FAILED
                
        except Exception as e:
            result.status = BatchStatus.FAILED
            result.errors.append({'error': str(e), 'type': 'batch_error'})
            logger.error(f"Batch processing failed: {e}")
        
        result.end_time = datetime.now()
        return result
    
    def _process_batch(self, batch: List[T], 
                       processor: Callable[[T], R]) -> List[Dict[str, Any]]:
        """Process a single batch of items"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_item = {
                executor.submit(self._process_item, item, processor): item
                for item in batch
            }
            
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result(timeout=self.config.timeout_per_item)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'item': item,
                        'error': {'message': str(e), 'type': type(e).__name__}
                    })
        
        return results
    
    def _process_item(self, item: T, processor: Callable[[T], R]) -> Dict[str, Any]:
        """Process a single item with retries"""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                result = processor(item)
                return {'success': True, 'result': result, 'item': item}
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
        
        return {
            'success': False,
            'item': item,
            'error': {
                'message': str(last_error),
                'type': type(last_error).__name__,
                'attempts': self.config.max_retries
            }
        }
    
    def process_parallel(self, items: List[T],
                        processor: Callable[[List[T]], List[R]]) -> BatchResult[R]:
        """
        Process items in parallel batches
        
        Args:
            items: Items to process
            processor: Function that processes a batch of items
            
        Returns:
            BatchResult with results
        """
        result = BatchResult[R](
            total_items=len(items),
            start_time=datetime.now()
        )
        result.status = BatchStatus.RUNNING
        
        # Split into batches
        batches = list(self._chunk_items(items, self.config.batch_size))
        
        try:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_batch = {
                    executor.submit(processor, batch): i
                    for i, batch in enumerate(batches)
                }
                
                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    batch = batches[batch_idx]
                    
                    try:
                        batch_results = future.result()
                        result.results.extend(batch_results)
                        result.successful_items += len(batch_results)
                        result.processed_items += len(batch)
                        
                    except Exception as e:
                        result.failed_items += len(batch)
                        result.processed_items += len(batch)
                        result.errors.append({
                            'batch_index': batch_idx,
                            'error': str(e)
                        })
                        
                        if not self.config.continue_on_error:
                            result.status = BatchStatus.FAILED
                            break
                    
                    if self.config.progress_callback:
                        self.config.progress_callback(result.processed_items, result.total_items)
            
            if result.failed_items == 0:
                result.status = BatchStatus.COMPLETED
            elif result.successful_items > 0:
                result.status = BatchStatus.PARTIAL
            else:
                result.status = BatchStatus.FAILED
                
        except Exception as e:
            result.status = BatchStatus.FAILED
            result.errors.append({'error': str(e)})
        
        result.end_time = datetime.now()
        return result
    
    def _chunk_items(self, items: List[T], chunk_size: int) -> Iterator[List[T]]:
        """Split items into chunks"""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]


class Pipeline:
    """
    Processing pipeline for chained operations
    """
    
    def __init__(self):
        self._stages: List[Callable] = []
        self._stage_names: List[str] = []
    
    def add_stage(self, processor: Callable, name: str = None) -> 'Pipeline':
        """Add a processing stage"""
        self._stages.append(processor)
        self._stage_names.append(name or f"stage_{len(self._stages)}")
        return self
    
    def execute(self, items: List[Any]) -> Dict[str, Any]:
        """Execute pipeline on items"""
        result = {
            'input_count': len(items),
            'stages': [],
            'output': None,
            'success': True
        }
        
        current_items = items
        
        for i, (stage, name) in enumerate(zip(self._stages, self._stage_names)):
            stage_start = time.time()
            
            try:
                current_items = stage(current_items)
                stage_duration = time.time() - stage_start
                
                result['stages'].append({
                    'name': name,
                    'success': True,
                    'duration_ms': stage_duration * 1000,
                    'output_count': len(current_items) if hasattr(current_items, '__len__') else 1
                })
                
            except Exception as e:
                result['stages'].append({
                    'name': name,
                    'success': False,
                    'error': str(e)
                })
                result['success'] = False
                logger.error(f"Pipeline stage {name} failed: {e}")
                break
        
        result['output'] = current_items
        return result


class BatchInsertBuilder:
    """
    Builder for efficient batch database inserts
    """
    
    def __init__(self, session_factory=None, batch_size: int = 1000):
        """
        Initialize batch insert builder
        
        Args:
            session_factory: SQLAlchemy session factory
            batch_size: Number of records per batch
        """
        self.session_factory = session_factory
        self.batch_size = batch_size
        self._pending: List[Any] = []
        self._lock = threading.Lock()
        self._total_inserted = 0
    
    def add(self, record: Any):
        """Add a record to the batch"""
        with self._lock:
            self._pending.append(record)
            
            if len(self._pending) >= self.batch_size:
                self._flush()
    
    def add_many(self, records: List[Any]):
        """Add multiple records"""
        with self._lock:
            self._pending.extend(records)
            
            while len(self._pending) >= self.batch_size:
                self._flush()
    
    def _flush(self):
        """Flush pending records to database"""
        if not self._pending:
            return
        
        batch = self._pending[:self.batch_size]
        self._pending = self._pending[self.batch_size:]
        
        if self.session_factory:
            session = self.session_factory()
            try:
                session.bulk_save_objects(batch)
                session.commit()
                self._total_inserted += len(batch)
            except Exception as e:
                session.rollback()
                logger.error(f"Batch insert failed: {e}")
                raise
            finally:
                session.close()
        else:
            self._total_inserted += len(batch)
    
    def flush_all(self):
        """Flush all remaining records"""
        with self._lock:
            while self._pending:
                self._flush()
    
    def get_stats(self) -> Dict[str, int]:
        """Get insert statistics"""
        return {
            'total_inserted': self._total_inserted,
            'pending': len(self._pending)
        }


class StreamProcessor:
    """
    Stream processor for continuous data processing
    """
    
    def __init__(self, processor: Callable[[Any], Any],
                 buffer_size: int = 1000,
                 flush_interval: float = 5.0):
        """
        Initialize stream processor
        
        Args:
            processor: Function to process items
            buffer_size: Maximum buffer size before flush
            flush_interval: Seconds between automatic flushes
        """
        self.processor = processor
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        self._buffer: List[Any] = []
        self._lock = threading.Lock()
        self._last_flush = time.time()
        self._running = False
        self._flush_thread = None
        
        self._stats = {
            'items_received': 0,
            'items_processed': 0,
            'flushes': 0,
            'errors': 0
        }
    
    def start(self):
        """Start the stream processor"""
        self._running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
        logger.info("StreamProcessor started")
    
    def stop(self):
        """Stop the stream processor"""
        self._running = False
        self.flush()
        logger.info("StreamProcessor stopped")
    
    def push(self, item: Any):
        """Push an item to the stream"""
        with self._lock:
            self._buffer.append(item)
            self._stats['items_received'] += 1
            
            if len(self._buffer) >= self.buffer_size:
                self._flush_buffer()
    
    def push_many(self, items: List[Any]):
        """Push multiple items"""
        for item in items:
            self.push(item)
    
    def _flush_loop(self):
        """Background flush loop"""
        while self._running:
            time.sleep(1)
            
            if time.time() - self._last_flush >= self.flush_interval:
                self.flush()
    
    def flush(self):
        """Flush the buffer"""
        with self._lock:
            self._flush_buffer()
    
    def _flush_buffer(self):
        """Internal flush method (must hold lock)"""
        if not self._buffer:
            return
        
        items = self._buffer[:]
        self._buffer = []
        self._last_flush = time.time()
        
        try:
            self.processor(items)
            self._stats['items_processed'] += len(items)
            self._stats['flushes'] += 1
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Stream processing error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            **self._stats,
            'buffer_size': len(self._buffer),
            'running': self._running
        }
