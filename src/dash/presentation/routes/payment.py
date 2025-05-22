from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.payment.dto import (GetPaymentStatsRequest,
                                       GetPaymentStatsResponse,
                                       ReadPaymentListRequest,
                                       ReadPaymentListResponse,
                                       ReadPublicPaymentListRequest,
                                       ReadPublicPaymentListResponse)
from dash.services.payment.service import PaymentService

payment_router = APIRouter(
    prefix="/payments",
    tags=["PAYMENTS"],
    route_class=DishkaRoute,
)


@payment_router.get("", dependencies=[bearer_scheme])
async def read_payments(
    payment_service: FromDishka[PaymentService],
    data: ReadPaymentListRequest = Depends(),
) -> ReadPaymentListResponse:
    return await payment_service.read_payments(data)


@payment_router.get("/statistics", dependencies=[bearer_scheme])
async def get_stats(
    payment_service: FromDishka[PaymentService],
    data: GetPaymentStatsRequest = Depends(),
) -> GetPaymentStatsResponse:
    return await payment_service.get_stats(data)

@payment_router.get("/public")
async def read_payments_public(
    payment_service: FromDishka[PaymentService],
    data: ReadPublicPaymentListRequest = Depends(),
) -> ReadPublicPaymentListResponse:
    return await payment_service.read_payments_public(data)
