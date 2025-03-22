from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.services.controller.controller import ControllerService
from dash.services.controller.dto import ReadControllerRequest, ReadControllerResponse

controller_router = APIRouter(
    prefix="/controllers", tags=["CONTROLLERS"], route_class=DishkaRoute
)


@controller_router.get("")
async def read_controllers(
    controller_service: FromDishka[ControllerService],
    data: ReadControllerRequest = Depends(),
) -> ReadControllerResponse:
    return await controller_service.read_controllers(data)
