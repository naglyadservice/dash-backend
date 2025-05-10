from uuid import UUID
from pydantic import BaseModel, ConfigDict

from dash.models.controllers.controller import ControllerStatus, ControllerType


class ControllerID(BaseModel):
    controller_id: UUID


class ReadControllerListRequest(BaseModel):
    type: ControllerType | None = None
    location_id: int | None = None


class ControllerScheme(BaseModel):
    id: int
    device_id: str
    location_id: int | None
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
    id: int


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
    location_id: int


class AddControllerLocationRequest(ControllerID, LocationID):
    pass
