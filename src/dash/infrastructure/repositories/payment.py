from datetime import UTC, datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, Date, case, cast, func, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.company import Company
from dash.models.controllers.controller import Controller
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.dashboard.dto import (
    GetPaymentAnalyticsRequest,
    PaymentAnalyticsDTO,
    GatewayAnalyticsDTO,
    ReadPaymentStatsRequest,
    PaymentStatsDTO,
)
from dash.services.payment.dto import (
    ReadPaymentListRequest,
    ReadPublicPaymentListRequest,
)


class PaymentRepository(BaseRepository):
    async def get_by_invoice_id(self, invoice_id: str) -> Payment | None:
        stmt = select(Payment).where(Payment.invoice_id == invoice_id)
        return await self.session.scalar(stmt)

    async def get(self, payment_id: UUID) -> Payment | None:
        return await self.session.get(Payment, payment_id)

    async def _get_list(
        self,
        data: ReadPaymentListRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> tuple[Sequence[Payment], int]:
        stmt = select(Payment)

        if data.date_from:
            stmt = stmt.where(Payment.created_at >= data.date_from)

        if data.date_to:
            stmt = stmt.where(Payment.created_at <= data.date_to)

        if data.company_id is not None:
            stmt = stmt.join(Location).where(Location.company_id == data.company_id)

        if data.controller_id is not None:
            stmt = stmt.where(Payment.controller_id == data.controller_id)

        if data.location_id is not None:
            stmt = stmt.where(Payment.location_id == data.location_id)

        if whereclause is not None:
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

    async def get_list_public(
        self, data: ReadPublicPaymentListRequest, limit: int
    ) -> Sequence[Payment]:
        stmt = (
            select(Payment)
            .join(Controller)
            .where(
                Controller.qr == data.qr,
                Payment.receipt_id.isnot(None),
            )
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return (await self.session.scalars(stmt)).unique().all()

    async def _get_stats(
        self,
        data: ReadPaymentStatsRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> list[PaymentStatsDTO]:
        date_expression = cast(Payment.created_at, Date).label("date")
        now = datetime.now(UTC)

        stmt = (
            select(
                date_expression,
                func.sum(Payment.amount).label("total"),
                func.sum(
                    case((Payment.type == PaymentType.CASH, Payment.amount), else_=0)
                ).label("cash"),
                func.sum(
                    case(
                        (Payment.type == PaymentType.CASHLESS, Payment.amount), else_=0
                    )
                ).label("cashless"),
            )
            .where(
                Payment.created_at >= data.date_from,
                Payment.created_at <= data.date_to,
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

        return [PaymentStatsDTO.model_validate(row) for row in rows]

    async def get_stats_all(
        self, data: ReadPaymentStatsRequest
    ) -> list[PaymentStatsDTO]:
        return await self._get_stats(data)

    async def get_stats_by_owner(
        self, data: ReadPaymentStatsRequest, user_id: UUID
    ) -> list[PaymentStatsDTO]:
        whereclause = Payment.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_stats(data, whereclause)

    async def get_stats_by_admin(
        self, data: ReadPaymentStatsRequest, user_id: UUID
    ) -> list[PaymentStatsDTO]:
        whereclause = Payment.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_stats(data, whereclause)

    async def _get_cashless_percentage(
        self,
        data: GetPaymentAnalyticsRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> float:
        now = datetime.now(UTC)

        total_stmt = select(func.count(Payment.id).label("total")).where(
            Payment.type.in_((PaymentType.CASH, PaymentType.CASHLESS)),
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= data.date_from,
            Payment.created_at <= data.date_to,
        )

        cashless_stmt = select(func.count(Payment.id).label("cashless")).where(
            Payment.type == PaymentType.CASHLESS,
            Payment.status == PaymentStatus.COMPLETED,
            Payment.created_at >= data.date_from,
            Payment.created_at <= data.date_to,
        )

        for stmt in [total_stmt, cashless_stmt]:
            if data.company_id:
                stmt = stmt.join(Controller).where(
                    Controller.company_id == data.company_id
                )
            elif data.location_id:
                stmt = stmt.where(Payment.location_id == data.location_id)
            elif data.controller_id:
                stmt = stmt.where(Payment.controller_id == data.controller_id)
            elif whereclause is not None:
                stmt = stmt.where(whereclause)

        total_result = await self.session.execute(total_stmt)
        cashless_result = await self.session.execute(cashless_stmt)

        total_payments = total_result.scalar() or 0
        cashless_payments = cashless_result.scalar() or 0

        if total_payments == 0:
            return 0.0

        return round(((cashless_payments / total_payments) * 100), 2)

    async def get_cashless_percentage_all(
        self, data: GetPaymentAnalyticsRequest
    ) -> float:
        return await self._get_cashless_percentage(data)

    async def get_cashless_percentage_by_owner(
        self, data: GetPaymentAnalyticsRequest, user_id: UUID
    ) -> float:
        whereclause = Payment.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_cashless_percentage(data, whereclause)

    async def get_cashless_percentage_by_admin(
        self, data: GetPaymentAnalyticsRequest, user_id: UUID
    ) -> float:
        whereclause = Payment.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_cashless_percentage(data, whereclause)

    async def _get_gateway_analytics(
        self,
        data: GetPaymentAnalyticsRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> list[GatewayAnalyticsDTO]:
        base_query = select(
            Payment.gateway_type, func.sum(Payment.amount).label("amount")
        ).where(
            Payment.status == PaymentStatus.COMPLETED,
            Payment.type == PaymentType.CASHLESS,
            Payment.created_at >= data.date_from,
            Payment.created_at <= data.date_to,
        )

        if data.company_id:
            base_query = base_query.join(Controller).where(
                Controller.company_id == data.company_id
            )
        elif data.location_id:
            base_query = base_query.where(Payment.location_id == data.location_id)
        elif data.controller_id:
            base_query = base_query.where(Payment.controller_id == data.controller_id)
        elif whereclause is not None:
            base_query = base_query.where(whereclause)

        base_query = base_query.group_by(Payment.gateway_type)

        result = await self.session.execute(base_query)
        gateway_data = result.fetchall()

        total_cashless = sum(row.amount for row in gateway_data)

        gateway_analytics = []
        for row in gateway_data:
            if row.gateway_type and total_cashless > 0:
                percentage = (row.amount / total_cashless) * 100
                gateway_analytics.append(
                    GatewayAnalyticsDTO(
                        gateway_type=row.gateway_type,
                        amount=row.amount,
                        percentage=round(percentage, 2),
                    )
                )

        return gateway_analytics

    async def get_gateway_analytics_all(
        self, data: GetPaymentAnalyticsRequest
    ) -> list[GatewayAnalyticsDTO]:
        return await self._get_gateway_analytics(data)

    async def get_gateway_analytics_by_owner(
        self, data: GetPaymentAnalyticsRequest, user_id: UUID
    ) -> list[GatewayAnalyticsDTO]:
        whereclause = Payment.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_gateway_analytics(data, whereclause)

    async def get_gateway_analytics_by_admin(
        self, data: GetPaymentAnalyticsRequest, user_id: UUID
    ) -> list[GatewayAnalyticsDTO]:
        whereclause = Payment.location_id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_gateway_analytics(data, whereclause)

    async def get_payment_analytics_all(
        self, data: GetPaymentAnalyticsRequest
    ) -> PaymentAnalyticsDTO:
        cashless_percentage = await self.get_cashless_percentage_all(data)
        gateway_analytics = await self.get_gateway_analytics_all(data)
        return PaymentAnalyticsDTO(
            cashless_percentage=cashless_percentage, gateway_analytics=gateway_analytics
        )

    async def get_payment_analytics_by_owner(
        self, data: GetPaymentAnalyticsRequest, user_id: UUID
    ) -> PaymentAnalyticsDTO:
        cashless_percentage = await self.get_cashless_percentage_by_owner(data, user_id)
        gateway_analytics = await self.get_gateway_analytics_by_owner(data, user_id)
        return PaymentAnalyticsDTO(
            cashless_percentage=cashless_percentage, gateway_analytics=gateway_analytics
        )

    async def get_payment_analytics_by_admin(
        self, data: GetPaymentAnalyticsRequest, user_id: UUID
    ) -> PaymentAnalyticsDTO:
        cashless_percentage = await self.get_cashless_percentage_by_admin(data, user_id)
        gateway_analytics = await self.get_gateway_analytics_by_admin(data, user_id)
        return PaymentAnalyticsDTO(
            cashless_percentage=cashless_percentage, gateway_analytics=gateway_analytics
        )
