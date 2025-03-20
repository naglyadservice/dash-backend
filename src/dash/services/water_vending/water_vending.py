from typing import Any, Literal

from npc_iot.exception import DeviceResponceError
from sqlalchemy.orm.attributes import flag_modified

from dash.infrastructure.mqtt.client import NpcClient
from dash.infrastructure.repositories.water_vending.controller import (
    WaterVendingControllerRepository,
)
from dash.infrastructure.repositories.water_vending.transaction import (
    WaterVendingTransactionRepository,
)
from dash.models.controllers.water_vending import WaterVendingController
from dash.services.errors import (
    ControllerNotFoundError,
    ControllerResponseError,
    ControllerTimeoutError,
)
from dash.services.water_vending.dto import (
    ClearPaymentsRequest,
    ControllerID,
    RebootControllerRequest,
    SendActionRequest,
    SendFreePaymentRequest,
    SendQRPaymentRequest,
    SetWaterVendingConfigRequest,
    SetWaterVendingSettingsRequest,
    WaterVendingControllerScheme,
    WaterVendingTransactionScheme,
)


class WaterVendingService:
    def __init__(
        self,
        npc_client: NpcClient,
        controller_repository: WaterVendingControllerRepository,
        transaction_repository: WaterVendingTransactionRepository,
    ):
        self.npc_client = npc_client
        self.controller_repository = controller_repository
        self.transaction_repository = transaction_repository

    async def _get_controller(self, controller_id: int) -> WaterVendingController:
        controller = await self.controller_repository.get(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def _send_message(
        self,
        device_id: str,
        topic: str,
        payload: dict[str, Any],
        qos: Literal[0, 1, 2] = 1,
        ttl: int = 5,
    ) -> dict[str, Any]:
        waiter = await self.npc_client._send_message(
            device_id=device_id,
            topic=topic,
            payload=payload,
            qos=qos,
            ttl=ttl,
        )
        try:
            response = await waiter.wait(timeout=5)
        except DeviceResponceError:
            raise ControllerResponseError
        except TimeoutError:
            raise ControllerTimeoutError

        return response

    async def set_config(self, data: SetWaterVendingConfigRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        config_dict = data.config.model_dump(exclude_unset=True)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/config/set",
            payload=config_dict,
            qos=1,
            ttl=5,
        )

        if controller.config:
            controller.config.update(config_dict)
            flag_modified(controller, "config")
        else:
            controller.config = config_dict

        await self.controller_repository.commit()

    async def set_settings(self, data: SetWaterVendingSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        settings_dict = data.settings.model_dump(exclude_unset=True)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/setting/set",
            payload=settings_dict,
            qos=1,
            ttl=5,
        )

        if controller.settings:
            controller.settings.update(settings_dict)
            flag_modified(controller, "settings")
        else:
            controller.settings = settings_dict

        await self.controller_repository.commit()

    async def _get_config(self, device_id: str) -> dict[str, Any]:
        return await self._send_message(
            device_id=device_id,
            topic="client/config/get",
            payload={"fields": []},
            qos=1,
            ttl=5,
        )

    async def _get_settings(self, device_id: str) -> dict[str, Any]:
        return await self._send_message(
            device_id=device_id,
            topic="client/setting/get",
            payload={"fields": []},
            qos=1,
            ttl=5,
        )

    async def _get_display(self, device_id: str) -> dict[str, Any]:
        display = await self._send_message(
            device_id=device_id,
            topic="client/display/get",
            payload={"fields": []},
            qos=1,
            ttl=5,
        )
        display = {
            k: v for k, v in display.items() if v and v != " " and k != "request_id"
        }

        return display

    async def read_controller(self, data: ControllerID) -> WaterVendingControllerScheme:
        controller = await self._get_controller(data.controller_id)

        if not controller.config or not controller.settings:
            if not controller.config:
                controller.config = await self._get_config(controller.device_id)
            if not controller.settings:
                controller.settings = await self._get_settings(controller.device_id)

            await self.controller_repository.commit()

        scheme = WaterVendingControllerScheme.model_validate(
            controller, from_attributes=True
        )
        scheme.display = await self._get_display(controller.device_id)
        return scheme

    async def reboot_controller(self, data: RebootControllerRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.npc_client.reboot(controller.device_id, {"delay": data.delay})

    async def send_qr_payment(self, data: SendQRPaymentRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/payment/set",
            payload={"addQRcode": {"order_id": data.order_id, "amount": data.amount}},
            qos=1,
            ttl=5,
        )

    async def send_free_payment(self, data: SendFreePaymentRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/payment/set",
            payload={"addFree": {"amount": data.amount}},
            qos=1,
            ttl=5,
        )

    async def clear_payments(self, data: ClearPaymentsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/payment/set",
            payload=data.options.model_dump(exclude_unset=True),
            qos=1,
            ttl=5,
        )

    async def send_action(self, data: SendActionRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/action/set",
            payload=data.model_dump(exclude_unset=True),
            qos=1,
            ttl=5,
        )

    async def read_transactions(
        self, data: ControllerID
    ) -> list[WaterVendingTransactionScheme]:
        controller = await self._get_controller(data.controller_id)

        transactions = await self.transaction_repository.get_list_by_controller_id(
            controller_id=controller.id
        )
        return [
            WaterVendingTransactionScheme.model_validate(
                transaction, from_attributes=True
            )
            for transaction in transactions
        ]
