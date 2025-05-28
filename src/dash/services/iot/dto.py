from abc import abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel

from dash.models.controllers.controller import Controller, ControllerType


class ControllerID(BaseModel):
    controller_id: UUID


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
    name: str
    type: ControllerType

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
    checkbox_active: bool | None

    state: BaseModel | None
    energy_state: EnergyStateDTO | None = None
    alert: str | None = None

    @classmethod
    @abstractmethod
    def get_state_dto(cls) -> type[BaseModel]:
        raise NotImplementedError

    @classmethod
    def make(
        cls,
        model: Controller,
        state: dict[str, Any] | None,
        energy_state: dict[str, Any] | None,
    ) -> Self:
        dto = cls.model_validate(model, from_attributes=True)
        if state:
            dto.state = cls.get_state_dto().model_validate(state)
            if dto.state.created + timedelta(minutes=5) < datetime.now(UTC):
                dto.alert = "Контролер не надсилав оновлення більше 5 хвилин"
        if energy_state:
            dto.energy_state = EnergyStateDTO.model_validate(energy_state)

        return dto
