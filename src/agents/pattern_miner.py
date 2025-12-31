"""
Pattern Miner Agent - Extracts successful patterns from historical data
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import json

from ..utils.database import db_manager
from ..utils.llm_client import llm_client
from ..rag.vector_store import vector_store
from ..rag.chunking import text_chunker

logger = logging.getLogger(__name__)


class PatternMiner:
    """Background agent for discovering patterns and generating playbooks"""

    def __init__(self):
        self.agent_name = "pattern_miner"

    def mine_patterns(self, days_lookback: int = 7) -> List[Dict]:
        """
        Analyze recent outcomes and extract successful patterns

        Args:
            days_lookback: How many days of data to analyze

        Returns:
            List of discovered patterns
        """
        logger.info(f"Mining patterns from last {days_lookback} days...")

        patterns = []

        # 1. Analyze successful sales opportunities
        sales_patterns = self._analyze_sales_patterns(days_lookback)
        patterns.extend(sales_patterns)

        # 2. Analyze project recoveries
        delivery_patterns = self._analyze_delivery_patterns(days_lookback)
        patterns.extend(delivery_patterns)

        logger.info(f"Discovered {len(patterns)} patterns")
        return patterns

    def _analyze_sales_patterns(self, days_lookback: int) -> List[Dict]:
        """Analyze successful sales patterns"""
        query = """
            SELECT *
            FROM opportunities
            WHERE outcome = 'Closed Won'
            AND updated_at >= CURRENT_TIMESTAMP - INTERVAL ':days days'
        """

        try:
            won_opps = db_manager.execute_query(query, {"days": days_lookback})

            if not won_opps:
                return []

            # Group by common factors
            patterns = []

            # Example: Multi-threading pattern
            multi_threaded = [o for o in won_opps if o['contacts_engaged'] >= 3]
            if len(multi_threaded) >= 5:
                pattern = {
                    "category": "sales",
                    "title": "Multi-threading Success Pattern",
                    "context": f"Analyzed {len(multi_threaded)} won deals with 3+ stakeholder engagement",
                    "success_rate": len(multi_threaded) / len(won_opps),
                    "num_cases": len(multi_threaded),
                    "key_factors": [
                        f"Average contacts engaged: {sum(o['contacts_engaged'] for o in multi_threaded) / len(multi_threaded):.1f}",
                        f"Average deal size: ${sum(o['deal_value'] for o in multi_threaded) / len(multi_threaded):,.0f}"
                    ]
                }
                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Sales pattern analysis failed: {str(e)}")
            return []

    def _analyze_delivery_patterns(self, days_lookback: int) -> List[Dict]:
        """Analyze project recovery patterns"""
        # This is simplified - in production, would track status changes over time
        query = """
            SELECT *
            FROM projects
            WHERE status = 'Green'
            AND updated_at >= CURRENT_TIMESTAMP - INTERVAL ':days days'
        """

        try:
            green_projects = db_manager.execute_query(query, {"days": days_lookback})

            if not green_projects:
                return []

            patterns = []

            # Projects that recovered despite overdue tasks
            recovered = [p for p in green_projects if p['overdue_tasks'] > 0]
            if len(recovered) >= 3:
                pattern = {
                    "category": "delivery",
                    "title": "Project Recovery Pattern",
                    "context": f"Analyzed {len(recovered)} projects that recovered to Green status",
                    "success_rate": len(recovered) / len(green_projects),
                    "num_cases": len(recovered),
                    "key_factors": [
                        f"Average overdue tasks addressed: {sum(p['overdue_tasks'] for p in recovered) / len(recovered):.1f}",
                        "Quick triage and prioritization critical"
                    ]
                }
                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Delivery pattern analysis failed: {str(e)}")
            return []

    def generate_playbook_from_pattern(self, pattern: Dict) -> Dict:
        """
        Generate a playbook from discovered pattern using LLM

        Args:
            pattern: Pattern dict

        Returns:
            Playbook dict
        """
        try:
            success_metrics = {
                "win_rate": pattern['success_rate'],
                "num_cases": pattern['num_cases'],
                "avg_time": "N/A"  # Could calculate from data
            }

            playbook_text = llm_client.generate_playbook(pattern, success_metrics)

            # Create playbook ID
            timestamp = datetime.now().strftime("%Y%m%d")
            playbook_id = f"PB-AUTO-{timestamp}-{pattern['category'][:3].upper()}"

            playbook = {
                "playbook_id": playbook_id,
                "title": pattern['title'],
                "content": playbook_text,
                "category": pattern['category'],
                "success_rate": pattern['success_rate'],
                "num_cases": pattern['num_cases']
            }

            return playbook

        except Exception as e:
            logger.error(f"Playbook generation failed: {str(e)}")
            return None

    def index_playbook(self, playbook: Dict) -> bool:
        """
        Add generated playbook to database and vector store

        Args:
            playbook: Playbook dict

        Returns:
            Success status
        """
        try:
            # Save to database
            db_manager.insert_playbook(playbook)

            # Chunk and index in vector store
            chunks = text_chunker.chunk_playbook(playbook)

            chunk_texts = [c['text'] for c in chunks]
            chunk_ids = [f"{playbook['playbook_id']}_chunk_{i}" for i in range(len(chunks))]
            chunk_metadatas = [c['metadata'] for c in chunks]

            vector_store.add_documents(
                documents=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            logger.info(f"Playbook indexed: {playbook['playbook_id']}")
            return True

        except Exception as e:
            logger.error(f"Playbook indexing failed: {str(e)}")
            return False

    def run_nightly_mining(self) -> Dict:
        """
        Complete nightly pattern mining workflow

        Returns:
            Mining summary
        """
        logger.info("Starting nightly pattern mining...")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "patterns_discovered": 0,
            "playbooks_generated": 0,
            "playbooks_indexed": 0
        }

        # 1. Mine patterns
        patterns = self.mine_patterns(days_lookback=7)
        summary['patterns_discovered'] = len(patterns)

        # 2. Generate playbooks
        for pattern in patterns:
            playbook = self.generate_playbook_from_pattern(pattern)

            if playbook:
                summary['playbooks_generated'] += 1

                # 3. Index playbook
                if self.index_playbook(playbook):
                    summary['playbooks_indexed'] += 1

        logger.info(f"Pattern mining complete: {summary}")
        return summary


# Global pattern miner instance
pattern_miner = PatternMiner()
