from dataclasses import dataclass
from datetime import datetime

import structlog
from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka

from dash.infrastructure.iot.fiscalizer.client import FiscalizerIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models import FiscalizerTransaction
from dash.models.transactions.transaction import TransactionType
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = structlog.get_logger()


@dataclass
class FiscalizerSaleCallbackPayload:
    id: int
    add_coin: int
    add_bill: int
    add_free: int
    add_qr: int
    created: datetime | None = None
    sended: datetime | None = None


fiscalizer_sale_callback_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            FiscalizerSaleCallbackPayload,
            map={
                "add_coin": "addCoin",
                "add_bill": "addBill",
                "add_free": "addFree",
                "add_qr": "add_QR",
            },
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=fiscalizer_sale_callback_retort)
@request_scope
@inject
async def fiscalizer_sale_callback(
    device_id: str,
    data: FiscalizerSaleCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    transaction_repository: FromDishka[TransactionRepository],
    fiscalizer_client: FromDishka[FiscalizerIoTClient],
) -> None:
    dict_data = fiscalizer_sale_callback_retort.dump(data)
    controller = await controller_repository.get_fiscalizer_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Fiscalizer sale request ignored: controller not found",
            device_id=device_id,
            data=dict_data,
        )
        return

    logger.info(
        "Fiscalizer sale request received",
        device_id=device_id,
        data=dict_data,
    )

    transaction = FiscalizerTransaction(
        controller_transaction_id=data.id,
        controller_id=controller.id,
        location_id=controller.location_id,
        coin_amount=data.add_coin,
        bill_amount=data.add_bill,
        free_amount=data.add_free,
        qr_amount=data.add_qr,
        prev_amount=0,
        paypass_amount=0,
        card_amount=0,
        sale_type="money",
        type=TransactionType.FISCALIZER.value,
        created_at_controller=data.created or data.sended,
    )

    was_inserted = await transaction_repository.insert_with_conflict_ignore(transaction)

    if not was_inserted:
        return

    await transaction_repository.commit()
    await fiscalizer_client.sale_ack(device_id, data.id)

    logger.info(
        "Sale ack sent",
        device_id=device_id,
        controller_id=controller.id,
        transaction_id=transaction.id,
        controller_transaction_id=data.id,
    )
