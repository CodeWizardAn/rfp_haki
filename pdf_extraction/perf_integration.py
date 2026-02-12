"""
PDF Extraction Performance Integration
======================================
Integrates performance optimizations into PDF extraction operations.

Usage:
    from pdf_extraction.perf_integration import init_pdf_performance
    
    # Initialize at app startup
    init_pdf_performance(app)
"""

import logging
import time
import functools
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import performance module
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from performance.integration import (
        get_performance_manager,
        init_performance,
        shutdown_performance,
        cached,
        rate_limited,
        profiled,
        integrate_flask_app,
        EmbeddingPerformanceOptimizer,
        AgentPerformanceTracker
    )
    from performance.batch_processor import BatchProcessor, BatchConfig
    from performance.parallel_matcher import ParallelMatcher
    
    PERFORMANCE_AVAILABLE = True
    logger.info("Performance module loaded for PDF extraction")
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    logger.warning(f"Performance module not available: {e}")


# =============================================================================
# PDF Processing Optimization
# =============================================================================

class PDFProcessingOptimizer:
    """
    Optimizes PDF processing operations
    """
    
    def __init__(self):
        self.pm = None
        self.embedding_optimizer = None
        self.parallel_matcher = None
        self._text_cache = {}
        self._match_cache = {}
        
        if PERFORMANCE_AVAILABLE:
            self.pm = get_performance_manager()
            try:
                self.embedding_optimizer = EmbeddingPerformanceOptimizer()
            except Exception as e:
                logger.warning(f"Could not initialize EmbeddingPerformanceOptimizer: {e}")
            try:
                self.parallel_matcher = ParallelMatcher(num_workers=4, chunk_size=100)
            except Exception as e:
                logger.warning(f"Could not initialize ParallelMatcher: {e}")
    
    def cache_extracted_text(self, file_hash: str, text: str, ttl: int = 3600):
        """
        Cache extracted PDF text
        
        Args:
            file_hash: Hash of PDF file
            text: Extracted text
            ttl: Cache TTL in seconds
        """
        if self.pm:
            self.pm.cache.set(f"pdf:text:{file_hash}", text, ttl=ttl)
        else:
            self._text_cache[file_hash] = {
                'text': text,
                'expires': time.time() + ttl
            }
    
    def get_cached_text(self, file_hash: str) -> Optional[str]:
        """
        Get cached extracted text
        
        Args:
            file_hash: Hash of PDF file
            
        Returns:
            Extracted text or None
        """
        if self.pm:
            return self.pm.cache.get(f"pdf:text:{file_hash}")
        
        entry = self._text_cache.get(file_hash)
        if entry and entry['expires'] > time.time():
            return entry['text']
        return None
    
    def parallel_match_terms(self, text: str, terms: List[str]) -> List[Dict[str, Any]]:
        """
        Match RFP terms in parallel
        
        Args:
            text: Document text
            terms: List of terms to match
            
        Returns:
            List of match results
        """
        if not self.parallel_matcher:
            # Fallback to sequential matching
            matches = []
            text_lower = text.lower()
            for term in terms:
                if term.lower() in text_lower:
                    matches.append({
                        'term': term,
                        'found': True,
                        'count': text_lower.count(term.lower())
                    })
            return matches
        
        # Parallel matching
        def match_term(term):
            text_lower = text.lower()
            term_lower = term.lower()
            
            if term_lower in text_lower:
                return {
                    'term': term,
                    'found': True,
                    'count': text_lower.count(term_lower)
                }
            return {'term': term, 'found': False, 'count': 0}
        
        results = self.parallel_matcher.map(match_term, terms)
        return [r for r in results if r['found']]
    
    def batch_process_pages(self, pages: List[Any], process_func: Callable) -> List[Any]:
        """
        Process PDF pages in batches
        
        Args:
            pages: List of PDF pages
            process_func: Function to process each page
            
        Returns:
            List of processed results
        """
        if PERFORMANCE_AVAILABLE:
            batch_processor = BatchProcessor(BatchConfig(batch_size=10, max_workers=4))
            result = batch_processor.process(pages, process_func)
            return result.results
        
        # Fallback to sequential
        return [process_func(page) for page in pages]
    
    def optimized_similarity_search(self, query_embedding: List[float],
                                     document_embeddings: List[List[float]],
                                     top_k: int = 10) -> List[int]:
        """
        Optimized similarity search for matching
        
        Args:
            query_embedding: Query vector
            document_embeddings: Document vectors
            top_k: Number of top results
            
        Returns:
            Indices of top matches
        """
        if self.embedding_optimizer:
            return self.embedding_optimizer.parallel_similarity_search(
                query_embedding, document_embeddings, top_k
            )
        
        # Fallback to simple search
        def cosine_sim(emb):
            dot = sum(a * b for a, b in zip(query_embedding, emb))
            norm_q = sum(a * a for a in query_embedding) ** 0.5
            norm_e = sum(a * a for a in emb) ** 0.5
            return dot / (norm_q * norm_e) if norm_q and norm_e else 0
        
        scores = [(i, cosine_sim(emb)) for i, emb in enumerate(document_embeddings)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in scores[:top_k]]


