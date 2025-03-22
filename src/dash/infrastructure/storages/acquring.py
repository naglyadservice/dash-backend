from datetime import datetime

from redis.asyncio import Redis


class AcquringStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.monopay_pub_key = "monopay:pub_key"
        self.modified_date_key = "monopay:modified_date:{invoice_id}"

    async def get_monopay_pub_key(self) -> bytes | None:
        return await self.redis.get(self.monopay_pub_key)

    async def set_monopay_pub_key(self, pub_key: bytes) -> None:
        await self.redis.set(self.monopay_pub_key, pub_key, ex=60 * 60 * 24 * 30)

    async def set_last_modified_date(
        self, invoice_id: str, last_modified_date: datetime
    ) -> None:
        await self.redis.set(
            self.modified_date_key.format(invoice_id=invoice_id),
            last_modified_date.isoformat(),
            ex=60 * 60 * 24 * 30,
        )

    async def get_last_modified_date(self, invoice_id: str) -> datetime | None:
        last_modified_date = await self.redis.get(
            self.modified_date_key.format(invoice_id=invoice_id)
        )
        if not last_modified_date:
            return None

        return datetime.fromisoformat(last_modified_date.decode())
