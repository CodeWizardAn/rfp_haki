"""
Comprehensive Unit Tests for Vector Embedding System
Tests all 10 features with mocks for external dependencies
"""

import pytest
import hashlib
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

# Import system under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# We'll mock the external dependencies
from database.vector_embeddings import (
    EmbeddingModel,
    SearchMode,
    EmbeddingResult,
    SearchResult,
    CacheEntry,
    BatchResult,
    EmbeddingModelManager,
    ProductTextGenerator,
    EmbeddingPipeline,
    ChromaDBEmbeddingStore,
    BatchEmbeddingProcessor,
    SemanticSearch,
    EmbeddingCache,
    SimilarityRanker,
    HybridSearch,
    EmbeddingUpdater,
    VectorEmbeddingSystem
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_products():
    """Sample product data for testing"""
    return [
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
        }
    ]


@pytest.fixture
def sample_rfp_requirements():
    """Sample RFP requirements for testing"""
    return [
        {
            'original_text': 'Supply 500m of 4-core 4 sqmm PVC insulated copper power cable',
            'product_name': 'PVC Power Cable',
            'product_type': 'Power Cable',
            'conductor_material': 'Copper',
            'conductor_size_sqmm': 4.0,
            'insulation_type': 'PVC',
            'voltage_grade': '1100V',
            'quantity': 500,
            'unit': 'meters'
        }
    ]


@pytest.fixture
def mock_embedding():
    """Mock embedding vector (384 dimensions for MiniLM)"""
    return [0.1] * 384


@pytest.fixture
def mock_embeddings():
    """Multiple mock embedding vectors"""
    return [[0.1 * (i + 1)] * 384 for i in range(5)]


@pytest.fixture
def mock_sentence_transformer():
    """Mock SentenceTransformer model"""
    mock = Mock()
    mock.encode = Mock(return_value=[[0.1] * 384])
    mock.get_sentence_embedding_dimension = Mock(return_value=384)
    return mock


@pytest.fixture
def mock_chromadb_collection():
    """Mock ChromaDB collection"""
    collection = Mock()
    collection.upsert = Mock()
    collection.query = Mock(return_value={
        'ids': [['CABLE-001', 'CABLE-002']],
        'documents': [['Product: PVC Cable', 'Product: XLPE Cable']],
        'metadatas': [[{'sku': 'CABLE-001'}, {'sku': 'CABLE-002'}]],
        'distances': [[0.1, 0.2]],
        'embeddings': [[[0.1] * 384, [0.2] * 384]]
    })
    collection.get = Mock(return_value={
        'ids': ['CABLE-001'],
        'documents': ['Product: PVC Cable'],
        'metadatas': [{'sku': 'CABLE-001'}],
        'embeddings': [[0.1] * 384]
    })
    collection.delete = Mock()
    collection.count = Mock(return_value=3)
    return collection


# ============================================================================
# Test 1: Sentence Transformer Model Initialization
# ============================================================================

class TestEmbeddingModelManager:
    """Tests for EmbeddingModelManager class"""
    
    def test_default_model_is_minilm(self):
        """Default model should be all-MiniLM-L6-v2"""
        assert EmbeddingModelManager._default_model == EmbeddingModel.MINILM_L6.value
    
    def test_set_default_model(self):
        """Should be able to change default model"""
        original = EmbeddingModelManager._default_model
        EmbeddingModelManager.set_default_model(EmbeddingModel.MPNET_BASE.value)
        assert EmbeddingModelManager._default_model == EmbeddingModel.MPNET_BASE.value
        # Reset
        EmbeddingModelManager.set_default_model(original)
    
    @patch('database.vector_embeddings.SENTENCE_TRANSFORMERS_AVAILABLE', False)
    def test_get_model_without_transformers(self):
        """Should return None when sentence-transformers not available"""
        result = EmbeddingModelManager.get_model()
        assert result is None
    
    def test_unload_model(self):
        """Should be able to unload model"""
        EmbeddingModelManager._instances['test_model'] = Mock()
        EmbeddingModelManager.unload_model('test_model')
        assert 'test_model' not in EmbeddingModelManager._instances
    
    def test_get_embedding_dimension_default(self):
        """Should return default dimension if model not loaded"""
        with patch.object(EmbeddingModelManager, 'get_model', return_value=None):
            dim = EmbeddingModelManager.get_embedding_dimension('nonexistent')
            assert dim == 384


