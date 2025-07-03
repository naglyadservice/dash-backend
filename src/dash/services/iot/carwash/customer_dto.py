from uuid import UUID

from pydantic import BaseModel, field_validator

from dash.services.common.errors.base import ValidationError
from dash.services.iot.carwash.dto import CarwashActionDTO


class StartCarwashSessionRequest(BaseModel):
    controller_id: UUID
    amount: int

    @field_validator("amount")
    @classmethod
    def validate(cls, v: int) -> int:
        if v < 1000:
            raise ValidationError("'amount' cannot be less than 1000")
        return v


class StartCarwashSessionResponse(BaseModel):
    timeout: int


class SelectCarwashModeRequest(BaseModel):
    controller_id: UUID
    mode: CarwashActionDTO


class SelectCarwashModeResponse(BaseModel):
    timeout: int


class FinishCarwashSessionRequest(BaseModel):
    controller_id: UUID
