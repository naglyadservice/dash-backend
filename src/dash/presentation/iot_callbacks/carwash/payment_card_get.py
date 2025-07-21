from dataclasses import dataclass

from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.storages.carwash_session import CarwashSessionStorage
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = get_logger()


@dataclass
class CarwashPaymentCardGetRequest:
    request_id: int
    created: str
    card_uid: str


carwash_payment_card_get_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            CarwashPaymentCardGetRequest,
            map={"card_uid": "cardUID"},
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=carwash_payment_card_get_retort)
@request_scope
@inject
async def carwash_payment_card_get_callback(
    device_id: str,
    data: CarwashPaymentCardGetRequest,
    customer_repository: FromDishka[CustomerRepository],
    controller_repository: FromDishka[ControllerRepository],
    carwash_client: FromDishka[CarwashIoTClient],
    session_storage: FromDishka[CarwashSessionStorage],
) -> None:
    dict_data = carwash_payment_card_get_retort.dump(data)

    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Carwash payment card request ignored: controller not found",
            device_id=device_id,
            card_id=data.card_uid,
            data=dict_data,
        )
        await carwash_client.payment_card_ack(
            device_id=device_id,
            payload={
                "request_id": data.request_id,
                "cardUID": data.card_uid,
                "code": 1,
            },
        )
        return

    if controller.company_id is None:
        logger.info(
            "Carwash payment card request ignored: company_id is None",
            device_id=device_id,
            controller_id=controller.id,
            data=dict_data,
        )
        await carwash_client.payment_card_ack(
            device_id=device_id,
            payload={
                "request_id": data.request_id,
                "cardUID": data.card_uid,
                "code": 1,
            },
        )
        return

    # If controller busy, always return 0 balance
    if not await session_storage.is_active(controller.id):
        await carwash_client.payment_card_ack(
            device_id=device_id,
            payload={
                "request_id": data.request_id,
                "cardUID": data.card_uid,
                "balance": 0,
                "replenishmentRatio": 100,
                "code": 0,
            },
        )
        return

    customer = await customer_repository.get_by_card_id(
        company_id=controller.company_id, card_id=data.card_uid
    )

    if customer is None:
        logger.info(
            "Carwash payment card request ignored: customer not found",
            device_id=device_id,
            card_id=data.card_uid,
            data=dict_data,
        )
        await carwash_client.payment_card_ack(
            device_id=device_id,
            payload={
                "request_id": data.request_id,
                "cardUID": data.card_uid,
                "code": 1,
            },
        )
        return

    logger.info(
        "Carwash payment card request received",
        device_id=device_id,
        data=dict_data,
    )

    await carwash_client.payment_card_ack(
        device_id=device_id,
        payload={
            "request_id": data.request_id,
            "cardUID": data.card_uid,
            "balance": int(customer.balance * 100),
            "replenishmentRatio": 100 + (customer.discount_percent or 0),
            "code": 0,
        },
    )
