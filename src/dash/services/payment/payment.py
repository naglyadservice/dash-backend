from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models.user import UserRole
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.payment.dto import (
    GetPaymentStatsRequest,
    GetPaymentStatsResponse,
    PaymentScheme,
    ReadPaymentListRequest,
    ReadPaymentListResponse,
)


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

    async def read_payments(
        self, data: ReadPaymentListRequest
    ) -> ReadPaymentListResponse:
        user = await self.identity_provider.authorize()

        if data.controller_id:
            controller = await self.controller_repository.get(data.controller_id)
            if not controller:
                raise ControllerNotFoundError
            await self.identity_provider.ensure_location_admin(controller.location_id)

        elif data.location_id:
            await self.identity_provider.ensure_location_admin(
                location_id=data.location_id
            )

        if user.role is UserRole.SUPERADMIN:
            payments, total = await self.payment_repository.get_list_all(data)
        elif user.role is UserRole.COMPANY_OWNER:
            payments, total = await self.payment_repository.get_list_by_owner(
                data, user.id
            )
        elif user.role is UserRole.LOCATION_ADMIN:
            payments, total = await self.payment_repository.get_list_by_admin(
                data, user.id
            )
        else:
            raise AccessForbiddenError

        return ReadPaymentListResponse(
            payments=[
                PaymentScheme.model_validate(payment, from_attributes=True)
                for payment in payments
            ],
            total=total,
        )

    async def get_stats(self, data: GetPaymentStatsRequest) -> GetPaymentStatsResponse:
        if data.location_id:
            location_id = data.location_id

        if data.controller_id:
            controller = await self.controller_repository.get(data.controller_id)
            if not controller:
                raise ControllerNotFoundError
            location_id = controller.location_id

        await self.identity_provider.ensure_location_admin(location_id)
        return await self.payment_repository.get_stats(data)
