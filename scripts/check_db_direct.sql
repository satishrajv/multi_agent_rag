-- Quick Database Verification Script
-- Run this to check if chunks are being stored

-- 1. Count total queries
SELECT 'Total Queries:' as metric, COUNT(*) as count FROM user_queries;

-- 2. Count total chunks
SELECT 'Total Chunks:' as metric, COUNT(*) as count FROM retrieved_chunks;

-- 3. Recent queries
SELECT
    'Recent Queries' as section,
    id,
    LEFT(query_text, 50) as query,
    timestamp,
    num_results
FROM user_queries
ORDER BY timestamp DESC
LIMIT 5;

-- 4. Most retrieved playbooks
SELECT
    'Top Playbooks' as section,
    playbook_id,
    LEFT(title, 40) as title,
    COUNT(*) as retrieval_count,
    ROUND(AVG(similarity_score)::numeric, 4) as avg_score
FROM retrieved_chunks
WHERE playbook_id IS NOT NULL
GROUP BY playbook_id, title
ORDER BY retrieval_count DESC
LIMIT 5;

-- 5. Sample chunk data (latest query)
SELECT
    'Sample Chunks' as section,
    rc.query_id,
    rc.chunk_rank,
    rc.playbook_id,
    LEFT(rc.title, 30) as title,
    rc.similarity_score,
    rc.rerank_score
FROM retrieved_chunks rc
WHERE query_id = (SELECT MAX(id) FROM user_queries)
ORDER BY chunk_rank
LIMIT 5;
