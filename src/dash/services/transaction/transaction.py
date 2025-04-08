from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models.user import UserRole
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.errors.location import LocationNotFoundError
from dash.services.transaction.dto import (
    GetTransactionStatsRequest,
    GetTransactionStatsResponse,
    ReadTransactionListRequest,
    ReadTransactionListResponse,
    WaterVendingTransactionScheme,
)


class TransactionService:
    def __init__(
        self,
        identity_provider: IdProvider,
        transaction_repository: TransactionRepository,
        location_repository: LocationRepository,
        controller_repository: ControllerRepository,
    ):
        self.identity_provider = identity_provider
        self.transaction_repository = transaction_repository
        self.location_repository = location_repository
        self.controller_repository = controller_repository

    async def read_transactions(
        self, data: ReadTransactionListRequest
    ) -> ReadTransactionListResponse:
        user = await self.identity_provider.get_current_user()

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
            transactions, total = await self.transaction_repository.get_list_all(data)
        elif user.role is UserRole.LOCATION_OWNER:
            transactions, total = await self.transaction_repository.get_list_by_owner(
                data, user.id
            )
        elif user.role is UserRole.LOCATION_ADMIN:
            transactions, total = await self.transaction_repository.get_list_by_admin(
                data, user.id
            )
        else:
            raise AccessForbiddenError

        return ReadTransactionListResponse(
            transactions=[
                WaterVendingTransactionScheme.model_validate(
                    transaction, from_attributes=True
                )
                for transaction in transactions
            ],
            total=total,
        )

    async def get_stats(
        self, data: GetTransactionStatsRequest
    ) -> GetTransactionStatsResponse:
        if data.location_id:
            location_id = data.location_id

        if data.controller_id:
            controller = await self.controller_repository.get(data.controller_id)
            if not controller:
                raise ControllerNotFoundError
            location_id = data.location_id

        await self.identity_provider.ensure_location_admin(location_id)
        return await self.transaction_repository.get_stats(data)
