from uuid import UUID

from pydantic import BaseModel

from dash.services.iot.carwash.dto import CarwashActionDTO


class StartCarwashSessionRequest(BaseModel):
    controller_id: UUID
    amount: int


class SelectCarwashModeRequest(BaseModel):
    controller_id: UUID
    mode: CarwashActionDTO


class FinishCarwashSessionRequest(BaseModel):
    controller_id: UUID
