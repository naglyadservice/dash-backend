from typing import Any
from uuid import UUID

from sqlalchemy.orm.attributes import flag_modified

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.models.controllers.water_vending import WaterVendingController
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
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
        controller_repository: ControllerRepository,
        identity_provider: IdProvider,
        iot_storage: IotStorage,
        wsm_client: WsmClient,
    ):
        self.controller_repository = controller_repository
        self.identity_provider = identity_provider
        self.iot_storage = iot_storage
        self.wsm_client = wsm_client

    async def _get_controller(self, controller_id: UUID) -> WaterVendingController:
        controller = await self.controller_repository.get_wsm(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def healtcheck(self, device_id: str) -> None:
        await self.wsm_client.get_state(device_id)

    async def set_config(self, data: SetWaterVendingConfigRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        config_dict = data.config.model_dump(exclude_unset=True)
        await self.wsm_client.set_config(
            device_id=controller.device_id, payload=config_dict
        )

        if controller.config:
            controller.config.update(config_dict)
            flag_modified(controller, "config")
        else:
            controller.config = config_dict

        await self.controller_repository.commit()

    async def set_settings(self, data: SetWaterVendingSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        settings_dict = data.settings.model_dump(exclude_unset=True)
        await self.wsm_client.set_settings(
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
        return await self.wsm_client.get_display(controller.device_id)

    async def read_controller(self, data: ControllerID) -> WaterVendingControllerScheme:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_location_admin(controller.location_id)

        if not controller.config or not controller.settings:
            if not controller.config:
                controller.config = await self.wsm_client.get_config(
                    device_id=controller.device_id
                )
            if not controller.settings:
                controller.settings = await self.wsm_client.get_settings(
                    device_id=controller.device_id
                )

            await self.controller_repository.commit()

        state = await self.iot_storage.get_state(controller.id)
        return WaterVendingControllerScheme.make(controller, state)

    async def reboot_controller(self, data: RebootControllerRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )
        await self.wsm_client.reboot(
            device_id=controller.device_id, payload={"delay": data.delay}
        )

    async def send_qr_payment(self, data: SendQRPaymentRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.wsm_client.set_payment(
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

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        await self.wsm_client.set_payment(
            device_id=controller.device_id,
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

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )
        await self.wsm_client.set_payment(
            device_id=controller.device_id,
            payload=data.options.model_dump(exclude_unset=True),
        )

    async def send_action(self, data: SendActionRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )
        await self.wsm_client.set_action(
            device_id=controller.device_id,
            payload=data.actions.model_dump(exclude_unset=True),
        )
