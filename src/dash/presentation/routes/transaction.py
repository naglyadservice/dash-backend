from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.transaction.dto import (
    GetTransactionStatsRequest,
    GetTransactionStatsResponse,
    ReadTransactionListRequest,
    ReadTransactionListResponse,
)
from dash.services.transaction.service import TransactionService

transaction_router = APIRouter(
    prefix="/transactions",
    tags=["TRANSACTIONS"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@transaction_router.get("")
async def read_transactions(
    transaction_service: FromDishka[TransactionService],
    data: ReadTransactionListRequest = Depends(),
) -> ReadTransactionListResponse:
    return await transaction_service.read_transactions(data)


@transaction_router.get("/statistics")
async def get_stats(
    transaction_service: FromDishka[TransactionService],
    data: GetTransactionStatsRequest = Depends(),
) -> GetTransactionStatsResponse:
    return await transaction_service.get_stats(data)
