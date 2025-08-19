from typing import Any
from uuid import UUID

from structlog import get_logger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models import Controller
from dash.models.controllers.carwash import CarwashController
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.payment_helper import PaymentHelper
from dash.services.iot.base import BaseIoTService
from dash.services.iot.carwash.dto import (
    CarwashIoTControllerScheme,
    GetCarwashDisplayResponse,
    SetCarwashSettingsRequest,
    CarwashServiceEnum,
    CarwashRelayBit,
)
from dash.services.iot.common.utils import MODE_LABELS, ServiceBitMaskCodec
from dash.services.iot.dto import GetDisplayInfoRequest

logger = get_logger()


carwash_service_labels: dict[int, str] = {
    0: "Піна",
    1: "Екстра піна",
    2: "Вода під тиском",
    3: "Тепла вода",
    4: "Осмос",
    5: "Воск",
    6: "Зима",
    7: "Чорніння",
    8: "Максимум",
    128: "Пауза",
    255: "Без послуги",
}


class CarwashService(BaseIoTService):
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        payment_helper: PaymentHelper,
        iot_storage: IoTStorage,
        carwash_client: CarwashIoTClient,
        check_online_interactor: CheckOnlineInteractor,
    ):
        super().__init__(
            carwash_client, identity_provider, controller_repository, payment_helper
        )
        self.iot_client: CarwashIoTClient
        self.iot_storage = iot_storage
        self.check_online = check_online_interactor

    async def _get_controller(self, controller_id: UUID) -> CarwashController:
        controller = await self.controller_repository.get_carwash(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def sync_settings_infra(self, controller: Controller) -> None:
        config = await self.iot_client.get_config(controller.device_id)
        config.pop("request_id")

        settings = await self.iot_client.get_settings(controller.device_id)
        codec = ServiceBitMaskCodec(CarwashServiceEnum, CarwashRelayBit)

        settings["servicesRelay"] = codec.decode_bit_mask(settings["servicesRelay"])
        settings["tariff"] = codec.decode_int_mask(settings["tariff"])
        settings["servicesPause"] = codec.decode_int_mask(settings["servicesPause"])
        settings["vfdFrequency"] = codec.decode_int_mask(settings["vfdFrequency"])
        settings.pop("request_id")

        controller.config = config
        controller.settings = settings

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
        codec = ServiceBitMaskCodec(CarwashServiceEnum, CarwashRelayBit)

        payload["servicesRelay"] = codec.encode_bit_mask(payload["servicesRelay"])
        payload["tariff"] = codec.encode_int_mask(payload["tariff"])
        payload["servicesPause"] = codec.encode_int_mask(payload["servicesPause"])
        payload["vfdFrequency"] = codec.encode_int_mask(payload["vfdFrequency"])

        return payload

    async def read_controller(self, data: ControllerID) -> CarwashIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return CarwashIoTControllerScheme.make(
            model=controller,
            state=await self.iot_storage.get_state(controller.id),
            energy_state=await self.iot_storage.get_energy_state(controller.id),
            is_online=await self.check_online(controller),
        )

    async def get_display(
        self, data: GetDisplayInfoRequest
    ) -> GetCarwashDisplayResponse:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        display_info = await self.iot_client.get_display(controller.device_id)

        return GetCarwashDisplayResponse(
            mode=MODE_LABELS.get(display_info.get("mode", 0), "-"),
            service=carwash_service_labels.get(display_info.get("service", 0), "-"),
            summa=display_info.get("summa", 0),
            time=display_info.get("time", 0),
        )

    async def get_display_infra(self, device_id: str) -> GetCarwashDisplayResponse:
        display_info = await self.iot_client.get_display(device_id)

        return GetCarwashDisplayResponse(
            mode=MODE_LABELS.get(display_info.get("mode", 0), "-"),
            service=carwash_service_labels.get(display_info.get("service", 0), "-"),
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
