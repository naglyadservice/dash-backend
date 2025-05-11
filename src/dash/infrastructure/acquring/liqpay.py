import base64
import json
import uuid

from fastapi import HTTPException
from liqpay.liqpay3 import LiqPay
from pydantic import BaseModel

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.main.config import LiqpayConfig
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.water_vending.dto import QRPaymentDTO, SendQRPaymentRequest
from dash.services.water_vending.water_vending import WaterVendingService


class CreateLiqpayInvoiceRequest(BaseModel):
    controller_id: uuid.UUID
    amount: int


class CreateLiqpayInvoiceResponse(BaseModel):
    invoice_url: str


class ProcessLiqpayWebhookRequest(BaseModel):
    body: str
    signature: str


class LiqpayService:
    def __init__(
        self,
        config: LiqpayConfig,
        water_vending_service: WaterVendingService,
        controller_repository: ControllerRepository,
        payment_repository: PaymentRepository,
    ):
        self.config = config
        self.water_vending_service = water_vending_service
        self.controller_repository = controller_repository
        self.payment_repository = payment_repository

    def _get_client(self, public_key: str, private_key: str) -> LiqPay:
        return LiqPay(public_key, private_key)

    async def create_invoice(
        self, data: CreateLiqpayInvoiceRequest
    ) -> CreateLiqpayInvoiceResponse:
        controller = await self.controller_repository.get(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        if not controller.liqpay_active or not (
            controller.liqpay_public_key and controller.liqpay_private_key
        ):
            raise HTTPException(
                status_code=400, detail="Controller is not supported Liqpay"
            )

        await self.water_vending_service.healtcheck(controller.device_id)

        invoice_id = str(uuid.uuid4())
        params = {
            "action": "hold",
            "amount": data.amount,
            "currency": "UAH",
            "description": f"Аренда контроллера {controller.device_id}",
            "order_id": invoice_id,
            "version": "3",
            "result_url": self.config.redirect_url,
            "server_url": self.config.webhook_url,
        }
        client = self._get_client(
            controller.liqpay_public_key, controller.liqpay_private_key
        )
        liqpay_data, signature = client.cnb_data(params), client.cnb_signature(params)
        invoice_url = f"https://www.liqpay.ua/api/3/checkout?data={liqpay_data}&signature={signature}"

        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            invoice_id=invoice_id,
            status=PaymentStatus.CREATED,
            amount=data.amount,
            type=PaymentType.LIQPAY,
        )
        self.payment_repository.add(payment)
        await self.payment_repository.commit()

        return CreateLiqpayInvoiceResponse(invoice_url=invoice_url)

    def _refund(self, client: LiqPay, order_id: str, amount: int) -> None:
        client.api(
            "request",
            {
                "action": "refund",
                "order_id": order_id,
                "version": "3",
                "amount": amount,
            },
        )

    def _finalize(self, client: LiqPay, order_id: str, amount: int) -> None:
        client.api(
            "request",
            {
                "action": "hold_completion",
                "order_id": order_id,
                "version": "3",
                "amount": amount,
            },
        )

    async def process_webhook(self, data: ProcessLiqpayWebhookRequest) -> None:
        dict_data = json.loads(base64.b64decode(data.body).decode("utf-8"))
        print(dict_data)
        invoice_id = dict_data["order_id"]

        payment = await self.payment_repository.get_by_invoice_id(invoice_id)
        if not payment:
            return

        controller = await self.controller_repository.get(payment.controller_id)
        if not controller or not (
            controller.liqpay_public_key and controller.liqpay_private_key
        ):
            return

        client = self._get_client(
            controller.liqpay_public_key, controller.liqpay_private_key
        )

        calculated_signature = client.str_to_sign(
            controller.liqpay_private_key + data.body + controller.liqpay_private_key
        )
        if calculated_signature != data.signature:
            print(data.signature, calculated_signature)
            raise HTTPException(status_code=400, detail="Invalid signature")

        status = dict_data["status"]
        if status == "hold_wait":
            payment.status = PaymentStatus.HOLD
            try:
                await self.water_vending_service.send_qr_payment(
                    SendQRPaymentRequest(
                        controller_id=payment.controller_id,
                        payment=QRPaymentDTO(
                            amount=payment.amount, order_id=invoice_id
                        ),
                    )
                )
            except Exception:
                self._refund(client, invoice_id, payment.amount)
                payment.failure_reason = (
                    "Не вдалося відправити запит контролеру на оплату"
                )
            else:
                self._finalize(client, invoice_id, payment.amount)

        elif status == "processing":
            payment.status = PaymentStatus.PROCESSING

        elif status == "success":
            payment.status = PaymentStatus.COMPLETED

        elif status == "reversed":
            payment.status = PaymentStatus.REVERSED

        elif status in ("failure", "error"):
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = dict_data["err_description"]

        await self.payment_repository.commit()
