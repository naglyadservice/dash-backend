from datetime import datetime, timedelta
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, Date, case, cast, func, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.company import Company
from dash.models.controllers.controller import Controller
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.models.payment import Payment, PaymentType
from dash.services.payment.dto import (
    GetPaymentStatsRequest,
    GetPaymentStatsResponse,
    PaymentStatDTO,
    ReadPaymentListRequest,
)


class PaymentRepository(BaseRepository):
    async def get_by_invoice_id(self, invoice_id: str) -> Payment | None:
        stmt = select(Payment).where(Payment.invoice_id == invoice_id)
        return await self.session.scalar(stmt)

    async def _get_list(
        self,
        data: ReadPaymentListRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> tuple[Sequence[Payment], int]:
        stmt = select(Payment)

        if data.company_id is not None:
            stmt = stmt.join(Location).where(Location.company_id == data.company_id)

        elif data.controller_id is not None:
            stmt = stmt.where(Payment.controller_id == data.controller_id)

        elif data.location_id is not None:
            stmt = stmt.where(Payment.location_id == data.location_id)

        elif whereclause is not None:
            stmt = stmt.where(whereclause)

        paginated_stmt = (
            stmt.order_by(Payment.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
        )

        paginated = (await self.session.scalars(paginated_stmt)).unique().all()
        total = await self._get_count(stmt)

        return paginated, total

    async def get_list_all(
        self, data: ReadPaymentListRequest
    ) -> tuple[Sequence[Payment], int]:
        return await self._get_list(data)

    async def get_list_by_owner(
        self, data: ReadPaymentListRequest, user_id: UUID
    ) -> tuple[Sequence[Payment], int]:
        whereclause = Payment.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def get_list_by_admin(
        self, data: ReadPaymentListRequest, user_id: UUID
    ) -> tuple[Sequence[Payment], int]:
        whereclause = Payment.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def _get_stats(
        self,
        data: GetPaymentStatsRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> GetPaymentStatsResponse:
        date_expression = cast(Payment.created_at, Date).label("date")
        now = datetime.now()

        stmt = (
            select(
                date_expression,
                func.sum(Payment.amount).label("total"),
                func.sum(
                    case((Payment.type == PaymentType.BILL, Payment.amount), else_=0)
                ).label("bill"),
                func.sum(
                    case((Payment.type == PaymentType.COIN, Payment.amount), else_=0)
                ).label("coin"),
                func.sum(
                    case((Payment.type == PaymentType.PAYPASS, Payment.amount), else_=0)
                ).label("paypass"),
                func.sum(
                    case((Payment.type == PaymentType.MONOPAY, Payment.amount), else_=0)
                ).label("qr"),
                func.sum(
                    case((Payment.type == PaymentType.FREE, Payment.amount), else_=0)
                ).label("free"),
            )
            .where(
                Payment.created_at >= now - timedelta(days=data.period),
                Payment.created_at <= now,
                Payment.status == "COMPLETED",
            )
            .group_by(date_expression)
            .order_by(date_expression)
        )

        if data.company_id:
            stmt = stmt.join(Controller).where(Controller.company_id == data.company_id)

        elif data.location_id:
            stmt = stmt.join(Controller).where(
                Controller.location_id == data.location_id
            )

        elif data.controller_id:
            stmt = stmt.where(Payment.controller_id == data.controller_id)

        elif whereclause is not None:
            stmt = stmt.where(whereclause)

        result = await self.session.execute(stmt)
        rows = result.mappings().fetchall()

        return GetPaymentStatsResponse(
            statistics=[PaymentStatDTO.model_validate(row) for row in rows]
        )

    async def get_stats(self, data: GetPaymentStatsRequest) -> GetPaymentStatsResponse:
        return await self._get_stats(data)

    async def get_stats_by_owner(
        self, data: GetPaymentStatsRequest, user_id: UUID
    ) -> GetPaymentStatsResponse:
        whereclause = Payment.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_stats(data, whereclause)

    async def get_stats_by_admin(
        self, data: GetPaymentStatsRequest, user_id: UUID
    ) -> GetPaymentStatsResponse:
        whereclause = Payment.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_stats(data, whereclause)
