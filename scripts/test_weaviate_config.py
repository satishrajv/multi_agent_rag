"""
Test Weaviate cloud configuration
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings
import weaviate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_weaviate_connection():
    """Test Weaviate cloud connection and configuration"""

    print("\n" + "=" * 60)
    print("Weaviate Cloud Configuration Test")
    print("=" * 60 + "\n")

    # Check configuration
    print("Configuration:")
    print(f"  Vector Store Type: {settings.vector_store_type}")
    print(f"  Cluster Name: {settings.weaviate_cluster_name}")
    print(f"  Cluster URL: {settings.weaviate_cluster_url}")
    print(f"  gRPC URL: {settings.weaviate_grpc_url}")
    print(f"  API Key: {settings.weaviate_api_key[:20]}...{settings.weaviate_api_key[-4:]}")
    print()

    # Test 1: Weaviate client initialization
    print("Test 1: Connecting to Weaviate cloud...")
    try:
        from weaviate.classes.init import AdditionalConfig, Timeout

        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=settings.weaviate_cluster_url,
            auth_credentials=weaviate.auth.AuthApiKey(settings.weaviate_api_key),
            skip_init_checks=True,  # Skip gRPC health check for firewall compatibility
            additional_config=AdditionalConfig(
                timeout=Timeout(init=30, query=60, insert=120)
            )
        )
        print("✓ Connected to Weaviate cloud successfully")

        # Check cluster status
        if client.is_ready():
            print("✓ Weaviate cluster is ready")
        else:
            print("✗ Weaviate cluster not ready")
            return False

    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False

    # Test 2: Check existing collections
    print("\nTest 2: Checking collections...")
    try:
        collections = client.collections.list_all()
        print(f"✓ Found {len(collections)} collection(s)")

        for collection_name in collections.keys():
            print(f"  - {collection_name}")

    except Exception as e:
        print(f"⚠ Could not list collections: {str(e)}")

    # Test 3: Create test collection
    print("\nTest 3: Creating test collection...")
    try:
        test_collection_name = "TestCollection"

        # Delete if exists
        if client.collections.exists(test_collection_name):
            client.collections.delete(test_collection_name)
            print(f"  Deleted existing {test_collection_name}")

        # Create new collection
        from weaviate.classes.config import Configure, Property, DataType

        test_collection = client.collections.create(
            name=test_collection_name,
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="category", data_type=DataType.TEXT),
            ]
        )
        print(f"✓ Created test collection: {test_collection_name}")

    except Exception as e:
        print(f"✗ Collection creation failed: {str(e)}")
        return False

    # Test 4: Insert test data
    print("\nTest 4: Inserting test document...")
    try:
        from src.rag.embedding import embedding_generator

        test_doc = "This is a test document for Weaviate configuration."
        test_embedding = embedding_generator.embed_text(test_doc)

        with test_collection.batch.dynamic() as batch:
            batch.add_object(
                properties={
                    "content": test_doc,
                    "category": "test"
                },
                vector=test_embedding
            )

        print(f"✓ Inserted test document")
        print(f"  Document: {test_doc}")
        print(f"  Embedding dimension: {len(test_embedding)}")

    except Exception as e:
        print(f"✗ Insert failed: {str(e)}")
        client.collections.delete(test_collection_name)
        return False

    # Test 5: Search test
    print("\nTest 5: Testing vector search...")
    try:
        query = "test configuration document"
        query_embedding = embedding_generator.embed_text(query)

        from weaviate.classes.query import MetadataQuery

        response = test_collection.query.near_vector(
            near_vector=query_embedding,
            limit=1,
            return_metadata=MetadataQuery(distance=True)
        )

        if len(response.objects) > 0:
            obj = response.objects[0]
            distance = obj.metadata.distance
            similarity = 1 - (distance / 2.0)

            print(f"✓ Search successful")
            print(f"  Query: {query}")
            print(f"  Found: {obj.properties.get('content', '')}")
            print(f"  Similarity: {similarity:.4f}")
        else:
            print("⚠ No results found")

    except Exception as e:
        print(f"✗ Search failed: {str(e)}")
        client.collections.delete(test_collection_name)
        return False

    # Test 6: Test our Weaviate vector store class
    print("\nTest 6: Testing custom Weaviate vector store...")
    try:
        from src.rag.vector_store_weaviate import WeaviateVectorStore

        # Create temporary collection
        temp_store = WeaviateVectorStore(collection_name="TempPlaybooks")

        # Add a document
        success = temp_store.add_documents(
            documents=["Sample playbook for testing"],
            metadatas=[{
                "playbook_id": "PB-TEST",
                "title": "Test Playbook",
                "category": "test",
                "success_rate": 0.95,
                "num_cases": 5,
                "chunk_id": 0
            }],
            ids=["test-doc-1"]
        )

        if success:
            print("✓ Custom vector store works")

            # Test search
            results = temp_store.similarity_search(
                query="sample playbook",
                top_k=1
            )

            if results:
                print(f"  Search returned {len(results)} result(s)")
                print(f"  Score: {results[0]['score']:.4f}")
            else:
                print("  ⚠ Search returned no results")

            # Cleanup
            temp_store.reset_collection()
        else:
            print("✗ Custom vector store failed")
            return False

    except Exception as e:
        print(f"✗ Custom vector store test failed: {str(e)}")
        return False

    # Cleanup
    print("\nCleaning up test collections...")
    try:
        client.collections.delete(test_collection_name)
        print(f"✓ Deleted {test_collection_name}")
    except:
        pass

    try:
        client.close()
        print("✓ Closed Weaviate connection")
    except:
        pass

    print("\n" + "=" * 60)
    print("✓ All tests passed! Weaviate configuration is working.")
    print("=" * 60 + "\n")

    return True


if __name__ == "__main__":
    success = test_weaviate_connection()
    sys.exit(0 if success else 1)
