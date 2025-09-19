from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.controllers.laundry import LaundryTariffType
from dash.models.transactions.laundry import LaundrySessionStatus
from dash.models.transactions.transaction import TransactionType
from dash.services.common.dto import BaseFilters
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination
from dash.services.iot.car_cleaner.dto import (
    CarCleanerTariffDTO,
    CarCleanerServicesIntListDTO,
)
from dash.services.iot.carwash.dto import CarwashTariffDTO, CarwashServicesIntListDTO
from dash.services.iot.vacuum.dto import VacuumServicesIntListDTO, VacuumTariffDTO


class CustomerDTO(BaseModel):
    id: UUID
    name: str
    readable_card_code: str | None

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    id: UUID
    type: TransactionType
    controller_transaction_id: int
    controller_id: UUID | None
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


class CarCleanerServicesSoldDTO(CarCleanerServicesIntListDTO):
    pass


class CarwashServicesSoldDTO(CarwashServicesIntListDTO):
    pass


class CarCleanerTransactionScheme(TransactionBase):
    services_sold_seconds: CarCleanerServicesSoldDTO
    tariff: CarCleanerTariffDTO
    replenishment_ratio: int | None


class CarwashTransactionScheme(TransactionBase):
    services_sold_seconds: CarwashServicesSoldDTO
    tariff: CarwashTariffDTO
    replenishment_ratio: int | None


class FiscalizerTransactionScheme(TransactionBase):
    pass


class LaundryTransactionScheme(TransactionBase):
    created_at_controller: None = None
    controller_transaction_id: None = None

    tariff_type: LaundryTariffType
    session_status: LaundrySessionStatus
    session_start_time: datetime | None
    session_end_time: datetime | None
    hold_amount: int | None
    refund_amount: int | None
    final_amount: int


class VacuumServicesSoldDTO(VacuumServicesIntListDTO):
    glass_washer: float


class VacuumTransactionScheme(TransactionBase):
    services_sold_seconds: VacuumServicesSoldDTO
    tariff: VacuumTariffDTO
    replenishment_ratio: int | None


TRANSACTION_SCHEME_TYPE = (
    WsmTransactionScheme
    | CarCleanerTransactionScheme
    | CarwashTransactionScheme
    | FiscalizerTransactionScheme
    | LaundryTransactionScheme
    | VacuumTransactionScheme
)


class ReadTransactionListRequest(Pagination, BaseFilters):
    date_from: datetime | None = None
    date_to: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        if (
            values.get("date_from")
            and values.get("date_to")
            and values["date_from"] > values["date_to"]
        ):
            raise ValidationError("date_from should be less than date_to")

        return values


class ReadTransactionListResponse(BaseModel):
    transactions: list[TRANSACTION_SCHEME_TYPE]
    total: int
