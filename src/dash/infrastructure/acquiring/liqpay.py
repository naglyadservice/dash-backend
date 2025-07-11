import base64
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.api_client import APIClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.main.config import LiqpayConfig
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.base import ValidationError
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.errors.customer_carwash import InsufficientDepositAmountError
from dash.services.iot.factory import IoTServiceFactory


class CreateLiqpayInvoiceRequest(BaseModel):
    controller_id: uuid.UUID
    amount: int


class CreateLiqpayInvoiceResponse(BaseModel):
    invoice_url: str


class ProcessLiqpayWebhookRequest(BaseModel):
    body: str
    signature: str


@dataclass
class ControllerNotSupportLiqpayError(ValidationError):
    message: str = "Controller does not support LiqPay"


class LiqpayService:
    def __init__(
        self,
        config: LiqpayConfig,
        service_factory: IoTServiceFactory,
        controller_repository: ControllerRepository,
        payment_repository: PaymentRepository,
        checkbox_service: CheckboxService,
    ):
        self.config = config
        self.factory = service_factory
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
        self, data: CreateLiqpayInvoiceRequest
    ) -> CreateLiqpayInvoiceResponse:
        controller = await self.controller_repository.get(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        if not controller.liqpay_active or not (
            controller.liqpay_public_key and controller.liqpay_private_key
        ):
            raise ControllerNotSupportLiqpayError

        if data.amount < controller.min_deposit_amount:
            raise InsufficientDepositAmountError

        await self.factory.get(controller.type).healthcheck(controller.device_id)

        invoice_id = str(uuid.uuid4())
        liqpay_data = {
            "public_key": controller.liqpay_public_key,
            "action": "hold",
            "amount": data.amount / 100,
            "currency": "UAH",
            "description": f"Поповнення для {controller.name}",
            "order_id": invoice_id,
            "version": "3",
            "result_url": self.config.redirect_url,
            "server_url": self.config.webhook_url,
        }
        params = self._prepare_data(liqpay_data, controller.liqpay_private_key)
        invoice_url = f"https://www.liqpay.ua/api/3/checkout?data={params['data']}&signature={params['signature']}"

        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            amount=data.amount,
            type=PaymentType.LIQPAY,
            status=PaymentStatus.CREATED,
            invoice_id=invoice_id,
        )
        self.payment_repository.add(payment)
        await self.payment_repository.commit()

        return CreateLiqpayInvoiceResponse(invoice_url=invoice_url)

    async def _refund(
        self, private_key: str, public_key: str, order_id: str, amount: int
    ) -> None:
        await self._make_request(
            method="POST",
            data=self._prepare_data(
                {
                    "public_key": public_key,
                    "action": "refund",
                    "order_id": order_id,
                    "version": "3",
                    "amount": amount / 100,
                },
                private_key,
            ),
        )

    async def _finalize(
        self, private_key: str, public_key: str, order_id: str, amount: int
    ) -> None:
        await self._make_request(
            method="POST",
            data=self._prepare_data(
                {
                    "public_key": public_key,
                    "action": "hold_completion",
                    "order_id": order_id,
                    "version": "3",
                    "amount": amount / 100,
                },
                private_key,
            ),
        )

    async def process_webhook(self, data: ProcessLiqpayWebhookRequest) -> None:
        dict_data = json.loads(base64.b64decode(data.body).decode("utf-8"))
        invoice_id = dict_data["order_id"]

        payment = await self.payment_repository.get_by_invoice_id(invoice_id)
        if not payment:
            return

        controller = await self.controller_repository.get(payment.controller_id)
        if not controller or not (
            controller.liqpay_public_key and controller.liqpay_private_key
        ):
            return

        if not self._verify_signature(
            private_key=controller.liqpay_private_key,
            data_to_sign=data.body,
            signature=data.signature,
        ):
            raise HTTPException(status_code=400, detail="Invalid signature")

        status = dict_data["status"]
        if status == "hold_wait":
            payment.status = PaymentStatus.HOLD
            try:
                await self.factory.get(controller.type).send_qr_payment_infra(
                    device_id=controller.device_id,
                    order_id=invoice_id,
                    amount=payment.amount,
                )
            except Exception:
                await self._refund(
                    private_key=controller.liqpay_private_key,
                    public_key=controller.liqpay_public_key,
                    order_id=invoice_id,
                    amount=payment.amount,
                )
                payment.failure_reason = (
                    "Не вдалося відправити запит контролеру на оплату"
                )
            else:
                await self._finalize(
                    private_key=controller.liqpay_private_key,
                    public_key=controller.liqpay_public_key,
                    order_id=invoice_id,
                    amount=payment.amount,
                )

        elif status == "processing":
            payment.status = PaymentStatus.PROCESSING

        elif status == "success":
            payment.status = PaymentStatus.COMPLETED
            if controller.checkbox_active:
                payment.receipt_id = await self.checkbox_service.create_receipt(
                    controller, payment
                )

        elif status == "reversed":
            payment.status = PaymentStatus.REVERSED
            if controller.checkbox_active:
                payment.receipt_id = await self.checkbox_service.create_receipt(
                    controller, payment, is_return=True
                )

        elif status in ("failure", "error"):
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = dict_data["err_description"]

        await self.payment_repository.commit()

    def _data_to_sign(self, params: dict[str, Any]) -> str:
        json_encoded_params = json.dumps(params, sort_keys=True)
        bytes_data = json_encoded_params.encode("utf-8")
        return base64.b64encode(bytes_data).decode("utf-8")

    def _make_signature(self, private_key: str, data_to_sign: str) -> str:
        joined_fields = private_key + data_to_sign + private_key
        joined_fields = joined_fields.encode("utf-8")
        return base64.b64encode(hashlib.sha1(joined_fields).digest()).decode("ascii")

    def _verify_signature(
        self, private_key: str, data_to_sign: str, signature: str
    ) -> bool:
        calculated_signature = self._make_signature(private_key, data_to_sign)
        return calculated_signature == signature
