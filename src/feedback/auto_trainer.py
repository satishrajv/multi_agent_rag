"""
Auto-training pipeline for weekly model retraining and threshold tuning
"""
import logging
from datetime import datetime, timedelta
from typing import Dict
import json
import random

from ..utils.database import db_manager
from ..models.threshold_tuner import sales_threshold_tuner, delivery_threshold_tuner
from ..rag.reranker import reranker
from ..config import settings

logger = logging.getLogger(__name__)


class AutoTrainer:
    """Handles automated weekly retraining of models"""

    def __init__(self):
        self.ab_test_pct = settings.ab_test_percentage

    def run_weekly_training(self, days_lookback: int = 7) -> Dict:
        """
        Execute weekly auto-training pipeline

        Args:
            days_lookback: How many days of feedback to use

        Returns:
            Training summary
        """
        logger.info("=" * 60)
        logger.info("STARTING WEEKLY AUTO-TRAINING PIPELINE")
        logger.info("=" * 60)

        summary = {
            "timestamp": datetime.now().isoformat(),
            "days_lookback": days_lookback,
            "results": {}
        }

        # 1. Collect feedback data
        logger.info(f"\nStep 1: Collecting feedback from last {days_lookback} days...")
        feedback_data = db_manager.get_feedback_for_training(days=days_lookback)

        if len(feedback_data) == 0:
            logger.warning("No feedback data available for training")
            summary['results']['status'] = 'no_data'
            return summary

        logger.info(f"Collected {len(feedback_data)} feedback records")

        # 2. Retrain reranker
        logger.info("\nStep 2: Retraining reranker...")
        reranker_result = self._retrain_reranker(feedback_data)
        summary['results']['reranker'] = reranker_result

        # 3. Tune sales agent threshold
        logger.info("\nStep 3: Tuning sales agent threshold...")
        sales_feedback = feedback_data[feedback_data['agent_name'] == 'sales_agent']
        if len(sales_feedback) > 0:
            sales_result = self._tune_threshold(sales_feedback, 'sales')
            summary['results']['sales_threshold'] = sales_result
        else:
            logger.info("No sales feedback available")
            summary['results']['sales_threshold'] = {'status': 'no_data'}

        # 4. Tune delivery agent threshold
        logger.info("\nStep 4: Tuning delivery agent threshold...")
        delivery_feedback = feedback_data[feedback_data['agent_name'] == 'delivery_agent']
        if len(delivery_feedback) > 0:
            delivery_result = self._tune_threshold(delivery_feedback, 'delivery')
            summary['results']['delivery_threshold'] = delivery_result
        else:
            logger.info("No delivery feedback available")
            summary['results']['delivery_threshold'] = {'status': 'no_data'}

        # 5. A/B test setup
        logger.info("\nStep 5: Setting up A/B testing...")
        ab_result = self._setup_ab_testing()
        summary['results']['ab_testing'] = ab_result

        logger.info("\n" + "=" * 60)
        logger.info("AUTO-TRAINING PIPELINE COMPLETED")
        logger.info("=" * 60)

        return summary

    def _retrain_reranker(self, feedback_data) -> Dict:
        """
        Retrain cross-encoder reranker on user feedback

        Args:
            feedback_data: Feedback DataFrame

        Returns:
            Training result
        """
        try:
            # Prepare training samples
            train_samples = []

            for _, row in feedback_data.iterrows():
                query = row['query']
                retrieved_playbooks = json.loads(row['retrieved_playbooks']) if row['retrieved_playbooks'] else []
                selected_id = row['selected_playbook_id']

                # Get the actual playbook documents
                for pb_info in retrieved_playbooks:
                    pb_id = pb_info['id']

                    # Fetch playbook content
                    playbook = db_manager.get_playbook(pb_id)
                    if not playbook:
                        continue

                    document = playbook['content'][:500]  # Truncate for training

                    # Label: 1 if user selected this playbook, 0 otherwise
                    label = 1 if pb_id == selected_id else 0

                    train_samples.append({
                        'query': query,
                        'document': document,
                        'label': label
                    })

            logger.info(f"Prepared {len(train_samples)} training samples for reranker")

            if len(train_samples) < 10:
                logger.warning("Insufficient samples for reranker training (need at least 10)")
                return {
                    'status': 'insufficient_data',
                    'samples': len(train_samples)
                }

            # Train reranker
            training_metrics = reranker.train(
                train_samples=train_samples,
                epochs=3,
                batch_size=16
            )

            # Save new model version
            version_name = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_path = reranker.save_model(version_name)

            # Register in database
            db_manager.register_model_version({
                'model_type': 'reranker',
                'version_name': version_name,
                'file_path': model_path,
                'metrics': json.dumps(training_metrics),
                'is_active': False  # Will be activated after A/B testing
            })

            logger.info(f"Reranker retrained successfully: {version_name}")

            return {
                'status': 'success',
                'version': version_name,
                'samples': len(train_samples),
                'metrics': training_metrics
            }

        except Exception as e:
            logger.error(f"Reranker retraining failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _tune_threshold(self, feedback_data, agent_type: str) -> Dict:
        """
        Tune classification threshold based on feedback

        Args:
            feedback_data: Feedback DataFrame for specific agent
            agent_type: 'sales' or 'delivery'

        Returns:
            Tuning result
        """
        try:
            # Select appropriate tuner
            if agent_type == 'sales':
                tuner = sales_threshold_tuner
                current_threshold = settings.sales_risk_threshold
            else:
                tuner = delivery_threshold_tuner
                current_threshold = settings.delivery_risk_threshold

            # Run threshold tuning
            result = tuner.tune_threshold(feedback_data, current_threshold)

            # Update config (in production, would update database/config file)
            if result['changed']:
                logger.info(
                    f"Threshold updated for {agent_type}: "
                    f"{result['old_threshold']:.3f} → {result['new_threshold']:.3f}"
                )

                # Update settings (note: this only persists in memory)
                if agent_type == 'sales':
                    settings.sales_risk_threshold = result['new_threshold']
                else:
                    settings.delivery_risk_threshold = result['new_threshold']

            return result

        except Exception as e:
            logger.error(f"Threshold tuning failed for {agent_type}: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _setup_ab_testing(self) -> Dict:
        """
        Setup A/B testing configuration for new models

        Returns:
            A/B test config
        """
        try:
            # Get latest model versions
            reranker_model = db_manager.get_active_model_version('reranker')

            ab_config = {
                'enabled': True,
                'traffic_split': {
                    'control': 1.0 - self.ab_test_pct,
                    'treatment': self.ab_test_pct
                },
                'models': {
                    'reranker_treatment': reranker_model['version_name'] if reranker_model else None
                }
            }

            logger.info(f"A/B testing configured: {self.ab_test_pct:.1%} traffic to new models")

            return ab_config

        except Exception as e:
            logger.error(f"A/B testing setup failed: {str(e)}")
            return {
                'enabled': False,
                'error': str(e)
            }

    def should_use_treatment_model(self) -> bool:
        """Determine if this request should use treatment (new) model"""
        return random.random() < self.ab_test_pct


# Global auto trainer instance
auto_trainer = AutoTrainer()
