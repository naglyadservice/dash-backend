from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.payment.dto import (
    GetPaymentStatsRequest,
    GetPaymentStatsResponse,
    ReadPaymentListRequest,
    ReadPaymentListResponse,
)
from dash.services.payment.service import PaymentService

payment_router = APIRouter(
    prefix="/payments",
    tags=["PAYMENTS"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@payment_router.get("")
async def read_payments(
    payment_service: FromDishka[PaymentService],
    data: ReadPaymentListRequest = Depends(),
) -> ReadPaymentListResponse:
    return await payment_service.read_payments(data)


@payment_router.get("/statistics")
async def get_stats(
    payment_service: FromDishka[PaymentService],
    data: GetPaymentStatsRequest = Depends(),
) -> GetPaymentStatsResponse:
    return await payment_service.get_stats(data)
