"""
Vector Embedding System using Sentence Transformers
Comprehensive semantic search with ChromaDB integration

Features:
1. Sentence transformer model initialization
2. Product text generation
3. Embedding generation pipeline
4. ChromaDB integration
5. Batch embedding processor
6. Semantic search
7. Embedding caching
8. Similarity ranking
9. Hybrid search (vector + keyword)
10. Embedding update mechanism
"""

import os
import json
import hashlib
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for required dependencies
SENTENCE_TRANSFORMERS_AVAILABLE = False
CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.info("sentence-transformers not installed — using built-in LightweightSemanticEmbedder fallback.")


class LightweightSemanticEmbedder:
    """
    Drop-in lightweight semantic embedding engine (384 dimensions).
    Used when sentence-transformers/PyTorch is not installed.
    Provides deterministic domain-aware dense vectors with true cosine similarity.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def get_sentence_embedding_dimension(self) -> int:
        return self.dimension

    def encode(self, sentences, normalize_embeddings: bool = True, batch_size: int = 32, show_progress_bar: bool = False):
        is_single = isinstance(sentences, str)
        items = [sentences] if is_single else list(sentences)
        vectors = []
        for text in items:
            v = self._embed_single(str(text))
            vectors.append(v)
        if NUMPY_AVAILABLE:
            arr = np.array(vectors, dtype=np.float32)
            return arr[0] if is_single else arr
        return vectors[0] if is_single else vectors

    def _embed_single(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        if not text:
            return vec
        tokens = re.findall(r'[a-zA-Z0-9_\.]+', text.lower())
        for token in tokens:
            weight = 1.0
            # Boost domain keywords
            if any(k in token for k in ['cu', 'copper', 'al', 'aluminium', 'xlpe', 'pvc', 'kv', 'sqmm', 'frls', 'armour']):
                weight = 2.5
            h = int(hashlib.md5(token.encode('utf-8')).hexdigest()[:8], 16)
            idx = h % self.dimension
            sign = 1.0 if (h & 1) else -1.0
            vec[idx] += sign * weight
            # Character n-grams for typo & morphology tolerance
            for i in range(len(token) - 2):
                ngram = token[i:i+3]
                nh = int(hashlib.md5(ngram.encode('utf-8')).hexdigest()[:8], 16)
                nidx = nh % self.dimension
                nsign = 1.0 if (nh & 1) else -1.0
                vec[nidx] += nsign * 0.4
        # L2 Normalization
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        return vec

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB not installed. Run: pip install chromadb")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not installed. Some features may be limited.")


# ============================================================================
# Enums and Data Classes
# ============================================================================

class EmbeddingModel(Enum):
    """Supported embedding models"""
    MINILM_L6 = "all-MiniLM-L6-v2"          # Fast, good quality (384 dim)
    MINILM_L12 = "all-MiniLM-L12-v2"        # Better quality (384 dim)
    MPNET_BASE = "all-mpnet-base-v2"         # Best quality (768 dim)
    DISTILBERT = "multi-qa-distilbert-cos-v1"  # Q&A optimized (768 dim)
    PARAPHRASE = "paraphrase-MiniLM-L6-v2"   # Paraphrase detection (384 dim)


class SearchMode(Enum):
    """Search modes"""
    SEMANTIC = "semantic"       # Vector similarity only
    KEYWORD = "keyword"         # Keyword matching only
    HYBRID = "hybrid"           # Combined vector + keyword


@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]
    hash: str
    generated_at: str


@dataclass
class SearchResult:
    """Result of semantic search"""
    id: str
    text: str
    score: float
    semantic_score: float
    keyword_score: float
    metadata: Dict[str, Any]
    match_type: str


@dataclass
class CacheEntry:
    """Cache entry for embeddings"""
    embedding: List[float]
    hash: str
    created_at: str
    access_count: int = 0
    last_accessed: str = ""


@dataclass
class BatchResult:
    """Result of batch embedding operation"""
    total_items: int
    processed: int
    cached: int
    failed: int
    processing_time_ms: float
    embeddings: List[EmbeddingResult]


# ============================================================================
# 1. Sentence Transformer Model Initialization
# ============================================================================

class EmbeddingModelManager:
    """
    Manages sentence transformer models for generating embeddings.
    Supports multiple models with lazy loading.
    """
    
    _instances: Dict[str, 'SentenceTransformer'] = {}
    _default_model: str = EmbeddingModel.MINILM_L6.value
    
    @classmethod
    def get_model(cls, model_name: str = None, allow_fallback: bool = False) -> Optional['SentenceTransformer']:
        """
        Get or load a sentence transformer model.
        
        Args:
            model_name: Name of the model to load
            allow_fallback: Whether to return lightweight embedder if sentence-transformers is missing
            
        Returns:
            Loaded SentenceTransformer model or LightweightSemanticEmbedder
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            if allow_fallback:
                if "_lightweight" not in cls._instances:
                    logger.info("Using built-in LightweightSemanticEmbedder (384 dim)")
                    cls._instances["_lightweight"] = LightweightSemanticEmbedder()
                return cls._instances["_lightweight"]
            logger.error("sentence-transformers not available")
            return None
        
        model_name = model_name or cls._default_model
        
        if model_name not in cls._instances:
            try:
                logger.info(f"Loading embedding model: {model_name}")
                cls._instances[model_name] = SentenceTransformer(model_name)
                logger.info(f"✅ Model loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                return None
        
        return cls._instances[model_name]
    
    @classmethod
    def set_default_model(cls, model_name: str):
        """Set the default model"""
        cls._default_model = model_name
    
    @classmethod
    def get_embedding_dimension(cls, model_name: str = None) -> int:
        """Get the embedding dimension for a model"""
        model = cls.get_model(model_name)
        if model:
            return model.get_sentence_embedding_dimension()
        return 384  # Default dimension
    
    @classmethod
    def unload_model(cls, model_name: str):
        """Unload a model to free memory"""
        if model_name in cls._instances:
            del cls._instances[model_name]
            logger.info(f"Unloaded model: {model_name}")


# ============================================================================
# 2. Product Text Generator
# ============================================================================

class ProductTextGenerator:
    """
    Generates searchable text representations from product specifications.
    """
    
    # Fields to include in product text (in priority order)
    PRODUCT_FIELDS = [
        ('name', 'Product: {value}'),
        ('description', '{value}'),
        ('sku', 'SKU: {value}'),
        ('manufacturer', 'Manufacturer: {value}'),
        ('oem', 'OEM: {value}'),
        ('category', 'Category: {value}'),
        ('conductor_material', 'Conductor Material: {value}'),
        ('conductor_size_sqmm', 'Conductor Size: {value} sq mm'),
        ('cross_section_sqmm', 'Cross Section: {value} sq mm'),
        ('insulation_type', 'Insulation: {value}'),
        ('voltage_rating', 'Voltage Rating: {value}'),
        ('rated_voltage', 'Rated Voltage: {value}'),
        ('number_of_cores', 'Cores: {value}'),
        ('temperature_rating', 'Temperature: {value}'),
        ('armour_type', 'Armour: {value}'),
        ('outer_sheath', 'Sheath: {value}'),
        ('standard', 'Standard: {value}'),
        ('certifications', 'Certifications: {value}'),
    ]
    
    # RFP requirement fields
    RFP_FIELDS = [
        ('original_text', '{value}'),
        ('product_name', 'Product: {value}'),
        ('product_type', 'Type: {value}'),
        ('conductor_material', 'Material: {value}'),
        ('conductor_size_sqmm', 'Size: {value} sq mm'),
        ('insulation_type', 'Insulation: {value}'),
        ('voltage_grade', 'Voltage: {value}'),
        ('quantity', 'Quantity: {value}'),
        ('unit', 'Unit: {value}'),
        ('standards', 'Standards: {value}'),
    ]
    
    @classmethod
    def generate_product_text(
        cls,
        product: Dict[str, Any],
        include_specs: bool = True,
        max_length: int = 1000
    ) -> str:
        """
        Generate searchable text from product data.
        
        Args:
            product: Product dictionary
            include_specs: Include specifications dict if present
            max_length: Maximum text length
            
        Returns:
            Searchable text representation
        """
        parts = []
        
        # Process standard fields
        for field, template in cls.PRODUCT_FIELDS:
            value = product.get(field)
            if value is not None and str(value).strip():
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                parts.append(template.format(value=value))
        
        # Include specifications dict if present
        if include_specs and 'specifications' in product:
            specs = product['specifications']
            if isinstance(specs, dict):
                for key, value in specs.items():
                    if value is not None and str(value).strip():
                        clean_key = key.replace('_', ' ').title()
                        parts.append(f"{clean_key}: {value}")
        
        text = ' | '.join(parts)
        
        # Truncate if needed
        if len(text) > max_length:
            text = text[:max_length - 3] + '...'
        
        return text
    
    @classmethod
    def generate_rfp_text(
        cls,
        requirement: Dict[str, Any],
        max_length: int = 1000
    ) -> str:
        """
        Generate searchable text from RFP requirement.
        
        Args:
            requirement: Requirement dictionary
            max_length: Maximum text length
            
        Returns:
            Searchable text representation
        """
        parts = []
        
        for field, template in cls.RFP_FIELDS:
            value = requirement.get(field)
            if value is not None and str(value).strip():
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                parts.append(template.format(value=value))
        
        # Include any specifications
        if 'specifications' in requirement:
            specs = requirement['specifications']
            if isinstance(specs, dict):
                for key, value in specs.items():
                    if value is not None:
                        clean_key = key.replace('_', ' ').title()
                        parts.append(f"{clean_key}: {value}")
        
        text = ' | '.join(parts)
        
        if len(text) > max_length:
            text = text[:max_length - 3] + '...'
        
        return text
    
    @classmethod
    def generate_search_text(cls, query: str, context: Dict[str, Any] = None) -> str:
        """
        Generate optimized search text from query and context.
        
        Args:
            query: Search query
            context: Additional context (filters, specs, etc.)
            
        Returns:
            Optimized search text
        """
        parts = [query]
        
        if context:
            for key, value in context.items():
                if value is not None and str(value).strip():
                    clean_key = key.replace('_', ' ').title()
                    parts.append(f"{clean_key}: {value}")
        
        return ' | '.join(parts)


# ============================================================================
# 3. Embedding Generation Pipeline
# ============================================================================

class EmbeddingPipeline:
    """
    Pipeline for generating embeddings from text.
    """
    
    def __init__(
        self,
        model_name: str = None,
        normalize: bool = True,
        batch_size: int = 32
    ):
        """
        Initialize the embedding pipeline.
        
        Args:
            model_name: Name of the embedding model
            normalize: Whether to normalize embeddings
            batch_size: Default batch size for processing
        """
        self.model_name = model_name or EmbeddingModel.MINILM_L6.value
        self.normalize = normalize
        self.batch_size = batch_size
        self._model = None
    
    @property
    def model(self):
        """Lazy load the model"""
        if self._model is None:
            self._model = EmbeddingModelManager.get_model(self.model_name, allow_fallback=True)
        return self._model
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list
        """
        if not self.model:
            return None
        
        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=self.normalize,
                show_progress_bar=False
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not self.model or not texts:
            return []
        
        batch_size = batch_size or self.batch_size
        
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=self.normalize,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return []
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score (0-1)
        """
        if NUMPY_AVAILABLE:
            a = np.array(embedding1)
            b = np.array(embedding2)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        else:
            # Manual computation
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            norm1 = sum(a * a for a in embedding1) ** 0.5
            norm2 = sum(b * b for b in embedding2) ** 0.5
            return dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0.0


# ============================================================================
# 4. ChromaDB Integration
# ============================================================================

class ChromaDBEmbeddingStore:
    """
    ChromaDB-based embedding storage and retrieval.
    """
    
    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "product_embeddings"
    ):
        """
        Initialize ChromaDB embedding store.
        
        Args:
            persist_directory: Directory for persistence
            collection_name: Name of the collection
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed")
        
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent / "db_vector")
        
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection_name = collection_name
        self._collection = None
        
        logger.info(f"✅ ChromaDB store initialized: {persist_directory}")
    
    @property
    def collection(self):
        """Get or create the collection"""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
    
    def add_embeddings(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]] = None
    ) -> int:
        """
        Add embeddings to the store.
        
        Args:
            ids: Unique identifiers
            embeddings: Embedding vectors
            documents: Original texts
            metadatas: Metadata for each embedding
            
        Returns:
            Number of embeddings added
        """
        if not ids or not embeddings:
            return 0
        
        # Ensure metadatas
        if metadatas is None:
            metadatas = [{}] * len(ids)
        
        # Clean metadata (ChromaDB only accepts str, int, float, bool)
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if v is None:
                    clean_meta[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif isinstance(v, list):
                    clean_meta[k] = ", ".join(str(x) for x in v)
                else:
                    clean_meta[k] = str(v)
            clean_metadatas.append(clean_meta)
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_metadatas
        )
        
        return len(ids)
    
    def query_by_embedding(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Dict = None,
        include_embeddings: bool = False
    ) -> Dict[str, Any]:
        """
        Query by embedding vector.
        
        Args:
            query_embedding: Query embedding
            n_results: Number of results
            where: Metadata filters
            include_embeddings: Include embeddings in results
            
        Returns:
            Query results
        """
        include = ['documents', 'metadatas', 'distances']
        if include_embeddings:
            include.append('embeddings')
        
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=include
        )
    
    def query_by_text(
        self,
        query_text: str,
        n_results: int = 10,
        where: Dict = None
    ) -> Dict[str, Any]:
        """
        Query by text (requires embedding function on collection).
        
        Args:
            query_text: Query text
            n_results: Number of results
            where: Metadata filters
            
        Returns:
            Query results
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances']
        )
    
    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """Get embeddings by IDs"""
        return self.collection.get(
            ids=ids,
            include=['documents', 'metadatas', 'embeddings']
        )
    
    def delete_by_ids(self, ids: List[str]):
        """Delete embeddings by IDs"""
        self.collection.delete(ids=ids)
    
    def count(self) -> int:
        """Get total count of embeddings"""
        return self.collection.count()
    
    def clear(self):
        """Clear all embeddings"""
        self.client.delete_collection(self.collection_name)
        self._collection = None
        logger.info(f"Cleared collection: {self.collection_name}")


