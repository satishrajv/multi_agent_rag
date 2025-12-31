"""
Cross-encoder reranker for improving retrieval quality
"""
from typing import List, Dict
from sentence_transformers import CrossEncoder
import logging
import os
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)


class Reranker:
    """Cross-encoder reranker for re-scoring retrieved documents"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.model_dir = Path("models/reranker")
        self.model_dir.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Loading reranker model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            logger.info("Reranker model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load reranker: {str(e)}")
            raise

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = None
    ) -> List[Dict]:
        """
        Rerank documents using cross-encoder

        Args:
            query: Search query
            documents: List of documents with 'document' field
            top_k: Number of top results to return

        Returns:
            Reranked list of documents
        """
        if not documents:
            return []

        try:
            # Prepare query-document pairs
            pairs = [[query, doc['document']] for doc in documents]

            # Get relevance scores
            scores = self.model.predict(pairs)

            # Add scores to documents
            for i, doc in enumerate(documents):
                doc['rerank_score'] = float(scores[i])

            # Sort by rerank score
            reranked = sorted(
                documents,
                key=lambda x: x['rerank_score'],
                reverse=True
            )

            # Return top-k
            if top_k:
                reranked = reranked[:top_k]

            logger.info(f"Reranked {len(documents)} documents, returning top {len(reranked)}")
            return reranked

        except Exception as e:
            logger.error(f"Reranking error: {str(e)}")
            # Fallback: return original order
            return documents

    def score_pair(self, query: str, document: str) -> float:
        """
        Score a single query-document pair

        Args:
            query: Search query
            document: Document text

        Returns:
            Relevance score
        """
        try:
            score = self.model.predict([[query, document]])[0]
            return float(score)
        except Exception as e:
            logger.error(f"Scoring error: {str(e)}")
            return 0.0

    def save_model(self, version_name: str) -> str:
        """
        Save current model

        Args:
            version_name: Version identifier

        Returns:
            Path to saved model
        """
        try:
            save_path = self.model_dir / f"reranker_{version_name}"
            self.model.save(str(save_path))
            logger.info(f"Saved reranker model to {save_path}")
            return str(save_path)
        except Exception as e:
            logger.error(f"Model save error: {str(e)}")
            raise

    def load_model(self, model_path: str) -> bool:
        """
        Load a saved model

        Args:
            model_path: Path to model

        Returns:
            Success status
        """
        try:
            self.model = CrossEncoder(model_path)
            logger.info(f"Loaded reranker model from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Model load error: {str(e)}")
            return False

    def train(
        self,
        train_samples: List[Dict],
        epochs: int = 3,
        batch_size: int = 16
    ) -> Dict:
        """
        Fine-tune reranker on feedback data

        Args:
            train_samples: List of {'query': str, 'document': str, 'label': int}
            epochs: Training epochs
            batch_size: Batch size

        Returns:
            Training metrics
        """
        try:
            from sentence_transformers import InputExample
            from torch.utils.data import DataLoader

            # Convert to InputExample format
            train_examples = []
            for sample in train_samples:
                train_examples.append(
                    InputExample(
                        texts=[sample['query'], sample['document']],
                        label=float(sample['label'])
                    )
                )

            # Create DataLoader
            train_dataloader = DataLoader(
                train_examples,
                shuffle=True,
                batch_size=batch_size
            )

            # Train
            logger.info(f"Training reranker on {len(train_samples)} samples")
            self.model.fit(
                train_dataloader=train_dataloader,
                epochs=epochs,
                warmup_steps=100,
                show_progress_bar=True
            )

            logger.info("Reranker training completed")
            return {"samples": len(train_samples), "epochs": epochs}

        except Exception as e:
            logger.error(f"Training error: {str(e)}")
            raise


# Global reranker instance
reranker = Reranker()
