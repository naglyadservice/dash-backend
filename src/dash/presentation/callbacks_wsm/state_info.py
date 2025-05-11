from typing import Any

from dishka import FromDishka

from dash.infrastructure.repositories.controller import ControllerRepository

from .di_injector import inject, request_scope


@request_scope
@inject
async def state_info_callback(
    device_id: str,
    data: dict[str, Any],
    controller_repository: FromDishka[ControllerRepository],
) -> None:
    controller = await controller_repository.get_wsm_by_device_id(device_id)

    if controller is None:
        return

    controller.state = data
    await controller_repository.commit()
