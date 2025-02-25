from datetime import timedelta

from redis.asyncio import Redis


class SessionStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.session_key = "session:{}"

    async def add(self, session_id: str, user_id: int) -> None:
        await self.redis.setex(
            name=self.session_key.format(session_id),
            time=timedelta(days=90),
            value=user_id,
        )

    async def get(self, session_id: str | None) -> int | None:
        if not session_id:
            return None

        user_id = await self.redis.get(self.session_key.format(session_id))
        return int(user_id) if user_id else None

    async def delete(self, session_id: str) -> None:
        await self.redis.delete(self.session_key.format(session_id))