# ============================================================================
# 5. Batch Embedding Processor
# ============================================================================

class BatchEmbeddingProcessor:
    """
    Efficient batch processing for large product catalogs.
    """
    
    def __init__(
        self,
        pipeline: EmbeddingPipeline = None,
        store: ChromaDBEmbeddingStore = None,
        cache: 'EmbeddingCache' = None,
        batch_size: int = 100
    ):
        """
        Initialize batch processor.
        
        Args:
            pipeline: Embedding pipeline
            store: ChromaDB store
            cache: Embedding cache
            batch_size: Batch size for processing
        """
        self.pipeline = pipeline or EmbeddingPipeline()
        self.store = store
        self.cache = cache
        self.batch_size = batch_size
    
    def process_products(
        self,
        products: List[Dict[str, Any]],
        id_field: str = 'sku',
        use_cache: bool = True
    ) -> BatchResult:
        """
        Process products and generate embeddings.
        
        Args:
            products: List of product dictionaries
            id_field: Field to use as ID
            use_cache: Whether to use embedding cache
            
        Returns:
            BatchResult with processed embeddings
        """
        start_time = datetime.now()
        results = []
        processed = 0
        cached = 0
        failed = 0
        
        # Separate cached and uncached items
        to_process = []
        for product in products:
            product_id = str(product.get(id_field, len(results)))
            text = ProductTextGenerator.generate_product_text(product)
            text_hash = self._compute_hash(text)
            
            # Check cache
            if use_cache and self.cache:
                cached_entry = self.cache.get(product_id)
                if cached_entry and cached_entry.hash == text_hash:
                    results.append(EmbeddingResult(
                        id=product_id,
                        text=text,
                        embedding=cached_entry.embedding,
                        metadata=self._extract_metadata(product),
                        hash=text_hash,
                        generated_at=cached_entry.created_at
                    ))
                    cached += 1
                    continue
            
            to_process.append({
                'id': product_id,
                'text': text,
                'hash': text_hash,
                'product': product
            })
        
        # Process in batches
        for i in range(0, len(to_process), self.batch_size):
            batch = to_process[i:i + self.batch_size]
            texts = [item['text'] for item in batch]
            
            # Generate embeddings
            embeddings = self.pipeline.generate_embeddings(texts)
            
            for j, item in enumerate(batch):
                if j < len(embeddings) and embeddings[j]:
                    embedding = embeddings[j]
                    result = EmbeddingResult(
                        id=item['id'],
                        text=item['text'],
                        embedding=embedding,
                        metadata=self._extract_metadata(item['product']),
                        hash=item['hash'],
                        generated_at=datetime.now().isoformat()
                    )
                    results.append(result)
                    processed += 1
                    
                    # Cache the embedding
                    if self.cache:
                        self.cache.set(item['id'], embedding, item['hash'])
                else:
                    failed += 1
        
        # Store in ChromaDB if available
        if self.store and results:
            self.store.add_embeddings(
                ids=[r.id for r in results],
                embeddings=[r.embedding for r in results],
                documents=[r.text for r in results],
                metadatas=[r.metadata for r in results]
            )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return BatchResult(
            total_items=len(products),
            processed=processed,
            cached=cached,
            failed=failed,
            processing_time_ms=processing_time,
            embeddings=results
        )
    
    def _compute_hash(self, text: str) -> str:
        """Compute hash of text for cache validation"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _extract_metadata(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from product"""
        fields = [
            'sku', 'name', 'manufacturer', 'oem', 'category',
            'conductor_material', 'insulation_type', 'conductor_size_sqmm',
            'voltage_rating', 'number_of_cores'
        ]
        return {k: product.get(k, '') for k in fields if product.get(k)}


