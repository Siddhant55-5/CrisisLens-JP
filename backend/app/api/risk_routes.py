"""Risk scoring and alert API routes.

GET  /v1/scores           — latest 3 risk scores with CI bounds
GET  /v1/scores/history   — 90-day score timeseries (all 3 categories)
GET  /v1/alerts           — paginated alert history (newest first)
GET  /v1/alerts/{id}      — single alert with full SHAP detail
POST /v1/simulate         — simulated scores with signal overrides
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.risk import (
    AlertDetailResponse,
    AlertResponse,
    RiskScoreHistoryPoint,
    RiskScoreResponse,
    ScoreDiff,
    ShapContribution,
    SimulateRequest,
    SimulateResponse,
)
from app.services.alert_service import alert_engine
from app.services.scoring_service import (
    compute_risk_scores,
    get_latest_scores,
    get_score_history,
)

logger = logging.getLogger(__name__)

risk_router = APIRouter()


@risk_router.get("/v1/scores", response_model=list[RiskScoreResponse], tags=["Risk Scores"])
async def list_scores(
    db: AsyncSession = Depends(get_db),
) -> list[RiskScoreResponse]:
    """Return latest risk scores for all 3 crisis types with CI bounds."""
    scores = await get_latest_scores(db)

    if not scores:
        # No scores yet — run a scoring cycle on demand
        logger.info("No scores found, triggering on-demand scoring")
        score_dicts = await compute_risk_scores(session=db)
        return [
            RiskScoreResponse(
                crisis_type=s["crisis_type"],
                score=s["score"],
                ci_lower=s["ci_lower"],
                ci_upper=s["ci_upper"],
                scored_at=s["scored_at"],
            )
            for s in score_dicts
        ]

    return [RiskScoreResponse.model_validate(s) for s in scores]


@risk_router.get(
    "/v1/scores/history",
    response_model=list[RiskScoreHistoryPoint],
    tags=["Risk Scores"],
)
async def scores_history(
    days: int = Query(default=90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> list[RiskScoreHistoryPoint]:
    """Return score timeseries for all 3 crisis categories over N days."""
    history = await get_score_history(db, days=days)
    return [RiskScoreHistoryPoint.model_validate(s) for s in history]


@risk_router.get("/v1/alerts", response_model=list[AlertResponse], tags=["Alerts"])
async def list_alerts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    """Return paginated alert history, newest first."""
    alerts = await alert_engine.get_alerts(db, limit=limit, offset=offset)
    results = []
    for a in alerts:
        actions = a.recommended_actions if isinstance(a.recommended_actions, list) else []
        results.append(
            AlertResponse(
                id=a.id,
                crisis_type=a.crisis_type.value,
                score=a.score,
                ci_lower=a.ci_lower,
                ci_upper=a.ci_upper,
                severity=a.severity.value,
                triggered_at=a.triggered_at,
                recommended_actions=actions,
            )
        )
    return results


@risk_router.get("/v1/alerts/{alert_id}", response_model=AlertDetailResponse, tags=["Alerts"])
async def get_alert_detail(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> AlertDetailResponse:
    """Return a single alert with full SHAP explanations and historical analog."""
    alert = await alert_engine.get_alert_by_id(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    # Parse SHAP contributions from JSONB
    top_shap = []
    if alert.top_shap and isinstance(alert.top_shap, list):
        top_shap = [ShapContribution(**s) for s in alert.top_shap]

    actions = alert.recommended_actions if isinstance(alert.recommended_actions, list) else []

    return AlertDetailResponse(
        id=alert.id,
        crisis_type=alert.crisis_type.value,
        score=alert.score,
        ci_lower=alert.ci_lower,
        ci_upper=alert.ci_upper,
        severity=alert.severity.value,
        triggered_at=alert.triggered_at,
        recommended_actions=actions,
        top_shap=top_shap,
        historical_analog=alert.historical_analog,
    )


@risk_router.post("/v1/simulate", response_model=SimulateResponse, tags=["Simulation"])
async def simulate_scenario(
    request: SimulateRequest,
    db: AsyncSession = Depends(get_db),
) -> SimulateResponse:
    """Simulate risk scores with overridden signal values.

    Returns simulated scores and diff vs current scores.
    """
    # Get current scores
    current_scores_list = await get_latest_scores(db)
    current_map = {s.crisis_type.value if hasattr(s.crisis_type, 'value') else s.crisis_type: s for s in current_scores_list}

    # Run simulation with overrides
    sim_results = await compute_risk_scores(session=db, overrides=request.overrides)

    scores = []
    diffs = []

    for sim in sim_results:
        score_resp = RiskScoreResponse(
            crisis_type=sim["crisis_type"],
            score=sim["score"],
            ci_lower=sim["ci_lower"],
            ci_upper=sim["ci_upper"],
            scored_at=sim["scored_at"],
        )
        scores.append(score_resp)

        current = current_map.get(sim["crisis_type"])
        current_score = current.score if current else 0.0

        diffs.append(
            ScoreDiff(
                crisis_type=sim["crisis_type"],
                current_score=current_score,
                simulated_score=sim["score"],
                delta=round(sim["score"] - current_score, 2),
                ci_lower=sim["ci_lower"],
                ci_upper=sim["ci_upper"],
            )
        )

    return SimulateResponse(scores=scores, diff=diffs)
