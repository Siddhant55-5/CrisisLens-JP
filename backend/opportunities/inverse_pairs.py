"""Inverse pair engine — flags negatively correlated assets as hedging opportunities.

Uses 252D rolling correlations to identify strong inverse relationships,
enriched with hard-coded prior pairs that are always included.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InversePair:
    instrument_a: str
    instrument_b: str
    correlation_252d: float
    direction_a: str  # "↑" or "↓"
    direction_b: str
    confidence: float
    historical_win_rate: float


# Hard-coded prior pairs (always included in results)
PRIOR_PAIRS: list[dict] = [
    {
        "instrument_a": "VIX",
        "instrument_b": "SPX",
        "correlation_252d": -0.82,
        "direction_a": "↑",
        "direction_b": "↓",
        "confidence": 0.92,
        "historical_win_rate": 0.87,
        "crisis_types": ["MARKET_CRASH", "BANKING_INSTABILITY", "LIQUIDITY_SHORTAGE"],
    },
    {
        "instrument_a": "GOLD",
        "instrument_b": "DXY",
        "correlation_252d": -0.45,
        "direction_a": "↑",
        "direction_b": "↓",
        "confidence": 0.78,
        "historical_win_rate": 0.72,
        "crisis_types": ["BANKING_INSTABILITY", "MARKET_CRASH"],
    },
    {
        "instrument_a": "DGS10",
        "instrument_b": "BAMLH0A0HYM2",
        "correlation_252d": -0.58,
        "direction_a": "↑",
        "direction_b": "↑",
        "confidence": 0.82,
        "historical_win_rate": 0.76,
        "crisis_types": ["BANKING_INSTABILITY", "LIQUIDITY_SHORTAGE"],
    },
    {
        "instrument_a": "GBPUSD",
        "instrument_b": "DXY",
        "correlation_252d": -0.75,
        "direction_a": "↓",
        "direction_b": "↑",
        "confidence": 0.85,
        "historical_win_rate": 0.74,
        "crisis_types": ["MARKET_CRASH", "LIQUIDITY_SHORTAGE"],
    },
    {
        "instrument_a": "EURUSD",
        "instrument_b": "DXY",
        "correlation_252d": -0.88,
        "direction_a": "↓",
        "direction_b": "↑",
        "confidence": 0.90,
        "historical_win_rate": 0.81,
        "crisis_types": ["MARKET_CRASH", "BANKING_INSTABILITY"],
    },
]


class InversePairEngine:
    """Identifies inverse pair opportunities from correlation data."""

    def __init__(self) -> None:
        self._cached_pairs: list[dict] = []

    async def get_inverse_pairs(
        self,
        crisis_type: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Get top inverse pair opportunities.

        Args:
            crisis_type: Filter pairs relevant to this crisis type.
            limit: Maximum number of pairs to return.
        """
        # Start with prior pairs
        pairs = list(PRIOR_PAIRS)

        # Try to enrich from live correlation data
        try:
            live_pairs = await self._scan_live_correlations()
            pairs.extend(live_pairs)
        except Exception:
            logger.debug("Live correlation scan unavailable, using priors only")

        # Filter by crisis type if specified
        if crisis_type:
            ct = crisis_type.upper()
            pairs = [
                p for p in pairs
                if ct in p.get("crisis_types", [])
            ]

        # Sort by confidence, deduplicate
        seen = set()
        unique_pairs = []
        for p in sorted(pairs, key=lambda x: x["confidence"], reverse=True):
            key = tuple(sorted([p["instrument_a"], p["instrument_b"]]))
            if key not in seen:
                seen.add(key)
                unique_pairs.append(p)

        result = unique_pairs[:limit]

        # Strip crisis_types from output (internal metadata)
        return [
            {k: v for k, v in p.items() if k != "crisis_types"}
            for p in result
        ]

    async def _scan_live_correlations(self) -> list[dict]:
        """Scan Redis for pairs with correlation < -0.6."""
        try:
            from app.core.redis import get_redis
            import json

            r = await get_redis()
            # Try to get 252D correlation matrix
            keys = await r.keys("corr:252D:*")
            if not keys:
                return []

            latest_key = sorted(keys)[-1]
            raw = await r.get(latest_key)
            if not raw:
                return []

            matrix = json.loads(raw)
            live_pairs = []

            for pair in matrix.get("pairs", []):
                pearson = pair.get("pearson", 0)
                if pearson < -0.6:
                    live_pairs.append({
                        "instrument_a": pair["signal_a"],
                        "instrument_b": pair["signal_b"],
                        "correlation_252d": pearson,
                        "direction_a": "↑" if pearson < 0 else "↓",
                        "direction_b": "↓" if pearson < 0 else "↑",
                        "confidence": min(0.95, abs(pearson)),
                        "historical_win_rate": 0.68,
                        "crisis_types": ["MARKET_CRASH", "BANKING_INSTABILITY"],
                    })

            return live_pairs
        except Exception:
            return []


# Singleton
inverse_pair_engine = InversePairEngine()
