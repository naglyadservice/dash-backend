from uuid import UUID

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.acquiring.liqpay import LiqpayService
from dash.infrastructure.acquiring.monopay import MonopayService
from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.fiscalizer.client import FiscalizerIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models.controllers.fiscalizer import FiscalizerController
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.base import BaseIoTService
from dash.services.iot.dto import SendFreePaymentRequest
from dash.services.iot.fiscalizer.dto import (
    FiscalizerIoTControllerScheme,
    SetDescriptionRequest,
    SetupQuickDepositButtonsRequest,
    SetupSIMRequest,
)


class FiscalizerService(BaseIoTService):
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        payment_repository: PaymentRepository,
        liqpay_service: LiqpayService,
        monopay_service: MonopayService,
        checkbox_service: CheckboxService,
        iot_storage: IoTStorage,
        fiscalizer_client: FiscalizerIoTClient,
        check_online_interactor: CheckOnlineInteractor,
    ):
        super().__init__(
            fiscalizer_client,
            identity_provider,
            controller_repository,
            payment_repository,
            liqpay_service,
            monopay_service,
            checkbox_service,
        )
        self.iot_storage = iot_storage
        self.check_online = check_online_interactor

    async def _get_controller(self, controller_id: UUID) -> FiscalizerController:
        controller = await self.controller_repository.get_fiscalizer(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def read_controller(
        self, data: ControllerID
    ) -> FiscalizerIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return FiscalizerIoTControllerScheme.make(
            model=controller,
            state=await self.iot_storage.get_state(controller.id),
            energy_state=await self.iot_storage.get_energy_state(controller.id),
            is_online=await self.check_online(controller),
        )

    async def send_qr_payment_infra(self, device_id: str, order_id: str, amount: int):
        amount = round(amount / 100, 2)  # type: ignore
        return await super().send_qr_payment_infra(device_id, order_id, amount)

    async def send_free_payment(self, data: SendFreePaymentRequest) -> None:
        data.payment.amount = round(data.payment.amount / 100, 2)  # type: ignore
        return await super().send_free_payment(data)

    async def setup_quick_deposit_buttons(
        self, data: SetupQuickDepositButtonsRequest
    ) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        dict_data = data.buttons.model_dump()
        for key, value in dict_data.items():
            if hasattr(controller, key):
                setattr(controller, key, value)

        await self.controller_repository.commit()

    async def setup_sim(self, data: SetupSIMRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        dict_data = data.sim.model_dump()
        for key, value in dict_data.items():
            if hasattr(controller, key):
                setattr(controller, key, value)

        await self.controller_repository.commit()

    async def set_description(self, data: SetDescriptionRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        controller.description = data.description
        await self.controller_repository.commit()
