"""Recalibration Cron — weekly model probability recalibration.

Runs every Sunday 02:00 UTC via APScheduler:
1. Collect past-week predictions vs simplified realised outcomes
2. Apply sklearn isotonic_regression to recalibrate probabilities
3. Log recalibration delta to MLflow experiment "recalibration"
4. If delta > 0.15, send degraded_model warning to Redis Stream
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.redis import get_redis
from app.models.alert import RiskScore

logger = logging.getLogger(__name__)

DEGRADATION_THRESHOLD = 0.15
DEGRADATION_STREAM = "model.warnings"


async def run_recalibration() -> None:
    """Weekly recalibration: compare predictions to simplified outcomes."""
    logger.info("Starting weekly recalibration...")

    async with async_session_factory() as session:
        # Get past week's scores
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        result = await session.execute(
            select(RiskScore).where(RiskScore.scored_at >= week_ago)
        )
        recent_scores = list(result.scalars().all())

        if len(recent_scores) < 3:
            logger.info("Insufficient scores for recalibration (%d), skipping", len(recent_scores))
            return

        # Group by crisis type
        from app.models.alert import CrisisType

        recal_deltas: dict[str, float] = {}

        for ct in CrisisType:
            ct_scores = [s for s in recent_scores if s.crisis_type == ct]
            if len(ct_scores) < 2:
                continue

            # Simplified realised outcome: use latest signal conditions as proxy
            # In production, this would compare against actual market events
            predicted_probs = np.array([s.score / 100.0 for s in ct_scores])

            # Generate simplified outcomes based on score stability
            # (proxy: if scores stayed high, treat as "near-miss" = partial positive)
            mean_score = float(np.mean(predicted_probs))
            std_score = float(np.std(predicted_probs))

            # Synthetic outcomes for calibration
            outcomes = np.zeros(len(predicted_probs))
            # Mark high-score periods as partial positives
            for i, prob in enumerate(predicted_probs):
                if prob > 0.7:
                    outcomes[i] = 0.8  # near-miss
                elif prob > 0.5:
                    outcomes[i] = 0.3  # elevated but not crisis
                else:
                    outcomes[i] = 0.05  # calm period

            # Apply isotonic regression for monotonic calibration
            try:
                from sklearn.isotonic import IsotonicRegression

                iso_reg = IsotonicRegression(out_of_bounds="clip")
                calibrated = iso_reg.fit_transform(predicted_probs, outcomes)

                # Compute recalibration delta (mean absolute shift)
                delta = float(np.mean(np.abs(calibrated - predicted_probs)))
                recal_deltas[ct.value] = delta

                logger.info(
                    "Recalibration %s: delta=%.4f (threshold=%.2f)",
                    ct.value, delta, DEGRADATION_THRESHOLD,
                )

                # Check for model degradation
                if delta > DEGRADATION_THRESHOLD:
                    logger.warning(
                        "⚠️ Model degradation detected for %s: delta=%.4f > %.2f",
                        ct.value, delta, DEGRADATION_THRESHOLD,
                    )
                    await _send_degradation_warning(ct.value, delta)

            except Exception:
                logger.exception("Isotonic regression failed for %s", ct.value)

        # Log to MLflow
        await _log_to_mlflow(recal_deltas)

    logger.info("Recalibration complete: %s", recal_deltas)


async def _send_degradation_warning(crisis_type: str, delta: float) -> None:
    """Publish model degradation warning to Redis stream."""
    try:
        r = await get_redis()
        await r.xadd(
            DEGRADATION_STREAM,
            {
                "type": "degraded_model",
                "crisis_type": crisis_type,
                "delta": str(round(delta, 4)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": f"Model calibration shifted by {delta:.4f} for {crisis_type}",
            },
            maxlen=1000,
        )
        logger.info("Published degradation warning for %s", crisis_type)
    except Exception:
        logger.exception("Failed to publish degradation warning")


async def _log_to_mlflow(deltas: dict[str, float]) -> None:
    """Log recalibration metrics to MLflow."""
    try:
        import mlflow

        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("recalibration")

        with mlflow.start_run(run_name=f"recal_{datetime.now(timezone.utc).strftime('%Y%m%d')}"):
            for crisis_type, delta in deltas.items():
                mlflow.log_metric(f"{crisis_type}_delta", delta)
            mlflow.log_param("timestamp", datetime.now(timezone.utc).isoformat())

        logger.info("Logged recalibration to MLflow")
    except Exception:
        logger.warning("MLflow logging failed for recalibration (non-critical)")
