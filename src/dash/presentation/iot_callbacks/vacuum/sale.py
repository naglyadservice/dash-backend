from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import cast

import structlog
from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka

from dash.infrastructure.iot.vacuum.client import VacuumIoTClient
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models import VacuumTransaction
from dash.models.payment import PaymentType
from dash.models.transactions.transaction import TransactionType
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)
from dash.services.common.payment_helper import PaymentHelper
from dash.services.iot.common.utils import ServiceBitMaskCodec
from dash.services.iot.vacuum.dto import VacuumServiceEnum, VacuumRelayBit

logger = structlog.get_logger()


@dataclass
class VacuumSaleCallbackPayload:
    id: int
    add_coin: int
    add_bill: int
    add_prev: int
    add_free: int
    add_qr: int
    add_pp: int
    sale_type: str
    services_sold: list[float]
    tariff: list[int]
    created: datetime | None = None
    sended: datetime | None = None
    card_uid: str | None = None
    card_balance_in: int | None = None
    card_balance_out: int | None = None
    replenishment_ratio: int | None = None


vacuum_sale_callback_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            VacuumSaleCallbackPayload,
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
@parse_payload(retort=vacuum_sale_callback_retort)
@request_scope
@inject
async def vacuum_sale_callback(
    device_id: str,
    data: VacuumSaleCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    transaction_repository: FromDishka[TransactionRepository],
    customer_repository: FromDishka[CustomerRepository],
    vacuum_client: FromDishka[VacuumIoTClient],
    payment_helper: FromDishka[PaymentHelper],
) -> None:
    dict_data = vacuum_sale_callback_retort.dump(data)
    controller = await controller_repository.get_vacuum_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Vacuum sale request ignored: controller not found",
            device_id=device_id,
            data=dict_data,
        )
        return

    company_id = controller.company_id
    customer_id = None
    card_amount = 0

    if data.sale_type == "card" and company_id is not None:
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
                "Vacuum sale request ignored: customer not found",
                device_id=device_id,
                controller_id=controller.id,
                company_id=company_id,
                card_id=data.card_uid,
                data=dict_data,
            )

    logger.info(
        "Vacuum sale request received",
        device_id=device_id,
        data=dict_data,
    )
    codec = ServiceBitMaskCodec(VacuumServiceEnum, VacuumRelayBit)
    transaction = VacuumTransaction(
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
        type=TransactionType.VACUUM,
        created_at_controller=data.created or data.sended,
        sale_type=data.sale_type,
        services_sold_seconds=codec.decode_int_mask(data.services_sold),
        tariff=codec.decode_int_mask(data.tariff),
        card_balance_in=data.card_balance_in,
        card_balance_out=data.card_balance_out,
        card_uid=data.card_uid,
        replenishment_ratio=data.replenishment_ratio,
    )

    was_inserted = await transaction_repository.insert_with_conflict_ignore(transaction)

    if not was_inserted:
        logger.info(
            "Vacuum transaction was not inserted due to conflict",
            device_id=device_id,
            controller_id=controller.id,
            transaction_id=transaction.id,
            data=dict_data,
        )
        await vacuum_client.sale_ack(device_id, data.id)
        return

    if data.add_bill + data.add_coin > 0:
        payment = payment_helper.create_payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            transaction_id=transaction.id,
            amount=data.add_bill + data.add_coin,
            payment_type=PaymentType.CASH,
        )
        if controller.checkbox_active:
            await payment_helper.fiscalize(controller, payment)

        payment_helper.save(payment)

    await transaction_repository.commit()
    await vacuum_client.sale_ack(device_id, data.id)

    logger.info(
        "Sale ack sent",
        device_id=device_id,
        controller_id=controller.id,
        transaction_id=transaction.id,
        controller_transaction_id=data.id,
        data=dict_data,
    )
