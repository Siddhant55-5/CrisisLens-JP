"""Signal model — the core entity in the CrisisLens signal registry.

TimescaleDB hypertable partitioned by freshness_ts.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SignalCategory(str, enum.Enum):
    """Classification categories for financial signals."""

    INTERBANK = "INTERBANK"
    FX = "FX"
    EQUITY = "EQUITY"
    BOND = "BOND"
    COMMODITY = "COMMODITY"
    MACRO = "MACRO"


class Signal(Base):
    """A single financial signal reading with quality metadata.

    This table is converted to a TimescaleDB hypertable partitioned
    on ``freshness_ts`` for efficient time-series queries.
    """

    __tablename__ = "signals"

    signal_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[SignalCategory] = mapped_column(
        Enum(SignalCategory, name="signal_category", create_constraint=True),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # ── Live values ───────────────────────────────────────────────
    raw_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    z_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    pct_change_1d: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)

    # ── Quality metadata ─────────────────────────────────────────
    freshness_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    completeness_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quality_badge: Mapped[str] = mapped_column(
        String(16), nullable=False, default="UNAVAILABLE"
    )
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Signal {self.signal_id} ({self.category.value}): {self.raw_value}>"
