from dataclasses import dataclass
from datetime import datetime

import structlog
from adaptix import Retort, dumper, loader, name_mapping
from dishka import FromDishka

from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models.transactions.transaction import TransactionType
from dash.models.transactions.water_vending import WaterVendingTransaction

from .di_injector import inject, parse_paylaad, request_scope

logger = structlog.get_logger()


@dataclass
class SaleCallbackPayload:
    id: int
    created: datetime
    add_coin: int
    add_bill: int
    add_prev: int
    add_free: int
    add_qr: int
    add_pp: int
    out_liters_1: int
    out_liters_2: int
    sale_type: str
    card_uid: str | None = None
    card_balance_in: int | None = None
    card_balance_out: int | None = None


sale_callabck_retort = Retort(
    recipe=[
        loader(datetime, lambda s: datetime.strptime(s, "%d.%m.%YT%H:%M:%S")),  # noqa: DTZ007
        dumper(datetime, lambda dt: dt.strftime("%d.%m.%YT%H:%M:%S")),
        name_mapping(
            SaleCallbackPayload,
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


@parse_paylaad(retort=sale_callabck_retort)
@request_scope
@inject
async def sale_callback(
    device_id: str,
    data: SaleCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    transaction_repository: FromDishka[TransactionRepository],
    wsm_client: FromDishka[WsmClient],
) -> None:
    logger.info("Sale received", data=data)

    controller = await controller_repository.get_wsm_by_device_id(device_id)

    if controller is None:
        return

    if await transaction_repository.exists(
        transaction_id=data.id, created=data.created
    ):
        await wsm_client.sale_ack(device_id, data.id)
        logger.info("Sale ack sent on duplicate", transaction_id=data.id)
        return

    transaction = WaterVendingTransaction(
        controller_transaction_id=data.id,
        controller_id=controller.id,
        location_id=controller.location_id,
        coin_amount=data.add_coin,
        bill_amount=data.add_bill,
        prev_amount=data.add_prev,
        free_amount=data.add_free,
        qr_amount=data.add_qr,
        paypass_amount=data.add_pp,
        type=TransactionType.WATER_VENDING.value,
        created_at_controller=data.created,
        out_liters_1=data.out_liters_1,
        out_liters_2=data.out_liters_2,
        sale_type=data.sale_type,
    )

    transaction_repository.add(transaction)
    await transaction_repository.commit()

    await wsm_client.sale_ack(device_id, data.id)
    logger.info("Sale ack sent", transaction_id=data.id)
