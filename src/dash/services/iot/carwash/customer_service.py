from decimal import Decimal
from uuid import UUID

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.storages.carwash_session import CarwashSessionStorage
from dash.models.controllers.carwash import CarwashController
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.errors.customer_carwash import (
    CarwashSessionActiveError,
    CarwashSessionNotFoundError,
    InsufficientBalanceError,
)
from dash.services.iot.carwash.customer_dto import (
    FinishCarwashSessionRequest,
    SelectCarwashModeRequest,
    SelectCarwashModeResponse,
    StartCarwashSessionRequest,
)
from dash.services.iot.carwash.service import CarwashService


class CustomerCarwashService:
    def __init__(
        self,
        id_provider: IdProvider,
        controller_repository: ControllerRepository,
        customer_repository: CustomerRepository,
        session_storage: CarwashSessionStorage,
        carwash_service: CarwashService,
    ) -> None:
        self.id_provider = id_provider
        self.controller_repository = controller_repository
        self.customer_repository = customer_repository
        self.session_storage = session_storage
        self.carwash_service = carwash_service

    async def _get_controller(self, controller_id: UUID) -> CarwashController:
        controller = await self.controller_repository.get_carwash(controller_id)
        if not controller:
            raise ControllerNotFoundError
        return controller

    async def start_session(self, data: StartCarwashSessionRequest) -> None:
        customer = await self.id_provider.authorize_customer()

        if await self.session_storage.is_active(data.controller_id):
            raise CarwashSessionActiveError

        amount_uah = Decimal(data.amount / 100)

        if customer.balance < amount_uah:
            raise InsufficientBalanceError

        controller = await self._get_controller(data.controller_id)

        await self.carwash_service.send_free_payment_infra(
            device_id=controller.device_id,
            amount=data.amount,
        )

        customer.balance -= amount_uah
        await self.customer_repository.commit()
        await self.session_storage.set_session(
            data.controller_id, customer.id, controller.time_one_pay
        )

    async def select_mode(
        self, data: SelectCarwashModeRequest
    ) -> SelectCarwashModeResponse:
        customer = await self.id_provider.authorize_customer()

        customer_session = await self.session_storage.get_session(data.controller_id)
        if customer_session != customer.id:
            raise CarwashSessionNotFoundError

        controller = await self._get_controller(data.controller_id)

        await self.carwash_service.send_action_infra(
            device_id=controller.device_id,
            payload=data.mode.model_dump(),
        )
        await self.session_storage.refresh_ttl(
            data.controller_id, controller.time_one_pay
        )

        return SelectCarwashModeResponse(timeout=controller.time_one_pay)

    async def finish_session(self, data: FinishCarwashSessionRequest) -> None:
        customer = await self.id_provider.authorize_customer()
        customer_session = await self.session_storage.get_session(data.controller_id)

        if customer_session != customer.id:
            raise CarwashSessionNotFoundError

        await self.session_storage.delete_session(data.controller_id)
