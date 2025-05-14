import json
from datetime import timedelta
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


class IotStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.state_key = "iot:state:{controller_id}"

    async def set_state(self, state: dict[str, Any], controller_id: UUID) -> None:
        await self.redis.setex(
            name=self.state_key.format(controller_id=controller_id),
            value=json.dumps(state),
            time=timedelta(days=1),
        )

    async def get_state(self, controller_id: UUID) -> dict[str, Any] | None:
        state = await self.redis.get(self.state_key.format(controller_id=controller_id))
        if state:
            return json.loads(state)
        return None
