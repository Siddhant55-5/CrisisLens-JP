"""FRED Data Connector — fetches macro/interbank signals from the Federal Reserve.

Signals:
  - SOFR (Secured Overnight Financing Rate)
  - DFF (Federal Funds Effective Rate)
  - DGS2 (2-Year Treasury Yield)
  - DGS10 (10-Year Treasury Yield)
  - T10Y2Y (10Y-2Y Yield Curve Spread)
  - BAMLH0A0HYM2 (ICE BofA US High Yield Spread)

Fetches every 15 minutes via APScheduler.
Falls back to mock data if FRED_API_KEY is not set.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.signal import SignalCategory
from app.services.signal_service import upsert_signal

logger = logging.getLogger(__name__)

FRED_SIGNALS: list[dict] = [
    {
        "signal_id": "SOFR",
        "name": "Secured Overnight Financing Rate",
        "category": SignalCategory.INTERBANK,
        "source": "FRED",
        "unit": "%",
        "description": "Benchmark interest rate for dollar-denominated derivatives and loans",
        "mock_range": (5.25, 5.45),
    },
    {
        "signal_id": "DFF",
        "name": "Federal Funds Effective Rate",
        "category": SignalCategory.INTERBANK,
        "source": "FRED",
        "unit": "%",
        "description": "Rate at which banks lend to each other overnight",
        "mock_range": (5.25, 5.50),
    },
    {
        "signal_id": "DGS2",
        "name": "2-Year Treasury Yield",
        "category": SignalCategory.BOND,
        "source": "FRED",
        "unit": "%",
        "description": "Market yield on U.S. Treasury securities at 2-year constant maturity",
        "mock_range": (4.50, 5.10),
    },
    {
        "signal_id": "DGS10",
        "name": "10-Year Treasury Yield",
        "category": SignalCategory.BOND,
        "source": "FRED",
        "unit": "%",
        "description": "Market yield on U.S. Treasury securities at 10-year constant maturity",
        "mock_range": (4.10, 4.70),
    },
    {
        "signal_id": "T10Y2Y",
        "name": "10Y-2Y Yield Curve Spread",
        "category": SignalCategory.BOND,
        "source": "FRED",
        "unit": "%",
        "description": "Spread between 10-year and 2-year Treasury yields — classic recession indicator",
        "mock_range": (-0.50, 0.30),
    },
    {
        "signal_id": "BAMLH0A0HYM2",
        "name": "ICE BofA US High Yield Spread",
        "category": SignalCategory.BOND,
        "source": "FRED",
        "unit": "bps",
        "description": "Option-adjusted spread of high-yield corporate bonds over Treasuries",
        "mock_range": (3.00, 5.50),
    },
]


async def fetch_fred_signals() -> None:
    """Fetch all FRED signals and upsert into the database."""
    logger.info("FRED connector: starting fetch cycle")

    use_live = bool(settings.FRED_API_KEY)
    fred = None

    if use_live:
        try:
            from fredapi import Fred

            fred = Fred(api_key=settings.FRED_API_KEY)
            logger.info("FRED connector: using live API")
        except Exception:
            logger.warning("FRED connector: failed to init fredapi, falling back to mock")
            use_live = False

    async with async_session_factory() as session:
        for sig_def in FRED_SIGNALS:
            try:
                if use_live and fred is not None:
                    series = fred.get_series(sig_def["signal_id"], observation_start="2024-01-01")
                    value = float(series.dropna().iloc[-1]) if len(series.dropna()) > 0 else None
                    is_mock = False
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
                    "FRED %s = %s (mock=%s)", sig_def["signal_id"], value, is_mock
                )
            except Exception:
                logger.exception("FRED connector: failed to fetch %s", sig_def["signal_id"])

        await session.commit()

    logger.info("FRED connector: fetch cycle complete")
