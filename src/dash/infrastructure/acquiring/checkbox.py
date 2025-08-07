from datetime import datetime, time
from typing import Any, Literal
from uuid import UUID, uuid4

import tenacity
from structlog import get_logger

from dash.infrastructure.api_client import APIClient
from dash.main.config import AppConfig
from dash.models import Controller
from dash.models.payment import Payment, PaymentType

logger = get_logger()


class CheckboxAPIError(Exception):
    pass


class CheckboxService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.api_client = APIClient()
        self.base_url = "https://api.checkbox.ua/api/v1"
        self.base_headers = {
            "X-Client-Name": "NaglyadService",
            "X-Client-Version": "1.0.0",
        }

    async def _make_request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        json: dict | None = None,
        headers: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        return await self.api_client.make_request(
            method=method,
            url=self.base_url + endpoint,
            headers=self.base_headers | (headers or {}),
            json=json,
        )

    async def _get_token(self, login: str, password: str) -> str | None:
        response, status = await self._make_request(
            method="POST",
            endpoint="/cashier/signin",
            json={"login": login, "password": password},
        )
        return response.get("access_token")

    async def _open_shift(self, controller: Controller, token: str):
        response, status = await self._make_request(
            method="POST",
            endpoint="/shifts",
            headers={
                "X-License-Key": controller.checkbox_license_key,
                "Authorization": f"Bearer {token}",
            },
            json={
                "id": str(uuid4()),
                "auto_close_at": datetime.now(self.config.timezone)
                .replace(hour=23, minute=45)
                .isoformat(),
            },
        )
        if status != 202:
            logger.error("Failed to open shift", response=response)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(10),
        wait=tenacity.wait_exponential(multiplier=30, min=30, max=3600),
    )
    async def create_receipt(
        self,
        controller: Controller,
        payment: Payment,
        receipt_id: UUID,
    ) -> UUID | None:
        if not controller.checkbox_active:
            logger.info(
                "Ignoring fiscalization request: Checkbox is not active",
                controller_id=controller.id,
            )
            return None

        if (
            not controller.checkbox_login
            or not controller.checkbox_password
            or not controller.checkbox_license_key
        ):
            logger.warning(
                "Ignoring fiscalization request: Credentials not provided",
                controller_id=controller.id,
            )
            return None

        if datetime.now(self.config.timezone).time() > time(23, 45):
            return None

        token = await self._get_token(
            controller.checkbox_login, controller.checkbox_password
        )
        if not token:
            logger.error(
                "Error while getting checkbox token", controller_id=controller.id
            )
            return None

        is_online_payment = payment.type in (PaymentType.LIQPAY, PaymentType.MONOPAY)

        data = {
            "id": str(receipt_id),
            "goods": [
                {
                    "good": {
                        "name": controller.good_name,
                        "code": controller.good_code,
                        "price": payment.amount,
                        "tax": [controller.tax_code] if controller.tax_code else None,
                    },
                    "quantity": 1000,
                }
            ],
            "payments": [
                {
                    "type": "CASHLESS" if is_online_payment else "CASH",
                    "value": payment.amount,
                    "payment_system": payment.type.value if is_online_payment else None,
                }
            ],
        }
        response, status = await self._make_request(
            method="POST",
            endpoint="/receipts/sell",
            json=data,
            headers={"Authorization": f"Bearer {token}"},
        )
        if status == 201:
            return
        elif status == 400 and response["message"] == "Зміну не відкрито":
            await self._open_shift(controller, token)
        else:
            logger.error(
                "Error while creating receipt",
                status=status,
                response=response,
                controller_id=controller.id,
            )
            raise CheckboxAPIError