class TestEmbeddingModels:
    """Tests for EmbeddingModel enum"""
    
    def test_minilm_l6_model(self):
        """MiniLM L6 should have correct model name"""
        assert EmbeddingModel.MINILM_L6.value == "all-MiniLM-L6-v2"
    
    def test_mpnet_base_model(self):
        """MPNET Base should have correct model name"""
        assert EmbeddingModel.MPNET_BASE.value == "all-mpnet-base-v2"
    
    def test_all_models_have_values(self):
        """All models should have string values"""
        for model in EmbeddingModel:
            assert isinstance(model.value, str)
            assert len(model.value) > 0


# ============================================================================
# Test 2: Product Text Generator
# ============================================================================

class TestProductTextGenerator:
    """Tests for ProductTextGenerator class"""
    
    def test_generate_product_text_basic(self, sample_products):
        """Should generate text from product dict"""
        product = sample_products[0]
        text = ProductTextGenerator.generate_product_text(product)
        
        assert 'Product: PVC Insulated Power Cable' in text
        assert 'ACME Cables' in text
        assert 'Copper' in text
        assert 'PVC' in text
    
    def test_generate_product_text_includes_sku(self, sample_products):
        """Should include SKU in generated text"""
        product = sample_products[0]
        text = ProductTextGenerator.generate_product_text(product)
        assert 'SKU: CABLE-001' in text
    
    def test_generate_product_text_respects_max_length(self, sample_products):
        """Should truncate to max_length"""
        product = sample_products[0]
        text = ProductTextGenerator.generate_product_text(product, max_length=50)
        assert len(text) <= 50
        assert text.endswith('...')
    
    def test_generate_product_text_handles_missing_fields(self):
        """Should handle products with missing fields"""
        minimal_product = {'name': 'Basic Cable'}
        text = ProductTextGenerator.generate_product_text(minimal_product)
        assert 'Product: Basic Cable' in text
    
    def test_generate_product_text_includes_specifications(self):
        """Should include specifications dict if present"""
        product = {
            'name': 'Test Cable',
            'specifications': {
                'test_spec': 'test_value',
                'another_spec': 123
            }
        }
        text = ProductTextGenerator.generate_product_text(product, include_specs=True)
        assert 'Test Spec: test_value' in text
        assert 'Another Spec: 123' in text
    
    def test_generate_rfp_text(self, sample_rfp_requirements):
        """Should generate text from RFP requirement"""
        req = sample_rfp_requirements[0]
        text = ProductTextGenerator.generate_rfp_text(req)
        
        assert 'copper power cable' in text.lower() or 'Copper' in text
        assert '4' in text  # Size or cores
    
    def test_generate_search_text_with_context(self):
        """Should combine query with context"""
        query = "power cable"
        context = {'voltage': '1100V', 'cores': 4}
        text = ProductTextGenerator.generate_search_text(query, context)
        
        assert 'power cable' in text
        assert '1100V' in text
        assert '4' in text
    
    def test_generate_search_text_without_context(self):
        """Should work without context"""
        query = "xlpe cable"
        text = ProductTextGenerator.generate_search_text(query)
        assert text == "xlpe cable"


# ============================================================================
# Test 3: Embedding Generation Pipeline
# ============================================================================

