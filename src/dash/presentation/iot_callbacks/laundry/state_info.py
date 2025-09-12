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

    cur_door = parse_state(data, "input", controller.input_id)
    prev_door = parse_state(prev_state, "input", controller.input_id)

    cur_btn = parse_state(data, "relay", controller.button_relay_id)
    prev_btn = parse_state(prev_state, "relay", controller.button_relay_id)

    cur_led = parse_state(data, "output", controller.led_output_id)
    prev_led = parse_state(prev_state, "output", controller.led_output_id)

    if returned_to_idle(cur_btn, prev_btn, cur_led, prev_led, cur_door):
        logger.info(
            "Machine returned to idle state",
            device_id=device_id,
            controller_id=controller.id,
        )
        await laundry_service.handle_idle_state(controller.id)

    if cur_door != prev_door:
        logger.info(
            "Door state changed",
            device_id=device_id,
            controller_id=controller.id,
            previous_state=prev_door,
            current_state=cur_door,
            input_id=controller.input_id,
        )

        if cur_door is True:
            await laundry_service.handle_door_locked(controller.id)
        elif cur_door is False:
            await laundry_service.handle_door_unlocked(controller.id)

    data["created"] = datetime.now(UTC).isoformat()
    await iot_storage.set_state(data, controller.id)


def parse_state(source: dict[str, Any], key: str, target_id: int) -> bool:
    return next(
        (item["state"] for item in source.get(key, []) if item.get("id") == target_id),
        False,
    )


def returned_to_idle(
    cur_btn: bool, prev_btn: bool, cur_led: bool, prev_led: bool, door: bool
) -> bool:
    door_closed = not door
    button_reset = prev_btn and not cur_btn
    # led_reset = prev_led and not cur_led

    return door_closed and button_reset  # and led_reset
