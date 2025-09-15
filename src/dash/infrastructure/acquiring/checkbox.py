import asyncio
from datetime import datetime, time
from typing import Any, Literal
from uuid import UUID, uuid4

from structlog import get_logger

from dash.infrastructure.api_client import APIClient
from dash.main.config import AppConfig
from dash.models import Controller
from dash.models.payment import Payment, PaymentGatewayType

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
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        return await self.api_client.make_request(
            method=method,
            url=self.base_url + endpoint,
            headers=self.base_headers | (headers or {}),
            json=json,
            params=params,
        )

    async def _get_token(self, login: str, password: str) -> str | None:
        response, status = await self._make_request(
            method="POST",
            endpoint="/cashier/signin",
            json={"login": login, "password": password},
        )
        return response.get("access_token")

    async def _get_active_shift(self, token: str):
        response, status = await self._make_request(
            method="GET",
            endpoint="/shifts",
            params=[
                ("statuses", "OPENED"),
                ("statuses", "OPENING"),
                ("statuses", "CREATED"),
                ("limit", "1"),
                ("desc", "true"),
            ],
            headers={"Authorization": f"Bearer {token}"},
        )
        if status == 200 and response.get("results"):
            return response["results"][0]
        return None

    async def _wait_for_shift_opened(
        self, shift_id: str, token: str, timeout: int = 30
    ):
        logger.info(f"Waiting for shift opening", shift_id=shift_id, timeout=timeout)

        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            shift_info, status = await self._make_request(
                method="GET",
                endpoint=f"/shifts/{shift_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if status == 200:
                if shift_info["status"] == "OPENED":
                    logger.info("Shift successfully opened", shift_id=shift_id)
                    return True
                elif shift_info["status"] == "CLOSED":
                    logger.error(
                        "Shift closed during opening",
                        shift_id=shift_id,
                        details=shift_info.get("initial_transaction"),
                    )
                    return False
            await asyncio.sleep(3)

        logger.error("Shift opening timeout", shift_id=shift_id, timeout=timeout)
        return False

    async def _open_shift(self, license_key: str, token: str) -> bool:
        shift_id = str(uuid4())
        response, status = await self._make_request(
            method="POST",
            endpoint="/shifts",
            headers={
                "X-License-Key": license_key,
                "Authorization": f"Bearer {token}",
            },
            json={
                "id": shift_id,
                "auto_close_at": datetime.now(self.config.timezone)
                .replace(hour=23, minute=45)
                .isoformat(),
            },
        )
        if status != 202:
            logger.error("Failed to open shift", response=response)
            return False

        return await self._wait_for_shift_opened(shift_id, token)

    async def _open_shift_if_needed(self, license_key: str, token: str) -> bool:
        active_shift = await self._get_active_shift(token)
        if active_shift:
            if active_shift["status"] == "OPENED":
                return True
            elif active_shift["status"] in ("OPENING", "CREATED"):
                return await self._wait_for_shift_opened(active_shift["id"], token)

        return await self._open_shift(license_key, token)

    async def create_receipt(
        self,
        controller: Controller,
        payment: Payment,
        receipt_id: UUID,
    ) -> None:
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

        logger.info(f"Creating receipt", receipt_id=receipt_id)

        token = await self._get_token(
            controller.checkbox_login, controller.checkbox_password
        )
        if not token:
            logger.error(
                "Error while getting checkbox token", controller_id=controller.id
            )
            return None

        if not await self._open_shift_if_needed(controller.checkbox_license_key, token):
            return None

        payment_dict = {
            "type": payment.type.value,
            "value": payment.amount,
            "payment_system": payment.gateway_type and payment.gateway_type.value,
        }
        if payment.gateway_type == PaymentGatewayType.PAYPASS and payment.extra:
            paypass_dict = {
                "card_mask": payment.masked_pan,
                "payment_system": payment.extra["paysys"],
                "acquirer_and_seller": payment.extra["mid"],
                "auth_code": payment.extra["auth"],
                "rrn": payment.extra["rrn"],
                "terminal": payment.extra["tid"],
            }
            payment_dict.update(paypass_dict)

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
            "payments": [payment_dict],
        }
        response, status = await self._make_request(
            method="POST",
            endpoint="/receipts/sell",
            json=data,
            headers={"Authorization": f"Bearer {token}"},
        )
        if status != 201:
            logger.error(
                "Error while creating receipt",
                status=status,
                response=response,
                controller_id=controller.id,
            )
            raise CheckboxAPIError

        logger.info(
            f"Receipt successfully created",
            receipt_id=receipt_id,
            payment_id=payment.id,
            controller_id=controller.id,
        )
        return None
