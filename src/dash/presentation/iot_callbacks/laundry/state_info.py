from datetime import datetime, UTC
from typing import Any

from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.presentation.iot_callbacks.common.di_injector import inject, request_scope
from dash.services.iot.laundry.service import LaundryService

logger = get_logger()


@tracer.wrap()
@request_scope
@inject
async def laundry_state_info_callback(
    device_id: str,
    data: dict[str, Any],
    controller_repository: FromDishka[ControllerRepository],
    iot_storage: FromDishka[IoTStorage],
    laundry_service: FromDishka[LaundryService],
) -> None:
    controller = await controller_repository.get_laundry_by_device_id(device_id)

    if controller is None:
        logger.info(
            "Laundry state info ignored: controller not found",
            device_id=device_id,
        )
        return

    logger.info(
        "Laundry state info received",
        device_id=device_id,
        controller_id=controller.id,
        data=data,
    )
    prev_state = await iot_storage.get_state(controller.id) or {}

    door_input_id = controller.input_id

    door_lock_inp: dict[str, Any] | None = next(
        (inp for inp in data.get("input", []) if inp.get("id") == door_input_id), None
    )
    door_lock_inp_prev: dict[str, Any] | None = next(
        (inp for inp in prev_state.get("input", []) if inp.get("id") == door_input_id),
        None,
    )

    current_state = door_lock_inp.get("state", False) if door_lock_inp else False
    prev_state_value = (
        door_lock_inp_prev.get("state", False) if door_lock_inp_prev else False
    )

    if current_state != prev_state_value:
        logger.info(
            "Door state changed",
            device_id=device_id,
            controller_id=controller.id,
            previous_state=prev_state_value,
            current_state=current_state,
            input_id=door_input_id,
        )

        if current_state is True:
            await laundry_service.handle_door_locked(controller.id)
        elif current_state is False:
            await laundry_service.handle_door_unlocked(controller.id)

    data["created"] = datetime.now(UTC).isoformat()
    await iot_storage.set_state(data, controller.id)