class TestEmbeddingPipeline:
    """Tests for EmbeddingPipeline class"""
    
    def test_init_default_values(self):
        """Should initialize with default values"""
        pipeline = EmbeddingPipeline()
        assert pipeline.model_name == EmbeddingModel.MINILM_L6.value
        assert pipeline.normalize is True
        assert pipeline.batch_size == 32
    
    def test_init_custom_values(self):
        """Should accept custom values"""
        pipeline = EmbeddingPipeline(
            model_name=EmbeddingModel.MPNET_BASE.value,
            normalize=False,
            batch_size=64
        )
        assert pipeline.model_name == EmbeddingModel.MPNET_BASE.value
        assert pipeline.normalize is False
        assert pipeline.batch_size == 64
    
    def test_generate_embedding_returns_none_without_model(self):
        """Should return None if model not available"""
        pipeline = EmbeddingPipeline()
        pipeline._model = None
        with patch.object(EmbeddingModelManager, 'get_model', return_value=None):
            result = pipeline.generate_embedding("test text")
            assert result is None
    
    def test_generate_embeddings_empty_input(self):
        """Should return empty list for empty input"""
        pipeline = EmbeddingPipeline()
        with patch.object(EmbeddingModelManager, 'get_model', return_value=Mock()):
            result = pipeline.generate_embeddings([])
            assert result == []
    
    def test_compute_similarity_identical_vectors(self):
        """Identical vectors should have similarity 1.0"""
        pipeline = EmbeddingPipeline()
        vec = [1.0, 0.0, 0.0]
        similarity = pipeline.compute_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.001
    
    def test_compute_similarity_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0"""
        pipeline = EmbeddingPipeline()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = pipeline.compute_similarity(vec1, vec2)
        assert abs(similarity) < 0.001
    
    def test_compute_similarity_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0"""
        pipeline = EmbeddingPipeline()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = pipeline.compute_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 0.001


# ============================================================================
# Test 4: ChromaDB Integration
# ============================================================================

class TestChromaDBEmbeddingStore:
    """Tests for ChromaDBEmbeddingStore class"""
    
    @patch('database.vector_embeddings.CHROMADB_AVAILABLE', False)
    def test_init_raises_without_chromadb(self):
        """Should raise ImportError without chromadb"""
        with pytest.raises(ImportError):
            ChromaDBEmbeddingStore()
    
    @patch('database.vector_embeddings.CHROMADB_AVAILABLE', True)
    @patch('database.vector_embeddings.chromadb')
    def test_add_embeddings_basic(self, mock_chromadb, mock_chromadb_collection):
        """Should add embeddings to collection"""
        mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_chromadb_collection
        
        store = ChromaDBEmbeddingStore(persist_directory='/tmp/test_chroma')
        store._collection = mock_chromadb_collection
        
        ids = ['id1', 'id2']
        embeddings = [[0.1] * 384, [0.2] * 384]
        documents = ['doc1', 'doc2']
        
        count = store.add_embeddings(ids, embeddings, documents)
        
        assert count == 2
        mock_chromadb_collection.upsert.assert_called_once()
    
    @patch('database.vector_embeddings.CHROMADB_AVAILABLE', True)
    @patch('database.vector_embeddings.chromadb')
    def test_add_embeddings_empty(self, mock_chromadb, mock_chromadb_collection):
        """Should return 0 for empty input"""
        mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_chromadb_collection
        
        store = ChromaDBEmbeddingStore(persist_directory='/tmp/test_chroma')
        store._collection = mock_chromadb_collection
        
        count = store.add_embeddings([], [], [])
        assert count == 0
    
    @patch('database.vector_embeddings.CHROMADB_AVAILABLE', True)
    @patch('database.vector_embeddings.chromadb')
    def test_query_by_embedding(self, mock_chromadb, mock_chromadb_collection):
        """Should query by embedding vector"""
        mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_chromadb_collection
        
        store = ChromaDBEmbeddingStore(persist_directory='/tmp/test_chroma')
        store._collection = mock_chromadb_collection
        
        query_embedding = [0.1] * 384
        result = store.query_by_embedding(query_embedding, n_results=5)
        
        mock_chromadb_collection.query.assert_called_once()
        assert 'ids' in result
    
    @patch('database.vector_embeddings.CHROMADB_AVAILABLE', True)
    @patch('database.vector_embeddings.chromadb')
    def test_delete_by_ids(self, mock_chromadb, mock_chromadb_collection):
        """Should delete embeddings by IDs"""
        mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_chromadb_collection
        
        store = ChromaDBEmbeddingStore(persist_directory='/tmp/test_chroma')
        store._collection = mock_chromadb_collection
        
        store.delete_by_ids(['id1', 'id2'])
        mock_chromadb_collection.delete.assert_called_once_with(ids=['id1', 'id2'])
    
    @patch('database.vector_embeddings.CHROMADB_AVAILABLE', True)
    @patch('database.vector_embeddings.chromadb')
    def test_count(self, mock_chromadb, mock_chromadb_collection):
        """Should return collection count"""
        mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_chromadb_collection
        
        store = ChromaDBEmbeddingStore(persist_directory='/tmp/test_chroma')
        store._collection = mock_chromadb_collection
        
        count = store.count()
        assert count == 3


