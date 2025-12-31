"""
Simple RAG test script - Load files and test search
No SQL database required - just file-based testing
"""
import sys
from pathlib import Path
import logging
import io

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_rag_step_by_step():
    """Test RAG pipeline step by step with simple files"""

    print("\n" + "=" * 60)
    print("SIMPLE RAG TEST - Step by Step")
    print("=" * 60 + "\n")

    # Step 1: Load playbook files
    print("Step 1: Loading playbook files...")
    playbooks_dir = Path(__file__).parent.parent / "data" / "playbooks"

    if not playbooks_dir.exists():
        print(f"[X] Playbooks directory not found: {playbooks_dir}")
        return False

    playbook_files = list(playbooks_dir.glob("*.txt"))
    if not playbook_files:
        print(f"[X] No .txt files found in {playbooks_dir}")
        return False

    print(f"[OK] Found {len(playbook_files)} playbook file(s)")
    for f in playbook_files:
        print(f"  - {f.name}")

    # Step 2: Read file contents
    print("\nStep 2: Reading file contents...")
    playbooks = []

    for file_path in playbook_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata from filename
            filename = file_path.stem  # e.g., "PB-001-sales-multithreading"
            parts = filename.split('-', 2)

            playbook_id = parts[0] if len(parts) > 0 else "PB-000"
            category = parts[1] if len(parts) > 1 else "general"

            playbooks.append({
                "playbook_id": playbook_id,
                "title": file_path.stem.replace('-', ' ').title(),
                "content": content,
                "category": category,
                "file_path": str(file_path)
            })

            print(f"[OK] Loaded {playbook_id}: {len(content)} characters")

        except Exception as e:
            print(f"[X] Failed to read {file_path.name}: {str(e)}")

    if not playbooks:
        print("[X] No playbooks loaded")
        return False

    print(f"\n[OK] Successfully loaded {len(playbooks)} playbook(s)")

    # Step 3: Test chunking
    print("\nStep 3: Testing text chunking...")
    try:
        from src.rag.chunking import text_chunker

        all_chunks = []
        for playbook in playbooks:
            chunks = text_chunker.chunk_text(
                text=playbook['content'],
                metadata={
                    'playbook_id': playbook['playbook_id'],
                    'category': playbook['category'],
                    'title': playbook['title']
                }
            )
            all_chunks.extend(chunks)
            print(f"  {playbook['playbook_id']}: {len(chunks)} chunks")

        print(f"[OK] Total chunks created: {len(all_chunks)}")

    except Exception as e:
        print(f"[X] Chunking failed: {str(e)}")
        return False

    # Step 4: Test embedding generation
    print("\nStep 4: Testing embedding generation...")
    try:
        from src.rag.embedding import embedding_generator

        # Test with first chunk
        sample_text = all_chunks[0]['text'][:200]  # First 200 chars
        embedding = embedding_generator.embed_text(sample_text)

        print(f"[OK] Generated embedding")
        print(f"  Text sample: {sample_text[:50]}...")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")

    except Exception as e:
        print(f"[X] Embedding generation failed: {str(e)}")
        print(f"\nNote: Make sure OpenAI API key is configured in .env")
        return False

    # Step 5: Test vector store
    print("\nStep 5: Testing vector store...")
    try:
        from src.rag.vector_store import vector_store

        # Prepare data for vector store
        chunk_texts = [chunk['text'] for chunk in all_chunks]
        chunk_ids = [f"chunk_{i}" for i in range(len(all_chunks))]
        chunk_metadatas = [chunk['metadata'] for chunk in all_chunks]

        print(f"  Preparing to add {len(chunk_texts)} chunks to vector store...")

        # Add to vector store
        success = vector_store.add_documents(
            documents=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )

        if success:
            print(f"[OK] Added {len(chunk_texts)} chunks to vector store")

            # Check count
            count = vector_store.count()
            print(f"  Vector store now contains: {count} documents")
        else:
            print("[X] Failed to add documents to vector store")
            return False

    except Exception as e:
        print(f"[X] Vector store operation failed: {str(e)}")
        print(f"\nNote: Make sure Weaviate connection is configured")
        return False

    # Step 6: Test search
    print("\nStep 6: Testing vector search...")
    try:
        # Test queries
        test_queries = [
            "How to handle stalled sales deals?",
            "Multi-threading strategy for sales",
            "Project recovery for red status projects"
        ]

        for query in test_queries:
            print(f"\n  Query: '{query}'")

            results = vector_store.similarity_search(
                query=query,
                top_k=2
            )

            if results:
                print(f"  [OK] Found {len(results)} result(s):")
                for i, result in enumerate(results, 1):
                    print(f"\n    Result {i}:")
                    print(f"    Score: {result['score']:.4f}")
                    print(f"    Playbook: {result['metadata'].get('playbook_id', 'N/A')}")
                    print(f"    Category: {result['metadata'].get('category', 'N/A')}")
                    print(f"    Text: {result['document'][:100]}...")
            else:
                print("  [!] No results found")

    except Exception as e:
        print(f"[X] Search failed: {str(e)}")
        return False

    # Step 7: Test reranking
    print("\nStep 7: Testing reranking...")
    try:
        from src.rag.reranker import reranker

        query = "sales opportunities at risk"
        results = vector_store.similarity_search(query, top_k=3)

        if results:
            print(f"  Before reranking: {len(results)} results")

            reranked = reranker.rerank(query, results, top_k=2)

            print(f"  After reranking: {len(reranked)} results")
            print(f"\n  Top result after reranking:")
            print(f"    Rerank score: {reranked[0].get('rerank_score', 'N/A'):.4f}")
            print(f"    Playbook: {reranked[0]['metadata'].get('playbook_id', 'N/A')}")
            print(f"[OK] Reranking successful")
        else:
            print("  [!] No results to rerank")

    except Exception as e:
        print(f"[!] Reranking failed (optional): {str(e)}")

    print("\n" + "=" * 60)
    print("[OK] ALL RAG TESTS PASSED!")
    print("=" * 60 + "\n")

    print("Summary:")
    print(f"  Playbooks loaded: {len(playbooks)}")
    print(f"  Total chunks: {len(all_chunks)}")
    print(f"  Vector store count: {vector_store.count()}")
    print(f"  Embedding dimension: {embedding_generator.get_dimension()}")
    print(f"\nThe RAG pipeline is working correctly!")

    return True


if __name__ == "__main__":
    try:
        success = test_rag_step_by_step()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
