"""
Vector store interface for ChromaDB
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
import logging
from pathlib import Path

from ..config import settings
from .embedding import embedding_generator

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB vector store manager"""

    def __init__(self, collection_name: str = "playbooks"):
        self.collection_name = collection_name

        # Ensure vector store directory exists
        store_path = Path(settings.vector_store_path)
        store_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(store_path),
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Initialized collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize collection: {str(e)}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> bool:
        """
        Add documents to vector store

        Args:
            documents: List of text documents
            metadatas: List of metadata dicts
            ids: List of unique document IDs

        Returns:
            Success status
        """
        try:
            # Generate embeddings
            embeddings = embedding_generator.embed_batch(documents)

            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to collection")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            return False

    def similarity_search(
        self,
        query: str,
        top_k: int = None,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Perform similarity search

        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Metadata filters

        Returns:
            List of results with documents, metadata, and scores
        """
        try:
            top_k = top_k or settings.top_k_retrieval

            # Generate query embedding
            query_embedding = embedding_generator.embed_text(query)

            # Search
            where_filter = filter_dict if filter_dict else None

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "id": results['ids'][0][i],
                        "document": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "score": 1 - results['distances'][0][i]  # Convert distance to similarity
                    })

            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    def get_by_ids(self, ids: List[str]) -> List[Dict]:
        """Get documents by IDs"""
        try:
            results = self.collection.get(ids=ids)

            formatted_results = []
            for i in range(len(results['ids'])):
                formatted_results.append({
                    "id": results['ids'][i],
                    "document": results['documents'][i],
                    "metadata": results['metadatas'][i]
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Get by IDs error: {str(e)}")
            return []

    def delete_by_ids(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            return False

    def update_document(
        self,
        doc_id: str,
        document: str,
        metadata: Dict
    ) -> bool:
        """Update a document"""
        try:
            embedding = embedding_generator.embed_text(document)

            self.collection.update(
                ids=[doc_id],
                documents=[document],
                embeddings=[embedding],
                metadatas=[metadata]
            )

            logger.info(f"Updated document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            return False

    def count(self) -> int:
        """Get total document count"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Count error: {str(e)}")
            return 0

    def reset_collection(self) -> bool:
        """Delete and recreate collection (use with caution)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Reset error: {str(e)}")
            return False


# Factory function to create appropriate vector store
def create_vector_store(collection_name: str = "playbooks"):
    """Create vector store based on configuration"""
    if settings.vector_store_type == 'weaviate':
        from .vector_store_weaviate import WeaviateVectorStore
        return WeaviateVectorStore(collection_name)
    else:
        # Use ChromaDB by default
        return VectorStore(collection_name)


# Global vector store instance
vector_store = create_vector_store()
