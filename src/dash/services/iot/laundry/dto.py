from typing import Any, Literal

from pydantic import BaseModel

from dash.models.controllers.laundry import LaundryStatus, LaundryTariffType
from dash.models.payment import PaymentGatewayType
from dash.services.common.dto import ControllerID
from dash.services.iot.dto import IoTControllerBaseDTO


class CreateLaundryInvoiceRequest(ControllerID):
    gateway_type: Literal[PaymentGatewayType.MONOPAY, PaymentGatewayType.LIQPAY]


class LaundryState(BaseModel):
    relay: list[dict[str, int | bool]]
    input: list[dict[str, int | bool]]
    output: list[dict[str, int | bool]]


class LaundryConfig(BaseModel):
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


class LaundryMqttSettings(BaseModel):
    inputCBT: list[dict[str, Any]]
    input_to_relay: list[dict[str, Any]]


class LaundryIoTControllerScheme(IoTControllerBaseDTO):
    input_id: int
    tariff_type: LaundryTariffType
    timeout_minutes: int
    laundry_status: LaundryStatus

    fixed_price: int
    max_hold_amount: int
    price_per_minute_before_transition: int
    transition_after_minutes: int
    price_per_minute_after_transition: int

    config: LaundryConfig | None
    settings: LaundryMqttSettings | None
    state: LaundryState | None = None

    @classmethod
    def get_state_dto(cls):
        return LaundryState


class LaundryBusinessSettings(BaseModel):
    input_id: int | None = None
    tariff_type: LaundryTariffType | None = None
    timeout_minutes: int | None = None
    fixed_price: int | None = None
    max_hold_amount: int | None = None
    price_per_minute_before_transition: int | None = None
    transition_after_minutes: int | None = None
    price_per_minute_after_transition: int | None = None


class UpdateLaudnrySettingsRequest(ControllerID):
    settings: LaundryBusinessSettings