# ============================================================================
# 6. Semantic Search Function
# ============================================================================

class SemanticSearch:
    """
    Semantic search functionality for products and RFP requirements.
    """
    
    def __init__(
        self,
        pipeline: EmbeddingPipeline = None,
        store: ChromaDBEmbeddingStore = None
    ):
        """
        Initialize semantic search.
        
        Args:
            pipeline: Embedding pipeline
            store: ChromaDB store
        """
        self.pipeline = pipeline or EmbeddingPipeline()
        self.store = store
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        filters: Dict[str, Any] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Perform semantic search.
        
        Args:
            query: Search query
            n_results: Number of results
            filters: Metadata filters
            min_score: Minimum similarity score
            
        Returns:
            List of search results
        """
        if not self.store:
            logger.error("No embedding store configured")
            return []
        
        # Generate query embedding
        query_embedding = self.pipeline.generate_embedding(query)
        if not query_embedding:
            return []
        
        # Build where clause
        where = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if value is not None:
                    if isinstance(value, list):
                        conditions.append({key: {"$in": value}})
                    else:
                        conditions.append({key: str(value)})
            if conditions:
                where = {"$and": conditions} if len(conditions) > 1 else conditions[0]
        
        # Query ChromaDB
        results = self.store.query_by_embedding(
            query_embedding,
            n_results=n_results,
            where=where
        )
        
        # Format results
        search_results = []
        if results['ids'] and results['ids'][0]:
            for i, id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = 1 - distance  # Convert distance to similarity
                
                if similarity >= min_score:
                    search_results.append(SearchResult(
                        id=id,
                        text=results['documents'][0][i] if results['documents'] else '',
                        score=similarity,
                        semantic_score=similarity,
                        keyword_score=0.0,
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                        match_type='semantic'
                    ))
        
        return search_results
    
    def find_similar(
        self,
        product_id: str,
        n_results: int = 5,
        exclude_self: bool = True
    ) -> List[SearchResult]:
        """
        Find similar products to a given product.
        
        Args:
            product_id: ID of the reference product
            n_results: Number of results
            exclude_self: Exclude the reference product
            
        Returns:
            List of similar products
        """
        if not self.store:
            return []
        
        # Get the product embedding
        product = self.store.get_by_ids([product_id])
        embeddings = product.get('embeddings')
        if embeddings is None:
            return []
        
        # Handle both list and numpy array cases
        try:
            if len(embeddings) == 0:
                return []
            embedding = embeddings[0]
            if embedding is None:
                return []
            if hasattr(embedding, '__len__') and len(embedding) == 0:
                return []
        except (TypeError, ValueError):
            return []
        
        # Search for similar
        results = self.store.query_by_embedding(
            embedding,
            n_results=n_results + (1 if exclude_self else 0)
        )
        
        # Format and filter results
        search_results = []
        if results['ids'] and results['ids'][0]:
            for i, id in enumerate(results['ids'][0]):
                if exclude_self and id == product_id:
                    continue
                
                distance = results['distances'][0][i] if results['distances'] else 0
                search_results.append(SearchResult(
                    id=id,
                    text=results['documents'][0][i] if results['documents'] else '',
                    score=1 - distance,
                    semantic_score=1 - distance,
                    keyword_score=0.0,
                    metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                    match_type='similarity'
                ))
                
                if len(search_results) >= n_results:
                    break
        
        return search_results


# ============================================================================
# 7. Embedding Caching
# ============================================================================

class EmbeddingCache:
    """
    Caching layer for embeddings to avoid regeneration.
    """
    
    def __init__(
        self,
        cache_dir: str = None,
        max_size: int = 10000,
        persist: bool = True
    ):
        """
        Initialize embedding cache.
        
        Args:
            cache_dir: Directory for cache persistence
            max_size: Maximum cache entries
            persist: Whether to persist cache to disk
        """
        if cache_dir is None:
            cache_dir = str(Path(__file__).parent / ".embedding_cache")
        
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.persist = persist
        self._cache: Dict[str, CacheEntry] = {}
        
        os.makedirs(cache_dir, exist_ok=True)
        
        if persist:
            self._load_cache()
        
        logger.info(f"✅ Embedding cache initialized: {len(self._cache)} entries")
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Get cached embedding.
        
        Args:
            key: Cache key (usually product ID)
            
        Returns:
            CacheEntry or None
        """
        entry = self._cache.get(key)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.now().isoformat()
        return entry
    
    def set(
        self,
        key: str,
        embedding: List[float],
        content_hash: str
    ):
        """
        Cache an embedding.
        
        Args:
            key: Cache key
            embedding: Embedding vector
            content_hash: Hash of the source content
        """
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        self._cache[key] = CacheEntry(
            embedding=embedding,
            hash=content_hash,
            created_at=datetime.now().isoformat(),
            access_count=0,
            last_accessed=datetime.now().isoformat()
        )
    
    def invalidate(self, key: str):
        """Invalidate a cache entry"""
        if key in self._cache:
            del self._cache[key]
    
    def invalidate_by_hash(self, content_hash: str):
        """Invalidate entries by content hash"""
        to_remove = [k for k, v in self._cache.items() if v.hash == content_hash]
        for key in to_remove:
            del self._cache[key]
    
    def clear(self):
        """Clear the entire cache"""
        self._cache.clear()
        if self.persist:
            cache_file = Path(self.cache_dir) / "embeddings.pkl"
            if cache_file.exists():
                cache_file.unlink()
    
    def save(self):
        """Save cache to disk"""
        if not self.persist:
            return
        
        cache_file = Path(self.cache_dir) / "embeddings.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(self._cache, f)
        logger.info(f"Saved {len(self._cache)} cache entries")
    
    def _load_cache(self):
        """Load cache from disk"""
        cache_file = Path(self.cache_dir) / "embeddings.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self._cache = pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self._cache = {}
    
    def _evict_lru(self):
        """Evict least recently used entries"""
        if not self._cache:
            return
        
        # Sort by last accessed and remove oldest 10%
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        
        evict_count = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:evict_count]:
            del self._cache[key]
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_entries': len(self._cache),
            'max_size': self.max_size,
            'utilization': len(self._cache) / self.max_size if self.max_size > 0 else 0
        }


