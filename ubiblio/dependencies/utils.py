from fastapi import Depends, Request
from fastapi_limiter.depends import RateLimiter

from ..vars import USE_REDIS

CHUNK_SIZE = 1024 * 1024


def get_rate_limiter(times: int, seconds: int):
    if USE_REDIS:
        return Depends(RateLimiter(times, seconds))
    else:
        return Depends(lambda: None)


async def get_body(request: Request):
    return await request.body()
