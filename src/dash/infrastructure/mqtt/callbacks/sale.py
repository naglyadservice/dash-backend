from datetime import datetime
from typing import Any

import structlog
from dishka import AsyncContainer
from npc_iot import NpcClient

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models.transactions.transaction import TransactionType
from dash.models.transactions.water_vending import WaterVendingTransaction

logger = structlog.get_logger()


async def sale_callback(
    device_id: str, data: dict[str, Any], di_container: AsyncContainer
) -> None:
    logger.info("Sale received", data=data)
    async with di_container() as container:
        controller_repository = await container.get(ControllerRepository)
        transaction_repository = await container.get(TransactionRepository)
        npc_client = await container.get(NpcClient)

        controller = await controller_repository.get_vending_by_device_id(device_id)

        if controller is None:
            return

        if await transaction_repository.exists(
            transaction_id=data["id"], created=datetime.fromisoformat(data["created"])
        ):
            await send_ack(npc_client, device_id, data["id"])
            return

        transaction = WaterVendingTransaction(
            controller_transaction_id=data["id"],
            controller_id=controller.id,
            location_id=controller.location_id,
            coin_amount=data["addCoin"],
            bill_amount=data["addBill"],
            prev_amount=data["addPrev"],
            free_amount=data["addFree"],
            qr_amount=data["add_QR"],
            paypass_amount=data["add_PP"],
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
    await npc_client._send_message(
        device_id=device_id,
        topic="client/sale/ack",
        payload={"id": transaction_id, "code": 0},
        qos=1,
        ttl=None,
    )
    logger.info("Sale ack sent", transaction_id=transaction_id)
