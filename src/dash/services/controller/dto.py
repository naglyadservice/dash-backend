from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.controllers.controller import ControllerStatus, ControllerType
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination


class ControllerID(BaseModel):
    controller_id: UUID


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
