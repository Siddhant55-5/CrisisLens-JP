"""SHAP Explainability — explains model predictions with feature attributions.

Uses shap.TreeExplainer on the XGBoost base model to compute
per-prediction feature importance, returning top-5 SHAP contributions.

Also finds the nearest historical crisis analog via Euclidean distance.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

TRAINING_DATA_PATH = Path(__file__).parent / "training_data" / "crisis_labels.csv"

# Known crisis events for historical analog matching
CRISIS_EVENTS = [
    {
        "event_name": "Dot-Com Crash",
        "date": "2000-03-10",
        "outcome_summary": "NASDAQ fell 78% over 30 months. Tech sector decimated, mild recession followed.",
    },
    {
        "event_name": "Global Financial Crisis",
        "date": "2008-09-15",
        "outcome_summary": "Lehman collapse triggered global banking crisis. S&P 500 fell 57%. Massive bailouts required.",
    },
    {
        "event_name": "European Sovereign Debt Crisis",
        "date": "2010-05-02",
        "outcome_summary": "Greek bailout triggered contagion to Portugal, Ireland, Spain. ECB intervention required.",
    },
    {
        "event_name": "China Stock Market Crash",
        "date": "2015-08-24",
        "outcome_summary": "Shanghai Composite fell 43% in 2 months. Global spillover via commodity and EM channels.",
    },
    {
        "event_name": "COVID-19 Market Crash",
        "date": "2020-03-16",
        "outcome_summary": "Fastest 30% drawdown in history. Fed cut rates to zero, unlimited QE. V-shaped recovery.",
    },
    {
        "event_name": "2022 Rate Shock",
        "date": "2022-06-13",
        "outcome_summary": "Aggressive Fed hiking cycle. S&P 500 bear market. Bond market worst year in decades.",
    },
    {
        "event_name": "SVB Banking Crisis",
        "date": "2023-03-10",
        "outcome_summary": "Silicon Valley Bank collapsed in 48 hours. Regional banking stress, FDIC intervention.",
    },
]

# Feature columns matching training data
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


class SHAPExplainer:
    """Explains model predictions using SHAP values and historical analogs."""

    def __init__(self) -> None:
        self._training_data: pd.DataFrame | None = None
        self._crisis_rows: pd.DataFrame | None = None

    def _load_training_data(self) -> None:
        """Lazy-load training data for historical analog search."""
        if self._training_data is None and TRAINING_DATA_PATH.exists():
            self._training_data = pd.read_csv(TRAINING_DATA_PATH)
            # Filter to crisis rows only
            self._crisis_rows = self._training_data[
                (self._training_data["banking_instability"] == 1)
                | (self._training_data["market_crash"] == 1)
                | (self._training_data["liquidity_shortage"] == 1)
            ].copy()

    def explain(
        self,
        classifier,  # CrisisClassifier
        feature_array: np.ndarray,
        feature_names: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """Compute top-K SHAP feature contributions for a prediction.

        Returns list of ShapContribution dicts:
            {feature_name, shap_value, direction, rank}
        """
        if not classifier.is_trained or classifier.xgb_model is None:
            logger.warning("Classifier not trained, returning empty SHAP")
            return []

        try:
            import shap

            explainer = shap.TreeExplainer(classifier.xgb_model)
            X_2d = feature_array.reshape(1, -1) if feature_array.ndim == 1 else feature_array
            shap_values = explainer.shap_values(X_2d)

            # shap_values may be list for binary classification
            if isinstance(shap_values, list):
                # Use class 1 (positive/crisis) SHAP values
                sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            elif shap_values.ndim == 2:
                sv = shap_values[0]
            else:
                sv = shap_values

            # Rank by absolute SHAP value
            abs_vals = np.abs(sv)
            top_indices = np.argsort(abs_vals)[::-1][:top_k]

            contributions = []
            for rank, idx in enumerate(top_indices, 1):
                contributions.append({
                    "feature_name": feature_names[idx] if idx < len(feature_names) else f"feature_{idx}",
                    "shap_value": round(float(sv[idx]), 6),
                    "direction": "up" if sv[idx] > 0 else "down",
                    "rank": rank,
                })

            return contributions

        except Exception:
            logger.exception("SHAP explanation failed for %s", classifier.crisis_type)
            return []

    def find_historical_analog(
        self,
        feature_array: np.ndarray,
    ) -> dict | None:
        """Find the nearest historical crisis event by Euclidean distance.

        Searches training data crisis rows, maps date to known crisis events.

        Returns HistoricalAnalog dict or None.
        """
        self._load_training_data()

        if self._crisis_rows is None or self._crisis_rows.empty:
            logger.warning("No training data available for analog search")
            return None

        try:
            X_crisis = self._crisis_rows[FEATURE_COLS].values.astype(np.float64)
            query = feature_array.reshape(1, -1) if feature_array.ndim == 1 else feature_array

            # Compute Euclidean distances
            distances = np.linalg.norm(X_crisis - query, axis=1)
            nearest_idx = int(np.argmin(distances))
            nearest_distance = float(distances[nearest_idx])

            # Convert distance to similarity score (0–1, higher is more similar)
            max_possible = float(np.max(distances)) if len(distances) > 1 else nearest_distance + 1
            similarity = round(1.0 - (nearest_distance / max(max_possible, 1e-6)), 4)
            similarity = max(0.0, min(1.0, similarity))

            # Get the date of nearest crisis row
            nearest_date = self._crisis_rows.iloc[nearest_idx]["date"]
            nearest_year = int(str(nearest_date)[:4])

            # Match to known crisis event by year proximity
            best_event = None
            best_year_diff = 100
            for event in CRISIS_EVENTS:
                event_year = int(event["date"][:4])
                diff = abs(event_year - nearest_year)
                if diff < best_year_diff:
                    best_year_diff = diff
                    best_event = event

            if best_event is None:
                return None

            return {
                "event_name": best_event["event_name"],
                "date": best_event["date"],
                "similarity_score": similarity,
                "outcome_summary": best_event["outcome_summary"],
            }

        except Exception:
            logger.exception("Historical analog search failed")
            return None


# Singleton
shap_explainer = SHAPExplainer()
