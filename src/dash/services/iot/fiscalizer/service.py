from uuid import UUID

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.fiscalizer.client import FiscalizerIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models.controllers.fiscalizer import FiscalizerController
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.base import BaseIoTService
from dash.services.iot.fiscalizer.dto import (
    FiscalizerIoTControllerScheme,
    SetFiscalizerConfigRequest,
    SetFiscalizerSettingsRequest,
)


class FiscalizerService(BaseIoTService):
    def __init__(
        self,
        controller_repository: ControllerRepository,
        identity_provider: IdProvider,
        iot_storage: IoTStorage,
        fiscalizer_client: FiscalizerIoTClient,
        check_online_interactor: CheckOnlineInteractor,
    ):
        super().__init__(fiscalizer_client, identity_provider, controller_repository)
        self.iot_storage = iot_storage
        self.check_online = check_online_interactor

    async def _get_controller(self, controller_id: UUID) -> FiscalizerController:
        controller = await self.controller_repository.get_fiscalizer(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def update_config(self, data: SetFiscalizerConfigRequest) -> None:
        await super().update_config(data)

    async def update_settings(self, data: SetFiscalizerSettingsRequest) -> None:
        await super().update_settings(data)

    async def read_controller(
        self, data: ControllerID
    ) -> FiscalizerIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return FiscalizerIoTControllerScheme.make(
            model=controller,
            state=await self.iot_storage.get_state(controller.id),
            energy_state=await self.iot_storage.get_energy_state(controller.id),
            is_online=await self.check_online(controller),
        )
