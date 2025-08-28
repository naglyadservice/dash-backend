from dataclasses import dataclass

from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.iot.wsm.client import WsmIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = get_logger()


@dataclass
class WsmPaymentCardGetRequest:
    request_id: int
    created: str
    card_uid: str


wsm_payment_card_get_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            WsmPaymentCardGetRequest,
            map={"card_uid": "cardUID"},
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=wsm_payment_card_get_retort)
@request_scope
@inject
async def wsm_payment_card_get_callback(
    device_id: str,
    data: WsmPaymentCardGetRequest,
    customer_repository: FromDishka[CustomerRepository],
    controller_repository: FromDishka[ControllerRepository],
    wsm_client: FromDishka[WsmIoTClient],
) -> None:
    dict_data = wsm_payment_card_get_retort.dump(data)
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Wsm payment card request ignored: controller not found",
            device_id=device_id,
            card_id=data.card_uid,
            data=dict_data,
        )
        # await wsm_client.payment_card_ack(
        #     device_id=device_id,
        #     payload={
        #         "request_id": data.request_id,
        #         "cardUID": data.card_uid,
        #         "code": 1,
        #     },
        # )
        return

    if controller.company_id is None:
        logger.info(
            "Wsm payment card request ignored: company_id is None",
            device_id=device_id,
            controller_id=controller.id,
            data=dict_data,
        )
        await wsm_client.payment_card_ack(
            device_id=device_id,
            payload={
                "request_id": data.request_id,
                "cardUID": data.card_uid,
                "code": 1,
            },
        )
        return

    customer = await customer_repository.get_by_card_id(
        company_id=controller.company_id, card_id=data.card_uid.rstrip("0"),
    )

    if customer is None:
        logger.info(
            "Wsm payment card request ignored: customer not found",
            device_id=device_id,
            card_id=data.card_uid,
            data=dict_data,
        )
        await wsm_client.payment_card_ack(
            device_id=device_id,
            payload={
                "request_id": data.request_id,
                "cardUID": data.card_uid,
                "code": 1,
            },
        )
        return

    tariff_per_liter_1 = customer.tariff_per_liter_1 or (
        controller.settings and controller.settings.get("tariffPerLiter_1")
    )
    tariff_per_liter_2 = customer.tariff_per_liter_2 or (
        controller.settings and controller.settings.get("tariffPerLiter_2")
    )

    logger.info(
        "Wsm payment card request received",
        device_id=device_id,
        data=dict_data,
    )

    await wsm_client.payment_card_ack(
        device_id=device_id,
        payload={
            "request_id": data.request_id,
            "cardUID": data.card_uid,
            "balance": int(customer.balance * 100),
            "tariffPerLiter_1": tariff_per_liter_1,
            "tariffPerLiter_2": tariff_per_liter_2,
            "code": 0,
        },
    )
