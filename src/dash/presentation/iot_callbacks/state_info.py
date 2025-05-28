from typing import Any

from ddtrace.trace import tracer
from dishka import FromDishka

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope
from dash.presentation.iot_callbacks.common.utils import dt_naive_to_zone_aware


@tracer.wrap()
@request_scope
@inject
async def state_info_callback(
    device_id: str,
    data: dict[str, Any],
    controller_repository: FromDishka[ControllerRepository],
    iot_storage: FromDishka[IotStorage],
) -> None:
    controller = await controller_repository.get_by_device_id(device_id)

    if controller is None:
        return

    zone_aware_dt = dt_naive_to_zone_aware(data["created"], controller.timezone)
    data["created"] = zone_aware_dt.isoformat()

    await iot_storage.set_state(data, controller.id)
