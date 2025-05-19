from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.controllers.controller import ControllerStatus, ControllerType
from dash.services.common.const import ControllerID
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination


class BaseControllerFilters(BaseModel):
    location_id: UUID | None = None
    company_id: UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        filters = [
            values.get("location_id"),
            values.get("company_id"),
        ]
        active_filters = [f for f in filters if f is not None]

        if len(active_filters) > 1:
            raise ValidationError(
                "Only one filter can be used at a time. Please use either 'location_id', or 'company_id'"
            )
        return values


class ReadControllerListRequest(Pagination, BaseControllerFilters):
    type: ControllerType | None = None


class ControllerScheme(BaseModel):
    id: UUID
    device_id: str
    location_id: UUID | None
    name: str
    type: ControllerType
    status: ControllerStatus

    model_config = ConfigDict(from_attributes=True)


class ReadControllerResponse(BaseModel):
    controllers: list[ControllerScheme]
    total: int


class AddControllerRequest(BaseModel):
    device_id: str
    type: ControllerType = ControllerType.WATER_VENDING
    name: str
    version: str
    status: ControllerStatus = ControllerStatus.ACTIVE


class AddControllerResponse(BaseModel):
    id: UUID


class MonopayCredentialsDTO(BaseModel):
    token: str | None
    is_active: bool


class AddMonopayCredentialsRequest(ControllerID):
    monopay: MonopayCredentialsDTO


class LiqpayCredentialsDTO(BaseModel):
    public_key: str | None
    private_key: str | None
    is_active: bool


class AddLiqpayCredentialsRequest(ControllerID):
    liqpay: LiqpayCredentialsDTO


class LocationID(BaseModel):
    location_id: UUID


class AddControllerLocationRequest(ControllerID, LocationID):
    pass


class EncashmentScheme(BaseModel):
    id: UUID
    created_at: datetime
    created_at_controller: datetime
    updated_at: datetime | None
    encashed_amount: int
    received_amount: int | None
    is_closed: bool
    coin_1: int
    coin_2: int
    coin_3: int
    coin_4: int
    coin_5: int
    coin_6: int
    bill_1: int
    bill_2: int
    bill_3: int
    bill_4: int
    bill_5: int
    bill_6: int
    bill_7: int
    bill_8: int

    model_config = ConfigDict(from_attributes=True)


class ReadEncashmentListRequest(Pagination):
    controller_id: UUID


class ReadEncashmentListResponse(BaseModel):
    encashments: list[EncashmentScheme]
    total: int


class CloseEncashmentRequest(BaseModel):
    encashment_id: UUID
    controller_id: UUID
    received_amount: int
