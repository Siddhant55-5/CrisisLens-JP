"""Signal API routes.

GET /v1/signals          — all signals with latest values + quality
GET /v1/signals/{id}     — single signal detail + 90-day history
GET /v1/quality          — all quality badges
GET /healthz             — service health check
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.models.signal import Signal
from app.schemas.signal import (
    HealthResponse,
    QualityResponse,
    SignalDetailResponse,
    SignalHistoryPoint,
    SignalResponse,
)
from app.services.signal_service import get_all_signals, get_signal_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/v1/signals", response_model=list[SignalResponse], tags=["Signals"])
async def list_signals(
    db: AsyncSession = Depends(get_db),
) -> list[SignalResponse]:
    """Return all signals with latest values and quality metadata."""
    signals = await get_all_signals(db)
    return [SignalResponse.model_validate(s) for s in signals]


@router.get("/v1/signals/{signal_id}", response_model=SignalDetailResponse, tags=["Signals"])
async def get_signal_detail(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
) -> SignalDetailResponse:
    """Return a single signal with 90-day history."""
    signal = await get_signal_by_id(db, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found")

    # Build mock history (in Sprint 2 we'll use a dedicated history table)
    history: list[SignalHistoryPoint] = []

    response = SignalDetailResponse.model_validate(signal)
    response.history = history
    return response


@router.get("/v1/quality", response_model=list[QualityResponse], tags=["Quality"])
async def list_quality(
    db: AsyncSession = Depends(get_db),
) -> list[QualityResponse]:
    """Return quality badges for all signals."""
    signals = await get_all_signals(db)
    return [QualityResponse.model_validate(s) for s in signals]


@router.get("/healthz", response_model=HealthResponse, tags=["Health"])
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> HealthResponse:
    """Service health check — verifies DB and Redis connectivity."""
    health = HealthResponse(status="ok", version="0.1.0")

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        health.db_connected = result.scalar() == 1

        count_result = await db.execute(select(func.count()).select_from(Signal))
        health.signal_count = count_result.scalar_one_or_none() or 0
    except Exception:
        logger.exception("Health check: DB connection failed")
        health.db_connected = False

    # Check Redis
    try:
        redis = await get_redis()
        pong = await redis.ping()
        health.redis_connected = pong
    except Exception:
        logger.exception("Health check: Redis connection failed")
        health.redis_connected = False

    if not health.db_connected or not health.redis_connected:
        health.status = "degraded"

    return health
