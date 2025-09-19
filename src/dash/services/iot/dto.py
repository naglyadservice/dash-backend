from abc import abstractmethod
from datetime import datetime
from typing import Any, Literal, Self, Type
from uuid import UUID

from pydantic import BaseModel, Field

from dash.models.controllers.controller import Controller, ControllerType
from dash.models.payment import PaymentGatewayType
from dash.services.common.dto import CompanyDTO, ControllerID, LocationDTO


class SetConfigRequest(ControllerID):
    config: BaseModel


class SetSettingsRequest(ControllerID):
    settings: BaseModel


class GetDisplayInfoRequest(ControllerID):
    pass


class RebootDelayDTO(BaseModel):
    delay: int


class RebootControllerRequest(ControllerID, RebootDelayDTO):
    pass


class QRPaymentDTO(BaseModel):
    order_id: str
    amount: int


class SendQRPaymentRequest(ControllerID):
    payment: QRPaymentDTO


class FreePaymentDTO(BaseModel):
    amount: int


class SendFreePaymentRequest(ControllerID):
    payment: FreePaymentDTO


class PaymentClearOptionsDTO(BaseModel):
    CoinClear: bool | None = None
    BillClear: bool | None = None
    PrevClear: bool | None = None
    FreeClear: bool | None = None
    QRcodeClear: bool | None = None
    PayPassClear: bool | None = None


class ClearPaymentsRequest(ControllerID):
    options: PaymentClearOptionsDTO


class SendActionRequest(ControllerID):
    action: BaseModel


class BlockingDTO(BaseModel):
    blocking: bool


class BlockingRequest(ControllerID, BlockingDTO):
    pass


class EnergyStateDTO(BaseModel):
    created: datetime
    energy_today: float
    energy_yesterday: float
    energy_total: float
    energy_total_since: datetime
    power: float
    apparent_power: float
    reactive_power: float
    power_factor: float
    voltage: float
    current: float


class IoTControllerBaseDTO(BaseModel):
    id: UUID
    device_id: str
    tasmota_id: str | None
    name: str
    type: ControllerType
    qr: str
    version: str
    location: LocationDTO | None
    company: CompanyDTO | None
    last_reboot: datetime | None

    monopay_token: str | None
    monopay_active: bool
    liqpay_active: bool
    liqpay_public_key: str | None
    liqpay_private_key: str | None

    checkbox_login: str | None
    checkbox_password: str | None
    checkbox_license_key: str | None
    good_code: str | None
    good_name: str | None
    tax_code: str | None
    checkbox_active: bool
    fiscalize_cash: bool

    is_online: bool = True
    state: BaseModel | None = None
    energy_state: EnergyStateDTO | None = None

    min_deposit_amount: int

    @classmethod
    @abstractmethod
    def get_state_dto(cls) -> Type[BaseModel]:
        raise NotImplementedError

    @classmethod
    def make(
        cls,
        model: Controller,
        state: dict[str, Any] | None,
        energy_state: dict[str, Any] | None,
        is_online: bool,
    ) -> Self:
        dto = cls.model_validate(model, from_attributes=True)
        dto.is_online = is_online

        if state:
            dto.state = cls.get_state_dto().model_validate(state)
        if energy_state:
            dto.energy_state = EnergyStateDTO.model_validate(energy_state)

        return dto


class SyncSettingsRequest(ControllerID):
    pass


class SyncSettingsResponse(BaseModel):
    config: dict[str, Any]
    settings: dict[str, Any]


class AmountDTO(BaseModel):
    amount: int = Field(gt=0)


class CreateInvoiceRequest(ControllerID, AmountDTO):
    gateway_type: Literal[PaymentGatewayType.LIQPAY, PaymentGatewayType.MONOPAY]
    redirect_url: str


class CreateInvoiceResponse(BaseModel):
    invoice_url: str
    invoice_id: str = Field(exclude=True)
