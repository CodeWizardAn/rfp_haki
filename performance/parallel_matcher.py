"""
Parallel Matching Engine

High-performance parallel matching with:
- Multi-threaded/process matching
- Work distribution
- Result aggregation
- Progress tracking
"""

import logging
import threading
import time
import hashlib
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp

logger = logging.getLogger(__name__)


class MatchingStrategy(Enum):
    """Matching strategy types"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


@dataclass
class MatchTask:
    """A matching task to be processed"""
    task_id: str
    query: str
    candidates: List[Any]
    strategy: MatchingStrategy = MatchingStrategy.HYBRID
    top_k: int = 10
    threshold: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchResult:
    """Result of a matching task"""
    task_id: str
    matches: List[Dict[str, Any]]
    processing_time_ms: float
    strategy_used: MatchingStrategy
    total_candidates: int
    matches_found: int
    success: bool = True
    error: Optional[str] = None


class ParallelMatcher:
    """
    Parallel matching engine for high-throughput matching
    """
    
    def __init__(self, 
                 num_workers: int = None,
                 use_processes: bool = False,
                 chunk_size: int = 100):
        """
        Initialize parallel matcher
        
        Args:
            num_workers: Number of worker threads/processes
            use_processes: Use processes instead of threads
            chunk_size: Number of candidates per chunk
        """
        self.num_workers = num_workers or (mp.cpu_count() - 1) or 1
        self.use_processes = use_processes
        self.chunk_size = chunk_size
        
        self._executor = None
        self._matching_functions: Dict[MatchingStrategy, Callable] = {}
        
        # Register default matchers
        self._register_default_matchers()
        
        # Statistics
        self._stats = {
            'tasks_processed': 0,
            'total_candidates': 0,
            'total_matches': 0,
            'avg_processing_time_ms': 0.0
        }
        self._lock = threading.Lock()
        
        logger.info(f"ParallelMatcher initialized: workers={self.num_workers}, use_processes={use_processes}")
    
    def _register_default_matchers(self):
        """Register default matching functions"""
        self._matching_functions[MatchingStrategy.EXACT] = self._exact_match
        self._matching_functions[MatchingStrategy.FUZZY] = self._fuzzy_match
        self._matching_functions[MatchingStrategy.SEMANTIC] = self._semantic_match
        self._matching_functions[MatchingStrategy.HYBRID] = self._hybrid_match
    
    def register_matcher(self, strategy: MatchingStrategy, 
                        matcher: Callable[[str, List[Any], float], List[Dict]]):
        """Register a custom matching function"""
        self._matching_functions[strategy] = matcher
    
    def _get_executor(self):
        """Get or create executor"""
        if self._executor is None:
            if self.use_processes:
                self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
            else:
                self._executor = ThreadPoolExecutor(max_workers=self.num_workers)
        return self._executor
    
    def match(self, task: MatchTask) -> MatchResult:
        """
        Execute a matching task
        
        Args:
            task: MatchTask to execute
            
        Returns:
            MatchResult with matches
        """
        start_time = time.time()
        
        try:
            matcher = self._matching_functions.get(task.strategy)
            if not matcher:
                raise ValueError(f"Unknown strategy: {task.strategy}")
            
            # Split candidates into chunks for parallel processing
            chunks = self._chunk_candidates(task.candidates, self.chunk_size)
            
            all_matches = []
            executor = self._get_executor()
            
            futures = [
                executor.submit(matcher, task.query, chunk, task.threshold)
                for chunk in chunks
            ]
            
            for future in as_completed(futures):
                try:
                    chunk_matches = future.result()
                    all_matches.extend(chunk_matches)
                except Exception as e:
                    logger.error(f"Chunk matching failed: {e}")
            
            # Sort and limit results
            all_matches.sort(key=lambda x: x.get('score', 0), reverse=True)
            top_matches = all_matches[:task.top_k]
            
            processing_time = (time.time() - start_time) * 1000
            
            result = MatchResult(
                task_id=task.task_id,
                matches=top_matches,
                processing_time_ms=processing_time,
                strategy_used=task.strategy,
                total_candidates=len(task.candidates),
                matches_found=len(top_matches)
            )
            
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Matching task {task.task_id} failed: {e}")
            
            return MatchResult(
                task_id=task.task_id,
                matches=[],
                processing_time_ms=processing_time,
                strategy_used=task.strategy,
                total_candidates=len(task.candidates),
                matches_found=0,
                success=False,
                error=str(e)
            )
    
    def match_batch(self, tasks: List[MatchTask],
                    progress_callback: Callable[[int, int], None] = None
                    ) -> List[MatchResult]:
        """
        Execute multiple matching tasks in parallel
        
        Args:
            tasks: List of MatchTask to execute
            progress_callback: Callback for progress updates
            
        Returns:
            List of MatchResult
        """
        results = []
        executor = self._get_executor()
        
        futures = {
            executor.submit(self.match, task): task
            for task in tasks
        }
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            
            if progress_callback:
                progress_callback(completed, len(tasks))
        
        return results
    
    def _chunk_candidates(self, candidates: List[Any], 
                         chunk_size: int) -> List[List[Any]]:
        """Split candidates into chunks"""
        return [
            candidates[i:i + chunk_size]
            for i in range(0, len(candidates), chunk_size)
        ]
    
    # ==================== Matching Strategies ====================
    
    def _exact_match(self, query: str, candidates: List[Any],
                    threshold: float) -> List[Dict[str, Any]]:
        """Exact string matching"""
        matches = []
        query_lower = query.lower().strip()
        
        for candidate in candidates:
            candidate_text = self._get_text(candidate)
            if candidate_text.lower().strip() == query_lower:
                matches.append({
                    'candidate': candidate,
                    'score': 1.0,
                    'strategy': 'exact'
                })
        
        return matches
    
    def _fuzzy_match(self, query: str, candidates: List[Any],
                    threshold: float) -> List[Dict[str, Any]]:
        """Fuzzy string matching using simple ratio"""
        matches = []
        query_lower = query.lower()
        
        for candidate in candidates:
            candidate_text = self._get_text(candidate).lower()
            score = self._simple_ratio(query_lower, candidate_text)
            
            if score >= threshold:
                matches.append({
                    'candidate': candidate,
                    'score': score,
                    'strategy': 'fuzzy'
                })
        
        return matches
    
    def _semantic_match(self, query: str, candidates: List[Any],
                       threshold: float) -> List[Dict[str, Any]]:
        """
        Semantic matching using embeddings
        Note: In production, would use actual embedding service
        """
        matches = []
        
        # Simplified semantic matching using keyword overlap
        query_words = set(query.lower().split())
        
        for candidate in candidates:
            candidate_text = self._get_text(candidate).lower()
            candidate_words = set(candidate_text.split())
            
            if not query_words or not candidate_words:
                continue
            
            overlap = len(query_words & candidate_words)
            score = overlap / max(len(query_words), len(candidate_words))
            
            if score >= threshold:
                matches.append({
                    'candidate': candidate,
                    'score': score,
                    'strategy': 'semantic'
                })
        
        return matches
    
    def _hybrid_match(self, query: str, candidates: List[Any],
                     threshold: float) -> List[Dict[str, Any]]:
        """Hybrid matching combining multiple strategies"""
        # Get matches from all strategies
        exact = self._exact_match(query, candidates, 0.99)
        fuzzy = self._fuzzy_match(query, candidates, threshold)
        semantic = self._semantic_match(query, candidates, threshold)
        
        # Combine and deduplicate
        all_matches: Dict[str, Dict] = {}
        
        for match in exact:
            key = self._get_candidate_key(match['candidate'])
            match['score'] = min(1.0, match['score'] * 1.2)  # Boost exact
            all_matches[key] = match
        
        for match in fuzzy:
            key = self._get_candidate_key(match['candidate'])
            if key not in all_matches:
                all_matches[key] = match
            else:
                # Average scores
                all_matches[key]['score'] = (all_matches[key]['score'] + match['score']) / 2
        
        for match in semantic:
            key = self._get_candidate_key(match['candidate'])
            if key not in all_matches:
                all_matches[key] = match
            else:
                all_matches[key]['score'] = (all_matches[key]['score'] + match['score']) / 2
        
        # Update strategy to hybrid
        for match in all_matches.values():
            match['strategy'] = 'hybrid'
        
        return list(all_matches.values())
    
    def _get_text(self, candidate: Any) -> str:
        """Extract text from candidate"""
        if isinstance(candidate, str):
            return candidate
        elif isinstance(candidate, dict):
            return candidate.get('text', candidate.get('name', str(candidate)))
        elif hasattr(candidate, 'text'):
            return candidate.text
        elif hasattr(candidate, 'name'):
            return candidate.name
        else:
            return str(candidate)
    
    def _get_candidate_key(self, candidate: Any) -> str:
        """Get unique key for candidate"""
        if isinstance(candidate, dict):
            if 'id' in candidate:
                return str(candidate['id'])
        elif hasattr(candidate, 'id'):
            return str(candidate.id)
        
        return hashlib.md5(str(candidate).encode()).hexdigest()
    
    def _simple_ratio(self, s1: str, s2: str) -> float:
        """Simple string similarity ratio"""
        if not s1 or not s2:
            return 0.0
        
        # Use longest common subsequence
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_length = dp[m][n]
        return 2.0 * lcs_length / (m + n)
    
    def _update_stats(self, result: MatchResult):
        """Update statistics"""
        with self._lock:
            self._stats['tasks_processed'] += 1
            self._stats['total_candidates'] += result.total_candidates
            self._stats['total_matches'] += result.matches_found
            
            # Running average of processing time
            n = self._stats['tasks_processed']
            prev_avg = self._stats['avg_processing_time_ms']
            self._stats['avg_processing_time_ms'] = (
                prev_avg * (n - 1) + result.processing_time_ms
            ) / n
    
    def get_stats(self) -> Dict[str, Any]:
        """Get matcher statistics"""
        with self._lock:
            return dict(self._stats)
    
    def close(self):
        """Close the executor"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None


