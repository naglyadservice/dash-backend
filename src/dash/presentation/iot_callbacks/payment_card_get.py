from dataclasses import dataclass

from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = get_logger()


retort = Retort()


@dataclass
class PaymentCardGetRequest:
    request_id: int
    created: str
    card_uid: str


payment_card_get_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            PaymentCardGetRequest,
            map={"card_uid": "cardUID"},
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=payment_card_get_retort)
@request_scope
@inject
async def payment_card_get_callback(
    device_id: str,
    data: PaymentCardGetRequest,
    customer_repository: FromDishka[CustomerRepository],
    controller_repository: FromDishka[ControllerRepository],
    wsm_client: FromDishka[WsmClient],
) -> None:
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Ignoring card_request from controller, controller not found by device_id",
            device_id=device_id,
            card_id=data.card_uid,
        )
        await wsm_client.payment_card_ack(
            device_id=device_id, payload={"request_id": data.request_id, "code": 1}
        )
        return

    if controller.company_id is None:
        logger.info(
            "Ignoring card_request from controller, company_id is None",
            device_id=device_id,
            controller_id=controller.id,
        )
        await wsm_client.payment_card_ack(
            device_id=device_id, payload={"request_id": data.request_id, "code": 1}
        )
        return

    customer = await customer_repository.get_by_card_id(
        company_id=controller.company_id, card_id=data.card_uid
    )

    if customer is None:
        logger.info(
            "Ignoring card_request from controller, customer not found by card_id",
            device_id=device_id,
            card_id=data.card_uid,
        )
        await wsm_client.payment_card_ack(
            device_id=device_id, payload={"request_id": data.request_id, "code": 1}
        )
        return

    tariff_per_liter_1 = customer.tariff_per_liter_1 or (
        controller.settings and controller.settings.get("tariffPerLiter_1")
    )
    tariff_per_liter_2 = customer.tariff_per_liter_2 or (
        controller.settings and controller.settings.get("tariffPerLiter_2")
    )

    if not tariff_per_liter_1 or not tariff_per_liter_2:
        logger.info(
            "Ignoring card_request from controller, tariffPerLiter is not found",
            device_id=device_id,
            card_id=data.card_uid,
        )
        return

    await wsm_client.payment_card_ack(
        device_id=device_id,
        payload={
            "request_id": data.request_id,
            "cardUID": data.card_uid,
            "balance": int(customer.balance * 100),
            "tariffPerLiter_1": tariff_per_liter_1,
            "tariffPerLiter_2": tariff_per_liter_2,
            "replenishmentRatio": 100 + (customer.discount_percent or 0),
            "code": 0,
        },
    )
