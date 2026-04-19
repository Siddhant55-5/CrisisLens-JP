"""Complementary asset engine — returns historically defensive/beneficiary assets per crisis type.

Maps each crisis category to specific instruments with metadata:
win rates, expected direction, confidence, suggested window, and plain-English basis.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Crisis type → list of complementary/defensive assets
DEFENSIVE_ASSETS: dict[str, list[dict]] = {
    "BANKING_INSTABILITY": [
        {
            "ticker": "XLU",
            "name": "Utilities Select Sector SPDR",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.82,
            "historical_win_rate_pct": 78,
            "suggested_window_days": 10,
            "basis": "Utilities outperform during banking stress — regulated cash flows, low credit sensitivity, and dividend stability attract defensive capital.",
        },
        {
            "ticker": "XLP",
            "name": "Consumer Staples Select Sector SPDR",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.79,
            "historical_win_rate_pct": 74,
            "suggested_window_days": 10,
            "basis": "Consumer staples provide recession-resistant earnings. In the 2008 GFC, XLP declined only 28% vs SPX -57%.",
        },
        {
            "ticker": "XLV",
            "name": "Health Care Select Sector SPDR",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.76,
            "historical_win_rate_pct": 72,
            "suggested_window_days": 15,
            "basis": "Healthcare demand is inelastic to credit cycles. Historically outperforms banks by 15-25% during banking crises.",
        },
        {
            "ticker": "TLT",
            "name": "iShares 20+ Year Treasury Bond ETF",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.85,
            "historical_win_rate_pct": 81,
            "suggested_window_days": 5,
            "basis": "Safe-haven inflow during banking stress historically benefits US Treasuries. Flight-to-quality intensifies as credit spreads widen.",
        },
        {
            "ticker": "GLD",
            "name": "SPDR Gold Shares",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.80,
            "historical_win_rate_pct": 76,
            "suggested_window_days": 15,
            "basis": "Gold acts as a store of value during banking crises. Post-Lehman, gold rallied 25% in 6 months.",
        },
    ],
    "MARKET_CRASH": [
        {
            "ticker": "VIXY",
            "name": "ProShares VIX Short-Term Futures ETF",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.88,
            "historical_win_rate_pct": 82,
            "suggested_window_days": 5,
            "basis": "VIX spikes dramatically during market crashes. VIXY captured 50-120% gains during COVID crash (Feb–Mar 2020).",
        },
        {
            "ticker": "SH",
            "name": "ProShares Short S&P500",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.85,
            "historical_win_rate_pct": 79,
            "suggested_window_days": 5,
            "basis": "Inverse S&P 500 ETF — direct hedge against broad equity drawdown. Effective for short-term crisis alpha.",
        },
        {
            "ticker": "GLD",
            "name": "SPDR Gold Shares",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.78,
            "historical_win_rate_pct": 74,
            "suggested_window_days": 10,
            "basis": "Gold benefits from risk-off flows and real rate compression during equity selloffs.",
        },
        {
            "ticker": "UUP",
            "name": "Invesco DB US Dollar Index Bullish Fund",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.75,
            "historical_win_rate_pct": 71,
            "suggested_window_days": 10,
            "basis": "USD strengthens as the global reserve currency during panic. Dollar smile theory — risk-off drives USD demand.",
        },
        {
            "ticker": "FXY",
            "name": "Invesco CurrencyShares Japanese Yen Trust",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.72,
            "historical_win_rate_pct": 68,
            "suggested_window_days": 10,
            "basis": "JPY is a traditional safe-haven currency. Carry trade unwind during crashes drives yen appreciation.",
        },
    ],
    "LIQUIDITY_SHORTAGE": [
        {
            "ticker": "TLT",
            "name": "iShares 20+ Year Treasury Bond ETF",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.86,
            "historical_win_rate_pct": 80,
            "suggested_window_days": 5,
            "basis": "Flight-to-quality drives Treasury demand during liquidity crises. In 2019 repo crisis, TLT gained 8% in 2 weeks.",
        },
        {
            "ticker": "UUP",
            "name": "Invesco DB US Dollar Index Bullish Fund",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.83,
            "historical_win_rate_pct": 77,
            "suggested_window_days": 5,
            "basis": "Global USD funding squeeze drives dollar demand. Eurodollar shortage amplifies USD strength during liquidity events.",
        },
        {
            "ticker": "BIL",
            "name": "SPDR Bloomberg 1-3 Month T-Bill ETF",
            "asset_type": "ETF",
            "expected_direction": "LONG",
            "confidence": 0.90,
            "historical_win_rate_pct": 92,
            "suggested_window_days": 20,
            "basis": "Ultra-short Treasuries as cash equivalent during funding stress. Near-zero duration risk with liquidity premium.",
        },
        {
            "ticker": "EEM",
            "name": "iShares MSCI Emerging Markets ETF",
            "asset_type": "ETF",
            "expected_direction": "SHORT",
            "confidence": 0.80,
            "historical_win_rate_pct": 75,
            "suggested_window_days": 15,
            "basis": "EM equities face capital outflows during USD funding crises. 2018 EM selloff saw EEM drop 20% as dollar surged.",
        },
        {
            "ticker": "FXE",
            "name": "Invesco CurrencyShares Euro Trust",
            "asset_type": "ETF",
            "expected_direction": "SHORT",
            "confidence": 0.74,
            "historical_win_rate_pct": 70,
            "suggested_window_days": 10,
            "basis": "EUR weakens against USD during global liquidity crises as Eurodollar funding dries up.",
        },
    ],
}


class ComplementaryAssetEngine:
    """Returns crisis-type-specific defensive and beneficiary asset recommendations."""

    def get_defensive_assets(
        self,
        crisis_type: str = "BANKING_INSTABILITY",
        limit: int = 5,
    ) -> list[dict]:
        """Get defensive asset recommendations for a crisis type."""
        ct = crisis_type.upper()
        assets = DEFENSIVE_ASSETS.get(ct, DEFENSIVE_ASSETS["BANKING_INSTABILITY"])
        return sorted(assets, key=lambda x: x["confidence"], reverse=True)[:limit]

    def get_watchlist(
        self,
        crisis_type: str | None = None,
        limit: int = 6,
    ) -> list[dict]:
        """Get merged watchlist across crisis types, prioritized by confidence."""
        if crisis_type:
            return self.get_defensive_assets(crisis_type, limit)

        # Merge all and deduplicate by ticker
        all_assets: list[dict] = []
        seen_tickers: set[str] = set()
        for assets in DEFENSIVE_ASSETS.values():
            for a in assets:
                if a["ticker"] not in seen_tickers:
                    seen_tickers.add(a["ticker"])
                    all_assets.append(a)

        return sorted(all_assets, key=lambda x: x["confidence"], reverse=True)[:limit]


# Singleton
asset_engine = ComplementaryAssetEngine()
