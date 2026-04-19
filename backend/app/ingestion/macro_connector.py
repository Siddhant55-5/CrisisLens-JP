"""Macro Batch Connector — daily cron for ECB sovereign spreads and other macro data.

Signals:
  - IT_DE_10Y_SPREAD (Italy-Germany 10Y sovereign bond spread)
  - ES_DE_10Y_SPREAD (Spain-Germany 10Y sovereign bond spread)
  - DE_10Y (Germany 10Y Bund yield)
  - JP_10Y (Japan 10Y JGB yield)
  - CN_10Y (China 10Y CGB yield)
  - US_BREAKEVEN_5Y (5Y US breakeven inflation)
  - US_BREAKEVEN_10Y (10Y US breakeven inflation)
  - PMI_US_MFG (US ISM Manufacturing PMI)
  - PMI_EU_MFG (EU Manufacturing PMI)
  - PMI_CN_MFG (China Caixin Manufacturing PMI)
  - US_INITIAL_CLAIMS (US Initial Jobless Claims)
  - US_CONT_CLAIMS (US Continuing Claims)
  - US_CPI_YOY (US CPI Year-over-Year)
  - EU_CPI_YOY (EU HICP Year-over-Year)
  - US_RETAIL_SALES (US Retail Sales MoM)
  - US_INDPRO (US Industrial Production MoM)
  - MOVE_INDEX (ICE BofA MOVE Index - bond vol)
  - SKEW_INDEX (CBOE SKEW Index)
  - PUT_CALL_RATIO (CBOE Total Put/Call Ratio)
  - MARGIN_DEBT (NYSE Margin Debt)
  - TED_SPREAD (TED Spread)
  - LIBOR_OIS (LIBOR-OIS Spread)
  - CREDIT_IMPULSE (Global Credit Impulse proxy)
  - FRA_OIS (FRA-OIS Spread)
  - COPPER_GOLD_RATIO (Copper/Gold Ratio)
  - BALTIC_DRY (Baltic Dry Index)
  - SEMI_INDEX (Philadelphia Semiconductor Index)

Runs daily cron at 06:00 UTC. All data is mock with is_mock=True (real ECB
API integration planned for Sprint 2).
"""

from __future__ import annotations

import logging
import random

from app.core.database import async_session_factory
from app.models.signal import SignalCategory
from app.services.signal_service import upsert_signal

logger = logging.getLogger(__name__)

