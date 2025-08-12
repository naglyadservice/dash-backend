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


class VacuumConfig(BaseModel):
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


class VacuumRelayBit(IntEnum):
    VACUUM_CLEANER = 1
    BLOWING = 2
    WHEEL_INFLATION = 3
    GLASS_WASHER = 4
    VALVE_BLACKENING = 5
    PUMP_BLACKENING = 6
    RESERVED_1 = 7
    RESERVED_2 = 8
    RESERVED_3 = 9
    RESERVED_4 = 10
    RESERVED_5 = 11
    RESERVED_6 = 12
    RESERVED_7 = 13


class VacuumServicesRelayDTO(BaseModel):
    vacuum_cleaner: list[VacuumRelayBit] | None = None
    blowing: list[VacuumRelayBit] | None = None
    wheel_inflation: list[VacuumRelayBit] | None = None
    glass_washer: list[VacuumRelayBit] | None = None
    blackening: list[VacuumRelayBit] | None = None


class VacuumServiceEnum(StrEnum):
    VACUUM_CLEANER = "vacuum_cleaner"
    BLOWING = "blowing"
    WHEEL_INFLATION = "wheel_inflation"
    GLASS_WASHER = "glass_washer"
    BLACKENING = "blackening"


class VacuumServicesIntListDTO(BaseModel):
    vacuum_cleaner: int | None = None
    blowing: int | None = None
    wheel_inflation: int | None = None
    glass_washer: int | None = None
    blackening: int | None = None


class VacuumServicesPauseDTO(VacuumServicesIntListDTO):
    pass


class VacuumTariffDTO(VacuumServicesIntListDTO):
    pass


class VacuumSettings(BaseModel):
    maxPayPass: int | None = None
    minPayPass: int | None = None
    deltaPayPass: int | None = None
    servicesPause: VacuumServicesPauseDTO | None = None
    tariff: VacuumTariffDTO | None = None
    pulsesPerLiter: int | None = None
    timeOnePay: int | None = None
    timePause: int | None = None
    servicesRelay: VacuumServicesRelayDTO | None = None
    enableSrvAfterPause: bool | None = None
    lightBtnAfterPay: bool | None = None
    timeLight: int | None = None
    timeTechnicalMode: int | None = None


class VacuumOperatingMode(StrEnum):
    WAIT = "WAIT"
    BLOCK = "BLOCK"
    INCASS = "INCASS"
    TECHNICAL = "TECHNICAL"
    SALEMONEY = "SALEMONEY"
    PAYPASS = "PAYPASS"
    SALECARD = "SALECARD"
    STARTTEST = "STARTTEST"


class VacuumSensorState(BaseModel):
    hum: int
    temp: list[int]


class VacuumStateErrors(BaseModel):
    ServerBlock: bool
    ExtPlata: bool
    PresenceWater: bool
    reserv: bool
    coinValidator: bool
    billValidator: bool
    PayPass: bool
    Card: bool


class VacuumState(BaseModel):
    created: datetime
    summaInBox: int
    operatingMode: VacuumOperatingMode
    service: Literal[
        "none",
        "pause",
        "vacuum_cleaner",
        "blowing",
        "wheel_inflation",
        "glass_washer",
        "blackening",
    ]
    timer: str
    summa: float
    depositBoxSensor: bool
    doorSensor: bool
    coinState: int
    billState: int | str
    sensors: VacuumSensorState
    ext_sensors: VacuumSensorState
    errors: VacuumStateErrors


class VacuumIoTControllerScheme(IoTControllerBaseDTO):
    config: VacuumConfig | None
    settings: VacuumSettings | None
    state: VacuumState | None = None

    @classmethod
    def get_state_dto(cls):
        return VacuumState


class SetVacuumConfigRequest(SetConfigRequest):
    config: VacuumConfig


class SetVacuumSettingsRequest(SetSettingsRequest):
    settings: VacuumSettings


class VacuumActionDTO(BaseModel):
    Service: (
        Literal[
            "Pause",
            "Vacuum_cleaner",
            "Blowing",
            "Wheel_inflation",
            "Glass_washer",
            "Blackening",
        ]
        | None
    ) = None
    Blocking: bool | None = None


class SendVacuumActionRequest(SendActionRequest):
    action: VacuumActionDTO


class GetVacuumDisplayResponse(BaseModel):
    mode: str
    service: str
    summa: float
    time: int
