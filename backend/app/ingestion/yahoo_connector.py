"""Yahoo Finance Connector — fetches equity, FX, commodity, and volatility signals.

Signals:
  - ^VIX (CBOE Volatility Index)
  - ^GSPC (S&P 500)
  - DX-Y.NYB (US Dollar Index)
  - GC=F (Gold Futures)
  - CL=F (WTI Crude Oil Futures)
  - GBPUSD=X (GBP/USD)
  - EURUSD=X (EUR/USD)

Fetches every 15 minutes via APScheduler.
Falls back to mock data if yfinance fails.
"""

from __future__ import annotations

import logging
import random

from app.core.database import async_session_factory
from app.models.signal import SignalCategory
from app.services.signal_service import upsert_signal

logger = logging.getLogger(__name__)

YAHOO_SIGNALS: list[dict] = [
    {
        "signal_id": "VIX",
        "ticker": "^VIX",
        "name": "CBOE Volatility Index (VIX)",
        "category": SignalCategory.EQUITY,
        "source": "Yahoo Finance",
        "unit": "pts",
        "description": "Market's expectation of 30-day forward-looking volatility",
        "mock_range": (12.0, 35.0),
    },
    {
        "signal_id": "SPX",
        "ticker": "^GSPC",
        "name": "S&P 500 Index",
        "category": SignalCategory.EQUITY,
        "source": "Yahoo Finance",
        "unit": "pts",
        "description": "Benchmark index of 500 large US companies",
        "mock_range": (4800.0, 5500.0),
    },
    {
        "signal_id": "DXY",
        "ticker": "DX-Y.NYB",
        "name": "US Dollar Index (DXY)",
        "category": SignalCategory.FX,
        "source": "Yahoo Finance",
        "unit": "pts",
        "description": "Weighted measure of USD against a basket of foreign currencies",
        "mock_range": (100.0, 108.0),
    },
    {
        "signal_id": "GOLD",
        "ticker": "GC=F",
        "name": "Gold Futures",
        "category": SignalCategory.COMMODITY,
        "source": "Yahoo Finance",
        "unit": "USD/oz",
        "description": "COMEX Gold futures price",
        "mock_range": (1950.0, 2400.0),
    },
    {
        "signal_id": "WTI_OIL",
        "ticker": "CL=F",
        "name": "WTI Crude Oil Futures",
        "category": SignalCategory.COMMODITY,
        "source": "Yahoo Finance",
        "unit": "USD/bbl",
        "description": "NYMEX WTI crude oil futures price",
        "mock_range": (65.0, 90.0),
    },
    {
        "signal_id": "GBPUSD",
        "ticker": "GBPUSD=X",
        "name": "GBP/USD Exchange Rate",
        "category": SignalCategory.FX,
        "source": "Yahoo Finance",
        "unit": "rate",
        "description": "British Pound to US Dollar exchange rate",
        "mock_range": (1.22, 1.32),
    },
    {
        "signal_id": "EURUSD",
        "ticker": "EURUSD=X",
        "name": "EUR/USD Exchange Rate",
        "category": SignalCategory.FX,
        "source": "Yahoo Finance",
        "unit": "rate",
        "description": "Euro to US Dollar exchange rate",
        "mock_range": (1.05, 1.12),
    },
]


async def fetch_yahoo_signals() -> None:
    """Fetch all Yahoo Finance signals and upsert into the database."""
    logger.info("Yahoo connector: starting fetch cycle")

    use_live = True
    try:
        import yfinance as yf  # noqa: F401
    except ImportError:
        logger.warning("Yahoo connector: yfinance not available, using mock data")
        use_live = False

    async with async_session_factory() as session:
        for sig_def in YAHOO_SIGNALS:
            try:
                value: float | None = None
                is_mock = False

                if use_live:
                    try:
                        import yfinance as yf

                        ticker = yf.Ticker(sig_def["ticker"])
                        hist = ticker.history(period="5d")
                        if not hist.empty:
                            value = round(float(hist["Close"].iloc[-1]), 4)
                        else:
                            raise ValueError("Empty history")
                    except Exception as e:
                        logger.warning(
                            "Yahoo connector: live fetch failed for %s (%s), using mock",
                            sig_def["signal_id"],
                            e,
                        )
                        use_live_this = False
                    else:
                        use_live_this = True

                    if not use_live_this:
                        low, high = sig_def["mock_range"]
                        value = round(random.uniform(low, high), 4)
                        is_mock = True
                else:
                    low, high = sig_def["mock_range"]
                    value = round(random.uniform(low, high), 4)
                    is_mock = True

                await upsert_signal(
                    session=session,
                    signal_id=sig_def["signal_id"],
                    raw_value=value,
                    name=sig_def["name"],
                    category=sig_def["category"],
                    source=sig_def["source"],
                    is_mock=is_mock,
                )
                logger.info(
                    "Yahoo %s = %s (mock=%s)", sig_def["signal_id"], value, is_mock
                )
            except Exception:
                logger.exception("Yahoo connector: failed to fetch %s", sig_def["signal_id"])

        await session.commit()

    logger.info("Yahoo connector: fetch cycle complete")
