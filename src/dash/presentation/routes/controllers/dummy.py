from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses, controller_errors
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.dummy.dto import (
    DummyControllerIoTScheme,
    SetDummyDescriptionRequest,
)
from dash.services.iot.dummy.service import DummyService
from dash.services.iot.dto import ControllerID

dummy_router = APIRouter(
    prefix="/dummy",
    tags=["DUMMY"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@dummy_router.get(
    "/{controller_id}",
    responses=build_responses((404, (ControllerNotFoundError,))),
)
async def read_controller(
    service: FromDishka[DummyService],
    data: ControllerID = Depends(),
) -> DummyControllerIoTScheme:
    return await service.read_controller(data)


@dummy_router.put(
    "/{controller_id}/description",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def set_description(
    service: FromDishka[DummyService],
    controller_id: UUID,
    data: SetDummyDescriptionRequest,
) -> None:
    data.controller_id = controller_id
    await service.set_description(data)
