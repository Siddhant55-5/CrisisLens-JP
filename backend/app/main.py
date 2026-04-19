"""CrisisLens Backend — FastAPI Application.

Startup sequence:
1. Create database tables (signals + alerts + risk_scores + TimescaleDB hypertables)
2. Train ML models from training data (or load saved models)
3. Seed 40+ signals across all categories
4. Initialize Redis stream consumer groups
5. Start APScheduler for ingestion + ML scoring
6. Run initial data fetch and scoring cycle
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.cross_market_routes import router as cross_market_router
from app.api.risk_routes import risk_router
from app.api.routes import router
from chat.chat_router import router as chat_ws_router
from chat.simulation_router import router as simulation_router
from app.api.opportunity_routes import router as opportunity_router
from app.core.config import settings
from app.core.database import engine
from app.core.redis import close_redis
from app.ingestion.fred_connector import fetch_fred_signals
from app.ingestion.macro_connector import fetch_macro_signals
from app.ingestion.yahoo_connector import fetch_yahoo_signals
from app.models.base import Base
from app.scheduler import start_scheduler, stop_scheduler
from app.services.stream_service import ensure_consumer_groups

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def _init_database() -> None:
    """Create tables and convert to TimescaleDB hypertables."""
    async with engine.begin() as conn:
        # Import all models so Base.metadata picks them up
        import app.models.alert  # noqa: F401
        import app.models.signal  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created (signals, alerts, risk_scores)")

        # Enable TimescaleDB extension
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
            logger.info("TimescaleDB extension enabled")
        except Exception:
            logger.warning("TimescaleDB extension not available — running as plain Postgres")

        # Convert tables to hypertables
        for table, col in [("signals", "freshness_ts"), ("risk_scores", "scored_at")]:
            try:
                await conn.execute(
                    text(
                        f"SELECT create_hypertable('{table}', '{col}', "
                        f"if_not_exists => TRUE, migrate_data => TRUE)"
                    )
                )
                logger.info("Table '%s' converted to hypertable on '%s'", table, col)
            except Exception as e:
                logger.warning("Hypertable creation skipped for '%s': %s", table, e)


def _init_ml_models() -> None:
    """Train or load ML models."""
    from ml.models.ensemble_model import ensemble

    # Try loading saved models first
    if ensemble.load_all():
        logger.info("ML models loaded from saved files")
        return

    # Train from scratch
    logger.info("No saved models found — training from scratch...")
    try:
        metrics = ensemble.train_all(mlflow_tracking_uri=settings.MLFLOW_TRACKING_URI)
        logger.info("ML models trained successfully: %s", metrics)
    except Exception:
        logger.exception("ML model training failed — scoring will return defaults")


async def _seed_and_fetch() -> None:
    """Run initial data ingestion to seed the signal registry."""
    logger.info("Running initial data fetch to seed signals...")
    try:
        await fetch_fred_signals()
        await fetch_yahoo_signals()
        await fetch_macro_signals()
        logger.info("Initial data seed complete")
    except Exception:
        logger.exception("Initial data seed encountered errors")

    # Run initial scoring cycle after data is seeded
    try:
        from app.services.scoring_service import run_scoring_cycle
        await run_scoring_cycle()
        logger.info("Initial risk scoring complete")
    except Exception:
        logger.exception("Initial risk scoring failed")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Application lifespan — startup and shutdown logic."""
    logger.info("🚀 CrisisLens Backend starting up...")

    # 1. Initialize database
    await _init_database()

    # 2. Train / load ML models (sync — runs in thread)
    await asyncio.get_event_loop().run_in_executor(None, _init_ml_models)

    # 3. Initialize Redis streams
    try:
        await ensure_consumer_groups()
        # Also create alert stream consumer groups
        from app.core.redis import get_redis
        r = await get_redis()
        for group in ["dashboard-alerts"]:
            try:
                await r.xgroup_create("alerts.live", group, "0", mkstream=True)
            except Exception:
                pass
    except Exception:
        logger.exception("Redis stream initialization failed")

    # 4. Start scheduler
    start_scheduler()

    # 5. Seed data and run initial scoring (background)
    asyncio.create_task(_seed_and_fetch())

    logger.info("✅ CrisisLens Backend ready")
    yield

    # Shutdown
    logger.info("🔻 CrisisLens Backend shutting down...")
    stop_scheduler()
    await close_redis()
    await engine.dispose()
    logger.info("👋 CrisisLens Backend stopped")


app = FastAPI(
    title="CrisisLens API",
    description="Real-time financial crisis early warning platform with ML risk scoring",
    version="0.5.0",
    lifespan=lifespan,
)

# CORS middleware for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(router)
app.include_router(risk_router)
app.include_router(cross_market_router)
app.include_router(simulation_router)
app.include_router(chat_ws_router)
app.include_router(opportunity_router)


# Replay endpoints
from chat.replay_data import list_replays, get_replay_frames  # noqa: E402


@app.get("/v1/replay")
async def replay_list():
    return list_replays()


@app.get("/v1/replay/{replay_id}/frames")
async def replay_frames(replay_id: str):
    frames = get_replay_frames(replay_id)
    if frames is None:
        from fastapi import HTTPException
        raise HTTPException(404, f"Replay '{replay_id}' not found")
    return frames

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        from app.core.redis import get_redis
        import json as _json
        r = await get_redis()
        score_last_id = "$"
        alert_last_id = "$"
        while True:
            # Read from BOTH streams simultaneously
            messages = await r.xread(
                {"scores.live": score_last_id, "alerts.live": alert_last_id},
                count=20, block=2000
            )
            if messages:
                for stream_name, entries in messages:
                    sname = stream_name.decode('utf-8') if isinstance(stream_name, bytes) else stream_name
                    for msg_id, fields in entries:
                        if sname == "scores.live":
                            score_last_id = msg_id
                            raw = fields.get(b"payload", fields.get("payload", b"[]"))
                            if isinstance(raw, bytes):
                                raw = raw.decode('utf-8')
                            try:
                                data = _json.loads(raw)
                                await websocket.send_json({"type": "score_update", "data": data})
                            except Exception:
                                pass

                        elif sname == "alerts.live":
                            alert_last_id = msg_id

                            def _s(v):
                                if isinstance(v, bytes): return v.decode('utf-8')
                                if v is None: return ""
                                return str(v)

                            alert_data = {
                                "id": _s(fields.get(b"alert_id", fields.get("alert_id", "1"))),
                                "crisis_type": _s(fields.get(b"crisis_type", fields.get("crisis_type", ""))),
                                "score": float(_s(fields.get(b"score", fields.get("score", "0")))),
                                "ci_lower": float(_s(fields.get(b"ci_lower", fields.get("ci_lower", "0")))),
                                "ci_upper": float(_s(fields.get(b"ci_upper", fields.get("ci_upper", "100")))),
                                "severity": _s(fields.get(b"severity", fields.get("severity", ""))),
                                "reason": _s(fields.get(b"reason", fields.get("reason", ""))),
                                "triggered_at": _s(fields.get(b"triggered_at", fields.get("triggered_at", ""))),
                                "recommended_actions": [_s(fields.get(b"reason", fields.get("reason", "")))]
                            }

                            await websocket.send_json({"type": "alert", "data": alert_data})

            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Dashboard WS error: {e}")

