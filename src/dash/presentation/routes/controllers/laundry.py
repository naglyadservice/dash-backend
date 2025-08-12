from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses, controller_errors
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.dto import (
    ControllerID,
    RebootControllerRequest,
    RebootDelayDTO,
    SetConfigRequest,
    SetSettingsRequest,
    SyncSettingsRequest,
)
from dash.services.iot.laundry.dto import (
    LaundryBusinessSettings,
    LaundryConfig,
    LaundryIoTControllerScheme,
    LaundryMqttSettings,
    UpdateLaudnrySettingsRequest,
)
from dash.services.iot.laundry.service import LaundryService

laundry_router = APIRouter(
    prefix="/laundry",
    tags=["LAUNDRY"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@laundry_router.get(
    "/{controller_id}",
    responses=build_responses((404, (ControllerNotFoundError,))),
)
async def read_controller(
    service: FromDishka[LaundryService],
    data: ControllerID = Depends(),
) -> LaundryIoTControllerScheme:
    return await service.read_controller(data)


@laundry_router.patch(
    "/{controller_id}/config",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_config(
    service: FromDishka[LaundryService],
    data: LaundryConfig,
    controller_id: UUID,
) -> None:
    await service.update_config(
        SetConfigRequest(controller_id=controller_id, config=data)
    )


@laundry_router.patch(
    "/{controller_id}/settings",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_settings(
    service: FromDishka[LaundryService],
    data: LaundryMqttSettings,
    controller_id: UUID,
) -> None:
    await service.update_settings(
        SetSettingsRequest(controller_id=controller_id, settings=data)
    )


@laundry_router.patch(
    "/{controller_id}",
    status_code=204,
    responses=build_responses((404, (ControllerNotFoundError,))),
)
async def update_business_settings(
    service: FromDishka[LaundryService],
    data: LaundryBusinessSettings,
    controller_id: UUID,
) -> None:
    await service.update(
        UpdateLaudnrySettingsRequest(controller_id=controller_id, settings=data)
    )


@laundry_router.post(
    "/{controller_id}/reboot",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def reboot_controller(
    service: FromDishka[LaundryService],
    data: RebootDelayDTO,
    controller_id: UUID,
) -> None:
    await service.reboot_controller(
        RebootControllerRequest(controller_id=controller_id, delay=data.delay)
    )


class SyncLaundrySettingsResponse(BaseModel):
    settings: LaundryMqttSettings
    config: LaundryConfig


@laundry_router.patch(
    "/{controller_id}/sync",
    responses=build_responses(*controller_errors),
)
async def sync_settings(
    service: FromDishka[LaundryService],
    data: SyncSettingsRequest = Depends(),
) -> SyncLaundrySettingsResponse:
    return await service.sync_settings(data)  # type: ignore
