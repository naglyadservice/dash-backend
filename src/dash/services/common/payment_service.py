from typing import Protocol

from dash.models.controllers import Controller
from dash.models.payment import Payment
from dash.services.iot.dto import CreateInvoiceResponse


class PaymentService(Protocol):
    async def create_invoice(
        self,
        controller: Controller,
        amount: int,
        hold_money: bool = True,
    ) -> CreateInvoiceResponse:
        raise NotImplementedError

    async def refund(self, controller: Controller, payment: Payment) -> None:
        raise NotImplementedError

    async def finalize(
        self, controller: Controller, payment: Payment, amount: int
    ) -> None:
        raise NotImplementedError