class MatcherPool:
    """
    Pool of parallel matchers for load distribution
    """
    
    def __init__(self, pool_size: int = 3):
        """
        Initialize matcher pool
        
        Args:
            pool_size: Number of matchers in pool
        """
        self.pool_size = pool_size
        self._matchers: List[ParallelMatcher] = []
        self._current_idx = 0
        self._lock = threading.Lock()
        
        for i in range(pool_size):
            matcher = ParallelMatcher(
                num_workers=max(1, mp.cpu_count() // pool_size),
                chunk_size=50
            )
            self._matchers.append(matcher)
        
        logger.info(f"MatcherPool initialized with {pool_size} matchers")
    
    def get_matcher(self) -> ParallelMatcher:
        """Get next matcher (round-robin)"""
        with self._lock:
            matcher = self._matchers[self._current_idx]
            self._current_idx = (self._current_idx + 1) % self.pool_size
            return matcher
    
    def match(self, task: MatchTask) -> MatchResult:
        """Match using next available matcher"""
        matcher = self.get_matcher()
        return matcher.match(task)
    
    def match_batch(self, tasks: List[MatchTask]) -> List[MatchResult]:
        """Distribute tasks across matchers"""
        # Distribute tasks round-robin
        task_assignments: Dict[int, List[MatchTask]] = {
            i: [] for i in range(self.pool_size)
        }
        
        for i, task in enumerate(tasks):
            matcher_idx = i % self.pool_size
            task_assignments[matcher_idx].append(task)
        
        # Execute in parallel
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.pool_size) as executor:
            futures = []
            
            for idx, assigned_tasks in task_assignments.items():
                if assigned_tasks:
                    future = executor.submit(
                        self._matchers[idx].match_batch,
                        assigned_tasks
                    )
                    futures.append(future)
            
            for future in as_completed(futures):
                results = future.result()
                all_results.extend(results)
        
        return all_results
    
    def get_all_stats(self) -> List[Dict[str, Any]]:
        """Get stats from all matchers"""
        return [m.get_stats() for m in self._matchers]
    
    def close(self):
        """Close all matchers"""
        for matcher in self._matchers:
            matcher.close()
