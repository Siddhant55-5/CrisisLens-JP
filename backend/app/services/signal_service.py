"""Signal Service — CRUD operations and upsert logic for the signal registry."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal, SignalCategory
from app.services.quality_service import update_signal_quality
from app.services.stream_service import publish_signal_update

logger = logging.getLogger(__name__)


async def upsert_signal(
    session: AsyncSession,
    signal_id: str,
    raw_value: float | None,
    *,
    name: str | None = None,
    category: SignalCategory | None = None,
    source: str | None = None,
    is_mock: bool = False,
) -> Signal:
    """Insert or update a signal reading, recompute quality, and publish to Redis."""
    result = await session.execute(
        select(Signal).where(Signal.signal_id == signal_id)
    )
    signal = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if signal is None:
        signal = Signal(
            signal_id=signal_id,
            name=name or signal_id,
            category=category or SignalCategory.MACRO,
            source=source,
            raw_value=raw_value,
            freshness_ts=now,
            is_mock=is_mock,
            created_at=now,
            updated_at=now,
        )
        session.add(signal)
    else:
        # Compute 1-day pct change
        if signal.raw_value is not None and raw_value is not None and signal.raw_value != 0:
            signal.pct_change_1d = ((raw_value - signal.raw_value) / abs(signal.raw_value)) * 100.0
        else:
            signal.pct_change_1d = 0.0

        signal.raw_value = raw_value
        signal.freshness_ts = now
        signal.is_mock = is_mock
        signal.updated_at = now
        if name:
            signal.name = name
        if source:
            signal.source = source

    # Compute z-score using recent history
    await _compute_z_score(session, signal)

    # Recompute quality metrics
    await update_signal_quality(session, signal)

    await session.flush()

    # Publish to Redis stream
    await publish_signal_update(
        signal_id=signal.signal_id,
        raw_value=signal.raw_value,
        z_score=signal.z_score,
        anomaly_flag=signal.anomaly_flag,
        ts=signal.freshness_ts,
    )

    return signal


async def _compute_z_score(session: AsyncSession, signal: Signal) -> None:
    """Compute z-score from the current value relative to recent history.

    Uses a rolling 90-day window. If insufficient history, z_score = 0.
    """
    if signal.raw_value is None:
        signal.z_score = 0.0
        return

    # For now, use a simple heuristic since we don't have a history table yet.
    # The z-score will be refined in Sprint 2 with proper history tables.
    # Here we use the signals table's own rows as a crude proxy.
    result = await session.execute(
        text("""
            SELECT AVG(raw_value) as mean_val, STDDEV(raw_value) as std_val
            FROM signals
            WHERE signal_id = :sid AND raw_value IS NOT NULL
        """),
        {"sid": signal.signal_id},
    )
    row = result.one_or_none()

    if row and row.std_val and row.std_val > 0:
        signal.z_score = round((signal.raw_value - row.mean_val) / row.std_val, 4)
    else:
        signal.z_score = 0.0


async def get_all_signals(session: AsyncSession) -> list[Signal]:
    """Retrieve all signals with latest values."""
    result = await session.execute(
        select(Signal).order_by(Signal.category, Signal.signal_id)
    )
    return list(result.scalars().all())


async def get_signal_by_id(session: AsyncSession, signal_id: str) -> Signal | None:
    """Retrieve a single signal by ID."""
    result = await session.execute(
        select(Signal).where(Signal.signal_id == signal_id)
    )
    return result.scalar_one_or_none()