# Global optimizer instance
_pdf_optimizer: Optional[PDFProcessingOptimizer] = None


def get_pdf_optimizer() -> PDFProcessingOptimizer:
    """Get the global PDF processing optimizer"""
    global _pdf_optimizer
    if _pdf_optimizer is None:
        _pdf_optimizer = PDFProcessingOptimizer()
    return _pdf_optimizer


# =============================================================================
# Flask Integration
# =============================================================================

def init_pdf_performance(app):
    """
    Initialize performance optimizations for PDF extraction Flask app
    
    Args:
        app: Flask application instance
    """
    if not PERFORMANCE_AVAILABLE:
        logger.warning("Performance module not available, skipping PDF optimization")
        return None
    
    # Integrate with Flask app
    pm = integrate_flask_app(app)
    
    # Initialize PDF optimizer
    optimizer = get_pdf_optimizer()
    
    # Add PDF-specific performance endpoints
    @app.route('/api/pdf/performance/stats')
    def pdf_performance_stats():
        from flask import jsonify
        
        return jsonify({
            'performance_enabled': True,
            'cache_stats': pm.cache.get_stats() if hasattr(pm.cache, 'get_stats') else {},
            'embedding_cache_stats': pm.embedding_cache.get_stats(),
            'timestamp': datetime.now().isoformat()
        })
    
    logger.info("PDF extraction performance integration complete")
    return pm


# =============================================================================
# Decorators for PDF Operations
# =============================================================================

def cache_extraction(ttl: int = 3600):
    """
    Cache PDF extraction results
    
    Args:
        ttl: Cache TTL in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(file_path: str, *args, **kwargs):
            optimizer = get_pdf_optimizer()
            
            # Generate file hash
            import hashlib
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Check cache
            cached = optimizer.get_cached_text(file_hash)
            if cached:
                logger.debug(f"Cache hit for PDF: {file_path}")
                return cached
            
            # Extract and cache
            result = func(file_path, *args, **kwargs)
            optimizer.cache_extracted_text(file_hash, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def rate_limit_upload(requests_per_minute: int = 10):
    """
    Rate limit PDF uploads
    
    Args:
        requests_per_minute: Maximum uploads per minute
    """
    if not PERFORMANCE_AVAILABLE:
        return lambda f: f
    
    return rate_limited(requests_per_minute=requests_per_minute)


# Export
__all__ = [
    'PDFProcessingOptimizer',
    'get_pdf_optimizer',
    'init_pdf_performance',
    'cache_extraction',
    'rate_limit_upload',
    'PERFORMANCE_AVAILABLE'
]
