"""
View Chunks Retrieved for User Queries
Shows all chunks that were retrieved and stored in PostgreSQL
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.query_logger import query_logger


def view_all_queries_and_chunks():
    """Display all queries and their retrieved chunks"""

    print("\n" + "=" * 80)
    print("QUERY CHUNKS VIEWER - All Stored Retrievals")
    print("=" * 80 + "\n")

    # Get all queries
    queries = query_logger.get_query_history(limit=50)

    if not queries:
        print("[!] No queries found in database.")
        print("    Run some searches at http://localhost:8501 first!\n")
        return

    print(f"Found {len(queries)} query/queries in database\n")

    for query in queries:
        print("\n" + "=" * 80)
        print(f"QUERY ID: {query['id']}")
        print("=" * 80)
        print(f"Query Text: {query['query_text']}")
        print(f"Timestamp: {query['timestamp']}")
        print(f"Results: {query['num_results']}")
        print(f"Top K: {query['top_k']}")
        print(f"Reranking: {'Yes' if query['use_reranking'] else 'No'}")
        print("-" * 80)

        # Get chunks for this query
        details = query_logger.get_query_results(query['id'])

        if details and 'chunks' in details:
            chunks = details['chunks']
            print(f"\nRetrieved {len(chunks)} chunks:\n")

            for chunk in chunks:
                print(f"  RANK {chunk['rank']}:")
                print(f"    Playbook ID: {chunk['playbook_id']}")
                print(f"    Title: {chunk['title']}")
                print(f"    Category: {chunk['category']}")
                print(f"    Similarity Score: {chunk['similarity_score']:.4f}")
                if chunk['rerank_score']:
                    print(f"    Rerank Score: {chunk['rerank_score']:.4f}")
                print(f"    Text Preview: {chunk['text']}")
                print()

        else:
            print("  [!] No chunks found for this query\n")

    print("=" * 80)
    print("END OF QUERY CHUNKS")
    print("=" * 80 + "\n")


def view_specific_query(query_id: int):
    """View chunks for a specific query"""

    print("\n" + "=" * 80)
    print(f"CHUNKS FOR QUERY ID: {query_id}")
    print("=" * 80 + "\n")

    details = query_logger.get_query_results(query_id)

    if not details:
        print(f"[!] Query ID {query_id} not found.\n")
        return

    # Query info
    query = details['query']
    print(f"Query Text: {query['query_text']}")
    print(f"Timestamp: {query['timestamp']}")
    print(f"Results: {query['num_results']}")
    print(f"Reranking: {'Yes' if query['use_reranking'] else 'No'}")
    print("\n" + "-" * 80 + "\n")

    # Chunks
    chunks = details['chunks']
    print(f"Retrieved {len(chunks)} chunks:\n")

    for chunk in chunks:
        print(f"RANK {chunk['rank']}:")
        print(f"  Playbook: {chunk['playbook_id']} - {chunk['title']}")
        print(f"  Category: {chunk['category']}")
        print(f"  Similarity: {chunk['similarity_score']:.4f}", end="")
        if chunk['rerank_score']:
            print(f" | Rerank: {chunk['rerank_score']:.4f}")
        else:
            print()
        print(f"  Text: {chunk['text']}")
        print()

    print("=" * 80 + "\n")


def view_full_chunk_text(query_id: int, chunk_rank: int):
    """View the full text of a specific chunk"""

    print("\n" + "=" * 80)
    print(f"FULL CHUNK TEXT - Query {query_id}, Rank {chunk_rank}")
    print("=" * 80 + "\n")

    # Query database directly for full text
    from src.utils.database import db_manager
    from sqlalchemy import text

    try:
        with db_manager.get_session() as session:
            query = text("""
                SELECT
                    rc.chunk_text,
                    rc.playbook_id,
                    rc.title,
                    rc.category,
                    rc.similarity_score,
                    rc.rerank_score,
                    uq.query_text
                FROM retrieved_chunks rc
                JOIN user_queries uq ON rc.query_id = uq.id
                WHERE rc.query_id = :query_id AND rc.chunk_rank = :chunk_rank
            """)

            result = session.execute(query, {
                'query_id': query_id,
                'chunk_rank': chunk_rank
            })

            row = result.fetchone()

            if not row:
                print(f"[!] Chunk not found (Query {query_id}, Rank {chunk_rank})\n")
                return

            print(f"Query: {row[6]}\n")
            print(f"Playbook: {row[1]} - {row[2]}")
            print(f"Category: {row[3]}")
            print(f"Similarity Score: {row[4]:.4f}")
            if row[5]:
                print(f"Rerank Score: {row[5]:.4f}")
            print("\n" + "-" * 80 + "\n")
            print("FULL CHUNK TEXT:")
            print("-" * 80)
            print(row[0])
            print("-" * 80 + "\n")

    except Exception as e:
        print(f"[X] Error: {str(e)}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='View query chunks from PostgreSQL')
    parser.add_argument('--query-id', type=int, help='View chunks for specific query ID')
    parser.add_argument('--chunk-rank', type=int, help='View full text of specific chunk rank (requires --query-id)')
    parser.add_argument('--all', action='store_true', help='View all queries and chunks (default)')

    args = parser.parse_args()

    if args.chunk_rank and args.query_id:
        # View specific chunk full text
        view_full_chunk_text(args.query_id, args.chunk_rank)
    elif args.query_id:
        # View specific query
        view_specific_query(args.query_id)
    else:
        # View all queries (default)
        view_all_queries_and_chunks()
