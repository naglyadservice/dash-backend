from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.transactions.transaction import TransactionType
from dash.services.common.errors.base import ValidationError
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
    created_at_controller: datetime


class WaterVendingTransactionScheme(TransactionBase):
    out_liters_1: int
    out_liters_2: int
    sale_type: str

    model_config = ConfigDict(from_attributes=True)


TRANSACTION_SCHEME_TYPE = WaterVendingTransactionScheme


class ReadTransactionListRequest(Pagination):
    controller_id: UUID | None = None
    location_id: int | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values["controller_id"] and values["location_id"]:
            raise ValidationError(
                "Filters 'controller_id' and 'location_id' cannot be used together"
            )
        return values


class ReadTransactionListResponse(BaseModel):
    transactions: list[TRANSACTION_SCHEME_TYPE]
    total: int


class GetTransactionStatsRequest(BaseModel):
    location_id: int | None = None
    controller_id: UUID | None = None
    period: int


class TransactionStatDTO(BaseModel):
    date: date
    total: int
    bill: int
    coin: int
    qr: int
    paypass: int
    out_liters_1: int | None = None
    out_liters_2: int | None = None


class GetTransactionStatsResponse(BaseModel):
    statistics: list[TransactionStatDTO]
