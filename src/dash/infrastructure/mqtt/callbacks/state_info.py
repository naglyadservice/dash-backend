from typing import Any

from dishka import AsyncContainer

from dash.infrastructure.repositories.controller import ControllerRepository


async def state_info_callback(
    device_id: str, data: dict[str, Any], di_container: AsyncContainer
) -> None:
    async with di_container() as container:
        controller_repository = await container.get(ControllerRepository)

        controller = await controller_repository.get_vending_by_device_id(device_id)

        if controller is None:
            return

        controller.state = data
        await controller_repository.commit()
