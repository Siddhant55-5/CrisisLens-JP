"""Alert model — stores triggered risk alerts with SHAP explanations.

TimescaleDB hypertable partitioned by triggered_at.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CrisisType(str, enum.Enum):
    """Types of crisis the model predicts."""

    BANKING_INSTABILITY = "BANKING_INSTABILITY"
    MARKET_CRASH = "MARKET_CRASH"
    LIQUIDITY_SHORTAGE = "LIQUIDITY_SHORTAGE"


class Alert(Base):
    """A triggered risk alert with explainability data."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crisis_type: Mapped[CrisisType] = mapped_column(
        Enum(CrisisType, name="crisis_type", create_constraint=True),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    ci_lower: Mapped[float] = mapped_column(Float, nullable=False)
    ci_upper: Mapped[float] = mapped_column(Float, nullable=False)

    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity", create_constraint=True),
        nullable=False,
    )

    # SHAP explanations stored as JSON array
    top_shap: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Historical analog match
    historical_analog: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Recommended actions
    recommended_actions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Alert {self.id} {self.crisis_type.value} score={self.score} severity={self.severity.value}>"


class RiskScore(Base):
    """Persisted risk score with confidence intervals."""

    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crisis_type: Mapped[CrisisType] = mapped_column(
        Enum(CrisisType, name="crisis_type", create_constraint=True),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    ci_lower: Mapped[float] = mapped_column(Float, nullable=False)
    ci_upper: Mapped[float] = mapped_column(Float, nullable=False)

    # Feature snapshot used for this score
    feature_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<RiskScore {self.crisis_type.value} score={self.score} [{self.ci_lower}-{self.ci_upper}]>"
