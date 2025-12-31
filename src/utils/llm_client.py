"""
LLM client wrapper supporting both Ollama and OpenAI
"""
import logging
from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain.schema import HumanMessage, SystemMessage

from ..config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client for Ollama and OpenAI"""

    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature

        if self.provider == 'openai':
            self.client = ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                api_key=settings.openai_api_key
            )
        elif self.provider == 'ollama':
            self.client = Ollama(
                model=self.model,
                temperature=self.temperature
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000
    ) -> str:
        """Generate text from prompt"""
        try:
            if self.provider == 'openai':
                messages = []
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))
                messages.append(HumanMessage(content=prompt))

                response = self.client.invoke(messages)
                return response.content

            else:  # ollama
                if system_prompt:
                    full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
                else:
                    full_prompt = prompt

                response = self.client.invoke(full_prompt)
                return response

        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            raise

    def generate_action_recommendations(
        self,
        context: str,
        risk_factors: List[str],
        playbooks: List[dict]
    ) -> str:
        """Generate action recommendations based on context and playbooks"""
        system_prompt = """You are an expert business advisor. Based on the provided context,
risk factors, and successful playbooks from similar situations, generate 2 specific,
actionable recommendations with clear reasoning."""

        playbook_context = "\n\n".join([
            f"Playbook {i+1}: {p.get('title', 'N/A')}\n"
            f"Success Rate: {p.get('success_rate', 0):.1%}\n"
            f"Key Actions: {p.get('content', 'N/A')[:200]}"
            for i, p in enumerate(playbooks[:3])
        ])

        prompt = f"""Context:
{context}

Risk Factors:
{', '.join(risk_factors)}

Relevant Playbooks:
{playbook_context}

Generate 2 priority-ranked action recommendations. For each recommendation, provide:
1. The specific action to take
2. Clear reasoning based on the playbooks
3. Expected impact

Format as JSON:
[
  {{
    "priority": 1,
    "action": "specific action",
    "reasoning": "why this works",
    "playbook_id": "PB-XXX"
  }},
  ...
]"""

        return self.generate(prompt, system_prompt, max_tokens=1000)

    def generate_email_draft(
        self,
        context: str,
        action: str,
        recipient_name: str = "[Name]"
    ) -> dict:
        """Generate email draft for a given action"""
        system_prompt = """You are a professional business communication expert.
Write concise, professional emails that are action-oriented and respectful."""

        prompt = f"""Context: {context}

Action to take: {action}

Generate a professional email draft with:
- Subject line
- Email body (3-4 paragraphs max)
- Professional tone
- Clear call-to-action

Recipient: {recipient_name}

Format as JSON:
{{
  "subject": "email subject",
  "body": "email body"
}}"""

        return self.generate(prompt, system_prompt, max_tokens=800)

    def generate_playbook(
        self,
        pattern: dict,
        success_metrics: dict
    ) -> str:
        """Generate a playbook from identified patterns"""
        system_prompt = """You are a business strategy expert. Create actionable
playbooks based on successful patterns from historical data."""

        prompt = f"""Based on the following successful pattern, create a detailed playbook:

Pattern Context:
{pattern.get('context', 'N/A')}

Success Metrics:
- Win Rate: {success_metrics.get('win_rate', 0):.1%}
- Cases Analyzed: {success_metrics.get('num_cases', 0)}
- Average Time to Success: {success_metrics.get('avg_time', 'N/A')} days

Key Factors:
{pattern.get('key_factors', 'N/A')}

Generate a playbook with:
1. Title (concise, descriptive)
2. When to use this playbook
3. 3-5 recommended actions
4. Success factors
5. Common pitfalls to avoid

Format as structured text."""

        return self.generate(prompt, system_prompt, max_tokens=1500)

    def classify_project_risk(
        self,
        project_info: dict,
        historical_patterns: str
    ) -> str:
        """Classify if project risk is true risk or housekeeping noise"""
        system_prompt = """You are a project management expert. Classify whether
project issues represent true risks requiring intervention or just housekeeping updates."""

        prompt = f"""Project Information:
Name: {project_info.get('project_name', 'N/A')}
Status: {project_info.get('status', 'N/A')}
Progress: {project_info.get('progress_pct', 0)}%
Days to Deadline: {project_info.get('days_to_deadline', 'N/A')}
Overdue Tasks: {project_info.get('overdue_tasks', 0)}
Last Update: {project_info.get('update_staleness', 'N/A')} days ago

Historical Patterns:
{historical_patterns}

Classify as:
- "TRUE RISK" - Requires immediate intervention
- "HOUSEKEEPING" - Normal project churn, no intervention needed

Provide classification and brief reasoning.

Format as JSON:
{{
  "classification": "TRUE RISK" or "HOUSEKEEPING",
  "reasoning": "explanation",
  "confidence": 0.0 to 1.0
}}"""

        return self.generate(prompt, system_prompt, max_tokens=500)


# Global LLM client instance
llm_client = LLMClient()
