"""Ensemble Model — XGBoost + LightGBM stacking for crisis prediction.

Three binary classifiers:
  - BankingInstabilityClassifier
  - MarketCrashClassifier
  - LiquidityShortageClassifier

Each uses XGBoost + LightGBM base learners with a LogisticRegression
meta-learner. Outputs probability 0.0–1.0, scaled to 0–100 score.

Models are saved/loaded via joblib and metrics logged to MLflow.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "ml" / "saved_models"
TRAINING_DATA_PATH = Path(__file__).parent.parent / "ml" / "training_data" / "crisis_labels.csv"

# Feature columns (must match FeatureVector.feature_names())
FEATURE_COLS = [
    "sofr_z5d", "sofr_z20d", "dff_z5d", "dff_z20d",
    "dgs2_z5d", "dgs2_z20d", "dgs10_z5d", "dgs10_z20d",
    "hy_spread_z5d", "hy_spread_z20d",
    "t10y2y_z5d", "t10y2y_z20d",
    "vix_z5d", "vix_z20d",
    "spx_pct5d", "spx_pct20d", "spx_vol20d",
    "dxy_z5d", "dxy_z20d",
    "gold_pct5d", "gold_pct20d",
    "oil_pct5d", "oil_pct20d",
    "eurusd_z5d", "eurusd_z20d",
    "gbpusd_z5d", "gbpusd_z20d",
    "interbank_stress", "cross_signal_corr_flag",
    "pmi_us", "pmi_eu", "pmi_cn",
    "initial_claims_z", "cpi_yoy",
    "move_index_z", "skew_index_z", "put_call_ratio",
    "ted_spread_z", "libor_ois_z", "fra_ois_z",
    "copper_gold_ratio", "baltic_dry_pct20d",
]

CRISIS_TYPES = {
    "banking_instability": "BANKING_INSTABILITY",
    "market_crash": "MARKET_CRASH",
    "liquidity_shortage": "LIQUIDITY_SHORTAGE",
}


class CrisisClassifier:
    """A single crisis classifier using XGBoost + LightGBM ensemble."""

    def __init__(self, crisis_type: str) -> None:
        self.crisis_type = crisis_type
        self.xgb_model = None
        self.lgb_model = None
        self.meta_learner = None
        self.is_trained = False

    def train(self, X: np.ndarray, y: np.ndarray) -> dict[str, float]:
        """Train XGBoost + LightGBM base learners and LogisticRegression meta-learner.

        Returns training metrics dict.
        """
        import xgboost as xgb
        import lightgbm as lgb

        logger.info("Training %s classifier on %d samples...", self.crisis_type, len(y))

        # XGBoost base learner
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
            use_label_encoder=False,
        )
        self.xgb_model.fit(X, y)

        # LightGBM base learner
        self.lgb_model = lgb.LGBMClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1,
        )
        self.lgb_model.fit(X, y)

        # Stack predictions as meta-features
        xgb_proba = self.xgb_model.predict_proba(X)[:, 1]
        lgb_proba = self.lgb_model.predict_proba(X)[:, 1]
        meta_features = np.column_stack([xgb_proba, lgb_proba])

        # Meta-learner: LogisticRegression on ensemble outputs
        self.meta_learner = LogisticRegression(random_state=42, max_iter=1000)
        self.meta_learner.fit(meta_features, y)

        self.is_trained = True

        # Compute metrics
        xgb_cv = cross_val_score(self.xgb_model, X, y, cv=5, scoring="roc_auc")
        lgb_cv = cross_val_score(self.lgb_model, X, y, cv=5, scoring="roc_auc")
        meta_proba = self.meta_learner.predict_proba(meta_features)[:, 1]
        from sklearn.metrics import roc_auc_score
        meta_auc = roc_auc_score(y, meta_proba)

        metrics = {
            f"{self.crisis_type}_xgb_auc_mean": float(np.mean(xgb_cv)),
            f"{self.crisis_type}_lgb_auc_mean": float(np.mean(lgb_cv)),
            f"{self.crisis_type}_meta_auc": float(meta_auc),
            f"{self.crisis_type}_positive_rate": float(np.mean(y)),
        }

        logger.info(
            "%s trained: XGB AUC=%.3f LGB AUC=%.3f Meta AUC=%.3f",
            self.crisis_type,
            metrics[f"{self.crisis_type}_xgb_auc_mean"],
            metrics[f"{self.crisis_type}_lgb_auc_mean"],
            metrics[f"{self.crisis_type}_meta_auc"],
        )

        return metrics

    def predict_probability(self, X: np.ndarray) -> float:
        """Predict crisis probability for a single feature vector.

        Returns probability 0.0–1.0.
        """
        if not self.is_trained:
            logger.warning("%s: not trained, returning 0.0", self.crisis_type)
            return 0.0

        X_2d = X.reshape(1, -1) if X.ndim == 1 else X

        xgb_proba = self.xgb_model.predict_proba(X_2d)[:, 1]
        lgb_proba = self.lgb_model.predict_proba(X_2d)[:, 1]
        meta_features = np.column_stack([xgb_proba, lgb_proba])

        return float(self.meta_learner.predict_proba(meta_features)[0, 1])

    def predict_score(self, X: np.ndarray) -> float:
        """Predict and scale to 0–100 score."""
        return round(self.predict_probability(X) * 100, 2)

    def save(self, directory: Path) -> None:
        """Save model to disk with joblib."""
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.xgb_model, directory / f"{self.crisis_type}_xgb.joblib")
        joblib.dump(self.lgb_model, directory / f"{self.crisis_type}_lgb.joblib")
        joblib.dump(self.meta_learner, directory / f"{self.crisis_type}_meta.joblib")
        logger.info("Saved %s models to %s", self.crisis_type, directory)

    def load(self, directory: Path) -> bool:
        """Load model from disk. Returns True if successful."""
        try:
            self.xgb_model = joblib.load(directory / f"{self.crisis_type}_xgb.joblib")
            self.lgb_model = joblib.load(directory / f"{self.crisis_type}_lgb.joblib")
            self.meta_learner = joblib.load(directory / f"{self.crisis_type}_meta.joblib")
            self.is_trained = True
            logger.info("Loaded %s models from %s", self.crisis_type, directory)
            return True
        except FileNotFoundError:
            logger.warning("No saved models found for %s in %s", self.crisis_type, directory)
            return False


class EnsembleModel:
    """Container for all three crisis classifiers."""

    def __init__(self) -> None:
        self.classifiers: dict[str, CrisisClassifier] = {
            crisis_type: CrisisClassifier(crisis_type)
            for crisis_type in CRISIS_TYPES.values()
        }

    def train_all(self, mlflow_tracking_uri: str | None = None) -> dict[str, float]:
        """Train all classifiers from the training data CSV.

        Optionally logs metrics to MLflow.
        """
        # Load training data
        if not TRAINING_DATA_PATH.exists():
            logger.error("Training data not found at %s", TRAINING_DATA_PATH)
            return {}

        df = pd.read_csv(TRAINING_DATA_PATH)
        X = df[FEATURE_COLS].values.astype(np.float64)

        all_metrics: dict[str, float] = {}

        # Set up MLflow (optional)
        mlflow_run = None
        if mlflow_tracking_uri:
            try:
                import mlflow
                mlflow.set_tracking_uri(mlflow_tracking_uri)
                mlflow.set_experiment("crisislens-training")
                mlflow_run = mlflow.start_run(run_name="ensemble_training")
            except Exception:
                logger.warning("MLflow not available, skipping experiment tracking")

        label_map = {
            "BANKING_INSTABILITY": "banking_instability",
            "MARKET_CRASH": "market_crash",
            "LIQUIDITY_SHORTAGE": "liquidity_shortage",
        }

        for crisis_type, classifier in self.classifiers.items():
            label_col = label_map[crisis_type]
            y = df[label_col].values.astype(np.int32)
            metrics = classifier.train(X, y)
            all_metrics.update(metrics)

        # Save models
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        for classifier in self.classifiers.values():
            classifier.save(MODELS_DIR)

        # Log to MLflow
        if mlflow_run:
            try:
                import mlflow
                mlflow.log_metrics(all_metrics)
                mlflow.log_param("training_rows", len(df))
                mlflow.log_param("feature_count", len(FEATURE_COLS))
                mlflow.end_run()
            except Exception:
                logger.warning("Failed to log to MLflow")

        logger.info("All classifiers trained. Metrics: %s", all_metrics)
        return all_metrics

    def load_all(self) -> bool:
        """Load all classifier models from disk."""
        all_loaded = True
        for classifier in self.classifiers.values():
            if not classifier.load(MODELS_DIR):
                all_loaded = False
        return all_loaded

    def predict_all(self, feature_array: np.ndarray) -> dict[str, float]:
        """Predict scores (0–100) for all crisis types."""
        return {
            crisis_type: classifier.predict_score(feature_array)
            for crisis_type, classifier in self.classifiers.items()
        }

    def predict_probabilities(self, feature_array: np.ndarray) -> dict[str, float]:
        """Predict raw probabilities (0.0–1.0) for all crisis types."""
        return {
            crisis_type: classifier.predict_probability(feature_array)
            for crisis_type, classifier in self.classifiers.items()
        }


# Singleton instance
ensemble = EnsembleModel()
