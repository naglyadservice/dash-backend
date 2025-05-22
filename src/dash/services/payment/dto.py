from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.payment import PaymentStatus, PaymentType
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination


class BasePaymentFilters(BaseModel):
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


class PaymentScheme(BaseModel):
    id: UUID
    controller_id: UUID
    amount: int
    status: PaymentStatus
    type: PaymentType
    created_at: datetime
    created_at_controller: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ReadPaymentListRequest(Pagination, BasePaymentFilters):
    pass

class ReadPaymentListResponse(BaseModel):
    payments: list[PaymentScheme]
    total: int

class ReadPublicPaymentListRequest(BaseModel):
    controller_id: UUID
    limit: Literal[3, 5]

class ReadPublicPaymentListResponse(BaseModel):
    payments: list[PaymentScheme]

class GetPaymentStatsRequest(BasePaymentFilters):
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
