from redis.asyncio import Redis

from dash.infrastructure.auth.dto import (
    RegisterCustomerRequest,
    StartPasswordResetRequest,
)


class VerificationStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.registration_key = "registration:{}"
        self.reset_key = "password_reset:{}"
        self.registration_ttl = 300
        self.reset_ttl = 300

    async def set_registration_code(
        self, code: str, data: RegisterCustomerRequest
    ) -> None:
        await self.redis.setex(
            name=self.registration_key.format(code),
            time=self.registration_ttl,
            value=data.model_dump_json(),
        )

    async def verify_registration_code(
        self, code: str
    ) -> RegisterCustomerRequest | None:
        raw = await self.redis.get(self.registration_key.format(code))
        if not raw:
            return None
        return RegisterCustomerRequest.model_validate_json(raw)

    async def delete_registration_code(self, code: str) -> None:
        await self.redis.delete(self.registration_key.format(code))

    async def registration_code_exists(self, code: str) -> bool:
        return await self.redis.exists(self.registration_key.format(code)) > 0

    async def set_reset_code(self, code: str, data: StartPasswordResetRequest) -> None:
        await self.redis.setex(
            name=self.reset_key.format(code),
            time=self.reset_ttl,
            value=data.model_dump_json(),
        )

    async def verify_reset_code(self, code: str) -> StartPasswordResetRequest | None:
        raw = await self.redis.get(self.reset_key.format(code))
        if not raw:
            return None
        return StartPasswordResetRequest.model_validate_json(raw)

    async def delete_reset_code(self, code: str) -> None:
        await self.redis.delete(self.reset_key.format(code))
