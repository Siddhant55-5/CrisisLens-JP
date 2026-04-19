"""Fallback service — graceful degradation when data sources are unavailable.

Priority chain:
  1. Live data (Redis + TimescaleDB)
  2. Redis cache (last 30 min)
  3. In-memory snapshot
  4. Synthetic scenario JSON
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from chat.system_prompt import ContextSnapshot

logger = logging.getLogger(__name__)

# Pre-built synthetic scenario for total data outage
SYNTHETIC_PATH = Path(__file__).parent / "synthetic_scenario.json"


class FallbackService:
    """Provides context snapshots with graceful fallbacks."""

    def __init__(self) -> None:
        self._last_snapshot: ContextSnapshot | None = None
        self._last_snapshot_at: str = ""
        self._synthetic: dict | None = None

    async def get_context(self) -> ContextSnapshot:
        """Get the best available context snapshot."""

        # 1. Try live data
        try:
            ctx = await self._fetch_live_context()
            self._last_snapshot = ctx
            self._last_snapshot_at = datetime.now(timezone.utc).isoformat()
            return ctx
        except Exception:
            logger.warning("Live data unavailable, falling back...")

        # 2. Try Redis cache
        try:
            ctx = await self._fetch_cached_context()
            if ctx:
                return ctx
        except Exception:
            logger.warning("Redis cache unavailable")

        # 3. In-memory snapshot
        if self._last_snapshot:
            logger.info("Using in-memory snapshot from %s", self._last_snapshot_at)
            self._last_snapshot.is_cached = True
            self._last_snapshot.cached_at = self._last_snapshot_at
            return self._last_snapshot

        # 4. Synthetic scenario
        return self._load_synthetic()

    async def _fetch_live_context(self) -> ContextSnapshot:
        """Fetch live scores + alerts from backend services."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()

            # Try to get latest scores from Redis
            scores_raw = await r.get("latest:scores")
            alerts_raw = await r.get("latest:alerts")

            if scores_raw:
                import json as _json
                scores = _json.loads(scores_raw)
                banking = next((s for s in scores if s.get("crisis_type") == "BANKING_INSTABILITY"), {})
                market = next((s for s in scores if s.get("crisis_type") == "MARKET_CRASH"), {})
                liquidity = next((s for s in scores if s.get("crisis_type") == "LIQUIDITY_SHORTAGE"), {})

                return ContextSnapshot(
                    banking_score=banking.get("score", 0),
                    banking_ci_lower=banking.get("ci_lower", 0),
                    banking_ci_upper=banking.get("ci_upper", 0),
                    market_score=market.get("score", 0),
                    market_ci_lower=market.get("ci_lower", 0),
                    market_ci_upper=market.get("ci_upper", 0),
                    liquidity_score=liquidity.get("score", 0),
                    liquidity_ci_lower=liquidity.get("ci_lower", 0),
                    liquidity_ci_upper=liquidity.get("ci_upper", 0),
                )
        except Exception:
            pass

        # Fall back to mock scores
        return self._mock_context()

    async def _fetch_cached_context(self) -> ContextSnapshot | None:
        """Fetch from Redis 30-min cache."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()
            cached = await r.get("context:snapshot:latest")
            if cached:
                data = json.loads(cached)
                ctx = ContextSnapshot(**data)
                ctx.is_cached = True
                ctx.cached_at = data.get("cached_at", "unknown")
                return ctx
        except Exception:
            pass
        return None

    def _load_synthetic(self) -> ContextSnapshot:
        """Load synthetic scenario from JSON file."""
        if not self._synthetic:
            try:
                self._synthetic = json.loads(SYNTHETIC_PATH.read_text())
            except Exception:
                logger.warning("Synthetic scenario file not found, using defaults")
                self._synthetic = {}

        s = self._synthetic
        return ContextSnapshot(
            banking_score=s.get("banking_score", 58.0),
            banking_ci_lower=s.get("banking_ci_lower", 52.0),
            banking_ci_upper=s.get("banking_ci_upper", 65.0),
            market_score=s.get("market_score", 52.0),
            market_ci_lower=s.get("market_ci_lower", 45.0),
            market_ci_upper=s.get("market_ci_upper", 60.0),
            liquidity_score=s.get("liquidity_score", 45.0),
            liquidity_ci_lower=s.get("liquidity_ci_lower", 38.0),
            liquidity_ci_upper=s.get("liquidity_ci_upper", 52.0),
            alert_summaries=s.get("alert_summaries", "MEDIUM: Banking instability elevated (HY spread +2.1σ)"),
            shap_signals=s.get("shap_signals", "hy_spread_z5d (+0.32), vix_z5d (+0.28), libor_ois_z (+0.24)"),
            regime_status=s.get("regime_status", "Elevated — avg |ρ| = 0.52"),
            quality_summary=s.get("quality_summary", "SIMULATION MODE — No live data"),
            is_cached=True,
            cached_at="synthetic",
        )

    def _mock_context(self) -> ContextSnapshot:
        """Return realistic mock context for demo."""
        return ContextSnapshot(
            banking_score=72.6,
            banking_ci_lower=66.0,
            banking_ci_upper=79.0,
            market_score=58.4,
            market_ci_lower=52.0,
            market_ci_upper=65.0,
            liquidity_score=45.2,
            liquidity_ci_lower=38.0,
            liquidity_ci_upper=52.0,
            alert_summaries="HIGH: Banking instability 72.6 [66–79]. MEDIUM: Market crash risk 58.4 [52–65].",
            shap_signals="hy_spread_z5d (+0.32), vix_z5d (+0.28), interbank_stress (+0.24), dgs10_momentum (-0.18), ted_spread (+0.15)",
            regime_status="Elevated — avg |ρ| = 0.52, rising from 0.38 over 5 sessions",
            quality_summary="42/42 signals nominal. Last update: <1 min ago.",
        )


# Singleton
fallback_service = FallbackService()
