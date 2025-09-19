from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.location.dto import (
    CreateLocationRequest,
    CreateLocationResponse,
    DeleteLocationRequest,
    EditLocationDTO,
    EditLocationRequest,
    ReadLocationListRequest,
    ReadLocationListResponse,
)
from dash.services.location.service import LocationService

location_router = APIRouter(
    prefix="/locations",
    tags=["LOCATIONS"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@location_router.post(
    "",
    responses=build_responses(
        (404, (CompanyNotFoundError,)),
    ),
)
async def create_location(
    service: FromDishka[LocationService],
    data: CreateLocationRequest,
) -> CreateLocationResponse:
    return await service.create_location(data)


@location_router.get("")
async def read_locations(
    service: FromDishka[LocationService],
    data: ReadLocationListRequest = Depends(),
) -> ReadLocationListResponse:
    return await service.read_locations(data)


@location_router.patch(
    "/{location_id}",
    status_code=204,
    responses=build_responses(
        (404, (CompanyNotFoundError,)),
    ),
)
async def edit_location(
    service: FromDishka[LocationService], data: EditLocationDTO, location_id: UUID
) -> None:
    return await service.edit_location(
        EditLocationRequest(location_id=location_id, data=data)
    )


@location_router.delete(
    "/{location_id}",
    status_code=204,
    responses=build_responses(
        (404, (CompanyNotFoundError,)),
    ),
)
async def delete_location(
    service: FromDishka[LocationService], data: DeleteLocationRequest = Depends()
) -> None:
    return await service.delete(data)
