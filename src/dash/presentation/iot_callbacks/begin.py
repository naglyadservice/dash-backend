from datetime import UTC, datetime
from typing import Any

from dishka import FromDishka

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.main.config import AppConfig
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope


@request_scope
@inject
async def begin_callback(
    device_id: str,
    data: dict[str, Any],
    controller_repository: FromDishka[ControllerRepository],
    config: FromDishka[AppConfig],
) -> None:
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        return

    controller.last_reboot = (
        datetime.strptime(data["time"], "%d.%m.%YT%H:%M:%S")
        .astimezone(config.timezone)
        .astimezone(UTC)
    )
    await controller_repository.commit()
