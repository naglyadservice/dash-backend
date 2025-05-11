from dataclasses import dataclass
from datetime import datetime
from typing import Any

from adaptix import Retort, name_mapping
from dishka import FromDishka

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models.payment import Payment, PaymentStatus, PaymentType

from .di_injector import datetime_recipe, inject, parse_paylaad, request_scope


@dataclass
class DenominationCallbackPayload:
    created: str
    coin: str
    bill: int


denomination_callback_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            DenominationCallbackPayload,
            map={"card_uid": "cardUID"},
        ),
    ]
)


@parse_paylaad(retort=denomination_callback_retort)
@request_scope
@inject
async def denomination_callback(
    device_id: str,
    data: dict[str, Any],
    payment_repository: FromDishka[PaymentRepository],
    controller_repository: FromDishka[ControllerRepository],
) -> None:
    controller = await controller_repository.get_wsm_by_device_id(device_id)

    if controller is None:
        return

    if data.get("bill"):
        amount = data["bill"]
        type = PaymentType.BILL

    elif data.get("coin"):
        amount = data["coin"]
        type = PaymentType.COIN

    else:
        return

    payment = Payment(
        controller_id=controller.id,
        location_id=controller.location_id,
        amount=amount,
        status=PaymentStatus.COMPLETED,
        type=type,
        created_at_controller=datetime.fromisoformat(data["time"]),
    )

    payment_repository.add(payment)
    await payment_repository.commit()
