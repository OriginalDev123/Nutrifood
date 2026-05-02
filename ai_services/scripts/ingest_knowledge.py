"""
Knowledge Base Ingestion Script
Load markdown files → chunk → embed → upload to Qdrant
Uses local sentence-transformer embeddings to match runtime retrieval.

Usage:
    python scripts/ingest_knowledge.py

Environment Variables:
    QDRANT_URL: Qdrant server URL (default: http://localhost:6333)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
import logging
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.services.local_embedding_service import get_local_embedding_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Chunk text into smaller pieces for embedding
    
    Strategy: Split by paragraphs, then combine until chunk_size
    
    Args:
        text: Input text
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    # Split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # If paragraph itself is too long, split it
        if len(para) > chunk_size * 2:
            # Split by sentences (simple split by ". ")
            sentences = [s.strip() + "." for s in para.split(". ") if s.strip()]
            
            for sent in sentences:
                if len(current_chunk) + len(sent) <= chunk_size:
                    current_chunk += " " + sent if current_chunk else sent
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sent
        else:
            # Normal paragraph
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
    
    # Add last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Filter out very short chunks
    chunks = [c for c in chunks if len(c) >= 50]
    
    return chunks


def load_markdown_files(knowledge_base_path: Path) -> List[Dict]:
    """
    Load all markdown files from knowledge base
    
    Args:
        knowledge_base_path: Path to knowledge_base/ directory
    
    Returns:
        List of documents with metadata
    """
    documents = []
    
    source_dirs = ["nutrition_facts", "recipes", "guidelines"]
    
    for source_dir in source_dirs:
        source_path = knowledge_base_path / source_dir
        
        if not source_path.exists():
            logger.warning(f"⚠️ Directory not found: {source_path}")
            continue
        
        logger.info(f"📂 Loading from {source_dir}/...")
        
        md_files = list(source_path.glob("*.md"))
        logger.info(f"   Found {len(md_files)} markdown files")
        
        for md_file in md_files:
            try:
                # Read file
                content = md_file.read_text(encoding="utf-8")
                
                # Extract title from filename or first heading
                title = md_file.stem.replace("_", " ").title()
                if content.startswith("# "):
                    first_line = content.split("\n")[0]
                    title = first_line.replace("# ", "").strip()
                
                # Chunk the content
                chunks = chunk_text(content, chunk_size=400, overlap=50)
                
                logger.info(f"   ✓ {md_file.name}: {len(chunks)} chunks")
                
                # Create document entries for each chunk
                for i, chunk in enumerate(chunks):
                    documents.append({
                        "id": f"{md_file.stem}_{i}",
                        "title": title,
                        "content": chunk,
                        "source": source_dir,
                        "chunk_index": i,
                        "filename": md_file.name
                    })
                    
            except Exception as e:
                logger.error(f"   ❌ Failed to load {md_file.name}: {str(e)}")
                continue
    
    return documents


def ingest_knowledge_base(qdrant_url: str, knowledge_base_path: Path):
    """
    Main ingestion pipeline
    
    Steps:
    1. Load markdown files
    2. Chunk documents
    3. Embed chunks
    4. Upload to Qdrant
    
    Args:
        qdrant_url: Qdrant server URL
        knowledge_base_path: Path to knowledge_base/ directory
    """
    start_time = time.time()
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Knowledge Base Ingestion")
    logger.info("=" * 60)
    
    # Initialize services
    logger.info(f"🔌 Connecting to Qdrant at {qdrant_url}...")
    client = QdrantClient(url=qdrant_url)
    
    logger.info("🧠 Initializing embedding service...")
    embedder = get_local_embedding_service()
    vector_size = embedder.get_embedding_dimension()

    collection_name = "nutriai_knowledge"
    
    # Create/recreate collection
    logger.info(f"📦 Creating collection '{collection_name}'...")
    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        logger.info("   ✓ Collection created")
    except Exception as e:
        logger.error(f"   ❌ Failed to create collection: {str(e)}")
        return
    
    # Load documents
    logger.info(f"\n📚 Loading markdown files from {knowledge_base_path}...")
    documents = load_markdown_files(knowledge_base_path)
    
    if not documents:
        logger.warning("⚠️ No documents found to ingest!")
        return
    
    logger.info(f"   ✓ Loaded {len(documents)} document chunks")
    
    # Embed documents
    logger.info(f"\n🔄 Embedding {len(documents)} chunks...")
    logger.info("   (This may take a few minutes...)")
    
    texts = [doc["content"] for doc in documents]
    embeddings = embedder.embed_batch(texts, task_type="retrieval_document")
    
    logger.info(f"   ✓ Generated {len(embeddings)} embeddings")
    
    # Create points
    logger.info("\n📝 Creating Qdrant points...")
    points = []
    
    for doc, embedding in zip(documents, embeddings):
        points.append(
            PointStruct(
                id=doc["id"],
                vector=embedding,
                payload={
                    "title": doc["title"],
                    "content": doc["content"],
                    "source": doc["source"],
                    "chunk_index": doc["chunk_index"],
                    "filename": doc.get("filename", "")
                }
            )
        )
    
    logger.info(f"   ✓ Created {len(points)} points")
    
    # Upload to Qdrant
    logger.info(f"\n⬆️ Uploading to Qdrant...")
    try:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        logger.info(f"   ✓ Upload complete")
    except Exception as e:
        logger.error(f"   ❌ Upload failed: {str(e)}")
        return
    
    # Verify
    logger.info(f"\n🔍 Verifying collection...")
    try:
        info = client.get_collection(collection_name=collection_name)
        logger.info(f"   ✓ Collection points: {info.points_count}")
        logger.info(f"   ✓ Collection vectors: {info.vectors_count}")
    except Exception as e:
        logger.warning(f"   ⚠️ Verification failed: {str(e)}")
    
    # Summary
    elapsed_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"📊 Statistics:")
    logger.info(f"   - Documents: {len(documents)} chunks")
    logger.info(f"   - Embeddings: {len(embeddings)} vectors")
    logger.info(f"   - Collection: {collection_name}")
    logger.info(f"   - Time: {elapsed_time:.1f}s")
    logger.info("=" * 60)


def main():
    """Main entry point"""
    
    # Get configuration
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # Determine knowledge base path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    knowledge_base_path = project_root / "knowledge_base"
    
    if not knowledge_base_path.exists():
        logger.error(f"❌ Knowledge base directory not found: {knowledge_base_path}")
        logger.error("   Create it with: mkdir -p knowledge_base/{{nutrition_facts,recipes,guidelines}}")
        sys.exit(1)
    
    # Run ingestion
    try:
        ingest_knowledge_base(qdrant_url, knowledge_base_path)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Ingestion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
