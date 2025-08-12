import asyncio
from abc import ABC, abstractmethod
from uuid import UUID

from uuid_utils.compat import uuid7

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.acquiring.liqpay import LiqpayService
from dash.infrastructure.acquiring.monopay import MonopayService
from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.common.base_client import BaseIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models import Controller
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.customer_carwash import InsufficientDepositAmountError
from dash.services.common.payment_service import PaymentService
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
    SyncSettingsResponse,
)


class BaseIoTService(ABC):
    def __init__(
        self,
        iot_client: BaseIoTClient,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        payment_repository: PaymentRepository,
        liqpay_service: LiqpayService,
        monopay_service: MonopayService,
        checkbox_service: CheckboxService,
    ) -> None:
        self.iot_client = iot_client
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository
        self.payment_repository = payment_repository
        self.liqpay_service = liqpay_service
        self.monopay_service = monopay_service
        self.checkbox_service = checkbox_service

    @abstractmethod
    async def _get_controller(self, controller_id: UUID) -> Controller:
        raise NotImplementedError

    async def sync_settings_infra(self, controller: Controller) -> None:
        config = await self.iot_client.get_config(controller.device_id)
        config.pop("request_id")

        settings = await self.iot_client.get_settings(controller.device_id)
        settings.pop("request_id")

        controller.config = config
        controller.settings = settings

    async def sync_settings(self, data: SyncSettingsRequest) -> SyncSettingsResponse:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        await self.sync_settings_infra(controller)
        await self.controller_repository.commit()

        return SyncSettingsResponse(
            config=controller.config,
            settings=controller.settings,
        )

    async def healthcheck(self, device_id: str) -> None:
        pass
        # await self.iot_client.get_state(device_id)

    async def update_config(self, data: SetConfigRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        config_dict = data.config.model_dump(exclude_unset=True)
        await self.iot_client.set_config(
            device_id=controller.device_id, payload=config_dict
        )

        controller.config = {**controller.config, **config_dict}
        await self.controller_repository.commit()

    async def update_settings(self, data: SetSettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        settings_dict = data.settings.model_dump(exclude_unset=True)
        await self.iot_client.set_settings(
            device_id=controller.device_id, payload=settings_dict
        )

        controller.settings = {**controller.settings, **settings_dict}
        await self.controller_repository.commit()

    async def get_display(self, data: GetDisplayInfoRequest) -> dict[str, str]:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        display_info = await self.iot_client.get_display(controller.device_id)
        display_info.pop("request_id")

        return display_info

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

    async def send_qr_payment_infra(
        self,
        device_id: str,
        order_id: str,
        amount: int,
    ):
        await self.iot_client.set_payment(
            device_id=device_id,
            payload={
                "addQRcode": {
                    "order_id": order_id,
                    "amount": amount,
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

    async def send_free_payment_infra(self, device_id: str, amount: int) -> None:
        await self.iot_client.set_payment(
            device_id=device_id,
            payload={"addFree": {"amount": amount}},
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
            payload=data.action.model_dump(),
        )

    async def send_action_infra(self, device_id: str, payload: dict) -> None:
        await self.iot_client.set_action(
            device_id=device_id,
            payload=payload,
        )

    async def blocking(self, data: BlockingRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)
        await self.iot_client.set_action(
            device_id=controller.device_id,
            payload={"Blocking": data.blocking},
        )

    def _get_payment_processor(self, payment_type: PaymentType) -> PaymentService:
        if payment_type is PaymentType.LIQPAY:
            return self.liqpay_service
        elif payment_type is PaymentType.MONOPAY:
            return self.monopay_service
        else:
            raise ValueError(
                f"No payment processor for {payment_type.value} payment type"
            )

    async def create_invoice(self, data: CreateInvoiceRequest) -> CreateInvoiceResponse:
        controller = await self._get_controller(data.controller_id)
        await self.healthcheck(controller.device_id)

        if data.amount < controller.min_deposit_amount:
            raise InsufficientDepositAmountError

        processor = self._get_payment_processor(data.payment_type)

        result = await processor.create_invoice(controller, data.amount)
        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            amount=data.amount,
            type=data.payment_type,
            status=PaymentStatus.CREATED,
            invoice_id=result.invoice_id,
        )
        self.payment_repository.add(payment)
        await self.payment_repository.commit()

        return result

    async def process_hold_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.HOLD
        controller = await self._get_controller(payment.controller_id)
        processor = self._get_payment_processor(payment.type)

        try:
            await self.send_qr_payment_infra(
                device_id=controller.device_id,
                order_id=payment.invoice_id,  # type: ignore
                amount=payment.amount,
            )
        except Exception:
            await processor.refund(controller, payment)
            payment.failure_reason = "Не вдалося встановити зв'язок з пристроєм"
        else:
            await processor.finalize(controller, payment, payment.amount)

        await self.payment_repository.commit()

    async def process_processing_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.PROCESSING
        await self.payment_repository.commit()

    async def process_success_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.COMPLETED
        controller = await self._get_controller(payment.controller_id)

        if controller.checkbox_active:
            receipt_id = uuid7()
            payment.receipt_id = receipt_id
            asyncio.create_task(
                self.checkbox_service.create_receipt(
                    controller=controller,
                    payment=payment,
                    receipt_id=receipt_id,
                )
            )
        await self.payment_repository.commit()

    async def process_reversed_status(self, payment: Payment) -> None:
        payment.status = PaymentStatus.REVERSED
        await self.payment_repository.commit()

    async def process_failed_status(self, payment: Payment, description: str) -> None:
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = description
        await self.payment_repository.commit()
