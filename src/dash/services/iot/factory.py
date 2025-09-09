from dash.models.controllers.controller import ControllerType
from dash.services.iot.base import BaseIoTService
from dash.services.iot.car_cleaner.service import CarCleanerService
from dash.services.iot.carwash.service import CarwashService
from dash.services.iot.dummy.service import DummyService
from dash.services.iot.fiscalizer.service import FiscalizerService
from dash.services.iot.laundry.service import LaundryService
from dash.services.iot.vacuum.service import VacuumService
from dash.services.iot.wsm.service import WsmService


class IoTServiceFactory:
    def __init__(
        self,
        wsm: WsmService,
        carwash: CarwashService,
        car_cleaner: CarCleanerService,
        fiscalizer: FiscalizerService,
        laundry: LaundryService,
        vacuum: VacuumService,
        dummy: DummyService,
    ) -> None:
        self.wsm = wsm
        self.carwash = carwash
        self.car_cleaner = car_cleaner
        self.fiscalizer = fiscalizer
        self.laundry = laundry
        self.vacuum = vacuum
        self.dummy = dummy

    def get(self, controller_type: ControllerType) -> BaseIoTService:
        match controller_type:
            case ControllerType.CARWASH:
                return self.carwash
            case ControllerType.CAR_CLEANER:
                return self.car_cleaner
            case ControllerType.WATER_VENDING:
                return self.wsm
            case ControllerType.FISCALIZER:
                return self.fiscalizer
            case ControllerType.LAUNDRY:
                return self.laundry
            case ControllerType.VACUUM:
                return self.vacuum
            case ControllerType.DUMMY:
                return self.dummy
            case _:
                raise ValueError(f"Unsupported controller type: {controller_type}")
