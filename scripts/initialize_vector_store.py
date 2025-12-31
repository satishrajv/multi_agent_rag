"""
Initialize vector store with playbook data
"""
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.database import db_manager
from src.rag.vector_store import vector_store
from src.rag.chunking import text_chunker
from src.rag.retrieval import hybrid_retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_vector_store():
    """Load playbooks into vector store"""
    logger.info("Initializing vector store with playbooks...")

    # Get all playbooks from database
    playbooks = db_manager.get_all_playbooks()

    if not playbooks:
        logger.warning("No playbooks found in database. Run setup_data.py first.")
        return False

    logger.info(f"Found {len(playbooks)} playbooks")

    # Chunk and index each playbook
    all_chunks = []
    all_ids = []
    all_metadatas = []

    for playbook in playbooks:
        chunks = text_chunker.chunk_playbook(playbook)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{playbook['playbook_id']}_chunk_{i}"
            all_chunks.append(chunk['text'])
            all_ids.append(chunk_id)
            all_metadatas.append(chunk['metadata'])

    logger.info(f"Created {len(all_chunks)} chunks from {len(playbooks)} playbooks")

    # Add to vector store
    success = vector_store.add_documents(
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids
    )

    if success:
        logger.info("✓ Vector store initialized successfully")

        # Build BM25 index for hybrid retrieval
        logger.info("Building BM25 index...")
        bm25_docs = [
            {
                'id': all_ids[i],
                'text': all_chunks[i],
                'metadata': all_metadatas[i]
            }
            for i in range(len(all_chunks))
        ]

        hybrid_retriever.build_bm25_index(bm25_docs)
        logger.info("✓ BM25 index built successfully")

        return True
    else:
        logger.error("✗ Vector store initialization failed")
        return False


if __name__ == "__main__":
    success = initialize_vector_store()
    sys.exit(0 if success else 1)
