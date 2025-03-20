from datetime import datetime

from sqlalchemy import delete, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.transactions.water_vending import WaterVendingTransaction


class WaterVendingTransactionRepository(BaseRepository):
    async def get_list_by_controller_id(
        self, controller_id: int
    ) -> list[WaterVendingTransaction]:
        query = select(WaterVendingTransaction).where(
            WaterVendingTransaction.controller_id == controller_id
        )
        transactions = await self.session.scalars(query)
        return list(transactions.all())

    async def ensure_exists(
        self, transaction_id: int, created: datetime
    ) -> WaterVendingTransaction | None:
        query = select(WaterVendingTransaction).where(
            WaterVendingTransaction.controller_transaction_id == transaction_id,
            WaterVendingTransaction.created_at == created,
        )
        return await self.session.scalar(query)
