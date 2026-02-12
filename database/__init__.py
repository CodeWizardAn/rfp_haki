"""
Centralized Database Management
All database files organized in structured subfolders

Modules:
- db_config: Database configuration and paths
- data_loaders: CSV/JSON data loading utilities
- models: SQLAlchemy ORM models
- db_engine: Connection pooling and session management
- crud: CRUD operations with repository pattern
- chromadb_setup: Vector database for semantic search
- migrations: Database schema versioning
"""

from .db_config import DatabaseConfig, get_db_path
from .data_loaders import (
    ProductDataLoader,
    PricingDataLoader,
    TestDataLoader,
    RFPDataLoader,
    DataLoaderManager,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    get_data_loader_manager
)

# SQLAlchemy Models
from .models import (
    Base,
    Product, OEM, Standard, Certification,
    RFP, RFPRequirement, ProductMatch,
    AgentLog, Bid, BidItem, AuditTrail, TestService,
    ProductStatus, RFPStatus, MatchStatus, AgentType, LogLevel, BidStatus
)

# Database Engine and Connection Pooling
from .db_engine import (
    DatabaseManager,
    DatabaseConfig as EngineConfig,
    get_db_manager
)

# CRUD Operations
from .crud import (
    BaseRepository,
    ProductRepository,
    OEMRepository,
    RFPRepository,
    RequirementRepository,
    MatchRepository,
    AgentLogRepository,
    BidRepository,
    AuditRepository
)

# Migrations
from .migrations import (
    MigrationManager,
    Migration,
    init_migrations,
    get_migration_status
)

# ChromaDB (optional - may not be installed)
try:
    from .chromadb_setup import (
        ChromaDBManager,
        get_chromadb_manager
    )
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    ChromaDBManager = None
    get_chromadb_manager = None

# Vector Embeddings with Sentence Transformers
try:
    from .vector_embeddings import (
        VectorEmbeddingSystem,
        EmbeddingModel,
        SearchMode,
        EmbeddingResult,
        SearchResult,
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
        get_embedding_system,
        index_products,
        semantic_search,
        find_similar_products
    )
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    VectorEmbeddingSystem = None
    get_embedding_system = None

__all__ = [
    # Config
    'DatabaseConfig', 
    'get_db_path',
    
    # Data Loaders
    'ProductDataLoader',
    'PricingDataLoader',
    'TestDataLoader',
    'RFPDataLoader',
    'DataLoaderManager',
    'ValidationResult',
    'ValidationIssue',
    'ValidationSeverity',
    'get_data_loader_manager',
    
    # Models
    'Base',
    'Product', 'OEM', 'Standard', 'Certification',
    'RFP', 'RFPRequirement', 'ProductMatch',
    'AgentLog', 'Bid', 'BidItem', 'AuditTrail', 'TestService',
    'ProductStatus', 'RFPStatus', 'MatchStatus', 'AgentType', 'LogLevel', 'BidStatus',
    
    # Engine
    'DatabaseManager',
    'EngineConfig',
    'get_db_manager',
    
    # CRUD
    'BaseRepository',
    'ProductRepository',
    'OEMRepository',
    'RFPRepository',
    'RequirementRepository',
    'MatchRepository',
    'AgentLogRepository',
    'BidRepository',
    'AuditRepository',
    
    # Migrations
    'MigrationManager',
    'Migration',
    'init_migrations',
    'get_migration_status',
    
    # ChromaDB
    'CHROMADB_AVAILABLE',
    'ChromaDBManager',
    'get_chromadb_manager',
    
    # Vector Embeddings
    'EMBEDDINGS_AVAILABLE',
    'VectorEmbeddingSystem',
    'EmbeddingModel',
    'SearchMode',
    'EmbeddingResult',
    'SearchResult',
    'BatchResult',
    'EmbeddingModelManager',
    'ProductTextGenerator',
    'EmbeddingPipeline',
    'ChromaDBEmbeddingStore',
    'BatchEmbeddingProcessor',
    'SemanticSearch',
    'EmbeddingCache',
    'SimilarityRanker',
    'HybridSearch',
    'EmbeddingUpdater',
    'get_embedding_system',
    'index_products',
    'semantic_search',
    'find_similar_products'
]
