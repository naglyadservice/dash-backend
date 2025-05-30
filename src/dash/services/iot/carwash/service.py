from typing import Any
from uuid import UUID

from structlog import getLogger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.models import Controller
from dash.models.controllers.carwash import CarwashController
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.base import BaseIoTService
from dash.services.iot.carwash.dto import (
    CarwashIoTControllerScheme,
    SetCarwashConfigRequest,
    SetCarwashSettingsRequest,
)
from dash.services.iot.carwash.utils import (
    decode_service_bit_mask,
    decode_service_int_mask,
    encode_service_bit_mask,
    encode_service_int_mask,
)
from dash.services.iot.dto import ControllerID

logger = getLogger()


class CarwashService(BaseIoTService):
    def __init__(
        self,
        controller_repository: ControllerRepository,
        identity_provider: IdProvider,
        iot_storage: IotStorage,
        carwash_client: CarwashIoTClient,
    ):
        super().__init__(carwash_client, identity_provider, controller_repository)
        self.iot_storage = iot_storage

    async def _get_controller(self, controller_id: UUID) -> CarwashController:
        controller = await self.controller_repository.get_carwash(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def init_controller_settings(self, controller: Controller) -> None:
        config = await self.iot_client.get_config(controller.device_id)
        config.pop("request_id")

        settings = await self.iot_client.get_settings(controller.device_id)
        settings["servicesRelay"] = decode_service_bit_mask(settings["servicesRelay"])
        settings["tariff"] = decode_service_int_mask(settings["tariff"])
        settings["servicesPause"] = decode_service_int_mask(settings["servicesPause"])
        settings["vfdFrequency"] = decode_service_int_mask(settings["vfdFrequency"])
        settings.pop("request_id")

        controller.config = config
        controller.settings = settings

    async def update_config(self, data: SetCarwashConfigRequest) -> None:
        await super().update_config(data)

    async def update_settings(self, data: SetCarwashSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        incoming_settings = data.settings.model_dump(exclude_unset=True)
        controller.settings = {**controller.settings, **incoming_settings}

        await self.iot_client.set_settings(
            device_id=controller.device_id,
            payload=self._prepare_settings_payload(controller.settings),
        )
        await self.controller_repository.commit()

    @staticmethod
    def _prepare_settings_payload(settings: dict[str, Any]) -> dict[str, Any]:
        payload = settings.copy()

        payload["servicesRelay"] = encode_service_bit_mask(payload["servicesRelay"])
        payload["tariff"] = encode_service_int_mask(payload["tariff"])
        payload["servicesPause"] = encode_service_int_mask(payload["servicesPause"])
        payload["vfdFrequency"] = encode_service_int_mask(payload["vfdFrequency"])

        return payload

    async def read_controller(self, data: ControllerID) -> CarwashIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        state = await self.iot_storage.get_state(controller.id)
        energy_state = await self.iot_storage.get_energy_state(controller.id)

        return CarwashIoTControllerScheme.make(controller, state, energy_state)
