from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from dash.services.common.const import COIN_VALIDATOR_TYPE
from dash.services.iot.dto import (
    IoTControllerBaseDTO,
    SendActionRequest,
    SetConfigRequest,
    SetSettingsRequest,
)


class CarCleanerConfig(BaseModel):
    pppos_apn: str | None = None
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
    cardReaderType: Literal["no", "card", "keyfob"] | None = None


class CarCleanerRelayBit(IntEnum):
    VACUUM_CLEANER = 1
    WET_VACUUM_CLEANER = 2
    STEAM_VACUUM_CLEANER = 3
    BLOWING = 4
    VALVE_SPRAYER = 5
    VALVE_TORNADORE = 6
    PUMP_SPRAYER = 7
    PUMP_TORNADORE = 8
    RESERVED_1 = 9
    RESERVED_2 = 10
    RESERVED_3 = 11
    RESERVED_4 = 12
    RESERVED_5 = 13


class CarCleanerServicesRelayDTO(BaseModel):
    vacuum_cleaner: list[CarCleanerRelayBit]
    wet_vacuum_cleaner: list[CarCleanerRelayBit]
    steam_vacuum_cleaner: list[CarCleanerRelayBit]
    blowing: list[CarCleanerRelayBit]
    sprayer: list[CarCleanerRelayBit]
    tornadore: list[CarCleanerRelayBit]


class CarCleanerServiceEnum(StrEnum):
    VACUUM_CLEANER = "vacuum_cleaner"
    WET_VACUUM_CLEANER = "wet_vacuum_cleaner"
    STEAM_VACUUM_CLEANER = "steam_vacuum_cleaner"
    BLOWING = "blowing"
    SPRAYER = "sprayer"
    TORNADORE = "tornadore"


class CarCleanerServicesIntListDTO(BaseModel):
    vacuum_cleaner: int
    wet_vacuum_cleaner: int
    steam_vacuum_cleaner: int
    blowing: int
    sprayer: int
    tornadore: int


class CarCleanerServicesPauseDTO(CarCleanerServicesIntListDTO):
    pass


class CarCleanerTariffDTO(CarCleanerServicesIntListDTO):
    pass


class CarCleanerSettings(BaseModel):
    maxPayPass: int | None = None
    minPayPass: int | None = None
    deltaPayPass: int | None = None
    servicesPause: CarCleanerServicesPauseDTO | None = None
    tariff: CarCleanerTariffDTO | None = None
    pulsesPerLiter: int | None = None
    timeOnePay: int | None = None
    timePause: int | None = None
    servicesRelay: CarCleanerServicesRelayDTO | None = None
    enableSrvAfterPause: bool | None = None
    lightBtnAfterPay: bool | None = None
    timeLight: int | None = None
    timeTechnicalMode: int | None = None


class CarCleanerOperatingMode(StrEnum):
    WAIT = "WAIT"
    BLOCK = "BLOCK"
    INCASS = "INCASS"
    TECHNICAL = "TECHNICAL"
    SALEMONEY = "SALEMONEY"
    PAYPASS = "PAYPASS"
    SALECARD = "SALECARD"
    STARTTEST = "STARTTEST"


class CarCleanerSensorState(BaseModel):
    hum: int
    temp: list[int]


class CarCleanerStateErrors(BaseModel):
    ServerBlock: bool
    ExtPlata: bool
    PresenceWater: bool
    reserv: bool
    coinValidator: bool
    billValidator: bool
    PayPass: bool
    Card: bool


class CarCleanerState(BaseModel):
    created: datetime
    summaInBox: int
    operatingMode: CarCleanerOperatingMode
    service: Literal[
        "none",
        "pause",
        "vacuum_cleaner",
        "wet_vacuum_cleaner",
        "steam_vacuum_cleaner",
        "blowing",
        "sprayer",
        "tornadore",
    ]
    timer: str
    summa: float
    depositBoxSensor: bool
    doorSensor: bool
    coinState: int
    billState: int | str
    sensors: CarCleanerSensorState
    ext_sensors: CarCleanerSensorState
    errors: CarCleanerStateErrors


class CarCleanerIoTControllerScheme(IoTControllerBaseDTO):
    config: CarCleanerConfig | None
    settings: CarCleanerSettings | None
    state: CarCleanerState | None = None

    @classmethod
    def get_state_dto(cls):
        return CarCleanerState


class SetCarCleanerConfigRequest(SetConfigRequest):
    config: CarCleanerConfig


class SetCarCleanerSettingsRequest(SetSettingsRequest):
    settings: CarCleanerSettings


class CarCleanerActionDTO(BaseModel):
    Service: (
        Literal[
            "Pause",
            "Vacuum_cleaner",
            "Wet_vacuum_cleaner",
            "Steam_vacuum_cleaner",
            "Blowing",
            "Sprayer",
            "Tornadore",
        ]
        | None
    ) = None


class SendCarCleanerActionRequest(SendActionRequest):
    action: CarCleanerActionDTO


class GetCarCleanerDisplayResponse(BaseModel):
    mode: str
    service: str
    summa: float
    time: int
