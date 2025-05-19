from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.carwash.carwash import CarwashService
from dash.services.carwash.dto import CarwashControllerScheme
from dash.services.common.const import ControllerID

carwash_router = APIRouter(
    prefix="/carwash",
    tags=["CARWASH"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@carwash_router.get("/{controller_id}")
async def read_controller(
    carwash_service: FromDishka[CarwashService],
    data: ControllerID = Depends(),
) -> CarwashControllerScheme:
    return await carwash_service.read_controller(data)
