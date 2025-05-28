from uuid import UUID

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.models.controllers.water_vending import WaterVendingController
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    ControllerTimeoutError,
)
from dash.services.iot.base import BaseIoTService
from dash.services.iot.dto import ControllerID
from dash.services.iot.wsm.dto import (
    SendWsmActionRequest,
    SetWsmConfigRequest,
    SetWsmSettingsRequest,
    WsmIoTControllerScheme,
)


class WsmService(BaseIoTService):
    def __init__(
        self,
        controller_repository: ControllerRepository,
        identity_provider: IdProvider,
        iot_storage: IotStorage,
        wsm_client: WsmClient,
    ):
        super().__init__(wsm_client, identity_provider, controller_repository)
        self.iot_storage = iot_storage

    async def _get_controller(self, controller_id: UUID) -> WaterVendingController:
        controller = await self.controller_repository.get_wsm(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def update_config(self, data: SetWsmConfigRequest) -> None:
        await super().update_config(data)

    async def update_settings(self, data: SetWsmSettingsRequest) -> None:
        await super().update_settings(data)

    async def read_controller(self, data: ControllerID) -> WsmIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        state = await self.iot_storage.get_state(controller.id)
        energy_state = await self.iot_storage.get_energy_state(controller.id)

        return WsmIoTControllerScheme.make(controller, state, energy_state)

    async def send_action(self, data: SendWsmActionRequest) -> None:
        await super().send_action(data)
