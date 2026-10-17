import redis.asyncio as redis
from typing import Optional

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        # Default: local Redis instance. Change URL via environment or config as needed.
        _redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None
