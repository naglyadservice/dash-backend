from datetime import datetime, time
from typing import Any, Literal
from uuid import UUID

import uuid_utils.compat
from structlog import get_logger

from dash.infrastructure.api_client import APIClient
from dash.main.config import AppConfig
from dash.models import Controller
from dash.models.payment import Payment, PaymentType

logger = get_logger()


class CheckboxService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.api_client = APIClient()
        self.base_url = "https://api.checkbox.ua/api/v1"
        self.base_headers = {
            "X-Client-Name": "NaglyadService",
            "X-Client-Version": "1.0.0",
        }
        self.token = None

    def _get_headers(
        self, additional_headers: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return (
            self.base_headers
            | {"Authorization": f"Bearer {self.token}"}
            | (additional_headers or {})
        )

    async def _make_request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        json: dict | None = None,
        additional_headers: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        return await self.api_client.make_request(
            method=method,
            url=self.base_url + endpoint,
            headers=self._get_headers(additional_headers),
            json=json,
        )

    async def _get_token(self, login: str, password: str) -> str | None:
        response, status = await self._make_request(
            method="POST",
            endpoint="/cashier/signin",
            json={"login": login, "password": password},
        )
        return response.get("access_token")

    async def _open_shift(self, controller: Controller):
        await self._make_request(
            method="POST",
            endpoint="/shifts",
            additional_headers={"X-License-Key": controller.checkbox_license_key},
        )

    async def create_receipt(
        self,
        controller: Controller,
        payment: Payment,
        is_return: bool = False,
    ) -> UUID | None:
        if datetime.now(self.config.timezone).time() > time(23, 45):
            return None

        if not controller.checkbox_login or not controller.checkbox_password:
            return None

        self.token = await self._get_token(
            controller.checkbox_login, controller.checkbox_password
        )
        if not self.token:
            logger.error(
                "Error while getting checkbox token", controller_id=controller.id
            )
            payment.checkbox_error = "401: Не вдалося отримати токен"
            return None

        receipt_id = uuid_utils.compat.uuid7()
        online_payment = payment.type in (PaymentType.LIQPAY, PaymentType.MONOPAY)

        data = {
            "id": str(receipt_id),
            "goods": [
                {
                    "good": {
                        "name": controller.good_name,
                        "code": controller.good_code,
                        "price": payment.amount,
                        "tax": controller.tax_code,
                    },
                    "good_id": str(controller.id),
                    "quantity": 1000,
                    "is_return": is_return,
                }
            ],
            "payments": [
                {
                    "type": "CASHLESS" if online_payment else "CASH",
                    "value": payment.amount,
                    "payment_system": payment.type.value if online_payment else None,
                }
            ],
        }
        for attempt in range(2):
            response, status = await self._make_request(
                method="POST",
                endpoint="/receipts/sell",
                json=data,
            )
            if status == 400 and response["message"] == "Зміну не відкрито":
                await self._open_shift(controller)
                if attempt == 1:
                    payment.checkbox_error = "400: Не вдалося відкрити зміну"
            elif status != 201:
                logger.error(
                    "Error while creating receipt",
                    status=status,
                    response=response,
                    controller_id=controller.id,
                )
                receipt_id = None
                payment.checkbox_error = (
                    f"{status}: {response.get('message', 'Невідома помилка')}"
                )
            else:
                break

        return receipt_id
