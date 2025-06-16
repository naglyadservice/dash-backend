from uuid import UUID

from redis.asyncio import Redis


class CarwashSessionStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.key = "carwash_session:{controller_id}"

    async def set_session(
        self, controller_id: UUID, customer_id: UUID, ttl: int
    ) -> None:
        await self.redis.setex(
            name=self.key.format(controller_id=controller_id),
            time=ttl,
            value=str(customer_id),
        )

    async def get_session(self, controller_id: UUID) -> UUID | None:
        data = await self.redis.get(self.key.format(controller_id=controller_id))
        if not data:
            return None
        return UUID(data.decode())

    async def delete_session(self, controller_id: UUID) -> None:
        await self.redis.delete(self.key.format(controller_id=controller_id))

    async def is_active(self, controller_id: UUID) -> bool:
        return await self.redis.exists(self.key.format(controller_id=controller_id)) > 0

    async def refresh_ttl(self, controller_id: UUID, ttl: int) -> None:
        await self.redis.expire(
            name=self.key.format(controller_id=controller_id),
            time=ttl,
        )