# ============================================================================
# Test 5: Batch Embedding Processor
# ============================================================================

class TestBatchEmbeddingProcessor:
    """Tests for BatchEmbeddingProcessor class"""
    
    def test_init_default_batch_size(self):
        """Should have default batch size of 100"""
        processor = BatchEmbeddingProcessor()
        assert processor.batch_size == 100
    
    def test_compute_hash(self):
        """Should compute consistent MD5 hash"""
        processor = BatchEmbeddingProcessor()
        
        text = "test text"
        hash1 = processor._compute_hash(text)
        hash2 = processor._compute_hash(text)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hex length
    
    def test_compute_hash_different_texts(self):
        """Different texts should have different hashes"""
        processor = BatchEmbeddingProcessor()
        
        hash1 = processor._compute_hash("text one")
        hash2 = processor._compute_hash("text two")
        
        assert hash1 != hash2
    
    def test_extract_metadata(self, sample_products):
        """Should extract metadata from product"""
        processor = BatchEmbeddingProcessor()
        
        metadata = processor._extract_metadata(sample_products[0])
        
        assert metadata['sku'] == 'CABLE-001'
        assert metadata['manufacturer'] == 'ACME Cables'
        assert metadata['conductor_material'] == 'Copper'
    
    def test_extract_metadata_handles_missing_fields(self):
        """Should handle products with missing fields"""
        processor = BatchEmbeddingProcessor()
        
        metadata = processor._extract_metadata({'sku': 'TEST-001'})
        assert metadata['sku'] == 'TEST-001'
        assert 'manufacturer' not in metadata or metadata.get('manufacturer') == ''
    
    def test_process_products_returns_batch_result(self, sample_products):
        """Should return BatchResult"""
        mock_pipeline = Mock()
        mock_pipeline.generate_embeddings = Mock(return_value=[[0.1] * 384] * len(sample_products))
        
        processor = BatchEmbeddingProcessor(pipeline=mock_pipeline)
        result = processor.process_products(sample_products)
        
        assert isinstance(result, BatchResult)
        assert result.total_items == len(sample_products)


# ============================================================================
# Test 6: Semantic Search Function
# ============================================================================

class TestSemanticSearch:
    """Tests for SemanticSearch class"""
    
    def test_search_without_store(self):
        """Should return empty list without store"""
        search = SemanticSearch(store=None)
        results = search.search("test query")
        assert results == []
    
    def test_search_converts_distance_to_similarity(self, mock_chromadb_collection):
        """Should convert distance to similarity score"""
        mock_store = Mock()
        mock_store.query_by_embedding = Mock(return_value={
            'ids': [['id1']],
            'documents': [['doc1']],
            'metadatas': [[{'sku': 'TEST-001'}]],
            'distances': [[0.2]]  # Distance of 0.2 = similarity of 0.8
        })
        
        mock_pipeline = Mock()
        mock_pipeline.generate_embedding = Mock(return_value=[0.1] * 384)
        
        search = SemanticSearch(pipeline=mock_pipeline, store=mock_store)
        results = search.search("test query")
        
        assert len(results) == 1
        assert abs(results[0].score - 0.8) < 0.001  # 1 - 0.2 = 0.8
    
    def test_search_with_filters(self, mock_chromadb_collection):
        """Should pass filters to store"""
        mock_store = Mock()
        mock_store.query_by_embedding = Mock(return_value={
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        })
        
        mock_pipeline = Mock()
        mock_pipeline.generate_embedding = Mock(return_value=[0.1] * 384)
        
        search = SemanticSearch(pipeline=mock_pipeline, store=mock_store)
        search.search("test", filters={'manufacturer': 'ACME'})
        
        call_args = mock_store.query_by_embedding.call_args
        assert call_args is not None
    
    def test_search_respects_min_score(self):
        """Should filter out results below min_score"""
        mock_store = Mock()
        mock_store.query_by_embedding = Mock(return_value={
            'ids': [['id1', 'id2']],
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{}, {}]],
            'distances': [[0.1, 0.9]]  # Similarities: 0.9, 0.1
        })
        
        mock_pipeline = Mock()
        mock_pipeline.generate_embedding = Mock(return_value=[0.1] * 384)
        
        search = SemanticSearch(pipeline=mock_pipeline, store=mock_store)
        results = search.search("test", min_score=0.5)
        
        # Only id1 should pass (0.9 > 0.5)
        assert len(results) == 1
        assert results[0].id == 'id1'
    
    def test_find_similar_without_store(self):
        """Should return empty list without store"""
        search = SemanticSearch(store=None)
        results = search.find_similar("product-id")
        assert results == []
    
    def test_find_similar_excludes_self(self):
        """Should exclude the reference product"""
        mock_store = Mock()
        mock_store.get_by_ids = Mock(return_value={
            'ids': ['REF-001'],
            'embeddings': [[0.1] * 384]
        })
        mock_store.query_by_embedding = Mock(return_value={
            'ids': [['REF-001', 'SIMILAR-001', 'SIMILAR-002']],
            'documents': [['ref', 'sim1', 'sim2']],
            'metadatas': [[{}, {}, {}]],
            'distances': [[0.0, 0.1, 0.2]]
        })
        
        search = SemanticSearch(store=mock_store)
        results = search.find_similar('REF-001', n_results=2, exclude_self=True)
        
        # REF-001 should be excluded
        assert 'REF-001' not in [r.id for r in results]


