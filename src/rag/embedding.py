"""
Embedding generation for RAG pipeline
"""
from typing import List
import numpy as np
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers or OpenAI"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        logger.info(f"Loading embedding model: {self.model_name}")

        # Detect if using OpenAI embedding model
        self.use_openai = self.model_name.startswith('text-embedding-')

        try:
            if self.use_openai:
                # Use OpenAI embeddings
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.openai_api_key)
                self.dimension = settings.embedding_dimension
                logger.info(f"Using OpenAI embedding model: {self.model_name} (dimension: {self.dimension})")
            else:
                # Use sentence-transformers (import only when needed to avoid PyTorch DLL issues)
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Embedding model loaded. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            Embedding vector as list
        """
        try:
            if self.use_openai:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=text
                )
                return response.data[0].embedding
            else:
                embedding = self.model.encode(text, convert_to_tensor=False)
                return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation error: {str(e)}")
            raise

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        try:
            if self.use_openai:
                # OpenAI supports batch embedding up to 2048 texts
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                return all_embeddings
            else:
                embeddings = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    show_progress_bar=True,
                    convert_to_tensor=False
                )
                return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding error: {str(e)}")
            raise

    def compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            emb1: First embedding
            emb2: Second embedding

        Returns:
            Similarity score (0 to 1)
        """
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)

        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


# Global embedding generator instance
embedding_generator = EmbeddingGenerator()
