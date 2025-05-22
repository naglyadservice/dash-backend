from dataclasses import dataclass
from datetime import datetime

from adaptix import Retort
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import getLogger

from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.models.encashment import Encashment
from dash.presentation.iot_callbacks.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = getLogger()


@dataclass
class EncashmentCallbackPayload:
    id: int
    coin_1: int
    coin_2: int
    coin_3: int
    coin_4: int
    coin_5: int
    coin_6: int
    bill_1: int
    bill_2: int
    bill_3: int
    bill_4: int
    bill_5: int
    bill_6: int
    bill_7: int
    bill_8: int
    amount: int
    created: datetime | None = None
    sended: datetime | None = None


encashment_callback_retort = Retort(recipe=[*datetime_recipe])


@tracer.wrap()
@parse_payload(retort=encashment_callback_retort)
@request_scope
@inject
async def encashment_callback(
    device_id: str,
    data: EncashmentCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    wsm_client: FromDishka[WsmClient],
    encashment_repository: FromDishka[ControllerRepository],
) -> None:
    controller = await controller_repository.get_by_device_id(device_id)
    if not controller:
        logger.info(
            "Ignoring encashment request from controller, controller not found by device_id",
            device_id=device_id,
        )
        await wsm_client.encashment_ack(
            device_id=device_id, payload={"id": data.id, "code": 1}
        )
        return

    encashment = Encashment(
        controller_id=controller.id,
        created_at_controller=data.created or data.sended,
        encashed_amount=data.amount,
        coin_1=data.coin_1,
        coin_2=data.coin_2,
        coin_3=data.coin_3,
        coin_4=data.coin_4,
        coin_5=data.coin_5,
        coin_6=data.coin_6,
        bill_1=data.bill_1,
        bill_2=data.bill_2,
        bill_3=data.bill_3,
        bill_4=data.bill_4,
        bill_5=data.bill_5,
        bill_6=data.bill_6,
        bill_7=data.bill_7,
        bill_8=data.bill_8,
    )
    encashment_repository.add(encashment)
    await encashment_repository.commit()

    await wsm_client.encashment_ack(
        device_id=device_id, payload={"id": data.id, "code": 0}
    )
