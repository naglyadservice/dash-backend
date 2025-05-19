from typing import Any
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified
from structlog import getLogger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.carwash.client import CarwashClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.models.controllers.carwash import CarwashController
from dash.services.carwash.dto import (
    CarwashControllerScheme,
    GetDisplayInfoRequest,
    SetCarwashConfigRequest,
    SetCarwashSettingsRequest,
)
from dash.services.carwash.utils import decode_relay_mask, encode_relay_mask
from dash.services.common.const import ControllerID
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    ControllerTimeoutError,
)

logger = getLogger()


class CarwashService:
    def __init__(
        self,
        controller_repository: ControllerRepository,
        identity_provider: IdProvider,
        iot_storage: IotStorage,
        carwash_client: CarwashClient,
    ):
        self.controller_repository = controller_repository
        self.identity_provider = identity_provider
        self.iot_storage = iot_storage
        self.carwash_client = carwash_client

    async def _get_controller(self, controller_id: UUID) -> CarwashController:
        controller = await self.controller_repository.get_carwash(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def healtcheck(self, device_id: str) -> None:
        await self.carwash_client.get_state(device_id)

    async def set_config(self, data: SetCarwashConfigRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        config_dict = data.config.model_dump(exclude_unset=True)
        await self.carwash_client.set_config(
            device_id=controller.device_id, payload=config_dict
        )

        if controller.config:
            controller.config.update(config_dict)
            flag_modified(controller, "config")
        else:
            controller.config = config_dict

        await self.controller_repository.commit()

    async def set_settings(self, data: SetCarwashSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        settings_dict = data.settings.model_dump(exclude_unset=True)
        if data.settings.servicesRelay is not None:
            settings_dict["servicesRelay"] = encode_relay_mask(
                settings_dict["servicesRelay"]
            )

        await self.carwash_client.set_settings(
            device_id=controller.device_id, payload=settings_dict
        )

        if controller.settings:
            controller.settings.update(settings_dict)
            flag_modified(controller, "settings")
        else:
            controller.settings = settings_dict

        await self.controller_repository.commit()

    async def get_display(self, data: GetDisplayInfoRequest) -> dict[str, Any]:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return await self.carwash_client.get_display(controller.device_id)

    async def read_controller(self, data: ControllerID) -> CarwashControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        commit = False

        if not controller.config:
            try:
                controller.config = await self.carwash_client.get_config(
                    device_id=controller.device_id
                )
                commit = True
            except ControllerTimeoutError:
                pass

        if not controller.settings:
            try:
                settings = await self.carwash_client.get_settings(
                    device_id=controller.device_id
                )
                logger.info(f"settings: {settings}")
            except ControllerTimeoutError:
                pass
            else:
                settings["servicesRelay"] = decode_relay_mask(settings["servicesRelay"])
                controller.settings = settings
                commit = True

        if commit:
            await self.controller_repository.commit()

        state = await self.iot_storage.get_state(controller.id)
        return CarwashControllerScheme.make(controller, state)
