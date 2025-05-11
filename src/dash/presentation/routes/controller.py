from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.controller.controller import ControllerService
from dash.services.controller.dto import (
    AddControllerLocationRequest,
    AddControllerRequest,
    AddControllerResponse,
    AddLiqpayCredentialsRequest,
    AddMonopayCredentialsRequest,
    LiqpayCredentialsDTO,
    LocationID,
    MonopayCredentialsDTO,
    ReadControllerListRequest,
    ReadControllerResponse,
)

controller_router = APIRouter(
    prefix="/controllers",
    tags=["CONTROLLERS"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@controller_router.get("")
async def read_controllers(
    controller_service: FromDishka[ControllerService],
    data: ReadControllerListRequest = Depends(),
) -> ReadControllerResponse:
    return await controller_service.read_controllers(data)


@controller_router.post("")
async def add_controller(
    controller_service: FromDishka[ControllerService],
    data: AddControllerRequest,
) -> AddControllerResponse:
    return await controller_service.add_controller(data)


@controller_router.post("/{controller_id}", status_code=204)
async def add_controller_location(
    controller_service: FromDishka[ControllerService],
    data: LocationID,
    controller_id: UUID,
) -> None:
    return await controller_service.add_location(
        AddControllerLocationRequest(
            controller_id=controller_id, location_id=data.location_id
        )
    )


@controller_router.post("/{controller_id}/monopay", status_code=204)
async def add_monopay_credentials(
    controller_service: FromDishka[ControllerService],
    data: MonopayCredentialsDTO,
    controller_id: UUID,
) -> None:
    await controller_service.add_monopay_credentials(
        AddMonopayCredentialsRequest(controller_id=controller_id, monopay=data)
    )


@controller_router.post("/{controller_id}/liqpay", status_code=204)
async def add_liqpay_credentials(
    controller_service: FromDishka[ControllerService],
    data: LiqpayCredentialsDTO,
    controller_id: UUID,
) -> None:
    await controller_service.add_liqpay_credentials(
        AddLiqpayCredentialsRequest(controller_id=controller_id, liqpay=data)
    )
