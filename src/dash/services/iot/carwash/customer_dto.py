from pydantic import BaseModel, field_validator

from dash.services.common.dto import ControllerID
from dash.services.common.errors.base import ValidationError
from dash.services.iot.carwash.dto import CarwashActionDTO


class StartCarwashSessionRequest(ControllerID):
    amount: int

    @field_validator("amount")
    @classmethod
    def validate(cls, v: int) -> int:
        if v < 1000:
            raise ValidationError("'amount' cannot be less than 1000")
        return v


class StartCarwashSessionResponse(BaseModel):
    timeout: int


class SelectCarwashModeRequest(ControllerID):
    mode: CarwashActionDTO


class SelectCarwashModeResponse(BaseModel):
    timeout: int


class FinishCarwashSessionRequest(ControllerID):
    pass


class GetCarwashSummaRequest(ControllerID):
    pass


class GetCarwashSummaResponse(BaseModel):
    summa: int
