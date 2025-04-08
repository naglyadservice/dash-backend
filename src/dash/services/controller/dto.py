from pydantic import BaseModel, ConfigDict

from dash.models.controllers.controller import ControllerStatus, ControllerType
from dash.services.common.pagination import Pagination


class ControllerID(BaseModel):
    controller_id: int


class ReadControllerListRequest(Pagination):
    type: ControllerType | None = None
    location_id: int | None = None


class ControllerScheme(BaseModel):
    id: int
    device_id: str
    location_id: int
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


class MonopayTokenDTO(BaseModel):
    token: str


class AddMonopayTokenRequest(ControllerID):
    monopay: MonopayTokenDTO


class LocationID(BaseModel):
    location_id: int


class AddControllerLocationRequest(ControllerID, LocationID):
    pass
