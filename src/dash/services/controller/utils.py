import random

from dash.models.controllers.controller import ControllerType

QR_PREFIX_MAP = {
    ControllerType.WATER_VENDING: "ws",
    ControllerType.FISCALIZER: "f",
    ControllerType.LAUNDRY: "l",
    ControllerType.CARWASH: "cw",
    ControllerType.VACUUM: "vc",
    ControllerType.CAR_CLEANER: "dc",
    ControllerType.DUMMY: "du"
}


def generate_qr(controller_type: ControllerType) -> str:
    return f"{QR_PREFIX_MAP[controller_type]}-{random.randint(0, 9999):04}"
