"""Redis connection pool for streams and caching."""

import redis.asyncio as aioredis

from app.core.config import settings

redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the global async Redis connection."""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return redis_pool


async def close_redis() -> None:
    """Cleanly close the Redis connection pool."""
    global redis_pool
    if redis_pool is not None:
        await redis_pool.close()
        redis_pool = None
