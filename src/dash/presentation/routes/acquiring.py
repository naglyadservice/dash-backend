import base64
import json
from datetime import datetime
from typing import Any, Literal

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Form, Request
from pydantic import Field
from structlog import get_logger

from dash.infrastructure.acquiring.liqpay import (
    LiqpayGateway,
)
from dash.infrastructure.acquiring.monopay import (
    MonopayGateway,
)
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.acquiring import AcquiringStorage
from dash.models.payment import PaymentGatewayType
from dash.presentation.response_builder import build_responses, controller_errors
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    InsufficientDepositAmountError,
    UnsupportedPaymentGatewayTypeError,
)
from dash.services.iot.base import CreateInvoiceRequest, CreateInvoiceResponse
from dash.services.iot.factory import IoTServiceFactory

acquiring_router = APIRouter(
    prefix="/acquiring", tags=["ACQUIRING"], route_class=DishkaRoute
)
logger = get_logger()


class CreateMonopayInvoiceRequest(CreateInvoiceRequest):
    gateway_type: Literal[PaymentGatewayType.MONOPAY] = Field(
        default=PaymentGatewayType.MONOPAY, init=False, frozen=True
    )


@acquiring_router.post(
    "/monopay/invoice",
    responses=build_responses(
        (400, (UnsupportedPaymentGatewayTypeError, InsufficientDepositAmountError)),
        *controller_errors,
    ),
)
async def monopay_invoice(
    factory: FromDishka[IoTServiceFactory],
    controller_repository: FromDishka[ControllerRepository],
    data: CreateMonopayInvoiceRequest,
) -> CreateInvoiceResponse:
    controller = await controller_repository.get(data.controller_id)
    if not controller:
        raise ControllerNotFoundError

    service = factory.get(controller.type)
    return await service.create_invoice(data)


@acquiring_router.post("/monopay/webhook", include_in_schema=False)
async def monopay_webhook(
    request: Request,
    monopay_service: FromDishka[MonopayGateway],
    payment_repository: FromDishka[PaymentRepository],
    controller_repository: FromDishka[ControllerRepository],
    storage: FromDishka[AcquiringStorage],
    factory: FromDishka[IoTServiceFactory],
) -> Any:
    bytes_data = await request.body()
    signature = request.headers.get("X-Sign")

    if not signature or not signature:
        return

    dict_data = json.loads(bytes_data.decode())
    invoice_id = dict_data["invoiceId"]
    logger.info(f"Monopay webhook request", data=dict_data)

    token = await storage.get_monopay_token(invoice_id)
    if not token:
        return

    await monopay_service.verify_signature(
        sign=signature, body=bytes_data, invoice_id=invoice_id, token=token
    )

    current_modified_date = datetime.fromisoformat(dict_data["modifiedDate"])
    last_modified_date = await storage.get_last_modified_date(invoice_id)

    if last_modified_date and current_modified_date < last_modified_date:
        return

    await storage.set_last_modified_date(invoice_id, current_modified_date)

    payment = await payment_repository.get_by_invoice_id(invoice_id)
    if not payment:
        return

    controller = await controller_repository.get(payment.controller_id)
    if not controller:
        return

    service = factory.get(controller.type)
    status = dict_data["status"]

    if status == "hold":
        await service.process_hold_status(payment)
    elif status == "processing":
        await service.process_processing_status(payment)
    elif status == "success":
        await service.process_success_status(payment)
    elif status == "reversed":
        await service.process_reversed_status(payment)
    elif status == "failure":
        await service.process_failed_status(payment, dict_data["err_description"])


class CreateLiqpayInvoiceRequest(CreateInvoiceRequest):
    gateway_type: Literal[PaymentGatewayType.LIQPAY] = Field(
        default=PaymentGatewayType.LIQPAY, init=False, frozen=True
    )


@acquiring_router.post(
    "/liqpay/invoice",
    responses=build_responses(
        (400, (UnsupportedPaymentGatewayTypeError, InsufficientDepositAmountError)),
        *controller_errors,
    ),
)
async def liqpay_invoice(
    factory: FromDishka[IoTServiceFactory],
    controller_repository: FromDishka[ControllerRepository],
    data: CreateLiqpayInvoiceRequest,
) -> CreateInvoiceResponse:
    controller = await controller_repository.get(data.controller_id)
    if not controller:
        raise ControllerNotFoundError

    service = factory.get(controller.type)
    return await service.create_invoice(data)


@acquiring_router.post("/liqpay/webhook", include_in_schema=False)
async def liqpay_webhook(
    liqpay_service: FromDishka[LiqpayGateway],
    payment_repository: FromDishka[PaymentRepository],
    controller_repository: FromDishka[ControllerRepository],
    factory: FromDishka[IoTServiceFactory],
    data: str = Form(...),
    signature: str = Form(...),
) -> Any:
    dict_data = json.loads(base64.b64decode(data).decode("utf-8"))
    invoice_id = dict_data["order_id"]
    logger.info(f"Liqpay webhook request", data=dict_data)

    payment = await payment_repository.get_by_invoice_id(invoice_id)
    if not payment:
        return

    controller = await controller_repository.get(payment.controller_id)
    if not controller or not (
        controller.liqpay_public_key and controller.liqpay_private_key
    ):
        return

    if not liqpay_service.verify_signature(
        private_key=controller.liqpay_private_key,
        data_to_sign=data,
        signature=signature,
    ):
        return

    status = dict_data["status"]
    service = factory.get(controller.type)

    if status == "hold_wait":
        await service.process_hold_status(payment)
    elif status == "processing":
        await service.process_processing_status(payment)
    elif status == "success":
        await service.process_success_status(payment)
    elif status == "reversed":
        await service.process_reversed_status(payment)
    elif status in ("failed", "error"):
        await service.process_failed_status(payment, dict_data["err_description"])
