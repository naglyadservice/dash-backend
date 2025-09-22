from typing import Any

from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.storages.iot import IoTStorage
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope

logger = get_logger()


@tracer.wrap()
@request_scope
@inject
async def sys_connect_callback(
    deivce_id: str,
    data: dict[str, Any],
    iot_storage: FromDishka[IoTStorage],
) -> None:
    real_device_id = data["username"]

    logger.info("$SYS connection established", deivce_id=real_device_id, data=data)

    await iot_storage.set_broker_online_status(True, real_device_id)


@tracer.wrap()
@request_scope
@inject
async def sys_disconnect_callback(
    deivce_id: str,
    data: dict[str, Any],
    iot_storage: FromDishka[IoTStorage],
) -> None:
    real_device_id = data["username"]

    logger.info("$SYS connection lost", deivce_id=deivce_id, data=data)

    await iot_storage.set_broker_online_status(False, real_device_id)
