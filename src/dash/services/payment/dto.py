from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.payment import PaymentStatus, PaymentType
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination


class PaymentScheme(BaseModel):
    id: UUID
    controller_id: UUID
    amount: int
    status: PaymentStatus
    type: PaymentType
    created_at: datetime
    created_at_controller: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ReadPaymentListRequest(Pagination):
    company_id: UUID | None = None
    controller_id: UUID | None = None
    location_id: UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        if any(
            [
                values.get("controller_id"),
                values.get("location_id"),
                values.get("company_id"),
            ]
        ):
            raise ValidationError(
                "Filters 'controller_id', 'location_id' and 'company_id' cannot be used together"
            )
        return values


class ReadPaymentListResponse(BaseModel):
    payments: list[PaymentScheme]
    total: int


class GetPaymentStatsRequest(BaseModel):
    company_id: UUID | None = None
    location_id: UUID | None = None
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
