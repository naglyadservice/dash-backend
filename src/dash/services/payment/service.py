from typing import Sequence

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.payment import Payment
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.payment.dto import (GetPaymentStatsRequest,
                                       GetPaymentStatsResponse, PaymentScheme,
                                       ReadPaymentListRequest,
                                       ReadPaymentListResponse)


class PaymentService:
    def __init__(
        self,
        identity_provider: IdProvider,
        payment_repository: PaymentRepository,
        location_repository: LocationRepository,
        controller_repository: ControllerRepository,
    ):
        self.identity_provider = identity_provider
        self.payment_repository = payment_repository
        self.location_repository = location_repository
        self.controller_repository = controller_repository

    async def _get_payments_by_role(
        self, data: ReadPaymentListRequest, user: AdminUser
    ) -> tuple[Sequence[Payment], int]:
        match user.role:
            case AdminRole.SUPERADMIN:
                return await self.payment_repository.get_list_all(data)
            case AdminRole.COMPANY_OWNER:
                return await self.payment_repository.get_list_by_owner(data, user.id)
            case AdminRole.LOCATION_ADMIN:
                return await self.payment_repository.get_list_by_admin(data, user.id)
            case _:
                raise AccessForbiddenError

    async def read_payments(
        self, data: ReadPaymentListRequest
    ) -> ReadPaymentListResponse:
        user = await self.identity_provider.authorize()

        if data.controller_id:
            controller = await self.controller_repository.get(data.controller_id)
            await self.identity_provider.ensure_location_admin(
                controller and controller.location_id
            )
            payments, total = await self.payment_repository.get_list_all(data)

        elif data.location_id:
            await self.identity_provider.ensure_location_admin(data.location_id)
            payments, total = await self.payment_repository.get_list_all(data)
        else:
            payments, total = await self._get_payments_by_role(data, user)

        return ReadPaymentListResponse(
            payments=[PaymentScheme.model_validate(payment) for payment in payments],
            total=total,
        )

    async def get_stats(self, data: GetPaymentStatsRequest) -> GetPaymentStatsResponse:
        user = await self.identity_provider.authorize()

        if data.company_id:
            await self.identity_provider.ensure_company_owner(data.company_id)

        elif data.location_id:
            await self.identity_provider.ensure_location_admin(data.location_id)

        elif data.controller_id:
            controller = await self.controller_repository.get(data.controller_id)
            await self.identity_provider.ensure_location_admin(
                controller and controller.location_id
            )

        else:
            if user.role is AdminRole.COMPANY_OWNER:
                return await self.payment_repository.get_stats_by_owner(data, user.id)
            elif user.role is AdminRole.LOCATION_ADMIN:
                return await self.payment_repository.get_stats_by_admin(data, user.id)

        return await self.payment_repository.get_stats(data)
