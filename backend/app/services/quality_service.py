"""Signal Quality Service — computes freshness, completeness, anomaly flags.

On every signal update this service re-evaluates quality metrics:
  - freshness_score: 1.0 if <15min stale, linear decay to 0 over 2h
  - completeness_ratio: non-null readings / expected readings over 24h
  - anomaly_flag: True if |z_score| > 3.0
  - quality_badge: FRESH | STALE | DEGRADED | UNAVAILABLE
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────
FRESHNESS_FULL_WINDOW = timedelta(minutes=15)
FRESHNESS_DECAY_WINDOW = timedelta(hours=2)
EXPECTED_READINGS_24H = 96  # one reading per 15 min = 96 per day
Z_SCORE_ANOMALY_THRESHOLD = 3.0


def compute_freshness_score(freshness_ts: datetime) -> float:
    """Compute freshness score: 1.0 if <15min stale, linear decay to 0 over 2h."""
    now = datetime.now(timezone.utc)
    age = now - freshness_ts.replace(tzinfo=timezone.utc) if freshness_ts.tzinfo is None else now - freshness_ts

    if age <= FRESHNESS_FULL_WINDOW:
        return 1.0
    elif age >= FRESHNESS_DECAY_WINDOW:
        return 0.0
    else:
        # Linear decay between 15min and 2h
        elapsed_past_fresh = (age - FRESHNESS_FULL_WINDOW).total_seconds()
        decay_range = (FRESHNESS_DECAY_WINDOW - FRESHNESS_FULL_WINDOW).total_seconds()
        return max(0.0, 1.0 - (elapsed_past_fresh / decay_range))


def compute_anomaly_flag(z_score: float | None) -> bool:
    """Flag as anomaly if |z_score| > 3.0."""
    if z_score is None:
        return False
    return abs(z_score) > Z_SCORE_ANOMALY_THRESHOLD


def compute_quality_badge(
    freshness_score: float,
    completeness_ratio: float,
    raw_value: float | None,
) -> str:
    """Determine overall quality badge.

    - FRESH: freshness_score >= 0.8 and completeness >= 0.5
    - STALE: freshness_score < 0.8 but data exists
    - DEGRADED: completeness < 0.5
    - UNAVAILABLE: no raw_value at all
    """
    if raw_value is None:
        return "UNAVAILABLE"
    if completeness_ratio < 0.5:
        return "DEGRADED"
    if freshness_score >= 0.8:
        return "FRESH"
    return "STALE"


async def update_signal_quality(
    session: AsyncSession,
    signal: Signal,
) -> Signal:
    """Recompute and persist quality metadata for a signal."""
    signal.freshness_score = compute_freshness_score(signal.freshness_ts)
    signal.anomaly_flag = compute_anomaly_flag(signal.z_score)

    # Count non-null readings in the last 24h for completeness
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await session.execute(
        select(func.count())
        .select_from(Signal)
        .where(
            Signal.signal_id == signal.signal_id,
            Signal.freshness_ts >= cutoff,
            Signal.raw_value.isnot(None),
        )
    )
    non_null_count = result.scalar_one_or_none() or 0
    signal.completeness_ratio = min(1.0, non_null_count / EXPECTED_READINGS_24H)

    signal.quality_badge = compute_quality_badge(
        signal.freshness_score,
        signal.completeness_ratio,
        signal.raw_value,
    )

    session.add(signal)
    await session.flush()
    logger.debug(
        "Quality updated for %s: badge=%s freshness=%.2f completeness=%.2f anomaly=%s",
        signal.signal_id,
        signal.quality_badge,
        signal.freshness_score,
        signal.completeness_ratio,
        signal.anomaly_flag,
    )
    return signal


async def refresh_all_quality(session: AsyncSession) -> list[Signal]:
    """Recompute quality for every signal in the registry."""
    result = await session.execute(select(Signal))
    signals = list(result.scalars().all())

    for sig in signals:
        await update_signal_quality(session, sig)

    await session.commit()
    return signals
