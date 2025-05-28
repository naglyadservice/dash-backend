from dataclasses import dataclass
from datetime import datetime

from adaptix import Retort
from ddtrace.trace import tracer
from dishka import FromDishka

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models.payment import Payment, PaymentStatus, PaymentType
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)


@dataclass
class DenominationCallbackPayload:
    created: datetime
    coin: int | None = None
    bill: int | None = None


denomination_callback_retort = Retort(recipe=[*datetime_recipe])


@tracer.wrap()
@parse_payload(retort=denomination_callback_retort)
@request_scope
@inject
async def denomination_callback(
    device_id: str,
    data: DenominationCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    payment_repository: FromDishka[PaymentRepository],
    checkbox_service: FromDishka[CheckboxService],
) -> None:
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        return

    if data.bill:
        amount = data.bill
        payment_type = PaymentType.BILL

    elif data.coin:
        amount = data.coin
        payment_type = PaymentType.COIN

    else:
        return

    payment = Payment(
        controller_id=controller.id,
        location_id=controller.location_id,
        invoice_id=None,
        amount=amount,
        type=payment_type,
        status=PaymentStatus.CREATED,
        created_at_controller=data.created,
    )
    if controller.checkbox_active:
        payment.receipt_id = await checkbox_service.create_receipt(controller, payment)

    payment_repository.add(payment)
    await payment_repository.commit()
