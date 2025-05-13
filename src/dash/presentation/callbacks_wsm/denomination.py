from dataclasses import dataclass
from datetime import datetime

from adaptix import Retort
from ddtrace.trace import tracer
from dishka import FromDishka

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models.payment import Payment, PaymentStatus, PaymentType

from .di_injector import datetime_recipe, inject, parse_paylaad, request_scope


@dataclass
class DenominationCallbackPayload:
    created: datetime
    coin: str
    bill: int


denomination_callback_retort = Retort(recipe=[*datetime_recipe])


@tracer.wrap()
@parse_paylaad(retort=denomination_callback_retort)
@request_scope
@inject
async def denomination_callback(
    device_id: str,
    data: DenominationCallbackPayload,
    payment_repository: FromDishka[PaymentRepository],
    controller_repository: FromDishka[ControllerRepository],
) -> None:
    controller = await controller_repository.get_wsm_by_device_id(device_id)

    if controller is None:
        return

    if data.bill:
        amount = data.bill
        type = PaymentType.BILL

    elif data.coin:
        amount = data.coin
        type = PaymentType.COIN

    else:
        return

    payment = Payment(
        controller_id=controller.id,
        location_id=controller.location_id,
        amount=amount,
        status=PaymentStatus.COMPLETED,
        type=type,
        created_at_controller=data.created,
    )

    payment_repository.add(payment)
    await payment_repository.commit()
