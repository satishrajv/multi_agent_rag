-- View All Chunks Stored in PostgreSQL
-- Shows chunks retrieved for user queries

-- Summary: Total queries and chunks
SELECT
    'SUMMARY' as section,
    (SELECT COUNT(*) FROM user_queries) as total_queries,
    (SELECT COUNT(*) FROM retrieved_chunks) as total_chunks;

-- Recent Queries with chunk count
SELECT
    'RECENT QUERIES' as section,
    uq.id,
    uq.query_text,
    uq.timestamp,
    uq.num_results,
    uq.use_reranking,
    COUNT(rc.id) as chunks_stored
FROM user_queries uq
LEFT JOIN retrieved_chunks rc ON uq.id = rc.query_id
GROUP BY uq.id, uq.query_text, uq.timestamp, uq.num_results, uq.use_reranking
ORDER BY uq.timestamp DESC
LIMIT 10;

-- All chunks for latest query
SELECT
    'CHUNKS FOR LATEST QUERY' as section,
    rc.chunk_rank,
    rc.playbook_id,
    LEFT(rc.title, 40) as title,
    rc.category,
    ROUND(rc.similarity_score::numeric, 4) as sim_score,
    ROUND(rc.rerank_score::numeric, 4) as rerank_score,
    LEFT(rc.chunk_text, 100) as chunk_preview
FROM retrieved_chunks rc
WHERE query_id = (SELECT MAX(id) FROM user_queries)
ORDER BY chunk_rank;

-- Full text of top chunk
SELECT
    'FULL TEXT - TOP CHUNK' as section,
    rc.playbook_id,
    rc.title,
    rc.category,
    ROUND(rc.similarity_score::numeric, 4) as score,
    rc.chunk_text
FROM retrieved_chunks rc
WHERE query_id = (SELECT MAX(id) FROM user_queries)
  AND chunk_rank = 1;
