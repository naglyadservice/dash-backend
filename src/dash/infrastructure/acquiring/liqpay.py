import base64
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from structlog import get_logger

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.api_client import APIClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.main.config import LiqpayConfig
from dash.models.controllers import Controller
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.base import ValidationError
from dash.services.common.errors.customer_carwash import InsufficientDepositAmountError
from dash.services.common.payment_service import PaymentService
from dash.services.iot.dto import CreateInvoiceResponse


@dataclass
class ControllerNotSupportLiqpayError(ValidationError):
    message: str = "Controller does not support LiqPay"


logger = get_logger()


class LiqpayService(PaymentService):
    def __init__(
        self,
        config: LiqpayConfig,
        controller_repository: ControllerRepository,
        payment_repository: PaymentRepository,
        checkbox_service: CheckboxService,
    ):
        self.config = config
        self.controller_repository = controller_repository
        self.payment_repository = payment_repository
        self.checkbox_service = checkbox_service
        self.api_client = APIClient()
        self.base_url = "https://www.liqpay.ua/api/request"

    def _prepare_data(self, data: dict[str, Any], private_key: str) -> dict[str, Any]:
        return {
            "data": self._data_to_sign(data),
            "signature": self._make_signature(private_key, self._data_to_sign(data)),
        }

    async def _make_request(
        self,
        method: Literal["GET", "POST"],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        response, status = await self.api_client.make_request(
            method=method,
            url=self.base_url,
            data=data,
        )
        return response

    async def create_invoice(
        self,
        controller: Controller,
        amount: int,
        hold_money: bool = True,
    ) -> CreateInvoiceResponse:
        if not controller.liqpay_active or not (
            controller.liqpay_public_key and controller.liqpay_private_key
        ):
            raise ControllerNotSupportLiqpayError

        if amount < controller.min_deposit_amount:
            raise InsufficientDepositAmountError

        invoice_id = str(uuid.uuid4())
        liqpay_data = {
            "public_key": controller.liqpay_public_key,
            "action": "hold" if hold_money else "pay",
            "amount": amount / 100,
            "currency": "UAH",
            "description": f"Поповнення для {controller.name}",
            "order_id": str(invoice_id),
            "version": "3",
            "result_url": self.config.redirect_url,
            "server_url": self.config.webhook_url,
        }
        params = self._prepare_data(liqpay_data, controller.liqpay_private_key)
        invoice_url = f"https://www.liqpay.ua/api/3/checkout?data={params['data']}&signature={params['signature']}"

        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            amount=amount,
            type=PaymentType.LIQPAY,
            status=PaymentStatus.CREATED,
            invoice_id=invoice_id,
        )
        self.payment_repository.add(payment)
        await self.payment_repository.commit()

        return CreateInvoiceResponse(invoice_url=invoice_url, invoice_id=invoice_id)

    async def refund(self, controller: Controller, payment: Payment) -> None:
        if not controller.liqpay_active or not controller.liqpay_private_key:
            raise ControllerNotSupportLiqpayError

        await self._make_request(
            method="POST",
            data=self._prepare_data(
                {
                    "public_key": controller.liqpay_public_key,
                    "action": "refund",
                    "order_id": payment.invoice_id,
                    "version": "3",
                    "amount": payment.amount / 100,
                },
                controller.liqpay_private_key,
            ),
        )

    async def finalize(
        self, controller: Controller, payment: Payment, amount: int
    ) -> None:
        if not controller.liqpay_active or not controller.liqpay_private_key:
            raise ControllerNotSupportLiqpayError

        await self._make_request(
            method="POST",
            data=self._prepare_data(
                {
                    "public_key": controller.liqpay_public_key,
                    "action": "hold_completion",
                    "order_id": payment.invoice_id,
                    "version": "3",
                    "amount": amount / 100,
                },
                controller.liqpay_private_key,
            ),
        )

    def _data_to_sign(self, params: dict[str, Any]) -> str:
        json_encoded_params = json.dumps(params, sort_keys=True)
        bytes_data = json_encoded_params.encode("utf-8")
        return base64.b64encode(bytes_data).decode("utf-8")

    def _make_signature(self, private_key: str, data_to_sign: str) -> str:
        joined_fields = private_key + data_to_sign + private_key
        joined_fields = joined_fields.encode("utf-8")
        return base64.b64encode(hashlib.sha1(joined_fields).digest()).decode("ascii")

    def verify_signature(
        self, private_key: str, data_to_sign: str, signature: str
    ) -> bool:
        calculated_signature = self._make_signature(private_key, data_to_sign)
        return calculated_signature == signature
