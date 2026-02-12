"""
ChromaDB Vector Database Setup
For semantic search and embeddings storage

Collections:
- products: Product descriptions and specifications for similarity search
- rfp_requirements: RFP requirement text for matching
- agent_knowledge: Agent knowledge base and responses
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if chromadb is available
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Install with: pip install chromadb")


@dataclass
class ChromaCollection:
    """Collection configuration"""
    name: str
    description: str
    metadata_fields: List[str]


class ChromaDBManager:
    """
    ChromaDB Manager for vector storage and semantic search
    
    Collections:
    - products: Product embeddings for specification matching
    - rfp_requirements: RFP text embeddings for similarity search
    - agent_knowledge: Historical agent responses and knowledge
    """
    
    # Default collection configurations
    COLLECTIONS = {
        'products': ChromaCollection(
            name='products',
            description='Product specifications and descriptions',
            metadata_fields=['sku', 'oem', 'category', 'conductor_material', 'insulation_type']
        ),
        'rfp_requirements': ChromaCollection(
            name='rfp_requirements',
            description='RFP requirement texts for matching',
            metadata_fields=['rfp_id', 'requirement_number', 'product_type']
        ),
        'agent_knowledge': ChromaCollection(
            name='agent_knowledge',
            description='Agent historical knowledge and responses',
            metadata_fields=['agent_type', 'action_type', 'confidence']
        ),
        'standards': ChromaCollection(
            name='standards',
            description='Technical standards and specifications',
            metadata_fields=['standard_code', 'issuing_body', 'category']
        )
    }
    
    def __init__(
        self,
        persist_directory: str = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize ChromaDB Manager
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            embedding_model: Name of the embedding model to use
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")
        
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent / "db_vector")
        
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Set up embedding function - use default to avoid heavy dependencies
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        self._collections: Dict[str, Any] = {}
        logger.info(f"ChromaDB initialized at: {persist_directory}")
    
    def get_or_create_collection(self, name: str) -> Any:
        """Get or create a collection"""
        if name not in self._collections:
            config = self.COLLECTIONS.get(name)
            metadata = {"description": config.description} if config else {}
            
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata=metadata
            )
            logger.info(f"Collection '{name}' ready")
        
        return self._collections[name]
    
    def create_all_collections(self):
        """Create all predefined collections"""
        for name in self.COLLECTIONS:
            self.get_or_create_collection(name)
        logger.info(f"Created {len(self.COLLECTIONS)} collections")
    
    def delete_collection(self, name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(name)
            if name in self._collections:
                del self._collections[name]
            logger.info(f"Deleted collection: {name}")
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}")
    
    def reset_all(self):
        """Reset all collections"""
        self.client.reset()
        self._collections.clear()
        logger.info("ChromaDB reset complete")
    
    # ==================== PRODUCT OPERATIONS ====================
    
    def add_products(
        self,
        products: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Add products to the vector database
        
        Args:
            products: List of product dictionaries
            batch_size: Batch size for insertion
            
        Returns:
            Number of products added
        """
        collection = self.get_or_create_collection('products')
        
        ids = []
        documents = []
        metadatas = []
        
        for product in products:
            # Create document from product info
            doc_parts = [
                product.get('name', ''),
                product.get('description', ''),
                f"Material: {product.get('conductor_material', '')}",
                f"Size: {product.get('conductor_size_sqmm', '')} sqmm",
                f"Insulation: {product.get('insulation_type', '')}",
                f"Cores: {product.get('number_of_cores', '')}",
                f"Voltage: {product.get('voltage_rating', '')}",
            ]
            document = ' '.join(filter(None, doc_parts))
            
            # Prepare metadata
            metadata = {
                'sku': str(product.get('sku', '')),
                'oem': str(product.get('oem', product.get('manufacturer', ''))),
                'category': str(product.get('category', '')),
                'conductor_material': str(product.get('conductor_material', '')),
                'insulation_type': str(product.get('insulation_type', '')),
                'conductor_size': float(product.get('conductor_size_sqmm', 0) or 0),
                'price': float(product.get('unit_price', 0) or 0)
            }
            
            ids.append(str(product.get('sku', product.get('id', len(ids)))))
            documents.append(document)
            metadatas.append(metadata)
        
        # Add in batches
        added = 0
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_docs = documents[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            
            collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta
            )
            added += len(batch_ids)
        
        logger.info(f"Added {added} products to vector DB")
        return added
    
    def search_products(
        self,
        query: str,
        n_results: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search products using semantic similarity
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filters: Metadata filters
            
        Returns:
            List of matching products with scores
        """
        collection = self.get_or_create_collection('products')
        
        where = None
        if filters:
            # Build ChromaDB where clause
            where_conditions = []
            for key, value in filters.items():
                if value is not None:
                    where_conditions.append({key: value})
            if where_conditions:
                where = {"$and": where_conditions} if len(where_conditions) > 1 else where_conditions[0]
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        products = []
        if results['ids'] and results['ids'][0]:
            for i, id in enumerate(results['ids'][0]):
                products.append({
                    'id': id,
                    'document': results['documents'][0][i] if results['documents'] else None,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'similarity': 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
        
        return products
    
    # ==================== RFP REQUIREMENT OPERATIONS ====================
    
    def add_rfp_requirements(
        self,
        rfp_id: str,
        requirements: List[Dict[str, Any]]
    ) -> int:
        """Add RFP requirements to vector database"""
        collection = self.get_or_create_collection('rfp_requirements')
        
        ids = []
        documents = []
        metadatas = []
        
        for req in requirements:
            req_id = f"{rfp_id}_{req.get('requirement_number', len(ids))}"
            
            document = req.get('original_text', '')
            
            metadata = {
                'rfp_id': str(rfp_id),
                'requirement_number': int(req.get('requirement_number', 0)),
                'product_type': str(req.get('product_type', '')),
                'conductor_material': str(req.get('conductor_material', '')),
                'conductor_size': float(req.get('conductor_size_sqmm', 0) or 0),
                'insulation_type': str(req.get('insulation_type', ''))
            }
            
            ids.append(req_id)
            documents.append(document)
            metadatas.append(metadata)
        
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(ids)} requirements for RFP {rfp_id}")
        return len(ids)
    
    def find_similar_requirements(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar RFP requirements"""
        collection = self.get_or_create_collection('rfp_requirements')
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        requirements = []
        if results['ids'] and results['ids'][0]:
            for i, id in enumerate(results['ids'][0]):
                requirements.append({
                    'id': id,
                    'text': results['documents'][0][i] if results['documents'] else None,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'similarity': 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
        
        return requirements
    
    # ==================== AGENT KNOWLEDGE OPERATIONS ====================
    
    def add_agent_knowledge(
        self,
        agent_type: str,
        action: str,
        input_text: str,
        output_text: str,
        confidence: float = 1.0,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store agent knowledge for future reference"""
        collection = self.get_or_create_collection('agent_knowledge')
        
        import uuid
        knowledge_id = str(uuid.uuid4())[:8]
        
        document = f"Input: {input_text}\nOutput: {output_text}"
        
        meta = {
            'agent_type': str(agent_type),
            'action_type': str(action),
            'confidence': float(confidence),
            **(metadata or {})
        }
        
        collection.add(
            ids=[knowledge_id],
            documents=[document],
            metadatas=[meta]
        )
        
        return knowledge_id
    
    def search_agent_knowledge(
        self,
        query: str,
        agent_type: str = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search agent knowledge base"""
        collection = self.get_or_create_collection('agent_knowledge')
        
        where = None
        if agent_type:
            where = {'agent_type': agent_type}
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=['documents', 'metadatas', 'distances']
        )
        
        knowledge = []
        if results['ids'] and results['ids'][0]:
            for i, id in enumerate(results['ids'][0]):
                knowledge.append({
                    'id': id,
                    'content': results['documents'][0][i] if results['documents'] else None,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'similarity': 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
        
        return knowledge
    
    # ==================== UTILITY METHODS ====================
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        stats = {}
        for name in self.COLLECTIONS:
            try:
                collection = self.get_or_create_collection(name)
                stats[name] = {
                    'count': collection.count(),
                    'description': self.COLLECTIONS[name].description
                }
            except Exception as e:
                stats[name] = {'error': str(e)}
        return stats
    
    def clear_collection(self, name: str):
        """Clear all data from a collection"""
        collection = self.get_or_create_collection(name)
        # Get all IDs and delete them
        results = collection.get()
        if results['ids']:
            collection.delete(ids=results['ids'])
        logger.info(f"Cleared collection: {name}")


# Global ChromaDB manager instance
_chroma_manager: Optional[ChromaDBManager] = None


def get_chroma_manager(persist_directory: str = None) -> Optional[ChromaDBManager]:
    """
    Get or create the global ChromaDB manager
    
    Returns None if ChromaDB is not available
    """
    global _chroma_manager
    
    if not CHROMADB_AVAILABLE:
        return None
    
    if _chroma_manager is None:
        try:
            _chroma_manager = ChromaDBManager(persist_directory)
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return None
    
    return _chroma_manager


def init_chromadb(persist_directory: str = None) -> bool:
    """
    Initialize ChromaDB with all collections
    
    Returns:
        True if successful, False otherwise
    """
    manager = get_chroma_manager(persist_directory)
    if manager:
        manager.create_all_collections()
        return True
    return False
