"""Pydantic v2 schemas for Signal API requests and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.signal import SignalCategory


class SignalBase(BaseModel):
    """Shared signal fields."""

    signal_id: str
    name: str
    category: SignalCategory
    description: str | None = None
    source: str | None = None
    unit: str | None = None


class SignalResponse(SignalBase):
    """Full signal response with live values and quality metadata."""

    model_config = ConfigDict(from_attributes=True)

    raw_value: float | None = None
    z_score: float | None = 0.0
    pct_change_1d: float | None = 0.0
    freshness_ts: datetime
    freshness_score: float = 1.0
    completeness_ratio: float = 0.0
    anomaly_flag: bool = False
    quality_badge: str = "UNAVAILABLE"
    is_mock: bool = False
    created_at: datetime
    updated_at: datetime


class SignalDetailResponse(SignalResponse):
    """Signal detail with 90-day history."""

    history: list[SignalHistoryPoint] = Field(default_factory=list)


class SignalHistoryPoint(BaseModel):
    """A single historical data point."""

    model_config = ConfigDict(from_attributes=True)

    raw_value: float | None = None
    z_score: float | None = None
    pct_change_1d: float | None = None
    freshness_ts: datetime
    anomaly_flag: bool = False


# Rebuild to resolve forward references
SignalDetailResponse.model_rebuild()


class QualityResponse(BaseModel):
    """Quality metadata for a single signal."""

    model_config = ConfigDict(from_attributes=True)

    signal_id: str
    name: str
    category: SignalCategory
    freshness_ts: datetime
    freshness_score: float
    completeness_ratio: float
    anomaly_flag: bool
    quality_badge: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"
    db_connected: bool = False
    redis_connected: bool = False
    signal_count: int = 0
