from typing import Any

from dishka import AsyncContainer

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models.controllers.water_vending import WaterVendingController
from dash.models.service_enum import WaterVendingServiceType
from dash.models.transactions.transaction import (
    PaymentMethod,
    PaymentStatus,
    TransactionType,
)
from dash.models.transactions.water_vending import WaterVendingTransaction


async def sales_callback(
    device_id: str, data: dict[str, Any], di_container: AsyncContainer
) -> None:
    pass
