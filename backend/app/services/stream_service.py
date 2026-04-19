"""Redis Streams Bus — publishes signal updates for downstream consumers.

On every signal upsert, publishes to Redis Stream "signals.live".
Consumer groups: "ml-pipeline" and "websocket-broadcaster".
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

STREAM_NAME = "signals.live"
CONSUMER_GROUPS = ["ml-pipeline", "websocket-broadcaster"]
MAX_STREAM_LEN = 10_000  # Cap stream at 10k messages


async def ensure_consumer_groups() -> None:
    """Create consumer groups if they don't exist."""
    r = await get_redis()
    for group_name in CONSUMER_GROUPS:
        try:
            await r.xgroup_create(
                name=STREAM_NAME,
                groupname=group_name,
                id="0",
                mkstream=True,
            )
            logger.info("Created consumer group '%s' on stream '%s'", group_name, STREAM_NAME)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug("Consumer group '%s' already exists", group_name)
            else:
                raise


async def publish_signal_update(
    signal_id: str,
    raw_value: float | None,
    z_score: float | None,
    anomaly_flag: bool,
    ts: datetime | None = None,
) -> str | None:
    """Publish a signal update to the Redis stream.

    Returns the stream message ID, or None if publishing fails.
    """
    try:
        r = await get_redis()
        message = {
            "signal_id": signal_id,
            "raw_value": str(raw_value) if raw_value is not None else "",
            "z_score": str(z_score) if z_score is not None else "",
            "anomaly_flag": "1" if anomaly_flag else "0",
            "ts": (ts or datetime.now(timezone.utc)).isoformat(),
        }

        msg_id = await r.xadd(
            name=STREAM_NAME,
            fields=message,
            maxlen=MAX_STREAM_LEN,
            approximate=True,
        )
        logger.debug("Published signal %s to stream: %s", signal_id, msg_id)
        return msg_id
    except Exception:
        logger.exception("Failed to publish signal %s to Redis stream", signal_id)
        return None


async def read_stream_messages(
    group_name: str,
    consumer_name: str,
    count: int = 10,
    block_ms: int = 2000,
) -> list[dict]:
    """Read new messages from the stream for a consumer group."""
    r = await get_redis()
    try:
        messages = await r.xreadgroup(
            groupname=group_name,
            consumername=consumer_name,
            streams={STREAM_NAME: ">"},
            count=count,
            block=block_ms,
        )
        results = []
        if messages:
            for stream_name, entries in messages:
                for msg_id, fields in entries:
                    results.append({"id": msg_id, **fields})
        return results
    except Exception:
        logger.exception("Failed to read from stream group %s", group_name)
        return []
