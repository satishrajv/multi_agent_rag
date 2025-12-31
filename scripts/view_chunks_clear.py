"""
Clear Chunk Display - Shows all chunks retrieved from Weaviate
"""
import sys
from pathlib import Path
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.database import db_manager
from sqlalchemy import text as sql_text


def display_query_chunks(query_id: int = None):
    """Display chunks in a clear format"""

    try:
        with db_manager.get_session() as session:
            # Get latest query if no ID specified
            if query_id is None:
                result = session.execute(sql_text("SELECT MAX(id) FROM user_queries"))
                query_id = result.fetchone()[0]

                if not query_id:
                    print("\n[!] No queries found. Run some searches first!\n")
                    return

            # Get query details
            query_sql = sql_text("""
                SELECT
                    id,
                    query_text,
                    timestamp,
                    top_k,
                    use_reranking,
                    num_results
                FROM user_queries
                WHERE id = :query_id
            """)

            result = session.execute(query_sql, {'query_id': query_id})
            query = result.fetchone()

            if not query:
                print(f"\n[!] Query ID {query_id} not found\n")
                return

            # Get all chunks
            chunks_sql = sql_text("""
                SELECT
                    chunk_rank,
                    chunk_text,
                    playbook_id,
                    category,
                    title,
                    similarity_score,
                    rerank_score
                FROM retrieved_chunks
                WHERE query_id = :query_id
                ORDER BY chunk_rank
            """)

            result = session.execute(chunks_sql, {'query_id': query_id})
            chunks = result.fetchall()

            # Display
            print("\n" + "=" * 100)
            print("CHUNK RETRIEVAL DETAILS")
            print("=" * 100)

            print(f"\nUser Query: \"{query[1]}\"")
            print(f"Timestamp: {query[2]}")
            print(f"Query ID: {query[0]}")

            print("\n" + "-" * 100)
            print("RETRIEVAL CONFIGURATION")
            print("-" * 100)
            print(f"Top K Requested: {query[3]}")
            print(f"Total Chunks Retrieved from Weaviate: {query[5]}")
            print(f"Reranking Used: {'YES' if query[4] else 'NO'}")

            if query[4]:
                print("\nReranking Details:")
                print("  - Model: cross-encoder/ms-marco-MiniLM-L-6-v2")
                print("  - Purpose: Re-scores chunks for better relevance")
                print("  - Higher rerank score = more relevant to query")

            print("\n" + "=" * 100)
            print(f"RETRIEVED CHUNKS ({len(chunks)} total)")
            print("=" * 100)

            for chunk in chunks:
                rank = chunk[0]
                text = chunk[1]
                playbook_id = chunk[2]
                category = chunk[3]
                title = chunk[4]
                sim_score = chunk[5]
                rerank_score = chunk[6]

                print(f"\n{'-' * 100}")
                print(f"CHUNK #{rank}")
                print(f"{'-' * 100}")
                print(f"Playbook: {playbook_id} - {title}")
                print(f"Category: {category}")
                print(f"Vector Similarity Score: {sim_score:.4f}")
                if rerank_score is not None:
                    print(f"Rerank Score: {rerank_score:.4f}")
                print(f"\nChunk Text:")
                print("+" + "-" * 98 + "+")

                # Wrap text nicely
                lines = text.split('\n')
                for line in lines:
                    if len(line) <= 96:
                        print(f"| {line:<96} |")
                    else:
                        # Wrap long lines
                        words = line.split(' ')
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) + 1 <= 96:
                                current_line += word + " "
                            else:
                                print(f"| {current_line:<96} |")
                                current_line = word + " "
                        if current_line:
                            print(f"| {current_line:<96} |")

                print("+" + "-" * 98 + "+")

            print("\n" + "=" * 100)
            print("END OF CHUNKS")
            print("=" * 100 + "\n")

            # Summary
            if query[4]:  # If reranking was used
                print("SUMMARY:")
                print(f"  • Original vector search returned {len(chunks)} chunks")
                print(f"  • Chunks were re-ranked by cross-encoder model")
                print(f"  • Final ordering based on rerank scores")
                print(f"  • Chunk #{chunks[0][0]} has highest relevance (rerank: {chunks[0][6]:.4f})")
            else:
                print("SUMMARY:")
                print(f"  • Vector search returned {len(chunks)} chunks")
                print(f"  • Chunks ordered by cosine similarity")
                print(f"  • Chunk #{chunks[0][0]} has highest similarity ({chunks[0][5]:.4f})")
            print()

    except Exception as e:
        print(f"\n[X] Error: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='View chunks retrieved from Weaviate')
    parser.add_argument('--query-id', type=int, help='Specific query ID (default: latest)')

    args = parser.parse_args()

    display_query_chunks(args.query_id)
