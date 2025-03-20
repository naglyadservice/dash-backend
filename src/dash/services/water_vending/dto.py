from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, field_validator

from dash.models.transactions.transaction import PaymentStatus

COIN_VALIDATOR_TYPE = Literal["protocol", "impulse"]


class ControllerID(BaseModel):
    controller_id: int


class WaterVendingConfig(BaseModel):
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
    bill_table: list[int] | None = None
    coinValidatorType: COIN_VALIDATOR_TYPE | None = None
    coinPulsePrice: int | None = None
    coin_table: list[int] | None = None

    @field_validator("bill_table", "coin_table", mode="before")
    def validate_tables(cls, v: list[int]):
        length = len(v)
        if length < 16:
            v.extend([0] * (16 - length))

        return sorted(v)


class SetWaterVendingConfigRequest(ControllerID):
    config: WaterVendingConfig


class WaterVendingSettings(BaseModel):
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


class SetWaterVendingSettingsRequest(ControllerID):
    settings: WaterVendingSettings


class OperatingMode(StrEnum):
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


class WaterVendingState(BaseModel):
    created: datetime
    summaInBox: int
    litersInTank: int
    operatingMode: OperatingMode
    tankLowLevelSensor: bool
    tankHighLevelSensor: bool
    depositBoxSensor: bool
    doorSensor: bool
    coinState: int
    billState: int
    errors: dict[str, bool]


class WaterVendingControllerScheme(BaseModel):
    id: int
    device_id: str
    config: WaterVendingConfig
    settings: WaterVendingSettings
    state: WaterVendingState | None
    display: dict[str, str] | None


class PaymentClearOptionsDTO(BaseModel):
    CoinClear: bool | None = None
    BillClear: bool | None = None
    PrevClear: bool | None = None
    FreeClear: bool | None = None
    QRcodeClear: bool | None = None
    PayPassClear: bool | None = None


class ClearPaymentsRequest(ControllerID):
    options: PaymentClearOptionsDTO


class WaterVendingActionDTO(BaseModel):
    Pour: Literal["Start", "Stop"] | None = None
    Blocking: bool | None = None


class SendActionRequest(ControllerID):
    actions: WaterVendingActionDTO


class RebootControllerRequest(ControllerID):
    delay: int


class QRPaymentRequest(BaseModel):
    amount: int
    order_id: str


class SendQRPaymentRequest(ControllerID, QRPaymentRequest):
    pass


class FreePaymentRequest(BaseModel):
    amount: int


class SendFreePaymentRequest(ControllerID, FreePaymentRequest):
    pass


class WaterVendingTransactionScheme(BaseModel):
    id: int
    controller_transaction_id: int
    controller_id: int
    location_id: int | None
    coin_amount: int
    bill_amount: int
    prev_amount: int
    free_amount: int
    qr_amount: int
    paypass_amount: int
    out_liters_1: int
    out_liters_2: int
    sale_type: str
    status: PaymentStatus
    created_at: datetime
    received_at: datetime
