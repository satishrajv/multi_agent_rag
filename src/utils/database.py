"""
Database utilities for PostgreSQL operations
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
import pandas as pd
import logging
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""

    def __init__(self):
        self.engine = create_engine(
            settings.postgres_url,
            poolclass=NullPool,
            echo=False
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a SELECT query and return results as list of dicts"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def execute_update(self, query: str, params: Optional[Dict] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result.rowcount

    # Opportunity operations
    def get_opportunity(self, opportunity_id: str) -> Optional[Dict]:
        """Fetch opportunity by ID"""
        query = "SELECT * FROM opportunities WHERE opportunity_id = :opportunity_id"
        results = self.execute_query(query, {"opportunity_id": opportunity_id})
        return results[0] if results else None

    def insert_opportunity(self, data: Dict) -> bool:
        """Insert new opportunity"""
        query = """
            INSERT INTO opportunities (
                opportunity_id, company, stage, days_in_stage,
                last_activity_date, contacts_engaged, deal_value,
                expected_close_date, outcome
            ) VALUES (
                :opportunity_id, :company, :stage, :days_in_stage,
                :last_activity_date, :contacts_engaged, :deal_value,
                :expected_close_date, :outcome
            )
        """
        try:
            self.execute_update(query, data)
            return True
        except Exception as e:
            logger.error(f"Failed to insert opportunity: {str(e)}")
            return False

    def update_opportunity_outcome(self, opportunity_id: str, outcome: str) -> bool:
        """Update opportunity outcome"""
        query = """
            UPDATE opportunities
            SET outcome = :outcome, updated_at = :updated_at
            WHERE opportunity_id = :opportunity_id
        """
        try:
            self.execute_update(query, {
                "opportunity_id": opportunity_id,
                "outcome": outcome,
                "updated_at": datetime.now()
            })
            return True
        except Exception as e:
            logger.error(f"Failed to update opportunity: {str(e)}")
            return False

    # Project operations
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Fetch project by ID"""
        query = "SELECT * FROM projects WHERE project_id = :project_id"
        results = self.execute_query(query, {"project_id": project_id})
        return results[0] if results else None

    def insert_project(self, data: Dict) -> bool:
        """Insert new project"""
        query = """
            INSERT INTO projects (
                project_id, project_name, status, progress_pct,
                end_date, overdue_tasks, last_update_date,
                client_response_gap_days
            ) VALUES (
                :project_id, :project_name, :status, :progress_pct,
                :end_date, :overdue_tasks, :last_update_date,
                :client_response_gap_days
            )
        """
        try:
            self.execute_update(query, data)
            return True
        except Exception as e:
            logger.error(f"Failed to insert project: {str(e)}")
            return False

    # Feedback operations
    def log_feedback(self, feedback_data: Dict) -> bool:
        """Log user feedback"""
        query = """
            INSERT INTO feedback_log (
                agent_name, entity_id, query, risk_score,
                retrieved_playbooks, selected_playbook_id,
                user_action, outcome, metadata, model_version
            ) VALUES (
                :agent_name, :entity_id, :query, :risk_score,
                :retrieved_playbooks::jsonb, :selected_playbook_id,
                :user_action, :outcome, :metadata::jsonb, :model_version
            )
        """
        try:
            self.execute_update(query, feedback_data)
            return True
        except Exception as e:
            logger.error(f"Failed to log feedback: {str(e)}")
            return False

    def get_feedback_for_training(self, days: int = 7, agent_name: Optional[str] = None) -> pd.DataFrame:
        """Get recent feedback for model training"""
        query = """
            SELECT *
            FROM feedback_log
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL ':days days'
        """
        if agent_name:
            query += " AND agent_name = :agent_name"

        params = {"days": days}
        if agent_name:
            params["agent_name"] = agent_name

        results = self.execute_query(query, params)
        return pd.DataFrame(results)

    # Playbook operations
    def get_playbook(self, playbook_id: str) -> Optional[Dict]:
        """Fetch playbook by ID"""
        query = "SELECT * FROM playbooks WHERE playbook_id = :playbook_id"
        results = self.execute_query(query, {"playbook_id": playbook_id})
        return results[0] if results else None

    def insert_playbook(self, data: Dict) -> bool:
        """Insert new playbook"""
        query = """
            INSERT INTO playbooks (
                playbook_id, title, content, category,
                success_rate, num_cases
            ) VALUES (
                :playbook_id, :title, :content, :category,
                :success_rate, :num_cases
            )
        """
        try:
            self.execute_update(query, data)
            return True
        except Exception as e:
            logger.error(f"Failed to insert playbook: {str(e)}")
            return False

    def get_all_playbooks(self) -> List[Dict]:
        """Get all playbooks"""
        query = "SELECT * FROM playbooks ORDER BY success_rate DESC"
        return self.execute_query(query)

    # Model version operations
    def register_model_version(self, model_data: Dict) -> bool:
        """Register a new model version"""
        query = """
            INSERT INTO model_versions (
                model_type, version_name, file_path, metrics, is_active
            ) VALUES (
                :model_type, :version_name, :file_path,
                :metrics::jsonb, :is_active
            )
        """
        try:
            self.execute_update(query, model_data)
            return True
        except Exception as e:
            logger.error(f"Failed to register model: {str(e)}")
            return False

    def get_active_model_version(self, model_type: str) -> Optional[Dict]:
        """Get active model version for a given type"""
        query = """
            SELECT * FROM model_versions
            WHERE model_type = :model_type AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """
        results = self.execute_query(query, {"model_type": model_type})
        return results[0] if results else None


# Global database manager instance
db_manager = DatabaseManager()
