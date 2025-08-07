from redis.asyncio import ConnectionPool, Redis

from dash.main.config import RedisConfig


def get_redis_pool(config: RedisConfig) -> ConnectionPool:
    return ConnectionPool(
        host=config.host,
        port=config.port,
        password=config.password,
    )


def get_redis_client(pool: ConnectionPool) -> Redis:
    return Redis.from_pool(pool)
