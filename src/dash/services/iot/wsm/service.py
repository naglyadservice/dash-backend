from uuid import UUID

from structlog import get_logger

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.acquiring.liqpay import LiqpayService
from dash.infrastructure.acquiring.monopay import MonopayService
from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.wsm.client import WsmIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models.controllers.water_vending import WaterVendingController
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.base import BaseIoTService

logger = get_logger()
from dash.services.iot.wsm.dto import SendWsmActionRequest, WsmIoTControllerScheme


class WsmService(BaseIoTService):
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        payment_repository: PaymentRepository,
        liqpay_service: LiqpayService,
        monopay_service: MonopayService,
        checkbox_service: CheckboxService,
        iot_storage: IoTStorage,
        wsm_client: WsmIoTClient,
        check_online_interactor: CheckOnlineInteractor,
    ):
        super().__init__(
            wsm_client,
            identity_provider,
            controller_repository,
            payment_repository,
            liqpay_service,
            monopay_service,
            checkbox_service,
        )
        self.iot_storage = iot_storage
        self.check_online = check_online_interactor

    async def _get_controller(self, controller_id: UUID) -> WaterVendingController:
        controller = await self.controller_repository.get_wsm(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def read_controller(self, data: ControllerID) -> WsmIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return WsmIoTControllerScheme.make(
            model=controller,
            state=await self.iot_storage.get_state(controller.id),
            energy_state=await self.iot_storage.get_energy_state(controller.id),
            is_online=await self.check_online(controller),
        )

    async def send_action(self, data: SendWsmActionRequest) -> None:
        await super().send_action(data)
