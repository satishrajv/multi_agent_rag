"""
Delivery Triage Agent - Classifies project risks and recommends recovery actions
"""
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.database import db_manager
from ..utils.redis_cache import redis_cache
from ..utils.llm_client import llm_client
from ..models.risk_classifier import RiskClassifier
from ..rag.retrieval import hybrid_retriever
from ..rag.reranker import reranker
from ..config import settings

logger = logging.getLogger(__name__)


class DeliveryAgent:
    """Agent for triaging delivery projects and recommending recovery actions"""

    def __init__(self):
        self.agent_name = "delivery_agent"
        self.risk_classifier = RiskClassifier(model_type="delivery")
        self.threshold = settings.delivery_risk_threshold

        # Try to load existing model
        try:
            self.risk_classifier.load()
        except Exception as e:
            logger.warning(f"Could not load delivery risk model: {e}")

    def analyze_project(
        self,
        project_id: str,
        use_cache: bool = True
    ) -> Dict:
        """
        Analyze project and provide triage classification

        Args:
            project_id: Project identifier
            use_cache: Whether to use cached results

        Returns:
            Analysis result with classification and recommendations
        """
        logger.info(f"Analyzing project: {project_id}")

        # Check cache
        if use_cache:
            cached = redis_cache.get_agent_state(self.agent_name, project_id)
            if cached:
                logger.info("Retrieved from cache")
                return cached

        # 1. Fetch project data
        project = db_manager.get_project(project_id)
        if not project:
            return {
                "error": f"Project {project_id} not found",
                "project_id": project_id
            }

        # 2. Rule-based + ML classification
        classification, risk_factors = self._classify_project(project)

        # 3. RAG retrieval - find recovery playbooks
        playbooks = []
        if classification == "TRUE RISK":
            playbooks = self._retrieve_playbooks(project, risk_factors)

        # 4. Generate action recommendations
        recommended_actions = []
        if playbooks or classification == "TRUE RISK":
            recommended_actions = self._generate_recommendations(
                project, risk_factors, playbooks
            )

        # Compile result
        result = {
            "project_id": project_id,
            "project_name": project['project_name'],
            "status": project['status'],
            "classification": classification,
            "risk_factors": risk_factors,
            "recommended_actions": recommended_actions,
            "timestamp": datetime.now().isoformat()
        }

        # Cache result
        redis_cache.cache_agent_state(self.agent_name, project_id, result, ttl=3600)

        return result

    def _classify_project(self, project: Dict) -> tuple[str, List[str]]:
        """
        Classify project as TRUE RISK or HOUSEKEEPING

        Returns:
            (classification, risk_factors)
        """
        risk_factors = []

        # Calculate derived metrics
        end_date = datetime.strptime(str(project['end_date']), "%Y-%m-%d")
        days_to_deadline = (end_date - datetime.now()).days

        # Estimate expected progress
        total_days = 90
        elapsed_days = total_days - days_to_deadline
        expected_progress = (elapsed_days / total_days) * 100 if total_days > 0 else 0
        progress_vs_expected = project['progress_pct'] - expected_progress

        # Rule-based classification
        is_true_risk = False

        # Critical deadline with low progress
        if days_to_deadline < 7 and project['progress_pct'] < 70:
            is_true_risk = True
            risk_factors.append(f"Progress {project['progress_pct']:.0f}% vs end date in {days_to_deadline} days")

        # Severely behind schedule
        if progress_vs_expected < -30:
            is_true_risk = True
            risk_factors.append(f"Progress {project['progress_pct']:.0f}% (expected {expected_progress:.0f}%)")

        # Many overdue tasks
        if project['overdue_tasks'] > 10:
            is_true_risk = True
            risk_factors.append(f"{project['overdue_tasks']} overdue tasks")
        elif project['overdue_tasks'] > 5:
            risk_factors.append(f"{project['overdue_tasks']} overdue tasks")

        # Client blockers
        if project['client_response_gap_days'] > 7:
            is_true_risk = True
            risk_factors.append(f"Client response gap: {project['client_response_gap_days']} days")
        elif project['client_response_gap_days'] > 3:
            risk_factors.append(f"Client response gap: {project['client_response_gap_days']} days")

        # Stale updates
        last_update = datetime.strptime(str(project['last_update_date']), "%Y-%m-%d")
        update_staleness = (datetime.now() - last_update).days

        if update_staleness > 5:
            risk_factors.append(f"No update in {update_staleness} days")

        # Check for false positive (Red status but actually OK)
        if project['status'] == "Red" and not is_true_risk:
            # Check if there's recent progress
            if project['progress_pct'] > 80 or update_staleness < 2:
                classification = "HOUSEKEEPING"
                risk_factors.append("Status marked Red but metrics look healthy")
            else:
                classification = "TRUE RISK"
        elif is_true_risk:
            classification = "TRUE RISK"
        else:
            classification = "HOUSEKEEPING"

        return classification, risk_factors

    def _retrieve_playbooks(
        self,
        project: Dict,
        risk_factors: List[str]
    ) -> List[Dict]:
        """Retrieve relevant recovery playbooks using RAG"""
        # Build query
        query = f"""Project in {project['status']} status requiring recovery.
Risk factors: {', '.join(risk_factors)}.
Progress: {project['progress_pct']:.0f}%.
Overdue tasks: {project['overdue_tasks']}."""

        # Hybrid search
        try:
            results = hybrid_retriever.hybrid_search(
                query=query,
                top_k=5,
                filter_dict={"category": "delivery"}
            )

            # Rerank
            if results:
                reranked = reranker.rerank(query, results, top_k=3)
                return reranked
            else:
                return []

        except Exception as e:
            logger.error(f"Playbook retrieval failed: {e}")
            return []

    def _generate_recommendations(
        self,
        project: Dict,
        risk_factors: List[str],
        playbooks: List[Dict]
    ) -> List[Dict]:
        """Generate recovery action recommendations"""
        # Build context
        context = f"""Project: {project['project_name']}
Status: {project['status']}
Progress: {project['progress_pct']:.0f}%
Overdue Tasks: {project['overdue_tasks']}
Client Response Gap: {project['client_response_gap_days']} days"""

        try:
            # Use LLM to generate recommendations
            llm_output = llm_client.generate_action_recommendations(
                context=context,
                risk_factors=risk_factors,
                playbooks=playbooks
            )

            recommendations = json.loads(llm_output)

            if isinstance(recommendations, list):
                return recommendations[:3]  # Top 3 actions
            else:
                return []

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            # Fallback recommendations
            fallback = []

            if project['overdue_tasks'] > 5:
                fallback.append({
                    "priority": 1,
                    "action": "Triage overdue tasks with delivery manager",
                    "reasoning": "High number of overdue tasks requires immediate prioritization"
                })

            if project['client_response_gap_days'] > 7:
                fallback.append({
                    "priority": 2,
                    "action": "Escalate client blockers to account team",
                    "reasoning": "Extended client response gap needs sales team intervention"
                })

            return fallback

    def log_feedback(
        self,
        project_id: str,
        query: str,
        classification: str,
        retrieved_playbooks: List[Dict],
        selected_playbook_id: Optional[str],
        user_action: str,
        outcome: Optional[str] = None
    ) -> bool:
        """Log user feedback for model training"""
        feedback_data = {
            "agent_name": self.agent_name,
            "entity_id": project_id,
            "query": query,
            "risk_score": 1.0 if classification == "TRUE RISK" else 0.0,
            "retrieved_playbooks": json.dumps([
                {"id": p['id'], "score": p.get('score', 0)}
                for p in retrieved_playbooks
            ]),
            "selected_playbook_id": selected_playbook_id,
            "user_action": user_action,
            "outcome": outcome,
            "metadata": json.dumps({"classification": classification}),
            "model_version": "v1"
        }

        return db_manager.log_feedback(feedback_data)


# Global delivery agent instance
delivery_agent = DeliveryAgent()
