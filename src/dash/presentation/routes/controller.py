from dataclasses import dataclass
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.controller.dto import (AddControllerLocationRequest,
                                          AddControllerRequest,
                                          AddControllerResponse,
                                          AddLiqpayCredentialsRequest,
                                          AddMonopayCredentialsRequest,
                                          CloseEncashmentRequest,
                                          LiqpayCredentialsDTO, LocationID,
                                          MonopayCredentialsDTO,
                                          PublicCarwashScheme, PublicWsmScheme,
                                          ReadControllerListRequest,
                                          ReadControllerRequest,
                                          ReadControllerResponse,
                                          ReadEncashmentListRequest,
                                          ReadEncashmentListResponse,
                                          ReadPublicControllerListRequest,
                                          ReadPublicControllerListResponse)
from dash.services.controller.service import ControllerService

controller_router = APIRouter(
    prefix="/controllers",
    tags=["CONTROLLERS"],
    route_class=DishkaRoute,
)


@controller_router.get("", dependencies=[bearer_scheme])
async def read_controllers(
    controller_service: FromDishka[ControllerService],
    data: ReadControllerListRequest = Depends(),
) -> ReadControllerResponse:
    return await controller_service.read_controllers(data)


@controller_router.post("", dependencies=[bearer_scheme])
async def add_controller(
    controller_service: FromDishka[ControllerService],
    data: AddControllerRequest,
) -> AddControllerResponse:
    return await controller_service.add_controller(data)


@controller_router.post("/{controller_id}", status_code=204, dependencies=[bearer_scheme])
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


@controller_router.post("/{controller_id}/monopay, dependencies=[bearer_scheme]", status_code=204)
async def add_monopay_credentials(
    controller_service: FromDishka[ControllerService],
    data: MonopayCredentialsDTO,
    controller_id: UUID,
) -> None:
    await controller_service.add_monopay_credentials(
        AddMonopayCredentialsRequest(controller_id=controller_id, monopay=data)
    )


@controller_router.post("/{controller_id}/liqpay", status_code=204, dependencies=[bearer_scheme])
async def add_liqpay_credentials(
    controller_service: FromDishka[ControllerService],
    data: LiqpayCredentialsDTO,
    controller_id: UUID,
) -> None:
    await controller_service.add_liqpay_credentials(
        AddLiqpayCredentialsRequest(controller_id=controller_id, liqpay=data)
    )


@controller_router.get("/{controller_id}/encashments", dependencies=[bearer_scheme])
async def read_encashments(
    controller_service: FromDishka[ControllerService],
    data: ReadEncashmentListRequest = Depends(),
) -> ReadEncashmentListResponse:
    return await controller_service.read_encashments(data)


@dataclass
class EncashmentReceivedAmount:
    received_amount: int


@controller_router.post("/{controller_id}/encashments/{encashment_id}", status_code=204, dependencies=[bearer_scheme])
async def close_encashment(
    controller_service: FromDishka[ControllerService],
    controller_id: UUID,
    encashment_id: UUID,
    data: EncashmentReceivedAmount,
) -> None:
    await controller_service.close_encashment(
        CloseEncashmentRequest(
            controller_id=controller_id,
            encashment_id=encashment_id,
            received_amount=data.received_amount,
        )
    )


@controller_router.get("/public")
async def read_controller_list_public(
    controller_service: FromDishka[ControllerService],
    data: ReadPublicControllerListRequest = Depends(),
) -> ReadPublicControllerListResponse:
    return await controller_service.read_controller_list_public(data)

@controller_router.get("/public/{controller_id}")
async def read_controller_public(
    controller_service: FromDishka[ControllerService],
    data: ReadControllerRequest = Depends(),
) -> PublicWsmScheme | PublicCarwashScheme:
    return await controller_service.read_controller_public(data)
