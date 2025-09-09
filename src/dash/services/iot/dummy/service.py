from uuid import UUID

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.models.controllers.dummy import DummyController
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.payment_helper import PaymentHelper
from dash.services.iot.base import BaseIoTService, InsufficientDepositAmountError
from dash.services.iot.dto import (
    BlockingRequest,
    ClearPaymentsRequest,
    CreateInvoiceRequest,
    CreateInvoiceResponse,
    GetDisplayInfoRequest,
    RebootControllerRequest,
    SendActionRequest,
    SendFreePaymentRequest,
    SendQRPaymentRequest,
    SetConfigRequest,
    SetSettingsRequest,
    SyncSettingsRequest,
)
from dash.services.iot.dummy.dto import (
    DummyControllerIoTScheme,
    SetDummyDescriptionRequest,
)


class DummyService(BaseIoTService):
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        payment_helper: PaymentHelper,
    ):
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository
        self.payment_helper = payment_helper

    async def _get_controller(self, controller_id: UUID) -> DummyController:
        controller = await self.controller_repository.get_dummy(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def read_controller(self, data: ControllerID) -> DummyControllerIoTScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)
        return DummyControllerIoTScheme.model_validate(controller)

    async def set_description(self, data: SetDummyDescriptionRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        controller.description = data.description
        await self.controller_repository.commit()

    async def sync_settings_infra(self, controller: DummyController) -> None:
        controller.config = {}
        controller.settings = {}

    async def sync_settings(self, data: SyncSettingsRequest) -> None:
        pass

    async def healthcheck(self, device_id: str) -> None:
        pass

    async def update_config(self, data: SetConfigRequest) -> None:
        pass

    async def update_settings(self, data: SetSettingsRequest) -> None:
        pass

    async def get_display(self, data: GetDisplayInfoRequest) -> dict[str, str]:
        return {}

    async def reboot_controller(self, data: RebootControllerRequest) -> None:
        pass

    async def send_qr_payment(self, data: SendQRPaymentRequest) -> None:
        pass

    async def send_qr_payment_infra(
        self, device_id: str, order_id: str, amount: float
    ) -> None:
        pass

    async def send_free_payment(self, data: SendFreePaymentRequest) -> None:
        pass

    async def send_free_payment_infra(self, device_id: str, amount: float) -> None:
        pass

    async def clear_payments(self, data: ClearPaymentsRequest) -> None:
        pass

    async def send_action(self, data: SendActionRequest) -> None:
        pass

    async def send_action_infra(self, device_id: str, payload: dict) -> None:
        pass

    async def blocking(self, data: BlockingRequest) -> None:
        pass

    async def create_invoice(self, data: CreateInvoiceRequest) -> CreateInvoiceResponse:
        controller = await self._get_controller(data.controller_id)

        if data.amount < controller.min_deposit_amount:
            raise InsufficientDepositAmountError

        invoice_result = await self.payment_helper.create_invoice(
            controller=controller,
            amount=data.amount,
            gateway_type=data.gateway_type,
        )
        payment = self.payment_helper.create_payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            payment_type=PaymentType.CASHLESS,
            gateway_type=data.gateway_type,
            amount=data.amount,
            invoice_id=invoice_result.invoice_id,
        )
        await self.payment_helper.save_and_commit(payment)
        return invoice_result

    async def process_hold_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.HOLD
        await self.payment_helper.commit()

    async def process_processing_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.PROCESSING
        await self.payment_helper.commit()

    async def process_success_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.COMPLETED
        controller = await self._get_controller(payment.controller_id)

        if controller.checkbox_active:
            await self.payment_helper.fiscalize(controller, payment)

        await self.payment_helper.commit()

    async def process_reversed_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.REVERSED
        await self.payment_helper.commit()

    async def process_failed_status(self, payment: Payment, description: str) -> None:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = description
        await self.payment_helper.commit()
