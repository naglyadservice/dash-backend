from typing import Any, Sequence

from sqlalchemy import ColumnElement, func, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.payment import Payment
from dash.services.payment.dto import ReadPaymentsRequest


class PaymentRepository(BaseRepository):
    async def get_by_invoice_id(self, invoice_id: str) -> Payment | None:
        query = select(Payment).where(Payment.invoice_id == invoice_id)
        return await self.session.scalar(query)

    async def get_list(
        self, data: ReadPaymentsRequest
    ) -> tuple[Sequence[Payment], int]:
        query = (
            select(Payment)
            .order_by(Payment.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
        )
        if data.controller_id is not None:
            query = query.where(Payment.controller_id == data.controller_id)

        result = await self.session.scalars(query)
        return result.all(), await self._get_count(query.whereclause)

    async def _get_count(self, whereclause: ColumnElement[Any] | None) -> int:
        query = select(func.count()).select_from(Payment)

        if whereclause is not None:
            query = query.where(whereclause)

        result = await self.session.execute(query)
        return result.scalar_one()
