from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast

import structlog
from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka

from dash.infrastructure.iot.wsm.client import WsmIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models.transactions.transaction import TransactionType
from dash.models.transactions.water_vending import WsmTransaction
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = structlog.get_logger()


@dataclass
class WsmSaleCallbackPayload:
    id: int
    add_coin: int
    add_bill: int
    add_prev: int
    add_free: int
    add_qr: int
    add_pp: int
    out_liters_1: int
    out_liters_2: int
    sale_type: str
    created: datetime | None = None
    sended: datetime | None = None
    card_uid: str | None = None
    card_balance_in: int | None = None
    card_balance_out: int | None = None


wsm_sale_callback_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            WsmSaleCallbackPayload,
            map={
                "add_coin": "addCoin",
                "add_bill": "addBill",
                "add_prev": "addPrev",
                "add_free": "addFree",
                "add_qr": "add_QR",
                "add_pp": "add_PP",
                "out_liters_1": "OutLiters_1",
                "out_liters_2": "OutLiters_2",
                "sale_type": "saleType",
                "card_uid": "cardUID",
                "card_balance_in": "cardBalanceIn",
                "card_balance_out": "cardBalanceOut",
            },
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=wsm_sale_callback_retort)
@request_scope
@inject
async def wsm_sale_callback(
    device_id: str,
    data: WsmSaleCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    transaction_repository: FromDishka[TransactionRepository],
    customer_repository: FromDishka[CustomerRepository],
    wsm_client: FromDishka[WsmIoTClient],
) -> None:
    dict_data = wsm_sale_callback_retort.dump(data)
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Wsm sale request ignored: controller not found",
            device_id=device_id,
            data=dict_data,
        )
        return

    company_id = controller.company_id
    if company_id is None:
        logger.info(
            "Wsm sale request ignored: company_id is None",
            device_id=device_id,
            controller_id=controller.id,
            data=dict_data,
        )
        return

    customer_id = None
    card_amount = 0

    if data.sale_type == "card":
        customer = await customer_repository.get_by_card_id(
            company_id=company_id,
            card_id=cast(str, data.card_uid),
        )
        if customer is not None:
            card_balance_in = cast(int, data.card_balance_in)
            card_balance_out = cast(int, data.card_balance_out)
            card_amount = card_balance_in - card_balance_out

            customer.balance -= Decimal(card_amount) / 100
            customer_id = customer.id
            card_amount = card_balance_in - card_balance_out
        else:
            logger.error(
                "Wsm sale request ignored: customer not found",
                device_id=device_id,
                controller_id=controller.id,
                company_id=company_id,
                card_id=data.card_uid,
                data=dict_data,
            )

    transaction = WsmTransaction(
        controller_transaction_id=data.id,
        controller_id=controller.id,
        location_id=controller.location_id,
        customer_id=customer_id,
        coin_amount=data.add_coin,
        bill_amount=data.add_bill,
        prev_amount=data.add_prev,
        free_amount=data.add_free,
        qr_amount=data.add_qr,
        paypass_amount=data.add_pp,
        card_amount=card_amount,
        type=TransactionType.WATER_VENDING.value,
        created_at_controller=data.created or data.sended,
        out_liters_1=data.out_liters_1,
        out_liters_2=data.out_liters_2,
        sale_type=data.sale_type,
        card_balance_in=data.card_balance_in,
        card_balance_out=data.card_balance_out,
        card_uid=data.card_uid,
    )

    was_inserted = await transaction_repository.insert_with_conflict_ignore(transaction)

    if not was_inserted:
        return

    await transaction_repository.commit()
    await wsm_client.sale_ack(device_id, data.id)

    logger.info(
        "Sale ack sent",
        device_id=device_id,
        controller_id=controller.id,
        transaction_id=transaction.id,
        controller_transaction_id=data.id,
    )
