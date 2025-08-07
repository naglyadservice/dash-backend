from datetime import UTC, datetime, timedelta
from typing import Any, Sequence, Type
from uuid import UUID

from sqlalchemy import ColumnElement, Date, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectin_polymorphic

from dash.infrastructure.repositories.base import BaseRepository
from dash.models import CarwashTransaction
from dash.models.base import Base
from dash.models.company import Company
from dash.models.controllers.controller import Controller
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.models.transactions.fiscalizer import FiscalizerTransaction
from dash.models.transactions.transaction import Transaction
from dash.models.transactions.water_vending import WsmTransaction
from dash.services.transaction.dto import (
    GetTransactionStatsRequest,
    GetTransactionStatsResponse,
    ReadTransactionListRequest,
    TransactionStatDTO,
)


def parse_model(instance: Base, model: Type[Base]) -> dict[str, Any]:
    return {
        c.name: getattr(instance, c.name)
        for c in model.__table__.columns
        if hasattr(instance, c.name) and getattr(instance, c.name) is not None
    }


class TransactionRepository(BaseRepository):
    async def insert_with_conflict_ignore(self, model: Base) -> bool:
        base_cols = parse_model(model, Transaction)
        insert_tx = (
            insert(Transaction)
            .values(
                **base_cols,
            )
            .on_conflict_do_nothing(
                constraint="uix_transaction_controller_transaction_id"
            )
            .returning(Transaction.id)
        )
        result = await self.session.execute(insert_tx)
        inserted_id = result.scalar_one_or_none()
        if not inserted_id:
            return False

        child_cols = parse_model(model, type(model))

        await self.session.execute(
            insert(type(model)).values(
                transaction_id=inserted_id,
                **child_cols,
            )
        )
        return True

    async def _get_list(
        self,
        data: ReadTransactionListRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> tuple[
        Sequence[WsmTransaction | CarwashTransaction | FiscalizerTransaction], int
    ]:
        loader_opt = selectin_polymorphic(
            Transaction, [WsmTransaction, CarwashTransaction, FiscalizerTransaction]
        )

        stmt = select(Transaction).options(loader_opt)

        if data.company_id is not None:
            stmt = stmt.join(Location).where(Location.company_id == data.company_id)

        elif data.controller_id is not None:
            stmt = stmt.where(Transaction.controller_id == data.controller_id)

        elif data.location_id is not None:
            stmt = stmt.where(Transaction.location_id == data.location_id)

        elif whereclause is not None:
            stmt = stmt.where(whereclause)

        paginated_stmt = (
            stmt.order_by(Transaction.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
            .order_by(Transaction.created_at.desc())
        )

        paginated = (await self.session.scalars(paginated_stmt)).unique().all()
        total = await self._get_count(stmt)

        return paginated, total  # type: ignore

    async def get_list_all(
        self, data: ReadTransactionListRequest
    ) -> tuple[Sequence[Transaction], int]:
        return await self._get_list(data)

    async def get_list_by_owner(
        self, data: ReadTransactionListRequest, user_id: UUID
    ) -> tuple[Sequence[Transaction], int]:
        whereclause = Transaction.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def get_list_by_admin(
        self, data: ReadTransactionListRequest, user_id: UUID
    ) -> tuple[Sequence[Transaction], int]:
        whereclause = Transaction.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def _get_stats(
        self,
        data: GetTransactionStatsRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> GetTransactionStatsResponse:
        date_expression = cast(Transaction.created_at, Date).label("date")

        now = datetime.now(UTC)

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
            )
            .where(
                Transaction.created_at >= now - timedelta(days=data.period),
                Transaction.created_at <= now,
            )
            .group_by(date_expression)
            .order_by(date_expression)
        )

        if data.company_id:
            stmt = stmt.join(Controller).where(Controller.company_id == data.company_id)

        elif data.location_id:
            stmt = stmt.where(Transaction.location_id == data.location_id)

        elif data.controller_id:
            stmt = stmt.where(Transaction.controller_id == data.controller_id)

        elif whereclause is not None:
            stmt = stmt.where(whereclause)

        result = await self.session.execute(stmt)
        rows = result.mappings().fetchall()

        return GetTransactionStatsResponse(
            statistics=[TransactionStatDTO.model_validate(row) for row in rows]
        )

    async def get_stats(
        self, data: GetTransactionStatsRequest
    ) -> GetTransactionStatsResponse:
        return await self._get_stats(data)

    async def get_stats_by_owner(
        self, data: GetTransactionStatsRequest, user_id: UUID
    ) -> GetTransactionStatsResponse:
        whereclause = Transaction.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_stats(data, whereclause)

    async def get_stats_by_admin(
        self, data: GetTransactionStatsRequest, user_id: UUID
    ) -> GetTransactionStatsResponse:
        whereclause = Transaction.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_stats(data, whereclause)
