"""
Sales/Opportunity Agent - Identifies at-risk deals and recommends actions
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


class SalesAgent:
    """Agent for analyzing sales opportunities and recommending actions"""

    def __init__(self):
        self.agent_name = "sales_agent"
        self.risk_classifier = RiskClassifier(model_type="sales")
        self.threshold = settings.sales_risk_threshold

        # Try to load existing model
        try:
            self.risk_classifier.load()
        except Exception as e:
            logger.warning(f"Could not load sales risk model: {e}")

    def analyze_opportunity(
        self,
        opportunity_id: str,
        use_cache: bool = True
    ) -> Dict:
        """
        Analyze opportunity and provide recommendations

        Args:
            opportunity_id: Opportunity identifier
            use_cache: Whether to use cached results

        Returns:
            Analysis result with risk score and recommendations
        """
        logger.info(f"Analyzing opportunity: {opportunity_id}")

        # Check cache
        if use_cache:
            cached = redis_cache.get_agent_state(self.agent_name, opportunity_id)
            if cached:
                logger.info("Retrieved from cache")
                return cached

        # 1. Fetch opportunity data
        opportunity = db_manager.get_opportunity(opportunity_id)
        if not opportunity:
            return {
                "error": f"Opportunity {opportunity_id} not found",
                "opportunity_id": opportunity_id
            }

        # 2. Calculate risk score
        try:
            risk_score = self.risk_classifier.predict_risk_score(opportunity)
        except Exception as e:
            logger.error(f"Risk scoring failed: {e}")
            risk_score = 0.5  # Default medium risk

        # 3. Classify risk status
        status = "AT RISK" if risk_score >= self.threshold else "HEALTHY"

        # 4. Identify risk factors
        risk_factors = self._identify_risk_factors(opportunity)

        # 5. RAG retrieval - find relevant playbooks
        if status == "AT RISK":
            playbooks = self._retrieve_playbooks(opportunity, risk_factors)
        else:
            playbooks = []

        # 6. Generate action recommendations
        if playbooks:
            recommended_actions = self._generate_recommendations(
                opportunity, risk_factors, playbooks
            )
        else:
            recommended_actions = []

        # 7. Generate email draft for top action
        draft_email = None
        if recommended_actions:
            draft_email = self._generate_email_draft(
                opportunity, recommended_actions[0]
            )

        # Compile result
        result = {
            "opportunity_id": opportunity_id,
            "company": opportunity['company'],
            "stage": opportunity['stage'],
            "status": status,
            "risk_score": round(risk_score, 3),
            "risk_factors": risk_factors,
            "recommended_actions": recommended_actions,
            "draft_email": draft_email,
            "timestamp": datetime.now().isoformat()
        }

        # Cache result
        redis_cache.cache_agent_state(self.agent_name, opportunity_id, result, ttl=3600)

        return result

    def _identify_risk_factors(self, opportunity: Dict) -> List[str]:
        """Identify specific risk factors"""
        factors = []

        # Activity gap
        last_activity = datetime.strptime(str(opportunity['last_activity_date']), "%Y-%m-%d")
        activity_gap = (datetime.now() - last_activity).days

        if activity_gap >= 7:
            factors.append(f"No activity in {activity_gap} days")

        # Stage duration
        if opportunity['days_in_stage'] > 30:
            factors.append(f"Stage stalled for {opportunity['days_in_stage']} days")
        elif opportunity['days_in_stage'] > 14:
            factors.append(f"In stage for {opportunity['days_in_stage']} days")

        # Single-threading
        if opportunity['contacts_engaged'] == 1:
            factors.append("Single-threaded engagement")
        elif opportunity['contacts_engaged'] == 2:
            factors.append("Limited stakeholder engagement (2 contacts)")

        # Deal size vs stage
        if opportunity['deal_value'] > 1000000 and opportunity['contacts_engaged'] < 3:
            factors.append("Large deal (>${opportunity['deal_value']:,.0f}) with limited engagement")

        # Time to close
        expected_close = datetime.strptime(str(opportunity['expected_close_date']), "%Y-%m-%d")
        days_to_close = (expected_close - datetime.now()).days

        if days_to_close < 14 and opportunity['stage'] in ['Discovery', 'Qualification']:
            factors.append(f"Early stage with close deadline ({days_to_close} days)")

        return factors

    def _retrieve_playbooks(
        self,
        opportunity: Dict,
        risk_factors: List[str]
    ) -> List[Dict]:
        """Retrieve relevant playbooks using RAG"""
        # Build query from context
        query = f"""Opportunity at risk in {opportunity['stage']} stage.
Risk factors: {', '.join(risk_factors)}.
Company: {opportunity['company']}.
Deal value: ${opportunity['deal_value']:,.0f}."""

        # Hybrid search
        try:
            results = hybrid_retriever.hybrid_search(
                query=query,
                top_k=5,
                filter_dict={"category": "sales"}
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
        opportunity: Dict,
        risk_factors: List[str],
        playbooks: List[Dict]
    ) -> List[Dict]:
        """Generate action recommendations using LLM"""
        context = f"""Opportunity: {opportunity['company']}
Stage: {opportunity['stage']}
Deal Value: ${opportunity['deal_value']:,.0f}
Days in Stage: {opportunity['days_in_stage']}
Contacts Engaged: {opportunity['contacts_engaged']}"""

        try:
            # Generate with LLM
            llm_output = llm_client.generate_action_recommendations(
                context=context,
                risk_factors=risk_factors,
                playbooks=playbooks
            )

            # Parse JSON response
            recommendations = json.loads(llm_output)

            # Ensure correct format
            if isinstance(recommendations, list):
                return recommendations[:2]  # Top 2 actions
            else:
                return []

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            # Fallback recommendations
            return [{
                "priority": 1,
                "action": "Review opportunity and re-engage stakeholders",
                "reasoning": "Standard follow-up protocol for at-risk deals",
                "playbook_id": playbooks[0]['id'] if playbooks else None
            }]

    def _generate_email_draft(
        self,
        opportunity: Dict,
        action: Dict
    ) -> Optional[Dict]:
        """Generate email draft for recommended action"""
        context = f"""Company: {opportunity['company']}
Current Stage: {opportunity['stage']}
Recommended Action: {action['action']}"""

        try:
            draft_output = llm_client.generate_email_draft(
                context=context,
                action=action['action']
            )

            # Parse JSON
            draft = json.loads(draft_output)
            return draft

        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            return {
                "subject": f"Following up - {opportunity['company']}",
                "body": f"Hi [Name],\n\nI wanted to follow up on our conversation about [topic].\n\n{action['action']}\n\nBest regards"
            }

    def log_feedback(
        self,
        opportunity_id: str,
        query: str,
        risk_score: float,
        retrieved_playbooks: List[Dict],
        selected_playbook_id: Optional[str],
        user_action: str,
        outcome: Optional[str] = None
    ) -> bool:
        """Log user feedback for model training"""
        feedback_data = {
            "agent_name": self.agent_name,
            "entity_id": opportunity_id,
            "query": query,
            "risk_score": risk_score,
            "retrieved_playbooks": json.dumps([
                {"id": p['id'], "score": p.get('score', 0)}
                for p in retrieved_playbooks
            ]),
            "selected_playbook_id": selected_playbook_id,
            "user_action": user_action,
            "outcome": outcome,
            "metadata": json.dumps({}),
            "model_version": "v1"
        }

        return db_manager.log_feedback(feedback_data)


# Global sales agent instance
sales_agent = SalesAgent()
