from dash.models.controllers.controller import ControllerType
from dash.services.iot.base import BaseIoTService
from dash.services.iot.carwash.service import CarwashService
from dash.services.iot.wsm.service import WsmService


class IoTServiceFactory:
    def __init__(self, wsm: WsmService, carwash: CarwashService) -> None:
        self.wsm = wsm
        self.carwash = carwash

    def get(self, controller_type: ControllerType) -> BaseIoTService:
        match controller_type:
            case ControllerType.CARWASH:
                return self.carwash
            case ControllerType.WATER_VENDING:
                return self.wsm
            case _:
                raise ValueError(f"Unsupported controller type: {controller_type}")
