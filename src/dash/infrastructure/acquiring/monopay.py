import base64
import hashlib
from typing import Any, Literal

import ecdsa
from fastapi import HTTPException
from redis.asyncio import Redis
from structlog import get_logger

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.api_client import APIClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.acquiring import AcquiringStorage
from dash.main.config import MonopayConfig
from dash.models.controllers import Controller
from dash.models.payment import Payment
from dash.services.common.payment_gateway import PaymentGateway
from dash.services.iot.dto import CreateInvoiceResponse

logger = get_logger()


class MonopayAPIError(Exception):
    pass


class MonopayGateway(PaymentGateway):
    def __init__(
        self,
        config: MonopayConfig,
        acquiring_storage: AcquiringStorage,
        payment_repository: PaymentRepository,
        checkbox_service: CheckboxService,
        controller_repository: ControllerRepository,
        locker: Redis,
    ):
        self.config = config
        self.acquiring_storage = acquiring_storage
        self.base_url = "https://api.monobank.ua/api"
        self.payment_repository = payment_repository
        self.checkbox_service = checkbox_service
        self.controller_repository = controller_repository
        self.locker = locker
        self.api_client = APIClient()

    def _prepare_headers(self, token: str) -> dict[str, str]:
        return {"X-Token": token}

    def _require_token(self, controller: Controller) -> str:
        if controller.monopay_token is None:
            raise ValueError("Monopay token is missing")

        return controller.monopay_token

    async def make_request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        return await self.api_client.make_request(
            method=method,
            url=self.base_url + endpoint,
            headers=headers,
            json=json,
            params=params,
        )

    async def _request_pub_key(self, invoice_id: str, token: str) -> bytes:
        response, status = await self.make_request(
            method="GET",
            endpoint="/merchant/pubkey",
            headers=self._prepare_headers(token),
        )
        if status != 200:
            logger.error(
                "Monopay API Error: request pub key failed",
                response=response,
                status=status,
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

    async def verify_signature(
        self, sign: str, body: bytes, invoice_id: str, token: str
    ) -> None:
        signature = base64.b64decode(sign)
        pub_key = await self.acquiring_storage.get_monopay_pub_key(invoice_id) or b""

        if not pub_key or not self._verify_pub_key(body, signature, pub_key):
            pub_key = await self._request_pub_key(invoice_id, token)

        if self._verify_pub_key(body, signature, pub_key):
            return

        raise HTTPException(status_code=400, detail="Invalid signature")

    async def create_invoice(
        self, controller: Controller, amount: int, hold_money: bool = True
    ) -> CreateInvoiceResponse:
        token = self._require_token(controller)
        response, status = await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/create",
            json={
                "amount": amount,
                "ccy": 980,
                "webHookUrl": self.config.webhook_url,
                "redirectUrl": self.config.redirect_url,
                "paymentType": "hold" if hold_money else "debit",
            },
            headers=self._prepare_headers(token),
        )
        if status != 200:
            logger.error(
                "Monopay API Error: create invoice failed",
                response=response,
                status=status,
            )
            raise MonopayAPIError

        invoice_id = response["invoiceId"]

        await self.acquiring_storage.set_monopay_token(
            token=token, invoice_id=invoice_id
        )
        return CreateInvoiceResponse(
            invoice_url=response["pageUrl"], invoice_id=invoice_id
        )

    async def finalize(
        self, controller: Controller, payment: Payment, amount: int
    ) -> None:
        response, status = await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/finalize",
            json={"invoiceId": payment.invoice_id, "amount": amount},
            headers=self._prepare_headers(self._require_token(controller)),
        )
        if status != 200:
            logger.error(
                "Monopay API Error: finalize failed", response=response, status=status
            )

    async def refund(self, controller: Controller, payment: Payment) -> None:
        response, status = await self.make_request(
            method="POST",
            endpoint="/merchant/invoice/cancel",
            json={"invoiceId": payment.invoice_id},
            headers=self._prepare_headers(self._require_token(controller)),
        )
        if status != 200:
            logger.error(
                "Monopay API Error: refund failed", response=response, status=status
            )

    async def request_pan(self, invoice_id: str, controller: Controller) -> str | None:
        response, _ = await self.make_request(
            method="GET",
            endpoint="/merchant/invoice/status",
            headers=self._prepare_headers(self._require_token(controller)),
            params={"invoiceId": invoice_id},
        )
        return response.get("paymentInfo", {}).get("maskedPan")
