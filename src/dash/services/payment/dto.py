from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dash.models.payment import PaymentStatus, PaymentType, PaymentGatewayType
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
    receipt_url: str | None
    amount: int
    status: PaymentStatus
    type: PaymentType
    gateway_type: PaymentGatewayType | None
    created_at: datetime
    created_at_controller: datetime | None
    failure_reason: str | None
    checkbox_error: str | None
    masked_pan: str | None

    model_config = ConfigDict(from_attributes=True)


class PublicPaymentScheme(BaseModel):
    id: UUID
    amount: int
    created_at: datetime
    type: PaymentType
    receipt_url: str

    model_config = ConfigDict(from_attributes=True)


class ReadPaymentListRequest(Pagination, BasePaymentFilters):
    date_from: datetime | None = None
    date_to: datetime | None = None
    masked_pan: str | None = Field(default=None, min_length=16, max_length=16)

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


class ReadPaymentListResponse(BaseModel):
    payments: list[PaymentScheme]
    total: int


class ReadPublicPaymentListRequest(BaseModel):
    qr: str


class ReadPublicPaymentListResponse(BaseModel):
    payments: list[PublicPaymentScheme]
