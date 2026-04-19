"""News sentiment service — headline scoring and aggregation.

Scores headlines using a keyword/heuristic approach (no external NLP dependency)
and classifies as STRESS / NEUTRAL / RELIEF.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Stress/relief keyword dictionaries for scoring
STRESS_WORDS = {
    "crisis": -0.7, "crash": -0.8, "collapse": -0.9, "default": -0.7,
    "recession": -0.6, "panic": -0.8, "plunge": -0.7, "selloff": -0.6,
    "sell-off": -0.6, "contagion": -0.7, "bank run": -0.9, "bankrun": -0.9,
    "liquidity crunch": -0.8, "credit freeze": -0.8, "margin call": -0.7,
    "downgrade": -0.5, "warning": -0.4, "risk": -0.3, "volatile": -0.4,
    "volatility": -0.3, "fears": -0.5, "concern": -0.3, "turmoil": -0.6,
    "slump": -0.5, "decline": -0.3, "losses": -0.4, "tumble": -0.5,
    "uncertainty": -0.3, "inflation": -0.3, "stagflation": -0.7,
    "insolvency": -0.8, "bankruptcy": -0.8, "bailout": -0.5,
    "rate hike": -0.3, "hawkish": -0.3, "tightening": -0.3,
}

RELIEF_WORDS = {
    "rally": 0.6, "surge": 0.5, "recovery": 0.7, "rebound": 0.6,
    "stabilize": 0.5, "stable": 0.4, "calm": 0.5, "easing": 0.4,
    "stimulus": 0.5, "rescue": 0.4, "support": 0.3, "boost": 0.4,
    "growth": 0.4, "optimism": 0.5, "confidence": 0.4, "resilient": 0.5,
    "dovish": 0.4, "rate cut": 0.5, "accommodation": 0.4,
    "earnings beat": 0.5, "upgrade": 0.4, "bullish": 0.5,
    "all-time high": 0.4, "record high": 0.3,
}

# Crisis category keywords
CATEGORY_KEYWORDS = {
    "BANKING": ["bank", "credit", "lending", "deposit", "loan", "mortgage", "financial institution", "fdic"],
    "MARKET": ["stock", "equity", "market", "index", "s&p", "dow", "nasdaq", "trading"],
    "LIQUIDITY": ["liquidity", "repo", "funding", "cash", "reserve", "money market", "treasury"],
    "MACRO": ["fed", "central bank", "gdp", "inflation", "employment", "policy", "rate"],
}


def score_headline(headline: str) -> float:
    """Score a headline from -1.0 (stress) to +1.0 (relief)."""
    text = headline.lower()
    score = 0.0
    count = 0

    for phrase, weight in STRESS_WORDS.items():
        if phrase in text:
            score += weight
            count += 1

    for phrase, weight in RELIEF_WORDS.items():
        if phrase in text:
            score += weight
            count += 1

    if count == 0:
        return 0.0

    # Normalize
    return max(-1.0, min(1.0, score / max(count, 1)))


def classify_sentiment(score: float) -> str:
    """Classify score into STRESS / NEUTRAL / RELIEF."""
    if score <= -0.2:
        return "STRESS"
    elif score >= 0.2:
        return "RELIEF"
    return "NEUTRAL"


def tag_category(headline: str) -> str:
    """Tag headline with most relevant crisis category."""
    text = headline.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in text)

    if max(scores.values()) == 0:
        return "MACRO"
    return max(scores, key=scores.get)


# Pre-built realistic headlines for demo
MOCK_HEADLINES: list[dict] = [
    {
        "headline": "Fed signals potential rate pause amid banking sector concerns",
        "source": "Reuters",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": -0.15,
        "classification": "NEUTRAL",
        "category": "MACRO",
    },
    {
        "headline": "Regional bank stocks tumble as deposit outflows accelerate",
        "source": "Bloomberg",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": -0.65,
        "classification": "STRESS",
        "category": "BANKING",
    },
    {
        "headline": "Treasury yields surge to 16-year high on hawkish Fed commentary",
        "source": "CNBC",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": -0.45,
        "classification": "STRESS",
        "category": "MACRO",
    },
    {
        "headline": "VIX spikes above 25 amid growing recession fears",
        "source": "MarketWatch",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": -0.55,
        "classification": "STRESS",
        "category": "MARKET",
    },
    {
        "headline": "Gold rallies to 6-month high as safe-haven demand surges",
        "source": "Financial Times",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": 0.35,
        "classification": "RELIEF",
        "category": "MARKET",
    },
    {
        "headline": "ECB announces additional liquidity facility for European banks",
        "source": "Reuters",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": 0.45,
        "classification": "RELIEF",
        "category": "BANKING",
    },
    {
        "headline": "Credit spreads widen to widest level since March 2023",
        "source": "Bloomberg",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": -0.60,
        "classification": "STRESS",
        "category": "BANKING",
    },
    {
        "headline": "S&P 500 drops 2.3% in worst session since Silicon Valley Bank collapse",
        "source": "CNBC",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": -0.70,
        "classification": "STRESS",
        "category": "MARKET",
    },
    {
        "headline": "Money market fund inflows hit record as investors seek safety",
        "source": "Financial Times",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": -0.30,
        "classification": "STRESS",
        "category": "LIQUIDITY",
    },
    {
        "headline": "FDIC reassures depositors amid regional banking turbulence",
        "source": "Wall Street Journal",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "score": 0.25,
        "classification": "RELIEF",
        "category": "BANKING",
    },
]


class SentimentService:
    """Manages news sentiment scoring and aggregation."""

    def __init__(self) -> None:
        self._headlines: list[dict] = list(MOCK_HEADLINES)

    def get_latest_headlines(self, limit: int = 10) -> list[dict]:
        """Get latest scored headlines."""
        return self._headlines[:limit]

    def get_daily_sentiment(self) -> dict:
        """Get aggregated daily sentiment score."""
        if not self._headlines:
            return {"score": 0.0, "classification": "NEUTRAL", "headline_count": 0}

        avg_score = sum(h["score"] for h in self._headlines) / len(self._headlines)
        stress_count = sum(1 for h in self._headlines if h["classification"] == "STRESS")
        relief_count = sum(1 for h in self._headlines if h["classification"] == "RELIEF")

        return {
            "score": round(avg_score, 3),
            "classification": classify_sentiment(avg_score),
            "headline_count": len(self._headlines),
            "stress_headlines": stress_count,
            "relief_headlines": relief_count,
            "neutral_headlines": len(self._headlines) - stress_count - relief_count,
        }

    def get_sentiment_history(self, days: int = 7) -> list[dict]:
        """Get sentiment trend over past N days (synthetic for demo)."""
        import random
        from datetime import timedelta

        history = []
        base_score = -0.25  # Slightly stressed
        now = datetime.now(timezone.utc)

        for i in range(days, 0, -1):
            day = now - timedelta(days=i)
            noise = random.uniform(-0.2, 0.2)
            # Trend: gradually worsening
            trend = -0.03 * (days - i)
            score = max(-1.0, min(1.0, base_score + noise + trend))
            history.append({
                "date": day.strftime("%Y-%m-%d"),
                "score": round(score, 3),
                "classification": classify_sentiment(score),
                "headline_count": random.randint(8, 25),
            })

        return history


# Singleton
sentiment_service = SentimentService()
