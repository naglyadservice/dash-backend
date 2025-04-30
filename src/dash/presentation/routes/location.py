from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from dash.presentation.bearer import bearer_scheme
from dash.services.location.dto import (
    CreateLocationRequest,
    CreateLocationResponse,
    ReadLocationListResponse,
)
from dash.services.location.location import LocationService

location_router = APIRouter(
    prefix="/locations",
    tags=["LOCATIONS"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@location_router.post("")
async def create_location(
    location_service: FromDishka[LocationService],
    data: CreateLocationRequest,
) -> CreateLocationResponse:
    return await location_service.create_location(data)


@location_router.get("")
async def read_locations(
    location_service: FromDishka[LocationService],
) -> ReadLocationListResponse:
    return await location_service.read_locations()
