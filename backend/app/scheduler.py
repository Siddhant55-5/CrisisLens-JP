"""APScheduler-based scheduler for data ingestion and ML scoring jobs.

Ingestion:
  - FRED connector: every 15 minutes
  - Yahoo Finance connector: every 15 minutes
  - Macro batch connector: daily at 06:00 UTC

ML Scoring:
  - Risk scoring cycle: every 15 minutes (after ingestion)
  - Recalibration: every Sunday 02:00 UTC
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.ingestion.fred_connector import fetch_fred_signals
from app.ingestion.macro_connector import fetch_macro_signals
from app.ingestion.yahoo_connector import fetch_yahoo_signals

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _wrap_async(coro_func):  # type: ignore[no-untyped-def]
    """Wrap an async function so APScheduler can run it."""
    def wrapper():  # type: ignore[no-untyped-def]
        loop = asyncio.get_event_loop()
        loop.create_task(coro_func())
    return wrapper


def start_scheduler() -> None:
    """Configure and start all ingestion + ML scoring jobs."""

    # ── Data Ingestion Jobs ───────────────────────────────────────

    # FRED: every 15 minutes
    scheduler.add_job(
        fetch_fred_signals,
        trigger=IntervalTrigger(minutes=15),
        id="fred_connector",
        name="FRED Data Connector",
        replace_existing=True,
    )

    # Yahoo Finance: every 15 minutes
    scheduler.add_job(
        fetch_yahoo_signals,
        trigger=IntervalTrigger(minutes=15),
        id="yahoo_connector",
        name="Yahoo Finance Connector",
        replace_existing=True,
    )

    # Macro batch: daily at 06:00 UTC
    scheduler.add_job(
        fetch_macro_signals,
        trigger=CronTrigger(hour=6, minute=0),
        id="macro_connector",
        name="Macro Batch Connector",
        replace_existing=True,
    )

    # ── ML Scoring Jobs ──────────────────────────────────────────

    # Risk scoring: every 5 seconds
    async def _run_scoring() -> None:
        from app.services.scoring_service import run_scoring_cycle
        await run_scoring_cycle()

    scheduler.add_job(
        _run_scoring,
        trigger=IntervalTrigger(seconds=5),
        id="risk_scoring",
        name="Risk Scoring Cycle",
        replace_existing=True,
    )

    # Recalibration: every Sunday 02:00 UTC
    async def _run_recalibration() -> None:
        from ml.recalibration import run_recalibration
        await run_recalibration()

    scheduler.add_job(
        _run_recalibration,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="recalibration",
        name="Weekly Model Recalibration",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with 5 jobs (3 ingestion + 2 ML)")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
