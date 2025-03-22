from datetime import datetime

from pydantic import BaseModel, ConfigDict

from dash.models.transactions.transaction import TransactionType
from dash.services.common.pagination import Pagination


class TransactionBase(BaseModel):
    id: int
    type: TransactionType
    controller_transaction_id: int
    controller_id: int
    location_id: int | None
    coin_amount: int
    bill_amount: int
    prev_amount: int
    free_amount: int
    qr_amount: int
    paypass_amount: int
    created_at: datetime
    received_at: datetime


class WaterVendingTransactionScheme(TransactionBase):
    out_liters_1: int
    out_liters_2: int
    sale_type: str

    model_config = ConfigDict(from_attributes=True)


TRANSACTION_SCHEME_TYPE = WaterVendingTransactionScheme


class ReadTransactionsRequest(Pagination):
    controller_id: int | None = None


class ReadTransactionsResponse(BaseModel):
    transactions: list[TRANSACTION_SCHEME_TYPE]
    total: int
