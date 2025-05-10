from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.payment import PaymentStatus, PaymentType
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination


class PaymentScheme(BaseModel):
    id: int
    controller_id: int
    amount: int
    status: PaymentStatus
    type: PaymentType
    created_at: datetime
    created_at_controller: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ReadPaymentListRequest(Pagination):
    controller_id: UUID | None = None
    location_id: int | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("controller_id") and values.get("location_id"):
            raise ValidationError(
                "Filters 'controller_id' and 'location_id' cannot be used together"
            )
        return values


class ReadPaymentListResponse(BaseModel):
    payments: list[PaymentScheme]
    total: int


class GetPaymentStatsRequest(BaseModel):
    location_id: int | None = None
    controller_id: UUID | None = None
    period: int


class PaymentStatDTO(BaseModel):
    date: date
    total: int
    bill: int
    coin: int
    qr: int
    paypass: int


class GetPaymentStatsResponse(BaseModel):
    statistics: list[PaymentStatDTO]
