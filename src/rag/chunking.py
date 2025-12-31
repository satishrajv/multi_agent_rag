"""
Text chunking strategies for RAG pipeline
"""
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """Handles text chunking for RAG pipeline"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_text(
        self,
        text: str,
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Chunk text with metadata

        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk

        Returns:
            List of chunks with metadata
        """
        try:
            chunks = self.splitter.split_text(text)

            result = []
            for i, chunk in enumerate(chunks):
                chunk_data = {
                    "text": chunk,
                    "chunk_id": i,
                    "metadata": metadata or {}
                }
                result.append(chunk_data)

            logger.info(f"Created {len(result)} chunks from text of length {len(text)}")
            return result

        except Exception as e:
            logger.error(f"Chunking error: {str(e)}")
            raise

    def chunk_documents(
        self,
        documents: List[Dict]
    ) -> List[Dict]:
        """
        Chunk multiple documents

        Args:
            documents: List of documents with 'content' and optional 'metadata'

        Returns:
            List of all chunks from all documents
        """
        all_chunks = []

        for doc_idx, doc in enumerate(documents):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            metadata['doc_id'] = doc_idx

            chunks = self.chunk_text(content, metadata)
            all_chunks.extend(chunks)

        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks

    def chunk_playbook(
        self,
        playbook: Dict
    ) -> List[Dict]:
        """
        Chunk a playbook document

        Args:
            playbook: Playbook dict with title, content, category, etc.

        Returns:
            List of chunks with playbook metadata
        """
        metadata = {
            "playbook_id": playbook.get('playbook_id', ''),
            "title": playbook.get('title', ''),
            "category": playbook.get('category', ''),
            "success_rate": playbook.get('success_rate', 0),
            "num_cases": playbook.get('num_cases', 0)
        }

        # Combine title and content for better context
        full_text = f"Title: {playbook.get('title', '')}\n\n{playbook.get('content', '')}"

        return self.chunk_text(full_text, metadata)


# Global chunker instance
text_chunker = TextChunker()
