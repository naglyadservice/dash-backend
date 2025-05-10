from dataclasses import dataclass
from datetime import datetime
from typing import Any

from adaptix import Retort
from dishka import AsyncContainer

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.models.payment import Payment, PaymentStatus, PaymentType

retort = Retort()


@dataclass
class PaymentCardGetRequest:
    request_id: int
    created: str
    cardUID: str  # noqa: N815


async def payment_card_get_callback(
    device_id: str, data: dict[str, Any], di_container: AsyncContainer
) -> None:
    payload = retort.load(data, PaymentCardGetRequest)
    async with di_container() as container:
        customer_repository = await container.get(CustomerRepository)
        controller_repository = await container.get(ControllerRepository)

        controller = await controller_repository.get_vending_by_device_id(device_id)

        if controller is None:
            return

        customer_repository.get_by_cart(company_id=controller.id)

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
            created_at=datetime.fromisoformat(data["time"]),
        )

        payment_repository.add(payment)
        await payment_repository.commit()
