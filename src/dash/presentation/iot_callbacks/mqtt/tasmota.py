from datetime import timedelta

from adaptix import Retort, name_mapping
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.energy_state import EnergyStateRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.models.energy_state import DailyEnergyState
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    default_retort,
    inject,
    parse_payload,
    request_scope,
)
from dash.services.iot.dto import EnergyStateDTO

logger = get_logger()


tasmota_callback_retort = Retort(
    recipe=[
        *datetime_recipe,
        name_mapping(
            EnergyStateDTO,
            map={
                "created": "Time",
                "energy_today": ["ENERGY", "Today"],
                "energy_yesterday": ["ENERGY", "Yesterday"],
                "energy_total": ["ENERGY", "Total"],
                "energy_total_since": ["ENERGY", "TotalStartTime"],
                "power": ["ENERGY", "Power"],
                "apparent_power": ["ENERGY", "ApparentPower"],
                "reactive_power": ["ENERGY", "ReactivePower"],
                "power_factor": ["ENERGY", "Factor"],
                "voltage": ["ENERGY", "Voltage"],
                "current": ["ENERGY", "Current"],
            },
        ),
    ]
)


@tracer.wrap()
@parse_payload(retort=tasmota_callback_retort)
@request_scope
@inject
async def tasmota_callback(
    device_id: str,
    data: EnergyStateDTO,
    controller_repository: FromDishka[ControllerRepository],
    energy_repository: FromDishka[EnergyStateRepository],
    iot_storage: FromDishka[IoTStorage],
) -> None:
    controller = await controller_repository.get_by_tasmota_id(device_id)

    if controller is None:
        logger.info(
            "Energy state ignored: controller not found", data=data, device_id=device_id
        )
        return

    logger.info(
        "Energy state received",
        data=data,
        device_id=device_id,
        controller_id=controller.id,
    )

    day_ago_date = (data.created - timedelta(days=1)).date()

    if not await energy_repository.exists_by_date(day_ago_date, controller.id):
        energy_state = DailyEnergyState(
            controller_id=controller.id,
            energy=data.energy_yesterday,
            date=day_ago_date,
        )
        energy_repository.add(energy_state)
        await energy_repository.commit()

    await iot_storage.set_energy_state(default_retort.dump(data), controller.id)
