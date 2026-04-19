"""Confidence Interval Calculator — Bootstrap CI for risk scores.

Runs the model 100x with ±5% Gaussian feature noise to produce
95% confidence bounds (ci_lower, ci_upper).

CI automatically widens when signal quality_score < 0.6.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

N_BOOTSTRAP = 100
NOISE_PCT = 0.05  # ±5% feature noise
CI_PERCENTILE_LOWER = 2.5
CI_PERCENTILE_UPPER = 97.5
QUALITY_THRESHOLD = 0.6
QUALITY_PENALTY_FACTOR = 1.5  # Widen CI by 50% when quality is low


class CICalculator:
    """Computes bootstrap confidence intervals for model predictions."""

    def compute_ci(
        self,
        model,  # CrisisClassifier instance
        feature_array: np.ndarray,
        avg_quality_score: float = 1.0,
    ) -> tuple[float, float]:
        """Run bootstrap to estimate 95% CI bounds.

        Args:
            model: A trained CrisisClassifier with predict_score method.
            feature_array: 1-D feature vector.
            avg_quality_score: Average signal quality score (0–1).
                If < 0.6, CI is widened by QUALITY_PENALTY_FACTOR.

        Returns:
            Tuple of (ci_lower, ci_upper) on the 0–100 scale.
        """
        if not model.is_trained:
            logger.warning("Model not trained, returning wide CI")
            return (0.0, 100.0)

        base_score = model.predict_score(feature_array)
        bootstrap_scores: list[float] = []

        for _ in range(N_BOOTSTRAP):
            # Add Gaussian noise: ±5% of each feature value
            noise = np.random.normal(1.0, NOISE_PCT, size=feature_array.shape)
            noisy_features = feature_array * noise
            score = model.predict_score(noisy_features)
            bootstrap_scores.append(score)

        scores_arr = np.array(bootstrap_scores)
        ci_lower = float(np.percentile(scores_arr, CI_PERCENTILE_LOWER))
        ci_upper = float(np.percentile(scores_arr, CI_PERCENTILE_UPPER))

        # Widen CI when signal quality is poor
        if avg_quality_score < QUALITY_THRESHOLD:
            spread = ci_upper - ci_lower
            extra = spread * (QUALITY_PENALTY_FACTOR - 1.0)
            ci_lower = max(0.0, ci_lower - extra / 2)
            ci_upper = min(100.0, ci_upper + extra / 2)

        # Ensure base score is within bounds
        ci_lower = min(ci_lower, base_score)
        ci_upper = max(ci_upper, base_score)

        # Clamp to valid range
        ci_lower = round(max(0.0, ci_lower), 2)
        ci_upper = round(min(100.0, ci_upper), 2)

        logger.debug(
            "CI for %s: score=%.2f [%.2f, %.2f] quality=%.2f",
            model.crisis_type, base_score, ci_lower, ci_upper, avg_quality_score,
        )

        return (ci_lower, ci_upper)

    def compute_all_ci(
        self,
        classifiers: dict,
        feature_array: np.ndarray,
        avg_quality_score: float = 1.0,
    ) -> dict[str, tuple[float, float]]:
        """Compute CI for all crisis classifiers.

        Returns dict of crisis_type → (ci_lower, ci_upper).
        """
        results = {}
        for crisis_type, model in classifiers.items():
            results[crisis_type] = self.compute_ci(model, feature_array, avg_quality_score)
        return results


# Singleton
ci_calculator = CICalculator()
