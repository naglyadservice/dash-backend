from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.services.transaction.dto import (
    ReadTransactionsRequest,
    ReadTransactionsResponse,
)
from dash.services.transaction.transaction import TransactionService

transaction_router = APIRouter(
    prefix="/transactions", tags=["TRANSACTIONS"], route_class=DishkaRoute
)


@transaction_router.get("")
async def read_transactions(
    transaction_service: FromDishka[TransactionService],
    data: ReadTransactionsRequest = Depends(),
) -> ReadTransactionsResponse:
    return await transaction_service.read_transactions(data)
