from typing import Sequence

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.transactions.transaction import Transaction, TransactionType
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.transaction.dto import (
    CarwashTransactionScheme,
    GetTransactionStatsRequest,
    GetTransactionStatsResponse,
    ReadTransactionListRequest,
    ReadTransactionListResponse,
    WsmTransactionScheme,
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

    async def _get_transactions_by_role(
        self, data: ReadTransactionListRequest, user: AdminUser
    ) -> tuple[Sequence[Transaction], int]:
        match user.role:
            case AdminRole.SUPERADMIN:
                return await self.transaction_repository.get_list_all(data)
            case AdminRole.COMPANY_OWNER:
                return await self.transaction_repository.get_list_by_owner(
                    data, user.id
                )
            case AdminRole.LOCATION_ADMIN:
                return await self.transaction_repository.get_list_by_admin(
                    data, user.id
                )
            case _:
                raise AccessForbiddenError

    async def read_transactions(
        self, data: ReadTransactionListRequest
    ) -> ReadTransactionListResponse:
        user = await self.identity_provider.authorize()

        if data.controller_id:
            controller = await self.controller_repository.get(data.controller_id)
            await self.identity_provider.ensure_location_admin(
                controller and controller.location_id
            )
            transactions, total = await self.transaction_repository.get_list_all(data)

        elif data.location_id:
            await self.identity_provider.ensure_location_admin(
                location_id=data.location_id
            )
            transactions, total = await self.transaction_repository.get_list_all(data)
        else:
            transactions, total = await self._get_transactions_by_role(data, user)

        transaction_list = []
        for transaction in transactions:
            if transaction.type is TransactionType.WATER_VENDING:
                transaction_list.append(
                    WsmTransactionScheme.model_validate(transaction)
                )
            elif transaction.type is TransactionType.CARWASH:
                transaction_list.append(
                    CarwashTransactionScheme.model_validate(transaction)
                )
            else:
                raise ValueError("Unknown transaction type")

        return ReadTransactionListResponse(transactions=transaction_list, total=total)

    async def get_stats(
        self, data: GetTransactionStatsRequest
    ) -> GetTransactionStatsResponse:
        user = await self.identity_provider.authorize()

        if data.company_id:
            await self.identity_provider.ensure_company_owner(data.company_id)

        elif data.location_id:
            await self.identity_provider.ensure_location_admin(data.location_id)

        elif data.controller_id:
            controller = await self.controller_repository.get(data.controller_id)
            if not controller:
                raise ControllerNotFoundError
            await self.identity_provider.ensure_location_admin(controller.location_id)

        else:
            if user.role is AdminRole.COMPANY_OWNER:
                return await self.transaction_repository.get_stats_by_owner(
                    data, user.id
                )
            elif user.role is AdminRole.LOCATION_ADMIN:
                return await self.transaction_repository.get_stats_by_admin(
                    data, user.id
                )

        return await self.transaction_repository.get_stats(data)
