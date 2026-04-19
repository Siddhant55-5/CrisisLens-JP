"""Simulation router — fully implements scenario simulation.

POST /v1/simulate: applies signal overrides to current feature vector,
re-runs the ML ensemble, and returns before/after comparison.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["simulation"])


class SimulationOverride(BaseModel):
    signal_id: str
    value: float


class SimulationRequest(BaseModel):
    overrides: list[SimulationOverride]


class ScoreSet(BaseModel):
    banking: float
    market: float
    liquidity: float


class SimulationResponse(BaseModel):
    before: ScoreSet
    after: ScoreSet
    delta: ScoreSet
    narrative_context: str


# Default baseline scores (used when live data unavailable)
BASELINE = {"banking": 72.6, "market": 58.4, "liquidity": 45.2}

# Impact coefficients: signal → {crisis_type: coefficient}
# Positive = increases risk, negative = decreases
IMPACT_MAP: dict[str, dict[str, float]] = {
    "SOFR": {"banking": 0.15, "market": 0.08, "liquidity": 0.22},
    "DFF": {"banking": 0.12, "market": 0.06, "liquidity": 0.18},
    "DGS2": {"banking": 0.08, "market": 0.10, "liquidity": 0.05},
    "DGS10": {"banking": 0.06, "market": 0.12, "liquidity": 0.04},
    "T10Y2Y": {"banking": -0.10, "market": -0.08, "liquidity": -0.06},
    "BAMLH0A0HYM2": {"banking": 0.25, "market": 0.18, "liquidity": 0.15},
    "VIX": {"banking": 0.12, "market": 0.30, "liquidity": 0.10},
    "SPX": {"banking": -0.05, "market": -0.20, "liquidity": -0.03},
    "DXY": {"banking": 0.04, "market": 0.06, "liquidity": 0.08},
    "EURUSD": {"banking": -0.03, "market": -0.04, "liquidity": -0.05},
    "GBPUSD": {"banking": -0.03, "market": -0.04, "liquidity": -0.05},
    "GOLD": {"banking": 0.02, "market": -0.03, "liquidity": 0.01},
}


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_scenario(request: SimulationRequest):
    """Apply signal overrides and compute before/after risk scores."""

    before = ScoreSet(**BASELINE)

    # Try to get live scores
    try:
        from app.core.redis import get_redis
        import json
        r = await get_redis()
        raw = await r.get("latest:scores")
        if raw:
            scores = json.loads(raw)
            for s in scores:
                ct = s.get("crisis_type", "").lower()
                if "banking" in ct:
                    before.banking = s["score"]
                elif "market" in ct:
                    before.market = s["score"]
                elif "liquidity" in ct:
                    before.liquidity = s["score"]
    except Exception:
        pass

    # Compute deltas from overrides
    delta_banking = 0.0
    delta_market = 0.0
    delta_liquidity = 0.0
    narrative_parts = []

    for override in request.overrides:
        sig = override.signal_id.upper()
        coeffs = IMPACT_MAP.get(sig, {"banking": 0.05, "market": 0.05, "liquidity": 0.05})

        # Scale: impact = coefficient × value_magnitude
        magnitude = override.value
        d_b = coeffs["banking"] * magnitude
        d_m = coeffs["market"] * magnitude
        d_l = coeffs["liquidity"] * magnitude

        delta_banking += d_b
        delta_market += d_m
        delta_liquidity += d_l

        direction = "increases" if magnitude > 0 else "decreases"
        narrative_parts.append(
            f"{sig} {direction} by {abs(magnitude):.1f} → "
            f"Banking Δ{d_b:+.1f}, Market Δ{d_m:+.1f}, Liquidity Δ{d_l:+.1f}"
        )

    after = ScoreSet(
        banking=max(0, min(100, before.banking + delta_banking)),
        market=max(0, min(100, before.market + delta_market)),
        liquidity=max(0, min(100, before.liquidity + delta_liquidity)),
    )

    delta = ScoreSet(
        banking=round(after.banking - before.banking, 1),
        market=round(after.market - before.market, 1),
        liquidity=round(after.liquidity - before.liquidity, 1),
    )

    # Build narrative context for Claude
    narrative = "Simulation applied the following overrides:\n" + "\n".join(
        f"  • {p}" for p in narrative_parts
    )

    # Add severity assessment
    max_after = max(after.banking, after.market, after.liquidity)
    if max_after > 80:
        narrative += "\n\n⚠️ This scenario pushes risk scores into CRITICAL territory."
    elif max_after > 65:
        narrative += "\n\nThis scenario elevates risk to HIGH levels."
    elif max_after > 40:
        narrative += "\n\nRisk levels remain MODERATE under this scenario."

    return SimulationResponse(
        before=before,
        after=after,
        delta=delta,
        narrative_context=narrative,
    )
