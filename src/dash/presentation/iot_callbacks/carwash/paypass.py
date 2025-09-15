from dataclasses import dataclass
from datetime import datetime

from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models.payment import Payment, PaymentGatewayType, PaymentStatus, PaymentType
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    parse_payload,
)
from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.services.common.payment_helper import PaymentHelper

logger = get_logger()


@dataclass
class CarwashPaypassCallbackPayload:
    id: int
    mid: str
    tid: str
    amount: str
    pan: str
    datetim: str
    rrn: str
    auth: str
    invoice: str
    paysys: str
    created: datetime | None = None
    sended: datetime | None = None


carwash_paypass_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            CarwashPaypassCallbackPayload,
            map={
                "mid": "MID",
                "tid": "TID",
                "amount": "AMOUNT",
                "pan": "PAN",
                "datetim": "DATETIM",
                "rrn": "RRN",
                "auth": "AUTH",
                "invoice": "INVOICE",
                "paysys": "PAYSYS",
            },
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=carwash_paypass_retort)
@request_scope
@inject
async def carwash_paypass_callback(
    device_id: str,
    data: CarwashPaypassCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    payment_repository: FromDishka[PaymentRepository],
    payment_helper: FromDishka[PaymentHelper],
    carwash_client: FromDishka[CarwashIoTClient],
) -> None:
    controller = await controller_repository.get_carwash_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Paypass ignored: controller not found",
            device_id=device_id,
            data=data,
        )
        return

    logger.info(
        "Paypass received",
        device_id=device_id,
        data=data,
    )

    payment = payment_helper.create_payment(
        controller_id=controller.id,
        location_id=controller.location_id,
        amount=int(data.amount),
        payment_type=PaymentType.CASHLESS,
        status=PaymentStatus.CREATED,
        gateway_type=PaymentGatewayType.PAYPASS,
        invoice_id=data.invoice,
        masked_pan=data.pan,
        extra=Retort().dump(data),
    )
    if controller.checkbox_active:
        await payment_helper.fiscalize(controller, payment)

    payment_repository.add(payment)
    await payment_repository.commit()

    await carwash_client.paypass_ack(
        device_id=device_id,
        payload={"id": data.id, "code": 0},
    )
