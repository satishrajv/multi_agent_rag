"""
Query Logger - Store user queries and chunk retrievals in PostgreSQL
"""
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .database import db_manager

logger = logging.getLogger(__name__)


class QueryLogger:
    """Logs user queries and retrieved chunks to PostgreSQL"""

    def __init__(self):
        """Initialize query logger"""
        self.db = db_manager

    def log_query(
        self,
        query_text: str,
        results: List[Dict],
        top_k: int = 5,
        use_reranking: bool = False,
        user_session: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Log a user query and its retrieved chunks

        Args:
            query_text: The user's search query
            results: List of retrieved chunks with scores
            top_k: Number of results requested
            use_reranking: Whether reranking was used
            user_session: Optional user session identifier
            metadata: Optional additional metadata

        Returns:
            query_id: The ID of the logged query, or None if failed
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import text

                # Insert query
                query_sql = text("""
                    INSERT INTO user_queries
                    (query_text, top_k, use_reranking, num_results, user_session, query_metadata)
                    VALUES (:query_text, :top_k, :use_reranking, :num_results, :user_session, :query_metadata)
                    RETURNING id
                """)

                result = session.execute(query_sql, {
                    'query_text': query_text,
                    'top_k': top_k,
                    'use_reranking': use_reranking,
                    'num_results': len(results),
                    'user_session': user_session,
                    'query_metadata': json.dumps(metadata) if metadata else None
                })

                query_id = result.fetchone()[0]

                # Insert retrieved chunks
                if results:
                    chunk_sql = text("""
                        INSERT INTO retrieved_chunks
                        (query_id, chunk_rank, chunk_text, playbook_id, category, title,
                         similarity_score, rerank_score, chunk_metadata)
                        VALUES (:query_id, :chunk_rank, :chunk_text, :playbook_id, :category, :title,
                         :similarity_score, :rerank_score, :chunk_metadata)
                    """)

                    for rank, result in enumerate(results, 1):
                        session.execute(chunk_sql, {
                            'query_id': query_id,
                            'chunk_rank': rank,
                            'chunk_text': result.get('document', ''),
                            'playbook_id': result.get('metadata', {}).get('playbook_id', ''),
                            'category': result.get('metadata', {}).get('category', ''),
                            'title': result.get('metadata', {}).get('title', ''),
                            'similarity_score': result.get('score', 0.0),
                            'rerank_score': result.get('rerank_score'),
                            'chunk_metadata': json.dumps(result.get('metadata', {}))
                        })

                logger.info(
                    f"Logged query (ID: {query_id}): '{query_text[:50]}...' with {len(results)} results"
                )

                return query_id

        except Exception as e:
            logger.error(f"Failed to log query: {str(e)}", exc_info=True)
            return None

    def get_query_history(
        self,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get query history

        Args:
            limit: Maximum number of queries to return
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of query records
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import text

                query = """
                    SELECT
                        id, query_text, timestamp, top_k, use_reranking,
                        num_results, user_session
                    FROM user_queries
                    WHERE 1=1
                """
                params = {}

                if start_date:
                    query += " AND timestamp >= :start_date"
                    params['start_date'] = start_date

                if end_date:
                    query += " AND timestamp <= :end_date"
                    params['end_date'] = end_date

                query += " ORDER BY timestamp DESC LIMIT :limit"
                params['limit'] = limit

                result = session.execute(text(query), params)
                rows = result.fetchall()

                return [
                    {
                        'id': row[0],
                        'query_text': row[1],
                        'timestamp': row[2],
                        'top_k': row[3],
                        'use_reranking': row[4],
                        'num_results': row[5],
                        'user_session': row[6]
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get query history: {str(e)}", exc_info=True)
            return []

    def get_query_results(self, query_id: int) -> Dict:
        """
        Get a specific query and its retrieved chunks

        Args:
            query_id: The query ID

        Returns:
            Dictionary with query info and chunks
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import text

                # Get query
                query_sql = text("SELECT * FROM user_queries WHERE id = :query_id")
                result = session.execute(query_sql, {'query_id': query_id})
                query_row = result.fetchone()

                if not query_row:
                    return {}

                # Get chunks
                chunks_sql = text("""
                    SELECT * FROM retrieved_chunks
                    WHERE query_id = :query_id
                    ORDER BY chunk_rank
                """)
                result = session.execute(chunks_sql, {'query_id': query_id})
                chunk_rows = result.fetchall()

                return {
                    'query': {
                        'id': query_row[0],
                        'query_text': query_row[1],
                        'timestamp': query_row[2],
                        'top_k': query_row[3],
                        'use_reranking': query_row[4],
                        'num_results': query_row[5]
                    },
                    'chunks': [
                        {
                            'rank': row[2],
                            'playbook_id': row[4],
                            'category': row[5],
                            'title': row[6],
                            'similarity_score': row[7],
                            'rerank_score': row[8],
                            'text': row[3][:200] + '...' if len(row[3]) > 200 else row[3]
                        }
                        for row in chunk_rows
                    ]
                }

        except Exception as e:
            logger.error(f"Failed to get query results: {str(e)}", exc_info=True)
            return {}

    def get_top_queries(self, limit: int = 10) -> List[Dict]:
        """
        Get most frequent queries

        Args:
            limit: Number of top queries to return

        Returns:
            List of queries with frequency counts
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import text

                query = text("""
                    SELECT
                        query_text,
                        COUNT(*) as frequency,
                        AVG(num_results) as avg_results,
                        MAX(timestamp) as last_queried
                    FROM user_queries
                    GROUP BY query_text
                    ORDER BY frequency DESC
                    LIMIT :limit
                """)

                result = session.execute(query, {'limit': limit})
                rows = result.fetchall()

                return [
                    {
                        'query_text': row[0],
                        'frequency': row[1],
                        'avg_results': float(row[2]) if row[2] else 0,
                        'last_queried': row[3]
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get top queries: {str(e)}", exc_info=True)
            return []

    def get_top_playbooks(self, limit: int = 10) -> List[Dict]:
        """
        Get most frequently retrieved playbooks

        Args:
            limit: Number of top playbooks to return

        Returns:
            List of playbooks with retrieval counts
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import text

                query = text("""
                    SELECT
                        playbook_id,
                        title,
                        category,
                        COUNT(*) as retrieval_count,
                        AVG(similarity_score) as avg_score,
                        AVG(chunk_rank) as avg_rank
                    FROM retrieved_chunks
                    WHERE playbook_id IS NOT NULL AND playbook_id != ''
                    GROUP BY playbook_id, title, category
                    ORDER BY retrieval_count DESC
                    LIMIT :limit
                """)

                result = session.execute(query, {'limit': limit})
                rows = result.fetchall()

                return [
                    {
                        'playbook_id': row[0],
                        'title': row[1],
                        'category': row[2],
                        'retrieval_count': row[3],
                        'avg_score': float(row[4]) if row[4] else 0,
                        'avg_rank': float(row[5]) if row[5] else 0
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get top playbooks: {str(e)}", exc_info=True)
            return []

    def get_stats(self) -> Dict:
        """Get overall statistics"""
        try:
            with self.db.get_session() as session:
                from sqlalchemy import text

                # Total queries
                result = session.execute(text("SELECT COUNT(*) FROM user_queries"))
                total_queries = result.fetchone()[0]

                # Total chunks retrieved
                result = session.execute(text("SELECT COUNT(*) FROM retrieved_chunks"))
                total_chunks = result.fetchone()[0]

                # Average results per query
                result = session.execute(text("SELECT AVG(num_results) FROM user_queries"))
                avg_results = result.fetchone()[0] or 0

                # Queries with reranking
                result = session.execute(text("SELECT COUNT(*) FROM user_queries WHERE use_reranking = true"))
                reranked_queries = result.fetchone()[0]

                return {
                    'total_queries': total_queries,
                    'total_chunks_retrieved': total_chunks,
                    'avg_results_per_query': round(float(avg_results), 2) if avg_results else 0,
                    'queries_with_reranking': reranked_queries
                }

        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}", exc_info=True)
            return {}


# Global query logger instance
query_logger = QueryLogger()
