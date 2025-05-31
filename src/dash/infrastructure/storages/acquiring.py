from datetime import datetime

from redis.asyncio import Redis


class AcquiringStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.monopay_pub_key = "monopay:pub_key:{invoice_id}"
        self.modified_date_key = "monopay:modified_date:{invoice_id}"
        self.monopay_token_key = "monopay:token:{invoice_id}"

        self.ttl = 60 * 60 * 24

    async def set_monopay_token(self, token: str, invoice_id: str) -> None:
        await self.redis.set(
            name=self.monopay_token_key.format(invoice_id=invoice_id),
            value=token,
            ex=self.ttl,
        )

    async def get_monopay_token(self, invoice_id: str) -> str | None:
        token = await self.redis.get(
            self.monopay_token_key.format(invoice_id=invoice_id)
        )
        return token.decode("utf-8") if token else None

    async def set_monopay_pub_key(self, pub_key: bytes, invoice_id: str) -> None:
        await self.redis.set(
            name=self.monopay_pub_key.format(invoice_id=invoice_id),
            value=pub_key,
            ex=60 * 60 * 24 * 30,
        )

    async def get_monopay_pub_key(self, invoice_id: str) -> bytes | None:
        return await self.redis.get(self.monopay_pub_key.format(invoice_id=invoice_id))

    async def set_last_modified_date(
        self, invoice_id: str, last_modified_date: datetime
    ) -> None:
        await self.redis.set(
            name=self.modified_date_key.format(invoice_id=invoice_id),
            value=last_modified_date.isoformat(),
            ex=60 * 60 * 24 * 30,
        )

    async def get_last_modified_date(self, invoice_id: str) -> datetime | None:
        last_modified_date = await self.redis.get(
            self.modified_date_key.format(invoice_id=invoice_id)
        )
        if not last_modified_date:
            return None

        return datetime.fromisoformat(last_modified_date.decode())
