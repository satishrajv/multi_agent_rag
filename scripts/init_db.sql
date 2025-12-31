-- Database initialization script for Multi-Agent RAG system

-- Create opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    opportunity_id VARCHAR(100) PRIMARY KEY,
    company VARCHAR(255) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    days_in_stage INTEGER NOT NULL,
    last_activity_date DATE NOT NULL,
    contacts_engaged INTEGER NOT NULL,
    deal_value DECIMAL(12, 2) NOT NULL,
    expected_close_date DATE NOT NULL,
    outcome VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(100) PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    progress_pct DECIMAL(5, 2) NOT NULL,
    end_date DATE NOT NULL,
    overdue_tasks INTEGER DEFAULT 0,
    last_update_date DATE NOT NULL,
    client_response_gap_days INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create feedback log table
CREATE TABLE IF NOT EXISTS feedback_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_name VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    risk_score FLOAT,
    retrieved_playbooks JSONB,
    selected_playbook_id VARCHAR(50),
    user_action VARCHAR(20) NOT NULL,
    outcome VARCHAR(50),
    metadata JSONB,
    model_version VARCHAR(50)
);

-- Create playbooks table
CREATE TABLE IF NOT EXISTS playbooks (
    playbook_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    success_rate DECIMAL(5, 4),
    num_cases INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create model versions table for A/B testing
CREATE TABLE IF NOT EXISTS model_versions (
    version_id SERIAL PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL,
    version_name VARCHAR(50) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    metrics JSONB,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_opportunities_stage ON opportunities(stage);
CREATE INDEX IF NOT EXISTS idx_opportunities_outcome ON opportunities(outcome);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_feedback_agent ON feedback_log(agent_name);
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_feedback_entity ON feedback_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_playbooks_category ON playbooks(category);
