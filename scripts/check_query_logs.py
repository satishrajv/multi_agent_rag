"""
Check Query Logs in PostgreSQL
Verify that chunks and queries are being stored
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.database import db_manager
from src.utils.query_logger import query_logger


def check_database():
    """Check if queries and chunks are being logged"""

    print("\n" + "=" * 60)
    print("QUERY LOGGING VERIFICATION")
    print("=" * 60 + "\n")

    try:
        # Get stats
        stats = query_logger.get_stats()

        print("📊 STATISTICS:")
        print(f"  Total Queries: {stats['total_queries']}")
        print(f"  Total Chunks Retrieved: {stats['total_chunks_retrieved']}")
        print(f"  Avg Results per Query: {stats['avg_results_per_query']}")
        print(f"  Queries with Reranking: {stats['queries_with_reranking']}")

        print("\n" + "-" * 60 + "\n")

        # Recent queries
        print("📝 RECENT QUERIES (Last 5):")
        history = query_logger.get_query_history(limit=5)

        if history:
            for i, query in enumerate(history, 1):
                print(f"\n{i}. Query ID: {query['id']}")
                print(f"   Text: {query['query_text']}")
                print(f"   Time: {query['timestamp']}")
                print(f"   Results: {query['num_results']}")
                print(f"   Reranking: {'Yes' if query['use_reranking'] else 'No'}")
        else:
            print("  [!] No queries found.")
            print("  → Run some searches in the Streamlit app first!")

        print("\n" + "-" * 60 + "\n")

        # Top playbooks
        print("🏆 TOP PLAYBOOKS (Most Retrieved):")
        top_playbooks = query_logger.get_top_playbooks(limit=5)

        if top_playbooks:
            for i, pb in enumerate(top_playbooks, 1):
                print(f"\n{i}. {pb['playbook_id']} - {pb['title']}")
                print(f"   Category: {pb['category']}")
                print(f"   Retrieved: {pb['retrieval_count']} times")
                print(f"   Avg Score: {pb['avg_score']:.4f}")
                print(f"   Avg Rank: {pb['avg_rank']:.2f}")
        else:
            print("  [!] No playbooks retrieved yet.")

        print("\n" + "-" * 60 + "\n")

        # Sample chunk details
        if stats['total_queries'] > 0:
            print("🔍 SAMPLE CHUNK DETAILS (Latest Query):")
            latest_query = history[0] if history else None

            if latest_query:
                details = query_logger.get_query_results(latest_query['id'])

                if details:
                    print(f"\nQuery: {details['query']['query_text']}")
                    print(f"Chunks Retrieved: {len(details['chunks'])}")

                    print("\nTop 3 Chunks:")
                    for i, chunk in enumerate(details['chunks'][:3], 1):
                        print(f"\n  {i}. Rank: {chunk['rank']}")
                        print(f"     Playbook: {chunk['playbook_id']} - {chunk['title']}")
                        print(f"     Category: {chunk['category']}")
                        print(f"     Similarity: {chunk['similarity_score']:.4f}")
                        if chunk['rerank_score']:
                            print(f"     Rerank Score: {chunk['rerank_score']:.4f}")
                        print(f"     Text: {chunk['text']}")

        print("\n" + "=" * 60)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 60 + "\n")

        if stats['total_queries'] == 0:
            print("💡 TIP: Go to http://localhost:8501 and run some searches!")
            print("   Then run this script again to see the logged data.\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_database()
