"""
ML risk scoring models for opportunities and projects
"""
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import joblib
import logging
from pathlib import Path
from typing import Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class RiskClassifier:
    """XGBoost-based risk classifier for opportunities and projects"""

    def __init__(self, model_type: str = "sales"):
        """
        Initialize classifier

        Args:
            model_type: 'sales' or 'delivery'
        """
        self.model_type = model_type
        self.model = None
        self.model_dir = Path("models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.model_dir / f"{model_type}_risk_classifier.pkl"

    def extract_sales_features(self, opportunity: Dict) -> Dict:
        """
        Extract features from opportunity data

        Args:
            opportunity: Opportunity dict from database

        Returns:
            Feature dict
        """
        from datetime import datetime

        # Calculate derived features
        last_activity = datetime.strptime(str(opportunity['last_activity_date']), "%Y-%m-%d")
        activity_gap = (datetime.now() - last_activity).days

        expected_close = datetime.strptime(str(opportunity['expected_close_date']), "%Y-%m-%d")
        time_to_close = (expected_close - datetime.now()).days

        features = {
            'activity_gap': activity_gap,
            'stage_duration': opportunity['days_in_stage'],
            'engagement_breadth': opportunity['contacts_engaged'],
            'deal_value': opportunity['deal_value'],
            'time_to_close': time_to_close,
            # Engineered features
            'single_threaded': 1 if opportunity['contacts_engaged'] == 1 else 0,
            'stalled_long': 1 if opportunity['days_in_stage'] > 30 else 0,
            'inactive_week': 1 if activity_gap >= 7 else 0
        }

        return features

    def extract_delivery_features(self, project: Dict) -> Dict:
        """
        Extract features from project data

        Args:
            project: Project dict from database

        Returns:
            Feature dict
        """
        from datetime import datetime

        # Calculate derived features
        end_date = datetime.strptime(str(project['end_date']), "%Y-%m-%d")
        days_to_deadline = (end_date - datetime.now()).days

        last_update = datetime.strptime(str(project['last_update_date']), "%Y-%m-%d")
        update_staleness = (datetime.now() - last_update).days

        # Estimate expected progress based on time
        total_days = 90  # Assume 90-day projects on average
        elapsed_days = total_days - days_to_deadline
        expected_progress = (elapsed_days / total_days) * 100 if total_days > 0 else 0

        progress_vs_expected = project['progress_pct'] - expected_progress

        features = {
            'progress_pct': project['progress_pct'],
            'days_to_deadline': days_to_deadline,
            'overdue_tasks': project['overdue_tasks'],
            'update_staleness': update_staleness,
            'client_response_gap': project['client_response_gap_days'],
            # Engineered features
            'progress_vs_expected': progress_vs_expected,
            'critical_deadline': 1 if days_to_deadline < 7 else 0,
            'many_overdue': 1 if project['overdue_tasks'] > 5 else 0,
            'client_blocking': 1 if project['client_response_gap_days'] > 7 else 0
        }

        return features

    def prepare_training_data(
        self,
        data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data with features and labels

        Args:
            data: Raw data with outcome labels

        Returns:
            X (features), y (labels)
        """
        features_list = []
        labels = []

        for _, row in data.iterrows():
            if self.model_type == "sales":
                features = self.extract_sales_features(row.to_dict())
                # Label: 1 if at risk (lost or stalled)
                label = 1 if row.get('outcome') in ['Closed Lost', 'Stalled'] else 0
            else:  # delivery
                features = self.extract_delivery_features(row.to_dict())
                # Label: 1 if Red status
                label = 1 if row.get('status') == 'Red' else 0

            features_list.append(features)
            labels.append(label)

        X = pd.DataFrame(features_list)
        y = pd.Series(labels)

        return X, y

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None
    ) -> Dict:
        """
        Train XGBoost classifier

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels

        Returns:
            Training metrics
        """
        logger.info(f"Training {self.model_type} risk classifier...")

        # XGBoost parameters
        params = {
            'objective': 'binary:logistic',
            'max_depth': 4,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'min_child_weight': 1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'eval_metric': 'auc'
        }

        self.model = xgb.XGBClassifier(**params)

        # Train
        if X_val is not None and y_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)

        # Evaluate
        train_preds = self.model.predict(X_train)
        train_proba = self.model.predict_proba(X_train)[:, 1]

        metrics = {
            'train_accuracy': accuracy_score(y_train, train_preds),
            'train_precision': precision_score(y_train, train_preds, zero_division=0),
            'train_recall': recall_score(y_train, train_preds, zero_division=0),
            'train_f1': f1_score(y_train, train_preds, zero_division=0)
        }

        if X_val is not None:
            val_preds = self.model.predict(X_val)
            val_proba = self.model.predict_proba(X_val)[:, 1]

            metrics.update({
                'val_accuracy': accuracy_score(y_val, val_preds),
                'val_precision': precision_score(y_val, val_preds, zero_division=0),
                'val_recall': recall_score(y_val, val_preds, zero_division=0),
                'val_f1': f1_score(y_val, val_preds, zero_division=0)
            })

        logger.info(f"Training completed. Validation F1: {metrics.get('val_f1', 0):.3f}")
        return metrics

    def predict_risk_score(self, data: Dict) -> float:
        """
        Predict risk score for a single instance

        Args:
            data: Opportunity or project dict

        Returns:
            Risk probability (0 to 1)
        """
        if not self.model:
            raise ValueError("Model not trained or loaded")

        # Extract features
        if self.model_type == "sales":
            features = self.extract_sales_features(data)
        else:
            features = self.extract_delivery_features(data)

        # Convert to DataFrame
        X = pd.DataFrame([features])

        # Predict probability
        risk_score = self.model.predict_proba(X)[0, 1]
        return float(risk_score)

    def save(self, version: str = "v1") -> str:
        """Save model to disk"""
        if not self.model:
            raise ValueError("No model to save")

        save_path = self.model_dir / f"{self.model_type}_risk_classifier_{version}.pkl"
        joblib.dump(self.model, save_path)
        logger.info(f"Model saved to {save_path}")
        return str(save_path)

    def load(self, version: str = "v1") -> bool:
        """Load model from disk"""
        load_path = self.model_dir / f"{self.model_type}_risk_classifier_{version}.pkl"

        if not load_path.exists():
            logger.error(f"Model file not found: {load_path}")
            return False

        self.model = joblib.load(load_path)
        logger.info(f"Model loaded from {load_path}")
        return True

    def get_feature_importance(self) -> Dict:
        """Get feature importance scores"""
        if not self.model:
            raise ValueError("Model not trained or loaded")

        importance = dict(zip(
            self.model.get_booster().feature_names,
            self.model.feature_importances_
        ))

        # Sort by importance
        sorted_importance = dict(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)
        )

        return sorted_importance
