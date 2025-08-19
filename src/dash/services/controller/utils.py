import random

from dash.models.controllers.controller import ControllerType

QR_PREFIX_MAP = {
    ControllerType.CARWASH: "c",
    ControllerType.WATER_VENDING: "w",
    ControllerType.FISCALIZER: "f",
    ControllerType.VACUUM: "v",
    ControllerType.LAUNDRY: "l",
    ControllerType.CAR_CLEANER: "cс"
}


def generate_qr(controller_type: ControllerType) -> str:
    return f"{QR_PREFIX_MAP[controller_type]}-{random.randint(0, 9999):04}"
