from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from dash.services.common.const import COIN_VALIDATOR_TYPE
from dash.services.iot.dto import (
    IoTControllerBaseDTO,
    SendActionRequest,
    SetConfigRequest,
    SetSettingsRequest,
)


class WsmConfig(BaseModel):
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


class SetWsmConfigRequest(SetConfigRequest):
    config: WsmConfig


class WsmSettings(BaseModel):
    maxPayment: int | None = None
    minPayPass: int | None = None
    maxPayPass: int | None = None
    deltaPayPass: int | None = None
    tariffPerLiter_1: int | None = None
    tariffPerLiter_2: int | None = None
    pulsesPerLiter_1: int | None = None
    pulsesPerLiter_2: int | None = None
    pulsesPerLiter_3: int | None = None
    timeOnePay: int | None = None
    litersInFullTank: int | None = None
    timeServiceMode: int | None = None
    spillTimer: int | None = None
    spillAmount: int | None = None


class SetWsmSettingsRequest(SetSettingsRequest):
    settings: WsmSettings


class WsmOperatingMode(StrEnum):
    WAIT = "WAIT"
    BLOCK = "BLOCK"
    INCASS = "INCASS"
    SERVICE = "SERVICE"
    SPILL = "SPILL"
    CALIBRATION = "CALIBRATION"
    SALEMONEY = "SALEMONEY"
    PAYPASS = "PAYPASS"
    SALECARD = "SALECARD"
    STARTTEST = "STARTTEST"


class WsmStateErrors(BaseModel):
    lowLevelSensor: bool
    ServerBlock: bool
    pour_1: bool
    pour_2: bool
    coinValidator: bool
    billValidator: bool
    PayPass: bool
    Card: bool


class WsmState(BaseModel):
    created: datetime
    summaInBox: int
    litersInTank: int
    operatingMode: WsmOperatingMode
    tankLowLevelSensor: bool
    tankHighLevelSensor: bool
    depositBoxSensor: bool
    doorSensor: bool
    coinState: int
    billState: int
    errors: WsmStateErrors


class WsmIoTControllerScheme(IoTControllerBaseDTO):
    config: WsmConfig | None
    settings: WsmSettings | None
    state: WsmState | None = None

    @classmethod
    def get_state_dto(cls):
        return WsmState


class WsmActionDTO(BaseModel):
    Pour: Literal["Start_1", "Start_2", "Stop"] | None = None


class SendWsmActionRequest(SendActionRequest):
    action: WsmActionDTO
