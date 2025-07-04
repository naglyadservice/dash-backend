from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

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


INTERFACE_TYPE = Literal["ccnet", "pulsed", "no"]


class InterfaceDTO(BaseModel):
    controller: INTERFACE_TYPE
    validator: INTERFACE_TYPE
    coin: INTERFACE_TYPE


class FiscalizerSettings(BaseModel):
    interface: InterfaceDTO | None = None
    simulatorMC_pulse_price: int | None = None
    bill_pulse_price: int | None = None
    coin_pulse_price: int | None = None
    simulatorMC_table: list[int] | None = Field(
        default=None, min_length=24, max_length=24
    )
    bill_table: list[int] | None = Field(default=None, min_length=24, max_length=24)
    coin_table: list[int] | None = Field(default=None, min_length=16, max_length=16)
    fiscalizationTime: int | None = None


class SetFiscalizerConfigRequest(SetConfigRequest):
    config: FiscalizerConfig


class SetFiscalizerSettingsRequest(SetSettingsRequest):
    settings: FiscalizerSettings


class FiscalizerState(BaseModel):
    created: datetime


class FiscalizerIoTControllerScheme(IoTControllerBaseDTO):
    settings: FiscalizerSettings | None = None
    config: FiscalizerConfig | None = None
    state: FiscalizerState | None = None

    @classmethod
    def get_state_dto(cls):
        return FiscalizerState
