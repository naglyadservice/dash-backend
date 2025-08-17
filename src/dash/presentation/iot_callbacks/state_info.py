from typing import Any

from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models.controllers.controller import ControllerType
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope
from dash.presentation.iot_callbacks.common.utils import parse_bill_state

logger = get_logger()


@tracer.wrap()
@request_scope
@inject
async def state_info_callback(
    device_id: str,
    data: dict[str, Any],
    controller_repository: FromDishka[ControllerRepository],
    iot_storage: FromDishka[IoTStorage],
) -> None:
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        logger.info(
            "State info ignored: controller not found",
            device_id=device_id,
            data=data,
        )
        return

    logger.info(
        "State info received",
        device_id=device_id,
        data=data,
    )

    # casting bill_state to billState - inconsistency in fiscalizer spelling
    if controller.type is ControllerType.FISCALIZER:
        if "bill_state" in data:
            data["billState"] = data.pop("bill_state")
        if "coin_state" in data:
            data["coinState"] = data.pop("coin_state")

    if "billState" in data:
        data["billState"] = parse_bill_state(data["billState"])

    await iot_storage.set_state(data, controller.id)
