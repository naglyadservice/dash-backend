from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from dash.services.common.dto import ControllerID
from dash.services.iot.dto import (
    IoTControllerBaseDTO,
    SetConfigRequest,
    SetSettingsRequest,
)


class FiscalizerConfig(BaseModel):
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


INTERFACE_TYPE = Literal["protocol", "pulsed", "no"]


class PortSettingsDTO(BaseModel):
    interface: INTERFACE_TYPE
    pulse_price: int
    time_pulse: int
    time_pause: int
    table: list[int] = Field(min_length=24, max_length=24)


class FiscalizerSettings(BaseModel):
    mc: PortSettingsDTO | None = None
    coin: PortSettingsDTO | None = None
    bill: PortSettingsDTO | None = None
    fiscalizationTime: int | None = None


class SetFiscalizerConfigRequest(SetConfigRequest):
    config: FiscalizerConfig


class SetFiscalizerSettingsRequest(SetSettingsRequest):
    settings: FiscalizerSettings


class FiscalizerState(BaseModel):
    created: datetime
    input: bool | None = None


class FiscalizerIoTControllerScheme(IoTControllerBaseDTO):
    settings: FiscalizerSettings | None = None
    config: FiscalizerConfig | None = None
    state: FiscalizerState | None = None

    quick_deposit_button_1: int | None = None
    quick_deposit_button_2: int | None = None
    quick_deposit_button_3: int | None = None

    sim_number: str | None = None
    sim_serial: str | None = None

    description: str | None = None

    @classmethod
    def get_state_dto(cls):
        return FiscalizerState


class QuickDepositButtonsDTO(BaseModel):
    quick_deposit_button_1: int | None
    quick_deposit_button_2: int | None
    quick_deposit_button_3: int | None


class SetupQuickDepositButtonsRequest(ControllerID):
    buttons: QuickDepositButtonsDTO


class SIMDTO(BaseModel):
    sim_number: str | None
    sim_serial: str | None


class SetupSIMRequest(ControllerID):
    sim: SIMDTO


class SetDescriptionRequest(ControllerID):
    description: str | None
