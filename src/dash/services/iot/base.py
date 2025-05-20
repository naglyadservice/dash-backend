from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.common.base_client import BaseNpcClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.models import Controller
from dash.services.iot.dto import (
    ClearPaymentsRequest,
    GetDisplayInfoRequest,
    RebootControllerRequest,
    SendActionRequest,
    SendFreePaymentRequest,
    SendQRPaymentRequest,
    SetConfigRequest,
    SetSettingsRequest,
)


class BaseIoTService(ABC):
    def __init__(
        self,
        iot_client: BaseNpcClient,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
    ) -> None:
        self.iot_client = iot_client
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository

    @abstractmethod
    async def _get_controller(self, controller_id: UUID) -> Controller:
        pass

    async def init_controller_settings(self, controller: Controller) -> None:
        controller.config = await self.iot_client.get_config(controller.device_id)
        controller.settings = await self.iot_client.get_settings(controller.device_id)

    async def healthcheck(self, device_id: str) -> None:
        await self.iot_client.get_state(device_id)

    async def set_config(self, data: SetConfigRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        config_dict = data.config.model_dump(exclude_unset=True)
        await self.iot_client.set_config(
            device_id=controller.device_id, payload=config_dict
        )

        if controller.config:
            controller.config.update(config_dict)
            flag_modified(controller, "config")
        else:
            controller.config = config_dict

        await self.controller_repository.commit()

    async def set_settings(self, data: SetSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        settings_dict = data.settings.model_dump(exclude_unset=True)
        await self.iot_client.set_settings(
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
        return await self.iot_client.get_display(controller.device_id)

    async def reboot_controller(self, data: RebootControllerRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)
        await self.iot_client.reboot(
            device_id=controller.device_id, payload={"delay": data.delay}
        )

    async def send_qr_payment(self, data: SendQRPaymentRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)
        await self.iot_client.set_payment(
            device_id=controller.device_id,
            payload={
                "addQRcode": {
                    "order_id": data.payment.order_id,
                    "amount": data.payment.amount,
                }
            },
        )

    async def send_free_payment(self, data: SendFreePaymentRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)
        await self.iot_client.set_payment(
            device_id=controller.device_id,
            payload={"addFree": {"amount": data.payment.amount}},
        )

    async def clear_payments(self, data: ClearPaymentsRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)
        await self.iot_client.set_payment(
            device_id=controller.device_id,
            payload=data.options.model_dump(exclude_unset=True),
        )

    async def send_action(self, data: SendActionRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)
        await self.iot_client.set_action(
            device_id=controller.device_id,
            payload=data.action.model_dump(exclude_unset=True),
        )
