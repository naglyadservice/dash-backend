from dataclasses import dataclass
from datetime import datetime

from adaptix import Retort
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.iot.car_cleaner.client import CarCleanerIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.models.encashment import Encashment
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = get_logger()


@dataclass
class CarCleanerEncashmentCallbackPayload:
    id: int
    coin: list[int]
    bill: list[int]
    amount: int
    created: datetime | None = None
    sended: datetime | None = None


car_cleaner_encashment_callback_retort = Retort(recipe=[*datetime_recipe])


@tracer.wrap()
@parse_payload(retort=car_cleaner_encashment_callback_retort)
@request_scope
@inject
async def car_cleaner_encashment_callback(
    device_id: str,
    data: CarCleanerEncashmentCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    car_cleaner_client: FromDishka[CarCleanerIoTClient],
    encashment_repository: FromDishka[ControllerRepository],
) -> None:
    dict_data = car_cleaner_encashment_callback_retort.dump(data)
    controller = await controller_repository.get_by_device_id(device_id)

    if not controller:
        logger.info(
            "Carwash encashment request ignored: controller not found",
            device_id=device_id,
            data=dict_data,
        )
        # await carwash_client.encashment_ack(
        #     device_id=device_id, payload={"id": data.id, "code": 1}
        # )
        return

    logger.info(
        "Carwash encashment request received",
        device_id=device_id,
        data=car_cleaner_encashment_callback_retort.dump(data),
    )

    encashment = Encashment(
        controller_id=controller.id,
        created_at_controller=data.created or data.sended,
        encashed_amount=data.amount,
        coin_1=data.coin[0],
        coin_2=data.coin[1],
        coin_3=data.coin[2],
        coin_4=data.coin[3],
        coin_5=data.coin[4],
        coin_6=data.coin[5],
        bill_1=data.bill[0],
        bill_2=data.bill[1],
        bill_3=data.bill[2],
        bill_4=data.bill[3],
        bill_5=data.bill[4],
        bill_6=data.bill[5],
        bill_7=data.bill[6],
        bill_8=data.bill[7],
    )
    encashment_repository.add(encashment)
    await encashment_repository.commit()

    await car_cleaner_client.encashment_ack(
        device_id=device_id, payload={"id": data.id, "code": 0}
    )
