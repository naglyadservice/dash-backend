from typing import Any, Literal
from uuid import UUID

from npc_iot.exception import DeviceResponceError
from sqlalchemy.orm.attributes import flag_modified

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.models.controllers.water_vending import WaterVendingController
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    ControllerResponseError,
    ControllerTimeoutError,
)
from dash.services.water_vending.dto import (
    ClearPaymentsRequest,
    ControllerID,
    GetDisplayInfoRequest,
    RebootControllerRequest,
    SendActionRequest,
    SendFreePaymentRequest,
    SendQRPaymentRequest,
    SetWaterVendingConfigRequest,
    SetWaterVendingSettingsRequest,
    WaterVendingControllerScheme,
)


class WaterVendingService:
    def __init__(
        self,
        npc_client: WsmClient,
        controller_repository: ControllerRepository,
        identity_provider: IdProvider,
    ):
        self.npc_client = npc_client
        self.controller_repository = controller_repository
        self.identity_provider = identity_provider

    async def _get_controller(self, controller_id: UUID) -> WaterVendingController:
        controller = await self.controller_repository.get_wsm(controller_id)

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
            response = await waiter.wait(timeout=2)
        except DeviceResponceError:
            raise ControllerResponseError
        except TimeoutError:
            raise ControllerTimeoutError

        return response

    async def healtcheck(self, device_id: str) -> None:
        await self._send_message(
            device_id=device_id,
            topic="client/state/get",
            payload={"fields": []},
        )

    async def set_config(self, data: SetWaterVendingConfigRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.location_id)

        config_dict = data.config.model_dump(exclude_unset=True)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/config/set",
            payload=config_dict,
        )

        if controller.config:
            controller.config.update(config_dict)
            flag_modified(controller, "config")
        else:
            controller.config = config_dict

        await self.controller_repository.commit()

    async def set_settings(self, data: SetWaterVendingSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.location_id)

        settings_dict = data.settings.model_dump(exclude_unset=True)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/setting/set",
            payload=settings_dict,
        )

        if controller.settings:
            controller.settings.update(settings_dict)
            flag_modified(controller, "settings")
        else:
            controller.settings = settings_dict

        await self.controller_repository.commit()

    async def _get_config(self, device_id: str) -> dict[str, Any] | None:
        try:
            return await self._send_message(
                device_id=device_id,
                topic="client/config/get",
                payload={"fields": []},
            )
        except (ControllerResponseError, ControllerTimeoutError):
            return None

    async def _get_settings(self, device_id: str) -> dict[str, Any] | None:
        try:
            return await self._send_message(
                device_id=device_id,
                topic="client/setting/get",
                payload={"fields": []},
            )
        except (ControllerResponseError, ControllerTimeoutError):
            return None

    async def get_display(self, data: GetDisplayInfoRequest) -> dict[str, Any]:
        controller = await self._get_controller(data.controller_id)

        display = await self._send_message(
            device_id=controller.device_id,
            topic="client/display/get",
            payload={"fields": []},
        )
        return {
            k: v for k, v in display.items() if v and v != " " and k != "request_id"
        }

    async def read_controller(self, data: ControllerID) -> WaterVendingControllerScheme:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_location_admin(controller.location_id)

        if not controller.config or not controller.settings:
            if not controller.config:
                controller.config = await self._get_config(controller.device_id)
            if not controller.settings:
                controller.settings = await self._get_settings(controller.device_id)

            await self.controller_repository.commit()

        return WaterVendingControllerScheme.model_validate(
            controller, from_attributes=True
        )

    async def reboot_controller(self, data: RebootControllerRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.location_id)

        await self.npc_client.reboot(controller.device_id, {"delay": data.delay})

    async def send_qr_payment(self, data: SendQRPaymentRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/payment/set",
            payload={
                "addQRcode": {
                    "order_id": data.payment.order_id,
                    "amount": data.payment.amount,
                }
            },
        )

    async def send_free_payment(self, data: SendFreePaymentRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.location_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/payment/set",
            payload={"addFree": {"amount": data.payment.amount}},
        )
        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            amount=data.payment.amount,
            status=PaymentStatus.COMPLETED,
            type=PaymentType.FREE,
        )
        self.controller_repository.add(payment)
        await self.controller_repository.commit()

    async def clear_payments(self, data: ClearPaymentsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.location_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/payment/set",
            payload=data.options.model_dump(exclude_unset=True),
        )

    async def send_action(self, data: SendActionRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.location_id)

        await self._send_message(
            device_id=controller.device_id,
            topic="client/action/set",
            payload=data.actions.model_dump(exclude_unset=True),
        )
