"""
Auto-threshold tuning based on user feedback
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class ThresholdTuner:
    """Automatically tunes classification thresholds based on feedback"""

    def __init__(self, initial_threshold: float = 0.85):
        self.threshold = initial_threshold
        self.history = []

    def analyze_feedback(
        self,
        feedback_data: pd.DataFrame,
        current_threshold: float
    ) -> Dict:
        """
        Analyze feedback to compute false positive and false negative rates

        Args:
            feedback_data: DataFrame with columns: risk_score, user_action
            current_threshold: Current classification threshold

        Returns:
            Analysis dict with metrics
        """
        if len(feedback_data) == 0:
            return {
                'false_positives': 0,
                'false_negatives': 0,
                'total_samples': 0,
                'recommendation': 'insufficient_data'
            }

        # Classify based on current threshold
        feedback_data['predicted_risk'] = feedback_data['risk_score'] >= current_threshold

        # User action indicates ground truth
        # 'accepted' or 'escalated' = true risk
        # 'rejected' or 'dismissed' = not a risk
        feedback_data['actual_risk'] = feedback_data['user_action'].isin(['accepted', 'escalated'])

        # Calculate confusion matrix
        true_positives = (
            (feedback_data['predicted_risk'] == True) &
            (feedback_data['actual_risk'] == True)
        ).sum()

        false_positives = (
            (feedback_data['predicted_risk'] == True) &
            (feedback_data['actual_risk'] == False)
        ).sum()

        true_negatives = (
            (feedback_data['predicted_risk'] == False) &
            (feedback_data['actual_risk'] == False)
        ).sum()

        false_negatives = (
            (feedback_data['predicted_risk'] == False) &
            (feedback_data['actual_risk'] == True)
        ).sum()

        total = len(feedback_data)

        # Calculate rates
        fp_rate = false_positives / total if total > 0 else 0
        fn_rate = false_negatives / total if total > 0 else 0

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        analysis = {
            'true_positives': int(true_positives),
            'false_positives': int(false_positives),
            'true_negatives': int(true_negatives),
            'false_negatives': int(false_negatives),
            'total_samples': int(total),
            'fp_rate': float(fp_rate),
            'fn_rate': float(fn_rate),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'current_threshold': float(current_threshold)
        }

        return analysis

    def recommend_threshold(
        self,
        analysis: Dict,
        step_size: float = 0.05,
        max_threshold: float = 0.95,
        min_threshold: float = 0.60
    ) -> Tuple[float, str]:
        """
        Recommend new threshold based on analysis

        Args:
            analysis: Analysis dict from analyze_feedback
            step_size: How much to adjust threshold
            max_threshold: Maximum allowed threshold
            min_threshold: Minimum allowed threshold

        Returns:
            (new_threshold, reasoning)
        """
        current = analysis['current_threshold']
        fp_rate = analysis['fp_rate']
        fn_rate = analysis['fn_rate']
        total = analysis['total_samples']

        # Need sufficient data
        if total < 10:
            return current, "Insufficient feedback data (need at least 10 samples)"

        # If FP and FN are balanced and low, keep threshold
        if abs(fp_rate - fn_rate) < 0.05 and (fp_rate + fn_rate) < 0.2:
            return current, "Threshold is well-calibrated (balanced error rates)"

        # If too many false positives, increase threshold (be more conservative)
        if fp_rate > fn_rate and fp_rate > 0.15:
            new_threshold = min(current + step_size, max_threshold)
            reasoning = f"Reducing false positives ({fp_rate:.1%} → target <15%)"
            return new_threshold, reasoning

        # If too many false negatives, decrease threshold (be more aggressive)
        if fn_rate > fp_rate and fn_rate > 0.15:
            new_threshold = max(current - step_size, min_threshold)
            reasoning = f"Reducing false negatives ({fn_rate:.1%} → target <15%)"
            return new_threshold, reasoning

        # Otherwise, make small adjustment toward balance
        if fp_rate > fn_rate:
            new_threshold = min(current + step_size / 2, max_threshold)
            reasoning = "Fine-tuning: slight reduction in false positives"
        else:
            new_threshold = max(current - step_size / 2, min_threshold)
            reasoning = "Fine-tuning: slight reduction in false negatives"

        return new_threshold, reasoning

    def tune_threshold(
        self,
        feedback_data: pd.DataFrame,
        current_threshold: float
    ) -> Dict:
        """
        Complete threshold tuning workflow

        Args:
            feedback_data: Feedback DataFrame
            current_threshold: Current threshold

        Returns:
            Tuning result dict
        """
        # Analyze feedback
        analysis = self.analyze_feedback(feedback_data, current_threshold)

        # Recommend new threshold
        new_threshold, reasoning = self.recommend_threshold(analysis)

        # Record in history
        self.history.append({
            'old_threshold': current_threshold,
            'new_threshold': new_threshold,
            'reasoning': reasoning,
            'analysis': analysis
        })

        result = {
            'old_threshold': float(current_threshold),
            'new_threshold': float(new_threshold),
            'changed': new_threshold != current_threshold,
            'reasoning': reasoning,
            'metrics': analysis
        }

        if result['changed']:
            logger.info(
                f"Threshold adjusted: {current_threshold:.3f} → {new_threshold:.3f} "
                f"({reasoning})"
            )
        else:
            logger.info(f"Threshold unchanged: {current_threshold:.3f} ({reasoning})")

        return result

    def evaluate_threshold_range(
        self,
        feedback_data: pd.DataFrame,
        threshold_range: np.ndarray = None
    ) -> pd.DataFrame:
        """
        Evaluate multiple thresholds to find optimal

        Args:
            feedback_data: Feedback DataFrame
            threshold_range: Array of thresholds to test

        Returns:
            DataFrame with metrics for each threshold
        """
        if threshold_range is None:
            threshold_range = np.arange(0.5, 1.0, 0.05)

        results = []

        for threshold in threshold_range:
            analysis = self.analyze_feedback(feedback_data, threshold)
            analysis['threshold'] = threshold
            results.append(analysis)

        df_results = pd.DataFrame(results)
        return df_results

    def find_optimal_threshold(
        self,
        feedback_data: pd.DataFrame,
        metric: str = 'f1_score'
    ) -> Tuple[float, Dict]:
        """
        Find optimal threshold by maximizing a metric

        Args:
            feedback_data: Feedback DataFrame
            metric: Metric to optimize ('f1_score', 'precision', 'recall')

        Returns:
            (optimal_threshold, analysis)
        """
        df_results = self.evaluate_threshold_range(feedback_data)

        if len(df_results) == 0:
            return 0.85, {}

        # Find threshold with best metric
        best_idx = df_results[metric].idxmax()
        best_row = df_results.iloc[best_idx]

        optimal_threshold = float(best_row['threshold'])
        analysis = best_row.to_dict()

        logger.info(
            f"Optimal threshold: {optimal_threshold:.3f} "
            f"({metric}={best_row[metric]:.3f})"
        )

        return optimal_threshold, analysis


# Global threshold tuner instances
sales_threshold_tuner = ThresholdTuner(initial_threshold=0.85)
delivery_threshold_tuner = ThresholdTuner(initial_threshold=0.80)
