from dash.models.controllers.controller import ControllerType
from dash.services.iot.base import BaseIoTService
from dash.services.iot.carwash.service import CarwashService
from dash.services.iot.fiscalizer.service import FiscalizerService
from dash.services.iot.laundry.service import LaundryService
from dash.services.iot.wsm.service import WsmService


class IoTServiceFactory:
    def __init__(
        self,
        wsm: WsmService,
        carwash: CarwashService,
        fiscalizer: FiscalizerService,
        laundry: LaundryService,
    ) -> None:
        self.wsm = wsm
        self.carwash = carwash
        self.fiscalizer = fiscalizer
        self.laundry = laundry

    def get(self, controller_type: ControllerType) -> BaseIoTService:
        match controller_type:
            case ControllerType.CARWASH:
                return self.carwash
            case ControllerType.WATER_VENDING:
                return self.wsm
            case ControllerType.FISCALIZER:
                return self.fiscalizer
            case ControllerType.LAUNDRY:
                return self.laundry
            case _:
                raise ValueError(f"Unsupported controller type: {controller_type}")
