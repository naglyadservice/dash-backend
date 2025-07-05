import base64
import hashlib
import json
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

import ecdsa
from fastapi import HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.api_client import APIClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.acquiring import AcquiringStorage
from dash.main.config import MonopayConfig
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.errors.customer_carwash import InsufficientDepositAmountError
from dash.services.iot.factory import IoTServiceFactory


class ProcessWebhookRequest(BaseModel):
    body: bytes
    signature: str


class CreateInvoiceRequest(BaseModel):
    controller_id: UUID
    amount: int


class CreateInvoiceResponse(BaseModel):
    invoice_url: str


class MonopayService:
    def __init__(
        self,
        config: MonopayConfig,
        acquiring_storage: AcquiringStorage,
        payment_repository: PaymentRepository,
        checkbox_service: CheckboxService,
        controller_repository: ControllerRepository,
        service_factory: IoTServiceFactory,
        locker: Redis,
    ):
        self.config = config
        self.acquiring_storage = acquiring_storage
        self.base_url = "https://api.monobank.ua/api"
        self.payment_repository = payment_repository
        self.checkbox_service = checkbox_service
        self.controller_repository = controller_repository
        self.factory = service_factory
        self.locker = locker
        self.api_client = APIClient()

    def _prepare_headers(self, token: str) -> dict[str, str]:
        return {"X-Token": token}

    async def make_request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response, status = await self.api_client.make_request(
            method=method,
            url=self.base_url + endpoint,
            headers=headers,
            json=json,
        )
        if status != 200:
            raise HTTPException(status_code=503, detail="Failed to connect to Monobank")

        return response

    async def _request_pub_key(self, invoice_id: str, token: str) -> bytes:
        response = await self.make_request(
            method="GET",
            endpoint="/merchant/pubkey",
            headers=self._prepare_headers(token),
        )

        pub_key = response["key"]
        pub_key_bytes = base64.b64decode(pub_key)

        await self.acquiring_storage.set_monopay_pub_key(pub_key_bytes, invoice_id)
        return pub_key_bytes

    @staticmethod
    def _verify_pub_key(body: bytes, signature: bytes, pub_key: bytes) -> bool:
        key = ecdsa.VerifyingKey.from_pem(pub_key.decode())
        return key.verify(
            signature=signature,
            data=body,
            sigdecode=ecdsa.util.sigdecode_der,  # type: ignore
            hashfunc=hashlib.sha256,
        )

    async def _verify_signature(
        self, sign: str, body: bytes, invoice_id: str, token: str
    ) -> None:
        signature = base64.b64decode(sign)
        pub_key = await self.acquiring_storage.get_monopay_pub_key(invoice_id) or b""

        if not pub_key or not self._verify_pub_key(body, signature, pub_key):
            pub_key = await self._request_pub_key(invoice_id, token)

        if self._verify_pub_key(body, signature, pub_key):
            return

        raise HTTPException(status_code=400, detail="Invalid signature")

    async def create_invoice(self, data: CreateInvoiceRequest) -> CreateInvoiceResponse:
        controller = await self.controller_repository.get(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        if not controller.monopay_active or not controller.monopay_token:
            raise HTTPException(
                status_code=400, detail="Controller is not supported Monopay"
            )

        if data.amount < controller.min_deposit_amount:
            raise InsufficientDepositAmountError

        await self.factory.get(controller.type).healthcheck(controller.device_id)

        response = await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/create",
            json={
                "amount": data.amount,
                "ccy": 980,
                "webHookUrl": self.config.webhook_url,
                "redirectUrl": self.config.redirect_url,
                "paymentType": "hold",
            },
            headers=self._prepare_headers(controller.monopay_token),
        )
        invoice_id = response["invoiceId"]

        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            amount=data.amount,
            type=PaymentType.MONOPAY,
            status=PaymentStatus.CREATED,
            invoice_id=invoice_id,
        )
        self.payment_repository.add(payment)
        await self.payment_repository.commit()

        await self.acquiring_storage.set_monopay_token(
            token=controller.monopay_token, invoice_id=invoice_id
        )

        return CreateInvoiceResponse(invoice_url=response["pageUrl"])

    async def _finalize(self, invoice_id: str, amount: int, token: str) -> None:
        await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/finalize",
            json={"invoiceId": invoice_id, "amount": amount},
            headers=self._prepare_headers(token),
        )

    async def _refund(self, invoice_id: str, token: str) -> None:
        await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/cancel",
            json={"invoiceId": invoice_id},
            headers=self._prepare_headers(token),
        )

    async def process_webhook(self, data: ProcessWebhookRequest) -> None:
        body = json.loads(data.body.decode())
        invoice_id = body["invoiceId"]

        token = await self.acquiring_storage.get_monopay_token(invoice_id)
        if not token:
            return

        await self._verify_signature(
            sign=data.signature, body=data.body, invoice_id=invoice_id, token=token
        )

        async with self.locker.lock(
            f"monopay_webhook:{invoice_id}",
            timeout=10,
            blocking=True,
            blocking_timeout=10,
        ):
            await self._process_webhook_locked(invoice_id, body, token)

    async def _process_webhook_locked(
        self, invoice_id: str, body: dict, token: str
    ) -> None:
        status = body["status"]
        current_modified_date = datetime.fromisoformat(body["modifiedDate"])
        last_modified_date = await self.acquiring_storage.get_last_modified_date(
            invoice_id
        )

        if last_modified_date:
            if last_modified_date > current_modified_date:
                return

            if last_modified_date == current_modified_date and status not in [
                "failure",
                "reversed",
                "success",
            ]:
                return

        await self.acquiring_storage.set_last_modified_date(
            invoice_id, current_modified_date
        )

        payment = await self.payment_repository.get_by_invoice_id(invoice_id)
        if not payment:
            return

        controller = await self.controller_repository.get(payment.controller_id)
        if not controller:
            return

        if status == "processing":
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

        elif status == "failure":
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = body["failureReason"]

        elif status == "hold":
            payment.status = PaymentStatus.HOLD
            try:
                await self.factory.get(controller.type).send_qr_payment_infra(
                    device_id=controller.device_id,
                    order_id=invoice_id,
                    amount=payment.amount,
                )
            except Exception:
                await self._refund(invoice_id, token)
                payment.failure_reason = (
                    "Не вдалося відправити запит контролеру на оплату"
                )
            else:
                await self._finalize(invoice_id, payment.amount, token)

        await self.payment_repository.commit()
