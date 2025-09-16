import asyncio

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models import Controller
from dash.models.admin_user import AdminRole, AdminUser
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.controller.dto import ReadControllerListRequest
from dash.services.dashboard.dto import (
    ReadDashboardStatsRequest,
    ReadDashboardStatsResponse,
    GetPaymentAnalyticsRequest,
    GetRevenueRequest,
    ReadPaymentStatsRequest,
    ReadTransactionStatsRequest,
    ActiveControllersDTO,
    TodayClientsDTO,
)


class DashboardService:
    def __init__(
        self,
        identity_provider: IdProvider,
        transaction_repository: TransactionRepository,
        payment_repository: PaymentRepository,
        controller_repository: ControllerRepository,
        check_online: CheckOnlineInteractor,
    ):
        self.identity_provider = identity_provider
        self.transaction_repository = transaction_repository
        self.payment_repository = payment_repository
        self.controller_repository = controller_repository
        self.check_online = check_online

    async def read_dashboard_stats(
        self, data: ReadDashboardStatsRequest
    ) -> ReadDashboardStatsResponse:
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

        controllers, total = await self._get_controllers_by_role(data, user)

        return ReadDashboardStatsResponse(
            revenue=await self._get_revenue_by_role(data, user),
            payment_analytics=await self._get_payment_analytics_by_role(data, user),
            active_controllers=await self._count_active_controllers(controllers, total),  # type: ignore
            today_clients=await self._get_today_clients_by_role(data, user),
            transaction_stats=await self._get_transaction_stats_by_role(data, user),
            payment_stats=await self._get_payment_stats_by_role(data, user),
        )

    async def _call_by_role(self, user: AdminUser, superadmin_fn, owner_fn, admin_fn):
        """Generic method to call appropriate function based on user role"""
        match user.role:
            case AdminRole.SUPERADMIN:
                return await superadmin_fn()
            case AdminRole.COMPANY_OWNER:
                return await owner_fn(user.id)
            case AdminRole.LOCATION_ADMIN:
                return await admin_fn(user.id)
            case _:
                raise AccessForbiddenError

    async def _get_revenue_by_role(
        self, data: ReadDashboardStatsRequest, user: AdminUser
    ):
        revenue_data = GetRevenueRequest(
            company_id=data.company_id,
            location_id=data.location_id,
            controller_id=data.controller_id,
        )
        return await self._call_by_role(
            user,
            lambda: self.transaction_repository.get_revenue_all(revenue_data),
            lambda user_id: self.transaction_repository.get_revenue_by_owner(
                revenue_data, user_id
            ),
            lambda user_id: self.transaction_repository.get_revenue_by_admin(
                revenue_data, user_id
            ),
        )

    async def _get_payment_analytics_by_role(
        self, data: ReadDashboardStatsRequest, user: AdminUser
    ):
        analytics_data = GetPaymentAnalyticsRequest(
            company_id=data.company_id,
            location_id=data.location_id,
            controller_id=data.controller_id,
            date_from=data.date_from,
            date_to=data.date_to,
        )
        return await self._call_by_role(
            user,
            lambda: self.payment_repository.get_payment_analytics_all(analytics_data),
            lambda user_id: self.payment_repository.get_payment_analytics_by_owner(
                analytics_data, user_id
            ),
            lambda user_id: self.payment_repository.get_payment_analytics_by_admin(
                analytics_data, user_id
            ),
        )

    async def _get_today_clients_by_role(
        self, data: ReadDashboardStatsRequest, user: AdminUser
    ) -> TodayClientsDTO:
        clients_data = GetRevenueRequest(
            company_id=data.company_id,
            location_id=data.location_id,
            controller_id=data.controller_id,
        )
        return await self._call_by_role(
            user,
            lambda: self.transaction_repository.get_today_clients_all(clients_data),
            lambda user_id: self.transaction_repository.get_today_clients_by_owner(
                clients_data, user_id
            ),
            lambda user_id: self.transaction_repository.get_today_clients_by_admin(
                clients_data, user_id
            ),
        )

    async def _get_controllers_by_role(
        self, data: ReadDashboardStatsRequest, user: AdminUser
    ):
        if data.controller_id:
            return [await self.controller_repository.get(data.controller_id)], 1

        controllers_data = ReadControllerListRequest(
            company_id=data.company_id,
            location_id=data.location_id,
        )
        return await self._call_by_role(
            user,
            lambda: self.controller_repository.get_list_all(controllers_data),
            lambda user_id: self.controller_repository.get_list_by_owner(
                controllers_data, user_id
            ),
            lambda user_id: self.controller_repository.get_list_by_admin(
                controllers_data, user_id
            ),
        )

    async def _get_transaction_stats_by_role(
        self, data: ReadDashboardStatsRequest, user: AdminUser
    ):
        stats_request = ReadTransactionStatsRequest(**data.model_dump())
        return await self._call_by_role(
            user,
            lambda: self.transaction_repository.get_stats_all(stats_request),
            lambda user_id: self.transaction_repository.get_stats_by_owner(
                stats_request, user_id
            ),
            lambda user_id: self.transaction_repository.get_stats_by_admin(
                stats_request, user_id
            ),
        )

    async def _get_payment_stats_by_role(
        self, data: ReadDashboardStatsRequest, user: AdminUser
    ):
        stats_request = ReadPaymentStatsRequest(**data.model_dump())
        return await self._call_by_role(
            user,
            lambda: self.payment_repository.get_stats_all(stats_request),
            lambda user_id: self.payment_repository.get_stats_by_owner(
                stats_request, user_id
            ),
            lambda user_id: self.payment_repository.get_stats_by_admin(
                stats_request, user_id
            ),
        )

    async def _count_active_controllers(
        self, controller_list: list[Controller], total: int
    ) -> ActiveControllersDTO:
        results = await asyncio.gather(*[self.check_online(c) for c in controller_list])
        return ActiveControllersDTO(total=total, active=sum(results))