MACRO_SIGNALS: list[dict] = [
    # ── Sovereign Spreads ─────────────────────────────────────────
    {
        "signal_id": "IT_DE_10Y_SPREAD",
        "name": "Italy-Germany 10Y Bond Spread",
        "category": SignalCategory.BOND,
        "source": "ECB/Mock",
        "unit": "bps",
        "description": "Spread between Italian and German 10-year sovereign bonds",
        "mock_range": (120.0, 220.0),
    },
    {
        "signal_id": "ES_DE_10Y_SPREAD",
        "name": "Spain-Germany 10Y Bond Spread",
        "category": SignalCategory.BOND,
        "source": "ECB/Mock",
        "unit": "bps",
        "description": "Spread between Spanish and German 10-year sovereign bonds",
        "mock_range": (70.0, 130.0),
    },
    # ── Global Sovereign Yields ───────────────────────────────────
    {
        "signal_id": "DE_10Y",
        "name": "Germany 10Y Bund Yield",
        "category": SignalCategory.BOND,
        "source": "Mock",
        "unit": "%",
        "description": "German 10-year government bond yield",
        "mock_range": (2.10, 2.80),
    },
    {
        "signal_id": "JP_10Y",
        "name": "Japan 10Y JGB Yield",
        "category": SignalCategory.BOND,
        "source": "Mock",
        "unit": "%",
        "description": "Japanese 10-year government bond yield",
        "mock_range": (0.50, 1.20),
    },
    {
        "signal_id": "CN_10Y",
        "name": "China 10Y CGB Yield",
        "category": SignalCategory.BOND,
        "source": "Mock",
        "unit": "%",
        "description": "Chinese 10-year government bond yield",
        "mock_range": (2.40, 3.10),
    },
    # ── Inflation ─────────────────────────────────────────────────
    {
        "signal_id": "US_BREAKEVEN_5Y",
        "name": "US 5Y Breakeven Inflation",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "%",
        "description": "Market-implied 5-year inflation expectation",
        "mock_range": (2.00, 2.80),
    },
    {
        "signal_id": "US_BREAKEVEN_10Y",
        "name": "US 10Y Breakeven Inflation",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "%",
        "description": "Market-implied 10-year inflation expectation",
        "mock_range": (2.10, 2.60),
    },
    {
        "signal_id": "US_CPI_YOY",
        "name": "US CPI Year-over-Year",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "%",
        "description": "US Consumer Price Index annual change",
        "mock_range": (2.50, 4.00),
    },
    {
        "signal_id": "EU_CPI_YOY",
        "name": "EU HICP Year-over-Year",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "%",
        "description": "Eurozone Harmonized Index of Consumer Prices annual change",
        "mock_range": (2.00, 3.50),
    },
    # ── PMIs ──────────────────────────────────────────────────────
    {
        "signal_id": "PMI_US_MFG",
        "name": "US ISM Manufacturing PMI",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "pts",
        "description": "US manufacturing purchasing managers' index",
        "mock_range": (46.0, 54.0),
    },
    {
        "signal_id": "PMI_EU_MFG",
        "name": "EU Manufacturing PMI",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "pts",
        "description": "Eurozone manufacturing purchasing managers' index",
        "mock_range": (43.0, 52.0),
    },
    {
        "signal_id": "PMI_CN_MFG",
        "name": "China Caixin Manufacturing PMI",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "pts",
        "description": "China Caixin manufacturing purchasing managers' index",
        "mock_range": (49.0, 52.0),
    },
    # ── Labour Market ─────────────────────────────────────────────
    {
        "signal_id": "US_INITIAL_CLAIMS",
        "name": "US Initial Jobless Claims",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "thousands",
        "description": "Weekly initial unemployment insurance claims",
        "mock_range": (200.0, 280.0),
    },
    {
        "signal_id": "US_CONT_CLAIMS",
        "name": "US Continuing Claims",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "thousands",
        "description": "Ongoing unemployment insurance claims",
        "mock_range": (1600.0, 1900.0),
    },
    # ── Real Economy ──────────────────────────────────────────────
    {
        "signal_id": "US_RETAIL_SALES",
        "name": "US Retail Sales MoM",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "%",
        "description": "US retail and food services sales month-over-month",
        "mock_range": (-0.5, 1.5),
    },
    {
        "signal_id": "US_INDPRO",
        "name": "US Industrial Production MoM",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "%",
        "description": "US industrial production month-over-month change",
        "mock_range": (-0.3, 0.8),
    },
    # ── Volatility & Sentiment ────────────────────────────────────
    {
        "signal_id": "MOVE_INDEX",
        "name": "ICE BofA MOVE Index",
        "category": SignalCategory.BOND,
        "source": "Mock",
        "unit": "pts",
        "description": "Bond market volatility index",
        "mock_range": (80.0, 160.0),
    },
    {
        "signal_id": "SKEW_INDEX",
        "name": "CBOE SKEW Index",
        "category": SignalCategory.EQUITY,
        "source": "Mock",
        "unit": "pts",
        "description": "Measures perceived tail risk in S&P 500",
        "mock_range": (120.0, 160.0),
    },
    {
        "signal_id": "PUT_CALL_RATIO",
        "name": "CBOE Total Put/Call Ratio",
        "category": SignalCategory.EQUITY,
        "source": "Mock",
        "unit": "ratio",
        "description": "Ratio of put to call options volume",
        "mock_range": (0.70, 1.30),
    },
    # ── Credit & Liquidity ────────────────────────────────────────
    {
        "signal_id": "MARGIN_DEBT",
        "name": "NYSE Margin Debt",
        "category": SignalCategory.EQUITY,
        "source": "Mock",
        "unit": "B USD",
        "description": "Total margin debt on NYSE",
        "mock_range": (650.0, 800.0),
    },
    {
        "signal_id": "TED_SPREAD",
        "name": "TED Spread",
        "category": SignalCategory.INTERBANK,
        "source": "Mock",
        "unit": "bps",
        "description": "Difference between 3-month LIBOR and 3-month T-Bill rate",
        "mock_range": (10.0, 50.0),
    },
    {
        "signal_id": "LIBOR_OIS",
        "name": "LIBOR-OIS Spread",
        "category": SignalCategory.INTERBANK,
        "source": "Mock",
        "unit": "bps",
        "description": "Spread between LIBOR and overnight index swap rate",
        "mock_range": (5.0, 35.0),
    },
    {
        "signal_id": "CREDIT_IMPULSE",
        "name": "Global Credit Impulse",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "% GDP",
        "description": "Change in new credit as a percentage of GDP",
        "mock_range": (-2.0, 3.0),
    },
    {
        "signal_id": "FRA_OIS",
        "name": "FRA-OIS Spread",
        "category": SignalCategory.INTERBANK,
        "source": "Mock",
        "unit": "bps",
        "description": "Forward rate agreement vs OIS spread — bank stress indicator",
        "mock_range": (3.0, 25.0),
    },
    # ── Cross-Asset ───────────────────────────────────────────────
    {
        "signal_id": "COPPER_GOLD_RATIO",
        "name": "Copper/Gold Ratio",
        "category": SignalCategory.COMMODITY,
        "source": "Mock",
        "unit": "ratio",
        "description": "Ratio of copper to gold price — economic activity proxy",
        "mock_range": (0.15, 0.25),
    },
    {
        "signal_id": "BALTIC_DRY",
        "name": "Baltic Dry Index",
        "category": SignalCategory.MACRO,
        "source": "Mock",
        "unit": "pts",
        "description": "Shipping cost index for raw materials",
        "mock_range": (1200.0, 2500.0),
    },
    {
        "signal_id": "SEMI_INDEX",
        "name": "Philadelphia Semiconductor Index",
        "category": SignalCategory.EQUITY,
        "source": "Mock",
        "unit": "pts",
        "description": "Benchmark index of semiconductor companies",
        "mock_range": (3500.0, 5200.0),
    },
]


async def fetch_macro_signals() -> None:
    """Fetch all macro batch signals (mock data with is_mock=True)."""
    logger.info("Macro connector: starting daily batch fetch")

    async with async_session_factory() as session:
        for sig_def in MACRO_SIGNALS:
            try:
                low, high = sig_def["mock_range"]
                value = round(random.uniform(low, high), 4)

                await upsert_signal(
                    session=session,
                    signal_id=sig_def["signal_id"],
                    raw_value=value,
                    name=sig_def["name"],
                    category=sig_def["category"],
                    source=sig_def["source"],
                    is_mock=True,
                )
                logger.info("Macro %s = %s (mock=True)", sig_def["signal_id"], value)
            except Exception:
                logger.exception("Macro connector: failed for %s", sig_def["signal_id"])

        await session.commit()

    logger.info("Macro connector: daily batch complete (%d signals)", len(MACRO_SIGNALS))
