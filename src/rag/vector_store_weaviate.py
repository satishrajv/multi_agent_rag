"""
Weaviate vector store interface for cloud deployment
"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from typing import List, Dict, Optional
import logging
import uuid

from ..config import settings
from .embedding import embedding_generator

logger = logging.getLogger(__name__)


class WeaviateVectorStore:
    """Weaviate cloud vector store manager"""

    def __init__(self, collection_name: str = "Playbooks"):
        self.collection_name = collection_name

        # Initialize Weaviate client
        try:
            from weaviate.classes.init import AdditionalConfig, Timeout

            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=settings.weaviate_cluster_url,
                auth_credentials=weaviate.auth.AuthApiKey(settings.weaviate_api_key),
                skip_init_checks=True,  # Skip gRPC health check for firewall compatibility
                additional_config=AdditionalConfig(
                    timeout=Timeout(init=30, query=60, insert=120)
                )
            )

            logger.info(f"Connected to Weaviate cluster: {settings.weaviate_cluster_name}")

            # Get or create collection
            self._initialize_collection()

        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            raise

    def _initialize_collection(self):
        """Initialize or get the collection"""
        try:
            # Check if collection exists
            if self.client.collections.exists(self.collection_name):
                self.collection = self.client.collections.get(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            else:
                # Create new collection with OpenAI embeddings
                self.collection = self.client.collections.create(
                    name=self.collection_name,
                    vectorizer_config=Configure.Vectorizer.none(),  # We provide our own vectors
                    properties=[
                        Property(name="document", data_type=DataType.TEXT),
                        Property(name="playbook_id", data_type=DataType.TEXT),
                        Property(name="title", data_type=DataType.TEXT),
                        Property(name="category", data_type=DataType.TEXT),
                        Property(name="success_rate", data_type=DataType.NUMBER),
                        Property(name="num_cases", data_type=DataType.INT),
                        Property(name="chunk_id", data_type=DataType.INT),
                    ]
                )
                logger.info(f"Created new collection: {self.collection_name}")

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
            logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = embedding_generator.embed_batch(documents)

            # Prepare data objects
            with self.collection.batch.dynamic() as batch:
                for i, (doc, metadata, doc_id) in enumerate(zip(documents, metadatas, ids)):
                    properties = {
                        "document": doc,
                        "playbook_id": metadata.get("playbook_id", ""),
                        "title": metadata.get("title", ""),
                        "category": metadata.get("category", ""),
                        "success_rate": float(metadata.get("success_rate", 0.0)),
                        "num_cases": int(metadata.get("num_cases", 0)),
                        "chunk_id": int(metadata.get("chunk_id", 0)),
                    }

                    # Generate valid UUID from doc_id if not already a valid UUID
                    try:
                        valid_uuid = uuid.UUID(doc_id)
                    except (ValueError, AttributeError):
                        # Generate deterministic UUID from string ID
                        valid_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, doc_id)

                    batch.add_object(
                        properties=properties,
                        vector=embeddings[i],
                        uuid=valid_uuid
                    )

            logger.info(f"Added {len(documents)} documents to Weaviate")
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

            # Build Weaviate query
            query_builder = self.collection.query.near_vector(
                near_vector=query_embedding,
                limit=top_k,
                return_metadata=MetadataQuery(distance=True)
            )

            # Add filters if provided
            if filter_dict:
                # Build filter conditions
                from weaviate.classes.query import Filter
                filters = []
                for key, value in filter_dict.items():
                    filters.append(Filter.by_property(key).equal(value))

                if len(filters) == 1:
                    query_builder = query_builder.with_where(filters[0])
                elif len(filters) > 1:
                    # Combine multiple filters with AND
                    combined_filter = filters[0]
                    for f in filters[1:]:
                        combined_filter = combined_filter & f
                    query_builder = query_builder.with_where(combined_filter)

            # Execute query
            response = query_builder.objects

            # Format results
            formatted_results = []
            for obj in response:
                # Convert distance to similarity (distance is 0-2 for cosine)
                similarity = 1 - (obj.metadata.distance / 2.0)

                formatted_results.append({
                    "id": str(obj.uuid),
                    "document": obj.properties.get("document", ""),
                    "metadata": {
                        "playbook_id": obj.properties.get("playbook_id", ""),
                        "title": obj.properties.get("title", ""),
                        "category": obj.properties.get("category", ""),
                        "success_rate": obj.properties.get("success_rate", 0.0),
                        "num_cases": obj.properties.get("num_cases", 0),
                        "chunk_id": obj.properties.get("chunk_id", 0),
                    },
                    "score": float(similarity)
                })

            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    def get_by_ids(self, ids: List[str]) -> List[Dict]:
        """Get documents by IDs"""
        try:
            formatted_results = []

            for doc_id in ids:
                obj = self.collection.query.fetch_object_by_id(doc_id)

                if obj:
                    formatted_results.append({
                        "id": str(obj.uuid),
                        "document": obj.properties.get("document", ""),
                        "metadata": {
                            "playbook_id": obj.properties.get("playbook_id", ""),
                            "title": obj.properties.get("title", ""),
                            "category": obj.properties.get("category", ""),
                            "success_rate": obj.properties.get("success_rate", 0.0),
                            "num_cases": obj.properties.get("num_cases", 0),
                        }
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Get by IDs error: {str(e)}")
            return []

    def delete_by_ids(self, ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            for doc_id in ids:
                self.collection.data.delete_by_id(doc_id)

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
            # Generate new embedding
            embedding = embedding_generator.embed_text(document)

            properties = {
                "document": document,
                "playbook_id": metadata.get("playbook_id", ""),
                "title": metadata.get("title", ""),
                "category": metadata.get("category", ""),
                "success_rate": float(metadata.get("success_rate", 0.0)),
                "num_cases": int(metadata.get("num_cases", 0)),
            }

            self.collection.data.update(
                uuid=doc_id,
                properties=properties,
                vector=embedding
            )

            logger.info(f"Updated document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            return False

    def count(self) -> int:
        """Get total document count"""
        try:
            result = self.collection.aggregate.over_all(total_count=True)
            return result.total_count

        except Exception as e:
            logger.error(f"Count error: {str(e)}")
            return 0

    def reset_collection(self) -> bool:
        """Delete and recreate collection (use with caution)"""
        try:
            self.client.collections.delete(self.collection_name)
            self._initialize_collection()
            logger.info(f"Reset collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Reset error: {str(e)}")
            return False

    def close(self):
        """Close the Weaviate client connection"""
        try:
            self.client.close()
            logger.info("Weaviate client connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.close()
        except:
            pass


# Factory function to create the appropriate vector store
def create_vector_store(collection_name: str = "Playbooks"):
    """Create vector store based on configuration"""
    if settings.vector_store_type == 'weaviate':
        return WeaviateVectorStore(collection_name)
    else:
        # Import and return ChromaDB store
        from .vector_store import VectorStore
        return VectorStore(collection_name)


# Global vector store instance
vector_store = create_vector_store()
