from datetime import datetime
from typing import Any

from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope

logger = get_logger()


@request_scope
@inject
async def begin_callback(
    device_id: str,
    data: dict[str, Any],
    controller_repository: FromDishka[ControllerRepository],
) -> None:
    logger.info("begin received", device_id=device_id)
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        return

    controller.last_reboot = datetime.fromisoformat(data["time"])
    await controller_repository.commit()
