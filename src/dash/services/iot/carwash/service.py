from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified
from structlog import getLogger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.carwash.client import CarwashClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.models.controllers.carwash import CarwashController
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    ControllerTimeoutError,
)
from dash.services.iot.base import BaseIoTService
from dash.services.iot.carwash.dto import (
    CarwashControllerScheme,
    SetCarwashSettingsRequest,
)
from dash.services.iot.carwash.utils import decode_relay_mask, encode_relay_mask
from dash.services.iot.dto import ControllerID

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

        await self.iot_client.set_settings(
            device_id=controller.device_id, payload=settings_dict
        )

        if controller.settings:
            controller.settings.update(settings_dict)
            flag_modified(controller, "settings")
        else:
            controller.settings = settings_dict

        await self.controller_repository.commit()

    async def read_controller(self, data: ControllerID) -> CarwashControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        commit = False

        if not controller.config:
            try:
                controller.config = await self.iot_client.get_config(
                    device_id=controller.device_id
                )
                commit = True
            except ControllerTimeoutError:
                pass

        if not controller.settings:
            try:
                settings = await self.iot_client.get_settings(
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
