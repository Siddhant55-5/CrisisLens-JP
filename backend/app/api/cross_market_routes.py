"""Cross-market contagion API routes.

Endpoints:
  GET /v1/correlations?window=20D    — correlation matrix
  GET /v1/correlations/regime        — current regime + shift alerts
  GET /v1/cascade?source=CURRENCY    — cascade path from source
  GET /v1/cascade/graph              — full D3 graph JSON
  GET /v1/sector-scorecard           — sector exposure table
"""

from fastapi import APIRouter, Query

from cross_market.correlation_engine import correlation_engine, WINDOWS
from cross_market.regime_detector import regime_detector
from cross_market.cascade_mapper import cascade_mapper

router = APIRouter(prefix="/v1", tags=["cross-market"])


@router.get("/correlations")
async def get_correlations(window: str = Query("20D", enum=WINDOWS)):
    """Get correlation matrix for the specified window."""
    matrix = await correlation_engine.compute_matrix(window)
    return matrix.model_dump()


@router.get("/correlations/regime")
async def get_regime():
    """Get current market regime and any shift alerts."""
    matrix = await correlation_engine.compute_matrix("20D")
    await regime_detector.evaluate(matrix)

    info = regime_detector.get_regime_info()
    info["avg_correlation"] = correlation_engine.get_avg_correlation(matrix)
    return info


@router.get("/cascade")
async def get_cascade(source: str = Query("CURRENCY")):
    """Get cascade propagation path from source asset class."""
    path = cascade_mapper.get_cascade_path(source.upper())
    return {"source": source.upper(), "cascade": path}


@router.get("/cascade/graph")
async def get_cascade_graph(source: str = Query(None)):
    """Get full NetworkX graph as D3-compatible JSON."""
    graph = cascade_mapper.get_full_graph(active_source=source.upper() if source else None)
    return graph


@router.get("/sector-scorecard")
async def get_sector_scorecard(
    alert_id: int | None = Query(None),
    crisis_type: str = Query("BANKING_INSTABILITY"),
):
    """Get sector exposure scorecard for active alert."""
    scorecard = cascade_mapper.get_sector_scorecard(crisis_type)
    return {
        "crisis_type": crisis_type,
        "sectors": scorecard,
    }
