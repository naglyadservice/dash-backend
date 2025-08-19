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
from dash.services.iot.common.utils import ServiceBitMaskCodec
from dash.services.iot.dto import GetDisplayInfoRequest

logger = get_logger()

# Human-readable labels for display information that the controller returns
MODE_LABELS: dict[int, str] = {
    0x00: "Логотип",
    0x01: "Очікування оплати",
    0x02: "Двері відкриті",
    0x03: "Блокування",
    0x04: "Сервісний режим 0",
    0x05: "Сервісний режим 1",
    0x06: "Сервісний режим 2",
    0x07: "Продажа готівкою",
    0x08: "Подяка",
    0x09: "Оплата PayPass 0",
    0x0A: "Оплата PayPass 1",
    0x0B: "Продажа карткою 0",
    0x0C: "Продажа карткою 1",
    0x0D: "Продажа карткою 2",
    0x0E: "Продажа карткою 3",
    0x0F: "Інкасація",
    0x10: "Перевірка при старі",
    0x80: "Реклама",
}

SERVICE_LABELS: dict[int, str] = {
    0x00: "Сесія закрита",
    0x01: "Пауза",
    0x02: "Пилосос",
    0x03: "Вологий пилосос",
    0x04: "Пилосос з паром",
    0x05: "Обдув",
    0x06: "Спреєр",
    0x07: "Торнадор",
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

    async def _decode_settings(self, controller: Controller, settings: dict[str, Any]):
        codec = ServiceBitMaskCodec(CarCleanerServiceEnum, CarCleanerRelayBit)

        settings["servicesRelay"] = codec.decode_bit_mask(settings["servicesRelay"])
        settings["tariff"] = codec.decode_int_mask(settings["tariff"])
        settings["servicesPause"] = codec.decode_int_mask(settings["servicesPause"])
        settings.pop("request_id")

        controller.settings = settings

        await self.controller_repository.commit()

    async def update_settings(
        self, data: SetCarCleanerSettingsRequest
    ) -> CarCleanerIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        payload = self._prepare_settings_payload(controller.settings)
        payload.update(data.settings.model_dump(exclude_none=True))

        await self.iot_client.set_settings(
            controller.device_id,
            payload=self._prepare_settings_payload(payload),
        )
        await self.controller_repository.commit()

        state = await self.iot_storage.get_state(controller.id)
        return CarCleanerIoTControllerScheme.make(
            controller,
            state=state,
            energy_state=None,
            is_online=False,
        )

    @staticmethod
    def _prepare_settings_payload(settings: dict[str, Any]) -> dict[str, Any]:
        payload = settings.copy()
        codec = ServiceBitMaskCodec(CarCleanerServiceEnum, CarCleanerRelayBit)

        payload["servicesRelay"] = codec.encode_bit_mask(payload["servicesRelay"])
        payload["tariff"] = codec.encode_int_mask(payload["tariff"])
        payload["servicesPause"] = codec.encode_int_mask(payload["servicesPause"])

        return payload

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
            service=SERVICE_LABELS.get(display_info.get("service", 0), "-"),
            summa=display_info.get("summa", 0),
            time=display_info.get("time", 0),
        )
