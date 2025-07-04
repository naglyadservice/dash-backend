from dataclasses import dataclass
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.iot.carwash.customer_dto import (
    FinishCarwashSessionRequest,
    GetCarwashSummaRequest,
    GetCarwashSummaResponse,
    SelectCarwashModeRequest,
    SelectCarwashModeResponse,
    StartCarwashSessionRequest,
    StartCarwashSessionResponse,
)
from dash.services.iot.carwash.customer_service import CustomerCarwashService
from dash.services.iot.carwash.dto import CarwashActionDTO

router = APIRouter(
    prefix="/controllers/carwash",
    tags=["CUSTOMER -> CARWASH"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@dataclass
class AmountDTO:
    amount: int


@router.post("/{controller_id}/start", status_code=204)
async def start_session(
    service: FromDishka[CustomerCarwashService], data: AmountDTO, controller_id: UUID
) -> StartCarwashSessionResponse:
    return await service.start_session(
        StartCarwashSessionRequest(controller_id=controller_id, amount=data.amount)
    )


@router.post("/{controller_id}/mode")
async def select_mode(
    service: FromDishka[CustomerCarwashService],
    data: CarwashActionDTO,
    controller_id: UUID,
) -> SelectCarwashModeResponse:
    return await service.select_mode(
        SelectCarwashModeRequest(controller_id=controller_id, mode=data)
    )


@router.post("/{controller_id}/finish", status_code=204)
async def finish_session(
    service: FromDishka[CustomerCarwashService],
    data: FinishCarwashSessionRequest = Depends(),
) -> None:
    await service.finish_session(data)


@router.get("/{controller_id}/summa")
async def get_summa(
    service: FromDishka[CustomerCarwashService],
    data: GetCarwashSummaRequest = Depends(),
) -> GetCarwashSummaResponse:
    return await service.get_summa(data)