# ============================================================================
# 8. Similarity Ranking
# ============================================================================

class SimilarityRanker:
    """
    Ranks search results by relevance with multiple scoring factors.
    """
    
    def __init__(
        self,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.2,
        metadata_weight: float = 0.1
    ):
        """
        Initialize ranker with weights.
        
        Args:
            semantic_weight: Weight for semantic similarity
            keyword_weight: Weight for keyword matches
            metadata_weight: Weight for metadata matches
        """
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.metadata_weight = metadata_weight
    
    def rank(
        self,
        results: List[SearchResult],
        query: str,
        boost_fields: Dict[str, float] = None
    ) -> List[SearchResult]:
        """
        Rank search results.
        
        Args:
            results: List of search results
            query: Original search query
            boost_fields: Fields to boost in ranking
            
        Returns:
            Ranked list of results
        """
        if not results:
            return []
        
        boost_fields = boost_fields or {}
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for result in results:
            # Calculate keyword score
            text_lower = result.text.lower()
            keyword_matches = sum(1 for word in query_words if word in text_lower)
            keyword_score = keyword_matches / len(query_words) if query_words else 0
            result.keyword_score = keyword_score
            
            # Calculate metadata boost
            metadata_score = 0.0
            for field, boost in boost_fields.items():
                if field in result.metadata:
                    field_value = str(result.metadata[field]).lower()
                    if any(word in field_value for word in query_words):
                        metadata_score += boost
            
            # Calculate final score
            result.score = (
                self.semantic_weight * result.semantic_score +
                self.keyword_weight * keyword_score +
                self.metadata_weight * min(metadata_score, 1.0)
            )
        
        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results
    
    def rerank_by_diversity(
        self,
        results: List[SearchResult],
        diversity_field: str = 'manufacturer',
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Rerank to ensure diversity in results.
        
        Args:
            results: Ranked results
            diversity_field: Field to diversify on
            top_k: Number of results to return
            
        Returns:
            Diverse results
        """
        if not results or len(results) <= top_k:
            return results
        
        seen_values: Set[str] = set()
        diverse_results = []
        remaining = []
        
        for result in results:
            value = str(result.metadata.get(diversity_field, ''))
            if value not in seen_values:
                diverse_results.append(result)
                seen_values.add(value)
            else:
                remaining.append(result)
            
            if len(diverse_results) >= top_k:
                break
        
        # Fill remaining slots with best remaining
        while len(diverse_results) < top_k and remaining:
            diverse_results.append(remaining.pop(0))
        
        return diverse_results


# ============================================================================
# 9. Hybrid Search (Vector + Keyword)
# ============================================================================

class HybridSearch:
    """
    Combines vector similarity with keyword matching for better results.
    """
    
    def __init__(
        self,
        semantic_search: SemanticSearch,
        ranker: SimilarityRanker = None
    ):
        """
        Initialize hybrid search.
        
        Args:
            semantic_search: Semantic search component
            ranker: Similarity ranker
        """
        self.semantic_search = semantic_search
        self.ranker = ranker or SimilarityRanker()
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        filters: Dict[str, Any] = None,
        mode: SearchMode = SearchMode.HYBRID,
        keyword_boost: float = 1.5,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and keyword matching.
        
        Args:
            query: Search query
            n_results: Number of results
            filters: Metadata filters
            mode: Search mode (semantic, keyword, hybrid)
            keyword_boost: Boost for exact keyword matches
            min_score: Minimum score threshold
            
        Returns:
            List of search results
        """
        if mode == SearchMode.KEYWORD:
            return self._keyword_search(query, n_results, filters)
        
        # Get semantic results (fetch more to allow for reranking)
        semantic_results = self.semantic_search.search(
            query,
            n_results=n_results * 2,
            filters=filters,
            min_score=min_score * 0.5  # Lower threshold for initial fetch
        )
        
        if mode == SearchMode.SEMANTIC:
            return semantic_results[:n_results]
        
        # Hybrid mode: enhance with keyword scoring
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for result in semantic_results:
            # Calculate keyword score
            text_lower = result.text.lower()
            
            # Exact phrase match
            if query_lower in text_lower:
                result.keyword_score = 1.0 * keyword_boost
            else:
                # Word overlap
                word_matches = sum(1 for w in query_words if w in text_lower)
                result.keyword_score = (word_matches / len(query_words)) if query_words else 0
            
            # Combined score
            result.score = (
                result.semantic_score * 0.6 +
                result.keyword_score * 0.4
            )
            result.match_type = 'hybrid'
        
        # Sort by combined score
        semantic_results.sort(key=lambda r: r.score, reverse=True)
        
        # Filter by min score
        filtered = [r for r in semantic_results if r.score >= min_score]
        
        return filtered[:n_results]
    
    def _keyword_search(
        self,
        query: str,
        n_results: int,
        filters: Dict[str, Any] = None
    ) -> List[SearchResult]:
        """Keyword-only search using ChromaDB's where clause"""
        if not self.semantic_search.store:
            return []
        
        # Build keyword filter
        query_words = query.lower().split()
        
        # Get all documents (limited approach - would need full-text index for large scale)
        all_docs = self.semantic_search.store.collection.get(
            include=['documents', 'metadatas']
        )
        
        results = []
        if all_docs['ids']:
            for i, id in enumerate(all_docs['ids']):
                doc = all_docs['documents'][i].lower() if all_docs['documents'] else ''
                
                # Calculate keyword match score
                matches = sum(1 for word in query_words if word in doc)
                if matches > 0:
                    score = matches / len(query_words)
                    results.append(SearchResult(
                        id=id,
                        text=all_docs['documents'][i] if all_docs['documents'] else '',
                        score=score,
                        semantic_score=0.0,
                        keyword_score=score,
                        metadata=all_docs['metadatas'][i] if all_docs['metadatas'] else {},
                        match_type='keyword'
                    ))
        
        # Sort and return top results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:n_results]


# ============================================================================
# 10. Embedding Update Mechanism
# ============================================================================

class EmbeddingUpdater:
    """
    Manages embedding updates when products change.
    """
    
    def __init__(
        self,
        processor: BatchEmbeddingProcessor,
        store: ChromaDBEmbeddingStore,
        cache: EmbeddingCache = None
    ):
        """
        Initialize embedding updater.
        
        Args:
            processor: Batch processor
            store: ChromaDB store
            cache: Embedding cache
        """
        self.processor = processor
        self.store = store
        self.cache = cache
        self._pending_updates: Dict[str, Dict[str, Any]] = {}
    
    def queue_update(self, product_id: str, product_data: Dict[str, Any]):
        """
        Queue a product for embedding update.
        
        Args:
            product_id: Product ID
            product_data: Updated product data
        """
        self._pending_updates[product_id] = product_data
    
    def queue_delete(self, product_id: str):
        """
        Queue a product for deletion.
        
        Args:
            product_id: Product ID to delete
        """
        self._pending_updates[product_id] = None  # None indicates deletion
    
    def process_updates(self) -> Dict[str, int]:
        """
        Process all pending updates.
        
        Returns:
            Statistics of processed updates
        """
        if not self._pending_updates:
            return {'updated': 0, 'deleted': 0}
        
        updates = []
        deletes = []
        
        for product_id, data in self._pending_updates.items():
            if data is None:
                deletes.append(product_id)
            else:
                updates.append(data)
        
        # Process deletions
        if deletes:
            self.store.delete_by_ids(deletes)
            if self.cache:
                for id in deletes:
                    self.cache.invalidate(id)
        
        # Process updates
        updated_count = 0
        if updates:
            result = self.processor.process_products(updates, use_cache=False)
            updated_count = result.processed
        
        self._pending_updates.clear()
        
        return {
            'updated': updated_count,
            'deleted': len(deletes)
        }
    
    def update_single(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """
        Immediately update a single product's embedding.
        
        Args:
            product_id: Product ID
            product_data: Product data
            
        Returns:
            Success status
        """
        # Invalidate cache
        if self.cache:
            self.cache.invalidate(product_id)
        
        # Generate new embedding
        text = ProductTextGenerator.generate_product_text(product_data)
        embedding = self.processor.pipeline.generate_embedding(text)
        
        if not embedding:
            return False
        
        # Update store
        self.store.add_embeddings(
            ids=[product_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[self.processor._extract_metadata(product_data)]
        )
        
        # Update cache
        if self.cache:
            text_hash = self.processor._compute_hash(text)
            self.cache.set(product_id, embedding, text_hash)
        
        return True
    
    def check_staleness(
        self,
        product_id: str,
        product_data: Dict[str, Any]
    ) -> bool:
        """
        Check if a product's embedding is stale.
        
        Args:
            product_id: Product ID
            product_data: Current product data
            
        Returns:
            True if embedding needs update
        """
        if not self.cache:
            return True
        
        cached = self.cache.get(product_id)
        if not cached:
            return True
        
        current_text = ProductTextGenerator.generate_product_text(product_data)
        current_hash = self.processor._compute_hash(current_text)
        
        return cached.hash != current_hash
    
    def sync_all(self, products: List[Dict[str, Any]], id_field: str = 'sku') -> Dict[str, int]:
        """
        Full sync of all products.
        
        Args:
            products: List of all products
            id_field: Field to use as ID
            
        Returns:
            Sync statistics
        """
        # Get existing IDs
        existing_count = self.store.count()
        
        # Clear and rebuild
        self.store.clear()
        if self.cache:
            self.cache.clear()
        
        # Process all products
        result = self.processor.process_products(products, id_field=id_field)
        
        return {
            'previous_count': existing_count,
            'new_count': result.processed,
            'failed': result.failed,
            'processing_time_ms': result.processing_time_ms
        }


# ============================================================================
# Main Embedding System Class
# ============================================================================

class VectorEmbeddingSystem:
    """
    Main class integrating all embedding components.
    """
    
    def __init__(
        self,
        model_name: str = None,
        persist_directory: str = None,
        collection_name: str = "product_embeddings",
        enable_cache: bool = True
    ):
        """
        Initialize the vector embedding system.
        
        Args:
            model_name: Sentence transformer model name
            persist_directory: Directory for persistence
            collection_name: ChromaDB collection name
            enable_cache: Whether to enable embedding caching
        """
        self.model_name = model_name or EmbeddingModel.MINILM_L6.value
        
        # Initialize components
        self.pipeline = EmbeddingPipeline(model_name=self.model_name)
        
        self.store = None
        if CHROMADB_AVAILABLE:
            self.store = ChromaDBEmbeddingStore(
                persist_directory=persist_directory,
                collection_name=collection_name
            )
        
        self.cache = EmbeddingCache() if enable_cache else None
        
        self.processor = BatchEmbeddingProcessor(
            pipeline=self.pipeline,
            store=self.store,
            cache=self.cache
        )
        
        self.semantic_search = SemanticSearch(
            pipeline=self.pipeline,
            store=self.store
        )
        
        self.ranker = SimilarityRanker()
        
        self.hybrid_search = HybridSearch(
            semantic_search=self.semantic_search,
            ranker=self.ranker
        )
        
        self.updater = EmbeddingUpdater(
            processor=self.processor,
            store=self.store,
            cache=self.cache
        ) if self.store else None
        
        logger.info("✅ VectorEmbeddingSystem initialized")
    
    def index_products(
        self,
        products: List[Dict[str, Any]],
        id_field: str = 'sku'
    ) -> BatchResult:
        """Index products for semantic search"""
        return self.processor.process_products(products, id_field=id_field)
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        filters: Dict[str, Any] = None,
        mode: SearchMode = SearchMode.HYBRID
    ) -> List[SearchResult]:
        """Search for products"""
        return self.hybrid_search.search(
            query=query,
            n_results=n_results,
            filters=filters,
            mode=mode
        )
    
    def find_similar(self, product_id: str, n_results: int = 5) -> List[SearchResult]:
        """Find similar products"""
        return self.semantic_search.find_similar(product_id, n_results)
    
    def update_product(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """Update a product's embedding"""
        if self.updater:
            return self.updater.update_single(product_id, product_data)
        return False
    
    def delete_product(self, product_id: str):
        """Delete a product's embedding"""
        if self.store:
            self.store.delete_by_ids([product_id])
        if self.cache:
            self.cache.invalidate(product_id)
    
    def stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'model': self.model_name,
            'embedding_dimension': self.pipeline.model.get_sentence_embedding_dimension() if self.pipeline.model else 0,
            'indexed_products': self.store.count() if self.store else 0,
            'cache_stats': self.cache.stats() if self.cache else None
        }
    
    def save_cache(self):
        """Persist cache to disk"""
        if self.cache:
            self.cache.save()


# ============================================================================
# Module-level convenience functions
# ============================================================================

_system: Optional[VectorEmbeddingSystem] = None


def get_embedding_system(
    model_name: str = None,
    persist_directory: str = None
) -> VectorEmbeddingSystem:
    """Get or create the embedding system singleton"""
    global _system
    if _system is None:
        _system = VectorEmbeddingSystem(
            model_name=model_name,
            persist_directory=persist_directory
        )
    return _system


def index_products(products: List[Dict[str, Any]]) -> BatchResult:
    """Index products for semantic search"""
    return get_embedding_system().index_products(products)


def semantic_search(
    query: str,
    n_results: int = 10,
    filters: Dict[str, Any] = None
) -> List[SearchResult]:
    """Perform semantic search"""
    return get_embedding_system().search(query, n_results, filters)


def find_similar_products(product_id: str, n_results: int = 5) -> List[SearchResult]:
    """Find similar products"""
    return get_embedding_system().find_similar(product_id, n_results)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("VECTOR EMBEDDING SYSTEM DEMO")
    print("=" * 60)
    
    # Check dependencies
    print(f"\nDependencies:")
    print(f"  sentence-transformers: {'✅' if SENTENCE_TRANSFORMERS_AVAILABLE else '❌'}")
    print(f"  chromadb: {'✅' if CHROMADB_AVAILABLE else '❌'}")
    print(f"  numpy: {'✅' if NUMPY_AVAILABLE else '❌'}")
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        print("\n⚠️ Install sentence-transformers: pip install sentence-transformers")
        exit(1)
    
    # Initialize system
    print("\nInitializing system...")
    system = VectorEmbeddingSystem()
    
    # Sample products
    sample_products = [
        {
            'sku': 'CABLE-001',
            'name': 'PVC Insulated Power Cable 4C x 4 sqmm',
            'manufacturer': 'ACME Cables',
            'category': 'Power Cables',
            'conductor_material': 'Copper',
            'insulation_type': 'PVC',
            'conductor_size_sqmm': 4.0,
            'number_of_cores': 4,
            'voltage_rating': '1100V'
        },
        {
            'sku': 'CABLE-002',
            'name': 'XLPE Insulated Armoured Cable 3C x 16 sqmm',
            'manufacturer': 'ACME Cables',
            'category': 'Power Cables',
            'conductor_material': 'Copper',
            'insulation_type': 'XLPE',
            'conductor_size_sqmm': 16.0,
            'number_of_cores': 3,
            'voltage_rating': '3.3kV'
        },
        {
            'sku': 'CABLE-003',
            'name': 'Control Cable PVC 7C x 1.5 sqmm',
            'manufacturer': 'Beta Wires',
            'category': 'Control Cables',
            'conductor_material': 'Copper',
            'insulation_type': 'PVC',
            'conductor_size_sqmm': 1.5,
            'number_of_cores': 7,
            'voltage_rating': '650V'
        },
        {
            'sku': 'CABLE-004',
            'name': 'Fire Resistant Cable FRLS 2C x 2.5 sqmm',
            'manufacturer': 'Gamma Electric',
            'category': 'Fire Cables',
            'conductor_material': 'Copper',
            'insulation_type': 'FRLS',
            'conductor_size_sqmm': 2.5,
            'number_of_cores': 2,
            'voltage_rating': '1100V'
        }
    ]
    
    # Index products
    print("\nIndexing products...")
    result = system.index_products(sample_products)
    print(f"  Processed: {result.processed}")
    print(f"  Cached: {result.cached}")
    print(f"  Time: {result.processing_time_ms:.2f}ms")
    
    # Search
    print("\n--- Semantic Search ---")
    query = "copper power cable PVC 4 cores for 1100V"
    print(f"Query: {query}")
    
    results = system.search(query, n_results=3)
    for i, r in enumerate(results, 1):
        print(f"\n  {i}. {r.metadata.get('name', r.id)}")
        print(f"     Score: {r.score:.3f} (Semantic: {r.semantic_score:.3f}, Keyword: {r.keyword_score:.3f})")
    
    # Find similar
    print("\n--- Similar Products ---")
    print(f"Similar to: {sample_products[0]['name']}")
    similar = system.find_similar('CABLE-001', n_results=2)
    for i, r in enumerate(similar, 1):
        print(f"  {i}. {r.metadata.get('name', r.id)} (Score: {r.score:.3f})")
    
    # Stats
    print("\n--- System Stats ---")
    stats = system.stats()
    print(f"  Model: {stats['model']}")
    print(f"  Embedding Dimension: {stats['embedding_dimension']}")
    print(f"  Indexed Products: {stats['indexed_products']}")
    
    print("\n✅ Demo complete!")
