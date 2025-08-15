from typing import Any
from uuid import UUID

from structlog import get_logger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.vacuum.client import VacuumIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models import Controller
from dash.models.controllers.vacuum import VacuumController
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.payment_helper import PaymentHelper
from dash.services.iot.base import BaseIoTService
from dash.services.iot.common.utils import ServiceBitMaskCodec
from dash.services.iot.dto import GetDisplayInfoRequest
from dash.services.iot.vacuum.dto import (
    GetVacuumDisplayResponse,
    SetVacuumSettingsRequest,
    VacuumIoTControllerScheme,
    VacuumServiceEnum,
    VacuumRelayBit,
)

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
    0: "Пилосос",
    1: "Обдув",
    2: "Підкачка шин",
    3: "Омивання скла",
    4: "Чорніння",
    5: "MAX",
    128: "Пауза",
    255: "Без послуги",
}


class VacuumService(BaseIoTService):
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        payment_helper: PaymentHelper,
        vacuum_client: VacuumIoTClient,
        check_online_interactor: CheckOnlineInteractor,
        iot_storage: IoTStorage,
    ):
        super().__init__(
            vacuum_client,
            identity_provider,
            controller_repository,
            payment_helper,
        )
        self.iot_client: VacuumIoTClient
        self.iot_storage = iot_storage
        self.check_online = check_online_interactor

    async def _get_controller(self, controller_id: UUID) -> VacuumController:
        controller = await self.controller_repository.get_vacuum(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def sync_settings_infra(self, controller: Controller) -> None:
        config = await self.iot_client.get_config(controller.device_id)
        config.pop("request_id")

        settings = await self.iot_client.get_settings(controller.device_id)
        codec = ServiceBitMaskCodec(VacuumServiceEnum, VacuumRelayBit)

        settings["servicesRelay"] = codec.decode_bit_mask(settings["servicesRelay"])
        settings["tariff"] = codec.decode_int_mask(settings["tariff"])
        settings["servicesPause"] = codec.decode_int_mask(settings["servicesPause"])
        settings.pop("request_id")

        controller.config = config
        controller.settings = settings

    async def update_settings(self, data: SetVacuumSettingsRequest) -> None:
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

    async def read_controller(self, data: ControllerID) -> VacuumIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return VacuumIoTControllerScheme.make(
            model=controller,
            state=await self.iot_storage.get_state(controller.id),
            energy_state=await self.iot_storage.get_energy_state(controller.id),
            is_online=await self.check_online(controller),
        )

    async def get_display(
        self, data: GetDisplayInfoRequest
    ) -> GetVacuumDisplayResponse:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        display_info = await self.iot_client.get_display(controller.device_id)

        return GetVacuumDisplayResponse(
            mode=MODE_LABELS.get(display_info.get("mode", 0), "-"),
            service=SERVICE_LABELS.get(display_info.get("service", 0), "-"),
            summa=display_info.get("summa", 0),
            time=display_info.get("time", 0),
        )

    async def get_display_infra(self, device_id: str) -> GetVacuumDisplayResponse:
        display_info = await self.iot_client.get_display(device_id)

        return GetVacuumDisplayResponse(
            mode=MODE_LABELS.get(display_info.get("mode", 0), "-"),
            service=SERVICE_LABELS.get(display_info.get("service", 0), "-"),
            summa=display_info.get("summa", 0),
            time=display_info.get("time", 0),
        )

    async def start_session_infra(self, device_id: str, card_id: str) -> None:
        await self.iot_client.set_session(
            device_id=device_id,
            payload={
                "cardUID": card_id,
                "session": "open",
            },
        )

    async def finish_session_infra(self, device_id: str, card_id: str) -> None:
        await self.iot_client.set_session(
            device_id=device_id,
            payload={
                "cardUID": card_id,
                "session": "close",
            },
        )

    @staticmethod
    def _prepare_settings_payload(settings: dict[str, Any]) -> dict[str, Any]:
        payload = settings.copy()
        codec = ServiceBitMaskCodec(VacuumServiceEnum, VacuumRelayBit)

        payload["servicesRelay"] = codec.encode_bit_mask(payload["servicesRelay"])
        payload["tariff"] = codec.encode_int_mask(payload["tariff"])
        payload["servicesPause"] = codec.encode_int_mask(payload["servicesPause"])

        return payload
