"""
Test custom RAG queries without database
"""
import sys
from pathlib import Path

# Fix Windows console encoding
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.rag.vector_store import vector_store

def test_query(query: str, top_k: int = 3):
    """Test a custom query against the RAG system"""
    print(f"\nQuery: '{query}'")
    print("=" * 60)

    # Search
    results = vector_store.similarity_search(query, top_k=top_k)

    if not results:
        print("[!] No results found")
        return

    # Print results
    print(f"[OK] Found {len(results)} result(s):\n")

    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Score: {result['score']:.4f}")
        print(f"  Playbook: {result['metadata'].get('playbook_id', 'N/A')}")
        print(f"  Category: {result['metadata'].get('category', 'N/A')}")
        print(f"  Title: {result['metadata'].get('title', 'N/A')}")
        print(f"  Text: {result['document'][:150]}...")
        print()


if __name__ == "__main__":
    # Test different queries
    test_queries = [
        "How do I revive a dead sales opportunity?",
        "What to do when a project is running behind schedule?",
        "Strategies for engaging multiple stakeholders",
        "How to handle overdue tasks?",
    ]

    for query in test_queries:
        test_query(query, top_k=2)
        print("\n" + "-" * 60 + "\n")
