from datetime import datetime, timedelta
from typing import Any, Sequence

from sqlalchemy import ColumnElement, Date, cast, func, select
from sqlalchemy.orm import aliased, selectin_polymorphic

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.models.transactions.transaction import Transaction
from dash.models.transactions.water_vending import WaterVendingTransaction
from dash.services.transaction.dto import (
    GetTransactionStatsRequest,
    GetTransactionStatsResponse,
    ReadTransactionListRequest,
    TransactionStatDTO,
)


class TransactionRepository(BaseRepository):
    async def _get_list(
        self,
        data: ReadTransactionListRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> tuple[Sequence[Transaction], int]:
        loader_opt = selectin_polymorphic(Transaction, [WaterVendingTransaction])

        stmt = (
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
            .options(loader_opt)
        )
        if whereclause is not None:
            stmt = stmt.where(whereclause)

        if data.controller_id is not None:
            stmt = stmt.where(Transaction.controller_id == data.controller_id)

        elif data.location_id is not None:
            stmt = stmt.where(Transaction.location_id == data.location_id)

        result = await self.session.scalars(stmt)
        return result.unique().all(), await self._get_count(stmt)

    async def get_list_all(
        self, data: ReadTransactionListRequest
    ) -> tuple[Sequence[Transaction], int]:
        return await self._get_list(data)

    async def get_list_by_owner(
        self, data: ReadTransactionListRequest, user_id: int
    ) -> tuple[Sequence[Transaction], int]:
        whereclause = Transaction.location_id.in_(
            select(Location.id).where(Location.owner_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def get_list_by_admin(
        self, data: ReadTransactionListRequest, user_id: int
    ) -> tuple[Sequence[Transaction], int]:
        whereclause = Transaction.location_id.in_(
            select(Location.id)
            .outerjoin(LocationAdmin)
            .where(LocationAdmin.user_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def exists(
        self, transaction_id: int, created: datetime
    ) -> Transaction | None:
        stmt = select(Transaction).where(
            Transaction.controller_transaction_id == transaction_id,
            Transaction.created_at == created,
        )
        return await self.session.scalar(stmt)

    async def get_stats(
        self, data: GetTransactionStatsRequest
    ) -> GetTransactionStatsResponse:
        date_expression = cast(Transaction.created_at, Date).label("date")
        water_vending_t = aliased(WaterVendingTransaction)
        now = datetime.now()

        stmt = (
            select(
                date_expression,
                func.sum(
                    Transaction.bill_amount
                    + Transaction.coin_amount
                    + Transaction.qr_amount
                    + Transaction.paypass_amount
                ).label("total"),
                func.sum(Transaction.bill_amount).label("bill"),
                func.sum(Transaction.coin_amount).label("coin"),
                func.sum(Transaction.qr_amount).label("qr"),
                func.sum(Transaction.paypass_amount).label("paypass"),
                func.sum(water_vending_t.out_liters_1).label("out_liters_1"),
                func.sum(water_vending_t.out_liters_2).label("out_liters_2"),
            )
            .outerjoin(water_vending_t)
            .where(
                Transaction.created_at >= now - timedelta(days=data.period),
                Transaction.created_at <= now,
            )
            .group_by(date_expression)
            .order_by(date_expression)
        )

        if data.location_id:
            stmt = stmt.where(Transaction.location_id == data.location_id)

        if data.controller_id:
            stmt = stmt.where(Transaction.controller_id == data.controller_id)

        result = await self.session.execute(stmt)
        rows = result.mappings().fetchall()

        return GetTransactionStatsResponse(
            statistics=[TransactionStatDTO.model_validate(row) for row in rows]
        )
