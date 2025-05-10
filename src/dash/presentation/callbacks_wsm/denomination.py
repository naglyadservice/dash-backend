from datetime import datetime
from typing import Any

from dishka import AsyncContainer

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.models.payment import Payment, PaymentStatus, PaymentType


async def denomination_callback(
    device_id: str, data: dict[str, Any], di_container: AsyncContainer
) -> None:
    async with di_container() as container:
        payment_repository = await container.get(PaymentRepository)
        controller_repository = await container.get(ControllerRepository)

        controller = await controller_repository.get_vending_by_device_id(device_id)

        if controller is None:
            return

        if data.get("bill"):
            amount = data["bill"]
            type = PaymentType.BILL

        elif data.get("coin"):
            amount = data["coin"]
            type = PaymentType.COIN

        else:
            return

        payment = Payment(
            controller_id=controller.id,
            location_id=controller.location_id,
            amount=amount,
            status=PaymentStatus.COMPLETED,
            type=type,
            created_at_controller=datetime.fromisoformat(data["time"]),
        )

        payment_repository.add(payment)
        await payment_repository.commit()
