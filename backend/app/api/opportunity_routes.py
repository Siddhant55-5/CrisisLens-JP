"""Opportunity intelligence + sentiment API routes.

GET /v1/opportunities/inverse      — top inverse pairs
GET /v1/opportunities/defensive    — complementary assets by crisis type
GET /v1/opportunities/watchlist    — merged watchlist (top 6)
GET /v1/sentiment                  — latest headlines + aggregate score
GET /v1/sentiment/history          — sentiment trend over N days
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from opportunities.inverse_pairs import inverse_pair_engine
from opportunities.asset_engine import asset_engine
from opportunities.sentiment_service import sentiment_service

router = APIRouter(prefix="/v1", tags=["opportunities"])


@router.get("/opportunities/inverse")
async def get_inverse_pairs(
    crisis_type: str | None = Query(None),
    limit: int = Query(5, ge=1, le=10),
):
    """Get top inverse pair opportunities."""
    pairs = await inverse_pair_engine.get_inverse_pairs(crisis_type, limit)
    return {"pairs": pairs}


@router.get("/opportunities/defensive")
async def get_defensive_assets(
    crisis_type: str = Query("BANKING_INSTABILITY"),
    limit: int = Query(5, ge=1, le=10),
):
    """Get defensive asset recommendations by crisis type."""
    assets = asset_engine.get_defensive_assets(crisis_type, limit)
    return {"crisis_type": crisis_type, "assets": assets}


@router.get("/opportunities/watchlist")
async def get_watchlist(
    crisis_type: str | None = Query(None),
    limit: int = Query(6, ge=1, le=12),
):
    """Get merged opportunity watchlist."""
    watchlist = asset_engine.get_watchlist(crisis_type, limit)
    return {"watchlist": watchlist}


@router.get("/sentiment")
async def get_sentiment(limit: int = Query(10, ge=1, le=50)):
    """Get latest headlines with sentiment scores + aggregate."""
    headlines = sentiment_service.get_latest_headlines(limit)
    aggregate = sentiment_service.get_daily_sentiment()
    return {
        "aggregate": aggregate,
        "headlines": headlines,
    }


@router.get("/sentiment/history")
async def get_sentiment_history(days: int = Query(7, ge=1, le=30)):
    """Get sentiment trend over past N days."""
    history = sentiment_service.get_sentiment_history(days)
    return {"history": history}
