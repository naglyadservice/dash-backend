from datetime import datetime, time, timedelta
from enum import IntEnum, StrEnum
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field

from dash.models.controllers.carwash import CarwashController
from dash.models.controllers.controller import ControllerType
from dash.services.common.const import COIN_VALIDATOR_TYPE, ControllerID


class CarwashConfig(BaseModel):
    ppos_apn: str | None = None
    wifi_STA_ssid: str | None = None
    wifi_STA_pass: str | None = None
    ntp_server: str | None = None
    timeZone: int | None = None
    broker_uri: str | None = None
    broker_port: int | None = None
    broker_user: str | None = None
    broker_pass: str | None = None
    OTA_server: str | None = None
    OTA_port: int | None = None
    bill_table: list[int] | None = Field(default=None, min_length=24, max_length=24)
    coinValidatorType: COIN_VALIDATOR_TYPE | None = None
    coinPulsePrice: int | None = None
    coin_table: list[int] | None = Field(default=None, min_length=16, max_length=16)


class RelayBit(IntEnum):
    VALVE_FOAM = 1
    VALVE_COLD_WATER = 2
    VALVE_HOT_WATER = 3
    VALVE_OSMOSIS = 4
    VALVE_BLACKENING = 5
    DOSE_FOAM = 6
    DOSE_WAX = 7
    DOSE_WINTER = 8
    DOSE_EXTRA_FOAM = 9
    PUMP_FOAM = 10
    PUMP_WATER = 11
    RESERVED_1 = 12
    RESERVED_2 = 13


class CarwashServicesRelay(BaseModel):
    relay_1: list[RelayBit] | None = None
    relay_2: list[RelayBit] | None = None
    relay_3: list[RelayBit] | None = None
    relay_4: list[RelayBit] | None = None
    relay_5: list[RelayBit] | None = None
    relay_6: list[RelayBit] | None = None
    relay_7: list[RelayBit] | None = None
    relay_8: list[RelayBit] | None = None


class CarwashSettings(BaseModel):
    maxPayment: int | None = None
    minPayPass: int | None = None
    maxPayPass: int | None = None
    deltaPayPass: int | None = None
    timeOnePay: int | None = None
    timePause: int | None = None
    servicesRelay: CarwashServicesRelay | None = None
    servicesPause: list[int] | None = Field(min_length=8, max_length=8)
    vfdFrequency: list[int] | None = Field(min_length=8, max_length=8)
    tariff: list[int] | None = Field(min_length=8, max_length=8)
    pulsesPerLiter: int | None = None
    enableSrcAfterPause: bool | None = None
    timeLight: int | None = None
    timeTechnicalMode: int | None = None


class CarwashOperatingMode(StrEnum):
    WAIT = "WAIT"
    BLOCK = "BLOCK"
    INCASS = "INCASS"
    TECHNICAL = "TECHNICAL"
    SALEMONEY = "SALEMONEY"
    PAYPASS = "PAYPASS"
    SALECARD = "SALECARD"
    STARTTEST = "STARTTEST"


class CarwashSensorState(BaseModel):
    hum: int
    temp: list[int]


class CarwashStateErrors(BaseModel):
    ServerBlock: bool
    reserv_1: bool
    reserv_2: bool
    reserv_3: bool
    coinValidator: bool
    billValidator: bool
    PayPass: bool
    Card: bool


class CarwashState(BaseModel):
    created: datetime
    summaInBox: int
    operatingMode: CarwashOperatingMode
    service: Literal[
        "none",
        "pause",
        "foam",
        "foam_extra",
        "water_pressured",
        "water_warm",
        "osmos",
        "wax",
        "winter",
        "blackening",
    ]
    timer: time
    summa: int
    depositBoxSensor: bool
    doorSensor: bool
    coinState: int
    billState: int
    sensors: CarwashSensorState
    ext_sensors: CarwashSensorState
    errors: CarwashStateErrors


class CarwashControllerScheme(BaseModel):
    id: UUID
    device_id: str
    name: str | None
    type: Literal[ControllerType.CARWASH]
    config: CarwashConfig | None
    settings: CarwashSettings | None
    state: CarwashState | None = None
    alert: str | None = None

    @classmethod
    def make(cls, controller: CarwashController, state: dict[str, Any] | None) -> Self:
        dto = cls.model_validate(controller, from_attributes=True)
        if state:
            dto.state = CarwashState.model_validate(state)
            if dto.state.created + timedelta(minutes=5) < datetime.now():
                dto.alert = "Контроллер не надсилав оновлення більше 5 хвилин"
        return dto


class SetCarwashConfigRequest(ControllerID):
    config: CarwashConfig


class SetCarwashSettingsRequest(ControllerID):
    settings: CarwashSettings


class GetDisplayInfoRequest(ControllerID):
    pass
