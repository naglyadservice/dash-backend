from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import selectin_polymorphic

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.transactions.transaction import Transaction
from dash.models.transactions.water_vending import WaterVendingTransaction
from dash.services.transaction.dto import ReadTransactionsRequest


class TransactionRepository(BaseRepository):
    async def get_list(
        self, data: ReadTransactionsRequest
    ) -> tuple[Sequence[Transaction], int]:
        loader_opt = selectin_polymorphic(Transaction, [WaterVendingTransaction])

        query = (
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
            .options(loader_opt)
        )
        if data.controller_id is not None:
            query = query.where(Transaction.controller_id == data.controller_id)

        result = await self.session.scalars(query)
        return result.all(), await self._get_count(query.whereclause)

    async def _get_count(self, whereclause: ColumnElement[Any] | None) -> int:
        query = select(func.count()).select_from(Transaction)

        if whereclause is not None:
            query = query.where(whereclause)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def ensure_exists(
        self, transaction_id: int, created: datetime
    ) -> Transaction | None:
        query = select(Transaction).where(
            Transaction.controller_transaction_id == transaction_id,
            Transaction.created_at == created,
        )
        return await self.session.scalar(query)
