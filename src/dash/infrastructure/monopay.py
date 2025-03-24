import base64
import hashlib
import json
from datetime import datetime
from typing import Literal

import aiohttp
import ecdsa
from fastapi import HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis

from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.acquring import AcquringStorage
from dash.main.config import MonopayConfig
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.water_vending.dto import SendQRPaymentRequest
from dash.services.water_vending.water_vending import WaterVendingService


class ProcessWebhookRequest(BaseModel):
    body: bytes
    signature: str


class CreateInvoiceRequest(BaseModel):
    controller_id: int
    amount: int


class CreateInvoiceResponse(BaseModel):
    invoice_url: str


class MonopayService:
    def __init__(
        self,
        config: MonopayConfig,
        acquring_storage: AcquringStorage,
        payment_repository: PaymentRepository,
        water_vending_service: WaterVendingService,
        locker: Redis,
    ):
        self.config = config
        self.acquring_storage = acquring_storage
        self.base_url = "https://api.monobank.ua/api"
        self.payment_repository = payment_repository
        self.water_vending_service = water_vending_service
        self.locker = locker

    def _check_response(self, response: aiohttp.ClientResponse) -> None:
        if response.status != 200:
            raise HTTPException(status_code=503, detail="Failed to connect to Monobank")

    async def make_request(
        self, method: Literal["GET", "POST"], endpoint: str, data: dict | None = None
    ) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                self.base_url + endpoint,
                headers={"X-Token": self.config.token},
                json=data,
            ) as response:
                self._check_response(response)
                return await response.json()

    async def _request_pub_key(self) -> bytes:
        response = await self.make_request(method="GET", endpoint="/merchant/pubkey")

        pub_key = response["key"]
        pub_key_bytes = base64.b64decode(pub_key)

        await self.acquring_storage.set_monopay_pub_key(pub_key_bytes)

        return pub_key_bytes

    def _verify_pub_key(self, body: bytes, signature: bytes, pub_key: bytes) -> bool:
        key = ecdsa.VerifyingKey.from_pem(pub_key.decode())
        return key.verify(
            signature=signature,
            data=body,
            sigdecode=ecdsa.util.sigdecode_der,  # type: ignore
            hashfunc=hashlib.sha256,
        )

    async def _verify_signature(self, data: ProcessWebhookRequest) -> None:
        signature = base64.b64decode(data.signature)
        pub_key = await self.acquring_storage.get_monopay_pub_key()
        attempts = 0

        if pub_key is None:
            pub_key = await self._request_pub_key()
            attempts += 1

        while attempts < 2:
            if self._verify_pub_key(data.body, signature, pub_key):
                return
            pub_key = await self._request_pub_key()
            attempts += 1

        raise HTTPException(status_code=400, detail="Invalid signature")

    async def create_invoice(self, data: CreateInvoiceRequest) -> CreateInvoiceResponse:
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

        payment = Payment(
            controller_id=data.controller_id,
            invoice_id=response["invoiceId"],
            status=PaymentStatus.CREATED,
            amount=data.amount,
            type=PaymentType.MONOPAY,
            created_at=datetime.now(),
        )
        self.payment_repository.add(payment)
        await self.payment_repository.commit()

        return CreateInvoiceResponse(invoice_url=response["pageUrl"])

    async def _finalize_invoice(self, invoice_id: str, amount: int) -> None:
        await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/finalize",
            data={"invoiceId": invoice_id, "amount": amount},
        )

    async def _cancel_invoice(self, invoice_id: str) -> None:
        await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/cancel",
            data={"invoiceId": invoice_id},
        )

    async def process_webhook(self, data: ProcessWebhookRequest) -> None:
        await self._verify_signature(data)

        body = json.loads(data.body.decode())
        invoice_id = body["invoiceId"]

        async with self.locker.lock(
            f"mono_hook:{invoice_id}",
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
                        order_id=invoice_id,
                        controller_id=payment.controller_id,
                        amount=payment.amount,
                    )
                )
            except Exception:
                await self._cancel_invoice(invoice_id)
                payment.failure_reason = (
                    "Не вдалося відправити запит контролеру на оплату"
                )
            else:
                await self._finalize_invoice(invoice_id, payment.amount)

        await self.payment_repository.commit()
