"""
Embedding Service - Gemini Text Embeddings
Convert text to 768-dimensional vectors for semantic search
"""

from google import genai
from google.genai import types
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Gemini"""
    
    def __init__(self, api_key: str):
        """
        Initialize embedding service
        
        Args:
            api_key: Google AI API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model = "models/text-embedding-004"
        logger.info(f"✅ EmbeddingService initialized with model: {self.model}")
    
    def embed_text(self, text: str, task_type: str = "retrieval_query") -> List[float]:
        """
        Embed single text using Gemini
        
        Args:
            text: Input text to embed
            task_type: Either "retrieval_query" (for search queries) 
                      or "retrieval_document" (for documents)
        
        Returns:
            768-dimensional embedding vector
        
        Example:
            >>> embedder = EmbeddingService(api_key="...")
            >>> vector = embedder.embed_text("Phở bó có bao nhiêu calo?")
            >>> len(vector)
            768
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 768  # Return zero vector for empty text
        
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=[types.Content(role="user", parts=[types.Part(text=text)])],
                config=types.EmbedContentConfig(task_type=task_type)
            )
            
            embedding = result.embeddings[0].values
            logger.debug(f"✓ Embedded text ({len(text)} chars) → {len(embedding)} dims")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Embedding failed: {str(e)}")
            raise
    
    def embed_batch(self, texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
        """
        Batch embed multiple texts
        
        Args:
            texts: List of texts to embed
            task_type: Task type for all texts
        
        Returns:
            List of 768-dimensional vectors
        
        Note:
            Currently processes sequentially. Can be optimized with true batch API.
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return []
        
        logger.info(f"🔄 Batch embedding {len(texts)} texts...")
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text, task_type=task_type)
                embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"   Progress: {i+1}/{len(texts)}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to embed text {i}: {str(e)}")
                # Add zero vector for failed embeddings
                embeddings.append([0.0] * 768)
        
        logger.info(f"✅ Batch embedding complete: {len(embeddings)} vectors")
        return embeddings


def get_embedding_service(api_key: str = None) -> EmbeddingService:
    """
    Factory function to get EmbeddingService instance
    
    Args:
        api_key: Google AI API key (required)
    
    Returns:
        Configured EmbeddingService instance
    """
    if not api_key:
        raise ValueError("Google AI API key is required")
    
    return EmbeddingService(api_key)
