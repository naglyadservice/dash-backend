from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.controllers.laundry import LaundryTariffType
from dash.models.transactions.laundry import LaundrySessionStatus
from dash.models.transactions.transaction import TransactionType
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination
from dash.services.iot.carwash.dto import CarwashTariffDTO, ServicesIntListDTO


class BaseTransactionFilters(BaseModel):
    controller_id: UUID | None = None
    location_id: UUID | None = None
    company_id: UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        filters = [
            values.get("controller_id"),
            values.get("location_id"),
            values.get("company_id"),
        ]
        active_filters = [f for f in filters if f is not None]

        if len(active_filters) > 1:
            raise ValidationError(
                "Only one filter can be used at a time. Please use either 'controller_id', 'location_id', or 'company_id'"
            )
        return values


class CustomerDTO(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    id: UUID
    type: TransactionType
    controller_transaction_id: int
    controller_id: UUID
    location_id: UUID | None
    coin_amount: int
    bill_amount: int
    prev_amount: int
    free_amount: int
    qr_amount: int
    paypass_amount: int
    card_amount: int
    created_at: datetime
    sale_type: Literal["no", "money", "card"]
    created_at_controller: datetime
    customer: CustomerDTO | None
    card_balance_in: int | None
    card_balance_out: int | None
    card_uid: str | None

    model_config = ConfigDict(from_attributes=True)


class WsmTransactionScheme(TransactionBase):
    out_liters_1: int
    out_liters_2: int


class CarwashServicesSoldDTO(ServicesIntListDTO):
    pass


class CarwashTransactionScheme(TransactionBase):
    services_sold_seconds: CarwashServicesSoldDTO
    tariff: CarwashTariffDTO
    replenishment_ratio: int | None


class FiscalizerTransactionScheme(TransactionBase):
    pass


class LaundryTransactionScheme(TransactionBase):
    tariff_type: LaundryTariffType
    session_status: LaundrySessionStatus
    session_start_time: datetime | None
    session_end_time: datetime | None
    hold_amount: int | None
    refund_amount: int | None
    final_amount: int


TRANSACTION_SCHEME_TYPE = (
    WsmTransactionScheme
    | CarwashTransactionScheme
    | FiscalizerTransactionScheme
    | LaundryTransactionScheme
)


class ReadTransactionListRequest(Pagination, BaseTransactionFilters):
    pass


class ReadTransactionListResponse(BaseModel):
    transactions: list[TRANSACTION_SCHEME_TYPE]
    total: int


class GetTransactionStatsRequest(BaseTransactionFilters):
    period: int


class TransactionStatDTO(BaseModel):
    date: date
    total: int
    bill: int
    coin: int
    qr: int
    paypass: int


class GetTransactionStatsResponse(BaseModel):
    statistics: list[TransactionStatDTO]
