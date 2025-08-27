from typing import Any
from uuid import UUID

from structlog import get_logger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.car_cleaner.client import CarCleanerIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models import Controller
from dash.models.controllers.car_cleaner import CarCleanerController
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.payment_helper import PaymentHelper
from dash.services.iot.base import BaseIoTService
from dash.services.iot.car_cleaner.dto import (
    CarCleanerIoTControllerScheme,
    GetCarCleanerDisplayResponse,
    SetCarCleanerSettingsRequest,
    CarCleanerServiceEnum,
    CarCleanerRelayBit,
)
from dash.services.iot.common.utils import MODE_LABELS, ServiceBitMaskCodec
from dash.services.iot.dto import GetDisplayInfoRequest

logger = get_logger()

car_cleaner_services_labels: dict[int, str] = {
    0: "Пилосос",
    1: "Вологий пилосос",
    2: "Паровий пилосос",
    3: "Обдув",
    4: "Спреєр",
    5: "Торнадор",
    6: "Максимум",
    128: "Пауза",
    255: "Без послуги",
}


class CarCleanerService(BaseIoTService):
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        iot_client: CarCleanerIoTClient,
        iot_storage: IoTStorage,
        payment_helper: PaymentHelper,
        check_online: CheckOnlineInteractor,
    ):
        super().__init__(
            iot_client, identity_provider, controller_repository, payment_helper
        )
        self.iot_client = iot_client
        self.iot_storage = iot_storage
        self.payment_helper = payment_helper
        self.check_online = check_online

    async def _get_controller(self, controller_id: UUID) -> CarCleanerController:
        controller = await self.controller_repository.get(controller_id)
        if not controller:
            raise ControllerNotFoundError
        if not isinstance(controller, CarCleanerController):
            raise ControllerNotFoundError
        return controller

    async def sync_settings_infra(self, controller: Controller) -> None:
        config = await self.iot_client.get_config(controller.device_id)
        config.pop("request_id")

        settings = await self.iot_client.get_settings(controller.device_id)
        codec = ServiceBitMaskCodec(CarCleanerServiceEnum, CarCleanerRelayBit)

        settings["servicesRelay"] = codec.decode_bit_mask(settings["servicesRelay"])
        settings["tariff"] = codec.decode_int_mask(settings["tariff"])
        settings["servicesPause"] = codec.decode_int_mask(settings["servicesPause"])
        settings.pop("request_id")

        controller.config = config
        controller.settings = settings

    async def update_settings(self, data: SetCarCleanerSettingsRequest) -> None:
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

    async def read_controller(
        self, data: ControllerID
    ) -> CarCleanerIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return CarCleanerIoTControllerScheme.make(
            controller,
            state=await self.iot_storage.get_state(controller.id),
            energy_state=await self.iot_storage.get_energy_state(controller.id),
            is_online=await self.check_online(controller),
        )

    async def get_display_info(
        self, data: GetDisplayInfoRequest
    ) -> GetCarCleanerDisplayResponse:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        display_info = await self.iot_client.get_display(controller.device_id)

        return GetCarCleanerDisplayResponse(
            mode=MODE_LABELS.get(display_info.get("mode", 0), "-"),
            service=car_cleaner_services_labels.get(
                display_info.get("service", 0), "-"
            ),
            summa=display_info.get("summa", 0),
            time=display_info.get("time", 0),
        )

    @staticmethod
    def _prepare_settings_payload(settings: dict[str, Any]) -> dict[str, Any]:
        payload = settings.copy()
        codec = ServiceBitMaskCodec(CarCleanerServiceEnum, CarCleanerRelayBit)

        payload["servicesRelay"] = codec.encode_bit_mask(payload["servicesRelay"])
        payload["tariff"] = codec.encode_int_mask(payload["tariff"])
        payload["servicesPause"] = codec.encode_int_mask(payload["servicesPause"])

        return payload
