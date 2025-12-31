"""
Hybrid retrieval system combining dense (vector) and sparse (BM25) retrieval
"""
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
import logging

from ..config import settings
from .vector_store import vector_store
from ..utils.redis_cache import redis_cache

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combines dense and sparse retrieval for better results"""

    def __init__(
        self,
        dense_weight: float = None,
        sparse_weight: float = None
    ):
        self.dense_weight = dense_weight or settings.hybrid_dense_weight
        self.sparse_weight = sparse_weight or settings.hybrid_sparse_weight

        # BM25 index (will be built from documents)
        self.bm25_index = None
        self.bm25_documents = []
        self.bm25_ids = []
        self.bm25_metadatas = []

    def build_bm25_index(self, documents: List[Dict]) -> bool:
        """
        Build BM25 index from documents

        Args:
            documents: List of docs with 'id', 'text', 'metadata'

        Returns:
            Success status
        """
        try:
            self.bm25_documents = [doc['text'] for doc in documents]
            self.bm25_ids = [doc['id'] for doc in documents]
            self.bm25_metadatas = [doc['metadata'] for doc in documents]

            # Tokenize for BM25
            tokenized_docs = [doc.lower().split() for doc in self.bm25_documents]
            self.bm25_index = BM25Okapi(tokenized_docs)

            logger.info(f"Built BM25 index with {len(documents)} documents")
            return True

        except Exception as e:
            logger.error(f"BM25 index building error: {str(e)}")
            return False

    def bm25_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Perform BM25 sparse retrieval

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of results with scores
        """
        if not self.bm25_index:
            logger.warning("BM25 index not built yet")
            return []

        try:
            tokenized_query = query.lower().split()
            scores = self.bm25_index.get_scores(tokenized_query)

            # Get top-k indices
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:top_k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include non-zero scores
                    results.append({
                        "id": self.bm25_ids[idx],
                        "document": self.bm25_documents[idx],
                        "metadata": self.bm25_metadatas[idx],
                        "score": float(scores[idx])
                    })

            return results

        except Exception as e:
            logger.error(f"BM25 search error: {str(e)}")
            return []

    def hybrid_search(
        self,
        query: str,
        top_k: int = None,
        filter_dict: Optional[Dict] = None,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Perform hybrid search combining dense and sparse retrieval

        Args:
            query: Search query
            top_k: Number of final results
            filter_dict: Metadata filters for dense search
            use_cache: Whether to use caching

        Returns:
            Ranked list of results
        """
        top_k = top_k or settings.top_k_retrieval

        # Check cache first
        if use_cache:
            cached_results = redis_cache.get_retrieval_results(query)
            if cached_results:
                logger.info("Retrieved results from cache")
                return cached_results[:top_k]

        try:
            # Dense retrieval (vector search)
            dense_results = vector_store.similarity_search(
                query=query,
                top_k=top_k * 2,  # Retrieve more for fusion
                filter_dict=filter_dict
            )

            # Sparse retrieval (BM25)
            sparse_results = self.bm25_search(query, top_k=top_k * 2)

            # Combine scores
            combined_scores = {}

            # Add dense scores
            for result in dense_results:
                doc_id = result['id']
                combined_scores[doc_id] = {
                    'score': self.dense_weight * result['score'],
                    'document': result['document'],
                    'metadata': result['metadata']
                }

            # Add sparse scores
            for result in sparse_results:
                doc_id = result['id']
                # Normalize BM25 score (simple min-max)
                normalized_bm25 = min(result['score'] / 10.0, 1.0)

                if doc_id in combined_scores:
                    combined_scores[doc_id]['score'] += self.sparse_weight * normalized_bm25
                else:
                    combined_scores[doc_id] = {
                        'score': self.sparse_weight * normalized_bm25,
                        'document': result['document'],
                        'metadata': result['metadata']
                    }

            # Sort by combined score
            sorted_results = sorted(
                [
                    {
                        'id': doc_id,
                        'document': data['document'],
                        'metadata': data['metadata'],
                        'score': data['score']
                    }
                    for doc_id, data in combined_scores.items()
                ],
                key=lambda x: x['score'],
                reverse=True
            )

            final_results = sorted_results[:top_k]

            # Cache results
            if use_cache:
                redis_cache.cache_retrieval_results(query, final_results)

            logger.info(f"Hybrid search returned {len(final_results)} results")
            return final_results

        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            # Fallback to dense-only search
            return vector_store.similarity_search(query, top_k, filter_dict)

    def rebuild_index_from_vector_store(self) -> bool:
        """Rebuild BM25 index from current vector store contents"""
        try:
            # This is a simplified version - in production, you'd fetch all docs
            logger.warning("rebuild_index_from_vector_store not fully implemented")
            return False
        except Exception as e:
            logger.error(f"Index rebuild error: {str(e)}")
            return False


# Global hybrid retriever instance
hybrid_retriever = HybridRetriever()
