"""
LRU Cache for Embeddings

High-performance caching for vector embeddings with:
- Thread-safe LRU eviction
- Size-based limits (count and memory)
- TTL support
- Similarity-aware caching
- Persistence support
"""

import threading
import hashlib
import pickle
import logging
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import sys
import os

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    key: str
    value: Any
    size_bytes: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[int] = None  # Seconds
    
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def touch(self):
        """Update access time and count"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class LRUCache:
    """
    Thread-safe LRU cache with size limits
    """
    
    def __init__(self, max_size: int = 1000, 
                 max_memory_mb: float = 100,
                 default_ttl: int = None):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default TTL in seconds (None = no expiry)
        """
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.default_ttl = default_ttl
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._current_memory = 0
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
        
        logger.info(f"LRUCache initialized: max_size={max_size}, max_memory={max_memory_mb}MB")
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value in bytes"""
        try:
            if hasattr(value, 'nbytes'):  # NumPy array
                return value.nbytes
            elif isinstance(value, (list, tuple)):
                # Estimate list/tuple of floats
                if value and isinstance(value[0], (int, float)):
                    return len(value) * 8  # 8 bytes per float
                return sys.getsizeof(value)
            else:
                return sys.getsizeof(value)
        except Exception:
            return 1024  # Default estimate
    
    def _evict_if_needed(self):
        """Evict entries if over limits"""
        # Check size limit
        while len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        # Check memory limit
        while self._current_memory > self.max_memory_bytes and self._cache:
            self._evict_oldest()
    
    def _evict_oldest(self):
        """Evict the oldest (least recently used) entry"""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size_bytes
            self._stats['evictions'] += 1
            logger.debug(f"Evicted cache entry: {key}")
    
    def _remove_expired(self):
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            entry = self._cache.pop(key)
            self._current_memory -= entry.size_bytes
            self._stats['expirations'] += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiry
            if entry.is_expired():
                self._cache.pop(key)
                self._current_memory -= entry.size_bytes
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            
            self._stats['hits'] += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        with self._lock:
            size = self._estimate_size(value)
            ttl = ttl or self.default_ttl
            
            # Remove existing entry if present
            if key in self._cache:
                old_entry = self._cache.pop(key)
                self._current_memory -= old_entry.size_bytes
            
            # Make room if needed
            self._evict_if_needed()
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                size_bytes=size,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl=ttl
            )
            
            self._cache[key] = entry
            self._current_memory += size
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self._current_memory -= entry.size_bytes
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                self._cache.pop(key)
                self._current_memory -= entry.size_bytes
                return False
            
            return True
    
    def clear(self):
        """Clear all entries"""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total if total > 0 else 0
            
            return {
                **self._stats,
                'size': len(self._cache),
                'memory_bytes': self._current_memory,
                'memory_mb': self._current_memory / (1024 * 1024),
                'hit_rate': hit_rate,
                'max_size': self.max_size,
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024)
            }
    
    def cleanup(self):
        """Remove expired entries"""
        with self._lock:
            self._remove_expired()


class EmbeddingCache:
    """
    Specialized cache for vector embeddings with similarity-aware features
    """
    
    def __init__(self, max_embeddings: int = 10000,
                 max_memory_mb: float = 500,
                 default_ttl: int = 86400,  # 24 hours
                 similarity_threshold: float = 0.95,
                 persist_path: Optional[str] = None):
        """
        Initialize embedding cache
        
        Args:
            max_embeddings: Maximum number of embeddings to cache
            max_memory_mb: Maximum memory for embeddings in MB
            default_ttl: Default TTL in seconds
            similarity_threshold: Threshold for similarity-based cache hits
            persist_path: Path to persist cache (optional)
        """
        self._cache = LRUCache(
            max_size=max_embeddings,
            max_memory_mb=max_memory_mb,
            default_ttl=default_ttl
        )
        
        self.similarity_threshold = similarity_threshold
        self.persist_path = persist_path
        
        # Text hash to embedding key mapping
        self._text_hashes: Dict[str, str] = {}
        self._hash_lock = threading.Lock()
        
        # Load persisted cache if exists
        if persist_path and os.path.exists(persist_path):
            self._load_from_disk()
        
        logger.info(f"EmbeddingCache initialized: max={max_embeddings}, memory={max_memory_mb}MB")
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text"""
        normalized = text.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    def get_embedding(self, text: str, model: str = "default") -> Optional[List[float]]:
        """
        Get cached embedding for text
        
        Args:
            text: Input text
            model: Model identifier
            
        Returns:
            Cached embedding or None if not found
        """
        text_hash = self._hash_text(text)
        cache_key = f"{model}:{text_hash}"
        
        return self._cache.get(cache_key)
    
    def set_embedding(self, text: str, embedding: List[float], 
                      model: str = "default", ttl: int = None) -> bool:
        """
        Cache an embedding for text
        
        Args:
            text: Input text
            embedding: Vector embedding
            model: Model identifier
            ttl: Optional TTL override
            
        Returns:
            True if cached successfully
        """
        text_hash = self._hash_text(text)
        cache_key = f"{model}:{text_hash}"
        
        # Store hash mapping
        with self._hash_lock:
            self._text_hashes[text_hash] = cache_key
        
        return self._cache.set(cache_key, embedding, ttl)
    
    def get_or_compute(self, text: str, compute_fn: Callable[[str], List[float]],
                       model: str = "default", ttl: int = None) -> List[float]:
        """
        Get embedding from cache or compute if not found
        
        Args:
            text: Input text
            compute_fn: Function to compute embedding if not cached
            model: Model identifier
            ttl: Optional TTL override
            
        Returns:
            Embedding vector
        """
        # Try cache first
        embedding = self.get_embedding(text, model)
        if embedding is not None:
            return embedding
        
        # Compute and cache
        embedding = compute_fn(text)
        self.set_embedding(text, embedding, model, ttl)
        
        return embedding
    
    def batch_get(self, texts: List[str], model: str = "default"
                  ) -> Tuple[Dict[str, List[float]], List[str]]:
        """
        Batch get embeddings
        
        Args:
            texts: List of texts
            model: Model identifier
            
        Returns:
            Tuple of (cached_embeddings dict, uncached_texts list)
        """
        cached = {}
        uncached = []
        
        for text in texts:
            embedding = self.get_embedding(text, model)
            if embedding is not None:
                cached[text] = embedding
            else:
                uncached.append(text)
        
        return cached, uncached
    
    def batch_set(self, embeddings: Dict[str, List[float]], 
                  model: str = "default", ttl: int = None) -> int:
        """
        Batch set embeddings
        
        Args:
            embeddings: Dict mapping text to embedding
            model: Model identifier
            ttl: Optional TTL override
            
        Returns:
            Number of embeddings cached
        """
        count = 0
        for text, embedding in embeddings.items():
            if self.set_embedding(text, embedding, model, ttl):
                count += 1
        return count
    
    def find_similar(self, query_embedding: List[float], 
                     top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar cached embeddings
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of (cache_key, similarity) tuples
        """
        results = []
        
        with self._cache._lock:
            for key, entry in self._cache._cache.items():
                if entry.is_expired():
                    continue
                
                similarity = self._cosine_similarity(query_embedding, entry.value)
                if similarity >= self.similarity_threshold:
                    results.append((key, similarity))
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self._cache.get_stats()
        stats['text_hashes'] = len(self._text_hashes)
        return stats
    
    def clear(self):
        """Clear all cached embeddings"""
        self._cache.clear()
        with self._hash_lock:
            self._text_hashes.clear()
    
    def cleanup(self):
        """Remove expired entries"""
        self._cache.cleanup()
    
    def persist(self):
        """Persist cache to disk"""
        if not self.persist_path:
            return
        
        try:
            with self._cache._lock:
                data = {
                    'cache': dict(self._cache._cache),
                    'text_hashes': self._text_hashes,
                    'stats': self._cache._stats
                }
            
            with open(self.persist_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Persisted {len(self._cache._cache)} embeddings to {self.persist_path}")
            
        except Exception as e:
            logger.error(f"Failed to persist cache: {e}")
    
    def _load_from_disk(self):
        """Load cache from disk"""
        try:
            with open(self.persist_path, 'rb') as f:
                data = pickle.load(f)
            
            with self._cache._lock:
                self._cache._cache = OrderedDict(data['cache'])
                self._cache._current_memory = sum(
                    e.size_bytes for e in self._cache._cache.values()
                )
                self._cache._stats = data.get('stats', self._cache._stats)
            
            with self._hash_lock:
                self._text_hashes = data.get('text_hashes', {})
            
            logger.info(f"Loaded {len(self._cache._cache)} embeddings from {self.persist_path}")
            
        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}")


class MultiTierCache:
    """
    Multi-tier caching: L1 (memory) -> L2 (Redis) -> Compute
    """
    
    def __init__(self, l1_max_size: int = 1000,
                 l1_max_memory_mb: float = 100,
                 enable_l2: bool = True):
        """
        Initialize multi-tier cache
        
        Args:
            l1_max_size: L1 (memory) max entries
            l1_max_memory_mb: L1 memory limit
            enable_l2: Enable Redis as L2 cache
        """
        # L1: In-memory LRU cache
        self._l1 = LRUCache(
            max_size=l1_max_size,
            max_memory_mb=l1_max_memory_mb,
            default_ttl=3600  # 1 hour
        )
        
        # L2: Redis cache
        self._l2 = None
        if enable_l2:
            try:
                from .redis_cache import RedisCache
                self._l2 = RedisCache()
            except Exception as e:
                logger.warning(f"L2 cache (Redis) unavailable: {e}")
        
        self._stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get from multi-tier cache"""
        # Try L1
        value = self._l1.get(key)
        if value is not None:
            self._stats['l1_hits'] += 1
            return value
        
        # Try L2
        if self._l2:
            value = self._l2.get(key)
            if value is not None:
                # Promote to L1
                self._l1.set(key, value)
                self._stats['l2_hits'] += 1
                return value
        
        self._stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set in multi-tier cache"""
        # Set in L1
        self._l1.set(key, value, ttl)
        
        # Set in L2
        if self._l2:
            self._l2.set(key, value, ttl or 86400)  # 24h default for L2
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete from all tiers"""
        l1_deleted = self._l1.delete(key)
        l2_deleted = self._l2.delete(key) if self._l2 else False
        return l1_deleted or l2_deleted
    
    def get_or_compute(self, key: str, compute_fn: Callable[[], Any],
                       ttl: int = None) -> Any:
        """Get from cache or compute"""
        value = self.get(key)
        if value is not None:
            return value
        
        value = compute_fn()
        self.set(key, value, ttl)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        total = sum(self._stats.values())
        return {
            **self._stats,
            'l1_stats': self._l1.get_stats(),
            'l2_stats': self._l2.get_stats() if self._l2 else None,
            'l1_hit_rate': self._stats['l1_hits'] / total if total > 0 else 0,
            'l2_hit_rate': self._stats['l2_hits'] / total if total > 0 else 0
        }
