"""
Retrieval Service - Qdrant Vector Search
Semantic search over knowledge base using vector similarity
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
import logging

from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for semantic search using Qdrant vector database"""
    
    def __init__(self, qdrant_url: str, embedding_service: EmbeddingService):
        """
        Initialize retrieval service
        
        Args:
            qdrant_url: Qdrant server URL (e.g., "http://qdrant:6333")
            embedding_service: EmbeddingService instance for query encoding
        """
        self.client = QdrantClient(url=qdrant_url)
        self.embedding_service = embedding_service
        self.collection_name = "nutriai_knowledge"
        self.vector_size = self.embedding_service.get_embedding_dimension()
        logger.info(
            f"✅ RetrievalService connected to Qdrant at {qdrant_url} with {self.vector_size}D embeddings"
        )
    
    def create_collection(self, recreate: bool = False):
        """
        Create Qdrant collection for knowledge base
        
        Args:
            recreate: If True, delete existing collection first
        """
        try:
            if recreate:
                logger.warning(f"⚠️ Recreating collection '{self.collection_name}'...")
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                )
            else:
                # Check if collection exists
                collections = self.client.get_collections().collections
                exists = any(c.name == self.collection_name for c in collections)
                
                if not exists:
                    logger.info(f"📦 Creating new collection '{self.collection_name}'...")
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                    )
                else:
                    logger.info(f"✓ Collection '{self.collection_name}' already exists")
            
            logger.info(f"✅ Collection '{self.collection_name}' ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection: {str(e)}")
            raise
    
    def search(
        self, 
        query: str, 
        top_k: int = 3,
        score_threshold: float = 0.5,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar documents using semantic similarity
        
        Args:
            query: User's search query
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)
            source_filter: Optional filter by source type (e.g., "nutrition_facts")
        
        Returns:
            List of dicts with keys: title, content, source, score
        
        Example:
            >>> retrieval = RetrievalService(...)
            >>> results = retrieval.search("Phở bò có bao nhiêu calo?", top_k=3)
            >>> print(results[0]['title'])
            'Phở Bò Thông Tin Dinh Dưỡng'
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        try:
            # Encode query to vector
            logger.debug(f"🔍 Searching for: {query[:50]}...")
            query_vector = self.embedding_service.embed_text(query, task_type="retrieval_query")
            
            # Build filter if source specified
            search_filter = None
            if source_filter:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=source_filter)
                        )
                    ]
                )
            
            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            # Format results
            formatted_results = []
            for hit in results:
                formatted_results.append({
                    "title": hit.payload.get("title", "Untitled"),
                    "content": hit.payload.get("content", ""),
                    "source": hit.payload.get("source", "unknown"),
                    "score": round(hit.score, 4),
                    "chunk_index": hit.payload.get("chunk_index", 0)
                })
            
            logger.info(f"✅ Found {len(formatted_results)} relevant documents (threshold: {score_threshold})")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            # Return empty list instead of raising - graceful degradation
            return []
    
    def get_collection_info(self) -> Dict:
        """
        Get information about the knowledge base collection
        
        Returns:
            Dict with collection stats (count, size, etc.)
        """
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"❌ Failed to get collection info: {str(e)}")
            return {"error": str(e)}
    
    def add_documents(self, documents: List[Dict]) -> int:
        """
        Add documents to the knowledge base
        
        Args:
            documents: List of dicts with keys: id, title, content, source
        
        Returns:
            Number of documents added
        
        Example:
            >>> docs = [
            ...     {
            ...         "id": "pho_bo_1",
            ...         "title": "Phở Bò",
            ...         "content": "Phở bò là món ăn...",
            ...         "source": "nutrition_facts"
            ...     }
            ... ]
            >>> count = retrieval.add_documents(docs)
        """
        if not documents:
            logger.warning("No documents to add")
            return 0
        
        try:
            logger.info(f"📝 Adding {len(documents)} documents...")
            
            # Embed all documents
            texts = [doc["content"] for doc in documents]
            embeddings = self.embedding_service.embed_batch(texts, task_type="retrieval_document")
            
            # Create points
            points = []
            for doc, embedding in zip(documents, embeddings):
                points.append(
                    PointStruct(
                        id=doc["id"],
                        vector=embedding,
                        payload={
                            "title": doc.get("title", ""),
                            "content": doc.get("content", ""),
                            "source": doc.get("source", "unknown"),
                            "chunk_index": doc.get("chunk_index", 0)
                        }
                    )
                )
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ Added {len(points)} documents to collection")
            return len(points)
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {str(e)}")
            raise


def get_retrieval_service(
    qdrant_url: str,
    embedding_service: EmbeddingService
) -> RetrievalService:
    """
    Factory function to get RetrievalService instance
    
    Args:
        qdrant_url: Qdrant server URL
        embedding_service: Configured EmbeddingService
    
    Returns:
        Configured RetrievalService instance
    """
    return RetrievalService(qdrant_url, embedding_service)
