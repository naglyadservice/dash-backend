from abc import ABC, abstractmethod
from uuid import UUID


from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.common.base_client import BaseIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.models import Controller
from dash.models.payment import Payment, PaymentStatus, PaymentType, PaymentGatewayType
from dash.services.common.errors.controller import (
    InsufficientDepositAmountError,
    UnsupportedPaymentGatewayTypeError,
    ControllerResponseError,
    ControllerTimeoutError,
)
from dash.services.common.payment_helper import PaymentHelper
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
        payment_helper: PaymentHelper,
    ) -> None:
        self.iot_client = iot_client
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository
        self.payment_helper = payment_helper

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

    async def create_invoice(self, data: CreateInvoiceRequest) -> CreateInvoiceResponse:
        controller = await self._get_controller(data.controller_id)
        if (
            data.gateway_type is PaymentGatewayType.LIQPAY
            and not controller.liqpay_active
        ) or (
            data.gateway_type is PaymentGatewayType.MONOPAY
            and controller.monopay_active
        ):
            raise UnsupportedPaymentGatewayTypeError

        if data.amount < controller.min_deposit_amount:
            raise InsufficientDepositAmountError

        await self.healthcheck(controller.device_id)

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
        controller = await self._get_controller(payment.controller_id)
        try:
            await self.send_qr_payment_infra(
                device_id=controller.device_id,
                order_id=payment.invoice_id,  # type: ignore
                amount=payment.amount,
            )
        except (ControllerResponseError, ControllerTimeoutError):
            await self.payment_helper.refund(controller, payment)
            payment.failure_reason = "Не вдалося встановити зв'язок з пристроєм"
        else:
            await self.payment_helper.finalize_hold(controller, payment, payment.amount)

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
