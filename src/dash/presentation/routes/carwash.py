from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.iot.carwash import CarwashControllerScheme
from dash.services.iot.carwash.service import CarwashService
from dash.services.iot.dto import ControllerID

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
