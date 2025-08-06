from typing import Any

from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope

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
    
    if bill_state := data.get("bill_state") is not None:
        data["billState"] = bill_state
    if coin_state := data.get("coin_state") is not None:
        data["coinState"] = coin_state

    await iot_storage.set_state(data, controller.id)
