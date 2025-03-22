from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.services.payment.dto import ReadPaymentsRequest, ReadPaymentsResponse
from dash.services.payment.payment import PaymentService

payment_router = APIRouter(
    prefix="/payments", tags=["PAYMENTS"], route_class=DishkaRoute
)


@payment_router.get("")
async def read_payments(
    payment_service: FromDishka[PaymentService],
    data: ReadPaymentsRequest = Depends(),
) -> ReadPaymentsResponse:
    return await payment_service.read_payments(data)
