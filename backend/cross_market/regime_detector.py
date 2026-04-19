"""Regime Detector — identifies normal vs stress market regimes.

Normal regime: avg pairwise correlation < 0.4
Stress regime: avg pairwise correlation > 0.65
Fires alert when regime shifts normal → stress.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pydantic import BaseModel

from app.core.redis import get_redis
from cross_market.correlation_engine import CorrelationMatrix, correlation_engine

logger = logging.getLogger(__name__)

REGIME_STREAM = "regime.alerts"
NORMAL_THRESHOLD = 0.4
STRESS_THRESHOLD = 0.65


class RegimeShiftAlert(BaseModel):
    """Alert fired when market regime changes."""
    detected_at: str
    from_regime: str  # "normal" | "stress"
    to_regime: str
    avg_correlation: float
    most_correlated_pairs: list[dict]  # [{signal_a, signal_b, value}]
    historical_precedent: str


class RegimeDetector:
    """Detects regime shifts by monitoring correlation convergence."""

    def __init__(self) -> None:
        self._current_regime: str = "normal"
        self._last_shift: RegimeShiftAlert | None = None

    @property
    def current_regime(self) -> str:
        return self._current_regime

    @property
    def last_shift(self) -> RegimeShiftAlert | None:
        return self._last_shift

    async def evaluate(self, matrix: CorrelationMatrix | None = None) -> RegimeShiftAlert | None:
        """Evaluate current regime based on correlation matrix.

        Returns RegimeShiftAlert if a regime shift occurred.
        """
        if matrix is None:
            matrix = await correlation_engine.compute_matrix("20D")

        avg_corr = correlation_engine.get_avg_correlation(matrix)

        # Determine regime
        if avg_corr >= STRESS_THRESHOLD:
            new_regime = "stress"
        elif avg_corr <= NORMAL_THRESHOLD:
            new_regime = "normal"
        else:
            new_regime = "elevated"  # In-between state

        # Check for regime shift
        if new_regime != self._current_regime:
            previous = self._current_regime
            self._current_regime = new_regime

            # Only fire alert on shift to stress
            if new_regime == "stress" and previous in ("normal", "elevated"):
                # Find most correlated pairs
                sorted_pairs = sorted(
                    matrix.pairs,
                    key=lambda p: abs(p.pearson),
                    reverse=True,
                )[:5]

                top_pairs = [
                    {"signal_a": p.signal_a, "signal_b": p.signal_b, "value": p.pearson}
                    for p in sorted_pairs
                ]

                precedent = self._find_precedent(avg_corr)

                alert = RegimeShiftAlert(
                    detected_at=datetime.now(timezone.utc).isoformat(),
                    from_regime=previous,
                    to_regime=new_regime,
                    avg_correlation=round(avg_corr, 4),
                    most_correlated_pairs=top_pairs,
                    historical_precedent=precedent,
                )

                self._last_shift = alert
                await self._publish_alert(alert)

                logger.warning(
                    "🔴 REGIME SHIFT: %s → %s (avg_corr=%.3f)",
                    previous, new_regime, avg_corr,
                )
                return alert

        return None

    def get_regime_info(self) -> dict:
        """Return current regime information."""
        return {
            "current_regime": self._current_regime,
            "last_shift": self._last_shift.model_dump() if self._last_shift else None,
        }

    def _find_precedent(self, avg_corr: float) -> str:
        """Match current conditions to historical precedent."""
        if avg_corr > 0.85:
            return "Correlation convergence at this level matches the 2008 Global Financial Crisis, when cross-asset correlations spiked above 0.85 as systemic risk materialized."
        if avg_corr > 0.75:
            return "Similar correlation levels were observed during the March 2020 COVID crash, with broad asset co-movement driven by liquidity withdrawal."
        if avg_corr > 0.65:
            return "Elevated correlations resemble the 2011 European Debt Crisis, where contagion spread across sovereign, banking, and equity markets."
        return "Correlation levels are within historical norms. No immediate crisis precedent identified."

    async def _publish_alert(self, alert: RegimeShiftAlert) -> None:
        """Publish regime shift alert to Redis stream."""
        try:
            r = await get_redis()
            await r.xadd(
                REGIME_STREAM,
                {
                    "type": "regime_shift",
                    "from_regime": alert.from_regime,
                    "to_regime": alert.to_regime,
                    "avg_correlation": str(alert.avg_correlation),
                    "detected_at": alert.detected_at,
                },
                maxlen=1000,
            )
        except Exception:
            logger.exception("Failed to publish regime shift alert")


# Singleton
regime_detector = RegimeDetector()
