from datetime import UTC, datetime
from uuid import UUID

from structlog import get_logger

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.iot.laundry.client import LaundryIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models import Payment
from dash.models.controllers.laundry import (
    LaundryController,
    LaundryStatus,
    LaundryTariffType,
)
from dash.models.payment import PaymentStatus, PaymentType, PaymentGatewayType
from dash.models.transactions.laundry import LaundrySessionStatus, LaundryTransaction
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import ControllerID
from dash.services.common.errors.controller import (
    ControllerIsBusyError,
    ControllerNotFoundError,
    ControllerResponseError,
    ControllerTimeoutError,
    UnsupportedPaymentGatewayTypeError,
)
from dash.services.common.payment_helper import PaymentHelper
from dash.services.iot.base import BaseIoTService
from dash.services.iot.dto import CreateInvoiceResponse
from dash.services.iot.laundry.dto import (
    CreateLaundryInvoiceRequest,
    LaundryIoTControllerScheme,
    UpdateLaudnrySettingsRequest,
)

logger = get_logger()


class LaundryService(BaseIoTService):
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        payment_helper: PaymentHelper,
        transaction_repository: TransactionRepository,
        iot_storage: IoTStorage,
        laundry_client: LaundryIoTClient,
        check_online_interactor: CheckOnlineInteractor,
    ):
        super().__init__(
            laundry_client,
            identity_provider,
            controller_repository,
            payment_helper,
        )
        self.iot_client: LaundryIoTClient = laundry_client
        self.transaction_repository = transaction_repository
        self.iot_storage = iot_storage
        self.check_online = check_online_interactor

    async def _get_controller(self, controller_id: UUID) -> LaundryController:
        controller = await self.controller_repository.get_laundry(controller_id)

        if not controller:
            raise ControllerNotFoundError

        return controller

    async def read_controller(self, data: ControllerID) -> LaundryIoTControllerScheme:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return LaundryIoTControllerScheme.make(
            model=controller,
            state=await self.iot_storage.get_state(controller.id),
            energy_state=await self.iot_storage.get_energy_state(controller.id),
            is_online=await self.check_online(controller),
        )

    async def update(self, data: UpdateLaudnrySettingsRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        for key, value in data.settings.model_dump(exclude_none=True).items():
            if hasattr(controller, key):
                setattr(controller, key, value)

        await self.controller_repository.commit()

    async def create_invoice(
        self, data: CreateLaundryInvoiceRequest
    ) -> CreateInvoiceResponse:
        controller = await self._get_controller(data.controller_id)

        if (
            data.gateway_type is PaymentGatewayType.LIQPAY
            and not controller.liqpay_active
        ) or (
            data.gateway_type is PaymentGatewayType.MONOPAY
            and not controller.monopay_active
        ):
            raise UnsupportedPaymentGatewayTypeError

        if controller.laundry_status is not LaundryStatus.AVAILABLE:
            raise ControllerIsBusyError

        await self.healthcheck(controller.device_id)

        amount = (
            controller.fixed_price
            if controller.tariff_type is LaundryTariffType.FIXED
            else controller.max_hold_amount
        )
        should_hold_money = controller.tariff_type is LaundryTariffType.PER_MINUTE

        controller = await self._get_controller(data.controller_id)
        invoice_result = await self.payment_helper.create_invoice(
            controller=controller,
            amount=amount,
            gateway_type=data.gateway_type,
            hold_money=should_hold_money,
        )
        payment = self.payment_helper.create_payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            payment_type=PaymentType.CASHLESS,
            gateway_type=data.gateway_type,
            amount=amount,
            invoice_id=invoice_result.invoice_id,
        )
        await self.payment_helper.save_and_commit(payment)

        return invoice_result

    async def handle_door_locked(self, controller_id: UUID) -> None:
        controller = await self._get_controller(controller_id)
        controller.laundry_status = LaundryStatus.IN_USE

        transaction = await self.transaction_repository.get_laundry_active(
            controller_id
        )
        if transaction:
            transaction.session_status = LaundrySessionStatus.IN_PROGRESS
            transaction.session_start_time = datetime.now()

        await self.iot_client.lock_button_and_turn_off_led(
            device_id=controller.device_id,
            relay_id=controller.button_relay_id,
            output_id=controller.led_output_id,
        )
        await self.controller_repository.commit()

    async def handle_door_unlocked(self, controller_id: UUID) -> None:
        controller = await self._get_controller(controller_id)
        controller.laundry_status = LaundryStatus.AVAILABLE

        transaction = await self.transaction_repository.get_laundry_active(
            controller_id
        )
        if transaction:
            if controller.tariff_type == LaundryTariffType.PER_MINUTE:
                self._calculate_per_minute_tariff(transaction, controller)
                await self.payment_helper.finalize_hold(
                    controller, transaction.payment, transaction.final_amount
                )
                transaction.qr_amount = transaction.final_amount

            transaction.session_status = LaundrySessionStatus.COMPLETED
            transaction.session_end_time = datetime.now()

        await self.controller_repository.commit()

    async def handle_idle_state(self, controller_id: UUID) -> None:
        controller = await self._get_controller(controller_id)
        if controller.laundry_status is LaundryStatus.AVAILABLE:
            return

        controller.laundry_status = LaundryStatus.AVAILABLE

        transaction = await self.transaction_repository.get_laundry_active(
            controller_id
        )
        if transaction:
            transaction.session_status = LaundrySessionStatus.TIMEOUT

        await self.controller_repository.commit()

    async def process_hold_status(self, payment: Payment) -> None:
        await self._start_laundry_session(payment)

    async def process_success_status(self, payment: Payment) -> None:
        controller = await self._get_controller(payment.controller_id)
        if controller.tariff_type is LaundryTariffType.FIXED:
            return await self._start_laundry_session(payment)

        await super().process_success_status(payment)

    async def _start_laundry_session(self, payment: Payment) -> None:
        controller = await self._get_controller(payment.controller_id)

        if controller.laundry_status is not LaundryStatus.AVAILABLE:
            raise ValueError(f"Controller is not available: {controller.status}")

        if controller.tariff_type is LaundryTariffType.PER_MINUTE:
            hold_amount = controller.max_hold_amount
            final_amount = 0
        else:
            hold_amount = 0
            final_amount = payment.amount

        transaction = LaundryTransaction(
            controller_id=controller.id,
            location_id=controller.location_id,
            payment_id=payment.id,
            tariff_type=controller.tariff_type,
            session_status=LaundrySessionStatus.WAITING_START,
            sale_type="money",
            hold_amount=hold_amount,
            final_amount=final_amount,
            qr_amount=final_amount or hold_amount,
        )
        self.transaction_repository.add(transaction)

        try:
            await self.iot_client.unlock_button_and_turn_on_led(
                device_id=controller.device_id,
                duration_mins=controller.timeout_minutes,
                relay_id=controller.button_relay_id,
                ouput_id=controller.led_output_id,
            )
            controller.laundry_status = LaundryStatus.PROCESSING
        except (ControllerTimeoutError, ControllerResponseError):
            logger.error(
                "Failed to unlock laundry machine",
                controller_id=controller.id,
                device_id=controller.device_id,
            )
            await self.payment_helper.refund(controller, payment)
            transaction.session_status = LaundrySessionStatus.ERROR
            controller.laundry_status = LaundryStatus.AVAILABLE
        finally:
            if controller.tariff_type is LaundryTariffType.PER_MINUTE:
                payment.status = PaymentStatus.HOLD
            else:
                payment.status = PaymentStatus.COMPLETED

            await self.transaction_repository.commit()

    def _calculate_per_minute_tariff(
        self, transaction: LaundryTransaction, controller: LaundryController
    ) -> None:
        if not transaction.session_start_time or not transaction.hold_amount:
            raise ValueError("Transaction is invalid")

        duration = datetime.now(UTC) - transaction.session_start_time
        duration_minutes = int(duration.total_seconds() / 60)

        minutes_before_transition = min(
            controller.transition_after_minutes, duration_minutes
        )
        amount_before_transition = (
            controller.price_per_minute_before_transition * minutes_before_transition
        )
        minutes_after_transition = max(
            0, duration_minutes - controller.transition_after_minutes
        )
        amount_after_transition = (
            controller.price_per_minute_after_transition * minutes_after_transition
        )
        transaction.final_amount = min(
            amount_before_transition + amount_after_transition,
            transaction.hold_amount,
        )
        transaction.refund_amount = transaction.hold_amount - transaction.final_amount
        transaction.payment.amount = transaction.final_amount
