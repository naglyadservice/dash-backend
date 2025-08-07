from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses, controller_errors
from dash.services.common.errors.customer_carwash import (
    CarwashSessionActiveError,
    CarwashSessionNotFoundError,
)
from dash.services.common.errors.user import CustomerHasNoCardError
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


@router.post(
    "/{controller_id}/start",
    responses=build_responses(
        (409, (CarwashSessionActiveError,)),
        (400, (CustomerHasNoCardError,)),
        *controller_errors,
    ),
)
async def start_session(
    service: FromDishka[CustomerCarwashService],
    data: StartCarwashSessionRequest = Depends(),
) -> StartCarwashSessionResponse:
    return await service.start_session(data)


@router.post(
    "/{controller_id}/mode",
    responses=build_responses(
        (404, (CarwashSessionNotFoundError,)),
        *controller_errors,
    ),
)
async def select_mode(
    service: FromDishka[CustomerCarwashService],
    data: CarwashActionDTO,
    controller_id: UUID,
) -> SelectCarwashModeResponse:
    return await service.select_mode(
        SelectCarwashModeRequest(controller_id=controller_id, mode=data)
    )


@router.post(
    "/{controller_id}/finish",
    status_code=204,
    responses=build_responses(
        (404, (CarwashSessionNotFoundError,)),
        *controller_errors,
    ),
)
async def finish_session(
    service: FromDishka[CustomerCarwashService],
    data: FinishCarwashSessionRequest = Depends(),
) -> None:
    await service.finish_session(data)


@router.get(
    "/{controller_id}/summa",
    responses=build_responses(
        (404, (CarwashSessionNotFoundError,)),
        *controller_errors,
    ),
)
async def get_summa(
    service: FromDishka[CustomerCarwashService],
    data: GetCarwashSummaRequest = Depends(),
) -> GetCarwashSummaResponse:
    return await service.get_summa(data)
