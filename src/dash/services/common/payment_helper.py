import asyncio
from uuid import UUID

from uuid_utils.compat import uuid7

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.acquiring.liqpay import LiqpayGateway
from dash.infrastructure.acquiring.monopay import MonopayGateway
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models import Controller
from dash.models.payment import PaymentType, PaymentGatewayType, PaymentStatus, Payment
from dash.services.common.payment_gateway import PaymentGateway
from dash.services.iot.dto import CreateInvoiceResponse


class PaymentHelper:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        monopay_gateway: MonopayGateway,
        liqpay_gateway: LiqpayGateway,
        checkbox_service: CheckboxService,
    ) -> None:
        self.payment_repository = payment_repository
        self.monopay_gateway = monopay_gateway
        self.liqpay_gateway = liqpay_gateway
        self.checkbox_service = checkbox_service

    @staticmethod
    def create_payment(
        controller_id: UUID,
        location_id: UUID | None,
        amount: int,
        payment_type: PaymentType,
        status: PaymentStatus = PaymentStatus.CREATED,
        gateway_type: PaymentGatewayType | None = None,
        invoice_id: str | None = None,
        transaction_id: UUID | None = None,
    ) -> Payment:
        payment = Payment(
            controller_id=controller_id,
            location_id=location_id,
            transaction_id=transaction_id,
            amount=amount,
            type=payment_type,
            status=status,
            gateway_type=gateway_type,
            invoice_id=invoice_id,
        )
        return payment

    def save(self, payment: Payment) -> None:
        self.payment_repository.add(payment)

    async def commit(self) -> None:
        await self.payment_repository.commit()

    async def save_and_commit(self, payment: Payment) -> None:
        self.save(payment)
        await self.commit()

    async def create_invoice(
        self,
        controller: Controller,
        amount: int,
        gateway_type: PaymentGatewayType,
        hold_money: bool = False,
    ) -> CreateInvoiceResponse:
        gateway = self._get_payment_gateway(gateway_type)
        return await gateway.create_invoice(controller, amount, hold_money)

    async def refund(self, controller: Controller, payment: Payment) -> None:
        gateway = self._get_payment_gateway(payment.gateway_type)
        await gateway.refund(controller, payment)

    async def finalize_hold(
        self, controller: Controller, payment: Payment, amount: int
    ) -> None:
        gateway = self._get_payment_gateway(payment.gateway_type)
        await gateway.finalize(controller, payment, amount)

    async def fiscalize(self, controller: Controller, payment: Payment) -> None:
        receipt_id = uuid7()
        asyncio.create_task(
            self.checkbox_service.create_receipt(controller, payment, receipt_id)
        )
        payment.receipt_id = receipt_id

    def _get_payment_gateway(self, gateway_type: PaymentGatewayType) -> PaymentGateway:
        if gateway_type is PaymentGatewayType.LIQPAY:
            return self.liqpay_gateway
        elif gateway_type is PaymentGatewayType.MONOPAY:
            return self.monopay_gateway
        else:
            raise ValueError(f"No payment processor for {gateway_type.value} payment")
