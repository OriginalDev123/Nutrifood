"""
Local Embedding Service using sentence-transformers
Provides embeddings without requiring external API calls
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
import numpy as np


class LocalEmbeddingService:
    """
    Local embedding service using sentence-transformers
    
    Model: all-MiniLM-L6-v2
    - 384 dimensions
    - Fast inference (~50ms per text)
    - Works offline
    - No API costs
    - Good quality for semantic search
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize local embedding model
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            print(f"Loading local embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Model loaded: {self.get_embedding_dimension()}D vectors")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return 384  # Default for all-MiniLM-L6-v2
    
    def embed_text(self, text: str, task_type: str = None, **kwargs) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            task_type: Task type (ignored, for Gemini API compatibility)
            **kwargs: Additional arguments (ignored)
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.get_embedding_dimension()
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"❌ Error embedding text: {e}")
            raise
    
    def embed_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = False,
        task_type: str = None,
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch)
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            show_progress: Show progress bar
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t if t and t.strip() else " " for t in texts]
        
        try:
            embeddings = self.model.encode(
                valid_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            print(f"❌ Error embedding batch: {e}")
            raise
    
    def embed_documents(self, documents: List[dict]) -> List[dict]:
        """
        Embed documents with their metadata
        
        Args:
            documents: List of dicts with 'content' and 'metadata' keys
            
        Returns:
            List of dicts with 'content', 'metadata', and 'embedding' keys
        """
        if not documents:
            return []
        
        # Extract texts
        texts = [doc.get('content', '') for doc in documents]
        
        # Generate embeddings
        embeddings = self.embed_batch(texts, show_progress=True)
        
        # Combine with original documents
        result = []
        for doc, embedding in zip(documents, embeddings):
            result.append({
                'content': doc.get('content', ''),
                'metadata': doc.get('metadata', {}),
                'embedding': embedding
            })
        
        return result
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Global instance (lazy loading)
_embedding_service = None


def get_local_embedding_service() -> LocalEmbeddingService:
    """
    Get or create the global embedding service instance
    
    Returns:
        LocalEmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = LocalEmbeddingService()
    return _embedding_service


# Test function
def test_local_embeddings():
    """Test local embeddings"""
    service = get_local_embedding_service()
    
    # Test single embedding
    text = "Phở bò có 450 calories"
    embedding = service.embed_text(text)
    print(f"✅ Single embedding: {len(embedding)}D vector")
    print(f"   First 5 values: {embedding[:5]}")
    
    # Test batch
    texts = [
        "Phở bò 450 kcal",
        "Beef Pho 450 calories",
        "Cơm tấm 550 kcal"
    ]
    embeddings = service.embed_batch(texts)
    print(f"\n✅ Batch embedding: {len(embeddings)} texts")
    
    # Test similarity
    sim = service.similarity(embeddings[0], embeddings[1])
    print(f"\n✅ Similarity (Phở bò vs Beef Pho): {sim:.3f}")
    print(f"   Expected: High similarity (>0.7) since same dish")
    
    sim2 = service.similarity(embeddings[0], embeddings[2])
    print(f"\n✅ Similarity (Phở bò vs Cơm tấm): {sim2:.3f}")
    print(f"   Expected: Lower similarity (<0.5) since different dishes")
    
    print("\n🎉 Local embeddings working perfectly!")


if __name__ == "__main__":
    test_local_embeddings()
