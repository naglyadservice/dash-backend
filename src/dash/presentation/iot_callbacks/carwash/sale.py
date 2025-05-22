from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast

import structlog
from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka

from dash.infrastructure.iot.carwash.client import CarwashClient
from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models import CarwashTransaction
from dash.models.transactions.transaction import TransactionType
from dash.presentation.iot_callbacks.di_injector import (datetime_recipe,
                                                         inject, parse_payload,
                                                         request_scope)
from dash.services.iot.carwash.utils import decode_service_int_mask

logger = structlog.get_logger()


@dataclass
class CarwashSaleCallbackPayload:
    id: int
    add_coin: int
    add_bill: int
    add_prev: int
    add_free: int
    add_qr: int
    add_pp: int
    sale_type: str
    services_sold: list[int]
    tariff: list[int]
    created: datetime | None = None
    sended: datetime | None = None
    card_uid: str | None = None
    card_balance_in: int | None = None
    card_balance_out: int | None = None
    replenishment_ratio: int | None = None


carwash_sale_callback_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            CarwashSaleCallbackPayload,
            map={
                "add_coin": "addCoin",
                "add_bill": "addBill",
                "add_prev": "addPrev",
                "add_free": "addFree",
                "add_qr": "add_QR",
                "add_pp": "add_PP",
                "sale_type": "saleType",
                "services_sold": "servicesSold",
                "card_uid": "cardUID",
                "card_balance_in": "cardBalanceIn",
                "card_balance_out": "cardBalanceOut",
                "replenishment_ratio": "replenishmentRatio",
            },
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=carwash_sale_callback_retort)
@request_scope
@inject
async def carwash_sale_callback(
    device_id: str,
    data: CarwashSaleCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    transaction_repository: FromDishka[TransactionRepository],
    customer_repository: FromDishka[CustomerRepository],
    carwash_client: FromDishka[CarwashClient],
) -> None:
    controller = await controller_repository.get_carwash_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Ignoring sale from controller, company_id not found", device_id=device_id
        )
        return

    company_id = controller.company_id
    if company_id is None:
        logger.info(
            "Ignoring sale from controller, company_id is None",
            device_id=device_id,
            controller_id=controller.id,
        )
        return

    transaction = CarwashTransaction(
        controller_transaction_id=data.id,
        controller_id=controller.id,
        location_id=controller.location_id,
        coin_amount=data.add_coin,
        bill_amount=data.add_bill,
        prev_amount=data.add_prev,
        free_amount=data.add_free,
        qr_amount=data.add_qr,
        paypass_amount=data.add_pp,
        type=TransactionType.CARWASH.value,
        created_at_controller=data.created or data.sended,
        sale_type=data.sale_type,
        services_sold_seconds=decode_service_int_mask(data.services_sold),
        tariff=decode_service_int_mask(data.tariff),
        card_balance_in=data.card_balance_in,
        card_balance_out=data.card_balance_out,
        card_uid=data.card_uid,
        replenishment_ratio=data.replenishment_ratio,
    )

    if data.sale_type == "card":
        customer = await customer_repository.get_by_card_id(
            company_id=company_id,
            card_id=cast(str, data.card_uid),
        )
        if customer is not None:
            card_balance_in = cast(int, data.card_balance_in)
            card_balance_out = cast(int, data.card_balance_out)

            customer.balance -= Decimal(card_balance_in - card_balance_out) / 100
            transaction.customer_id = customer.id
        else:
            logger.error(
                "Customer not found",
                device_id=device_id,
                controller_id=controller.id,
                company_id=company_id,
                card_id=data.card_uid,
            )

    was_inserted = await transaction_repository.insert_with_conflict_ignore(transaction)

    if not was_inserted:
        logger.error(
            "Transaction not inserted",
            device_id=device_id,
            controller_id=controller.id,
            company_id=company_id,
            card_id=data.card_uid,
        )
        return

    await transaction_repository.commit()
    await carwash_client.sale_ack(device_id, data.id)

    logger.info(
        "Sale ack sent",
        device_id=device_id,
        controller_id=controller.id,
        company_id=company_id,
        card_id=data.card_uid,
        controller_transaction_id=data.id,
        was_inserted=was_inserted,
    )