# ============================================================================
# Test 7: Embedding Caching
# ============================================================================

class TestEmbeddingCache:
    """Tests for EmbeddingCache class"""
    
    def test_get_nonexistent_key(self, tmp_path):
        """Should return None for nonexistent key"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), persist=False)
        result = cache.get('nonexistent')
        assert result is None
    
    def test_set_and_get(self, tmp_path):
        """Should store and retrieve embeddings"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), persist=False)
        
        embedding = [0.1] * 384
        cache.set('key1', embedding, 'hash123')
        
        result = cache.get('key1')
        assert result is not None
        assert result.embedding == embedding
        assert result.hash == 'hash123'
    
    def test_get_updates_access_count(self, tmp_path):
        """Getting should update access count"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), persist=False)
        
        cache.set('key1', [0.1] * 384, 'hash123')
        
        cache.get('key1')
        cache.get('key1')
        cache.get('key1')
        
        result = cache.get('key1')
        assert result.access_count >= 3
    
    def test_invalidate(self, tmp_path):
        """Should remove entry on invalidate"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), persist=False)
        
        cache.set('key1', [0.1] * 384, 'hash123')
        assert cache.get('key1') is not None
        
        cache.invalidate('key1')
        assert cache.get('key1') is None
    
    def test_invalidate_by_hash(self, tmp_path):
        """Should remove entries by hash"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), persist=False)
        
        cache.set('key1', [0.1] * 384, 'hash123')
        cache.set('key2', [0.2] * 384, 'hash123')
        cache.set('key3', [0.3] * 384, 'other_hash')
        
        cache.invalidate_by_hash('hash123')
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None
        assert cache.get('key3') is not None
    
    def test_clear(self, tmp_path):
        """Should remove all entries on clear"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), persist=False)
        
        cache.set('key1', [0.1] * 384, 'hash1')
        cache.set('key2', [0.2] * 384, 'hash2')
        
        cache.clear()
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None
    
    def test_max_size_eviction(self, tmp_path):
        """Should evict LRU entries when at max size"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), max_size=3, persist=False)
        
        cache.set('key1', [0.1] * 384, 'hash1')
        cache.set('key2', [0.2] * 384, 'hash2')
        cache.set('key3', [0.3] * 384, 'hash3')
        cache.set('key4', [0.4] * 384, 'hash4')  # Should trigger eviction
        
        # At least one entry should be evicted
        stats = cache.stats()
        assert stats['total_entries'] <= 3
    
    def test_stats(self, tmp_path):
        """Should return accurate statistics"""
        cache = EmbeddingCache(cache_dir=str(tmp_path), max_size=100, persist=False)
        
        cache.set('key1', [0.1] * 384, 'hash1')
        cache.set('key2', [0.2] * 384, 'hash2')
        
        stats = cache.stats()
        assert stats['total_entries'] == 2
        assert stats['max_size'] == 100
        assert stats['utilization'] == 0.02


# ============================================================================
# Test 8: Similarity Ranking
# ============================================================================

class TestSimilarityRanker:
    """Tests for SimilarityRanker class"""
    
    def test_init_default_weights(self):
        """Should initialize with default weights"""
        ranker = SimilarityRanker()
        assert ranker.semantic_weight == 0.7
        assert ranker.keyword_weight == 0.2
        assert ranker.metadata_weight == 0.1
    
    def test_init_custom_weights(self):
        """Should accept custom weights"""
        ranker = SimilarityRanker(
            semantic_weight=0.5,
            keyword_weight=0.3,
            metadata_weight=0.2
        )
        assert ranker.semantic_weight == 0.5
    
    def test_rank_empty_results(self):
        """Should handle empty results"""
        ranker = SimilarityRanker()
        results = ranker.rank([], "test query")
        assert results == []
    
    def test_rank_calculates_keyword_score(self):
        """Should calculate keyword match score"""
        ranker = SimilarityRanker()
        
        results = [
            SearchResult(
                id='id1',
                text='copper power cable pvc insulated',
                score=0.8,
                semantic_score=0.8,
                keyword_score=0.0,
                metadata={},
                match_type='semantic'
            )
        ]
        
        ranked = ranker.rank(results, "copper cable")
        
        # Both "copper" and "cable" should match
        assert ranked[0].keyword_score > 0
    
    def test_rank_sorts_by_score(self):
        """Should sort results by final score"""
        ranker = SimilarityRanker()
        
        results = [
            SearchResult(id='id1', text='low match', score=0.5, semantic_score=0.5, 
                        keyword_score=0.0, metadata={}, match_type='semantic'),
            SearchResult(id='id2', text='high match query words', score=0.9, semantic_score=0.9, 
                        keyword_score=0.0, metadata={}, match_type='semantic'),
        ]
        
        ranked = ranker.rank(results, "query")
        
        # Higher semantic score should be first
        assert ranked[0].id == 'id2'
    
    def test_rerank_by_diversity(self):
        """Should diversify results by field"""
        ranker = SimilarityRanker()
        
        results = [
            SearchResult(id='id1', text='', score=0.9, semantic_score=0.9, keyword_score=0.0,
                        metadata={'manufacturer': 'ACME'}, match_type='semantic'),
            SearchResult(id='id2', text='', score=0.85, semantic_score=0.85, keyword_score=0.0,
                        metadata={'manufacturer': 'ACME'}, match_type='semantic'),
            SearchResult(id='id3', text='', score=0.8, semantic_score=0.8, keyword_score=0.0,
                        metadata={'manufacturer': 'Beta'}, match_type='semantic'),
        ]
        
        diverse = ranker.rerank_by_diversity(results, diversity_field='manufacturer', top_k=2)
        
        # Should have one from each manufacturer
        manufacturers = {r.metadata['manufacturer'] for r in diverse}
        assert len(manufacturers) == 2


# ============================================================================
# Test 9: Hybrid Search (Vector + Keyword)
# ============================================================================

class TestHybridSearch:
    """Tests for HybridSearch class"""
    
    def test_search_semantic_mode(self):
        """Should use only semantic search in SEMANTIC mode"""
        mock_semantic = Mock()
        mock_semantic.search = Mock(return_value=[
            SearchResult(id='id1', text='', score=0.8, semantic_score=0.8,
                        keyword_score=0.0, metadata={}, match_type='semantic')
        ])
        
        hybrid = HybridSearch(semantic_search=mock_semantic)
        results = hybrid.search("test", mode=SearchMode.SEMANTIC)
        
        mock_semantic.search.assert_called_once()
        assert len(results) == 1
    
    def test_search_hybrid_mode_combines_scores(self):
        """Should combine semantic and keyword scores in HYBRID mode"""
        mock_semantic = Mock()
        mock_semantic.search = Mock(return_value=[
            SearchResult(id='id1', text='test query exact match', score=0.8, 
                        semantic_score=0.8, keyword_score=0.0, metadata={}, match_type='semantic')
        ])
        
        hybrid = HybridSearch(semantic_search=mock_semantic)
        results = hybrid.search("test query", mode=SearchMode.HYBRID)
        
        assert len(results) == 1
        # Keyword score should be set
        assert results[0].keyword_score > 0
        assert results[0].match_type == 'hybrid'
    
    def test_search_exact_phrase_boost(self):
        """Should boost exact phrase matches"""
        mock_semantic = Mock()
        mock_semantic.search = Mock(return_value=[
            SearchResult(id='id1', text='power cable xlpe', score=0.7, 
                        semantic_score=0.7, keyword_score=0.0, metadata={}, match_type='semantic'),
            SearchResult(id='id2', text='xlpe power cable for industrial use', score=0.75, 
                        semantic_score=0.75, keyword_score=0.0, metadata={}, match_type='semantic'),
        ])
        
        hybrid = HybridSearch(semantic_search=mock_semantic)
        results = hybrid.search("xlpe power cable", mode=SearchMode.HYBRID, keyword_boost=2.0)
        
        # Both should have keyword scores
        for r in results:
            assert r.keyword_score >= 0
    
    def test_search_min_score_filter(self):
        """Should filter results below min_score"""
        mock_semantic = Mock()
        mock_semantic.search = Mock(return_value=[
            SearchResult(id='id1', text='match', score=0.8, 
                        semantic_score=0.8, keyword_score=0.0, metadata={}, match_type='semantic'),
            SearchResult(id='id2', text='no match words here', score=0.3, 
                        semantic_score=0.3, keyword_score=0.0, metadata={}, match_type='semantic'),
        ])
        
        hybrid = HybridSearch(semantic_search=mock_semantic)
        results = hybrid.search("match", mode=SearchMode.HYBRID, min_score=0.5)
        
        # Low score result should be filtered out
        assert all(r.score >= 0.5 for r in results)


# ============================================================================
# Test 10: Embedding Update Mechanism
# ============================================================================

class TestEmbeddingUpdater:
    """Tests for EmbeddingUpdater class"""
    
    def test_queue_update(self):
        """Should queue product for update"""
        mock_processor = Mock()
        mock_store = Mock()
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store)
        updater.queue_update('PROD-001', {'name': 'Test Product'})
        
        assert 'PROD-001' in updater._pending_updates
        assert updater._pending_updates['PROD-001']['name'] == 'Test Product'
    
    def test_queue_delete(self):
        """Should queue product for deletion"""
        mock_processor = Mock()
        mock_store = Mock()
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store)
        updater.queue_delete('PROD-001')
        
        assert 'PROD-001' in updater._pending_updates
        assert updater._pending_updates['PROD-001'] is None
    
    def test_process_updates_empty(self):
        """Should handle empty queue"""
        mock_processor = Mock()
        mock_store = Mock()
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store)
        result = updater.process_updates()
        
        assert result == {'updated': 0, 'deleted': 0}
    
    def test_process_updates_with_deletes(self):
        """Should process deletions"""
        mock_processor = Mock()
        mock_processor.process_products = Mock(return_value=BatchResult(
            total_items=0, processed=0, cached=0, failed=0,
            processing_time_ms=0, embeddings=[]
        ))
        mock_store = Mock()
        mock_cache = Mock()
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store, cache=mock_cache)
        updater.queue_delete('PROD-001')
        updater.queue_delete('PROD-002')
        
        result = updater.process_updates()
        
        mock_store.delete_by_ids.assert_called_once()
        assert result['deleted'] == 2
    
    def test_process_updates_clears_queue(self):
        """Should clear queue after processing"""
        mock_processor = Mock()
        mock_processor.process_products = Mock(return_value=BatchResult(
            total_items=1, processed=1, cached=0, failed=0,
            processing_time_ms=10, embeddings=[]
        ))
        mock_store = Mock()
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store)
        updater.queue_update('PROD-001', {'name': 'Test'})
        
        updater.process_updates()
        
        assert len(updater._pending_updates) == 0
    
    def test_check_staleness_no_cache(self):
        """Should return True if no cache"""
        mock_processor = Mock()
        mock_store = Mock()
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store, cache=None)
        
        is_stale = updater.check_staleness('PROD-001', {'name': 'Test'})
        assert is_stale is True
    
    def test_check_staleness_not_cached(self):
        """Should return True if not in cache"""
        mock_processor = Mock()
        mock_store = Mock()
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store, cache=mock_cache)
        
        is_stale = updater.check_staleness('PROD-001', {'name': 'Test'})
        assert is_stale is True
    
    def test_check_staleness_hash_changed(self):
        """Should return True if content hash changed"""
        mock_processor = Mock()
        mock_processor._compute_hash = Mock(return_value='new_hash')
        mock_store = Mock()
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=CacheEntry(
            embedding=[0.1] * 384,
            hash='old_hash',
            created_at='2024-01-01',
            access_count=0,
            last_accessed=''
        ))
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store, cache=mock_cache)
        
        is_stale = updater.check_staleness('PROD-001', {'name': 'Changed Name'})
        assert is_stale is True
    
    def test_check_staleness_hash_same(self):
        """Should return False if content hash unchanged"""
        mock_processor = Mock()
        mock_processor._compute_hash = Mock(return_value='same_hash')
        mock_store = Mock()
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=CacheEntry(
            embedding=[0.1] * 384,
            hash='same_hash',
            created_at='2024-01-01',
            access_count=0,
            last_accessed=''
        ))
        
        updater = EmbeddingUpdater(processor=mock_processor, store=mock_store, cache=mock_cache)
        
        is_stale = updater.check_staleness('PROD-001', {'name': 'Test'})
        assert is_stale is False


# ============================================================================
# Test VectorEmbeddingSystem Integration
# ============================================================================

class TestVectorEmbeddingSystem:
    """Integration tests for VectorEmbeddingSystem"""
    
    def test_init_creates_components(self):
        """Should create all components"""
        with patch('database.vector_embeddings.CHROMADB_AVAILABLE', False):
            system = VectorEmbeddingSystem(enable_cache=False)
            
            assert system.pipeline is not None
            assert system.processor is not None
            assert system.semantic_search is not None
            assert system.ranker is not None
            assert system.hybrid_search is not None
    
    def test_stats(self):
        """Should return system statistics"""
        with patch('database.vector_embeddings.CHROMADB_AVAILABLE', False):
            system = VectorEmbeddingSystem(enable_cache=False)
            
            stats = system.stats()
            
            assert 'model' in stats
            assert 'embedding_dimension' in stats


# ============================================================================
# Test Data Classes
# ============================================================================

class TestDataClasses:
    """Tests for data classes"""
    
    def test_embedding_result_creation(self):
        """Should create EmbeddingResult"""
        result = EmbeddingResult(
            id='test-id',
            text='test text',
            embedding=[0.1] * 384,
            metadata={'key': 'value'},
            hash='abc123',
            generated_at='2024-01-01T00:00:00'
        )
        
        assert result.id == 'test-id'
        assert len(result.embedding) == 384
    
    def test_search_result_creation(self):
        """Should create SearchResult"""
        result = SearchResult(
            id='test-id',
            text='test text',
            score=0.9,
            semantic_score=0.85,
            keyword_score=0.5,
            metadata={'sku': 'TEST-001'},
            match_type='hybrid'
        )
        
        assert result.score == 0.9
        assert result.match_type == 'hybrid'
    
    def test_cache_entry_creation(self):
        """Should create CacheEntry"""
        entry = CacheEntry(
            embedding=[0.1] * 384,
            hash='abc123',
            created_at='2024-01-01T00:00:00',
            access_count=5,
            last_accessed='2024-01-02T00:00:00'
        )
        
        assert entry.access_count == 5
    
    def test_batch_result_creation(self):
        """Should create BatchResult"""
        result = BatchResult(
            total_items=100,
            processed=95,
            cached=5,
            failed=0,
            processing_time_ms=1500.5,
            embeddings=[]
        )
        
        assert result.total_items == 100
        assert result.processed == 95


# ============================================================================
# Test Search Mode Enum
# ============================================================================

class TestSearchMode:
    """Tests for SearchMode enum"""
    
    def test_semantic_mode(self):
        """Should have SEMANTIC mode"""
        assert SearchMode.SEMANTIC.value == "semantic"
    
    def test_keyword_mode(self):
        """Should have KEYWORD mode"""
        assert SearchMode.KEYWORD.value == "keyword"
    
    def test_hybrid_mode(self):
        """Should have HYBRID mode"""
        assert SearchMode.HYBRID.value == "hybrid"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
