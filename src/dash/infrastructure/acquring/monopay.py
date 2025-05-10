import base64
import hashlib
import json
from datetime import datetime
from typing import Literal
from uuid import UUID

import aiohttp
import ecdsa
from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from redis.asyncio import Redis

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.acquring import AcquringStorage
from dash.main.config import MonopayConfig
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.base import ValidationError
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.water_vending.dto import QRPaymentDTO, SendQRPaymentRequest
from dash.services.water_vending.water_vending import WaterVendingService


class ProcessWebhookRequest(BaseModel):
    body: bytes
    signature: str


class CreateInvoiceRequest(BaseModel):
    controller_id: UUID
    amount: int

    @field_validator("amount")
    @classmethod
    def validate(cls, v: int) -> int:
        if v < 1:
            raise ValidationError("'amount' cannot be less than 1")
        return v


class CreateInvoiceResponse(BaseModel):
    invoice_url: str


class MonopayService:
    def __init__(
        self,
        config: MonopayConfig,
        acquring_storage: AcquringStorage,
        payment_repository: PaymentRepository,
        controller_repository: ControllerRepository,
        water_vending_service: WaterVendingService,
        locker: Redis,
    ):
        self.config = config
        self.acquring_storage = acquring_storage
        self.base_url = "https://api.monobank.ua/api"
        self.payment_repository = payment_repository
        self.controller_repository = controller_repository
        self.water_vending_service = water_vending_service
        self.locker = locker
        self.token: str

    async def _check_response(self, response: aiohttp.ClientResponse) -> None:
        if response.status != 200:
            raise HTTPException(status_code=503, detail="Failed to connect to Monobank")

    async def make_request(
        self, method: Literal["GET", "POST"], endpoint: str, data: dict | None = None
    ) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                self.base_url + endpoint,
                headers={"X-Token": self.token},
                json=data,
            ) as response:
                await self._check_response(response)
                return await response.json()

    async def _request_pub_key(self, invoice_id: str) -> bytes:
        response = await self.make_request(method="GET", endpoint="/merchant/pubkey")

        pub_key = response["key"]
        pub_key_bytes = base64.b64decode(pub_key)

        await self.acquring_storage.set_monopay_pub_key(pub_key_bytes, invoice_id)
        return pub_key_bytes

    def _verify_pub_key(self, body: bytes, signature: bytes, pub_key: bytes) -> bool:
        key = ecdsa.VerifyingKey.from_pem(pub_key.decode())
        return key.verify(
            signature=signature,
            data=body,
            sigdecode=ecdsa.util.sigdecode_der,  # type: ignore
            hashfunc=hashlib.sha256,
        )

    async def _verify_signature(self, sign: str, body: bytes, invoice_id: str) -> None:
        signature = base64.b64decode(sign)
        pub_key = await self.acquring_storage.get_monopay_pub_key(invoice_id)

        if pub_key is None:
            pub_key = await self._request_pub_key(invoice_id)

        for attempt in range(2):
            if self._verify_pub_key(body, signature, pub_key):
                return
            if attempt == 2:
                break
            pub_key = await self._request_pub_key(invoice_id)

        raise HTTPException(status_code=400, detail="Invalid signature")

    async def create_invoice(self, data: CreateInvoiceRequest) -> CreateInvoiceResponse:
        controller = await self.controller_repository.get(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        if not controller.monopay_active or not controller.monopay_token:
            raise HTTPException(
                status_code=400, detail="Controller is not supported Monopay"
            )

        await self.water_vending_service.healtcheck(controller.device_id)

        self.token = controller.monopay_token
        response = await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/create",
            data={
                "amount": data.amount,
                "ccy": 980,
                "webHookUrl": self.config.webhook_url,
                "redirectUrl": self.config.redirect_url,
                "paymentType": "hold",
            },
        )
        invoice_id = response["invoiceId"]

        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            invoice_id=invoice_id,
            status=PaymentStatus.CREATED,
            amount=data.amount,
            type=PaymentType.MONOPAY,
        )
        self.payment_repository.add(payment)
        await self.payment_repository.commit()

        await self.acquring_storage.set_monopay_token(
            token=controller.monopay_token, invoice_id=invoice_id
        )

        return CreateInvoiceResponse(invoice_url=response["pageUrl"])

    async def _finalize(self, invoice_id: str, amount: int) -> None:
        await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/finalize",
            data={"invoiceId": invoice_id, "amount": amount},
        )

    async def _refund(self, invoice_id: str) -> None:
        await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/cancel",
            data={"invoiceId": invoice_id},
        )

    async def process_webhook(self, data: ProcessWebhookRequest) -> None:
        body = json.loads(data.body.decode())
        invoice_id = body["invoiceId"]

        token = await self.acquring_storage.get_monopay_token(invoice_id)
        if not token:
            payment = await self.payment_repository.get_by_invoice_id(invoice_id)
            if not payment:
                return
            controller = await self.controller_repository.get(payment.controller_id)
            if not controller:
                return
            if not controller.monopay_token:
                return
            token = controller.monopay_token

        self.token = token
        await self._verify_signature(
            sign=data.signature, body=data.body, invoice_id=invoice_id
        )

        async with self.locker.lock(
            f"monopay_webhook:{invoice_id}",
            timeout=10,
            blocking=True,
            blocking_timeout=10,
        ):
            await self._process_webhook_locked(invoice_id, body)

    async def _process_webhook_locked(self, invoice_id: str, body: dict) -> None:
        status = body["status"]
        current_modified_date = datetime.fromisoformat(body["modifiedDate"])
        last_modified_date = await self.acquring_storage.get_last_modified_date(
            invoice_id
        )

        if last_modified_date:
            if last_modified_date == current_modified_date and status not in [
                "failure",
                "reversed",
                "success",
            ]:
                return
            elif last_modified_date > current_modified_date:
                return

        await self.acquring_storage.set_last_modified_date(
            invoice_id, current_modified_date
        )

        payment = await self.payment_repository.get_by_invoice_id(invoice_id)
        if not payment:
            raise HTTPException(status_code=400, detail="Payment not found")

        if status == "processing":
            payment.status = PaymentStatus.PROCESSING

        elif status == "success":
            payment.status = PaymentStatus.COMPLETED

        elif status == "reversed":
            payment.status = PaymentStatus.REVERSED

        elif status == "failure":
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = body["failureReason"]

        elif status == "hold":
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
                await self._refund(invoice_id)
                payment.failure_reason = (
                    "Не вдалося відправити запит контролеру на оплату"
                )
            else:
                await self._finalize(invoice_id, payment.amount)

        await self.payment_repository.commit()
