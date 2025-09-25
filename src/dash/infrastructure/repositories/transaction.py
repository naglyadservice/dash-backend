from datetime import UTC, datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, Date, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectin_polymorphic

from dash.infrastructure.repositories.base import BaseRepository
from dash.infrastructure.repositories.utils import parse_model_fields
from dash.models import CarwashTransaction, VacuumTransaction
from dash.models.company import Company
from dash.models.controllers.controller import Controller
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.models.transactions.car_cleaner import CarCleanerTransaction
from dash.models.transactions.fiscalizer import FiscalizerTransaction
from dash.models.transactions.laundry import LaundrySessionStatus, LaundryTransaction
from dash.models.transactions.transaction import Transaction
from dash.models.transactions.water_vending import WsmTransaction
from dash.services.dashboard.dto import (
    GetRevenueRequest,
    RevenueDTO,
    ReadTransactionStatsRequest,
    TransactionStatsDTO,
    TodayClientsDTO,
)
from dash.services.transaction.dto import (
    ReadTransactionListRequest,
)


class TransactionRepository(BaseRepository):
    async def insert_with_conflict_ignore(self, model: Transaction) -> bool:
        base_cols = parse_model_fields(model, Transaction)

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

        await self.session.execute(
            insert(type(model)).values(
                transaction_id=inserted_id,
                **parse_model_fields(model, type(model)),
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
            Transaction,
            [
                WsmTransaction,
                CarwashTransaction,
                FiscalizerTransaction,
                LaundryTransaction,
                VacuumTransaction,
                CarCleanerTransaction,
            ],
        )

        stmt = select(Transaction).options(loader_opt)

        if data.date_from:
            stmt = stmt.where(Transaction.created_at >= data.date_from)

        if data.date_to:
            stmt = stmt.where(Transaction.created_at <= data.date_to)

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
        data: ReadTransactionStatsRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> list[TransactionStatsDTO]:
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
                    + Transaction.card_amount
                ).label("total"),
                func.sum(Transaction.bill_amount).label("bill"),
                func.sum(Transaction.coin_amount).label("coin"),
                func.sum(Transaction.qr_amount).label("qr"),
                func.sum(Transaction.paypass_amount).label("paypass"),
                func.sum(Transaction.card_amount).label("card"),
            )
            .where(
                Transaction.created_at >= data.date_from,
                Transaction.created_at <= data.date_to,
            )
            .group_by(date_expression)
            .order_by(date_expression)
        )

        if data.company_id:
            stmt = stmt.join(Controller).where(Controller.company_id == data.company_id)

        if data.location_id:
            stmt = stmt.where(Transaction.location_id == data.location_id)

        if data.controller_id:
            stmt = stmt.where(Transaction.controller_id == data.controller_id)

        if whereclause is not None:
            stmt = stmt.where(whereclause)

        result = await self.session.execute(stmt)
        rows = result.mappings().fetchall()

        return [TransactionStatsDTO.model_validate(row) for row in rows]

    async def get_stats_all(
        self, data: ReadTransactionStatsRequest
    ) -> list[TransactionStatsDTO]:
        return await self._get_stats(data)

    async def get_stats_by_owner(
        self, data: ReadTransactionStatsRequest, user_id: UUID
    ) -> list[TransactionStatsDTO]:
        whereclause = Transaction.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_stats(data, whereclause)

    async def get_stats_by_admin(
        self, data: ReadTransactionStatsRequest, user_id: UUID
    ) -> list[TransactionStatsDTO]:
        whereclause = Transaction.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_stats(data, whereclause)

    async def _get_revenue(
        self,
        data: GetRevenueRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> RevenueDTO:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_revenue_query = select(
            func.coalesce(
                func.sum(
                    Transaction.bill_amount
                    + Transaction.coin_amount
                    + Transaction.qr_amount
                    + Transaction.paypass_amount
                    + Transaction.card_amount
                ),
                0,
            ).label("total_revenue")
        )

        today_revenue_query = select(
            func.coalesce(
                func.sum(
                    Transaction.bill_amount
                    + Transaction.coin_amount
                    + Transaction.qr_amount
                    + Transaction.paypass_amount
                    + Transaction.card_amount
                ),
                0,
            ).label("today_revenue")
        ).where(Transaction.created_at >= today_start)

        if data.company_id:
            total_revenue_query = total_revenue_query.join(Controller).where(
                Controller.company_id == data.company_id
            )
            today_revenue_query = today_revenue_query.join(Controller).where(
                Controller.company_id == data.company_id
            )
        elif data.location_id:
            total_revenue_query = total_revenue_query.where(
                Transaction.location_id == data.location_id
            )
            today_revenue_query = today_revenue_query.where(
                Transaction.location_id == data.location_id
            )
        elif data.controller_id:
            total_revenue_query = total_revenue_query.where(
                Transaction.controller_id == data.controller_id
            )
            today_revenue_query = today_revenue_query.where(
                Transaction.controller_id == data.controller_id
            )
        elif whereclause is not None:
            total_revenue_query = total_revenue_query.where(whereclause)
            today_revenue_query = today_revenue_query.where(whereclause)

        total_result = await self.session.execute(total_revenue_query)
        today_result = await self.session.execute(today_revenue_query)

        total_revenue = total_result.scalar() or 0
        today_revenue = today_result.scalar() or 0

        return RevenueDTO(total=total_revenue, today=today_revenue)

    async def get_revenue_all(self, data: GetRevenueRequest) -> RevenueDTO:
        return await self._get_revenue(data)

    async def get_revenue_by_owner(
        self, data: GetRevenueRequest, user_id: UUID
    ) -> RevenueDTO:
        whereclause = Transaction.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_revenue(data, whereclause)

    async def get_revenue_by_admin(
        self, data: GetRevenueRequest, user_id: UUID
    ) -> RevenueDTO:
        whereclause = Transaction.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_revenue(data, whereclause)

    async def _get_today_clients(
        self,
        data: GetRevenueRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> TodayClientsDTO:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        query = select(func.count(Transaction.id)).where(
            Transaction.created_at >= today_start, Transaction.created_at <= now
        )

        if data.company_id:
            query = query.join(Controller).where(
                Controller.company_id == data.company_id
            )
        elif data.location_id:
            query = query.where(Transaction.location_id == data.location_id)
        elif data.controller_id:
            query = query.where(Transaction.controller_id == data.controller_id)
        elif whereclause is not None:
            query = query.where(whereclause)

        result = await self.session.execute(query)
        count = result.scalar() or 0

        return TodayClientsDTO(count=count)

    async def get_today_clients_all(self, data: GetRevenueRequest) -> TodayClientsDTO:
        return await self._get_today_clients(data)

    async def get_today_clients_by_owner(
        self, data: GetRevenueRequest, user_id: UUID
    ) -> TodayClientsDTO:
        whereclause = Transaction.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_today_clients(data, whereclause)

    async def get_today_clients_by_admin(
        self, data: GetRevenueRequest, user_id: UUID
    ) -> TodayClientsDTO:
        whereclause = Transaction.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_today_clients(data, whereclause)

    async def get_laundry_active(
        self, controller_id: UUID
    ) -> LaundryTransaction | None:
        query = (
            select(LaundryTransaction)
            .where(
                LaundryTransaction.controller_id == controller_id,
                LaundryTransaction.session_status.in_(
                    (
                        LaundrySessionStatus.WAITING_START,
                        LaundrySessionStatus.IN_PROGRESS,
                    )
                ),
            )
            .order_by(LaundryTransaction.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(query)

    async def get_laundry(self, transaction_id: UUID) -> LaundryTransaction | None:
        return await self.session.get(LaundryTransaction, transaction_id)
