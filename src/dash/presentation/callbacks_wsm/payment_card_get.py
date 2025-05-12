from dataclasses import dataclass

from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository

from .di_injector import datetime_recipe, inject, parse_paylaad, request_scope

logger = get_logger()


retort = Retort()


@dataclass
class PaymentCardGetRequest:
    request_id: int
    created: str
    card_uid: str


payment_cart_get_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            PaymentCardGetRequest,
            map={"card_uid": "cardUID"},
        ),
    ]
)


@tracer.wrap()
@parse_paylaad(retort=payment_cart_get_retort)
@request_scope
@inject
async def payment_card_get_callback(
    device_id: str,
    data: PaymentCardGetRequest,
    customer_repository: FromDishka[CustomerRepository],
    controller_repository: FromDishka[ControllerRepository],
    wsm_client: FromDishka[WsmClient],
) -> None:
    controller = await controller_repository.get_wsm_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Ignoring card_request from controller, controller not found by device_id",
            device_id=device_id,
            card_id=data.card_uid,
        )
        return

    if controller.company_id is None:
        logger.info(
            "Ignoring card_request from controller, company_id is None",
            device_id=device_id,
            controller_id=controller.id,
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
        return

    await wsm_client.respond_payment_cart(
        device_id=device_id,
        payload={
            "request_id": data.request_id,
            "cardUID": data.card_uid,
            "balance": int(customer.balance * 100),  # Баланс карты в копейках
            # "tariffPerLiter1": 160,  # Тариф 1 для этой карты (в копейках за литр)
            # "tariffPerLiter2": 200,  # Тариф 2 для этой карты (в копейках за литр)
            "replenishmentRatio": 100,  # Коэффициент пополнения (например, 110 = 10% бонус)
        },
    )
