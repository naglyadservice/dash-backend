from pydantic import BaseModel

from dash.services.common.dto import ControllerID
from dash.services.iot.carwash.dto import CarwashActionDTO


class StartCarwashSessionRequest(ControllerID):
    amount: int


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
