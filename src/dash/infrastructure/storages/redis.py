from typing import AsyncIterable
from redis.asyncio import Redis

from dash.main.config import RedisConfig


async def get_redis_client(config: RedisConfig) -> AsyncIterable[Redis]:
    async with Redis(
        host=config.host, port=config.port, password=config.password
    ) as redis:
        yield redis
