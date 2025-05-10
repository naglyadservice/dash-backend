from dataclasses import dataclass

from adaptix import Retort
from dishka import FromDishka

from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository

from .di_injector import inject, parse_paylaad, request_scope

retort = Retort()


@dataclass
class PaymentCardGetRequest:
    request_id: int
    created: str
    cardUID: str  # noqa: N815


@parse_paylaad
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
        return

    customer = await customer_repository.get_by_card_id(
        company_id=controller.id, card_id=data.cardUID
    )

    if customer is None:
        return

    await wsm_client.respond_payment_cart(
        device_id=device_id,
        payload={
            "request_id": data.request_id,
            "cardUID": data.cardUID,
            "balance": int(customer.balance * 100),  # Баланс карты в копейках
            "tariffPerLiter1": 160,  # Тариф 1 для этой карты (в копейках за литр)
            "tariffPerLiter2": 200,  # Тариф 2 для этой карты (в копейках за литр)
            "replenishmentRatio": 100,  # Коэффициент пополнения (например, 110 = 10% бонус)
        },
    )
