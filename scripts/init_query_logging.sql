-- Query Logging Tables
-- Store user queries and retrieved chunks for analysis

-- Table to store user queries
CREATE TABLE IF NOT EXISTS user_queries (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    top_k INTEGER,
    use_reranking BOOLEAN DEFAULT FALSE,
    num_results INTEGER,
    user_session VARCHAR(255),
    query_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store retrieved chunks for each query
CREATE TABLE IF NOT EXISTS retrieved_chunks (
    id SERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL REFERENCES user_queries(id) ON DELETE CASCADE,
    chunk_rank INTEGER NOT NULL,
    chunk_text TEXT,
    playbook_id VARCHAR(50),
    category VARCHAR(50),
    title VARCHAR(255),
    similarity_score FLOAT,
    rerank_score FLOAT,
    chunk_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON user_queries(timestamp);
CREATE INDEX IF NOT EXISTS idx_queries_text ON user_queries(query_text);
CREATE INDEX IF NOT EXISTS idx_chunks_query_id ON retrieved_chunks(query_id);
CREATE INDEX IF NOT EXISTS idx_chunks_playbook ON retrieved_chunks(playbook_id);
CREATE INDEX IF NOT EXISTS idx_chunks_category ON retrieved_chunks(category);
CREATE INDEX IF NOT EXISTS idx_chunks_score ON retrieved_chunks(similarity_score);

-- View for query analytics
CREATE OR REPLACE VIEW query_analytics AS
SELECT
    uq.id,
    uq.query_text,
    uq.timestamp,
    uq.num_results,
    uq.use_reranking,
    COUNT(rc.id) as chunks_retrieved,
    AVG(rc.similarity_score) as avg_similarity,
    AVG(rc.rerank_score) as avg_rerank_score,
    STRING_AGG(DISTINCT rc.playbook_id, ', ') as playbooks_used
FROM user_queries uq
LEFT JOIN retrieved_chunks rc ON uq.id = rc.query_id
GROUP BY uq.id, uq.query_text, uq.timestamp, uq.num_results, uq.use_reranking
ORDER BY uq.timestamp DESC;

-- View for most popular playbooks
CREATE OR REPLACE VIEW popular_playbooks AS
SELECT
    playbook_id,
    title,
    category,
    COUNT(*) as retrieval_count,
    AVG(similarity_score) as avg_score,
    AVG(chunk_rank) as avg_rank,
    MAX(created_at) as last_retrieved
FROM retrieved_chunks
WHERE playbook_id IS NOT NULL AND playbook_id != ''
GROUP BY playbook_id, title, category
ORDER BY retrieval_count DESC;

-- View for query patterns
CREATE OR REPLACE VIEW query_patterns AS
SELECT
    query_text,
    COUNT(*) as frequency,
    AVG(num_results) as avg_results,
    MAX(timestamp) as last_queried,
    SUM(CASE WHEN use_reranking THEN 1 ELSE 0 END) as times_with_reranking
FROM user_queries
GROUP BY query_text
ORDER BY frequency DESC;
