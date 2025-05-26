from copy import deepcopy
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified
from structlog import getLogger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.carwash.client import CarwashClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.models import Controller
from dash.models.controllers.carwash import CarwashController
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    ControllerTimeoutError,
)
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
from dash.services.iot.dto import ControllerID, SetConfigRequest

logger = getLogger()


class CarwashService(BaseIoTService):
    def __init__(
        self,
        controller_repository: ControllerRepository,
        identity_provider: IdProvider,
        iot_storage: IotStorage,
        carwash_client: CarwashClient,
    ):
        super().__init__(carwash_client, identity_provider, controller_repository)
        self.iot_storage = iot_storage

    async def _get_controller(self, controller_id: UUID) -> CarwashController:
        controller = await self.controller_repository.get_carwash(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def init_controller_settings(self, controller: Controller) -> None:
        controller.config = await self.iot_client.get_config(controller.device_id)

        settings = await self.iot_client.get_settings(controller.device_id)
        settings["servicesRelay"] = decode_service_bit_mask(settings["servicesRelay"])
        settings["tariff"] = decode_service_int_mask(settings["tariff"])
        settings["servicesPause"] = decode_service_int_mask(settings["servicesPause"])
        settings["vfdFrequency"] = decode_service_int_mask(settings["vfdFrequency"])

        controller.settings = settings

    async def set_config(self, data: SetCarwashConfigRequest) -> None:
        await super().set_config(data)

    async def set_settings(self, data: SetCarwashSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        settings_dict = data.settings.model_dump(exclude_unset=True)
        controller_settings_dict = deepcopy(settings_dict)

        if data.settings.servicesRelay is not None:
            controller_settings_dict["servicesRelay"] = encode_service_bit_mask(
                controller_settings_dict["servicesRelay"]
            )
        if data.settings.tariff is not None:
            controller_settings_dict["tariff"] = encode_service_int_mask(
                controller_settings_dict["tariff"]
            )
        if data.settings.servicesPause is not None:
            controller_settings_dict["servicesPause"] = encode_service_int_mask(
                controller_settings_dict["servicesPause"]
            )
        if data.settings.vfdFrequency is not None:
            controller_settings_dict["vfdFrequency"] = encode_service_int_mask(
                controller_settings_dict["vfdFrequency"]
            )

        await self.iot_client.set_settings(
            device_id=controller.device_id, payload=controller_settings_dict
        )

        if controller.settings:
            controller.settings.update(settings_dict)
            flag_modified(controller, "settings")
        else:
            controller.settings = settings_dict

        await self.controller_repository.commit()

    async def read_controller(self, data: ControllerID) -> CarwashIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        state = await self.iot_storage.get_state(controller.id)
        return CarwashIoTControllerScheme.make(controller, state)
