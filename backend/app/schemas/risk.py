"""Pydantic v2 schemas for risk scores, alerts, and simulation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShapContribution(BaseModel):
    """A single SHAP feature contribution to a risk score."""

    feature_name: str
    shap_value: float
    direction: str  # "up" or "down"
    rank: int


class HistoricalAnalog(BaseModel):
    """Nearest historical crisis event match."""

    event_name: str
    date: str
    similarity_score: float
    outcome_summary: str


class RiskScoreResponse(BaseModel):
    """Risk score with mandatory confidence interval bounds."""

    model_config = ConfigDict(from_attributes=True)

    crisis_type: str
    score: float
    ci_lower: float  # Required — never returned without bounds
    ci_upper: float  # Required — never returned without bounds
    scored_at: datetime


class RiskScoreHistoryPoint(BaseModel):
    """A single point in score history timeseries."""

    model_config = ConfigDict(from_attributes=True)

    crisis_type: str
    score: float
    ci_lower: float
    ci_upper: float
    scored_at: datetime


class AlertResponse(BaseModel):
    """Alert summary for list endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    crisis_type: str
    score: float
    ci_lower: float
    ci_upper: float
    severity: str
    triggered_at: datetime
    recommended_actions: list[str] = Field(default_factory=list)


class AlertDetailResponse(AlertResponse):
    """Full alert detail with SHAP explanations and historical analog."""

    top_shap: list[ShapContribution] = Field(default_factory=list)
    historical_analog: HistoricalAnalog | None = None


class SimulateRequest(BaseModel):
    """Request body for scenario simulation."""

    overrides: dict[str, float] = Field(
        ...,
        description="Map of signal_id → overridden value",
        examples=[{"VIX": 45.0, "SOFR": 6.5, "DGS10": 5.2}],
    )


class SimulateResponse(BaseModel):
    """Simulation result showing new scores vs current."""

    scores: list[RiskScoreResponse]
    diff: list[ScoreDiff]


class ScoreDiff(BaseModel):
    """Difference between simulated and current score."""

    crisis_type: str
    current_score: float
    simulated_score: float
    delta: float
    ci_lower: float
    ci_upper: float


# Rebuild forward references
SimulateResponse.model_rebuild()
