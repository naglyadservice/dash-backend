import logging
from datetime import datetime
from typing import Any

from dishka import AsyncContainer
from npc_iot import NpcClient
from npc_iot.exception import DeviceResponceError

from dash.infrastructure.repositories.water_vending.controller import (
    WaterVendingControllerRepository,
)
from dash.infrastructure.repositories.water_vending.transaction import (
    WaterVendingTransactionRepository,
)
from dash.models.transactions.transaction import PaymentStatus, TransactionType
from dash.models.transactions.water_vending import WaterVendingTransaction


async def sales_callback(
    device_id: str, data: dict[str, Any], di_container: AsyncContainer
) -> None:
    async with di_container() as container:
        controller_repository = await container.get(WaterVendingControllerRepository)
        transaction_repository = await container.get(WaterVendingTransactionRepository)
        npc_client = await container.get(NpcClient)

        controller = await controller_repository.get_by_device_id(device_id)

        if controller is None:
            return

        if await transaction_repository.ensure_exists(
            transaction_id=data["id"], created=datetime.fromisoformat(data["created"])
        ):
            await send_ack(npc_client, device_id, data["id"])
            return

        transaction = WaterVendingTransaction(
            controller_transaction_id=data["id"],
            controller_id=controller.id,
            coin_amount=data["addCoin"],
            bill_amount=data["addBill"],
            prev_amount=data["addPrev"],
            free_amount=data["addFree"],
            qr_amount=data["add_QR"],
            paypass_amount=data["add_PP"],
            status=PaymentStatus.COMPLETED,
            type=TransactionType.WATER_VENDING.value,
            created_at=datetime.fromisoformat(data["created"]),
            out_liters_1=data["OutLiters_1"],
            out_liters_2=data["OutLiters_2"],
            sale_type=data["saleType"],
        )

        transaction_repository.add(transaction)
        await transaction_repository.commit()

        await send_ack(npc_client, device_id, data["id"])


async def send_ack(
    npc_client: NpcClient,
    device_id: str,
    transaction_id: int,
) -> None:
    waiter = await npc_client._send_message(
        device_id=device_id,
        topic="client/sale/ack",
        payload={"id": transaction_id, "code": 0},
        qos=1,
        ttl=5,
    )
    try:
        await waiter.wait(timeout=5)
    except (DeviceResponceError, TimeoutError):
        logging.exception(
            "Failed to send sale ack. transaction_id: %s, device_id: %s",
            transaction_id,
            device_id,
        )
    else:
        logging.info(
            "Sale ack successfully sent. transaction_id: %s, device_id: %s",
            transaction_id,
            device_id,
        )
