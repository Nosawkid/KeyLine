import time
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import get_settings


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after


async def enforce_rate_limit(redis: Redis, api_key_id: UUID) -> tuple[int, int]:
    settings = get_settings()
    window = int(time.time() // 60)
    key = f"rate-limit:{api_key_id}:{window}"
    async with redis.pipeline(transaction=True) as pipe:
        pipe.incr(key)
        pipe.expire(key, 60, nx=True)
        results = await pipe.execute()
    count = int(results[0])
    remaining = max(0, settings.rate_limit_per_minute - count)
    if count > settings.rate_limit_per_minute:
        raise RateLimitExceeded(60 - (int(time.time()) % 60))
    return remaining, 60 - (int(time.time()) % 60)
