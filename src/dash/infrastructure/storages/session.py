from datetime import timedelta

from redis.asyncio import Redis


class SessionStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.session_key = "session:{}"

    async def add_blacklist(self, token: str) -> None:
        await self.redis.setex(
            name=self.session_key.format(token),
            time=timedelta(days=90),
            value=token,
        )

    async def is_blacklisted(self, token: str) -> bool:
        return await self.redis.get(self.session_key.format(token)) is not None
